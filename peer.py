import os
import sys
import json
import time
import random
import asyncio
import logging
from collections import Counter

from block_manager import BlockManager
from protocol import (
    send_message,
    recv_message,
    make_handshake_msg,
    make_have_msg,
    make_request_msg,
    make_block_msg,
    extract_block_data,
)

def setup_hybrid_logger(peer_id: str, log_dir: str = "logs") -> logging.Logger:
    """Decisão 5.1 (Opção A): Log completo em arquivo (.log) e progresso limpo no terminal."""
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(peer_id)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    # Handler 1: Arquivo .log detalhado (registra absolutamente todos os blocos)
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"{peer_id}.log"), mode="w", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Handler 2: Terminal resumido (mostra eventos principais, marcos de 10% e verificação final)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


class Peer:
    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        self.peer_id = self.config["peer_id"]
        self.ip = self.config["ip"]
        self.port = self.config["port"]
        self.neighbors = self.config["neighbors"]
        self.is_seeder = self.config["is_seeder"]
        self.file_path = self.config.get("file_path")
        self.metadata_path = self.config["metadata_path"]
        self.output_dir = self.config["output_dir"]
        self.log_dir = self.config.get("log_dir", "logs")

        self.logger = setup_hybrid_logger(self.peer_id, self.log_dir)

        self.block_manager = BlockManager(
            metadata_path=self.metadata_path,
            work_dir=self.output_dir,
            is_seeder=self.is_seeder,
            original_file_path=self.file_path,
            logger=self.logger
        )

        self.client_writers: set[asyncio.StreamWriter] = set()
        self.neighbor_bitfields: dict[tuple[str, int], list[bool]] = {}
        self.neighbor_ids: dict[tuple[str, int], str] = {}
        self.in_flight_blocks: set[int] = set()
        self.pending_requests: dict[tuple[tuple[str, int], int], asyncio.Future] = {}

        self.new_info_event = asyncio.Event()
        self.blocks_from_source = Counter()
        self.blocks_sent_to = Counter()
        self.start_time = None
        self.reassembled = self.is_seeder
        self.last_logged_milestone = 0

    async def broadcast_have(self, block_id: int):
        msg = make_have_msg(block_id)
        dead_writers = []
        for writer in list(self.client_writers):
            try:
                await send_message(writer, msg)
            except Exception:
                dead_writers.append(writer)
        for w in dead_writers:
            self.client_writers.discard(w)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        self.client_writers.add(writer)
        remote_peer_id = str(addr)

        try:
            await send_message(writer, make_handshake_msg(self.peer_id, self.block_manager.bitfield))

            while True:
                msg = await recv_message(reader)
                if msg is None:
                    break

                msg_type = msg.get("type")
                if msg_type == "HANDSHAKE":
                    remote_peer_id = msg["peer_id"]
                    self.logger.info(f"[{self.peer_id}] Servidor conectou com {remote_peer_id} ({addr})")

                elif msg_type == "REQUEST_BLOCK":
                    block_id = msg["block_id"]
                    if self.block_manager.bitfield[block_id]:
                        raw_data = self.block_manager.read_block(block_id)
                        await send_message(writer, make_block_msg(block_id, raw_data))
                        self.blocks_sent_to[remote_peer_id] += 1
                        self.logger.debug(
                            f"[{self.peer_id}] SERVIU bloco {block_id} para {remote_peer_id}"
                        )
                    else:
                        self.logger.warning(
                            f"[{self.peer_id}] {remote_peer_id} solicitou bloco {block_id} indisponível"
                        )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.debug(f"[{self.peer_id}] Conexão encerrada com {remote_peer_id}: {e}")
        finally:
            self.client_writers.discard(writer)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def connect_and_run_neighbor(self, neighbor_ip: str, neighbor_port: int):
        neighbor_key = (neighbor_ip, neighbor_port)

        while True:
            try:
                reader, writer = await asyncio.open_connection(neighbor_ip, neighbor_port)
                break
            except ConnectionRefusedError:
                await asyncio.sleep(0.5)

        await send_message(writer, make_handshake_msg(self.peer_id, self.block_manager.bitfield))

        listener_task = asyncio.create_task(self._listen_to_neighbor(neighbor_key, reader))
        worker_task = asyncio.create_task(self._neighbor_download_worker(neighbor_key, writer))

        try:
            await listener_task
        except Exception as e:
            self.logger.debug(f"[{self.peer_id}] Erro de leitura na conexão com {neighbor_key}: {e}")
        finally:
            # Conexão encerrada: cancela o worker (liberando o bloco em voo) e esquece o bitfield
            # do vizinho, para que os blocos que faltam sejam buscados nos vizinhos restantes
            worker_task.cancel()
            self.neighbor_bitfields.pop(neighbor_key, None)
            self.new_info_event.set()
            writer.close()
            neighbor_name = self.neighbor_ids.get(neighbor_key, str(neighbor_key))
            self.logger.warning(f"[{self.peer_id}] Conexão com {neighbor_name} encerrada; vizinho descartado")

    async def _listen_to_neighbor(self, neighbor_key: tuple[str, int], reader: asyncio.StreamReader):
        while True:
            msg = await recv_message(reader)
            if msg is None:
                break

            msg_type = msg.get("type")
            if msg_type == "HANDSHAKE":
                self.neighbor_ids[neighbor_key] = msg["peer_id"]
                self.neighbor_bitfields[neighbor_key] = list(msg["bitfield"])
                avail = sum(msg["bitfield"])
                self.logger.info(
                    f"[{self.peer_id}] Handshake recebido de {msg['peer_id']} "
                    f"({avail}/{self.block_manager.total_blocks} blocos disponíveis)"
                )
                self.new_info_event.set()

            elif msg_type == "HAVE":
                block_id = msg["block_id"]
                if neighbor_key in self.neighbor_bitfields:
                    self.neighbor_bitfields[neighbor_key][block_id] = True
                    self.logger.debug(
                        f"[{self.peer_id}] Notificação HAVE recebida: {self.neighbor_ids.get(neighbor_key)} "
                        f"agora possui o bloco {block_id}"
                    )
                    self.new_info_event.set()

            elif msg_type == "BLOCK_DATA":
                block_id = msg["block_id"]
                raw_data = extract_block_data(msg)
                req_key = (neighbor_key, block_id)
                if req_key in self.pending_requests:
                    fut = self.pending_requests.pop(req_key)
                    if not fut.done():
                        fut.set_result(raw_data)

    async def _neighbor_download_worker(self, neighbor_key: tuple[str, int], writer: asyncio.StreamWriter):
        while neighbor_key not in self.neighbor_bitfields:
            await asyncio.sleep(0.05)

        neighbor_name = self.neighbor_ids.get(neighbor_key, str(neighbor_key))
        total = self.block_manager.total_blocks

        while not self.block_manager.is_complete():
            neighbor_bf = self.neighbor_bitfields[neighbor_key]

            candidates = [
                b_id for b_id in self.block_manager.missing_set
                if b_id not in self.in_flight_blocks and neighbor_bf[b_id]
            ]

            if not candidates:
                self.new_info_event.clear()
                try:
                    await asyncio.wait_for(self.new_info_event.wait(), timeout=0.2)
                except asyncio.TimeoutError:
                    pass
                continue

            chosen_block = random.choice(candidates)
            self.in_flight_blocks.add(chosen_block)

            if self.start_time is None:
                self.start_time = time.time()

            req_key = (neighbor_key, chosen_block)
            fut = asyncio.get_running_loop().create_future()
            self.pending_requests[req_key] = fut

            try:
                await send_message(writer, make_request_msg(chosen_block))
                block_bytes = await asyncio.wait_for(fut, timeout=10.0)

                if not self.block_manager.save_block(chosen_block, block_bytes):
                    # Bloco rejeitado na verificação: continua em missing_set e será solicitado novamente
                    self.logger.warning(
                        f"[{self.peer_id}] Bloco {chosen_block} recebido de {neighbor_name} rejeitado; "
                        f"será solicitado novamente"
                    )
                    continue

                self.blocks_from_source[neighbor_name] += 1
                have_count = total - len(self.block_manager.missing_set)

                # Log detalhado no arquivo .log
                self.logger.debug(
                    f"[{self.peer_id}] BAIXOU bloco {chosen_block} de {neighbor_name} "
                    f"({have_count}/{total})"
                )

                # No terminal: mostra cada bloco se <= 20 blocos, ou a cada 10% em arquivos maiores
                pct = int((have_count / total) * 100)
                if total <= 20 or pct >= self.last_logged_milestone + 10 or have_count == total:
                    self.last_logged_milestone = (pct // 10) * 10
                    self.logger.info(
                        f"[{self.peer_id}] Progresso: {have_count}/{total} blocos ({pct}%) "
                        f"| Último: bloco {chosen_block} via {neighbor_name}"
                    )

                # Tornando-se Seeder desse bloco imediatamente (shield: o HAVE deve chegar a
                # todos os vizinhos mesmo que este worker seja cancelado no meio do envio)
                await asyncio.shield(self.broadcast_have(chosen_block))

            except TimeoutError:
                self.logger.warning(
                    f"[{self.peer_id}] Timeout aguardando bloco {chosen_block} de {neighbor_name}; "
                    f"será solicitado novamente"
                )
            except Exception as e:
                # Falha de envio = conexão perdida. Fecha o socket (o listener detecta e descarta o
                # vizinho) e encerra o worker, em vez de repetir o erro em loop sem ceder o event loop
                self.logger.error(f"[{self.peer_id}] Erro ao solicitar bloco {chosen_block} de {neighbor_name}: {e!r}")
                writer.close()
                return
            finally:
                self.in_flight_blocks.discard(chosen_block)
                self.pending_requests.pop(req_key, None)

        if not self.reassembled:
            self.reassembled = True
            elapsed = time.time() - (self.start_time or time.time())
            self.logger.info(f"[{self.peer_id}] Download completo em {elapsed:.3f}s! Remontando arquivo...")
            verify_info = self.block_manager.reassemble_and_verify()

            self.logger.info(
                f"[{self.peer_id}] VERIFICAÇÃO -> Integridade SHA-256: "
                f"{'OK' if verify_info['hash_ok'] else 'FALHOU'} | "
                f"Tamanho: {verify_info['actual_size']}/{verify_info['expected_size']} bytes | "
                f"Fontes dos blocos: {dict(self.blocks_from_source)}"
            )

            # Salva relatório JSON local do Peer para o script de testes automatizados
            # (grava em .tmp e renomeia, para o script nunca ler um JSON pela metade)
            status_path = os.path.join(self.output_dir, "status.json")
            tmp_path = status_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as sf:
                json.dump({
                    "peer_id": self.peer_id,
                    "elapsed_seconds": round(elapsed, 4),
                    "blocks_from_source": dict(self.blocks_from_source),
                    "verification": verify_info
                }, sf, indent=2)
            os.replace(tmp_path, status_path)

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.ip, self.port)
        have_count = self.block_manager.total_blocks - len(self.block_manager.missing_set)
        self.logger.info(
            f"[{self.peer_id}] Iniciado em {self.ip}:{self.port} | "
            f"Seeder Inicial: {self.is_seeder} ({have_count}/{self.block_manager.total_blocks} blocos)"
        )

        async with server:
            for n in self.neighbors:
                asyncio.create_task(self.connect_and_run_neighbor(n["ip"], n["port"]))
            await server.serve_forever()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python peer.py <caminho_config.json>")
        sys.exit(1)

    peer = Peer(sys.argv[1])
    try:
        asyncio.run(peer.start())
    except KeyboardInterrupt:
        pass
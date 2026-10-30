import os
import json
import hashlib
import logging

class BlockManager:
    def __init__(self, metadata_path: str, work_dir: str, is_seeder: bool, original_file_path: str = None,
                 logger: logging.Logger = None):
        # Usa o logger do Peer para que as mensagens caiam no .log dele (o logger raiz descartaria INFO)
        self.logger = logger or logging.getLogger(__name__)

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.file_name = self.metadata["file_name"]
        self.file_size = self.metadata["file_size"]
        self.block_size = self.metadata["block_size"]
        self.total_blocks = self.metadata["total_blocks"]
        self.expected_sha256 = self.metadata["sha256"]
        self.block_hashes: list[str] = self.metadata["block_hashes"]

        self.work_dir = work_dir
        self.blocks_dir = os.path.join(work_dir, "blocks")
        os.makedirs(self.blocks_dir, exist_ok=True)

        # Decisão 2.2 (Opção A): Array booleano rastreando quais blocos o Peer possui
        self.bitfield: list[bool] = [False] * self.total_blocks
        self.missing_set: set[int] = set(range(self.total_blocks))

        if is_seeder:
            if not original_file_path or not os.path.exists(original_file_path):
                raise FileNotFoundError(f"Seeder precisa do arquivo original: {original_file_path}")
            self._fragment_original_file(original_file_path)

    def _get_block_path(self, block_id: int) -> str:
        return os.path.join(self.blocks_dir, f"block_{block_id:06d}.bin")

    def expected_block_length(self, block_id: int) -> int:
        if block_id == self.total_blocks - 1:
            remainder = self.file_size % self.block_size
            return remainder if remainder != 0 else self.block_size
        return self.block_size

    def _fragment_original_file(self, original_file_path: str):
        self.logger.info(f"Fragmentando arquivo original em {self.total_blocks} blocos de {self.block_size} bytes...")
        with open(original_file_path, "rb") as f:
            for block_id in range(self.total_blocks):
                data = f.read(self.block_size)
                with open(self._get_block_path(block_id), "wb") as bf:
                    bf.write(data)
                self.bitfield[block_id] = True
                self.missing_set.discard(block_id)
        self.logger.info("Fragmentação concluída com sucesso.")

    def save_block(self, block_id: int, data: bytes) -> bool:
        if block_id < 0 or block_id >= self.total_blocks:
            self.logger.error(f"Bloco inválido recebido: {block_id}")
            return False

        expected_len = self.expected_block_length(block_id)
        if len(data) != expected_len:
            self.logger.error(f"Bloco {block_id} corrompido: tamanho {len(data)} != esperado {expected_len}")
            return False

        # Verificação individual: o bloco só é aceito se o SHA-256 bater com o do metadado
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != self.block_hashes[block_id]:
            self.logger.error(f"Bloco {block_id} corrompido: SHA-256 {actual_hash[:12]}... não confere com o metadado")
            return False

        with open(self._get_block_path(block_id), "wb") as bf:
            bf.write(data)

        self.bitfield[block_id] = True
        self.missing_set.discard(block_id)
        return True

    def read_block(self, block_id: int) -> bytes:
        if not self.bitfield[block_id]:
            raise ValueError(f"Tentativa de ler bloco {block_id} que o Peer ainda não possui.")
        with open(self._get_block_path(block_id), "rb") as bf:
            return bf.read()

    def is_complete(self) -> bool:
        return len(self.missing_set) == 0

    def reassemble_and_verify(self) -> dict:
        """Remonta o arquivo final e retorna dicionário com os dados de verificação."""
        final_path = os.path.join(self.work_dir, self.file_name)
        sha256 = hashlib.sha256()

        with open(final_path, "wb") as out_f:
            for block_id in range(self.total_blocks):
                block_data = self.read_block(block_id)
                out_f.write(block_data)
                sha256.update(block_data)

        actual_size = os.path.getsize(final_path)
        actual_hash = sha256.hexdigest()

        size_ok = (actual_size == self.file_size)
        hash_ok = (actual_hash == self.expected_sha256)

        return {
            "final_path": final_path,
            "expected_size": self.file_size,
            "actual_size": actual_size,
            "size_ok": size_ok,
            "expected_sha256": self.expected_sha256,
            "actual_sha256": actual_hash,
            "hash_ok": hash_ok,
            "verified": size_ok and hash_ok
        }
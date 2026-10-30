import json
import struct
import base64
import asyncio

async def send_message(writer: asyncio.StreamWriter, message: dict):
    """Serializa um dicionário em JSON (UTF-8) precedido por 4 bytes de tamanho (Big-Endian)."""
    payload_bytes = json.dumps(message).encode("utf-8")
    header = struct.pack(">I", len(payload_bytes))
    writer.write(header + payload_bytes)
    await writer.drain()

async def recv_message(reader: asyncio.StreamReader) -> dict | None:
    """Lê o cabeçalho de 4 bytes e desserializa a mensagem JSON completa."""
    try:
        header = await reader.readexactly(4)
        (msg_length,) = struct.unpack(">I", header)
        payload_bytes = await reader.readexactly(msg_length)
        return json.loads(payload_bytes.decode("utf-8"))
    except asyncio.IncompleteReadError:
        return None

def make_handshake_msg(peer_id: str, bitfield: list[bool]) -> dict:
    return {
        "type": "HANDSHAKE",
        "peer_id": peer_id,
        "bitfield": bitfield
    }

def make_have_msg(block_id: int) -> dict:
    return {
        "type": "HAVE",
        "block_id": block_id
    }

def make_request_msg(block_id: int) -> dict:
    return {
        "type": "REQUEST_BLOCK",
        "block_id": block_id
    }

def make_block_msg(block_id: int, raw_data: bytes) -> dict:
    return {
        "type": "BLOCK_DATA",
        "block_id": block_id,
        "data_b64": base64.b64encode(raw_data).decode("ascii")
    }

def extract_block_data(message: dict) -> bytes:
    return base64.b64decode(message["data_b64"].encode("ascii"))
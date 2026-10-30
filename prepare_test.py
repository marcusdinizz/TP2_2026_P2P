import os
import json
import math
import hashlib
import argparse

def calculate_sha256(file_path: str) -> str:
    """Calcula o hash SHA-256 lendo o arquivo do disco em pedaços."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def generate_test_environment(file_name: str, size_kb: int, block_size: int, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, file_name)
    file_size_bytes = size_kb * 1024

    # 1. Cria arquivo binário com conteúdo aleatório único
    with open(file_path, "wb") as f:
        f.write(os.urandom(file_size_bytes))

    # 2. Calcula checksum SHA-256 do arquivo, de cada bloco e total de blocos
    file_hash = calculate_sha256(file_path)
    total_blocks = math.ceil(file_size_bytes / block_size)

    block_hashes = []
    with open(file_path, "rb") as f:
        while block := f.read(block_size):
            block_hashes.append(hashlib.sha256(block).hexdigest())

    # 3. Salva o arquivo de metadados (.meta.json)
    metadata = {
        "file_name": file_name,
        "file_size": file_size_bytes,
        "block_size": block_size,
        "total_blocks": total_blocks,
        "sha256": file_hash,
        "block_hashes": block_hashes
    }

    meta_path = f"{file_path}.meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Arquivo criado: {file_path} ({file_size_bytes} bytes)")
    print(f"[OK] Metadado criado: {meta_path} ({total_blocks} blocos de {block_size} B)")
    print(f"[OK] SHA-256: {file_hash}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerador de arquivos e metadados para o TP2 P2P")
    parser.add_argument("--name", default="file_A.bin", help="Nome do arquivo (ex: file_A.bin)")
    parser.add_argument("--size-kb", type=int, default=10, help="Tamanho em KB (ex: 10, 1024, 10240)")
    parser.add_argument("--block-size", type=int, default=1024, help="Tamanho do bloco em bytes (1024 ou 4096)")
    parser.add_argument("--dir", default="arquivos", help="Diretório de saída")
    args = parser.parse_args()

    generate_test_environment(args.name, args.size_kb, args.block_size, args.dir)
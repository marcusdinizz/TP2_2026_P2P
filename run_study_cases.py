import os
import sys
import json
import time
import shutil
import subprocess
from prepare_test import generate_test_environment

# Parâmetros da Tabela 1 do enunciado (valor padrão e variação de cada um)
TEST_FILES = [
    ("File_A", 10), ("File_A", 20),        # Arquivo pequeno: 10 KB / 20 KB
    ("File_B", 1024), ("File_B", 5120),    # Arquivo médio:   1 MB / 5 MB
    ("File_C", 10240), ("File_C", 20480),  # Arquivo grande: 10 MB / 20 MB
]
BLOCK_SIZES = [1024, 4096]
PEER_COUNTS = [2, 4]


def format_size(size_kb: int) -> str:
    return f"{size_kb // 1024} MB" if size_kb >= 1024 else f"{size_kb} KB"


def format_ratio(numerator: float, denominator: float) -> str:
    return f"{numerator / denominator:.2f}x" if denominator > 0 else "N/A"


def build_peer_configs(num_peers: int, meta_path: str, orig_file_path: str, base_work_dir: str, log_dir: str) -> list[str]:
    """
    Cria os arquivos JSON de configuração estática para 2 Peers ou 4 Peers (Decisão 5.2 - Opção B).
    """
    configs_dir = os.path.join(base_work_dir, "configs")
    os.makedirs(configs_dir, exist_ok=True)

    if num_peers == 2:
        # 2 Peers: Peer_A (Seeder: 5001) <-> Peer_B (Leecher: 5002)
        topology = {
            "Peer_A": {"port": 5001, "is_seeder": True,  "neighbors": [{"ip": "127.0.0.1", "port": 5002}]},
            "Peer_B": {"port": 5002, "is_seeder": False, "neighbors": [{"ip": "127.0.0.1", "port": 5001}]},
        }
    else:
        # 4 Peers (Decisão 5.2 - Opção B):
        # Peer_A (Seeder: 5001) conectado apenas a B e C.
        # Peer_B (5002) e Peer_C (5003) conectados a A, entre si (B<->C) e a D.
        # Peer_D (5004) conectado APENAS a B e C (prova que baixa 100% de Leechers que viraram Seeders).
        topology = {
            "Peer_A": {
                "port": 5001,
                "is_seeder": True,
                "neighbors": [
                    {"ip": "127.0.0.1", "port": 5002},
                    {"ip": "127.0.0.1", "port": 5003},
                ],
            },
            "Peer_B": {
                "port": 5002,
                "is_seeder": False,
                "neighbors": [
                    {"ip": "127.0.0.1", "port": 5001},
                    {"ip": "127.0.0.1", "port": 5003},
                    {"ip": "127.0.0.1", "port": 5004},
                ],
            },
            "Peer_C": {
                "port": 5003,
                "is_seeder": False,
                "neighbors": [
                    {"ip": "127.0.0.1", "port": 5001},
                    {"ip": "127.0.0.1", "port": 5002},
                    {"ip": "127.0.0.1", "port": 5004},
                ],
            },
            "Peer_D": {
                "port": 5004,
                "is_seeder": False,
                "neighbors": [
                    {"ip": "127.0.0.1", "port": 5002},
                    {"ip": "127.0.0.1", "port": 5003},
                ],
            },
        }

    config_paths = []
    for peer_id, info in topology.items():
        peer_out_dir = os.path.join(base_work_dir, peer_id)
        os.makedirs(peer_out_dir, exist_ok=True)
        cfg = {
            "peer_id": peer_id,
            "ip": "127.0.0.1",
            "port": info["port"],
            "neighbors": info["neighbors"],
            "is_seeder": info["is_seeder"],
            "file_path": orig_file_path if info["is_seeder"] else None,
            "metadata_path": meta_path,
            "output_dir": peer_out_dir,
            "log_dir": log_dir,
        }
        cfg_path = os.path.join(configs_dir, f"{peer_id}.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        config_paths.append(cfg_path)

    return config_paths


def run_single_case(case_name: str, file_label: str, size_kb: int, block_size: int, num_peers: int) -> dict:
    print(f"\n{'='*75}")
    print(f"Executando Caso: {case_name} | Arquivo: {file_label} ({size_kb} KB) | Bloco: {block_size} B | Peers: {num_peers}")
    print(f"{'='*75}")

    case_dir = os.path.join("test_runs", case_name)
    if os.path.exists(case_dir):
        shutil.rmtree(case_dir)

    data_dir = os.path.join(case_dir, "arquivos")
    log_dir = os.path.join(case_dir, "logs")
    file_name = f"{file_label}.bin"

    # 1. Preparação: cria arquivo aleatório e metadado
    generate_test_environment(file_name, size_kb, block_size, data_dir)
    orig_file_path = os.path.join(data_dir, file_name)
    meta_path = f"{orig_file_path}.meta.json"

    # 2. Geração dos arquivos de configuração estática dos Peers
    config_paths = build_peer_configs(num_peers, meta_path, orig_file_path, case_dir, log_dir)

    # 3. Início de todos os processos Peers simultaneamente
    procs = []
    start_wall = time.time()
    for cfg_path in config_paths:
        p = subprocess.Popen([sys.executable, "peer.py", cfg_path])
        procs.append(p)

    # 4. Monitoramento: aguarda todos os Leechers gerarem seu status.json de conclusão
    leecher_ids = ["Peer_B"] if num_peers == 2 else ["Peer_B", "Peer_C", "Peer_D"]
    status_files = [os.path.join(case_dir, pid, "status.json") for pid in leecher_ids]

    try:
        while True:
            if all(os.path.exists(sf) for sf in status_files):
                break
            if time.time() - start_wall > 300:
                raise TimeoutError(f"Tempo limite excedido no caso {case_name}")
            time.sleep(0.2)
    finally:
        # Encerra os processos Peers após todos concluírem e verificarem o arquivo
        time.sleep(0.3)
        for p in procs:
            p.terminate()
        for p in procs:
            p.wait()

    # 5. Coleta dos resultados de verificação
    with open(meta_path, "r", encoding="utf-8") as f:
        total_blocks = json.load(f)["total_blocks"]

    results_per_peer = {}
    all_verified = True
    max_time = 0.0

    for sf in status_files:
        with open(sf, "r", encoding="utf-8") as f:
            st = json.load(f)
            pid = st["peer_id"]
            results_per_peer[pid] = st
            max_time = max(max_time, st["elapsed_seconds"])
            if not st["verification"]["verified"]:
                all_verified = False

    return {
        "case_name": case_name,
        "file_label": f"{file_label} ({format_size(size_kb)})",
        "block_size": block_size,
        "num_peers": num_peers,
        "total_blocks": total_blocks,
        "max_time_s": max_time,
        "all_verified": all_verified,
        "peers": results_per_peer,
        "log_dir": log_dir
    }


def main():
    # Também deixa uma pasta de configuração manual pronta para demonstrações rápidas
    generate_test_environment("file_A.bin", 10, 1024, "arquivos_manual")
    build_peer_configs(
        4,
        "arquivos_manual/file_A.bin.meta.json",
        "arquivos_manual/file_A.bin",
        "manual_demo_4peers",
        "manual_demo_4peers/logs"
    )

    # Matriz fatorial completa da Tabela 1 do TP2: cada arquivo (valor padrão e variação) é
    # testado com cada tamanho de bloco e cada quantidade de peers. Assim, para isolar o efeito
    # de um parâmetro, basta comparar casos que diferem apenas nele.
    study_cases = []
    for file_label, size_kb in TEST_FILES:
        for block_size in BLOCK_SIZES:
            for num_peers in PEER_COUNTS:
                case_name = (
                    f"{len(study_cases) + 1:02d}_{file_label.replace('_', '')}_{format_size(size_kb).replace(' ', '')}"
                    f"_{block_size // 1024}KB_{num_peers}P"
                )
                study_cases.append((case_name, file_label, size_kb, block_size, num_peers))

    summary_rows = []
    for case in study_cases:
        res = run_single_case(*case)
        summary_rows.append(res)

    # Gera tabelas Markdown para o Relatório
    md_lines = [
        "# Resultados Experimentais dos Estudos de Caso (TP2 P2P)\n",
        "Tempo = tempo do leecher mais lento, do primeiro pedido até a conclusão do download.\n",
        "## Todos os casos\n",
        "| Caso | Arquivo | Bloco | Blocos | Peers | Tempo Total (s) | SHA-256 & Tamanho | Fontes de Blocos por Leecher |",
        "|---|---|---|---|---|---|---|---|"
    ]

    for r in summary_rows:
        sources_str = " / ".join(
            f"**{pid}**: {data['blocks_from_source']}"
            for pid, data in r["peers"].items()
        )
        ver_str = "100% Íntegro" if r["all_verified"] else "ERRO"
        md_lines.append(
            f"| {r['case_name']} | {r['file_label']} | {r['block_size']} B | {r['total_blocks']} | "
            f"{r['num_peers']} | {r['max_time_s']:.3f}s | {ver_str} | {sources_str} |"
        )

    by_params = {(r["file_label"], r["block_size"], r["num_peers"]): r for r in summary_rows}
    file_labels = list(dict.fromkeys(r["file_label"] for r in summary_rows))

    # Impacto dos peers: mesmo arquivo e mesmo bloco, variando só a quantidade de peers
    md_lines += [
        "\n## Impacto da quantidade de peers (bloco fixo)\n",
        f"| Arquivo | Bloco | Tempo {PEER_COUNTS[0]} peers (s) | Tempo {PEER_COUNTS[1]} peers (s) "
        f"| Razão {PEER_COUNTS[1]}P/{PEER_COUNTS[0]}P |",
        "|---|---|---|---|---|"
    ]
    for label in file_labels:
        for block_size in BLOCK_SIZES:
            t_a = by_params[(label, block_size, PEER_COUNTS[0])]["max_time_s"]
            t_b = by_params[(label, block_size, PEER_COUNTS[1])]["max_time_s"]
            md_lines.append(f"| {label} | {block_size} B | {t_a:.3f} | {t_b:.3f} | {format_ratio(t_b, t_a)} |")

    # Impacto da fragmentação: mesmo arquivo e mesma quantidade de peers, variando só o bloco
    md_lines += [
        "\n## Impacto do tamanho do bloco (peers fixos)\n",
        f"| Arquivo | Peers | Blocos ({BLOCK_SIZES[0]} B) | Tempo {BLOCK_SIZES[0]} B (s) "
        f"| Blocos ({BLOCK_SIZES[1]} B) | Tempo {BLOCK_SIZES[1]} B (s) | Razão {BLOCK_SIZES[1]}/{BLOCK_SIZES[0]} |",
        "|---|---|---|---|---|---|---|"
    ]
    for label in file_labels:
        for num_peers in PEER_COUNTS:
            r_a = by_params[(label, BLOCK_SIZES[0], num_peers)]
            r_b = by_params[(label, BLOCK_SIZES[1], num_peers)]
            md_lines.append(
                f"| {label} | {num_peers} | {r_a['total_blocks']} | {r_a['max_time_s']:.3f} | "
                f"{r_b['total_blocks']} | {r_b['max_time_s']:.3f} | {format_ratio(r_b['max_time_s'], r_a['max_time_s'])} |"
            )

    md_output = "\n".join(md_lines)
    print("\n" + md_output)

    with open("resultado_testes.md", "w", encoding="utf-8") as f:
        f.write(md_output + "\n")
    print("\n[OK] Tabela salva em 'resultado_testes.md' e logs completos gravados em 'test_runs/<caso>/logs/'!")


if __name__ == "__main__":
    main()
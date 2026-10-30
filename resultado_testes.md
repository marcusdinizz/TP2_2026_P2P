# Resultados Experimentais dos Estudos de Caso (TP2 P2P)

Tempo = tempo do leecher mais lento, do primeiro pedido até a conclusão do download.

## Todos os casos

| Caso | Arquivo | Bloco | Blocos | Peers | Tempo Total (s) | SHA-256 & Tamanho | Fontes de Blocos por Leecher |
|---|---|---|---|---|---|---|---|
| 01_FileA_10KB_1KB_2P | File_A (10 KB) | 1024 B | 10 | 2 | 0.028s | 100% Íntegro | **Peer_B**: {'Peer_A': 10} |
| 02_FileA_10KB_1KB_4P | File_A (10 KB) | 1024 B | 10 | 4 | 0.045s | 100% Íntegro | **Peer_B**: {'Peer_A': 7, 'Peer_C': 3} / **Peer_C**: {'Peer_A': 6, 'Peer_B': 4} / **Peer_D**: {'Peer_B': 5, 'Peer_C': 5} |
| 03_FileA_10KB_4KB_2P | File_A (10 KB) | 4096 B | 3 | 2 | 0.007s | 100% Íntegro | **Peer_B**: {'Peer_A': 3} |
| 04_FileA_10KB_4KB_4P | File_A (10 KB) | 4096 B | 3 | 4 | 0.009s | 100% Íntegro | **Peer_B**: {'Peer_A': 2, 'Peer_C': 1} / **Peer_C**: {'Peer_A': 3} / **Peer_D**: {'Peer_C': 1, 'Peer_B': 2} |
| 05_FileA_20KB_1KB_2P | File_A (20 KB) | 1024 B | 20 | 2 | 0.040s | 100% Íntegro | **Peer_B**: {'Peer_A': 20} |
| 06_FileA_20KB_1KB_4P | File_A (20 KB) | 1024 B | 20 | 4 | 0.134s | 100% Íntegro | **Peer_B**: {'Peer_A': 13, 'Peer_C': 6, 'Peer_D': 1} / **Peer_C**: {'Peer_A': 11, 'Peer_B': 7, 'Peer_D': 2} / **Peer_D**: {'Peer_B': 11, 'Peer_C': 9} |
| 07_FileA_20KB_4KB_2P | File_A (20 KB) | 4096 B | 5 | 2 | 0.009s | 100% Íntegro | **Peer_B**: {'Peer_A': 5} |
| 08_FileA_20KB_4KB_4P | File_A (20 KB) | 4096 B | 5 | 4 | 0.016s | 100% Íntegro | **Peer_B**: {'Peer_A': 5} / **Peer_C**: {'Peer_A': 2, 'Peer_B': 2, 'Peer_D': 1} / **Peer_D**: {'Peer_B': 5} |
| 09_FileB_1MB_1KB_2P | File_B (1 MB) | 1024 B | 1024 | 2 | 2.293s | 100% Íntegro | **Peer_B**: {'Peer_A': 1024} |
| 10_FileB_1MB_1KB_4P | File_B (1 MB) | 1024 B | 1024 | 4 | 3.650s | 100% Íntegro | **Peer_B**: {'Peer_A': 676, 'Peer_C': 277, 'Peer_D': 71} / **Peer_C**: {'Peer_A': 411, 'Peer_B': 299, 'Peer_D': 314} / **Peer_D**: {'Peer_B': 671, 'Peer_C': 353} |
| 11_FileB_1MB_4KB_2P | File_B (1 MB) | 4096 B | 256 | 2 | 0.643s | 100% Íntegro | **Peer_B**: {'Peer_A': 256} |
| 12_FileB_1MB_4KB_4P | File_B (1 MB) | 4096 B | 256 | 4 | 0.934s | 100% Íntegro | **Peer_B**: {'Peer_A': 183, 'Peer_C': 69, 'Peer_D': 4} / **Peer_C**: {'Peer_B': 79, 'Peer_A': 98, 'Peer_D': 79} / **Peer_D**: {'Peer_B': 176, 'Peer_C': 80} |
| 13_FileB_5MB_1KB_2P | File_B (5 MB) | 1024 B | 5120 | 2 | 11.825s | 100% Íntegro | **Peer_B**: {'Peer_A': 5120} |
| 14_FileB_5MB_1KB_4P | File_B (5 MB) | 1024 B | 5120 | 4 | 22.669s | 100% Íntegro | **Peer_B**: {'Peer_A': 2560, 'Peer_C': 1699, 'Peer_D': 861} / **Peer_C**: {'Peer_B': 1693, 'Peer_A': 2573, 'Peer_D': 854} / **Peer_D**: {'Peer_B': 2554, 'Peer_C': 2566} |
| 15_FileB_5MB_4KB_2P | File_B (5 MB) | 4096 B | 1280 | 2 | 2.977s | 100% Íntegro | **Peer_B**: {'Peer_A': 1280} |
| 16_FileB_5MB_4KB_4P | File_B (5 MB) | 4096 B | 1280 | 4 | 4.104s | 100% Íntegro | **Peer_B**: {'Peer_C': 419, 'Peer_A': 640, 'Peer_D': 221} / **Peer_C**: {'Peer_A': 649, 'Peer_B': 420, 'Peer_D': 211} / **Peer_D**: {'Peer_C': 642, 'Peer_B': 638} |
| 17_FileC_10MB_1KB_2P | File_C (10 MB) | 1024 B | 10240 | 2 | 26.959s | 100% Íntegro | **Peer_B**: {'Peer_A': 10240} |
| 18_FileC_10MB_1KB_4P | File_C (10 MB) | 1024 B | 10240 | 4 | 61.135s | 100% Íntegro | **Peer_B**: {'Peer_A': 5099, 'Peer_D': 1763, 'Peer_C': 3378} / **Peer_C**: {'Peer_B': 3382, 'Peer_A': 5159, 'Peer_D': 1699} / **Peer_D**: {'Peer_B': 5089, 'Peer_C': 5151} |
| 19_FileC_10MB_4KB_2P | File_C (10 MB) | 4096 B | 2560 | 2 | 5.969s | 100% Íntegro | **Peer_B**: {'Peer_A': 2560} |
| 20_FileC_10MB_4KB_4P | File_C (10 MB) | 4096 B | 2560 | 4 | 9.304s | 100% Íntegro | **Peer_B**: {'Peer_A': 1311, 'Peer_C': 840, 'Peer_D': 409} / **Peer_C**: {'Peer_A': 1263, 'Peer_B': 848, 'Peer_D': 449} / **Peer_D**: {'Peer_C': 1255, 'Peer_B': 1305} |
| 21_FileC_20MB_1KB_2P | File_C (20 MB) | 1024 B | 20480 | 2 | 63.462s | 100% Íntegro | **Peer_B**: {'Peer_A': 20480} |
| 22_FileC_20MB_1KB_4P | File_C (20 MB) | 1024 B | 20480 | 4 | 119.150s | 100% Íntegro | **Peer_B**: {'Peer_A': 10230, 'Peer_C': 7541, 'Peer_D': 2709} / **Peer_C**: {'Peer_A': 10266, 'Peer_B': 7516, 'Peer_D': 2698} / **Peer_D**: {'Peer_B': 10217, 'Peer_C': 10263} |
| 23_FileC_20MB_4KB_2P | File_C (20 MB) | 4096 B | 5120 | 2 | 10.905s | 100% Íntegro | **Peer_B**: {'Peer_A': 5120} |
| 24_FileC_20MB_4KB_4P | File_C (20 MB) | 4096 B | 5120 | 4 | 21.395s | 100% Íntegro | **Peer_B**: {'Peer_A': 2575, 'Peer_C': 1795, 'Peer_D': 750} / **Peer_C**: {'Peer_A': 2565, 'Peer_B': 1793, 'Peer_D': 762} / **Peer_D**: {'Peer_B': 2567, 'Peer_C': 2553} |

## Impacto da quantidade de peers (bloco fixo)

| Arquivo | Bloco | Tempo 2 peers (s) | Tempo 4 peers (s) | Razão 4P/2P |
|---|---|---|---|---|
| File_A (10 KB) | 1024 B | 0.028 | 0.045 | 1.61x |
| File_A (10 KB) | 4096 B | 0.007 | 0.009 | 1.24x |
| File_A (20 KB) | 1024 B | 0.040 | 0.134 | 3.35x |
| File_A (20 KB) | 4096 B | 0.009 | 0.016 | 1.82x |
| File_B (1 MB) | 1024 B | 2.293 | 3.650 | 1.59x |
| File_B (1 MB) | 4096 B | 0.643 | 0.934 | 1.45x |
| File_B (5 MB) | 1024 B | 11.825 | 22.669 | 1.92x |
| File_B (5 MB) | 4096 B | 2.977 | 4.104 | 1.38x |
| File_C (10 MB) | 1024 B | 26.959 | 61.135 | 2.27x |
| File_C (10 MB) | 4096 B | 5.969 | 9.304 | 1.56x |
| File_C (20 MB) | 1024 B | 63.462 | 119.150 | 1.88x |
| File_C (20 MB) | 4096 B | 10.905 | 21.395 | 1.96x |

## Impacto do tamanho do bloco (peers fixos)

| Arquivo | Peers | Blocos (1024 B) | Tempo 1024 B (s) | Blocos (4096 B) | Tempo 4096 B (s) | Razão 4096/1024 |
|---|---|---|---|---|---|---|
| File_A (10 KB) | 2 | 10 | 0.028 | 3 | 0.007 | 0.25x |
| File_A (10 KB) | 4 | 10 | 0.045 | 3 | 0.009 | 0.19x |
| File_A (20 KB) | 2 | 20 | 0.040 | 5 | 0.009 | 0.22x |
| File_A (20 KB) | 4 | 20 | 0.134 | 5 | 0.016 | 0.12x |
| File_B (1 MB) | 2 | 1024 | 2.293 | 256 | 0.643 | 0.28x |
| File_B (1 MB) | 4 | 1024 | 3.650 | 256 | 0.934 | 0.26x |
| File_B (5 MB) | 2 | 5120 | 11.825 | 1280 | 2.977 | 0.25x |
| File_B (5 MB) | 4 | 5120 | 22.669 | 1280 | 4.104 | 0.18x |
| File_C (10 MB) | 2 | 10240 | 26.959 | 2560 | 5.969 | 0.22x |
| File_C (10 MB) | 4 | 10240 | 61.135 | 2560 | 9.304 | 0.15x |
| File_C (20 MB) | 2 | 20480 | 63.462 | 5120 | 10.905 | 0.17x |
| File_C (20 MB) | 4 | 20480 | 119.150 | 5120 | 21.395 | 0.18x |

# Phase L / Lesson L.2 -- Bien ban validate OWD probe

Ngay: 2026-07-29
Script: measurements/owd_probe.py, measurements/owd_analyze.py, measurements/l2_verify.py
Output JSON: results/phase-L/l2_probe_0729_0752.json
Raw prefix: results/phase-L/raw/0729_0752_*

Lenh da chay:

```bash
sudo -n mn -c
sudo -n python3 -u -m measurements.l2_verify
```

Ket luan ngan: PASS. V-L0 do san nhieu co SD < 0.2 ms, V-L2 cho thay
OWD tai 0 co HTB bang san phan mem va khong phu thuoc bw, V-L2b khop bac
thang token bucket o ca 8/6/4 Mbps.

## 1. V-L0 -- San nhieu

Khong dat qdisc o chieu do, khong tai nen, probe Poisson 100 pps trong 20 s.

| n | mean (ms) | sd (ms) | p50 (ms) | p99 (ms) | max (ms) | socket drops | foreign |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1988 | 0.1453 | 0.1186 | 0.1593 | 0.3090 | 3.7388 | 0 | 0 |

Ket qua: PASS, nguong SD <= 0.2 ms.

## 2. V-L2 -- Tai 0 co HTB

Amendment 1 doi ky vong: OWD tai 0 co HTB phai bang san phan mem, khong
ti le nghich voi bw.

| bw (Mbps) | q | mean (ms) | sd (ms) | abs(mean-floor) (ms) | socket drops | foreign | ket qua |
|---:|---:|---:|---:|---:|---:|---:|---|
| 8 | 18 | 0.1624 | 0.0702 | 0.0170 | 0 | 0 | PASS |
| 6 | 13 | 0.1407 | 0.0678 | 0.0046 | 0 | 0 | PASS |
| 4 | 10 | 0.1273 | 0.0687 | 0.0181 | 0 | 0 | PASS |

Tat ca deu nam duoi nguong 0.3 ms.

## 3. V-L2b -- Bac thang token bucket

Gui 8 goi 1470 B payload (= 1512 B tai qdisc) lien tiep vao link rong.
Dung median qua 5 burst doc lap. Cong thuc:

```text
d1 = d2 = 0
d_k = ((k - 1) * 1512 - 1600) / C   voi k >= 3
```

### bw = 8 Mbps, q = 18

| k | measured median (ms) | predicted (ms) | abs err (ms) |
|---:|---:|---:|---:|
| 1 | 0.117 | 0.000 | 0.117 |
| 2 | 0.091 | 0.000 | 0.091 |
| 3 | 1.468 | 1.424 | 0.044 |
| 4 | 2.933 | 2.936 | 0.003 |
| 5 | 4.442 | 4.448 | 0.006 |
| 6 | 5.939 | 5.960 | 0.021 |
| 7 | 7.464 | 7.472 | 0.008 |
| 8 | 8.946 | 8.984 | 0.038 |

Max err k>=3 = 0.0435 ms. PASS.

### bw = 6 Mbps, q = 13

| k | measured median (ms) | predicted (ms) | abs err (ms) |
|---:|---:|---:|---:|
| 1 | 0.074 | 0.000 | 0.074 |
| 2 | 0.044 | 0.000 | 0.044 |
| 3 | 1.877 | 1.899 | 0.022 |
| 4 | 3.941 | 3.915 | 0.026 |
| 5 | 5.905 | 5.931 | 0.026 |
| 6 | 7.915 | 7.947 | 0.031 |
| 7 | 9.923 | 9.963 | 0.040 |
| 8 | 11.949 | 11.979 | 0.029 |

Max err k>=3 = 0.0398 ms. PASS.

### bw = 4 Mbps, q = 10

| k | measured median (ms) | predicted (ms) | abs err (ms) |
|---:|---:|---:|---:|
| 1 | -0.025 | 0.000 | 0.025 |
| 2 | -0.050 | 0.000 | 0.050 |
| 3 | 2.860 | 2.848 | 0.012 |
| 4 | 5.874 | 5.872 | 0.002 |
| 5 | 8.856 | 8.896 | 0.040 |
| 6 | 11.858 | 11.920 | 0.062 |
| 7 | 14.920 | 14.944 | 0.024 |
| 8 | 17.938 | 17.968 | 0.030 |

Max err k>=3 = 0.0623 ms. PASS.

## 4. Raw/analyzer integrity checks

Analyzer outputs:

```text
results/phase-L/l2_vl0_floor_stats_0729_0752.json
results/phase-L/l2_vl2_bw6_stats_0729_0752.json
results/phase-L/l2_vl2b_bw6_r0_stats_0729_0752.json
```

| file | n_sent | n_recv_unique | loss | dup | reorder | owd_negative | c_a |
|---|---:|---:|---:|---:|---:|---:|---:|
| vl0_floor | 1776 | 1776 | 0.0 | 0 | 0 | 0 | 0.984 |
| vl2_bw6 | 1253 | 1253 | 0.0 | 0 | 0 | 0 | 0.963 |
| vl2b_bw6_r0 | 8 | 8 | 0.0 | 0 | 0 | 0 | 1.739 |

Tat ca raw RX co kich thuoc chia het cho 24 byte; tat ca raw TX co kich
thuoc chia het cho 16 byte. `socket_drops_delta = 0` va `n_foreign_packets = 0`
trong moi lan chay validation.

## 5. Dieu da hoc

- V-L0 xac nhan userspace timestamp du de di tiep, chua can SO_TIMESTAMPNS.
- V-L2 xac nhan Amendment 1: HTB khong them serialization delay tai zero load.
- V-L2b chung minh dong thoi ba tham so T0: probe timestamp dung, rate C dung,
  va burst 1600 B dung. Sai so lon nhat tu k>=3 chi 0.0623 ms.

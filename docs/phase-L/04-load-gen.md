# Phase L / Lesson L.4 -- Load generator

Muc tieu cua L.4 la bien `c_a` thanh bien thiet ke co the dat, do lai, va
doi chieu. Bo sinh tai cu khong lam duoc dieu nay vi schedule phu thuoc dong ho
tuong va cach gui that.

## File

| file | vai tro |
|---|---|
| `mininet/load_spec.py` | spec thuan: byte accounting, sinh gap, chuan hoa toc do, digest |
| `measurements/load_gen.py` | sender song: nen + probe trong mot tien trinh, mot socket |
| `measurements/owd_probe.py` | receiver tach `_bg.bin` va `_probe.bin` theo packet kind |
| `measurements/l4_verify.py` | live verifier cho V-L3, V-L4, V-L7 |
| `test/test_phase_l_load_spec.py` | regression tests khong can root |

## Bon che do

| mode | design c_a | y nghia |
|---|---:|---|
| cbr | 0 | gap tat dinh |
| poisson | 1 | renewal Exp |
| h2 | 2 | hyperexponential balanced-means |
| onoff | null | Pareto ON-OFF LRD, c_a phai do lai |

`h2` la truc chinh vi seed-to-seed rat on dinh; `onoff` la doi chung thuc te
cho tuong quan tam xa.

## Accounting rho

```
frame_bg    = 1470 + 42 = 1512 B
frame_probe =   64 + 42 =  106 B
C_bytes     = bw_mbps * 1e6 / 8
rho         = (bg_pps * 1512 + probe_pps * 106) / C_bytes
```

Vi probe nam trong qdisc, probe nam trong rho. Khong dung `OVERHEAD_FACTOR`.

## Provenance moi diem

Moi file `*_tx.meta.json` cua `load_gen.py` ghi:

| nhom | truong chinh |
|---|---|
| config | bw, rho_nominal, mode, duration, seed, run_id, payload/frame bytes |
| schedule | n_bg, n_probe, digest_bg, digest_probe |
| c_a | design_target, schedule_bg, actual_bg, aggregate_schedule |
| rates | bg_pps_target, bg_pps_actual, probe_pps_actual, rho_actual, rate_ratio |
| counts | n_bg_sent, n_probe_sent, n_late, max_late_ms, duration_s_actual |

Ba so `design_target`, `schedule_bg`, `actual_bg` dung de dinh vi loi: spec hay
khau phat. `aggregate_schedule` la dong ma hang doi nhin thay.

## Lenh chay lai

Unit tests:

```bash
pytest test/test_phase_l_load_spec.py -q
pytest test/test_phase_l_*.py -q
```

Live verification:

```bash
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.l4_verify 2>&1 | tee /tmp/dt4n_l4.out
```

Ghi chu V-L7: cac diem probe 0/10/20 pps dung duration 80 s, vi run 40 s dau
tien cho signed deviation am 2.94% tai 20 pps. Gate khong doi: `|dev| < 2%`
voi probe <=20 pps; chi tang cua so do de giam noise.

Chay rieng sender/receiver trong Mininet thu cong:

```bash
python3 -m measurements.owd_probe recv --port 5555 --duration 80 \
  --out-prefix results/phase-L/raw/manual_l4

python3 -m measurements.load_gen --dst 10.0.0.2 --port 5555 \
  --bw 6 --rho 0.90 --mode h2 --duration 70 --seed 1 --run-id 1 \
  --out-prefix results/phase-L/raw/manual_l4
```

## Gates L.4

| gate | dieu kien |
|---|---|
| V-L3 | rho thap: loss=0, socket_drops=0, foreign=0 |
| V-L4a | c_a actual khop design trong 10% cho poisson/h2; cbr gan 0 |
| V-L4b | `abs(rate_ratio - 1) < 0.001` |
| V-L4c | `abs(rho_actual - rho_nominal) < 0.002` |
| V-L4d | socket_drops=0, foreign=0, n_late_ratio < 0.001, max_late_ms < 50 |
| V-L7 | probe <=20 pps lam q_delay lech < 2% |

Smoke khong dung de HARK: tai rho=0.90 ky vong `cbr < poisson < h2`.

## Ket qua live 2026-07-29

Artifact PASS:

```
results/phase-L/l4_loadgen_0729_1007.json
```

V-L3:

| mean_ms | p99_ms | loss | pass |
|---:|---:|---:|---|
| 0.1504 | 0.3081 | 0.00000 | PASS |

V-L4 tai bw=6 Mbps, q=13, rho=0.90:

| mode | c_a actual | rate_ratio | rho_actual | q_mean_ms | loss | pass |
|---|---:|---:|---:|---:|---:|---|
| cbr | 0.0060 | 0.999997 | 0.899997 | 0.135 | 0.0000 | PASS |
| poisson | 1.0121 | 0.999997 | 0.899997 | 6.077 | 0.0059 | PASS |
| h2 | 2.0151 | 0.999997 | 0.899997 | 10.799 | 0.0693 | PASS |
| onoff | 1.5056 | 0.999997 | 0.899997 | 5.825 | 0.0091 | PASS |

Smoke order:

```
cbr 0.135 < poisson 6.077 < h2 10.799  -> PASS
```

V-L7 probe intrusiveness:

| probe_pps | duration_s | q_mean_ms | loss | rho_actual |
|---:|---:|---:|---:|---:|
| 0 | 80 | 6.083 | 0.0041 | 0.899993 |
| 10 | 80 | 6.028 | 0.0043 | 0.899995 |
| 20 | 80 | 5.994 | 0.0044 | 0.899997 |
| 40 | 40 | 5.983 | 0.0067 | 0.899950 |

`max_dev_le20 = 1.46% -> PASS`. Ket luan van hanh: probe 20 pps khong tao
xam lan do duoc tai diem tham chieu bw=6 Mbps, q=13, rho=0.90.

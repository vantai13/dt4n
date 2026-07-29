# Phase L / Lesson L.5 -- Pilot

Muc tieu cua pilot la do duong cong `q(rho)` va do bien thien giua seed truoc
khi chay chien dich dai. Pilot khong dung de doi dai rho, doi mode, hay doi
nguong sau khi nhin so.

## File

| file | vai tro |
|---|---|
| `measurements/l5_pilot.py` | chay 42 diem live, in bang va ghi JSON |
| `measurements/owd_analyze.py` | analyzer co batch means |
| `test/test_phase_l_l5_pilot.py` | test plan/gate/power summary |

## Ke hoach do

| phan | diem |
|---|---:|
| 3 mode x 6 rho x 1 seed | 18 |
| 3 mode x 2 rho x 4 seed bo sung | 24 |
| tong | 42 |

Mode: `cbr`, `poisson`, `h2`.

Rho main: `0.50, 0.70, 0.80, 0.90, 0.95, 1.00`.

Rho do phuong sai: `0.80, 0.95`.

Seed: `11..15`, voi seed 11 da nam trong luoi main.

Thu tu chay duoc xao tron bang `ORDER_SEED = 9000` va ghi vao JSON.

## Lenh chay

Dry-run de xem thu tu:

```bash
python3 -m measurements.l5_pilot --dry-run
```

Full pilot, khoang 50 phut:

```bash
sudo -n mn -c
sudo -n env PYTHONPATH="$PWD" python3 -u -m measurements.l5_pilot 2>&1 | tee /tmp/dt4n_l5_pilot.out
```

Sau khi xong, xem file moi nhat:

```bash
ls -1t results/phase-L/l5_pilot_*.json | head -1
python3 -m json.tool "$(ls -1t results/phase-L/l5_pilot_*.json | head -1)" | less
```

Kiem gate nhanh:

```bash
python3 - <<'PY'
import glob, json
p = sorted(glob.glob("results/phase-L/l5_pilot_*.json"))[-1]
d = json.load(open(p))
s = d["summary"]
print("file", p)
print("P1 prediction:", s["prediction"]["n_close"], "/", s["prediction"]["n_total"], s["prediction"]["pass"])
print("P2 monotonic:", s["monotonic"]["pass"], s["monotonic"]["by_mode"])
print("P3 separated:", s["separated"]["pass"], s["separated"]["by_rho"])
print("P4 seed n:", s["power"]["n_for_gap_4p72_ms"], "pass", s["power"]["pass"])
print("P5 point gates:", s["point_gates"]["n_fail"], "/", s["point_gates"]["n_total"], s["point_gates"]["pass"])
PY
```

## Gates

| gate | dieu kien |
|---|---|
| P1 | >=14/18 diem co `abs(delta) < max(0.5 ms, 20%)` |
| P2 | moi duong `q(rho)` don dieu voi dung sai 0.3 ms |
| P3 | `cbr < poisson < h2` voi moi `rho >= 0.70` |
| P4 | seed can thiet cho gap 4.72 ms `<= 5` |
| P5 | it nhat 40/42 diem qua gate van hanh |

Gate van hanh tung diem:

```text
socket_drops_delta = 0
n_foreign_packets = 0
abs(rate_ratio - 1) < 0.001
abs(rho_actual - rho_nominal) < 0.002
n_late_ratio < 0.001
max_late_ms < 50
```

## Sau Pilot

Ket qua can doc:

- Bang du doan-vs-thuc te theo rho.
- `sd_between_seed_max_ms` va so seed can thiet.
- CI95 cua `delta_pasta_ms` cho poisson tai rho 0.80 va 0.95.
- Diem bat dau loss >= 1% cho tung mode.

Quyet dinh L.6 dua tren nhung so nay, khong dua tren cam giac.

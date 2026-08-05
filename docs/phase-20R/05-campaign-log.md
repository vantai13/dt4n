# Phase 20R.4 -- Campaign Log

## Pre-Full Smoke And Continuity

Ngay ghi: 2026-08-04

Smoke state hien co: `results/phase-20R/smoke_state.json`.

```text
smoke rows      : 10/10
smoke gate fail : 0
sentinel smoke  : z = +0.53 sigma so voi Phase L ref
```

Continuity state hien co: `results/phase-20R/continuity_state.json`.
Check: `results/phase-20R/continuity_check.json`.

```text
continuity: 8/8 pass
max |diff|/tol_2se < 0.50
```

Chi tiet dang ghi nho: ca 3 diem `cbr` trong continuity deu lech cung dau
am, co -0.003 ms so voi Phase L. Day la khoang 0.6% san nhieu 0.4646 ms va
khong co y nghia vat chat cho bai toan quyet dinh. Neu sau nay thay pattern
nay lap lai, xem nhu ghi chu drift nho can theo doi, khong phai blocker.

## Provenance Freeze

Smoke va continuity dau tien duoc chay tren commit
`ef7a778d4559dbcb7f5ed3de9c88df44392002e9`, nhung row provenance co
`git_dirty=true` vi state/log/output chua duoc freeze. Khong dung cac row do
lam bang chung final ve reproducibility.

Truoc full campaign, runner da duoc sua de:

```text
- chup git/environment fingerprint mot lan dau phien
- loai campaign output khoi dirty signal cua provenance
- van ghi git_dirty_raw va git_status_raw de minh bach
- dung neu git_status_relevant con bat ky thay doi code/config nao
```

Sau commit freeze, phai chay mot diem smoke rieng bang `--limit 1` va xac minh
`env.git_dirty == false` truoc khi bam full.

## Full Campaign Closure

Ngay ghi: 2026-08-05

Full campaign ket thuc hop le sau resume bang watchdog:

```text
n_done              : 609/609
n_rows              : 609
failed_rows         : 0
retry               : 4/609 = 0.66%
gate_fail           : 0
socket_drop_rows    : 0
foreign_rows        : 0
max_abs_rate_error  : 5.635101754253302e-05
timeout_history     : 0
```

Hai commit xuat hien trong provenance:

```text
65f15ec0  freeze campaign start
c4a0704b  add campaign point watchdog
```

Diff chi nam o runner/wrapper watchdog va test; `measurements/l6_campaign.py`,
`measurements/load_gen.py`, `measurements/owd_probe.py`, `mininet/`, va
`twin/` khong doi giua hai commit. A/B sentinel theo commit:

```text
65f15ec0  n=13  mean=10.865892  sd_pop=0.011970
c4a0704b  n= 6  mean=10.872600  sd_pop=0.017931
diff = +0.006708 ms, se = 0.008038, z = +0.83
```

Ket luan: watchdog la operational robustness, khong doi measurement semantics.
Chi tiet va update `SENTINEL_REF` duoc ghi o
`docs/phase-20R/00e-amendment-4.md`.

Sentinel so voi Phase L that:

```text
Phase L  : n=23 mean=10.874913 sd_sample=0.012231
Phase 20R: n=19 mean=10.868010 sd_sample=0.014864
diff=-0.006903 ms, se=0.004258 ms, z=-1.62
```

`SENTINEL_REF` cu `(10.751, 0.212)` la hang so pilot qua rong; no khong lam
hong Phase 20R, nhung da duoc cap nhat cho cac phase sau.

## Truth Table Post-Build Check

Build artifact sau full campaign:

```text
truth rows=176 field=q_mean_ms -> results/phase-20R/truth_table.parquet
continuity 8/8 pass -> results/phase-20R/continuity_check.json
sentinel n=19 -> results/phase-20R/sentinel_control.json
```

`truth_table` chi giu dung mien rho Phase 20R da ky: 58 muc thua ke tu Phase L
va 118 muc moi do o Phase 20R. `n_seed min = 5` va metadata
`truth_field = q_mean_ms` deu co mat.

Kiem noi suy tuyen tinh theo nguong `0.0465 ms`:

```text
cbr      bw=4 q=10  0.0082 ms
cbr      bw=6 q=13  0.0080 ms
cbr      bw=8 q=18  0.0099 ms
h2       bw=4 q=10  0.1527 ms  VUOT
h2       bw=6 q=13  0.1221 ms  VUOT
h2       bw=8 q=18  0.0589 ms  VUOT
poisson  bw=4 q=10  0.2023 ms  VUOT
poisson  bw=6 q=13  0.3016 ms  VUOT
poisson  bw=8 q=18  0.2463 ms  VUOT
```

Check tren la diagnostic ad-hoc sai thu tuc: no lay `max`, do tren nhip `2h`,
va khong tru nhieu do. Amendment 5 thay the ket luan nay.

Check dung dung RMS, tru nhieu theo phuong sai tu `se_mean_ms`, va chia 4 de
quy ve nhip `h`:

```text
cbr|4|10        e_true=0.0012 ms  OK
cbr|6|13        e_true=0.0010 ms  OK
cbr|8|18        e_true=0.0016 ms  OK
h2|4|10         e_true=0.0000 ms  OK
h2|6|13         e_true=0.0000 ms  OK
h2|8|18         e_true=0.0000 ms  OK
poisson|4|10    e_true=0.0000 ms  OK
poisson|6|13    e_true=0.0000 ms  OK
poisson|8|18    e_true=0.0100 ms  OK
```

Ket luan cap nhat: campaign measurement PASS va ngan sach noi suy DAT. Khong
do bu, khong doi interpolator.

## Frozen Residual Field For 20R.5

Nhieu dong bang trong bang tra, tinh bang `se_mean_ms` sau khi trung binh 5
seed:

```text
           mean     max
mode
cbr      0.0025  0.0070
h2       0.0843  0.1903
poisson  0.0553  0.1767
```

Du doan 20R.3 gia dinh bien do truong du `0.27 ms` cho mot seed. Bang tra
thuc te thap hon gia dinh khoang 2-4 lan, nen D1 `err(z=0) in [0.000, 0.10]`
van kha bac nhung ky vong nam o dau thap cua khoang. Khong sua
`02-prediction.md`.

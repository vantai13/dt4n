# Phase 20R.4 -- Campaign Grid

Ngay ky: 2026-08-04
Commit prereg prediction: b3d11a7c1bb1455fc7a77f9cea893db3776a378d

File nay chot luoi do Mininet truoc khi chay chien dich 20R.4.

## Nguyen Tac

- Ground truth la bang tra tua tinh, khong phai trace dong.
- Khong luong tu hoa quy dao `rho(t)`; Lesson 20R.5 se noi suy bang do that.
- Buoc luoi duoc chon bang ngan sach sai so noi suy <= 10% san nhieu.
- `cbr` dung `h = 0.05`; `poisson`/`h2` dung `h = 0.02`.
- Moi muc rho moi chay 5 seed: `21, 22, 23, 24, 25`.
- Thu tu full campaign xao tron bang seed co dinh `20260804`.
- Sentinel giu nguyen Phase L: `h2|bw=6|q=13|rho=0.90|seed=999`, moi 30 diem.

## Bang Luoi

```text
mode     bw q   domain_used       h      levels  new
cbr        4 10 [0.600, 0.950]   0.05       8    2
cbr        6 13 [0.500, 0.950]   0.05      10    3
cbr        8 18 [0.500, 0.850]   0.05       8    3
h2         4 10 [0.600, 1.040]   0.02      23   16
h2         6 13 [0.500, 1.040]   0.02      28   20
h2         8 18 [0.500, 0.960]   0.02      24   19
poisson    4 10 [0.600, 1.040]   0.02      23   16
poisson    6 13 [0.500, 1.040]   0.02      28   20
poisson    8 18 [0.500, 0.960]   0.02      24   19
```

Tong muc moi: `118`; full regular runs: `590`; sentinel: `19`; tong: `609`.

Ghi chu: cbr bi cat tai reliable ceiling `rho <= 0.95`; so muc moi van
giu dung ngan sach 118 muc / 590 run.

## Stages

```text
smoke       10 diem -> results/phase-20R/smoke_state.json
continuity   8 diem -> results/phase-20R/continuity_state.json
full       609 diem -> results/phase-20R/campaign_state.json
```

## Gate Chay Song

```text
socket_drops == 0
n_foreign == 0
abs(rate_ratio - 1) <= 1e-4
abs(rho_actual - rho) <= 0.002
n_late_ratio <= 0.001
max_late_ms <= 50
se_batch_ms va se_naive_ms deu co mat
probe_pps == 20.0
```

## Bit Chot

```text
full_plan_digest = ae9c409ea2956cae0eaf6e9bf1776f32783ac83be1b1cae0fa937c16fe60daf1
smoke_plan_digest = 5c3bdafe6a83774570ec2caecf536ab3baf7cbdf80cbbc53f17c3f6e3b1535ed
continuity_plan_digest = a6887709f2e2ed284373dc94cefe4baef6adf181075e6d0dd973ed381fec8d8d
calibration_sha256 = 0387d300dbdd039c004a7fc89d062a0e9219968be8ad0cfeac65e53cf34826db
```

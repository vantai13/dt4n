# AMENDMENT 6 - Phase 20 Pre-Registration

Ngay: 2026-07-27
Trang thai: TRUOC Lesson 20.3. Thuoc chinh `decision_error.py` da chay tren
trace offered da dong bang.

San khau da dong bang tai `phase-20-stage-frozen`; amendment nay chi chot
thuoc do, doi chung, bootstrap, va P3' truoc khi so sanh sim-vs-real.

## A6.1 Jensen: Gate Dung Ban Van Hanh

AoI khong co dinh o `E[AoI] = 0.298 s`; he that di theo rang cua:

```text
age(t) = ((t - d_sync) mod T) + d_sync
T = 0.5 s, d_sync = 0.051 s
```

`decision_error.py` bao cao ca hai:

```text
err(z* = 0.298 s)
E[err(AoI)] tren rang cua van hanh
```

Gate G1/G2 dung ban van hanh. Doi nay khong tu phuc vu: voi duong cong lom,
G1 co the de hon, nhung G2 co the kho hon. Tren trace offered da dong bang,
hai so gan nhau:

```text
err(0.298) = 0.17555
err_op     = 0.17286
jensen_gap_err = +0.00269

d_sla(0.298) = 0.07260
d_sla_op     = 0.07287
jensen_gap_d_sla = -0.00026
```

Sai khac cua `d_sla` rat nho; gate van dung ban van hanh.

## A6.2 Common Random Numbers

Moi `z` duoc danh gia tren cung mot cua so trace, cat mot lan theo `z_max`.
Voi `z_max = 4.0 s`, cua so chung bat dau tai `t = 4.0 s`, `n_eval = 143600`.

Cam ba cach pha CRN:

```text
lay mau z ngau nhien
bootstrap rieng tung z
cat cua so rieng cho tung z
```

Hinh dang `err(z)` la kiem dinh chinh cua co che. Tren trace offered,
Spearman:

```text
rho_s = 1.0
p_one_sided = 2.7557e-06
```

## A6.3 Paired Moving Block Bootstrap

Bootstrap dung block lien tiep va giu cung bo block cho moi `z`.

Chot truoc:

```text
tau_core = 2.87 s
dt = 0.010 s
b = round(5 * tau_core / dt) = 1435 mau = 14.35 s
n_blocks = 100
n_boot = 2000
```

Dung tau lon nhat trong link loi, khong dung tau toan cuc cua link bien. Link
bien gan nhu tinh va khong la nguon chinh cua lat quyet dinh; neu dung
`vD = 32 s` thi chi con 9 block va CI vo dung.

## A6.4 P3 Cu Bi Bo, P3' Duoc Dung

P3 cu:

```text
>= 70% loi co r_jump(s) < 0.01
```

Bi bo vi thieu ti le nen va chi nhin hien tai. Thay bang:

```text
crossed(t,z) = co link nao ma rho(t) va rho(t-z)
               nam khac phia mot nguong trong J = {0.9250, 0.9325}

P3' PASS neu:
  risk_ratio = P(sai | crossed) / P(sai | not crossed) >= 3.0
  P(sai | not crossed) <= 0.10
```

Ket qua operational tren trace offered:

```text
P(crossed)             = 0.4134
P(crossed | sai)       = 0.8630
P(sai | crossed)       = 0.3608
P(sai | not crossed)   = 0.0404
risk_ratio             = 8.94
share_errors_crossed   = 0.8630
```

P3' PASS rong. `r_jump` base-rate checks van duoc ghi de tranh base-rate
fallacy, nhung khong con la gate.

## A6.5 Doi Chung Ben Trong

`decision_error.py` chay NC1-NC4 trong cung file output:

```text
NC1 z=0                 -> err = 0.000000
NC2 tiny noise 1e-12    -> err = 0.000000
NC3 block permutation   -> err ~ independent stale twin, lech < 0.05
NC4 random uniform twin -> err ~ 1 - 1/K
```

Chay `--nc-only` tren trace offered:

```text
NC all_pass = True
NC1 err = 0.000000
NC2 err = 0.000000
NC3 err = 0.610885
NC4 err = 0.749417
```

## A6.6 Ket Qua Offered Trace

Trace:

```text
results/phase-20/rho_offered_long.csv
warmup_frac = 0.2
dt = 0.010 s
```

SLA tu dong hoi tu:

```text
w_loss = 1451.377
T_delay = 14.514 ms
T_loss = 0.010
optimal_violation = 0.1500
tie_rate = 0.0000
```

Ket qua 3 bootstrap/control seeds:

```text
seed 100: err_op = 0.1729 CI [0.1557, 0.1885]
          d_sla_op = 0.0729 CI [0.0650, 0.0818]
          risk_ratio = 8.94, pass_without_G6 = True

seed 101: err_op = 0.1729 CI [0.1564, 0.1889]
          d_sla_op = 0.0729 CI [0.0650, 0.0816]
          risk_ratio = 8.94, pass_without_G6 = True

seed 102: err_op = 0.1729 CI [0.1556, 0.1891]
          d_sla_op = 0.0729 CI [0.0648, 0.0818]
          risk_ratio = 8.94, pass_without_G6 = True
```

Gate status truoc Lesson 20.3:

```text
G1 operational err CI nam trong [0.05, 0.40]       PASS
G2 operational d_sla lower >= 0.03                 PASS
G3 Spearman positive                               PASS
G4 NC1-NC4                                         PASS
G5 P3' risk ratio                                  PASS
G6 sim-vs-real                                     pending Lesson 20.3
```

## A6.7 Output

Ket qua chinh:

```text
results/phase-20/decision_error_offered.json
results/phase-20/decision_error_offered_nc.json
```

Tag sau khi commit:

```text
phase-20-measured
```

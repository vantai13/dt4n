# AMENDMENT 5 - Phase 20 Pre-Registration

Ngay: 2026-07-27
Git tag: `phase-20-stage-frozen`
Trang thai: SAN KHAU DONG BANG. Dat C1-C7 + V1 + T1-T4.

Tu day khong sua san khau nua. Moi thay doi sau diem nay phai co amendment
rieng, ghi ro da thay so nao truoc khi sua.

## A5.1 Dac Trung San Khau - Chot

Trace chot: `results/phase-20/rho_offered_long.csv`, seed `0`, 1440 s sau
warm-up.

| link | mu | sigma | tau(s) | u_min(s) | chu ky | dung |
|---|---:|---:|---:|---:|---:|---|
| uA | 0.7988 | 0.0319 | 22.87 | 18.20 | 63 | OK |
| uB | 0.8160 | 0.0276 | 21.70 | 24.82 | 66 | OK |
| ac | 0.9188 | 0.1070 | 2.869 | 2.51 | 502 | OK |
| ad | 0.9300 | 0.0959 | 3.958 | 3.81 | 364 | OK |
| bc | 0.9099 | 0.0956 | 2.441 | 2.50 | 590 | OK |
| bd | 0.9250 | 0.0968 | 2.605 | 2.52 | 553 | OK |
| vC | 0.7984 | 0.0279 | 17.38 | 18.20 | 83 | OK |
| vD | 0.8365 | 0.0345 | 32.00 | 25.21 | 45 | OK |

Prediction check dat 16/16:

```text
sigma = sqrt(rho * r_f / C): 8/8 trong |log2| <= 0.20
tau   ~= 1.06 * S_min/r_f : 8/8 trong |log2| <= 0.28
```

Trace 1440 s xac nhan chan doan `vD`: lan 240 s chi co 19 chu ky tuong quan
nen `tau_vD = 12.58 s` va truot C5; lan 1440 s co 45 chu ky tuong quan nen
`tau_vD = 32.00 s` va dat C5. Van de la thieu du lieu, khong phai sai mo hinh.

## A5.2 Sua Phat Bieu Sai O Lesson 20.1d

Phat bieu cu sai:

```text
ACF co than mu + duoi luy thua.
```

Phat bieu dung:

```text
M/G/inf voi D ~ Pareto(kappa, u_min) cho ACF hai doan:

s <= u_min : ACF(s) = ((kappa - 1) * (1 - s/u_min) + 1) / kappa
s >= u_min : ACF(s) = (1/kappa) * (s/u_min) ** (1-kappa)
```

Doan tuyen tinh tren mot khoang hep trong giong ham mu, nen phep khop mot
doan co the goi no la `EXP`. Su lat `EXP`/`POWER` la model
misspecification cua thuoc, khong phai mot hien tuong moi cua he thong.

He qua: cac `kappa_hat = 1.40/1.45` tung bao cao o Lesson 20.1d la rac va
khong duoc trich dan.

## A5.3 T4 - Bo Phan Loai Decay Co Guard

`measurements/measure_tau.py` tu nay dung hai lop bao ve:

```text
L1. R2 floor:
    max(R2_exp, R2_power) >= 0.80
    neu khong -> NO_FIT, khong bao cao kappa_hat

L2. residual-ratio:
    so sanh phan du 1-R2, khong so sanh R2 truc tiep
    chi tuyen bo thang neu residual_thang < (1/3) * residual_thua
    dung tolerance so hoc 1e-3 quanh nguong 1/3 de tranh flip do lam tron
    neu khong -> AMBIGUOUS, khong bao cao kappa_hat
```

Ap lai trace 1440 s:

```text
uA  6s: undetermined       60s: EXP
uB  6s: undetermined       60s: EXP
ac  6s: EXP                60s: EXP
ad  6s: EXP                60s: NO_FIT
bc  6s: POWER k=2.45       60s: POWER k=2.22
bd  6s: AMBIGUOUS          60s: NO_FIT
vC  6s: undetermined       60s: POWER k=2.42
vD  6s: undetermined       60s: EXP
```

Bo loc tu dong loai dung hai gia tri rac (`ad@60s`, `bd@60s`) va giu lai cac
gia tri `kappa_hat` hop le. Khi viet paper, nen khop truc tiep dang ACF hai
doan cua ly thuyet bang hai tham so `(u_min, kappa)` thay vi chon cua so cho
fit mot doan.

## A5.4 Diem Van Hanh - Con So Chinh

```text
z* = A = E[AoI] = 0.298 s
z* / u_min_loi = 0.08 - 0.12
ACF(z*) ly thuyet = 0.928 - 0.953
```

Tai diem van hanh, uoc luong tai cua twin con tuong quan khoang 93% voi su
that, nhung du doan ti le sai quyet dinh la 19-21%.

Day la minh hoa dinh luong cho luan diem trung tam: do chinh xac muc gia tri
khong chuyen truc tiep thanh do chinh xac muc quyet dinh. `tau` duoc bao cao
nhu dac trung cuc bo quanh diem van hanh, nhung khong duoc dung lam rang buoc
thiet ke de ngoai suy xa.

## A5.5 Du Doan Gate 20

Day la du doan de uoc luong rui ro, khong phai ket qua confirmatory.

Hai kich ban bao tai `z* = 0.298 s`:

```text
w_loss hoi tu: 1445-1451
T_delay: 14.45-14.51 ms
toi uu vi pham SLA: 15.0%
err: 0.194-0.211
CI95(err): [0.163, 0.243] nam trong [0.05, 0.40]
Delta_sla_lower: 0.059-0.066 >= 0.03
err tang don dieu: 0.000 -> 0.549
err(z=0): 0.000000
tie: 0.0000%
K_eff: 3.20-3.26 / 4
```

Can theo doi G2 trong phep do that vi bien an toan hep lai khi `T_delay` hoi
tu ve khoang 14.45 ms thay vi 15.0 ms.

## A5.6 Nhieu Telemetry Xuong Hang

`estimator_compare` tren trace 1440 s:

```text
link bien: noise_var_share = 0.05-0.11
link loi : noise_var_share = 0.00
```

Lan 240 s tung bao `0.51/0.63` cho `uA/uB` chu yeu vi `sigma_offered` bi uoc
luong thap tren trace ngan co it chu ky tuong quan. Phase 20 van dung
`rho_offered` cho ca twin lan oracle de co lap bien do cu; nhieu telemetry
chi con la mot dong future work.

## A5.7 Dong Bang

Moi tham so o A5.1 la co dinh tu day. Pilot dung seed `0`. Phep do chinh dung
seed moi `100, 101, 102`.

Sang Lesson 20.2: xay `decision_error.py` tren trace that, voi negative
controls, common random numbers, block bootstrap, va phan ra loi theo
`r_jump`.

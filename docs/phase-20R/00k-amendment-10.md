# AMENDMENT 10 -- H9: tach bien giua do cu va hinh hoc che do

Ngay: 2026-08-06
Trang thai: ky truoc khi chay formal script `measurements.h9_separability`.
Ghi chu: phat hien H9 la hoi cuu tu cac parquet da co; khong duoc xem la
bang chung tien nghiem moi cho cung tap du lieu. Gia tri chinh cua amendment
nay la khoa tieu chi, cach fit, va cach bao cao truoc khi sang Mininet G6.

## Phat Hien Hoi Cuu

Gop ba tap thiet ke doc lap tai `z = 0.55, tau = 1.0`:

```text
sigma_fixed  : decision_error_unimodal + margin_cv_unimodal
operational  : decision_error_by_age_by_regime + margin_cv_operational
a = 0.2      : sensitivity_a02 + margin_cv_a02
```

Bien gop:

```text
R = sd(cost_margin) / mean(cost_margin)
cost_margin = cost duong nhi - cost duong tot nhat, tinh tu twin
```

Dang dong duoc kiem:

```text
err = c(z/tau) . Phi(-k/R)
```

Trong cach doc nay, `Phi(-k/R)` la xac suat khe cost dao dong ve 0; `k`
la do xa hinh hoc theo don vi do lech chuan cua margin; `c(z/tau)` la thua
so do cu.

## Gia Thuyet H9

H9a -- tach bien:

```text
err(z, che_do) = c(z/tau) . Phi(-k/R)
k khong doi theo z/tau.
```

Kiem tren cac `z_key = {0.050, 0.100, 0.200, 0.300, 0.550}` cua ba tap
`sigma_fixed`, `operational`, `a02`. PASS neu do lech chuan cua `k` qua cac
muc `z/tau` nho hon `0.15`.

Kiem bo sung tren tau sweep operational:

```text
tau in {0.2, 1.0, 5.0}
z/tau in {0.10, 0.30, 0.55, 1.00}
```

Dung cung nguong `sd(k) < 0.15`.

H9b -- thua so do cu tang va bao hoa:

```text
Spearman(z/tau, c) > 0.9
```

H9c -- nguong zero:

```text
Moi o co R < 0.30 phai co err_total = 0.0.
```

Quy tac: dung gia tri raw trong parquet, khong lam tron `R`. Mot o duy nhat
co `R < 0.30` va `err_total > 0` la bac bo H9c. Neu fail sat bien, bao cao
la fail sat bien, khong doi nguong hau nghiem.

## H8b CI Review

Dung `results/phase-20R/margin_cv_ci.json`. Vi JSON hien luu CI rieng cho R
tung tau, formal script se dung khoang bao thu:

```text
signed_delta_CI ~= [lo_tau - hi_tau1, hi_tau - lo_tau1]
```

Day khong phai paired bootstrap cho delta, nen chi dung de canh bao. Neu
khoang bao thu cham 0.02, viet `H8b PASS (bien hep, CI cham nguong)`.

## Khong Sua

H3/G4 van FAIL. H6, H7, H8 giu nguyen. H9 la gia thuyet co che moi, khong
thay the gate G1-G7. Neu H9 bi bac bo, bao cao ket qua am va giu hai luat
H6/H8 rieng re.

Lenh formal:

```bash
python3 -m measurements.h9_separability \
  --out results/phase-20R/h9_separability.json
```

## Ket Qua Formal Tren Artifact Da Co

Chay sau commit prereg `cfad852`.

```text
pooled n = 30
Spearman(R, err_total) = 0.994651
```

So sanh dang ham tai `z = 0.55, tau = 1.0`:

```text
threshold linear      MAE = 0.014825   RMSE = 0.021605
Phi(-k/R)             MAE = 0.051513   RMSE = 0.066018
c * Phi(-k/R)         MAE = 0.013371   RMSE = 0.019946
```

Fit hai tham so:

```text
k = 1.159900
c = 4.760398
```

Theo tap:

```text
set           n   MAE       RMSE      k         c
a02           8   0.008110  0.013339  1.233800  5.526398
operational   8   0.022962  0.027396  1.055700  3.844557
sigma_fixed  14   0.006386  0.008748  1.281900  6.663054
```

H9a/H9b:

```text
tau=1, ba tap, theo z:
  sd(k) = 0.020053 < 0.15        PASS
  Spearman(z/tau, c) = 1.000000  PASS

tau operational, theo tau va z/tau:
  sd(k) = 0.015017 < 0.15        PASS
  Spearman(z/tau, c) = 0.971625  PASS
```

H9c strict `R < 0.30 -> err_total = 0.0`: FAIL sat bien, vi dung gia tri raw
khong lam tron:

```text
set           mode  rho_bar  R         z/tau  err_total
sigma_fixed   h2    0.925    0.293424  0.55   0.001137
operational   h2    0.960    0.299915  0.55   0.001675
```

Tren tau sweep operational cung co cac diem fail sat bien tai `h2, rho_bar =
0.960`, `R` khoang `0.295-0.299`, `err_total` khoang `0.0012-0.0021`.

Ket luan: H9a/H9b ung ho manh tich `c(z/tau) * Phi(-k/R)`, nhung H9c o
nguong raw `0.30` bi bac bo. Neu can phat bieu nguong zero, phai dang ky lai
nguong thap hon; khong doi nguong trong Phase 20R.6.

H8b CI review:

```text
worst point delta: tau=5, poisson rho_bar=0.85, |Delta R| = 0.018882
conservative CI signed range = [-0.025670, +0.062551]
```

Do CI bao thu cham/vuot `0.02`, H8b phai viet:

```text
PASS theo point estimate; bien hep, CI cham nguong.
```

Artifacts:

```text
results/phase-20R/h9_separability.json
docs/phase-20R/figures/decision_error_h9_separability.png
```

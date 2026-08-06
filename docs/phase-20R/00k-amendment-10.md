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

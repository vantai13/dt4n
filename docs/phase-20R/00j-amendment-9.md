# AMENDMENT 9 -- Phase 20R.5: H8 luat gop err = g(R)

Ngay: 2026-08-06
Trang thai: KY TRUOC khi chay phep kiem tau cua H8.

## Phat Hien Hoi Cuu

Tu lat cat constant-sigma trong Amendment 8, co mot bien gop hai family:

```text
R = sd(cost_margin) / mean(cost_margin)
cost_margin = khe cost giua duong tot nhat va duong nhi theo twin
```

`R` tinh hoan toan tu twin va phan phoi rho, khong can measured truth.

Ket qua hoi cuu:

```text
Tren 14 o constant-sigma (poisson+h2, 7 rho_bar):
  Spearman(R, err) ~= +0.9945
  err ~ 0 khi R < 0.35

Tren 8 o sigma-van-hanh:
  Spearman(R, err) ~= +1.0000
  MAE du doan diem bang g(R) ~= 0.054
```

R la chi so thu hang/manh-yeu cua regime, khong phai cong thuc diem chinh xac.

## Gia Thuyet Moi H8

```text
H8a Voi tau co dinh, err phu thuoc che do chu yeu qua R.
     Kiem tren tap moi: Spearman(R, err) > 0.9.

H8b R khong phu thuoc tau, vi phan phoi dung yen cua AR(1) duoc giu theo sigma.
     Do do luat day du la err = g(R, z/tau).
     Kiem: R(tau=0.2), R(tau=1.0), R(tau=5.0) khop nhau trong 0.02 tuyet doi.

H8c R la du doan thu hang, khong phai du doan diem.
     Du bao: MAE diem cua g(R) tren tap moi se > 0.03.
```

H8 la gia thuyet moi, khong thay the H3/G4. H3/G4 van FAIL neu thong ke da
tien dang ky khong dat.

## Phep Kiem Tien Nghiem

Tap kiem la quet tau da co, chua dung de rut luat R:

```text
results/phase-20R/decision_error_tau0.2.parquet
results/phase-20R/decision_error_tau1.0.parquet
results/phase-20R/decision_error_tau5.0.parquet
```

Lenh tinh R:

```bash
python3 -m measurements.decision_error_v2 --compute-margin-cv \
  --tau 0.2,1.0,5.0 \
  --sigma-override 0.0096 \
  --n 200000 \
  --seeds 101,102,103 \
  --out results/phase-20R/margin_cv_by_tau.parquet
```

Lenh bo sung de ve hinh R-vs-err:

```bash
python3 -m measurements.decision_error_v2 --compute-margin-cv \
  --tau 1.0 \
  --sigma-override 0.0096 \
  --rho-bar-extra 0.65,0.78,0.88 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/margin_cv_unimodal.parquet

python3 -m measurements.decision_error_v2 --compute-margin-cv \
  --tau 1.0 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/margin_cv_operational.parquet
```

## Khong Sua

Khong sua `02-prediction.md`, H3, H7, hay gate G1-G7. H8 la ket qua co che
bo sung neu phep kiem tau dat.


# AMENDMENT 7 -- Phase 20R.5: H3 bi bac bo, phat hien confound sigma-rho_bar

Ngay: 2026-08-06

## Van De

Ket qua operational calibration tai `z = 0.55` cho thay H3/G4 khong sach:

```text
poisson err_total: 0.1879, 0.4301, 0.3756, 0.2650
h2      err_total: 0.3898, 0.3340, 0.1047, 0.0017
rho_bar          : 0.700, 0.850, 0.925, 0.960
```

Neu doc truc tiep theo `rho_bar`, `poisson` khong don dieu va `h2` giam manh.
Nhung calibration Q8 khong giu nhieu dong nhat:

```text
rho_bar:   0.700   0.850   0.925   0.960
sigma_rho: 0.0462  0.0480  0.0218  0.0096
```

Do do, trend theo `rho_bar` bi confound voi bien do dao dong `sigma_rho`.
Khong duoc ket luan co che cua H3/G4 tren operational calibration cho den khi
tach confound nay.

## Thi Nghiem Chot

Chay them fixed-z grid voi cung `sigma_rho = 0.0096` cho moi gate cell:

```bash
python3 -m measurements.decision_error_v2 \
  --run-fixed \
  --sigma-override 0.0096 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_constant_sigma.parquet \
  2>&1 | tee logs/20r5_03_constant_sigma.log
```

Prediction truoc khi chay: neu confound `sigma_rho` la nguyen nhan chinh,
`poisson` se tang don dieu theo `rho_bar` trong grid constant-sigma. `h2` co
the tang nhe hoac gan phang vi do doc h2 gan hang so.

## Phat Bieu Lai Gia Thuyet

```text
H3'  err tang don dieu theo rho_bar KHI GIU sigma co dinh.
H3'' Trong van hanh thuc (sigma bi rang buoc kha thi), err KHONG don dieu
     theo rho_bar; no dat cuc dai o rho_bar trung binh.
```

Ca hai deu kha bac va se doc tu
`results/phase-20R/decision_error_constant_sigma.parquet`.

## Gate

`20R-G4` doc tren H3' (sigma co dinh). Ket qua confound operational duoc bao
cao nhu mot phat hien rieng, khong phai ly do de lam ngo H3.

## Dieu Kien Dien Giai

Ket qua constant-sigma la deconfounding diagnostic. Artifact operational
calibration chinh van duoc bao cao rieng trong sawtooth point va fixed-z grid
da ky.

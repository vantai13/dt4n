# Phase 20R Erratum -- decision-error scale labels

Ngay ky: 2026-08-12

Day la erratum bo sung, khong sua nguoc cac file Phase 20R da ky.

## Noi dung can lam ro

Cac cot sau trong artifact Phase 20R:

```text
results/phase-20R/decision_error_by_age_by_regime.parquet
results/phase-20R/decision_error_constant_sigma.parquet

rms_e_model
rms_e_stale
cov_e
```

duoc tinh tren muc DUONG, kenh DELAY. Chung khong phai muc BIEN va khong phai
thang COST.

Nguon code: `measurements/decision_error_v2.py::_fixed_metric_series` dung
`d_true` va `d_fresh`:

```text
e_model = d_true[current] - d_fresh[current]
stale   = d_fresh[current] - d_fresh[twin_rows]
```

## Vi sao can erratum

Phase 21R chung nhan dai luong khac:

```text
level   = margin
channel = cost
```

Neu doc cot Phase 20R roi dien vao decomposition Phase 21R, se tao loi khop
thang do. Loi nay khong lam test do, nhung doi nghia khoa hoc cua con so.

Tai `poisson@0.925`, `z=0.550`:

| Level/channel | rms_e_model | rms_e_stale | corr |
|---|---:|---:|---:|
| path/delay | 0.305538 | 0.727837 | -0.081854 |
| path/cost | 2.502552 | 12.650174 | -0.149085 |
| margin/cost | 2.139427 | 16.814918 | -0.411349 |

Khuyech dai tu `path/delay` sang `path/cost`:

```text
rms_e_model: 0.305538 -> 2.502552   = 8.19x
rms_e_stale: 0.727837 -> 12.650174  = 17.38x
```

Nguyen nhan: `w_loss` trong cell chinh khuech dai kenh loss, va dao ham cua
loss theo rho doc gan vung tai cao. Vi vay thang cost nhay hon nhieu so voi
thang delay.

## Quy tac tu nay

Moi so decomposition phai kem ba nhan:

```text
1. THANG   : delay / cost / chuan hoa
2. MUC     : per-link / per-path / margin
3. TAP HANG: cua so chung nao, z nao, seed nao
```

Trong Phase 21R, khi ghi `z_cross`, viet ro dang noi `z_cross(level, channel)`.

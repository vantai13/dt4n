# LESSON 22.7 -- aoi_profiles.py

Ngay: 2026-08-13

Trang thai: da chay tren du lieu Phase 22 v3 that. Ket qua chinh la mot null
result sach cho cac ho so poll thuc te: gia dinh AoI dong nhat cua 21R an toan
trong mien `sd(d) << tau`.

## 1. San pham

| File | Vai tro |
|---|---|
| `cert/aoi_profiles.py` | dung lai physics v3, can giua offset, build U0/U1/U2/PC4 |
| `test/test_phase22_aoi.py` | 11 tests khoa Jensen, null result, PC4, P10, L13 |
| `results/phase-22/aoi_profiles_*.json` | report cho `poisson@0.925`, `poisson@0.850`, `h2@0.700` |

Lenh chinh:

```text
/tmp/dt4n-venv/bin/python -m cert.aoi_profiles --mode poisson --rho-bar 0.925 \
  --out results/phase-22/aoi_profiles_poisson_0.925.json
```

## 2. Thiet ke

So sanh U0/U1/U2 chi co nghia khi tuoi trung binh khop nhau. Neu chi cong
offset vao tung link, U1 se cu hon U0 trung binh 22.5 ms; do la confounding,
lon hon Jensen gap hang tram lan.

Thuc thi:

```text
old_adj = old + round(mean(offset_steps))
rho_stale[l] = rho[old_adj - offset_l, l]
z_bar = (cur - old_adj + mean(offset_steps)) * dt
```

`z_bar` la tuoi trung binh thuc qua 8 link. Them `mean(offset_steps)` la bat
buoc vi integer shift khong tri tieu duoc mean nua buoc.

## 3. Ly thuyet Jensen

Voi `h(z) = 1 - exp(-z/tau)`:

```text
mean_l h(z_bar + d_l) - h(z_bar)
  ~= 0.5*h''(z_bar)*Var(d)
  = -0.5*exp(-z_bar/tau)*Var(d)/tau^2
```

Do do khe Jensen am va ti le voi `Var(d)/tau^2`.

| profile | z_bar | h(z_bar) | exact gap | second-order | rel rms gap |
|---|---:|---:|---:|---:|---:|
| U1 | 0.077 | 0.074110 | -1.020e-04 | -1.020e-04 | -0.0688% |
| U1 | 0.425 | 0.346230 | -7.200e-05 | -7.200e-05 | -0.0104% |
| U2 | 0.077 | 0.074110 | -7.234e-05 | -7.234e-05 | -0.0488% |
| U2 | 0.425 | 0.346230 | -5.108e-05 | -5.108e-05 | -0.0074% |
| PC4 | 0.077 | 0.074110 | -1.124e-02 | -1.266e-02 | -7.8943% |
| PC4 | 0.425 | 0.346230 | -7.936e-03 | -8.938e-03 | -1.1527% |

U1/U2: exact gap va khai trien bac hai trung nhau den 4 chu so. PC4 lech
khoang 12%, dung nhu mong doi khi offset da qua lon de Taylor bac hai la mo
hinh dinh luong day du.

## 4. O chinh poisson@0.925

### Ho so

| profile | mean ms | sd ms | shift steps | residual mean ms | rows dropped | clipped |
|---|---:|---:|---:|---:|---:|---:|
| U0 | 0.0 | 0.00 | 0 | 0.0 | 500 | 0.00% |
| U1 | 22.5 | 14.79 | 4 | 2.5 | 500 | 1.00% |
| U2 | 12.5 | 12.50 | 2 | 2.5 | 500 | 1.00% |
| PC4 | 62.5 | 165.36 | 12 | 2.5 | 10495 | 1.01% |

Tuoi trung binh khop trong mot buoc lay mau:

```text
U0 0.3025, U1 0.3050, U2 0.3050, PC4 0.3075
```

### Qhat va ratio voi U0

| profile | qhat B0 | qhat B1 | qhat B2 | qhat B3 | ratio vs U0 B0/B1/B2/B3 |
|---|---:|---:|---:|---:|---|
| U0 | 11.5878 | 15.6376 | 19.6503 | 24.3254 | 1.0000, 1.0000, 1.0000, 1.0000 |
| U1 | 11.5442 | 15.6206 | 19.7333 | 24.3567 | 0.9962, 0.9989, 1.0042, 1.0013 |
| U2 | 11.7494 | 15.6339 | 19.6457 | 24.3636 | 1.0139, 0.9998, 0.9998, 1.0016 |
| PC4 | 6.5454 | 12.3150 | 17.1247 | 22.6500 | 0.5649, 0.7875, 0.8715, 0.9311 |

U1/U2: moi lech deu nam trong 1.4%, khong co dau nhat quan. PC4: hieu ung lon,
dung chieu Jensen, va giam dan khi z lon.

### Bootstrap ghep cap

CI 95% cua `qhat(profile)/qhat(U0)`, cung rutt block cho ca bon profile:

| profile | B0 | B1 | B2 | B3 |
|---|---|---|---|---|
| U1 | [0.9866, 1.0072] | [0.9904, 1.0073] | [0.9965, 1.0118] | [0.9953, 1.0075] |
| U2 | [0.9994, 1.0286] | [0.9887, 1.0107] | [0.9886, 1.0097] | [0.9936, 1.0104] |
| PC4 | [0.5527, 0.5781] | [0.7722, 0.8025] | [0.8550, 0.8891] | [0.9163, 0.9451] |

Ket luan o chinh: U1/U2 khong phan biet duoc voi U0 o muc 95%; PC4 loai tru
1.0 o ca bon bin.

## 5. P10: neo phai tinh theo profile

| profile | anchor err | coverage | acc kappa=1 | err\|accept | risk ratio | viol\|accept |
|---|---:|---:|---:|---:|---:|---:|
| U0 | 0.2225 | 0.9087 | 0.2836 | 0.0329 | 0.1480 | 0.1214 |
| U1 | 0.2196 | 0.9083 | 0.2834 | 0.0337 | 0.1535 | 0.1256 |
| U2 | 0.2230 | 0.9058 | 0.2855 | 0.0337 | 0.1512 | 0.1271 |
| PC4 | 0.1923 | 0.9053 | 0.3501 | 0.0276 | 0.1436 | 0.1164 |

Dung nham anchor U0 cho PC4 se tinh:

```text
dung : 0.0276 / 0.1923 = 0.1436
sai  : 0.0276 / 0.2225 = 0.1240
```

Sai 13.6%, nen P10 khong phai hinh thuc.

## 6. L13 moi

| profile | qhat(B3)/qhat(B0) |
|---|---:|
| U0 | 2.0992 |
| U1 | 2.1099 |
| U2 | 2.0736 |
| PC4 | 3.4604 |

Dinh luat ratio tuoi cua Lesson 22.6 giu cho U0/U1/U2, nhung vo o PC4. Dieu
kien ap dung phai viet la `sd(d) << tau`, tuc AoI qua link gan dong nhat tren
thang tu tuong quan cua tai.

## 7. O phu

| cell | gates | U1/U0 B0-B3 | U2/U0 B0-B3 | PC4/U0 B0-B3 | ghi chu |
|---|---:|---|---|---|---|
| poisson@0.925 | 8/8 | 0.9962, 0.9989, 1.0042, 1.0013 | 1.0139, 0.9998, 0.9998, 1.0016 | 0.5649, 0.7875, 0.8715, 0.9311 | headline |
| poisson@0.850 | 8/8 | 0.9999, 0.9941, 0.9977, 0.9972 | 1.0133, 1.0023, 0.9942, 0.9974 | 0.5751, 0.7976, 0.8802, 0.9362 | lap lai null result |
| h2@0.700 | 6/8 | 0.9848, 0.9964, 0.9959, 0.9965 | 0.9929, 1.0023, 0.9933, 1.0015 | 0.6310, 0.8115, 0.8873, 0.9343 | lech nho <2%; CI U1/B0 loai 1 |

`h2@0.700` la pham vi can ghi ro: do lon van nho hon 2%, nhung paired
bootstrap bat duoc U1/B0 thap hon U0. Vi vay ket luan "khong co hieu ung lon"
lap lai; ket luan "khong phan biet thong ke" chi dung sach cho hai o poisson.

## 8. Du doan va P16

Du doan theo chu:

| Du doan | Dai | Do duoc | KQ |
|---|---:|---:|---|
| qhat(U1)/qhat(U0) | 0.95-1.00 | 0.9962 B0, 1.0042 B2 | mixed |
| qhat(U2)/qhat(U0) | 0.96-1.00 | 1.0139 B0 | miss |
| acceptance(U1) >= acceptance(U0) | TRUE | 0.2834 < 0.2836 | miss |

Chuyen bai hoc thanh P16: khong du doan dau khi hieu ung du kien nam duoi san
nhieu. Du doan dung le ra la:

```text
|qhat(U1)/qhat(U0) - 1| < 2%
|qhat(U2)/qhat(U0) - 1| < 2%
PC4/U0 < 0.95 va CI loai 1
```

Du doan ve can nay dung tren o chinh.

## 9. Tests

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase22_aoi.py -q
11 passed in 0.32s

/tmp/dt4n-venv/bin/python -m pytest -q test/test_phase22_simscore.py test/test_phase22_calibv3.py test/test_phase22_conformalsim.py test/test_phase22_selective.py test/test_phase22_matrix.py test/test_phase22_tau.py test/test_phase22_aoi.py
92 passed in 127.31s (0:02:07)

/tmp/dt4n-venv/bin/python -m pytest -q
729 passed, 4 skipped in 311.84s (0:05:11)
```

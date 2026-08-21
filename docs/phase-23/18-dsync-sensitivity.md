# Lesson 23.8[A] -- do nhay theo d_sync

Ngay chay: 2026-08-21
Trang thai: **SENSITIVITY_ONLY -- khong dong P23-A.**

## Ket luan chinh

Bracket Poisson `(0.900, 0.925)` **khong ben** tren dai `d_sync` da khoa.
Tai `poisson@0.900`, `lift-swing` doi dau tu `-0.024447` o 51 ms sang
`+0.002810` o 175 ms; `Delta_F2` doi tu `+0.005378` sang `-0.000618`.
Tai `poisson@0.925`, hai dau tuong ung van giu nguyen tren toan dai.

Vi M-62 va M-63 MISS o Tang 1, stop rule mo Tang 2 dung mot lan va sau do
dung. Ket qua di theo **Nhanh 2 da viet truoc**: P23-A la rui ro chi mang co
bang chung; cac ket luan Lesson 23.15/23.16 phai duoc doc la
`conditional on d_sync = 51 ms` cho den khi do lai tren vong sync DT cua
`topology_v7`.

## 1. Range-setting micro-pilot

Pilot khong doc certificate outcome. No do 200 cycle sau 20 warm-up cycle,
moi cycle gom 20 Thing gia di qua snapshot -> PATCH -> Ditto ack -> GET va
kiem token read-back.

| Dai luong | Ket qua |
|---|---:|
| cycle p05 | 173.449 ms |
| cycle p50 | 201.793 ms |
| cycle p95 | 260.590 ms |
| cycle mean | 207.728 ms |
| cycle min / max | 168.093 / 331.235 ms |
| push p50 | 117.335 ms |
| read p50 | 83.287 ms |
| HTTP va token controls | 100% PASS |

Vi pilot nam ngoai dai de xuat 30--90 ms, amendment khoa lai:

```text
D = {0.051, 0.175, 0.205, 0.230, 0.260} s
```

51 ms van duoc giu lam negative control ke thua.

## 2. Ket qua Tang 1

| cell | d_sync (s) | err_neo | lift-swing | Delta F2 |
|---|---:|---:|---:|---:|
| poisson@0.900 | 0.051 | 0.229301 | -0.024447 | +0.005378 |
| poisson@0.900 | 0.175 | 0.269443 | +0.002810 | -0.000618 |
| poisson@0.900 | 0.205 | 0.277588 | +0.010975 | -0.002415 |
| poisson@0.900 | 0.230 | 0.284026 | +0.016295 | -0.003585 |
| poisson@0.900 | 0.260 | 0.291487 | +0.022671 | -0.004988 |
| poisson@0.925 | 0.051 | 0.222399 | +0.058495 | -0.012869 |
| poisson@0.925 | 0.175 | 0.260081 | +0.079026 | -0.017386 |
| poisson@0.925 | 0.205 | 0.268022 | +0.084321 | -0.018551 |
| poisson@0.925 | 0.230 | 0.274150 | +0.089233 | -0.019631 |
| poisson@0.925 | 0.260 | 0.281306 | +0.094384 | -0.020764 |

`poisson@0.900` MISS M-62/M-63; `poisson@0.925` HIT. Vi mot dau bracket
doi dau, menh de bracket cu khong con bat bien tren D.

## 3. Ket qua Tang 2

Tang 2 duoc mo boi MISS da dinh nghia truoc, khong phai boi mot quyet dinh
sau khi xem so.

| cell | LS @51 ms | LS @175 ms | LS @260 ms | Delta @51 ms | Delta @260 ms | sign invariant |
|---|---:|---:|---:|---:|---:|---|
| poisson@0.850 | -0.014183 | +0.003719 | +0.017396 | +0.003120 | -0.003827 | MISS |
| poisson@0.960 | +0.022874 | +0.039272 | +0.055926 | -0.005032 | -0.012304 | HIT |
| h2@0.700 | -0.017574 | +0.028451 | +0.053189 | +0.003866 | -0.011702 | MISS |

Pham vi dieu tra cho thay hien tuong khong rieng `poisson@0.900`: cell
`poisson@0.850` va `h2@0.700` cung doi dau, trong khi `poisson@0.960` giu dau.
Khong mo Tang 3 va khong lam min diem giao.

## 4. Cham M-58..M-65

| ID | Ket qua | Readout |
|---|---|---|
| M-58 | HIT | max gap tai 51 ms = `0.0` cho err/lift/swing/Delta, moi cell |
| M-59 | HIT | max bin-share gap = `8.55e-05 <= 1e-4` |
| M-60 | HIT | `w_loss` bitwise identical tren moi d, moi cell |
| M-61 | MISS | err_neo tang don dieu o moi cell, nhung amplitude `poisson@0.900 = 0.062186 > 0.060` |
| M-62 | **MISS** | LS doi dau tai `poisson@0.900` |
| M-63 | **MISS** | Delta F2 doi dau tai `poisson@0.900` |
| M-64 | HIT | `A(poisson@0.925) = 0.007896 <= 0.018` |
| M-65 | HIT | qhat slot 1 o `(z_bin=0,m_hat_bin=0)` tang don dieu tai moi cell |

M-61 MISS rat hep ve nguong amplitude, khong ve huong: ca nam cell deu co
`err_neo` tang don dieu. Khong noi rong nguong sau khi chay.

Qhat slot 1 tai hai cell Tang 1:

```text
poisson@0.900 : 10.514945, 16.167179, 17.389679, 18.105310, 18.515324
poisson@0.925 : 14.448727, 21.789417, 23.089384, 24.390066, 24.821335
```

M-65 HIT cho thay truc tuoi trong certificate co chiu tai; sensitivity khong
phai mot sweep tren tham so khong anh huong den calibration.

## 5. Controls va tinh co lap

Tat ca controls bat buoc deu PASS:

```text
NC-L  w_loss bitwise                  PASS
NC-M  baseline 51 ms gap <= 1e-12     PASS (max gap = 0.0)
NC-N  bin shares <= 1e-4              PASS (max = 8.55e-05)
NC-O  Delta identity <= 1e-12         PASS
NC-P  row disjoint / seed disjoint    PASS / PASS
NC-Q  n_valid_rows bao cao            PASS
```

Bin shares tai 51 ms la
`0.090005 / 0.200011 / 0.200011 / 0.509973`; tai 260 ms la
`0.090013 / 0.200052 / 0.200047 / 0.509888`. Sai lech toi da nho hon nguong
khoa, nen bien doi ket qua khong do doi khoi luong cac bin.

`n_valid_rows` moi seed giam dung theo lag: 199989 tai 51 ms, 199965 tai
175 ms, 199959 tai 205 ms, 199954 tai 230 ms, va 199948 tai 260 ms. Khong co
lam tron hoac cat ve cung so hang.

## 6. Chi phi chay va artifact

Da chay 25 build, moi build dung `N=200000`, seeds 101--105. Tong wall time
la 219.47 s; trong artifact, tong build time 124.40 s va tong analysis time
93.57 s. Peak resident memory cua process la 957972 KB.

```text
results/phase-23/dsync_sensitivity.json
results/phase-23/fig7_dsync_sensitivity.png
```

Artifact va tung row deu mang `status="SENSITIVITY_ONLY"` va
`closes_P23A=false`.

## 7. Dien giai dung pham vi

Ket qua nay khong uoc tinh `d_sync` that cua `topology_v7`; pilot chi do vong
software local voi 20 Thing gia. No chi chung minh rang ket luan cu **phu thuoc
vao gia tri 51 ms** khi dat trong dai phan ung da do cua bridge. Buoc tiep theo
bat buoc la tich hop collector/pusher/reader vao `topology_v7`, do AoI tai cho,
roi tai danh gia cac ket luan dang mang dieu kien 51 ms.

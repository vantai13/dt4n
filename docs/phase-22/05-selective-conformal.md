# LESSON 22.4 -- selective_conformal.py

Ngay: 2026-08-13

Trang thai: da chay tren du lieu Phase 22 v3 that. Muc tieu cua lesson nay la
khoi phuc tinh hop le SAU KHI da quyet dinh chap nhan.

## 1. San pham

| File | Vai tro |
|---|---|
| `cert/selective_conformal.py` | 3 thu tuc sua post-selection validity |
| `test/test_phase22_selective.py` | 10 golden/characterization tests |
| `results/phase-22/selective_*.json` | report duong cong theo kappa |
| `docs/phase-22/00-preregistration.md` | them D8 va quy tac he so nhan |

Ba thu tuc:

```text
none      : 21R baseline, marginal qhat theo z_bin
fcr       : alpha' = alpha * P(accept), giai bang fixed point
mondrian  : qhat theo taxonomy (z_bin, m_hat_bin)
selective : qhat tren tap calib duoc chon, co phat hien cycle
```

Moi bang ket qua phai co ca hai cot: `violation_given_accept` va
`decision_failure_given_accept`. Lesson nay sua cot thu nhat; cot thu hai da
an toan tu truoc.

## 2. Bang chinh tren poisson@0.925

Input: `results/phase-22/calib_set_v3_poisson_0.925.parquet`

| Thu tuc | kappa | accept | viol\|acc | inflation | fail\|acc | iter | Ket qua |
|---|---:|---:|---:|---:|---:|---:|---|
| none | 0.0 | 1.0000 | 0.0913 | 1.000 | 0.2135 | 1 | PASS |
| none | 0.5 | 0.5855 | 0.1039 | 1.138 | 0.0982 | 1 | FAIL |
| none | 1.0 | 0.2835 | 0.1214 | 1.330 | 0.0307 | 1 | FAIL |
| none | 2.0 | 0.0485 | 0.1614 | 1.767 | 0.0005 | 1 | FAIL |
| none | 4.0 | 0.0012 | 0.3061 | 3.352 | 0.0000 | 1 | FAIL |
| fcr | 0.0 | 1.0000 | 0.0913 | 1.000 | 0.2135 | 2 | PASS |
| fcr | 0.5 | 0.5168 | 0.0571 | 1.264 | 0.0824 | 5 | PASS |
| fcr | 1.0 | 0.0988 | 0.0160 | 2.190 | 0.0037 | 6 | PASS |
| fcr | 2.0 | 0.0000 | nan | nan | nan | 3 | DEGENERATE |
| fcr | 4.0 | 0.0000 | nan | nan | nan | 2 | DEGENERATE |
| mondrian | 0.0 | 1.0000 | 0.0915 | 1.000 | 0.2135 | 1 | PASS |
| mondrian | 0.5 | 0.6031 | 0.0893 | 0.977 | 0.1025 | 1 | PASS |
| mondrian | 1.0 | 0.2564 | 0.0884 | 0.966 | 0.0246 | 1 | PASS |
| mondrian | 2.0 | 0.0302 | 0.1199 | 1.311 | 0.0001 | 1 | FAIL |
| mondrian | 4.0 | 0.0004 | 0.2110 | 2.306 | 0.0000 | 1 | FAIL |
| selective | 0.0 | 1.0000 | 0.0913 | 1.000 | 0.2135 | 1 | PASS |
| selective | 0.5 | 0.5678 | 0.0909 | 1.177 | 0.0946 | 6 | PASS |
| selective | 1.0 | 0.2233 | 0.0849 | 1.631 | 0.0195 | 8 | PASS |
| selective | 2.0 | 0.0256 | 0.0994 | 3.451 | 0.0001 | 1 | PASS observed |
| selective | 4.0 | 0.0012 | 0.3061 | 3.352 | 0.0000 | 0 | DEGENERATE |

Gate tren diem chinh `kappa = 1`:

| Gate | Ket qua |
|---|---|
| G22-6 `viol|accept <= alpha` cho fcr/mondrian/selective | PASS |
| G22-7 fixed points terminate | PASS |
| NC22-2 `kappa=0` quy ve 21R | PASS |
| FCR per-bin collapse duoc bao cao | PASS |
| Mondrian boundary: fail tu `kappa=2` | PASS |

## 3. Tong ket tai kappa=1

| Thu tuc | accept | % so voi 21R | viol\|acc | fail\|acc | he so qhat |
|---|---:|---:|---:|---:|---|
| 21R / none | 0.2835 | 100.0% | 0.1214 FAIL | 0.0307 | 1.000 |
| mondrian | 0.2564 | 90.4% | 0.0884 PASS | 0.0246 | 0.92-1.15 |
| selective | 0.2233 | 78.8% | 0.0849 PASS | 0.0195 | 1.02-1.20 |
| fcr | 0.0988 | 34.8% | 0.0160 PASS | 0.0037 | 1.58-1.63 |

Ket luan: Mondrian la thu tuc re nhat de sua post-selection coverage tai
`kappa=1`: chi mat 9.6% acceptance so voi 21R. FCR an toan hon nhung tra gia
dong nhat, mat 65.2% acceptance.

## 4. FCR la fixed point, khong phai one-shot

One-shot so voi fixed point global:

| Thu tuc | qhat B0..B3 | B0/21R | accept | viol\|acc | iter |
|---|---|---:|---:|---:|---:|
| 21R | [11.5878, 15.6348, 19.6461, 24.3222] | 1.0000 | 0.2835 | 0.1214 | 1 |
| FCR one-shot | [15.5859, 21.1385, 26.2106, 33.0389] | 1.3450 | 0.1590 | 0.0439 | 2 |
| FCR fixed point | [18.8151, 25.1195, 31.0369, 39.6438] | 1.6237 | 0.0988 | 0.0160 | 6 |

Trace fixed point global tai `kappa=1`:

| iter | alpha' | P_accept_global | qhat B0..B3 |
|---:|---|---:|---|
| 0 | [0.10000, 0.10000, 0.10000, 0.10000] | 0.2970 | [11.588, 15.635, 19.646, 24.322] |
| 1 | [0.02970, 0.02970, 0.02970, 0.02970] | 0.1653 | [15.586, 21.139, 26.211, 33.039] |
| 2 | [0.01653, 0.01653, 0.01653, 0.01653] | 0.1296 | [17.303, 23.306, 28.678, 36.665] |
| 3 | [0.01296, 0.01296, 0.01296, 0.01296] | 0.1128 | [18.275, 24.439, 30.173, 38.558] |
| 4 | [0.01128, 0.01128, 0.01128, 0.01128] | 0.1042 | [18.815, 25.119, 31.037, 39.644] |
| 5 | [0.01042, 0.01042, 0.01042, 0.01042] | 0.1042 | [18.815, 25.119, 31.037, 39.644] |

Per-bin FCR sup do tai B3:

| iter | alpha' B0..B3 | P_accept B0..B3 | qhat B0..B3 |
|---:|---|---|---|
| 0 | [0.10000, 0.10000, 0.10000, 0.10000] | [0.5538, 0.4128, 0.3042, 0.2034] | [11.588, 15.635, 19.646, 24.322] |
| 1 | [0.05538, 0.04128, 0.03042, 0.02034] | [0.4770, 0.3034, 0.1738, 0.0627] | [13.634, 19.687, 25.867, 35.161] |
| 2 | [0.04770, 0.03034, 0.01738, 0.00627] | [0.4644, 0.2756, 0.1286, 0.0230] | [14.110, 20.869, 28.678, 42.668] |
| 3 | [0.04644, 0.02756, 0.01286, 0.00230] | [0.4644, 0.2614, 0.1100, 0.0000] | [14.110, 21.410, 30.173, 70.770] |
| 4 | [0.04644, 0.02614, 0.01100, 0.00000] | [0.4644, 0.2614, 0.0994, 0.0000] | [14.110, 21.410, 31.037, inf] |

Co che: `P=0` la trang thai hap thu. Voi `n_eff=500`, FCR can
`P(accept) >= 1/(alpha*(n_eff+1)) = 0.01996`. B3 roi duoi nguong dung luong
do, nen `conformal_level` khong con huu ich va qhat phai la `inf`.

## 5. Co che Mondrian thang

Bang qhat Mondrian tai `kappa=1`, so voi qhat 21R theo z-bin:

| (z_bin, m_hat_bin) | qhat Mondrian | qhat 21R | ti so |
|---|---:|---:|---:|
| (0, 0) | 11.1315 | 11.5878 | 0.9606 |
| (0, 1) | 11.4492 | 11.5878 | 0.9880 |
| (0, 2) | 11.2527 | 11.5878 | 0.9711 |
| (0, 3) | 12.8160 | 11.5878 | 1.1060 |
| (1, 0) | 14.7598 | 15.6348 | 0.9440 |
| (1, 1) | 15.1288 | 15.6348 | 0.9676 |
| (1, 2) | 15.1786 | 15.6348 | 0.9708 |
| (1, 3) | 17.6133 | 15.6348 | 1.1265 |
| (2, 0) | 18.2901 | 19.6461 | 0.9310 |
| (2, 1) | 18.4838 | 19.6461 | 0.9408 |
| (2, 2) | 19.0644 | 19.6461 | 0.9704 |
| (2, 3) | 22.5419 | 19.6461 | 1.1474 |
| (3, 0) | 22.3407 | 24.3222 | 0.9185 |
| (3, 1) | 22.9409 | 24.3222 | 0.9432 |
| (3, 2) | 23.8045 | 24.3222 | 0.9787 |
| (3, 3) | 28.0528 | 24.3222 | 1.1534 |

Ba bin `m_hat=0,1,2` hep hon 21R; bin `m_hat=3` rong hon 1.11-1.15x.
Mondrian tra gia dung noi co selection effect, trong khi FCR tra gia dong nhat
tren moi bin. He so bin `m_hat=3` tang theo tuoi: 1.106 -> 1.153.

Ranh gioi: Mondrian hap thu selection GIUA cac bin `m_hat`, khong hap thu
selection TRONG mot bin. Khi `kappa=2`, tap accept nam gan het trong
`m_hat_bin=3`, nen within-bin selection quay lai va `viol|acc = 0.1199`.

## 6. Selective fixed point va limit cycle

Tai `kappa=1`, selective ket thuc sau 8 vong va phat hien chu trinh dai 4.
Vi qhat la phan vi mau, anh xa la ham bac thang tren tap huu han; no co the
vao limit cycle thay vi hoi tu tron. Quyet dinh thuc thi:

```text
phat hien cycle -> lay max theo tung z-bin tren cycle
```

Day la bao thu va tat dinh. Khong tra ve gia tri vong cuoi vi no phu thuoc
`max_iter` chan/le.

## 7. Doi chieu du doan

| # | Du doan | Do duoc | Ket qua |
|---:|---|---:|---|
| 1 | viol sau chon loc truoc sua 0.115-0.130 | 0.1214 | HIT |
| 2 | FCR fixed point `viol|acc <= 0.10` | 0.0160 | HIT |
| 3 | Mondrian `viol|acc <= 0.10` | 0.0884 | HIT |
| 4 | selective `viol|acc <= 0.10` | 0.0849 | HIT |
| 5 | FCR qhat multiplier 1.45-1.58 | 1.58-1.63 | MISS high |
| 6 | Mondrian multiplier 1.05-1.15 | 0.92-1.15 | PARTIAL |
| 7 | fixed point iters 3-12 | 6 va 8 | HIT |

Ket luan du doan: 5 hit / 1 partial / 1 miss. Loi lap lai tu Lesson 22.3:
voi thu tuc thich ung, "he so nhan" khong phai mot so; phai chi ro he so cua
nhom nao hoac hinh dang phan bo he so.

## 8. Sweep tat ca artifact v3 tai kappa=1

| Artifact | none acc / viol | fcr acc / viol | mondrian acc / viol | selective acc / viol |
|---|---|---|---|---|
| `selective_cbr_0.700.json` | 1.0000 / 0.0790 | 1.0000 / 0.0790 | 1.0000 / 0.0831 | 1.0000 / 0.0790 |
| `selective_h2_0.700.json` | 0.4966 / 0.1252 | 0.3606 / 0.0541 | 0.5215 / 0.0932 | 0.4345 / 0.0935 |
| `selective_poisson_0.700.json` | 1.0000 / 0.0935 | 1.0000 / 0.0935 | 1.0000 / 0.0927 | 1.0000 / 0.0935 |
| `selective_poisson_0.850.json` | 0.2409 / 0.1016 | 0.0000 / nan | 0.2286 / 0.0923 | 0.2214 / 0.0922 |
| `selective_poisson_0.925.json` | 0.2835 / 0.1214 | 0.0988 / 0.0160 | 0.2564 / 0.0884 | 0.2233 / 0.0849 |
| `selective_poisson_0.925_V3.json` | 0.2963 / 0.1349 | 0.1142 / 0.0233 | 0.2717 / 0.1023 | 0.2404 / 0.0994 |

Ghi chu: sweep phu la boundary/control. Gate confirmatory cua Lesson 22.4 khoa
tren o chinh `poisson@0.925`. V3 la positive-control split theo hang, nen
Mondrian vuot alpha nhe tai `kappa=1` la dau hieu boundary, khong phai claim
confirmatory.

## 9. Tests

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase22_selective.py -q
10 passed in 4.92s

/tmp/dt4n-venv/bin/python -m pytest -q test/test_phase22_simscore.py test/test_phase22_calibv3.py test/test_phase22_conformalsim.py test/test_phase22_selective.py
56 passed in 30.50s

/tmp/dt4n-venv/bin/python -m pytest -q
693 passed, 4 skipped in 194.16s (0:03:14)
```

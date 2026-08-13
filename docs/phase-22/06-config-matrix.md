# LESSON 22.5 -- config_matrix.py

Ngay: 2026-08-13

Trang thai: da chay tren du lieu Phase 22 v3 that. Day la ket qua headline cua
Phase 22: ghep C0/C1/C2/C3 va dung duong cong risk-coverage de tra loi H22-7.

## 1. San pham

| File | Vai tro |
|---|---|
| `cert/config_matrix.py` | fit/eval C0/C1/C2/C3 bang mot code path |
| `test/test_phase22_matrix.py` | 12 tests khoa ma tran, H22-7, frontier |
| `results/phase-22/config_matrix_*.json` | report risk-coverage cho 5 o + V3 |
| `scripts/fig_risk_coverage.py` | ve hinh headline |
| `results/phase-22/fig_risk_coverage.pdf` | hinh risk-coverage |

Ma tran:

| | post-selection: no | post-selection: yes |
|---|---|---|
| pair only | C0 = 21R | C2 |
| simultaneous | C1 | C3 = full claim |

H22-7 dat neu ton tai `kappa` sao cho:

```text
acceptance >= 0.10
err|accept <= 0.50 * anchor_err
viol|accept <= alpha
```

## 2. O chinh poisson@0.925

```text
anchor_err_on_test = 0.222399
threshold_risk = 0.111199
```

### Bon duong cong

| cfg | kappa | accept | err\|accept | risk ratio | viol\|accept | pass coverage |
|---|---:|---:|---:|---:|---:|---|
| C0 | 0.00 | 1.0000 | 0.2224 | 1.000 | 0.0913 | True |
| C0 | 0.50 | 0.5855 | 0.1034 | 0.465 | 0.1039 | False |
| C0 | 1.00 | 0.2835 | 0.0330 | 0.148 | 0.1214 | False |
| C0 | 1.50 | 0.1211 | 0.0074 | 0.033 | 0.1417 | False |
| C0 | 2.00 | 0.0485 | 0.0009 | 0.004 | 0.1614 | False |
| C1 | 0.00 | 1.0000 | 0.2224 | 1.000 | 0.0747 | True |
| C1 | 0.50 | 0.4730 | 0.0774 | 0.348 | 0.0896 | True |
| C1 | 1.00 | 0.1679 | 0.0137 | 0.062 | 0.1076 | False |
| C2 | 0.00 | 1.0000 | 0.2224 | 1.000 | 0.0915 | True |
| C2 | 0.50 | 0.6031 | 0.1079 | 0.485 | 0.0893 | True |
| C2 | 1.00 | 0.2564 | 0.0262 | 0.118 | 0.0884 | True |
| C2 | 1.50 | 0.0900 | 0.0026 | 0.012 | 0.1022 | False |
| C2 | 2.00 | 0.0302 | 0.0001 | 0.000 | 0.1199 | False |
| C3 | 0.00 | 1.0000 | 0.2224 | 1.000 | 0.0773 | True |
| C3 | 0.50 | 0.4911 | 0.0809 | 0.364 | 0.0794 | True |
| C3 | 1.00 | 0.1436 | 0.0095 | 0.043 | 0.0823 | True |
| C3 | 1.50 | 0.0348 | 0.0001 | 0.000 | 0.0876 | True |
| C3 | 2.00 | 0.0095 | 0.0000 | 0.000 | 0.0987 | True |
| C3 | 3.00 | 0.0005 | 0.0000 | 0.000 | 0.0760 | True |

### H22-7

| cfg | AURC | H22-7 | kappa | acceptance | risk ratio |
|---|---:|---|---:|---:|---:|
| C0 | 0.091335 | False | n/a | n/a | n/a |
| C1 | 0.091855 | True | 0.50 | 0.4730 | 0.3478 |
| C2 | 0.091051 | True | 0.50 | 0.6031 | 0.4852 |
| C3 | 0.091085 | True | 0.50 | 0.4911 | 0.3636 |

Ket luan headline:

```text
C3 tai kappa=0.5:
  acceptance = 0.4911
  err|accept = 0.0809 = 36.4% anchor
  viol|accept = 0.0794 <= alpha

H22-7 PASS cho tuyen bo day du.
C0 FAIL vi moi diem co risk du thap deu vi pham post-selection coverage.
```

## 3. Frontier gan nhu khong doi

Rui ro tai cung muc chap nhan:

| cfg | acc=0.70 | acc=0.50 | acc=0.30 | acc=0.15 |
|---|---:|---:|---:|---:|
| C0 | 0.13534 | 0.08387 | 0.03694 | 0.01105 |
| C1 | 0.13568 | 0.08429 | 0.03746 | 0.01128 |
| C2 | 0.13518 | 0.08410 | 0.03672 | 0.01006 |
| C3 | 0.13568 | 0.08319 | 0.03535 | 0.01044 |

C3/C0:

| acc | ti so |
|---:|---:|
| 0.70 | 1.0026 |
| 0.50 | 0.9919 |
| 0.30 | 0.9571 |
| 0.15 | 0.9444 |

Ket luan: tren o chinh, chi phi cua tinh chat che hinh thuc la di chuyen diem
van hanh doc duong bien, khong lam duong bien xau di. AURC cua bon cau hinh
nam trong `[0.0911, 0.0919]`.

Co che: Lesson 22.3 cho thay slot 1 gan nhu binding. Neu qhat moi chi la he so
gan hang so `c` cua qhat 21R, thi:

```text
accept(config, kappa) <=> accept(C0, kappa*c)
```

Tuc la doi cau hinh gan nhu chi doi tham so `kappa`. Kiem chung:

```text
C1(kappa=0.5) ~ C0(kappa=0.655)
acceptance 0.4730 vs 0.4784, lech 1.1%
```

## 4. Tuong tac co loi

Bonferroni thua bao phu tai bien:

```text
C0 viol marginal = 0.0913
C1 viol marginal = 0.0747
C2 viol marginal = 0.0915
C3 viol marginal = 0.0773
```

Phan bao thu du cua simultaneous correction tai tro cho selection trong bin ma
Mondrian bo sot:

| kappa | C2 viol\|acc | C3 viol\|acc |
|---:|---:|---:|
| 1.00 | 0.0884 | 0.0823 |
| 1.50 | 0.1022 FAIL | 0.0876 PASS |
| 2.00 | 0.1199 FAIL | 0.0987 PASS |
| 3.00 | 0.1538 FAIL | 0.0760 PASS |

Day la interaction effect co loi: hai hieu chinh khong chi cong chi phi, ma
mot hieu chinh lam hieu chinh kia ben hon.

## 5. Bon post variants trong C3

| post | AURC | H22-7 | kappa H22-7 | acceptance H22-7 | risk ratio | accept @ kappa=1 |
|---|---:|---|---:|---:|---:|---:|
| mondrian | 0.0911 | True | 0.50 | 0.4911 | 0.3636 | 0.1436 |
| selective | 0.0917 | True | 0.50 | 0.4450 | 0.3231 | 0.1108 |
| none | 0.0919 | True | 0.50 | 0.4730 | 0.3478 | 0.1679 |
| fcr | 0.1067 | True | 0.50 | 0.4022 | 0.2739 | 0.0000 |

FCR la variant duy nhat lam xau frontier tren o chinh (`AURC +17%`) va sup tu
`kappa >= 1` trong C3.

## 6. Sweep tat ca artifact v3

| Artifact | anchor | C3 H22-7 | C3 kappa | C3 acceptance | C3 risk ratio | frontier unchanged | frontier not degraded |
|---|---:|---|---:|---:|---:|---|---|
| `config_matrix_cbr_0.700.json` | 0.0000 | n/a | n/a | n/a | n/a | False | True |
| `config_matrix_h2_0.700.json` | 0.1265 | True | 0.50 | 0.7000 | 0.3561 | False | True |
| `config_matrix_poisson_0.700.json` | 0.0000 | n/a | n/a | n/a | n/a | False | True |
| `config_matrix_poisson_0.850.json` | 0.2207 | True | 0.50 | 0.4287 | 0.3055 | True | True |
| `config_matrix_poisson_0.925.json` | 0.2224 | True | 0.50 | 0.4911 | 0.3636 | True | True |
| `config_matrix_poisson_0.925_V3.json` | 0.2201 | True | 0.50 | 0.5039 | 0.3755 | True | True |

Ghi chu pham vi:

```text
cbr@0.700 va poisson@0.700 co anchor_err = 0, nen H22-7 suy bien / khong ap dung.
h2@0.700 khong dat "within 8%" vi C3 tot hon C0 qua 8% tai acceptance thap,
khong phai vi frontier xau di. Gate "not degraded" van PASS.
```

## 7. Hinh

```text
results/phase-22/fig_risk_coverage.pdf
```

Panel trai: risk-coverage frontier, marker dac la coverage valid, marker rong
la coverage violated. Panel phai: `P(s > qhat | accept)` theo `kappa`.

## 8. Du doan

Cham theo C3+Mondrian: 1 hit / 5 miss. Nguyen nhan la cac dong C3 trong bang
du doan bi rang ngam voi FCR, trong khi Lesson 22.4 da chon Mondrian lam thu
tuc chinh. Du doan cau truc van trung: H22-7 dat tai `kappa=0.5`.

Them P15 vao prereg: moi dong du doan phai dinh danh day du thu tuc, nhom/slot
va tap hang.

## 9. Tests

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase22_matrix.py -q
12 passed in 97.13s (0:01:37)

/tmp/dt4n-venv/bin/python -m pytest -q test/test_phase22_simscore.py test/test_phase22_calibv3.py test/test_phase22_conformalsim.py test/test_phase22_selective.py test/test_phase22_matrix.py
68 passed in 124.01s (0:02:04)

/tmp/dt4n-venv/bin/python -m pytest -q
705 passed, 4 skipped in 293.68s (0:04:53)
```

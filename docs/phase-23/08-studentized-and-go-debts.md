# Lesson 23.5[A] -- Studentized max-score and GO-3 debt

Ngay chay: 2026-08-16
Trang thai: EXPLORATORY, theo `docs/phase-23/00u-amendment-20.md`.

Input:

```text
results/phase-22/calib_set_v3_poisson_0.925.parquet
results/phase-22/calib_set_v3_poisson_0.850.parquet
results/phase-22/calib_set_v3_h2_0.700.parquet
```

Output:

```text
results/phase-23/studentized_poisson_0.925.json
results/phase-23/studentized_poisson_0.850.json
results/phase-23/studentized_h2_0.700.json
```

## 1. Doc ket qua theo dung thu tu khoa

| Cell | `sigma_max/min` theo bin | `c` theo bin | G3 ratios slot1/2/3 | coverage | acceptance max -> stud |
|---|---|---|---|---:|---:|
| poisson@0.925 | 1.1117, 1.1110, 1.1167, 1.1421 | 2.1018, 2.1252, 2.1030, 2.0928 | 0.9525 / 0.9966 / 1.0671 | 0.9095 | 0.1666 -> 0.1857 |
| poisson@0.850 | 1.2787, 1.2914, 1.3051, 1.3325 | 2.1946, 2.1842, 2.1596, 2.1418 | 0.8740 / 0.9865 / 1.1378 | 0.9113 | 0.0952 -> 0.1356 |
| h2@0.700 | 1.6557, 1.4976, 1.4268, 1.3897 | 1.9661, 2.0340, 2.0609, 2.0672 | 0.7678 / 0.9931 / 1.1411 | 0.9048 | 0.2611 -> 0.3867 |

S-5 phai doc truoc: main cell co slot heterogeneity nho (`~1.11-1.14`), nen
studentization chi mua duoc +0.0191 acceptance. Hai cell phu co heterogeneity
lon hon va lift acceptance lon hon, dung co che tai phan bo.

## 2. GO-3

G3a v1 tren main cell PASS:

```text
qhat_stud/qhat_max slot 1 = 0.9525, nam trong dai v1 0.92-0.98.
```

G3b v1 la PARTIAL/MISS:

```text
slot 2 = 0.9966, nam trong dai v1 0.98-1.02.
slot 3 = 1.0671, nam ngoai dai v1 0.98-1.02.
```

Theo Amendment 23-20, slot 3 rong hon maxscore khong phai loi: studentization
tai phan bo budget, khong lam moi qhat nho di. Dai v2 PASS cho ca ba slot tren
main cell:

```text
slot 1: 0.90-1.00  -> 0.9525 PASS
slot 2: 0.94-1.05  -> 0.9966 PASS
slot 3: 1.00-1.12  -> 1.0671 PASS
```

## 3. Coverage, acceptance, controls

| Cell | coverage stud | coverage maxscore | delta acceptance | NC-S-1 max diff | PC-S-1 full drop | PC-S-1 small drop |
|---|---:|---:|---:|---:|---:|---:|
| poisson@0.925 | 0.909492 | 0.906662 | +0.019147 | 0.0 | 0.000894 | 0.002591 |
| poisson@0.850 | 0.911294 | 0.905742 | +0.040419 | 0.0 | 0.000346 | 0.001955 |
| h2@0.700 | 0.904788 | 0.902250 | +0.125620 | 0.0 | 0.000740 | 0.001000 |

G23-25 PASS: simultaneous coverage giu quanh 0.90 tren ca ba cell.

G23-26 PASS: NC-S-1 cho `max_abs_diff = 0.0`, nghia la sigma dong nhat dung
bang maxscore tren fold2 nhu D7.

G23-27 duoc doc theo Amendment 23-20: full-data PC-S-1 khong phat hien duoc
ro ri vi hieu ung nam duoi do phan giai. Ket qua nay la diagnostic
"khong phat hien duoc", khong phai PASS.

## 4. Ket luan

Studentization dung ve co che va giu coverage. Tren main cell, loi ich nho
nhung dung du bao: +1.9 diem phan tram acceptance, vi cac rank slot gan dong
nhat. Tren cell phu co `sigma_max/min` lon hon, acceptance lift lon hon.

Ket luan GO-3: studentized max-score nen giu la EXPLORATORY. No dong no GO-3
bang mot ket qua co co che ro, nhung chua thay the duong ong maxscore
confirmatory cua Phase 22.

# AMENDMENT 19 -- Lesson 20R.8: exact zero err needs a mechanism

Ngay ky: 2026-08-12
Trang thai: KY trong Lesson 20R.8, sau khi them
`measurements/locked_argmin_check.py`.

## 1. Van de

Mot so o poisson trong `decision_error_unimodal.parquet` co
`err_total = 0.000000` dung bang 0. Day la gia tri bien nen khong duoc de nhu
mot con so "dep": no phai co co che giai thich, neu khong thi nghi bug.

## 2. Tieu chi co hoc

Voi moi thoi diem `t`, tinh khe giua duong tot nhat va duong nhi theo bang
truth measured:

```text
gap(t) = cost_second(t) - cost_best(t)
```

Va tinh sai so twin lon nhat tren tat ca path:

```text
eps_max = max_t |cost_twin(t) - cost_true(t)|
lock_ratio = min_t gap(t) / eps_max
```

Neu `lock_ratio > 1`, sai so twin khong bao gio du de dong khe cost. Khi do
argmin khong the lat, nen `err = 0` la tat yeu.

## 3. Ket qua representative

Artifact: `results/phase-20R/locked_argmin_check.json`

```text
mode     rho_bar | opt_path_share                  | min gap | twin err | ratio
poisson    0.635 | {P1: 1.000}                     |  1.1219 |   0.1899 | 5.91
poisson    0.650 | {P1: 1.000}                     |  1.0660 |   0.1999 | 5.33
poisson    0.700 | {P1: 1.000}                     |  0.5134 |   0.3758 | 1.37
poisson    0.850 | {P1:0.657, P3:0.325, P4:0.019} |  0.0001 |   3.2054 | 0.00
h2         0.635 | {P1:0.717, P3:0.277, P4:0.007} |  0.0002 |   5.4678 | 0.00
h2         0.700 | {P1:0.842, P3:0.158}           |  0.0000 |   9.4112 | 0.00
h2         0.850 | {P1:0.994, P3:0.006}           |  0.0048 |   9.0891 | 0.00
```

## 4. Quyet dinh

`err = 0` trong regime poisson tai tai thap la CHE DO khoa argmin, khong phai
bug. Neu mot artifact sau nay cho `err = 0` trong cell co `lock_ratio <= 1`,
phai dung phase va dieu tra truoc khi dung ket qua.

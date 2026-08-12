# Lesson 21R.1 -- margin_score.py

Ngay hoan thanh: 2026-08-12

## Dinh nghia da chot

```text
a1 = argmin_a y_hat(a)
a2 = argmin_{a != a1} y_hat(a)

m_hat  = y_hat(a2)  - y_hat(a1)
m_true = y_true(a2) - y_true(a1)

s_margin = |m_true - m_hat| = |e(a2) - e(a1)|
e = y_true - y_hat
```

`a1` va `a2` chon theo twin, khong theo truth. Day la ranh gioi chong ro ri.

## Rao chan an ninh

`top_two_by_twin()` co dung mot tham so: `y_hat`. Golden test G-M1 dung
`inspect.signature` de khoa rang ham khong the nhin `y_true`.

Tie duoc xu ly bang `np.argsort(kind="stable")`, nen neu cac chi phi bang nhau
thi action index nho hon duoc chon truoc. Moi phep tinh ep ve `float64`.

## Quy tac chap nhan da sua

```text
C1: accept <=> m_hat >= q_hat
C2: ub_regret = max(0, q_hat - m_hat)
C3: accept <=> m_hat >= kappa * q_hat
```

He so C1 la `1*q_hat`, khong phai `2*q_hat`, vi `q_hat` duoc dat tren bien
quyet dinh. `kappa=2` van duoc giu lam diem so sanh lich su voi quy uoc v7.

## 16 golden test -- ket qua

Lenh:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_margin.py -q
```

Ket qua:

```text
................                                                         [100%]
16 passed in 0.14s
```

## Toan bo test suite -- ket qua

Lenh:

```bash
/tmp/dt4n-venv/bin/python -m pytest -q
```

Lan chay dau dung o collection vi venv tam `/tmp/dt4n-venv` thieu dependency
`mpmath`. Sau khi cai `mpmath` vao venv tam, full suite dat:

```text
550 passed, 1 skipped, 2 warnings in 155.72s (0:02:35)
```

## Smoke tren du lieu that

Smoke chay tren seed `999`, nam ngoai tap tien dang ky `{101,102,103,104,105}`.
Chi bao cao bat bien va ti so; khong bao cao `q_hat` tuyet doi.

```text
== SMOKE (poisson@0.925, sigma=0.0096, z=0.20s, seed 999) ==
chay khong loi                : True
khong NaN/inf                 : True
m_hat >= 0 (moi hang)         : True
m_true co gia tri am          : True     ti le = 0.1878
s_margin <= s_vs_a1           : True
s_signed <= s_margin          : True
hai cong thuc trung khop      : True
score khong suy bien          : True
cap top-2 chua a* (R2)        : 0.9907
clip_fraction max             : 0.000000

-- DOI CHIEU THU BAC (chi ti so, tranh peeking) --
p90(s_margin) / p90(s_vs_a1)  = 0.7512
p90(s_margin) / p90(s_maxabs) = 0.9374
p90(s_signed) / p90(s_margin) = 0.9039

-- KIEM CHUNG CHEO 20R --
ti le m_true < 0 module moi   = 0.187773
err_total 20R constant_sigma  = 0.190658
chenh lech tuyet doi          = 0.002885
```

## Doc ket qua smoke

Ket qua `m_true < 0` cua module moi sat voi `err_total` tu Phase 20R, du hai
duong tinh doc lap va seed khac. Chenh lech nho vi `m_true < 0` chi tinh tren
cap top-2 cua twin, con `err_total` 20R tinh tren ca K=4.

`pair_is_true_contender = 0.9907`, nen rui ro R2 co that nhung nho trong smoke
nay. Ti so `p90(s_margin)/p90(s_vs_a1) = 0.7512` cho thay loi chinh cua
`s_margin` den tu viec thu hep tu K-1 doi thu xuong 1 doi thu. Ti so
`p90(s_margin)/p90(s_maxabs) = 0.9374` cho thay sai so chu yeu la vi sai, khong
phai common-mode.

## Artifact

```text
cert/margin_score.py
test/test_phase21r_margin.py
docs/phase-21R/00b-amendment-1.md
docs/phase-21R/02-margin-score.md
```

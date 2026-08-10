# Phase 20R.7 -- Mechanism Map

Trang thai: draft sau B.3, truoc khi ve bon hinh final.

## 1. Estimand

Lesson 20R.7 do co che cua:

```text
cost = delay + w_loss * loss
```

Khong dung `d2(delay)/d(rho)^2` lam hinh chinh. Delay curvature chi la phu luc
de doi chieu, vi Lesson 20R.5 va cascade v2 deu chi ra co che loss-driven.

## 2. K4 Gap Mechanism

Tai `rho_bar=0.925`, path cost baseline:

```text
poisson:
  P1 = 112.9658
  P2 = 174.1808
  P3 = 120.5115
  P4 = 146.5933
  khe nho nhat = |P1-P3| = 7.5457

h2:
  P1 = 745.4047
  P2 = 1005.9540
  P3 = 848.0640
  P4 = 986.3044
  khe nho nhat = |P2-P4| = 19.6496
```

Scan cascade lam `poisson@0.925` doi ranking:

```text
P1,P3,P4,P2 -> P3,P1,P4,P2
```

Tuc K4 gay dung o cap co khe quyet dinh nho nhat cua o binding.

## 3. First-Order Formula Is Not Enough

Voi common-mode `delta` tren loss tung link, cong thuc khong-clip bac nhat la:

```text
S_P = sum_i prod_{j != i}(1 - p_j)
d(gap_ab)/d(delta) = w_loss * (S_a - S_b)
delta*_ab = |gap_ab| / (w_loss * |S_a - S_b|)
```

Chay B.3 cho:

```text
poisson first-order best = P2/P4, r*_path = 1.533354
h2 first-order best      = P3/P4, r*_path = 1.398990
```

Dieu nay khong khop scan `poisson`:

```text
scan r* = 0.008868
scan cap gay = P1/P3
```

Vi vay cong thuc khong-clip khong duoc bao cao nhu closed-form cua `r*`.

## 4. Clipped Piecewise Mechanism

Scan K4 gay o dau am cua residual:

```text
r_path = 0.008868
per_link_shift = -0.002956
clip_events = 4 / 12
```

Hai link bi clip:

```text
uA loss = 0.000536
vC loss = 0.000536
```

Dung cong thuc piecewise:

```text
p'_i = max(p_i - x, 0)
loss_P(x) = 1 - prod_i(1 - p'_i)
cost_P(x) = delay_P + w_loss * loss_P(x)
```

Giai `cost_P1(x) = cost_P3(x)` cho:

```text
x_link* = 0.002936189839
r_path* = 3*x_link* = 0.008808569518
scan bracket = [0.008804852308, 0.008868196569]
```

Day la ket qua co che chinh: K4 cascade khong chi do leak tuyen tinh cua
common-mode qua composition phi tuyen; no do leak phi tuyen **cong voi clipping
vat ly o mien loss >= 0**.

## 5. H2 Safety

Trong artifact `mechanism_k4_closed_form.json`, `h2` khong co root clipped trong
vung `|r_path| <= 0.15` cho ca dau am va dau duong. Dieu nay khop scan cascade:

```text
h2/loss safety > 10.00
h2/delay safety > 10.03
```

Viec `h2` an toan khong duoc giai thich bang cung cong thuc khong-clip; no duoc
giai thich bang piecewise clipped landscape: tai bien do cascade da do, khong
co cap path nao cat nhau.

## 6. Artifacts

```text
results/phase-20R/mechanism_k4_closed_form.json
measurements/mechanism_map.py
test/test_phase20r7_mechanism.py
```

Validation hien co:

```text
[x] S_P voi p deu: S_P = 3(1-p)^2
[x] grad_cost gom w_loss * dloss/drho
[x] clipped negative P1/P3 root nam trong bracket scan
[x] first-order unclipped khong bi nham thanh co che K4 clipped
```

## 7. Figures To Produce

Thu tu uu tien sau B.3:

```text
1. gap_ab(x) piecewise clipped cho poisson va h2
2. tach dong gop d2(delay)/drho2 vs w_loss*d2(loss)/drho2
3. d2(cost)/drho2 theo rho
4. median r(s) vs err(z=0.3)
```

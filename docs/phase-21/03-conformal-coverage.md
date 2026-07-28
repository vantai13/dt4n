# PHASE 21.3 - Conformal Coverage

Ngay chay: 2026-07-28
Script: `cert/conformal_age.py`

## 1. Offered Primary: `z_bin`, `s_vs_a1`

```text
SPLIT: 248 block calib | 247 block test | score=s_vs_a1 | o=z_bin
```

Ba bien the `q_hat`:

```text
(A) coverage=0.88782 target=0.90000 H4=PASS q=[62.9, 88.6, 99.7, 118.4, 125.6]
(B) coverage=0.90110 target=0.90726 H4=PASS q=[64.1, 88.8, 105.9, 120.2, 133.2]
(C) coverage=0.99884 target=0.90000 H4=FAIL q=[145.0, 188.4, 212.6, 239.0, 260.9]
primary variant = B
```

H3/H4/H6:

```text
o  n_blk_calib  q_hat    coverage
0       248      64.112   0.90177
1       248      88.802   0.90077
2       248     105.896   0.89989
3       248     120.171   0.90263
4       248     133.201   0.90045

H3 PASS: marginal 0.90110, |0.90110 - 0.90| = 0.00110
H4 PASS: moi o trong 0.90 +- 0.05
H6 PASS: q_hat(alpha/K) > q_hat(alpha) moi o
```

V3:

```text
SD(sample)/SD(block) mean = 0.349 < 0.5 -> PASS
```

V3c:

```text
leave-one-trace-out span = 0.01297 <= 0.05 -> PASS
```

Ket luan: coverage conformal cho source chinh PASS sach tren split block.

## 2. Offered Appendix: `z_bin x u_bin`

```text
primary variant = A
H3 PASS: marginal 0.90359
H4 PASS: 20/20 o trong 0.90 +- 0.05
H6 PASS
V3 PASS: SD(sample)/SD(block) mean = 0.376
V3c FAIL: span = 0.08190 > 0.05
```

Dien giai: 2D co the cho risk-coverage phu tot hon o vai diem, nhung bi vi
pham robustness giua trace. Theo Amendment 3, giu 1D `z_bin` lam chinh va dua
2D vao phu luc/limitations.

## 3. Measured Robustness: `z_bin`

```text
SPLIT: 248 block calib | 247 block test | score=s_vs_a1 | o=z_bin

(A) coverage=0.91078 H4=PASS q=[74.7, 104.7]
(B) coverage=0.90079 H4=PASS q=[68.6, 103.0]
(C) coverage=0.99638 H4=FAIL q=[145.9, 184.5]
primary variant = B

H3 PASS: marginal 0.90079
H4 PASS
H6 PASS
V3 FAIL: SD(sample)/SD(block) mean = 0.930
V3c PASS: span = 0.03389
```

Dien giai: measured co do phan giai tuoi 200 ms, dung lam robustness only.
Coverage H3/H4/H6 dat, V3 khong thay ro trieu chung sup phuong sai. Ghi vao
limitations; khong dung measured de calibrate certificate chinh.

## 4. Risk-Coverage OUT-OF-SAMPLE

Primary 1D `z_bin`, variant B, danh gia tren 247 test block:

```text
 eps(ms)  coverage   err|acc  d_sla|acc  regret|acc
       0    0.0573    0.0339    0.01335       0.483
       5    0.0644    0.0405    0.01638       0.657
      10    0.0715    0.0472    0.02115       0.689
      20    0.0918    0.0656    0.02772       1.027
      30    0.1166    0.0912    0.04059       1.348
      50    0.1674    0.1393    0.06161       2.331
      70    0.3569    0.1473    0.06376       3.129
     100    0.5551    0.1704    0.07346       4.439
  ANCHOR    1.0000    0.1868    0.08100       6.280
```

Appendix 2D `z_bin x u_bin`, variant A:

```text
 eps(ms)  coverage   err|acc  d_sla|acc  regret|acc
       0    0.0636    0.0411    0.01966       0.565
       5    0.0755    0.0464    0.02213       0.639
      10    0.0828    0.0576    0.02633       0.747
      20    0.1019    0.0731    0.03478       0.965
      30    0.1253    0.1016    0.05015       1.323
      50    0.1688    0.1382    0.06072       2.265
      70    0.3298    0.1346    0.05493       2.693
     100    0.6216    0.1578    0.06503       4.287
  ANCHOR    1.0000    0.1868    0.08100       6.280
```

H_C moi tren primary 1D PASS:

```text
co diem coverage >= 0.01 va err|acc <= 0.09117: eps 0,5,10,20 thoa; eps 30 sat nguong
co >= 4 diem trong coverage [0.01,0.90]
err|acc tang theo coverage tren cac diem eps
```

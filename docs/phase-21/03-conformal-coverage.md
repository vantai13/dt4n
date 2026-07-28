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

### 1.1. Kiem Tra V3 Voi Ly Thuyet Nhi Thuc

`SD(sample)` khop cong thuc nhi thuc thuan tuy:

```text
sqrt(2 * alpha * (1 - alpha) / n_half)
  offered: n_half = 70,378 -> sqrt(0.18 / 70378) = 0.001599
  do duoc trung binh 5 o = 0.001622
```

Trong khi do `SD(block)` xap xi 0.0046. Phan du giua block:

```text
sqrt(0.0046^2 - 0.0016^2) = 0.0043
```

Ket qua nay cho thay split theo mau xoa mat bien thien that giua block va lam
ta qua tu tin vao coverage; split theo block giu lai nguon bat dinh dung can do.

### 1.2. Ba Bien The Va Mo Ho A3.2

Bien the (A) thieu bao phu 0.01218 diem so voi 0.90, nhung day nam trong sai
so lay mau cua 248 block:

```text
sqrt(0.09 / 248) = 0.019
0.01218 / 0.019 = 0.64 SD
```

Bien the (B) dat marginal 0.90110 va muc tieu rieng 0.90726, on dinh hon (A)
vi dung nhieu mau trong moi bin va noi muc phan vi theo so block. Bien the (C)
dat marginal 0.99884 va H4 FAIL vi no dung block-max, bao dam manh hon muc tieu
0.90; day khong phai bug.

Van ban A3.2 va hien thuc trong code dung hai cach doc khac nhau cua "lech".
Kiem tra lai cho thay bien the (B) thang duoi ca hai cach doc:

```text
                  |bien - 0.90|    |bien - muc tieu rieng|
(A)                  0.01218             0.01218
(B)                  0.00110             0.00616
(C)                  0.09884             0.09884
```

Do do viec chon (B) khong phu thuoc cach dien giai. Ghi nhan mo ho nay de minh
bach; khong sua nguoc Amendment 3.

## 2. Offered Appendix: `z_bin x u_bin`

```text
primary variant = A
H3 PASS: marginal 0.90359
H4 PASS: 20/20 o trong 0.90 +- 0.05
H6 PASS
V3 PASS: SD(sample)/SD(block) mean = 0.376
V3c FAIL: span = 0.08190 > 0.05
```

Dien giai: 2D H3/H4/H6/V3 PASS nhung V3c FAIL. Day khong phai artifact do so
sanh nhieu gia tri hon: span ky vong neu chi do multiple comparison tang tu
0.01297 cho 25 gia tri len khoang 0.0166 cho 100 gia tri, trong khi do duoc
0.08190.

Co che that:

```text
z_bin sinh tu lich dong bo tat dinh -> phan hoach giong nhau o moi trace
u_bin sinh tu rho_hat/thresh       -> phan hoach phu thuoc hien thuc rho(t)
```

Vi `u_bin` la trace-specific, o `(z,u)` cua trace nay khong hoan toan la cung
mot o voi trace khac khi leave-one-trace-out. Ket qua nay xac nhan doc lap
quyet dinh A3.1: giu 1D `z_bin` lam primary; 2D chi bao cao phu luc kem canh
bao V3c FAIL va khong dung cho ket luan chinh.

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
V3 FAIL theo nguong A3.3: SD(sample)/SD(block) mean = 0.930
V3c PASS: span = 0.03389
```

Dien giai: measured co do phan giai tuoi 200 ms, dung lam robustness only.
Coverage H3/H4/H6 dat. V3 tren measured la INCONCLUSIVE, khong phai bang chung
chong lai cau truc block.

Chan doan:

```text
SD_mau ly thuyet = sqrt(2 * alpha * (1 - alpha) / n_half)

offered : n_half = 70,378 -> du doan 0.001599 | do 0.001622
measured: n_half =  7,464 -> du doan 0.004911 | do 0.004918
```

Phep kiem V3 chi co luc khi:

```text
sqrt(0.18 / n_half) < 0.5 * SD_block
n_half > 0.18 / 0.0025^2 = 28,800 mau/o moi nua
```

Offered co 70,378 mau/o moi nua nen V3 co luc. Measured chi co 7,464, thieu
3.9 lan, nen khong du luc de phan biet `SD(sample)` va `SD(block)`. Bang chung
thay the van ung ho split theo block:

```text
dt = 0.2 s, tau = 2.87 s
corr mau ke nhau = exp(-0.2 / 2.87) = 0.9325

offered : block_mean 0.9073 vs sample_mean 0.9000 -> +0.0073
measured: block_mean 0.9073 vs sample_mean 0.9001 -> +0.0072
noi muc phan vi cua (B) = 0.90726 - 0.90000 = 0.00726
```

Khong ha nguong V3. Ghi measured V3 la INCONCLUSIVE va chi dung measured nhu
robustness check, khong dung de calibrate certificate chinh.

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
anchor err = 0.1868 -> 0.5 * anchor = 0.0934
co diem coverage >= 0.01 va err|acc <= 0.0934:
  eps 0, 5, 10, 20, 30 thoa
Spearman(cov, err|acc) = 1.0000
co 8 diem phan biet trong coverage [0.01,0.90]
```

H_C cu FAIL va duoc bao cao cong khai:

```text
coverage(eps = 0) = 0.0573 < 0.10
```

In-sample preview va OOS rat gan nhau:

```text
              in-sample    OOS       chen h
cov eps=0       0.0543     0.0573    +0.0030
err|acc         0.0333     0.0339    +0.0006
d_sla|acc       0.01120    0.01335   +0.00215
```

Headline OOS:

```text
cov 5.73% : err 0.1868 -> 0.0339 (5.5x), d_sla 0.0810 -> 0.0134 (6.1x),
            regret 6.28 -> 0.48 ms (13.0x)
cov 11.66%: err 0.1868 -> 0.0912 (2.0x), d_sla 0.0810 -> 0.0406 (2.0x),
            regret 6.28 -> 1.35 ms (4.7x)
```

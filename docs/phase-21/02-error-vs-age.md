# PHASE 21.2 - Error Versus Age

Ngay chay: 2026-07-28
Script: `cert/error_vs_age.py`
Nguon chinh: `cert/calib_set_offered.parquet`

## 1. Offered, Score Chinh `s_vs_a1`

```text
Q1 - q_hat theo BIN TUOI (score = s_vs_a1, alpha = 0.1)
tensor X: (495, 5, 256)

bin      q_hat       CI lo       CI hi    p50(s)    p90(s)
0       63.962      62.804      66.974    30.391    63.359
1       88.753      87.800      90.667    43.866    88.548
2      105.870     103.856     107.021    53.659   104.366
3      119.739     117.854     121.772    60.405   118.924
4      132.654     129.853     134.767    68.323   131.469

4 hieu lien tiep, CI99.75:
bin1-bin0 = 24.641 CI[22.026, 25.793] OK
bin2-bin1 = 16.763 CI[15.254, 17.845] OK
bin3-bin2 = 14.138 CI[12.837, 15.810] OK
bin4-bin3 = 12.905 CI[11.226, 14.427] OK

H1: ratio = 2.074, monotone PASS, 4/4 hieu > 0 PASS
```

Effect size:

```text
eta^2_raw  = 0.1239
eta^2_log  = 0.0639
eta^2_rank = 0.1315
CI95 raw   = [0.1190, 0.1282]
H2 PASS
```

Q4 exploratory:

```text
eta^2(s | z_bin)       raw=0.1239 log=0.0639 rank=0.1315
eta^2(s | u_bin)       raw=0.0211 log=0.0227 rank=0.0222
eta^2(s | z_bin*u_bin) raw=0.1349 log=0.0794 rank=0.1433
u tang them raw +0.0110
```

H7:

```text
err(z_bin)   = [0.11029 0.15739 0.18790 0.21504 0.23936]
q_hat(z_bin) = [63.962 88.753 105.870 119.739 132.654]
Spearman = 1.0000 PASS
```

Ket luan: tuoi `z` la bien dieu kien chinh hop le. `u` co them mot it thong tin
nhung khong du manh de thay thiet ke confirmatory.

Luu y truoc Lesson 21.3: bang risk-coverage trong file nay la IN-SAMPLE, vi
`q_hat` duoc fit tren toan bo 495 block roi danh gia tren chinh cac block do.
Con so dua vao paper phai la OUT-OF-SAMPLE: fit `q_hat` tren `D_calib`, danh
gia tren `D_test`.

## 2. Sensitivity Scores

`s_range`:

```text
q_hat = [78.241, 107.169, 129.088, 145.894, 160.674]
ratio = 2.054
4/4 hieu CI99.75 > 0
eta^2_raw/log/rank = 0.1229 / 0.0624 / 0.1242
H1 PASS, H2 PASS, H7 PASS
```

`s_maxabs`:

```text
q_hat = [60.743, 84.133, 99.234, 107.732, 121.239]
ratio = 1.996
4/4 hieu CI99.75 > 0
eta^2_raw/log/rank = 0.1359 / 0.0636 / 0.1409
H1 PASS, H2 PASS, H7 PASS
```

## 3. Measured Robustness

Sau Amendment 2, measured dung 2 bin tuoi va loai `z=0`.

```text
tensor X: (495, 2, 256)
q_hat = [68.152, 102.930]
bin1-bin0 = 34.543 CI99[32.417, 36.363] OK
H1 ratio = 1.510 PASS

eta^2_raw/log/rank = 0.0448 / 0.0171 / 0.0381
H2 FAIL nhe voi nguong 0.05

eta^2(s | u_bin)       raw=0.0498
eta^2(s | z_bin*u_bin) raw=0.0885
```

Measured xac nhan xu huong q_hat tang theo tuoi, nhung do phan giai tuoi 200 ms
qua tho nen H2 khong dat nguong confirmatory. Day la artifact cua do phan giai,
khong phai bang chung chong lai gia thuyet tuoi:

```text
offered eta2(z)/(k-1)  = 0.1239 / 4 = 0.0310
measured eta2(z)/(k-1) = 0.0448 / 1 = 0.0448
```

Tren moi bac tu do, measured `z` con manh hon offered. Khong ha nguong H2; ghi
FAIL nhe va dien giai bang artifact aliasing tuoi. Dung measured nhu robustness
check, khong dung de hieu chuan certificate chinh.

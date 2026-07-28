# PHASE 21.1 - Build Calibration Set Run

Ngay chay: 2026-07-28
Script: `cert/build_calib_set.py`

## 1. Offered Trace - Nguon Chinh

Lenh:

```bash
python -m cert.build_calib_set \
  --traces results/phase-20/rho_offered_long.csv \
           results/phase-20/rho_offered_long_s1.csv \
           results/phase-20/rho_offered_long_s2.csv \
           results/phase-20/rho_offered_long_s3.csv \
           results/phase-20/rho_offered_long_s4.csv \
  --out cert/calib_set_offered.parquet \
  --report-json results/phase-21/calib_set_offered_report.json
```

Ket qua:

```text
BANG: 718,000 hang | 505 block (495 block DAY) | 5 trace
SELF-CHECK: TAT CA PASS

err        = 0.1823300835654596
d_sla      = 0.07938857938718663
regret|err = 33.297649 ms
mean regret= 6.071163 ms

|err - 0.18233|   = 8.36e-08
|d_sla - 0.07939| = 1.42e-06
```

V5 khop Phase 20. Sai khac nam duoi nguong `1e-4`.

So block moi o Mondrian `(z_bin x u_bin)`:

```text
u_bin    0    1    2    3
z_bin
0      490  495  477  495
1      494  479  493  495
2      494  475  478  495
3      494  474  479  495
4      494  487  485  495
```

Khong co o vi pham `<9 block`.

Phan phoi `gap_twin`:

```text
p10=0.330  p25=0.777  p50=1.145  p75=19.404  p90=72.502  p99=150.524
```

Preview `q_hat` theo `z_bin`, `alpha=0.10`:

```text
 z_bin  n_blk   2q(s_maxabs,a/K)   q(s_range,a)   q(s_vs_a1,a)  triet tieu  gap_twin p50
     0    495            167.306         78.161         63.919        2.62x         1.145
     1    495            212.541        107.082         88.751        2.39x         1.145
     2    495            255.409        128.988        105.729        2.42x         1.145
     3    495            288.008        145.882        119.531        2.41x         1.145
     4    495            316.206        160.675        132.657        2.38x         1.145
```

Dien giai dung: khong doc `q_hat` mot minh, va khong so voi `gap_twin p50`.
Gate ACCEPT khi gap lon, nen thang doi chieu dung la duoi tren cua `gap_twin`.
Trace flow-level that co duoi gap nang hon pilot AR(1): `gap_twin p90 = 72.5`
ms, trong khi `q_hat_vs_a1(z0) = 63.9` ms. Vi vay trace that de hon pilot o
nghia co nhieu quyet dinh co gap du lon de gate co viec lam.

Risk-coverage preview chinh xac tu parquet:

```text
 eps(ms)  coverage   err|acc  d_sla|acc  regret|acc
       0    0.0543    0.0333    0.01120       0.436
       5    0.0613    0.0401    0.01538       0.573
      10    0.0677    0.0463    0.01829       0.640
      20    0.0872    0.0639    0.02583       0.936
      30    0.1118    0.0901    0.03811       1.285
      50    0.1587    0.1348    0.05767       2.165
      70    0.3487    0.1444    0.06196       2.998
     100    0.5479    0.1668    0.07258       4.270
  ANCHOR    1.0000    0.1820    0.07941       6.074
```

## 2. Measured Trace - Cross-Check Phu

Lenh:

```bash
python -m cert.build_calib_set \
  --traces results/phase-20/rho_measured_long.csv \
           results/phase-20/rho_measured_long_s1.csv \
           results/phase-20/rho_measured_long_s2.csv \
           results/phase-20/rho_measured_long_s3.csv \
           results/phase-20/rho_measured_long_s4.csv \
  --out cert/calib_set_measured.parquet \
  --report-json results/phase-21/calib_set_measured_report.json
```

Ket qua:

```text
BANG: 30,156 hang | 500 block (495 block DAY) | 5 trace
SELF-CHECK: TAT CA PASS

err        = 0.16929
d_sla      = 0.07276
regret|err = 29.855 ms
```

Canh bao quan trong: `dt=0.2s`, tuoi rang cua measured chi co do phan giai
thap. Sau Amendment 2, cac hang `z=0` bi loai va measured dung 2 bin tuoi:
`[0.10,0.30)` va `[0.30,0.70)`. Vi vay measured chi la robustness/cross-check,
khong lam nguon gate chinh cho Phase 21.

So block moi o measured:

```text
u_bin    0    1    2    3
z_bin
0      495  336  431  495
1      495  438  452  495
```

## 3. Artifacts

Parquet khong version hoa:

```text
cert/calib_set_offered.parquet   24.6 MB
cert/calib_set_measured.parquet   2.4 MB
```

Checksums:

```text
83ab9f4c9701fc275c698c43ac92ca7225efba5c1da6ae996e1dfed1cb3726f2  cert/calib_set_offered.parquet
5274f0dcfeed1e67c245b98cfae3baaabd155aa3ce538d222963980dd3b23627  cert/calib_set_measured.parquet
```

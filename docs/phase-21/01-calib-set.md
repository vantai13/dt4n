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

Dien giai nhanh: so voi pilot AR(1), trace flow-level that co duoi nang hon rat
nhieu. `q_hat` lon hon `gap_twin p50` khoang 56-116 lan, nen Lesson 21.3-21.4
can dac biet chu y risk-coverage theo `eps` va cac o `(z,u)`.

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
BANG: 34,000 hang | 30 block (20 block DAY) | 5 trace
SELF-CHECK: TAT CA PASS

err        = 0.14400
d_sla      = 0.06229
regret|err = 30.072 ms
```

Canh bao quan trong: `dt=0.2s`, tuoi rang cua chi con 3 muc khac nhau va co
clip bin tuoi. Vi vay measured chi la robustness/cross-check, khong lam nguon
gate chinh cho Phase 21.

O sparse tren measured:

```text
{'4_0': 4, '4_1': 4, '4_2': 4, '4_3': 4}
```

## 3. Artifacts

Parquet khong version hoa:

```text
cert/calib_set_offered.parquet   24.6 MB
cert/calib_set_measured.parquet   2.5 MB
```

Checksums:

```text
83ab9f4c9701fc275c698c43ac92ca7225efba5c1da6ae996e1dfed1cb3726f2  cert/calib_set_offered.parquet
139fa884772926c169347f50d27b8d1c8d60a29cc565f27e4abc9630c3bf666b  cert/calib_set_measured.parquet
```

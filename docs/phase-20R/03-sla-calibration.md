# SLA CALIBRATION -- Phase 20R.2

Ngay lap: 2026-08-04
Trang thai: sinh tu `python3 -m measurements.sla_calib_v2 --write`.

## Ket Qua Chinh

```text
mode     rho_bar sigma   p      T_delay  T_loss    w_loss  optviol clip   margin_ms  best-path
----------------------------------------------------------------------------------------------
cbr      0.700  0.0462  50.00    12.46  0.00000     1246  0.000  0.001     1.504  P1(1.00) <-- NGOAI BAND
cbr      0.850  0.0131  50.00    12.46  0.00000     1246  0.000  0.000     1.504  P1(1.00) <-- NGOAI BAND
cbr      0.925   --      --     --       --        --      --     --      --      LOAI: sigma_max_regime = 0 (het headroom den tran do tin cay)
cbr      0.960   --      --     --       --        --      --     --      --      LOAI: sigma_max_regime = 0 (het headroom den tran do tin cay)
poisson  0.700  0.0462  92.16    16.56  0.00042     1656  0.150  0.001     1.651  P1(0.87)
poisson  0.850  0.0480  89.53    24.24  0.00722     2424  0.150  0.001    10.640  P1(0.48)
poisson  0.925  0.0218  90.39    32.22  0.02921     3222  0.150  0.000    24.722  P1(0.53)
poisson  0.960  0.0096  91.17    36.56  0.04791     3656  0.150  0.000    23.829  P1(0.72)
h2       0.700  0.0462  90.22    28.61  0.02645     2861  0.150  0.001    26.499  P1(0.56)
h2       0.850  0.0480  89.33    40.21  0.11026     4021  0.150  0.001    95.019  P1(0.67)
h2       0.925  0.0218  88.67    45.16  0.16684     4516  0.150  0.000   112.682  P1(0.93)
h2       0.960  0.0096  87.99    47.23  0.19461     4723  0.150  0.000   121.097  P1(1.00)

8/12 o vao gate; 4 o PC1; max fixpoint rounds = 4; max clip = 0.0007.
```

## Opt Path Share

Day la kiem tra som xem bai toan co rong khong. Neu mot path thang 1.00
thi o do khong co bai toan quyet dinh cho gate chinh.

```text
mode     rho_bar  margin_mean  margin_p10   ti le duong nao la toi uu
cbr      0.700        1.504       1.504   P1=1.00
cbr      0.850        1.504       1.504   P1=1.00
poisson  0.700        1.651       0.365   P1=0.87, P3=0.09, P4=0.03
poisson  0.850       10.640       1.405   P1=0.48, P2=0.05, P3=0.32, P4=0.16
poisson  0.925       24.722       3.585   P1=0.53, P2=0.02, P3=0.36, P4=0.09
poisson  0.960       23.829       3.902   P1=0.72, P3=0.28
h2       0.700       26.499       3.801   P1=0.56, P2=0.03, P3=0.30, P4=0.10
h2       0.850       95.019      14.443   P1=0.67, P2=0.03, P3=0.25, P4=0.05
h2       0.925      112.682      27.753   P1=0.93, P3=0.07
h2       0.960      121.097      75.465   P1=1.00
```

Hinh: `docs/phase-20R/figures/opt_path_share.svg`.

## Dieu Chinh So Voi Pre-registration

Amendment 2 tach `LOSS_EXCHANGE = 0.01` khoi `T_loss`: `0.01` la ti
gia quy doi loss sang ms, con `T_loss` la nguong SLA duoc hieu chuan
tung o. Percentile `p` duoc giai nguoc bang bisection de dat
`TARGET_VIOL = 0.15`, thay vi co dinh p85.

Gate doc tai `z_max = 0.55 s`; cac diem `z in {1, 2, 4}` van bao cao
nhung danh dau ngoai suy.

## Provenance

```text
n=200000  dt=0.005  tau=1.000  a=0.9  seed=100
LOSS_EXCHANGE=0.0100  TARGET_VIOL=0.15  VIOL_BAND=[0.1, 0.25]
```

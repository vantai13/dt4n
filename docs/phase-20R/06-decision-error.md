# Phase 20R.5 -- Decision Error V2

Ngay ghi: 2026-08-06

Trang thai: fixed-z, sawtooth, CI95 cho `err_total` va `d_sla`,
constant-sigma deconfounding, tau sweep H6, va 5 hinh deu da chay xong.

## Implementation

Module va test:

```text
measurements/decision_error_v2.py
measurements/plot_decision_error_v2.py
test/test_phase20r_decision.py
```

`decision_error_v2.py` them:

```text
--sigma-override FLOAT
--tau FLOAT
--z-grid-scaled          # z = {0.10,0.30,0.55,1.00} * tau
--boot-metrics TEXT      # accepted; hien tai bootstrap tat ca metric
```

Raw fixed-z dung chung cua so danh gia `max(z_steps)` cho moi z, nen
`err_model` khong phu thuoc vao z va bat dang thuc tam giac duoc kiem dung
tren cung mot mau.

## Runtime

```text
fixed-z rerun             : 45.30 s
summary+sawtooth bootstrap: 89.97 s
constant-sigma run        : 41.25 s
tau sweep                 : 24.19 s, 23.00 s, 21.41 s
H7 calibrated/w2500/w0    : 76.80 s, 78.06 s, 51.36 s
plot 6 hinh               : 1.33 s
```

## Artifacts

```text
results/phase-20R/decision_error_by_age_by_regime.parquet
results/phase-20R/decision_error_by_age_summary.parquet
results/phase-20R/decision_error_sawtooth.json
results/phase-20R/decision_error_constant_sigma.parquet
results/phase-20R/decision_error_tau0.2.parquet
results/phase-20R/decision_error_tau1.0.parquet
results/phase-20R/decision_error_tau5.0.parquet
results/phase-20R/decision_error_unimodal.parquet
results/phase-20R/decision_error_w2500.parquet
results/phase-20R/decision_error_delay_only.parquet
```

## Fixed-Z Result

Tai `z = 0.55`:

```text
mode     rho_bar  sigma_rho  err_total  CI95 err_total       err_model  err_stale  d_sla   CI95 d_sla
cbr      0.700      0.0462      0.0000  [0.0000,0.0000]        0.0000     0.0000  0.0000 [0.0000,0.0000]
cbr      0.850      0.0131      0.0000  [0.0000,0.0000]        0.0000     0.0000  0.0000 [0.0000,0.0000]
h2       0.700      0.0462      0.3898  [0.3807,0.3991]        0.0220     0.3854  0.1457 [0.1404,0.1514]
h2       0.850      0.0480      0.3340  [0.3243,0.3438]        0.0275     0.3261  0.1134 [0.1086,0.1183]
h2       0.925      0.0218      0.1047  [0.0976,0.1121]        0.0136     0.0969  0.0268 [0.0244,0.0292]
h2       0.960      0.0096      0.0017  [0.0010,0.0025]        0.0008     0.0010  0.0001 [0.0000,0.0002]
poisson  0.700      0.0462      0.1879  [0.1777,0.1971]        0.0243     0.1758  0.0698 [0.0656,0.0740]
poisson  0.850      0.0480      0.4301  [0.4213,0.4388]        0.0137     0.4290  0.1819 [0.1768,0.1872]
poisson  0.925      0.0218      0.3756  [0.3672,0.3848]        0.0233     0.3784  0.1467 [0.1418,0.1519]
poisson  0.960      0.0096      0.2650  [0.2564,0.2733]        0.0155     0.2675  0.0900 [0.0859,0.0942]
```

D1 dat: `err(z=0)` nam trong `[0, 0.10]`, va o dau thap cua khoang.

D2 dat: `err_model / err_total < 0.50`. Trong cac o co error co y nghia, ti so
lon nhat la `h2@0.925 = 0.130`; `h2@0.960 = 0.469` nhung ca mau so va tu so
deu gan 0.

D3 dung mot phan: `poisson@0.700` nam trong nhom nhay voi `e_model`, nhung
khong cao nhat rieng; no gan bang `h2@0.925`.

## Consistency Checks

Bat dang thuc tam giac tren raw fixed-z:

```text
|err_stale - err_model| <= err_total <= err_stale + err_model
so hang = 90
vi pham = 0
max std(err_model across z) = 0.0
err_stale > err_total = 14 / 90
```

`err_stale > err_total` khong phai bug. No la cancellation: co thoi diem twin
cu lech khoi model tuoi 0, nhung lai trung voi measured truth. Do do khong
duoc cong `err_model + err_stale` nhu hai loi doc lap.

## G2: d_sla CI

Threshold prereg: `d_sla_ci95_lo >= 0.03` cho o dung de doc G1/G2/G3.

Tai `z = 0.55`, cac o PASS G2:

```text
h2      0.700  lo=0.1404
h2      0.850  lo=0.1086
poisson 0.700  lo=0.0656
poisson 0.850  lo=0.1768
poisson 0.925  lo=0.1418
poisson 0.960  lo=0.0859
```

Cac o FAIL G2:

```text
h2      0.925  lo=0.0244
h2      0.960  lo=0.0000
```

## Sawtooth Operational Point

```text
age_mean_s = 0.3025
age_min_s  = 0.055
age_max_s  = 0.55
```

Summary sawtooth:

```text
mode     rho_bar  err_total  CI95 err_total       d_sla   CI95 d_sla
cbr      0.700      0.0000  [0.0000,0.0000]      0.0000 [0.0000,0.0000]
cbr      0.850      0.0000  [0.0000,0.0000]      0.0000 [0.0000,0.0000]
h2       0.700      0.2962  [0.2887,0.3034]      0.0898 [0.0856,0.0938]
h2       0.850      0.2551  [0.2471,0.2623]      0.0699 [0.0665,0.0737]
h2       0.925      0.0805  [0.0745,0.0866]      0.0165 [0.0146,0.0184]
h2       0.960      0.0015  [0.0008,0.0023]      0.0000 [-0.0001,0.0002]
poisson  0.700      0.1459  [0.1382,0.1525]      0.0449 [0.0417,0.0481]
poisson  0.850      0.3271  [0.3196,0.3349]      0.1155 [0.1112,0.1200]
poisson  0.925      0.2832  [0.2756,0.2912]      0.0937 [0.0896,0.0979]
poisson  0.960      0.1986  [0.1917,0.2056]      0.0575 [0.0539,0.0612]
```

## Prediction Check

So voi prediction da ky tai `z = 0.55`:

```text
mode     rho_bar  predicted  measured  ratio   abs_gap
h2       0.700      0.3892    0.3898   1.002   0.0007
h2       0.850      0.3236    0.3340   1.032   0.0104
h2       0.925      0.0898    0.1047   1.166   0.0149
h2       0.960      0.0003    0.0017   5.072   0.0013
poisson  0.700      0.1857    0.1879   1.012   0.0022
poisson  0.850      0.4378    0.4301   0.982   0.0077
poisson  0.925      0.3921    0.3756   0.958   0.0165
poisson  0.960      0.2629    0.2650   1.008   0.0021
```

`h2@0.960` duoc doc theo Amendment 6: prediction `< 0.02`, nen dung absolute
law. `abs_gap = 0.0013 <= 0.02`, PASS. Cac o con lai co ratio trong khoang
da ky.

## Constant-Sigma Deconfounding

Run:

```bash
python3 -m measurements.decision_error_v2 \
  --run-fixed \
  --sigma-override 0.0096 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_constant_sigma.parquet
```

Tai `z = 0.55`:

```text
mode     rho_bar  err_total  err_model  err_stale  d_sla
cbr      0.700      0.0000     0.0000     0.0000  0.0000
cbr      0.850      0.0000     0.0000     0.0000  0.0000
h2       0.700      0.1672     0.0357     0.1496  0.0026
h2       0.850      0.0058     0.0015     0.0046  0.0003
h2       0.925      0.0011     0.0004     0.0008  0.0001
h2       0.960      0.0017     0.0008     0.0010  0.0001
poisson  0.700      0.0000     0.0000     0.0000  0.0000
poisson  0.850      0.2870     0.0378     0.2820  0.0888
poisson  0.925      0.2905     0.0403     0.2954  0.0923
poisson  0.960      0.2650     0.0155     0.2675  0.0900
```

Ket luan: confound `sigma_rho` la that, nhung khong giai thich het H3. Du doan
truoc khi chay constant-sigma noi `poisson@0.960` se lon nhat; du doan do BI
BAC BO. Thuc te `poisson` co dang dai/dinh: nho tai 0.70, lon tai 0.85-0.925,
roi giam tai 0.960. `h2` van giam manh, gan nhu ranking bi khoa o tai cao.

Do do `20R-G4` khong duoc ghi PASS. G4/H3 nhu da tien dang ky FAIL; phan
constant-sigma chi la diagnostic dan den Amendment 8/H7.

## H7 Loss-Driven Unimodal Mechanism

Amendment 8 duoc commit truoc khi chay tai `1d78812`. Run H7 khong dung
Mininet; no dung `truth_table.parquet` da do, `sigma_rho = 0.0096`, va them
`rho_bar = 0.65, 0.78, 0.88`.

Tai `z = 0.55`:

```text
mode     rho_bar  w=hieu chuan  w=2500   w=0 delay-only
h2       0.650       0.2103      0.2101      0.0000
h2       0.700       0.1672      0.1606      0.0000
h2       0.780       0.0431      0.0391      0.0000
h2       0.850       0.0058      0.0053      0.0000
h2       0.880       0.0041      0.0037      0.0000
h2       0.925       0.0011      0.0011      0.0000
h2       0.960       0.0017      0.0016      0.0000
poisson  0.650       0.0000      0.0000      0.0000
poisson  0.700       0.0000      0.0000      0.0000
poisson  0.780       0.0936      0.1300      0.0000
poisson  0.850       0.2870      0.2887      0.0016
poisson  0.880       0.3005      0.2979      0.0050
poisson  0.925       0.2905      0.2857      0.0080
poisson  0.960       0.2650      0.2588      0.0078
```

H7 read:

```text
H7a/H7b poisson: PASS. Dung mot cuc dai noi bo tai rho_bar=0.88.
H7c h2        : PARTIAL. Err tang khi giam 0.70 -> 0.65, nen dinh nam ben
                trai 0.70; nhung luoi chua co diem thap hon de thay su giam
                sau dinh.
H7d delay-only: PASS. max err_total(w=0) = 0.007979 < 0.02.
```

`w_loss = 2500` khong lam thay doi dang co che o cac o da ky; tren extended
grid no lam `poisson@0.78` tang them `0.0364`, tuc anh huong vi tri/suon trai
cua dai chuyen tiep. Nhung khi `w_loss = 0`, err sup xuong duoi `0.008` o moi
o, nen co che chinh van ro: decision flips den tu so hang loss, khong phai
delay.

## H6 Tau Scaling

Run:

```bash
for TAU in 0.2 1.0 5.0; do
  python3 -m measurements.decision_error_v2 --run-fixed \
    --tau "$TAU" \
    --z-grid-scaled \
    --n 200000 \
    --seeds 101,102,103 \
    --out "results/phase-20R/decision_error_tau${TAU}.parquet"
done
```

Tai `z/tau = 0.55`:

```text
mode     rho_bar    tau=0.2  tau=1.0  tau=5.0
cbr      0.700       0.0000   0.0000   0.0000
cbr      0.850       0.0000   0.0000   0.0000
h2       0.700       0.3925   0.3953   0.4144
h2       0.850       0.3373   0.3345   0.3467
h2       0.925       0.0979   0.1004   0.1086
h2       0.960       0.0019   0.0019   0.0019
poisson  0.700       0.1861   0.1854   0.1977
poisson  0.850       0.4325   0.4347   0.4515
poisson  0.925       0.3800   0.3830   0.4003
poisson  0.960       0.2638   0.2628   0.2689
```

Max spread tren toan bo luoi `(mode, rho_bar, z/tau)`:

```text
max_spread = 0.029201 < 0.05
worst = poisson@0.925, z/tau=1.0, [0.4624, 0.4916]
```

H6 PASS.

## Figures

Matplotlib da duoc cai va hinh da sinh:

```text
docs/phase-20R/figures/decision_error_pred_vs_measured_z055.png
docs/phase-20R/figures/decision_error_decomposition_vs_z.png
docs/phase-20R/figures/decision_error_d_sla_ci_z055.png
docs/phase-20R/figures/decision_error_constant_sigma_z055.png
docs/phase-20R/figures/decision_error_tau_scaling.png
docs/phase-20R/figures/decision_error_loss_mechanism_z055.png
```

## Threats

`clip_fraction` duoc ghi trong artifact. O vuot 1%:

```text
h2      rho_bar=0.960  max_clip ~= 0.037
poisson rho_bar=0.960  max_clip ~= 0.037
```

Day la mep tren cua truth table, chu yeu link `ad`/`bd`. Khong dung de sua
nguoc prediction, nhung phai ghi la threat khi dien giai cac o `rho_bar=0.960`.

`20R-G6` end-to-end additivity khong nam trong artifact decision-error v2 nay.
Khong duoc danh dau PASS cho G6 neu khong co artifact DC1 rieng.

## Re-run Trong Tmux

```bash
cd /home/ubuntu/dt4n
tmux new -s p20r5
export PYTHONPATH="$PWD"

python3 -m measurements.decision_error_v2 --control \
  2>&1 | tee logs/20r5_00_controls.log

python3 -m measurements.decision_error_v2 \
  --run-fixed \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_by_age_by_regime.parquet \
  2>&1 | tee logs/20r5_02_fixed_rerun.log

python3 -m measurements.decision_error_v2 \
  --summarize-fixed \
  --run-sawtooth \
  --boot-metrics err_total,d_sla \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --n-boot 2000 \
  --summary-out results/phase-20R/decision_error_by_age_summary.parquet \
  --sawtooth-out results/phase-20R/decision_error_sawtooth.json \
  2>&1 | tee logs/20r5_03_summary_sawtooth_rerun.log

python3 -m measurements.decision_error_v2 \
  --run-fixed \
  --sigma-override 0.0096 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_constant_sigma.parquet \
  2>&1 | tee logs/20r5_04_constant_sigma.log

for TAU in 0.2 1.0 5.0; do
  python3 -m measurements.decision_error_v2 --run-fixed \
    --tau "$TAU" \
    --z-grid-scaled \
    --n 200000 \
    --seeds 101,102,103 \
    --out "results/phase-20R/decision_error_tau${TAU}.parquet"
done 2>&1 | tee logs/20r5_05_tau_sweep.log

python3 -m measurements.plot_decision_error_v2 \
  2>&1 | tee logs/20r5_06_plots.log

python3 -m measurements.decision_error_v2 --run-fixed \
  --sigma-override 0.0096 \
  --rho-bar-extra 0.65,0.78,0.88 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_unimodal.parquet \
  2>&1 | tee logs/20r5_07_unimodal.log

python3 -m measurements.decision_error_v2 --run-fixed \
  --sigma-override 0.0096 \
  --w-loss-override 2500 \
  --rho-bar-extra 0.65,0.78,0.88 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_w2500.parquet \
  2>&1 | tee logs/20r5_08_w2500.log

python3 -m measurements.decision_error_v2 --run-fixed \
  --sigma-override 0.0096 \
  --w-loss-override 0 \
  --rho-bar-extra 0.65,0.78,0.88 \
  --n 200000 \
  --seeds 101,102,103 \
  --out results/phase-20R/decision_error_delay_only.parquet \
  2>&1 | tee logs/20r5_09_delay_only.log

python3 -m measurements.plot_decision_error_v2 \
  2>&1 | tee logs/20r5_10_plots_with_h7.log
```

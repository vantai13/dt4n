# Phase 20R.5 -- Decision Error V2

Ngay ghi: 2026-08-05

Trang thai hien tai: controls PASS, fixed-z grid 5 seed da chay xong, paired
block bootstrap da sinh CI95, va sawtooth operational point da chay xong.
Figures va final gate write-up se lam o buoc tiep theo.

## Implementation

Module moi:

```text
measurements/decision_error_v2.py
test/test_phase20r_decision.py
```

Golden tests:

```text
G-D1 TruthTable.delay_loss tai dung muc luoi tra ve dung gia tri parquet
G-D2 clip_fraction ghi dung ti le ngoai mien
G-D3 e_model + e_stale == total voi atol 1e-9
G-D4 check_z_grid raise khi dt = 0.2 lam trung lag
```

Ket qua:

```text
4 passed
```

## Rho Source

Mac dinh cua `decision_error_v2.py` la `--rho-source calibration_ar1`, dung
cung `measurements.sla_calib_v2.ar1_matrix` voi calibration va prediction da
ky. Diagnostic `--rho-source scalar_ou` duoc giu lai nhung khong dung cho
artifact chinh.

Ly do: Q7 trong preregistration da canh bao neu moi link cung mot rho common
mode thi ranking bi khoa va `err ~= 0` nhan tao. Smoke voi scalar common-mode
da tai hien dung bay nay.

## Controls

Command:

```bash
python3 -m measurements.decision_error_v2 --control
```

Output:

```text
NC1b_max_abs              : 0.0
NC2_min                   : 0.74692
NC2_max                   : 0.75124
NC2_pass_0p72_0p78         : true
PC1_cbr_one_step_churn_max : 0.0
```

Ket luan: doi chung bat buoc PASS. `NC1b = 0.000000` tuyet doi, nen thua
do khong co loi ghep bang/off-by-one co ban. `NC2` nam dung quanh `1 - 1/K`.

Artifact:

```text
results/phase-20R/controls.json
```

## Fixed-Z Grid

Command da chay:

```bash
python3 -m measurements.decision_error_v2 \
  --run-fixed \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_by_age_by_regime.parquet
```

Runtime thuc te: `37.95 s`.

Artifact:

```text
results/phase-20R/decision_error_by_age_by_regime.parquet
results/phase-20R/decision_error_by_age_summary.parquet
```

Kich thuoc:

```text
rows  = 450
cells = 10
seeds = 5
z     = 9
```

Ket qua trung binh tai `z = 0`:

```text
mode     rho_bar  err_total  err_model  err_stale  d_sla
cbr      0.700      0.0000     0.0000     0.0000   0.0000
cbr      0.850      0.0000     0.0000     0.0000   0.0000
h2       0.700      0.0220     0.0220     0.0000  -0.0015
h2       0.850      0.0276     0.0276     0.0000  -0.0006
h2       0.925      0.0136     0.0136     0.0000  -0.0011
h2       0.960      0.0008     0.0008     0.0000  -0.0000
poisson  0.700      0.0243     0.0243     0.0000   0.0006
poisson  0.850      0.0137     0.0137     0.0000   0.0012
poisson  0.925      0.0232     0.0232     0.0000   0.0056
poisson  0.960      0.0155     0.0155     0.0000   0.0051
```

Ket qua trung binh tai `z = 0.55`:

```text
mode     rho_bar  err_total  err_model  err_stale  d_sla
cbr      0.700      0.0000     0.0000     0.0000   0.0000
cbr      0.850      0.0000     0.0000     0.0000   0.0000
h2       0.700      0.3899     0.0220     0.3855   0.1457
h2       0.850      0.3344     0.0276     0.3265   0.1134
h2       0.925      0.1048     0.0136     0.0971   0.0268
h2       0.960      0.0017     0.0008     0.0010   0.0001
poisson  0.700      0.1879     0.0243     0.1758   0.0699
poisson  0.850      0.4301     0.0137     0.4290   0.1820
poisson  0.925      0.3757     0.0232     0.3784   0.1467
poisson  0.960      0.2652     0.0155     0.2676   0.0901
```

Invariant:

```text
max sd(err_model across z) = 0.0
```

Paired block bootstrap:

```text
block_s   = 5.0
block_len = 1000 samples
n_boot    = 2000
```

Tai `poisson@0.850, z=0.55`, block CI half-width la `0.00879`, trong khi
naive iid binomial half-width chi `0.00097`; block CI rong hon `9.06x`, dung
huong voi du doan "bootstrap thuong hep gia tao".

Summary fixed-z tai `z = 0.55`:

```text
mode     rho_bar  err_total  CI95 err_total     err_model  err_stale  d_sla   CI95 d_sla
cbr      0.700      0.0000   [0.0000,0.0000]      0.0000     0.0000  0.0000 [0.0000,0.0000]
cbr      0.850      0.0000   [0.0000,0.0000]      0.0000     0.0000  0.0000 [0.0000,0.0000]
h2       0.700      0.3898   [0.3807,0.3991]      0.0220     0.3854  0.1457 [0.1404,0.1514]
h2       0.850      0.3340   [0.3243,0.3438]      0.0275     0.3261  0.1134 [0.1086,0.1183]
h2       0.925      0.1047   [0.0976,0.1121]      0.0136     0.0969  0.0268 [0.0244,0.0292]
h2       0.960      0.0017   [0.0010,0.0025]      0.0008     0.0010  0.0001 [0.0000,0.0002]
poisson  0.700      0.1879   [0.1777,0.1971]      0.0243     0.1758  0.0698 [0.0656,0.0740]
poisson  0.850      0.4301   [0.4213,0.4388]      0.0137     0.4290  0.1819 [0.1768,0.1872]
poisson  0.925      0.3756   [0.3672,0.3848]      0.0233     0.3784  0.1467 [0.1418,0.1519]
poisson  0.960      0.2650   [0.2564,0.2733]      0.0155     0.2675  0.0900 [0.0859,0.0942]
```

## Sawtooth Operational Point

Command da chay:

```bash
python3 -m measurements.decision_error_v2 \
  --run-sawtooth \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --n-boot 2000 \
  --sawtooth-out results/phase-20R/decision_error_sawtooth.json
```

Runtime khi chay chung voi fixed summary: `85.61 s`.

Artifact:

```text
results/phase-20R/decision_error_sawtooth.json
```

AoI sawtooth:

```text
age_mean_s = 0.3025
age_min_s  = 0.055
age_max_s  = 0.55
```

Summary sawtooth:

```text
mode     rho_bar  err_total  CI95 err_total     err_model  err_stale  d_sla   CI95 d_sla
cbr      0.700      0.0000   [0.0000,0.0000]      0.0000     0.0000  0.0000 [0.0000,0.0000]
cbr      0.850      0.0000   [0.0000,0.0000]      0.0000     0.0000  0.0000 [0.0000,0.0000]
h2       0.700      0.2962   [0.2887,0.3034]      0.0220     0.2924  0.0898 [0.0856,0.0938]
h2       0.850      0.2551   [0.2471,0.2623]      0.0276     0.2487  0.0699 [0.0665,0.0737]
h2       0.925      0.0805   [0.0745,0.0866]      0.0136     0.0747  0.0165 [0.0146,0.0184]
h2       0.960      0.0015   [0.0008,0.0023]      0.0008     0.0010  0.0000 [-0.0001,0.0002]
poisson  0.700      0.1459   [0.1382,0.1525]      0.0243     0.1361  0.0449 [0.0417,0.0481]
poisson  0.850      0.3271   [0.3196,0.3349]      0.0137     0.3257  0.1155 [0.1112,0.1200]
poisson  0.925      0.2832   [0.2756,0.2912]      0.0232     0.2848  0.0937 [0.0896,0.0979]
poisson  0.960      0.1986   [0.1917,0.2056]      0.0155     0.2004  0.0575 [0.0539,0.0612]
```

## Prediction Check

So voi `02-prediction.md` tai `z = 0.55`, cac o chinh khop rat sat:

```text
poisson 0.700  measured=0.1879  predicted=0.1594  ratio=1.18
poisson 0.850  measured=0.4301  predicted=0.4364  ratio=0.99
poisson 0.925  measured=0.3756  predicted=0.3928  ratio=0.96
poisson 0.960  measured=0.2650  predicted=0.2622  ratio=1.01
h2      0.700  measured=0.3898  predicted=0.3889  ratio=1.00
h2      0.850  measured=0.3340  predicted=0.3235  ratio=1.03
h2      0.925  measured=0.1047  predicted=0.0902  ratio=1.16
```

`h2@0.960` co ratio `5.07x` vi prediction gan 0 (`0.0003`) va measured cung
gan 0 (`0.0017`). Day la near-zero denominator, absolute gap `0.0014`, khong
phai gate-driving discrepancy.

## Clip Threats

`clip_fraction` duoc ghi trong artifact. O vuot 1% hien tai:

```text
h2      rho_bar=0.960  max_clip=0.0372
poisson rho_bar=0.960  max_clip=0.0372
```

Day la clip tai mep tren cua truth table, chu yeu link `ad`/`bd`, do bang tra
20R ket thuc o `rho=1.04` trong khi quang van hanh co the cham sat `1.05`.
Can ghi vao Threats cua final `06-decision-error.md` khi hoan tat sawtooth va
bootstrap. Khong dung de sua nguoc `02-prediction.md`.

## Re-run

Neu muon chay lai trong tmux:

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
  2>&1 | tee logs/20r5_01_fixed.log

python3 -m measurements.decision_error_v2 \
  --summarize-fixed \
  --run-sawtooth \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --n-boot 2000 \
  --summary-out results/phase-20R/decision_error_by_age_summary.parquet \
  --sawtooth-out results/phase-20R/decision_error_sawtooth.json \
  2>&1 | tee logs/20r5_02_summary_sawtooth.log
```

Runtime uoc tinh tren may nay:

```text
controls          : < 1 s
fixed grid        : ~38 s
summary+sawtooth  : ~86 s
```

# Phase 20R.5 -- Decision Error V2

Ngay ghi: 2026-08-05

Trang thai hien tai: Day 1 controls PASS va fixed-z grid 5 seed da chay xong.
Sawtooth operational point, paired block bootstrap, figures, va final gate
write-up se lam o buoc tiep theo.

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
```

Runtime uoc tinh tren may nay:

```text
controls  : < 1 s
fixed grid: ~38 s
```

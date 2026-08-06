# Phase 20R -- Gate Decision

Ngay ghi: 2026-08-06

Ket luan ngan: decision-error gates dat voi ghi chu quan trong ve H3/G4. H6
PASS. `20R-G6` end-to-end additivity khong co artifact trong lesson nay, nen
khong duoc danh dau PASS neu chua co DC1 rieng.

## Gate Table

```text
Gate    Status          Evidence
G1      PASS            poisson@0.700, z=0.55: err=0.187870 in [0.05,0.40]
G2      PASS            same cell: d_sla_ci95_lo=0.065583 >= 0.03
G3      PASS            same cell: Spearman(err,z)=1.0, exact p=0.002778
G4      PASS/WEAK       Amendment 7, constant-sigma poisson: Spearman(err,rho)=0.4 > 0
G5      PASS            NC1b=0, NC2 in [0.74692,0.75124], PC1 cbr=0
G6      NOT EVALUATED   no end-to-end additivity DC1 artifact in decision-error v2
G7      PASS            CI95 from paired block bootstrap, not naive iid SE
H6      PASS            max spread across tau at fixed z/tau = 0.029201 < 0.05
```

## Qualification On G4

Operational calibration does not support the original monotonic story:

```text
poisson: 0.1879, 0.4301, 0.3756, 0.2650
h2     : 0.3898, 0.3340, 0.1047, 0.0017
rho_bar: 0.700,  0.850,  0.925,  0.960
```

Amendment 7 correctly identifies a `sigma_rho` confound. Constant-sigma partly
rescues G4 by the prereg Spearman metric:

```text
poisson constant-sigma: 0.0000, 0.2870, 0.2905, 0.2650
Spearman(err,rho_bar) = 0.4 > 0
```

But strict monotonic H3' is not clean because `rho_bar=0.960` drops below
`0.925`. Report this as a qualified/weak G4 pass, not as a clean monotonic law.

## Prediction Decision

Prediction at `z=0.55` matched the measured run tightly:

```text
h2      0.700  ratio=1.002
h2      0.850  ratio=1.032
h2      0.925  ratio=1.166
poisson 0.700  ratio=1.012
poisson 0.850  ratio=0.982
poisson 0.925  ratio=0.958
poisson 0.960  ratio=1.008
```

`h2@0.960` is handled by Amendment 6 near-zero absolute law:

```text
predicted=0.000330, measured=0.001675, abs_gap=0.001345 <= 0.02
```

## Final Read

Phase 20R.5 establishes the main decision-error result: measured truth, paired
block CI, sawtooth operational point, prediction validation, deconfounded sigma
diagnostic, and tau scaling. The paper claim should emphasize:

```text
1. staleness dominates model error in substantive cells;
2. model and stale error can cancel, so do not add them;
3. operational err is not monotonic in rho_bar because feasible sigma shrinks;
4. z/tau scaling is empirically stable within 0.029 absolute spread.
```


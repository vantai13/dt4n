# Phase G1-A result — estimator validation

Run date: 2026-08-29 UTC.  The first run followed tag `phase-G-g1a-prereg`
at commit `6c43ac44`.  No experimental data was read.

## Verdict

**G1-0 FAIL.  Do not apply the supplied estimators to Phase D or Mininet data.**

The signal-fraction estimator passed all five locked cells.  The raw
first-difference correlation did not recover `rho_epsilon=1` once residual
signal leakage became material.

| sf true | sf hat | sf bias | rho eps true | raw rho hat | raw theory | estimated leakage | sf gate | rho gate |
|---:|---:|---:|---:|---:|---:|---:|:---:|:---:|
| 0.30 | 0.298 | 0.992 | 1.000 | 0.973 | 0.973 | 0.025 | PASS | PASS |
| 0.50 | 0.498 | 0.996 | 1.000 | 0.939 | 0.939 | 0.057 | PASS | PASS |
| 0.70 | 0.696 | 0.994 | 1.000 | 0.869 | 0.869 | 0.121 | PASS | FAIL |
| 0.85 | 0.853 | 1.004 | 1.000 | 0.733 | 0.732 | 0.257 | PASS | FAIL |
| 0.95 | 0.950 | 1.000 | 1.000 | 0.449 | 0.449 | 0.516 | PASS | FAIL |

The maximum absolute difference between measured raw correlation and its
attenuation theory was only `0.000584`.  Thus the synthetic generator behaves
as designed: the raw statistic estimates the *mixture after high-pass
attenuation*, not `rho_epsilon` itself when signal leakage is non-negligible.

The preregistered leakage validity threshold `<0.20` is also too loose for the
locked `abs(rho_hat-1)<=0.10` gate.  In the equal-variance, `r_true=0` control,
`rho_hat=1/(1+leakage)`; guaranteeing `rho_hat>=0.90` requires true leakage at
most `1/9 = 0.111`.  The `sf=0.70` cell demonstrates the mismatch.

## Resource use and artifact

- Elapsed: `0:03.66`.
- Maximum RSS: `40,892 KiB`.
- Artifact: `results/SMOKE/phase-G/g1a_estimator_validation.json`.
- SHA256: `fd33dc8145060132719f289141a1c6e2d1d6fa0d42a4aac5b08bf7f6d161f15c`.

G1-B and G1-C remain unopened.  In addition to this estimator failure,
`results/DATA_MANIFEST.json::doi` remains null, so any branch that creates new
RAW Mininet data is custody-blocked.

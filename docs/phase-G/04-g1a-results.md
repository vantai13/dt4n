# Phase G1-A historical raw-estimator receipt — reclassified by G-A002

Run date: 2026-08-29 UTC.  The first run followed tag `phase-G-g1a-prereg`
at commit `6c43ac44`.  No experimental data was read.

## Amended verdict

The original automated verdict was G1-0 FAIL under the original preregistration.
G-A002 preserves that receipt but separates three findings:

- G1-0a: signal-fraction estimator PASS 5/5.
- G1-0b: `MODEL_VALIDATED`; raw attenuation theory predicted all five points
  with maximum error `0.000584`.
- Raw first-difference correlation:
  `INSUFFICIENT_BY_DESIGN` as a direct `rho_epsilon` estimator.  It remains a
  positive control for the error model and is replaced by the two-band
  estimator validated in `06-g1a-G-A002-results.md`.

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

Tightening leakage to `1/9` is not a viable repair: it implies approximately
`sf<=0.63` at this `tau/dt`, while the intended operating gate requires
`sf>=0.85`.  The viable regions do not intersect.  G-A002 instead solves the
level and difference equations jointly.

## Resource use and artifact

- Elapsed: `0:03.66`.
- Maximum RSS: `40,892 KiB`.
- Artifact: `results/SMOKE/phase-G/g1a_estimator_validation.json`.
- SHA256: `fd33dc8145060132719f289141a1c6e2d1d6fa0d42a4aac5b08bf7f6d161f15c`.

At the time of this historical run G1-B and G1-C remained unopened.  G-A002
subsequently closed synthetic G1-0, but `results/DATA_MANIFEST.json::doi`
remains null, so any branch that creates new RAW Mininet data is still
custody-blocked.

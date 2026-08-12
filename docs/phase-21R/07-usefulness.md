# Lesson 21R.6 -- usefulness_v2.py

Ngay hoan thanh: 2026-08-12

## Artifact

Source:

```text
cert/usefulness_v2.py
test/test_phase21r_usefulness.py
```

Results:

```text
results/phase-21R/usefulness_poisson_0.925.json
results/phase-21R/usefulness_poisson_0.850.json
results/phase-21R/usefulness_h2_0.700.json
results/phase-21R/usefulness_cbr_0.700.json
```

## Commands

```bash
/tmp/dt4n-venv/bin/python -m cert.usefulness_v2 --calib results/phase-21R/calib_set_poisson_0.925.parquet --out results/phase-21R/usefulness_poisson_0.925.json --anchor-err 0.2208351459330263 --eps-regret 3.2222446816474113
/tmp/dt4n-venv/bin/python -m cert.usefulness_v2 --calib results/phase-21R/calib_set_poisson_0.850.parquet --out results/phase-21R/usefulness_poisson_0.850.json --anchor-err 0.2190620484126627 --eps-regret 2.4243596038611255
/tmp/dt4n-venv/bin/python -m cert.usefulness_v2 --calib results/phase-21R/calib_set_h2_0.700.parquet --out results/phase-21R/usefulness_h2_0.700.json --anchor-err 0.12725899924495848 --eps-regret 2.861395300891912
/tmp/dt4n-venv/bin/python -m cert.usefulness_v2 --calib results/phase-21R/calib_set_cbr_0.700.parquet --out results/phase-21R/usefulness_cbr_0.700.json --anchor-err 0.0 --eps-regret 1.2456355455410035
```

## Definition

Selective prediction gate:

```text
accept <=> m_hat >= kappa * q_hat(z_bin)
```

`kappa=0` accepts all rows and defines the test-set anchor. `kappa=1` is the C1
certificate. `kappa=2` is the historical v7-style separated-interval point.

## Main curve

`poisson@0.925`, test set only, `n=499967`.

| kappa | acceptance | err\|accept | err/anchor | d_sla\|accept | regret\|accept | err\|reject |
|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 1.00000 | 0.222399 | 1.000 | 0.060752 | 1.7675 | -- |
| 0.25 | 0.78784 | 0.159862 | 0.719 | 0.039620 | 1.1190 | 0.45463 |
| 0.50 | 0.58551 | 0.103373 | 0.465 | 0.023434 | 0.6551 | 0.39054 |
| 0.75 | 0.41270 | 0.063964 | 0.288 | 0.013662 | 0.3740 | 0.33373 |
| 1.00 | 0.28354 | 0.032992 | 0.148 | 0.005904 | 0.1762 | 0.29736 |
| 1.25 | 0.18716 | 0.015784 | 0.071 | 0.002276 | 0.0804 | 0.26997 |
| 1.50 | 0.12114 | 0.007380 | 0.033 | 0.000908 | 0.0293 | 0.25204 |
| 2.00 | 0.04845 | 0.000867 | 0.004 | 0.000000 | 0.0019 | 0.23368 |
| 3.00 | 0.00747 | 0.000000 | 0.000 | 0.000000 | 0.0000 | 0.22407 |

H7 passes with 5 qualifying points. The highest-acceptance qualifying point is
`kappa=0.50`, with acceptance `0.5855` and risk ratio `0.4648`.

## G12 and discrimination

```text
G12 at kappa=1: acceptance = 0.28354 <= 0.90, PASS
AURC = 0.091333
```

The gate is informative:

| kappa | err\|accept | err\|reject | reject/accept |
|---:|---:|---:|---:|
| 0.25 | 0.159862 | 0.454625 | 2.84x |
| 1.00 | 0.032992 | 0.297358 | 9.01x |
| 2.00 | 0.000867 | 0.233679 | 269.56x |

## Post-selection diagnostics

At `kappa=1`:

```text
violation_marginal             = 0.091316
violation_given_accept         = 0.121435
violation_inflation            = 1.3298
p_mtrue_neg_given_accept       = 0.030741
median_slack_given_accept      = 7.6171 ms
corr_score_vs_gap              = 0.1122
```

Conformal coverage is violated after selection, but the operational decision
certificate still holds with a wide margin. This distinction must be explicit
in the paper.

## Cross-cell summary

| Cell | H7 | Best kappa | Acceptance | err\|accept | Risk ratio | G12 at k=1 | PC1 |
|---|---|---:|---:|---:|---:|---|---|
| poisson@0.925 | PASS | 0.50 | 0.5855 | 0.1034 | 0.465 | PASS | N/A |
| poisson@0.850 | PASS | 0.50 | 0.5490 | 0.0943 | 0.427 | PASS | N/A |
| h2@0.700 | PASS | 0.50 | 0.7467 | 0.0532 | 0.421 | PASS | N/A |
| cbr@0.700 | N/A | -- | 1.0000 | 0.0000 | -- | N/A | PASS |

G10 passes because all three non-degenerate cells pass H7. PC1 passes because
the degenerate `cbr@0.700` cell accepts all decisions with zero error.

## C2

At `poisson@0.925`, `eps_regret=3.2222 ms` and:

```text
regret|accept(kappa=1) = 0.1762 ms
```

C2 is non-binding at the certificate point. The explicit kappa mapping is:

```text
B1 0.7219
B2 0.7939
B3 0.8360
B4 0.8675
```

## Test

Targeted:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_usefulness.py -q
```

```text
13 passed
```

Phase 21R related:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_usefulness.py test/test_phase21r_conformal.py test/test_phase21r_errage.py test/test_phase21r_decomp.py test/test_phase21r_calib.py test/test_phase21r_margin.py -q
```

```text
70 passed
```

Full suite:

```bash
/tmp/dt4n-venv/bin/python -m pytest -q
```

```text
604 passed, 1 skipped, 2 warnings in 157.88s (0:02:37)
```

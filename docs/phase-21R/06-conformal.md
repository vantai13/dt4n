# Lesson 21R.5 -- conformal_v2.py

Ngay hoan thanh: 2026-08-12

## Artifact

Source:

```text
cert/conformal_v2.py
test/test_phase21r_conformal.py
```

Results:

```text
results/phase-21R/conformal_poisson_0.925.json
results/phase-21R/conformal_poisson_0.850.json
results/phase-21R/conformal_h2_0.700.json
results/phase-21R/conformal_cbr_0.700.json
```

## Test

Targeted:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_conformal.py -q
```

```text
15 passed
```

Phase 21R related:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_conformal.py test/test_phase21r_errage.py test/test_phase21r_decomp.py test/test_phase21r_calib.py test/test_phase21r_margin.py -q
```

```text
57 passed
```

Full suite:

```bash
/tmp/dt4n-venv/bin/python -m pytest -q
```

```text
591 passed, 1 skipped, 2 warnings in 159.38s (0:02:39)
```

## Conformal rule

For each age bin:

```text
k     = ceil((n_eff + 1) * (1 - alpha))
level = k / n_eff
q_hat = empirical quantile with method="higher"
```

`n_eff` is the number of calibration blocks, not rows. With 500 calibration
blocks and `alpha=0.10`, `level=451/500=0.902`.

Variants:

```text
A: one random row per calibration block, exact finite-sample anchor
B: all calibration rows, level corrected by block count, main method
C: max score per block, conservative whole-block upper bound
```

## Commands

```bash
/tmp/dt4n-venv/bin/python -m cert.conformal_v2 --calib results/phase-21R/calib_set_poisson_0.925.parquet --out results/phase-21R/conformal_poisson_0.925.json
/tmp/dt4n-venv/bin/python -m cert.conformal_v2 --calib results/phase-21R/calib_set_poisson_0.850.parquet --out results/phase-21R/conformal_poisson_0.850.json
/tmp/dt4n-venv/bin/python -m cert.conformal_v2 --calib results/phase-21R/calib_set_h2_0.700.parquet --out results/phase-21R/conformal_h2_0.700.json
/tmp/dt4n-venv/bin/python -m cert.conformal_v2 --calib results/phase-21R/calib_set_cbr_0.700.parquet --out results/phase-21R/conformal_cbr_0.700.json
```

## Cell chinh

`poisson@0.925`, `s_margin`, `z_bin`, Variant B:

| Bin | n_calib_blocks | n_test_rows | level | q_hat | coverage |
|---|---:|---:|---:|---:|---:|
| B1 | 500 | 45000 | 0.902 | 11.587758 | 0.91020 |
| B2 | 500 | 100000 | 0.902 | 15.634801 | 0.91177 |
| B3 | 500 | 100000 | 0.902 | 19.646107 | 0.90981 |
| B4 | 500 | 254967 | 0.902 | 24.322243 | 0.90676 |

```text
coverage_marginal = 0.908684
G3 pass: |0.908684 - 0.90| = 0.008684 <= 0.02
G4 pass: max_abs_dev_per_bin = 0.011770 <= 0.05
```

## G8 alpha/K

| Bin | q(alpha=0.10) | q(alpha/4=0.025) |
|---|---:|---:|
| B1 | 11.587758 | 16.082920 |
| B2 | 15.634801 | 21.735090 |
| B3 | 19.646107 | 26.894810 |
| B4 | 24.322243 | 33.938534 |

All increase, so G8 passes.

## G6 positive control

V3 repeats: 20.

| Split | mean coverage by bin | SD by bin |
|---|---:|---:|
| block | .90254 .90395 .90372 .90272 | .00417 .00423 .00500 .00470 |
| row leak | .90105 .90134 .90101 .90067 | .00122 .00145 .00104 .00094 |

```text
SD(row) / SD(block) = 0.256182
```

This passes G6. The important signature is variance collapse, not coverage mean
moving away from 0.90.

## Independent seed validation

Calibration seeds `{101,102,103}`, test seeds `{104,105}`:

| Bin | q_hat | coverage |
|---|---:|---:|
| B1 | 11.520279 | 0.90808 |
| B2 | 15.407788 | 0.90201 |
| B3 | 19.325661 | 0.89923 |
| B4 | 24.136398 | 0.90179 |

```text
coverage_marginal = 0.901887
```

This is the strongest leakage check because calibration and test trajectories
share no seed.

## Variants

| Variant | q_hat B1 | q_hat B2 | q_hat B3 | q_hat B4 | coverage bins | marginal |
|---|---:|---:|---:|---:|---|---:|
| A | 11.100814 | 15.775669 | 19.444059 | 26.057087 | .8963 .9148 .9068 .9281 | 0.91834 |
| B | 11.587758 | 15.634801 | 19.646107 | 24.322243 | .9102 .9118 .9098 .9068 | 0.90868 |
| C | 21.392284 | 28.754477 | 33.899490 | 45.904232 | .9985 .9979 .9959 .9979 | 0.99753 |

`A` and `B` are within 7.13% in q_hat on this cell. `C` is intentionally very
conservative.

## Bridge to RMS

| Bin | q_hat | 1.645*rms | ratio |
|---|---:|---:|---:|
| B1 | 11.587758 | 11.380854 | 1.01818 |
| B2 | 15.634801 | 15.323975 | 1.02028 |
| B3 | 19.646107 | 19.265418 | 1.01976 |
| B4 | 24.322243 | 24.070188 | 1.01047 |

All ratios are within 5%, confirming the Lesson 3 -> Lesson 4 -> Lesson 5
bridge.

## One-sided score

| Bin | q_two_sided | q_one_sided | coverage |
|---|---:|---:|---:|
| B1 | 11.587758 | 10.465103 | 0.90511 |
| B2 | 15.634801 | 14.156768 | 0.90808 |
| B3 | 19.646107 | 18.029781 | 0.90898 |
| B4 | 24.322243 | 22.546635 | 0.90465 |

One-sided score saves 7-10%, but remains secondary.

## Cross-cell summary

| Cell | G3 marginal | Max bin dev | G3 | G4 | G6 SD ratio | G8 | Seed-split marginal |
|---|---:|---:|---|---|---:|---|---:|
| poisson@0.925 | 0.908684 | 0.011770 | PASS | PASS | 0.256182 | PASS | 0.901887 |
| poisson@0.850 | 0.907670 | 0.008984 | PASS | PASS | 0.263858 | PASS | 0.901242 |
| h2@0.700 | 0.906710 | 0.007282 | PASS | PASS | 0.312357 | PASS | 0.903642 |
| cbr@0.700 | 0.921027 | 0.022574 | FAIL | PASS | 0.171670 | PASS | 0.877463 |

`cbr@0.700` is a degenerate positive-control cell from Lesson 2, so it is not a
headline robustness cell. Its two-sided score is slightly over-conservative
relative to G3, while G4/G6/G8 still pass.

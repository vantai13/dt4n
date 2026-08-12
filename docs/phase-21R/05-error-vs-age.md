# Lesson 21R.4 -- error_vs_age_v2.py

Ngay hoan thanh: 2026-08-12

## Artifact

Source:

```text
cert/error_vs_age_v2.py
test/test_phase21r_errage.py
```

Results:

```text
results/phase-21R/error_vs_age_poisson_0.925.json
results/phase-21R/error_vs_age_poisson_0.850.json
results/phase-21R/error_vs_age_h2_0.700.json
results/phase-21R/error_vs_age_cbr_0.700.json
```

## Test

Targeted:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_errage.py -q
```

```text
10 passed
```

Phase 21R related:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_errage.py test/test_phase21r_decomp.py test/test_phase21r_calib.py test/test_phase21r_margin.py -q
```

```text
42 passed
```

Full suite:

```bash
/tmp/dt4n-venv/bin/python -m pytest -q
```

```text
576 passed, 1 skipped, 2 warnings in 168.03s (0:02:48)
```

## Lenh sinh artifact

```bash
/tmp/dt4n-venv/bin/python -m cert.error_vs_age_v2 --mode poisson --rho-bar 0.925 --calib results/phase-21R/calib_set_poisson_0.925.parquet --out results/phase-21R/error_vs_age_poisson_0.925.json
/tmp/dt4n-venv/bin/python -m cert.error_vs_age_v2 --mode poisson --rho-bar 0.850 --calib results/phase-21R/calib_set_poisson_0.850.parquet --out results/phase-21R/error_vs_age_poisson_0.850.json
/tmp/dt4n-venv/bin/python -m cert.error_vs_age_v2 --mode h2 --rho-bar 0.700 --calib results/phase-21R/calib_set_h2_0.700.parquet --out results/phase-21R/error_vs_age_h2_0.700.json
/tmp/dt4n-venv/bin/python -m cert.error_vs_age_v2 --mode cbr --rho-bar 0.700 --calib results/phase-21R/calib_set_cbr_0.700.parquet --out results/phase-21R/error_vs_age_cbr_0.700.json
```

## Quy uoc

Lesson nay co ba loai nguong:

```text
q_pooled        = q90 cua tat ca hang trong bin
q_block_median  = median cua q90 theo block
q_of_block_q    = q90 cua q90 theo block
```

Duong cong `s(z)` va bang marginal-vs-conditional dung `q_pooled`. Bootstrap
gate G1/H2 dung `q_of_block_q` de bao ton cau truc block. Forecast Lesson 6
bao cao ca ba de bai toan sau khong bi lan dai luong.

## Cell chinh: poisson@0.925

Thong ke `s_margin`, bin chinh:

| Bin | n | blocks | mean | rms | p50 | q_pooled | q_block_median | q_of_block_q | q95 | kurt | q/rms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 | 90000 | 1000 | 5.520986 | 6.919068 | 4.673182 | 11.377967 | 10.844943 | 14.206512 | 13.535036 | 3.865 | 1.6444 |
| B2 | 200000 | 1000 | 7.425455 | 9.316315 | 6.258182 | 15.322567 | 14.832834 | 19.164635 | 18.314310 | 3.983 | 1.6447 |
| B3 | 200000 | 1000 | 9.334884 | 11.712542 | 7.884977 | 19.276593 | 18.460567 | 24.519946 | 23.061627 | 3.940 | 1.6458 |
| B4 | 509945 | 1000 | 11.649079 | 14.633635 | 9.842242 | 24.022124 | 23.403852 | 30.417170 | 28.621830 | 4.023 | 1.6416 |

Gates:

| Gate | Result |
|---|---|
| G1 monotone | 3/3 steps positive, PASS |
| H2 ratio | 2.1510, CI95 [2.0879, 2.2135], PASS |
| G2 eta^2 | 0.0730, CI95 [0.0696, 0.0763], PASS |
| G7 Spearman vs 20R | 1.0000, PASS |

G1 consecutive differences use block bootstrap with family 99% Bonferroni /3:

| Step | diff_mean | CI |
|---|---:|---:|
| B2 - B1 | 5.0143 | [4.3864, 5.5687] |
| B3 - B2 | 5.3209 | [4.4863, 5.9867] |
| B4 - B3 | 5.9639 | [4.8343, 7.1197] |

## Mondrian evidence

One marginal threshold gives correct average coverage but wrong per-bin
coverage:

```text
q_marginal = 20.752588 ms
```

| Bin | q_conditional | coverage_if_marginal | gap_from_target |
|---|---:|---:|---:|
| B1 | 11.377967 | 0.9972 | +0.0972 |
| B2 | 15.322567 | 0.9737 | +0.0737 |
| B3 | 19.276592 | 0.9223 | +0.0223 |
| B4 | 24.022125 | 0.8452 | -0.0548 |

This is the central Section 5 figure/table: marginal coverage can satisfy the
contract on average while under-covering the oldest bin.

## Secondary bins

For `poisson@0.925`, equal-width secondary bins have the same direction:

| Bin | q_pooled |
|---|---:|
| B1' | 13.018484 |
| B2' | 17.567873 |
| B3' | 20.994175 |
| B4' | 23.551112 |
| B5' | 25.713567 |

`q_pooled(B5') / q_pooled(B1') = 1.975`, so the conclusion is not an artifact
of the main bin grid.

## Cross-cell summary

| Cell | eta^2 | eta CI95 | G1 | H2 ratio CI95 | G7 |
|---|---:|---:|---|---:|---|
| poisson@0.925 | 0.073033 | [0.069641, 0.076286] | PASS | 2.151 [2.088, 2.213] | PASS |
| poisson@0.850 | 0.068509 | [0.065314, 0.071584] | PASS | 2.100 [2.027, 2.166] | PASS |
| h2@0.700 | 0.065167 | [0.062016, 0.068250] | PASS | 2.006 [1.945, 2.066] | PASS |
| cbr@0.700 | 0.000002 | [0.000001, 0.000032] | FAIL | 1.015 [1.000, 1.032] | N/A |

`cbr@0.700` la positive control suy bien tu Lesson 2, nen duong cong phang la
ket qua mong doi.

## Half-normal check

Cell chinh:

```text
mean(|s|)/rms mean = 0.797006 vs theory 0.797885
q90(|s|)/rms mean  = 1.644129 vs theory 1.644854
q90/rms rel spread = 0.002578
```

Vi vay `q_hat(g) ~= 1.645 * rms(s | g)` la mot cau noi giai thich tu Lesson
21R.3 sang Lesson 21R.5. No van la quan sat, khong phai gia dinh cua conformal.

## Bias and invariance

Systematic bias on the main cell:

```text
mean(s_signed) = +3.638827 ms
sd(s_signed)   = 12.044626 ms
skew           = 0.098153
mean_e_model   = -0.741876 ms
mean_e_stale   = -2.896951 ms
```

The twin is optimistic about the decision margin. Do not correct this in Phase
21R; record it for future work.

Stationarity check:

| Bin | m_hat p10 | m_hat p50 | m_hat p90 |
|---|---:|---:|---:|
| B1 | 2.514757 | 12.847007 | 30.842481 |
| B2 | 2.514757 | 12.847007 | 30.842481 |
| B3 | 2.514757 | 12.847007 | 30.842481 |
| B4 | 2.513934 | 12.845900 | 30.841530 |

Median relative spread is `8.62e-05`, PASS. Thus the age effect is from score
growth, not from a drifting decision-gap distribution.

## Forecast for Lesson 21R.6

| Threshold family | pooled P(accept) |
|---|---:|
| q_block_median | 0.3128 |
| q_pooled | 0.2978 |
| q_of_block_q | 0.1943 |

All are below 0.90, so G12 is expected to pass. The useful-risk curve H7 remains
the main remaining risk.

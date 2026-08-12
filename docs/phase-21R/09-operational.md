# Lesson 21R.8 -- operational_sigma.py

Ngay hoan thanh: 2026-08-12

## Artifact

Source:

```text
cert/operational_sigma.py
test/test_phase21r_operational.py
```

Result:

```text
results/phase-21R/operational_sigma.json
```

Docs:

```text
docs/phase-21R/00i-amendment-8.md
docs/phase-21R/09-operational.md
```

## Command

```bash
/tmp/dt4n-venv/bin/python -m cert.operational_sigma --out results/phase-21R/operational_sigma.json --also-fixed
```

## Purpose

Lessons 21R.1-21R.7 use fixed `sigma_rho=0.0096` to isolate rho effects from
sigma effects. This lesson runs the pre-declared operational path, where each
cell uses its calibrated `sigma_rho`, to check whether the conclusions survive.

The two paths answer different questions and must not be pooled into one gate.

## Operational Results

| Cell | sigma | anchor | coverage | q(B0) | q(B3) | ratio | acc(k=1) | err(k=1) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `cbr@0.700` | 0.04622 | 0.000000 | 0.90858 | 0.0103 | 0.0103 | 0.998 | 1.0000 | 0.000000 |
| `cbr@0.850` | 0.01308 | 0.000000 | 0.91110 | 0.0081 | 0.0081 | 0.999 | 1.0000 | 0.000000 |
| `poisson@0.700` | 0.04622 | 0.141305 | 0.90399 | 1.0083 | 2.2645 | 2.246 | 0.3941 | 0.018530 |
| `poisson@0.850` | 0.04797 | 0.330766 | 0.90090 | 15.1663 | 35.0995 | 2.314 | 0.0794 | 0.064478 |
| `poisson@0.925` | 0.02180 | 0.288899 | 0.89912 | 24.3053 | 51.9968 | 2.139 | 0.1969 | 0.041572 |
| `poisson@0.960` | 0.00959 | 0.199325 | 0.90735 | 17.8291 | 38.4545 | 2.157 | 0.2956 | 0.023267 |
| `h2@0.700` | 0.04622 | 0.301304 | 0.90166 | 27.3326 | 58.9691 | 2.157 | 0.1697 | 0.047947 |
| `h2@0.850` | 0.04797 | 0.258487 | 0.90594 | 81.4597 | 174.9093 | 2.147 | 0.2325 | 0.030575 |
| `h2@0.925` | 0.02180 | 0.077595 | 0.90887 | 48.0028 | 102.9331 | 2.144 | 0.6146 | 0.008618 |
| `h2@0.960` | 0.00959 | 0.000512 | 0.90615 | 24.3486 | 51.3169 | 2.108 | 0.9846 | 0.000240 |

Summary:

```text
coverage range                 = [0.899123, 0.911104]
sigma range                    = [0.009593, 0.047965]
G3                             = PASS 10/10
G4                             = PASS 10/10
H7 nondegenerate cells          = PASS 7/7
near-zero degenerate diagnostics = PASS 3/3
```

## H7 Detail

| Cell | anchor | acc k=0.5 | err k=0.5 | ratio | acc k=1 | err k=1 | ratio | H7 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `poisson@0.700` | 0.141305 | 0.71701 | 0.056494 | 0.400 | 0.39409 | 0.018530 | 0.131 | PASS |
| `poisson@0.850` | 0.330766 | 0.28729 | 0.143243 | 0.433 | 0.07944 | 0.064478 | 0.195 | PASS at k=0.5 |
| `poisson@0.925` | 0.288899 | 0.49777 | 0.135942 | 0.471 | 0.19692 | 0.041572 | 0.144 | PASS |
| `poisson@0.960` | 0.199325 | 0.59502 | 0.086308 | 0.433 | 0.29564 | 0.023267 | 0.117 | PASS |
| `h2@0.700` | 0.301304 | 0.45718 | 0.139050 | 0.461 | 0.16966 | 0.047947 | 0.159 | PASS |
| `h2@0.850` | 0.258487 | 0.52933 | 0.113365 | 0.439 | 0.23249 | 0.030575 | 0.118 | PASS |
| `h2@0.925` | 0.077595 | 0.82641 | 0.028218 | 0.364 | 0.61456 | 0.008618 | 0.111 | PASS |

`poisson@0.850` is the reminder not to collapse the family to only `kappa=1`.
It passes the original H7 family but not the single-point `kappa=1` criterion.

## Shape Invariance

The age-shape ratio report uses non-CBR cells. It includes `h2@0.960` even
though that cell is H7-degenerate, because q_hat itself is nontrivial there.

```text
n cells                 = 8
qhat(B0) spread factor  = 80.79x
ratio mean              = 2.176621
ratio sd                = 0.068233
ratio range             = [2.107591, 2.314317]
relative spread         = 0.094975
```

Conclusion:

```text
q_hat scale changes a lot across traffic regimes; q_hat age-shape changes little.
```

Limit:

```text
Observed on synthetic AR(1), tau=1.0. Not yet shown on real telemetry.
```

## Non-monotone Difficulty

Operational anchor error:

| Mode | rho=0.700 | rho=0.850 | rho=0.925 | rho=0.960 | Shape |
|---|---:|---:|---:|---:|---|
| `poisson` | 0.141 | 0.331 | 0.289 | 0.199 | peaks at 0.850 |
| `h2` | 0.301 | 0.258 | 0.078 | 0.001 | decreasing |

Mean load alone does not explain difficulty on the operational path because
operational sigma also changes with rho_bar.

## Fixed vs Operational

| Cell | fixed anchor | operational anchor | fixed acc(k=1) | operational acc(k=1) | rescued? |
|---|---:|---:|---:|---:|---|
| `poisson@0.700` | 0.0000 | 0.1413 | 1.000 | 0.394 | YES |
| `poisson@0.850` | 0.2207 | 0.3308 | 0.241 | 0.079 | NO |
| `poisson@0.925` | 0.2224 | 0.2889 | 0.284 | 0.197 | NO |
| `poisson@0.960` | 0.1995 | 0.1993 | 0.296 | 0.296 | NO |
| `h2@0.700` | 0.1265 | 0.3013 | 0.497 | 0.170 | NO |
| `h2@0.850` | 0.0029 | 0.2585 | 0.945 | 0.232 | YES |
| `h2@0.925` | 0.0002 | 0.0776 | 0.987 | 0.615 | YES |
| `h2@0.960` | 0.0005 | 0.0005 | 0.984 | 0.985 | NO |

`n_rescued_by_operational = 3`, not 4. This is verified directly from
`results/phase-21R/operational_sigma.json`.

## Tests

Targeted:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_operational.py -q
```

```text
10 passed
```

Phase 21R related:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_operational.py test/test_phase21r_freshness.py test/test_phase21r_usefulness.py test/test_phase21r_conformal.py test/test_phase21r_errage.py test/test_phase21r_decomp.py test/test_phase21r_calib.py test/test_phase21r_margin.py -q
```

```text
94 passed
```

Full suite:

```bash
/tmp/dt4n-venv/bin/python -m pytest -q
```

```text
628 passed, 1 skipped, 2 warnings in 156.68s (0:02:36)
```

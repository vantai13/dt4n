# Lesson 21R.7 -- freshness_requirement.py

Ngay hoan thanh: 2026-08-12

## Artifact

Source:

```text
cert/freshness_requirement.py
test/test_phase21r_freshness.py
```

Results:

```text
results/phase-21R/freshness_poisson_0.925.json
results/phase-21R/freshness_poisson_0.850.json
results/phase-21R/freshness_h2_0.700.json
```

Docs:

```text
docs/phase-21R/00h-amendment-7.md
docs/phase-21R/08-freshness.md
```

## Commands

```bash
/tmp/dt4n-venv/bin/python -m cert.freshness_requirement --mode poisson --rho-bar 0.925 --out results/phase-21R/freshness_poisson_0.925.json --target-err 0.01 --measured-sawtooth-err 0.222399
/tmp/dt4n-venv/bin/python -m cert.freshness_requirement --mode poisson --rho-bar 0.850 --out results/phase-21R/freshness_poisson_0.850.json --target-err 0.01 --measured-sawtooth-err 0.219062
/tmp/dt4n-venv/bin/python -m cert.freshness_requirement --mode h2 --rho-bar 0.700 --out results/phase-21R/freshness_h2_0.700.json --target-err 0.01 --measured-sawtooth-err 0.127259
```

## Definition

The module converts quality targets into freshness requirements:

```text
quality target -> z* -> synchronization rate
```

For sawtooth AoI:

```text
z_max  = d_sync + T
z_mean = d_sync + T / 2
```

Therefore `sync_hz_max_interp` is exactly `2x` `sync_hz_mean_interp` for the
same numeric `z*`.

## Main Fixed-z Table

`poisson@0.925`, fixed z, `sigma=0.0096`, 5 seeds. The `err_anchor` column is
computed on the conformal test split. The model-floor section below separately
reports all rows at `z=0`.

| z | err_anchor | q_hat | acc k=1 | err k=1 | regret k=1 | acc k=0.5 | err k=0.5 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.000 | 0.040826 | 3.6949 | 0.8425 | 0.000131 | 0.00005 | 0.9212 | 0.010748 |
| 0.005 | 0.049168 | 4.5919 | 0.8048 | 0.002272 | 0.00166 | 0.9020 | 0.015463 |
| 0.010 | 0.057502 | 5.4009 | 0.7713 | 0.003468 | 0.00343 | 0.8846 | 0.018926 |
| 0.020 | 0.071670 | 6.7427 | 0.7175 | 0.004927 | 0.00703 | 0.8560 | 0.024330 |
| 0.030 | 0.083706 | 7.8237 | 0.6755 | 0.006191 | 0.01069 | 0.8333 | 0.029148 |
| 0.040 | 0.093852 | 8.7804 | 0.6390 | 0.007353 | 0.01430 | 0.8132 | 0.033266 |
| 0.055 | 0.107526 | 10.0361 | 0.5922 | 0.009274 | 0.02067 | 0.7872 | 0.039086 |
| 0.075 | 0.122651 | 11.4702 | 0.5409 | 0.011680 | 0.03049 | 0.7579 | 0.046440 |
| 0.100 | 0.139620 | 13.0036 | 0.4879 | 0.014854 | 0.04458 | 0.7272 | 0.055094 |
| 0.150 | 0.167615 | 15.5538 | 0.4062 | 0.020242 | 0.07535 | 0.6776 | 0.071022 |
| 0.200 | 0.190398 | 17.6879 | 0.3441 | 0.027296 | 0.11411 | 0.6367 | 0.085607 |
| 0.300 | 0.226728 | 21.0404 | 0.2582 | 0.039514 | 0.19682 | 0.5747 | 0.112076 |
| 0.400 | 0.255034 | 23.7591 | 0.2016 | 0.051190 | 0.29550 | 0.5259 | 0.136425 |
| 0.550 | 0.288742 | 26.8521 | 0.1484 | 0.072541 | 0.46934 | 0.4730 | 0.170468 |

## Model Floor

At `z=0`, the twin sees the current telemetry. The remaining error is model or
measurement floor:

```text
err_at_z0_all_rows       = 0.040297
err_at_z0_test_rows      = 0.040826
rms_s_margin_all_rows    = 2.142942 ms
q_hat_at_z0              = 3.694914 ms
accept(kappa=1)          = 0.842462
err|accept(kappa=1)      = 0.000131
```

This is a floor for forced decisions, not for selective decisions.

## AoI Averaging Check

`poisson@0.925`:

```text
E_z[err(z)] = 0.217859
err(E[z])   = 0.227436
err(z_max)  = 0.288742
measured    = 0.222399
```

The measured sawtooth value is closest to `E_z[err(z)]`, confirming the Jensen
diagnosis from Lesson 21R.2.

## Requirement Inversion

`poisson@0.925`:

| Target | z* | Feasible | Hz mean | Hz max |
|---|---:|---|---:|---:|
| `err_anchor <= 0.10`, no gate | 0.046744 | NO | -- | -- |
| `err|accept <= 0.01`, `kappa=1` | 0.061035 | YES | 49.83 | 99.66 |
| `acceptance >= 0.50`, `kappa=1` | 0.094278 | YES | 11.55 | 23.11 |

The no-gate `10%` target is infeasible because `z*=46.7 ms` is below the
physical floor `d_sync=51 ms`.

## Iso-quality Frontier

`poisson@0.925`, target `err|accept = 1%`:

| z | q_hat | kappa* | acceptance | err check | Hz mean | Hz max |
|---:|---:|---:|---:|---:|---:|---:|
| 0.055 | 10.0361 | 0.9790 | 0.6002 | 0.0100 | 125.0 | 250.0 |
| 0.100 | 13.0036 | 1.1308 | 0.4325 | 0.0100 | 10.2 | 20.4 |
| 0.150 | 15.5538 | 1.2437 | 0.2997 | 0.0100 | 5.1 | 10.1 |
| 0.200 | 17.6879 | 1.3575 | 0.1973 | 0.0100 | 3.4 | 6.7 |
| 0.300 | 21.0404 | 1.4489 | 0.1003 | 0.0100 | 2.0 | 4.0 |
| 0.400 | 23.7591 | 1.6971 | 0.0291 | 0.0100 | 1.4 | 2.9 |
| 0.550 | 26.8521 | 2.2159 | 0.0012 | 0.0100 | 1.0 | 2.0 |

Knee estimate:

```text
knee_z = 0.100
knee_sync_hz_mean = 10.204
knee_acceptance = 0.4325
```

Marginal value:

```text
2.0 Hz -> 10.2 Hz : +0.332 acceptance
10.2 Hz -> 125 Hz : +0.168 acceptance
```

The first 5x increase in synchronization frequency buys about twice the
acceptance gain of the next 12x increase.

## Cross-cell Summary

| Cell | E_z[err] | measured | no-gate `err<=0.10` | gated `err<=0.01` | acc>=0.50 | knee mean Hz |
|---|---:|---:|---|---|---|---:|
| `poisson@0.925` | 0.217859 | 0.222399 | z*=0.0467, infeasible | z*=0.0610, feasible | z*=0.0943 | 10.2 |
| `poisson@0.850` | 0.215214 | 0.219062 | z*=0.0492, infeasible | z*=0.0913, feasible | z*=0.0738 | 10.2 |
| `h2@0.700` | 0.126533 | 0.127259 | z*=0.1546, feasible | z*=0.1357, feasible | z*=0.2774 | 10.2 |

The main impossibility headline is strongest for the two `poisson` cells. The
`h2@0.700` cell is easier: even no-gate `err<=0.10` is feasible above the
physical floor.

## Tests

Targeted:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_freshness.py -q
```

```text
14 passed
```

Phase 21R related:

```bash
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_freshness.py test/test_phase21r_usefulness.py test/test_phase21r_conformal.py test/test_phase21r_errage.py test/test_phase21r_decomp.py test/test_phase21r_calib.py test/test_phase21r_margin.py -q
```

```text
84 passed
```

Full suite command:

```bash
/tmp/dt4n-venv/bin/python -m pytest -q
```

```text
618 passed, 1 skipped, 2 warnings in 171.49s (0:02:51)
```

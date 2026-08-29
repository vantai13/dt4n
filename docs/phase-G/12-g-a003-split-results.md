# G-A003 split-sample result — stopped by power before outcome

## Verdict

`INSUFFICIENT_POWER_PRE_OUTCOME`.  The censoring-first gate keeps all six
edge-edge pairs, but the first-half time-scale calibration leaves zero pairs
above the locked `T_test/tau >= 50` floor.  In accordance with G-A003, the test
stage did not calculate any held-out correlation.  `G1_closed=false`; G2-0 is
not opened.

The result is not an estimator FAIL.  It says this 50/50 split of the existing
1,504.8 s run cannot support the requested confirmatory claim.

## Split-sample six-pair table

Each half contains 3,762 samples at 0.20 s, or 752.4 s.  `min T/tau` is the
minimum over offered/measured calibration time scales for both links.

| pair | censoring gate | min test T/tau | temporal power | held-out result |
|---|---|---:|---|---|
| uA-uB | PASS | 33.56 | FAIL | `NOT_EVALUATED_TEMPORAL_POWER_GATE` |
| uA-vC | PASS | 21.10 | FAIL | `NOT_EVALUATED_TEMPORAL_POWER_GATE` |
| uA-vD | PASS | 22.21 | FAIL | `NOT_EVALUATED_TEMPORAL_POWER_GATE` |
| uB-vC | PASS | 21.10 | FAIL | `NOT_EVALUATED_TEMPORAL_POWER_GATE` |
| uB-vD | PASS | 22.21 | FAIL | `NOT_EVALUATED_TEMPORAL_POWER_GATE` |
| vC-vD | PASS | 21.10 | FAIL | `NOT_EVALUATED_TEMPORAL_POWER_GATE` |

Consequently `max(abs(r_offered))`, the six-pair median error, and all six
held-out `rho_eps` values are `null`/not evaluated.  Reporting a median below
0.02 here would require bypassing the gate signed before the test.

## Retrospective censoring audit

This separate post-hoc audit uses the full run only for single-link marginal
diagnosis.  The hard-clip model is `Y=min(X,K09)`, with Gaussian `X` fixed to
the observed offered mean and SD and no fitted free parameter.

| link | class | P Gaussian above K09 | SD offered | SD measured | hard-clip SD | measured / prediction |
|---|---|---:|---:|---:|---:|---:|
| uA | edge | 0.0000 | 0.02836 | 0.02864 | 0.02836 | 101.0% |
| uB | edge | 0.0000 | 0.02628 | 0.02779 | 0.02628 | 105.7% |
| ac | core | 0.3787 | 0.10481 | 0.06975 | 0.07190 | 97.0% |
| ad | core | 0.4306 | 0.10440 | 0.05835 | 0.06710 | 87.0% |
| bc | core | 0.3202 | 0.09994 | 0.07039 | 0.07339 | 95.9% |
| bd | core | 0.3712 | 0.09910 | 0.06835 | 0.06859 | 99.6% |
| vC | edge | 0.0000 | 0.02978 | 0.02981 | 0.02978 | 100.1% |
| vD | edge | 0.0000 | 0.02675 | 0.02807 | 0.02675 | 104.9% |

The core censoring range is 32.0–43.1%; the zero-free-parameter clip model
reproduces core measured SD to 87.0–99.6%.  For `ac`, the G.0 feasibility limit
is `sigma_max=0.00697`, while offered SD is 0.10481, a 15.04x violation.  This
is a retrospective positive control for the G.0 feasibility layer.

## Clean historical edge diagnostic (not the split outcome)

For traceability, the only readable pair table from the already-inspected full
run remains the six edge-edge rows below.  These numbers are post-hoc/full-run,
not held-out results and cannot close G1.

| pair | r measured | r true hat | r offered | absolute error | rho_eps hat |
|---|---:|---:|---:|---:|---:|
| uA-uB | 0.18250 | 0.10249 | 0.10525 | 0.00276 | 0.688 |
| uA-vC | 0.01016 | 0.00152 | -0.00814 | 0.00965 | 0.078 |
| uA-vD | 0.06183 | 0.06005 | 0.06508 | 0.00503 | 0.073 |
| uB-vC | 0.07329 | 0.06817 | 0.05969 | 0.00848 | 0.113 |
| uB-vD | 0.03201 | 0.02033 | 0.00869 | 0.01164 | 0.100 |
| vC-vD | 0.12306 | 0.05046 | 0.00340 | 0.04706 | 0.653 |

Historical median absolute error is 0.00906 and the maximum is 0.04706.  The
same-side median `rho_eps` is 0.6704 versus 0.0891 cross-side (7.52x), which
motivates H6b but does not test it.

## Limits recorded

- G-L20: R7 used the wrong variable.  Censoring eligibility must use
  `p(rho_offered > K09) < 0.05`, before correlations.
- G-L21: core links in `cellA_long` are censored 32–43%; the additive nugget
  model is invalid there.  `sf_hat>1` is a model-class warning, not evidence of
  zero nugget.
- G-L22: G.0's analytic feasibility layer retrospectively rejects the observed
  core configuration; `ac` exceeds its sigma limit by 15.04x.
- G-L23: the 7.52x same-side/cross-side `rho_eps` pattern is post-hoc.  H6b is
  frozen only for fresh G1-B data.
- G-L24: the historical “18/18 reduced-model PASS” interpretation is retracted;
  15 pairs include a censored core link and the remaining control lacked the
  locked dynamic range.  The six-edge table above replaces it as diagnostic.

## Reproduction and artifacts

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_a003_split_sample.py --stage calibrate
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_a003_split_sample.py --stage test
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g1_censoring_retro_audit.py
```

- Calibration: `results/SMOKE/phase-G/g_a003_split_calibration.json`
- Split verdict: `results/SMOKE/phase-G/g_a003_split_sample.json`
- Censoring audit: `results/SMOKE/phase-G/g1_censoring_retro_audit.json`
- Historical pair estimates: `results/SMOKE/phase-G/g1_4_physical_reanalysis.json`


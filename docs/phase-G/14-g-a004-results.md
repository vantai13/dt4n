# G-A004 result — paired power passes, held-out accuracy fails

Run date: 2026-08-29 UTC.  The power run followed tag
`phase-G-g-a004-prereg` at commit `5248218d`.  Its PASS artifact was frozen at
tag `phase-G-g-a004-power-pass` before the held-out test was opened.

## Synthetic paired-power gate

The synthetic stage retained `held_out_correlations_read=false`.

| Gate | Estimate | 95% Wilson lower | Required | Verdict |
|---|---:|---:|---:|---|
| P(all six errors <= 0.10) | 0.9905 | 0.9852 | >=0.95 | PASS |
| P(median six errors < 0.02) | 0.9975 | 0.9942 | >=0.90 | PASS |

The power model therefore authorized the held-out test.  It did not guarantee
a physical PASS: 19/2,000 synthetic replicates had at least one pair above
0.10 under the locked model.

## Held-out six-pair result

| pair | r measured | r offered | r true hat | rho eps hat | absolute error | pair gate |
|---|---:|---:|---:|---:|---:|---|
| uA-uB | 0.24981 | 0.11410 | 0.22318 | 0.93858 | 0.10907 | FAIL |
| uA-vC | -0.04682 | -0.05206 | -0.05310 | 0.02060 | 0.00104 | PASS |
| uA-vD | 0.07396 | 0.10594 | 0.08444 | 0.01425 | 0.02150 | PASS |
| uB-vC | 0.06978 | 0.09219 | 0.07694 | 0.01513 | 0.01525 | PASS |
| uB-vD | 0.00486 | 0.01953 | 0.00390 | 0.01272 | 0.01563 | PASS |
| vC-vD | -0.20022 | -0.20428 | -0.24890 | -0.00456 | 0.04461 | PASS |

Locked adjudication:

```text
dynamic range max|r_offered| = 0.20428 >= 0.20     PASS
median absolute error        = 0.01856 < 0.02      PASS
all pair errors <= 0.10      = 5/6                 FAIL
overall verdict                                    FAIL
G1_closed                                          false
```

No threshold is changed.  `uA-uB` exceeds the pair gate by `0.00907`; because
the signed rule requires all six pairs, the near miss is still a FAIL.  G2-0
is not opened.

## Interpretation boundary

The direct paired-power correction was warranted: both paired power gates
passed and the physical median gate also passed.  Nevertheless, the physical
test rejects certification of the locked estimator/model combination because
one pair failed.  The test alone cannot distinguish an estimator defect, a
misspecified/stationarity-violating measurement model, or the approximately
0.95% familywise tail allowed by the synthetic model.

The held-out `rho_eps` pattern is also not stable in the simple same-side form:
`uA-uB=0.9386`, while `vC-vD=-0.0046`; all four cross-side estimates are
`0.0127–0.0206`.  This is descriptive only.  H6b was formed after the full
historical run had been seen and remains reserved for genuinely fresh G1-B
data.

## Files and reproduction

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_a004_paired_power.py --stage power
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_a004_paired_power.py --stage test
```

- Power: `results/SMOKE/phase-G/g_a004_paired_power.json`
- Held-out result: `results/SMOKE/phase-G/g_a004_split_sample.json`
- Frozen first-half calibration:
  `results/SMOKE/phase-G/g_a003_split_calibration.json`


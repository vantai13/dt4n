# G-A004 — direct paired-statistic power gate

Date signed: 2026-08-29 UTC.  This amendment is signed while
`results/SMOKE/phase-G/g_a003_split_sample.json` still records
`held_out_correlations_read=false` at raw-input hashes frozen by G-A003.

## Why this amendment is valid

This is not post-outcome threshold relaxation:

1. No held-out correlation or held-out estimator result has been calculated.
2. `PAIR_ERROR_MAX=0.10`, strict `MEDIAN_ERROR_MAX=0.02`, the six edge pairs,
   censoring rule, dynamic-range floor `0.20`, and split index `3762` remain
   unchanged.
3. The marginal proxy `T_test/tau>=50` is replaced by a direct power calculation
   on the paired decision statistic `abs(r_true_hat-r_offered)`.  The new gate
   can be stricter in configurations where paired cancellation is weak.

## Locked synthetic power calculation

Use only first-half `sf` and `tau` from the immutable calibration artifact.
Generate four independent unit-variance AR(1) ground-truth edge signals at
`r_true=0`, then add temporally white Gaussian measurement nugget.  Nugget
correlation is locked to `0.65` for same telemetry side and `0.10` cross-side.
The measured traces go through the already signed unequal-phi
`estimate_two_band`; each estimate is paired with the offered correlation from
the same synthetic realization.

```text
seed             = 20260830
repetitions      = 2000
n_test           = 3762
dt               = 0.20 s
pair error gate  = abs(r_true_hat-r_offered) <= 0.10
median gate      = median(six absolute errors) < 0.02
```

Proceed only when both 95% Wilson lower bounds pass:

```text
P(all six pair errors <= 0.10) >= 0.95
P(median six-pair error < 0.02) >= 0.90.
```

This simulation assumes the additive white-nugget model and exponential ACF
are correct.  It proves only that the locked accuracy thresholds are not
impossible by construction.  It does not promise a physical PASS; a physical
FAIL is evidence against the estimator/model combination and must be reported.

## Execution order

1. Commit this amendment, code, NT57, G-L25/G-L26, and the Phase-23 correction.
2. Create annotated tag `phase-G-g-a004-prereg`.
3. Run `--stage power`; it must retain `held_out_correlations_read=false`.
4. Only if both power gates pass, run `--stage test` and report every outcome.

No code path may use `T_test/tau>=50` to adjudicate this paired test.  The same
floor remains valid for marginal questions such as estimating a population
network correlation without a paired same-realization reference.

## Reproduction after the preregistration tag

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_a004_paired_power.py --stage power
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_a004_paired_power.py --stage test
```

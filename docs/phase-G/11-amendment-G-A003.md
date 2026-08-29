# G-A003 — censoring-first, power-gated edge split

Date signed: 2026-08-29 UTC.  This amendment is signed after inspecting only
the first contiguous half of `cellA_long`.  No correlation from the held-out
second half has been read.  The calibration artifact records
`held_out_correlations_read=false`.

## 1. Censoring gate comes first

At the common 0.20 s interval, a link passes only when

```text
mean(rho_offered > K09) < 0.05,  K09 = 1.0094102536.
```

Both links must pass before a pair can enter any correlation model.  A failed
pair is labelled `CENSORED`; neither the full nor reduced additive-nugget model
may be applied to it.  The gate is on the uncensored offered ledger, not on
`rho_measured`.

## 2. Power gates precede outcome interpretation

The first half estimates two time scales per link: the offered-ledger time
scale (ground-truth control) and measured-ledger time scale (estimator
control).  With `T_test = 752.4 s`, both links of every test pair must satisfy

```text
T_test / tau_offered >= 50
T_test / tau_measured >= 50.
```

All six edge pairs must pass before any held-out correlation is read.  If they
do, the offered correlations on that fixed six-pair set must additionally
satisfy

```text
max(abs(r_offered)) >= 2 * 0.10 = 0.20.
```

Failure at either stage is `INSUFFICIENT_POWER`, not evidence for or against
the estimator.  A valid accuracy PASS further requires every pair's absolute
error to be at most 0.10 and the six-pair median absolute error to be strictly
below 0.02.

## 3. Reduced model retained but restricted

The `sf -> 1` reduced model remains available only for uncensored pairs that
pass the power gates.  It is not used to rescue a pair rejected by censoring,
nor to reinterpret the historical 18/18 table.  No `cellA_long` pair currently
requires this branch after the censoring gate.

## 4. Fresh-data prediction H6b

The spatial pattern seen in the historical full run is post-hoc.  It is frozen
here solely as a falsifiable prediction for fresh G1-B bundle-factorial data:

```text
H6b: rho_eps(same telemetry side) >= 0.50
     AND rho_eps(opposite telemetry sides) <= 0.25.
```

`uA-uB` and `vC-vD` are the same-side pairs; `uA-vC`, `uA-vD`, `uB-vC`, and
`uB-vD` are opposite-side pairs.  The `cellA_long` split cannot promote H6b to
confirmatory because these thresholds were formed after the full historical
run had already been examined.

## 5. Locked split and pre-outcome audit

The split is deterministic and contiguous: samples `[0, 3762)` calibrate;
samples `[3762, 7524)` are held out.  No reseeding or boundary search is
allowed.  The first-half audit produced:

| pair | min test T/tau | censoring | eligible before outcome |
|---|---:|---|---|
| uA-uB | 33.56 | PASS | no |
| uA-vC | 21.10 | PASS | no |
| uA-vD | 22.21 | PASS | no |
| uB-vC | 21.10 | PASS | no |
| uB-vD | 22.21 | PASS | no |
| vC-vD | 21.10 | PASS | no |

Thus the preregistered test-stage action is already determined: record all six
pairs as `NOT_EVALUATED_TEMPORAL_POWER_GATE`, do not read held-out correlations,
and return `INSUFFICIENT_POWER_PRE_OUTCOME`.  Thresholds must not be relaxed.

## Reproduction

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python \
  tools/g_a003_split_sample.py --stage calibrate
```

Calibration artifact:
`results/SMOKE/phase-G/g_a003_split_calibration.json`.

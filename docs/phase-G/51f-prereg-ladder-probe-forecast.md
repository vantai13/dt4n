# G-A016 ladder-probe forecast preregistration

Recorded: 2026-09-04 UTC, after implementation and calibration of the v2
probe but before any 300-second floor or ladder measurement and before the
reduced loopback benchmark. Status: `PREREG_NO_LADDER_MEASUREMENT`.

## Locked predictions

| Quantity | Prediction |
|---|---:|
| binding role | sink or sampler |
| ladder `p_stall` / floor `p_stall` | 2x--25x |
| ladder Wilson upper endpoint | 0.004--0.08 |
| admission outcome | PASS probability about 55%; FAIL about 45% |
| A1 no-socket timing statistic, `1 x 1500` | 0.10--0.85 |

The mechanism is CPU-role contention: sampler CPU 6 and sink CPU 7 share
physical cores with spinning emitters under the signed L0 map. The range is
intentionally wide because this full role population has not yet been
measured. A result outside any interval is retained as evidence and does not
authorize changing a gate.

## Shape-matched A1 reading reference

The A1 statistic is the maximum absolute off-diagonal entry of one
eight-link correlation matrix. Its exact `1 replicate x 1500 windows` null,
computed by `simulate_emit3_null` with 3,000 trials and seed `20260913`, is:

| Null quantity | Value |
|---|---:|
| median | 0.0579735581 |
| p95 | 0.0803380519 |
| p99 | **0.0905129212** |
| signed safety factor | 1.957 |
| `1.957 x p99` reading reference | **0.1771337867** |

This is calibration to read, not calibration to decide. The artifact must
carry status `REPORTED_NOT_GATING`; neither 0.0905 nor 0.1771 is an admission
threshold. Admission continues to use only the binding role's Wilson upper
endpoint against the unchanged `GATE_P_STALL = 0.02`.

For scale, the same simulator and seed give p99 `0.2008431719` at `1 x 300`
and `0.0503643166` at `16 x 300`. Thus the historical doc-41 timing threshold
cannot be applied to A1, even though the reduction function has the same
name.

## Two forecasts after measurement

Once the binding Wilson endpoint is observed, it will be inserted into the
mechanistic model twice:

1. `replicates=1, windows=1500`, compared only with the measured A1 timing
   diagnostic.
2. `replicates=8, windows=150`, retained as the prediction for the reduced
   benchmark's timing diagnostic.

No cross-shape comparison is allowed. The two forecasts do not predict
EMIT-3', which is a load-residual gate and remains unmeasured.

## Stop rules

- Ladder admission FAIL stops before provenance tagging and benchmark work.
- A1 above its reading reference is reported as evidence of common timing
  structure but cannot independently stop or authorize a run.
- EMIT-3' failure does not widen its gate; it activates the decomposition
  order already signed in doc 51d.
- The prediction intervals in this file are the record. Later correspondence
  may explain them but cannot narrow them retrospectively.

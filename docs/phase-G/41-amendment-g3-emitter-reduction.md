# G.3 emitter amendment — correlation reduction before pairwise maximum

Signed: 2026-09-01 UTC, after the CPU ladder preregistration and before any
64-minute real-time execution. Status: `CODE_ONLY_NO_BENCHMARK`.

## Reduction order

For each ladder level and replicate, compute the complete 8x8 correlation
matrix of per-window maximum deadline lateness. EMIT-3 is then reduced as:

    1. mean the 16 within-replicate correlation matrices elementwise;
    2. select the 28 unique off-diagonal link pairs;
    3. take max(abs(rho_pair)).

The gate is not the median or mean of 16 replicate-level maxima. Maximum and
averaging do not commute; maximizing each noisy 300-window replicate first
creates an upward multiple-comparison bias that later aggregation cannot undo.

The previous implementation centered each replicate, concatenated 4,800
windows, and computed one matrix. That approach already avoided max-first bias,
but it did not implement the explicitly auditable mean-of-matrices estimand.
It is replaced before execution.

## Locked null calibration

A fixed synthetic null uses eight independent Gaussian white series:

    trials     = 3000
    replicates = 16
    windows    = 300
    seed       = 20260909
    reduction  = mean 16 matrices, then max 28 pairs

Observed calibration:

| statistic | max absolute pair correlation |
|---|---:|
| median | .032332 |
| p95 | .045294 |
| p99 | .051107 |

The existing EMIT-3 gate `.10` is `1.957x` the null p99. The deterministic
calibration is recomputed into every formal artifact. Its values document gate
feasibility; they are not used to relax the gate after seeing emitter data.

L0 alone is adjudicated against `.10`. L1 and L2 retain exactly the same
reduction but remain a reported dose-response curve.

## Remote-state check

`scripts/verify_pushed.sh` is the sole operational check for whether local HEAD
and requested evidence tags exist on origin. The formal runner requires local
HEAD, origin main, and annotated tag
`phase-G-g3-emitter-reduction-prereg` to resolve to the same commit.

## Scope of estimator selection

The topology-specific corrected two-class selector remains fixed for this
emitter run. Prospective per-cell RMSE selection is a valid future extension,
but it requires its own synthetic selection artifact and preregistration. It is
not inserted immediately before the real-time run, and no candidate may restore
the known-invalid white lag-1--2 estimator without reopening G-A012.

**G-L85:** when a gate maximizes over many comparisons, aggregation order is
part of the estimand. Reduce independent repetitions before applying the tail-
amplifying maximum, and calibrate that exact operator under its null.

Mininet remains prohibited until the amended L0 emitter gates pass.

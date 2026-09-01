# G-A013 — variance-aware and multi-lag persistence reporting

Signed: 2026-09-01 UTC, after the tagged G-A012 result and before execution of
the v4 artifact. Status: `SYNTHETIC_NO_NETWORK`.

G-A012 removed the analytic persistence bias caused by independent-round
covariance at lags two and three. This append-only amendment addresses the
resulting variance and checks whether reusing lags one through eight recovers
some precision. It does not rewrite the G-A012 artifact.

## Reduction audit

`DRY-T-Q` is confirmed to gate the per-link **median of 16 preregistered
replicates**, not one realization. For each estimator and link, v4 additionally
records:

    valid replicate count
    median tau
    sample SD across replicates
    approximate SE(median) = 1.253314*SD/sqrt(N)

The SE formula is an asymptotic normal diagnostic, not a replacement for the
executed Monte Carlo distribution and not a new pass threshold.

## Multi-lag estimator

For trial persistence `phi`, define corrected signal covariance at lag k:

    y_k(phi) = T*ACF_k - v_pack*c_k(phi).

For lags one through eight, fit

    log(y_k) = intercept + k*log(phi)

by weighted least squares with weight proportional to `y_k`. The fit iterates
because the analytic rounding ACF `c_k` depends on phi. Any `y_k<=0`, invalid
initial ratio, or iterate outside `(0,1)` is refused as NaN rather than clipped.
The implementation is `solve_phi_multilag` in `tools/g1_quant_model.py`.

## Pre-execution diagnostic

A disposable `/tmp` diagnostic used the unchanged stress seed and design. All
eight links returned 16/16 valid multi-lag estimates. Representative results:

| link | two-lag SD | multi-lag SD | ratio | multi-lag median |
|---|---:|---:|---:|---:|
| uA | 3.649 | 3.705 | 1.015 | 27.688 |
| ac | 3.231 | 2.422 | .749 | 29.337 |
| ad | 5.332 | 4.250 | .797 | 30.840 |
| bd | 4.817 | 3.741 | .777 | 28.833 |
| vD | 2.143 | 2.180 | 1.017 | 30.541 |

Multi-lag reduces variance materially on the difficult low-capacity class but
is not uniformly better on every finite sample. Consequently variance ratio is
reported, not gated after observation.

## Gates

The existing `DRY-T-Q` threshold remains maximum two-lag corrected median
relative bias `<=0.15`; its artifact record now makes the 16-replicate median
reduction and uncertainty explicit.

The new `DRY-T-M` requires:

    maximum multi-lag median relative tau bias <= 0.15
    valid multi-lag estimates per link          = 16/16

No gate claims that multi-lag SD must be lower on every link. Exact-population
moment controls must recover 30 s for both corrected estimators to numerical
precision.

Output:

    results/SMOKE/phase-G/g3_dryrun_a013.json

## Lessons

**G-L81:** a bias correction must report its variance again. A corrected point
estimate without replicate SD and the uncertainty of its reduction can mistake
one draw for residual bias.

**G-L82:** a provenance stop rule must be bounded by the damage it prevents.
Missing remote tags prohibit creating result evidence, but do not prohibit
writing unexecuted code. Remote state is established by querying remote refs,
not by treating a previous push transcript as permanent state.

After v4 passes, writing the real-time emitter is allowed. Mininet remains
prohibited until the separate emitter dry-run passes its preregistered gates.

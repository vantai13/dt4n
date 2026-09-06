# G′.4 — preregistration of stored-data reanalysis

Status: predictions and analysis choices frozen before executing the new tools.
This is NOT a preregistration before acquisition: G3b results and the external
review have already been seen. Original doc 66 and all signed G3b gates stand.
Tag: `phase-G2-g4-prereg`.

## Scope and predictions

No network traffic. Analyse all five existing G3b cells (9 runs, 72 link/run
series) plus the four G2 run-3 replicates (32 series). The G3b grid is not a
complete 3-by-2 grid: tau=30 has only sigma_ref=.036. G2 is a separate control.
Use NPZ metadata for capacity and dt; verify link order and source SHA256.

Conserving frame quantiser hypothesis: v = 2*(8*1442/(C*dt))^2/12;
ACF(1)=-.5, higher positive lags zero, assuming independent uniform frame
remainders at sample boundaries. Conservation alone does not imply these
distributional assumptions. Keep kappa=2 fixed, never fit it for the self-test.
Predictions from supplied review: median direct kappa 1.85–2.05,
median ACF1 -.50 +/- .02, max absolute residual correlation <=.05,
alignment minimum at lag zero. These are predictions, not acceptance gates.

## Frozen gates and implementation corrections

- M-1: residual variance minimum at lag 0 for EVERY link/run, search -3..3.
  Hold measured indices fixed; shift target with an equal-length overlap.
  Record both sides and asymmetry; do not shift an already-subtracted residual.
- M-2: all direct residual variances, correlations and summary values finite.
- M-3: max absolute residual correlation <=.15 (B-2), both Fisher-z pooled
  across replicates within a cell and individual run maxima reported; require
  both to pass so opposite signs cannot hide contamination.
- M-4: median per-link/cell kappa in [1.5,2.5], for G3b and G2 separately;
  report all per-run values and extrema rather than certifying every point
  from a pooled median.
- M-5: median per-link/cell ACF1 within .05 of -.5 in each dataset.
- M-6: RMS difference between theoretical sf and measured lag-2+ sf <=.02
  across 40 G3b cell/link medians. The guide defines this threshold but omits
  it from its adjudicator; include it before execution. Also report direct sf
  and indirect v; retain sf outliers.

Compute variance within each replicate (ddof=1), average within cell; do not
create artificial ACF pairs across replicate boundaries. Store all 28 signed
residual correlations per run and per cell, and ACF lags 1..8.
M-1 failure => STOP_ALIGNMENT; M-3 failure => DIAG_CONTAMINATION; other failures
=> FAIL, no PASS certificate. No threshold amendments after results.

## G3b addendum, diagnostic only

Recompute 72 estimates from raw NPZ, verify against recorded JSON. Fit 64 small-
tau estimates: log(tau_hat/tau) on intercept, log(sigma_ref/.028), log(tau/2),
and seven link dummies. Report OLS t interval (54 residual degrees of freedom),
HC3 and CR1 cluster-by-link/run sensitivity (8 clusters, t with 7 df). Fixed
effects do not make observations independent; few-cluster intervals are only
approximate. Report all methods, not whichever gives the narrowest interval.
Bootstrap the actual signed pooled-median statistic with 20000 draws, seed
20260906: resample the eight link identities jointly across all four cells
and keep their two replicates. Report RT-O1 and RT-O2 percentile intervals,
bootstrap SD and normal-approximation P(pass | slope=0) and slope=.2.
Range drift: report both |beta|_upper*log(.045/.028) and exact exp(bound)-1.
Do not label a log change as an exact percentage. Diagnose sf outlier and
per-link tau spread without changing original verdicts or data.

## Certificate boundaries

Generate certificate only from clean tracked worktree, with all analysis code
and input JSON committed, all inputs hashed, no dirty bypass. Certify fixed
kappa=2 conditional on this mechanism at observed dt=.1 and capacities in NPZ.
Report empirical kappa separately. Tables at other dt are MODEL PREDICTIONS,
not empirical validation; measured rho_eps maxima are not population bounds
nor automatically portable to untested dt/C/L. Keep real elapsed-time
normalisation, frame size, no-drops/backlog and same datapath as conditions.
Self-test must use actual G3b data and enforce M-6, not hardcoded rounded sf.
Do not retrospectively substitute model sf into G3b gates.

Drop the proposed telemetry decomposition grid because this reduced task tests
the residual model directly on existing evidence. Passing does not prove zero
unmodelled residual or certify arbitrary telemetry configurations.

## Custody and reporting

Append a separate doc 66 addendum (G-L107); write doc 68 with measured tables,
formula, limitations, SHA256 and certificate location. Preserve historical
artifacts. DOI remains a separate publication requirement: inspect manifest
and prepare local inventory; never invent a DOI or claim a private backup is
a public archive. Publishing requires an actual repository/account and metadata.

# G-A001 — non-degenerate G.0 amendment

This amendment was signed after auditing G.0 v1 and before the first v2 round
trip.  It does not rewrite the v1 artifact or move the original tags.

## Reason for amendment

G.0 v1 used `dt=tau/10` and `T=200*tau`.  Therefore
`phi=exp(-dt/tau)=exp(-0.1)` and `n=T/dt=2000` were constant.  With the same
seed, every tau cell reused a bit-identical standardized AR(1) sequence and
only relabelled its time units.  The near-zero spread of `tau_hat/tau` was a
degenerate-design fingerprint, not unusually strong Monte Carlo evidence.

G0-1b is also explicitly relabelled as a code-correctness check.  ACF is scale
invariant, so normalized AR(1) makes `tau_hat` independent of sigma by
construction.  Physical evidence that sigma and tau remain uncoupled belongs
to a later Mininet measurement, not this synthetic dry run.

## Locked v2 design

- Declared measurement/modulation axis: `dt in {0.05, 0.20}` seconds.  A cell
  never derives or changes dt from tau.
- Relative amplitude axis: `a in {0.2,0.4,0.6,0.8}` and
  `sigma=a*sigma_max_regime("poisson", rho_bar=0.857)`.  Absolute sigma is
  recorded in every cell.
- Tau axis: `{0.5,1,3,10,30}` seconds.
- Feasibility requires all three conditions:
  `tau >= 10*dt`, packet headroom at least 5, and the clipping-headroom gate.
- `T=200*tau`, 16 preregistered seeds per feasible cell.
- The estimator-bias simulation must run at every exact `tau/dt` ratio used by
  the v2 round trip, with the same `T/tau=200` and median-of-16 aggregation.

The pre-round-trip diagnostic used 32 Monte Carlo replicates at each deployed
`tau/dt` in `{10,15,20,50,60,150,200,600}`.  `P(pass +/-20%)` ranged from
0.969 to 1.000, so `T=200*tau` is retained.  The diagnostic artifact is
`results/SMOKE/phase-G/g0_estimator_bias_v2.json`.

## Locked v2 gates

- G0-1 through G0-6 retain their numerical thresholds from v1.
- G0-BIAS: every deployed `tau/dt` configuration must have estimated
  `P(pass G0-1) >= 0.95` under synthetic ground truth before v2 is run.
- G0-1b: at fixed `(dt,tau)`, tau-ratio spread across two or more feasible
  amplitudes is at most 0.05.  This is a code-correctness check only.
- G0-1c, anti-degeneracy positive control: at fixed `(dt,a)` with at least two
  feasible tau values, tau-ratio spread across tau is at least 0.02.
- Overall PASS requires every cell gate plus G0-1b and G0-1c on every
  evaluable group.  Non-evaluable groups remain visible and do not become
  evidence.

## New limits

- G-L8: `dt=tau/10` made v1's tau axis degenerate.  `dt` is henceforth fixed
  within a measurement configuration and recorded in every artifact.
- G-L9: absolute sigma is coupled to load headroom.  The design axis is now
  relative amplitude `a`; every artifact must also report absolute sigma, and
  sigma values are not directly comparable across different `rho_bar` values.
- G-L10: estimator calibration and deployment must share `(T/tau,tau/dt)`.
  The v2 diagnostic enumerates every deployed ratio before the round trip.

The preregistration tag for the first v2 round trip is
`phase-G-g0-amendment-v2-prereg`.  Successful closeout will use
`phase-G-g0-complete-v2`.

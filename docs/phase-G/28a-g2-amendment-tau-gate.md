# G.2 amendment — replace the stochastic tau-spread gate

Date: 2026-08-31 UTC. This amendment was written after the first G.2 algebra
run failed and before that tool was changed or rerun. The failed artifact is
preserved in Git with SHA-256
`909e873798f2aa39921d931f0f6c27a4ce2ef891ec044220db4903cec9263633`.

## Trigger

All omega-specific gates passed, including the path/link round trip, but the
preregistered auxiliary gate `INV-G2-2` failed:

    tau_hat spread across omega = 0.0587534
    fixed gate                 = 0.0500000

The maximum came from `tau=10 s`; the five medians were 9.6901, 9.7661,
9.5300, 10.1043, and 9.7882 s. Omega estimation itself had maximum absolute
median bias 0.0105 and maximum SD 0.0363, both inside their 0.05 gates.

## Root cause

The fixed 5% threshold tests sampling fluctuation of five independently drawn
sample medians, not whether omega changes the marginal time scale. A diagnostic
bootstrap from 600 fresh AR(1) tau estimates per tau gave the following null
spread distributions for five groups of 120 estimates:

| true tau | null median | null p95 | null p99 |
|---:|---:|---:|---:|
| 3 s | 0.02733 | 0.04805 | 0.05794 |
| 10 s | 0.02721 | 0.05097 | 0.06281 |
| 30 s | 0.02600 | 0.04694 | 0.05657 |

Thus the observed 0.05875 is rare but compatible with the tau=10 null at the
1% level. Choosing p95 or p99 now would be a post-outcome threshold choice and
is not adopted.

More importantly, the generator supplies an exact test. Every path and link
component is a stationary AR(1) with the same
`phi=exp(-dt/tau)`. A linear combination is therefore also AR(1), and

    Cov(rho_l(t),rho_l(t+k)) = phi^k Var(rho_l)
    ACF_l(k)                 = phi^k

for every link and every omega. The covariance and variance both vary through
the same mixture and cancel in the normalized ACF. This is the property the
old gate intended to test.

## Amendment

- `INV-G2-2` becomes an analytic gate: maximum error between the designed
  normalized lag covariance and `phi^lag`, over all links, omega values, tau
  values, and lags 1--3, must be at most `1e-12`.
- The observed finite-sample tau_hat spread remains in the artifact as
  `OBS-G2-1`, with its retired 5% threshold recorded for provenance, but it is
  explicitly `REPORTED` and cannot fail or pass G.2.
- Absolute finite-sample tau_hat bias becomes `OBS-G2-2`, also `REPORTED`.
- No omega estimator, simulation seed, sample size, feasibility condition, or
  run-length gate changes.

This amendment does not turn the failed value into a pass. It replaces a test
of the wrong random contrast with an exact test of the intended invariant and
retains the failed observation for audit.

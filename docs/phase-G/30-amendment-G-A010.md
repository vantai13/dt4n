# G-A010 — omega has no pairwise decision content under one time scale

Date: 2026-09-01 UTC. Status: `SYNTHETIC_NO_NETWORK`. No Mininet process was
started and no RAW data was created. This amendment does not withdraw the G.2
topology, covariance, feasibility, or run-length results.

## Question added after G.2

G.2 proved that `r_lm=omega*k_topo` and that every link variance is invariant
while omega is swept. It did not test whether omega survives into a downstream
decision quantity.

For a zero-mean pairwise linear margin

    Delta(t)   = c . drho(t)
    Delta_z(t) = c . drho(t-z)

and one common AR(1) decay `phi(z)` for all path and link components,

    Sigma(z) = phi(z)*Sigma
    Corr(Delta(t),Delta_z(t)) = phi(z)*V(omega)/V(omega) = phi(z)
    P(sign disagreement) = arccos(phi(z))/pi.

Omega changes `V(omega)` but that factor occurs at the same power in the
numerator and denominator. It therefore cancels from the normalized decision
correlation.

**G-L74:** an exact design axis is not necessarily a consequential axis. A
knob must be traced into the reported estimand rather than declared useful
because its immediate algebra is correct.

## Executed checks

The source was committed at `1163e412` before execution. The successful tool
run took 3.32 s with maximum RSS 62,828 KiB.

| id | quantity | observed | verdict |
|---|---|---:|---|
| DEC-0 | shared links cancel from pairwise contrasts | 0 | PASS |
| DEC-1 | common-tau omega spread in `P(flip)` | `1.11e-16` | PASS |
| DEC-2 | G.1 per-link nugget mechanism | `0.0006575` | PASS, negligible |
| DEC-3 | two time scales, maximum omega spread | `0.2134361` | PASS, PC fires |
| DEC-3-NC | `tau_p=tau_g` flat-curve control | 0 | PASS |
| DEC-4 | CostV2 nonlinearity, centered margin | `0.0134534` | REPORTED |
| DEC-5 | full four-path argmin error | not measured | DEFERRED |

DEC-1 is exact across all six path pairs. `P(flip)=0.328379` at every omega,
while `Var(omega=1)/Var(omega=0)` ranges from 1.667 to 1.908. Looking at only
the variance ratio would falsely imply a decision effect; looking at only the
flat probability would hide that the covariance structure did change.

## Measurement nugget is link-specific

The proposed diagnostic hardcoded one scalar nugget. That is invalid on the
4/6/8 Mbps topology because packet-counter variance scales with capacity. The
executed tool instead verifies the G.1 artifact digest against the LIVE
certificate and reads `v_pack_future_independent_round` separately for every
link, taking the conservative per-link maximum across the three retained runs.

For P1-P2 the resulting nugget effect is `0.0006575`, below the signed upper
bound 0.01. Two time scales dominate it by **324.6x**. DEC-2 is an upper-bound
gate: PASS means the mechanism is currently negligible. If the measurement
path changes, the certificate expires and this conclusion must be recomputed.

## Operational meaning supplied by two time scales

Let the path processes use `tau_p` and link-private processes use `tau_g`.
Then

    r = [omega*A*phi_p(z) + (1-omega)*B*phi_g(z)]
        / [omega*A + (1-omega)*B]

and the endpoints are exact:

    omega=0 -> r=phi_g
    omega=1 -> r=phi_p.

At `(tau_p,tau_g)=(30,3) s`, `P(flip)` moves monotonically from 0.32838 to
0.11494, a spread of 0.21344. Reversing the time scales reverses the curve.
At `(3,3) s` it is exactly flat and becomes a quantitative negative control.

This gives omega a scoped operational interpretation: it selects which time
scale a pairwise stale linear margin inherits. It does not yet establish the
effect on the full four-path argmin, which remains DEC-5.

**G-L75:** under two time scales, a regime label must record
`(tau_p,tau_g,omega)`. A scalar tau is factually incomplete, just as a scalar
sigma is incomplete under the physical G.2 amplitude design.

## Nonlinearity audit correction

The draft DEC-4 used `twin.link_model`, although that module explicitly says it
is deprecated for new work. It also compared a zero-centered linear margin to
a nonlinear cost margin with a static P1-P2 offset. The raw offset is large:
`-31.63` at the uniform anchor and `-41.64` in the core-0.90 profile. Leaving it
in changes sign-flip spread to 0.04549 and 0.04076, but that is not an isolated
nonlinearity effect.

The executed audit uses `twin.cost_v2.CostV2`, `mode=poisson`, `w_loss=5000`,
and subtracts the deterministic cost margin at the profile centre before sign
comparison. Results:

| profile | centered spread | raw/confounded spread | max clip fraction |
|---|---:|---:|---:|
| all links at 0.857 | 0.00373 | 0.04549 | 0 |
| core links at 0.90 | 0.01345 | 0.04076 | 0.000019 |

The upper Monte Carlo standard error for one probability is 0.0025 and for a
spread of two probabilities is 0.00354. DEC-4 is therefore reported without a
gate or a claim that nonlinearity necessarily makes decisions easier.

**G-L76:** nonlinear decision comparisons must either match the deterministic
baseline margin or remove it explicitly. Otherwise baseline separability is
mislabelled as curvature.

## Design amendment and boundary

G.3 adds the ordered time-scale regimes `(tau_p,tau_g)=(3,3)` and `(30,3)` s.
The inverse `(3,30)` is a signed symmetry diagnostic, not a separate primary
axis. This avoids the unintended `(300,30)` cell that would result from taking
a Cartesian product of `tau_g in {3,30}` and `kappa in {1,10}`.

The original G.2 covariance identities remain valid because time scale does
not enter stationary variance. The amended temporal gate is scoped as follows:

- `tau_p=tau_g`: `INV-G2-2` applies and the single-exponential identity must
  hold.
- `tau_p!=tau_g`: a link is a mixture of two AR(1) processes. `INV-G2-2` is
  inapplicable and is replaced by PC-G2-3, which checks endpoint inheritance,
  monotonic movement, and the preregistered mixture prediction.

The full K=4 argmin consequence is still unmeasured. No statement in this
amendment upgrades the pairwise diagnostic into the paper's final endpoint.

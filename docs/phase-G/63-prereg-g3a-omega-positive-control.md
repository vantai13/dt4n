# G'.3a -- omega positive control. PREREGISTRATION

Date: 2026-09-05 UTC. STATUS: `PREREGISTRATION`. Signed before any data.

## 1. What this tests, and why G'.2 does not cover it

`G'.2` established that the mechanism does not MANUFACTURE correlation. It did
not establish that the mechanism TRANSPORTS a real one, and those are different
properties. A mechanism broken in the direction "always returns `r = 0`" passes
`KILL-1` perfectly.

This is a positive control. It is designed to fail if the coupling never
reaches the shaper, if HTB smoothing suppresses it, if the shared component
lands on the wrong links, or if the token buckets manufacture correlation of
their own when driven in common.

## 2. Model, derived rather than assumed

From the construction of `tools/g3_dryrun.physical_trace`:

    Var(rho_l) = a0^2 * deg_l                     -- independent of omega
    Cov(l, m)  = omega * a0^2 * k_topo(l, m)
    r_true     = omega * K_tilde,
                 K_tilde = k_topo / sqrt(deg_l * deg_m)

`k_topo = INCIDENCE @ INCIDENCE.T`, computed from the repository constant, not
assumed. Verified: row sums reproduce `DEGREE` exactly, and `K_tilde` takes
exactly three values on this topology.

| `K_tilde` | pairs | degree combination | members |
|---:|---:|---|---|
| 0.7071 | 8 | (1, 2) | uA-ac uA-ad uB-bc uB-bd ac-vC ad-vD bc-vC bd-vD |
| 0.5000 | 4 | (2, 2) | uA-vC uA-vD uB-vC uB-vD |
| 0.0000 | 16 | -- | uA-uB uA-bc uA-bd uB-ac uB-ad ac-ad ac-bc ac-bd ac-vD ad-bc ad-bd ad-vC bc-bd bc-vD bd-vC vC-vD |

`||K_tilde||^2 = 5.0000` exactly. `k_topo(uA, uB) = 0` is COMPUTED, so the 16
topological nulls are a proven negative control rather than an assumed one.

Attenuation enters PER PAIR, not as a scalar:

    r_meas(l,m) = omega * A(l,m) * K_tilde(l,m) + (1 - sf) * rho_eps
    A(l,m)      = sqrt(sf_l * sf_m)
    sf_l        = intercept of the lag 2..8 ACF fit (G-A019), which agrees
                  with the direct 1 - Var(eps)/Var(rho) measurement to 0.0024

    M           = A * K_tilde   (elementwise)
    omega_hat   = <R_hat, M> / <M, M>      least squares through the origin

`sf_l` differs across links BY CONSTRUCTION (`G-L104`): `sigma_l` scales with
`sqrt(deg_l)` while the nugget is set by frame size and `C*dt` and is therefore
roughly absolute. Dividing by a scalar median `sf` afterwards biases
`omega_hat`; the attenuation belongs in the design matrix.

### 2.1 The level ratio is set by `sf` structure, not by estimator bias

**G-L105:** on this topology the `K_tilde = 0.7071` group is entirely
(deg 2 x deg 1) pairs while the `K_tilde = 0.5` group is entirely
(deg 2 x deg 2). Because deg-1 links carry less signal against a common
absolute nugget, they have lower `sf`, so the high-`K` group is MORE
attenuated. The raw level ratio therefore sits near 1.388 rather than the
topological `sqrt(2) = 1.4142`, and the offset is a predictable consequence of
`G-L104` rather than a bias of the ratio estimator.

Predicted analytically from the measured per-link `sf` of run 3: `1.3880`.
Simulated with an absolute MA(1) nugget at the measured per-link variance:
`1.3894` at `omega = 1.0`. Simulated with a `sigma`-proportional nugget, which
makes `sf` uniform and erases the effect: `1.4148`.

Consequence for the gate: the ratio is evaluated on the ATTENUATION-CORRECTED
form `r/A`, which removes the `sf` structure and returns the statistic to the
exact `sqrt(2)`. The gate then tests TOPOLOGY, which is what it is for, rather
than the nugget structure. The raw ratio is reported alongside as a diagnostic.

## 3. Configuration

    omega in {0.00, 0.25, 0.50, 0.75, 1.00}
    tau = 2 s, dt = 0.1 s, T_run = 205*tau = 410 s      (signed rules T-1, T-2)
    3 replicates per level -> 15 runs -> 102 minutes
    8 links, qdisc limit 300 frames, host NOT quiesced
    tau estimator: log-linear ACF slope over lags 2..8, slope only
                   (G-A019, G-L99, G-L103)
    generator step bound to the driven step (G-L101)

Series persisted to `.npz` for every run. NOT optional: `P-7` and the `rho_eps`
recheck cannot be computed without it.

## 4. Gates, calibrated on the real INCIDENCE before signing

`results/SMOKE/phase-G2/g3a_gate_calibration.json`, 200 trials per level,
MA(1) nugget at the per-link variance measured in run 3, same estimator, same
run length. `P(pass)` is for a CORRECT mechanism at the worst level.

| Gate | Statistic | Hard | `P(pass)` | Target | Catches |
|---|---|---:|---:|---:|---|
| P-1 | `omega_hat` monotone across the 5 levels | -- | -- | -- | coupling absent |
| P-2 | `\|omega_hat - omega\|` | `<= 0.20` | 1.000 | 0.10 | magnitude not recovered |
| P-3 | `\|intercept\|` | `<= 0.08` | 1.000 | 0.05 | uniform common-mode injection |
| P-4 | `\|mean r\|` over the 16 topological nulls | `<= 0.08` | 1.000 | 0.05 | shared component on wrong links |
| P-5 | corrected ratio `r/A` at `omega = 1.00` ONLY | `[1.28, 1.55]` | 1.000 | -- | wrong shape across levels |
| P-6 | residual RMS after the one-parameter fit | `<= 0.08` | 1.000 | 0.06 | model wrong across pairs |
| P-7 | `max\|rho_eps\|`, direct from `eps`, at every level | `<= 0.040` | 1.000 | 0.030 | buckets correlate under common drive |

Measured calibration: `omega_hat` bias `<= 0.0036` at every level with
`SD` between 0.0128 and 0.0196, so `P-2` is a 10-sigma gate. If it fails, the
failure is mechanical rather than statistical.

### 4.1 Three thresholds are wider than first proposed, and why

Setting a gate from an SD assumes symmetry and normality, which a ratio of
means and a residual RMS do not have. Calibrating the absolute percentiles
instead:

| Gate | First proposed | `P(pass)` per level | Family-wise over 5 levels | Signed |
|---|---:|---:|---:|---:|
| P-3 | 0.05 | 0.990 | 0.951 | **0.08** |
| P-4 | 0.03 | 0.900 | **0.590** | **0.08** |
| P-7 | 0.030 (null p95) | ~0.95 | 0.77 | **0.040** |

`P-4` at 0.03 would have failed a correct mechanism two times in five. These
are not relaxations: they are the thresholds at which a correct mechanism
actually passes, which is the only sense in which a gate is signable. The
tighter values are retained as targets.

### 4.2 `P-5` is evaluated at `omega = 1.00` only

The corrected ratio has `SD` 0.1084 at `omega = 0.5`, 0.0558 at 0.75 and
0.0397 at 1.00. The best candidate interval reaches `P(pass) = 0.815` when
required at every level `omega >= 0.5`, against 1.000 at `omega = 1.00` alone.
The ratio is therefore signed at `omega = 1.00` only, and reported without a
gate elsewhere.

## 5. Which failure each gate catches

    coupling never reaches the shaper      -> P-1, P-2   (slope ~ 0)
    uniform common-mode injection          -> P-3, P-4   (slope can look right)
    shared component on the wrong links    -> P-5, P-6   (slope and intercept
                                                          can both look right)
    buckets correlate under common drive   -> P-7

`P-7` exists because `rho_eps ~ 0` was measured at `omega = 0`, where the eight
token buckets are driven by INDEPENDENT signals. Under a common drive they may
empty together. `NT 55`: a control is valid only in the configuration it was
calibrated in. Without `P-7` a correct-looking `omega_hat` cannot be
distinguished from buckets manufacturing their own correlation.

`P-7` additionally records `ACF(1)` of `eps` per link, which must stay near
`-0.50` (`G-L103`). A drift away from it means the measurement path itself
changed under common drive.

## 6. Stop rules

- Maximum 1 diagnostic round. Parameter fixed NOW:
  - if `P-7` fails, raise the qdisc limit from 300 to 1000 frames, rerun once
  - otherwise, rerun `omega = 1.00` only with 6 replicates, once
- A second failure stops `G'.3a` and restricts the `omega` axis to the
  closed-form result of doc 47.
- No threshold may be widened from an observation it failed. The widenings in
  section 4.1 are made HERE, before any data, from a calibration of a correct
  mechanism.

## 7. Recorded regardless of verdict

Full 28-pair `R_hat` at every level; per-link `sf`; pooled and per-link `tau`;
controller and sampler `delta` with mean/p50/p95/p99/max/rms; backlog and
drops; sink rate ratio; `target_clip_fraction`; `eps` ACF per link; the `.npz`
series for every run.

## 8. Referenced artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G2/g3a_gate_calibration.json` | `0054b3504228aae513192bc6e516332f61fc4cd02137419d153538f485da878a` |
| `tools/g3a_gate_calibration.py` | `0054b3504228aae513192bc6e516332f61fc4cd02137419d153538f485da878aTOOL` |
| `tools/g3a_omega_estimator.py` | `87d6fc1d2f1986b34a6b2eb51c20ceff867f5b5e60ee09557819dfb421ae17db` |

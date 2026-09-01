# G.3 preregistration — dry-run first, then wire the physical generator

Signed: 2026-09-01 UTC, before the first Phase-G Mininet run. No threshold in
this document may be relaxed after seeing network data. G.3 creates RAW data
only after the NumPy dry-run passes.

## Pinned inputs

| input | SHA-256 |
|---|---|
| `results/LIVE/phase-G/measurement_path_cert.json` | `45ab6135da047dac0f2d9a70424add890b341a7addb9b2789a9099b73ea0f3d2` |
| `results/SMOKE/phase-G/g2_feasibility_omega.json` | `550f043afdd6da7246b0cbad06778401e116f55d6fe3c93224d49a1d31484795` |
| `results/SMOKE/phase-G/g2_runlength.json` | `132f09dd47e9eed900dcdb7372e0d39cf302a232241ba0ccbe56eed338836725` |
| `results/SMOKE/phase-G/g2_decision_flow.json` | `0997098941a5f24929805ef12028d82053c17e6e31c83a48e728a76e7570d393` |

The G.1 certificate is conditional. A change in quantisation, wire size,
measurement interval, topology, telemetry, pacing, or scheduler isolation
expires it and stops automatic reuse of its sigma boundary.

## Mandatory pre-network stage

`tools/g3_dryrun.py` must exercise the complete synthetic contract before any
Mininet command is allowed:

1. generate path and link-private AR(1) components with two time scales;
2. map them to all eight link loads and verify stationary covariance;
3. independently round requested packet counts per 0.2 s window;
4. create target, sent-packet, and measured-counter ledgers on one grid;
5. classify quantisation from the target-to-sent residual;
6. classify measurement-path whiteness before reading residual correlation;
7. recover omega and the signed time-scale mixture;
8. evaluate the pairwise P1-P2 stale-margin diagnostic.

Any failed dry-run gate stops implementation work. Synthetic data cannot prove
the physical emitter, but it can disprove an internally inconsistent pipeline
before network time is spent.

## G3-Q — quantisation mechanism

The certificate assumes independent per-window `round()` with packet variance
`1/12` and approximately zero lag-one correlation. `rate_modulator.pace()`
currently computes a new rounded count inside each window and advances the
window origin by exactly `dt`; the eventual emitter must preserve that contract
rather than scheduling a conserved cumulative packet deadline.

Two ledgers are required and must not be conflated:

- `rho_target`: continuous requested load before packet rounding;
- `rho_sent`: exact integer packet count scheduled in that same window.

Define `eps_quant=rho_sent-rho_target`. On the first physical run, per link:

    abs(ACF1(eps_quant)) <= 0.10    independent-round confirmed
    ACF1(eps_quant) <= -0.25        cumulative mechanism detected
    otherwise                       INCONCLUSIVE

The cumulative verdict expires G.1, selects packet variance `1/6`, and forces
the G.1 boundary and G.2 feasibility grid to be recomputed. An inconclusive
verdict stops G.3 before any second cell.

The emitter also records cumulative packet count and cumulative wire bytes at
every window boundary. Cumulative drift is reported but is not corrected with
a carry accumulator, because such a correction would change the mechanism.

## Anchor design

The first run uses the only G.2 cell feasible under both quantisation models:

    mean load vector: rho_bar_l = 0.857 on every link
    sigma_ref(uA)    = 0.030348837209302317
    a0               = 171679 bit/s
    dt               = 0.2 s
    omega            in {0,.25,.5,.75,1}

All artifacts record the complete sigma vector. It ranges from about 0.02861
to 0.04292 and has spread 1.5x.

The historic `topology_v7.LOAD_MEAN` is not modified. It is a deprecated Phase
20 target vector and is inconsistent with the scalar-mean assumptions used by
the G.2 feasibility calculation. G.3 owns an explicit per-link mean vector in
its run manifest.

At the anchor, per-link clipping is checked against
`rho_bar_l+2.58*sigma_l<=0.995`. In particular, assigning `ad=0.921` at the
anchor would fail: its bound is approximately 0.884. The proposed 0.921 value
belongs only to the lower-amplitude cell where `sigma_ad` is about 0.02861.

A second, transition-adjacent cell is not selected until G3-Q resolves and a
new CostV2-based mean-vector feasibility report passes. The deprecated v1
cliff at 0.9275 is not used to preregister a new paper-operating region.

## Physical component mapping

For each path process and link-private process, the emitter needs a nonnegative
baseline packet rate large enough to carry signed AR perturbations. The dry-run
and run manifest report, for every component:

- baseline bit/s;
- target perturbation bit/s and clipped perturbation bit/s;
- component clipping fraction;
- reconstructed per-link mean, sigma, and covariance.

Component clipping above 1% or a reconstructed link-mean error above 0.005
stops the run. Passing only the aggregate link clipping gate is insufficient;
a physically impossible negative component rate can otherwise be hidden by a
positive background on the same link.

## Ordered time-scale regimes

G-A010 adds two primary ordered regimes:

    NC: (tau_p,tau_g) = (3,3) s       kappa=1
    PC: (tau_p,tau_g) = (30,3) s      kappa=10

The inverse `(3,30) s`, `kappa=0.1`, is a signed symmetry diagnostic. The grid
is not the Cartesian product `tau_g in {3,30}` by `kappa in {1,10}` because
that would silently add an unbudgeted `(tau_p,tau_g)=(300,30) s` cell.

At kappa=1:

- normalized lag covariance must be a single exponential to analytic tolerance
  in the dry-run and within Monte Carlo uncertainty physically;
- the pairwise P1-P2 `P(flip)` curve is flat in omega.

At kappa=10, PC-G2-3 replaces INV-G2-2:

- per-link ACF at preregistered lags 1--3 matches
  `omega*exp(-lag*dt/tau_p)+(1-omega)*exp(-lag*dt/tau_g)` within 0.05;
- the fitted persistence moves monotonically from the link endpoint at omega=0
  to the path endpoint at omega=1;
- the analytic pairwise P1-P2 flip curve is monotone with spread at least 0.10.

Every regime label records `(tau_p,tau_g,omega)`. A scalar tau is invalid.
The full K=4 argmin remains DEC-5 and is not silently promoted from this
pairwise diagnostic.

## Aligned measurement residual and rho-epsilon

A third series, `rho_measured`, comes from interface counters. The emitter and
sampler use a shared monotonic epoch and identical window-boundary indices.
Define

    eps_path = rho_measured - rho_sent_aligned.

This differs from `eps_quant`; using one residual for both questions would mix
packet rounding with telemetry error.

Before any cross-link residual correlation is read, gate G3-E requires every
link to satisfy

    abs(ACF1(eps_path)) <= 0.10.

If it passes, report the complete 8x8 residual correlation matrix, all 16
topological null pairs, and confidence bounds under the validated white null.
If it fails, `rho_eps` remains deferred and no correlation point estimate is
promoted as evidence.

Alignment gates, evaluated first:

- every target/sent/measured row carries the same integer `window_index`;
- no duplicate or missing index after burn-in;
- boundary timestamp mismatch p95 <= 0.02 s and maximum <= 0.05 s;
- cumulative sent-byte reconstruction agrees with the sent ledger exactly.

Any alignment failure stops G3-E regardless of apparent correlation.

## Omega round trip and duration

Omega is estimated with the existing topology LS contrast and all 16 null
pairs remain explicit controls. At every primary cell:

    abs(median(omega_hat)-omega_set) <= 0.05
    sd(omega_hat)                    <= 0.05

Duration is `T=200*max(tau_p,tau_g)`, not `200*tau_g` and never an ambiguous
scalar tau. Thus the NC duration is 600 s and the kappa=10 duration is 6000 s.
The G.2 conservative envelope required 109.3 times the slowest time scale,
leaving a 1.83x duration safety factor.

## Outputs

    results/SMOKE/phase-G/g3_dryrun.json
    results/RAW/phase-G/g3-*/rho_target.csv
    results/RAW/phase-G/g3-*/rho_sent.csv
    results/RAW/phase-G/g3-*/rho_measured.csv
    results/SMOKE/phase-G/g3_quant_mode.json
    results/SMOKE/phase-G/g3_rho_eps.json
    results/SMOKE/phase-G/g3_omega_roundtrip.json
    docs/phase-G/32-g3-results.md

RAW directories remain local custody under the existing ignore policy. Compact
JSON receipts and their input hashes are committed.

## Stop conditions

- Any dry-run gate fails: do not start Mininet.
- G3-Q is INCONCLUSIVE: stop after the first physical run.
- G3-Q detects cumulative pacing: expire G.1 and recompute before proceeding.
- Alignment gate fails: do not read G3-E or rho-epsilon.
- Kappa=1 omega curve is not flat within its preregistered uncertainty: stop;
  kappa=10 is inadmissible.
- G3-E fails: keep rho-epsilon deferred.
- Six elapsed days: stop and close with the claims actually established.

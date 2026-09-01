# G-A011 — sign-based G3-Q and persistent-rounding control

Signed: 2026-09-01 UTC, after the tagged G.3 NumPy dry-run and before the
amended dry-run artifact is executed. Status: `SYNTHETIC_NO_NETWORK`.

This amendment preserves the original preregistration and artifact. It does
not silently rewrite either. The old G3-Q gate is withdrawn because a targeted
diagnostic exposed a regime-dependent false stop:

    old: abs(ACF1(eps_quant)) <= 0.10  -> independent round

Independent per-window rounding is white only after the fractional packet
phase mixes. For a persistent target, adjacent requested packet counts move by
less than one quantum and the rounding errors are positively correlated. The
old magnitude gate therefore confounded target persistence with a change in
packet-counting mechanism.

## Diagnostic that triggered the amendment

The uncommitted diagnostic used the fixed lower cell
`sigma_ref(uA)=0.020232558139534878`, `tau=30 s`, `dt=0.2 s`, `n=30000`, 32
replicates and seed `20260905`. It was run before changing the classifier.

| link | step, packets | median ACF1 independent round | median ACF1 cumulative |
|---|---:|---:|---:|
| uA | .323490 | .077489 | -.500265 |
| ad | .228742 | .221612 | -.500784 |

The ad result is not sampling noise and exceeds the old absolute gate despite
using the certified independent-window `round()` mechanism. The two mechanisms
remain cleanly separated by sign.

## Replacement gates

Per physical link, with `eps_quant=rho_sent-rho_target`:

    ACF1(eps_quant) >= -0.05  -> INDEPENDENT_ROUND
    ACF1(eps_quant) <= -0.25  -> CUMULATIVE
    otherwise                 -> INCONCLUSIVE

The cumulative verdict still expires the G.1 certificate. An inconclusive
verdict still stops G.3. Only the discriminator changes from magnitude to sign.

The amended synthetic dry-run reduces replicates by taking the median ACF for
each cell and link, then applies the sign gate to the minimum of those medians.
It continues to report the maximum absolute single-replicate ACF as a
descriptive statistic, but does not confuse an extreme over many Monte Carlo
replicates with a physical one-run gate.

## Quantitative positive control

Let `step` be the standard deviation of the adjacent target increment in packet
quanta. Under a mixed fractional phase, the independent-round sawtooth gives

    ACF1_A(step) = (6/pi^2) * sum_{k>=1}
                   exp(-2*pi^2*k^2*step^2) / k^2.

`tools/g1_quant_model.py` owns this calculation as
`acf1_predicted_mechanism_a`. The positive-control gate is

    abs(ACF1_observed - ACF1_A(step)) <= 0.05

for every cell and link after the preregistered replicate reduction. The
amended dry-run also adds the previously omitted dangerous cell:

    sigma_ref(uA) = 0.020232558139534878
    (tau_p,tau_g) = (30,30) s
    omega          = 0
    n              = 30000
    replicates     = 16
    seed           = 20260906

A cumulative-floor construction on the identical targets is the negative
control. Every link must classify `CUMULATIVE`, and its median ACF1 must be
within 0.05 of `-0.5`.

## Lessons and identifier continuity

**G-L77:** a mechanism discriminator must use a feature invariant to regime
parameters. The magnitude of independent-round ACF changes with sigma, tau,
capacity and packet quantum; its nonnegative sign is stable, while cumulative
flooring remains strongly negative.

The supplied note called this lesson G-L76, but G-L76 is already assigned by
G-A010 to deterministic baseline removal. Identifiers are append-only here, so
the new lesson is G-L77.

**G-L78:** deterministic path margin is a regime variable. Every new decision
artifact that reports raw `P(flip)` must also report
`m_norm=m_static/sd(Delta)` and the centered curve. G-A010's existing artifact
already preserves raw, centered, and `m_static`; future artifacts add the
normalized value without rewriting that tagged result.

## Execution and custody

The amended output is separate from the tagged v1 artifact:

    results/SMOKE/phase-G/g3_dryrun_a011.json

No Mininet or OVS run is authorized until every amended gate passes. The old
`g3_dryrun.json` remains immutable evidence of why the magnitude-gate flaw was
noticed.

# G-A016 — two emitter gates are re-scoped to diagnostics; the estimand is gated instead

Signed: 2026-09-03 UTC, before any repetition of the emitter benchmark.
Status: `SYNTHETIC_NO_NETWORK`.

This amendment re-scopes `EMIT-2` and `EMIT-3`, adds `EMIT-3'` and
`EMIT-4'`, and does not change `EMIT-1` or `EMIT-4a`. Sections 1--4 do not
use a measured network value. Deleting every sentence that refers to the
2026-09-03 benchmark leaves the argument intact, as required by
`47-proposal-omega-as-coverage-axis.md` section 0.

## 1. EMIT-2 carries no network information

`window_sent[l,w]` is `int(round(rate_pps*dt))`: `emit_window` never breaks
its packet loop. `target_packets[l,w]` is `rate_pps*dt` by construction in
`run_replicate`. The EMIT-2 estimand is consequently a function of
`round(x)-x` alone. It is deterministic in `SEED` and contains no socket,
CPU, scheduler, or received-packet observation.

Consequence, fixed before any repetition: EMIT-2 moves to `diagnostics`.
`tools/g3_emit2_offline.py` computes and reports it without a real-time run.

## 2. EMIT-2 requires its own null calibration

G-L85 requires a gate that maximizes over comparisons to be calibrated under
the exact operator it uses. EMIT-3 received a 3,000-trial calibration in doc
41. EMIT-2 maximizes over sixteen rows and received none.
`tools/g3_emit2_null.py` supplies the missing deterministic calibration with
seeds `50000..50799` and 800 trials, using no network data.

If EMIT-2 is ever restored as a gate, its threshold must be the signed
EMIT-3 safety factor (`1.957`) times its own null p99, not a free constant.

## 3. EMIT-3 gates a proxy, so EMIT-3' gates the estimand

`window_lateness_s` is a maximum over all per-packet lateness observations in
a window. A shared host stall can therefore dominate all emitter maxima. The
emitter loop does not break and elapsed deadlines are caught up within the
window, so the campaign estimand remains the measured packet count.

Closed-form transfer bound at the signed anchor, using no measured value:

    quantum = wire_bits / (C * dt) = 11536 / (8e6 * 0.2) = 7.21e-3 load
    sigma   = 3.0348837209302317e-2                    (doc 29 anchor)
    p_e     <= GATE_OVERRUN_FRACTION = 1e-3           (EMIT-1, unchanged)

A stall displaces a packet across a window boundary only when the emitter
overruns, whose rate EMIT-1 already bounds. Even under perfect cross-link
correlation of the displacement, its variance relative to signal variance is
bounded by

    p_e * quantum^2 / sigma^2 = 5.64399e-5.

The omega round-trip tolerance is `5e-2`. The timing proxy may therefore fail
by an order of magnitude while the estimand retains nearly three orders of
margin.

EMIT-3 moves to `diagnostics`, retaining its L0/L1/L2 dose-response report.
It is replaced as a validity gate by EMIT-3', which applies the doc-41
`mean_correlation_then_max` reduction to the load residual. It is calibrated
on `N_WINDOWS-1` observations because differencing loses one boundary.

The reduced design's calibrated EMIT-3' gate is `0.202181`. Although larger
in its own units than the historical timing gate, its worst-case propagation
to the campaign estimand is bounded from signed quantities:

    bias(omega_hat) = r_e * (v_e / sigma^2) * (sum(k) / sum(k^2))
    sum(k) / sum(k^2) = 7.656854 / 5 = 1.531371
    v_e / sigma^2 <= 1 / headroom^2 <= 1 / 5^2 = 0.04   (G3-F)
    bias(omega_hat) <= 0.202181 * 0.04 * 1.531371 = 0.012385.

That is 24.8 percent of the signed omega tolerance `0.05`. At the anchor
headroom `14.58`, the corresponding bound is `0.00146`, or 2.9 percent. The
gate is loose in residual-correlation units and quantitatively tight in the
estimand's units; reducing runtime does not relax the final scientific
tolerance.

The EMIT-3' null uses white series. Serial correlation inflates the sampling
variance of a correlation estimate by Bartlett's factor
`(1+r1*r1')/(1-r1*r1')`. G3-E already requires
`|ACF1(eps_path)| <= 0.10` on every link, limiting the factor to `1.0202` in
variance and `1.010` in standard deviation. G3-E is therefore a precondition
of EMIT-3', not an independent parallel gate: EMIT-3' is inadmissible unless
G3-E passes first.

## 4. EMIT-4' observes and compensates for sampler timing

The sampler is one process reading every link. Its wake lateness enters a
nominal-interval load estimate as common mode and is indistinguishable from
`omega=1`. `tick_sampler.sample_at` records `snapshot_start-deadline`, so the
actual boundary time is recoverable exactly:

    t_actual[w] = deadline[w] + tick_lateness[w]
    dt_actual[w] = dt + tick_lateness[w] - tick_lateness[w-1]

`measurements/rho_from_counters.py` divides counter increments by the
observed interval. EMIT-4' gates the standard deviation of the resulting
common-mode correction relative to the designed signal amplitude. The
effective sampling grid is no longer exactly uniform; its relative standard
deviation and extrema are reported as limits.

## 5. Deadline phases are detuned under G-L62

Equal-capacity, equal-load links request the same packet count and otherwise
share an identical absolute deadline grid. `deadline_phase_fraction` adds a
deterministic offset below half a packet gap. It changes no packet count,
target load, or independent-round mechanism. It does change pacing, so the
G.1 certificate expires and G3-V/G3-F remain mandatory on the first physical
run.

## 6. Locked scope

- EMIT-1 remains `1e-3`.
- EMIT-4a remains 1 ms.
- The 2026-09-03 benchmark remains FAIL.
- Mininet remains prohibited until a preregistered reduced loopback benchmark
  passes EMIT-1, EMIT-3', EMIT-4a, and EMIT-4'.
- EMIT-2 and EMIT-3 remain reported at full precision as diagnostics.
- The optional merged single-process emitter is not adopted by this
  amendment.
- Host `load1` remains a diagnostic only. It has no published transfer to
  shared-stall probability and cannot block the benchmark.
- The 60-second CPU-0 no-socket probes remain intervention evidence, not
  admission evidence. Admission requires a fresh 300-second `ladder` probe:
  eight emitter-cadence processes plus sampler- and sink-labelled probes on
  the signed L0 CPU map. It decides on the worst role's 95% Wilson upper
  endpoint at the unchanged `GATE_P_STALL = 0.02`, requires the current boot,
  and is repeated live immediately before `--execute`. The probe screens
  whether a benchmark is worth starting; it does not replace EMIT-3' or claim
  that timing correlation and load-residual correlation are the same
  quantity.

**G-A016-L1:** a proxy gate must publish its transfer to the estimand before
it may block the campaign.

**G-A016-L2:** a maximum over many intra-window timing observations gates the
host's shared-stall behavior, not packet-count fidelity.

**G-A016-L3:** observe and compensate for clock timing instead of requiring a
general-purpose host to be hard real-time.

**G-A016-L4:** a proxy may move in the opposite direction to the estimand
under an intervention. Directional agreement must be demonstrated before a
proxy is promoted to a gate; PSI and load average remain diagnostic here.

**G-A016-L5:** a prediction interval is the interval written in the signed
artifact. A range restated in correspondence, even contemporaneously, is not
the record and cannot narrow it retrospectively.

## 7. Post-measurement admission addendum

Added 2026-09-04 after the floor-probe intervention result, but before the
reduced network benchmark. This addendum tightens the admission instrument
and changes no scientific gate:

- `floor` mode answers whether quiescing changed the idle host-noise floor.
- `ladder` mode supplies the representative-condition admission measurement.
  It uses all ten signed L0 roles and includes CPUs 6 and 7, whose sampler and
  sink roles share physical cores with emitters on this host.
- `ADMISSION_MIN_DURATION_S = 300` gives more than the already-signed 1.5x
  margin between `GATE_P_STALL` and the Wilson upper endpoint at the observed
  floor rate. A 60-second result at one event in 300 windows is too fragile:
  the second event would move its Wilson endpoint above the gate.
- Admission uses the worst role's Wilson endpoint, not its point estimate.
- `measured_at_unix`, `boot_id`, and a 30-minute maximum artifact age bound
  the check/use interval. `--a016 --execute` additionally requires a live
  300-second ladder probe, eliminating that interval by construction.
- Ladder timing correlation is a one-replicate, no-socket diagnostic. The
  doc-41 threshold is not applied because that null is calibrated after
  averaging sixteen replicate matrices. The diagnostic instead carries a
  reading-only null calibrated at its exact `1 x W` shape. Neither the null
  nor the signed safety-factor reference can refuse a run.

Intended preregistration tag: `phase-G-g3-a016-prereg`.

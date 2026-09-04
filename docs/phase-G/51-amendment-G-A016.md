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

EMIT-3 moves to `diagnostics`, retaining its L0/L1/L2 dose-response report.
It is replaced as a validity gate by EMIT-3', which applies the doc-41
`mean_correlation_then_max` reduction to the load residual. It is calibrated
on `N_WINDOWS-1` observations because differencing loses one boundary.

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

**G-A016-L1:** a proxy gate must publish its transfer to the estimand before
it may block the campaign.

**G-A016-L2:** a maximum over many intra-window timing observations gates the
host's shared-stall behavior, not packet-count fidelity.

**G-A016-L3:** observe and compensate for clock timing instead of requiring a
general-purpose host to be hard real-time.

Intended preregistration tag: `phase-G-g3-a016-prereg`.

# G-A015 — EMIT-4 is unsatisfiable as signed; split it, and re-anchor

Signed: 2026-09-03 UTC, after `phase-G-g3-a014-prereg` and the first emitter
benchmark, and before any repetition. Status: `CODE_ONLY_NO_BENCHMARK`.

This amendment changes exactly one gate. `EMIT-1`, `EMIT-2` and `EMIT-3` are
not touched, not relaxed, and not rewritten. Section 1 shows that `EMIT-4`
cannot be satisfied together with `EMIT-1` for reasons that follow from the
gate definitions alone, using no measurement from any run.

## 1. EMIT-1 and EMIT-4 are mutually unsatisfiable

This section cites no observed value. It follows from `emit_window`, the
sampler tick, and the two gate definitions as signed in
`41-amendment-g3-emitter-reduction.md`.

Let `p_e` be the probability that a window's emit loop finishes after
`t_end`. That is exactly the `EMIT-1` estimand: `emit_window` sends
`n_target` packets without breaking, the last deadline is
`t_end - 0.5*dt/n`, and `overrun = max(0, clock() - t_end)` is evaluated
after that send returns.

`window_sent[w]` is always `n_target`, because the loop never breaks. The
sampler reads `shared_sent_cumulative` at exactly `epoch + (w+1)*dt = t_end`.
A window with `overrun > 0` therefore yields
`snapshot_sent[w] < cumsum(window_sent)[w]`, unless the sampler's own tick is
itself at least as late as the overrun. That exception requires a SECOND
process to fail its timing, so it cannot raise the probability of agreement.
Hence

    P(alignment_exact) <= (1 - p_e)^N,
    N = N_WINDOWS * REPLICATES * len(CELLS) * len(LINKS) = 76,800 at L0.

`EMIT-1` declares `p_e <= 1e-3` acceptable. At the value its own tolerance
permits,

    (1 - 1e-3)^76800 = 4.3e-34

so `EMIT-4` fails with probability `1 - 4.3e-34` on a run that passes
`EMIT-1` at its limit. Solving `(1 - p_e)^N >= 0.50` gives `p_e <= 9.0e-06`
and `>= 0.05` gives `p_e <= 3.9e-05`: between 26 and 111 times stricter than
the tolerance `EMIT-1` grants.

The two gates are jointly satisfiable only at `p_e = 0` exactly, where the
`EMIT-1` tolerance is inoperative. A preregistration cannot simultaneously
declare a tolerance and require its absence.

**G-L96:** two signed gates must be checked for MUTUAL SATISFIABILITY before
signing. An exact boolean placed on a stochastic phenomenon and evaluated over
`N` trials is a gate on `N` and on every tolerance upstream of it, not on the
system.

## 2. EMIT-4 becomes EMIT-4a, EMIT-4b, EMIT-4c

    EMIT-4a  snapshot span p99                              <= 1 ms   UNCHANGED
    EMIT-4b  fraction of windows whose sampler tick returns
             later than that window's own margin            <= 1e-3   NEW
    EMIT-4c  alignment mismatch fraction over (link,window),
             reported split by sign, with exact delivery     <= 2e-3   NEW

`EMIT-4a` keeps the quantity the old gate reported and its threshold.
`snapshot_span_s` is measured between the first and last counter read, both
after `sleep_until` returns, so it is the width of the read and cannot
detect a late tick.

`EMIT-4b` measures the quantity the old composite depended on but never
recorded. `mininet/tick_sampler.py` now returns `tick_lateness_s`, the gap
between the absolute deadline and the moment the read began. This completes an
incomplete specification rather than moving a line: the composite already
depended on sampler timing.

Its margin is DERIVED per window, not fixed. The sampler must read at `t_end`
of window `w` before the first packet of window `w+1`, whose deadline is
`t_end + 0.5*dt/n`. The binding link is the busiest one in that next window,
and `n` is read from the sent ledger:

    margin[w] = 0.5 * dt / max_link(window_sent[:, w+1])

A constant taken at the mean load would be wrong in the direction that
matters. At `rho_bar = 0.857` the tightest margin is 0.840 ms on `uA` and
`vC`; at the campaign clip `RHO_MAX = 0.995` the same link gives 0.725 ms.
A fixed 0.840 ms would forgive exactly the busiest windows, which are the
ones most likely to break alignment.

`EMIT-4c` replaces the exact boolean. Its tolerance is derived from the two
directions in which alignment can break:

    snapshot < cumsum    the emitter finished after t_end          rate p_e
    snapshot > cumsum    the sampler read after t_end + margin     rate p_s

A mismatch requires one or the other, so by the union bound the mismatch rate
is at most `p_e + p_s`, and the gate is the sum of the two gates that bound
them: `1e-3 + 1e-3 = 2e-3`. No new number is introduced; both terms are
`GATE_OVERRUN_FRACTION`. `test/test_g3_emitter_reanchor.py` asserts that
identity so the thresholds cannot silently become free constants.

The mismatch fraction is reported SPLIT BY SIGN, and the split is
diagnostic, not cosmetic. The sampler is one process: when it wakes late all
eight links move together in the same window. The emitters are eight
processes: when they overrun they do so independently. Undershoot pointing at
eight independent failures and overshoot pointing at one correlated failure
are different repairs, and a composite that hid which had fired would repeat
the defect this amendment corrects.

Exact final delivery, `final_sent == final_received`, is retained inside
`EMIT-4c` as a boolean. It is an end-of-run total, not a sub-millisecond race,
so no tolerance is appropriate for it.

## 3. Physical cores are recorded

`emitters_per_core` is computed from LOGICAL CPUs. `cpu_preflight` now also
reports, from `/sys/devices/system/cpu/cpu*/topology/core_id`:

    physical_core_count            smt_threads_per_core
    emitter_physical_core_count    emitters_per_physical_core
    sampler_shares_core_with_emitter
    sink_shares_core_with_emitter

REPORTED, not gated. Gating any of it now, with this host's topology already
known, would be an outcome-based change.

The last two fields exist because `role_isolation` is a logical check and
cannot see SMT siblings. It is worth stating what the new fields show on the
host used for the first run, since the reader will otherwise assume logical
isolation implies physical isolation: `physical_core_count = 4`,
`smt_threads_per_core = 2`, `emitters_per_physical_core = 2.0`, and BOTH
`sampler_shares_core_with_emitter` and `sink_shares_core_with_emitter` are
true. The sampler on CPU 6 shares physical core 2 with the emitter pinned to
CPU 2. That is a candidate cause for sampler tick lateness which `EMIT-4b`
will now measure rather than assume.

## 4. Re-anchor, for the second time

Committing this amendment moves HEAD past `phase-G-g3-emitter-run-prereg`.
Per G-L89 no tag is moved. A new annotated tag
`phase-G-g3-emitter-run-2-prereg` is created at this commit and `PREREG_TAG`
is repointed to it. The gates that do NOT change across the re-anchor are
listed in `test/test_g3_emitter_reanchor.py` and asserted against literals:
`GATE_OVERRUN_FRACTION`, `GATE_QUANT_SIGN`, `GATE_QUANT_PREDICTION`,
`GATE_TIMING_CORRELATION`, `EMIT3_NULL_TRIALS`, `EMIT3_NULL_SEED`,
`REPLICATES`, `N_WINDOWS`, `SEED`, `DT_S`, `DURATION_S`, `PAYLOAD_BYTES`,
`CELLS`, and the L0/L1/L2 ladder mapping.

Note. This is the second re-anchor. A provenance rule requiring HEAD to equal
a pre-named tag forces one on every legitimate amendment. If a third becomes
necessary, the rule should be reconsidered in favour of recording the executed
tree hash inside the artifact rather than requiring a name agreed in advance.

## 5. What this amendment does NOT do

- `EMIT-1` stays at 1e-3. The observed 0.0016 is not a reason to move it; a
  quiet host is the test of whether it is achievable.
- `EMIT-3` stays at 0.10. The decomposition in doc 46 attributes the
  background to the host, so the host is what changes.
- `EMIT-2` stays at 0.05. The mechanism passed on 16 of 16 rows.
- No result of the 2026-09-03 run is reinterpreted. Its verdict remains FAIL.

## 6. Scope

Mininet remains prohibited. This amendment authorises a repetition of the
emitter benchmark only, and only after its tag is on origin and the three
provenance references agree. Any repetition on a quiet host is a NEW run in a
DIFFERENT environment, recorded as such, and is not a replacement for the run
adjudicated in doc 45.

## Artifacts

    mininet/tick_sampler.py          tick_lateness_s
    tools/g3_emitter_dryrun.py       EMIT-4a/4b/4c, physical cores, PREREG_TAG
    test/test_g3_emitter_reanchor.py derived-threshold and margin assertions

Preregistration tag: `phase-G-g3-emitter-run-2-prereg`.

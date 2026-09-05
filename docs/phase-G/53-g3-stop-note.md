# G.3 stop note -- mechanism not provisionable

Date: 2026-09-05 UTC. Status: `STOPPED_MECHANISM_NOT_PROVISIONABLE`.

This note closes the G.3 emitter branch. It adjudicates no new data, relaxes
no gate, reverses no verdict, and authorises no run. It records that the
question G.3 was asked to answer has been answered, and that the answer is a
bound on what this host can provision rather than a bound on what the emitter
can do.

## 1. Verdict

The G.3 mechanism -- open-loop per-link packet pacing driven from a userspace
deadline loop -- is NOT PROVISIONABLE under the signed L0 ladder map on the
hosts available to this project. This is a feasibility conclusion, not a
tuning failure. No repetition is authorised.

The four locked checks of the final benchmark stand exactly as measured in
`docs/phase-G/52-g-a016-reduced-loopback-results.md`. Both hard-gate failures
are preserved.

## 2. Evidence, in the order it was produced

| Source | Observation | What it excludes |
|---|---|---|
| doc 46, arm A1 `no_send` | pearson 0.9126 against baseline 0.9107 | the network path, and network I/O as the cause of the EMIT-1 overrun, which persists at 0.0025 with no packet sent |
| doc 46, arm A2 `split_sink` | pearson 0.9396, slightly above baseline | shared sink process contention |
| doc 46, arm A3 `staggered` | 0.4808, and the drop is accounted for by the calibrated mechanical baseline | synchronised window boundaries, and the coincident per-packet deadline grids of the two 594.3 pps links |
| doc 46, residual reading | the dominant term is extrinsic, a machine-wide stall source | an intrinsic-to-emitter explanation |
| doc 51d, post-quiesce probe | `p_stall_1ms` 0.0866667 to 0.00333333, window-max lateness p99 2.84169 ms to 0.0450627 ms | host load as a remediable cause; the remedy doc 46 indicated was applied and measured |
| doc 52, EMIT-3' | 0.9999864422162134 against a locked gate of 0.20218127605200112 | a tuning-scale explanation; see section 3 |
| doc 50, section 2 | exhaustive enumeration over 8 logical CPUs on 4 physical cores | observer-role physical isolation *under the signed L0 map*; see section 4 for what it does not exclude |

The closing arc is the one that matters. Doc 46 ruled out the network path,
the shared sink, and window synchronisation, and named a machine-wide stall
source as the residual. G-A016 then applied exactly that indicated remedy:
the operator quiesced the host, and doc 51d measures a 26x reduction in
`p_stall_1ms` and a 63x reduction in window-max lateness p99. The benchmark
was admitted on the quiesced host by its own same-process live probe. EMIT-3'
still returned 0.99999. The indicated remedy was applied and the mechanism
still failed.

## 3. The arithmetic that makes this structural, not incidental

A machine-wide stall of duration `delta` removes packets from every link's
window simultaneously and with the same sign. The resulting error is additive
and common-mode:

    e_l = -(delta/dt) * rho_bar          corr(e_l, e_m) -> 1

Relative to the signal under measurement, with the signed G.3 constants
`dt = 0.2 s`, `rho_bar = 0.857`, and the per-link `sigma` vector of doc 31
spanning 0.02861 to 0.030349:

    |e|/sigma = (delta/dt) * rho_bar/sigma
    delta =  5 ms  ->  0.706 .. 0.749
    delta = 50 ms  ->  7.06  .. 7.49

At `delta = 5 ms` the common-mode term is already 71 to 75 percent of the
signal being measured. This is why no amount of emitter tuning closes the
gap: the term does not scale with anything the emitter controls.

At `rho_eps -> 1` the measured correlation is
`r_meas = sf*r_true + (1-sf)*rho_eps`, which saturates near unity for any
signal fraction `sf` bounded away from 1. The observed value is the expected
behaviour of this expression, not an anomaly requiring a further mechanism.

The magnitude of the failure is best read on the null calibration rather than
on the gate ratio alone:

| Comparison | Value |
|---|---:|
| observed / locked gate | 4.946 |
| observed / null p99 `0.10331184264282121` | 9.679 |
| observed / null median `0.06568533809572381` | 15.224 |
| `1 - observed` | `1.355778e-05` |

The statistic is saturated at unity to five decimal digits. The 3,000-trial
null that produced the gate does not authorise a post-result threshold change,
and no threshold change would be adequate: the gap is not a tuning distance.

## 4. What this does NOT establish

- It does not establish that the emitter implementation is incorrect. Doc 50
  section 4 makes this distinction and it is preserved here: a FAIL on this
  host bounds what this host can provision, and the two readings lead to
  opposite repairs.
- **It does not establish that no CPU assignment on this host can physically
  isolate the observer roles.** Doc 50 section 2 states the opposite: such an
  assignment exists, for example emitters on `{0,1,4,5}` with sampler 2 and
  sink 3, but only by confining the emitters to at most two physical cores.
  What the enumeration bounds is the SIGNED L0 MAP, which spreads eight
  emitters over six logical CPUs and therefore touches all four physical
  cores. Changing that is a change to the ladder map and would require its
  own amendment. None is proposed here.
- It does not establish that disabling SMT is available as a remedy. Doc 50
  section 3 records that SMT off leaves 4 logical CPUs against a
  `MIN_LADDER_CPUS` of 8, so the ladder refuses and the adjudicated cell does
  not run at all.
- It does not establish that packet-level pacing is infeasible in general. It
  bounds this class of host: 4 physical cores, SMT on, no `isolcpus`, no
  `PREEMPT_RT`, `sched_rt_runtime_us` at 950000 of a 1000000 period, and
  hypervisor steal time not observable from the guest.
- It does not reinterpret any adjudicated result. Docs 45, 46, 49, 50, 51 and
  52 stand exactly as published.

## 5. Open items carried out of the branch, not resolved by it

- Doc 46 records that no calibration cell reproduces the observed aligned
  level (0.41) and the observed residual together. The indicated next probe,
  high shared amplitude with stalls of order 100 ms, was not run because no
  gate depended on it. It is not run here either, and no mechanism is
  asserted.
- Doc 52 lists the vC/vD-only EMIT-1 pattern as a decomposition input for a
  separately preregistered amendment. This note does not perform that
  decomposition.
- The `G-L90` identifier is defined twice with different content, in
  `docs/phase-G/43-amendment-G-A014a-corrigendum-and-reanchor.md:37` and in
  `docs/phase-G/45-g3-emitter-dryrun-results.md:106`, and `G-L96` in
  `docs/phase-G/49-amendment-G-A015-emit4-satisfiability.md:48` repeats the
  text of the latter. This is recorded as a known collision in the `G-L*`
  namespace. It is not resolved here, because resolving it would edit
  published adjudicating documents.

## 6. Custody observation recorded during closure

An untracked file `results/SMOKE/phase-G/g3_a016_benchmark.json7r1a` was found
on disk during this closure, SHA256
`faea5e75ee48224ff01432d87ddfce2a18213e9ecbea88020e7f2520cfd1d241`, mtime
2026-09-04 03:38, 13 minutes after the adjudicated benchmark artifact. The
facts established about it are:

- It is a complete, well-formed benchmark output of schema
  `dt4n.phase_g.g3_emitter_dryrun.v4`, not a truncated write.
- It records the same commit `5ba4d105cfb133d1cdb31ac962237047fb6f89fd`, the
  same status `REALTIME_LOOPBACK_NO_MININET`, and the same overall `FAIL`.
- Its embedded live probe carries `p_stall=0.0033333333333333335`, Wilson
  upper `0.007779452326555608`, and A1 `0.9817975319043042`. These are the
  values doc 52 attributes to the standalone
  `SECOND_LIVE_PROBE_NO_COMPLETED_BENCHMARK_RECEIPT`.
- Its locked checks are EMIT-1 `0.0016666666666666668` FAIL, EMIT-3'
  `0.9999885671993461` FAIL, EMIT-4a `5.577655999999999e-05` PASS, EMIT-4'
  `0.016064506196258474` PASS.
- Its filename is produced by no tool in `tools/`. The suffix defeats the
  `.gitignore` allowlist, which admits `results/**/phase-*/*.json`, so the
  file was invisible to `git status`.

Consequences, stated narrowly:

1. Doc 52's sentence that the second invocation "did not produce a
   replacement completed benchmark" is incomplete as a statement of fact. The
   second invocation did complete and did write an artifact, under a filename
   that no process reads. Doc 52 is published and is not edited; this note
   records the correction.
2. The verdict of doc 52 is unaffected in every direction. The second run
   reproduces both hard-gate failures independently, so it corroborates the
   adjudicated result rather than competing with it.
3. This artifact is NOT adjudicated and is NOT substituted for the
   benchmark's embedded same-process receipt. It is brought under git custody
   at its original filename and original bytes, as found, so that the record
   is preserved rather than tidied away.

## 7. Limit recorded

`G-L98`, defined in `docs/phase-G/54-limits-G-L98.md` and registered in
`docs/phase-23/LIMITS.md`.

## 8. Successor

Any successor preregisters a different MECHANISM, not a different gate. It is
not a continuation of this branch and does not inherit its receipts. Per doc
52, a changed emitter design or new benchmark requires a new commit, a new
preregistration record, and a new tag. Any threshold it uses must be derived
from an error budget and signed there.

## 9. Referenced artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G/g3_emit3_decomposition.json` | `f594f08272895d37ee47e88b465489a8e5d7ba1521fe0594c5ffef9c0ba29566` |
| `results/SMOKE/phase-G/g3_a016_benchmark.json` | `7683e06250e64eeacbb5356480bbd50293c4ce75758664db3fa5e5c6f45db290` |
| `results/SMOKE/phase-G/g3_emitter_dryrun.json` | `96a4a744abb2e00f457aa18b72c4bcbf5724487fd1f1fa2bdf6edca0c8423bdb` |
| `results/SMOKE/phase-G/g3_emitter_run_environment.md` | `d955ead1d3b442faba6d9cc7f0c0d5ab514f50df7fb9a5fe2458fa82b1e35851` |
| `results/SMOKE/phase-G/g3_a016_benchmark.json7r1a` (unadjudicated, section 6) | `faea5e75ee48224ff01432d87ddfce2a18213e9ecbea88020e7f2520cfd1d241` |

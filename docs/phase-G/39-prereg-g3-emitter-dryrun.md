# G.3 real-time emitter dry-run preregistration

Signed: 2026-09-01 UTC, after G-A013 and before the first emitter benchmark.
Status: `CODE_ONLY_NO_BENCHMARK`. Mininet remains prohibited.

## Provenance prerequisite

The benchmark may create a result artifact only after local HEAD, origin main,
and the annotated tag `phase-G-g3-emitter-prereg` resolve to the same commit.
The earlier `phase-G-g3-a013-pass` tag is an ancestor. The runner queries the
remote refs directly; a prior push transcript is not a substitute. Missing
provenance may block execution, but not code development.

## Hardware prerequisite

The runner requires ten distinct allowed logical CPUs:

- eight pinned emitter CPUs;
- one sampler CPU;
- one UDP sink CPU.

The CPU map and current affinity/cpuset are recorded. Duplicate or unavailable
CPUs cause refusal. The present eight-CPU development VM is intentionally too
small for the formal benchmark; unit tests may use fake clocks and sockets.

## Fixed design

- clock: `time.perf_counter()` for every deadline and snapshot;
- window: `dt=0.2 s`;
- packet payload: 1400 B; wire accounting: 1442 B;
- pacing: coarse sleep followed by spin for the final 200 us;
- mechanism: independent `round(rate_pps*dt)` in each window;
- absolute window origin: `t_start=t0+k*dt`;
- no deficit carry, packet compensation, or cumulative deadline;
- shared counters: aligned native int64 arrays;
- bench cells: anchor `(sigma_ref=.0303488372,tau=3)` and dangerous
  `(sigma_ref=.0202325581,tau=30)`;
- duration: 60 s per replicate and cell (300 windows);
- replicates: 16 per cell;
- RNG seed: `20260908`;
- sampler reads L2 shared sent counters before L3 UDP sink counters and records
  the complete snapshot span.

The UDP loopback sink exercises a real kernel socket without Mininet. Per-window
maximum packet-deadline lateness is the scheduler residual used to test shared
CPU noise; target-to-sent packet residual remains the quantisation ledger.

## Gates

| id | gate |
|---|---|
| EMIT-1 | aggregate `overrun_fraction<=.001`; every cell/link recorded |
| EMIT-2 | per cell/link median `ACF1(eps_quant)>=-.05` and prediction error `<=.05` |
| EMIT-3 | maximum absolute off-diagonal correlation of pooled per-window deadline-lateness residuals `<=.10` |
| EMIT-4 | pooled snapshot-span p99 `<=1 ms`; no missing/duplicate window index; final sent ledger equals emitter cumulative count; final UDP sink count equals final sent count |

EMIT-2 is reduced over 16 replicates because a single 60 s trace has only 300
windows and an ACF sampling error of about `.058`, larger than its prediction
gate. EMIT-3 pools 4,800 windows per cell after centering within replicate.

Any failed gate keeps Mininet prohibited. Observations remain in the artifact
without threshold relaxation.

## Outputs and custody

    results/SMOKE/phase-G/g3_emitter_dryrun.json

Only the compact JSON receipt is tracked. Packet ledgers, timing traces, and
any debug captures live below `results/RAW/phase-G/g3-*` and are already
ignored by Git.

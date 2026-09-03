# Note — what this host can and cannot provision for the emitter ladder

Status: append-only note on `docs/phase-G/49-amendment-G-A015-emit4-satisfiability.md`,
which is published at commit `29abd8e0` and is not edited. This note changes
no gate, no threshold and no verdict. It records a feasibility result about
the HOST, computed before the emitter benchmark is repeated, so that the
repetition is not planned around an assumption.

## 1. The question

Doc 49 section 3 records that on this host the sampler and the sink are SMT
siblings of spinning emitters, and that `role_isolation` reports true because
it compares logical identifiers. It does not say whether that sharing is
avoidable. Planning a repetition requires the answer, because the obvious
remedy, disabling SMT, would also halve the logical CPU count.

## 2. The answer, by exhaustive enumeration

The host reports `core_id` `{0:0, 1:1, 2:2, 3:3, 4:0, 5:1, 6:2, 7:3}`: eight
logical CPUs on four physical cores. Enumerating every assignment of emitter
CPUs, sampler and sink over those eight logical CPUs gives:

| emitter logical CPUs | sampler and sink on emitter-free physical cores |
|---:|---|
| 6 | not possible |
| 5 | not possible |
| 4 | possible, e.g. emitters `{0,1,4,5}`, sampler 2, sink 3 |
| 3 | possible |
| 2 | possible |

Physical isolation of the sampler and the sink is therefore ACHIEVABLE on
this host, but only by confining the emitters to at most two physical cores.
It is a design trade-off, not a hardware impossibility.

The signed L0 map spreads eight emitters over six logical CPUs, which touches
all four physical cores, so under that map the sharing is forced. L0 was
chosen as the least-contended rung of the ladder measured in emitters per
logical CPU; measured in emitters per PHYSICAL core it is not, because it
leaves no core free for the two observer roles.

## 3. Disabling SMT would remove the adjudicated cell

    SMT on   8 logical CPUs, 4 cores.  L0 runs; sampler and sink share cores.
    SMT off  4 logical CPUs.           MIN_LADDER_CPUS is 8, so the ladder
                                       refuses and the adjudicated cell does
                                       not run at all.

Both conditions cannot be met on this host at once under the signed map. A
repetition should therefore NOT disable SMT, and should not reboot for it.

`isolcpus` is likewise of little use here: the benchmark occupies all eight
logical CPUs, so there is no CPU left to isolate it from.

## 4. Consequence for how a repetition is read

A `FAIL` of `EMIT-3` or `EMIT-4b` on this host bounds what this host can
provision. It does not bound what the emitter can do. That distinction must
be stated in the receipt of any repetition, because the two readings lead to
opposite repairs: one changes the machine or the map, the other changes the
emitter.

If physical isolation of the observer roles is wanted, the change is to the
LADDER MAP, not to the emitter and not to any gate, and it would require its
own amendment: the map above places eight emitters on four logical CPUs, two
per logical CPU and four per physical core, which is denser in emitter
contention than the signed L0 while being cleaner in observer isolation. No
such amendment is proposed here, and no gate is relaxed. `EMIT-4b`, added by
G-A015, will now measure the sampler-side cost directly rather than leaving
it to be assumed in either direction.

## 5. One operational fact, recorded to prevent a plausible mistake

`/proc/sys/kernel/sched_rt_runtime_us` is `950000` against a period of
`1000000`. Real-time scheduling is therefore throttled at 95 percent of a
CPU per second, and a task exceeding it is stalled for the remainder of the
period. Promoting the emitters to `SCHED_FIFO` would introduce a periodic,
machine-wide, correlated stall of exactly the kind doc 46 was written to
diagnose, and would be most likely to fire on the densest ladder rung. The
value is not `-1`, so such a promotion would not hang the host, but it is not
a neutral change and is not made here.

**G-L97:** relaxing a CPU requirement from a role count to a LOGICAL CPU
count silently accepts physical-core sharing on any SMT host. Under the
signed L0 map this host cannot give the sampler and the sink an
emitter-free physical core, though another map could; `role_isolation`
reports true throughout because it compares logical identifiers. A ladder
that measures per-core contention must count PHYSICAL cores, and a host that
cannot provide them bounds the claim, not the instrument.

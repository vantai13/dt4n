# G-L98 -- common-mode floor of userspace multi-link packet pacing

Established: 2026-09-05 UTC, closing `docs/phase-G/53-g3-stop-note.md`.

## Statement

On a commodity virtualised host -- 4 physical cores, SMT enabled, no
`isolcpus`, no `PREEMPT_RT`, `sched_rt_runtime_us` at 950000 against a
1000000 period, hypervisor steal time not observable from the guest --
open-loop per-link packet pacing driven from a userspace deadline loop
carries an irreducible common-mode component in the per-link load residual,
with `rho_eps -> 1`.

The cause is arithmetic rather than implementation. A machine-wide stall of
duration `delta` deletes `(delta/dt)*n` packets from every link's window at
once and with the same sign, giving a common-mode error of relative size
`(delta/dt)*rho_bar/sigma`. With the signed G.3 constants `dt = 0.2 s`,
`rho_bar = 0.857`, and the per-link `sigma` vector of `docs/phase-G/31-prereg-g3.md`
spanning 0.02861 to 0.030349, a `delta` of 5 ms already gives 0.706 to 0.749,
that is 71 to 75 percent of the signal under measurement.

Because the term does not scale with anything the emitter controls, it is not
reachable by tuning. The measured EMIT-3' of 0.9999864422162134 exceeds the
locked gate by 4.946x and the null p99 by 9.679x, with `1 - r` equal to
`1.355778e-05`.

## What the limit does not say

It does not say the emitter implementation is defective. It does not say no
CPU assignment on this host can physically isolate the observer roles --
`docs/phase-G/50-note-smt-provisioning-limit.md` section 2 shows one exists,
at the cost of confining the emitters to at most two physical cores. What is
bounded is the mechanism under the SIGNED L0 LADDER MAP, which spreads eight
emitters over six logical CPUs and so touches all four physical cores.

Host quiescing is not a remedy. `docs/phase-G/51d-host-jitter-after-quiesce-results.md`
records a 26x reduction in `p_stall_1ms` and a 63x reduction in window-max
lateness p99, and EMIT-3' still returned 0.99999 on the quiesced host.

`SCHED_FIFO` promotion is not a remedy either, and is a hazard: with
`sched_rt_runtime_us` throttled at 95 percent of a CPU per second, a task
exceeding it is stalled for the remainder of the period, which introduces a
periodic machine-wide correlated stall of exactly the kind under diagnosis
(`docs/phase-G/50` section 5).

## Scope of the limit

The mechanism requires, at minimum: bare metal with no hypervisor, a
`PREEMPT_RT` kernel, `isolcpus` plus `nohz_full` over the emitter set, and
enough physical cores that the sampler and the sink each hold an emitter-free
physical core while the ladder still satisfies `MIN_LADDER_CPUS`. None of
these is available to this project. Disabling SMT on the present host is not
a partial remedy: it leaves 4 logical CPUs against a `MIN_LADDER_CPUS` of 8,
so the adjudicated cell does not run at all.

## What remains available

Any mechanism in which the packet schedule is enforced by the KERNEL rather
than by a userspace deadline loop is not bounded by this limit, because a
common stall then produces a common PHASE SHIFT rather than a common ADDITIVE
error. The relative variance of a phase shift is `2*delta^2/(dt*tau)`, which
at `delta = 50 ms` and `dt = 0.2 s` is `8.333e-03` for `tau = 3 s` and
`8.333e-04` for `tau = 30 s`, against `7.06` for the pacing case at the same
`delta`. That is a factor of about 847 at the shorter `tau` and about 8500 at
the longer one.

This is an argument about the FORM of the error term, not a measurement. No
kernel-enforced mechanism has been benchmarked in this project, and this
paragraph authorises no run and signs no threshold.

## Provenance

Established by `docs/phase-G/46-g3-emit3-decomposition-results.md`,
`docs/phase-G/50-note-smt-provisioning-limit.md`,
`docs/phase-G/51d-host-jitter-after-quiesce-results.md` and
`docs/phase-G/52-g-a016-reduced-loopback-results.md`; closed by
`docs/phase-G/53-g3-stop-note.md`.

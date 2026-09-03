# G.3 emitter dry-run results — FAIL

Executed: 2026-09-03 06:25--07:29 UTC, 3808 s wall clock.
Preregistration: `docs/phase-G/41-amendment-g3-emitter-reduction.md`, tag
`phase-G-g3-emitter-run-prereg` at `39de0adc`.
Provenance at launch: local HEAD = `origin/main` = prereg tag = `39de0adc`,
`provenance.pass = true`, `role_isolation = true`, 8/8 CPUs available.

## Verdict

    EMIT-1  0.0016015625        gate 0.001    FAIL
    EMIT-2  0.0577710175        gate 0.05     FAIL
    EMIT-3  0.9179140575        gate 0.10     FAIL
    EMIT-4  4.782821e-05        gate 0.001    FAIL (composite)

    G.3 EMITTER DRY-RUN: FAIL
    mininet_authorized: false

Mininet remains prohibited. No gate is relaxed and no result is set aside.

## Environment, recorded before launch

The host was NOT quiet. Six Eclipse Ditto JVM processes and a VS Code server
were running; there is no `isolcpus`; the CPU is an 8-vCPU Xeon at 2.80 GHz
with 2 threads per core, so the six L0 emitter vCPUs occupy three physical
cores. Load average at launch was 0.72. The full snapshot is
`results/SMOKE/phase-G/g3_emitter_run_environment.md`.

This was recorded BEFORE the run and is a preregistered caveat, not a
post-hoc excuse. It does not convert FAIL into PASS. A clean-host repetition,
if performed, is a NEW run in a DIFFERENT environment and is not a
replacement for this one.

`cpu_preflight` reports `emitters_per_core` in LOGICAL CPUs. With two threads
per core the true L0 spin load is 2.67 emitters per physical core, twice the
reported 1.33. The pre-flight does not record physical core count.

## Per-gate observations

### EMIT-1 --- overrun fraction 0.00271 worst, 0.00146 L0 median

The two worst links are `uA` and `vC`, which the L0 ladder map places on the
same CPU 0. `uB` and `vD` on CPU 1 rank next. The ordering matches the map.

### EMIT-2 --- one failing row of sixteen

`L0/stress/vD`: `acf1_median` 0.01932 against predicted 0.07709, absolute
error 0.05777 against the 0.05 gate. All sixteen rows have
`acf1_median >= -0.0225`, above the -0.05 sign gate, so the
`INDEPENDENT_ROUND` mechanism is confirmed on every link. What failed is
agreement with the packet-step prediction, not the mechanism.

### EMIT-3 --- 0.9179

Two same-CPU pairs carry 0.9179 (`uA`-`vC`) and 0.8462 (`uB`-`vD`). The
remaining 26 different-CPU pairs run 0.3684 to 0.4897, median 0.4511,
against the calibrated null p99 of 0.051107. The ladder is flat: L0 0.9179,
L1 0.9068, L2 0.9204. Packing eight emitters onto one core is not worse than
onto six, which removes emitter-to-core packing as the dominant term. The
decomposition of the remaining background is
`docs/phase-G/46-g3-emit3-decomposition-results.md`, which adjudicates
nothing.

### EMIT-4 --- composite

    snapshot span p99          4.783e-05 s   <= 1e-03   MET
    final_udp_delivery_exact   true                     MET
    alignment_exact            false                    NOT MET

The gate is `snap_p99 <= GATE and alignment_ok and delivery_ok`. Only
`alignment_exact` failed. No packet was lost.

## OBSERVATION --- EMIT-1 and EMIT-4 cannot both pass

Recorded as an observation of the preregistration, not as a change to it.
Any change belongs in a separate amendment.

`window_sent[w]` is always `n_target`; the emit loop never breaks. The last
packet deadline is `t_end - 0.5*dt/n`. `overrun > 0` means the loop finished
after `t_end`. The sampler snapshots at exactly `epoch + (w+1)*dt = t_end`.
A window with `overrun > 0` therefore yields
`snapshot_sent[w] < cumsum(window_sent)[w]`.

`alignment_exact` is a boolean over `300 x 16 x 2 x 8 = 76,800` sub-
millisecond races at L0. Taking the measured per-window overrun probability
as the per-tuple mismatch probability:

| per-tuple probability | expected mismatches | P(alignment_exact) |
|---|---:|---:|
| 0.00271 observed L0 max | 208.1 | 3.08e-91 |
| 0.00146 observed L0 median | 112.1 | 1.85e-49 |
| 0.00100 EMIT-1 gate boundary | 76.8 | 4.26e-34 |

Reaching `P(alignment_exact) = 0.05` requires 3.901e-05, which is 26 times
better than the `EMIT-1` gate itself; reaching 0.50 requires 9.025e-06, 111
times better. **A run that exactly satisfies `EMIT-1` still fails `EMIT-4`
with probability 1 - 4.26e-34.** The two gates are jointly satisfiable only
if overrun is exactly zero, in which case the `EMIT-1` tolerance of 0.001 is
dead letter.

Separately, `snapshot_span_s` is measured after `sleep_until` returns, so it
excludes the sampler's own wake lateness. The quantity that breaks alignment
in the sampler-late direction is not measured anywhere. The smallest slack is
0.840 ms, on `uA` and `vC`.

**G-L90:** two signed gates must be checked for MUTUAL SATISFIABILITY before
signing. A boolean with no tolerance, placed on a stochastic phenomenon over
many trials, is infeasible by construction and measures the design rather
than the system.

## Artifacts

    results/SMOKE/phase-G/g3_emitter_dryrun.json
    sha256 96a4a744abb2e00f457aa18b72c4bcbf5724487fd1f1fa2bdf6edca0c8423bdb

    results/SMOKE/phase-G/g3_emitter_run_environment.md
    sha256 d955ead1d3b442faba6d9cc7f0c0d5ab514f50df7fb9a5fe2458fa82b1e35851

## Next

`G-A015` will address the mutual satisfiability of `EMIT-1` and `EMIT-4` and
add physical core count to the pre-flight. No rerun is authorised until it is
signed.

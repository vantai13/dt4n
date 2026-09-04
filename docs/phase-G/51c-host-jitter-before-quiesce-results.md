# G-A016 host jitter — before-quiesce result and forecast

Executed: 2026-09-04 UTC, after doc 51b was recorded and before any host
quiescing or network benchmark. Status: `BEFORE_COMPLETE_AFTER_PENDING`.

## Direct no-socket measurement

The probe ran for 60 seconds on CPU 0 at the fastest-link anchor cadence:

| Quantity | Value |
|---|---:|
| packets per 200 ms window | 119 |
| windows | 300 |
| windows with max lateness >= 1 ms | 26 |
| `p_stall_1ms` | **0.0866667** |
| Wilson upper endpoint (reported finite-N context) | 0.123957 |
| window-max lateness p99 | 2.84169 ms |
| maximum packet-deadline lateness | 3.10853 ms |
| load average at start, diagnostic only | 0.464355 |
| PSI `some` delta rate | 0.00467676 |
| PSI `full` delta rate | 0 |
| steal ticks delta | **0** |
| wall time | 60.64 s |

The point estimate lies inside the preregistered before-quiesce range
`0.02--0.20`. The zero steal delta independently repeats the earlier
cumulative observation and again rejects hypervisor steal as the source over
the measured interval. PSI is interpreted through its cumulative delta, not
its rounded averages.

## Forecast made from the measured model input

The measured `p_stall_1ms=0.0866667` was fed to the conditional >=1 ms model
at the exact reduced-bench shape of eight replicates and 150 windows. Three
simulation repeats produced timing EMIT-3 values

    0.987808, 0.986800, 0.991653; mean = 0.988754.

This forecast was written before any reduced network benchmark. It agrees
with doc 51b's preregistered before-quiesce range `0.66--0.99` at its upper
edge.

As an audit of the operational admission boundary, 20 simulations at
`p_stall_1ms=0.02` forecast mean timing EMIT-3 `0.8824`. Therefore 0.02 is
not claimed to imply that the historical timing EMIT-3 passes 0.10, nor that
EMIT-3' load-residual correlation passes 0.202. It remains only a coarse
after-quiesce screen for whether the network bench is worth starting; the two
correlations are different quantities.

## Artifacts

    results/SMOKE/phase-G/host_jitter_before_quiesce.json
    sha256 242a952b9f4727ae24d9268fc7aa961f879eaa58e336e088a9d10336667150ff

    results/SMOKE/phase-G/g3_emit3_forecast_before_quiesce_a016.json
    sha256 49836216612e270bcd37331072a8d660434520594b75c705bc266382954a8773

    results/SMOKE/phase-G/g3_emit3_forecast_admission_boundary_a016.json
    sha256 6e35351a358321adbc5b2f9281a258aa39930450bfd96fffbde664cd55cbc3ff

Each artifact declares commit `73ef8e94`, which contains its generating tool,
and embeds that tool's SHA256.

## Stop state

The before-quiesce point estimate exceeds the prospective after-quiesce
admission ceiling `0.02`, as expected. No conclusion about the after-quiesce
host is drawn from it. The next measurement must be produced after running
`scripts/bench_quiesce.sh --apply` from plain tmux/SSH; that operation stops
coding agents and is intentionally not run inside this session.

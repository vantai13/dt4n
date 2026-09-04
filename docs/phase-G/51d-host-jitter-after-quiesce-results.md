# G-A016 host jitter — after-quiesce result and forecast

Executed: 2026-09-04 UTC, after the operator completed host quiescing from a
plain shell. Status: `AFTER_COMPLETE_ADMISSION_PASS_BENCH_BLOCKED_PROVENANCE`.

## Direct no-socket measurement

The same probe and cadence used for the before-quiesce baseline ran for 60
seconds on CPU 0:

| Quantity | Before | After | Change |
|---|---:|---:|---:|
| load average at start, diagnostic only | 0.464355 | 0.0712891 | -84.6% |
| windows with max lateness >= 1 ms | 26 / 300 | **1 / 300** | -25 windows |
| `p_stall_1ms` | 0.0866667 | **0.00333333** | 26x reduction |
| Wilson upper endpoint (reported finite-N context) | 0.123957 | **0.0186372** | -0.105320 |
| window-max lateness p99 | 2.84169 ms | **0.0450627 ms** | 63.1x reduction |
| window-max lateness median | 0.0179523 ms | 0.0153549 ms | -14.5% |
| maximum packet-deadline lateness | 3.10853 ms | 2.65836 ms | -14.5% |
| PSI `some` delta rate | 0.00467676 | 0.00540166 | +0.000724893 |
| PSI `full` delta rate | 0 | 0 | unchanged |
| steal ticks delta | 0 | **0** | unchanged |

The point estimate passes the preregistered operational admission ceiling
`p_stall_1ms <= 0.02`. Its Wilson upper endpoint is also below 0.02, although
the implemented gate is explicitly based on the point estimate. Every
artifact-integrity check passes: schema, scenario, duration, threshold, tool
path, tool hash, and proof that the recorded commit contains the tool.

The slight increase in PSI `some` delta rate while the deadline-tail metrics
improved substantially shows why PSI is retained as a diagnostic rather than
used as the admission variable. There was no steal time during either probe.

## Forecast made from the measured model input

The measured `p_stall_1ms=0.00333333` was fed to the conditional >=1 ms model
at the exact reduced-bench shape of eight replicates and 150 windows. Three
simulation repeats produced timing EMIT-3 values

    0.323143, 0.295983, 0.479030; mean = 0.366052.

This is a substantial reduction from the before-quiesce forecast mean
`0.988754`, but it still forecasts failure of the historical timing EMIT-3
criterion `<= 0.10`. Passing the host-jitter admission gate therefore
authorizes only the next experimental stage; it does not predict a passing
network-benchmark result.

## Artifacts

    results/SMOKE/phase-G/host_jitter_after_quiesce.json
    sha256 426579fcfe994662cbd5361eda9e696ef96089b13faa7d8454e5a9e7d391eb6e

    results/SMOKE/phase-G/g3_emit3_forecast_after_quiesce_a016.json
    sha256 ecaa54eff387181363c1801d212727820a6bf4eff6e38e867ffa0f4875fbceaf

    results/SMOKE/phase-G/g3_a016_benchmark_preflight.json
    sha256 7f5a32fd8d15fbc5fa966e0fcdedbd2ecf9c9e2fdeade246ccc34c5801b93ea8

The measurement and forecast declare commit `30f2f7da`, which contains their
generating tools, and embed the respective tool SHA256 values.

## Stop state

Host-jitter admission and CPU-environment preflight pass, but benchmark
execution remains correctly blocked: local HEAD `30f2f7da` is not yet on
`origin/main`, and the remote preregistration tag
`phase-G-g3-a016-prereg` does not exist. The preflight therefore reports
`provenance.pass=false`, `environment_pass=true`, and
`mininet_authorized=false`. No reduced network benchmark was started.

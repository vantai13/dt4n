# G-A016 host jitter — after-quiesce result and forecast

Executed: 2026-09-04 UTC, after the operator completed host quiescing from a
plain shell. Status: `FLOOR_COMPLETE_LADDER_ADMISSION_PENDING`.

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

The point estimate and its Wilson upper endpoint both fall below the original
coarse operational ceiling. The later admission addendum reclassifies this
single-process, 60-second result as a `floor` measurement: it demonstrates
the effect of quiescing but does not authorize the benchmark. Admission now
requires a fresh 300-second `ladder` measurement under the full L0 CPU-role
population and decides on the binding role's Wilson upper endpoint.

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

## Preregistered mechanistic forecast verification

Four intervals were recorded before the corresponding host measurement, and
all four later contained the observed value:

| Quantity | Predicted | Measured | In interval |
|---|---:|---:|:---:|
| `p_stall` before quiesce | 0.02--0.20 | 0.086667 | yes |
| timing EMIT-3 forecast before | 0.66--0.99 | 0.988754 | yes |
| `p_stall` after quiesce | 0.001--0.02 | 0.003333 | yes |
| timing EMIT-3 forecast after | 0.18--0.80 | 0.366052 | yes |

The accompanying prediction that quiescing would not bring timing EMIT-3
below 0.10 also held. The mechanistic model behind G-A016-L2 was therefore
forecast and verified across a 26-fold intervention; it was not fitted to
the after-quiesce result.

## PSI moved opposite to the estimand

| Quantity | Before | After | Improvement ratio |
|---|---:|---:|---:|
| `p_stall(>=1ms)` | 0.086667 | 0.003333 | 26.00x |
| lateness p99.9 | 1.086 ms | 24.0 us | 45.23x |
| window-max p99 | 2.842 ms | 45.1 us | 63.06x |
| lateness maximum | 3.109 ms | 2.658 ms | 1.17x |
| PSI `some` delta rate | 0.004677 | 0.005402 | 0.87x |

PSI `some` rose about 15 percent while the directly measured stall-window
rate fell by a factor of 26. A PSI gate would therefore have assigned the
wrong direction to this intervention. PSI remains diagnostic, establishing
G-A016-L4: directional agreement of a proxy must be demonstrated rather than
assumed.

The maximum barely moved because one 2.658 ms event remained after the
frequent tail largely disappeared. Its source is not identified by this
probe; zero steal ticks makes guest steal unsupported over both intervals,
while kernel, interrupt, firmware, or unaccounted virtualization effects
remain possible. The defensible conclusion is only that this quiesced VM was
not hard real-time during the measurement.

## No forecast is claimed for EMIT-3'

The forecast above covers timing EMIT-3, a diagnostic. The benchmark gate is
EMIT-3', a load-residual statistic. Section 3 of the amendment bounds the
timing-to-load transfer at `5.64399e-5`; the timing forecast consequently
does not predict whether EMIT-3' clears its calibrated gate near 0.202.

The reduced benchmark will be the first measurement of EMIT-3'. Its value,
PASS or FAIL, is a result rather than a confirmation check.

## Stop rule signed before the EMIT-3' run

An EMIT-3' failure does not authorize widening its gate or shortening the
benchmark. It authorizes decomposition of the sink/sampler boundary effect.
Candidate mechanisms, each requiring an amendment before it is tried, are:

1. Increase `SO_RCVBUF` or use batched `recvmmsg` on the sink read path.
2. Retain split sinks only as an expected-ineffective control, because doc 46
   branch A2 increased timing correlation.
3. Try the optional merged single-process emitter to free physical cores for
   sink and sampler roles.

## Artifacts

    results/SMOKE/phase-G/host_jitter_after_quiesce.json
    sha256 426579fcfe994662cbd5361eda9e696ef96089b13faa7d8454e5a9e7d391eb6e

    results/SMOKE/phase-G/g3_emit3_forecast_after_quiesce_a016.json
    sha256 ecaa54eff387181363c1801d212727820a6bf4eff6e38e867ffa0f4875fbceaf

    results/SMOKE/phase-G/g3_a016_benchmark_preflight.json
    sha256 9b8f041f7699f2d32912af27764fe1a333c527acfa1455d1f5b3615837898b8d

The measurement and forecast declare commit `30f2f7da`, which contains their
generating tools, and embed the respective tool SHA256 values.

## Stop state

The original five commits, including `712d92f0`, are present on
`origin/main`; the earlier statement that they were unpushed was incorrect.
The intended remote preregistration reference, named
`phase-G-g3-a016-prereg`, is still absent.

After the admission addendum, the v1 artifact is deliberately insufficient:
the 300-second ladder artifact does not yet exist, so preflight must report
`environment_pass=false`, `provenance.pass=false`, and
`mininet_authorized=false`. No reduced network benchmark was started.

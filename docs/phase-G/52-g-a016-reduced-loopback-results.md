# G-A016 reduced loopback benchmark results

Executed: 2026-09-04 UTC. Status: `FAIL_RECORDED_NO_RERUN`.

The preregistered reduced loopback benchmark completed at commit
`5ba4d105cfb133d1cdb31ac962237047fb6f89fd`. Its overall verdict is
**FAIL**: EMIT-1 and EMIT-3' failed their locked gates, while EMIT-4a and
EMIT-4' passed. In accordance with the signed stop rules, the result is kept
as measured: no replicate was repeated, no threshold was widened, and no
Mininet campaign was authorized.

## Custody and execution scope

Before execution, local HEAD, `origin/main`, and the peeled annotated tag
`phase-G-g3-a016-prereg` all resolved to the same commit:
`5ba4d105cfb133d1cdb31ac962237047fb6f89fd`. The refreshed preflight records
`provenance.pass=true`, `environment_pass=true`, and the expected
`mininet_authorized=false`. The benchmark artifact independently records the
same provenance and `status=REALTIME_LOOPBACK_NO_MININET`.

The executed design was the signed L0 anchor/stress reduction: eight
replicates per cell, 150 windows per replicate, 30 seconds per replicate,
and eight links. This is 16 real-time runs and 480 scheduled benchmark
seconds, following the mandatory 300-second live-admission probe.

The preregistration tag remains attached to the pre-execution commit. It must
not be moved to the later result-recording commit.

## Host admission and preregistered forecast

The 300-second post-quiesce ladder admitted execution. Its binding role was
the sink on CPU 7, with `p_stall=0.004` and Wilson 95% upper endpoint
`0.00869950911020438`, below the locked admission gate of 0.02. Its A1
single-replicate, no-socket timing statistic was `0.8054272956870778`, within
the preregistered range 0.10--0.85. The shape-matched `1 x 1500` mechanistic
forecast was `0.8805417869482044`; this comparison is diagnostic only.

The live probe embedded in the completed benchmark is the authoritative
same-process admission receipt for this run. It passed with binding role
`emitter-ad` on CPU 3, `p_stall=0.0026666666666666666` (4/1500), and Wilson
upper endpoint `0.006836652179307764`. The artifact age at use was
`0.0008699893951416016` seconds. Its A1 diagnostic was
`0.9745301687864898` with median absolute off-diagonal
`0.05322560695261812`; A1 was reported but was not an admission gate.

## Locked gate results

| Check | Observed | Locked gate | Verdict |
|---|---:|---:|---|
| EMIT-1, socket overrun fraction | `0.0016666666666666668` | `<= 0.001` | **FAIL** |
| EMIT-3', load-residual cross-link correlation | `0.9999864422162134` | `<= 0.20218127605200112` | **FAIL** |
| EMIT-4a, shared-tick snapshot read width | `0.000053925349999999804` | `<= 0.001` | PASS |
| EMIT-4', sampler common-mode correction ratio | `0.0161078023418152` | `<= 0.05` | PASS |

EMIT-1 counted 32 overruns in 19,200 link-windows. They were fully localized
to vC and vD: each link contributed 8/1200 windows in the anchor cell and
8/1200 in the stress cell. The other six links had zero overruns in both
cells.

EMIT-3' was `0.9999313703095389` in the anchor cell and
`0.9999864422162134` in the stress cell. Its locked gate came from a
3,000-trial null calibration with p99 `0.10331184264282121` and signed safety
factor 1.957. The observed value therefore remains a hard failure; the
calibration does not authorize a post-result threshold change.

## Non-gating diagnostics

| Diagnostic | Observed | Historical gate | Historical reading |
|---|---:|---:|---|
| EMIT-2 | `0.081700239712313` | `0.05` | FAIL, reported only |
| EMIT-3 | `0.9692137292772358` | `0.10` | FAIL, reported only |
| EMIT-4b | `0.006711409395973154` | `0.001` | FAIL, reported only |
| EMIT-4c | `0.0038541666666666668` | `0.002` | FAIL, reported only |

EMIT-4b records 16 late windows out of 2,384. EMIT-4c records 32
undershoots and 42 overshoots, while final UDP delivery remained exact.
These quantities were explicitly diagnostic under G-A016 and do not replace
the four locked checks above.

## Receipt boundary after completion

The standalone `host_jitter_live_admission.json` on disk has measurement time
after the completed benchmark and differs from the live receipt embedded in
that benchmark. It is recorded as
`SECOND_LIVE_PROBE_NO_COMPLETED_BENCHMARK_RECEIPT`: it passed with
`p_stall=0.0033333333333333335`, Wilson upper endpoint
`0.007779452326555608`, and A1 `0.9817975319043042`. The timestamps and file
ordering are consistent with a second invocation that did not produce a
replacement completed benchmark; they do not establish why it ended. It is
not substituted for the benchmark's embedded, same-process receipt.

## Decision and next boundary

The scientific stop state is final for this execution:

- preserve the overall FAIL and both hard-gate failures;
- do not rerun the benchmark and do not widen a gate from these observations;
- do not authorize Mininet;
- treat the vC/vD-only EMIT-1 pattern and the near-unit EMIT-3' dependence as
  decomposition inputs for a separately preregistered amendment.

The next permitted engineering investigation is to isolate the co-resident
vC/vD emitter path for EMIT-1 and the sink/sampler queue boundary for
EMIT-3'. Any changed emitter design or new benchmark requires a new commit,
new preregistration record, and new tag; it is not a continuation of this
receipt.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G/host_jitter_ladder_after_quiesce.json` | `f18cf02d1b7b19decbf923102cedfe8260bcc51c7ea4fcf002a5bd961db108a0` |
| `results/SMOKE/phase-G/g3_emit3_forecast_probe_shape_a016.json` | `19577f6c34f16a1d5eedf2fb7f5cdd165978d572340f83d6754664f86f9ae5b2` |
| `results/SMOKE/phase-G/g3_emit3_forecast_ladder_a016.json` | `081bacc09440fc6dac6734afe8a08ed10facc9859f899c38c4f9a2ea43bdac46` |
| `results/SMOKE/phase-G/g3_a016_benchmark_preflight.json` | `42895f11981b523bb4dd374c117b95250918fb4a813f66abf2d9d555613f5c8b` |
| `results/SMOKE/phase-G/g3_a016_benchmark.json` | `7683e06250e64eeacbb5356480bbd50293c4ce75758664db3fa5e5c6f45db290` |
| `results/SMOKE/phase-G/host_jitter_live_admission.json` | `4707ad201f6316c7c209e6b1f89d6106c317919ca58a91d7e82089670dd91bf7` |

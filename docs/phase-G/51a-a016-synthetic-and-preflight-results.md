# G-A016 synthetic calibration and network preflight

Executed: 2026-09-03 UTC. Status: `SYNTHETIC_COMPLETE_NETWORK_REFUSED`.

The G-A016 amendment was recorded before these runs. All reported scientific
values in this note came from synthetic, no-network tools. No loopback network
benchmark and no Mininet run was started.

## Results shown by the tools

| Measurement | Result | Runtime recorded by tool |
|---|---:|---:|
| EMIT-2 offline | `0.057771017504482686` | 0.152 s |
| Historical EMIT-2 gate | 0.05, `FAIL` | — |
| EMIT-2 null median | 0.0370582 | 23.909 s (800 trials) |
| EMIT-2 null p95 | 0.0553575 | — |
| EMIT-2 null p99 | 0.0655034 | — |
| `P(null > 0.05)` | 0.1075 | — |
| `P(null > 0.057771)` | 0.03625 | — |
| EMIT-2 calibrated threshold (`1.957*p99`) | 0.128190 | — |
| EMIT-3 with no shared stall | 0.0354 | 0.894 s (all stall levels) |
| EMIT-3 with `p_stall=0.0005` | 0.1140 | — |
| EMIT-3 with `p_stall=0.001` | 0.1816 | — |
| EMIT-3 with `p_stall=0.05` | 0.8997 | — |
| EMIT-3' null p99, reduced bench | 0.103312 | 0.570 s (3,000 trials) |
| EMIT-3' calibrated threshold (`1.957*p99`) | 0.202181 | — |

The offline EMIT-2 result reproduces the 2026-09-03 network benchmark value
to the displayed precision without opening a socket. In its own calibrated
null, the historical 0.05 threshold false-fails in 10.75% of trials. This is
the preregistered basis for reporting EMIT-2 as a diagnostic.

The max-per-window EMIT-3 simulation crosses its historical 0.10 gate at a
shared-stall probability of 0.0005 per 200 ms window (one opportunity per
400 seconds). This is the preregistered basis for reporting timing EMIT-3 as
a diagnostic and gating the load residual with EMIT-3' instead.

## Reduced benchmark preflight

The prepared G-A016 design is L0 anchor/stress, eight replicates per cell,
150 windows per replicate, 30 seconds per replicate. CPU logical-role checks
pass, but the formal preflight does not authorize execution:

- latest `load1 = 0.10`; this is now diagnostic rather than an admission
  variable because no transfer from load average to shared-stall probability
  is available;
- local HEAD is not yet on origin and `phase-G-g3-a016-prereg` does not yet
  exist there;
- the required `host_jitter_after_quiesce.json` artifact does not yet exist;
- the host exposes four physical cores with two SMT threads each; the sampler
  and sink logical CPUs share physical cores with emitters;
- cumulative steal time is zero. This rejects the preregistered candidate
  explanation that hypervisor steal contributes to the observed stalls and
  narrows the candidate sources to activity inside the guest;
- CPU PSI full-stall avg10 is zero, but this does not establish a quiet host.
  A 1 ms event every 400 seconds contributes only 2.5 parts per million and
  is invisible after PSI's displayed averaging and rounding. Only the change
  in PSI `total` across a measured interval is used by the new host probe.

The current preflight artifact records `environment_pass=false`,
`provenance.pass=false`, and `mininet_authorized=false`. Per the stop rule,
the approximately 11-minute loopback run and the subsequent Mininet campaign
were not started. `scripts/bench_quiesce.sh` was exercised in its safe dry-run
mode only; no service or process was stopped.

## Verification

Latest targeted G-A016/emitter/custody suite:

    50 passed in 0.71 s

The full repository suite ran for 731 seconds and reported 2,014 passed, 72
skipped, 13 deselected, and two failures. The G-A016 artifact tag-claim
failure was corrected and its custody test then passed. The remaining failure
is pre-existing and out of scope: seven already-present Phase-22 parquet files
remain listed in `KNOWN_DANGLING` in
`test/test_no_dangling_parquet_refs.py`. No Phase-22 custody data or allowlist
was changed here.

## Artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G/g3_emit2_offline_a016.json` | `cc8dbb011376af5ad655914287c74eac1a6a1a3d9377710b9fdc7704140011db` |
| `results/SMOKE/phase-G/g3_emit2_null_a016.json` | `0f76d7f8ecd920f674506d9b5ca4311b845e718a63724c79e4c7221bdef2d2a7` |
| `results/SMOKE/phase-G/g3_emit3_feasibility_a016.json` | `178d81e2259824e905dcf4f3b6ca4cb801a54ce61897aa89f565a0ef3c642d98` |
| `results/SMOKE/phase-G/g3_emit3_prime_null_a016.json` | `f6d812f88aff4d71bbc6edcc3cb93d169e78de302922702a71fd75d5fde0ef19` |
| `results/SMOKE/phase-G/g3_a016_benchmark_preflight.json` | `b0900454eaa7884a118abc94e76ad8668ce713aa123ef64888b47b50e9497fc0` |

Each synthetic JSON embeds the SHA256 of the exact tool that generated it.
The four primary synthetic artifacts were regenerated from a clean tree at
commit `68b3a219`, and each declared commit contains its generating tool.
The intended preregistration tag is represented as `git_tag_to_create`, not
as an assertion that a missing tag already exists.

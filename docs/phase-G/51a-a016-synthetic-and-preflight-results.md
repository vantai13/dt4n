# G-A016 synthetic calibration and network preflight

Executed: 2026-09-03 UTC. Status: `SYNTHETIC_COMPLETE_NETWORK_REFUSED`.

The G-A016 amendment was recorded before these runs. All reported scientific
values in this note came from synthetic, no-network tools. No loopback network
benchmark and no Mininet run was started.

## Results shown by the tools

| Measurement | Result | Runtime recorded by tool |
|---|---:|---:|
| EMIT-2 offline | `0.057771017504482686` | 0.169 s |
| Historical EMIT-2 gate | 0.05, `FAIL` | — |
| EMIT-2 null median | 0.0370582 | 23.604 s (800 trials) |
| EMIT-2 null p95 | 0.0553575 | — |
| EMIT-2 null p99 | 0.0655034 | — |
| `P(null > 0.05)` | 0.1075 | — |
| `P(null > 0.057771)` | 0.03625 | — |
| EMIT-2 calibrated threshold (`1.957*p99`) | 0.128190 | — |
| EMIT-3 with no shared stall | 0.0354 | 0.981 s (all stall levels) |
| EMIT-3 with `p_stall=0.0005` | 0.1140 | — |
| EMIT-3 with `p_stall=0.001` | 0.1816 | — |
| EMIT-3 with `p_stall=0.05` | 0.8997 | — |
| EMIT-3' null p99, reduced bench | 0.103312 | 0.574 s (3,000 trials) |
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

- latest `load1 = 0.96`; this is now diagnostic rather than an admission
  variable because no transfer from load average to shared-stall probability
  is available;
- `phase-G-g3-a016-prereg` does not yet exist on origin;
- the host exposes four physical cores with two SMT threads each; the sampler
  and sink logical CPUs share physical cores with emitters;
- cumulative steal time is zero. This rejects the preregistered candidate
  explanation that hypervisor steal contributes to the observed stalls and
  narrows the candidate sources to activity inside the guest;
- CPU PSI full-stall avg10 is zero, but this does not establish a quiet host.
  A 1 ms event every 400 seconds contributes only 2.5 parts per million and
  is invisible after PSI's displayed averaging and rounding. Only the change
  in PSI `total` across a measured interval is used by the new host probe.

That historical preflight artifact records `environment_pass=false`,
`provenance.pass=false`, and `mininet_authorized=false`. Per the stop rule then
in force,
the approximately 11-minute loopback run and the subsequent Mininet campaign
were not started. `scripts/bench_quiesce.sh` was exercised in its safe dry-run
mode only; no service or process was stopped.

## Verification

Targeted G-A016/emitter/custody suite:

    45 passed in 0.68 s

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
| `results/SMOKE/phase-G/g3_emit2_offline_a016.json` | `b64612242d61d03c33e100f484ea0f04d9e177a022fc80bcaf84963db08499fe` |
| `results/SMOKE/phase-G/g3_emit2_null_a016.json` | `8f353efee783d4bbd122f87a648576d6b57d8930383cb42d71c302eccd4edd62` |
| `results/SMOKE/phase-G/g3_emit3_feasibility_a016.json` | `071f887327fc663bc37c33e1fd4a99ac50719f9c3a5ae15764d550d9655bcfb5` |
| `results/SMOKE/phase-G/g3_emit3_prime_null_a016.json` | `7abd6ab66b1af884e5b9f9404712477b88f160c8007bf113d554d8c095261339` |
| `results/SMOKE/phase-G/g3_a016_benchmark_preflight.json` | `84954aabd6e7c067abe459c6ee85d49c897cac9eb988965ea002d7d5e6878aff` |

Each synthetic JSON embeds the SHA256 of the exact tool that generated it.
The intended preregistration tag is represented as `git_tag_to_create`, not
as an assertion that a missing tag already exists.

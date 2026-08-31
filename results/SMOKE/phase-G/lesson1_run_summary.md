# Lesson 1 - run summary

Run date: 2026-08-31 (UTC)

## Commands

```bash
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m tools.g_lesson1_verify
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m tools.g_lesson1_replay_v3
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m py_compile \
  tools/g_quant_null.py tools/g_lesson1_verify.py tools/g_lesson1_replay_v3.py
/home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m pytest -q test/test_g1_static_nc.py
```

The initial replay used no Mininet, root, or sudo. The later root-cause
investigation did use a disposable Mininet topology, `tcpdump`, and reversible
IPv6 sysctls. IPv6 was restored to `0/0` (`all/default`) and Mininet/OVS was
cleaned after every control run.

## Main measured results

- E1: `dN` has two values (`112`, `113`); when `f=0`, every window has
  exactly `112` packets and measured variance is `0.000000`.
- E2: the 200,000-window sweep matches `f(1-f)` with reported error
  `0.00%` at every tested `f`.
- Replay R2: `f(1-f)` predicts the real PASS/FAIL result on `8/8` links;
  the old pure `1/dt^2` rule predicts `3/8`.
- Corrected E3 executes the measured-`dt` normalization used by `RhoLogger`.
  Packet-equivalent `Var(rho)` converges to `1/6` from both directions by
  `jitter/gap` about `0.4`.
- Replay R3 now labels `v_measured-v_det` only as an unidentified exploratory
  residual; it is not called `v_path`.
- Replay R4 fits the cross-link phase signature at `0.07 ms` (relative
  SSE `0.104`).
- Direct RAW timing in R5 gives timestamp jitter `0.01720--0.01796 ms`.
  Steady-state `sd(dt)` is `0.02369--0.02449 ms`, and `p95-p05` is
  `0.07731--0.08055 ms`.
- Verification: all three new scripts compile, and the existing focused test
  suite reports `15 passed`.

## Correction history and unresolved mismatch

The supplied sample output is not fully reproducible from its own code:

- Its printed E1 sequence has population variance `0.187500`, not
  `0.159722`.
- The original E3 omitted measured-`dt` normalization and therefore measured
  `Var(dN)`, which grows with interval jitter. The corrected E3 now measures
  `Var(rho)` through the deployed normalization and converges to `1/6`.
- The supplied `rate_pps` formula with `C=8e6`, `rho=0.857`, and
  `wire_bytes=1442` gives `594.313454 pps`, not `594.16 pps`.
- R1 percentiles from the current 72-link artifact are approximately
  `p10=0.991`, `p90=1.995` for `f(1-f)`, while the supplied sample says
  `0.985` and `1.850`. The decisive R2 result still matches exactly (`8/8`).

The corrected E3 is reproducible, but its indirect jitter estimate (`0.07 ms`)
does not agree with direct timestamp timing (`about 0.0175 ms`). Therefore the
claim that most of the residual is sampler jitter is not identified by these
data. Per the lesson's stop condition, an additional mechanism or model
mismatch must be investigated before advancing to Lesson 2.

The indirect/direct ratio is about `3.90--4.07x`. Also, `uA` and `vC` have
identical modeled geometry but observed packet-equivalent variances `0.16707`
and `0.21987`, which a single common jitter parameter cannot explain.

## Existing-RAW forensics

`tools.g_lesson1_forensics` was run on both same-configuration repetitions:
`D/rep1` and `D_dt_0p2/rep1`.

- T1: H1 is confirmed on every link. There are 11 and 10 post-burn foreign
  byte events respectively, and every residue is exactly 70 B.
- Removing those residues changes packet-equivalent variance by at most
  `0.002935`, so H1 alone does not explain the full residual.
- T2: the signed queue criterion is not met. Only one adjacent-window packet
  shift appears on `vC` in D and `bc` in D_dt_0p2.
- T3: post-batch ledger deviation SD is only `0.0207--0.0396` packet, but the
  emitter reports `0--368` catch-up batches and maximum backlog `1--7`.
  Because the ledger is written after catch-up, this test cannot observe
  intra-batch send timing.
- T4: raw quarter max/min exceeds 1.5 on `bc` and `bd` in both runs and on
  `uA` in D_dt_0p2. This heuristic needs an `f`-specific finite-block null;
  it is not valid as a verdict near `f=0.9821`.
- T5: only `vC` in D crosses `|corr|>0.2` (`-0.206`), and this does not repeat
  (`-0.048`). Read cost is not supported as a common cause.

## Live root-cause result

The investigation continued with one IPv6-on packet capture, one exactly
matched IPv6-off run, and four additional pacing controls:

```text
                     run  pace_ms  residue support_bad   sum_excess   catchups  backlog
                 ipv6-on    2.000        8          11     +0.23192        900        5
        ipv6-off/matched    2.000        0           2     +0.05912        274        5
     ipv6-off/default-r1    2.000        0           3     +0.07508        131        5
     ipv6-off/default-r2    2.000        0           0     +0.00366        115        3
       ipv6-off/tight-r1    0.100        0           0     +0.00786         23        3
       ipv6-off/tight-r2    0.100        0           7     +1.01102         26       11
```

The 70-byte frame is conclusively ICMPv6 Router Solicitation: 14-byte
Ethernet + 40-byte IPv6 + 16-byte ICMPv6. It is locally emitted on measured
veth/OVS interfaces, so static OpenFlow drop rules do not keep it out of the
port counters. Disabling IPv6 makes every residue disappear.

The remaining full-packet residual is an intermittent host-side scheduler
event. In tight rep2, `ac`, `bd`, and `vD` all ended their largest ledger gap
at monotonic time about `5948.62544 s`, with 25--30 ms gaps and maximum
backlogs of 10, 11, and 9 packets. `ac` and `bd` then showed adjacent
deficit/surplus windows; TX and RX were identical. The Python emitter sends
all overdue packets immediately after resuming, converting descheduling into
a batch. A smaller independent `uA` stall aligns with its 113/116 pair.

Thus two causes have been identified: local IPv6 control traffic explains the
70-byte events, while non-stationary host scheduling/catch-up batches explain
the much larger whole-packet excursions. Lowering `pace_tick` reduces routine
catchups but cannot prevent an external 25--30 ms scheduling pause.

## Files

- Formula module: `tools/g_quant_null.py`
- NumPy verification: `tools/g_lesson1_verify.py`
- Real-data replay: `tools/g_lesson1_replay_v3.py`
- Full verification output: `results/SMOKE/phase-G/lesson1_verify_output.txt`
- Full replay output: `results/SMOKE/phase-G/lesson1_replay_v3_output.txt`
- Source artifact: `results/SMOKE/phase-G/g1_static_v3_smoke_detail.json`
- G-A008 amendment: `docs/phase-G/26-amendment-G-A008-quantization-jitter.md`
- Forensics script: `tools/g_lesson1_forensics.py`
- Root-cause replay: `tools/g_lesson1_root_cause.py`
- Root-cause output: `results/SMOKE/phase-G/lesson1_root_cause_output.txt`
- Packet capture: `results/RAW/phase-G/lesson1-forensics-live/rep1/control_under200.pcap`
- IPv6-off controls: `results/RAW/phase-G/lesson1-ipv6-off-default/` and
  `results/RAW/phase-G/lesson1-ipv6-off-tight/`
- Matched IPv6-off control: `results/RAW/phase-G/lesson1-ipv6-off-matched/`
- D output: `results/SMOKE/phase-G/lesson1_forensics_D_output.txt`
- D_dt_0p2 output:
  `results/SMOKE/phase-G/lesson1_forensics_D_dt_0p2_output.txt`

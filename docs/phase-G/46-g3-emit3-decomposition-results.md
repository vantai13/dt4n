# EMIT-3 decomposition — diagnostic results

Date: 2026-09-03 UTC. Status: `DIAGNOSTIC_NOT_ADJUDICATED`.

This document adjudicates nothing. It does not change the `FAIL` verdict of
`docs/phase-G/45-g3-emitter-dryrun-results.md`, renews no certificate, relaxes
no gate, and authorises no run. It answers one technical question: where does
the cross-link timing correlation background in `EMIT-3` come from.

Host environment unchanged from the 64-minute run: six Ditto JVMs and a VS
Code server, no `isolcpus`, load 0.17 at launch. That is deliberate. The
purpose of arm A0 is to REPRODUCE the observed background so the other three
arms have a baseline; cleaning the host first would have removed the thing
under study.

## Design

Four arms, all driving the same signed `emit_window` and the same
`physical_trace` rate path on the stress cell whose L0 row produced 0.9179.
Every arm sees the identical rate series for a given replicate index, so the
arms differ only in the mechanism under test.

| arm | send | private sinks | staggered epochs | hypothesis under test |
|---|:--:|:--:|:--:|---|
| A0 baseline | yes | no | no | none; reproduces the background |
| A1 no_send | no | n/a | no | network path |
| A2 split_sink | yes | yes | no | shared sink process contention |
| A3 staggered | yes | no | yes | synchronised window boundaries |

Eight replicates of 20 s per arm, 100 windows each, reduced with the doc-41
order: mean the within-replicate 8x8 matrices, then take the pairwise
maximum. The null is recalibrated for this shape: p99 `0.12551`, against the
`0.051107` of the 300-window EMIT-3 null, which must not be substituted.

## Results, two independent executions

| arm | pearson | spearman | co_spike | diffCPU median | overrun |
|---|---:|---:|---:|---:|---:|
| A0 baseline | 0.9107 | 0.4943 | 0.02500 | 0.4123 | 0.00375 |
| A1 no_send | 0.9126 | 0.4862 | 0.03125 | 0.4078 | 0.00250 |
| A2 split_sink | 0.9396 | 0.5139 | 0.03375 | 0.4248 | 0.00500 |
| A3 staggered | 0.4808 | 0.1994 | 0.01375 | 0.3035 | 0.00500 |

An earlier execution of the same design, before the tool was committed, gave
A0 0.9061, A1 0.8937, A2 0.9265, A3 0.4782 with diffCPU medians 0.4167,
0.4026, 0.4618, 0.3142. The two executions agree to about 0.02 on every arm.
Only the committed execution is the artifact; the earlier one is reported
because a replication is evidence and suppressing it would not be.

A0 reproduces the 64-minute background: 0.9107 against 0.9179, diffCPU median
0.4123 against 0.4511.

## Readings

**A1 stays high.** The network path is ruled out. This direction is
conclusive: removing the send also removes its syscall cost, so a DROP would
have been confounded, but a value that does not drop cannot be explained by
the path that was removed. Overrun persists at 0.0025 with no packet sent at
all, so the `EMIT-1` failure is not caused by network I/O either.

**A2 stays high, slightly higher.** Shared sink process contention is ruled
out. The slight increase is consistent with eight sink processes sharing the
same two sink CPUs.

**A3 drops, and the drop is accounted for.** See the next section. There is
no evidence for a synchronisation contribution.

**Therefore the dominant term is extrinsic**, a machine-wide stall source.
Cleaning the host is the indicated direction. That conclusion is bounded by
the limits below, in particular that no arm contained a sampler process.

## A3 requires a calibrated baseline, not the overlap coefficient

The naive prediction for the staggered/aligned ratio under the
no-synchronisation hypothesis is the window overlap coefficient
`1 - |i-j|/8`. That coefficient is a BIASED predictor for a MAXIMUM
statistic, and the size of its bias is not a constant: it depends on how long
the shared stalls last. It was therefore calibrated by simulation under a null
that has no synchronisation component at all, with shared stalls arriving
independently of every window boundary.

| shared stall | residual (ratio - overlap), median +- SE |
|---|---|
| 2.5 ms (point) | -0.0108 +- 0.0050 at the amplitude matching the observed aligned level |
| 25 ms | +0.0515 +- 0.0080 |
| 50 ms | +0.0773 +- 0.0100 |
| 100 ms | +0.1099 +- 0.0163 |

Observed on the host: **+0.0842** in the committed execution, **+0.127** in
the earlier one. The run-to-run spread of about 0.04 means the exact value
must not be read closely.

The synchronisation hypothesis predicts a ratio BELOW the calibrated baseline,
because staggering would remove a synchronised contribution IN ADDITION to
the mechanical decorrelation. In every calibrated cell, and in both
executions, the observed ratio sits ABOVE it. The hypothesis is not supported.

The two same-CPU pairs fall from 0.9107 and 0.8646 to 0.2675 and 0.2521,
ratios 0.294 and 0.292. Those are the pairs with `|i-j| = 6`, whose windows
overlap only 25 percent under the stagger, so their collapse is the largest
mechanical effect in the design and not an additional finding.

**A3 removes two mechanisms, not one.** Besides the synchronised window
boundaries, `uA` and `vC` carry the same 594.3 pps rate, so their per-packet
deadline grids coincide exactly when epochs are aligned. The negative
conclusion covers both, which makes it stronger than a test of window
boundaries alone would have been.

**An open observation.** The calibration grid contains no cell that
reproduces the observed aligned level (0.41) and the observed residual
together: matching the aligned level requires point stalls, which predict a
residual near -0.01, while matching the residual requires stalls of 25 to
100 ms, which drive the aligned level down to 0.03--0.16. The simple
"shared stall plus independent noise" null is therefore insufficient to
describe this host. The residual increases with shared amplitude at 100 ms
while it decreases at 25 ms, so high amplitude with stalls of order 100 ms is
the indicated next probe. It was not run because no gate depends on it. No
mechanism is asserted.

**G-L91:** a mechanical-decorrelation baseline must be calibrated by
simulation under the null whenever the estimand is an order statistic. A
geometric overlap argument gives the right answer only for instantaneous
shared events, and the bias grows with the duration of the shared cause.

## The coupling is tail-driven, and two statistics were needed to see it

Pearson runs 0.89 to 0.94 while Spearman runs 0.49 to 0.51, so the coupling is
concentrated in extreme windows rather than spread across all of them.
`co_spike_fraction` is 0.025, against an independent null of `2.341e-05`: in
100 windows, about 2.5 windows have at least six of eight links
simultaneously in their own top decile.

Neither statistic alone distinguishes a rare-shared-stall model from a
continuous-shared-component model. `co_spike` alone is consistent with rare
stalls only; a Spearman of 0.49 is not, because ranks in the other 97 percent
of windows would be independent under that model. Together they show both
components are present.

**G-L92:** when a null must be chosen for calibration, its SHAPE has to be
supported by the data rather than assumed. A tail statistic and a rank
statistic computed on the same trace discriminate between a rare-event null
and a continuous-common-component null; either one alone does not.

## Limits

Recorded in the artifact under `limits`, and repeated here because they bound
every reading above:

1. A1 removes the send syscall cost as well as the network path; only a HIGH
   A1 is conclusive.
2. A3 mechanically decorrelates the measurement; the baseline above exists
   precisely to quantify that.
3. A2 separates sink processes but leaves the sink CPU count and the shared
   loopback softirq path unchanged.
4. **No arm contains a sampler process.** The 64-minute run had one pinned to
   the first sink CPU, waking at every window boundary. A synchronised
   wake-up on that CPU is a candidate cause this experiment does NOT test.
5. `co_spike_fraction` thresholds each link at its own empirical 90th
   percentile, so a shared stall occupying more than about a tenth of the
   windows hides itself. The observed 0.025 is inside the usable range; a
   value near 0.10 would have to be read as saturation.
6. 20-second replicates give 100 windows, so the null differs from the
   300-window EMIT-3 null and the two must not be compared.

## Artifacts

    results/SMOKE/phase-G/g3_emit3_decomposition.json
    sha256 f594f08272895d37ee47e88b465489a8e5d7ba1521fe0594c5ffef9c0ba29566

    results/SMOKE/phase-G/g3_stagger_baseline.json
    sha256 b91456e97826460105b90ed8cc0f6f96fc00057d7890f28329135e8c652cc140

Reproduce with:

    python -m tools.g3_emit3_decomposition --out <path>
    python -m tools.g3_emit3_decomposition --baseline-out <path>

The first takes about 11 minutes of real time and its values depend on the
host; the second is synthetic and deterministic.

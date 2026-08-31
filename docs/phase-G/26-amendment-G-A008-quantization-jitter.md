# G-A008 — deterministic packet quantization and sampler jitter

Date: 2026-08-31 UTC.

This amendment is a `POST_HOC_REANALYSIS_EXISTING_DATA` of the already-burned
NC-G1-static v3 smoke. It changes no v3 verdict: all 9 runs remain INVALID,
no LIVE certificate is created, and the signed `0/9 INVALID` result is not
recomputed. Existing G-L1--G-L51 retain their committed meanings. The limit
identifiers below follow the requested G-L53--G-L57 allocation; G-L52 remains
unallocated in this document.

## Evidence retained

For a deterministic emitter with `N(t)=floor((t-t0)*r)` and a stable sampling
grid, `delta_N` takes two adjacent integer values. If
`n=r*dt=m+f`, its asymptotic packet-count variance is `f*(1-f)`. A 200,000
window simulation matches this law to displayed error 0.00% at all 11 tested
values of `f`. On the burned dt-control artifact, this law predicts the
observed PASS/FAIL pattern on 8/8 links; the prior pure `1/dt^2` prediction
matches 3/8. This is explanatory post-hoc evidence, not a replacement gate.

The corrected full-pipeline simulation computes
`rho=delta_N*B*8/(dt_measured*C)`. It shows deterministic-phase variance
moving toward the random-phase value `1/6` as timestamp jitter grows. Fitting
that signature across cell-D links gives `0.07 ms`, but direct RAW timing gives
only `0.01720--0.01796 ms` timestamp jitter (`sd(dt)` after the initialization
sample is `0.02369--0.02449 ms`). The mismatch means the phase-signature fit
is an artifact of a rejected model, not a second sampler-jitter measurement.

The mismatch is also visible without fitting: `uA` and `vC` have identical
`r`, `C`, and `f=0.7857`, so the sampler-jitter model predicts the same
packet-equivalent variance for both. Cell D observes `0.16707` versus
`0.21987`. A single common sampler-jitter parameter cannot explain that
link-specific separation.

## New limits

- **G-L53 (revised):** Cell-D residuals cannot be explained by one common
  sampler-jitter parameter. `uA` and `vC` share `(r,C,f)` but have
  packet-equivalent variances `0.16707` and `0.21987`, even though one
  `/proc/net/dev` read supplies all link counters per sample. Measured-dt
  normalization also bounds sampler phase randomization near `1/6`, so it
  cannot explain `vC/f(1-f)=1.31`. Direct timing (`0.01720--0.01796 ms`
  timestamp SD; `0.02369--0.02449 ms` steady interval SD) is retained. The
  `0.07 ms` indirect fit is withdrawn as an artifact of a falsified model.
- **G-L54:** Every power/null simulation must execute the complete deployed
  measurement pipeline, including normalization by measured `dt`. `Var(dN)`
  and `Var(rho)` answer different questions: interval jitter strongly changes
  packet counts, while measured-dt normalization cancels its first-order rate
  effect. This applies NT59 at the measurement-simulation layer.
- **G-L55:** `f=frac(r*dt)` is a design parameter, not an incidental product of
  `rho_target`. A future preregistration must list `f` per link and use enough
  deliberately separated values to distinguish phase-jitter and additive
  signatures. Rates near `f=0` remain useful but do not imply zero total
  instrument variance under real sampler jitter.
- **G-L56:** Variance gates for the deterministic staircase must use a
  finite-sample simulated null with the exact window count, random initial
  phase, deployed measured-`dt` normalization, and the same `ddof` convention
  as the reported estimator. The iid approximation `sqrt(2/(n-1))` is not a
  valid precision calculation for this quasi-periodic sequence. The null is
  discrete and usually much tighter, but its relative width can expand near
  `f=0` or `f=1`.
- **G-L57:** The residual is not reproducible as a fixed per-link parameter.
  Under the corrected full-pipeline finite null, `uB`, `bc`, and `bd` exceed
  the upper null in both cell-D repetitions, while `ad` lies inside in both.
  `uA`, `ac`, `vC`, and `vD` change classification between repetitions. The
  effect is real and link-specific but not stationary as a fixed nugget; no
  result may label it `v_path` before its mechanism is identified.

## Existing-RAW forensics (T1--T5)

The same script was run on `D/rep1` and `D_dt_0p2/rep1` without network use.

- **T1 confirms H1:** every link has at least one post-burn window whose TX
  byte count is not divisible by 1442. All nonzero residues are exactly 70 B;
  there are 11 events in D and 10 in D_dt_0p2. Their packet type cannot be
  recovered from counters alone because no pcap was captured.
- Removing the 70-B residues changes packet-equivalent variance by at most
  `0.002935`. The larger residuals remain and are associated with windows one
  full CBR packet outside the deterministic two-value support. Across the 16
  run-links, excess variance and the count of such windows correlate `0.993`.
- **T2 does not meet the queue criterion:** TX/RX correlation is 1.000 except
  `vC=0.977` in D and `bc=0.943` in D_dt_0p2; both have only
  `sd(TX-RX)=0.1005` packet, below the 1-packet threshold.
- **T3's post-batch deviation is small** (`sd(dev)=0.0207--0.0396` packet),
  but this statistic is measured after each due batch. Emitter metadata records
  `n_catchup=0--368` and `max_backlog=1--7`; therefore the test cannot rule out
  emitter-side intra-batch timing as a source.
- **T4 is descriptive, not yet a calibrated verdict.** The raw quarter ratio
  exceeds 1.5 for `bc` and `bd` in both runs and for `uA` in D_dt_0p2. Near
  `f=0.9821`, a finite deterministic block can have variance zero, so the
  uncalibrated max/min statistic is invalid for `bd` without a block null.
- **T5 is not reproducible:** only `vC` in D crosses the proposed absolute
  correlation threshold (`-0.206`); it is `-0.048` in D_dt_0p2.

## Live identification and controls

A new 40 s live diagnostic captured all frames at most 200 bytes while the
same static workload and counter logger ran. The exact 70-byte contaminant is
an ICMPv6 Router Solicitation (type 133) sent from link-local addresses to
`ff02::2`. Its Ethernet accounting length is `14 + 40 + 16 = 70` bytes.
`tcpdump -i any` displays 76 bytes because its Linux SLL2 cooked header is 20
bytes rather than the 14-byte Ethernet header used by `/proc/net/dev`.

This traffic is locally originated on Mininet/OVS veth interfaces. It is
therefore already present in a measured port's TX counter before any static
OpenFlow default-drop decision can protect the measurement. A reversible
control disabled IPv6 in an otherwise matched run with the same
`rho_bar=0.857` and `pace_tick=2 ms`. All post-burn non-1442-byte residues
changed from 8/8 links in the IPv6-on run to zero in the matched IPv6-off run
(784 post-burn link-windows). Four additional pacing controls also had zero
residues. IPv6 was
restored to its original host setting after each run. This establishes H1
causally, not merely by packet-size coincidence.

H1 is not the whole residual. After removing it, occasional whole-packet
deficit/surplus pairs remain. In the second tight-pacing repetition, `ac` and
`bd` simultaneously recorded 94 packets followed by 103/104 packets, while
their nominal supports were `{98,99}` and `{99,100}`. TX and RX counts were
identical, which puts the event upstream of the measured link and rejects a
queue between its two counter endpoints.

The cumulative ledgers locate the same event. The `ac`, `bd`, and `vD`
emitter processes ended their largest post-burn gaps at monotonic time
`5948.62544 s`, after gaps of 24.944, 29.589, and 26.606 ms. Their recorded
maximum due backlogs were 10, 11, and 9 packets. The emitter implementation
computes `due` after resuming and immediately sends every due packet in a
loop, so a userspace scheduling pause becomes a catch-up batch. A separate
11.862 ms ledger gap on `uA` aligns with its adjacent 113/116 packet windows.

Reducing `pace_tick` from 2.0 to 0.1 ms reduced ordinary catch-up counts, but
did not eliminate external descheduling: one tight run was clean and the
other contained the common 25--30 ms pause. Therefore the remaining mechanism
is an intermittent host-side scheduling/batch event, not a stable emitter
jitter parameter. The old post-batch `sd(dev)` statistic is blind to it
because it records only after the catch-up loop.

The root-cause disposition is now:

- **H1 confirmed:** local ICMPv6 Router Solicitation creates the exact 70-byte
  counter residue.
- **H2 rejected at the measured link:** TX and RX see the same whole-packet
  event.
- **H3/H4 confirmed:** intermittent userspace/host scheduling gaps cause
  catch-up batches and non-stationary adjacent-window deficits/surpluses.
- **H5 unsupported as a common cause:** read-cost correlation is not
  reproducible and the counter sampler stays on its deadline while affected
  emitters show link-specific pauses.

For v4, disable IPv6 on every measured interface (or filter/account control
traffic explicitly), and replace or isolate the Python userspace pacing path
with observable send timestamps and scheduler controls. Lowering
`pace_tick` alone is not a sufficient fix.

## Artifacts

- `tools/g_quant_null.py`
- `tools/g_lesson1_verify.py`
- `tools/g_lesson1_replay_v3.py`
- `tools/g_lesson1_forensics.py`
- `tools/g_lesson1_root_cause.py`
- `results/SMOKE/phase-G/lesson1_verify_output.txt`
- `results/SMOKE/phase-G/lesson1_replay_v3_output.txt`
- `results/SMOKE/phase-G/lesson1_forensics_D_output.txt`
- `results/SMOKE/phase-G/lesson1_forensics_D_dt_0p2_output.txt`
- `results/SMOKE/phase-G/lesson1_root_cause_output.txt`
- `results/RAW/phase-G/lesson1-forensics-live/rep1/control_under200.pcap`
- `results/RAW/phase-G/lesson1-forensics-live/rep1/rho_measured.csv`
- `results/RAW/phase-G/lesson1-ipv6-off-default/rep{1,2}/`
- `results/RAW/phase-G/lesson1-ipv6-off-matched/rep1/`
- `results/RAW/phase-G/lesson1-ipv6-off-tight/rep{1,2}/`
- `results/RAW/phase-G/g1-static-v3-smoke/D/rep1/rho_measured.csv`
- `results/RAW/phase-G/g1-static-v3-smoke/D/rep1/rho_measured_s1.csv`

# G'.3a omega positive control -- results

Executed: 2026-09-05 UTC. Status: `MEASURED_ADJUDICATED`.

**VERDICT: `GO`**

Preregistered in `docs/phase-G/63-prereg-g3a-omega-positive-control.md`, tag
`phase-G2-g3a-prereg`, commit `09f84a45`, signed before any data. 15 runs,
5 omega levels x 3 replicates x 410 s, 8 links, host not quiesced.

> **Read section 4 before section 3.** The artifact as produced records
> `verdict: FAIL` on `P-7`. That failure is a defect in how `P-7` was computed,
> found after the fact. Section 4 states the defect, why the correction does
> not depend on my judgement, and what was wrong with `P-7`'s calibration in
> the preregistration itself.

## 1. The mechanism transports omega

| `omega` | `omega_hat` | error | intercept | null-pair mean `r` | residual RMS | `sf` min |
|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | -0.0151 | -0.0151 | +0.0057 | +0.0070 | 0.0334 | 0.9305 |
| 0.25 | 0.2771 | +0.0271 | +0.0215 | +0.0204 | 0.0466 | 0.9266 |
| 0.50 | 0.4900 | -0.0100 | -0.0000 | +0.0008 | 0.0314 | 0.9223 |
| 0.75 | 0.7284 | -0.0216 | -0.0026 | -0.0030 | 0.0239 | 0.9192 |
| 1.00 | 1.0062 | +0.0062 | -0.0004 | +0.0001 | 0.0238 | 0.9288 |

Worst recovery error over the five levels is **0.0271** against a budget of
0.20, a margin of 7.4x. This is the property `G'.2` could not establish: a
mechanism broken toward "always returns `r = 0`" passes `KILL-1` perfectly and
fails here.

## 2. Gate results

| Gate | Statistic | Observed | Signed | Verdict |
|---|---|---:|---:|---|
| P-1 | `omega_hat` monotone across 5 levels | monotone | -- | **PASS** |
| P-2 | `max \|omega_hat - omega\|` | 0.0271 | `<= 0.20` | **PASS** (target 0.10 also met) |
| P-3 | `max \|intercept\|` | 0.0215 | `<= 0.08` | **PASS** (target 0.05 also met) |
| P-4 | `max \|mean r\|` over 16 topological nulls | 0.0204 | `<= 0.08` | **PASS** (target 0.05 also met) |
| P-5 | corrected ratio `r/A` at `omega = 1.00` | 1.4414 | `[1.28, 1.55]` | **PASS** |
| P-6 | `max` residual RMS | 0.0466 | `<= 0.08` | **PASS** (target 0.06 also met) |
| P-7 | `max \|rho_eps\|` at every level | 0.0336 | `<= 0.040` | **PASS**, see section 4 |

Every gate passes, and five of the seven also meet their tighter targets.

`P-5` deserves a note: the corrected ratio came in at **1.4414** against the
topological `sqrt(2) = 1.4142`. `G-L105` predicted that correcting for
attenuation would return the statistic to `sqrt(2)`, and it did, to 1.9
percent. The raw ratio at the same level is displaced as predicted.

Supporting instruments, at every level: backlog underrun `0.0` with zero drops;
sink rate ratio error `<= 4.6e-05`; controller `delta_rms` `<= 0.089 ms`;
`target_clip_fraction <= 1.01e-03` against the `C-1` gate of 0.01; and the
`eps` lag-1 autocorrelation held between `-0.4961` and `-0.5003`, confirming
the conserving MA(1) nugget of `G-L103` was unchanged throughout.

## 3. The hazard P-7 was written to catch did not occur

`P-7` exists because `rho_eps ~ 0` was measured at `omega = 0`, where the eight
token buckets are driven by INDEPENDENT signals, and under a COMMON drive they
might empty together and correlate.

    omega        0.00    0.25    0.50    0.75    1.00
    pooled       0.0336  0.0260  0.0200  0.0229  0.0216

`rho_eps` does not grow with `omega`. It is non-monotone, it peaks at
`omega = 0`, and the value at full common drive is LOWER than at zero. The
buckets do not correlate under common drive.

## 4. The `P-7` defect, and why the correction is not a judgement call

The artifact as produced reports `P-7 = 0.0616` and `verdict: FAIL`. That
number is the maximum over the three PER-REPLICATE maxima. `P-7`'s null, in
doc 62 section 2, is computed on the FISHER-Z POOLED statistic. Those are
different statistics with different distributions, and the implementation
compared one against the other's threshold.

**G-L106:** a gate must be computed on the same statistic as the null that set
its threshold. Pooling changes the distribution of a maximum, so "max over
pairs" pooled across replicates and "max over replicates of the per-replicate
max over pairs" are different quantities with different nulls, and a threshold
calibrated for one is meaningless applied to the other.

Both nulls, recomputed at the executed 3 replicates,
`results/SMOKE/phase-G2/g3a_readjudicated.json`:

| Statistic | null median | p95 | p99 | `P(pass 0.040)` |
|---|---:|---:|---:|---:|
| Fisher-z pooled | 0.0244 | 0.0358 | 0.0418 | 0.983 |
| max over per-replicate maxima | 0.0509 | 0.0648 | 0.0733 | **0.045** |

On the statistic as implemented, the signed gate of 0.040 sits BELOW that
statistic's own null p99. `P(pass)` is 0.045 per level and 0.000 family-wise
over five levels: **a correct mechanism could not have passed it.** That is an
objective property of the threshold, independent of what was observed.

### 4.1 The resolution does not depend on which statistic is preferred

I found this defect after seeing a `FAIL`, which is exactly the situation in
which motivated reasoning is a hazard. So the adjudication rests on the one
statement that requires no choice between the two readings:

> **Every level is inside its OWN null under BOTH statistics.**

| `omega` | pooled | `P(null >= obs)` | per-replicate | `P(null >= obs)` |
|---:|---:|---:|---:|---:|
| 0.00 | 0.0336 | 0.080 | 0.0473 | 0.705 |
| 0.25 | 0.0260 | 0.420 | 0.0447 | 0.825 |
| 0.50 | 0.0200 | 0.888 | 0.0616 | 0.098 |
| 0.75 | 0.0229 | 0.658 | 0.0587 | 0.150 |
| 1.00 | 0.0216 | 0.773 | 0.0558 | 0.245 |

The physical conclusion -- the buckets do not correlate under common drive --
holds under either reading. Only the gate arithmetic differs between them.

### 4.2 The preregistration's own P-7 calibration was wrong

Doc 63 section 4 records `P(pass) = 1.000` for `P-7`. That figure came from the
doc 62 null, which was computed at **4** replicates, while `G'.3a` executes at
**3**. At 3 replicates the correct figure for the pooled statistic is 0.983 per
level and 0.916 family-wise. This does not change the verdict, and it is
recorded because a calibration quoted in a signed preregistration should be
correct.

## 5. Disposition, and the diagnostic round

`GO`. All seven gates pass on the statistic each was calibrated for.

**The single diagnostic round remains UNSPENT.** Doc 63 section 6 fixes its
parameter: raise the qdisc limit from 300 to 1000 frames if `P-7` fails. That
remedy addresses backlog underrun, and underrun was `0.0` at every level with
zero drops. Spending a hardware change on a statistic mismatch would answer a
question nobody asked. The round is retained.

No rerun was needed to reach this adjudication: the stored `.npz` allowed the
gates to be recomputed off the host, which is what persisting the raw series
was for.

## 6. What this establishes, and what it does not

**Establishes**, for this host and configuration: the mechanism transports a
known coupling with a worst-case recovery error of 0.0271 against a 0.20
budget; the 16 topological-null pairs stay flat across all five levels; the
shape across the two signal levels matches topology once attenuation is
removed; and the token buckets do not manufacture correlation under common
drive.

**Does not establish:** anything about `omega` between the tested levels beyond
the linearity the model assumes by construction; anything about hosts other
than this one; and nothing about `tau` or `sigma` recovery, which these gates
do not test. `P-6` bounds the residual across pairs but does not prove the
model correct, only that no structure large enough to matter was left over.

## 7. Referenced artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G2/g3a_omega_sweep.json` (as measured, defect included) | `947a987f33889201034d86407c4efe78a8a9f05fe4ba5e42298ce4237b3ebe0e` |
| `results/SMOKE/phase-G2/g3a_readjudicated.json` | `351049ee17185cd2ac6909767316821b8efa9713a572716122655b1767b59757` |
| `results/SMOKE/phase-G2/g3a_omega_series.npz` | `44f87da7b5a09d7b7f9d6d50365dd6e54803765891c1d8e0b5a73656a971bf6a` |
| `results/SMOKE/phase-G2/g3a_gate_calibration.json` | `0054b3504228aae513192bc6e516332f61fc4cd02137419d153538f485da878a` |

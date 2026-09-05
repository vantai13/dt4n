# G'.2 kill test -- results

Executed: 2026-09-05 UTC. Status: `MEASURED_ADJUDICATED`.

**VERDICT: `GO*`**

Preregistered in `docs/phase-G/58-prereg-g2-kill-test.md` (tag
`phase-G2-kill-test-prereg`, commit `3149f30a`) and amended before
adjudication by `docs/phase-G/59-amendment-g2-harness-defect-and-null.md`.
This is run 2. Run 1 is recorded invalid on configuration grounds in doc 59
and is not adjudicated here.

## 1. Verdict and gate readings

Executed configuration, matching the signed one: 8 links at full campaign
concurrency, `omega = 0`, `tau = 2.0 s`, `dt = 0.1 s`, `T_run = 410 s`, 4,100
windows, 4 replicates, host NOT quiesced. The realised time constant is
confirmed by the run's own estimator: `tau_hat = 2.1027 s` against a signed
2.0 s, a ratio of 1.051.

| Gate | Observed | Signed threshold | Verdict |
|---|---:|---:|---|
| KILL-1, `max` over 28 pairs of `\|r_meas\|` | `0.0705` | hard `<= 0.20` | **PASS** |
| KILL-1 target, reported as diagnostic (doc 59 sec 3.1) | `0.0705` | `<= 0.10` | pass |
| KILL-2, shaper underrun fraction | `0.0` | `<= 0.001` | **PASS** |
| KILL-3, `v_measured/v_predicted(delta)` | `8.891e+05` | `[0.5, 3.0]` | **FAIL** |
| KILL-4, sink rate ratio error | `4.886e-05` | `<= 0.05` | **PASS** |

Doc 58 section 5 maps `r ~ 0` together with a KILL-3 ratio out of range to
`GO*`: an unmodelled INDEPENDENT nugget source, harmless to claim A under
`G-L100`, to be recorded as a limit before proceeding. Section 5 of this
document records it.

## 2. KILL-1: Prediction 1 of `H_shape` is confirmed, decisively

The observed maximum absolute correlation over 28 pairs is `0.0705`. Against
the corrected null of doc 59 section 3:

| Corrected null under `H0` | Value |
|---|---:|
| median | 0.0796 |
| p95 | 0.1107 |
| p99 | 0.1221 |
| observed | **0.0705** |

**The observed value sits below the null MEDIAN.** There is no detectable
common-mode component at all: the measurement is what one expects when every
true correlation is exactly zero and the only spread is finite-sample noise.

Per-replicate maxima were `0.1494, 0.1351, 0.1319, 0.1808`, consistent with
single-replicate noise; Fisher-z pooling over 4 replicates brings the estimate
to 0.0705, as designed.

The quantity KILL-1 measures is, by `G-L100`, the bias on claim A itself:

    bias = rho_c*v_c/(sigma^2 + v_q + v_c) = |r_meas| at omega = 0 <= 0.0705

against a budget of 0.20.

### 2.1 The comparison that motivated the whole branch

| Mechanism | Cross-link correlation of the load residual |
|---|---:|
| G.3, userspace open-loop packet pacing (doc 52, `EMIT-3'`) | `0.9999864422162134` |
| G'.2, kernel-enforced rate shaping | `0.0705` |

`G-L98` predicted that moving the schedule into the kernel converts a common
ADDITIVE error into a common PHASE SHIFT, and that the relative size of the
latter is three orders of magnitude smaller. The measurement is consistent
with that prediction: the same host, the same 8 links, the same rate path,
the same `omega = 0`, and the host deliberately left un-quiesced.

`G-L98` is therefore NOT widened. Its "What remains available" clause, which
was explicitly labelled an argument about the FORM of the error term and not
a measurement, now has a measurement behind it for this configuration.

## 3. KILL-2: the backlogged-source assumption holds

Zero underrun windows across every link and every replicate, at 5 Hz polling,
with zero drops. The 300-frame qdisc limit absorbs a controller stall of
433 ms, against a measured controller `delta_rms` of `0.0818 ms`, i.e. a
margin of about 5,000x. The mechanism never degraded toward packet pacing
during the run, so the KILL-1 result was obtained in the regime `H_shape`
describes.

## 4. KILL-3 fails as signed, and the predictor is why

    v_measured                       7.4524e-05
    v_phase = 2E[delta^2]/(dt*tau)*sigma^2   8.3815e-11   <- the signed predictor
    v_q     = (8L/(C*dt))^2/12       1.7328e-05   <- closed form, omitted
    v_measured/(v_q + v_phase)       4.301

The signed predictor of doc 58 contains ONLY the phase-shift term. Frame
quantisation is an always-present, closed-form nugget that doc 57 had already
identified as `v_q`, and it was not carried into the KILL-3 formula. Because
the measured controller `delta` is tiny, `v_phase` is 8.4e-11 and the ratio is
guaranteed to be enormous whatever the run does. **KILL-3 as written could not
have passed.**

This is a specification defect in the preregistration, and it is recorded
rather than repaired: the gate is adjudicated exactly as signed, which is a
FAIL, and the verdict mapping of doc 58 section 5 is applied to that FAIL
unchanged. The decomposition above is reported as a diagnostic and does not
alter the verdict.

**G-L102:** a residual-nugget budget must enumerate EVERY known nugget term
before it is signed. KILL-3 predicted `v` from the controller stall alone
while `v_q`, a closed-form term two orders of magnitude larger, was known and
documented in the immediately preceding amendment. A predictor that omits a
dominant known term cannot be satisfied by any run, and its failure carries no
information about the hypothesis it was written to test.

## 5. The residual nugget, and why it does not threaten claim A

Even after `v_q` is removed, a residual remains:

    v_residual = v_measured - v_q = 5.7196e-05,  76.7 percent of v_measured

Its source is not identified here, and no mechanism is asserted. What IS
established is its correlation class, and that is the property that matters:

> KILL-1 came in BELOW the null median. A common-mode nugget of this size
> would have raised `|r_meas|` far above the null. The residual is therefore
> INDEPENDENT across links to within the resolution of this test.

By `G-L100`, an independent nugget enters `bias = rho_c*v_c/(sigma^2+v)` only
through the denominator. It attenuates and cannot contaminate. It is harmless
to claim A, which is why `GO*` is a proceed state and not a stop state.

It is NOT harmless to claim C, and section 6 records that cost.

## 6. Cost to claim C: `B-1a` limit met, target missed

    total measured variance   1.2518e-03      sigma = 0.0354
    sf_hat (uncorrected)      0.9347          B-1a target 0.95, limit 0.90
    implied v                 8.1772e-05
    v_q                       1.7328e-05      21.2 percent of v
    sf after removing v_q     0.9485          still short of 0.95

The closed-form quantisation correction of doc 57 section 3 works and requires
no calibration branch, but it moves `sf` only from 0.9347 to 0.9485. `B-1a`'s
LIMIT of 0.90 is met with margin; its TARGET of 0.95 is missed by 0.0015.

Recorded consequence: at `dt = 0.1 s` the measurement path does not reach the
`sf` target that doc 55 section 2.1 chose in order to make the `rho_eps`
correction a formality. The margin argument of doc 55 section 2.1 was computed
at `sf = 0.95`; at `sf = 0.9485` it is essentially unchanged, so the design
intent survives, but the target is not met and is not declared met.

## 7. What this establishes, and what it does not

**Establishes**, for this host and this configuration:

- Kernel-enforced rate shaping shows no detectable common-mode contamination
  of the cross-link load residual at `omega = 0`, on an un-quiesced host at
  full 8-link campaign concurrency.
- The backlogged-source condition holds throughout, with about 5,000x margin.
- The `tc` control path is verified independently at the sink to `4.9e-05`.

**Does not establish:**

- It does not establish that `H_shape` is correct in its second prediction.
  KILL-3 failed, and the decomposition shows the predictor was under-specified,
  so the run is UNINFORMATIVE about the phase-shift term rather than evidence
  against it. `v_phase` is far too small here to be observable at all.
- It does not identify the source of the residual nugget. Only its correlation
  class is established.
- It does not extend to `omega > 0`. A negative control at `omega = 0` bounds
  contamination; it says nothing about whether a real coupling is recovered
  with the right magnitude. That is a separate test.
- It does not license any claim about hosts other than this one.

## 8. Disposition

`GO*`. Phase G' proceeds. `G-L102` is recorded. The single diagnostic round of
doc 58 section 6 remains UNSPENT: it is reserved for a gate failure that
carries information, and the KILL-3 failure does not, for the reason given in
section 4.

The next test must recover a KNOWN NON-ZERO coupling, since this one only
bounds the zero case.

## 9. Artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G2/g2_kill_test.json` | `50a30667e33a2c076e731752b84c0d42a4ed608e3e05eea51c858b459e2ec6e7` |
| `results/SMOKE/phase-G2/g2_kill_null.json` (corrected null) | `ef6a5f378fdf4ccc1ce22e1ce3c91e4ac19131a2d0ee3f28a2f05f4f378ab8af` |
| `results/SMOKE/phase-G2/g2_kill_test_run1_invalid.json` | `0a95f4cb0026721cac607ba066b1a50cfa794d58a97a5a17ba5e3bcad7407b9e` |
| `results/SMOKE/phase-G2/g2_pipeline_smoke.json` | `8b62307b5a2a16d7f3a31b8bbba3db9b268d35c400bc211a6d5c909d550b6709` |
| `tools/g2_kill_test.py` | `5a34f45e9d4cddfa4d0bd6159a2bad043b5034794d1a24df29f66475d42b3419` |

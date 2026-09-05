# Amendment to G'.2 -- harness defect, corrected null, run 1 invalidated

Date: 2026-09-05 UTC. Status: `AMENDMENT_POST_RUN_1_PRE_ADJUDICATION`.

Append-only amendment to `docs/phase-G/58-prereg-g2-kill-test.md`, which is
published at commit `3149f30a` under tag `phase-G2-kill-test-prereg` and is NOT
edited. It records a defect in the execution harness, invalidates the first
run on CONFIGURATION grounds, and replaces a calibration that the same defect
had corrupted. It relaxes no adjudicating gate and reverses no verdict,
because no verdict has been issued.

## 1. The defect

`tools/g3_dryrun.py:157`:

    def ar1(n_processes, tau_s, n, rng):
        phi = float(np.exp(-DT_S / tau_s))

`DT_S` is read from MODULE SCOPE, where it is `0.2`. It is not a parameter and
the signature gives no hint of it. `physical_trace(tau_path_s=2.0, ...)`
therefore generates `phi = exp(-0.2/2.0) = 0.904837` regardless of the step the
caller intends to drive it at.

`tools/g2_kill_test.py` drove that series at `dt = 0.1 s`, so the realised
correlation time was

    tau_eff = -dt/log(phi) = -0.1/log(0.904837) = 1.0000 s

against the preregistered 2.0 s. The run's own estimator agrees: the measured
`tau_hat` was `1.0393 s`, which recovers `tau_eff` and not `tau_signed`. The
estimator was correct; the configuration was not.

**G-L101:** a generator that reads its timestep from module scope silently
decouples the REALISED time constant from the REQUESTED one. Every caller that
drives such a series at a different step gets a different `tau` than it asked
for, with no error and no warning, and the discrepancy is invisible unless the
run independently estimates `tau` and the estimate is compared against the
request. Record the realised `tau` in the artifact, and bind the constant to
the step actually used.

## 2. What run 1 does and does not satisfy

| Signed gate | Requirement | Realised | Status |
|---|---|---|---|
| T-1 | `T_run/tau >= 200` | 410 | met, better than signed |
| T-2 | `dt/tau <= 1/20` | `1/10` | **VIOLATED** |

A result produced in a configuration that violates a signed gate cannot be
adjudicated as the preregistered test. Run 1 is recorded
`INVALID_CONFIGURATION_HARNESS_DEFECT` and preserved at
`results/SMOKE/phase-G2/g2_kill_test_run1_invalid.json`. The repository has
precedent for exactly this disposition in the tags
`phase-G-g1-static-smoke-invalid`, `-v2-smoke-invalid` and `-v3-smoke-invalid`.

**Run 1 is discarded for its CONFIGURATION, not for its result.** Its KILL-1
reading was `0.0509` against a target of `0.10`, i.e. it PASSED. Discarding a
passing run is the conservative direction, and it is being discarded because
the run does not test what was signed. It therefore does NOT consume the single
diagnostic round of doc 58 section 6, which is reserved for a gate failure.

## 3. The KILL-1 null in doc 58 section 3.1 was computed under the same defect

`tools/g2_kill_null.py` calls the same `physical_trace`, so the null published
in the preregistration was also calibrated at `tau_eff = 1.0 s`, i.e. at
`n_eff = 410` rather than the signed `n_eff = 205`. A null computed with twice
the effective sample size is too narrow.

Recomputed at the true signed configuration, 400 trials:

| Statistic of `max\|r\|` under H0 | Doc 58 (defective) | Corrected |
|---|---:|---:|
| median | 0.0558 | 0.0796 |
| p95 | 0.0785 | 0.1107 |
| p99 | 0.0884 | **0.1221** |
| observed max | 0.0957 | 0.1410 |

| Gate | `P(pass)` under H0 | Safety over null p99 |
|---:|---:|---:|
| 0.10 (doc 58 TARGET) | **0.8850** | **0.82** |
| 0.15 | 1.0000 | 1.23 |
| 0.20 (doc 58 HARD) | 1.0000 | 1.64 |

### 3.1 Consequence, stated precisely

The doc 58 **target** of 0.10 is not reachable with confidence at the signed
configuration: it sits BELOW the null p99, and would fail 11.5 percent of the
time when every true correlation is exactly zero. Doc 58 section 3.1 claimed
`P(pass) = 1.0000` and a safety factor of 1.13 for this gate; that claim was
computed on the defective null and does not hold.

The doc 58 **hard** gate of 0.20 is unaffected: `P(pass) = 1.0000` under H0
with a safety factor of 1.64 over the corrected null.

**No adjudicating gate changes.** Doc 58 section 5 maps the verdict from
`r ~ 0`, and doc 58 section 8 makes "the KILL-1 hard gate" non-negotiable. The
hard gate is what the verdict logic reads. The 0.10 figure was a target, was
never the adjudicating threshold, and is from here reported as a diagnostic
with its true false-fail rate attached rather than presented as a gate that a
correct null supports.

This is the `G-L90` failure mode recurring one level up: the gate itself was
checked for satisfiability, but the CALIBRATION that established its
satisfiability was produced by the defective harness. Checking a threshold
against a null is only as good as the configuration the null was computed in.

## 4. Corrective action

`tools/g2_kill_null.py` and `tools/g2_kill_test.py` now bind
`g3_dryrun.DT_S` to the step actually used, before generating any series, and
record the realised value in the artifact. `tools/g3_dryrun.py` is NOT edited:
it is referenced by adjudicated G.3 documents and its hash must not move.

Run 2 executes at the signed configuration, `tau = 2.0 s`, `dt = 0.1 s`,
`T_run = 410 s`, 4 replicates, 8 links, host not quiesced. Everything else in
doc 58 stands unchanged.

## 5. Referenced artifacts

| Artifact | SHA256 |
|---|---|
| `results/SMOKE/phase-G2/g2_kill_test_run1_invalid.json` | `0a95f4cb0026721cac607ba066b1a50cfa794d58a97a5a17ba5e3bcad7407b9e` |
| `results/SMOKE/phase-G2/g2_kill_null.json` (corrected) | `ef6a5f378fdf4ccc1ce22e1ce3c91e4ac19131a2d0ee3f28a2f05f4f378ab8af` |
| `results/SMOKE/phase-G2/g2_pipeline_smoke.json` | `8b62307b5a2a16d7f3a31b8bbba3db9b268d35c400bc211a6d5c909d550b6709` |

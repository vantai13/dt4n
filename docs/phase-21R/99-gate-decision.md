# Phase 21R -- Gate Decision

Ngay dong phase: 2026-08-12

## Verdict

```text
PHASE 21R: GO

Gate status:
  PASS           : 11
  PASS_MARGINAL  : 1   (G2)
  INCOMPLETE     : 0
  FAIL           : 0
```

G5 was incomplete in the Lesson 21R.9 prompt because Lesson 21R.3 reported the
decomposition moments without confidence intervals. It is now complete:
`cert/gate_report.py` adds block-bootstrap CI for `Var(e_model)`,
`Var(e_stale)`, and `Cov`.

## Gate Table

Fixed-sigma headline path: `sigma_rho=0.0096`, main cell `poisson@0.925`.

| Gate | Criterion | Threshold | Measured | Status | Source |
|---|---|---:|---:|---|---|
| G1 | q_hat monotonic steps with adjusted CI | at least 2/3 | 3/3 | PASS | L4 |
| G1b | q_hat(B3)/q_hat(B0) | at least 1.3 | 2.151, CI [2.088, 2.214] | PASS | L4 |
| G2 | eta2(z) on s_margin | at least 0.05 | 0.0730, CI [0.0696, 0.0763] | PASS_MARGINAL | L4 |
| G3 | abs(marginal coverage - 0.90) | at most 0.02 | 0.00868 | PASS | L5 |
| G4 | max abs(per-bin coverage - 0.90) | at most 0.05 | 0.01177 | PASS | L5 |
| G5 | report Var(em), Var(es), Cov with CI | required | completed for 3 cells | PASS | L9 |
| G6 | V3 positive control exposes leakage via SD collapse | SD ratio < 0.5 | 0.2562 | PASS | L5 |
| G7 | Spearman(q_hat by bin, err20 by z) | 1.0 | 1.0000 | PASS | L4 |
| G8 | q_hat(alpha/K) > q_hat(alpha), all bins | 4/4 | 4/4 | PASS | L5 |
| G9/H7 | exists acceptance >= 0.10 and err\|accept <= 0.5*anchor | at least 1 point | 5 points | PASS | L6 |
| G10 | robustness over at least 2 nondegenerate modes | at least 2 | 3 fixed / 7 operational | PASS | L6, L8 |
| G11 | q_hat above measurement floor | all cells | 10/10 operational | PASS | L9 |
| G12 | P(accept at kappa=1) <= 0.90 | at most 0.90 | 0.28354 | PASS | L6 |

G2 is deliberately marked `PASS_MARGINAL`. The effect size is small-to-medium:
age explains about `7.3%` of pointwise score variance. That is enough to move
the 90th percentile by about `2.15x`, which is the conformal quantity that
matters, but it is not a claim that age dominates all score variation.

## G5 Completion

Block bootstrap, `n_boot=2000`, pooled over the sawtooth calibration set.

| Cell | rms em | CI95 | rms es | CI95 | cov | CI95 | cov excludes 0 |
|---|---:|---|---:|---|---:|---|---|
| `poisson@0.925` | 2.1401 | [2.1066, 2.1710] | 13.1116 | [12.9662, 13.2524] | -9.0897 | [-9.4246, -8.7728] | yes |
| `poisson@0.850` | 0.6560 | [0.6452, 0.6662] | 3.1610 | [3.1243, 3.1991] | 0.7853 | [0.7522, 0.8191] | yes |
| `h2@0.700` | 2.0537 | [2.0323, 2.0747] | 6.9162 | [6.8387, 6.9951] | -1.1324 | [-1.2883, -0.9814] | yes |

Covariance changes sign by regime. It must be reported, not assumed away.

## Operational Robustness

Operational-sigma path:

```text
G3: PASS 10/10, coverage range [0.899123, 0.911104]
G4: PASS 10/10
H7: PASS 7/7 nondegenerate cells
near-zero controls: PASS 3/3
q_hat age-shape ratio: 8 non-CBR cells in [2.1076, 2.3143], mean 2.1766
```

Operational path rescued 3 cells from fixed-sigma degeneracy:
`poisson@0.700`, `h2@0.850`, and `h2@0.925`. It is 3, not 4; the artifact is
the source of truth.

## G11 By Cell

| Cell | w_loss | floor delay | floor loss | floor total | q_hat(B0) | q_hat/floor |
|---|---:|---:|---:|---:|---:|---:|
| `cbr@0.700` | 1245.6 | 0.0057 | 0.0000 | 0.0057 | 0.0103 | 1.81 |
| `cbr@0.850` | 1245.6 | 0.0031 | 0.0000 | 0.0031 | 0.0081 | 2.59 |
| `poisson@0.700` | 1656.4 | 0.0515 | 0.0913 | 0.1048 | 1.0083 | 9.62 |
| `poisson@0.850` | 2424.4 | 0.1862 | 0.7214 | 0.7450 | 15.1663 | 20.36 |
| `poisson@0.925` | 3222.2 | 0.1735 | 1.4750 | 1.4851 | 24.3053 | 16.37 |
| `poisson@0.960` | 3655.9 | 0.1907 | 2.1369 | 2.1454 | 17.8291 | 8.31 |
| `h2@0.700` | 2861.4 | 0.1947 | 1.7554 | 1.7661 | 27.3326 | 15.48 |
| `h2@0.850` | 4021.4 | 0.2052 | 4.6873 | 4.6918 | 81.4597 | 17.36 |
| `h2@0.925` | 4515.9 | 0.1031 | 5.2206 | 5.2217 | 48.0028 | 9.19 |
| `h2@0.960` | 4722.7 | 0.1656 | 5.9204 | 5.9227 | 24.3486 | 4.11 |

G11 passes in all 10 cells. The CBR positive controls have `q_hat` only about
`1.8-2.6x` the measurement floor, which is the expected behavior when the
decision problem is otherwise nearly empty.

## Prediction Scorecard

The numeric preregistration intervals are preserved as written.

| Prediction | Preregistered | Observed | Result | Root cause |
|---|---:|---:|---|---|
| q_hat(B1) | [1.5, 2.2] ms | 11.5878 ms | MISS | scale mismatch |
| q_hat(B4) | [2.0, 3.0] ms | 24.3222 ms | MISS | scale mismatch |
| B4/B1 ratio | [1.2, 1.6] | 2.151 | MISS | scale mismatch |
| P(accept at kappa=1) | [0.75, 0.87] | 0.28354 | MISS | scale mismatch |
| z_cross | [0.05, 0.10] s | 0.007085 s | MISS | level/channel mismatch |
| err_anchor | [0.27, 0.31] | 0.220835 | MISS | Jensen |

Strict numeric scorecard:

```text
n_hit = 0
n_miss = 6
root-cause families = scale_mismatch 5, Jensen 1
```

Separate amendment checks:

```text
C2 nonbinding at GO cell: PASS
dimensionless kappa needed: PASS
q_hat ~= 1.645*rms: PASS
```

The misses are useful because they are traceable to two families of reading
errors: scale/level mismatch and Jensen/AoI averaging.

## Amendments

| Amendment | Main content | Discipline check |
|---|---|---|
| 1 | 1*q_hat not 2*q_hat; C2 nonbinding; kappa family | logic correction, no threshold relaxation |
| 2 | anchor miss and cell-list correction | recorded after measurement |
| 3 | z_cross miss; delay/channel mismatch; q_hat warning | recorded after decomposition |
| 4 | Variant B, half-normal bridge, bias | reported after s(z) |
| 5 | V3 is variance collapse; A/B caveat | reported after conformal |
| 6 | H7 pass; post-selection caveat | reported after usefulness |
| 7 | Jensen closure; model floor; AoI max vs mean | reported after freshness |
| 8 | operational path; 2.17 age-shape ratio; nonmonotone difficulty | reported after robustness |

No amendment relaxes a gate threshold.

## Threats To Validity

| ID | Scope | Limitation | Resolution |
|---|---|---|---|
| L1 | construct | Ground truth is a dense measured lookup table, not pure physical truth. | Phase 23 direct telemetry validation |
| L2 | measurement | A large share of e_model variance is measurement noise. | Larger truth-table measurement campaign |
| L3 | external | Guarantees are for synthetic AR(1) rho, tau=1.0. | Phase 23 |
| L4 | statistical | Exact finite-sample guarantee belongs to Variant A; B is the headline approximation. | Report A/B side by side |
| L5 | post-selection | Coverage is not preserved after selection: 0.0913 -> 0.1214 violation. | Phase 22 selective conformal |
| L6 | construct | Certificate is pairwise, not simultaneous over K=4 actions. | Phase 22 simultaneous coverage |
| L7 | external | Fixed path has only one second traffic family outside poisson. | Add traffic families |
| L8 | external | Age-shape ratio 2.17 is observed, not proven as a law. | Phase 22/23 sensitivity |
| L9 | statistical | Operating cells share trajectories by seed, so pooled p-values are optimistic. | Independent seed design |
| L10 | internal | Absolute path ranking inherits Phase 20R residual-bound assumptions. | Phase 23 |

## Phase 22

Phase 22 should address exactly:

```text
P22-A: simultaneous coverage for K=4 actions
P22-B: post-selection coverage guarantee
P22-C: sensitivity of the 2.17 age-shape ratio to tau/AoI/real telemetry
```

Phase 21R is therefore GO for Phase 22, with scope explicitly bounded by the
limitations above.

## Verification

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_gate.py -q
9 passed

/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_gate.py test/test_phase21r_operational.py test/test_phase21r_freshness.py test/test_phase21r_usefulness.py test/test_phase21r_conformal.py test/test_phase21r_errage.py test/test_phase21r_decomp.py test/test_phase21r_calib.py test/test_phase21r_margin.py -q
103 passed

/tmp/dt4n-venv/bin/python -m pytest -q
637 passed, 1 skipped, 2 warnings in 156.87s (0:02:36)
```

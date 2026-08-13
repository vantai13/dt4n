# LESSON 22.8 -- gate_report_22.py

Ngay: 2026-08-13

Trang thai: Phase 22 GO tren o chinh `poisson@0.925`, voi 17/17 cong PASS,
0 FAIL, 0 NOT_RUN, 0 ERROR. Ty le du doan trung la 21/32 = 65.6%; con so nay
duoc bao cao, khong phai dieu kien gate.

## 1. San pham

| File | Vai tro |
|---|---|
| `cert/gate_report_22.py` | doc artifact 22.2--22.7 va dong gate read-only |
| `test/test_phase22_gate.py` | 7 tests khoa tri-state gate, scorecard day du, GO rule |
| `results/phase-22/gate_report_poisson_0.925.json` | report quyet dinh GO chinh |
| `results/phase-22/gate_report_{poisson_0.850,h2_0.700,cbr_0.700}.json` | audit phu theo cell |

Lenh chinh:

```text
/tmp/dt4n-venv/bin/python -m cert.gate_report_22 \
  --cell poisson_0.925 \
  --out results/phase-22/gate_report_poisson_0.925.json
```

## 2. Decision

```json
{
  "decision": "GO",
  "gates_pass": 17,
  "gates_total": 17,
  "gates_blocking": [],
  "gates_not_run": [],
  "predictions_hit": 21,
  "predictions_scored": 32,
  "hit_rate": 0.65625,
  "hit_rate_by_lesson": {
    "22.3": "4/7",
    "22.4": "5/6",
    "22.5": "2/7",
    "22.6": "7/7",
    "22.7": "3/5"
  }
}
```

Rule:

```text
GO requires zero FAIL/ERROR and zero NOT_RUN. Prediction hit rate is REPORTED,
never a gate: a missed prediction with an understood mechanism is a result, not
a defect.
```

## 3. Gate table

| Gate | Lesson | Claim | Status |
|---|---:|---|---|
| G22-2 | 22.2 | U0 reproduces calib_set_v2 bit-for-bit | PASS |
| G22-3 | 22.2 | every (z_bin x m_hat_bin) cell has at least 9 calibration blocks | PASS |
| G22-4 | 22.3 | corrected procedures achieve simultaneous coverage | PASS |
| G22-5 | 22.3 | negative control collapses without correction | PASS |
| V22-6 | 22.3 | uncorrected slot 1 equals the 21R qhat exactly | PASS |
| PC22-3 | 22.3 | row split collapses the coverage variance | PASS |
| G22-6 | 22.4 | post-selection validity is restored at kappa=1 | PASS |
| G22-7 | 22.4 | fixed points terminate | PASS |
| NC22-2 | 22.4 | kappa=0 reduces to 21R | PASS |
| G22-8 | 22.5 | H22-7 holds for the full C3 claim | PASS |
| G22-9 | 22.5 | risk-coverage curves are monotone in kappa | PASS |
| G22-9b | 22.5 | frontier is not degraded: AURC(C3)/AURC(C0) < 1.02 | PASS |
| G22-10 | 22.6 | all five tau ratios lie inside signed bands | PASS |
| G22-11 | 22.6 | AR(1) amplitude A is independent of tau | PASS |
| G22-12 | 22.7 | realistic AoI profiles are indistinguishable from uniform | PASS |
| PC22-4 | 22.7 | extreme AoI offset is visible | PASS |
| G22-13 | 22.7 | coverage holds under every AoI profile | PASS |

Controls are part of the design, not decoration:

| Type | Gates |
|---|---|
| reproduction | G22-2, V22-6 |
| negative control | G22-5, NC22-2 |
| positive control | PC22-3, PC22-4 |

## 4. Honest prediction scorecard

All signed misses are retained. Dropping M1..M10 would turn 21/32 into a pretty
but false 21/22.

| ID | Lesson | Measured | Band | Verdict | What |
|---|---:|---:|---|---|---|
| P1 | 22.3 | 1.3104 | [1.28, 1.33] | HIT | qhat_bonferroni_B0 / qhat_21R_B0 |
| P2 | 22.3 | 1.2955 | [1.27, 1.32] | HIT | qhat_sidak_B0 / qhat_21R_B0 |
| P3 | 22.3 | 1.3179 | [1.22, 1.30] | MISS | qhat_maxscore_B0 / qhat_21R_B0 |
| P4 | 22.3 | 0.9718 | [0.955, 0.975] | HIT | pointwise coverage under simultaneous correction |
| P5 | 22.3 | 0.7706 | [0.74, 0.80] | HIT | negative-control simultaneous coverage |
| M1 | 22.3 | 1.0058 | [0.94, 0.98] | MISS | qhat_maxscore / qhat_bonferroni |
| M2 | 22.3 | 0.9253 | [0.88, 0.92] | MISS | simultaneous coverage (bonferroni) |
| P6 | 22.4 | 0.1214 | [0.115, 0.13] | HIT | violation\|accept before repair |
| P7 | 22.4 | 0.0160 | [0, 0.10] | HIT | violation\|accept after fcr |
| P8 | 22.4 | 0.0884 | [0, 0.10] | HIT | violation\|accept after mondrian |
| P9 | 22.4 | 0.0849 | [0, 0.10] | HIT | violation\|accept after selective |
| P10 | 22.4 | 8 | [3, 12] | HIT | fixed-point iterations |
| M3 | 22.4 | 1.6237 | [1.45, 1.58] | MISS | fcr multiplier at the fixed point |
| P11 | 22.5 | 4.4398 | [>=3] | HIT | err\|reject / err\|accept at operating point |
| M4 | 22.5 | 1.2980 | [1.72, 1.88] | MISS | C3 multiplier at the operating point |
| M5 | 22.5 | 0.1436 | [0.075, 0.110] | MISS | C3 acceptance at kappa=1 |
| M6 | 22.5 | 0.4911 | [0.30, 0.42] | MISS | C3 acceptance at kappa=0.5 |
| M7 | 22.5 | 0.2734 | [0.15, 0.24] | MISS | C3 acceptance at kappa=0.75 |
| M8 | 22.5 | 0.0809 | [0.045, 0.075] | MISS | C3 err\|accept at kappa=0.5 |
| S1 | 22.5 | true | structural | HIT | H22-7 holds at kappa in {0.5, 0.75} |
| P12 | 22.6 | 1.9779 | [1.77, 2.16] | HIT | ratio at tau=0.50 |
| P13 | 22.6 | 2.0990 | [1.87, 2.29] | HIT | ratio at tau=1.00 |
| P14 | 22.6 | 2.1432 | [1.88, 2.30] | HIT | ratio at tau=2.00 |
| P15 | 22.6 | 2.0834 | [1.86, 2.27] | HIT | ratio at tau=2.87 |
| P16 | 22.6 | 2.0076 | [1.77, 2.17] | HIT | ratio at tau=5.00 |
| S2 | 22.6 | true | structural | HIT | ratio over tau is hump-shaped |
| S3 | 22.6 | true | structural | HIT | A is independent of tau (<2%) |
| P17 | 22.7 | 0.0042 | [0, 0.02] | HIT | max abs qhat(U1)/qhat(U0)-1 |
| P18 | 22.7 | 0.0139 | [0, 0.02] | HIT | max abs qhat(U2)/qhat(U0)-1 |
| M9 | 22.7 | 1.0042 | [0.95, 1.00] | MISS | qhat(U1)/qhat(U0) at B2 |
| M10 | 22.7 | 1.0139 | [0.96, 1.00] | MISS | qhat(U2)/qhat(U0) at B0 |
| S4 | 22.7 | true | structural | HIT | PC4 makes the Jensen effect visible |

By lesson:

| Lesson | Hit rate | Interpretation |
|---|---:|---|
| 22.3 | 4/7 | simultaneous correction worked; exact procedure ranking was too tight |
| 22.4 | 5/6 | post-selection fix worked; FCR multiplier was underestimated |
| 22.5 | 2/7 | extrapolating a single multiplier for a family failed |
| 22.6 | 7/7 | mechanism-based AR(1) prediction transferred cleanly across tau |
| 22.7 | 3/5 | bound prediction worked; sign prediction below noise floor failed |

## 5. Phase statement

For `poisson@0.925`, full C3 at `kappa=0.5`:

| Quantity | Value |
|---|---:|
| acceptance | 0.4911 |
| err\|accept | 0.0809 |
| risk ratio vs anchor | 0.3636 |
| violation\|accept | 0.0794 |
| err\|reject / err\|accept | 4.4398 |

Frontier:

| Quantity | Value |
|---|---:|
| AURC C0 | 0.0913346 |
| AURC C3 | 0.0910854 |
| AURC(C3)/AURC(C0) | 0.9973 |
| risk delta at acceptance 0.70 | +0.255% |
| risk delta at acceptance 0.50 | -0.814% |
| risk delta at acceptance 0.30 | -4.293% |

Allowed claim:

```text
Simultaneous K=4 and post-selection-valid certification is feasible on the
main cell. The cost of formal correctness is a shift along the risk-coverage
curve, not a degraded frontier.
```

Not allowed without extra work:

```text
Do not claim a universal frontier law, an FWER ranking, or completion of
Amendment 1 without the GO conditions below.
```

## 6. Cell audit

The final GO decision is for the main cell. The same 17-gate report was also
run on adjacent cells to expose scope.

| Cell | Decision | PASS | FAIL | NOT_RUN | Non-PASS gates |
|---|---|---:|---:|---:|---|
| poisson_0.925 | GO | 17 | 0 | 0 | none |
| poisson_0.850 | NO_GO | 15 | 2 | 0 | G22-6, G22-7 |
| h2_0.700 | NO_GO | 14 | 3 | 0 | PC22-3, G22-10, G22-12 |
| cbr_0.700 | NO_GO | 11 | 3 | 3 | G22-8, G22-9b, G22-10, G22-12, PC22-4, G22-13 |

This does not weaken the headline, because Phase 22's decision was scoped to
the main fixed-sigma cell. It does constrain abstract-level wording.

## 7. GO conditions

| ID | Status | Requirement |
|---|---|---|
| GO-1 | CONDITION | Before putting frontier invariance in the abstract, confirm AURC(C3)/AURC(C0) < 1.02 on all non-degenerate cells. Current scan: 3/3 evaluable pass; 2 cells are degenerate/not evaluable. |
| GO-2 | CONDITION | Rank FWER procedures only with paired bootstrap deltas. Current artifact has 200 paired bootstrap draws; 5/24 delta CIs contain zero. |
| GO-3 | FUTURE_WORK | Amendment 1, studentized max-score, was signed but not run in Phase 22. Record it as future work or run it as exploratory. |

## 8. Threats to validity

| Limitation | Status after Phase 22 |
|---|---|
| L5 post-selection coverage | CLOSED by G22-6 |
| L6 pairwise vs simultaneous K=4 | CLOSED by G22-4, G22-8 |
| L8 age-shape ratio not proven as law | CLOSED for AR(1) tau sweep; scope condition retained |
| L12 uniform AoI assumption | CLOSED for realistic U1/U2 on poisson cells |
| L3 synthetic AR(1) traffic | PARTIAL, because tau sensitivity passed but non-AR traffic remains |
| L13 non-uniform AoI can break the ratio law | NEW, opened by PC4 |

## 9. Phase 23 priorities

| Priority | Targets | Work |
|---|---|---|
| P23-A | L11, L13 | measure AoI directly on topology_v7 and rerun U0/U1/U2/PC4 |
| P23-B | L3, L7 | non-AR(1) load: burst, on/off, real traces |
| P23-C | L1, L2 | packet-level truth from Mininet, not lookup-table truth |
| P23-D | L10 | remove the inherited Phase 20R residual-bound assumption for absolute ranking |
| P23-E | transfer | if the tau limit is a law, calibrate at one age bin and transfer across bins |

## 10. Verification

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase22_gate.py -q
7 passed in 0.19s

/tmp/dt4n-venv/bin/python -m pytest -q \
  test/test_phase22_simscore.py test/test_phase22_calibv3.py \
  test/test_phase22_conformalsim.py test/test_phase22_selective.py \
  test/test_phase22_matrix.py test/test_phase22_tau.py \
  test/test_phase22_aoi.py test/test_phase22_gate.py
99 passed in 245.26s (0:04:05)

/tmp/dt4n-venv/bin/python -m pytest -q
736 passed, 4 skipped in 575.14s (0:09:35)
```

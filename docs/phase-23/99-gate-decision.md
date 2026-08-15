# 99 -- Gate decision, Phase 23 through Lesson 23.4

Ngay checkpoint: 2026-08-15

Trang thai: Lessons 23.0--23.4 da chay. Ket luan cu "C3 giu cross-cell" bi
rut lai; ket luan moi la law co dieu kien `lift > swing` trong Amendment 23-19
va `05-cross-cell.md`.

Latest cross-cell artifact commit before this document: `095a34d`.
Latest lift-law artifact commit: `d180804`.

## Artifacts

| File | Vai tro |
|---|---|
| `results/phase-23/fallback_grid_poisson_0.925_C3.json` | Lesson 23.1 fallback sweep |
| `results/phase-23/threshold_families_poisson_0.925_C3_static.json` | Lesson 23.2 threshold-family sweep |
| `results/phase-23/baseline_rankings_poisson_0.925_C3_static.json` | Lesson 23.3 baseline ranking sweep |
| `results/phase-23/baseline_c3_b2_audit_poisson_0.925_C3_static.json` | C3-B2, argmin, gamma, tie-break audit |
| `results/phase-23/g23_17a_cell_margins.json` | G23-17a marginal priors for three cells |
| `results/phase-23/g23_17b_code_sanity.json` | G23-17b cross-cell code sanity |
| `results/phase-23/g23_17c_scale_and_sla.json` | G23-17c scale/SLA comparability and Mechanism #8 |
| `results/phase-23/g23_23_lift_law.json` | G23-23 lift-vs-swing law for cross-cell benefit |
| `results/phase-23/cross_cell_summary.json` | Lesson 23.4 cross-cell C3 summary and selector table |
| `results/phase-23/cross_cell_err_panels.png` | Three-panel err_system coverage figure |
| `results/phase-23/baseline_rankings_poisson_0.850_C3_static.json` | Lesson 23.4 baseline ranking sweep for poisson@0.850 |
| `results/phase-23/baseline_rankings_h2_0.700_C3_static.json` | Lesson 23.4 baseline ranking sweep for h2@0.700 |

Lenh tai tao audit cuoi:

```text
/tmp/dt4n-venv/bin/python cert/baselines.py --audit-c3-b2 --n-boot 2000
```

## Gate da PASS

| Gate | Lesson | Noi dung | Bang chung |
|---|---:|---|---|
| G23-4b | 23.1 | break-even fallback equals twin risk on reject rows | `test_phase23_fallback.py` |
| V23-4 | 23.2 | CONG(delta=0) == NHAN(kappa=1) bitwise | `test_phase23_thresholds.py` |
| G23-6b | 23.2 | REGRET family is algebraically additive | `test_phase23_thresholds.py` |
| G23-7b | 23.2 | CONG degenerates locally by age bin | `test_phase23_thresholds.py` |
| G23-9 | 23.2 | scale-agreement self-check passes | `test_phase23_thresholds.py` |
| G23-10b | 23.3 | B4 variance proxy == B3 AoI bitwise | `test_phase23_baselines.py` |
| G23-12c | 23.3 | B6-sys closed form matches measured curve | `test_phase23_baselines.py` |
| PC23-1 | 23.3 | random baseline keeps err\|accept near anchor | `test_phase23_baselines.py` |
| G23-20 | 23.3 | argmin agreement uses chance agreement/kappa, not 0.5 | `test_phase23_baselines.py` |
| G23-21 | 23.3 | break-even argmin identity reconstructs delta | `test_phase23_baselines.py` |

Ghi chu ten: "G23-11" trong ghi chep lam viec tuong ung voi `PC23-1` trong
repo. Ten chuan trong repo la `PC23-1`.

## Gate/adjudication bo sung

| ID | Lesson | Ket qua | Dien giai |
|---|---:|---|---|
| L20 | 23.3 | PASS | intervention-rate C3-B2 gap = 0.001274 <= 0.010 |
| G23-21b | 23.3 | ADJUDICATED | simple B2-to-B3 gamma interpolation rejected; no gamma > 2 beats gamma=1; gamma0.5-vs-gamma1 CI contains 0 |
| G23-21c | 23.3 | PASS | C3 Mondrian cells have finite-sample support; min effective blocks = 433 >= 29 actual and >= 39 conservative |
| tie-break audit | 23.3 | PASS | max spread = 0.000100, far below C3-B3 gap 0.025430 |
| G23-17a/b/c | 23.4 preflight | ADJUDICATED | `poisson@0.850` is a scale-invariance control; `h2@0.700` is the real regime shift; cross-cell regret needs three-factor decomposition |
| artifact parity | 23.4 preflight | PASS | both new cell parquets rebuilt to 45 columns with `y_hat_a1` and `sla_viol_p0..p3`; builder fail=[] |
| G23-23 | 23.4 | PASS | benefit iff `lift=twin_deg-prior_deg` exceeds `swing=err_P1-err_neo`; max delta identity error 2.17e-17 |
| G23-15 | 23.4 | FAIL | B3 beats C3 at `h2@0.700` around the operating point |
| G23-17 | 23.4 | FAIL | main-cell C3 conclusion does not hold on both new cells |
| S7 | 23.4 | FAIL | threshold-family Pareto front contains additive and multiplicative survivors in both new cells |

G23-21b measured:

```text
qhat slots = 3, keys = z_bin,m_hat_bin
cell-level qhat monotone by z = True
row-level qhat monotone by z  = False

b2_to_b3_interpolation_supported = False
no_gamma_gt2_beats_gamma1        = True
paired gamma0.5-gamma1 CI95      = [-0.001932176, +0.000872232]
```

G23-21c measured:

```text
keys = z_bin,m_hat_bin
n_cells = 16
n_calib_rows = 499978
n_calib_blocks = 500
n_score_slots = 3
actual alpha_each = 0.033333333
actual n_min = 29
conservative action-split n_min = 39
min_n_eff_blocks_per_cell = 433
cells_below_actual = 0
cells_below_conservative = 0
cells_with_nonfinite_qhat = 0
```

## Ket qua chinh 23.3

Tai coverage 0.78:

| Selector | err_system | delta vs anchor | Co loi? |
|---|---:|---:|:--:|
| B1 random | 0.248794420 | +0.026395742 | no |
| B3 AoI | 0.234959507 | +0.012560829 | no |
| B2 constant gap | 0.209413821 | -0.012984857 | yes |
| C3 conformal | 0.209529829 | -0.012868849 | yes |

C3 vs B2 paired block bootstrap:

| scale | C3-B2 | CI95 | contains 0 |
|---|---:|---|:--:|
| err | +0.000116008 | [-0.001968714, +0.002256247] | yes |
| regret | -0.005496808 | [-0.033357486, +0.021128896] | yes |
| sla | -0.000236016 | [-0.001338032, +0.000852087] | yes |

Allowed statement:

```text
C3 beats the AoI baseline B3 clearly at the operating point and over the
beneficial band, but C3 is not distinguishable from B2 constant gap on
err/regret/sla at matched coverage. The contribution of conformal certification
relative to B2 is a formal guarantee at no measurable system-risk cost.
```

## Sua dien giai da thuc hien

1. Rut lai "C3 vuot moi baseline" tai coverage 0.78. B2 la doi thu that; C3-B2
   CIs chua 0 tren ca ba thang.
2. Rut lai "tin hieu khong nam o tuoi". B3 co kappa separation `0.166247`,
   bang 31.7% cua C3, nhung chua vuot nguong hoa von.
3. Rut lai moc "dong xu 0.5" cho argmin. Moc dung la chance agreement tren
   cung tap con, bao cao kem kappa.
4. Rut lai cach doc "gamma=0.5 tot hon". Gamma khac 1 pha bao dam conformal va
   duoc chon tren test; doc dung la diagnostic do chi phi bao dam
   `0.000538` err, CI chua 0.
5. Rut lai "gamma noi B2 voi B3" cho C3 hien tai. C3 condition theo
   `z_bin x m_hat_bin`, nen gamma lon di theo cell/slot `q_hat`, khong ve B3.
6. Ghi nhan hai luoi `beneficial_band`: Lesson 23.1 dung luoi kappa min
   `[0.6151,1.0000]`; Lesson 23.3 dung luoi coverage deu `[0.6076,0.99995]`.
7. Sua notation age-only thanh `q_hat(z_bin,m_hat_bin)` cho C3. Cac bang
   marginal theo age bin chi la tom tat/diagnostic, khong phai taxonomy
   guarantee cua C3.
8. Khoa Mechanism #8 cho cross-cell regret:
   `regret_ratio = err_ratio x normpen_ratio x scale_ratio`. Headline
   cross-cell la `err`; `regret` phai kem phan ra; `sla_rate` khong lam
   headline vi `t_d`/`t_l` khac nhau giua cell.
9. Sau G23-21c tren hai cell moi, rut lai ket luan "C3 thang cross-cell".
   Tai coverage 0.78, C3 thua always-trust o ca `poisson@0.850` va
   `h2@0.700`; B3 la bo chon duy nhat co loi o `h2@0.700`.
10. Khoa Co che #9: `delta_vs_anchor = reject_share * (swing - lift)`. Ket
    qua co loi khi va chi khi `lift > swing`.

## No da tra

| No | Trang thai | File |
|---|---|---|
| C3-A/B2-A | CLOSED by algebra | `04-baselines.md` |
| L20 intervention rate | CLOSED | `baseline_c3_b2_audit_*.json` |
| Co che argmin | CLOSED | `04-baselines.md` |
| G23-21 break-even identity | CLOSED | `test_phase23_baselines.py` |
| G23-21b gamma closure | CLOSED as rejected mechanism | `baseline_c3_b2_audit_*.json` |
| G23-21c qhat cell sample support | CLOSED | `baseline_c3_b2_audit_*.json`, `test_phase23_baselines.py` |
| tie-break sensitivity | CLOSED | `baseline_c3_b2_audit_*.json` |
| grid labels for beneficial band | CLOSED | `00m-amendment-12.md`, `04-baselines.md` |
| artifact parity for new cells | CLOSED | rebuilt 45-column `calib_set_v3_poisson_0.850.parquet` and `calib_set_v3_h2_0.700.parquet`; hashes in `INHERITED.sha256` |

## Threats to validity

| ID | Scope | Limitation | Status |
|---|---|---|---|
| L20 | comparison | Matched coverage can hide different true intervention rates. | Closed for C3-B2 at 0.78; abs gap 0.001274 <= 0.010 |
| L21 | multiplicity | Effective action space is 3, while nominal design has K=4 actions and K-1=3 score slots. Cost of the dead action/slot is not quantified. | Open |
| L22 | model selection | Gamma sweep is on test; gamma != 1 is not guarantee-preserving. | Closed as diagnostic only |
| L23 | taxonomy | C3 uses `z_bin x m_hat_bin`; age-only asymptotic arguments can fail. | Closed by G23-21b for current artifact |
| L24 | finite cells | Mondrian cells could be too thin, making `q_hat=+inf` or weak. | Closed by G23-21c for current artifact; min effective blocks 433 |
| L25 | theorem statement | Old MASTER_PLAN wording used `alpha/K` for K cost intervals, while Phase 22--23 code certifies K-1 margins with `alpha/(K-1)`. | Closed by Amendment 23-16; optional dead-action pruning remains separate |

## Before Lesson 23.4

Lesson 23.4 was run with these constraints:

```text
1. Do not use gamma != 1 as a certified operating point unless a new conformal
   calibration theorem and validation are written first.
2. Any learned B7-like selector must fit on CALIB and evaluate on TEST.
3. Any argmin-information claim must report chance agreement and kappa.
4. Any cross-cell claim must keep C3-vs-B2 as "reported, not thresholded" unless
   paired CIs exclude 0.
5. Preserve the C3 taxonomy as `z_bin x m_hat_bin`; do not collapse it to
   age-only notation in claims about guarantees.
6. State the C3 theorem on `K-1` margins with `alpha/(K-1)`, per
   `00q-amendment-16.md`; do not use the superseded `alpha/K` cost-interval
   wording.
7. For Lesson 23.4 cross-cell reporting, use Amendment 23-18: headline `err`;
   decompose `regret`; do not headline `sla_rate`; use `gap_closed` rather
   than `delta/neo`.
8. G23-21c was rerun on 45-column artifacts; both cells pass conservative
   action-split support, with min effective blocks 433 and 397.
9. Amendment 23-19 governs cross-cell interpretation: report G23-23 lift law,
   mark G23-15/G23-17 as FAIL because B3 beats C3 in `h2@0.700` and C3 loses
   to always-trust at 0.78 in both new cells.
```

## Lesson 23.4 cross-cell result

| Cell | C3 beneficial band | Improvement area | partial AURC [0.6,1] | gap_closed @0.78 |
|---|---:|---:|---:|---:|
| poisson@0.925 | [0.6076, 0.99995] | 0.003403849 | 0.213898526 | +0.100191538 |
| poisson@0.850 | [0.8091, 0.9892] | 0.000596149 | 0.225453621 | -0.031775777 |
| h2@0.700 | [0.84285, 0.99995] | 0.000274377 | 0.130903199 | -0.086048789 |

Tai coverage 0.78, C3 thua always-trust o hai cell moi. O `h2@0.700`, B3 AoI
la selector duy nhat co loi trong bang chinh (`delta=-0.001378091`) va tot hon
C3 (`delta=+0.003866255`). Day la dao nguoc ket luan van hanh, khong phai
NO-GO: ket qua moi la dieu kien `lift > swing`.

## Verification

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase23_baselines.py -q
11 passed in 14.42s

/tmp/dt4n-venv/bin/python -m pytest \
  test/test_phase23_baselines.py test/test_phase23_thresholds.py \
  test/test_phase23_prereg.py -q
26 passed in 25.49s
```

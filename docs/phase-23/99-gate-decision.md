# 99 -- Gate decision, Phase 23 through Lesson 23.3

Ngay checkpoint: 2026-08-15

Trang thai: Lessons 23.0--23.3 da dong so cho o chinh `poisson@0.925`,
fallback F2 STATIC. Lesson 23.4 chua chay. Day la checkpoint de tiep tuc
23.4, khong phai GO/NO-GO cuoi Phase 23.

Artifact provenance git hash: `eafa328` (`git_dirty_before_write=false`).
Latest artifact refresh commit: `982aa0c`.

## Artifacts

| File | Vai tro |
|---|---|
| `results/phase-23/fallback_grid_poisson_0.925_C3.json` | Lesson 23.1 fallback sweep |
| `results/phase-23/threshold_families_poisson_0.925_C3_static.json` | Lesson 23.2 threshold-family sweep |
| `results/phase-23/baseline_rankings_poisson_0.925_C3_static.json` | Lesson 23.3 baseline ranking sweep |
| `results/phase-23/baseline_c3_b2_audit_poisson_0.925_C3_static.json` | C3-B2, argmin, gamma, tie-break audit |

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

## Threats to validity

| ID | Scope | Limitation | Status |
|---|---|---|---|
| L20 | comparison | Matched coverage can hide different true intervention rates. | Closed for C3-B2 at 0.78; abs gap 0.001274 <= 0.010 |
| L21 | multiplicity | Effective action space is 3, while nominal design has K=4 actions and K-1=3 score slots. Cost of the dead action/slot is not quantified. | Open |
| L22 | model selection | Gamma sweep is on test; gamma != 1 is not guarantee-preserving. | Closed as diagnostic only |
| L23 | taxonomy | C3 uses `z_bin x m_hat_bin`; age-only asymptotic arguments can fail. | Closed by G23-21b for current artifact |
| L24 | finite cells | Mondrian cells could be too thin, making `q_hat=+inf` or weak. | Closed by G23-21c for current artifact; min effective blocks 433 |

## Before Lesson 23.4

Lesson 23.4 may proceed only with these constraints:

```text
1. Do not use gamma != 1 as a certified operating point unless a new conformal
   calibration theorem and validation are written first.
2. Any learned B7-like selector must fit on CALIB and evaluate on TEST.
3. Any argmin-information claim must report chance agreement and kappa.
4. Any cross-cell claim must keep C3-vs-B2 as "reported, not thresholded" unless
   paired CIs exclude 0.
5. Preserve the C3 taxonomy as `z_bin x m_hat_bin`; do not collapse it to
   age-only notation in claims about guarantees.
```

## Verification

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase23_baselines.py -q
11 passed in 14.42s

/tmp/dt4n-venv/bin/python -m pytest \
  test/test_phase23_baselines.py test/test_phase23_thresholds.py \
  test/test_phase23_prereg.py -q
26 passed in 25.49s
```

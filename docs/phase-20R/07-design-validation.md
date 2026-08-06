# Phase 20R.6 -- Design Validation

Trang thai: preregistration truoc khi chay testbed additivity/quasistatic.
Ngay ky: 2026-08-06.

## Muc Tieu

Lesson 20R.6 kiem tra ba diem con lai sau H7/H8:

- G6 additivity: chi so `cost_path` co tuong duong voi tong chi phi link hay
  co cascade end-to-end dang ke.
- Quasistatic o muc decision: composition bang tinh theo `rho(t)` co khop
  measured dynamic trace theo cua so 60 s hay khong.
- Sensitivity voi `a=0.2`: giam bien do `sigma_rho = a * sigma_max` va kiem
  tra `R = sd(cost margin) / mean(cost margin)` van xep hang `err_total`.

Hai ghi chu duoc khoa truoc khi chay:

- H8b margin gan nguong: max `|Delta R| = 0.0189`, nguong 0.02. Vi vay
  20R.6 phai bao cao CI bootstrap block cho chinh `R`; khong chi dung point
  estimate.
- Spearman pooled tau = 0.989 khong mau thuan voi tau-scaling. Luat day du la
  `err = g(R, z/tau)`. Khi gom tau tai `z = 0.55`, `z/tau` thay doi tu 0.11
  den 2.75, nen bao cao dung la `R` dominates trong mien nay, khong phai
  `R` giai thich tat ca.

## Additivity G6

Chi so test la mean cost, khong cong p95/p99. Percentile chi duoc bao cao
neu co end-to-end measurement truc tiep.

Ba nhanh:

- A: link duoc do rieng, lay tu `results/phase-20R/truth_table.parquet`.
- B: link duoc probe rieng trong khi ca path dang mang traffic. `B - A`
  tach CPU contention/probe artifact.
- C: probe end-to-end qua path. `C - sum(B)` la cascade/G6 thuan; `C - sum(A)`
  la tong artifact + cascade.

Thiet ke live mac dinh:

```text
modes       = poisson,h2
rho_bar     = 0.85,0.925
seeds       = 101,102,103,104,105
paths C     = P1,P4 va P2-extra
paths B     = P1 tai rho_bar=0.925; analyzer chap nhan mo rong B
Delta       = 0.44 ms (= 20% cost gap)
TOST        = CI90 phai nam trong [-0.44,+0.44]
power check = 1.645 * se < 0.44
probe gate  = probe intrusion <= 2%
schedule    = paired; `trajectory_digest` phai khop giua cac nhanh cung seed
```

So run du kien:

```text
Branch B: 2 mode x 2 rho x 3 link x 5 seed = 60 run ~= 1.2 h
Branch C: 2 mode x 2 rho x 2 path x 5 seed = 40 run ~= 0.8 h
C-extra P2: 2 mode x 2 rho x 1 path x 5 seed = 20 run ~= 0.4 h
Tong additivity live ~= 2.4 h, cong cleanup/overhead nen nen du tru 3 h
```

Cat giam truoc live run, sau khi co ket qua `a=0.2` va truoc khi chay
Mininet G6:

```text
Branch B: 2 mode x 1 rho_bar(0.925) x 3 link(P1) x 5 seed = 30 run ~= 0.6 h
Branch C: P1/P4 khong cat = 40 run ~= 0.8 h
C-extra P2: poisson x rho_bar 0.925 x 5 seed = 5 run ~= 0.1 h
Tong additivity live moi ~= 1.5 h; du tru 1.8 h ca cleanup/overhead
```

Ly do cat Branch B: B do CPU contention/probe artifact cua ha tang. Chay tai
`rho_bar=0.925`, muc R cao nhat, la worst-case contention. Ket luan G6 chinh
van den tu Branch C end-to-end P1/P4; khong cat o day.

Lenh khoa plan:

```bash
python3 -m measurements.additivity_check --plan-only
python3 -m measurements.additivity_check \
  --write-plan results/phase-20R/additivity_plan.json
```

Sau khi co state live B/C:

```bash
python3 -m measurements.additivity_check \
  --from-state results/phase-20R/additivity_branch_b_state.json,results/phase-20R/additivity_branch_c_state.json \
  --out results/phase-20R/additivity_check.json
```

## Quasistatic Decision

Thiet ke:

```text
mode       = poisson
rho_bar    = 0.925
duration   = 600 s
window     = 60 s
seeds      = 101,102,103,104,105
threshold  = max |measured_cost - table_cost(rho(t))| <= 0.44 ms
```

So run du kien: `600 s x 5 seed = 50 min`, du tru 60 phut ca startup/cleanup.

Cat giam truoc live run: dung `seeds = 101,102,103`, `600 s x 3 seed = 30 min`,
du tru 40 phut. Ly do: day la xac nhan o muc decision, khong phai uoc luong
link-level moi; nguong bat cap can phat hien la `0.44 ms`.

Lenh khoa plan:

```bash
python3 -m measurements.quasistatic_check --plan-only
python3 -m measurements.quasistatic_check \
  --write-plan results/phase-20R/quasistatic_plan.json
```

Sau khi co state live:

```bash
python3 -m measurements.quasistatic_check \
  --from-state results/phase-20R/quasistatic_state.json \
  --out results/phase-20R/quasistatic_check.json
```

## Sensitivity a=0.2 va CI R

Khong chay Mininet; dung `truth_table.parquet`, AR(1) generator da ky, va
bang calibration hien co.

```bash
python3 -m measurements.decision_error_v2 --run-fixed \
  --a-override 0.2 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/sensitivity_a02.parquet

python3 -m measurements.decision_error_v2 --compute-margin-cv \
  --a-override 0.2 \
  --n 200000 \
  --seeds 101,102,103 \
  --out results/phase-20R/margin_cv_a02.parquet

python3 -m measurements.decision_error_v2 --compute-margin-cv-ci \
  --sigma-override 0.0096 \
  --tau 0.2,1.0,5.0 \
  --n 200000 \
  --seeds 101,102,103 \
  --n-boot 2000 \
  --out results/phase-20R/margin_cv_ci.json

python3 -m measurements.plot_decision_error_v2
```

Criterion sensitivity: tai `z=0.55`, `Spearman(R, err_total) > 0.9` tren
`poisson,h2`. Neu fail, bao cao huong fail va tac dong len gate H8.

## Ket Qua Khong-Mininet Sau Prereg

Prereg/code duoc commit truoc khi sinh so tai commit `986a8a3`.

Artifacts da sinh:

```text
results/phase-20R/additivity_plan.json
results/phase-20R/quasistatic_plan.json
results/phase-20R/sensitivity_a02.parquet
results/phase-20R/margin_cv_a02.parquet
results/phase-20R/margin_cv_ci.json
docs/phase-20R/figures/decision_error_a02_margin_cv_vs_err.png
```

Sensitivity `a=0.2` tai `z=0.55`:

```text
mode     rho_bar  R         err_total
h2       0.700    0.667557  0.180545
h2       0.850    0.392885  0.012725
h2       0.925    0.145859  0.000000
h2       0.960    0.064526  0.000000
poisson  0.700    0.177920  0.000000
poisson  0.850    0.747392  0.297133
poisson  0.925    0.733750  0.228484
poisson  0.960    0.438822  0.016551
```

`Spearman(R, err_total) = 0.975900`, `n = 8`, PASS > 0.9.

CI `R` da duoc tinh bang block bootstrap, dung estimator mean theo seed nhu
H8b. Max point delta vs tau=1:

```text
tau=0.2: max |Delta R| = 0.003991
tau=5.0: max |Delta R| = 0.018882
```

H8b van o sat nguong 0.02; CI95 cua R ton tai trong
`results/phase-20R/margin_cv_ci.json`, va ket luan nen viet la `R` on dinh
theo tau trong point estimate, nhung tau=5 co uncertainty rong hon do effective
sample nho hon.

Sau formal H9 review, khoang CI bao thu cho worst H8b:

```text
tau=5, poisson rho_bar=0.85
point |Delta R| = 0.018882
CI bao thu signed delta = [-0.025670, +0.062551]
```

Vi CI bao thu cham/vuot `0.02`, ghi H8b la `PASS theo point estimate; bien
hep, CI cham nguong`, khong viet PASS tron.

H9 formal:

```text
pooled n = 30
Spearman(R, err_total) = 0.994651
c * Phi(-k/R): k = 1.159900, c = 4.760398
H9a PASS: sd(k) = 0.020053 tren ba tap tau=1; 0.015017 tren tau sweep
H9b PASS: Spearman(z/tau, c) = 1.000000 tren tau=1; 0.971625 tren tau sweep
H9c FAIL sat bien: R=0.293424 va R=0.299915 co err_total > 0
```

Artifacts H9:

```text
results/phase-20R/h9_separability.json
docs/phase-20R/figures/decision_error_h9_separability.png
```

`results/phase-20R/additivity_check.json` va
`results/phase-20R/quasistatic_check.json` hien chi la placeholder
`not evaluated`, vi chua chay live Branch B/C va dynamic trace.

## Loi Khong Duoc Lam

- Khong dung ordinary t-test thay cho TOST equivalence.
- Khong dung unpaired schedule neu so sanh B/C.
- Khong chay tat ca probe cung luc.
- Khong bo Branch B khi ket luan G6.
- Khong cong p95/p99.
- Khong chon `Delta` sau khi nhin ket qua.
- Khong sua nguoc `truth_table.parquet` de lam dep G6.

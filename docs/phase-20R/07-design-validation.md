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
paths B     = P1 mac dinh theo ngan sach 60 run; analyzer chap nhan mo rong B
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

## Loi Khong Duoc Lam

- Khong dung ordinary t-test thay cho TOST equivalence.
- Khong dung unpaired schedule neu so sanh B/C.
- Khong chay tat ca probe cung luc.
- Khong bo Branch B khi ket luan G6.
- Khong cong p95/p99.
- Khong chon `Delta` sau khi nhin ket qua.
- Khong sua nguoc `truth_table.parquet` de lam dep G6.

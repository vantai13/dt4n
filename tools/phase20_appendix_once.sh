#!/usr/bin/env bash
set -euo pipefail

cd /home/ubuntu/dt4n
export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"

mkdir -p logs results/phase-20 /tmp/p20_audit

Z_LIST="0,0.05,0.10,0.20,0.298,0.50,1.0,2.0,4.0"
MEASURED_Z_LIST="0,0.2,0.4,0.6,1.0,2.0,4.0"
OFFERED_TRACES="results/phase-20/rho_offered_long.csv,results/phase-20/rho_offered_long_s1.csv,results/phase-20/rho_offered_long_s2.csv,results/phase-20/rho_offered_long_s3.csv,results/phase-20/rho_offered_long_s4.csv"

echo "== Phase 20 appendix/audit once =="
echo "PYTHON_BIN=$PYTHON_BIN"
echo "No Mininet is started by this script."

echo "== 1. L7 diagnostics: core mean and block crossing =="
"$PYTHON_BIN" -m measurements.phase20_core_load_diagnostic \
  --traces "$OFFERED_TRACES" \
  --summary results/phase-20/between_trace_summary_n5.json \
  --out results/phase-20/core_load_diagnostic_n5.json \
  2>&1 | tee logs/phase20_appendix_01_core_load_diagnostic.log

"$PYTHON_BIN" -m measurements.phase20_block_crossing_diagnostic \
  --traces "$OFFERED_TRACES" \
  --calibration results/phase-20/decision_error_offered.json \
  --out results/phase-20/block_crossing_diagnostic_n5.json \
  2>&1 | tee logs/phase20_appendix_01_block_crossing_diagnostic.log

echo "== 2. L8 measured fixed cross-check =="
for S in 0 1 2 3 4; do
  TRACE="results/phase-20/rho_measured_long.csv"
  if [[ "$S" != "0" ]]; then TRACE="results/phase-20/rho_measured_long_s${S}.csv"; fi
  "$PYTHON_BIN" -m measurements.decision_error \
    --trace "$TRACE" \
    --tau-core 2.87 \
    --sync-period 0.5 \
    --d-sync 0.051 \
    --z-list "$MEASURED_Z_LIST" \
    --operational-mode bracket \
    --freeze-calibration results/phase-20/decision_error_offered.json \
    --seeds 100 \
    --n-boot 2000 \
    --out "results/phase-20/decision_error_measured_fixed_trace_s${S}.json" \
    2>&1 | tee "logs/phase20_appendix_02_measured_fixed_s${S}.log"
done

MEASURED_INPUTS="results/phase-20/decision_error_measured_fixed_trace_s0.json,results/phase-20/decision_error_measured_fixed_trace_s1.json,results/phase-20/decision_error_measured_fixed_trace_s2.json,results/phase-20/decision_error_measured_fixed_trace_s3.json,results/phase-20/decision_error_measured_fixed_trace_s4.json"
"$PYTHON_BIN" -m measurements.summarize_decision_error_replicates \
  --inputs "$MEASURED_INPUTS" \
  --run-seed 100 \
  --out results/phase-20/decision_error_measured_fixed_replicates_summary.json \
  2>&1 | tee logs/phase20_appendix_02_measured_fixed_summary.log

"$PYTHON_BIN" -m measurements.phase20_measured_crosscheck_diagnostic \
  --out results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json \
  2>&1 | tee logs/phase20_appendix_02_measured_fixed_diagnostic.log

echo "== 3. Reproducibility audit for offered n=5 =="
rm -rf /tmp/p20_audit
mkdir -p /tmp/p20_audit
for S in 0 1 2 3 4; do
  TRACE="results/phase-20/rho_offered_long.csv"
  if [[ "$S" != "0" ]]; then TRACE="results/phase-20/rho_offered_long_s${S}.csv"; fi
  "$PYTHON_BIN" -m measurements.decision_error \
    --trace "$TRACE" \
    --tau-core 2.87 \
    --sync-period 0.5 \
    --d-sync 0.051 \
    --z-list "$Z_LIST" \
    --freeze-calibration results/phase-20/decision_error_offered.json \
    --seeds 100 \
    --n-boot 2000 \
    --out "/tmp/p20_audit/s${S}.json" \
    2>&1 | tee "logs/phase20_appendix_03_audit_s${S}.log"
done

"$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

tol = 1e-12
ok = True
for s in range(5):
    new = json.load(open(f"/tmp/p20_audit/s{s}.json"))["runs"]["100"]["evaluation"]["operational"]
    old = json.load(open(f"results/phase-20/decision_error_trace_s{s}.json"))["runs"]["100"]["evaluation"]["operational"]
    derr = abs(float(new["err"]) - float(old["err"]))
    dd = abs(float(new["d_sla"]) - float(old["d_sla"]))
    passed = derr < tol and dd < tol
    ok = ok and passed
    print(f"s{s}: err_delta={derr:.3g} d_sla_delta={dd:.3g} pass={passed}")

Path("/tmp/p20_audit/audit_status.txt").write_text(
    "PASS\n" if ok else "FAIL\n",
    encoding="utf-8",
)
if not ok:
    raise SystemExit("Phase 20 reproducibility audit failed")
PY

echo "== 4. Final compact report =="
"$PYTHON_BIN" - <<'PY'
import json

def metric_line(name, row):
    ci = row["ci95_mean_t"]
    return f"{name}: mean={row['point_mean']:.5f}, CI95=[{ci['lo']:.5f}, {ci['hi']:.5f}]"

offered = json.load(open("results/phase-20/between_trace_summary_n5.json"))
measured = json.load(open("results/phase-20/decision_error_measured_fixed_replicates_summary.json"))
block = json.load(open("results/phase-20/block_crossing_diagnostic_n5.json"))
paired = json.load(open("results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json"))

print("\n=== offered n=5 ===")
print(metric_line("err", offered["err"]))
print(metric_line("d_sla", offered["d_sla"]))

print("\n=== measured fixed n=5 ===")
print(metric_line("err", measured["err"]))
print(metric_line("d_sla", measured["d_sla"]))
print(
    "ratios measured/offered: "
    f"err={measured['err']['point_mean'] / offered['err']['point_mean']:.3f}, "
    f"d_sla={measured['d_sla']['point_mean'] / offered['d_sla']['point_mean']:.3f}"
)
print(
    "d_sla lower/0.03: "
    f"offered={offered['d_sla']['ci95_mean_t']['lo'] / 0.03:.2f}x, "
    f"measured_fixed={measured['d_sla']['ci95_mean_t']['lo'] / 0.03:.2f}x"
)

print("\n=== L7 block crossing ===")
for key, row in block["correlations"].items():
    ci = row["ci95"]
    print(f"{key}: r={row['r']:.3f}, CI95=[{ci['lo']:.3f}, {ci['hi']:.3f}]")

print("\n=== offered - measured_fixed ===")
for metric in ["err", "d_sla"]:
    row = paired["paired_offered_minus_measured"][metric]
    vals = ", ".join(f"{x:.4f}" for x in row["values"])
    print(f"{metric}: [{vals}], t={row['t_stat']:.2f}, df={row['df']}")
print("two-sided sign-test p for 5/5 same sign: 0.0625")

print("\n=== mechanism risk ratio ===")
mech = paired["mechanism_comparison"]
off = mech["offered"]
mf = mech["measured_fixed"]
rr = mech["paired_measured_minus_offered"]["risk_ratio"]
print(f"offered: mean={off['risk_ratio_mean']:.2f}, SD={off['risk_ratio_sd']:.2f}")
print(f"measured_fixed: mean={mf['risk_ratio_mean']:.2f}, SD={mf['risk_ratio_sd']:.2f}")
print(f"measured-offered: mean={rr['mean']:.2f}, t={rr['t_stat']:.2f}, df={rr['df']} (p ~= 0.65)")
print(
    "P(error|not crossed): "
    f"offered={off['p_error_given_not_crossed_mean']:.4f}, "
    f"measured_fixed={mf['p_error_given_not_crossed_mean']:.4f}"
)

print("\n=== measured fixed gates ===")
for row in paired["measured_run_diagnostics"]:
    print(
        f"s{row['trace_id']}: mean_age={row['mean_age_s']:.3f}, "
        f"pass_without_G6={row['pass_without_G6']}, false={row['false_bool_gates']}"
    )

print("\nAudit status: " + open("/tmp/p20_audit/audit_status.txt", encoding="utf-8").read().strip())
PY

echo "== Complete =="
echo "Audit files: /tmp/p20_audit/"
echo "Main log: logs/phase20_appendix_once.log if run through tee"

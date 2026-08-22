#!/usr/bin/env bash
set -euo pipefail

cd /home/ubuntu/dt4n
export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
mkdir -p logs results/SUPERSEDED/phase-20

Z_LIST="0,0.05,0.10,0.20,0.298,0.50,1.0,2.0,4.0"
MEASURED_Z_LIST="0,0.2,0.4,0.6,1.0,2.0,4.0"
DE_COMMON=(--tau-core 2.87 --sync-period 0.5 --d-sync 0.051 --z-list "$Z_LIST")
DE_MEASURED_COMMON=(--tau-core 2.87 --sync-period 0.5 --d-sync 0.051 --z-list "$MEASURED_Z_LIST" --operational-mode bracket)

echo "== Phase 20 full n=5 rerun =="
echo "PYTHON_BIN=$PYTHON_BIN"

echo "== 0. Smoke =="
./tools/phase20_smoke.sh 2>&1 | tee logs/phase20_full5_00_smoke.log

echo "== 1. Quick check C1-C3 =="
sudo mn -c
sudo "$PYTHON_BIN" -m mininet.run_sync_v7 \
  --traffic v7 \
  --duration 60 \
  --log-dt 0.010 \
  --measured-window 0.200 \
  --core-sigma 0.10 \
  --edge-sigma 0.03 \
  --seed 0 \
  --quick-check \
  --offered-out results/SUPERSEDED/phase-20/rho_offered_quick.csv \
  --measured-out results/SUPERSEDED/phase-20/rho_measured_quick.csv \
  --meta-out results/SUPERSEDED/phase-20/rho_trace_quick_meta.json \
  --flow-log-dir results/SUPERSEDED/phase-20/flow_logs_quick \
  2>&1 | tee logs/phase20_full5_01_quick.log

echo "== 2. Resolution check 10 ms =="
sudo mn -c
sudo "$PYTHON_BIN" -m mininet.run_sync_v7 \
  --traffic v7 \
  --duration 300 \
  --log-dt 0.010 \
  --measured-window 0.200 \
  --core-sigma 0.10 \
  --edge-sigma 0.03 \
  --seed 0 \
  --offered-out results/SUPERSEDED/phase-20/rho_offered_10ms.csv \
  --measured-out results/SUPERSEDED/phase-20/rho_measured_10ms.csv \
  --meta-out results/SUPERSEDED/phase-20/rho_trace_10ms_meta.json \
  --flow-log-dir results/SUPERSEDED/phase-20/flow_logs_10ms \
  2>&1 | tee logs/phase20_full5_02_10ms.log

echo "== 3. Resolution check 2 ms =="
sudo mn -c
sudo "$PYTHON_BIN" -m mininet.run_sync_v7 \
  --traffic v7 \
  --duration 300 \
  --log-dt 0.002 \
  --measured-window 0.200 \
  --core-sigma 0.10 \
  --edge-sigma 0.03 \
  --seed 0 \
  --offered-out results/SUPERSEDED/phase-20/rho_offered_2ms.csv \
  --measured-out results/SUPERSEDED/phase-20/rho_measured_2ms.csv \
  --meta-out results/SUPERSEDED/phase-20/rho_trace_2ms_meta.json \
  --flow-log-dir results/SUPERSEDED/phase-20/flow_logs_2ms \
  2>&1 | tee logs/phase20_full5_03_2ms.log

echo "== 4. Long traces seed 0..4 =="
for S in 0 1 2 3 4; do
  sudo mn -c
  OFFERED="results/SUPERSEDED/phase-20/rho_offered_long.csv"
  MEASURED="results/SUPERSEDED/phase-20/rho_measured_long.csv"
  META="results/SUPERSEDED/phase-20/rho_trace_long_meta.json"
  FLOW_DIR="results/SUPERSEDED/phase-20/flow_logs_long"
  if [[ "$S" != "0" ]]; then
    OFFERED="results/SUPERSEDED/phase-20/rho_offered_long_s${S}.csv"
    MEASURED="results/SUPERSEDED/phase-20/rho_measured_long_s${S}.csv"
    META="results/SUPERSEDED/phase-20/rho_trace_long_s${S}_meta.json"
    FLOW_DIR="results/SUPERSEDED/phase-20/flow_logs_long_s${S}"
  fi
  sudo "$PYTHON_BIN" -m mininet.run_sync_v7 \
    --traffic v7 \
    --duration 1800 \
    --log-dt 0.010 \
    --measured-window 0.200 \
    --core-sigma 0.10 \
    --edge-sigma 0.03 \
    --seed "$S" \
    --offered-out "$OFFERED" \
    --measured-out "$MEASURED" \
    --meta-out "$META" \
    --flow-log-dir "$FLOW_DIR" \
    2>&1 | tee "logs/phase20_full5_04_trace_s${S}.log"
done
sudo mn -c

echo "== 5. Tau and estimator analysis =="
"$PYTHON_BIN" -m measurements.measure_tau \
  --input results/SUPERSEDED/phase-20/rho_offered_10ms.csv \
  --core-sigma-target 0.10 \
  --edge-sigma-target 0.03 \
  --acf-windows 6,60 \
  --out results/SUPERSEDED/phase-20/tau_summary_10ms.json \
  2>&1 | tee logs/phase20_full5_05_tau_10ms.log

"$PYTHON_BIN" -m measurements.measure_tau \
  --input results/SUPERSEDED/phase-20/rho_offered_2ms.csv \
  --core-sigma-target 0.10 \
  --edge-sigma-target 0.03 \
  --acf-windows 6,60 \
  --out results/SUPERSEDED/phase-20/tau_summary_2ms.json \
  2>&1 | tee logs/phase20_full5_05_tau_2ms.log

"$PYTHON_BIN" -m measurements.measure_tau \
  --input results/SUPERSEDED/phase-20/rho_offered_long.csv \
  --core-sigma-target 0.10 \
  --edge-sigma-target 0.03 \
  --acf-windows 6,60 \
  --out results/SUPERSEDED/phase-20/tau_summary_long.json \
  2>&1 | tee logs/phase20_full5_05_tau_long.log

"$PYTHON_BIN" -m measurements.compare_estimators \
  --offered results/SUPERSEDED/phase-20/rho_offered_10ms.csv \
  --measured results/SUPERSEDED/phase-20/rho_measured_10ms.csv \
  --out results/SUPERSEDED/phase-20/estimator_compare_10ms.json \
  2>&1 | tee logs/phase20_full5_05_estimator_10ms.log

"$PYTHON_BIN" -m measurements.compare_estimators \
  --offered results/SUPERSEDED/phase-20/rho_offered_long.csv \
  --measured results/SUPERSEDED/phase-20/rho_measured_long.csv \
  --out results/SUPERSEDED/phase-20/estimator_compare_long.json \
  2>&1 | tee logs/phase20_full5_05_estimator_long.log

echo "== 6. Decision error self-calibrated offered seed0 =="
"$PYTHON_BIN" -m measurements.decision_error \
  --trace results/SUPERSEDED/phase-20/rho_offered_long.csv \
  --dt 0.010 \
  "${DE_COMMON[@]}" \
  --seeds 100 \
  --nc-only \
  --out results/SUPERSEDED/phase-20/decision_error_offered_nc.json \
  2>&1 | tee logs/phase20_full5_06_decision_error_nc.log

"$PYTHON_BIN" -m measurements.decision_error \
  --trace results/SUPERSEDED/phase-20/rho_offered_long.csv \
  --dt 0.010 \
  "${DE_COMMON[@]}" \
  --seeds 100,101,102 \
  --n-boot 2000 \
  --out results/SUPERSEDED/phase-20/decision_error_offered.json \
  2>&1 | tee logs/phase20_full5_06_decision_error_offered.log

echo "== 7. Frozen offered decision error seed0..4 =="
for S in 0 1 2 3 4; do
  TRACE="results/SUPERSEDED/phase-20/rho_offered_long.csv"
  if [[ "$S" != "0" ]]; then TRACE="results/SUPERSEDED/phase-20/rho_offered_long_s${S}.csv"; fi
  "$PYTHON_BIN" -m measurements.decision_error \
    --trace "$TRACE" \
    --dt 0.010 \
    "${DE_COMMON[@]}" \
    --freeze-calibration results/SUPERSEDED/phase-20/decision_error_offered.json \
    --seeds 100 \
    --n-boot 2000 \
    --out "results/SUPERSEDED/phase-20/decision_error_trace_s${S}.json" \
    2>&1 | tee "logs/phase20_full5_07_decision_error_trace_s${S}.log"
done

SUMMARY_INPUTS="results/SUPERSEDED/phase-20/decision_error_trace_s0.json,results/SUPERSEDED/phase-20/decision_error_trace_s1.json,results/SUPERSEDED/phase-20/decision_error_trace_s2.json,results/SUPERSEDED/phase-20/decision_error_trace_s3.json,results/SUPERSEDED/phase-20/decision_error_trace_s4.json"
"$PYTHON_BIN" -m measurements.summarize_decision_error_replicates \
  --inputs "$SUMMARY_INPUTS" \
  --run-seed 100 \
  --out results/SUPERSEDED/phase-20/decision_error_replicates_summary.json
"$PYTHON_BIN" -m measurements.summarize_decision_error_replicates \
  --inputs "$SUMMARY_INPUTS" \
  --run-seed 100 \
  --out results/SUPERSEDED/phase-20/between_trace_summary.json
"$PYTHON_BIN" -m measurements.summarize_decision_error_replicates \
  --inputs "$SUMMARY_INPUTS" \
  --run-seed 100 \
  --out results/SUPERSEDED/phase-20/between_trace_summary_n5.json

"$PYTHON_BIN" -m measurements.phase20_core_load_diagnostic \
  --traces results/SUPERSEDED/phase-20/rho_offered_long.csv,results/SUPERSEDED/phase-20/rho_offered_long_s1.csv,results/SUPERSEDED/phase-20/rho_offered_long_s2.csv,results/SUPERSEDED/phase-20/rho_offered_long_s3.csv,results/SUPERSEDED/phase-20/rho_offered_long_s4.csv \
  --summary results/SUPERSEDED/phase-20/between_trace_summary_n5.json \
  --out results/SUPERSEDED/phase-20/core_load_diagnostic_n5.json \
  2>&1 | tee logs/phase20_full5_07_core_load_diagnostic.log

"$PYTHON_BIN" -m measurements.phase20_block_crossing_diagnostic \
  --traces results/SUPERSEDED/phase-20/rho_offered_long.csv,results/SUPERSEDED/phase-20/rho_offered_long_s1.csv,results/SUPERSEDED/phase-20/rho_offered_long_s2.csv,results/SUPERSEDED/phase-20/rho_offered_long_s3.csv,results/SUPERSEDED/phase-20/rho_offered_long_s4.csv \
  --calibration results/SUPERSEDED/phase-20/decision_error_offered.json \
  --out results/SUPERSEDED/phase-20/block_crossing_diagnostic_n5.json \
  2>&1 | tee logs/phase20_full5_07_block_crossing_diagnostic.log

echo "== 8. Measured telemetry cross-check seed0..4 =="
for S in 0 1 2 3 4; do
  TRACE="results/SUPERSEDED/phase-20/rho_measured_long.csv"
  if [[ "$S" != "0" ]]; then TRACE="results/SUPERSEDED/phase-20/rho_measured_long_s${S}.csv"; fi
  "$PYTHON_BIN" -m measurements.decision_error \
    --trace "$TRACE" \
    "${DE_MEASURED_COMMON[@]}" \
    --freeze-calibration results/SUPERSEDED/phase-20/decision_error_offered.json \
    --seeds 100 \
    --n-boot 2000 \
    --out "results/SUPERSEDED/phase-20/decision_error_measured_fixed_trace_s${S}.json" \
    2>&1 | tee "logs/phase20_full5_08_decision_error_measured_fixed_s${S}.log"
done

MEASURED_INPUTS="results/SUPERSEDED/phase-20/decision_error_measured_fixed_trace_s0.json,results/SUPERSEDED/phase-20/decision_error_measured_fixed_trace_s1.json,results/SUPERSEDED/phase-20/decision_error_measured_fixed_trace_s2.json,results/SUPERSEDED/phase-20/decision_error_measured_fixed_trace_s3.json,results/SUPERSEDED/phase-20/decision_error_measured_fixed_trace_s4.json"
"$PYTHON_BIN" -m measurements.summarize_decision_error_replicates \
  --inputs "$MEASURED_INPUTS" \
  --run-seed 100 \
  --out results/SUPERSEDED/phase-20/decision_error_measured_fixed_replicates_summary.json

"$PYTHON_BIN" -m measurements.phase20_measured_crosscheck_diagnostic \
  --out results/SUPERSEDED/phase-20/measured_fixed_crosscheck_diagnostic_n5.json \
  2>&1 | tee logs/phase20_full5_08_measured_crosscheck_diagnostic.log

echo "== Phase 20 full n=5 rerun complete =="
echo "Main outputs:"
echo "  results/SUPERSEDED/phase-20/between_trace_summary_n5.json"
echo "  results/SUPERSEDED/phase-20/core_load_diagnostic_n5.json"
echo "  results/SUPERSEDED/phase-20/block_crossing_diagnostic_n5.json"
echo "  results/SUPERSEDED/phase-20/decision_error_measured_fixed_replicates_summary.json"
echo "  results/SUPERSEDED/phase-20/measured_fixed_crosscheck_diagnostic_n5.json"

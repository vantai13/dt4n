#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"

mkdir -p logs results/phase-20

echo "[1/5] compile"
"$PYTHON_BIN" -m py_compile \
  mininet/flow_engine.py \
  mininet/traffic_v7.py \
  mininet/run_sync_v7.py \
  measurements/measure_tau.py \
  measurements/compare_estimators.py

echo "[2/5] dry-run traffic profile"
"$PYTHON_BIN" -m mininet.run_sync_v7 --dry-run

echo "[3/5] 12s Mininet smoke trace"
sudo mn -c >/dev/null 2>&1 || true
sudo "$PYTHON_BIN" -m mininet.run_sync_v7 \
  --traffic v7 \
  --log-dt 0.050 \
  --measured-window 0.200 \
  --duration 12 \
  --seed 0 \
  --core-sigma 0.10 \
  --edge-sigma 0.03 \
  --offered-out results/phase-20/rho_offered_smoke.csv \
  --measured-out results/phase-20/rho_measured_smoke.csv \
  --meta-out results/phase-20/rho_trace_smoke_meta.json \
  --flow-log-dir results/phase-20/flow_logs_smoke \
  2>&1 | tee logs/phase20_tau_smoke.log

echo "[4/5] analyze offered smoke trace"
"$PYTHON_BIN" -m measurements.measure_tau \
  --input results/phase-20/rho_offered_smoke.csv \
  --core-sigma-target 0.10 \
  --edge-sigma-target 0.03 \
  --out results/phase-20/tau_summary_smoke.json \
  2>&1 | tee logs/phase20_tau_smoke_analyze.log

echo "[5/5] compare offered vs measured estimators"
"$PYTHON_BIN" -m measurements.compare_estimators \
  --offered results/phase-20/rho_offered_smoke.csv \
  --measured results/phase-20/rho_measured_smoke.csv \
  --out results/phase-20/estimator_compare_smoke.json \
  2>&1 | tee logs/phase20_tau_smoke_compare.log

echo "OK: smoke outputs are in results/phase-20/ and logs/"

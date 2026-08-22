#!/usr/bin/env bash
# Fine sweep around the measured finite-queue cliff on the canonical
# bw=4M, base=2ms, q=13 calibration link.

set -uo pipefail

cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"

PY="${PYTHON:-$(command -v python3)}"
STAMP="$(date +%m%d_%H%M)"
OUT="results/SUPERSEDED/calib/cliff_fine_${STAMP}.csv"
RAW="results/SUPERSEDED/calib/cliff_fine_${STAMP}_raw.csv"
LOG="logs/calib/cliff_fine_${STAMP}.log"

mkdir -p results/SUPERSEDED/calib logs/calib
sudo mn -c >/dev/null 2>&1 || true

sudo -E env PYTHONPATH="$PWD" "$PY" measurements/qdisc_density_probe.py \
  --bw 4 --delay 2 --queue 13 \
  --rates 3.70,3.72,3.74,3.76,3.78,3.80 \
  --samples 200 --interval 0.05 --settle 3 \
  --out "$OUT" \
  --raw-out "$RAW" \
  2>&1 | tee "$LOG" | grep -E 'rho_off=|Wrote|Traceback|RuntimeError|Error'
status=${PIPESTATUS[0]}

sudo mn -c >/dev/null 2>&1 || true

if [ "$status" -ne 0 ]; then
  echo "FAILED; xem $LOG"
  exit "$status"
fi

echo
echo "=== analysis ==="
"$PY" measurements/analyze_qdisc_density.py "$OUT"

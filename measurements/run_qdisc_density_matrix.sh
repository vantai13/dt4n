#!/usr/bin/env bash
# Run the three qdisc-density configurations needed to test whether the
# low-load 0/1-packet distribution depends on base delay.

set -uo pipefail

cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"

PY="${PYTHON:-$(command -v python3)}"
STAMP="$(date +%m%d_%H%M)"
SUMMARY_FILES=()

mkdir -p results/SUPERSEDED/calib logs/calib

rates_for_bw() {
  "$PY" - "$1" <<'PY'
import sys
bw = float(sys.argv[1])
fracs = [0.3, 0.5, 0.7, 0.9, 0.925, 0.95, 1.3]
print(",".join("%g" % round(bw * frac, 3) for frac in fracs))
PY
}

run_cfg() {
  local bw="$1"
  local delay="$2"
  local queue="$3"
  local tag="bw${bw}_d${delay}_q${queue}_${STAMP}"
  local rates
  local out
  local raw
  local log
  local status

  rates="$(rates_for_bw "$bw")"
  out="results/SUPERSEDED/calib/density_${tag}.csv"
  raw="results/SUPERSEDED/calib/density_${tag}_raw.csv"
  log="logs/calib/density_${tag}.log"
  SUMMARY_FILES+=("$out")

  sudo mn -c >/dev/null 2>&1 || true
  echo
  echo "=== bw=${bw}M base=${delay}ms q=${queue} rates=${rates} ==="
  echo "log: ${log}"

  sudo -E env PYTHONPATH="$PWD" "$PY" measurements/qdisc_density_probe.py \
    --bw "$bw" --delay "$delay" --queue "$queue" \
    --rates "$rates" \
    --samples 200 --interval 0.05 --settle 3 \
    --out "$out" \
    --raw-out "$raw" \
    2>&1 | tee "$log" | grep -E 'rho_off=|Wrote|Traceback|RuntimeError|Error'
  status=${PIPESTATUS[0]}

  if [ "$status" -ne 0 ]; then
    echo "FAILED: bw=${bw} base=${delay} q=${queue}; xem ${log}"
    sudo mn -c >/dev/null 2>&1 || true
    exit "$status"
  fi
}

run_cfg 4 2.0 13
run_cfg 6 3.0 20
run_cfg 8 1.5 26

sudo mn -c >/dev/null 2>&1 || true

echo
echo "=== analysis ==="
"$PY" measurements/analyze_qdisc_density.py "${SUMMARY_FILES[@]}"

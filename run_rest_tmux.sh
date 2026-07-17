#!/usr/bin/env bash
# run_rest_tmux.sh - Run D, B, A2, A3 with live screen output and logs.

set -u
set -o pipefail

cd ~/dt4n
export PYTHONPATH="$PWD"
export PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache

mkdir -p results/calib logs/calib
T="$(date +%m%d_%H%M)"
MASTER_LOG="logs/calib/run_rest_${T}.log"

log(){
  printf '%s\n' "$*" | tee -a "$MASTER_LOG"
}

preflight(){
  log "== PREFLIGHT $(date '+%F %T') =="
  which mn mnexec tc iperf | tee -a "$MASTER_LOG"
  conda run -n sdn_net ryu-manager --version | tee -a "$MASTER_LOG"
  python3 - <<'PY' | tee -a "$MASTER_LOG"
import numpy
import mininet
import requests
print("python imports ok")
PY
  sudo -v
}

run_step(){
  local name="$1"
  local limit="$2"
  shift 2
  local step_log="logs/calib/${name}_${T}.log"

  log ""
  log "▶ [$(date +%H:%M:%S)] ${name}"
  log "  log: ${step_log}"

  # B starts its own Ryu controller after this cleanup. D/A2/A3 do not need Ryu.
  sudo mn -c >/dev/null 2>&1 || true

  {
    echo "=== ${name} START $(date '+%F %T') ==="
    echo "CMD: $*"
    stdbuf -oL -eL timeout "$limit" "$@"
    status=$?
    echo "=== ${name} END status=${status} $(date '+%F %T') ==="
    exit "$status"
  } 2>&1 | tee -a "$step_log" | tee -a "$MASTER_LOG"

  local status=${PIPESTATUS[0]}
  case "$status" in
    0)   log "  ✅ ${name} xong ($(date +%H:%M:%S))" ;;
    124) log "  ⏰ ${name} TIMEOUT -> ${step_log}" ;;
    *)   log "  ❌ ${name} lỗi status=${status} -> ${step_log}" ;;
  esac
  return "$status"
}

analyze_optional(){
  log ""
  log "== ANALYZE SNAPSHOT $(date '+%F %T') =="
  if [[ -s results/calib/raw_tcp_probe.csv ]]; then
    python3 measurements/analyze_tcp_probe.py \
      --csv results/calib/raw_tcp_probe.csv 2>&1 | tee -a "$MASTER_LOG" || true
  fi
  if [[ -s results/calib/raw_composition.csv ]]; then
    python3 measurements/analyze_topo_validate.py \
      --csv results/calib/raw_composition.csv 2>&1 | tee -a "$MASTER_LOG" || true
  fi
  if [[ -s results/calib/raw_sweep_2node.csv ]]; then
    python3 -m rl.routing.link_model_fit \
      --csv results/calib/raw_sweep_2node.csv \
      --out-json results/calib/link_profiles.json \
      --out-report results/calib/fit_report.md 2>&1 | tee -a "$MASTER_LOG" || true
  fi
}

main(){
  preflight

  # D: TCP probe. Cheap and first. Measures instrument effect.
  run_step D_tcp 600 \
    sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX="$PYTHONPYCACHEPREFIX" \
    python3 measurements/tcp_probe.py \
    --bw 4 --delay 2 --queues 4,13 \
    --out results/calib/raw_tcp_probe.csv

  # B: path composition. calib_composition starts/stops Ryu in sdn_net itself.
  run_step B_composition 2400 \
    sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX="$PYTHONPYCACHEPREFIX" \
    python3 measurements/calib_composition.py \
    --repeats 8 --duration 8 \
    --out results/calib/raw_composition.csv

  # A2/A3: expensive bandwidth generalization checks.
  run_step A2_bw6 12000 \
    sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX="$PYTHONPYCACHEPREFIX" \
    python3 -m measurements.calib_link_sweep \
    --bw 6 --delay 3 --repeats 10 --duration 10 --settle 2 \
    --queue-targets 5,15,40 \
    --out results/calib/raw_sweep_2node.csv

  run_step A3_bw8 12000 \
    sudo -E env PYTHONPATH="$PWD" PYTHONPYCACHEPREFIX="$PYTHONPYCACHEPREFIX" \
    python3 -m measurements.calib_link_sweep \
    --bw 8 --delay 1.5 --repeats 10 --duration 10 --settle 2 \
    --queue-targets 5,15,40 \
    --out results/calib/raw_sweep_2node.csv

  sudo mn -c >/dev/null 2>&1 || true
  analyze_optional

  log ""
  log "═══ XONG $(date '+%F %T') ═══"
  wc -l results/calib/*.csv 2>&1 | tee -a "$MASTER_LOG" || true
  log "MASTER_LOG=${MASTER_LOG}"
}

main "$@"

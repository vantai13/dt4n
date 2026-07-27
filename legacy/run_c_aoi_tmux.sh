#!/usr/bin/env bash
# run_c_aoi_tmux.sh - Run Lesson 9.0 measurement C with logs.

set -u
set -o pipefail

cd ~/dt4n
export PYTHONPATH="$PWD"
export PYTHONPYCACHEPREFIX=/tmp/dt4n-pycache

mkdir -p results/calib logs/calib
T="$(date +%m%d_%H%M)"
LOG="logs/calib/C_aoi_${T}.log"

{
  echo "== C AOI START $(date '+%F %T') =="
  echo "Ditto health:"
  python3 - <<'PY'
import requests
r = requests.get('http://localhost:8080/health', timeout=2)
print(r.status_code, r.text[:120])
PY
  echo "Ryu:"
  conda run -n sdn_net ryu-manager --version
  echo "Clean Mininet:"
  sudo mn -c >/dev/null 2>&1 || true
  echo "Run measurement C:"
  stdbuf -oL -eL timeout 1200 sudo -E env \
    PYTHONPATH="$PWD" \
    PYTHONPYCACHEPREFIX="$PYTHONPYCACHEPREFIX" \
    python3 measurements/calib_aoi_routing_auto.py \
      --mode all \
      --duration 60 \
      --period 1.0 \
      --interval 0.2 \
      --out results/calib/raw_aoi_routing.csv
  status=$?
  echo "== C AOI MEASURE END status=${status} $(date '+%F %T') =="
  if [[ "$status" -eq 0 && -s results/calib/raw_aoi_routing.csv ]]; then
    echo "Analyze C:"
    python3 measurements/analyze_aoi.py \
      --csv results/calib/raw_aoi_routing.csv
    echo "CSV lines:"
    wc -l results/calib/raw_aoi_routing.csv
  fi
  sudo mn -c >/dev/null 2>&1 || true
  echo "== C AOI DONE $(date '+%F %T') =="
  exit "$status"
} 2>&1 | tee -a "$LOG"

exit "${PIPESTATUS[0]}"

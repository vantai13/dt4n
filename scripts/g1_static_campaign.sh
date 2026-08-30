#!/usr/bin/env bash
# Phase G.1 NC-G1-static campaign. Network data may only be generated after
# the preregistration tag exists and the restricted local custody gate passes.
set -euo pipefail

PY="${PY:-/home/ubuntu/miniforge3/envs/sdn_rl/bin/python}"
DURATION="${DURATION:-300}"
RHO_BAR="${RHO_BAR:-0.857}"
REPS="${REPS:-3}"

if [ "$DURATION" = "300" ] && [ "$REPS" = "3" ]; then
  ROOT="${ROOT:-results/RAW/phase-G/g1-static}"
  CERT_OUT="${CERT_OUT:-results/LIVE/phase-G/measurement_path_cert.json}"
  DETAIL_OUT="${DETAIL_OUT:-results/SMOKE/phase-G/g1_static_nc_detail.json}"
else
  ROOT="${ROOT:-results/RAW/phase-G/g1-static-smoke}"
  CERT_OUT="${CERT_OUT:-results/SMOKE/phase-G/g1_static_smoke_cert.json}"
  DETAIL_OUT="${DETAIL_OUT:-results/SMOKE/phase-G/g1_static_smoke_detail.json}"
fi

"$PY" -m tools.check_phase_g_custody
git rev-parse -q --verify 'refs/tags/phase-G-g1-static-nc-prereg' >/dev/null || {
  echo '[G1S-4] BLOCKED: preregistration tag does not exist' >&2
  exit 1
}

run_cell () {
  local name="$1" ditto="$2" aoi="$3" recon="$4" rep="$5"
  local out="$ROOT/$name/rep$rep"
  if [ -f "$out/run_complete.json" ]; then
    echo "=== SKIP complete $name rep$rep ==="
    return
  fi
  mkdir -p "$out/flow_logs"
  echo "=== $name rep$rep (ditto=$ditto aoi=$aoi reconcile=$recon) ==="

  local flags=(
    --traffic static --duration "$DURATION" --rho-bar "$RHO_BAR"
    --measured-window 0.200 --log-dt 0.010
    --measured-out "$out/rho_measured.csv"
    --meta-out "$out/rho_trace_meta.json"
    --flow-log-dir "$out/flow_logs"
    --reconcile-every "$recon" --seed "$rep"
  )
  if [ "$ditto" = "on" ]; then
    # prod+tol=0 preserves recon=1 as full-push while allowing recon=30 to
    # remain a real factor. clean mode would silently force every value to 1.
    flags+=(--ditto --measurement-mode prod --tol 0)
  elif [ "$aoi" = "on" ]; then
    flags+=(--measurement-mode prod)
  fi
  [ "$aoi" = "on" ] && flags+=(--aoi-probe-out "$out/aoi_probe.jsonl")

  "$PY" -m tools.infra_monitor \
    --out "$out/infra.jsonl" --interval 0.1 --duration "$((DURATION + 10))" &
  local monitor_pid=$!
  local run_rc=0
  sudo -E "$PY" -m mininet.run_sync_v7 "${flags[@]}" || run_rc=$?
  wait "$monitor_pid" || true
  if [ "$run_rc" -ne 0 ]; then
    return "$run_rc"
  fi
  "$PY" -c 'import json,sys; json.dump({"complete": True}, open(sys.argv[1], "w")); open(sys.argv[1], "a").write("\n")' "$out/run_complete.json"
}

for rep in $(seq 1 "$REPS"); do
  run_cell A on  on  1  "$rep"
  run_cell B on  on  30 "$rep"
  run_cell C on  off 1  "$rep"
  run_cell D off off 30 "$rep"
  run_cell E off on  1  "$rep"
  run_cell F on  off 30 "$rep"
done

"$PY" -m tools.g1_static_nc \
  --campaign "$ROOT" \
  --sigma-grid 0.01,0.02,0.03,0.05,0.10 \
  --out "$CERT_OUT" \
  --detail-out "$DETAIL_OUT"

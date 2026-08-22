#!/usr/bin/env bash
# Phase 20R.6 -- RC7 session: re-measure branch A' with the probe IN-BAND.
#
# What this decides:
#   RC7 hypothesis  -> the residual disappears  -> the deficit was an artifact
#                      of injecting the probe from a separate host.
#   counting-artifact hypothesis -> the residual survives.
#
# poisson matters more than h2 here: h2's link-to-link spread is smaller than the
# standard error of a single link (no established differential), while poisson's
# is not. 8 seeds instead of 5 tightens the poisson per-link standard error.
#
# Safe to re-run: additivity_live checkpoints into --state and skips done points.
set -Eeuo pipefail

cd "$(dirname "$0")/.."
RUN_TAG="${RUN_TAG:-inband}"
SEEDS="${SEEDS:-101,102,103,104,105,106,107,108}"
MODES="${MODES:-poisson,h2}"
DUR="${DUR:-70}"

STATE="results/SUPERSEDED/phase-20R/additivity_branch_a_state_${RUN_TAG}.json"
BG_STATE="results/SUPERSEDED/phase-20R/additivity_branch_a_state_${RUN_TAG}_bg.json"
CHECK="results/SUPERSEDED/phase-20R/additivity_check_${RUN_TAG}_bg.json"
RAW="results/SUPERSEDED/phase-20R/raw_additivity_${RUN_TAG}"
mkdir -p logs "$RAW"

log_msg() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

run_logged() {
  local name="$1" log="$2"; shift 2
  log_msg "START $name  (log: $log)"
  if ! "$@" >>"$log" 2>&1; then
    log_msg "FAIL  $name -- xem $log"
    tail -30 "$log" || true
    exit 1
  fi
  log_msg "DONE  $name"
}

trap 'log_msg "ABORT o dong $LINENO"; exit 1' ERR

log_msg "RC7 in-band session. tag=$RUN_TAG modes=$MODES seeds=$SEEDS"
log_msg "Uoc luong: 2 mode x 3 link x 8 seed = 48 diem x ~83 s ~ 70 phut"

sudo -n true 2>/dev/null || { echo "can sudo khong mat khau (sudo -n)"; exit 1; }
sudo -n mn -c >/dev/null 2>&1 || true

run_logged "smoke topology" "logs/20r6_${RUN_TAG}_00_smoke.log" \
  sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -m measurements.additivity_live \
  --branch Aprime --smoke-topo

sudo -n mn -c >/dev/null 2>&1 || true

# The measurement itself. --probe-inband makes load_gen emit the probe from the
# same socket and the same schedule as the background, exactly like branch A.
run_logged "Aprime in-band" "logs/20r6_${RUN_TAG}_01_branch.log" \
  sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -m measurements.additivity_live \
  --branch Aprime --modes "$MODES" --rho-bar 0.925 --seeds "$SEEDS" \
  --duration "$DUR" --probe-inband \
  --raw-dir "$RAW" --state "$STATE"

sudo -n chown -R "$(id -un):$(id -gn)" "$RAW" "$STATE" 2>/dev/null || true

run_logged "rescore tu luong bg" "logs/20r6_${RUN_TAG}_02_rescore.log" \
  python3 -m measurements.additivity_rescore --state "$STATE" --out "$BG_STATE" --warmup 10

run_logged "additivity check" "logs/20r6_${RUN_TAG}_03_check.log" \
  python3 -m measurements.additivity_check --from-state "$BG_STATE" --out "$CHECK"

run_logged "c_a / late / probe injection" "logs/20r6_${RUN_TAG}_04_ca.log" \
  python3 -m measurements.diag_ca_late --aprime-raw "$RAW" \
  --out "results/SUPERSEDED/phase-20R/diag_ca_late_${RUN_TAG}.json"

log_msg "ALL DONE"
log_msg "  state : $STATE"
log_msg "  check : $CHECK"
log_msg "  c_a   : results/SUPERSEDED/phase-20R/diag_ca_late_${RUN_TAG}.json"
echo
echo "So sanh voi lan chay out-of-band:"
echo "  python3 -m measurements.g6_differential \\"
echo "    --diag-ca results/SUPERSEDED/phase-20R/diag_ca_late_${RUN_TAG}.json \\"
echo "    --check-report $CHECK \\"
echo "    --out results/SUPERSEDED/phase-20R/g6_differential_${RUN_TAG}.json"

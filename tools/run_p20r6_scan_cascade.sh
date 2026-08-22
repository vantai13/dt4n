#!/usr/bin/env bash
set -o pipefail

LOG="results/SUPERSEDED/phase-20R/tmux_logs/p20r6_scan_cascade.log"
mkdir -p "$(dirname "$LOG")"
: > "$LOG"

PYTHONUNBUFFERED=1 python3 -m measurements.band_v2 \
  --residual results/SUPERSEDED/phase-20R/residual_cascade.json \
  --mode scan --rho-bar 0.925 --seeds 101,102,103,104,105 --n 120000 \
  --variants common_mode \
  --out results/SUPERSEDED/phase-20R/breakdown_scan_cascade.json 2>&1 | tee "$LOG"

status=${PIPESTATUS[0]}
printf "[p20r6_scan_cascade] exit=%s done_utc=%s\n" \
  "$status" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
exit "$status"

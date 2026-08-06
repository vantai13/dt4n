#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$HOME/dt4n}"
cd "$ROOT"
export PYTHONPATH="$PWD"
mkdir -p logs results/phase-20R

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

log_msg() {
  printf '\n[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

run_logged() {
  local name="$1"
  local log="$2"
  shift 2
  log_msg "START ${name} | log=${log}"
  if [[ "$DRY_RUN" == "1" ]]; then
    printf 'DRY-RUN: %q ' "$@"
    printf '\n'
    return 0
  fi
  {
    printf '\n===== %s | %s =====\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$name"
    printf '+'
    printf ' %q' "$@"
    printf '\n'
  } | tee -a "$log"
  "$@" 2>&1 | tee -a "$log"
  log_msg "DONE  ${name}"
}

cleanup_mininet() {
  run_logged "cleanup-mininet" "logs/20r6_00_cleanup.log" sudo -n mn -c
}

check_sudo() {
  run_logged "sudo-check" "logs/20r6_00_sudo_check.log" sudo -n true
  run_logged "mininet-import-check" "logs/20r6_00_sudo_check.log" sudo -n env PYTHONPATH="$PWD" python3 -c "import mininet; print('mininet OK')"
}

require_additivity_branch_ok() {
  local branch="$1"
  local state="$2"
  log_msg "CHECK branch ${branch} state=${state}"
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  python3 - "$branch" "$state" <<'PY'
import json, sys
from measurements import additivity_live as AL

branch, state_path = sys.argv[1], sys.argv[2]
with open(state_path, "r", encoding="utf-8") as f:
    state = json.load(f)
plan = AL.build_plan(branch)
summary = AL.summarize_state(state, plan)
print(json.dumps(summary, indent=2, sort_keys=True))
bad = []
if not summary.get("coverage_pass"):
    bad.append("coverage incomplete: %s/%s" % (summary.get("n_done"), summary.get("n_plan")))
if not summary.get("fail_pass"):
    bad.append("gate failures: n_fail=%s" % summary.get("n_fail"))
if bad:
    raise SystemExit("BRANCH %s FAIL: %s" % (branch, "; ".join(bad)))
PY
}

require_aprime_transfer_ok() {
  log_msg "CHECK A-prime transfer vs truth table"
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  python3 - <<'PY'
import json
path = "results/phase-20R/additivity_check.json"
with open(path, "r", encoding="utf-8") as f:
    report = json.load(f)
summary = report.get("summary", {})
print(json.dumps(summary, indent=2, sort_keys=True))
if not summary.get("topology_transfer_evaluated"):
    raise SystemExit("A-prime transfer was not evaluated")
if not summary.get("topology_transfer_pass"):
    raise SystemExit("STOP: A-prime minus A exceeds equivalence gate")
if not summary.get("probe_intrusion_pass"):
    raise SystemExit("STOP: probe intrusion gate failed/missing for A-prime")
PY
}

require_additivity_final_ok() {
  log_msg "CHECK final additivity analysis"
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  python3 - <<'PY'
import json
path = "results/phase-20R/additivity_check.json"
with open(path, "r", encoding="utf-8") as f:
    report = json.load(f)
summary = report.get("summary", {})
print(json.dumps(summary, indent=2, sort_keys=True))
bad = []
for key in ("topology_transfer_pass", "g6_pass", "power_pass", "paired_schedule_pass", "probe_intrusion_pass"):
    if not summary.get(key):
        bad.append(key)
if bad:
    raise SystemExit("FINAL ADDITIVITY CHECK FAIL: " + ", ".join(bad))
PY
}

require_quasistatic_state_ok() {
  local state="results/phase-20R/quasistatic_state.json"
  log_msg "CHECK quasistatic state=${state}"
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  python3 - "$state" <<'PY'
import json, sys
state_path = sys.argv[1]
with open(state_path, "r", encoding="utf-8") as f:
    state = json.load(f)
done = sorted(set(int(x) for x in state.get("done_seeds", [])))
failed = state.get("failed_windows", [])
timeouts = state.get("timeout_history", [])
summary = {
    "done_seeds": done,
    "n_done_seeds": len(done),
    "n_failed_windows": len(failed),
    "n_timeouts": len(timeouts),
}
print(json.dumps(summary, indent=2, sort_keys=True))
if done != [101, 102, 103]:
    raise SystemExit("quasistatic incomplete")
if failed:
    raise SystemExit("quasistatic has failed windows")
if timeouts:
    raise SystemExit("quasistatic has timeout history")
PY
}

require_quasistatic_analysis_ok() {
  log_msg "CHECK quasistatic analysis"
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  python3 - <<'PY'
import json
path = "results/phase-20R/quasistatic_check.json"
with open(path, "r", encoding="utf-8") as f:
    report = json.load(f)
summary = report.get("summary", {})
print(json.dumps(summary, indent=2, sort_keys=True))
if not summary.get("evaluated"):
    raise SystemExit("quasistatic analysis not evaluated")
if not summary.get("pass"):
    raise SystemExit("quasistatic analysis failed")
PY
}

log_msg "Phase 20R.6 one-button run starting in $PWD"
log_msg "Estimated wall time: smoke ~1m, A' ~42m, B ~42m, C ~28m, quasistatic ~37m, total ~2.5h"

check_sudo
cleanup_mininet

run_logged "B1 smoke topology" "logs/20r6_00_smoke_topo.log" \
  sudo -n env PYTHONPATH="$PWD" python3 -m measurements.additivity_live --smoke-topo

cleanup_mininet
run_logged "B2 branch Aprime" "logs/20r6_01_branch_a.log" \
  sudo -n env PYTHONPATH="$PWD" python3 -m measurements.additivity_live \
  --branch Aprime --modes poisson,h2 --rho-bar 0.925 \
  --seeds 101,102,103,104,105 \
  --state results/phase-20R/additivity_branch_a_state.json
require_additivity_branch_ok "Aprime" "results/phase-20R/additivity_branch_a_state.json"

run_logged "B2 check Aprime vs truth table" "logs/20r6_01_compare_a.log" \
  python3 -m measurements.additivity_check --compare-a-vs-truthtable
require_aprime_transfer_ok

cleanup_mininet
run_logged "B3 branch B" "logs/20r6_02_branch_b.log" \
  sudo -n env PYTHONPATH="$PWD" python3 -m measurements.additivity_live \
  --branch B --modes poisson,h2 --rho-bar 0.925 \
  --seeds 101,102,103,104,105 \
  --state results/phase-20R/additivity_branch_b_state.json
require_additivity_branch_ok "B" "results/phase-20R/additivity_branch_b_state.json"

cleanup_mininet
run_logged "B4 branch C" "logs/20r6_03_branch_c.log" \
  sudo -n env PYTHONPATH="$PWD" python3 -m measurements.additivity_live \
  --branch C --modes poisson,h2 --rho-bar 0.85,0.925 \
  --seeds 101,102,103,104,105 \
  --state results/phase-20R/additivity_branch_c_state.json
require_additivity_branch_ok "C" "results/phase-20R/additivity_branch_c_state.json"

cleanup_mininet
run_logged "B5 quasistatic live" "logs/20r6_04_quasistatic.log" \
  sudo -n env PYTHONPATH="$PWD" python3 -m measurements.quasistatic_check \
  --live --duration 600 --tau 1.0 --rho-bar 0.925 --mode poisson \
  --seeds 101,102,103 \
  --state results/phase-20R/quasistatic_state.json
require_quasistatic_state_ok

run_logged "B6 additivity analyze" "logs/20r6_05_additivity_analyze.log" \
  python3 -m measurements.additivity_check --analyze
require_additivity_final_ok

run_logged "B6 quasistatic analyze" "logs/20r6_06_quasistatic_analyze.log" \
  python3 -m measurements.quasistatic_check --analyze
require_quasistatic_analysis_ok

cleanup_mininet
log_msg "ALL DONE. Outputs:"
printf '  %s\n' \
  "results/phase-20R/additivity_check.json" \
  "results/phase-20R/quasistatic_check.json" \
  "logs/20r6_05_additivity_analyze.log" \
  "logs/20r6_06_quasistatic_analyze.log"

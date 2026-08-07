#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="${ROOT:-$HOME/dt4n}"
cd "$ROOT"
export PYTHONPATH="$PWD"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
mkdir -p logs results/phase-20R

RUN_TAG="${RUN_TAG:-budgetfix}"
SMOKE_REPS="${SMOKE_REPS:-5}"
RAW_ADD="results/phase-20R/raw_additivity_${RUN_TAG}"
APRIME_STATE="results/phase-20R/additivity_branch_a_state_${RUN_TAG}.json"
APRIME_BG_STATE="results/phase-20R/additivity_branch_a_state_${RUN_TAG}_bg.json"
B_STATE="results/phase-20R/additivity_branch_b_state_${RUN_TAG}.json"
B_BG_STATE="results/phase-20R/additivity_branch_b_state_${RUN_TAG}_bg.json"
C_STATE="results/phase-20R/additivity_branch_c_state_${RUN_TAG}.json"
ADD_CHECK="results/phase-20R/additivity_check_${RUN_TAG}.json"

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

run_smoke_topo() {
  for i in $(seq 1 "$SMOKE_REPS"); do
    if run_logged "B1 smoke topology ${i}/${SMOKE_REPS}" "logs/20r6_00_smoke_topo.log" \
      sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -m measurements.additivity_live --smoke-topo; then
      cleanup_mininet
      continue
    fi
    log_msg "Smoke ${i}/${SMOKE_REPS} failed once; cleanup and retry once before stopping"
    cleanup_mininet
    run_logged "B1 smoke topology retry ${i}/${SMOKE_REPS}" "logs/20r6_00_smoke_topo.log" \
      sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -m measurements.additivity_live --smoke-topo
    cleanup_mininet
  done
}

check_sudo() {
  run_logged "sudo-check" "logs/20r6_00_sudo_check.log" sudo -n true
  run_logged "mininet-import-check" "logs/20r6_00_sudo_check.log" sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -c "import mininet; print('mininet OK')"
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
  python3 - "$ADD_CHECK" <<'PY'
import json
import sys
path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    report = json.load(f)
summary = report.get("summary", {})
print(json.dumps(summary, indent=2, sort_keys=True))
if not summary.get("topology_transfer_path_evaluated"):
    raise SystemExit("A-prime path-level transfer was not evaluated")

# The pre-registered G6 margin is defined on the PATH cost, so the path contrast
# is the gate and the per-link contrast is printed as a diagnostic only. An
# INCONCLUSIVE path verdict is a power result, not evidence of bias: it is
# reported loudly but must not be recorded as FAIL and must not silently pass.
verdict = summary.get("topology_transfer_path_verdict")
for row in report.get("checks", []):
    if row.get("contrast") in ("Aprime_minus_A_path", "Aprime_minus_A"):
        print("  %-22s %-8s %-3s mean=%+9.3f CI90=[%+9.3f,%+9.3f] delta=%8.3f -> %s"
              % (row["contrast"], row.get("mode"), row.get("link") or "ALL",
                 row.get("mean_ms", float("nan")), row.get("ci90_lo_ms", float("nan")),
                 row.get("ci90_hi_ms", float("nan")), row.get("delta_ms", float("nan")),
                 row.get("verdict")))
if verdict == "FAIL":
    raise SystemExit("STOP: A-prime minus A path cost is non-equivalent (bias established)")
if verdict != "PASS":
    print("WARN: A-prime path transfer is %s -- underpowered, not a detected bias. "
          "Branches B/C continue; the transfer claim stays INCONCLUSIVE with its CI." % verdict)
if not summary.get("probe_intrusion_pass"):
    raise SystemExit("STOP: probe intrusion gate failed/missing for A-prime")
PY
}

require_additivity_final_ok() {
  log_msg "CHECK final additivity analysis"
  if [[ "$DRY_RUN" == "1" ]]; then
    return 0
  fi
  python3 - "$ADD_CHECK" <<'PY'
import json
import sys
path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    report = json.load(f)
summary = report.get("summary", {})
print(json.dumps(summary, indent=2, sort_keys=True))

# Validity gates are binary: a broken measurement is always a hard stop.
bad = [key for key in ("paired_schedule_pass", "probe_intrusion_pass") if not summary.get(key)]

# Scientific gates are three-way. FAIL means a bias was established and stops the
# run; INCONCLUSIVE means the CI is wider than delta and is reported as such --
# it is never rewritten into PASS, and never into FAIL either.
unresolved = []
for key in ("topology_transfer_path_verdict", "g6_verdict"):
    verdict = summary.get(key)
    if verdict == "FAIL":
        bad.append("%s=FAIL" % key)
    elif verdict is not None and verdict != "PASS":
        unresolved.append("%s=%s" % (key, verdict))
    elif verdict is None:
        unresolved.append("%s=NOT_EVALUATED" % key)
if unresolved:
    print("UNRESOLVED (underpowered, report CI -- do NOT widen delta): " + ", ".join(unresolved))
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
log_msg "Estimated wall time: smoke x${SMOKE_REPS} ~1m, A' ~42m, B ~42m, C ~28m, quasistatic ~37m, total ~2.5h"
log_msg "Run tag=${RUN_TAG}; additivity state/report files use this suffix to avoid stale pre-budgetfix data"

check_sudo
cleanup_mininet

run_smoke_topo

cleanup_mininet
run_logged "B2 branch Aprime" "logs/20r6_01_branch_a.log" \
  sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -m measurements.additivity_live \
  --branch Aprime --modes poisson,h2 --rho-bar 0.925 \
  --seeds 101,102,103,104,105 \
  --raw-dir "$RAW_ADD" \
  --state "$APRIME_STATE"
require_additivity_branch_ok "Aprime" "$APRIME_STATE"

run_logged "B2 rescore Aprime from bg stream" "logs/20r6_01_rescore_a.log" \
  python3 -m measurements.additivity_rescore \
  --state "$APRIME_STATE" \
  --out "$APRIME_BG_STATE"

run_logged "B2 check Aprime-bg vs truth table" "logs/20r6_01_compare_a.log" \
  python3 -m measurements.additivity_check \
  --from-state "$APRIME_BG_STATE" \
  --out "$ADD_CHECK"
require_aprime_transfer_ok

cleanup_mininet
run_logged "B3 branch B" "logs/20r6_02_branch_b.log" \
  sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -m measurements.additivity_live \
  --branch B --modes poisson,h2 --rho-bar 0.925 \
  --seeds 101,102,103,104,105 \
  --raw-dir "$RAW_ADD" \
  --state "$B_STATE"
require_additivity_branch_ok "B" "$B_STATE"
run_logged "B3 rescore B from bg stream" "logs/20r6_02_rescore_b.log" \
  python3 -m measurements.additivity_rescore \
  --state "$B_STATE" \
  --out "$B_BG_STATE"

cleanup_mininet
run_logged "B4 branch C" "logs/20r6_03_branch_c.log" \
  sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -m measurements.additivity_live \
  --branch C --modes poisson,h2 --rho-bar 0.85,0.925 \
  --seeds 101,102,103,104,105 \
  --raw-dir "$RAW_ADD" \
  --state "$C_STATE"
require_additivity_branch_ok "C" "$C_STATE"

cleanup_mininet
run_logged "B5 quasistatic live" "logs/20r6_04_quasistatic.log" \
  sudo -n env PYTHONPATH="$PWD" PYTHONUNBUFFERED=1 python3 -m measurements.quasistatic_check \
  --live --duration 600 --tau 1.0 --rho-bar 0.925 --mode poisson \
  --seeds 101,102,103 \
  --state results/phase-20R/quasistatic_state.json
require_quasistatic_state_ok

run_logged "B6 additivity analyze" "logs/20r6_05_additivity_analyze.log" \
  python3 -m measurements.additivity_check \
  --from-state "$APRIME_BG_STATE,$B_BG_STATE,$C_STATE" \
  --out "$ADD_CHECK"
require_additivity_final_ok

run_logged "B6 quasistatic analyze" "logs/20r6_06_quasistatic_analyze.log" \
  python3 -m measurements.quasistatic_check --analyze
require_quasistatic_analysis_ok

cleanup_mininet
log_msg "ALL DONE. Outputs:"
printf '  %s\n' \
  "$ADD_CHECK" \
  "results/phase-20R/quasistatic_check.json" \
  "logs/20r6_05_additivity_analyze.log" \
  "logs/20r6_06_quasistatic_analyze.log"

# Phase 20 Full n=5 Rerun

This reruns the full Phase 20 pipeline with five independent Mininet traffic
seeds. It writes the canonical `results/phase-20/*` outputs and will overwrite
existing Phase 20 rerun artifacts.

Expected wall time: roughly 3-4 hours.

Run from anywhere:

```bash
cd /home/ubuntu/dt4n
export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
```

## Start Full Rerun

```bash
tmux new -d -s p20full5
tmux send-keys -t p20full5 'cd /home/ubuntu/dt4n && ./tools/phase20_full5_rerun.sh 2>&1 | tee logs/phase20_full5_rerun.log' C-m
```

Attach:

```bash
tmux attach -t p20full5
```

Detach without stopping:

```text
Ctrl-b d
```

Check whether it is still running:

```bash
tmux has-session -t p20full5 && echo "dang chay" || echo "da xong"
```

## Watch Logs

Full log:

```bash
tail -f logs/phase20_full5_rerun.log
```

Long Mininet trace logs:

```bash
tail -f logs/phase20_full5_04_trace_s0.log
tail -f logs/phase20_full5_04_trace_s1.log
tail -f logs/phase20_full5_04_trace_s2.log
tail -f logs/phase20_full5_04_trace_s3.log
tail -f logs/phase20_full5_04_trace_s4.log
```

Decision-error logs:

```bash
tail -f logs/phase20_full5_07_decision_error_trace_s4.log
tail -f logs/phase20_full5_08_decision_error_measured_fixed_s4.log
```

Diagnostic logs:

```bash
tail -f logs/phase20_full5_07_core_load_diagnostic.log
tail -f logs/phase20_full5_07_block_crossing_diagnostic.log
tail -f logs/phase20_full5_08_measured_crosscheck_diagnostic.log
```

## Show Final Results

```bash
python - <<'PY'
import json

for path in [
    "results/phase-20/between_trace_summary_n5.json",
    "results/phase-20/decision_error_measured_fixed_replicates_summary.json",
]:
    with open(path) as f:
        d = json.load(f)
    print(f"\n=== {path} ===")
    print("n_traces:", d["n_traces"])
    for metric in ["err", "d_sla"]:
        x = d[metric]
        ci = x["ci95_mean_t"]
        print(
            f"{metric}: mean={x['point_mean']:.5f}, "
            f"SD_between={x['between_trace_sd']:.5f}, "
            f"SE_mean={x['se_mean']:.5f}, "
            f"CI_t=[{ci['lo']:.5f}, {ci['hi']:.5f}]"
        )
        if metric == "d_sla":
            sd_ci = x["sd_between_ci95_chi_square"]
            print(f"  SD_between_CI95=[{sd_ci['lo']:.5f}, {sd_ci['hi']:.5f}]")
    print("gates:", d["gates"])

with open("results/phase-20/core_load_diagnostic_n5.json") as f:
    diag = json.load(f)
print("\n=== core-load diagnostic ===")
print("rho_core_after_warmup:", [round(x, 5) for x in diag["rho_core_mean_after_warmup"]])
for key in ["corr_warm_core_mean_vs_err", "corr_warm_core_mean_vs_d_sla"]:
    ci = diag[f"{key}_ci95"]
    print(f"{key}: r={diag[key]:.3f}, CI95=[{ci['lo']:.3f}, {ci['hi']:.3f}]")
print("diagnosis:", diag["diagnosis"])

with open("results/phase-20/block_crossing_diagnostic_n5.json") as f:
    block = json.load(f)
print("\n=== block crossing diagnostic ===")
print("n_blocks:", block["n_blocks"])
for key, row in block["correlations"].items():
    ci = row["ci95"]
    print(f"{key}: r={row['r']:.3f}, CI95=[{ci['lo']:.3f}, {ci['hi']:.3f}]")

with open("results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json") as f:
    m = json.load(f)
print("\n=== measured cross-check diagnostic ===")
for metric in ["err", "d_sla"]:
    row = m["paired_offered_minus_measured"][metric]
    vals = ", ".join(f"{x:.4f}" for x in row["values"])
    print(f"offered - measured {metric}: [{vals}], t={row['t_stat']:.2f}, df={row['df']}")
mech = m["mechanism_comparison"]
off = mech["offered"]
mf = mech["measured_fixed"]
rr = mech["paired_measured_minus_offered"]["risk_ratio"]
print(f"risk ratio offered={off['risk_ratio_mean']:.2f}, measured_fixed={mf['risk_ratio_mean']:.2f}")
print(f"risk ratio measured-offered: mean={rr['mean']:.2f}, t={rr['t_stat']:.2f}, df={rr['df']} (p ~= 0.65)")
print("measured gates:", m["measured_summary"]["gates"])
for row in m["measured_run_diagnostics"]:
    print(f"s{row['trace_id']}: mean_age={row['mean_age_s']:.3f}, false={row['false_bool_gates']}")
PY
```

## Main Outputs

```text
results/phase-20/decision_error_offered.json
results/phase-20/decision_error_trace_s0.json
results/phase-20/decision_error_trace_s1.json
results/phase-20/decision_error_trace_s2.json
results/phase-20/decision_error_trace_s3.json
results/phase-20/decision_error_trace_s4.json
results/phase-20/between_trace_summary_n5.json
results/phase-20/core_load_diagnostic_n5.json
results/phase-20/block_crossing_diagnostic_n5.json
results/phase-20/decision_error_measured_fixed_trace_s0.json
results/phase-20/decision_error_measured_fixed_trace_s1.json
results/phase-20/decision_error_measured_fixed_trace_s2.json
results/phase-20/decision_error_measured_fixed_trace_s3.json
results/phase-20/decision_error_measured_fixed_trace_s4.json
results/phase-20/decision_error_measured_fixed_replicates_summary.json
results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json
```

## Stop

```bash
tmux send-keys -t p20full5 C-c
sudo mn -c
sudo pkill -f 'mininet.flow_engine' || true
```

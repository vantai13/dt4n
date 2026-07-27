# Phase 20 Appendix/Audit Once

Script nay chay mot lan toan bo phan hau kiem khong can Mininet:

```text
L7 core-load diagnostic
L7 block-crossing diagnostic
L8 measured fixed cross-check
offered n=5 reproducibility audit
compact final report
```

Dieu kien: cac raw trace da co san local:

```text
results/phase-20/rho_offered_long.csv
results/phase-20/rho_offered_long_s1.csv
results/phase-20/rho_offered_long_s2.csv
results/phase-20/rho_offered_long_s3.csv
results/phase-20/rho_offered_long_s4.csv
results/phase-20/rho_measured_long.csv
results/phase-20/rho_measured_long_s1.csv
results/phase-20/rho_measured_long_s2.csv
results/phase-20/rho_measured_long_s3.csv
results/phase-20/rho_measured_long_s4.csv
```

## Start

```bash
cd /home/ubuntu/dt4n
export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"

tmux new -d -s p20appendix
tmux send-keys -t p20appendix 'cd /home/ubuntu/dt4n && ./tools/phase20_appendix_once.sh 2>&1 | tee logs/phase20_appendix_once.log' C-m
```

## Watch

```bash
tail -f logs/phase20_appendix_once.log
```

Attach:

```bash
tmux attach -t p20appendix
```

Detach without stopping:

```text
Ctrl-b d
```

Check done:

```bash
tmux has-session -t p20appendix && echo "dang chay" || echo "da xong"
```

## Show Results Again

```bash
python - <<'PY'
import json

def metric_line(name, row):
    ci = row["ci95_mean_t"]
    return f"{name}: mean={row['point_mean']:.5f}, CI95=[{ci['lo']:.5f}, {ci['hi']:.5f}]"

offered = json.load(open("results/phase-20/between_trace_summary_n5.json"))
measured = json.load(open("results/phase-20/decision_error_measured_fixed_replicates_summary.json"))
block = json.load(open("results/phase-20/block_crossing_diagnostic_n5.json"))
paired = json.load(open("results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json"))

print("\n=== offered n=5 ===")
print(metric_line("err", offered["err"]))
print(metric_line("d_sla", offered["d_sla"]))

print("\n=== measured fixed n=5 ===")
print(metric_line("err", measured["err"]))
print(metric_line("d_sla", measured["d_sla"]))
print(
    "ratios measured/offered: "
    f"err={measured['err']['point_mean'] / offered['err']['point_mean']:.3f}, "
    f"d_sla={measured['d_sla']['point_mean'] / offered['d_sla']['point_mean']:.3f}"
)
print(
    "d_sla lower/0.03: "
    f"offered={offered['d_sla']['ci95_mean_t']['lo'] / 0.03:.2f}x, "
    f"measured_fixed={measured['d_sla']['ci95_mean_t']['lo'] / 0.03:.2f}x"
)

print("\n=== L7 block crossing ===")
for key, row in block["correlations"].items():
    ci = row["ci95"]
    print(f"{key}: r={row['r']:.3f}, CI95=[{ci['lo']:.3f}, {ci['hi']:.3f}]")

print("\n=== offered - measured_fixed ===")
for metric in ["err", "d_sla"]:
    row = paired["paired_offered_minus_measured"][metric]
    vals = ", ".join(f"{x:.4f}" for x in row["values"])
    print(f"{metric}: [{vals}], t={row['t_stat']:.2f}, df={row['df']}")
print("two-sided sign-test p for 5/5 same sign: 0.0625")

print("\n=== mechanism risk ratio ===")
mech = paired["mechanism_comparison"]
off = mech["offered"]
mf = mech["measured_fixed"]
rr = mech["paired_measured_minus_offered"]["risk_ratio"]
print(f"offered: mean={off['risk_ratio_mean']:.2f}, SD={off['risk_ratio_sd']:.2f}")
print(f"measured_fixed: mean={mf['risk_ratio_mean']:.2f}, SD={mf['risk_ratio_sd']:.2f}")
print(f"measured-offered: mean={rr['mean']:.2f}, t={rr['t_stat']:.2f}, df={rr['df']} (p ~= 0.65)")
print(
    "P(error|not crossed): "
    f"offered={off['p_error_given_not_crossed_mean']:.4f}, "
    f"measured_fixed={mf['p_error_given_not_crossed_mean']:.4f}"
)

print("\n=== measured fixed gates ===")
for row in paired["measured_run_diagnostics"]:
    print(
        f"s{row['trace_id']}: mean_age={row['mean_age_s']:.3f}, "
        f"pass_without_G6={row['pass_without_G6']}, false={row['false_bool_gates']}"
    )

print("\nAudit status:", open("/tmp/p20_audit/audit_status.txt", encoding="utf-8").read().strip())
PY
```

## Outputs

```text
results/phase-20/core_load_diagnostic_n5.json
results/phase-20/block_crossing_diagnostic_n5.json
results/phase-20/decision_error_measured_fixed_trace_s0.json
results/phase-20/decision_error_measured_fixed_trace_s1.json
results/phase-20/decision_error_measured_fixed_trace_s2.json
results/phase-20/decision_error_measured_fixed_trace_s3.json
results/phase-20/decision_error_measured_fixed_trace_s4.json
results/phase-20/decision_error_measured_fixed_replicates_summary.json
results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json
/tmp/p20_audit/s0.json
/tmp/p20_audit/s1.json
/tmp/p20_audit/s2.json
/tmp/p20_audit/s3.json
/tmp/p20_audit/s4.json
/tmp/p20_audit/audit_status.txt
```

## Stop

```bash
tmux send-keys -t p20appendix C-c
```

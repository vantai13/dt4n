# Phase 20 Traffic V7 Tmux Runbook

Run from repo root:

```bash
cd /home/ubuntu/dt4n
export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
set -o pipefail
```

For a single full rerun command covering smoke, quick check, resolution checks,
five long traces, offered decision error, L7 diagnostics, and measured telemetry
cross-check, use:

```bash
less runbooks/phase-20-full5-rerun.md
```

## 0. Smoke Test

```bash
./tools/phase20_smoke.sh
```

Smoke only checks plumbing. It is too short for final tau/stationarity.

## 1. Quick Check C1-C3, 60 Seconds

```bash
sudo mn -c
sudo "$PYTHON_BIN" -m mininet.run_sync_v7 \
  --traffic v7 \
  --duration 60 \
  --log-dt 0.010 \
  --measured-window 0.200 \
  --core-sigma 0.10 \
  --edge-sigma 0.03 \
  --seed 0 \
  --quick-check \
  --offered-out results/phase-20/rho_offered_quick.csv \
  --measured-out results/phase-20/rho_measured_quick.csv \
  --meta-out results/phase-20/rho_trace_quick_meta.json \
  --flow-log-dir results/phase-20/flow_logs_quick \
  2>&1 | tee logs/phase20_tau_quick.log
```

If quick-check prints `MISS`, do not run decision error. Fix traffic first.

## 2. Resolution Check Run In Tmux, 10 ms

```bash
tmux new -d -s p20tau10
tmux send-keys -t p20tau10 'cd /home/ubuntu/dt4n && export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}" && sudo mn -c && sudo "$PYTHON_BIN" -m mininet.run_sync_v7 --traffic v7 --duration 300 --log-dt 0.010 --measured-window 0.200 --core-sigma 0.10 --edge-sigma 0.03 --seed 0 --offered-out results/phase-20/rho_offered_10ms.csv --measured-out results/phase-20/rho_measured_10ms.csv --meta-out results/phase-20/rho_trace_10ms_meta.json --flow-log-dir results/phase-20/flow_logs_10ms 2>&1 | tee logs/phase20_tau_10ms_run.log' C-m
```

Watch or detach:

```bash
tmux attach -t p20tau10
```

Detach without stopping:

```text
Ctrl-b d
```

## 3. Resolution Check Run In Tmux, 2 ms

Run after the 10 ms run finishes:

```bash
tmux new -d -s p20tau2
tmux send-keys -t p20tau2 'cd /home/ubuntu/dt4n && export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}" && sudo mn -c && sudo "$PYTHON_BIN" -m mininet.run_sync_v7 --traffic v7 --duration 300 --log-dt 0.002 --measured-window 0.200 --core-sigma 0.10 --edge-sigma 0.03 --seed 0 --offered-out results/phase-20/rho_offered_2ms.csv --measured-out results/phase-20/rho_measured_2ms.csv --meta-out results/phase-20/rho_trace_2ms_meta.json --flow-log-dir results/phase-20/flow_logs_2ms 2>&1 | tee logs/phase20_tau_2ms_run.log' C-m
```

## 4. Required Long Run Before Lesson 20.2, 1800 Seconds

Run after the resolution checks. Do not change the traffic config; only make
the trace longer so edge links have enough correlation cycles.

```bash
tmux new -d -s p20tau1800
tmux send-keys -t p20tau1800 'cd /home/ubuntu/dt4n && export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}" && sudo mn -c && sudo "$PYTHON_BIN" -m mininet.run_sync_v7 --traffic v7 --duration 1800 --log-dt 0.010 --measured-window 0.200 --core-sigma 0.10 --edge-sigma 0.03 --seed 0 --offered-out results/phase-20/rho_offered_long.csv --measured-out results/phase-20/rho_measured_long.csv --meta-out results/phase-20/rho_trace_long_meta.json --flow-log-dir results/phase-20/flow_logs_long 2>&1 | tee logs/phase20_tau_long_run.log' C-m
```

Watch or detach:

```bash
tmux attach -t p20tau1800
```

Detach without stopping:

```text
Ctrl-b d
```

## 5. Analyze

```bash
$PYTHON_BIN -m measurements.measure_tau \
  --input results/phase-20/rho_offered_10ms.csv \
  --core-sigma-target 0.10 \
  --edge-sigma-target 0.03 \
  --acf-windows 6,60 \
  --out results/phase-20/tau_summary_10ms.json \
  2>&1 | tee logs/phase20_tau_10ms_analyze.log

$PYTHON_BIN -m measurements.measure_tau \
  --input results/phase-20/rho_offered_2ms.csv \
  --core-sigma-target 0.10 \
  --edge-sigma-target 0.03 \
  --acf-windows 6,60 \
  --out results/phase-20/tau_summary_2ms.json \
  2>&1 | tee logs/phase20_tau_2ms_analyze.log

$PYTHON_BIN -m measurements.measure_tau \
  --input results/phase-20/rho_offered_long.csv \
  --core-sigma-target 0.10 \
  --edge-sigma-target 0.03 \
  --acf-windows 6,60 \
  --out results/phase-20/tau_summary_long.json \
  2>&1 | tee logs/phase20_tau_long_analyze.log

$PYTHON_BIN -m measurements.compare_estimators \
  --offered results/phase-20/rho_offered_10ms.csv \
  --measured results/phase-20/rho_measured_10ms.csv \
  --out results/phase-20/estimator_compare_10ms.json \
  2>&1 | tee logs/phase20_tau_10ms_compare.log

$PYTHON_BIN -m measurements.compare_estimators \
  --offered results/phase-20/rho_offered_long.csv \
  --measured results/phase-20/rho_measured_long.csv \
  --out results/phase-20/estimator_compare_long.json \
  2>&1 | tee logs/phase20_tau_long_compare.log
```

Tau from 10 ms and 2 ms should agree. If tau tracks dt, it is still on the
resolution floor.

The long-run summary must include `correlation_cycles` and `decay_fits` for
both `6s` and `60s` windows.

## 6. Decision Error, Offered Trace

Run the internal controls first:

```bash
$PYTHON_BIN -m measurements.decision_error \
  --trace results/phase-20/rho_offered_long.csv \
  --dt 0.010 \
  --tau-core 2.87 \
  --sync-period 0.5 \
  --d-sync 0.051 \
  --z-list 0,0.05,0.10,0.20,0.298,0.50,1.0,2.0,4.0 \
  --seeds 100 \
  --nc-only \
  --out results/phase-20/decision_error_offered_nc.json \
  2>&1 | tee logs/phase20_decision_error_nc.log
```

Only run the full measurement if NC1-NC4 pass:

```bash
$PYTHON_BIN -m measurements.decision_error \
  --trace results/phase-20/rho_offered_long.csv \
  --dt 0.010 \
  --tau-core 2.87 \
  --sync-period 0.5 \
  --d-sync 0.051 \
  --z-list 0,0.05,0.10,0.20,0.298,0.50,1.0,2.0,4.0 \
  --seeds 100,101,102 \
  --n-boot 2000 \
  --out results/phase-20/decision_error_offered.json \
  2>&1 | tee logs/phase20_decision_error_offered.log
```

## 7. Lesson 20.3 Between-Run Replicates

This is the long part. It runs two new 1800 s Mininet traces, changing only the
traffic seed. Keep the original seed-0 files as the first replicate:

```text
seed 0 -> results/phase-20/rho_offered_long.csv
seed 1 -> results/phase-20/rho_offered_long_s1.csv
seed 2 -> results/phase-20/rho_offered_long_s2.csv
```

Start the two long runs in one tmux session:

```bash
tmux new -d -s p20rep12
tmux send-keys -t p20rep12 'cd /home/ubuntu/dt4n && export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}" && mkdir -p logs results/phase-20 && set -o pipefail && for S in 1 2; do sudo mn -c; sudo "$PYTHON_BIN" -m mininet.run_sync_v7 --traffic v7 --duration 1800 --log-dt 0.010 --measured-window 0.200 --core-sigma 0.10 --edge-sigma 0.03 --seed "$S" --offered-out "results/phase-20/rho_offered_long_s${S}.csv" --measured-out "results/phase-20/rho_measured_long_s${S}.csv" --meta-out "results/phase-20/rho_trace_long_s${S}_meta.json" --flow-log-dir "results/phase-20/flow_logs_long_s${S}" 2>&1 | tee "logs/phase20_trace_s${S}.log"; done; sudo mn -c' C-m
```

Watch it:

```bash
tmux attach -t p20rep12
```

Detach without stopping:

```text
Ctrl-b d
```

Check whether it finished:

```bash
tmux has-session -t p20rep12
tail -n 40 logs/phase20_trace_s1.log
tail -n 40 logs/phase20_trace_s2.log
ls -lh results/phase-20/rho_offered_long_s1.csv results/phase-20/rho_offered_long_s2.csv
```

After both traces exist, run decision error with the calibration frozen from the
original offered trace. Do not recalibrate per trace.

```bash
$PYTHON_BIN -m measurements.decision_error \
  --trace results/phase-20/rho_offered_long.csv \
  --dt 0.010 \
  --tau-core 2.87 \
  --sync-period 0.5 \
  --d-sync 0.051 \
  --z-list 0,0.05,0.10,0.20,0.298,0.50,1.0,2.0,4.0 \
  --freeze-calibration results/phase-20/decision_error_offered.json \
  --seeds 100 \
  --n-boot 2000 \
  --out results/phase-20/decision_error_trace_s0.json \
  2>&1 | tee logs/phase20_decision_error_trace_s0.log

for S in 1 2; do
  $PYTHON_BIN -m measurements.decision_error \
    --trace "results/phase-20/rho_offered_long_s${S}.csv" \
    --dt 0.010 \
    --tau-core 2.87 \
    --sync-period 0.5 \
    --d-sync 0.051 \
    --z-list 0,0.05,0.10,0.20,0.298,0.50,1.0,2.0,4.0 \
    --freeze-calibration results/phase-20/decision_error_offered.json \
    --seeds 100 \
    --n-boot 2000 \
    --out "results/phase-20/decision_error_trace_s${S}.json" \
    2>&1 | tee "logs/phase20_decision_error_trace_s${S}.log"
done
```

Summarize the three replicates:

```bash
$PYTHON_BIN -m measurements.summarize_decision_error_replicates \
  --inputs results/phase-20/decision_error_trace_s0.json,results/phase-20/decision_error_trace_s1.json,results/phase-20/decision_error_trace_s2.json \
  --run-seed 100 \
  --out results/phase-20/decision_error_replicates_summary.json
```

Report these fields:

```text
results/phase-20/decision_error_replicates_summary.json
  traces[*].err
  traces[*].d_sla
  d_sla.between_trace_sd
  d_sla.se_single_measurement
  d_sla.se_mean
  d_sla.ci95_mean_t.lo
  d_sla.sd_between_ci95_chi_square
  gates.G2_d_sla_mean_t_lower_ge_003
```

## 8. Optional n=5 Replicate Tightening

Gate 20 passes at `n=3`, but the chi-square CI of the between-trace SD is wide.
Run seeds 3/4 only if you want to tighten that limitation.

```bash
tmux new -d -s p20rep34
tmux send-keys -t p20rep34 'cd /home/ubuntu/dt4n && export PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}" && mkdir -p logs results/phase-20 && set -o pipefail && for S in 3 4; do sudo mn -c; sudo "$PYTHON_BIN" -m mininet.run_sync_v7 --traffic v7 --duration 1800 --log-dt 0.010 --measured-window 0.200 --core-sigma 0.10 --edge-sigma 0.03 --seed "$S" --offered-out "results/phase-20/rho_offered_long_s${S}.csv" --measured-out "results/phase-20/rho_measured_long_s${S}.csv" --meta-out "results/phase-20/rho_trace_long_s${S}_meta.json" --flow-log-dir "results/phase-20/flow_logs_long_s${S}" 2>&1 | tee "logs/phase20_trace_s${S}.log"; done; sudo mn -c; for S in 3 4; do "$PYTHON_BIN" -m measurements.decision_error --trace "results/phase-20/rho_offered_long_s${S}.csv" --dt 0.010 --tau-core 2.87 --sync-period 0.5 --d-sync 0.051 --z-list 0,0.05,0.10,0.20,0.298,0.50,1.0,2.0,4.0 --freeze-calibration results/phase-20/decision_error_offered.json --seeds 100 --n-boot 2000 --out "results/phase-20/decision_error_trace_s${S}.json" 2>&1 | tee "logs/phase20_decision_error_trace_s${S}.log"; done; "$PYTHON_BIN" -m measurements.summarize_decision_error_replicates --inputs results/phase-20/decision_error_trace_s0.json,results/phase-20/decision_error_trace_s1.json,results/phase-20/decision_error_trace_s2.json,results/phase-20/decision_error_trace_s3.json,results/phase-20/decision_error_trace_s4.json --run-seed 100 --out results/phase-20/between_trace_summary_n5.json' C-m
```

Watch it:

```bash
tmux attach -t p20rep34
```

After it finishes, the n=5 summary is:

```text
results/phase-20/between_trace_summary_n5.json
```

The offered CSVs are long-format files with `link,rho` columns, not wide files
with one column per link. Use this diagnostic, not `df[["ac", ...]]`:

```bash
python -m measurements.phase20_core_load_diagnostic \
  --traces results/phase-20/rho_offered_long.csv,results/phase-20/rho_offered_long_s1.csv,results/phase-20/rho_offered_long_s2.csv,results/phase-20/rho_offered_long_s3.csv,results/phase-20/rho_offered_long_s4.csv \
  --summary results/phase-20/between_trace_summary_n5.json \
  --out results/phase-20/core_load_diagnostic_n5.json
```

## 9. Lesson 20.3 Measured-Telemetry Cross-Check

This is not the between-run replicate gate. It checks the same decision-error
meter on measured telemetry rather than offered load. Measured telemetry has a
200 ms trace grid, so do not use the 10 ms z-list or sawtooth operational mode
here; that aliases multiple z values onto the same integer lag.

```bash
$PYTHON_BIN -m measurements.decision_error \
  --trace results/phase-20/rho_measured_long.csv \
  --tau-core 2.87 \
  --sync-period 0.5 \
  --d-sync 0.051 \
  --z-list 0,0.2,0.4,0.6,1.0,2.0,4.0 \
  --operational-mode bracket \
  --freeze-calibration results/phase-20/decision_error_offered.json \
  --seeds 100 \
  --n-boot 2000 \
  --out results/phase-20/decision_error_measured_fixed_trace_s0.json \
  2>&1 | tee logs/phase20_decision_error_measured_fixed_s0.log
```

For the full n=5 measured-telemetry cross-check:

```bash
for S in 0 1 2 3 4; do
  TRACE="results/phase-20/rho_measured_long.csv"
  if [ "$S" != "0" ]; then TRACE="results/phase-20/rho_measured_long_s${S}.csv"; fi
  $PYTHON_BIN -m measurements.decision_error \
    --trace "$TRACE" \
    --tau-core 2.87 \
    --sync-period 0.5 \
    --d-sync 0.051 \
    --z-list 0,0.2,0.4,0.6,1.0,2.0,4.0 \
    --operational-mode bracket \
    --freeze-calibration results/phase-20/decision_error_offered.json \
    --seeds 100 \
    --n-boot 2000 \
    --out "results/phase-20/decision_error_measured_fixed_trace_s${S}.json" \
    2>&1 | tee "logs/phase20_decision_error_measured_fixed_trace_s${S}.log"
done

$PYTHON_BIN -m measurements.summarize_decision_error_replicates \
  --inputs results/phase-20/decision_error_measured_fixed_trace_s0.json,results/phase-20/decision_error_measured_fixed_trace_s1.json,results/phase-20/decision_error_measured_fixed_trace_s2.json,results/phase-20/decision_error_measured_fixed_trace_s3.json,results/phase-20/decision_error_measured_fixed_trace_s4.json \
  --run-seed 100 \
  --out results/phase-20/decision_error_measured_fixed_replicates_summary.json

$PYTHON_BIN -m measurements.phase20_measured_crosscheck_diagnostic \
  --out results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json
```

## 10. Emergency Stop

```bash
tmux send-keys -t p20tau10 C-c
tmux send-keys -t p20tau2 C-c
tmux send-keys -t p20tau1800 C-c
tmux send-keys -t p20rep12 C-c
tmux send-keys -t p20rep34 C-c
sudo mn -c
sudo pkill -f 'mininet.flow_engine' || true
```

## Outputs To Report

```text
results/phase-20/tau_summary_10ms.json
results/phase-20/tau_summary_2ms.json
results/phase-20/tau_summary_long.json
results/phase-20/estimator_compare_10ms.json
results/phase-20/estimator_compare_long.json
results/phase-20/decision_error_offered_nc.json
results/phase-20/decision_error_offered.json
results/phase-20/decision_error_trace_s0.json
results/phase-20/decision_error_trace_s1.json
results/phase-20/decision_error_trace_s2.json
results/phase-20/decision_error_replicates_summary.json
results/phase-20/between_trace_summary.json
results/phase-20/between_trace_summary_n5.json
results/phase-20/core_load_diagnostic_n5.json
results/phase-20/decision_error_measured_fixed_replicates_summary.json
results/phase-20/measured_fixed_crosscheck_diagnostic_n5.json
```

# G-A016 ladder and live-admission runbook

Status: code-ready, measurement pending. Run only from plain tmux/SSH because
quiescing intentionally stops coding-agent and editor processes.

## Before quiescing

```bash
cd /home/ubuntu/dt4n
VENV_PY=/home/ubuntu/.venvs/dt4n-mininet/bin/python
A016_PREREG=phase-G-g3-a016-prereg

git status --porcelain
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
git rev-parse HEAD origin/main | uniq | wc -l  # must print 1
git ls-remote --tags origin | grep "$A016_PREREG" || echo "TAG CHUA CO"

$VENV_PY -m pytest -q \
  test/test_host_jitter_admission_v2.py \
  test/test_g3_a016_reanchor.py \
  test/test_g3_a016_artifact_provenance.py
```

`git status --porcelain` must be empty. HEAD must contain the v2 probe so the
measurement artifact can prove that its generating tool was committed.

## Measure from the quiesced shell

```bash
sudo bash scripts/bench_quiesce.sh --apply

$VENV_PY -m tools.host_jitter_probe \
  --mode floor --cpu 0 --duration-s 300 --label after_quiesce \
  --out results/SMOKE/phase-G/host_jitter_floor_after_quiesce_300s.json

$VENV_PY -m tools.host_jitter_probe \
  --mode ladder --duration-s 300 --label after_quiesce \
  --out results/SMOKE/phase-G/host_jitter_ladder_after_quiesce.json
```

The floor result extends the intervention comparison. Only the ladder result
can grant admission. Record its `binding_role`,
`p_stall_1ms_wilson_upper_95`, and
`emit3_timing_no_socket.max_abs_offdiag`. The last value is a one-replicate
diagnostic and must not be compared with the doc-41 16-replicate 0.10 gate.

## Forecast and preflight

Use the ladder artifact's binding Wilson endpoint as the conservative model
input. Produce two forecasts because the reduction operator is shape
dependent:

```bash
$VENV_PY -m tools.g3_emit3_feasibility \
  --p-stall WILSON_UPPER_FROM_LADDER \
  --replicates 1 --windows 1500 \
  --out results/SMOKE/phase-G/g3_emit3_forecast_probe_shape_a016.json

$VENV_PY -m tools.g3_emit3_feasibility \
  --p-stall WILSON_UPPER_FROM_LADDER \
  --replicates 8 --windows 150 \
  --out results/SMOKE/phase-G/g3_emit3_forecast_ladder_a016.json

$VENV_PY -m tools.g3_emitter_dryrun --a016 \
  --host-jitter-artifact \
    results/SMOKE/phase-G/host_jitter_ladder_after_quiesce.json \
  --out results/SMOKE/phase-G/g3_a016_benchmark_preflight.json
```

Compare `emit3_timing_no_socket.max_abs_offdiag` only with the `1 x 1500`
forecast and null. Keep the `8 x 150` result for the later benchmark timing
diagnostic. Cross-shape comparison is invalid even though both values use the
same correlation-reduction function.

Stop if `environment_pass` is false. A ladder admission failure is a measured
result and does not authorize a gate change.

## Commit, push, and preregister

Only after ladder admission passes:

```bash
A016_PREREG=phase-G-g3-a016-prereg
git add \
  results/SMOKE/phase-G/host_jitter_floor_after_quiesce_300s.json \
  results/SMOKE/phase-G/host_jitter_ladder_after_quiesce.json \
  results/SMOKE/phase-G/g3_emit3_forecast_probe_shape_a016.json \
  results/SMOKE/phase-G/g3_emit3_forecast_ladder_a016.json \
  results/SMOKE/phase-G/g3_a016_benchmark_preflight.json
git commit -m "G-A016: record ladder admission measurement"
git push origin main
git tag "$A016_PREREG"
git push origin "$A016_PREREG"

git rev-parse HEAD
git rev-parse origin/main
git ls-remote --tags origin | grep "$A016_PREREG"
```

The three printed commits must resolve to the same object before execution.

## Execute with live admission

```bash
$VENV_PY -m tools.g3_emitter_dryrun --a016 --execute --live-admission \
  --host-jitter-artifact \
    results/SMOKE/phase-G/host_jitter_ladder_after_quiesce.json \
  --out results/SMOKE/phase-G/g3_a016_benchmark.json
```

Execution first repeats the 300-second ladder probe in the same process. It
writes `results/SMOKE/phase-G/host_jitter_live_admission.json` and refuses
the benchmark if the fresh Wilson endpoint exceeds 0.02. This live check is
mandatory for `--a016 --execute`; it cannot be bypassed by omitting the flag.

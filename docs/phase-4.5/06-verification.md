# Phase 4.5.6 - Verification Gate

This is the final Phase 4.5 gate. It must be passed with numbers before Phase 5.

## What Was Added

- `rl/measure_delta.py`
- `rl/state_builder_draft.py`
- `rl/soft_reset_equivalence.py`
- `measurements/regression_report.py`
- `rl/configs/env_v0.yaml`
- `docs/phase-4.5/delta.json`
- `docs/phase-4.5/equivalence.json`

The JSON files are placeholders until runtime measurements overwrite them.

## Machine Config

Record this beside measured results:

```bash
hostnamectl
uname -a
lscpu | sed -n '1,25p'
free -h
/usr/bin/python3 --version
/usr/bin/python3 - <<'PY'
import numpy, scipy
print('numpy', numpy.__version__)
print('scipy', scipy.__version__)
PY
```

## 1. Delta

`Delta` is not command acknowledgement time.

- `t1`: `capacity.bwMbps` changes in Ditto
- `t2`: traffic rate stabilizes at the new level

Use `t2`.

Run with Ryu and Ditto healthy:

```bash
cd ~/dt4n
sudo mn -c
sudo PYTHONPATH=$PWD /usr/bin/python3 rl/measure_delta.py \
  --trials 20 --period 1.0 --out docs/phase-4.5/delta.json
```

The script saturates `srv1 -> srv2` with TCP on port `5004`, sends
`setBandwidth(s2-s3, 15)` through Ditto, and requires both:

- 3 consecutive stable samples within 5%
- rate changed by more than 10%

Final rule:

```text
Delta = p95(t2) + 0.3s
```

If `t2/t1 < 1.5`, assume the link was not saturated or the consequence check is
wrong. Do not use that Delta.

## 2. Soft Reset Equivalence

Hypothesis:

```text
H0: s0_soft and s0_hard have the same distribution
```

Use KS-test per state dimension, not t-test. Correct for 47 comparisons:

```text
alpha' = 0.05 / 47 = 0.001064
```

Run:

```bash
cd ~/dt4n
sudo PYTHONPATH=$PWD /usr/bin/python3 rl/soft_reset_equivalence.py \
  --samples 20 --period 1.0 \
  --out docs/phase-4.5/equivalence.json
```

Prediction table before data:

| Dimension group | Prediction | Reason |
| --- | --- | --- |
| `util_avg3` | should not differ | `StateBuilderDraft.reset()` clears history |
| `path_latency_norm` | may differ lightly | ARP/cache effects; soft reset flushes ARP |
| `bw_norm` | should not differ | `_restore_links()` restores baseline |
| `link_up`, `host_up`, `switch_up` | should not differ | all baseline up |
| `util` | should not differ | `_wait_steady_state()` absorbs startup |
| `data_fresh` | should not differ | Ditto healthy |

Interpretation:

- `<= 2/47` rejected: accept, explain dimensions
- `3..5/47`: investigate
- `> 5/47`: soft reset is not clean; stop

## 3. Regression

Run the old gates one at a time:

```bash
sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync \
  --period 1.0 --verify --output docs/phase-2/verify_report.json

sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync \
  --period 1.0 --measure-latency --trials 10 \
  | tee logs/measure_latency_after_45.log

sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync \
  --period 1.0 --measure-command --trials 10 \
  | tee logs/measure_command_after_45.log

sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync \
  --period 1.0 --measure-flow --trials 3 --flow-reset-log \
  --flow-report logs/command_flow_measure.log
```

Then:

```bash
/usr/bin/python3 measurements/regression_report.py \
  --sync-latency-report logs/measure_latency_after_45.log \
  --command-latency-report logs/measure_command_after_45.log \
  --soak-csv logs/env_runner_soak_50.csv \
  --delta-json docs/phase-4.5/delta.json \
  --equivalence-json docs/phase-4.5/equivalence.json \
  --out docs/phase-4.5/regression_report.json
```

Regression gates:

| Metric | Threshold |
| --- | --- |
| sync latency p95 | `< 2.0s` |
| command latency p95 | `< 2.0s` |
| cycle elapsed p95 | `<= baseline * 1.2` |
| patches per static delta cycle | `<= baseline` |
| verify accuracy | `>= baseline` |
| tests | 100% pass |

Patch count is the observer-effect gate. If a static network starts patching
every cycle, delta sync is broken.

## 4. Soft Reset Soak

Run:

```bash
sudo PYTHONPATH=$PWD /usr/bin/python3 measurements/soak_env_runner.py \
  --resets 100 --period 1.0 --hard-every 20 \
  --csv logs/env_runner_soak_100.csv
```

Record:

- reset p95
- dirty count
- iperf first/last
- whether reset time trends upward

## 5. Budget

Formula:

```text
seconds/episode = T_reset_avg + avg_steps * Delta
```

Hybrid reset:

```text
T_reset_avg = ((hard_every - 1) * T_soft + T_hard) / hard_every
```

Generate table with measured values:

```bash
/usr/bin/python3 measurements/regression_report.py \
  --delta-s <MEASURED_DELTA> \
  --soft-reset-s <MEASURED_T_SOFT> \
  --hard-reset-s <MEASURED_T_HARD> \
  --avg-steps 20 \
  --out docs/phase-4.5/regression_report.json
```

Target:

```text
300 episodes * 5 seeds <= about 24h
```

Do not reduce seed count below 5. Change period, `T_max`, or episode count
instead, and re-measure.

## Pure Checks

```bash
cd ~/dt4n
python3 test/test_state_builder_draft.py
python3 -m py_compile rl/measure_delta.py rl/state_builder_draft.py \
  rl/soft_reset_equivalence.py measurements/regression_report.py
```

## Final Gate

Pass all before Phase 5:

- Delta measured from `t2`, with `t2/t1 >= 1.5`
- Delta is at least `p95(t2) + 0.3s`
- soft/hard equivalence has `<= 2/47` rejected dimensions after Bonferroni
- regression gates pass
- soft reset soak has no crash/leak/trend
- budget is acceptable or a measured mitigation is chosen
- tests pass

Do not create the `phase-4.5-done` tag until measured JSON files are real and
the regression report is green.

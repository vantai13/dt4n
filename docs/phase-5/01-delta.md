# Phase 5.1 - Delta / Env Step Interval

## Decision

Use:

```text
period = 0.5s
traffic = TCP
read path = direct GET
Delta = 1.80s
T_max = 15  # temporary, pending oracle measurement in V6
```

Delta is the delay between sending an action and reading `s_{t+1}`. It uses
50% rise time, not full settling time:

```text
Delta = t50_p95 + period + snapshot_span_p95 + margin
      = 0.845   + 0.500  + 0.144             + 0.300
      = 1.789s ~= 1.80s
```

The confirmation run uses 20 trials:

- Source: `docs/phase-5/artifacts/delta_final.json`
- Gate: `docs/phase-5/artifacts/delta_final_gate.json`
- `t50`: p50 `0.632s`, p95 `0.845s`, max `1.046s`
- `t_s` settling: p50 `2.083s`, p95 `2.091s`, max `2.095s`
- `t_change=None`: `0/20`
- `t2/t1 p95`: `3.30`

An earlier screening run with 5 trials gave Delta about `1.58s`. We reject that
as a screening value only. The n=20 confirmation value is larger by about 14%,
which is the cost of not stopping early.

## Collector Gate

`period=0.5s` is not overloading the collector on this machine.

- Source: `docs/phase-5/raw/cycle_gate_p05.json`
- `cycle_elapsed`: p50 `0.058s`, p95 `0.127s`, max `0.340s`
- duty cycle: p50 `11.6%`, p95 `25.4%`, max `68.0%`
- gate: pass (`p95 duty <= 80%`)

Delta-sync is not full-sync on static network:

- delta patch cycles: `58/374` nonzero
- reconciliation cycles: `13/13` nonzero, expected because reconciliation is full

## t50 Validity

`t50` is not simply "any tiny rate change". The final detector requires:

- direction-correct rate movement
- progress >= `0.5 * expected_swing`
- progress >= `3 * sigma_robust`

Noise source:

- Source: `docs/phase-5/artifacts/rate_noise_final.json`
- `sigma_robust = 0.0694 Mbps`
- `3sigma = 0.2083 Mbps`
- median saturated rate around `4.9065 Mbps`

The t50 sample index is not constant:

- sample #2 in full collector sequence: 12/20 trials
- sample #3 in full collector sequence: 8/20 trials
- min progress fraction at t50: `0.506`

This is why the 20-trial p95 is larger than the 5-trial screening result.

## Phase vs Ramp

Source:

- `docs/phase-5/artifacts/phase_vs_ramp_analysis.txt`
- `docs/phase-5/artifacts/phase_vs_ramp_decompose.txt`
- `docs/phase-5/artifacts/phase_vs_ramp_analysis.json`

Findings:

- `corr(phi, sample_idx) = -0.839`: sampling phase strongly affects which
  collector sample crosses t50.
- `corr(rate_before, t50_source) = 0.177`: baseline rate/queue proxy does not
  explain t50 well in this run.
- `CV(t50_seen) = 0.308`: t50 spread is still high.

Conclusion: this is not cleanly pure phase and not proven physical ramp. For
Phase 7, do not blindly extrapolate one formula across sync interval or delay
axes. Remeasure Delta when period or RTT changes.

## Read Path

Keep direct GET.

- Source: `docs/phase-5/raw/bench_reader_snapshot.txt`
- direct GET: p50 `119.1ms`, p95 `144.0ms`, max `185.1ms`, `17` Things
- search: p50 `22.3ms`, p95 `41.7ms`, max `664.9ms`, `19` Things
- tSource skew search - direct: `0.000s`

Search is rejected despite lower p95 because:

- tail is heavy (`max/p95` about 16x)
- search returns extra Things:
  - `org.dt4n:controller`
  - `org.dt4n:link-h1-srv1`
- D5 studies staleness, so read path should stay simple and predictable

Entity-set check:

- Source: `docs/phase-5/raw/search_vs_direct.txt`

## Command Ack

Ditto fire-and-forget timeout is lowered so POST does not block the env step.
Therefore HTTP 202 means only "Ditto accepted the message", not "Command Agent
executed the action".

Safety checks:

- Source: `docs/phase-5/raw/whitelist_probe.json`
- invalid commands still reject in Command Agent audit
- HTTP status alone cannot distinguish success/reject

Implementation:

- `rl/flow_ack.py`
- unit tests: `test/test_flow_ack.py`
- live probe: `docs/phase-5/raw/flow_ack_command_only_probe.json`

The live command-only probe passed 5/5:

- valid `setBandwidth(15)`: executed
- negative bandwidth: rejected
- string bandwidth: rejected
- unknown command: rejected
- bad target: rejected

`TwinEnv` should write `action_requested` to replay, not `action_executed`.
Rejected commands are part of the environment dynamics `P(s'|s,a)`. Keep
`action_executed` in `info` for audit/debugging.

## T_max

Temporary value:

```text
T_max = 15
```

Reason:

- `env_v0` used 30 steps.
- `oracle_plan()` currently returns one recovery action.
- Long episodes can create reward-hacking pressure if per-step throughput
  reward is always positive.

V6 must run oracle over 50 seeds and set:

```text
T_max = p95(oracle steps_to_terminate) + 5
```

V5 should revisit reward shaping. Prefer throughput gap versus healthy baseline
over always-positive raw throughput reward.

## Artifacts

- `rl/configs/env_v1.yaml`
- `docs/phase-5/artifacts/delta_final.json`
- `docs/phase-5/artifacts/delta_final.csv`
- `docs/phase-5/artifacts/delta_final_gate.json`
- `docs/phase-5/artifacts/rate_noise_final.json`
- `docs/phase-5/artifacts/phase5_delta_final_check.md`
- `docs/phase-5/artifacts/phase_vs_ramp_analysis.json`
- `docs/phase-5/raw/cycle_gate_p05.json`
- `docs/phase-5/raw/bench_reader_snapshot.txt`
- `docs/phase-5/raw/search_vs_direct.txt`
- `docs/phase-5/raw/flow_ack_command_only_probe.json`

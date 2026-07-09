# Phase 4.5.5 - InjectionChannel

This lesson adds the fault-injection back door for experiments.

## Two Channels

```text
RL agent action
  -> Ditto message
  -> Command Agent whitelist
  -> command_agent_audit.log
  -> Mininet

Scenario fault
  -> InjectionChannel
  -> Mininet directly
```

The two paths must stay separate.

## Why Separate Them

1. Audit cleanliness

`logs/command_agent_audit.log` is evidence for "safe exploration by
construction". It should contain agent actions only. Scenario faults in that log
would make it impossible to tell what the agent actually did.

2. No information leakage

The agent should infer faults from metrics such as utilization, loss, and
latency. If scenarios go through Ditto messages, the agent can learn a hidden
"fault type" signal that was intentionally excluded from the observation.

3. D5 staleness needs a clean event time

In D5, the network fault should happen in the real net at t=0, while the agent
sees it only after the twin pipeline catches up. If fault injection also goes
through Ditto, the injection itself is delayed by the pipeline being studied.

## Added Files

- `rl/scenarios.py`
  - `Scenario`
  - `LinkDegrade`
  - `TrafficFlood`
  - `make_scenario(seed, spec)`
- `rl/injection.py`
  - `InjectionChannel`
- `rl/oracle_policy.py`
  - `oracle_action()`
  - `oracle_plan()`
  - `oracle_feasible()`
- `measurements/measure_noise_std.py`
  - writes `docs/phase-4.5/baseline/noise_std.json`

## Scenario Contract

Every scenario has:

- `params_from_seed(rng, spec)`: deterministic, no global random
- `apply(net)`: inject fault, caller holds `net_lock`
- `revert(net)`: idempotent cleanup
- `describe()`: metadata for experiment logs, not Command Agent audit

`revert()` is required even though `EnvRunner.soft_reset()` also restores links.
Scenario code must clean up what it creates, independently of the runner.

## Current Scenarios

| Scenario | Injection | Seeded parameters | Cleanup |
| --- | --- | --- | --- |
| `LinkDegrade` | `intf.config(bw=..., delay=...)` | non-bridge link, factor 0.2..0.6 | restore baseline bw + delay |
| `TrafficFlood` | UDP iperf on port 5003 | client, server, rate 30..60 Mbps | `pkill` only flood port |

`TrafficFlood` uses port `5003` because the current DT4N background
srv1->srv2 flow uses port `5002`.

`LinkDegrade` chooses from `toggleable_links(spec)`, not from all links. In the
current topology, that means:

```text
s1-s2, s1-s3, s2-s3
```

## 3-Sigma Calibration

Do not choose scenario strength by feel.

1. Run healthy network traffic.
2. Measure baseline observation noise.
3. A scenario should move at least one observation dimension by `>= 3 * sigma`.
4. The oracle should still name a recovery action within the step budget.

Generate baseline noise:

```bash
cd ~/dt4n
/usr/bin/python3 measurements/measure_noise_std.py \
  --samples 300 --interval 1.0 \
  --out docs/phase-4.5/baseline/noise_std.json
```

The committed baseline file is intentionally marked `"measured": false` until
you run this on a healthy live system.

## Local Checks

Pure checks:

```bash
cd ~/dt4n
python3 test/test_scenarios.py
/usr/bin/python3 test/test_scenarios.py
python3 -m py_compile rl/scenarios.py rl/injection.py rl/oracle_policy.py \
  test/test_scenarios.py measurements/measure_noise_std.py
```

Check no global RNG use in scenario generation:

```bash
grep -En 'random\.|np\.random\.[^d]' rl/scenarios.py || true
```

Expected: no matches.

## Runtime Audit Check

Start Ditto, Ryu, and an `EnvRunner`, then inject one scenario through
`InjectionChannel` and send one normal agent command through Ditto. The audit
log must contain the agent command only.

Manual skeleton:

```bash
cd ~/dt4n
: > logs/command_agent_audit.log
sudo PYTHONPATH=$PWD /usr/bin/python3 - <<'PY'
from mininet.env_runner import EnvRunner
from rl.scenarios import LinkDegrade

r = EnvRunner(hard_every=0)
try:
    r.start()
    sc = LinkDegrade('s1-s2', 0.5, '2ms', 20.0)
    r.injection.apply(sc)
    print('active:', r.injection.active())
    r.injection.revert_all()
finally:
    r.close()
PY
grep -E 'LinkDegrade|TrafficFlood|INJECT' logs/command_agent_audit.log || true
```

Expected: no grep output. Injection logs may appear in `logs/run_sync.log`, but
not in `logs/command_agent_audit.log`.

## Validation

- `revert()` can be called twice safely
- `make_scenario(seed, spec)` is deterministic
- `LinkDegrade` never picks a bridge link
- `InjectionChannel` reverts and clears active scenarios
- `oracle_policy` returns a recovery action for current scenarios
- scenario code does not use global random
- Command Agent audit remains scenario-free

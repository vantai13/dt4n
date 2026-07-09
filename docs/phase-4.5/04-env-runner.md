# Phase 4.5.4 - EnvRunner + Soft Reset

This lesson splits the live network lifecycle out of `mininet/run_sync.py` into
`mininet/env_runner.py`.

## What Changed

- `mininet/topology_meta.py`
  - computes baseline bandwidth per link
  - uses Tarjan DFS to find graph bridges
  - exposes `toggleable_links()`, currently `s1-s2`, `s1-s3`, `s2-s3`
- `mininet/env_runner.py`
  - component API: `start()`, `soft_reset()`, `hard_reset()`, `close()`,
    `observe_raw()`
  - owns `net`, `net_lock`, `stop_event`, Sync Agent thread, Command Agent thread
  - returns reset diagnostics in an `info` dict
- `mininet/run_sync.py`
  - remains the CLI entry point
  - now delegates lifecycle work to `EnvRunner`
- `bridge/sync_agent.py`
  - stores `net.dt4n_collector` so soft reset can clear rate caches
- `measurements/soak_env_runner.py`
  - runs repeated soft resets and writes timing CSV

## Lifecycle

```text
start()
  build Mininet
  wait static controller convergence
  bootstrap Ditto Things
  start Sync Agent
  start Command Agent

soft_reset()
  kill iperf
  restore links up + baseline bw + original delay
  flush ARP caches
  clear Collector rate caches
  restart episode background traffic
  wait steady state
  optionally apply scenario
  return reset diagnostics

hard_reset()
  close()
  start()

close()
  stop threads
  kill iperf
  stop Mininet
  mn -c
```

## Reset Hygiene Checklist

Soft reset cleans the silent state that can leak between RL episodes:

- iperf processes: old clients/servers can keep ports busy
- link state: a down link must not survive into the next episode
- bandwidth: degraded links return to baseline
- delay: `TCIntf.config(bw=...)` rebuilds qdisc, so reset passes the original
  delay back too
- ARP cache: soft and hard reset should both start cold for path-latency tests
- collector counters: `_prev` and `_prev_link` must not mix two episodes
- steady state: the first observation waits until throughput is stable

`EnvRunner` does not delete all OpenFlow rules during soft reset. The static
controller needs its table-miss and ARP controller rules; link up/down events
already trigger route refreshes.

## Why `_wait_steady_state()` Exists

`rxRate` is a rate over the previous collector cycle. Right after iperf starts,
that window includes socket setup and TCP slow start. Reading `s0` immediately
would make the initial state depend on Linux scheduling rather than the
experiment seed.

`soft_reset()` therefore records:

- `reset_wait_s`
- `reset_steady_ok`
- `reset_dirty`

Those values are future Gym `info` fields. If `reset_wait_s` is wide or many
episodes are dirty, reset is not clean enough to trust.

## Local Checks

Pure checks, no root and no live Mininet:

```bash
cd ~/dt4n
python3 -m mininet.topology_meta
python3 test/test_topology_meta.py
python3 test/test_env_runner.py
python3 -m py_compile mininet/topology_meta.py mininet/env_runner.py \
  mininet/run_sync.py bridge/sync_agent.py measurements/soak_env_runner.py
```

Expected metadata:

```text
Cau (KHONG duoc toggle): ['h1-s1', 'h2-s1', 'h3-s1', 's2-srv1', 's3-srv2']
Toggle duoc          : ['s1-s2', 's1-s3', 's2-s3']
```

`run_sync.py --help` needs the Python interpreter that has `requests`:

```bash
/usr/bin/python3 -m mininet.run_sync --help
```

## Runtime Smoke Test

Terminal 1:

```bash
cd ~/dt4n
PYTHONPATH=$PWD ryu-manager mininet.controller_static --ofp-tcp-listen-port 6653
```

Terminal 2:

```bash
cd ~/dt4n
sudo mn -c
sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync --period 1.0 --verify
```

Then test one measurement mode at a time:

```bash
sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync --period 1.0 \
  --measure-latency --trials 3

sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync --period 1.0 \
  --measure-command --trials 3

sudo PYTHONPATH=$PWD /usr/bin/python3 -m mininet.run_sync --period 1.0 \
  --measure-flow --trials 2 --flow-reset-log
```

## Soft Reset Soak

Use a small run first:

```bash
cd ~/dt4n
sudo mn -c
sudo PYTHONPATH=$PWD /usr/bin/python3 measurements/soak_env_runner.py \
  --resets 5 --period 1.0 --csv logs/env_runner_soak_5.csv
```

Then the lesson validation:

```bash
sudo PYTHONPATH=$PWD /usr/bin/python3 measurements/soak_env_runner.py \
  --resets 50 --period 1.0 --csv logs/env_runner_soak_50.csv
```

Record:

- `reset_total_s` mean, p95, max
- `reset_wait_s` histogram
- `dirty=0/50` target
- `iperf_count` should not trend upward

Quick manual checks after a soft reset:

```bash
pgrep -c -f iperf
sudo tc qdisc show dev s1-eth2 | grep -E 'netem|delay'
sudo PYTHONPATH=$PWD /usr/bin/python3 - <<'PY'
from mininet.env_runner import EnvRunner
r = EnvRunner(hard_every=0)
try:
    r.start()
    print(r.soft_reset())
    print(r.net.get('h1').cmd('arp -n'))
finally:
    r.close()
PY
```

After ARP flush, `arp -n` should have no learned peer entries until traffic
repopulates it.

# Lesson 9.0 Rev5 - Density Resolves The Link Law

## Corrections

rev1 was wrong: `q_delay = base_delay * rho` looked like a new queueing law
because the old sweep had high R2 across configs.

rev2 was wrong: netem/BDP occupancy was rejected using a few instantaneous
samples. BDP predicts an expectation, not one qdisc read.

rev3 was wrong: `P(1p) = 0.53*rho + 0.09` was a single-config artifact. The
coefficient changes across bandwidth/base-delay configs.

rev4 was wrong: `P(2..q-2) = 0` was a coarse-sweep artifact. The fine cliff
sweep found middle queue sizes inside a very narrow band.

rev5 is the current interpretation: density probes show BDP occupancy below
the cliff, a metastable critical band, and a full finite queue above it.

## Evidence

Low-load mean backlog packets match BDP:

| bw Mbps | base ms | rho_meas | mean packets | BDP packets |
|---:|---:|---:|---:|---:|
| 4 | 2.0 | 0.969 | 0.61 | 0.64 |
| 6 | 3.0 | 0.969 | 1.52 | 1.44 |
| 8 | 1.5 | 0.968 | 0.96 | 0.96 |

Fine cliff sweep on `bw=4, base=2.0, q=13`:

| rho_offered | mean packets | middle mass | qdisc delay ms | loss |
|---:|---:|---:|---:|---:|
| 0.925 | 0.64 | 0.000 | 1.94 | 0.000 |
| 0.930 | 8.91 | 0.720 | 26.94 | 0.001 |
| 0.935 | 12.24 | 0.090 | 37.03 | 0.007 |
| 0.940 | 12.49 | 0.000 | 37.77 | 0.014 |

The robust cliff is therefore much narrower than the first bracket:

```text
rho_offered in (0.925, 0.930]
```

## Current Physical Interpretation

Below `rho_offered <= 0.925`, the measured qdisc backlog is netem/BDP
occupancy: packets already in flight. It is not a congestion queue.

Around `rho_offered ~= 0.930`, the queue is metastable. The measured queue
spreads across the middle and high packet counts and averages about `0.71` of
the finite ceiling.

At and above about `rho_offered >= 0.935`, the finite queue is near full.
Overload magnitude is represented by loss:

```text
loss = max(0, 1 - 1 / (1.079 * rho_offered))
```

The loss-derived threshold `1 / 1.079 = 0.927` remains a useful cross-check,
but rev5 uses the direct fine-density bracket for delay.

## Model Contract

`rl/routing/link_model.py` now expects offered load in `queueing_delay_ms()` and
`total_delay_ms()`. This is intentional: measured utilization clips near 1.0
and cannot distinguish the critical point from full overload.

```text
rho_offered <= 0.925   -> qdisc_delay = base_delay * rho_measured
0.925 < rho_offered < 0.9325 -> qdisc_delay = 0.71 * ceiling
rho_offered >= 0.9325  -> qdisc_delay = ceiling
```

The agent state still exposes measured utilization and loss. Reward, Dijkstra
oracles, gates, and static expected weights use offered-load snapshots so the
simulator can reproduce the measured physical regimes.

## Files

- `results/calib/qdisc_density.csv`
- `results/calib/density_bw4_d2.0_q13_0718_0158.csv`
- `results/calib/density_bw6_d3.0_q20_0718_0158.csv`
- `results/calib/density_bw8_d1.5_q26_0718_0158.csv`
- `results/calib/cliff_fine_0718_0212.csv`
- `measurements/qdisc_density_probe.py`
- `measurements/analyze_qdisc_density.py`
- `rl/routing/link_model.py`

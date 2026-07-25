# Phase 14C.7 - Threshold unit audit for r_v3

Ngay tao: 2026-07-24
Status: pre-measurement audit, then measured proxy result.

## Question

The Phase 14 gate is:

```text
PASS iff lower CI95 >= 0.10
```

The threshold came from the Phase 9 anchor:

```text
0.10 ~= 2 x std_agent
std_agent ~= 0.045
```

Phase 14C changed the reward scale from `r_v2` to `r_v3` and changed the best
objective to CVaR alpha=0.1. Therefore the unit of the measured gap changed.
This raises a legitimate unit-consistency question: the formula should remain
`2 x noise`, but the noise input should match the same stage and reward scale.

## Pre-measurement rule

This audit keeps the old formula:

```text
candidate_threshold = 2 x measured_noise
```

It does not choose a threshold after seeing whether `gap=0.02029` passes.

However, there are two different noise quantities:

| quantity | what it measures | can replace Phase 9 std_agent? |
|---|---|---|
| `std_agent` | seed-to-seed variation of trained agents | yes, if measured on the new stage/reward/objective |
| `noise_floor.py` | seed-to-seed variation of Bayes-marginalized oracle/evaluation | no, proxy only unless explicitly approved |

The repository already records that `noise_floor.py` did not reproduce the
Phase 9 anchor on routing_2path. It measured about `0.0095`, while the Phase 9
agent-training anchor was `0.045`. Therefore a low Bayes noise floor by itself
must not be used to lower the official gate.

## Tool availability check

`measurements.measure_std_agent` imports `torch` and evaluates frozen DQN
policies. In the current environment, `torch` is not installed, so the true
agent-training std cannot be measured here:

```text
ModuleNotFoundError: No module named 'torch'
```

That blocks replacing the official gate with a true `std_agent(r_v3)` value in
this environment.

## Proxy measurement plan

Run the Bayes/evaluation proxy anyway, with reward provenance, to understand
the scale:

```bash
python3 -m measurements.noise_floor \
  --topology routing3 --reward-model r_v3 \
  --objective cvar --cvar-alpha 0.1 \
  --seeds 10 --cases 200 --mc-samples 100 \
  --out results/phase-14c/noise_floor_routing3_v3_cvar01.json
```

This result is exploratory and must be reported as a proxy. It cannot by itself
convert the Phase 14C reward-only FAIL into a PASS.

## Proxy result

Command:

```bash
python3 -m measurements.noise_floor \
  --topology routing3 --reward-model r_v3 \
  --objective cvar --cvar-alpha 0.1 \
  --seeds 10 --cases 200 --mc-samples 100 \
  --out results/phase-14c/noise_floor_routing3_v3_cvar01.json
```

Output:

| metric | value |
|---|---:|
| topology | `routing3` |
| load_cfg | `EVENT_3PATH_V4_RATE_0.12_PROFILE_cliffband_BIAS_0` |
| reward_model | `r_v3` |
| reward_model_sha | `4fb73b561a44` |
| objective | `cvar` |
| cvar_alpha | 0.1 |
| seeds | 10 |
| cases | 200 |
| mc_samples | 100 |
| performance_mean | -3.336721 |
| noise_floor | 0.074054 |
| threshold_2x | 0.148108 |

Per-seed Bayes-marginalized returns:

```text
[-3.3729, -3.2907, -3.2889, -3.3196, -3.3189,
 -3.4001, -3.4303, -3.4464, -3.2107, -3.2886]
```

## Interpretation

The proxy measurement does not support lowering the Phase 14C gate. Even if the
Bayes/evaluation proxy were accepted as the noise quantity, the formula
`2 x noise_floor` gives:

```text
candidate_threshold = 0.148108
```

This is higher than the old `0.10` gate and much higher than the best
reward-only result:

```text
best lower CI95 = 0.02027
```

Therefore the threshold-unit audit does not convert the Phase 14C reward-only
pilot into a PASS. The correct status remains FAIL.

The true `std_agent(r_v3)` question remains blocked in this environment because
the agent-evaluation path requires `torch`.

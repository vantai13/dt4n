# Lesson 9 - Expired Constants Checklist

When the link model changes, every constant below must be re-audited before
using gates, presets, or headline numbers.

## Expired Constants Found

| Constant | Old Context | Failure |
|---|---|---|
| `LOSS_THRESHOLD = 0.85` | Uncalibrated routing-sdn/M/M/1 simulator | No measured source; contradicted by Mininet loss cliff. |
| `STD_SEED_ESTIMATE = 0.0276` | Older Phase-8/M/M/1 agent variance | Underestimated rev5 1500-episode agent std by about 2.9x. |
| `LOAD_PRESETS['bottleneck_E'] = (0.70, 0.85)` | M/M/1 world where 0.85 looked congested | In rev5, 0.85 is below the measured cliff, so `safe_delta` compared two mostly uncongested worlds. |

## Current Rev5 Anchors

Measured delay regimes:

```text
rho_offered <= 0.925          BDP/netem occupancy
0.925 < rho_offered < 0.9325  critical band
rho_offered >= 0.9325         near-full finite queue
```

Current eval presets:

```text
normal        e_load=(0.40, 0.70),  drift_sigma=0.0
borderline    e_load=(0.925, 0.935), drift_sigma=0.0
bottleneck_E  e_load=(0.95, 1.15),  drift_sigma=0.0
```

Training remains stochastic:

```text
LOAD_CFG_TRAIN e_load=(0.70, 1.00), drift_sigma=0.15
```

Preset drift is off because presets measure reaction on one side of the cliff.
Training drift stays on because the policy must learn under the real stage
distribution.

## Audit Rule

Before reporting a new result after a link-model change:

1. Search for old thresholds and presets:
   `rg "0\\.85|0\\.9275|STD_SEED|LOAD_PRESETS|LOSS_THRESHOLD|safe_delta"`.
2. Re-run `scripts/analyze_5seed.py` without retraining if only eval presets
   changed.
3. Re-run `oracle_gate.py` with a `--std-seed-estimate` measured from the same
   episode/config/model context.
4. Do not carry SNR, `safe_delta`, or preset conclusions across model changes.

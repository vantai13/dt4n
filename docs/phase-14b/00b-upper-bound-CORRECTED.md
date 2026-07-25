# Lesson 14B.0 (CORRECTED) - Direct G_sync Headroom

Ngay tao: 2026-07-25
Current Git at measurement: `ccec7d4`
Corrected artifact: `results/phase-14b/sync_headroom_corrected_200x150_s0.json`

## 1. Retraction

`docs/phase-14b/00-upper-bound.md` used:

```text
G_sync_gross(z) <= disagree_14A(z) x decision_regret_14A
```

That formula is wrong. `decision_regret_14A` measures the value of knowing `z`
while still routing from a stale snapshot. It is bounded by the q-margin of
near-tied routing actions. A sync action buys a fresh snapshot, so its regret is
the value of avoiding a route that may now be physically wrong. That quantity
is not bounded by the Phase 14A q-margin.

## 2. Correct Measurement

The corrected gross upper bound is measured directly:

```text
G_sync_gross(z) = objective(R(a_fresh(w), w)) - objective(R(a_stale, w))

a_stale = argmax_a Q(a | old_obs, z)
a_fresh = argmax_a R(a, w)
```

`a_fresh` is clairvoyant on the sampled true world, so this is still an upper
bound before subtracting `c_sync`. The measurement uses split-sample selection
and scoring (`--estimator honest`) to avoid winner's curse.

Configuration:

```text
topology    = routing3
load_cfg    = EVENT_3PATH_V4_RATE_0.12_PROFILE_cliffband_BIAS_0
objective   = CVaR alpha=0.1
cases       = 200 per z
mc_samples  = 150
seed        = 0
```

## 3. Evidence

| z | old wrong bound | measured G_sync | lower CI95 | fresh disagree | sync regret | measured / old |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.000000 | 0.000000 | 0.000000 | 0.000 | 0.000 | n/a |
| 1 | 0.001170 | 0.543952 | 0.514764 | 0.126 | 4.321 | 464.9x |
| 3 | 0.012197 | 1.047122 | 1.030979 | 0.600 | 1.745 | 85.9x |
| 5 | 0.023188 | 1.115858 | 1.103754 | 0.666 | 1.674 | 48.1x |
| 8 | 0.019794 | 1.159938 | 1.155751 | 0.664 | 1.746 | 58.6x |
| 12 | 0.019571 | 1.165848 | 1.156088 | 0.680 | 1.714 | 59.6x |

The old "upper bound" is exceeded by 48-60x on the main stale range and by
85x at z=3. Therefore it is not an upper bound; it was measuring the wrong
regret term.

## 4. Design Lesson

The Phase 14B design spec says:

```text
Q(SYNC, o, z) = -c_sync + E[V(o', 0)]
```

That statement implies sync regret has a floor from the value of a fresh
snapshot. The old implementation imported `decision_regret_14A`, which has a
ceiling from q-margin. This is specification-implementation drift.

Regression guard:

```bash
python -m pytest -q test/routing/test_sync_headroom.py
```

The test checks that measured sync regret at z=5 is more than 10x the Phase 14A
decision regret (`0.028867`).

## 5. Next Gate

Large `G_sync` does not prove adaptive AoI-triggered sync is useful. Periodic
sync can collect much of this value too. The next quantity is:

```text
G_AoI_upper(B/N) = E[G_sync | top B/N states] - E[G_sync]
```

for sync budgets such as `B/N = 0.1, 0.2, 0.3`. This must be compared against
the best periodic or threshold baseline at the same sync budget.

Measured on the same `200 x 150` artifact with a uniform z-grid:

| budget B/N | n_sync | E[top] | E[all] | G_AoI_upper | threshold |
|---:|---:|---:|---:|---:|---:|
| 0.100 | 120 | 1.193601 | 0.838786 | 0.354815 | 1.184684 |
| 0.200 | 240 | 1.185466 | 0.838786 | 0.346679 | 1.170533 |
| 0.300 | 360 | 1.177875 | 0.838786 | 0.339088 | 1.154418 |

This is only an adaptive-oracle upper bound. The next required comparison is
against best periodic and best threshold sync at the same budget.

## 6. Re-run Commands

```bash
python -m measurements.sync_headroom \
  --cases 200 --mc-samples 150 \
  --objective cvar --cvar-alpha 0.1 \
  --estimator honest --seed 0 \
  --out results/phase-14b/sync_headroom_corrected_200x150_s0.json

python -m measurements.sync_headroom \
  --cases 200 --mc-samples 150 --z-values 5 \
  --objective cvar --cvar-alpha 0.1 \
  --estimator honest --seed 0 \
  --out results/phase-14b/sync_headroom_z5_200x150_s0.json
```

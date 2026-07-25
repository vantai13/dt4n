# Phase 14C.6 - Positive pilot results for routing3 with r_v3

Ngay tao: 2026-07-24
Prereg: `docs/phase-14c/05-positive-pilot-preregistration.md`
Reward sha: `4fb73b561a44`

## Preregistered Prediction

Prediction before running:

```text
r_v3 alone will still FAIL the Phase 14A gate.
Directional prediction: gap stays roughly the same as r_v2 or decreases,
not enough to matter.
```

The gate remained FAIL for all six runs. The directional prediction was mixed:
`mean` decreased strongly, while `CVaR alpha=0.1` increased relative to the
recorded r_v2 best but stayed far below the gate.

## Commands

```bash
for s in 0 1 2; do
python3 -m measurements.pilot_marginalized \
  --topology routing3 --reward-model r_v3 \
  --cases 400 --mc-samples 200 --seed "$s" \
  --objective mean \
  --out "results/phase-14c/pilot3_v3_mean_seed${s}.json"
done

for s in 0 1 2; do
python3 -m measurements.pilot_marginalized \
  --topology routing3 --reward-model r_v3 \
  --cases 400 --mc-samples 200 --seed "$s" \
  --objective cvar --cvar-alpha 0.1 \
  --out "results/phase-14c/pilot3_v3_cvar01_seed${s}.json"
done
```

## Results

| file | objective | seed | gap | lower | disagree | regret | q_margin | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `pilot3_v3_cvar01_seed0.json` | cvar | 0 | 0.01965 | 0.01635 | 0.4325 | 0.04543 | 0.6366 | FAIL |
| `pilot3_v3_cvar01_seed1.json` | cvar | 1 | 0.01707 | 0.01359 | 0.3625 | 0.04710 | 0.7059 | FAIL |
| `pilot3_v3_cvar01_seed2.json` | cvar | 2 | 0.02414 | 0.02027 | 0.4650 | 0.05191 | 0.6346 | FAIL |
| `pilot3_v3_mean_seed0.json` | mean | 0 | 0.00157 | 0.00022 | 0.0225 | 0.06996 | 1.3881 | FAIL |
| `pilot3_v3_mean_seed1.json` | mean | 1 | 0.00273 | 0.00037 | 0.0250 | 0.10935 | 1.3814 | FAIL |
| `pilot3_v3_mean_seed2.json` | mean | 2 | 0.00057 | -0.00011 | 0.0125 | 0.04562 | 1.4289 | FAIL |

Seed averages:

| objective | gap mean | gap std | lower mean | disagree mean | regret mean | q_margin mean |
|---|---:|---:|---:|---:|---:|---:|
| cvar alpha=0.1 | 0.02029 | 0.00292 | 0.01674 | 0.4200 | 0.04815 | 0.6591 |
| mean | 0.00163 | 0.00088 | 0.00016 | 0.0200 | 0.07498 | 1.3995 |

## Interpretation

Mean objective:

`r_v3` makes mean-objective routing more decisive (`q_margin ~= 1.40`), and
disagreement collapses to about `0.02`. The regret on rare disagree cases is
larger than in r_v2, but the product is tiny:

```text
gap ~= 0.0200 x 0.07498 = 0.00150
```

CVaR objective:

CVaR keeps disagreement high (`0.42`) by putting decisions near risk-sensitive
boundaries. r_v3 raises the measured gap above the recorded r_v2 best
(`0.02029` vs `0.0123`), but the lower CI is still only about `0.0167`, far
below the pre-registered `0.10` gate.

The reward redesign is therefore useful diagnostically but not sufficient as a
positive result. It confirms the Phase 14A mechanism: headroom depends on the
product `disagree_rate x decision_regret`. Increasing reward severity alone can
increase regret, but it can also increase q_margin and suppress disagreement.

## Decision

Phase 14C reward-only positive pilot: FAIL.

Allowed next step under prereg: at most one additional pre-registered round
with `criticality`, reporting both reward-only and reward+criticality results.

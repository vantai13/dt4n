# Phase 14C.3 - Same-stage static routing3 negative control

Ngay tao: 2026-07-24
Status: same-stage negative control. Positive reward-only pilot is documented
separately in `05-positive-pilot-preregistration.md` and
`06-positive-pilot-results.md`.

## Purpose

The two-path negative control is necessary but not sufficient for r_v3 because
it is structurally different from routing3 and is not sensitive to the reward
redesign in the headline gap. This check uses the actual routing3 stage while
turning off events. If the world is static, AoI should not change the optimal
action:

```text
expected: gap = 0 and disagree_rate = 0 for every z
```

## Command

```bash
ROUTING3_EVENT_RATE=0 python3 -m measurements.pilot_marginalized \
  --topology routing3 --reward-model r_v3 \
  --cases 400 --mc-samples 200 --seed 0 \
  --out results/phase-14c/negctrl_static3_v3_seed0.json
```

## Provenance

| field | value |
|---|---:|
| git_hash | `4cf5846` |
| topology | `routing3` |
| load_cfg | `EVENT_3PATH_V4_RATE_0_PROFILE_cliffband_BIAS_0` |
| reward_model | `r_v3` |
| reward_model_path | `rl/routing3/reward3_v3.py` |
| reward_model_sha | `4fb73b561a44` |
| objective | `mean` |
| cases | 400 |
| mc_samples | 200 |
| seed | 0 |

## Result

| metric | value |
|---|---:|
| gap_marginalized | 0.000000 |
| gap_ci95 | 0.000000 |
| lower CI95 | 0.000000 |
| threshold | 0.100000 |
| verdict | `FAIL` |
| agree_rate | 1.000000 |
| disagree_rate | 0.000000 |
| n_disagree | 0 |
| decision_regret | 0.000000 |
| q_margin | 2.117270 |
| q_margin_marginalized | 2.115014 |

## Static-control validity checks

This control is valid for three independent reasons, not just because the
headline gap is zero.

First, the provenance confirms that events were actually disabled:

```text
load_cfg = EVENT_3PATH_V4_RATE_0_PROFILE_cliffband_BIAS_0
```

Second, `gap_ci95 = 0.000000`. This means every evaluated case had zero gap;
the result is deterministic under the static world rather than an average that
happened to wash out.

Third, the selected actions are not degenerate. Both `a_star_z` and
`a_star_marg` choose all three paths, with identical counts at every z:

| z | a_star_z | a_star_marg |
|---:|---|---|
| 0 | P1=24, P2=28, P3=21 | P1=24, P2=28, P3=21 |
| 1 | P1=14, P2=26, P3=26 | P1=14, P2=26, P3=26 |
| 3 | P1=27, P2=16, P3=20 | P1=27, P2=16, P3=20 |
| 5 | P1=24, P2=16, P3=23 | P1=24, P2=16, P3=23 |
| 8 | P1=19, P2=21, P3=25 | P1=19, P2=21, P3=25 |
| 12 | P1=19, P2=29, P3=22 | P1=19, P2=29, P3=22 |

So the measurement is not returning zero because every case collapses to one
path. The static rho values still separate P1/P2/P3; AoI simply adds no extra
decision information when events are disabled.

Per-z disagreement:

| z | disagree | q_margin |
|---:|---:|---:|
| 0 | 0.000 | 2.286562 |
| 1 | 0.000 | 2.082484 |
| 3 | 0.000 | 2.114600 |
| 5 | 0.000 | 1.968405 |
| 8 | 0.000 | 1.995185 |
| 12 | 0.000 | 2.223269 |

## Decision

The same-stage static negative control passes: `gap = 0`, `n_disagree = 0`, and
`disagree_rate = 0` for every z. Therefore r_v3 does not leak AoI value from
reward mechanics alone on routing3.

The large static q-margin (`q_margin ~= 2.117`) is also recorded as a warning
signal for the positive pilot: r_v3 increases reward span, but it can also make
the best action harder to flip. The reward-only positive pilot is therefore
pre-registered and reported separately before any criticality round.

# Phase 14C.1 - Negative control for r_v3

Ngay tao: 2026-07-24
Base Git: `4cf5846`
Reward under test: `rl/routing3/reward3_v3.py`

## Purpose

Before using `r_v3` for any positive claim on routing3 or sync, rerun the
known negative control on the old two-path topology. This checks that the new
reward did not become a reward-scale amplifier that reports headroom on a stage
already rejected by Phase 14A.

## Command

```bash
python3 -m measurements.pilot_marginalized \
  --topology routing_2path --reward-model r_v3 \
  --cases 400 --mc-samples 200 --seed 0 \
  --out results/phase-14c/negctrl_2path_v3_seed0.json
```

## Provenance

| field | value |
|---|---:|
| git_hash | `4cf5846` |
| topology | `routing_2path` |
| load_cfg | `LOAD_CFG_DYNAMIC` |
| reward_model | `r_v3` |
| reward_model_path | `rl/routing3/reward3_v3.py` |
| reward_model_sha | `4fb73b561a44` |
| objective | `mean` |
| cases | 400 |
| mc_samples | 200 |
| seed | 0 |

## Result

Single-seed result kept for continuity with the Phase 14A negative control:

| metric | value |
|---|---:|
| gap_marginalized | 0.005583 |
| gap_ci95 | 0.002360 |
| lower CI95 | 0.003222 |
| threshold | 0.100000 |
| verdict | `FAIL` |
| agree_rate | 0.947500 |
| disagree_rate | 0.052500 |
| n_disagree | 21 |
| decision_regret | 0.106341 |
| q_margin | 3.987588 |
| q_margin_marginalized | 3.915399 |

Three-seed comparison against r_v2:

| file | reward | seed | gap | regret | n_disagree | disagree | q_margin | verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `negctrl_2path_v2_seed0.json` | `r_v2` | 0 | 0.005583 | 0.106341 | 21 | 0.0525 | 1.1457 | FAIL |
| `negctrl_2path_v2_seed1.json` | `r_v2` | 1 | 0.005430 | 0.114320 | 19 | 0.0475 | 1.0943 | FAIL |
| `negctrl_2path_v2_seed2.json` | `r_v2` | 2 | 0.005597 | 0.106607 | 21 | 0.0525 | 1.0920 | FAIL |
| `negctrl_2path_v3_seed0.json` | `r_v3` | 0 | 0.005583 | 0.106341 | 21 | 0.0525 | 3.9876 | FAIL |
| `negctrl_2path_v3_seed1.json` | `r_v3` | 1 | 0.005430 | 0.114320 | 19 | 0.0475 | 3.7900 | FAIL |
| `negctrl_2path_v3_seed2.json` | `r_v3` | 2 | 0.005597 | 0.106607 | 21 | 0.0525 | 3.9114 | FAIL |

Summary:

| reward | mean gap | mean q_margin | n_disagree by seed |
|---|---:|---:|---|
| `r_v2` | 0.005537 | 1.1107 | 21, 19, 21 |
| `r_v3` | 0.005537 | 3.8963 | 21, 19, 21 |

Per-z disagreement:

| z | disagree |
|---:|---:|
| 0 | 0.300 |
| 1 | 0.000 |
| 3 | 0.000 |
| 5 | 0.000 |
| 8 | 0.000 |
| 12 | 0.000 |

## Mechanism audit

Important correction: the original r_v2 negative control in
`docs/phase-14/01-meter-validation.md` was already concentrated at `z=0`.
The r_v3 negative control did not newly move disagreement into `z=0`; it kept
the same per-z disagreement pattern while making the two-path margins much
larger.

| z | r_v2 q_margin | r_v3 q_margin | ratio | r_v2 disagree | r_v3 disagree |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.413652 | 1.210033 | 2.925 | 0.300 | 0.300 |
| 1 | 0.936809 | 3.852075 | 4.112 | 0.000 | 0.000 |
| 3 | 1.368395 | 4.729604 | 3.456 | 0.000 | 0.000 |
| 5 | 1.372540 | 4.756411 | 3.465 | 0.000 | 0.000 |
| 8 | 1.413165 | 4.586254 | 3.245 | 0.000 | 0.000 |
| 12 | 1.327590 | 4.728335 | 3.562 | 0.000 | 0.000 |

Interpretation: r_v3 amplifies the existing two-path margin by roughly
3.2-4.1x after z leaves zero. This is consistent with the known structural
asymmetry of the negative-control topology: path E has 3 hops, path F has
2 hops. When overloaded links are penalized more strongly, the extra hop makes
the E/F ranking more decisive. The negative control still serves its guardrail
purpose, but its mechanism should not be extrapolated directly to routing3,
whose three paths are iso-structural.

The three-seed table also shows that this two-path negative control is not
sensitive to the reward redesign in its headline metric: r_v2 and r_v3 have the
same `gap`, `decision_regret`, and `n_disagree` for every seed. What changes is
the margin scale. Therefore the correct claim is narrow:

> The two-path negative control confirms that r_v3 does not create a false
> positive on a rejected topology, but it does not distinguish r_v2 from r_v3
> because failure is dominated by structural asymmetry and saturation.

For `z >= 3`, q_margin saturates near a constant. This is consistent with the
two-path drift dynamics clipping offered load at its configured bounds: after
enough steps, the stage approaches an absorbing/saturated regime where E/F
differ mostly by hop-count structure. That makes `disagree = 0` exact rather
than merely small.

## Decision

`r_v3` passes the negative-control guardrail: the two-path stage still fails by
a wide margin (`lower CI95 = 0.003222 < 0.10`). It is therefore allowed to move
to Phase 14C.2 calibration, but this is not yet a positive result for routing3
or sync.

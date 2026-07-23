# Phase 11 Rev - Dynamic-heavy Results

**Ngay chay:** 2026-07-23

## Pre-train Controls

`LOAD_CFG_DYNAMIC` passed the pre-registered headroom gate:

- heavy probe: `python3 measurements/probe_aoi_dependence.py --design dynamic --cases 400 --mc-samples 200`
- observed gap: `0.315-0.333` for `z>=1`
- gate: `gap >= 0.25` -> GO

Masked-branch eval control was clean:

- command: `python3 measurements/probe_agent_reads_aoi.py --ckpt frozen_policies/huong_a/policy_mask_s0.pt --mask-input`
- all four hand states reported `swing = 0.0000`
- conclusion: raw nonzero-AoI flips in the mask checkpoint were OOD artifacts,
  not leakage under the actual masked evaluation path.

Golden reproducibility passed for the dynamic AoI config:

- `ROUTE_REPRO_CONFIG=rl/routing/configs/train_r_dyn_aoi.yaml`
- `ROUTE_REPRO_ROOT_PREFIX=results/repro_dyn`
- same seed produced identical `train_return` sequence.

## Training Run

Command:

```bash
./scripts/train_ablation_10run.sh train_r_dyn results/ablation_dyn
```

Outputs:

- `results/ablation_dyn/aoi/r_seed0..4_*/`
- `results/ablation_dyn/mask/r_seed0..4_*/`
- `results/ablation_dyn/train_log.txt`

Manifest verification passed:

- 10 `train.json` files found
- branches: 5 AoI, 5 mask
- seeds: `0..4` in each branch
- single `link_model_version`
- single `link_model_sha256`
- paired train seeds and z choices

Each training run completed in about `26.4-26.9s`; all reported baseline drift
`0.0000 <= 0.04`.

## Full-route Z-sweep

Commands:

```bash
python3 scripts/eval_ablation_zsweep.py \
  --root results/ablation_dyn \
  --out results/ablation_dyn/zsweep.csv
python3 scripts/analyze_ablation.py \
  --csv results/ablation_dyn/zsweep.csv \
  --out results/ablation_dyn/analysis_summary.txt \
  --stats-csv results/ablation_dyn/analysis_by_z.csv
```

Primary return channel:

| z | AoI(s) | ret_aoi | ret_mask | diff | p | verdict |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 0.00 | 4.053 | 4.078 | -0.0241 | 0.2779 | tie |
| 1 | 0.50 | 4.066 | 4.078 | -0.0118 | 0.3595 | tie |
| 3 | 1.50 | 4.062 | 4.077 | -0.0154 | 0.0668 | tie |
| 5 | 2.50 | 3.822 | 3.838 | -0.0162 | 0.0081 | mask higher |
| 8 | 4.00 | 4.055 | 4.057 | -0.0014 | 0.9113 | tie |
| 12 | 6.00 | 4.047 | 4.053 | -0.0057 | 0.7956 | tie |

Conclusion: H1 is consistent with a tie at fresh data, but H2 is not supported.
There is no positive high-AoI return advantage in the full-route evaluation.

## Decision-node Paired Probe

Commands:

```bash
python3 scripts/eval_paired.py --scenario dynamic_heavy --mode probe ...
python3 scripts/analyze_eval_paired.py \
  --glob 'results/eval_ablation_dyn/paired_seed*_probe.csv' \
  --cases probe_C,probe_D \
  --out results/eval_ablation_dyn/summary_probe_5seed.csv \
  --seed-out results/eval_ablation_dyn/seed_z_probe_5seed.csv
```

Seed-level z=0-corrected summary:

| z | VoI_raw | VoI_corr | p_corr | AoI_wrong | mask_wrong | targetF | AoI_F | mask_F |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | +0.0035 | +0.0000 | 1.0000 | 0.0260 | 0.0440 | 0.4820 | 0.5080 | 0.5240 |
| 1 | +0.0032 | -0.0003 | 0.6942 | 0.0260 | 0.0440 | 0.4820 | 0.5080 | 0.5240 |
| 3 | +0.0015 | -0.0020 | 0.5325 | 0.0440 | 0.0450 | 0.4820 | 0.5260 | 0.5230 |
| 5 | -0.0176 | -0.0211 | 0.3610 | 0.1730 | 0.1590 | 0.4820 | 0.5790 | 0.5990 |
| 8 | +0.0028 | -0.0007 | 0.9512 | 0.0610 | 0.0630 | 0.4820 | 0.5390 | 0.5350 |
| 12 | +0.0148 | +0.0113 | 0.4388 | 0.0510 | 0.0690 | 0.4820 | 0.5170 | 0.5290 |

Corrected slope: `+0.00078`, `p=0.5143`, `r=0.337`.

Decision-node conclusion: even after removing pre-decision path differences
(`preDiff = 0.0000`), the trained AoI branch does not show a statistically
supported positive stale-data advantage.

## Interpretation

The theoretical headroom gate was necessary but not sufficient. The dynamic
stage created an action-dependence gap, and the old AoI checkpoint proved that
the architecture can react to AoI. However, the 2x5 dynamic-heavy training run
did not turn that headroom into reliable return advantage.

The next diagnosis should focus on optimization/objective mismatch: whether the
learned Q policy is matching the Bayes-aware action implied by the gap probe,
and whether return rewards are too close after both branches converge to mostly
similar F usage around the decision node.

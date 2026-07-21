#!/usr/bin/env python3
"""Probe scenario designs before paying for DQN training.

The goal is to find dynamic scenarios where stale observations are costly:
old data should say a decision link is still below the queue cliff while the
true load has crossed it by the time the route reaches C/D.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, '.')

from rl.routing.link_model import CRITICAL_TO_FULL_RHO_OFFERED
from rl.routing.metrics_r import run_episode, summarize_episode_stats
from rl.routing.oracles import blind_dijkstra, clairvoyant_dijkstra, posthoc_dijkstra
from rl.routing.route_env import RouteEnv
from rl.routing.staleness_r import StalenessWrapper
from rl.routing.topology_r import FREE_LOAD, TOPO, _SCEN_BASE


DEFAULT_NEAR_CLIFFS = (
    (0.40, 0.75),
    (0.70, 0.80),
    (0.80, 0.88),
    (0.85, 0.92),
    (0.88, 0.93),
)
DEFAULT_SAFE_LOADS = ((0.20, 0.40), FREE_LOAD)
DEFAULT_TRENDS = (0.10, 0.15, 0.25)
DEFAULT_Z_VALUES = (2, 4, 6)


def parse_pairs(value: str) -> tuple[tuple[float, float], ...]:
    """Parse '0.80:0.88,0.85:0.92' into load intervals."""
    pairs = []
    for item in str(value).split(','):
        item = item.strip()
        if not item:
            continue
        lo, hi = item.split(':', 1)
        pairs.append((float(lo), float(hi)))
    return tuple(pairs)


def parse_floats(value: str) -> tuple[float, ...]:
    return tuple(float(x.strip()) for x in str(value).split(',') if x.strip())


def parse_ints(value: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in str(value).split(',') if x.strip())


def make_dynamic(near_cliff: tuple[float, float], safe_load: tuple[float, float],
                 trend: float) -> dict:
    """Create mirrored E-rising/F-rising scenarios for one design point."""
    return {
        'S5_E_rising': {
            'base_load': _SCEN_BASE,
            'e_load': tuple(near_cliff),
            'f_load': tuple(safe_load),
            'e_trend': float(trend),
            'f_trend': 0.0,
            'drift_sigma': 0.02,
        },
        'S6_F_rising': {
            'base_load': _SCEN_BASE,
            'e_load': tuple(safe_load),
            'f_load': tuple(near_cliff),
            'e_trend': 0.0,
            'f_trend': float(trend),
            'drift_sigma': 0.02,
        },
    }


def make_env(load_cfg: dict, z: int, seed: int, max_steps: int):
    base = RouteEnv(TOPO, load_cfg=load_cfg, max_steps=max_steps, seed=seed)
    return StalenessWrapper(base, z_steps_choices=(int(z),))


def cob_at(scenarios: dict, z: int, eval_seeds: range, max_steps: int,
           offered_load_max: float | None) -> dict:
    """Measure clairvoyant-vs-blind oracle gap for one scenario design."""
    load_cfg = {
        'scenarios': scenarios,
        'scenario_mix': tuple(scenarios),
    }
    if offered_load_max is not None:
        load_cfg['offered_load_max'] = float(offered_load_max)
    clair_rows = []
    blind_rows = []
    for seed in eval_seeds:
        clair_env = make_env(load_cfg, z=z, seed=seed, max_steps=max_steps)
        blind_env = make_env(load_cfg, z=z, seed=seed, max_steps=max_steps)
        clair_rows.append(
            run_episode(
                clair_env,
                clairvoyant_dijkstra,
                seed=seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )
        blind_rows.append(
            run_episode(
                blind_env,
                blind_dijkstra,
                seed=seed,
                target_fn=posthoc_dijkstra,
            ).as_dict()
        )

    clair = summarize_episode_stats(clair_rows)
    blind = summarize_episode_stats(blind_rows)
    return {
        'aoi_mean_s': float(blind['aoi_mean_s']),
        'clair_return': float(clair['return']),
        'blind_return': float(blind['return']),
        'cost_of_blindness': float(clair['return'] - blind['return']),
        'wrong_excess': float(blind['wrong_rate'] - clair['wrong_rate']),
        'clair_wrong_rate': float(clair['wrong_rate']),
        'blind_wrong_rate': float(blind['wrong_rate']),
    }


def write_csv(path: str | None, rows: list[dict]) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        'near_cliff',
        'safe_load',
        'trend',
        'offered_load_max',
        'z',
        'aoi_mean_s',
        'clair_return',
        'blind_return',
        'cost_of_blindness',
        'wrong_excess',
        'clair_wrong_rate',
        'blind_wrong_rate',
    ]
    with open(out, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'\n[CSV] wrote {out}')


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--near-cliffs',
        '--near_cliffs',
        default=','.join(f'{lo}:{hi}' for lo, hi in DEFAULT_NEAR_CLIFFS),
        dest='near_cliffs',
        help='comma list of low:high intervals, e.g. 0.80:0.88,0.85:0.92',
    )
    parser.add_argument(
        '--safe-loads',
        '--safe_loads',
        default=','.join(f'{lo}:{hi}' for lo, hi in DEFAULT_SAFE_LOADS),
        dest='safe_loads',
        help='comma list of low:high intervals for the non-rising side',
    )
    parser.add_argument('--trends', default=','.join(str(x) for x in DEFAULT_TRENDS))
    parser.add_argument('--offered-load-maxes', '--offered_load_maxes',
                        default='default,1.6', dest='offered_load_maxes',
                        help='comma list like default,1.6,2.0')
    parser.add_argument('--z-values', '--z_values',
                        default=','.join(str(x) for x in DEFAULT_Z_VALUES),
                        dest='z_values')
    parser.add_argument('--eval-seeds', '--eval_seeds', type=int, default=50,
                        dest='eval_seeds')
    parser.add_argument('--eval-seed-start', '--eval_seed_start', type=int,
                        default=0, dest='eval_seed_start')
    parser.add_argument('--max-steps', '--max_steps', type=int, default=15,
                        dest='max_steps')
    parser.add_argument('--target-cob', '--target_cob', type=float, default=0.5,
                        dest='target_cob')
    parser.add_argument('--out', default='results/debug/probe_cob_design.csv')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    near_cliffs = parse_pairs(args.near_cliffs)
    safe_loads = parse_pairs(args.safe_loads)
    trends = parse_floats(args.trends)
    offered_maxes = []
    for item in str(args.offered_load_maxes).split(','):
        item = item.strip()
        if not item:
            continue
        offered_maxes.append(None if item == 'default' else float(item))
    z_values = parse_ints(args.z_values)
    eval_seeds = range(
        int(args.eval_seed_start),
        int(args.eval_seed_start) + int(args.eval_seeds),
    )

    print('Probe scenario designs before training')
    print(f'queue cliff ~= {CRITICAL_TO_FULL_RHO_OFFERED:.4f}')
    print(f'eval_seeds = {eval_seeds.start}..{eval_seeds.stop - 1}')
    print(
        f"{'near_cliff':>14} {'safe_load':>14} {'trend':>6} {'cap':>7} "
        f"{'z':>3} {'AoI(s)':>7} {'clair':>9} {'blind':>9} "
        f"{'CoB':>9} {'wrong_ex':>9}"
    )

    rows = []
    design_summaries = []
    for near in near_cliffs:
        for safe in safe_loads:
            for trend in trends:
                for offered_max in offered_maxes:
                    scenarios = make_dynamic(near, safe, trend)
                    design_rows = []
                    for z in z_values:
                        metrics = cob_at(
                            scenarios,
                            z=z,
                            eval_seeds=eval_seeds,
                            max_steps=args.max_steps,
                            offered_load_max=offered_max,
                        )
                        row = {
                            'near_cliff': f'{near[0]:.3f}:{near[1]:.3f}',
                            'safe_load': f'{safe[0]:.3f}:{safe[1]:.3f}',
                            'trend': float(trend),
                            'offered_load_max': (
                                'default' if offered_max is None else float(offered_max)
                            ),
                            'z': int(z),
                            **metrics,
                        }
                        rows.append(row)
                        design_rows.append(row)
                        cap = 'default' if offered_max is None else f'{offered_max:.2f}'
                        print(
                            f"{str(tuple(round(x, 3) for x in near)):>14} "
                            f"{str(tuple(round(x, 3) for x in safe)):>14} "
                            f"{trend:6.3f} {cap:>7} {z:3d} "
                            f"{metrics['aoi_mean_s']:7.2f} "
                            f"{metrics['clair_return']:9.3f} "
                            f"{metrics['blind_return']:9.3f} "
                            f"{metrics['cost_of_blindness']:9.3f} "
                            f"{metrics['wrong_excess']:9.3f}"
                        )

                    best = max(design_rows, key=lambda row: row['cost_of_blindness'])
                    design_summaries.append(best)
                    flag = (
                        '  <== target met'
                        if best['cost_of_blindness'] >= args.target_cob else ''
                    )
                    print(
                        f"{'':>14} {'':>14} {'':>6} {'':>7} {'max':>3} "
                        f"{'':>7} {'':>9} {'':>9} "
                        f"{best['cost_of_blindness']:9.3f}{flag}"
                    )
                    print()

    write_csv(args.out, rows)

    best = max(design_summaries, key=lambda row: row['cost_of_blindness'])
    print('Best design:')
    print(
        f"  near_cliff={best['near_cliff']} safe_load={best['safe_load']} "
        f"trend={best['trend']:.3f} cap={best['offered_load_max']} "
        f"best_z={best['z']} CoB={best['cost_of_blindness']:.4f}"
    )
    if best['cost_of_blindness'] >= args.target_cob:
        print(f'  PASS: CoB >= target {args.target_cob:.3f}; worth training.')
    else:
        print(f'  FAIL: CoB < target {args.target_cob:.3f}; redesign before training.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

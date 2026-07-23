#!/usr/bin/env python3
"""Plot routing training dashboards from train_r.py outputs.

Examples:
    python scripts/plot_training.py results/train_scenario/r_seed0_...
    python scripts/plot_training.py --runs-glob 'results/train_scenario/r_seed*'
"""

import argparse
import csv
import glob
import json
import os
import sys

import numpy as np

os.environ.setdefault(
    'MPLCONFIGDIR',
    os.path.join('/tmp', 'matplotlib-%s' % os.getuid()),
)
os.makedirs(os.environ['MPLCONFIGDIR'], exist_ok=True)

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent  # noqa: E402
from rl.routing_2path.route_env import RouteEnv  # noqa: E402
from rl.routing_2path.state_r import MAX_NEIGHBORS, R_STATE_DIM  # noqa: E402
from rl.routing_2path.topology_r import SCENARIOS_TRAIN, TOPO_V2  # noqa: E402


def read_csv(path):
    with open(path, encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def read_json(path):
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def as_float(row, key, default=np.nan):
    value = row.get(key, '')
    if value in ('', None):
        return default
    return float(value)


def moving_average(values, window):
    if len(values) < window:
        return None
    weights = np.ones(int(window), dtype=float) / float(window)
    return np.convolve(np.asarray(values, dtype=float), weights, mode='valid')


def infer_seed(meta, run_dir):
    if 'agent_seed' in meta:
        return int(meta['agent_seed'])
    name = os.path.basename(os.path.normpath(run_dir))
    if name.startswith('r_seed'):
        return int(name.split('_', 1)[0].replace('r_seed', ''))
    raise ValueError('cannot infer agent seed from %s' % run_dir)


def latest_run_dirs(pattern, expected_seeds=(0, 1, 2, 3, 4)):
    by_seed = {}
    for run_dir in sorted(glob.glob(pattern)):
        if not os.path.isdir(run_dir):
            continue
        train_json = os.path.join(run_dir, 'train.json')
        model_path = os.path.join(run_dir, 'model.pt')
        episodes_path = os.path.join(run_dir, 'episodes.csv')
        eval_path = os.path.join(run_dir, 'eval.csv')
        if not all(os.path.exists(p) for p in (
                train_json, model_path, episodes_path, eval_path)):
            continue
        meta = read_json(train_json)
        seed = infer_seed(meta, run_dir)
        by_seed.setdefault(seed, []).append(run_dir)

    selected = []
    for seed in expected_seeds:
        candidates = by_seed.get(seed, [])
        if not candidates:
            continue
        candidates.sort(
            key=lambda path: os.path.getmtime(os.path.join(path, 'train.json')),
            reverse=True,
        )
        selected.append(candidates[0])
    return selected


def default_run_dir():
    candidates = latest_run_dirs('results/train_scenario/r_seed*')
    if candidates:
        return sorted(candidates, key=os.path.getmtime)[-1]
    candidates = [
        path for path in glob.glob('results/train_scenario/r_seed*')
        if os.path.isdir(path)
    ]
    if not candidates:
        raise SystemExit(
            'No run_dir provided and no runs found in results/train_scenario/.'
        )
    return sorted(candidates, key=os.path.getmtime)[-1]


def e_usage_by_scenario(model_path, cfg, episodes=20, seed0=700):
    """Measure how often the trained agent routes through E per scenario."""
    agent = DQNAgent(R_STATE_DIM, MAX_NEIGHBORS, cfg)
    agent.load(model_path)
    agent.main_net.eval()
    agent.target_net.eval()

    out = {}
    for name, scenario_cfg in SCENARIOS_TRAIN.items():
        used_e = 0
        for offset in range(int(episodes)):
            env = RouteEnv(
                TOPO_V2,
                load_cfg=scenario_cfg,
                max_steps=cfg['env']['max_steps'],
                seed=seed0 + offset,
            )
            obs, info = env.reset(seed=seed0 + offset)
            done = False
            while not done:
                action = agent.select_action(
                    obs,
                    epsilon=0.0,
                    valid_mask=env.valid_mask(),
                )
                obs, _reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
            used_e += int('E' in info['path'])
        out[name] = used_e / max(int(episodes), 1)
    return out


def load_run(run_dir):
    return {
        'run_dir': run_dir,
        'episodes': read_csv(os.path.join(run_dir, 'episodes.csv')),
        'eval': read_csv(os.path.join(run_dir, 'eval.csv')),
        'meta': read_json(os.path.join(run_dir, 'train.json')),
        'model_path': os.path.join(run_dir, 'model.pt'),
    }


def run_summary(run_dir, eusage_episodes):
    data = load_run(run_dir)
    meta = data['meta']
    cfg = meta['config']
    episodes = data['episodes']
    eval_rows = data['eval']
    train_returns = [as_float(row, 'train_return') for row in episodes]
    eval_returns = [as_float(row, 'return') for row in eval_rows]
    eusage = e_usage_by_scenario(data['model_path'], cfg, episodes=eusage_episodes)
    delta = eusage.get('S1_viaE_better', 0.0) - eusage.get('S2_direct_better', 0.0)
    return {
        'run_dir': run_dir,
        'seed': infer_seed(meta, run_dir),
        'run_id': meta.get('run_id', os.path.basename(run_dir)),
        'train_final_ma25': float(np.nanmean(train_returns[-25:])),
        'eval_final': float(eval_returns[-1]) if eval_returns else np.nan,
        'ospf_return': meta.get('baseline_start', {})
        .get('ospf_calibrated', {})
        .get('return'),
        'eusage': eusage,
        'delta_s1_s2': float(delta),
    }


def plot_single(run_dir, eusage_episodes=20):
    data = load_run(run_dir)
    meta = data['meta']
    cfg = meta['config']
    episodes = data['episodes']
    eval_rows = data['eval']

    ep = [int(row['episode']) for row in episodes]
    train_ret = [as_float(row, 'train_return') for row in episodes]
    epsilon = [as_float(row, 'epsilon') for row in episodes]
    eval_ep = [int(row['episode']) for row in eval_rows]
    eval_ret = [as_float(row, 'return') for row in eval_rows]
    eusage = e_usage_by_scenario(data['model_path'], cfg, episodes=eusage_episodes)

    baseline = meta.get('baseline_start', {}).get('ospf_calibrated', {})
    baseline_return = baseline.get('return')

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle('Training dashboard: %s' % os.path.basename(run_dir), fontsize=13)

    ax = axes[0, 0]
    ax.plot(ep, train_ret, alpha=0.22, color='tab:blue', label='raw')
    smooth = moving_average(train_ret, 25)
    if smooth is not None:
        ax.plot(ep[24:], smooth, color='tab:blue', lw=2, label='MA-25')
    if baseline_return is not None:
        ax.axhline(
            float(baseline_return),
            color='tab:orange',
            ls='--',
            label='ospf baseline',
        )
    ax.set_title('Learning curve')
    ax.set_xlabel('episode')
    ax.set_ylabel('return')
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    ax.plot(ep, epsilon, color='tab:green')
    ax.axhline(0.1, color='gray', ls=':', label='eps=0.1')
    ax.set_title('Epsilon decay')
    ax.set_xlabel('episode')
    ax.set_ylabel('epsilon')
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    names = list(eusage)
    values = [eusage[name] for name in names]
    want_high = {'S1_viaE_better', 'S3_both_free'}
    colors = ['tab:green' if name in want_high else 'tab:red' for name in names]
    labels = [
        name.replace('_better', '').replace('_', '\n')
        for name in names
    ]
    bars = ax.bar(labels, values, color=colors, alpha=0.75)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            value + 0.02,
            '%.2f' % value,
            ha='center',
            fontsize=9,
        )
    delta = eusage['S1_viaE_better'] - eusage['S2_direct_better']
    ax.text(
        0.5,
        1.05,
        'delta(S1-S2)=%.2f' % delta,
        transform=ax.transAxes,
        ha='center',
        fontsize=10,
        color='green' if delta > 0.5 else 'red',
        weight='bold',
    )
    ax.set_ylim(0.0, 1.15)
    ax.set_title('E usage by scenario')
    ax.set_ylabel('fraction through E')

    ax = axes[1, 1]
    ax.plot(eval_ep, eval_ret, marker='o', ms=3, color='tab:purple')
    if baseline_return is not None:
        ax.axhline(
            float(baseline_return),
            color='tab:orange',
            ls='--',
            label='ospf baseline',
        )
        ax.legend(fontsize=8)
    ax.set_title('Eval return, z=0')
    ax.set_xlabel('episode')
    ax.set_ylabel('return')

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_path = os.path.join(run_dir, 'dashboard.png')
    fig.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close(fig)

    print('saved: %s' % out_path)
    print('summary:')
    print('  final train return MA-25: %.3f' % float(np.nanmean(train_ret[-25:])))
    print('  final eval return:        %.3f' % float(eval_ret[-1]))
    print('  ospf baseline:            %s' % baseline_return)
    print('  delta(S1-S2):             %.2f' % delta)
    for name, value in eusage.items():
        print('  E_usage %-18s %.2f' % (name + ':', value))
    return out_path


def plot_many(run_dirs, out_path, eusage_episodes=20):
    summaries = [run_summary(run_dir, eusage_episodes) for run_dir in run_dirs]
    summaries.sort(key=lambda row: row['seed'])

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle('Five-seed routing scenario dashboard', fontsize=14)

    ax = axes[0, 0]
    all_curves = []
    max_len = 0
    for summary in summaries:
        data = load_run(summary['run_dir'])
        ep = [int(row['episode']) for row in data['episodes']]
        train_ret = [as_float(row, 'train_return') for row in data['episodes']]
        smooth = moving_average(train_ret, 25)
        if smooth is None:
            continue
        smooth_ep = ep[24:]
        max_len = max(max_len, len(smooth))
        all_curves.append(np.asarray(smooth, dtype=float))
        ax.plot(smooth_ep, smooth, alpha=0.35, lw=1.2,
                label='seed %d' % summary['seed'])
    if all_curves:
        min_len = min(len(curve) for curve in all_curves)
        mean_curve = np.mean([curve[-min_len:] for curve in all_curves], axis=0)
        mean_ep = list(range(max_len - min_len + 25, max_len + 25))
        ax.plot(mean_ep, mean_curve, color='black', lw=2.2, label='mean')
    ax.set_title('Learning curves, MA-25')
    ax.set_xlabel('episode')
    ax.set_ylabel('return')
    ax.legend(fontsize=7, ncol=2)

    ax = axes[0, 1]
    seeds = [row['seed'] for row in summaries]
    eval_final = [row['eval_final'] for row in summaries]
    bars = ax.bar([str(seed) for seed in seeds], eval_final, color='tab:purple',
                  alpha=0.75)
    for bar, value in zip(bars, eval_final):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value, '%.2f' % value,
                ha='center', va='bottom', fontsize=8)
    baseline = next(
        (row['ospf_return'] for row in summaries if row['ospf_return'] is not None),
        None,
    )
    if baseline is not None:
        ax.axhline(float(baseline), color='tab:orange', ls='--',
                   label='ospf baseline')
        ax.legend(fontsize=8)
    ax.set_title('Final eval return by seed')
    ax.set_xlabel('agent seed')
    ax.set_ylabel('return')

    ax = axes[1, 0]
    scenario_names = list(SCENARIOS_TRAIN)
    means = []
    stds = []
    for name in scenario_names:
        vals = [row['eusage'][name] for row in summaries]
        means.append(float(np.mean(vals)))
        stds.append(float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0)
    colors = [
        'tab:green' if name in {'S1_viaE_better', 'S3_both_free'} else 'tab:red'
        for name in scenario_names
    ]
    labels = [
        name.replace('_better', '').replace('_', '\n')
        for name in scenario_names
    ]
    bars = ax.bar(labels, means, yerr=stds, capsize=4, color=colors, alpha=0.75)
    for bar, value in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.03,
                '%.2f' % value, ha='center', fontsize=8)
    ax.set_ylim(0.0, 1.15)
    ax.set_title('Mean E usage by scenario')
    ax.set_ylabel('fraction through E')

    ax = axes[1, 1]
    deltas = [row['delta_s1_s2'] for row in summaries]
    bars = ax.bar([str(seed) for seed in seeds], deltas, color='tab:blue',
                  alpha=0.75)
    ax.axhline(0.5, color='tab:red', ls='--', label='pass line')
    for bar, value in zip(bars, deltas):
        ax.text(bar.get_x() + bar.get_width() / 2.0, value + 0.02,
                '%.2f' % value, ha='center', fontsize=8)
    ax.set_ylim(0.0, 1.15)
    ax.set_title('delta(S1-S2) by seed')
    ax.set_xlabel('agent seed')
    ax.set_ylabel('delta')
    ax.legend(fontsize=8)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=120, bbox_inches='tight')
    plt.close(fig)

    print('saved: %s' % out_path)
    print('five-seed summary:')
    print('  seeds: %s' % ', '.join(str(row['seed']) for row in summaries))
    print('  eval return mean: %.3f' % float(np.mean(eval_final)))
    print('  eval return std:  %.3f' % float(np.std(eval_final, ddof=1)))
    print('  delta mean:        %.2f' % float(np.mean(deltas)))
    for row in summaries:
        print(
            '  seed %d: eval=%.3f delta=%.2f dir=%s'
            % (row['seed'], row['eval_final'], row['delta_s1_s2'], row['run_dir'])
        )
    return out_path


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('run_dir', nargs='?', default=None)
    parser.add_argument(
        '--runs-glob',
        default=None,
        help='plot aggregate dashboard from latest usable runs per seed',
    )
    parser.add_argument('--out', default=None)
    parser.add_argument('--eusage-episodes', type=int, default=20)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.runs_glob:
        run_dirs = latest_run_dirs(args.runs_glob)
        if len(run_dirs) < 5:
            raise SystemExit(
                'Need one usable run for each seed 0..4, found %d from %s'
                % (len(run_dirs), args.runs_glob)
            )
        out_path = args.out
        if out_path is None:
            common = os.path.commonpath([os.path.dirname(path) for path in run_dirs])
            out_path = os.path.join(common, 'dashboard_5seed.png')
        plot_many(run_dirs, out_path, eusage_episodes=args.eusage_episodes)
        return 0

    run_dir = args.run_dir or default_run_dir()
    plot_single(run_dir, eusage_episodes=args.eusage_episodes)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

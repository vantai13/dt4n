#!/usr/bin/env python3
"""A2 plotting helpers for evaluation and training artifacts."""

import os

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402


POLICY_COLOR = {
    'agent': '#4a3aa7',
    'greedy_strong': '#1baf7a',
    'greedy': '#73726c',
    'equal': '#eda100',
    'noop': '#e34948',
    'myopic_oracle': '#008300',
}


def bar_by_scenario(results, out_path, metric='return'):
    """Grouped bar chart by scenario and policy, with CI95 error bars."""
    scenarios = list(results.keys())
    if not scenarios:
        raise ValueError('results is empty')
    policies = list(next(iter(results.values())).keys())
    n_s, n_p = len(scenarios), len(policies)

    fig, ax = plt.subplots(figsize=(max(9, n_s * 2.2), 5))
    width = 0.8 / max(n_p, 1)

    for i, policy in enumerate(policies):
        xs = [j + i * width - 0.4 + width / 2 for j in range(n_s)]
        ys = [results[s][policy]['mean'] or 0.0 for s in scenarios]
        errs = [results[s][policy]['ci95'] or 0.0 for s in scenarios]
        ax.bar(
            xs,
            ys,
            width,
            yerr=errs,
            capsize=3,
            label=policy,
            color=POLICY_COLOR.get(policy, '#888780'),
        )

    ax.set_xticks(range(n_s))
    ax.set_xticklabels(scenarios, rotation=15, ha='right', fontsize=9)
    ax.set_ylabel(metric)
    ax.set_title('%s by scenario (error bars = CI95)' % metric)
    ax.legend(fontsize=8, ncol=3)
    ax.grid(axis='y', alpha=0.3)
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return out_path


def gap_heatmap(results, out_path, ref='agent'):
    """Heatmap of mean gap = ref policy - each baseline."""
    scenarios = list(results.keys())
    if not scenarios:
        raise ValueError('results is empty')
    first = next(iter(results.values()))
    if ref not in first:
        raise ValueError('reference policy %r not found' % ref)
    policies = [p for p in first.keys() if p != ref]

    grid = []
    for scenario in scenarios:
        row = []
        for policy in policies:
            ref_mean = results[scenario][ref]['mean']
            base_mean = results[scenario][policy]['mean']
            row.append(
                ref_mean - base_mean
                if ref_mean is not None and base_mean is not None
                else 0.0
            )
        grid.append(row)

    fig, ax = plt.subplots(
        figsize=(max(7, len(policies) * 1.6),
                 max(3.5, len(scenarios) * 0.6))
    )
    im = ax.imshow(grid, cmap='RdYlGn', aspect='auto', vmin=-1.5, vmax=1.5)
    ax.set_xticks(range(len(policies)))
    ax.set_xticklabels(policies, rotation=20, ha='right', fontsize=9)
    ax.set_yticks(range(len(scenarios)))
    ax.set_yticklabels(scenarios, fontsize=9)

    for i in range(len(scenarios)):
        for j in range(len(policies)):
            ax.text(j, i, '%+.2f' % grid[i][j], ha='center', va='center',
                    fontsize=9)

    ax.set_title('gap = %s - baseline (green = %s better)' % (ref, ref))
    fig.colorbar(im, ax=ax, shrink=0.8)
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return out_path


def learning_curve(train_log, out_dir):
    """Write train and eval curve PNGs from A2 training log rows."""
    if not train_log:
        raise ValueError('train_log is empty')
    os.makedirs(out_dir, exist_ok=True)
    episodes = [row['episode'] for row in train_log]
    paths = []

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.plot(
        episodes,
        [row.get('train_return') for row in train_log],
        'o-',
        color=POLICY_COLOR['agent'],
        label='train_return',
    )
    ax1.set_xlabel('episode')
    ax1.set_ylabel('train return', color=POLICY_COLOR['agent'])
    ax1.grid(alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(
        episodes,
        [row.get('epsilon') for row in train_log],
        's--',
        color=POLICY_COLOR['equal'],
        label='epsilon',
    )
    ax2.plot(
        episodes,
        [row.get('train_loss') or 0.0 for row in train_log],
        '^:',
        color=POLICY_COLOR['noop'],
        label='loss',
    )
    ax2.set_ylabel('epsilon / loss')
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [line.get_label() for line in lines],
               loc='center right', fontsize=8)
    plt.title('Train curve')
    path = os.path.join(out_dir, 'train_curve.png')
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
    paths.append(path)

    plt.figure(figsize=(9, 5))
    for key, label, style, color_key in [
        ('agent_return', 'agent (RL)', 'o-', 'agent'),
        ('greedy_strong_return', 'greedy_strong', 's-.', 'greedy_strong'),
        ('greedy_return', 'greedy', '--', 'greedy'),
        ('myopic_oracle_return', 'myopic oracle', '-', 'myopic_oracle'),
        ('noop_return', 'noop', ':', 'noop'),
    ]:
        if key in train_log[0]:
            plt.plot(
                episodes,
                [row.get(key) for row in train_log],
                style,
                color=POLICY_COLOR[color_key],
                label=label,
            )
    plt.xlabel('episode')
    plt.ylabel('eval return')
    plt.title('Eval curve')
    plt.legend(fontsize=8)
    plt.grid(alpha=0.3)
    path = os.path.join(out_dir, 'eval_curve.png')
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
    paths.append(path)

    return paths

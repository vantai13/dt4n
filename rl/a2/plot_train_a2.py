#!/usr/bin/env python3
"""Write CSV and SVG reports from an A2 train artifact.

The SVG writer is intentionally stdlib-only, so EC2 does not need matplotlib.
"""

import argparse
import csv
import json
import os


COLORS = {
    'train': '#2563eb',
    'agent': '#7c3aed',
    'myopic': '#16a34a',
    'greedy': '#64748b',
    'greedy_strong': '#0891b2',
    'equal': '#f59e0b',
    'noop': '#ef4444',
    'gap': '#0f766e',
    'loss': '#db2777',
}


def sidecar_path(path, suffix):
    root, _ext = os.path.splitext(path)
    return root + suffix


def load_artifact(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def write_csv(path, rows, fieldnames):
    if not rows:
        return None
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _clean_number(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _series(rows, x_key, y_key):
    pts = []
    for row in rows:
        x = _clean_number(row.get(x_key))
        y = _clean_number(row.get(y_key))
        if x is not None and y is not None:
            pts.append((x, y))
    return pts


def _polyline(points, sx, sy):
    return ' '.join('%.1f,%.1f' % (sx(x), sy(y)) for x, y in points)


def _escape(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def write_svg(path, artifact):
    episode_rows = artifact.get('episode_log') or []
    eval_rows = artifact.get('log') or []
    baselines = artifact.get('baselines') or {}

    all_points = []
    train_return = _series(episode_rows, 'episode', 'train_return')
    train_loss = _series(episode_rows, 'episode', 'train_loss')
    eval_agent = _series(eval_rows, 'episode', 'agent_return')
    eval_gap = _series(eval_rows, 'episode', 'agent_minus_greedy')
    eval_gap_strong = _series(eval_rows, 'episode', 'agent_minus_greedy_strong')
    all_points.extend(train_return)
    all_points.extend(eval_agent)

    if not all_points and eval_rows:
        # Old artifacts only have eval rows. Plot their train_return too.
        train_return = _series(eval_rows, 'episode', 'train_return')
        all_points.extend(train_return)

    if not all_points:
        raise ValueError('artifact has no train/eval points to plot')

    max_ep = max(x for x, _ in all_points)
    returns = [y for _, y in all_points]
    for name in ('myopic_oracle', 'greedy', 'greedy_strong', 'equal', 'noop'):
        row = baselines.get(name) or {}
        val = _clean_number(row.get('return'))
        if val is not None:
            returns.append(val)
    y_min = min(returns)
    y_max = max(returns)
    pad = max(0.5, (y_max - y_min) * 0.12)
    y_min -= pad
    y_max += pad

    width, height = 1100, 700
    left, right, top, bottom = 82, 34, 58, 84
    plot_w = width - left - right
    plot_h = height - top - bottom

    def sx(x):
        return left + (float(x) / max(max_ep, 1.0)) * plot_w

    def sy(y):
        return top + (y_max - float(y)) / max(y_max - y_min, 1e-9) * plot_h

    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' %
                 (width, height, width, height))
    lines.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    title = '%s A2 training (%s)' % (
        os.path.basename(path), artifact.get('mode', 'unknown'))
    lines.append('<text x="%d" y="34" font-family="sans-serif" font-size="22" font-weight="700">%s</text>' %
                 (left, _escape(title)))

    # Grid and axes.
    for i in range(6):
        y = top + i * plot_h / 5.0
        value = y_max - i * (y_max - y_min) / 5.0
        lines.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#e5e7eb"/>' %
                     (left, y, width - right, y))
        lines.append('<text x="%d" y="%.1f" font-family="monospace" font-size="12" text-anchor="end" fill="#475569">%.2f</text>' %
                     (left - 10, y + 4, value))
    for i in range(6):
        x = left + i * plot_w / 5.0
        ep = i * max_ep / 5.0
        lines.append('<line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="#f1f5f9"/>' %
                     (x, top, x, height - bottom))
        lines.append('<text x="%.1f" y="%d" font-family="monospace" font-size="12" text-anchor="middle" fill="#475569">%d</text>' %
                     (x, height - bottom + 22, int(round(ep))))
    lines.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#0f172a" stroke-width="1.2"/>' %
                 (left, height - bottom, width - right, height - bottom))
    lines.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#0f172a" stroke-width="1.2"/>' %
                 (left, top, left, height - bottom))
    lines.append('<text x="%d" y="%d" font-family="sans-serif" font-size="13" text-anchor="middle" fill="#334155">episode</text>' %
                 (left + plot_w // 2, height - 28))
    lines.append('<text transform="translate(22,%d) rotate(-90)" font-family="sans-serif" font-size="13" text-anchor="middle" fill="#334155">return</text>' %
                 (top + plot_h // 2))

    # Baselines as horizontal lines.
    baseline_defs = [
        ('myopic_oracle', 'myopic_oracle', COLORS['myopic']),
        ('greedy', 'greedy', COLORS['greedy']),
        ('greedy_strong', 'greedy_strong', COLORS['greedy_strong']),
        ('equal', 'equal', COLORS['equal']),
        ('noop', 'noop', COLORS['noop']),
    ]
    legend = []
    for key, label, color in baseline_defs:
        val = _clean_number((baselines.get(key) or {}).get('return'))
        if val is None:
            continue
        y = sy(val)
        lines.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1.5" stroke-dasharray="7 5"/>' %
                     (left, y, width - right, y, color))
        lines.append('<text x="%d" y="%.1f" font-family="sans-serif" font-size="12" fill="%s">%s %.2f</text>' %
                     (width - right - 135, y - 5, color, label, val))
        legend.append((label, color))

    def add_line(points, color, label, width_px=2.4):
        if not points:
            return
        lines.append('<polyline fill="none" stroke="%s" stroke-width="%.1f" points="%s"/>' %
                     (color, width_px, _polyline(points, sx, sy)))
        for x, y in points:
            lines.append('<circle cx="%.1f" cy="%.1f" r="3" fill="%s"/>' %
                         (sx(x), sy(y), color))
        legend.append((label, color))

    add_line(train_return, COLORS['train'], 'train_return', 1.8)
    add_line(eval_agent, COLORS['agent'], 'eval_agent_return', 3.0)

    # Gap panel in miniature.
    gap_top = height - 58
    gap_points = list(eval_gap) + list(eval_gap_strong)
    if gap_points:
        g_min = min(0.0, min(y for _, y in gap_points))
        g_max = max(0.0, max(y for _, y in gap_points))
        g_pad = max(0.1, (g_max - g_min) * 0.2)
        g_min -= g_pad
        g_max += g_pad

        def gy(y):
            return gap_top - 72 + (g_max - float(y)) / max(g_max - g_min, 1e-9) * 55

        zero_y = gy(0)
        lines.append('<text x="%d" y="%d" font-family="sans-serif" font-size="13" font-weight="700" fill="#334155">agent - baselines</text>' %
                     (left, gap_top - 82))
        lines.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#94a3b8" stroke-dasharray="4 4"/>' %
                     (left, zero_y, width - right, zero_y))
        if eval_gap:
            lines.append('<polyline fill="none" stroke="%s" stroke-width="2.4" points="%s"/>' %
                         (COLORS['gap'], _polyline(eval_gap, sx, gy)))
            for x, y in eval_gap:
                lines.append('<circle cx="%.1f" cy="%.1f" r="3" fill="%s"/>' %
                             (sx(x), gy(y), COLORS['gap']))
        if eval_gap_strong:
            lines.append('<polyline fill="none" stroke="%s" stroke-width="2.4" points="%s"/>' %
                         (COLORS['greedy_strong'], _polyline(eval_gap_strong, sx, gy)))
            for x, y in eval_gap_strong:
                lines.append('<rect x="%.1f" y="%.1f" width="6" height="6" fill="%s"/>' %
                             (sx(x) - 3, gy(y) - 3, COLORS['greedy_strong']))

    # Compact legend.
    lx, ly = left, top - 24
    for label, color in legend[:8]:
        lines.append('<rect x="%d" y="%d" width="12" height="12" fill="%s"/>' %
                     (lx, ly - 10, color))
        lines.append('<text x="%d" y="%d" font-family="sans-serif" font-size="12" fill="#334155">%s</text>' %
                     (lx + 17, ly, _escape(label)))
        lx += 145

    if train_loss:
        loss_path = sidecar_path(path, '.loss.csv')
        write_csv(loss_path, [
            {'episode': int(x), 'train_loss': y} for x, y in train_loss
        ], ['episode', 'train_loss'])

    lines.append('</svg>')
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n')
    return path


def write_reports(json_path, plot_svg=None, episode_csv=None, eval_csv=None):
    artifact = load_artifact(json_path)
    episode_rows = artifact.get('episode_log') or []
    eval_rows = artifact.get('log') or []

    episode_csv = episode_csv or sidecar_path(json_path, '.episodes.csv')
    eval_csv = eval_csv or sidecar_path(json_path, '.eval.csv')
    plot_svg = plot_svg or sidecar_path(json_path, '.svg')

    outputs = {}
    if episode_rows:
        outputs['episode_csv'] = write_csv(
            episode_csv,
            episode_rows,
            ['episode', 'seed', 'epsilon', 'train_return', 'train_loss', 'steps'],
        )
    if eval_rows:
        outputs['eval_csv'] = write_csv(
            eval_csv,
            eval_rows,
            [
                'episode', 'epsilon', 'train_return', 'train_loss',
                'agent_return', 'agent_sat', 'myopic_oracle_return',
                'oracle_return', 'greedy_return', 'greedy_strong_return',
                'equal_return', 'noop_return', 'agent_minus_greedy',
                'agent_minus_greedy_strong', 'agent_minus_myopic_oracle',
            ],
        )
    outputs['plot_svg'] = write_svg(plot_svg, artifact)
    return outputs


def parse_args():
    parser = argparse.ArgumentParser(description='Plot/report A2 train artifact')
    parser.add_argument('artifact', help='train JSON, e.g. results/train/a2_train_dynamic_clean.json')
    parser.add_argument('--plot-svg')
    parser.add_argument('--episode-csv')
    parser.add_argument('--eval-csv')
    return parser.parse_args()


def main():
    args = parse_args()
    outputs = write_reports(
        args.artifact,
        plot_svg=args.plot_svg,
        episode_csv=args.episode_csv,
        eval_csv=args.eval_csv,
    )
    for key, path in outputs.items():
        if path:
            print('%s -> %s' % (key, path))


if __name__ == '__main__':
    main()

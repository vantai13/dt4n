#!/usr/bin/env python3
"""A2 evaluation statistics.

Evaluation should not report only a mean.  A mean hides whether the result is
stable, so this helper returns standard deviation, median, min/max, and a 95%
confidence interval.
"""

import math


def summarize(values, drop_none=True):
    """Return mean/std/median/min/max/ci95 for a numeric sequence."""
    if drop_none:
        vals = [
            float(v)
            for v in values
            if v is not None and not _is_nan(float(v))
        ]
    else:
        vals = [float(v) for v in values]

    n = len(vals)
    if n == 0:
        return {
            'n': 0,
            'mean': None,
            'std': None,
            'median': None,
            'min': None,
            'max': None,
            'ci95': None,
        }

    mean = sum(vals) / n
    if n > 1:
        var = sum((v - mean) ** 2 for v in vals) / (n - 1)
        std = math.sqrt(var)
    else:
        std = 0.0
    ci95 = 1.96 * std / math.sqrt(n) if n > 1 else 0.0

    sorted_vals = sorted(vals)
    mid = n // 2
    if n % 2 == 1:
        median = sorted_vals[mid]
    else:
        median = (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0

    return {
        'n': n,
        'mean': round(mean, 3),
        'std': round(std, 3),
        'median': round(median, 3),
        'min': round(min(vals), 3),
        'max': round(max(vals), 3),
        'ci95': round(ci95, 3),
    }


def significantly_better(stat_a, stat_b):
    """Return whether A is better than B using non-overlapping CI95 bands.

    Returns one of: 'yes', 'no', or 'inconclusive'.
    """
    if stat_a['mean'] is None or stat_b['mean'] is None:
        return 'inconclusive'

    lo_a = stat_a['mean'] - (stat_a['ci95'] or 0)
    hi_a = stat_a['mean'] + (stat_a['ci95'] or 0)
    lo_b = stat_b['mean'] - (stat_b['ci95'] or 0)
    hi_b = stat_b['mean'] + (stat_b['ci95'] or 0)

    if lo_a > hi_b:
        return 'yes'
    if hi_a < lo_b:
        return 'no'
    return 'inconclusive'


def format_stat(stat, pct=False):
    """Format a summarized statistic as 'mean+/-ci95'."""
    if stat['mean'] is None:
        return '-'
    scale = 100.0 if pct else 1.0
    return '%.2f+/-%.2f' % (
        stat['mean'] * scale,
        (stat['ci95'] or 0) * scale,
    )


def _is_nan(x):
    return x != x

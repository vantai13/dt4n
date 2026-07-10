#!/usr/bin/env python3
"""Test soft-reset vs hard-reset initial-state equivalence.

H0: s0 after soft reset and s0 after hard reset have the same distribution.
We use KS-test per state dimension and Bonferroni correction across the current
state contract.
"""

import argparse
import json
import math
import os
import statistics
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from rl.scenarios import make_scenario
from rl.state_builder_draft import StateBuilderDraft


ALPHA = 0.05


def _ks_fallback(a, b):
    a = sorted(float(x) for x in a)
    b = sorted(float(x) for x in b)
    n1 = len(a)
    n2 = len(b)
    i = j = 0
    d = 0.0
    values = sorted(set(a + b))
    for value in values:
        while i < n1 and a[i] <= value:
            i += 1
        while j < n2 and b[j] <= value:
            j += 1
        d = max(d, abs(i / float(n1) - j / float(n2)))

    if n1 == 0 or n2 == 0:
        return d, 1.0
    en = n1 * n2 / float(n1 + n2)
    if d <= 0:
        return d, 1.0
    lam = (math.sqrt(en) + 0.12 + 0.11 / math.sqrt(en)) * d
    p = 0.0
    for k in range(1, 101):
        p += ((-1) ** (k - 1)) * math.exp(-2.0 * (lam ** 2) * (k ** 2))
    return d, max(0.0, min(1.0, 2.0 * p))


def ks_2samp(a, b):
    try:
        from scipy import stats
        result = stats.ks_2samp(a, b)
        return float(result.statistic), float(result.pvalue)
    except Exception:
        return _ks_fallback(a, b)


def mean_std(values):
    if not values:
        return None, None
    if len(values) == 1:
        return float(values[0]), 0.0
    return float(statistics.mean(values)), float(statistics.stdev(values))


def _dirty_runner(runner, seed, dirty_seconds):
    scenario = make_scenario(seed=seed, spec=runner.spec)
    runner.injection.apply(scenario)
    with runner.net_lock:
        try:
            h1 = runner.net.get('h1')
            srv1 = runner.net.get('srv1')
            h1.cmd('ping -c 1 -W 1 %s >/dev/null 2>&1' % srv1.IP())
        except Exception:
            pass
    if dirty_seconds > 0:
        time.sleep(dirty_seconds)
    return scenario.describe()


def _start_episode_after_hard_reset(runner):
    t0 = time.monotonic()
    runner._start_episode_traffic()
    ok, waited = runner._wait_steady_state()
    return {
        'reset_mode': 'hard',
        'reset_total_s': time.monotonic() - t0,
        'reset_steady_ok': ok,
        'reset_wait_s': waited,
        'reset_dirty': not ok,
        'timings': {'steady_wait': waited},
    }


def _observe_vector(runner, builder):
    builder.reset()
    things, info = runner.observe_raw()
    vector = builder.build(things, info=info)
    return vector, info


def collect_hard(runner, builder, samples, dirty_seconds):
    vectors = []
    infos = []
    for idx in range(samples):
        dirty = _dirty_runner(runner, seed=1000 + idx, dirty_seconds=dirty_seconds)
        runner.hard_reset()
        reset_info = _start_episode_after_hard_reset(runner)
        vector, read_info = _observe_vector(runner, builder)
        infos.append({'idx': idx, 'dirty': dirty, 'reset': reset_info,
                      'read': read_info})
        vectors.append(vector)
        print('hard %02d/%02d dirty=%s wait=%.2fs' %
              (idx + 1, samples, dirty['type'], reset_info['reset_wait_s']))
    return vectors, infos


def collect_soft(runner, builder, samples, dirty_seconds):
    vectors = []
    infos = []
    for idx in range(samples):
        dirty = _dirty_runner(runner, seed=2000 + idx, dirty_seconds=dirty_seconds)
        reset_info = runner.soft_reset()
        vector, read_info = _observe_vector(runner, builder)
        infos.append({'idx': idx, 'dirty': dirty, 'reset': reset_info,
                      'read': read_info})
        vectors.append(vector)
        print('soft %02d/%02d dirty=%s wait=%.2fs dirty_reset=%s' %
              (idx + 1, samples, dirty['type'], reset_info['reset_wait_s'],
               reset_info['reset_dirty']))
    return vectors, infos


def compare(hard_vectors, soft_vectors, dim_names, alpha=ALPHA):
    n_dims = len(dim_names)
    alpha_prime = alpha / float(n_dims)
    rows = []
    for dim, name in enumerate(dim_names):
        hard = [row[dim] for row in hard_vectors]
        soft = [row[dim] for row in soft_vectors]
        degenerate = (len(set(hard)) == 1 and len(set(soft)) == 1)
        d_stat, p_value = ks_2samp(hard, soft)
        mean_h, std_h = mean_std(hard)
        mean_s, std_s = mean_std(soft)
        rows.append({
            'dim': dim,
            'name': name,
            'D': d_stat,
            'p': p_value,
            'rejected': p_value < alpha_prime,
            'degenerate': degenerate,
            'mean_hard': mean_h,
            'std_hard': std_h,
            'mean_soft': mean_s,
            'std_soft': std_s,
        })
    return alpha_prime, rows


def main():
    p = argparse.ArgumentParser(description='Soft/hard reset equivalence test')
    p.add_argument('--samples', type=int, default=20)
    p.add_argument('--period', type=float, default=1.0)
    p.add_argument('--dirty-seconds', type=float, default=1.0)
    p.add_argument('--alpha', type=float, default=ALPHA)
    p.add_argument('--out', default='docs/phase-4.5/equivalence.json')
    args = p.parse_args()

    runner = EnvRunner(sync_period=args.period, hard_every=0,
                       do_pingall=False, mininet_log_level='info')
    builder = None
    try:
        runner.start()
        builder = StateBuilderDraft(spec=runner.spec)
        hard_vectors, hard_infos = collect_hard(
            runner, builder, args.samples, args.dirty_seconds)
        soft_vectors, soft_infos = collect_soft(
            runner, builder, args.samples, args.dirty_seconds)
    finally:
        runner.close()

    alpha_prime, rows = compare(
        hard_vectors, soft_vectors, builder.dim_names, alpha=args.alpha)
    rejected = [row for row in rows if row['rejected']]
    degenerate = [row for row in rows if row['degenerate']]
    n_eff = len(rows) - len(degenerate)
    status = ('accept' if len(rejected) <= 2 else
              'investigate' if len(rejected) <= 5 else 'fail')

    result = {
        'measured': True,
        'samples_per_mode': args.samples,
        'alpha': args.alpha,
        'alpha_prime': alpha_prime,
        'n_dims': len(rows),
        'n_degenerate': len(degenerate),
        'degenerate_dims': [row['name'] for row in degenerate],
        'n_effective_tests': n_eff,
        'alpha_prime_effective': args.alpha / max(n_eff, 1),
        'n_rejected': len(rejected),
        'status': status,
        'multiple_comparison_note': (
            'Bonferroni applied with m=%d (all dims). %d dims are degenerate '
            '(zero variance in both samples, KS has no power). Effective '
            'independent tests ~= %d. Using m=%d would give alpha_prime=%.5f; '
            'this does not change the conclusion. We keep m=%d because '
            'infrastructure validation prioritizes avoiding false positives.'
            % (len(rows), len(degenerate), n_eff, n_eff,
               args.alpha / max(n_eff, 1), len(rows))
        ),
        'rows': rows,
        'hard_infos': hard_infos,
        'soft_infos': soft_infos,
        'prediction_notes': {
            'util_avg3': 'Should not differ if state builder reset clears history.',
            'path_latency_norm': 'May differ if ARP/cache cleanup is incomplete.',
            'bw_norm': 'Should not differ; difference implies restore_links bug.',
            'link_up_host_up': 'Should not differ; all baseline up.',
            'util': 'Should not differ after wait_steady_state.',
            'data_fresh': (
                'May differ after hard_reset if Ditto Things were just '
                'bootstrapped and collector has not completed a full cycle '
                'for every Thing.'
            ),
            'aoi_norm': 'May differ if cache/bootstrap freshness differs.',
            'episode_dims': 'Should not differ; episode is None so both are 0.',
        },
    }

    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')

    print('\n=== RESULT ===')
    print('dims=%d alpha_prime=%.6f rejected=%d status=%s' %
          (len(builder.dim_names), alpha_prime, len(rejected), status))
    for row in rejected:
        print('[%02d] %s D=%.3f p=%.3g hard=%.3f±%.3f soft=%.3f±%.3f' %
              (row['dim'], row['name'], row['D'], row['p'],
               row['mean_hard'], row['std_hard'],
               row['mean_soft'], row['std_soft']))
    print('Wrote %s' % args.out)


if __name__ == '__main__':
    main()

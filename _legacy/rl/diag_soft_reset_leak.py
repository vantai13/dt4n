#!/usr/bin/env python3
"""Gate 1a-tang-2: tai hien state leak qua soft_reset + inject + toggle spam.

Script tang 1 (diag_hard_reset) da loai tru hard_reset. Bug 18-episode phai
nam o thu ma tang 1 khong lam: soft_reset lien tiep + inject scenario + agent
gui lenh, dac biet toggle link.

Chay tren may co Mininet + controller:
    sudo python3 rl/diag_soft_reset_leak.py --episodes 30 --toggle-bias 0.6
"""

import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from mininet.env_runner import EnvRunner
from mininet.topology_meta import load_spec
from rl.action_space import ActionSpace
from rl.twin_env import TwinEnv


class TogglePronePolicy:
    """Random policy nhung thien ve toggle de ep _link_up lech pha nhanh."""

    def __init__(self, action_space_n, toggle_start_idx, toggle_bias, seed=0):
        self.n = int(action_space_n)
        self.toggle_start = int(toggle_start_idx)
        self.bias = float(toggle_bias)
        self.rng = np.random.default_rng(seed)

    def select_action(self, state, epsilon=None):
        if self.rng.random() < self.bias and self.toggle_start < self.n:
            return int(self.rng.integers(self.toggle_start, self.n))
        return int(self.rng.integers(self.n))


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--episodes', type=int, default=30)
    ap.add_argument('--toggle-bias', type=float, default=0.6,
                    help='xac suat moi buoc chon action toggle')
    ap.add_argument('--spec', default='ditto/topology_spec.json')
    ap.add_argument('--sync-period', type=float, default=0.5)
    ap.add_argument('--delta-s', type=float, default=1.8)
    ap.add_argument('--t-max', type=int, default=15)
    ap.add_argument('--out', default='docs/phase-6/artifacts/diag_soft_leak.json')
    return ap.parse_args()


def main():
    args = parse_args()
    spec = load_spec(args.spec)

    # hard_every lon de khong bi hard_reset rua sach leak giua chung.
    runner = EnvRunner(spec_path=args.spec, sync_period=args.sync_period,
                       hard_every=10_000)
    print('[leak] start()...', flush=True)
    runner.start()

    action_space = ActionSpace(spec)
    n_action = action_space.n
    toggle_start = n_action - len(action_space.toggle_links)
    policy = TogglePronePolicy(n_action, toggle_start, args.toggle_bias)
    env = TwinEnv(runner, spec, cfg={'delta_s': args.delta_s,
                                     't_max_steps': args.t_max})

    rows = []
    try:
        for ep in range(1, args.episodes + 1):
            obs, reset_info = env.reset(seed=1000 + ep)
            health = reset_info.get('health') or {}
            scenario = reset_info.get('scenario') or {}
            done = False
            last_thr = None
            steps = 0
            term = trunc = False

            while not done:
                action = policy.select_action(obs)
                obs, reward, term, trunc, info = env.step(action)
                last_thr = info.get('throughput')
                steps += 1
                done = term or trunc

            row = {
                'episode': ep,
                'scenario': scenario,
                'health_throughput': health.get('throughput_norm'),
                'final_throughput': (
                    round(float(last_thr), 4) if last_thr is not None else None
                ),
                'steps': steps,
                'terminated': int(term),
                'truncated': int(trunc),
                'health_attempts': int(health.get('attempts', 0)),
                'health_recovered': bool(
                    health.get('recovered_by_hard_reset', False)),
            }
            rows.append(row)

            flag = '  <<< EPISODE_LOW' if (
                last_thr is not None and float(last_thr) < 0.1) else ''
            print('[leak] ep %2d: base_thr=%s final_thr=%s steps=%d term=%d '
                  'health_retry=%d%s'
                  % (ep, row['health_throughput'], row['final_throughput'],
                     steps, int(term), row['health_attempts'], flag),
                  flush=True)
    finally:
        runner.close(cleanup_mn=True)

    # SUA: leak that = mang-NEN chet TRUOC inject. final_thr thap SAU inject
    # co the dung thiet ke (LinkDown/CongestionShift lam mang om) -> KHONG dem.
    # Chi tin health_retries (do base_thr, tuc suc khoe NEN truoc khi inject).
    n_retries = sum(r['health_attempts'] for r in rows)
    k = max(1, len(rows) // 3)
    base_first = [
        r['health_throughput'] for r in rows[:k]
        if r.get('health_throughput') is not None
    ]
    base_last = [
        r['health_throughput'] for r in rows[-k:]
        if r.get('health_throughput') is not None
    ]
    trend = {
        'mean_base_first_third': (
            round(float(np.mean(base_first)), 4) if base_first else None
        ),
        'mean_base_last_third': (
            round(float(np.mean(base_last)), 4) if base_last else None
        ),
        'n_health_retries': n_retries,
    }
    # leak/race THAT: base tut dan (state leak) HOAC co retry (race + gate cuu)
    base_drop = (
        trend['mean_base_first_third'] is not None
        and trend['mean_base_last_third'] is not None
        and trend['mean_base_last_third'] < 0.5 * trend['mean_base_first_third']
    )
    trend['infra_problem'] = bool(base_drop or n_retries > 0)
    trend['diagnosis'] = (
        'STATE LEAK (base tut dan)'
        if base_drop else 'RACE (retry rai rac, gate cuu)' if n_retries > 0
        else 'SACH')

    out = {
        'episodes': args.episodes,
        'toggle_bias': args.toggle_bias,
        'trend': trend,
        'rows': rows,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write('\n')

    verdict = trend['diagnosis']
    print('\n[leak] ' + verdict)
    print('[leak] wrote %s' % args.out)


if __name__ == '__main__':
    main()

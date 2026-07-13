# rl/eval.py
"""Evaluation harness — DONG DAU tai Lesson 6.2 (dung nguyen cho 6.5 + Phase 7).

Cham MOT policy tren mot danh sach seed, greedy (epsilon=0), ghi CSV moi
episode + bang tong hop. Khong biet dang cham ai (polymorphism) -> cong bang.
"""

import csv
import numpy as np


def eval_policy(policy, env, seeds, t_max, epsilon=0.0):
    """Chay policy tren tung seed, thu 4 metric moi episode.

    Args:
        policy : object co select_action(state, epsilon) -> int
        env    : TwinEnv da khoi tao (runner .start() roi)
        seeds  : list seed moi truong (vd heldout 1000..1049)
        t_max  : so buoc toi da / episode (de nhan biet truncated)
    Returns:
        list[dict] — mot dict metric moi episode
    """
    rows = []
    for seed in seeds:
        obs, info = env.reset(seed=seed)
        done = False
        ep_return = 0.0
        thr_sum = 0.0
        n_interv = 0
        steps = 0
        terminated = truncated = False
        while not done:
            a = policy.select_action(obs, epsilon=epsilon)   # greedy
            obs, r, terminated, truncated, info = env.step(a)
            ep_return += r
            thr_sum += info.get('throughput', 0.0)
            if not info.get('action_is_noop', True):
                n_interv += 1
            steps += 1
            done = terminated or truncated
        rows.append({
            'seed': seed,
            'recovery_time': steps if terminated else t_max,  # truncated -> t_max
            'return': ep_return,
            'mean_throughput': thr_sum / max(steps, 1),
            'n_interventions': n_interv,
            'terminated': int(terminated),
            'truncated': int(truncated),
        })
    return rows


def summarize(rows):
    """Gop list episode -> 1 dict tong hop (dung cho 1 policy / 1 seed thuat toan)."""
    def col(name):
        return np.array([r[name] for r in rows], dtype=float)
    n = len(rows)
    n_fail = int(sum(r['truncated'] for r in rows))
    return {
        'n_episodes': n,
        'recovery_time_mean': float(col('recovery_time').mean()),
        'return_mean': float(col('return').mean()),
        'mean_throughput_mean': float(col('mean_throughput').mean()),
        'n_interventions_mean': float(col('n_interventions').mean()),
        'fail_rate': n_fail / max(n, 1),          # % episode truncated (that bai)
    }


def write_csv(rows, path):
    if not rows:
        return
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def load_seeds(cfg_section):
    """Doc {start, count} -> list seed. Vd {start:1000,count:50} -> [1000..1049]."""
    return list(range(cfg_section['start'],
                      cfg_section['start'] + cfg_section['count']))
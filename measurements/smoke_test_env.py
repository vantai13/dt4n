#!/usr/bin/env python3
"""Lop 2: Smoke-test TwinEnv — chay that N episode voi action ngau nhien.

Kiem 5 dieu: khong crash, reward huu han, obs dung shape/dai, episode
ket thuc dung han, thu thap phan bo reward de mat thuong kiem "hop ly".
Chua kiem dung-sai chi tiet (do la viec cua agent Phase 6), chi kiem
"khong chay nha".
"""
import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--episodes', type=int, default=20)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--out', default='docs/phase-5/artifacts/smoke_test.json')
    args = p.parse_args()

    import numpy as np
    from mininet.env_runner import EnvRunner
    from mininet.topology_meta import load_spec
    from rl.twin_env import TwinEnv

    spec = load_spec('ditto/topology_spec.json')
    runner = EnvRunner()
    runner.start()
    rng = np.random.RandomState(args.seed)

    episodes = []
    problems = []
    try:
        env = TwinEnv(runner, spec)
        for ep in range(args.episodes):
            obs, info = env.reset(seed=1000 + ep)
            # Kiem obs dau: shape + dai + khong NaN
            _check_obs(obs, env, ep, -1, problems)

            ep_reward = 0.0
            n_actions = 0
            terminated = truncated = False
            step_rewards = []
            while not (terminated or truncated):
                action = rng.randint(env.action_space.n)   # AGENT NGAU NHIEN
                obs, reward, terminated, truncated, sinfo = env.step(action)
                _check_obs(obs, env, ep, sinfo['t'], problems)
                if not math.isfinite(reward):
                    problems.append('ep%d step%d reward khong huu han: %s'
                                    % (ep, sinfo['t'], reward))
                ep_reward += reward
                step_rewards.append(reward)
                if not sinfo['action_is_noop']:
                    n_actions += 1

            # Kiem episode ket thuc dung han
            if sinfo['t'] > env.t_max:
                problems.append('ep%d chay qua t_max (%d > %d)'
                                % (ep, sinfo['t'], env.t_max))

            episodes.append({
                'ep': ep,
                'scenario': info['scenario'].get('type'),
                'steps': sinfo['t'],
                'total_reward': ep_reward,
                'n_actions': n_actions,
                'terminated': terminated,
                'truncated': truncated,
                'reset_dirty': info.get('reset_dirty'),
                'min_step_reward': min(step_rewards),
                'max_step_reward': max(step_rewards),
            })
            print('ep%02d %-12s steps=%2d reward=%+.2f actions=%2d %s dirty=%s'
                  % (ep, info['scenario'].get('type'), sinfo['t'], ep_reward,
                     n_actions, 'TERM' if terminated else 'TRUNC',
                     info.get('reset_dirty')))
    finally:
        runner.close()

    # Tong hop + mat thuong kiem "hop ly"
    rewards = [e['total_reward'] for e in episodes]
    n_term = sum(1 for e in episodes if e['terminated'])
    n_dirty = sum(1 for e in episodes if e['reset_dirty'])
    summary = {
        'n_episodes': len(episodes),
        'n_problems': len(problems),
        'problems': problems,
        'n_terminated': n_term,
        'n_truncated': len(episodes) - n_term,
        'n_reset_dirty': n_dirty,
        'reward_mean': sum(rewards) / max(len(rewards), 1),
        'reward_min': min(rewards) if rewards else None,
        'reward_max': max(rewards) if rewards else None,
        'verdict': 'PASS' if not problems else 'FAIL',
        'episodes': episodes,
    }
    parent = os.path.dirname(os.path.abspath(args.out))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print('\n== SMOKE TEST ==')
    print('episodes=%d problems=%d term=%d/%d dirty=%d'
          % (len(episodes), len(problems), n_term, len(episodes), n_dirty))
    print('reward: mean=%.2f min=%.2f max=%.2f'
          % (summary['reward_mean'], summary['reward_min'] or 0,
             summary['reward_max'] or 0))
    print('VERDICT:', summary['verdict'])
    for pr in problems[:10]:
        print('  !', pr)


def _check_obs(obs, env, ep, t, problems):
    import numpy as np
    if obs.shape != env.observation_space.shape:
        problems.append('ep%d t%d obs shape sai: %s' % (ep, t, obs.shape))
    if not np.all(np.isfinite(obs)):
        problems.append('ep%d t%d obs co NaN/inf' % (ep, t))
    low, high = env.observation_space.low, env.observation_space.high
    if np.any(obs < low - 1e-6) or np.any(obs > high + 1e-6):
        bad = np.where((obs < low - 1e-6) | (obs > high + 1e-6))[0]
        problems.append('ep%d t%d obs vuot dai tai chieu %s' % (ep, t, list(bad)))


if __name__ == '__main__':
    main()
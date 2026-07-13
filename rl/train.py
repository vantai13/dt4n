# rl/train.py
"""Training loop Phase 6 (Lesson 6.3).

Diem cot tu: cach xu ly terminated/truncated khi push vao buffer.
    - done dung de THOAT while  = terminated OR truncated
    - done dung day vao BUFFER  = CHI terminated  (truncated van co tuong lai!)
"""

import os
import csv
import time
import argparse
import numpy as np
import yaml

from rl.run_identity import create_run_dir


def run_one_episode(agent, env, seed, warmup_done_fn, train=True):
    """Chay 1 episode. Tra ve dict metric. TACH RIENG de unit-test duoc.

    warmup_done_fn() -> bool: da qua warmup chua (co train_step khong).
    """
    obs, info = env.reset(seed=seed)
    done = False
    ep_return = 0.0
    n_interv = 0
    steps = 0
    # gom thanh phan reward de log duong 4
    comp_sum = {}
    terminated = truncated = False

    while not done:
        a = agent.select_action(obs)                 # e-greedy theo agent.epsilon
        obs2, r, terminated, truncated, info = env.step(a)

        if train:
            # ============================================================
            # BẪY terminated/truncated — CHO NAY LA LINH HON CUA 6.3:
            #   - Thoat vong while: terminated OR truncated (episode dung)
            #   - Day vao BUFFER  : CHI 'terminated'
            #     Vi truncated (het gio) van CO tuong lai -> khong duoc cat
            #     hang gamma*maxQ(s') trong TD target.
            # ============================================================
            agent.remember(obs, a, r, obs2, terminated)   # <-- CHI terminated!
            if warmup_done_fn():
                agent.train_step()

        obs = obs2
        ep_return += r
        if not info.get('action_is_noop', True):
            n_interv += 1
        # gom thanh phan reward
        for k, v in info.get('reward_breakdown', {}).items():
            comp_sum[k] = comp_sum.get(k, 0.0) + float(v)
        steps += 1
        done = terminated or truncated                # <-- day moi la co thoat while

    return {
        'seed': seed,
        'return': ep_return,
        'steps': steps,
        'terminated': int(terminated),
        'truncated': int(truncated),
        'n_interventions': n_interv,
        'reward_components': comp_sum,
        'epsilon': agent.epsilon,
    }


def evaluate_on_val(agent, env, val_seeds):
    """Eval greedy (epsilon=0) tren VAL. Tra ve return trung binh (suc khoe THAT)."""
    rets = []
    for seed in val_seeds:
        obs, info = env.reset(seed=seed)
        done = False
        R = 0.0
        while not done:
            a = agent.select_action(obs, epsilon=0.0)   # GREEDY — khong nhieu e
            obs, r, term, trunc, info = env.step(a)
            R += r
            done = term or trunc
        rets.append(R)
    return float(np.mean(rets)) if rets else 0.0


def train(agent, env, cfg, train_seeds, val_seeds, seed, config_paths=()):
    tcfg = cfg['train']
    run_dir = create_run_dir(tcfg['log_dir'], seed, config_paths)
    log_path = os.path.join(run_dir, 'train_log.csv')

    total_steps = [0]
    warmup = tcfg['warmup_steps']
    def warmup_done():
        return total_steps[0] > warmup

    best_val = -float('inf')
    ma_window = tcfg['moving_avg_window']
    returns = []

    # header CSV log
    with open(log_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['episode', 'return', 'return_ma', 'steps', 'epsilon',
                    'terminated', 'truncated', 'n_interventions', 'val_return'])

    rng = np.random.default_rng(seed)
    for ep in range(tcfg['n_episodes']):
        # rut 1 seed moi truong tu TRAIN_SEEDS (co the ngau nhien hoac tuan tu)
        env_seed = int(rng.choice(train_seeds))
        # dem step qua bao dong (de biet warmup)
        # before = env.total_steps if hasattr(env, 'total_steps') else None

        res = run_one_episode(agent, env, env_seed, warmup_done, train=True)
        total_steps[0] += res['steps']
        agent.decay_epsilon()
        returns.append(res['return'])
        ret_ma = float(np.mean(returns[-ma_window:]))
        status = 'TERM' if res['terminated'] else 'TRUNC'
        print(f"ep {ep+1:3d}/{tcfg['n_episodes']:3d} | "
              f"ret={res['return']:7.2f} | ret_ma={ret_ma:7.2f} | "
              f"steps={res['steps']:2d} | {status} | "
              f"actions={res['n_interventions']:2d} | eps={agent.epsilon:.3f}",
              flush=True)

        # eval dinh ky tren VAL (greedy)
        val_return = ''
        if (ep + 1) % tcfg['eval_every'] == 0:
            val_return = evaluate_on_val(agent, env, val_seeds)
            # chon best-validation, KHONG chon ban cuoi
            if val_return > best_val:
                best_val = val_return
                agent.save(os.path.join(run_dir, 'checkpoints', 'best.pt'))
            print(f"ep {ep+1:3d} | ret_ma={ret_ma:6.2f} | val={val_return:6.2f} "
                  f"| eps={agent.epsilon:.3f} | best_val={best_val:.2f}")

        # checkpoint dinh ky (de resume)
        if (ep + 1) % tcfg['ckpt_every'] == 0:
            agent.save(os.path.join(run_dir, 'checkpoints', f'ep{ep+1}.pt'))

        # ghi log dong nay
        with open(log_path, 'a', newline='') as f:
            csv.writer(f).writerow([
                ep + 1, f"{res['return']:.4f}", f"{ret_ma:.4f}", res['steps'],
                f"{res['epsilon']:.4f}", res['terminated'], res['truncated'],
                res['n_interventions'], val_return])

    print(f"\nXong. Run dir: {run_dir}  best_val={best_val:.2f}")
    return run_dir, best_val

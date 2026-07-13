import argparse
import numpy as np
import gymnasium as gym

from rl.agent.dqn_agent import DQNAgent


def make_config(use_double, use_dueling):
    return {'agent': {
        'hidden_layers': [128, 128], 'device': 'cpu',
        'use_double': use_double, 'use_dueling': use_dueling,
        'exploration': 'epsilon_greedy',
        'gamma': 0.99, 'learning_rate': 5e-4, 'batch_size': 64,
        'buffer_capacity': 50000, 'target_update_freq': 500,
        'epsilon_start': 1.0, 'epsilon_end': 0.02, 'epsilon_decay': 0.99,
    }}


WARMUP = 1000


def run(use_double, use_dueling, max_episodes=600, seed=0, verbose=True):
    env = gym.make('CartPole-v1')
    obs, _ = env.reset(seed=seed)
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)
    agent = DQNAgent(state_size=env.observation_space.shape[0],
                     action_size=env.action_space.n,
                     config=make_config(use_double, use_dueling))
    returns = []
    total_steps = 0
    for ep in range(max_episodes):
        obs, _ = env.reset()
        done = False
        ep_ret = 0.0
        while not done:
            a = agent.select_action(obs)
            obs2, r, term, trunc, _ = env.step(a)
            done = term or trunc
            agent.remember(obs, a, r, obs2, float(term))
            if total_steps > WARMUP:
                agent.train_step()
            obs = obs2
            ep_ret += r
            total_steps += 1
        agent.decay_epsilon()
        returns.append(ep_ret)
        avg20 = np.mean(returns[-20:])
        if verbose and (ep + 1) % 20 == 0:
            print(f"ep {ep+1:3d} | avg20={avg20:6.1f} | eps={agent.epsilon:.3f} | steps={total_steps}")
        if avg20 >= 475 and len(returns) >= 20:
            print(f"  PASS o episode {ep+1} (avg20={avg20:.1f}, steps={total_steps})")
            env.close()
            return True, avg20, total_steps
        if total_steps > 100000:
            break
    env.close()
    return False, float(np.mean(returns[-20:])), total_steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    configs = [('double+dueling', True, True)]
    if args.all:
        configs = [('dqn_thuong', False, False),
                   ('double', True, False),
                   ('double+dueling', True, True)]
    print("=" * 60)
    for name, ud, udl in configs:
        print(f"\n>>> Cau hinh: {name}")
        ok, avg, steps = run(ud, udl)
        status = "PASS" if ok else "FAIL"
        print(f"<<< {name}: {status} (avg20={avg:.1f}, steps={steps})")
    print("=" * 60)


if __name__ == '__main__':
    main()
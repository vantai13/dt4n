#!/usr/bin/env python3
"""Greedy hand-trace for a saved routing DQN policy."""

import argparse
import random
import sys

import numpy as np
import torch

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing.route_env import RouteEnv
from rl.routing.staleness_r import StalenessWrapper
from rl.routing.state_r import R_DIM_NAMES, R_STATE_DIM
from rl.routing.topology_r import (
    LOAD_CFG_ABLATION,
    SCENARIOS_DYNAMIC,
    SCENARIOS_TRAIN,
    TOPO,
)


def set_seed(seed):
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def parse_hidden_layers(value):
    return [int(x.strip()) for x in str(value).split(',') if x.strip()]


def build_agent_config(hidden_layers):
    return {
        'version': 'eval_debug',
        'agent': {
            'hidden_layers': list(hidden_layers),
            'device': 'cpu',
            'use_double': True,
            'use_dueling': True,
            'exploration': 'epsilon_greedy',
            'gamma': 0.95,
            'learning_rate': 0.001,
            'batch_size': 64,
            'buffer_capacity': 20000,
            'target_update_freq': 200,
            'epsilon_start': 1.0,
            'epsilon_end': 0.05,
            'epsilon_decay': 0.995,
            'temp_start': 2.0,
            'temp_end': 0.1,
            'temp_decay': 0.9985,
        },
    }


def build_load_cfg(kind):
    if kind == 'dynamic':
        return {
            'scenarios': SCENARIOS_DYNAMIC,
            'scenario_mix': tuple(SCENARIOS_DYNAMIC),
        }
    if kind == 'static':
        return {
            'scenarios': SCENARIOS_TRAIN,
            'scenario_mix': tuple(SCENARIOS_TRAIN),
        }
    return LOAD_CFG_ABLATION


def fmt_link(link):
    return f'{link[0]}->{link[1]}'


def fmt_snapshot(snapshot):
    items = sorted(snapshot.items(), key=lambda item: (item[0][0], item[0][1]))
    return '  '.join(f'{fmt_link(link)}={value:.3f}' for link, value in items)


def fmt_neighbor_values(neighbors, values):
    return '  '.join(
        f'{neighbor}={float(value):.3f}'
        for neighbor, value in zip(neighbors, values)
    )


def fmt_obs(obs):
    return '  '.join(
        f'{name}={float(value):.3f}'
        for name, value in zip(R_DIM_NAMES, obs)
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Print a step-by-step greedy trace for a routing policy.',
    )
    parser.add_argument('--policy', required=True)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--episodes', type=int, default=5)
    parser.add_argument('--z', type=int, default=4)
    parser.add_argument('--scenario', choices=['dynamic', 'static', 'mix'],
                        default='dynamic')
    parser.add_argument('--mask-aoi', '--mask_aoi', action='store_true',
                        dest='mask_aoi')
    parser.add_argument('--max-steps', '--max_steps', type=int, default=15,
                        dest='max_steps')
    parser.add_argument('--hidden-layers', default='64,32')
    args = parser.parse_args(argv)

    set_seed(args.seed)
    hidden_layers = parse_hidden_layers(args.hidden_layers)
    load_cfg = build_load_cfg(args.scenario)

    base = RouteEnv(
        TOPO,
        load_cfg=load_cfg,
        max_steps=args.max_steps,
        seed=args.seed,
    )
    env = StalenessWrapper(
        base,
        z_steps_choices=(int(args.z),),
        mask_aoi_dims=args.mask_aoi,
    )
    agent = DQNAgent(R_STATE_DIM, env.action_space.n, build_agent_config(hidden_layers))
    agent.load(args.policy)

    returns = []
    for ep in range(1, int(args.episodes) + 1):
        obs, info = env.reset(seed=args.seed * 100000 + ep)
        print('\n' + '=' * 78)
        print(
            f'EPISODE {ep} | scenario={info.get("load_scenario")} '
            f'| z={info.get("z_steps")} | mask_aoi={args.mask_aoi}'
        )
        print('=' * 78)

        terminated = truncated = False
        ep_return = 0.0
        step = 0
        while not (terminated or truncated):
            step += 1
            node = info['current_node']
            neighbors = env.adj[node]
            obs_arr = np.asarray(obs, dtype=np.float32)
            q_values = agent.q_values(obs_arr)
            action = agent.select_action(
                obs_arr,
                epsilon=0.0,
                valid_mask=info['valid_mask'],
            )
            chosen = (
                neighbors[action]
                if action < len(neighbors)
                else f'invalid({action})'
            )

            print(f'\n  Step {step}: node={node}')
            print(f'  neighbors      : {neighbors}')
            print(
                f'  util true      : '
                f'{fmt_neighbor_values(neighbors, info["neighbor_utils_true"])}'
            )
            print(
                f'  util observed  : '
                f'{fmt_neighbor_values(neighbors, info["neighbor_utils_observed"])}'
            )
            print(
                f'  loss true      : '
                f'{fmt_neighbor_values(neighbors, info["neighbor_losses_true"])}'
            )
            print(
                f'  loss observed  : '
                f'{fmt_neighbor_values(neighbors, info["neighbor_losses_observed"])}'
            )
            print(f'  offered true   : {fmt_snapshot(info["rho_offered_snapshot"])}')
            print(
                f'  offered obs    : '
                f'{fmt_snapshot(info["rho_offered_snapshot_observed"])}'
            )
            print(
                f'  AoI seen       : {float(info.get("aoi_measured_s", 0.0)):.3f}s '
                f'| stale={bool(info.get("util_is_stale", False))}'
            )
            print(f'  obs vector     : {fmt_obs(obs_arr)}')
            print(f'  Q-values       : {fmt_neighbor_values(neighbors, q_values)}')
            print(f'  >>> action     : {chosen} (idx={action})')

            obs, reward, terminated, truncated, info = env.step(action)
            ep_return += float(reward)
            print(
                f'      reward={float(reward):+.3f} '
                f'link_delay={float(info.get("link_delay_ms", 0.0)):.2f}ms '
                f'link_loss={float(info.get("link_loss", 0.0)):.3f} '
                f'link_rho_offered={float(info.get("link_rho_offered", 0.0)):.3f}'
            )

        outcome = 'ARRIVED' if info.get('arrived') else (
            'TIMEOUT' if info.get('timeout') else 'TRUNCATED'
        )
        print(
            f'\n  ==> episode {ep}: {outcome} | '
            f'return={ep_return:+.3f} | steps={step} | path={info.get("path")}'
        )
        returns.append(ep_return)

    print('\n' + '#' * 78)
    print(
        f'SUMMARY: episodes={len(returns)} '
        f'mean_return={np.mean(returns):+.3f} std={np.std(returns):.3f}'
    )
    print('#' * 78)


if __name__ == '__main__':
    main()

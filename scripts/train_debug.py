#!/usr/bin/env python3
"""Train one routing seed while printing every episode return."""

import argparse
import os
import random
import sys
from collections import deque

import numpy as np
import torch

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.state_r import R_STATE_DIM
from rl.routing_2path.topology_r import (
    LOAD_CFG_ABLATION,
    LOAD_CFG_ASYM,
    SCENARIOS_DYNAMIC,
    SCENARIOS_TRAIN,
    TOPO,
)


def set_seed(seed):
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def parse_hidden_layers(value):
    return [int(x.strip()) for x in str(value).split(',') if x.strip()]


def build_agent_config(hidden_layers):
    return {
        'version': 'train_debug',
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
    if kind == 'asym':
        return LOAD_CFG_ASYM
    return LOAD_CFG_ABLATION


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Debug train one DQN seed and print episode rewards.',
    )
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--episodes', type=int, default=800)
    parser.add_argument('--scenario', choices=['dynamic', 'static', 'mix', 'asym'],
                        default='dynamic')
    parser.add_argument('--mask-aoi', '--mask_aoi', action='store_true',
                        dest='mask_aoi')
    parser.add_argument('--z-max', '--z_max', type=int, default=6,
                        dest='z_max')
    parser.add_argument('--max-steps', '--max_steps', type=int, default=15,
                        dest='max_steps')
    parser.add_argument('--warmup-steps', '--warmup_steps', type=int,
                        default=500, dest='warmup_steps')
    parser.add_argument('--print-every', '--print_every', type=int, default=1,
                        dest='print_every')
    parser.add_argument('--hidden-layers', default='64,32')
    parser.add_argument('--out', default=None)
    args = parser.parse_args(argv)

    set_seed(args.seed)
    hidden_layers = parse_hidden_layers(args.hidden_layers)
    cfg = build_agent_config(hidden_layers)
    load_cfg = build_load_cfg(args.scenario)
    z_choices = tuple(range(0, int(args.z_max) + 1))

    base = RouteEnv(
        TOPO,
        load_cfg=load_cfg,
        max_steps=args.max_steps,
        seed=args.seed,
    )
    env = StalenessWrapper(
        base,
        z_steps_choices=z_choices,
        mask_aoi_dims=args.mask_aoi,
    )
    agent = DQNAgent(R_STATE_DIM, env.action_space.n, cfg)

    out = args.out
    if out is None:
        suffix = '_mask' if args.mask_aoi else ''
        out = f'frozen_policies/debug/policy{suffix}.pt'

    print(
        f"{'ep':>5} {'reward':>9} {'avg50':>9} {'eps':>7} "
        f"{'loss':>9} {'steps':>6} {'z':>3} {'arrived':>7}",
        flush=True,
    )

    returns = deque(maxlen=50)
    print_every = max(1, int(args.print_every))
    for ep in range(1, int(args.episodes) + 1):
        obs, info = env.reset(seed=args.seed * 100000 + ep)
        terminated = truncated = False
        ep_return = 0.0
        losses = []
        steps = 0

        while not (terminated or truncated):
            action = agent.select_action(obs, valid_mask=info['valid_mask'])
            next_obs, reward, terminated, truncated, next_info = env.step(action)
            done = bool(terminated or truncated)
            agent.remember(
                obs,
                action,
                reward,
                next_obs,
                done,
                next_info['valid_mask'],
            )
            if len(agent.buffer) >= max(int(args.warmup_steps), agent.batch_size):
                loss = agent.train_step()
                if loss is not None:
                    losses.append(float(loss))

            obs, info = next_obs, next_info
            ep_return += float(reward)
            steps += 1

        agent.decay_epsilon()
        returns.append(ep_return)

        if ep <= 5 or ep % print_every == 0:
            mean_loss = np.mean(losses) if losses else float('nan')
            print(
                f'{ep:5d} {ep_return:9.3f} {np.mean(returns):9.3f} '
                f'{agent.epsilon:7.3f} {mean_loss:9.4f} {steps:6d} '
                f'{int(info.get("z_steps", 0)):3d} '
                f'{str(bool(info.get("arrived", False))):>7}',
                flush=True,
            )

    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    agent.save(out)
    print(f'\nSaved policy -> {out}', flush=True)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Paired AoI-vs-mask evaluation across z values.

Default mode is a decision-node probe: both agents are forced along the same
prefix to C or D, then the policy chooses E/F. This removes the early
SRC/A/B/C/D path confounder while keeping the stale observation mechanics.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, '.')

from rl.agent.dqn_agent import DQNAgent
from rl.routing_2path.oracles import posthoc_dijkstra
from rl.routing_2path.route_env import RouteEnv
from rl.routing_2path.staleness_r import StalenessWrapper
from rl.routing_2path.state_r import AOI_DIMS, R_STATE_DIM
from rl.routing_2path.topology_r import (
    LOAD_CFG_ABLATION,
    LOAD_CFG_ASYM,
    LOAD_CFG_DYNAMIC,
    SCENARIOS_DYNAMIC,
    SCENARIOS_TRAIN,
    TOPO,
)


DECISION_NODES = {'C', 'D'}
PROBE_PREFIXES = {
    'C': ('A', 'C'),
    'D': ('B', 'D'),
}


def set_seed(seed: int) -> None:
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def parse_int_list(value: str) -> tuple[int, ...]:
    return tuple(int(x.strip()) for x in str(value).split(',') if x.strip())


def load_checkpoint(path: str) -> dict:
    return torch.load(path, map_location='cpu', weights_only=False)


def infer_hidden_layers(policy_path: str) -> list[int]:
    """Infer QNetwork trunk hidden sizes from a saved DQN checkpoint."""
    ckpt = load_checkpoint(policy_path)
    state = ckpt.get('main_net_state', ckpt)
    trunk_weights = []
    for key, tensor in state.items():
        if not key.startswith('trunk.') or not key.endswith('.weight'):
            continue
        if getattr(tensor, 'ndim', 0) == 2:
            layer_idx = int(key.split('.')[1])
            trunk_weights.append((layer_idx, tensor))
    hidden = [int(tensor.shape[0]) for _idx, tensor in sorted(trunk_weights)]
    if not hidden:
        raise ValueError(
            f'cannot infer hidden layers from {policy_path}; pass --hidden-layers'
        )
    return hidden


def build_agent_config(hidden_layers: list[int]) -> dict:
    return {
        'version': 'eval_paired',
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


def load_agent(policy_path: str, hidden_layers: list[int]) -> DQNAgent:
    agent = DQNAgent(R_STATE_DIM, 2, build_agent_config(hidden_layers))
    agent.load(policy_path)
    agent.main_net.eval()
    agent.target_net.eval()
    return agent


def build_load_cfg(kind: str) -> dict:
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
    if kind == 'dynamic_heavy':
        return LOAD_CFG_DYNAMIC
    return LOAD_CFG_ABLATION


def make_env(load_cfg: dict, z: int, mask_aoi: bool, seed: int, max_steps: int):
    base = RouteEnv(TOPO, load_cfg=load_cfg, max_steps=max_steps, seed=seed)
    return StalenessWrapper(
        base,
        z_steps_choices=(int(z),),
        mask_aoi_dims=bool(mask_aoi),
    )


def valid_action(info: dict, action: int) -> int:
    valid = np.flatnonzero(info['valid_mask'])
    if len(valid) == 0:
        return 0
    action = int(action)
    return action if action in set(valid.tolist()) else int(valid[0])


def fmt_floats(values) -> str:
    return '|'.join(f'{float(value):.6g}' for value in values)


def decision_view(env, info: dict, q_values, obs) -> dict:
    """Capture what the policy saw at the first C/D decision."""
    node = info['current_node']
    neighbors = list(env.adj[node])
    links = [(node, nb) for nb in neighbors]

    def values(snapshot_name: str):
        snapshot = info.get(snapshot_name, {})
        return [float(snapshot.get(link, float('nan'))) for link in links]

    obs = np.asarray(obs, dtype=np.float32)
    q_values = np.asarray(q_values, dtype=np.float32)
    q_valid = [float(q_values[idx]) for idx in range(len(neighbors))]
    return {
        'decision_z_steps': int(info.get('z_steps', -1)),
        'decision_aoi_s': float(info.get('aoi_measured_s', 0.0)),
        'decision_obs_aoi_norm': float(obs[AOI_DIMS[0]]),
        'decision_obs_data_fresh': float(obs[AOI_DIMS[1]]),
        'decision_neighbors': '|'.join(neighbors),
        'decision_q_values': fmt_floats(q_valid),
        'decision_true_offered': fmt_floats(values('rho_offered_snapshot')),
        'decision_seen_offered': fmt_floats(values('rho_offered_snapshot_observed')),
        'decision_next_offered': fmt_floats(values('rho_offered_snapshot_next')),
        'decision_true_loss': fmt_floats(values('loss_snapshot')),
        'decision_seen_loss': fmt_floats(values('loss_snapshot_observed')),
        'decision_next_loss': fmt_floats(values('loss_snapshot_next')),
    }


def force_prefix(env, obs, info, prefix: tuple[str, ...]):
    total = 0.0
    steps = 0
    terminated = truncated = False
    for next_hop in prefix:
        node = info['current_node']
        if next_hop not in env.adj[node]:
            raise ValueError(f'cannot force {node}->{next_hop}; path={info["path"]}')
        action = env.adj[node].index(next_hop)
        obs, reward, terminated, truncated, info = env.step(action)
        total += float(reward)
        steps += 1
        if terminated or truncated:
            break
    return obs, info, total, steps, terminated, truncated


def run_policy_episode(agent, load_cfg, z, mask_aoi, seed, prefix, max_steps):
    env = make_env(load_cfg, z, mask_aoi, seed, max_steps)
    obs, info = env.reset(seed=seed)
    total = 0.0
    steps = 0
    terminated = truncated = False

    if prefix:
        obs, info, prefix_return, prefix_steps, terminated, truncated = force_prefix(
            env,
            obs,
            info,
            prefix,
        )
        total += prefix_return
        steps += prefix_steps

    decision_node = None
    decision_choice = None
    decision_target = None
    decision_wrong = None
    aoi_at_decision_s = None
    obs_aoi_norm_at_decision = None
    obs_data_fresh_at_decision = None
    z_steps_at_decision = None
    stale_at_decision = None
    pre_decision_path = None
    view_at_decision = {}

    while not (terminated or truncated):
        node = info['current_node']
        q_values = agent.q_values(np.asarray(obs, dtype=np.float32))
        action = agent.select_action(
            np.asarray(obs, dtype=np.float32),
            epsilon=0.0,
            valid_mask=info['valid_mask'],
        )
        action = valid_action(info, action)

        if node in DECISION_NODES and decision_node is None:
            best = valid_action(info, posthoc_dijkstra(env, info))
            neighbors = env.adj[node]
            decision_node = node
            decision_choice = neighbors[action]
            decision_target = neighbors[best]
            decision_wrong = bool(action != best)
            aoi_at_decision_s = float(info.get('aoi_measured_s', 0.0))
            obs_aoi_norm_at_decision = float(np.asarray(obs)[AOI_DIMS[0]])
            obs_data_fresh_at_decision = float(np.asarray(obs)[AOI_DIMS[1]])
            z_steps_at_decision = int(info.get('z_steps', -1))
            stale_at_decision = bool(info.get('util_is_stale', False))
            pre_decision_path = tuple(info.get('path', ()))
            view_at_decision = decision_view(env, info, q_values, obs)

        obs, reward, terminated, truncated, info = env.step(action)
        total += float(reward)
        steps += 1

    if pre_decision_path is None:
        pre_decision_path = tuple(info.get('path', ()))

    return {
        'return': float(total),
        'arrived': bool(info.get('arrived', False)),
        'steps': int(steps),
        'path': tuple(info.get('path', ())),
        'pre_decision_path': pre_decision_path,
        'decision_node': decision_node,
        'decision_choice': decision_choice,
        'decision_target': decision_target,
        'decision_wrong': decision_wrong,
        'aoi_at_decision_s': aoi_at_decision_s,
        'obs_aoi_norm_at_decision': obs_aoi_norm_at_decision,
        'obs_data_fresh_at_decision': obs_data_fresh_at_decision,
        'z_steps_at_decision': z_steps_at_decision,
        'stale_at_decision': stale_at_decision,
        **view_at_decision,
    }


def paired_t(diff: np.ndarray) -> tuple[float, float]:
    sd = float(diff.std(ddof=1)) if len(diff) > 1 else 0.0
    if sd <= 1e-12:
        if abs(float(diff.mean())) <= 1e-12:
            return 0.0, 1.0
        return math.copysign(float('inf'), float(diff.mean())), 0.0
    t_stat = float(diff.mean()) / (sd / math.sqrt(len(diff)))
    try:
        from scipy import stats

        p_value = float(stats.ttest_1samp(diff, 0.0).pvalue)
    except Exception:
        p_value = float('nan')
    return t_stat, p_value


def mean_bool(values):
    clean = [float(bool(v)) for v in values if v is not None]
    return float(np.mean(clean)) if clean else float('nan')


def mean_float(values):
    clean = [float(value) for value in values if value is not None]
    return float(np.mean(clean)) if clean else float('nan')


def summarize(case: str, z: int, rows: list[dict]) -> dict:
    aoi_returns = np.array([row['aoi_return'] for row in rows], dtype=float)
    mask_returns = np.array([row['mask_return'] for row in rows], dtype=float)
    diff = aoi_returns - mask_returns
    t_stat, p_value = paired_t(diff)
    return {
        'case': case,
        'z': int(z),
        'n': len(rows),
        'aoi_s': mean_float(row['aoi_at_decision_s'] for row in rows),
        'z_seen': mean_float(row['aoi_z_steps_at_decision'] for row in rows),
        'mask_z_seen': mean_float(row['mask_z_steps_at_decision'] for row in rows),
        'aoi_obs_aoi_norm': mean_float(
            row['aoi_obs_aoi_norm_at_decision'] for row in rows
        ),
        'mask_obs_aoi_norm': mean_float(
            row['mask_obs_aoi_norm_at_decision'] for row in rows
        ),
        'aoi_return': float(aoi_returns.mean()),
        'mask_return': float(mask_returns.mean()),
        'voi': float(diff.mean()),
        'diff_sd': float(diff.std(ddof=1)) if len(diff) > 1 else 0.0,
        't': t_stat,
        'p': p_value,
        'aoi_wrong': mean_bool(row['aoi_decision_wrong'] for row in rows),
        'mask_wrong': mean_bool(row['mask_decision_wrong'] for row in rows),
        'decision_disagree': mean_bool(
            row['aoi_decision_choice'] != row['mask_decision_choice']
            for row in rows
            if row['aoi_decision_choice'] and row['mask_decision_choice']
        ),
        'pre_path_diff': mean_bool(
            row['aoi_pre_decision_path'] != row['mask_pre_decision_path']
            for row in rows
        ),
        'aoi_arrived': mean_bool(row['aoi_arrived'] for row in rows),
        'mask_arrived': mean_bool(row['mask_arrived'] for row in rows),
    }


def case_prefixes(mode: str, probe_node: str) -> list[tuple[str, tuple[str, ...]]]:
    cases = []
    if mode in {'free', 'all'}:
        cases.append(('free', ()))
    if mode in {'probe', 'all'}:
        nodes = ('C', 'D') if probe_node == 'both' else (probe_node,)
        for node in nodes:
            cases.append((f'probe_{node}', PROBE_PREFIXES[node]))
    return cases


def write_csv(rows: list[dict], path: str | None) -> None:
    if not path:
        return
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with open(out, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'\n[CSV] wrote {out}')


def print_table(summaries: list[dict]) -> None:
    print(
        f"{'case':>8} {'z':>3} {'zSeen':>5} {'AoI_s':>6} {'n':>4} "
        f"{'AoI_ret':>9} {'mask_ret':>9} "
        f"{'VoI':>9} {'t':>7} {'p':>8} {'AoI_wrong':>10} "
        f"{'mask_wrong':>10} {'disagree':>9} {'preDiff':>8}"
    )
    for row in summaries:
        print(
            f"{row['case']:>8} {row['z']:3d} {row['z_seen']:5.1f} "
            f"{row['aoi_s']:6.2f} {row['n']:4d} "
            f"{row['aoi_return']:9.3f} {row['mask_return']:9.3f} "
            f"{row['voi']:+9.3f} {row['t']:7.2f} {row['p']:8.4f} "
            f"{row['aoi_wrong']:10.3f} {row['mask_wrong']:10.3f} "
            f"{row['decision_disagree']:9.3f} {row['pre_path_diff']:8.3f}"
        )


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--policy-aoi', '--policy_aoi', required=True,
                        dest='policy_aoi')
    parser.add_argument('--policy-mask', '--policy_mask', required=True,
                        dest='policy_mask')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--n-ep', '--n_ep', type=int, default=50, dest='n_ep')
    parser.add_argument('--z-values', '--z_values', default='0,2,4,6',
                        dest='z_values')
    parser.add_argument('--scenario',
                        choices=['dynamic', 'static', 'mix', 'asym', 'dynamic_heavy'],
                        default='dynamic')
    parser.add_argument('--mode', choices=['probe', 'free', 'all'], default='probe')
    parser.add_argument('--probe-node', choices=['C', 'D', 'both'], default='both')
    parser.add_argument('--max-steps', '--max_steps', type=int, default=15,
                        dest='max_steps')
    parser.add_argument('--hidden-layers', default=None)
    parser.add_argument('--out', default='results/debug/eval_paired.csv')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    set_seed(args.seed)

    if args.hidden_layers:
        hidden_layers = parse_int_list(args.hidden_layers)
    else:
        hidden_layers = infer_hidden_layers(args.policy_aoi)

    load_cfg = build_load_cfg(args.scenario)
    agent_aoi = load_agent(args.policy_aoi, list(hidden_layers))
    agent_mask = load_agent(args.policy_mask, list(hidden_layers))
    z_values = parse_int_list(args.z_values)

    pair_rows = []
    summaries = []
    for case, prefix in case_prefixes(args.mode, args.probe_node):
        for z in z_values:
            rows_for_summary = []
            for ep in range(int(args.n_ep)):
                episode_seed = int(args.seed) * 100000 + ep
                aoi = run_policy_episode(
                    agent_aoi,
                    load_cfg,
                    z,
                    mask_aoi=False,
                    seed=episode_seed,
                    prefix=prefix,
                    max_steps=args.max_steps,
                )
                mask = run_policy_episode(
                    agent_mask,
                    load_cfg,
                    z,
                    mask_aoi=True,
                    seed=episode_seed,
                    prefix=prefix,
                    max_steps=args.max_steps,
                )
                for branch, result in (('aoi', aoi), ('mask', mask)):
                    seen = result['z_steps_at_decision']
                    if seen is not None and int(seen) != int(z):
                        raise RuntimeError(
                            f'{case} episode={ep} branch={branch}: '
                            f'expected z={z}, env reported z={seen}'
                        )
                row = {
                    'case': case,
                    'z': int(z),
                    'episode': ep,
                    'episode_seed': episode_seed,
                    'aoi_return': aoi['return'],
                    'mask_return': mask['return'],
                    'diff': aoi['return'] - mask['return'],
                    'aoi_arrived': aoi['arrived'],
                    'mask_arrived': mask['arrived'],
                    'aoi_steps': aoi['steps'],
                    'mask_steps': mask['steps'],
                    'aoi_path': '>'.join(aoi['path']),
                    'mask_path': '>'.join(mask['path']),
                    'aoi_pre_decision_path': '>'.join(aoi['pre_decision_path']),
                    'mask_pre_decision_path': '>'.join(mask['pre_decision_path']),
                    'aoi_decision_node': aoi['decision_node'],
                    'mask_decision_node': mask['decision_node'],
                    'aoi_decision_choice': aoi['decision_choice'],
                    'mask_decision_choice': mask['decision_choice'],
                    'aoi_decision_target': aoi['decision_target'],
                    'mask_decision_target': mask['decision_target'],
                    'aoi_decision_wrong': aoi['decision_wrong'],
                    'mask_decision_wrong': mask['decision_wrong'],
                    'aoi_at_decision_s': aoi['aoi_at_decision_s'],
                    'mask_aoi_at_decision_s': mask['aoi_at_decision_s'],
                    'aoi_obs_aoi_norm_at_decision': (
                        aoi['obs_aoi_norm_at_decision']
                    ),
                    'mask_obs_aoi_norm_at_decision': (
                        mask['obs_aoi_norm_at_decision']
                    ),
                    'aoi_obs_data_fresh_at_decision': (
                        aoi['obs_data_fresh_at_decision']
                    ),
                    'mask_obs_data_fresh_at_decision': (
                        mask['obs_data_fresh_at_decision']
                    ),
                    'aoi_z_steps_at_decision': aoi['z_steps_at_decision'],
                    'mask_z_steps_at_decision': mask['z_steps_at_decision'],
                    'aoi_stale_at_decision': aoi['stale_at_decision'],
                    'mask_stale_at_decision': mask['stale_at_decision'],
                    'aoi_decision_neighbors': aoi.get('decision_neighbors'),
                    'mask_decision_neighbors': mask.get('decision_neighbors'),
                    'aoi_decision_q_values': aoi.get('decision_q_values'),
                    'mask_decision_q_values': mask.get('decision_q_values'),
                    'aoi_decision_true_offered': aoi.get('decision_true_offered'),
                    'mask_decision_true_offered': mask.get('decision_true_offered'),
                    'aoi_decision_seen_offered': aoi.get('decision_seen_offered'),
                    'mask_decision_seen_offered': mask.get('decision_seen_offered'),
                    'aoi_decision_next_offered': aoi.get('decision_next_offered'),
                    'mask_decision_next_offered': mask.get('decision_next_offered'),
                    'aoi_decision_true_loss': aoi.get('decision_true_loss'),
                    'mask_decision_true_loss': mask.get('decision_true_loss'),
                    'aoi_decision_seen_loss': aoi.get('decision_seen_loss'),
                    'mask_decision_seen_loss': mask.get('decision_seen_loss'),
                    'aoi_decision_next_loss': aoi.get('decision_next_loss'),
                    'mask_decision_next_loss': mask.get('decision_next_loss'),
                }
                pair_rows.append(row)
                rows_for_summary.append(row)
            summaries.append(summarize(case, z, rows_for_summary))

    print_table(summaries)
    write_csv(pair_rows, args.out)
    print(
        '\nRead it like this: zSeen should equal z and preDiff should be 0.000 '
        'in probe rows. If zSeen is correct but VoI/disagree are 0, both '
        'policies chose the same action under that fixed-z observation.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

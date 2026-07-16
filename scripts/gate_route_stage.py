#!/usr/bin/env python3
"""Formal hard gates for the routing AoI measurement harness.

Failure policy: any red gate means stop. Do not sweep, train, or plot until
the harness is fixed. A red gate means the numbers are uninterpretable.
"""

from dataclasses import dataclass
import sys

import numpy as np

sys.path.insert(0, '.')

from rl.routing.metrics_r import evaluate_z_range
from rl.routing.route_env import RouteEnv
from rl.routing.staleness_r import StalenessWrapper
from rl.routing.state_r import UTIL_DIMS
from rl.routing.topology_r import LOAD_CFG_V1, TOPO


DEFAULT_LOAD_CFG = LOAD_CFG_V1


@dataclass
class GateResult:
    name: str
    ok: bool
    detail: str


def _fixed_actions_rollout(env, seed, actions):
    obs, info = env.reset(seed=seed)
    rows = [(obs.copy(), None, dict(info))]
    for action in actions:
        obs, reward, terminated, truncated, info = env.step(action)
        rows.append((obs.copy(), reward, dict(info)))
        if terminated or truncated:
            break
    return rows


def gate1_zero_divergence(load_cfg, n_seeds=50):
    """z=0 wrapper must be invisible on util dims."""
    max_residue = 0.0
    util_exact = True
    actions = [0, 0, 0, 0, 0, 0]
    for seed in range(n_seeds):
        bare = RouteEnv(TOPO, load_cfg=load_cfg, seed=0)
        wrapped = StalenessWrapper(
            RouteEnv(TOPO, load_cfg=load_cfg, seed=0), z_steps_choices=(0,))
        t_bare = _fixed_actions_rollout(bare, seed, actions)
        t_wrapped = _fixed_actions_rollout(wrapped, seed, actions)
        if len(t_bare) != len(t_wrapped):
            return GateResult('gate1_zero_divergence', False, 'rollout length differs')
        for idx, ((obs_b, _r_b, _i_b), (obs_w, _r_w, _i_w)) in enumerate(zip(t_bare, t_wrapped)):
            util_diff = np.abs(obs_b[list(UTIL_DIMS)] - obs_w[list(UTIL_DIMS)])
            if np.any(util_diff != 0.0):
                util_exact = False
            max_residue = max(max_residue, float(np.max(np.abs(obs_b - obs_w))))
            if not util_exact:
                return GateResult(
                    'gate1_zero_divergence',
                    False,
                    f'seed={seed} step={idx} util_diff={util_diff}',
                )
    return GateResult(
        'gate1_zero_divergence',
        True,
        f'util dims exact-zero=True; max obs residue={max_residue:.3e}',
    )


def gate2_staleness_alive(load_cfg, z=3, n_seeds=30):
    """z>0 must actually stale data and AoI must stay under z*step duration."""
    stale = 0
    total = 0
    aoi_values = []
    ceiling = z * RouteEnv.STEP_DURATION_S
    rng = np.random.default_rng(42)
    for seed in range(n_seeds):
        env = StalenessWrapper(
            RouteEnv(TOPO, load_cfg=load_cfg, seed=0), z_steps_choices=(z,))
        _obs, info = env.reset(seed=seed)
        for _ in range(8):
            stale += int(bool(info.get('util_is_stale', False)))
            total += 1
            aoi_values.append(float(info.get('aoi_measured_s', 0.0)))
            valid = np.flatnonzero(info['valid_mask'])
            if len(valid) == 0:
                break
            action = int(rng.choice(valid))
            _obs, _reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                stale += int(bool(info.get('util_is_stale', False)))
                total += 1
                aoi_values.append(float(info.get('aoi_measured_s', 0.0)))
                break

    stale_frac = stale / max(total, 1)
    aoi_max = max(aoi_values) if aoi_values else 0.0
    if stale_frac < 0.50:
        return GateResult('gate2_staleness_alive', False, f'stale_frac={stale_frac:.3f}')
    if aoi_max > ceiling + 1e-9:
        return GateResult(
            'gate2_staleness_alive',
            False,
            f'aoi_max={aoi_max:.3f}s exceeds ceiling={ceiling:.3f}s',
        )
    return GateResult(
        'gate2_staleness_alive',
        True,
        f'stale_frac={stale_frac:.3f}; aoi_max={aoi_max:.3f}s ceiling={ceiling:.3f}s',
    )


def gate3_reward_invariance(load_cfg, z_levels=(0, 2, 5, 8), n_seeds=30):
    """Rewards must be bit-identical across z for same seed/actions."""
    actions = [0, 0, 0, 0, 0, 0]
    for seed in range(n_seeds):
        rewards_by_z = {}
        for z in z_levels:
            env = StalenessWrapper(
                RouteEnv(TOPO, load_cfg=load_cfg, seed=0), z_steps_choices=(z,))
            rewards_by_z[z] = [
                reward for _obs, reward, _info in _fixed_actions_rollout(env, seed, actions)
                if reward is not None
            ]
        first = rewards_by_z[z_levels[0]]
        for z in z_levels[1:]:
            if rewards_by_z[z] != first:
                return GateResult(
                    'gate3_reward_invariance',
                    False,
                    f'seed={seed} z={z} rewards differ: {rewards_by_z}',
                )
    return GateResult(
        'gate3_reward_invariance',
        True,
        f'reward bit-identical across z={list(z_levels)} over {n_seeds} seeds',
    )


def gate4_clairvoyant_flat(load_cfg, z_levels=(0, 1, 3, 5, 8),
                           n_seeds=100, noise_tol=1e-9):
    """Truth oracle must be flat across z."""
    rows = evaluate_z_range(z_values=z_levels, seeds=range(n_seeds), load_cfg=load_cfg)
    values = np.array([row['clair_return'] for row in rows], dtype=float)
    std = float(values.std())
    if std > noise_tol:
        return GateResult(
            'gate4_clairvoyant_flat',
            False,
            f'std={std:.3e} exceeds tol={noise_tol:.3e}; values={values.tolist()}',
        )
    return GateResult('gate4_clairvoyant_flat', True, f'std={std:.3e}')


def main():
    load_cfg = DEFAULT_LOAD_CFG
    gates = [
        gate1_zero_divergence(load_cfg),
        gate2_staleness_alive(load_cfg),
        gate3_reward_invariance(load_cfg),
        gate4_clairvoyant_flat(load_cfg),
    ]

    print('=== ROUTING AOI HARD GATES ===')
    ok_all = True
    for gate in gates:
        status = 'PASS' if gate.ok else 'FAIL'
        print(f'{status:4s}  {gate.name}: {gate.detail}')
        ok_all = ok_all and gate.ok

    if not ok_all:
        print('\nSTOP: at least one gate is red. Do not run sweeps.')
        return 1

    print('\nALL GREEN: harness is ready for pilot/sweep.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Pre-train oracle gate for the calibrated routing task.

This gate asks whether the measured-physics routing stage has a learnable
decision before spending time on DQN training. A red gate means the topology or
load schedule should be rebalanced; the calibrated link model must not be
changed to make the task prettier.
"""

import argparse
from dataclasses import dataclass

import numpy as np

from rl.routing.link_model import (
    loss_rate,
    total_delay_ms,
)
from rl.routing.reward_r import DELAY_NORM_MS, W_HOP, W_LOSS, step_reward
from rl.routing.topology_r import LOAD_CFG_TRAIN, TOPO_V2


DEFAULT_DRIFT_STEPS = 2
OFFERED_MIN = 0.02


@dataclass
class OracleGateResult:
    n_samples: int
    p_e_optimal: float
    regret_always_f: float
    regret_always_e: float
    snr_f: float
    regret_ratio: float
    g1_balance: bool
    g2_snr: bool
    g3_symmetry: bool

    @property
    def ok(self):
        return self.g1_balance and self.g2_snr and self.g3_symmetry


@dataclass
class OracleHeadroomResult:
    n_samples: int
    p_e_optimal: float
    regret_always_f: float
    regret_always_e: float
    regret_ratio: float


def _edge_map(topo=TOPO_V2):
    edges = {}
    default_queue = topo.get('default_queue_pkts', 13)
    for src, dst, delay_ms, bw_mbps in topo['edges']:
        edges[(src, dst)] = {
            'base_delay': float(delay_ms),
            'bw_mbps': float(bw_mbps),
            'queue_pkts': default_queue,
        }
    return edges


def _offered_max(load_cfg):
    """Match RouteEnv's offered-load ceiling for drift clipping."""
    base_hi = load_cfg.get('base_load', (0.25, 0.40))[1]
    e_hi = load_cfg.get('e_load', (0.60, 0.95))[1]
    return float(load_cfg.get('offered_load_max', max(1.30, base_hi, e_hi)))


def _sample_offered_with_drift(rng, lo, hi, sigma, n_steps, hi_clip):
    """Sample offered load as seen after the flow has drifted to C/D.

    RouteEnv samples offered load at reset, then calls _drift() after each hop.
    The E/F decision happens after SRC->{A,B}->{C,D}, so the useful oracle gate
    should see the post-drift distribution, not only the reset distribution.
    """
    value = float(rng.uniform(float(lo), float(hi)))
    for _ in range(int(n_steps)):
        value = float(np.clip(
            value + rng.normal(0.0, float(sigma)),
            OFFERED_MIN,
            float(hi_clip),
        ))
    return value


def _sample_rho_offered_after_drift(rng, edges, load_cfg, drift_steps):
    """Sample one RouteEnv-shaped offered-load snapshot at the C/D decision."""
    base_lo, base_hi = load_cfg['base_load']
    e_lo, e_hi = load_cfg['e_load']
    sigma = float(load_cfg.get('drift_sigma', 0.15))
    hi_clip = _offered_max(load_cfg)

    rho_off = {
        link: _sample_offered_with_drift(
            rng,
            base_lo,
            base_hi,
            sigma,
            drift_steps,
            hi_clip,
        )
        for link in edges
    }

    # RouteEnv gives the E bottleneck links one shared initial level, then each
    # link drifts independently. Only C->E is used by this C-node gate, but keep
    # D->E shaped the same for audit symmetry.
    e_initial = float(rng.uniform(float(e_lo), float(e_hi)))
    for link in (('C', 'E'), ('D', 'E')):
        if link in rho_off:
            value = e_initial
            for _ in range(int(drift_steps)):
                value = float(np.clip(
                    value + rng.normal(0.0, sigma),
                    OFFERED_MIN,
                    hi_clip,
                ))
            rho_off[link] = value

    return rho_off


def path_cost(path, rho_off_map, edges, w_loss=None):
    """Return positive cost for a path using the same link reward terms."""
    total = 0.0
    for src, dst in zip(path[:-1], path[1:]):
        link = (src, dst)
        info = edges[link]
        rho_off = rho_off_map[link]
        delay_ms = total_delay_ms(
            info['base_delay'],
            rho_off,
            bw_mbps=info['bw_mbps'],
            queue_pkts=info['queue_pkts'],
        )
        loss = loss_rate(rho_off)
        if w_loss is None:
            total += -step_reward(delay_ms, loss).total
        else:
            total += delay_ms / DELAY_NORM_MS + float(w_loss) * loss + W_HOP
    return total


def _sample_path_cost_arrays(load_cfg, n_samples, seed, w_loss, drift_steps):
    """Return paired C/D path costs for the current measured-physics stage."""
    edges = _edge_map()
    rng = np.random.default_rng(int(seed))

    path_e = ['C', 'E', 'F', 'DST']
    path_f = ['C', 'F', 'DST']
    c_e = np.zeros(int(n_samples), dtype=float)
    c_f = np.zeros(int(n_samples), dtype=float)

    for idx in range(int(n_samples)):
        rho_off = _sample_rho_offered_after_drift(
            rng,
            edges,
            load_cfg,
            drift_steps,
        )
        c_e[idx] = path_cost(path_e, rho_off, edges, w_loss=w_loss)
        c_f[idx] = path_cost(path_f, rho_off, edges, w_loss=w_loss)

    return c_e, c_f


def estimate_oracle_headroom(load_cfg=LOAD_CFG_TRAIN, n_samples=200_000,
                             seed=0, w_loss=None,
                             drift_steps=DEFAULT_DRIFT_STEPS):
    """Estimate oracle balance/regret without making an SNR gate decision."""
    c_e, c_f = _sample_path_cost_arrays(
        load_cfg,
        n_samples,
        seed,
        w_loss,
        drift_steps,
    )
    e_wins = c_e < c_f
    p_e = float(e_wins.mean())
    regret_f = float(np.where(e_wins, c_f - c_e, 0.0).mean())
    regret_e = float(np.where(~e_wins, c_e - c_f, 0.0).mean())
    ratio = max(regret_f, regret_e) / max(min(regret_f, regret_e), 1e-9)

    return OracleHeadroomResult(
        n_samples=int(n_samples),
        p_e_optimal=p_e,
        regret_always_f=regret_f,
        regret_always_e=regret_e,
        regret_ratio=ratio,
    )


def _require_std_seed_estimate(std_seed_estimate):
    if std_seed_estimate is None:
        raise ValueError(
            'std_seed_estimate is required. Measure it from the 5 seed run of '
            'the CURRENT link model, then pass --std-seed-estimate. Do not '
            'reuse the old Phase-8 value 0.0276; the model has changed.'
        )
    value = float(std_seed_estimate)
    if value <= 0.0:
        raise ValueError('std_seed_estimate must be > 0')
    return value


def evaluate_oracle_gate(load_cfg=LOAD_CFG_TRAIN, n_samples=200_000, seed=0,
                         std_seed_estimate=None, w_loss=None,
                         drift_steps=DEFAULT_DRIFT_STEPS):
    """Evaluate the three pre-train oracle gates.

    ``std_seed_estimate`` intentionally has no usable default. Agent variance
    depends on the current link model and training harness; reusing a Phase-8
    noise floor after the physics changed would make G2 report a false PASS.
    """
    std_seed_estimate = _require_std_seed_estimate(std_seed_estimate)
    headroom = estimate_oracle_headroom(
        load_cfg=load_cfg,
        n_samples=n_samples,
        seed=seed,
        w_loss=w_loss,
        drift_steps=drift_steps,
    )
    snr = headroom.regret_always_f / max(std_seed_estimate, 1e-12)

    return OracleGateResult(
        n_samples=int(n_samples),
        p_e_optimal=headroom.p_e_optimal,
        regret_always_f=headroom.regret_always_f,
        regret_always_e=headroom.regret_always_e,
        snr_f=snr,
        regret_ratio=headroom.regret_ratio,
        g1_balance=0.35 <= headroom.p_e_optimal <= 0.65,
        g2_snr=snr > 3.0,
        g3_symmetry=headroom.regret_ratio < 5.0,
    )


def evaluate_config(base_load=None, e_load=None, w_loss=None, n=50_000,
                    seed=0, std_seed_estimate=None,
                    drift_steps=DEFAULT_DRIFT_STEPS):
    """Return a compact dict for config sweeps."""
    cfg = dict(LOAD_CFG_TRAIN)
    if base_load is not None:
        cfg['base_load'] = tuple(base_load)
    if e_load is not None:
        cfg['e_load'] = tuple(e_load)
    result = evaluate_oracle_gate(
        load_cfg=cfg,
        n_samples=int(n),
        seed=seed,
        std_seed_estimate=std_seed_estimate,
        w_loss=w_loss,
        drift_steps=drift_steps,
    )
    return {
        'p_e': result.p_e_optimal,
        'regret_f': result.regret_always_f,
        'regret_e': result.regret_always_e,
        'snr': result.snr_f,
        'asym': result.regret_ratio,
        'g1': result.g1_balance,
        'g2': result.g2_snr,
        'g3': result.g3_symmetry,
        'ok': result.ok,
    }


def print_result(result, load_cfg=LOAD_CFG_TRAIN,
                 std_seed_estimate=None,
                 drift_steps=DEFAULT_DRIFT_STEPS):
    std_seed_estimate = _require_std_seed_estimate(std_seed_estimate)
    e_lo, e_hi = load_cfg['e_load']
    b_lo, b_hi = load_cfg['base_load']

    print('=' * 72)
    print(
        'ORACLE GATE - LOAD_CFG_TRAIN: '
        'base_load=(%.2f, %.2f), e_load=(%.2f, %.2f)'
        % (b_lo, b_hi, e_lo, e_hi)
    )
    print('=' * 72)
    print('drift_steps = %d' % int(drift_steps))
    print('samples = %d' % result.n_samples)
    print('P(E optimal) = %.3f   P(F optimal) = %.3f'
          % (result.p_e_optimal, 1.0 - result.p_e_optimal))
    print('regret(ALWAYS-F) = %.4f' % result.regret_always_f)
    print('regret(ALWAYS-E) = %.4f' % result.regret_always_e)
    print('seed std estimate = %.4f' % std_seed_estimate)
    print('SNR = regret_F / std = %.2f' % result.snr_f)
    print('-' * 72)
    print('%s G1: P(E optimal) in [0.35, 0.65] -> %.3f'
          % ('PASS' if result.g1_balance else 'FAIL', result.p_e_optimal))
    print('%s G2: SNR > 3.0 -> %.2f'
          % ('PASS' if result.g2_snr else 'FAIL', result.snr_f))
    print('%s G3: regret asymmetry < 5x -> %.2fx'
          % ('PASS' if result.g3_symmetry else 'FAIL', result.regret_ratio))
    print('-' * 72)
    print('CONCLUSION: %s'
          % ('TRAIN ALLOWED' if result.ok else 'DO NOT TRAIN - rebalance first'))


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=int, default=200_000)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--std-seed-estimate', type=float,
                        required=True,
                        help='measured std_agent from the current 5-seed run')
    parser.add_argument('--w-loss', type=float, default=None,
                        help='temporary reward loss weight for what-if sweeps')
    parser.add_argument('--drift-steps', type=int, default=DEFAULT_DRIFT_STEPS,
                        help='RouteEnv drift steps before the C/D decision')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result = evaluate_oracle_gate(
        n_samples=args.samples,
        seed=args.seed,
        std_seed_estimate=args.std_seed_estimate,
        w_loss=args.w_loss,
        drift_steps=args.drift_steps,
    )
    print_result(
        result,
        std_seed_estimate=args.std_seed_estimate,
        drift_steps=args.drift_steps,
    )
    return 0 if result.ok else 1


if __name__ == '__main__':
    raise SystemExit(main())

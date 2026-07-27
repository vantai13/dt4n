#!/usr/bin/env python3
"""Measure the AoI-dependence gap for Phase 11 route decisions.

The gap is the fraction of sampled stale observations where the action picked
by trusting that observation differs from the action picked by accounting for
how stale it is.

    fresh: Dijkstra-style route choice on the observed stale snapshot.
    aware: route choice with the lowest expected true cost after z drift steps.

If this gap is near zero, an AoI-aware policy has little theoretical room to
beat the no-AoI policy on the current two-branch design.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.routing_2path.oracles import edge_cost
from rl.routing_2path.reward_r import W_HOP
from rl.routing_2path.topology_r import (
    DIRECT_F_LINKS,
    DYNAMIC_TREND_RANGE,
    LOAD_CFG_ABLATION,
    LOAD_CFG_ASYM,
    LOAD_CFG_DYNAMIC,
    LOAD_CFG_TRAIN,
    OFFERED_LOAD_MIN,
    TOPO_V2,
    VIA_E_LINKS,
    default_offered_load_max,
    sample_offered_load,
)


ACTION_VIA_E = 0
ACTION_DIRECT_F = 1

PATH_VIA_E = (("C", "E"), ("E", "F"), ("F", "DST"))
PATH_DIRECT_F = (("C", "F"), ("F", "DST"))
PATH_LINKS = tuple(dict.fromkeys(PATH_VIA_E + PATH_DIRECT_F))

DEFAULT_Z_VALUES = (0, 1, 3, 5, 8, 12)
DEFAULT_CASES = 200
DEFAULT_MC_SAMPLES = 80

DESIGNS = {
    "train": ("LOAD_CFG_TRAIN (S1-S4 static)", LOAD_CFG_TRAIN, 0.0, 0.0),
    "ablation": (
        "LOAD_CFG_ABLATION (S1-S6)",
        LOAD_CFG_ABLATION,
        0.02,
        DYNAMIC_TREND_RANGE[1],
    ),
    "dynamic": (
        "LOAD_CFG_DYNAMIC (75% dynamic)",
        LOAD_CFG_DYNAMIC,
        0.02,
        DYNAMIC_TREND_RANGE[1],
    ),
    "asym": ("LOAD_CFG_ASYM (Goldilocks)", LOAD_CFG_ASYM, 0.15, 0.0),
}


def edge_map(topo: dict = TOPO_V2) -> dict[tuple[str, str], dict[str, float]]:
    """Return RouteEnv-shaped link metadata keyed by edge."""
    default_queue = topo.get("default_queue_pkts")
    return {
        (src, dst): {
            "base_delay": float(base_delay),
            "base_bw": float(bw_mbps),
            "queue_pkts": default_queue,
        }
        for src, dst, base_delay, bw_mbps in topo["edges"]
    }


LINK_CFG = edge_map()


def path_cost(
    rho_view: dict[tuple[str, str], float],
    path: tuple[tuple[str, str], ...],
) -> float:
    """Return positive route cost in the same units as the Dijkstra oracle."""
    total = 0.0
    for link in path:
        meta = LINK_CFG[link]
        total += edge_cost(
            meta["base_delay"],
            float(rho_view[link]),
            bw_mbps=meta["base_bw"],
            queue_pkts=meta["queue_pkts"],
        ) + W_HOP
    return total


def fresh_action(rho_obs: dict[tuple[str, str], float]) -> int:
    """Best action if the stale snapshot is trusted as current."""
    cost_e = path_cost(rho_obs, PATH_VIA_E)
    cost_f = path_cost(rho_obs, PATH_DIRECT_F)
    return ACTION_VIA_E if cost_e <= cost_f else ACTION_DIRECT_F


def drift_forward(
    rho_view: dict[tuple[str, str], float],
    z_steps: int,
    drift_sigma: float,
    rng: np.random.Generator,
    offered_max: float,
    trend_per_step: float = 0.0,
    trend_links: tuple[tuple[str, str], ...] | None = None,
) -> dict[tuple[str, str], float]:
    """Sample how true offered load may move after the stale snapshot.

    The uncertainty model has two parts: a directed trend on one decision-link
    family and an undirected random-walk term. The trend is the predictable
    component that can make AoI useful.
    """
    out = dict(rho_view)
    steps = int(z_steps)
    if steps <= 0:
        return out

    for link in out:
        delta = 0.0
        if trend_per_step and (trend_links is None or link in trend_links):
            delta += float(trend_per_step) * float(steps)
        if drift_sigma > 0.0:
            delta += rng.normal(0.0, float(drift_sigma)) * np.sqrt(float(steps))
        if delta:
            out[link] = float(np.clip(
                float(out[link]) + delta,
                OFFERED_LOAD_MIN,
                offered_max,
            ))
    return out


def aware_action(
    rho_obs: dict[tuple[str, str], float],
    z_steps: int,
    drift_sigma: float,
    rng: np.random.Generator,
    offered_max: float,
    n_samples: int = DEFAULT_MC_SAMPLES,
    trend_scale: float = 0.0,
) -> int:
    """Best action under expected true cost given the observation age."""
    steps = int(z_steps)
    if steps <= 0:
        return fresh_action(rho_obs)

    if float(drift_sigma) == 0.0 and float(trend_scale) == 0.0:
        return fresh_action(rho_obs)

    cost_e = 0.0
    cost_f = 0.0
    for _ in range(int(n_samples)):
        if trend_scale > 0.0:
            trend_links = VIA_E_LINKS if rng.random() < 0.5 else DIRECT_F_LINKS
            trend = rng.uniform(0.0, float(trend_scale))
        else:
            trend_links = None
            trend = 0.0
        rho_maybe = drift_forward(
            rho_obs,
            steps,
            drift_sigma,
            rng,
            offered_max,
            trend_per_step=trend,
            trend_links=trend_links,
        )
        rho_maybe = {
            link: rho_maybe[link]
            for link in PATH_LINKS
        }
        cost_e += path_cost(rho_maybe, PATH_VIA_E)
        cost_f += path_cost(rho_maybe, PATH_DIRECT_F)
    return ACTION_VIA_E if cost_e <= cost_f else ACTION_DIRECT_F


def measure_gap(
    load_cfg: dict,
    z_steps: int,
    drift_sigma: float,
    n_cases: int = DEFAULT_CASES,
    seed: int = 0,
    trend_scale: float = 0.0,
    mc_samples: int = DEFAULT_MC_SAMPLES,
) -> dict[str, float]:
    """Return the AoI-dependence gap and direct-F rates for one load config."""
    if int(n_cases) <= 0:
        raise ValueError("n_cases must be positive")
    if int(mc_samples) <= 0:
        raise ValueError("mc_samples must be positive")

    case_rng = np.random.default_rng(int(seed))
    mc_rng = np.random.default_rng(int(seed) + 1_000_003 + 9973 * int(z_steps))
    link_keys = list(LINK_CFG)
    hi_clip = default_offered_load_max(load_cfg)
    differs = 0
    f_fresh = 0
    f_aware = 0

    for _ in range(int(n_cases)):
        rho_obs, _scenario_name, _active_cfg = sample_offered_load(
            link_keys,
            load_cfg,
            case_rng,
        )
        a_fresh = fresh_action(rho_obs)
        a_aware = aware_action(
            rho_obs,
            z_steps,
            drift_sigma,
            mc_rng,
            hi_clip,
            n_samples=mc_samples,
            trend_scale=trend_scale,
        )
        differs += int(a_fresh != a_aware)
        f_fresh += int(a_fresh == ACTION_DIRECT_F)
        f_aware += int(a_aware == ACTION_DIRECT_F)

    cases = float(n_cases)
    return {
        "gap": differs / cases,
        "f_rate_fresh": f_fresh / cases,
        "f_rate_aware": f_aware / cases,
    }


def parse_ints(value: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in str(value).split(",") if item.strip())


def selected_designs(name: str) -> list[tuple[str, dict, float, float]]:
    if name == "all":
        return [DESIGNS[key] for key in ("train", "ablation", "dynamic", "asym")]
    return [DESIGNS[name]]


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure the AoI-dependence ceiling for Phase 11.",
    )
    parser.add_argument(
        "--design",
        choices=("all", "train", "ablation", "dynamic", "asym"),
        default="all",
        help="which load config to probe",
    )
    parser.add_argument(
        "--z-values",
        default=",".join(str(z) for z in DEFAULT_Z_VALUES),
        help="comma-separated staleness steps",
    )
    parser.add_argument("--cases", type=int, default=DEFAULT_CASES)
    parser.add_argument("--mc-samples", type=int, default=DEFAULT_MC_SAMPLES)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    z_values = parse_ints(args.z_values)

    print("AoI-dependence gap")
    print(f"cases={args.cases} mc_samples={args.mc_samples} seed={args.seed}")
    print(
        f"{'design':30s} {'z':>3s} {'gap':>7s} "
        f"{'F|fresh':>8s} {'F|aware':>8s}"
    )
    print("-" * 62)

    for label, cfg, sigma, trend in selected_designs(args.design):
        for z in z_values:
            result = measure_gap(
                cfg,
                z,
                drift_sigma=sigma,
                n_cases=args.cases,
                seed=args.seed,
                trend_scale=trend,
                mc_samples=args.mc_samples,
            )
            print(
                f"{label:30s} {z:3d} {result['gap']:7.3f} "
                f"{result['f_rate_fresh']:8.3f} {result['f_rate_aware']:8.3f}"
            )
        print("-" * 62)

    print("Readout:")
    print("  gap ~= 0.00     -> no useful AoI action split in this design")
    print("  gap > 0.15      -> AoI has real policy headroom")
    print("  F|aware ~= 1.00 -> possible over-hedge toward direct F")
    print("  z=0 gap must be 0.000 as the zero-divergence check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

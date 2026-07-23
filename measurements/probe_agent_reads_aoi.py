#!/usr/bin/env python3
"""Check whether a trained routing agent's Q-values respond to AoI inputs.

A return ablation asks this indirectly through full episodes. This probe asks
directly: hold the decision state fixed, sweep AoI, and inspect Q(F)-Q(viaE).
If the gap is flat, the checkpoint is not using the AoI dimensions as an
action-changing signal.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from measurements.measure_baseline_v2 import load_agent
from rl.routing.state_r import R_STATE_DIM, build_route_state, mask_aoi


DEFAULT_CKPT = "frozen_policies/huong_a/policy_aoi_s0.pt"
DEFAULT_AOI_GRID = (0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0)

DEFAULT_CASES = (
    ("E looks free", 0.30, 0.55, 0.00, 0.00),
    ("E looks busy", 0.95, 0.50, 0.05, 0.00),
    ("both look mid", 0.70, 0.70, 0.00, 0.00),
    ("E near cliff", 0.90, 0.45, 0.00, 0.00),
)


def make_state(util_e: float, util_f: float, loss_e: float, loss_f: float,
               aoi_s: float) -> np.ndarray:
    """Build one C-node decision state: neighbor 0=via E, neighbor 1=direct F."""
    state = build_route_state(
        current_idx=3,
        n_nodes=8,
        step=2,
        max_steps=15,
        neighbor_utils=[util_e, util_f],
        neighbor_valid=[1.0, 1.0],
        neighbor_losses=[loss_e, loss_f],
        aoi_s=aoi_s,
    )
    if state.shape != (R_STATE_DIM,):
        raise RuntimeError(f"unexpected state shape: {state.shape}")
    return state


def parse_float_list(value: str) -> tuple[float, ...]:
    return tuple(float(item.strip()) for item in str(value).split(",") if item.strip())


def probe_checkpoint(
    ckpt_path: str,
    cases: tuple[tuple[str, float, float, float, float], ...] = DEFAULT_CASES,
    aoi_grid: tuple[float, ...] = DEFAULT_AOI_GRID,
    move_threshold: float = 0.05,
    mask_input: bool = False,
) -> list[dict[str, float | str | bool]]:
    """Print and return per-case AoI sensitivity summaries."""
    agent = load_agent(ckpt_path)

    summaries = []
    print(f"\ncheckpoint: {ckpt_path}")
    print(f"input_mode: {'mask_aoi(state)' if mask_input else 'raw state'}")
    print(
        f"{'case':22s} {'aoi_s':>6s} {'Q(viaE)':>9s} {'Q(F)':>9s} "
        f"{'Q(F)-Q(E)':>10s} {'action':>7s}"
    )
    print("-" * 70)

    for label, util_e, util_f, loss_e, loss_f in cases:
        gaps = []
        actions = []
        for aoi_s in aoi_grid:
            state = make_state(util_e, util_f, loss_e, loss_f, aoi_s)
            if mask_input:
                state = mask_aoi(state)
            q = agent.q_values(state)
            gap = float(q[1] - q[0])
            action = "F" if q[1] > q[0] else "viaE"
            gaps.append(gap)
            actions.append(action)
            print(
                f"{label:22s} {aoi_s:6.1f} {float(q[0]):9.4f} "
                f"{float(q[1]):9.4f} {gap:10.4f} {action:>7s}"
            )

        swing = float(max(gaps) - min(gaps))
        flipped = len(set(actions)) > 1
        verdict = "FLIPS" if flipped else ("moves" if swing > move_threshold else "FLAT")
        print(f"{'':22s} {'-> swing':>6s} {swing:26.4f}   {verdict}")
        print("-" * 70)
        summaries.append({
            "case": label,
            "swing": swing,
            "flipped": flipped,
            "verdict": verdict,
        })

    return summaries


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe whether a DQN checkpoint reads AoI dimensions.",
    )
    parser.add_argument(
        "--ckpt",
        action="append",
        help=(
            "checkpoint path; may be passed multiple times. Defaults to "
            f"{DEFAULT_CKPT}"
        ),
    )
    parser.add_argument(
        "--aoi-grid",
        default=",".join(str(x) for x in DEFAULT_AOI_GRID),
        help="comma-separated AoI values in seconds",
    )
    parser.add_argument(
        "--mask-input",
        action="store_true",
        help="apply mask_aoi(state) before querying Q-values",
    )
    parser.add_argument("--move-threshold", type=float, default=0.05)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    ckpts = args.ckpt or [DEFAULT_CKPT]
    aoi_grid = parse_float_list(args.aoi_grid)

    for ckpt in ckpts:
        probe_checkpoint(
            ckpt,
            aoi_grid=aoi_grid,
            move_threshold=args.move_threshold,
            mask_input=args.mask_input,
        )

    print("\nReadout:")
    if args.mask_input:
        print("  FLAT  -> masked input is constant across AoI: eval control is clean")
        print("  moves/FLIPS -> leakage or masking bug: investigate before ablation")
    else:
        print("  FLAT  -> Q-values barely move with AoI: agent is not reading AoI")
        print("  moves -> Q-values move, but the greedy action does not flip")
        print("  FLIPS -> AoI changes the chosen route on at least one case")
        print("  Note  -> LayerNorm means mask-branch controls may move on OOD AoI")
        print("  Use --mask-input to test exactly what the masked branch sees at eval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

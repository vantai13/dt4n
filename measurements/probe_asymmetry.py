#!/usr/bin/env python3
"""Measure route-risk asymmetry before training.

This probe compares the two decision-node route families:

    via E:    C -> E -> F -> DST
    direct F: C -> F -> DST

It reports positive costs in the same reward units as the routing oracle. A
positive F advantage means direct F is safer than via E for that case.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl.routing.link_model import CLIFF_RHO_OFFERED, loss_rate, total_delay_ms
from rl.routing.reward_r import DELAY_CLIP, DELAY_NORM_MS, W_HOP, W_LOSS
from rl.routing.topology_r import SCENARIOS_ASYM, TOPO_V2


PATH_VIA_E = ("C", "E", "F", "DST")
PATH_DIRECT_F = ("C", "F", "DST")

CURRENT_CASES = (
    ("S1: E free, F busy", 0.55, 1.05, 0.35),
    ("S2: E busy, F free", 1.05, 0.55, 0.35),
    ("S3: both free", 0.55, 0.55, 0.35),
    ("S4: both busy", 1.05, 1.05, 0.35),
)

ASYMMETRIC_CASES = (
    ("E warning", 0.88, 0.35, 0.35),
    ("E crosses cliff", 0.93, 0.40, 0.35),
    ("E overloaded", 0.98, 0.45, 0.35),
    ("E heavy while stale", 1.05, 0.55, 0.35),
)


@dataclass(frozen=True)
class CaseResult:
    label: str
    rho_e: float
    rho_f: float
    rho_base: float
    cost_e: float
    cost_f: float
    weight: float = 1.0

    @property
    def f_advantage(self) -> float:
        return self.cost_e - self.cost_f

    @property
    def winner(self) -> str:
        return "F" if self.f_advantage > 0.0 else "E"


def edge_map(topo: dict = TOPO_V2) -> dict[tuple[str, str], dict[str, float]]:
    """Return link metadata keyed by (src, dst)."""
    default_queue = int(topo.get("default_queue_pkts", 13))
    return {
        (src, dst): {
            "base_delay": float(base_delay),
            "bw_mbps": float(bw_mbps),
            "queue_pkts": float(default_queue),
        }
        for src, dst, base_delay, bw_mbps in topo["edges"]
    }


def link_cost(base_delay_ms: float, rho_offered: float, bw_mbps: float,
              queue_pkts: float) -> float:
    """Return positive route cost using the same terms as the Dijkstra oracle."""
    delay_ms = total_delay_ms(
        base_delay_ms,
        rho_offered,
        bw_mbps=bw_mbps,
        queue_pkts=queue_pkts,
    )
    delay_cost = min(delay_ms / DELAY_NORM_MS, -DELAY_CLIP)
    return delay_cost + W_LOSS * loss_rate(rho_offered) + W_HOP


def path_cost(path: tuple[str, ...], rho_map: dict[tuple[str, str], float],
              edges: dict[tuple[str, str], dict[str, float]]) -> float:
    """Return total positive cost for a complete path."""
    total = 0.0
    for src, dst in zip(path[:-1], path[1:]):
        link = (src, dst)
        meta = edges[link]
        total += link_cost(
            meta["base_delay"],
            rho_map[link],
            meta["bw_mbps"],
            meta["queue_pkts"],
        )
    return total


def rho_map_for_case(rho_e: float, rho_f: float, rho_base: float,
                     edges: dict[tuple[str, str], dict[str, float]]
                     ) -> dict[tuple[str, str], float]:
    """Build a RouteEnv-shaped offered-load snapshot for one hand-picked case."""
    rho = {link: float(rho_base) for link in edges}
    for link in (("C", "E"), ("D", "E")):
        if link in rho:
            rho[link] = float(rho_e)
    for link in (("C", "F"), ("D", "F")):
        if link in rho:
            rho[link] = float(rho_f)
    return rho


def measure_cases(cases: tuple[tuple[str, float, float, float], ...]
                  ) -> list[CaseResult]:
    """Measure all cases and return rows ready for printing/testing."""
    edges = edge_map()
    rows = []
    for label, rho_e, rho_f, rho_base in cases:
        rho = rho_map_for_case(rho_e, rho_f, rho_base, edges)
        rows.append(CaseResult(
            label=label,
            rho_e=float(rho_e),
            rho_f=float(rho_f),
            rho_base=float(rho_base),
            cost_e=path_cost(PATH_VIA_E, rho, edges),
            cost_f=path_cost(PATH_DIRECT_F, rho, edges),
            weight=1.0,
        ))
    return rows


def midpoint(pair: tuple[float, float]) -> float:
    lo, hi = pair
    return (float(lo) + float(hi)) / 2.0


def measure_asym_scenarios() -> list[CaseResult]:
    """Measure the midpoint of the actual SCENARIOS_ASYM config."""
    edges = edge_map()
    rows = []
    for name, cfg in SCENARIOS_ASYM.items():
        rho_e = midpoint(cfg["e_load"])
        rho_f = midpoint(cfg.get("direct_load", cfg["f_load"]))
        rho_base = midpoint(cfg["base_load"])
        rho = rho_map_for_case(rho_e, rho_f, rho_base, edges)
        rows.append(CaseResult(
            label=name,
            rho_e=rho_e,
            rho_f=rho_f,
            rho_base=rho_base,
            cost_e=path_cost(PATH_VIA_E, rho, edges),
            cost_f=path_cost(PATH_DIRECT_F, rho, edges),
            weight=1.0,
        ))
    return rows


def print_asym_load_guardrail() -> None:
    max_f_load = max(float(cfg["f_load"][1]) for cfg in SCENARIOS_ASYM.values())
    verdict = "PASS" if max_f_load < CLIFF_RHO_OFFERED else "FAIL"
    print(
        f"max configured F load = {max_f_load:.3f} "
        f"< cliff {CLIFF_RHO_OFFERED:.4f} -> {verdict}\n"
    )


def print_goldilocks_check(rows: list[CaseResult], gate: float) -> bool:
    """Print whether SCENARIOS_ASYM is in the pre-train Goldilocks zone."""
    penalty_when_e_good = [
        row.f_advantage
        for row in rows
        if row.rho_e < CLIFF_RHO_OFFERED
    ]
    advantage_when_e_bad = [
        row.f_advantage
        for row in rows
        if row.rho_e >= CLIFF_RHO_OFFERED
    ]
    if not penalty_when_e_good or not advantage_when_e_bad:
        raise RuntimeError("SCENARIOS_ASYM must include both E-good and E-bad cases")

    penalty = sum(penalty_when_e_good) / len(penalty_when_e_good)
    advantage = sum(advantage_when_e_bad) / len(advantage_when_e_bad)
    pass_gate = advantage > gate and penalty < -gate

    print("--- GOLDILOCKS ZONE CHECK ---")
    print(f"  F advantage when E is GOOD  (should be clearly NEGATIVE): {penalty:+.3f}")
    print(f"  F advantage when E is BAD   (should be POSITIVE):         {advantage:+.3f}")
    print(f"  separation width (adv - pen): {advantage - penalty:.3f}")
    if pass_gate:
        print("  PASS: F is useful when E is bad, but always-F is penalized when E is good.")
        print("        Train the AoI vs mask pair next.")
    elif penalty >= -gate:
        print("  FAIL: F is still too safe. Lower E_FREE_LOAD and rerun this probe.")
    else:
        print("  FAIL: F is too risky as a retreat. Lower F_BUSY_LOAD and rerun this probe.")
    print()
    return pass_gate


def print_table(title: str, rows: list[CaseResult], gate: float | None) -> float:
    """Print one scenario table and return mean direct-F advantage."""
    print(title)
    print("-" * len(title))
    show_weight = any(row.weight != 1.0 for row in rows)
    weight_header = f" {'w':>4}" if show_weight else ""
    print(
        f"{'case':<24} {'rho_E':>6} {'rho_F':>6} {'cost_E':>8} "
        f"{'cost_F':>8} {'F_adv':>8}{weight_header} {'win':>4}"
    )
    for row in rows:
        weight_text = f" {row.weight:4.1f}" if show_weight else ""
        print(
            f"{row.label:<24} {row.rho_e:6.2f} {row.rho_f:6.2f} "
            f"{row.cost_e:8.3f} {row.cost_f:8.3f} "
            f"{row.f_advantage:8.3f}{weight_text} {row.winner:>4}"
        )

    weight_sum = sum(row.weight for row in rows)
    mean_advantage = (
        sum(row.f_advantage * row.weight for row in rows) / weight_sum
    )
    mean_label = "weighted mean" if show_weight else "mean"
    if gate is None:
        print(f"\n{mean_label} F advantage = {mean_advantage:+.3f}\n")
    else:
        verdict = "PASS" if mean_advantage > gate else "FAIL"
        print(
            f"\n{mean_label} F advantage = {mean_advantage:+.3f} -> "
            f"{verdict} (gate {gate:.3f})\n"
        )
    return mean_advantage


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gate",
        type=float,
        default=0.3,
        help="minimum mean direct-F advantage required for PASS",
    )
    parser.add_argument(
        "--only",
        choices=("current", "asymmetric", "scenarios_asym", "train", "both", "all"),
        default="all",
        help="which hand-picked case set to print",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    means = []
    goldilocks_pass = None

    if args.only in ("current", "both", "all"):
        means.append(print_table(
            "[A] current symmetric-style cases",
            measure_cases(CURRENT_CASES),
            args.gate,
        ))
    if args.only in ("asymmetric", "both", "all"):
        means.append(print_table(
            "[B] proposed asymmetric safety cases",
            measure_cases(ASYMMETRIC_CASES),
            args.gate,
        ))
    if args.only in ("scenarios_asym", "train", "all"):
        asym_rows = measure_asym_scenarios()
        means.append(print_table(
            "[C] actual SCENARIOS_ASYM midpoints",
            asym_rows,
            None,
        ))
        print_asym_load_guardrail()
        goldilocks_pass = print_goldilocks_check(asym_rows, args.gate)

    if goldilocks_pass is not None:
        return 0 if goldilocks_pass else 1
    return 0 if means and means[-1] > args.gate else 1


if __name__ == "__main__":
    raise SystemExit(main())

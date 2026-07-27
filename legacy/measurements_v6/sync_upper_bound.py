#!/usr/bin/env python3
"""Generate the Phase 14B.0 cheap upper-bound report.

This script consumes a Phase 14A ``pilot_marginalized`` JSON result and writes
the reproducible documentation artifact for the first Phase 14B decision:

    G_sync_gross(z) <= disagree(z) * decision_regret

The bound is deliberately gross of sync cost.  It is used to screen possible
``c_sync`` values before implementing a sync action.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np


DEFAULT_RESULT = "results/phase-14/pilot_cvar_a01.json"
DEFAULT_OUT = "docs/phase-14b/00-upper-bound.md"
DEFAULT_COSTS = (0.001, 0.005, 0.01, 0.02, 0.05, 0.1)


@dataclass(frozen=True)
class BoundRow:
    z: int
    disagree: float
    upper_bound: float


@dataclass(frozen=True)
class RewardScale:
    n_samples: int
    seed: int
    terminal_mean: float
    terminal_std: float
    differential_mean: float
    differential_std: float
    differential_abs_mean: float
    r_arrived: float
    delay_norm_ms: float


def git_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def sha12(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
    except OSError:
        return None


def load_result(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"missing result JSON: {path}. Rerun measurements.pilot_marginalized "
            "or pass --result to an existing Phase 14A JSON."
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(f"result JSON must contain an object: {path}")
    return payload


def bound_rows(payload: dict) -> list[BoundRow]:
    if "decision_regret" not in payload:
        raise ValueError("result JSON is missing decision_regret")
    disagree_by_z = payload.get("disagree_rate_by_z")
    if not isinstance(disagree_by_z, dict) or not disagree_by_z:
        raise ValueError("result JSON is missing disagree_rate_by_z")

    regret = float(payload["decision_regret"])
    rows = []
    for z_key, disagree in sorted(disagree_by_z.items(), key=lambda item: int(item[0])):
        if disagree is None:
            continue
        dis = float(disagree)
        rows.append(BoundRow(int(z_key), dis, dis * regret))
    if not rows:
        raise ValueError("disagree_rate_by_z has no numeric rows")
    return rows


def max_bound(rows: list[BoundRow]) -> BoundRow:
    return max(rows, key=lambda row: row.upper_bound)


def parse_costs(raw: str) -> tuple[float, ...]:
    if not raw.strip():
        return ()
    costs = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        value = float(item)
        if value < 0.0:
            raise ValueError("--sync-costs must be nonnegative")
        costs.append(value)
    return tuple(costs)


def routing3_env_from_load_cfg(load_cfg: str | None) -> dict[str, str]:
    """Recover routing3 environment knobs recorded in the old load_cfg label."""
    if not load_cfg:
        return {}
    out = {}
    rate = re.search(r"RATE_([^_]+)", load_cfg)
    profile = re.search(r"PROFILE_([^_]+)", load_cfg)
    bias = re.search(r"BIAS_([^_]+)", load_cfg)
    if rate:
        out["ROUTING3_EVENT_RATE"] = rate.group(1)
    if profile:
        out["ROUTING3_BAND_PROFILE"] = profile.group(1)
    if bias:
        out["ROUTING3_CRASH_BIAS_TEMP"] = bias.group(1)
    return out


def apply_env(env: dict[str, str]) -> None:
    for key, value in env.items():
        os.environ[key] = value


def _stats(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=np.float64)
    mean = float(arr.mean())
    std = float(arr.std(ddof=1)) if arr.size > 1 else 0.0
    return mean, std


def _routing3_reward_no_terminal(sampler, action, rho) -> float:
    from rl.routing3 import link_model, reward3, topology3 as T3

    total = 0.0
    for link in T3.PATH_LINKS[action]:
        meta = sampler.link_cfg[link]
        rho_offered = float(rho[link])
        delay_ms = link_model.total_delay_ms(
            meta["base_delay"],
            rho_offered,
            bw_mbps=meta["base_bw"],
            queue_pkts=meta["queue_pkts"],
        )
        total += reward3.step_reward(
            delay_ms,
            link_model.loss_rate(rho_offered),
            arrived=False,
        ).total
    return float(total)


def measure_routing3_reward_scale(
    n_samples: int,
    seed: int,
    source_env: dict[str, str] | None = None,
) -> RewardScale:
    if n_samples <= 0:
        raise ValueError("--samples must be positive")
    apply_env(source_env or {})

    from measurements.samplers3 import Sampler3Path
    from rl.routing3 import reward3

    sampler = Sampler3Path()
    rng = np.random.default_rng(int(seed))
    terminal_values = []
    differential_values = []

    for _ in range(int(n_samples)):
        obs, _z_true = sampler.sample_observation((0,), rng)
        world = sampler.roll_forward(obs, 0, rng)
        terminal_values.append(
            max(sampler.reward_of(action, world) for action in sampler.actions)
        )
        differential_values.append(
            max(
                _routing3_reward_no_terminal(sampler, action, world["rho"])
                for action in sampler.actions
            )
        )

    term_mean, term_std = _stats(terminal_values)
    diff_mean, diff_std = _stats(differential_values)
    return RewardScale(
        n_samples=int(n_samples),
        seed=int(seed),
        terminal_mean=term_mean,
        terminal_std=term_std,
        differential_mean=diff_mean,
        differential_std=diff_std,
        differential_abs_mean=abs(diff_mean),
        r_arrived=float(reward3.R_ARRIVED),
        delay_norm_ms=float(reward3.DELAY_NORM_MS),
    )


def objective_label(payload: dict) -> str:
    objective = payload.get("objective")
    if objective == "cvar":
        return f"cvar alpha={float(payload.get('cvar_alpha', 0.0)):g}"
    if objective:
        return str(objective)
    return "mean/legacy"


def cost_screen(rows: list[BoundRow], cost: float) -> str:
    viable = [str(row.z) for row in rows if row.upper_bound > cost]
    if viable:
        return ", ".join(viable)
    return "none"


def render_markdown(
    payload: dict,
    result_path: Path,
    result_sha: str | None,
    rows: list[BoundRow],
    costs: tuple[float, ...],
    scale: RewardScale | None,
    source_env: dict[str, str],
    command: str,
) -> str:
    regret = float(payload["decision_regret"])
    best = max_bound(rows)
    current_git = git_hash()
    source_git = payload.get("git_hash", "unknown")
    lines = [
        "# Lesson 14B.0 - Cheap upper bound for G_sync",
        "",
        f"Ngay tao: {date.today().isoformat()}",
        f"Current Git: `{current_git}`",
        f"Source Git in JSON: `{source_git}`",
        f"Nguon so 14A: `{result_path}`",
        f"Source JSON sha256/12: `{result_sha or 'unknown'}`",
        f"Generated by: `{command}`",
        "",
        "> Tai lieu nay copy cac so 14A tu `results/` sang `docs/` vi",
        "> `results/` bi gitignore. Day la artifact de bao ve va chay lai",
        "> Lesson 14B.0 ma khong phu thuoc vao file ket qua cuc bo.",
        "",
        "## 1. Source result",
        "",
        "| field | value |",
        "|---|---:|",
        f"| topology | `{payload.get('topology', 'unknown')}` |",
        f"| load_cfg | `{payload.get('load_cfg', 'unknown')}` |",
        f"| objective | `{objective_label(payload)}` |",
        f"| cases | {int(payload.get('cases', 0))} |",
        f"| mc_samples | {int(payload.get('mc_samples', 0))} |",
        f"| seed | {int(payload.get('seed', 0))} |",
        f"| gap_mean | {float(payload.get('gap_mean', 0.0)):.6f} |",
        f"| gap_ci95 | {float(payload.get('gap_ci95', 0.0)):.6f} |",
        f"| gap_lower | {float(payload.get('gap_lower', 0.0)):.6f} |",
        f"| verdict | `{payload.get('verdict', 'unknown')}` |",
        f"| disagree_rate | {float(payload.get('disagree_rate', 0.0)):.6f} |",
        f"| n_disagree | {int(payload.get('n_disagree', 0))} |",
        f"| decision_regret | {regret:.6f} |",
        f"| q_margin | {float(payload.get('q_margin', 0.0)):.6f} |",
        f"| q_margin_marginalized | {float(payload.get('q_margin_marginalized', 0.0)):.6f} |",
        "",
        "## 2. Upper-bound formula",
        "",
        "```text",
        "G_sync_gross(z) <= disagree(z) x decision_regret",
        "```",
        "",
        "Interpretation: SYNC can only help when the fresh snapshot changes the",
        "selected action. The 14A disagreement rate is exactly that screening",
        "probability. This is a gross upper bound, not an estimate of net value;",
        "real sync still pays `c_sync` and consumes a step.",
        "",
        "| z | disagree(z) | upper_bound = disagree x regret |",
        "|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.z} | {row.disagree:.6f} | {row.upper_bound:.6f} |"
        )
    lines.extend([
        "",
        f"Break-even gross cost `c* = max_z upper_bound = {best.upper_bound:.6f}`",
        f"at `z = {best.z}`.",
        "",
        "If `c_sync >= c*`, adaptive sync cannot be worth it under this bound.",
        "If `c_sync < c*`, sync is only still possible, not proven useful.",
        "",
        "## 3. c_sync screen",
        "",
        "| c_sync | z values where upper_bound > c_sync | screen |",
        "|---:|---|---|",
    ])
    for cost in costs:
        viable = cost_screen(rows, cost)
        screen = "possible" if viable != "none" else "ruled out"
        lines.append(f"| {cost:.6f} | {viable} | {screen} |")

    lines.extend([
        "",
        "This table is the allowed sweep view: report the whole curve / break-even",
        "point. Do not pick one cost after seeing whether it passes.",
        "",
        "## 4. Reward-unit audit",
        "",
        "Naive conversion `c_sync = sync_delay_ms / DELAY_NORM_MS` is not a valid",
        "unit conversion. `DELAY_NORM_MS` scores one packet over one route link;",
        "`c_sync` scores a different action type: spend a decision step to buy",
        "fresh information.",
        "",
    ])

    if scale is None:
        lines.append("Reward scale measurement was skipped.")
    else:
        env_text = ", ".join(
            f"`{key}={value}`" for key, value in sorted(source_env.items())
        ) or "`<default routing3 env>`"
        lines.extend([
            f"Routing3 env used for scale: {env_text}",
            "",
            "| quantity | value |",
            "|---|---:|",
            f"| samples | {scale.n_samples} |",
            f"| seed | {scale.seed} |",
            f"| best route reward, with terminal mean | {scale.terminal_mean:.6f} |",
            f"| best route reward, with terminal std | {scale.terminal_std:.6f} |",
            f"| best route reward, no terminal mean | {scale.differential_mean:.6f} |",
            f"| best route reward, no terminal std | {scale.differential_std:.6f} |",
            f"| abs(no-terminal mean) | {scale.differential_abs_mean:.6f} |",
            f"| R_ARRIVED | {scale.r_arrived:.6f} |",
            f"| DELAY_NORM_MS | {scale.delay_norm_ms:.6f} |",
            "",
            "`R_ARRIVED` was harmless in 14A because every routing action received",
            "the same terminal constant. In 14B, the action space contains SYNC,",
            "so that constant is no longer common across action types.",
        ])

    lines.extend([
        "",
        "## 5. Signed Phase 14B.0 decision",
        "",
        "Decision before implementing the sync action: use A + C.",
        "",
        "- A: score sync economics on differential reward: delay + loss + hop,",
        "  excluding the terminal arrival constant.",
        "- C: sweep/report `c_sync` and the break-even point `c*`; this is not",
        "  tuning a cost until PASS.",
        "",
        "Prediction before 14B implementation: the measured gross headroom is small.",
        "Adaptive sync can only be justified if the real control-plane cost is below",
        "`c*`; otherwise the operational conclusion is periodic sync with a long",
        "period, not request-on-demand sync.",
        "",
        "## 6. Re-run commands",
        "",
        "```bash",
        f"{command}",
        "python3 -m pytest test/routing/test_sync_upper_bound.py",
        "# If pytest is not installed in this Python environment:",
        "python3 test/routing/test_sync_upper_bound.py",
        "```",
        "",
        "To regenerate the source 14A JSON used here:",
        "",
        "```bash",
        "ROUTING3_EVENT_RATE=0.12 ROUTING3_BAND_PROFILE=cliffband \\",
        "ROUTING3_CRASH_BIAS_TEMP=0 \\",
        "python3 -m measurements.pilot_marginalized \\",
        "  --topology routing3 --objective cvar --cvar-alpha 0.1 \\",
        "  --cases 400 --mc-samples 200 --seed 0 \\",
        "  --out results/phase-14/pilot_cvar_a01_rerun.json",
        "```",
        "",
    ])
    return "\n".join(lines)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", default=DEFAULT_RESULT,
                        help="Phase 14A pilot_marginalized JSON")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="markdown report path")
    parser.add_argument("--samples", type=int, default=2000,
                        help="samples for routing3 reward-scale audit")
    parser.add_argument("--seed", type=int, default=0,
                        help="seed for routing3 reward-scale audit")
    parser.add_argument("--sync-costs", default=",".join(map(str, DEFAULT_COSTS)),
                        help="comma-separated c_sync values for the screen table")
    parser.add_argument("--skip-scale", action="store_true",
                        help="write the bound report without reward-scale audit")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    result_path = Path(args.result)
    out_path = Path(args.out)
    payload = load_result(result_path)
    rows = bound_rows(payload)
    costs = parse_costs(args.sync_costs)
    source_env = routing3_env_from_load_cfg(payload.get("load_cfg"))

    scale = None
    if not args.skip_scale:
        if payload.get("topology") != "routing3":
            raise ValueError("--skip-scale is required for non-routing3 results")
        scale = measure_routing3_reward_scale(
            int(args.samples),
            int(args.seed),
            source_env,
        )

    command = (
        "python3 -m measurements.sync_upper_bound "
        f"--result {result_path} --out {out_path} "
        f"--samples {int(args.samples)} --seed {int(args.seed)}"
    )
    if args.skip_scale:
        command += " --skip-scale"
    if args.sync_costs != ",".join(map(str, DEFAULT_COSTS)):
        command += f" --sync-costs {args.sync_costs}"

    text = render_markdown(
        payload=payload,
        result_path=result_path,
        result_sha=sha12(result_path),
        rows=rows,
        costs=costs,
        scale=scale,
        source_env=source_env,
        command=command,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")

    best = max_bound(rows)
    print(f"source      : {result_path}")
    print(f"out         : {out_path}")
    print(f"regret      : {float(payload['decision_regret']):.6f}")
    print(f"c* gross    : {best.upper_bound:.6f} at z={best.z}")
    if scale is not None:
        print(f"route mean  : {scale.terminal_mean:.6f} with terminal")
        print(f"diff mean   : {scale.differential_mean:.6f} no terminal")
    return 0


if __name__ == "__main__":
    sys.exit(main())

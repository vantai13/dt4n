#!/usr/bin/env python3
"""Direct Phase 14B sync headroom measurement.

This measures the gross value of buying a fresh snapshot at age z:

    G_sync(z) = objective(R(a_fresh(w), w)) - objective(R(a_stale, w))

where ``a_stale`` is selected from the stale observation with a split-sample
Monte Carlo estimate, and ``a_fresh(w)`` is the best route in the sampled true
world. The fresh branch is clairvoyant, so this is an upper bound for any
deployable sync policy before subtracting sync cost.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from measurements.pilot_marginalized import Z_CHOICES, objective_value
from measurements.samplers import build_sampler


def git_hash():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def file_sha(path, n_chars=12):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:int(n_chars)]
    except OSError:
        return None


def estimate_reward_samples(
    sampler,
    obs,
    z,
    actions,
    n_mc,
    rng,
):
    """Sample reward arrays for all actions with common random worlds."""
    rewards = {
        action: np.empty(int(n_mc), dtype=np.float64)
        for action in actions
    }
    best_rewards = np.empty(int(n_mc), dtype=np.float64)
    best_actions = []

    for idx in range(int(n_mc)):
        true_world = sampler.roll_forward(obs, z, rng)
        values = {
            action: float(sampler.reward_of(action, true_world))
            for action in actions
        }
        for action, value in values.items():
            rewards[action][idx] = value
        best_action = max(actions, key=lambda action: values[action])
        best_actions.append(best_action)
        best_rewards[idx] = values[best_action]

    return rewards, best_rewards, best_actions


def one_sync_case(
    sampler,
    obs,
    z,
    actions,
    n_mc,
    rng,
    objective,
    cvar_alpha,
    estimator="honest",
):
    """Return one gross sync-headroom sample and diagnostics."""
    select_rewards, select_best, select_best_actions = estimate_reward_samples(
        sampler,
        obs,
        z,
        actions,
        n_mc,
        rng,
    )
    select_q = {
        action: objective_value(values, objective, cvar_alpha)
        for action, values in select_rewards.items()
    }
    a_stale = max(actions, key=lambda action: select_q[action])

    if estimator == "naive":
        score_rewards = select_rewards
        score_best = select_best
        score_best_actions = select_best_actions
    elif estimator == "honest":
        score_rewards, score_best, score_best_actions = estimate_reward_samples(
            sampler,
            obs,
            z,
            actions,
            n_mc,
            rng,
        )
    else:
        raise ValueError(f"unknown estimator: {estimator!r}")

    stale_values = score_rewards[a_stale]
    fresh_values = score_best
    fresh_objective = objective_value(fresh_values, objective, cvar_alpha)
    stale_objective = objective_value(stale_values, objective, cvar_alpha)
    gap = fresh_objective - stale_objective
    disagree = float(
        np.mean([best_action != a_stale for best_action in score_best_actions])
    )
    return float(gap), {
        "z": int(z),
        "a_stale": a_stale,
        "gap": float(gap),
        "disagree": disagree,
        "fresh_objective": float(fresh_objective),
        "stale_objective": float(stale_objective),
    }


def summarize(values):
    arr = np.asarray(values, dtype=np.float64)
    mean = float(arr.mean()) if arr.size else 0.0
    ci95 = (
        float(1.96 * arr.std(ddof=1) / np.sqrt(arr.size))
        if arr.size > 1 else 0.0
    )
    return mean, ci95


def quantiles(values):
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    return {
        "p50": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "max": float(arr.max()),
    }


def histogram(values, bins=12):
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return []
    counts, edges = np.histogram(arr, bins=int(bins))
    return [
        {
            "lo": float(edges[idx]),
            "hi": float(edges[idx + 1]),
            "count": int(count),
        }
        for idx, count in enumerate(counts)
    ]


def parse_float_values(raw):
    values = []
    for item in str(raw).split(","):
        item = item.strip()
        if not item:
            continue
        value = float(item)
        if not (0.0 < value <= 1.0):
            raise ValueError("budget fractions must be in (0, 1]")
        values.append(value)
    if not values:
        raise ValueError("at least one budget fraction is required")
    return tuple(values)


def budget_upper_rows(values, fractions):
    """Upper bound for adaptive sync at fixed sync budget.

    A periodic policy samples states uniformly, so its expected gross value is
    E[all]. An adaptive oracle with budget fraction b can spend syncs on the top
    b fraction of states, giving E[top b] - E[all] before costs.
    """
    arr = np.sort(np.asarray(values, dtype=np.float64))[::-1]
    if arr.size == 0:
        return []
    all_mean = float(arr.mean())
    rows = []
    for frac in fractions:
        k = max(1, int(np.ceil(float(frac) * arr.size)))
        top = arr[:k]
        top_mean = float(top.mean())
        rows.append({
            "budget_frac": float(frac),
            "n_sync": int(k),
            "all_mean": all_mean,
            "top_mean": top_mean,
            "g_aoi_upper": top_mean - all_mean,
            "top_threshold": float(top[-1]),
        })
    return rows


def budget_decomposition_rows(values_by_z, fractions):
    """Split pooled adaptive headroom into between-z and within-z terms.

    The pooled top-budget oracle can mostly select high-z states. That is a
    threshold/periodic effect, not state-adaptive value. The within-z term
    keeps each age group fixed and only ranks states inside the same z bucket.
    """
    groups = [
        (int(z), np.asarray(values, dtype=np.float64))
        for z, values in values_by_z.items()
        if len(values) > 0
    ]
    if not groups:
        return []

    all_values = np.concatenate([values for _z, values in groups])
    total_n = int(all_values.size)
    pooled_by_frac = {
        row["budget_frac"]: row
        for row in budget_upper_rows(all_values, fractions)
    }

    rows = []
    for frac in fractions:
        frac = float(frac)
        components = []
        within_z_upper = 0.0
        for z, values in groups:
            z_row = budget_upper_rows(values, (frac,))[0]
            weight = float(values.size) / float(total_n)
            within_z_upper += weight * float(z_row["g_aoi_upper"])
            components.append({
                "z": int(z),
                "weight": weight,
                **z_row,
            })

        pooled = pooled_by_frac[frac]
        pooled_upper = float(pooled["g_aoi_upper"])
        between_z_upper = pooled_upper - within_z_upper
        rows.append({
            "budget_frac": frac,
            "pooled_n_sync": int(pooled["n_sync"]),
            "pooled_upper": pooled_upper,
            "within_z_upper": float(within_z_upper),
            "between_z_upper": float(between_z_upper),
            "within_z_components": components,
        })
    return rows


def parse_z_values(raw):
    if raw is None:
        return tuple(Z_CHOICES)
    values = []
    for item in str(raw).split(","):
        item = item.strip()
        if item:
            values.append(int(item))
    if not values:
        raise ValueError("--z-values must contain at least one integer")
    return tuple(values)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", default="routing3",
                        choices=("routing3", "routing_2path"))
    parser.add_argument("--load-cfg", default=None)
    parser.add_argument("--reward-model", default="default",
                        choices=("default", "r_v2", "r_v3"))
    parser.add_argument("--objective", default="cvar", choices=("mean", "cvar"))
    parser.add_argument("--cvar-alpha", type=float, default=0.1)
    parser.add_argument("--estimator", default="honest",
                        choices=("honest", "naive"))
    parser.add_argument("--cases", type=int, default=200)
    parser.add_argument("--mc-samples", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--z-values", default=None,
                        help="comma-separated z values; default Z_CHOICES")
    parser.add_argument("--budget-fracs", default="0.1,0.2,0.3",
                        help="comma-separated sync budget fractions")
    parser.add_argument("--hist-bins", type=int, default=12)
    parser.add_argument("--out", default=None)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.cases <= 0:
        raise ValueError("--cases must be positive")
    if args.mc_samples <= 0:
        raise ValueError("--mc-samples must be positive")
    if not (0.0 < float(args.cvar_alpha) <= 1.0):
        raise ValueError("--cvar-alpha must be in (0, 1]")

    sampler_kwargs = {}
    if args.load_cfg:
        sampler_kwargs["load_cfg_name"] = args.load_cfg
    if args.reward_model != "default":
        sampler_kwargs["reward_model"] = args.reward_model
    sampler = build_sampler(args.topology, **sampler_kwargs)
    actions = tuple(sampler.actions)
    z_values = parse_z_values(args.z_values)
    budget_fracs = parse_float_values(args.budget_fracs)
    rng = np.random.default_rng(int(args.seed))

    all_gaps = []
    gaps_by_z = {}
    rows = []
    for z in z_values:
        gaps = []
        disagrees = []
        action_counts = {action: 0 for action in actions}
        for _idx in range(int(args.cases)):
            obs, _z_true = sampler.sample_observation((int(z),), rng)
            gap, detail = one_sync_case(
                sampler,
                obs,
                int(z),
                actions,
                int(args.mc_samples),
                rng,
                args.objective,
                float(args.cvar_alpha),
                args.estimator,
            )
            gaps.append(gap)
            all_gaps.append(gap)
            disagrees.append(float(detail["disagree"]))
            action_counts[detail["a_stale"]] += 1

        gaps_by_z[int(z)] = list(gaps)
        mean, ci95 = summarize(gaps)
        disagree_mean = float(np.mean(disagrees)) if disagrees else 0.0
        row = {
            "z": int(z),
            "cases": int(args.cases),
            "gap_mean": mean,
            "gap_ci95": ci95,
            "gap_lower": mean - ci95,
            "disagree_fresh": disagree_mean,
            "sync_regret_when_disagree": (
                mean / disagree_mean if disagree_mean > 1e-12 else 0.0
            ),
            "gap_distribution": quantiles(gaps),
            "budget_upper": budget_upper_rows(gaps, budget_fracs),
            "a_stale_counts": action_counts,
        }
        rows.append(row)

    overall_mean, overall_ci95 = summarize(all_gaps)
    budget_upper = budget_upper_rows(all_gaps, budget_fracs)
    budget_decomposition = budget_decomposition_rows(gaps_by_z, budget_fracs)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "git_hash": git_hash(),
        "topology": args.topology,
        "load_cfg": getattr(sampler, "load_cfg_name", args.load_cfg),
        "objective": args.objective,
        "cvar_alpha": float(args.cvar_alpha),
        "estimator": args.estimator,
        "reward_model": getattr(sampler, "reward_model", args.reward_model),
        "link_model_path": getattr(sampler, "link_model_path", None),
        "link_model_sha": file_sha(getattr(sampler, "link_model_path", "")),
        "reward_model_path": getattr(sampler, "reward_model_path", None),
        "reward_model_sha": file_sha(getattr(sampler, "reward_model_path", "")),
        "dynamics_source_path": getattr(sampler, "dynamics_source_path", None),
        "dynamics_source_sha": file_sha(
            getattr(sampler, "dynamics_source_path", "")
        ),
        "cases_per_z": int(args.cases),
        "mc_samples": int(args.mc_samples),
        "seed": int(args.seed),
        "z_values": [int(z) for z in z_values],
        "overall_gap_mean": overall_mean,
        "overall_gap_ci95": overall_ci95,
        "overall_gap_distribution": quantiles(all_gaps),
        "overall_gap_histogram": histogram(all_gaps, args.hist_bins),
        "budget_upper": budget_upper,
        "budget_decomposition": budget_decomposition,
        "rows": rows,
    }

    print("=" * 78)
    print("  gross sync headroom: fresh clairvoyant route minus stale route")
    print("=" * 78)
    print(f"topology          : {payload['topology']}")
    print(f"load_cfg          : {payload['load_cfg']}")
    print(f"objective         : {args.objective}")
    if args.objective == "cvar":
        print(f"cvar_alpha        : {float(args.cvar_alpha):g}")
    print(f"estimator         : {args.estimator}")
    print(f"cases             : {args.cases}/z   (MC {args.mc_samples}/cell)")
    print(f"seed              : {args.seed}    git: {git_hash()}")
    print("-" * 78)
    print(
        f"{'z':>3} {'gap':>10} {'+/-':>8} {'lower':>10} "
        f"{'disagree':>10} {'regret':>10} {'p90':>10}"
    )
    for row in rows:
        print(
            f"{row['z']:>3d} {row['gap_mean']:>+10.4f}"
            f"{row['gap_ci95']:>8.4f}{row['gap_lower']:>+10.4f}"
            f"{row['disagree_fresh']:>10.3f}"
            f"{row['sync_regret_when_disagree']:>10.4f}"
            f"{row['gap_distribution']['p90']:>10.4f}"
        )
    print("-" * 78)
    print(
        f"overall_gap       : {overall_mean:+.4f} +/- {overall_ci95:.4f}"
    )
    print(f"overall p90/p99   : {payload['overall_gap_distribution']['p90']:.4f} / "
          f"{payload['overall_gap_distribution']['p99']:.4f}")
    print("-" * 78)
    print(f"{'budget':>8} {'n_sync':>8} {'E[top]':>10} {'E[all]':>10} {'G_AoI_ub':>10} {'thr':>10}")
    for row in payload["budget_upper"]:
        print(
            f"{row['budget_frac']:>8.3f}"
            f"{row['n_sync']:>8d}"
            f"{row['top_mean']:>10.4f}"
            f"{row['all_mean']:>10.4f}"
            f"{row['g_aoi_upper']:>10.4f}"
            f"{row['top_threshold']:>10.4f}"
        )
    print("-" * 78)
    print(f"{'budget':>8} {'pooled':>10} {'within-z':>10} {'between-z':>10}")
    for row in payload["budget_decomposition"]:
        print(
            f"{row['budget_frac']:>8.3f}"
            f"{row['pooled_upper']:>10.4f}"
            f"{row['within_z_upper']:>10.4f}"
            f"{row['between_z_upper']:>10.4f}"
        )
    print("=" * 78)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"-> wrote {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

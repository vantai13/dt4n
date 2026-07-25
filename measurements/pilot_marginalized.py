#!/usr/bin/env python3
"""Measure the true headroom of AoI information.

    gap_marginalized = Bayes(obs + z) - Bayes(obs, marginalize z)

The AoI-aware ceiling chooses with the true z. The z-blind ceiling chooses one
action after marginalizing over the prior P(z), then both are scored at z_true.
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

from measurements.samplers import build_sampler


Z_CHOICES = (0, 1, 3, 5, 8, 12)
GATE_THRESHOLD = 0.10


def objective_value(rewards, objective="mean", cvar_alpha=0.2):
    """Collapse sampled rewards into a decision objective."""
    values = np.asarray(rewards, dtype=np.float64)
    if values.size <= 0:
        raise ValueError("rewards must be non-empty")
    if objective == "mean":
        return float(values.mean())
    if objective == "cvar":
        alpha = float(cvar_alpha)
        if not (0.0 < alpha <= 1.0):
            raise ValueError("--cvar-alpha must be in (0, 1]")
        k = max(1, int(alpha * values.size))
        return float(np.sort(values)[:k].mean())
    raise ValueError(f"unknown objective: {objective!r}")


def estimate_q_for_z(
    sampler,
    obs,
    z,
    actions,
    n_mc,
    rng,
    objective="mean",
    cvar_alpha=0.2,
):
    """Estimate Q(a, o, z) for all actions with common random worlds."""
    rewards = {
        action: np.empty(int(n_mc), dtype=np.float64)
        for action in actions
    }
    for idx in range(int(n_mc)):
        true_world = sampler.roll_forward(obs, z, rng)
        for action in actions:
            rewards[action][idx] = sampler.reward_of(action, true_world)
    return {
        action: objective_value(values, objective, cvar_alpha)
        for action, values in rewards.items()
    }


def gap_one_case(
    sampler,
    obs,
    z_true,
    z_choices,
    p_z,
    actions,
    n_mc,
    rng,
    objective="mean",
    cvar_alpha=0.2,
):
    """Return one marginalized-gap sample and diagnostic detail."""
    q = {action: {} for action in actions}
    for z in z_choices:
        q_for_z = estimate_q_for_z(
            sampler,
            obs,
            z,
            actions,
            n_mc,
            rng,
            objective,
            cvar_alpha,
        )
        for action, value in q_for_z.items():
            q[action][z] = value

    a_star_z = max(actions, key=lambda action: q[action][z_true])

    def ev_marginal(action):
        return sum(p_z[z] * q[action][z] for z in z_choices)

    q_marg = {action: ev_marginal(action) for action in actions}
    a_star_marg = max(actions, key=ev_marginal)

    # Choose blind, score on the true z. Scoring at any averaged z would give
    # the blind branch a world that no episode actually experienced.
    gap = q[a_star_z][z_true] - q[a_star_marg][z_true]
    q_true_values = sorted((q[action][z_true] for action in actions), reverse=True)
    q_marg_values = sorted(q_marg.values(), reverse=True)
    q_margin_true = (
        q_true_values[0] - q_true_values[1] if len(q_true_values) > 1 else 0.0
    )
    q_margin_marg = (
        q_marg_values[0] - q_marg_values[1] if len(q_marg_values) > 1 else 0.0
    )
    return float(gap), {
        "z_true": int(z_true),
        "a_star_z": a_star_z,
        "a_star_marg": a_star_marg,
        "agree": a_star_z == a_star_marg,
        "gap": float(gap),
        "gap_naive": float(gap),
        "selection_bias": 0.0,
        "q_margin": float(q_margin_true),
        "q_margin_marginalized": float(q_margin_marg),
    }


def gap_one_case_honest(
    sampler,
    obs,
    z_true,
    z_choices,
    p_z,
    actions,
    n_mc,
    rng,
    objective="mean",
    cvar_alpha=0.2,
):
    """Return one split-sample marginalized-gap estimate.

    ``gap_one_case`` uses the same Monte Carlo estimates to choose an argmax and
    score that chosen action. This can create winner's curse / maximization
    bias, especially when the true action values are close. The honest estimator
    chooses actions with sample A and scores them with an independent sample B.
    """
    q_a = {action: {} for action in actions}
    q_b = {action: {} for action in actions}
    for z in z_choices:
        q_for_z_a = estimate_q_for_z(
            sampler,
            obs,
            z,
            actions,
            n_mc,
            rng,
            objective,
            cvar_alpha,
        )
        q_for_z_b = estimate_q_for_z(
            sampler,
            obs,
            z,
            actions,
            n_mc,
            rng,
            objective,
            cvar_alpha,
        )
        for action, value in q_for_z_a.items():
            q_a[action][z] = value
        for action, value in q_for_z_b.items():
            q_b[action][z] = value

    a_star_z = max(actions, key=lambda action: q_a[action][z_true])

    def ev_marginal_a(action):
        return sum(p_z[z] * q_a[action][z] for z in z_choices)

    a_star_marg = max(actions, key=ev_marginal_a)

    gap = q_b[a_star_z][z_true] - q_b[a_star_marg][z_true]
    gap_naive = q_a[a_star_z][z_true] - q_a[a_star_marg][z_true]
    q_true_values = sorted((q_b[action][z_true] for action in actions), reverse=True)
    q_marg_b = {
        action: sum(p_z[z] * q_b[action][z] for z in z_choices)
        for action in actions
    }
    q_marg_values = sorted(q_marg_b.values(), reverse=True)
    q_margin_true = (
        q_true_values[0] - q_true_values[1] if len(q_true_values) > 1 else 0.0
    )
    q_margin_marg = (
        q_marg_values[0] - q_marg_values[1] if len(q_marg_values) > 1 else 0.0
    )
    return float(gap), {
        "z_true": int(z_true),
        "a_star_z": a_star_z,
        "a_star_marg": a_star_marg,
        "agree": a_star_z == a_star_marg,
        "gap": float(gap),
        "gap_naive": float(gap_naive),
        "selection_bias": float(gap_naive - gap),
        "q_margin": float(q_margin_true),
        "q_margin_marginalized": float(q_margin_marg),
    }


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
        digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None
    return digest[:int(n_chars)]


def summarize_gaps(gaps):
    mean = float(gaps.mean())
    if len(gaps) < 2:
        return mean, 0.0
    ci95 = float(1.96 * gaps.std(ddof=1) / np.sqrt(len(gaps)))
    return mean, ci95


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, default=400,
                        help="number of sampled (obs, z) cases")
    parser.add_argument("--mc-samples", type=int, default=200,
                        help="Monte Carlo worlds per (action, obs, z) cell")
    parser.add_argument("--topology", default="routing3",
                        choices=("routing3", "routing_2path"))
    parser.add_argument("--load-cfg", default=None,
                        help="optional sampler load config name")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default=None,
                        help="optional JSON result path")
    parser.add_argument("--objective", default="mean", choices=("mean", "cvar"),
                        help="decision objective for sampled rewards")
    parser.add_argument("--cvar-alpha", type=float, default=0.2,
                        help="tail fraction for --objective cvar")
    parser.add_argument("--reward-model", default="default",
                        choices=("default", "r_v2", "r_v3"),
                        help="reward module for sampler scoring")
    parser.add_argument("--estimator", default="honest",
                        choices=("naive", "honest"),
                        help="honest split-sample estimator removes winner's "
                             "curse; naive preserves old Phase 14A meter")
    parser.add_argument("--strict", action="store_true",
                        help="return exit code 1 when the gate fails")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.cases <= 0:
        raise ValueError("--cases must be positive")
    if args.mc_samples <= 0:
        raise ValueError("--mc-samples must be positive")
    if not (0.0 < float(args.cvar_alpha) <= 1.0):
        raise ValueError("--cvar-alpha must be in (0, 1]")

    rng = np.random.default_rng(int(args.seed))
    sampler_kwargs = {}
    if args.load_cfg:
        sampler_kwargs["load_cfg_name"] = args.load_cfg
    if args.reward_model != "default":
        sampler_kwargs["reward_model"] = args.reward_model
    sampler = build_sampler(args.topology, **sampler_kwargs)
    actions = tuple(sampler.actions)
    load_cfg_name = getattr(sampler, "load_cfg_name", args.load_cfg)
    link_model_path = getattr(sampler, "link_model_path", None)
    reward_model_path = getattr(sampler, "reward_model_path", None)
    reward_model_name = getattr(sampler, "reward_model", args.reward_model)
    dynamics_source_path = getattr(sampler, "dynamics_source_path", None)

    z_choices = tuple(Z_CHOICES)
    p_z = {z: 1.0 / len(z_choices) for z in z_choices}

    gaps = np.empty(int(args.cases), dtype=np.float64)
    gap_naive_samples = np.empty(int(args.cases), dtype=np.float64)
    selection_bias_samples = np.empty(int(args.cases), dtype=np.float64)
    n_agree = 0
    per_z = {z: [] for z in z_choices}
    disagree_by_z = {z: 0 for z in z_choices}
    q_margin_by_z = {z: [] for z in z_choices}
    q_marg_margin_by_z = {z: [] for z in z_choices}
    disagreement_gaps = []
    action_counts_z = {
        z: {action: 0 for action in actions}
        for z in z_choices
    }
    action_counts_marginal = {
        z: {action: 0 for action in actions}
        for z in z_choices
    }

    gap_fn = gap_one_case_honest if args.estimator == "honest" else gap_one_case

    for idx in range(int(args.cases)):
        obs, z_true = sampler.sample_observation(z_choices, rng)
        gap, detail = gap_fn(
            sampler,
            obs,
            z_true,
            z_choices,
            p_z,
            actions,
            int(args.mc_samples),
            rng,
            args.objective,
            float(args.cvar_alpha),
        )
        gaps[idx] = gap
        gap_naive_samples[idx] = float(detail.get("gap_naive", gap))
        selection_bias_samples[idx] = float(detail.get("selection_bias", 0.0))
        agree = bool(detail["agree"])
        n_agree += int(agree)
        if not agree:
            disagree_by_z[int(z_true)] += 1
            disagreement_gaps.append(float(gap))
        per_z[int(z_true)].append(float(gap))
        action_counts_z[int(z_true)][detail["a_star_z"]] += 1
        action_counts_marginal[int(z_true)][detail["a_star_marg"]] += 1
        q_margin_by_z[int(z_true)].append(float(detail["q_margin"]))
        q_marg_margin_by_z[int(z_true)].append(
            float(detail["q_margin_marginalized"])
        )

    mean, ci95 = summarize_gaps(gaps)
    gap_naive_mean, gap_naive_ci95 = summarize_gaps(gap_naive_samples)
    selection_bias_mean, selection_bias_ci95 = summarize_gaps(selection_bias_samples)
    lower = mean - ci95
    verdict = "PASS" if lower >= GATE_THRESHOLD else "FAIL"
    agree_rate = n_agree / float(args.cases)
    disagree_rate = 1.0 - agree_rate
    n_disagree = int(args.cases) - n_agree
    decision_regret = (
        float(np.mean(disagreement_gaps)) if disagreement_gaps else 0.0
    )
    q_margin = float(
        np.mean([value for values in q_margin_by_z.values() for value in values])
    )
    q_margin_marginalized = float(
        np.mean(
            [value for values in q_marg_margin_by_z.values() for value in values]
        )
    )
    gap_by_z = {
        str(z): float(np.mean(values)) if values else None
        for z, values in per_z.items()
    }
    disagree_rate_by_z = {
        str(z): (
            float(disagree_by_z[z] / len(per_z[z])) if per_z[z] else None
        )
        for z in z_choices
    }
    q_margin_by_z_mean = {
        str(z): float(np.mean(values)) if values else None
        for z, values in q_margin_by_z.items()
    }
    action_counts_by_z = {
        str(z): {
            "a_star_z": dict(action_counts_z[z]),
            "a_star_marg": dict(action_counts_marginal[z]),
        }
        for z in z_choices
    }

    print("=" * 62)
    print("  gap_marginalized = Bayes(obs+z) - Bayes(obs, marginalize z)")
    print("=" * 62)
    print(f"topology          : {args.topology}")
    print(f"load_cfg          : {load_cfg_name}")
    print(f"objective         : {args.objective}")
    print(f"estimator         : {args.estimator}")
    print(f"reward_model      : {reward_model_name}")
    if args.objective == "cvar":
        print(f"cvar_alpha        : {float(args.cvar_alpha):g}")
    print(f"actions           : {actions}")
    print(f"cases             : {args.cases}   (MC {args.mc_samples}/cell)")
    print(f"seed              : {args.seed}    git: {git_hash()}")
    print("-" * 62)
    print(f"gap_marginalized  : {mean:.4f} +/- {ci95:.4f}")
    print(f"gap_naive_ref     : {gap_naive_mean:.4f} +/- {gap_naive_ci95:.4f}")
    print(
        f"selection_bias    : {selection_bias_mean:+.4f} "
        f"+/- {selection_bias_ci95:.4f}"
    )
    print(f"  lower CI95      : {lower:.4f}")
    print(f"  threshold       : {GATE_THRESHOLD:.2f}")
    print(f"GATE              : {verdict}")
    print("-" * 62)
    print(
        f"a*(z) == a*_marg  : {n_agree}/{args.cases} "
        f"({100.0 * agree_rate:.1f}%)"
    )
    print(f"disagree_rate     : {disagree_rate:.4f}")
    print(f"n_disagree        : {n_disagree}")
    print(f"decision_regret   : {decision_regret:.4f}")
    print(f"q_margin          : {q_margin:.4f}")
    print(f"q_margin_marg     : {q_margin_marginalized:.4f}")
    print("-" * 62)
    print("gap / disagreement by z:")
    for z in z_choices:
        values = per_z[z]
        if values:
            counts_z = action_counts_z[z]
            counts_marg = action_counts_marginal[z]
            print(
                f"  z={z:<3d} n={len(values):<4d} "
                f"gap={np.mean(values):+.4f} "
                f"disagree={disagree_rate_by_z[str(z)]:.3f} "
                f"q_margin={q_margin_by_z_mean[str(z)]:.4f} "
                f"a*z={counts_z} amarg={counts_marg}"
            )
    print("=" * 62)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now().isoformat(),
            "git_hash": git_hash(),
            "topology": args.topology,
            "load_cfg": load_cfg_name,
            "objective": args.objective,
            "estimator": args.estimator,
            "cvar_alpha": float(args.cvar_alpha),
            "reward_model": reward_model_name,
            "link_model_path": link_model_path,
            "link_model_sha": file_sha(link_model_path) if link_model_path else None,
            "reward_model_path": reward_model_path,
            "reward_model_sha": file_sha(reward_model_path) if reward_model_path else None,
            "dynamics_source_path": dynamics_source_path,
            "dynamics_source_sha": (
                file_sha(dynamics_source_path) if dynamics_source_path else None
            ),
            "cases": int(args.cases),
            "mc_samples": int(args.mc_samples),
            "seed": int(args.seed),
            "gap_mean": mean,
            "gap_ci95": ci95,
            "gap_lower": lower,
            "gap_honest": mean if args.estimator == "honest" else None,
            "gap_naive": gap_naive_mean,
            "gap_naive_ci95": gap_naive_ci95,
            "selection_bias": selection_bias_mean,
            "selection_bias_ci95": selection_bias_ci95,
            "threshold": GATE_THRESHOLD,
            "verdict": verdict,
            "agree_rate": agree_rate,
            "disagree_rate": disagree_rate,
            "n_disagree": n_disagree,
            "decision_regret": decision_regret,
            "q_margin": q_margin,
            "q_margin_marginalized": q_margin_marginalized,
            "gap_by_z": gap_by_z,
            "disagree_rate_by_z": disagree_rate_by_z,
            "q_margin_by_z": q_margin_by_z_mean,
            "action_counts_by_z": action_counts_by_z,
        }
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"-> wrote {out_path}")

    if args.strict and verdict == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

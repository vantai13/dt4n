#!/usr/bin/env python3
"""Run the Phase 14C 2x2 oracle factorial.

Factors:
  1. symmetric vs heterogeneous-volatility routing3 dynamics
  2. mean vs CVaR decision objective
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from measurements.pilot_marginalized import (
    Z_CHOICES,
    gap_one_case,
    gap_one_case_honest,
    gap_one_case_placebo,
)
from measurements.samplers3 import Sampler3Path
from measurements.samplers3_hetero import Sampler3PathHetero


def run_one(sampler, cases, n_mc, seed, objective, alpha, estimator):
    rng = np.random.default_rng(int(seed))
    z_choices = tuple(Z_CHOICES)
    p_z = {z: 1.0 / len(z_choices) for z in z_choices}
    actions = tuple(sampler.actions)
    if estimator == "honest":
        gap_fn = gap_one_case_honest
    elif estimator == "placebo":
        gap_fn = gap_one_case_placebo
    else:
        gap_fn = gap_one_case

    gaps = np.empty(int(cases), dtype=np.float64)
    naive_gaps = np.empty(int(cases), dtype=np.float64)
    selection_biases = np.empty(int(cases), dtype=np.float64)
    disagreement_gaps = []
    for idx in range(int(cases)):
        obs, z_true = sampler.sample_observation(z_choices, rng)
        gap, detail = gap_fn(
            sampler,
            obs,
            z_true,
            z_choices,
            p_z,
            actions,
            int(n_mc),
            rng,
            objective,
            float(alpha),
        )
        gaps[idx] = gap
        naive_gaps[idx] = float(detail.get("gap_naive", gap))
        selection_biases[idx] = float(detail.get("selection_bias", 0.0))
        if not detail["agree"]:
            disagreement_gaps.append(float(gap))

    mean = float(gaps.mean())
    ci95 = float(1.96 * gaps.std(ddof=1) / np.sqrt(int(cases)))
    naive_mean = float(naive_gaps.mean())
    bias_mean = float(selection_biases.mean())
    disagree_rate = len(disagreement_gaps) / float(cases)
    decision_regret = (
        float(np.mean(disagreement_gaps)) if disagreement_gaps else 0.0
    )
    return {
        "gap": mean,
        "ci95": ci95,
        "lower_ci95": mean - ci95,
        "gap_honest": mean if estimator == "honest" else None,
        "gap_placebo": mean if estimator == "placebo" else None,
        "gap_naive": naive_mean,
        "selection_bias": bias_mean,
        "disagree_rate": disagree_rate,
        "decision_regret": decision_regret,
    }


def build_grid(include_isochurn=False):
    grid = [
        ("SYM x mean", Sampler3Path(), "mean", 0.2),
        ("SYM x CVaR0.1", Sampler3Path(), "cvar", 0.1),
        (
            "HETERO x mean",
            Sampler3PathHetero((0.0, 0.10, 0.35), "by_load"),
            "mean",
            0.2,
        ),
        (
            "HETERO x CVaR0.1",
            Sampler3PathHetero((0.0, 0.10, 0.35), "by_load"),
            "cvar",
            0.1,
        ),
    ]
    if include_isochurn:
        grid.append(
            (
                "C1_ISOCHURN x CVaR0.1",
                Sampler3PathHetero((0.15, 0.15, 0.15), "by_load"),
                "cvar",
                0.1,
            )
        )
    return grid


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, default=300)
    parser.add_argument("--mc-samples", type=int, default=200)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--estimator", default="honest",
                        choices=("naive", "honest", "placebo"),
                        help="honest split-sample estimator, placebo fake-z "
                             "control, or old naive meter")
    parser.add_argument("--include-isochurn", action="store_true",
                        help="include symmetric iso-churn control C1")
    parser.add_argument(
        "--out",
        default=None,
        help="optional JSON output path for the row data",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.cases <= 0:
        raise ValueError("--cases must be positive")
    if args.mc_samples <= 0:
        raise ValueError("--mc-samples must be positive")
    if not args.seeds:
        raise ValueError("--seeds must not be empty")

    rows = []
    print(
        f"{'config':<20}{'seed':>5}{'gap':>10}{'+/-':>8}{'lowerCI':>10}"
        f"{'naive':>10}{'bias':>9}{'disagr':>8}{'regret':>9}"
    )
    print("-" * 89)
    for name, sampler, objective, alpha in build_grid(args.include_isochurn):
        for seed in args.seeds:
            result = run_one(
                sampler,
                args.cases,
                args.mc_samples,
                int(seed),
                objective,
                alpha,
                args.estimator,
            )
            row = {
                "config": name,
                "seed": int(seed),
                "objective": objective,
                "alpha": float(alpha),
                "estimator": args.estimator,
                "cases": int(args.cases),
                "mc_samples": int(args.mc_samples),
                **result,
            }
            rows.append(row)
            print(
                f"{name:<20}{int(seed):>5}{result['gap']:>+10.4f}"
                f"{result['ci95']:>8.4f}{result['lower_ci95']:>+10.4f}"
                f"{result['gap_naive']:>+10.4f}"
                f"{result['selection_bias']:>+9.4f}"
                f"{result['disagree_rate']:>8.3f}"
                f"{result['decision_regret']:>9.4f}"
            )

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
        print(f"-> wrote {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

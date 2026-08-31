#!/usr/bin/env python3
"""Mechanistic null for cross-link correlation in static CBR controls.

The null preserves each run's actual sampler boundaries and ``dt`` values,
then randomises only the independent initial packet phases.  This avoids the
iid-Gaussian assumption and also avoids silently replacing the measured clock
with a perfect 0.2 s grid.

The ``abs(r)=0.50`` result is a threshold-separation diagnostic, not a full
power calculation for a particular shared-noise data-generating process.
"""
from __future__ import annotations

import argparse
import collections
import csv
import itertools
import json
import math
import subprocess
from pathlib import Path

import numpy as np


LINK_ORDER = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
N_REPS = 20_000
ABS_R_THRESHOLD = 0.50
BURN_IN_S = 20.0


def git_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() or "unknown"


def load(run: Path) -> tuple[dict[str, list[dict[str, float]]], dict]:
    rows: dict[str, list[dict[str, float]]] = collections.defaultdict(list)
    with (run / "rho_measured.csv").open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            if int(raw["sampler_id"]) == 0:
                rows[raw["link"]].append(
                    {
                        "monotonic_s": float(raw["monotonic_s"]),
                        "rho": float(raw["rho"]),
                        "dt_s": float(raw["dt_s"]),
                    }
                )
    meta = json.loads((run / "rho_trace_meta.json").read_text(encoding="utf-8"))
    return rows, meta


def retained_arrays(
    rows: dict[str, list[dict[str, float]]]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    reference = rows[LINK_ORDER[0]]
    start = reference[0]["monotonic_s"] + BURN_IN_S
    keep = np.asarray([row["monotonic_s"] > start for row in reference])
    ends = np.asarray([row["monotonic_s"] for row in reference])[keep]
    dts = np.asarray([row["dt_s"] for row in reference])[keep]
    boundaries = np.concatenate(([ends[0] - dts[0]], ends))
    boundaries -= boundaries[0]
    observed = np.asarray(
        [
            np.asarray([row["rho"] for row in rows[link]])[keep]
            for link in LINK_ORDER
        ]
    )
    return boundaries, dts, observed


def staircase_rates(
    rate_pps: float,
    boundaries: np.ndarray,
    dts: np.ndarray,
    phases: np.ndarray,
) -> np.ndarray:
    cumulative = np.floor((boundaries[None, :] + phases[:, None]) * rate_pps)
    return np.diff(cumulative, axis=1) / dts[None, :]


def row_correlations(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a - a.mean(axis=1, keepdims=True)
    b = b - b.mean(axis=1, keepdims=True)
    numerator = np.sum(a * b, axis=1)
    denominator = np.sqrt(np.sum(a * a, axis=1) * np.sum(b * b, axis=1))
    return np.divide(
        numerator,
        denominator,
        out=np.zeros_like(numerator),
        where=denominator > 0.0,
    )


def null_distribution(
    rate_a: float,
    rate_b: float,
    boundaries: np.ndarray,
    dts: np.ndarray,
    reps: int,
    rng: np.random.Generator,
) -> np.ndarray:
    phase_a = rng.uniform(0.0, 1.0 / rate_a, reps)
    phase_b = rng.uniform(0.0, 1.0 / rate_b, reps)
    a = staircase_rates(rate_a, boundaries, dts, phase_a)
    b = staircase_rates(rate_b, boundaries, dts, phase_b)
    return row_correlations(a, b)


def binomial_upper_tail(k: int, n: int, p: float) -> float:
    return float(
        sum(math.comb(n, value) * p**value * (1.0 - p) ** (n - value) for value in range(k, n + 1))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--reps", type=int, default=N_REPS)
    args = parser.parse_args()
    if args.reps < 1000:
        raise SystemExit("--reps must be at least 1000")

    run = Path(args.run)
    rows, meta = load(run)
    boundaries, dts, observed = retained_arrays(rows)
    observed_corr = np.corrcoef(observed)
    rng = np.random.default_rng(20260901)
    n = observed.shape[1]
    iid_sd = 1.0 / np.sqrt(max(n - 3, 1))
    pairs = []
    for i, j in itertools.combinations(range(len(LINK_ORDER)), 2):
        link_a, link_b = LINK_ORDER[i], LINK_ORDER[j]
        rate_a = float(meta["flow_engine"][link_a]["rate_pps"])
        rate_b = float(meta["flow_engine"][link_b]["rate_pps"])
        null = null_distribution(
            rate_a, rate_b, boundaries, dts, args.reps, rng
        )
        r_observed = float(observed_corr[i, j])
        low, high = np.percentile(null, (2.5, 97.5))
        abs_p95 = float(np.percentile(np.abs(null), 95))
        pairs.append(
            {
                "pair": "%s-%s" % (link_a, link_b),
                "f_a_nominal": float((rate_a * float(np.median(dts))) % 1.0),
                "f_b_nominal": float((rate_b * float(np.median(dts))) % 1.0),
                "r_observed": r_observed,
                "null_mean": float(np.mean(null)),
                "null_sd": float(np.std(null)),
                "null_p2_5": float(low),
                "null_p97_5": float(high),
                "null_abs_p95": abs_p95,
                "iid_null_sd": float(iid_sd),
                "null_inflation_vs_iid": float(np.std(null) / iid_sd),
                "observed_inside_null": bool(low <= r_observed <= high),
                "two_sided_empirical_p": float(
                    (1 + np.count_nonzero(np.abs(null) >= abs(r_observed)))
                    / (args.reps + 1)
                ),
                "abs_r_0p50_separated_from_null95": bool(abs_p95 < ABS_R_THRESHOLD),
            }
        )

    n_inside = sum(pair["observed_inside_null"] for pair in pairs)
    n_separated = sum(pair["abs_r_0p50_separated_from_null95"] for pair in pairs)
    n_outside = len(pairs) - n_inside
    model_check_p = binomial_upper_tail(n_outside, len(pairs), 0.05)
    verdict = (
        "IDENTIFIABLE_AT_ABS_R_0P50_THRESHOLD"
        if n_separated == len(pairs)
        else "NOT_IDENTIFIABLE_STATIC_QUASIPERIODIC_AT_ABS_R_0P50"
    )
    artifact = {
        "schema": "dt4n.phase_g.g1_quasiperiodic_null.v2",
        "status": "SYNTHETIC_NULL_PLUS_EXISTING_RAW_NO_NETWORK",
        "git_hash": git_hash(),
        "run": str(run),
        "n_samples": n,
        "dt_median_s": float(np.median(dts)),
        "uses_actual_sample_boundaries": True,
        "reps": args.reps,
        "abs_r_threshold": ABS_R_THRESHOLD,
        "iid_null_sd": float(iid_sd),
        "max_true_null_sd": max(pair["null_sd"] for pair in pairs),
        "n_pairs": len(pairs),
        "n_observed_inside_null": n_inside,
        "n_pairs_threshold_separated": n_separated,
        "null_model_check": {
            "n_outside_95_interval": n_outside,
            "binomial_upper_tail_p_if_calibrated": model_check_p,
            "verdict": "PASS" if model_check_p >= 0.05 else "FAIL",
        },
        "verdict": verdict,
        "pairs": pairs,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("RUN %s n=%d dt_median=%.6f" % (run, n, np.median(dts)))
    print("iid null sd(r): %.3f" % iid_sd)
    print(
        "mechanistic null max sd(r): %.3f (%.1fx iid)"
        % (artifact["max_true_null_sd"], artifact["max_true_null_sd"] / iid_sd)
    )
    print(
        "%8s %7s %7s | %7s | %8s %8s %8s | %7s %9s"
        % ("pair", "f_a", "f_b", "r_obs", "null_sd", "p2.5", "p97.5", "inside", "sep@.50")
    )
    for pair in sorted(pairs, key=lambda item: -item["null_sd"])[:12]:
        print(
            "%8s %7.3f %7.3f | %+7.3f | %8.3f %8.3f %8.3f | %7s %9s"
            % (
                pair["pair"],
                pair["f_a_nominal"],
                pair["f_b_nominal"],
                pair["r_observed"],
                pair["null_sd"],
                pair["null_p2_5"],
                pair["null_p97_5"],
                str(pair["observed_inside_null"]),
                str(pair["abs_r_0p50_separated_from_null95"]),
            )
        )
    print("\nobserved inside pairwise 95%% null: %d/%d" % (n_inside, len(pairs)))
    print("pairs separating |r|=0.50 from null95: %d/%d" % (n_separated, len(pairs)))
    print(
        "null model check: %s (outside=%d, binomial-tail p=%.4f)"
        % (artifact["null_model_check"]["verdict"], n_outside, model_check_p)
    )
    print("VERDICT: %s" % verdict)


if __name__ == "__main__":
    main()

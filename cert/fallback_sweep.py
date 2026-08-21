#!/usr/bin/env python3
"""Lesson 23.14 -- leakage-safe fallback sweep across three cells."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import baselines as BL
from cert import config_matrix as CM
from cert import fallback as FB
from cert.cell_matrices import (
    ALPHA_FAMILY,
    GAMMA_OP,
    MAIN_CELL,
    git,
    json_clean,
    pin,
)
from twin import topology_v7 as T7


AMENDMENT = "docs/phase-23/00zo-amendment-38.md"
LIFT_ARTIFACT = "results/phase-23/lift_decomposition_by_cell.json"
OUTPUT = "results/phase-23/fallback_sweep.json"
CELL_SPECS: Dict[str, Dict[str, Any]] = {
    MAIN_CELL: {
        "parquet": "results/phase-22/calib_set_v3.parquet",
        "slug": "poisson_0.925",
    },
    "poisson@0.850": {
        "parquet": "results/phase-22/calib_set_v3_poisson_0.850.parquet",
        "slug": "poisson_0.850",
    },
    "h2@0.700": {
        "parquet": "results/phase-22/calib_set_v3_h2_0.700.parquet",
        "slug": "h2_0.700",
    },
}
FAMILIES = ("F2", "F2b", "F2c", "F4", "F5", "F6")
K = len(T7.PATH_NAMES)
LEGACY_DELTA = {
    MAIN_CELL: -0.0128688493440567,
    "poisson@0.850": 0.0031202059335916,
    "h2@0.700": 0.0038662551728414,
}


def _digest_indices(indices: Iterable[int]) -> str:
    arr = np.asarray(list(indices), dtype=np.int64)
    return hashlib.sha256(arr.tobytes()).hexdigest()


@dataclass(frozen=True)
class PolicyFit:
    family: str
    params: Mapping[str, Any]
    indices_seen: frozenset[int]
    seeds_seen: frozenset[int]

    def provenance(self) -> Dict[str, Any]:
        indices = sorted(self.indices_seen)
        return {
            "family": self.family,
            "n_indices_seen": len(indices),
            "indices_seen_sha256": _digest_indices(indices),
            "index_min": min(indices) if indices else None,
            "index_max": max(indices) if indices else None,
            "seeds_seen": sorted(self.seeds_seen),
            "params": dict(self.params),
        }


def _best_constant(actions: np.ndarray) -> int:
    counts = np.bincount(np.asarray(actions, dtype=np.int64), minlength=K)
    return int(np.flatnonzero(counts == counts.max())[0])


def fit_policy(family: str, df: pd.DataFrame, allowed_idx: np.ndarray) -> PolicyFit:
    """Fit only on explicitly allowed calibration indices."""
    family = str(family)
    idx = np.asarray(allowed_idx, dtype=np.int64)
    if family not in FAMILIES:
        raise ValueError("family phai thuoc %s" % (FAMILIES,))
    seen = frozenset(int(i) for i in idx) if family in ("F2c", "F6") else frozenset()
    seeds = (
        frozenset(int(x) for x in df.iloc[idx]["seed"].unique())
        if seen
        else frozenset()
    )
    if family == "F2":
        params: Dict[str, Any] = {"action": int(FB.path_static_shortest())}
    elif family == "F2b":
        params = {"action": int(T7.PATH_NAMES.index("P3"))}
    elif family == "F2c":
        if idx.size == 0:
            raise ValueError("F2c can calibration rows")
        params = {"action": _best_constant(df.iloc[idx]["a_star"].to_numpy())}
    elif family in ("F4", "F5"):
        params = {}
    else:
        if idx.size == 0:
            raise ValueError("F6 can calibration rows")
        sub = df.iloc[idx]
        mapping: Dict[str, int] = {}
        for (z_bin, m_bin), rows in sub.groupby(["z_bin", "m_hat_bin"], sort=True):
            mapping["%d:%d" % (int(z_bin), int(m_bin))] = _best_constant(
                rows["a_star"].to_numpy()
            )
        params = {"action_by_bin": mapping, "default_action": int(FB.path_static_shortest())}
    return PolicyFit(family=family, params=params, indices_seen=seen, seeds_seen=seeds)


def score_f6(
    z_bin: np.ndarray, m_hat_bin: np.ndarray, fit: PolicyFit
) -> np.ndarray:
    """Score F6 using only the two gate bins and a frozen action map."""
    if fit.family != "F6":
        raise ValueError("score_f6 can PolicyFit F6")
    mapping = fit.params["action_by_bin"]
    default = int(fit.params["default_action"])
    return np.asarray(
        [mapping.get("%d:%d" % (int(z), int(m)), default) for z, m in zip(z_bin, m_hat_bin)],
        dtype=np.int64,
    )


def policy_probabilities(fit: PolicyFit, df: pd.DataFrame, idx: np.ndarray) -> np.ndarray:
    """Return action probabilities; F5 is evaluated without Monte Carlo noise."""
    idx = np.asarray(idx, dtype=np.int64)
    sub = df.iloc[idx]
    probs = np.zeros((len(idx), K), dtype=np.float64)
    rows = np.arange(len(idx))
    if fit.family in ("F2", "F2b", "F2c"):
        probs[:, int(fit.params["action"])] = 1.0
    elif fit.family == "F4":
        probs[rows, sub["a_rank_1"].to_numpy(np.int64)] = 1.0
    elif fit.family == "F5":
        probs[rows, sub["a_twin"].to_numpy(np.int64)] += 0.5
        probs[rows, sub["a_rank_1"].to_numpy(np.int64)] += 0.5
    elif fit.family == "F6":
        actions = score_f6(
            sub["z_bin"].to_numpy(np.int64),
            sub["m_hat_bin"].to_numpy(np.int64),
            fit,
        )
        probs[rows, actions] = 1.0
    else:  # pragma: no cover - guarded by fit_policy
        raise ValueError(fit.family)
    if not np.allclose(probs.sum(axis=1), 1.0):
        raise AssertionError("policy probabilities khong cong thanh 1")
    return probs


def expected_error(probs: np.ndarray, a_star: np.ndarray) -> np.ndarray:
    a = np.asarray(a_star, dtype=np.int64)
    return 1.0 - np.asarray(probs, dtype=np.float64)[np.arange(len(a)), a]


def c3_accept_set(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    calib = df[df["is_calib"]]
    fit = CM.fit_config(
        calib, "C3", 1.0, alpha=ALPHA_FAMILY, multiplicity="bonferroni"
    )
    qrows = CM._q_rows(df, fit["keys"], fit["_q"], 3)
    score = BL.score_C3(df, qrows)
    test = ~df["is_calib"].to_numpy(bool)
    accept = np.zeros(len(df), dtype=bool)
    accept[test] = BL._accept_at_coverage(score[test], GAMMA_OP)
    return score, accept


def _proxy_reject_indices(
    df: pd.DataFrame, score: np.ndarray, scoring_seed: int
) -> np.ndarray:
    selection = df["is_calib"].to_numpy(bool) & (
        df["seed"].to_numpy(np.int64) != int(scoring_seed)
    )
    idx = np.flatnonzero(selection)
    accept = BL._accept_at_coverage(score[idx], GAMMA_OP)
    return idx[~accept]


def build_crossfit_predictions(
    df: pd.DataFrame,
    score: np.ndarray,
    accept: np.ndarray,
) -> Dict[str, Any]:
    """Fit/select on other-seed calibration and predict each held-out test seed."""
    is_test = ~df["is_calib"].to_numpy(bool)
    test_idx = np.flatnonzero(is_test)
    family_probs = {
        family: np.full((len(df), K), np.nan, dtype=np.float32) for family in FAMILIES
    }
    selected_probs = np.full((len(df), K), np.nan, dtype=np.float32)
    fold_rows = []
    for scoring_seed in sorted(int(x) for x in df.loc[is_test, "seed"].unique()):
        scoring_idx = np.flatnonzero(is_test & (df["seed"].to_numpy(np.int64) == scoring_seed))
        train_idx = _proxy_reject_indices(df, score, scoring_seed)
        if np.intersect1d(train_idx, scoring_idx).size:
            raise AssertionError("NC-A row leakage o seed %d" % scoring_seed)
        train_seeds = set(int(x) for x in df.iloc[train_idx]["seed"].unique())
        if scoring_seed in train_seeds:
            raise AssertionError("NC-A seed leakage o seed %d" % scoring_seed)

        fits = {family: fit_policy(family, df, train_idx) for family in FAMILIES}
        train_star = df.iloc[train_idx]["a_star"].to_numpy(np.int64)
        calibration_risk = {}
        for family in FAMILIES:
            calibration_risk[family] = float(
                expected_error(
                    policy_probabilities(fits[family], df, train_idx), train_star
                ).mean()
            )
            family_probs[family][scoring_idx] = policy_probabilities(
                fits[family], df, scoring_idx
            ).astype(np.float32)
        selected = min(FAMILIES, key=lambda name: (calibration_risk[name], FAMILIES.index(name)))
        selected_probs[scoring_idx] = family_probs[selected][scoring_idx]
        fold_rows.append(
            {
                "scoring_seed": scoring_seed,
                "n_scoring_test": int(len(scoring_idx)),
                "n_selection_reject": int(len(train_idx)),
                "selection_indices_sha256": _digest_indices(train_idx),
                "selection_seeds": sorted(train_seeds),
                "row_disjoint": True,
                "seed_disjoint": True,
                "calibration_risk": calibration_risk,
                "selected_family": selected,
                "fits": {name: fit.provenance() for name, fit in fits.items()},
            }
        )
    if any(np.isnan(probs[test_idx]).any() for probs in family_probs.values()):
        raise AssertionError("family predictions thieu test row")
    if np.isnan(selected_probs[test_idx]).any():
        raise AssertionError("selected predictions thieu test row")
    return {
        "test_idx": test_idx,
        "family_probs": family_probs,
        "selected_probs": selected_probs,
        "folds": fold_rows,
        "accept": accept,
    }


def _risk_summary(
    probs: np.ndarray,
    df: pd.DataFrame,
    accept: np.ndarray,
    test_idx: np.ndarray,
) -> Dict[str, float]:
    a_star = df["a_star"].to_numpy(np.int64)
    a_twin = df["a_twin"].to_numpy(np.int64)
    test_accept = accept[test_idx]
    reject_idx = test_idx[~test_accept]
    fb_err = expected_error(probs[reject_idx], a_star[reject_idx])
    twin_wrong = (a_twin[test_idx] != a_star[test_idx]).astype(np.float64)
    c_star = float((a_twin[reject_idx] != a_star[reject_idx]).mean())
    system = twin_wrong.copy()
    system[~test_accept] = fb_err
    gap = float(fb_err.mean() - c_star)
    reject_share = float((~test_accept).mean())
    delta = float(system.mean() - twin_wrong.mean())
    return {
        "err_neo": float(twin_wrong.mean()),
        "c_star_err_twin_given_reject": c_star,
        "err_F_given_reject": float(fb_err.mean()),
        "gap_err_F_reject_minus_c_star": gap,
        "reject_share": reject_share,
        "delta_system_vs_neo": delta,
        "identity_residual": float(abs(delta - reject_share * gap)),
    }


def analyze_cell(cell: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    spec = CELL_SPECS[cell]
    df = pd.read_parquet(spec["parquet"])
    score, accept = c3_accept_set(df)
    crossfit = build_crossfit_predictions(df, score, accept)
    test_idx = crossfit["test_idx"]
    families = {
        family: _risk_summary(crossfit["family_probs"][family], df, accept, test_idx)
        for family in FAMILIES
    }
    selected = _risk_summary(crossfit["selected_probs"], df, accept, test_idx)
    selected["families_by_fold"] = {
        str(row["scoring_seed"]): row["selected_family"] for row in crossfit["folds"]
    }
    f2_gap = abs(families["F2"]["delta_system_vs_neo"] - LEGACY_DELTA[cell])
    controls = {
        "NC_A_all_row_disjoint": bool(all(row["row_disjoint"] for row in crossfit["folds"])),
        "NC_A_all_seed_disjoint": bool(all(row["seed_disjoint"] for row in crossfit["folds"])),
        "NC_B_F6_information": ["z_bin", "m_hat_bin", "frozen_action_map"],
        "NC_C_F2_expected_delta": LEGACY_DELTA[cell],
        "NC_C_F2_absolute_gap": float(f2_gap),
        "NC_C_F2_reproduced_at_1e_12": bool(f2_gap <= 1e-12),
        "all_identity_residual_le_1e_12": bool(
            max(row["identity_residual"] for row in [*families.values(), selected]) <= 1e-12
        ),
    }
    if not all(
        controls[key]
        for key in (
            "NC_A_all_row_disjoint",
            "NC_A_all_seed_disjoint",
            "NC_C_F2_reproduced_at_1e_12",
            "all_identity_residual_le_1e_12",
        )
    ):
        raise AssertionError("cell controls failed for %s: %s" % (cell, controls))
    report = {
        "cell": cell,
        "n_rows": int(len(df)),
        "n_test": int(len(test_idx)),
        "families": families,
        "calibration_selected": selected,
        "folds": crossfit["folds"],
        "controls": controls,
    }
    return json_clean(report), crossfit


def run() -> Dict[str, Any]:
    with open(LIFT_ARTIFACT, "r", encoding="utf-8") as handle:
        lift = json.load(handle)
    cells = {}
    for cell in CELL_SPECS:
        report, _crossfit = analyze_cell(cell)
        cells[cell] = report
    heldout = ("poisson@0.850", "h2@0.700")
    winners = [
        family
        for family in FAMILIES
        if all(cells[cell]["families"][family]["gap_err_F_reject_minus_c_star"] < 0.0 for cell in heldout)
    ]
    selected_gaps = {
        cell: float(cells[cell]["calibration_selected"]["gap_err_F_reject_minus_c_star"])
        for cell in CELL_SPECS
    }
    selected_deltas = {
        cell: float(cells[cell]["calibration_selected"]["delta_system_vs_neo"])
        for cell in CELL_SPECS
    }
    m40 = float(lift["spreads"]["prior_deg"]["max_over_min"])
    m41 = float(lift["spreads"]["twin_deg"]["max_over_min"])
    report = {
        "schema": "fallback_sweep/v1",
        "lesson": "23.14",
        "families": list(FAMILIES),
        "selection": "leave_one_seed_out_calibration_only",
        "cells": cells,
        "metrics": {
            "M_40_prior_deg_spread": m40,
            "M_41_twin_deg_spread": m41,
            "M_42_poisson_0.850_selected_gap": selected_gaps["poisson@0.850"],
            "M_43_h2_0.700_selected_gap": selected_gaps["h2@0.700"],
            "M_44_common_winning_families_heldout": winners,
            "M_45_selected_delta_by_cell": selected_deltas,
        },
        "verdict": {
            "M_40_in_3_0_6_0": bool(3.0 <= m40 <= 6.0),
            "M_41_in_1_00_1_15": bool(1.00 <= m41 <= 1.15),
            "M_42_in_minus_0_05_0": bool(-0.05 <= selected_gaps["poisson@0.850"] <= 0.0),
            "M_43_in_minus_0_05_0": bool(-0.05 <= selected_gaps["h2@0.700"] <= 0.0),
            "M_44_common_family_exists": bool(winners),
            "M_45_selected_delta_negative_all_cells": bool(
                all(delta < 0.0 for delta in selected_deltas.values())
            ),
        },
        "provenance": {
            "script": "cert/fallback_sweep.py",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": bool(git("git", "status", "--porcelain", "--untracked-files=no")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "inputs": [pin(AMENDMENT), pin(LIFT_ARTIFACT)]
            + [pin(spec["parquet"]) for spec in CELL_SPECS.values()],
        },
    }
    return json_clean(report)


def print_report(report: Mapping[str, Any]) -> None:
    print("=== LESSON 23.14: FALLBACK SWEEP ===")
    for cell, row in report["cells"].items():
        selected = row["calibration_selected"]
        folds = ",".join(
            "%s:%s" % (seed, family)
            for seed, family in selected["families_by_fold"].items()
        )
        print(
            "%-16s selected_gap=%+.6f Delta=%+.6f folds=%s"
            % (
                cell,
                selected["gap_err_F_reject_minus_c_star"],
                selected["delta_system_vs_neo"],
                folds,
            )
        )
    print("M-44 common winners=%s" % report["metrics"]["M_44_common_winning_families_heldout"])
    print("verdict=%s" % json.dumps(report["verdict"], sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args(argv)
    report = run()
    print_report(report)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("artifact -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

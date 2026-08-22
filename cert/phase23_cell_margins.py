#!/usr/bin/env python3
"""G23-17a/G23-17b/G23-17c audits before Phase 23.4 sweeps."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from cert import fallback as FB


DEFAULT_CELLS: Mapping[str, str] = {
    "poisson@0.925": "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.925.parquet",
    "poisson@0.850": "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.850.parquet",
    "h2@0.700": "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.700.parquet",
}
DEFAULT_OUT_G23_17A_JSON = "results/SUPERSEDED/phase-23/g23_17a_cell_margins.json"
DEFAULT_OUT_G23_17B_JSON = "results/SUPERSEDED/phase-23/g23_17b_code_sanity.json"
DEFAULT_OUT_G23_17C_JSON = "results/SUPERSEDED/phase-23/g23_17c_scale_and_sla.json"


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _json_clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_clean(x) for x in value]
    if isinstance(value, tuple):
        return [_json_clean(x) for x in value]
    if isinstance(value, np.ndarray):
        return _json_clean(value.tolist())
    if isinstance(value, np.generic):
        return _json_clean(value.item())
    return value


def _meta_path(path: str) -> str:
    if not path.endswith(".parquet"):
        raise ValueError("artifact path must end with .parquet: %s" % path)
    return path[:-8] + ".json"


def _load_meta(path: str) -> Dict[str, Any]:
    meta_path = _meta_path(path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return {
        "path": meta_path,
        "sha256": _sha256(meta_path),
        "t_delay_ms": float(meta["t_delay_ms"]),
        "t_loss": float(meta["t_loss"]),
        "eps_regret_ms": float(meta["eps_regret_ms"]),
    }


def _select_rowset(df: pd.DataFrame, rowset: str) -> pd.DataFrame:
    if rowset == "test":
        return df[~df["is_calib"]]
    if rowset == "calib":
        return df[df["is_calib"]]
    if rowset == "all":
        return df
    raise ValueError("rowset must be one of: test, calib, all")


def cell_margin_row(cell: str, path: str, rowset: str = "test") -> Dict[str, Any]:
    """Compute the three marginal probabilities behind the break-even identity."""
    cols = ["is_calib", "block_id", "a_twin", "a_star"]
    df = pd.read_parquet(path, columns=cols)
    d = _select_rowset(df, rowset)

    p1 = int(FB.path_static_shortest())
    a_twin = d["a_twin"].to_numpy(np.int64)
    a_star = d["a_star"].to_numpy(np.int64)
    twin_wrong = a_twin != a_star
    p1_wrong = a_star != p1
    both_wrong = twin_wrong & p1_wrong
    both = float(both_wrong.mean())
    mass_pos = float(p1_wrong.mean()) - both
    mass_neg = float(twin_wrong.mean()) - both
    return {
        "cell": str(cell),
        "artifact": str(path),
        "artifact_sha256": _sha256(path),
        "rowset": str(rowset),
        "n_rows_total": int(len(df)),
        "n_rows": int(len(d)),
        "n_blocks": int(d["block_id"].nunique()),
        "static_path": p1,
        "err_neo": float(twin_wrong.mean()),
        "err_P1": float(p1_wrong.mean()),
        "both_wrong": both,
        "mass_pos": mass_pos,
        "mass_neg": mass_neg,
        "D_mass_pos_over_mass_neg": float(mass_pos / max(mass_neg, 1e-12)),
        "swing_mass_pos_minus_mass_neg": float(mass_pos - mass_neg),
    }


def run_report(cells: Mapping[str, str], rowset: str = "test") -> Dict[str, Any]:
    rows = [cell_margin_row(cell, path, rowset=rowset) for cell, path in cells.items()]
    ref = next(row for row in rows if row["cell"] == "poisson@0.925")
    return {
        "gate": "G23-17a",
        "rowset": str(rowset),
        "definition": (
            "mass_pos=P(twin correct, P1 wrong); "
            "mass_neg=P(twin wrong, P1 correct); "
            "swing=mass_pos-mass_neg."
        ),
        "identity": "random-reject delta at reject share r is r * swing.",
        "reference_poisson_0.925": {
            "swing": ref["swing_mass_pos_minus_mass_neg"],
            "D": ref["D_mass_pos_over_mass_neg"],
        },
        "rows": rows,
    }


def cell_code_sanity_row(cell: str, path: str, rowset: str = "test") -> Dict[str, Any]:
    """G23-17b: sanity checks before trusting the G23-17a marginal table."""
    cols = ["is_calib", "block_id", "a_twin", "a_star", "m_true_1", "m_hat_1"]
    df = pd.read_parquet(path, columns=cols)
    d = _select_rowset(df, rowset)
    p1 = int(FB.path_static_shortest())
    a_star = d["a_star"].to_numpy(np.int64)
    a_twin = d["a_twin"].to_numpy(np.int64)
    star_dist = np.bincount(a_star, minlength=FB.K_ACTIONS).astype(np.float64)
    star_dist = star_dist / max(float(len(a_star)), 1.0)
    twin_dist = np.bincount(a_twin, minlength=FB.K_ACTIONS).astype(np.float64)
    twin_dist = twin_dist / max(float(len(a_twin)), 1.0)
    return {
        "cell": str(cell),
        "artifact": str(path),
        "artifact_sha256": _sha256(path),
        "rowset": str(rowset),
        "n_rows_total": int(len(df)),
        "n_rows": int(len(d)),
        "n_blocks": int(d["block_id"].nunique()),
        "static_path": p1,
        "p_a_star_eq_p1": float((a_star == p1).mean()),
        "p_a_twin_eq_p1": float((a_twin == p1).mean()),
        "a_star_distribution": [float(x) for x in star_dist],
        "a_twin_distribution": [float(x) for x in twin_dist],
        "median_m_true_1": float(np.median(d["m_true_1"].to_numpy(np.float64))),
        "median_m_hat_1": float(np.median(d["m_hat_1"].to_numpy(np.float64))),
    }


def run_code_sanity_report(
    cells: Mapping[str, str],
    rowset: str = "test",
) -> Dict[str, Any]:
    rows = [cell_code_sanity_row(cell, path, rowset=rowset) for cell, path in cells.items()]
    by_cell = {row["cell"]: row for row in rows}
    ref = by_cell["poisson@0.925"]
    h2 = by_cell["h2@0.700"]
    p1_values = {int(row["static_path"]) for row in rows}
    return {
        "gate": "G23-17b",
        "rowset": str(rowset),
        "purpose": (
            "Rule out implementation mistakes before interpreting the G23-17a "
            "drop in err_P1 for h2@0.700."
        ),
        "checks": {
            "static_path_same_across_cells": bool(len(p1_values) == 1),
            "static_path_values": sorted(int(x) for x in p1_values),
            "h2_median_m_true_1_at_least_30pct_lower_vs_poisson_0p925": bool(
                float(h2["median_m_true_1"]) <= 0.70 * float(ref["median_m_true_1"])
            ),
            "h2_p_a_star_eq_p1_above_poisson_0p925": bool(
                float(h2["p_a_star_eq_p1"]) > float(ref["p_a_star_eq_p1"])
            ),
        },
        "reference_poisson_0.925": {
            "p_a_star_eq_p1": ref["p_a_star_eq_p1"],
            "median_m_true_1": ref["median_m_true_1"],
            "median_m_hat_1": ref["median_m_hat_1"],
        },
        "h2_vs_poisson_0.925": {
            "p_a_star_eq_p1_delta": float(
                h2["p_a_star_eq_p1"] - ref["p_a_star_eq_p1"]
            ),
            "median_m_true_1_ratio": float(
                h2["median_m_true_1"] / max(float(ref["median_m_true_1"]), 1e-12)
            ),
            "median_m_hat_1_ratio": float(
                h2["median_m_hat_1"] / max(float(ref["median_m_hat_1"]), 1e-12)
            ),
        },
        "rows": rows,
    }


def cell_scale_sla_row(cell: str, path: str, rowset: str = "test") -> Dict[str, Any]:
    """G23-17c: compare regret scale, error, and SLA thresholds across cells."""
    cols = [
        "is_calib",
        "block_id",
        "a_twin",
        "a_star",
        "a1",
        "a_rank_1",
        "a_rank_2",
        "a_rank_3",
        "m_true_1",
        "m_true_2",
        "m_true_3",
    ]
    df = pd.read_parquet(path, columns=cols)
    d = _select_rowset(df, rowset)
    a_twin = d["a_twin"].to_numpy(np.int64)
    err_neo = float(FB.loss_of(d, a_twin, "err").mean())
    regret_neo = float(FB.loss_of(d, a_twin, "regret").mean())
    median_m_true_1 = float(np.median(d["m_true_1"].to_numpy(np.float64)))
    penalty_per_error = float(regret_neo / max(err_neo, 1e-12))
    normpen_per_margin = float(penalty_per_error / max(median_m_true_1, 1e-12))
    meta = _load_meta(path)
    return {
        "cell": str(cell),
        "artifact": str(path),
        "artifact_sha256": _sha256(path),
        "metadata": meta,
        "rowset": str(rowset),
        "n_rows_total": int(len(df)),
        "n_rows": int(len(d)),
        "n_blocks": int(d["block_id"].nunique()),
        "err_neo": err_neo,
        "regret_neo": regret_neo,
        "penalty_per_error": penalty_per_error,
        "median_m_true_1": median_m_true_1,
        "normpen_per_margin": normpen_per_margin,
        "t_delay_ms": float(meta["t_delay_ms"]),
        "t_loss": float(meta["t_loss"]),
        "eps_regret_ms": float(meta["eps_regret_ms"]),
    }


def run_scale_sla_report(
    cells: Mapping[str, str],
    rowset: str = "test",
    ratio_tol: float = 0.15,
) -> Dict[str, Any]:
    rows = [cell_scale_sla_row(cell, path, rowset=rowset) for cell, path in cells.items()]
    by_cell = {row["cell"]: row for row in rows}
    ref = by_cell["poisson@0.925"]
    enriched = []
    for row in rows:
        r = dict(row)
        r["regret_neo_ratio_vs_poisson_0p925"] = float(
            r["regret_neo"] / max(float(ref["regret_neo"]), 1e-12)
        )
        r["err_neo_ratio_vs_poisson_0p925"] = float(
            r["err_neo"] / max(float(ref["err_neo"]), 1e-12)
        )
        r["median_m_true_1_ratio_vs_poisson_0p925"] = float(
            r["median_m_true_1"] / max(float(ref["median_m_true_1"]), 1e-12)
        )
        r["normpen_ratio_vs_poisson_0p925"] = float(
            r["normpen_per_margin"] / max(float(ref["normpen_per_margin"]), 1e-12)
        )
        r["three_factor_regret_ratio_product"] = float(
            r["err_neo_ratio_vs_poisson_0p925"]
            * r["normpen_ratio_vs_poisson_0p925"]
            * r["median_m_true_1_ratio_vs_poisson_0p925"]
        )
        r["three_factor_abs_error_vs_regret_ratio"] = float(
            abs(
                r["three_factor_regret_ratio_product"]
                - r["regret_neo_ratio_vs_poisson_0p925"]
            )
        )
        ratio_gap = abs(
            float(r["regret_neo_ratio_vs_poisson_0p925"])
            - float(r["median_m_true_1_ratio_vs_poisson_0p925"])
        )
        r["abs_ratio_gap"] = float(ratio_gap)
        r["ratio_gap_fraction_of_m_true_ratio"] = float(
            ratio_gap / max(abs(float(r["median_m_true_1_ratio_vs_poisson_0p925"])), 1e-12)
        )
        r["regret_ratio_matches_m_true_ratio_within_tol"] = bool(
            r["ratio_gap_fraction_of_m_true_ratio"] <= float(ratio_tol)
        )
        enriched.append(r)

    t_delay_values = [float(row["t_delay_ms"]) for row in enriched]
    t_loss_values = [float(row["t_loss"]) for row in enriched]
    t_delay_same = bool(np.allclose(t_delay_values, t_delay_values[0], rtol=0.0, atol=1e-12))
    t_loss_same = bool(np.allclose(t_loss_values, t_loss_values[0], rtol=0.0, atol=1e-12))
    poisson_0850 = by_cell["poisson@0.850"]["cell"]
    poisson_0850_row = next(row for row in enriched if row["cell"] == poisson_0850)
    h2_row = next(row for row in enriched if row["cell"] == "h2@0.700")
    max_decomp_error = max(
        float(row["three_factor_abs_error_vs_regret_ratio"]) for row in enriched
    )
    return {
        "gate": "G23-17c",
        "rowset": str(rowset),
        "ratio_tolerance": float(ratio_tol),
        "purpose": (
            "Check whether cross-cell regret differences track the true-margin "
            "scale, decompose regret ratios into true-effect and unit factors, "
            "and whether SLA thresholds are comparable across cells."
        ),
        "decomposition_identity": (
            "regret_ratio = err_ratio * normpen_ratio * scale_ratio, where "
            "normpen = (regret / err) / median_m_true_1 and scale_ratio is "
            "median_m_true_1_ratio_vs_poisson_0p925."
        ),
        "checks": {
            "poisson_0p850_regret_ratio_matches_m_true_ratio_within_tol": bool(
                poisson_0850_row["regret_ratio_matches_m_true_ratio_within_tol"]
            ),
            "all_regret_ratios_match_m_true_ratios_within_tol": bool(
                all(row["regret_ratio_matches_m_true_ratio_within_tol"] for row in enriched)
            ),
            "three_factor_identity_matches_regret_ratio": bool(max_decomp_error <= 1e-12),
            "poisson_0p850_true_effect_ratios_near_one_within_tol": bool(
                abs(float(poisson_0850_row["err_neo_ratio_vs_poisson_0p925"]) - 1.0)
                <= float(ratio_tol)
                and abs(float(poisson_0850_row["normpen_ratio_vs_poisson_0p925"]) - 1.0)
                <= float(ratio_tol)
            ),
            "h2_true_effect_ratios_both_below_0p70": bool(
                float(h2_row["err_neo_ratio_vs_poisson_0p925"]) < 0.70
                and float(h2_row["normpen_ratio_vs_poisson_0p925"]) < 0.70
            ),
            "sla_t_delay_same_across_cells": t_delay_same,
            "sla_t_loss_same_across_cells": t_loss_same,
            "sla_thresholds_same_across_cells": bool(t_delay_same and t_loss_same),
        },
        "mechanism_8_summary": {
            "poisson_0p850": (
                "err and normalized penalty ratios are near 1, while scale is "
                "near the regret ratio; the regret drop is a unit artifact for "
                "the poisson control pair."
            ),
            "h2_0p700": (
                "err and normalized penalty ratios are both about 0.55, while "
                "scale is near 0.89; most of the regret drop is a real decision "
                "effect, not a unit artifact."
            ),
        },
        "interpretation": {
            "regret_cross_cell": (
                "Raw regret is not a standalone cross-cell headline. Report "
                "the three-factor decomposition before deciding whether a "
                "difference is a unit artifact or a real decision effect."
            ),
            "sla_cross_cell": (
                "SLA thresholds differ across cells; SLA is not a clean cross-cell "
                "headline unless thresholds are fixed or a separate normalization "
                "is preregistered."
            ),
        },
        "rows": enriched,
    }


def write_json_report(report: Dict[str, Any], out_json: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    payload = dict(report)
    payload["provenance"] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "git_hash": _git("git", "rev-parse", "HEAD"),
        "git_dirty_before_write": bool(_git("git", "status", "--porcelain")),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(_json_clean(payload), f, indent=2, sort_keys=True)
        f.write("\n")


def _print_g23_17a_summary(report: Dict[str, Any], out_json: str) -> None:
    print("=== G23-17a: marginal break-even probabilities before Phase 23.4 ===")
    print("rowset=%s" % report["rowset"])
    print(
        "%-16s %10s %10s %10s %10s %10s %8s %10s"
        % ("cell", "err_neo", "err_P1", "both", "mass_pos", "mass_neg", "D", "swing")
    )
    for row in report["rows"]:
        print(
            "%-16s %10.6f %10.6f %10.6f %10.6f %10.6f %8.3f %10.6f"
            % (
                row["cell"],
                row["err_neo"],
                row["err_P1"],
                row["both_wrong"],
                row["mass_pos"],
                row["mass_neg"],
                row["D_mass_pos_over_mass_neg"],
                row["swing_mass_pos_minus_mass_neg"],
            )
        )
    print("wrote_json=%s" % out_json)


def _fmt_dist(values: Sequence[float]) -> str:
    return "[" + ",".join("%.4f" % float(x) for x in values) + "]"


def _print_g23_17b_summary(report: Dict[str, Any], out_json: str) -> None:
    print("=== G23-17b: code sanity before trusting G23-17a ===")
    print("rowset=%s" % report["rowset"])
    print(
        "%-16s %4s %10s %-29s %14s %14s"
        % ("cell", "P1", "a*=P1", "a*dist", "med_m_true_1", "med_m_hat_1")
    )
    for row in report["rows"]:
        print(
            "%-16s %4d %10.6f %-29s %14.6f %14.6f"
            % (
                row["cell"],
                row["static_path"],
                row["p_a_star_eq_p1"],
                _fmt_dist(row["a_star_distribution"]),
                row["median_m_true_1"],
                row["median_m_hat_1"],
            )
        )
    checks = report["checks"]
    print()
    print("checks:")
    for key in (
        "static_path_same_across_cells",
        "h2_median_m_true_1_at_least_30pct_lower_vs_poisson_0p925",
        "h2_p_a_star_eq_p1_above_poisson_0p925",
    ):
        print("  %s=%s" % (key, checks[key]))
    h2 = report["h2_vs_poisson_0.925"]
    print(
        "h2_vs_poisson_0.925: p_a_star_eq_p1_delta=%+.6f "
        "median_m_true_1_ratio=%.6f median_m_hat_1_ratio=%.6f"
        % (
            h2["p_a_star_eq_p1_delta"],
            h2["median_m_true_1_ratio"],
            h2["median_m_hat_1_ratio"],
        )
    )
    print("wrote_json=%s" % out_json)


def _print_g23_17c_summary(report: Dict[str, Any], out_json: str) -> None:
    print("=== G23-17c: regret scale and SLA threshold comparability ===")
    print("rowset=%s ratio_tol=%.3f" % (report["rowset"], report["ratio_tolerance"]))
    print(
        "%-16s %12s %9s %12s %9s %8s %8s %8s"
        % ("cell", "regret_neo", "ratio", "med_m_true", "ratio", "gap_pct", "t_d", "t_l")
    )
    for row in report["rows"]:
        print(
            "%-16s %12.6f %9.4f %12.6f %9.4f %8.3f %8.3f %8.5f"
            % (
                row["cell"],
                row["regret_neo"],
                row["regret_neo_ratio_vs_poisson_0p925"],
                row["median_m_true_1"],
                row["median_m_true_1_ratio_vs_poisson_0p925"],
                100.0 * row["ratio_gap_fraction_of_m_true_ratio"],
                row["t_delay_ms"],
                row["t_loss"],
            )
        )
    print()
    print("Mechanism #8 decomposition vs poisson@0.925")
    print(
        "%-16s %8s %10s %8s %10s %9s"
        % ("cell", "err_r", "normpen_r", "scale_r", "product", "regret_r")
    )
    for row in report["rows"]:
        print(
            "%-16s %8.4f %10.4f %8.4f %10.5f %9.4f"
            % (
                row["cell"],
                row["err_neo_ratio_vs_poisson_0p925"],
                row["normpen_ratio_vs_poisson_0p925"],
                row["median_m_true_1_ratio_vs_poisson_0p925"],
                row["three_factor_regret_ratio_product"],
                row["regret_neo_ratio_vs_poisson_0p925"],
            )
        )
    print()
    print("checks:")
    for key, value in report["checks"].items():
        print("  %s=%s" % (key, value))
    print("wrote_json=%s" % out_json)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--audit",
        choices=("g23-17a", "g23-17b", "g23-17c"),
        default="g23-17a",
    )
    parser.add_argument("--rowset", choices=("test", "calib", "all"), default="test")
    parser.add_argument("--out-json", default=None)
    args = parser.parse_args(argv)

    if args.audit == "g23-17c":
        report = run_scale_sla_report(DEFAULT_CELLS, rowset=args.rowset)
        out_json = args.out_json or DEFAULT_OUT_G23_17C_JSON
        write_json_report(report, out_json)
        _print_g23_17c_summary(report, out_json)
        return 0

    if args.audit == "g23-17b":
        report = run_code_sanity_report(DEFAULT_CELLS, rowset=args.rowset)
        out_json = args.out_json or DEFAULT_OUT_G23_17B_JSON
        write_json_report(report, out_json)
        _print_g23_17b_summary(report, out_json)
        return 0

    report = run_report(DEFAULT_CELLS, rowset=args.rowset)
    out_json = args.out_json or DEFAULT_OUT_G23_17A_JSON
    write_json_report(report, out_json)
    _print_g23_17a_summary(report, out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phase 23 cross-cell summaries and G23-23 lift law gate."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence

import numpy as np


DEFAULT_G23_17A = "results/phase-23/g23_17a_cell_margins.json"
DEFAULT_AUDITS: Mapping[str, str] = {
    "poisson@0.925": "results/phase-23/baseline_c3_b2_audit_poisson_0.925_C3_static.json",
    "poisson@0.850": "results/phase-23/baseline_c3_b2_audit_poisson_0.850_C3_static.json",
    "h2@0.700": "results/phase-23/baseline_c3_b2_audit_h2_0.700_C3_static.json",
}
DEFAULT_BASELINES: Mapping[str, str] = {
    "poisson@0.925": "results/phase-23/baseline_rankings_poisson_0.925_C3_static.json",
    "poisson@0.850": "results/phase-23/baseline_rankings_poisson_0.850_C3_static.json",
    "h2@0.700": "results/phase-23/baseline_rankings_h2_0.700_C3_static.json",
}
DEFAULT_LIFT_JSON = "results/phase-23/g23_23_lift_law.json"
DEFAULT_SUMMARY_JSON = "results/phase-23/cross_cell_summary.json"
DEFAULT_SUMMARY_CSV = "results/phase-23/cross_cell_summary.csv"
DEFAULT_PLOT = "results/phase-23/cross_cell_err_panels.png"
SELECTORS_AT_TARGET = (
    "B1_random",
    "B2_constant_gap",
    "B3_aoi",
    "B5_relative_margin",
    "C3_conformal",
)
PLOT_SELECTORS = ("C3_conformal", "B2_constant_gap", "B3_aoi", "B6_sys_oracle")


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return "unknown"


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
    if isinstance(value, float) and not np.isfinite(value):
        if np.isposinf(value):
            return "inf"
        if np.isneginf(value):
            return "-inf"
        return None
    return value


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(payload: Mapping[str, Any], out_json: str) -> None:
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    data = dict(payload)
    data["provenance"] = {
        "script": "cert/phase23_cross_cell.py",
        "git_hash": _git("git", "rev-parse", "HEAD"),
        "git_dirty_before_write": bool(_git("git", "status", "--porcelain")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(_json_clean(data), f, indent=2, sort_keys=True)
        f.write("\n")


def _sign(x: float, tol: float) -> int:
    if float(x) > float(tol):
        return 1
    if float(x) < -float(tol):
        return -1
    return 0


def _cell_margins(g23_17a: Mapping[str, Any]) -> Dict[str, Dict[str, float]]:
    out = {}
    for row in g23_17a["rows"]:
        err_neo = float(row["err_neo"])
        err_p1 = float(row["err_P1"])
        out[str(row["cell"])] = {
            "err_neo": err_neo,
            "err_P1": err_p1,
            "swing": float(err_p1 - err_neo),
        }
    return out


def lift_law_report(
    audit_paths: Mapping[str, str] = DEFAULT_AUDITS,
    g23_17a_path: str = DEFAULT_G23_17A,
    tol: float = 1e-9,
) -> Dict[str, Any]:
    """G23-23: benefit iff lift exceeds swing on the rejected set."""
    margins = _cell_margins(_load_json(g23_17a_path))
    rows = []
    max_abs_delta_error = 0.0
    for expected_cell, path in audit_paths.items():
        audit = _load_json(path)
        cell = str(audit["cell"])
        if cell != str(expected_cell):
            raise ValueError("audit %s has cell=%s, expected %s" % (path, cell, expected_cell))
        m = margins[cell]
        err_neo = float(m["err_neo"])
        err_p1 = float(m["err_P1"])
        swing = float(m["swing"])
        for row in audit["break_even_identity_at_078"]["rows"]:
            twin_deg = float(row["err_twin_given_reject"]) - err_neo
            prior_deg = float(row["err_p1_given_reject"]) - err_p1
            lift = float(twin_deg - prior_deg)
            lift_minus_swing = float(lift - swing)
            delta_expected = float(row["reject_share"]) * float(swing - lift)
            delta = float(row["delta_vs_anchor"])
            abs_err = abs(delta - delta_expected)
            max_abs_delta_error = max(max_abs_delta_error, abs_err)
            rows.append(
                {
                    "cell": cell,
                    "selector": str(row["selector"]),
                    "err_neo": err_neo,
                    "err_P1": err_p1,
                    "swing": swing,
                    "err_twin_given_reject": float(row["err_twin_given_reject"]),
                    "err_p1_given_reject": float(row["err_p1_given_reject"]),
                    "twin_deg": float(twin_deg),
                    "prior_deg": float(prior_deg),
                    "lift": lift,
                    "lift_minus_swing": lift_minus_swing,
                    "reject_share": float(row["reject_share"]),
                    "delta_vs_anchor": delta,
                    "delta_expected_from_lift": delta_expected,
                    "abs_delta_identity_error": abs_err,
                    "beneficial_by_lift": bool(lift_minus_swing > 0.0),
                    "beneficial_by_delta": bool(delta < 0.0),
                    "sign_lift_minus_swing": _sign(lift_minus_swing, tol),
                    "sign_minus_delta": _sign(-delta, tol),
                    "sign_match": bool(
                        _sign(lift_minus_swing, tol) == _sign(-delta, tol)
                    ),
                }
            )
    return {
        "gate": "G23-23",
        "definition": (
            "twin_deg=err_twin|reject-err_neo; "
            "prior_deg=err_P1|reject-err_P1; lift=twin_deg-prior_deg; "
            "benefit iff lift > swing=err_P1-err_neo."
        ),
        "identity": "delta_vs_anchor = reject_share * (swing - lift).",
        "tolerance": float(tol),
        "checks": {
            "max_abs_delta_identity_error": float(max_abs_delta_error),
            "identity_pass": bool(max_abs_delta_error <= float(tol)),
            "all_signs_match": bool(all(row["sign_match"] for row in rows)),
            "n_rows": int(len(rows)),
            "c3_fails_both_new_cells_at_078": bool(
                all(
                    (
                        row["selector"] != "C3_conformal"
                        or row["cell"] == "poisson@0.925"
                        or row["delta_vs_anchor"] > 0.0
                    )
                    for row in rows
                )
            ),
            "b3_beats_h2_at_078": bool(
                any(
                    row["cell"] == "h2@0.700"
                    and row["selector"] == "B3_aoi"
                    and row["delta_vs_anchor"] < 0.0
                    for row in rows
                )
            ),
        },
        "rows": rows,
    }


def _band_payload(band: Mapping[str, Any]) -> Dict[str, Any]:
    if not bool(band.get("beneficial", False)):
        return {
            "beneficial": False,
            "band_low": None,
            "band_high": None,
            "improvement_area": float(band.get("improvement_area", 0.0)),
            "partial_aurc_060_100": None,
            "partial_aurc_060_100_ratio_vs_anchor": None,
        }
    return {
        "beneficial": True,
        "band_low": float(band["band_low"]),
        "band_high": float(band["band_high"]),
        "improvement_area": float(band["improvement_area"]),
        "partial_aurc_060_100": float(band["partial_aurc_060_100"]),
        "partial_aurc_060_100_ratio_vs_anchor": float(
            band["partial_aurc_060_100_ratio_vs_anchor"]
        ),
    }


def summary_report(
    baseline_paths: Mapping[str, str] = DEFAULT_BASELINES,
    audit_paths: Mapping[str, str] = DEFAULT_AUDITS,
) -> Dict[str, Any]:
    """Build the four-column C3 summary and selector table for Lesson 23.4."""
    rows = []
    selector_rows = []
    for cell, baseline_path in baseline_paths.items():
        baseline = _load_json(baseline_path)
        audit = _load_json(audit_paths[cell])
        anchor_err = float(baseline["anchor_always_trust"]["err"])
        c3_band = _band_payload(baseline["beneficial_band_err"]["C3_conformal"])
        c3_target = baseline["at_target_coverage"]["C3_conformal"]
        rows.append(
            {
                "cell": cell,
                "c3_beneficial": bool(c3_band["beneficial"]),
                "c3_band_low": c3_band["band_low"],
                "c3_band_high": c3_band["band_high"],
                "c3_improvement_area": c3_band["improvement_area"],
                "c3_partial_aurc_060_100": c3_band["partial_aurc_060_100"],
                "c3_partial_aurc_060_100_ratio_vs_anchor": c3_band[
                    "partial_aurc_060_100_ratio_vs_anchor"
                ],
                "gap_closed_C3_vs_B6sys_at_078": float(
                    audit["gap_closed_by_C3_vs_B6sys_at_078"]
                ),
                "anchor_err": anchor_err,
                "c3_err_system_at_078": float(c3_target["err_system"]),
                "c3_delta_vs_anchor_at_078": float(c3_target["err_delta_vs_anchor"]),
            }
        )
        candidates = []
        for selector in SELECTORS_AT_TARGET:
            if selector not in baseline["at_target_coverage"]:
                continue
            at = baseline["at_target_coverage"][selector]
            band = _band_payload(baseline["beneficial_band_err"][selector])
            rec = {
                "cell": cell,
                "selector": selector,
                "err_system_at_078": float(at["err_system"]),
                "err_delta_vs_anchor_at_078": float(at["err_delta_vs_anchor"]),
                "beneficial_band": bool(band["beneficial"]),
                "band_low": band["band_low"],
                "band_high": band["band_high"],
            }
            selector_rows.append(rec)
            candidates.append(rec)
        best = min(candidates, key=lambda r: r["err_system_at_078"])
        rows[-1]["best_selector_at_078"] = best["selector"]
        rows[-1]["best_err_system_at_078"] = best["err_system_at_078"]
        rows[-1]["best_delta_vs_anchor_at_078"] = best["err_delta_vs_anchor_at_078"]
    return {
        "table": "cross-cell C3 four-column summary",
        "rows": rows,
        "selector_rows_at_078": selector_rows,
    }


def write_summary_csv(report: Mapping[str, Any], out_csv: str) -> None:
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    fields = [
        "cell",
        "c3_beneficial",
        "c3_band_low",
        "c3_band_high",
        "c3_improvement_area",
        "c3_partial_aurc_060_100",
        "gap_closed_C3_vs_B6sys_at_078",
        "best_selector_at_078",
        "best_delta_vs_anchor_at_078",
    ]
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({field: row.get(field) for field in fields})


def write_err_panels(
    baseline_paths: Mapping[str, str],
    out_png: str,
    selectors: Sequence[str] = PLOT_SELECTORS,
) -> None:
    import matplotlib.pyplot as plt

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0), sharey=False)
    for ax, (cell, path) in zip(axes, baseline_paths.items()):
        baseline = _load_json(path)
        anchor = float(baseline["anchor_always_trust"]["err"])
        ax.axhline(anchor, color="black", linewidth=1.0, linestyle="--", label="neo")
        for selector in selectors:
            if selector not in baseline["sweeps"]:
                continue
            sweep = baseline["sweeps"][selector]
            x = [float(row["coverage"]) for row in sweep]
            y = [float(row["err_system"]) for row in sweep]
            ax.plot(x, y, linewidth=1.5, label=selector.replace("_", " "))
        ax.set_title(cell)
        ax.set_xlabel("coverage")
        ax.set_ylabel("err_system")
        ax.grid(True, linewidth=0.4, alpha=0.35)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(out_png, dpi=180)
    plt.close(fig)


def _parse_mapping(values: Sequence[str] | None, default: Mapping[str, str]) -> Dict[str, str]:
    if not values:
        return dict(default)
    out = {}
    for value in values:
        if "=" not in value:
            raise ValueError("mapping values must be cell=path, got %r" % value)
        cell, path = value.split("=", 1)
        out[str(cell)] = str(path)
    return out


def _print_lift(report: Mapping[str, Any], out_json: str) -> None:
    print("=== G23-23 lift law ===")
    checks = report["checks"]
    print(
        "identity_pass=%s all_signs_match=%s max_abs_delta_identity_error=%.3g"
        % (
            checks["identity_pass"],
            checks["all_signs_match"],
            checks["max_abs_delta_identity_error"],
        )
    )
    print("%-14s %-16s %9s %10s %9s %9s %11s" % ("cell", "selector", "lift", "swing", "lift-sw", "delta", "benefit"))
    for row in report["rows"]:
        if row["selector"] not in ("C3_conformal", "B3_aoi"):
            continue
        print(
            "%-14s %-16s %9.6f %10.6f %+9.6f %+9.6f %11s"
            % (
                row["cell"],
                row["selector"],
                row["lift"],
                row["swing"],
                row["lift_minus_swing"],
                row["delta_vs_anchor"],
                row["beneficial_by_lift"],
            )
        )
    print("wrote_json=%s" % out_json)


def _print_summary(report: Mapping[str, Any], out_json: str, out_csv: str, out_png: str | None) -> None:
    print("=== Cross-cell C3 summary ===")
    print(
        "%-14s %12s %17s %14s %13s %16s"
        % ("cell", "beneficial", "band", "impr_area", "pAURC", "gap_closed")
    )
    for row in report["rows"]:
        band = (
            "[%.4f,%.4f]" % (row["c3_band_low"], row["c3_band_high"])
            if row["c3_beneficial"]
            else "EMPTY"
        )
        p_aurc = row["c3_partial_aurc_060_100"]
        print(
            "%-14s %12s %17s %14.9f %13s %+16.9f"
            % (
                row["cell"],
                row["c3_beneficial"],
                band,
                row["c3_improvement_area"],
                "%.9f" % p_aurc if p_aurc is not None else "NA",
                row["gap_closed_C3_vs_B6sys_at_078"],
            )
        )
    print("wrote_json=%s" % out_json)
    print("wrote_csv=%s" % out_csv)
    if out_png:
        print("wrote_png=%s" % out_png)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("lift", "summary", "all"), default="lift")
    parser.add_argument("--audit-json", action="append", default=None, help="cell=path")
    parser.add_argument("--baseline-json", action="append", default=None, help="cell=path")
    parser.add_argument("--g23-17a", default=DEFAULT_G23_17A)
    parser.add_argument("--out-lift-json", default=DEFAULT_LIFT_JSON)
    parser.add_argument("--out-summary-json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--out-summary-csv", default=DEFAULT_SUMMARY_CSV)
    parser.add_argument("--out-plot", default=DEFAULT_PLOT)
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args(argv)

    audit_paths = _parse_mapping(args.audit_json, DEFAULT_AUDITS)
    baseline_paths = _parse_mapping(args.baseline_json, DEFAULT_BASELINES)

    if args.mode in ("lift", "all"):
        lift = lift_law_report(audit_paths, g23_17a_path=args.g23_17a)
        _write_json(lift, args.out_lift_json)
        _print_lift(lift, args.out_lift_json)

    if args.mode in ("summary", "all"):
        summary = summary_report(baseline_paths, audit_paths)
        _write_json(summary, args.out_summary_json)
        write_summary_csv(summary, args.out_summary_csv)
        out_plot = None if args.no_plot else args.out_plot
        if out_plot is not None:
            write_err_panels(baseline_paths, out_plot)
        _print_summary(summary, args.out_summary_json, args.out_summary_csv, out_plot)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

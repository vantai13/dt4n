#!/usr/bin/env python3
"""Phase 20R.6 -- did the LOAD SOURCE change between branch A and branch A'?

``A' - A`` is read as a topology effect, but it also spans two different runner
paths. If the tandem topology makes the generator emit a less bursty stream, the
loss deficit has nothing to do with cascade or with the truth table:

    lower c_a  ->  thinner backlog tail  ->  less loss
                   body of the backlog barely moves  ->  mean delay unchanged
                   p99 still pinned at the buffer ceiling  ->  p99 unchanged

which is exactly the signature observed. This module compares the generator's own
recorded arrival statistics on both sides, from the ``*_tx.meta.json`` written by
``load_gen`` -- no testbed time required.

Branch A rows are located through ``pid``/``raw_dir`` in the campaign states, so
only the runs that actually built the truth table are compared.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import statistics
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from twin import cost_v2 as C
from twin import topology_v7 as T7
from mininet.topology_tandem import TANDEM_LINKS


APRIME_RAW = "results/SUPERSEDED/phase-20R/raw_additivity_budgetfix"
CAMPAIGN_STATES = ("results/SUPERSEDED/phase-20R/campaign_state.json", "results/SUPERSEDED/phase-L/campaign_state.json")
OUT = "results/SUPERSEDED/phase-20R/diag_ca_late.json"
RHO_BAR = 0.925
RHO_TOL = 0.021
MODES = ("poisson", "h2")


def _f(value: Any, default: float = float("nan")) -> float:
    """Tolerant float: older metadata writes ``null`` for some fields."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out


def _meta_row(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except (OSError, ValueError):
        return None
    cfg, ca, counts, rates = meta.get("config", {}), meta.get("c_a", {}), meta.get("counts", {}), meta.get("rates", {})
    n_sent = max(int(counts.get("n_bg_sent", 0)), 1)
    return {
        "mode": str(cfg.get("mode")),
        "bw": _f(cfg.get("bw_mbps")),
        "rho_nominal": _f(cfg.get("rho_nominal")),
        "probe_pps_nominal": _f(cfg.get("probe_pps_nominal"), 0.0),
        "ca_actual": _f(ca.get("actual_bg")),
        "ca_schedule": _f(ca.get("schedule_bg")),
        "ca_target": _f(ca.get("design_target")),
        "rho_actual": _f(rates.get("rho_actual")),
        "n_bg_sent": n_sent,
        "n_late": int(counts.get("n_late", 0)),
        "late_ratio": int(counts.get("n_late", 0)) / n_sent,
        "max_late_ms": _f(counts.get("max_late_ms"), 0.0),
        "meta_path": path,
    }


def aprime_rows(raw_dir: str = APRIME_RAW) -> List[Dict[str, Any]]:
    link_of = {name: name for name, _t7, _bw, _q, _b in TANDEM_LINKS}
    rows: List[Dict[str, Any]] = []
    for path in sorted(glob.glob(os.path.join(raw_dir, "*_load_L*_tx.meta.json"))):
        row = _meta_row(path)
        if row is None:
            continue
        tail = os.path.basename(path).split("_load_")[1]
        link = tail.split("_")[0]
        if link not in link_of:
            continue
        row["branch"] = "Aprime"
        row["link"] = link
        rows.append(row)
    return rows


def branch_a_rows(campaign_states: Sequence[str] = CAMPAIGN_STATES) -> List[Dict[str, Any]]:
    """Only the campaign runs that fed the truth table, via pid/raw_dir."""
    rows: List[Dict[str, Any]] = []
    for state_path in campaign_states:
        if not os.path.exists(state_path):
            continue
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        for entry in state.get("rows", []):
            if entry.get("gate_fail"):
                continue
            # Phase L's state predates the raw_dir column; fall back to the raw
            # directory that sits beside the state file.
            raw_dir = entry.get("raw_dir") or os.path.join(os.path.dirname(state_path), "raw")
            pid = entry.get("pid")
            if not pid:
                continue
            row = _meta_row(os.path.join(str(raw_dir), "%s_tx.meta.json" % pid))
            if row is None:
                continue
            row["branch"] = "A"
            row["state"] = state_path
            row["q"] = entry.get("q")
            row["rho_grid"] = float(entry.get("rho", float("nan")))
            rows.append(row)
    return rows


def _welch(a: Sequence[float], b: Sequence[float]) -> Dict[str, Any]:
    a = [float(v) for v in a if not math.isnan(float(v))]
    b = [float(v) for v in b if not math.isnan(float(v))]
    if len(a) < 2 or len(b) < 2:
        return {"delta": float("nan"), "t": float("nan"), "n_a": len(a), "n_b": len(b)}
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va = statistics.variance(a) / len(a)
    vb = statistics.variance(b) / len(b)
    se = math.sqrt(va + vb)
    return {
        "mean_a": ma,
        "mean_b": mb,
        "delta": mb - ma,
        "se": se,
        "t": (mb - ma) / se if se > 0 else float("nan"),
        "n_a": len(a),
        "n_b": len(b),
    }


EXPECTED_MIN_A_ROWS = 500


def assert_join_is_populated(rows_a: Sequence[Dict[str, Any]], cells: Sequence[Dict[str, Any]]) -> None:
    """Fail loudly when a join silently returns nothing.

    RC8: ``phase-L/campaign_state.json`` has no ``raw_dir`` column, so an earlier
    version dropped all 728 Phase L runs without raising. The comparison still
    completed and returned SOURCE_MATCHES -- an empty join looks like a result,
    which makes it the most dangerous failure mode in an analysis pipeline. Every
    join here now states its own expectation.
    """
    n = len(rows_a)
    if n < EXPECTED_MIN_A_ROWS:
        raise SystemExit(
            "join hong: chi lay duoc %d run branch-A, ky vong >= %d. "
            "Kiem tra raw_dir/pid trong campaign state." % (n, EXPECTED_MIN_A_ROWS)
        )
    seen = {(str(cell["mode"]), str(cell["link"])) for cell in cells}
    expected = {(mode, name) for mode in MODES for name, _t7, _bw, _q, _b in TANDEM_LINKS}
    missing = sorted(expected - seen)
    if missing:
        raise SystemExit(
            "join hong: cac o sau RONG %s. Mot o rong khong phai ket qua." % missing
        )


def compare(
    rows_a: Sequence[Dict[str, Any]],
    rows_ap: Sequence[Dict[str, Any]],
    rho_bar: float = RHO_BAR,
    rho_tol: float = RHO_TOL,
    modes: Sequence[str] = MODES,
) -> List[Dict[str, Any]]:
    da, dap = pd.DataFrame(list(rows_a)), pd.DataFrame(list(rows_ap))
    out: List[Dict[str, Any]] = []
    for mode in modes:
        for link, t7_link, _bw, _q, _base in TANDEM_LINKS:
            bw = float(T7.LINKS[t7_link][0])
            rho = float(C.rho_vector(float(rho_bar))[t7_link])
            sub_ap = dap[(dap["mode"] == mode) & (dap["link"] == link)]
            sub_a = da[
                (da["mode"] == mode)
                & (np.abs(da["bw"] - bw) < 1e-9)
                & (np.abs(da["rho_nominal"] - rho) <= float(rho_tol))
            ]
            if sub_ap.empty or sub_a.empty:
                continue
            ca = _welch(sub_a["ca_actual"], sub_ap["ca_actual"])
            deg_a = sub_a["ca_actual"] - sub_a["ca_schedule"]
            deg_ap = sub_ap["ca_actual"] - sub_ap["ca_schedule"]
            deg = _welch(deg_a, deg_ap)
            late = _welch(sub_a["late_ratio"], sub_ap["late_ratio"])
            out.append(
                {
                    "mode": mode,
                    "link": link,
                    "bw": bw,
                    "rho_target": rho,
                    "n_a": int(len(sub_a)),
                    "n_aprime": int(len(sub_ap)),
                    "rho_grid_used": sorted({float(v) for v in sub_a["rho_nominal"]}),
                    "ca_a": ca.get("mean_a"),
                    "ca_aprime": ca.get("mean_b"),
                    "d_ca": ca.get("delta"),
                    "d_ca_se": ca.get("se"),
                    "d_ca_t": ca.get("t"),
                    "ca_target": float(sub_ap["ca_target"].iloc[0]),
                    "deg_a": deg.get("mean_a"),
                    "deg_aprime": deg.get("mean_b"),
                    "d_degradation": deg.get("delta"),
                    "d_degradation_t": deg.get("t"),
                    "late_a": late.get("mean_a"),
                    "late_aprime": late.get("mean_b"),
                    "d_late": late.get("delta"),
                    "maxlate_a": float(sub_a["max_late_ms"].max()),
                    "maxlate_aprime": float(sub_ap["max_late_ms"].max()),
                    "probe_pps_a": float(sub_a["probe_pps_nominal"].median()),
                    "probe_pps_aprime": float(sub_ap["probe_pps_nominal"].median()),
                }
            )
    return out


def burstiness_sensitivity(
    cells: Sequence[Dict[str, Any]],
    truth_table: str = "results/LIVE/phase-20R/truth_table.parquet",
    check_report: str = "results/SMOKE/phase-20R/additivity_check_budgetfix_bg.json",
) -> List[Dict[str, Any]]:
    """How much of the loss deficit a drop in c_a can account for.

    The truth table itself supplies the anchor: at one (bw, q, rho) it holds both
    a poisson curve (c_a ~ 1) and an h2 curve (c_a ~ 2), so their difference is
    the loss response to burstiness at fixed load. Treating that as locally linear
    gives d(loss)/d(c_a); it is a first-order estimate, and because loss(c_a) is
    convex it most likely UNDERSTATES the response near c_a = 2.
    """
    table = pd.read_parquet(truth_table)
    deficit: Dict[Tuple[str, str], float] = {}
    if os.path.exists(check_report):
        with open(check_report, "r", encoding="utf-8") as f:
            for row in json.load(f).get("checks", []):
                if row.get("contrast") == "Aprime_minus_A_loss":
                    deficit[(str(row["mode"]), str(row["link"]))] = float(row["mean_ms"])
    out: List[Dict[str, Any]] = []
    for cell in cells:
        t7_link = next(t7 for name, t7, _b, _q, _base in TANDEM_LINKS if name == cell["link"])
        bw, _base, q = T7.LINKS[t7_link]
        rho = float(cell["rho_target"])
        losses = {}
        for mode in ("poisson", "h2"):
            curve = table[(table["mode"] == mode) & (table["bw"] == float(bw)) & (table["q"] == int(q))].sort_values("rho")
            losses[mode] = float(np.interp(rho, curve["rho"].to_numpy(float), curve["loss"].to_numpy(float)))
        # Two ways to read the same anchor:
        #   secant   = average slope over c_a in [1, 2]
        #   quad     = LOCAL slope at c_a = 2, from the parabola through
        #              (0, 0), (1, l_p), (2, l_h). The cbr curves measure exactly
        #              zero loss, which is what licenses the (0, 0) anchor.
        # loss(c_a) is convex, so the secant understates the response near c_a = 2.
        slope = losses["h2"] - losses["poisson"]
        slope_quad = 1.5 * losses["h2"] - 2.0 * losses["poisson"]
        predicted = slope * float(cell["d_ca"])
        predicted_quad = slope_quad * float(cell["d_ca"])
        observed = deficit.get((cell["mode"], cell["link"]))
        out.append(
            {
                "mode": cell["mode"],
                "link": cell["link"],
                "d_ca": float(cell["d_ca"]),
                "d_ca_rel": float(cell["d_ca"]) / float(cell["ca_a"]) if cell["ca_a"] else float("nan"),
                "dloss_dca": slope,
                "dloss_dca_quad": slope_quad,
                "predicted_dloss": predicted,
                "predicted_dloss_quad": predicted_quad,
                "observed_dloss": observed,
                "share_explained": None if not observed else float(predicted / observed),
                "share_explained_quad": None if not observed else float(predicted_quad / observed),
                "residual": None if observed is None else float(observed - predicted),
                "residual_quad": None if observed is None else float(observed - predicted_quad),
            }
        )
    return out


def verdict(rows: Sequence[Dict[str, Any]], t_alert: float = 3.0, rel_alert: float = 0.01) -> Dict[str, Any]:
    """Flag a source-side difference in burstiness or scheduling fidelity."""
    flagged = [
        row
        for row in rows
        if (row.get("d_ca") is not None and row["ca_a"] and abs(row["d_ca"] / row["ca_a"]) > rel_alert)
        or (row.get("d_ca_t") is not None and not math.isnan(row["d_ca_t"]) and abs(row["d_ca_t"]) > t_alert)
    ]
    return {
        "n_cells": len(rows),
        "n_flagged": len(flagged),
        "flagged": [{k: row[k] for k in ("mode", "link", "d_ca", "d_ca_t")} for row in flagged],
        "source_differs": bool(flagged),
        "verdict": "SOURCE_DIFFERS" if flagged else "SOURCE_MATCHES",
        "probe_injection_differs": bool(
            rows and any(abs(row["probe_pps_a"] - row["probe_pps_aprime"]) > 1e-9 for row in rows)
        ),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--aprime-raw", default=APRIME_RAW)
    ap.add_argument("--campaign-states", default=",".join(CAMPAIGN_STATES))
    ap.add_argument("--rho-bar", type=float, default=RHO_BAR)
    ap.add_argument("--rho-tol", type=float, default=RHO_TOL)
    ap.add_argument("--check-report", default="results/SMOKE/phase-20R/additivity_check_budgetfix_bg.json",
                    help="report whose Aprime_minus_A_loss means are the observed deficit")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    rows_ap = aprime_rows(args.aprime_raw)
    rows_a = branch_a_rows(tuple(s.strip() for s in args.campaign_states.split(",") if s.strip()))
    cells = compare(rows_a, rows_ap, args.rho_bar, args.rho_tol)
    assert_join_is_populated(rows_a, cells)
    summary = verdict(cells)

    print("nguon: A=%d run (tu campaign state), A'=%d run (tu raw meta)" % (len(rows_a), len(rows_ap)))
    print()
    print("=== c_a (he so bien thien khoang den) -- do GIAT CUC cua tai ===")
    print("%-8s %-4s %6s %8s %8s %9s %7s | %9s %9s %9s" % (
        "mode", "link", "n_A/A'", "ca_A", "ca_A'", "d_ca", "t", "late_A", "late_A'", "d_late"))
    for row in cells:
        print(
            "%-8s %-4s %3d/%-2d %8.4f %8.4f %+9.4f %7.2f | %9.6f %9.6f %+9.6f"
            % (row["mode"], row["link"], row["n_a"], row["n_aprime"], row["ca_a"], row["ca_aprime"],
               row["d_ca"], row["d_ca_t"], row["late_a"], row["late_aprime"], row["d_late"])
        )
    print()
    print("=== do lech lich phat (actual - schedule), va diem bom probe ===")
    print("%-8s %-4s %10s %10s %11s %7s | %9s %9s | %9s %9s" % (
        "mode", "link", "deg_A", "deg_A'", "d_deg", "t", "maxlate_A", "maxlate_A'", "probe_A", "probe_A'"))
    for row in cells:
        print(
            "%-8s %-4s %10.5f %10.5f %+11.5f %7.2f | %9.2f %9.2f | %9.1f %9.1f"
            % (row["mode"], row["link"], row["deg_a"], row["deg_aprime"], row["d_degradation"],
               row["d_degradation_t"], row["maxlate_a"], row["maxlate_aprime"],
               row["probe_pps_a"], row["probe_pps_aprime"])
        )
    sens = burstiness_sensitivity(cells, check_report=args.check_report)
    print()
    print("=== c_a co du giai thich deficit loss khong? ===")
    print("%-8s %-4s %9s %8s %10s %10s %12s %12s %9s %11s" % (
        "mode", "link", "d_ca", "d_ca_%", "secant", "quad@2", "du_doan_q", "quan_sat", "giai_q", "phan_du_q"))
    for row in sens:
        print("%-8s %-4s %+9.4f %7.2f%% %10.5f %10.5f %+12.6f %12s %8s %+11.6f" % (
            row["mode"], row["link"], row["d_ca"], 100.0 * row["d_ca_rel"],
            row["dloss_dca"], row["dloss_dca_quad"], row["predicted_dloss_quad"],
            "n/a" if row["observed_dloss"] is None else "%+.6f" % row["observed_dloss"],
            "n/a" if row["share_explained_quad"] is None else "%.0f%%" % (100.0 * row["share_explained_quad"]),
            row["residual_quad"] if row["residual_quad"] is not None else float("nan")))
    for mode in sorted({r["mode"] for r in sens}):
        vals = [r["residual_quad"] for r in sens if r["mode"] == mode and r["residual_quad"] is not None]
        if len(vals) > 1:
            print("   %-8s phan du: mean=%+.6f sd=%.6f CV=%.0f%%"
                  % (mode, float(np.mean(vals)), float(np.std(vals, ddof=1)),
                     100.0 * float(np.std(vals, ddof=1)) / abs(float(np.mean(vals)))))
    print()
    print("verdict = %s  (n_flagged=%d/%d, probe_injection_differs=%s)" % (
        summary["verdict"], summary["n_flagged"], summary["n_cells"], summary["probe_injection_differs"]))

    report = {
        "phase": "20R.6",
        "kind": "load_source_fidelity_diagnostic",
        "rho_bar": float(args.rho_bar),
        "rho_tol": float(args.rho_tol),
        "cells": cells,
        "burstiness_sensitivity": sens,
        "summary": summary,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, default=str)
        f.write("\n")
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

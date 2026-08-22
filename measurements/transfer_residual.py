#!/usr/bin/env python3
"""Convert existing A' - A artifacts to residual_spec/v2.

This is a smoke/golden-test input for ``band_v2``. It preserves the old transfer
artifact as a residual source without pretending it is the new cascade estimand.
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional, Sequence

from measurements import additivity_band
from measurements import residual_spec as RS


def _path_delay_rows(check_report: str) -> Dict[str, Dict[str, Any]]:
    with open(check_report, "r", encoding="utf-8") as f:
        checks = json.load(f).get("checks", [])
    out = {}
    for row in checks:
        if row.get("contrast") == "Aprime_minus_A_path_delay":
            out[str(row["mode"])] = dict(row)
    return out


def _link_delay_rows(check_report: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    with open(check_report, "r", encoding="utf-8") as f:
        checks = json.load(f).get("checks", [])
    out: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for row in checks:
        if row.get("contrast") == "Aprime_minus_A_delay":
            out.setdefault(str(row["mode"]), {})[str(row["link"])] = dict(row)
    return out


def _branch_a_baselines(check_report: str, rho_bar: float = 0.925) -> Dict[str, Dict[str, float]]:
    with open(check_report, "r", encoding="utf-8") as f:
        rows = json.load(f).get("branch_a", [])
    out: Dict[str, Dict[str, float]] = {}
    for mode in sorted({str(row["mode"]) for row in rows}):
        selected = [
            row for row in rows
            if str(row["mode"]) == mode and abs(float(row["rho_bar"]) - float(rho_bar)) <= 1e-9
        ]
        if not selected:
            raise ValueError("missing branch-A baseline for %s@%.3f" % (mode, rho_bar))
        out[mode] = {
            "loss": float(sum(float(row["loss"]) for row in selected) / len(selected)),
            "delay_ms": float(sum(float(row["delay_ms"]) for row in selected)),
        }
    return out


def build_records(diag_ca: str, check_report: str) -> List[RS.ResidualRecord]:
    residuals = additivity_band.load_residuals(diag_ca, check_report)
    delay_rows = _path_delay_rows(check_report)
    delay_link_rows = _link_delay_rows(check_report)
    baselines = _branch_a_baselines(check_report)
    records: List[RS.ResidualRecord] = []
    for mode, info in sorted(residuals.items()):
        records.append(
            RS.ResidualRecord(
                estimand=(
                    "Topology-transfer residual A-prime minus A on loss, pooled "
                    "over TandemTopo links. This is legacy transfer evidence, not "
                    "the new C minus sum(B) cascade estimand."
                ),
                source="transfer",
                channel="loss",
                level="per_link",
                mode=mode,
                point=float(info["point"]),
                se=float(info["se_pooled"]),
                rho_bar_measured=0.925,
                baseline_magnitude=float(baselines[mode]["loss"]),
                relative_point=float(info["point"]) / float(baselines[mode]["loss"]),
                valid_range=None,
                per_unit={str(k): float(v) for k, v in dict(info.get("per_link", {})).items()},
                cochran_q=float(info["cochran_q"]),
                cochran_df=int(info["cochran_df"]),
                i_squared=float(info["i_squared"]),
                provenance={
                    **RS.git_commit(),
                    "diag_ca": diag_ca,
                    "check_report": check_report,
                    "source_script": "measurements.additivity_band.load_residuals",
                },
            )
        )
        delay = delay_rows.get(mode)
        if delay is not None:
            links = delay_link_rows.get(mode, {})
            records.append(
                RS.ResidualRecord(
                    estimand=(
                        "Topology-transfer residual A-prime minus A on path delay. "
                        "This is legacy transfer evidence, not the new C minus "
                        "sum(B) cascade estimand."
                    ),
                    source="transfer",
                    channel="delay_ms",
                    level="per_path",
                    mode=mode,
                    point=float(delay.get("mean_ms", 0.0)),
                    se=float(delay.get("se_ms", 0.0)),
                    rho_bar_measured=0.925,
                    baseline_magnitude=float(baselines[mode]["delay_ms"]),
                    relative_point=float(delay.get("mean_ms", 0.0)) / float(baselines[mode]["delay_ms"]),
                    valid_range=None,
                    per_unit={link: float(row["mean_ms"]) for link, row in links.items()},
                    se_unit={link: float(row["se_ms"]) for link, row in links.items()},
                    provenance={
                        **RS.git_commit(),
                        "diag_ca": diag_ca,
                        "check_report": check_report,
                        "source_contrast": "Aprime_minus_A_path_delay",
                    },
                )
            )
    return records


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--diag-ca", default=additivity_band.DIAG_CA)
    ap.add_argument("--check-report", default=additivity_band.CHECK_REPORT)
    ap.add_argument("--out", default="results/SUPERSEDED/phase-20R/residual_transfer.json")
    args = ap.parse_args(argv)

    records = build_records(args.diag_ca, args.check_report)
    RS.save(records, args.out)
    print("=== RESIDUAL TRANSFER (legacy A' - A) ===")
    for rec in records:
        print(
            "  %-8s %-9s r=%+.6f se=%.6f CI90=[%+.6f,%+.6f]"
            % (rec.mode, rec.channel, rec.point, rec.se, *rec.ci90)
        )
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

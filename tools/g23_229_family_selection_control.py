#!/usr/bin/env python3
"""G23-229: positive control for the family-selection risk wiring."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from typing import Any, Dict, Sequence

import pandas as pd

from cert import fallback_sweep as F
from cert import live_region_sweep as L
from cert.cell_matrices import git, json_clean, pin


CELL = "poisson@0.900"
OUTPUT = "results/RAW/phase-23/g23_229_family_selection_control.json"


def run() -> Dict[str, Any]:
    spec = L.NEW_SPECS[CELL]
    path = L._calib_path(spec, L.CALIB_TEMPLATE_WAVE4)
    df = pd.read_parquet(path)
    score, accept = F.c3_accept_set(df)
    crossfit = F.build_crossfit_predictions(df, score, accept)
    test_idx = crossfit["test_idx"]
    f2 = F._risk_summary(
        crossfit["family_probs"]["F2"], df, accept, test_idx
    )
    forced_f2b = F._risk_summary(
        crossfit["family_probs"]["F2b"], df, accept, test_idx
    )
    selected = F._risk_summary(
        crossfit["selected_probs"], df, accept, test_idx
    )
    selected_families = {
        str(row["scoring_seed"]): str(row["selected_family"])
        for row in crossfit["folds"]
    }
    selected_minus_f2 = float(
        selected["delta_system_vs_neo"] - f2["delta_system_vs_neo"]
    )
    forced_minus_f2 = float(
        forced_f2b["delta_system_vs_neo"] - f2["delta_system_vs_neo"]
    )
    selection_exercised = "F6" in selected_families.values()
    observed_f6_degeneracy = selected_minus_f2 == 0.0
    forced_family_changes_risk = forced_minus_f2 != 0.0
    return json_clean(
        {
            "schema": "dt4n.g23_229.v1",
            "gate": "G23-229",
            "pass": bool(
                selection_exercised
                and observed_f6_degeneracy
                and forced_family_changes_risk
            ),
            "claim": (
                "the selected-family probability path reaches _risk_summary; "
                "F6 ties F2 in this observed cell, while forced F2b changes risk"
            ),
            "cell": CELL,
            "selected_families_by_fold": selected_families,
            "selection_exercised_nondefault_F6": selection_exercised,
            "selected_delta": float(selected["delta_system_vs_neo"]),
            "F2_delta": float(f2["delta_system_vs_neo"]),
            "selected_minus_F2": selected_minus_f2,
            "observed_F6_equals_F2": observed_f6_degeneracy,
            "forced_family": "F2b_constant_P3",
            "forced_F2b_delta": float(forced_f2b["delta_system_vs_neo"]),
            "forced_F2b_minus_F2": forced_minus_f2,
            "forced_family_changes_risk": forced_family_changes_risk,
            "provenance": {
                "git_hash": git("git", "rev-parse", "HEAD"),
                "git_dirty": bool(
                    git("git", "status", "--porcelain", "--untracked-files=no")
                ),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "input": pin(path),
            },
        }
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=OUTPUT)
    args = parser.parse_args(argv)
    report = run()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("selected folds = %s" % report["selected_families_by_fold"])
    print("selected - F2 = %+.17g" % report["selected_minus_F2"])
    print("forced F2b - F2 = %+.17g" % report["forced_F2b_minus_F2"])
    print("G23-229 %s" % ("PASS" if report["pass"] else "FAIL"))
    print("artifact -> %s" % args.out)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

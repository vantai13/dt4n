#!/usr/bin/env python3
"""G23-17a: marginal break-even probabilities before Phase 23.4 sweeps."""

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
    "poisson@0.925": "results/phase-22/calib_set_v3_poisson_0.925.parquet",
    "poisson@0.850": "results/phase-22/calib_set_v3_poisson_0.850.parquet",
    "h2@0.700": "results/phase-22/calib_set_v3_h2_0.700.parquet",
}
DEFAULT_OUT_JSON = "results/phase-23/g23_17a_cell_margins.json"


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


def cell_margin_row(cell: str, path: str, rowset: str = "test") -> Dict[str, Any]:
    """Compute the three marginal probabilities behind the break-even identity."""
    cols = ["is_calib", "block_id", "a_twin", "a_star"]
    df = pd.read_parquet(path, columns=cols)
    if rowset == "test":
        d = df[~df["is_calib"]]
    elif rowset == "calib":
        d = df[df["is_calib"]]
    elif rowset == "all":
        d = df
    else:
        raise ValueError("rowset must be one of: test, calib, all")

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


def _print_summary(report: Dict[str, Any], out_json: str) -> None:
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rowset", choices=("test", "calib", "all"), default="test")
    parser.add_argument("--out-json", default=DEFAULT_OUT_JSON)
    args = parser.parse_args(argv)

    report = run_report(DEFAULT_CELLS, rowset=args.rowset)
    write_json_report(report, args.out_json)
    _print_summary(report, args.out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

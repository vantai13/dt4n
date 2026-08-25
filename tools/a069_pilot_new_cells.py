#!/usr/bin/env python3
"""A069 pilot: sinh 6 cell moi va CHI bao cao cac bien thiet ke duoc phep."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import pandas as pd

from cert import recalibrate_transfer as RT
from cert import transfer_matrix as TM
from measurements import decision_error_v2 as DE

RHOS = (0.740, 0.780, 0.820)
MODES = ("poisson", "h2")
BASE_CALIBRATION = "results/LIVE/phase-20R/sla_calibration.json"
PILOT_CALIBRATION = "results/LIVE/phase-20R/sla_calibration_A069_pilot.json"
OUT_DIR = "results/LIVE/phase-21R"
PILOT_REPORT = "results/LIVE/phase-23/a069_pilot.json"
MAX_CELL_SECONDS = 30.0 * 60.0
ALIVE_ERR_FLOOR = 0.05
ALLOWED_CELL_FIELDS = {
    "cell", "mode", "rho_bar", "err_neo", "n_calib_blocks",
    "n_test_blocks", "kappa_A", "build_seconds", "parquet_sha256",
    "builder_report_sha256",
}


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cell_name(mode: str, rho: float) -> str:
    return f"{mode}@{rho:.3f}"


def _paths(mode: str, rho: float, out_dir: str = OUT_DIR) -> tuple[str, str]:
    stem = os.path.join(
        out_dir, f"calib_set_{mode}_{rho:.3f}_U3_measured_v7_A069"
    )
    return stem + ".parquet", stem + "_report.json"


def make_calibration_sidecar(
    base_path: str = BASE_CALIBRATION,
    out_path: str = PILOT_CALIBRATION,
) -> Dict[str, Any]:
    with open(base_path, "r", encoding="utf-8") as fh:
        base = json.load(fh)
    out = copy.deepcopy(base)
    existing = {
        (str(row["mode"]), round(float(row["rho_bar"]), 12))
        for row in out["cells"]
    }
    extra = DE.extra_calibrated_cells(RHOS, modes=MODES)
    for cell in extra:
        cell = dict(cell)
        cell["a069_original_role"] = cell.get("role")
        # `build_calib_set_v3._load_cell` chi nap role `gate`/`pc1`. Sidecar
        # danh dau 6 cell nay la gate CUA PILOT; calibration goc khong doi.
        cell["role"] = "gate"
        key = (str(cell["mode"]), round(float(cell["rho_bar"]), 12))
        if key not in existing:
            out["cells"].append(cell)
            existing.add(key)
    out["a069_pilot"] = {
        "amendment": "23-69",
        "base_calibration": base_path,
        "base_sha256": _sha256(base_path),
        "added_cells": [_cell_name(m, r) for m in MODES for r in RHOS],
        "generator": "measurements.decision_error_v2.extra_calibrated_cells",
        "note": "sidecar only; original calibration and SLA manifest unchanged",
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return out


def _run_builder(mode: str, rho: float, calibration: str, out_dir: str) -> Dict[str, Any]:
    parquet, report = _paths(mode, rho, out_dir)
    cmd = [
        sys.executable, "-m", "cert.build_calib_set_v3",
        "--mode", mode, "--rho-bar", f"{rho:.3f}",
        "--aoi-profile", "U3", "--axis", "measured_v7",
        "--calibration", calibration, "--out", parquet, "--report", report,
    ]
    started = time.monotonic()
    subprocess.run(cmd, check=True)
    elapsed = time.monotonic() - started
    return {"parquet": parquet, "report": report, "build_seconds": elapsed}


def _allowed_summary(mode: str, rho: float, built: Mapping[str, Any]) -> Dict[str, Any]:
    # PILOT allowlist A069 muc 3. Khong tinh/in bat ky outcome nao khac.
    columns = ["is_calib", "block_id", "wrong", *TM.NEEDED_COLS]
    columns = list(dict.fromkeys(columns))
    frame = pd.read_parquet(str(built["parquet"]), columns=columns)
    calib = frame[frame["is_calib"]].copy()
    test = frame[~frame["is_calib"]]
    kappa = RT.solve_kappa(calib)["kappa_A"]
    row = {
        "cell": _cell_name(mode, rho),
        "mode": mode,
        "rho_bar": float(rho),
        "err_neo": float(test["wrong"].mean()),
        "n_calib_blocks": int(calib["block_id"].nunique()),
        "n_test_blocks": int(test["block_id"].nunique()),
        "kappa_A": float(kappa),
        "build_seconds": float(built["build_seconds"]),
        "parquet_sha256": _sha256(str(built["parquet"])),
        "builder_report_sha256": _sha256(str(built["report"])),
    }
    assert set(row) == ALLOWED_CELL_FIELDS
    return row


def score_stop_rules(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    rows = list(rows)
    common_alive = []
    for rho in RHOS:
        pair = [r for r in rows if abs(float(r["rho_bar"]) - rho) < 1e-12]
        if len(pair) == 2 and all(float(r["err_neo"]) >= ALIVE_ERR_FLOOR for r in pair):
            common_alive.append(float(rho))
    low_blocks = [r["cell"] for r in rows if int(r["n_calib_blocks"]) < 500]
    slow = [r["cell"] for r in rows if float(r["build_seconds"]) > MAX_CELL_SECONDS]
    return {
        "common_alive_rho": common_alive,
        "stop_no_common_alive_rho": not bool(common_alive),
        "stop_low_calib_blocks": low_blocks,
        "stop_slow_cells": slow,
        "may_proceed_to_prereg": bool(common_alive and not low_blocks and not slow),
    }


def run(args: argparse.Namespace) -> Dict[str, Any]:
    make_calibration_sidecar(args.base_calibration, args.pilot_calibration)
    rows = []
    for mode in MODES:
        for rho in RHOS:
            built = _run_builder(mode, rho, args.pilot_calibration, args.out_dir)
            row = _allowed_summary(mode, rho, built)
            rows.append(row)
            print(
                f"{row['cell']}: err_neo={row['err_neo']:.6f}, "
                f"blocks={row['n_calib_blocks']}/{row['n_test_blocks']}, "
                f"kappa_A={row['kappa_A']:.6f}, seconds={row['build_seconds']:.2f}",
                flush=True,
            )
    report = {
        "schema": "dt4n.a069_pilot.v1",
        "amendment": "23-69",
        "allowlist": sorted(ALLOWED_CELL_FIELDS),
        "config": {
            "rho_grid": list(RHOS), "modes": list(MODES),
            "alive_err_floor": ALIVE_ERR_FLOOR,
            "max_cell_seconds": MAX_CELL_SECONDS,
            "calibration_sidecar": args.pilot_calibration,
            "calibration_sidecar_sha256": _sha256(args.pilot_calibration),
        },
        "cells": rows,
        "stop_rules": score_stop_rules(rows),
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"pilot -> {args.report}")
    print(json.dumps(report["stop_rules"], sort_keys=True))
    return report


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-calibration", default=BASE_CALIBRATION)
    ap.add_argument("--pilot-calibration", default=PILOT_CALIBRATION)
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--report", default=PILOT_REPORT)
    args = ap.parse_args(argv)
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

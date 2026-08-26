#!/usr/bin/env python3
"""A070 nhanh W: build kin 12 cell, sau do chi mo allowlist ba outcome."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import pandas as pd

from cert.taxonomy_audit import W_LOSS

RHOS = (0.744, 0.750, 0.756, 0.760, 0.764, 0.770)
MODES = ("poisson", "h2")
MANIFEST = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_32cells_A070.json"
OUT_DIR = "results/LIVE/phase-21R"
SEALED_RECEIPT = "results/LIVE/phase-23/.sealed/a070_window_receipt.json"
REPORT = "results/LIVE/phase-23/a070_window_allowlist.json"
PREREG_TAG = "lesson-23-22d-a-prereg"
ALIVE_ERR_FLOOR = 0.05
EXPECTED_CALIB_BLOCKS = 500
MAX_BUILD_SECONDS = 60.0
OUTCOME_ALLOWLIST = {"err_neo", "n_calib_blocks", "build_seconds"}


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cell_name(mode: str, rho: float) -> str:
    return f"{mode}@{rho:.3f}"


def expected_cells() -> tuple[str, ...]:
    return tuple(_cell_name(mode, rho) for mode in MODES for rho in RHOS)


def _paths(mode: str, rho: float, out_dir: str = OUT_DIR) -> tuple[str, str]:
    stem = os.path.join(
        out_dir, f"calib_set_{mode}_{rho:.3f}_U3_measured_v7_A070W"
    )
    return stem + ".parquet", stem + "_report.json"


def validate_manifest(path: str = MANIFEST) -> None:
    with open(path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    cells = manifest.get("cells", [])
    got = {(str(c["mode"]), round(float(c["rho_bar"]), 3)) for c in cells}
    want = {(mode, rho) for mode in MODES for rho in RHOS}
    if not want <= got:
        raise ValueError(f"manifest thieu cell A070W: {sorted(want - got)}")
    if {float(c["w_loss"]) for c in cells} != {W_LOSS}:
        raise ValueError("manifest A070W khong dong nhat w_loss=5000")


def _run_builder(mode: str, rho: float, manifest: str, out_dir: str) -> Dict[str, Any]:
    parquet, report = _paths(mode, rho, out_dir)
    if os.path.exists(parquet) or os.path.exists(report):
        raise FileExistsError(
            f"sealed target da ton tai cho {_cell_name(mode, rho)}; "
            "khong tu dong ghi de/rerun"
        )
    cmd = [
        sys.executable, "-m", "cert.build_calib_set_v3",
        "--mode", mode, "--rho-bar", f"{rho:.3f}",
        "--aoi-profile", "U3", "--axis", "measured_v7",
        "--calibration", manifest, "--out", parquet, "--report", report,
    ]
    started = time.monotonic()
    # Niem phong tai NGUON: ca stdout va stderr builder deu khong toi terminal.
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    elapsed = time.monotonic() - started
    return {
        "cell": _cell_name(mode, rho),
        "parquet": parquet,
        "report": report,
        "parquet_sha256": _sha256(parquet),
        "report_sha256": _sha256(report),
        "build_seconds": float(elapsed),
    }


def _batch_digest(rows: Sequence[Mapping[str, Any]]) -> str:
    h = hashlib.sha256()
    for row in sorted(rows, key=lambda r: str(r["cell"])):
        line = "%s\0%s\0%s\n" % (
            row["cell"], row["parquet_sha256"], row["report_sha256"]
        )
        h.update(line.encode("utf-8"))
    return h.hexdigest()


def _write_json_atomic(path: str, value: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(value, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, target)


def build_all_sealed(manifest: str = MANIFEST, out_dir: str = OUT_DIR,
                     receipt_path: str = SEALED_RECEIPT) -> Dict[str, Any]:
    """Sinh tron batch; KHONG doc parquet/report va KHONG tra outcome."""
    validate_manifest(manifest)
    if os.path.exists(receipt_path):
        raise FileExistsError("sealed receipt da ton tai; khong tu dong rerun")
    sealed = []
    for mode in MODES:
        for rho in RHOS:
            sealed.append(_run_builder(mode, rho, manifest, out_dir))
    if tuple(sorted(r["cell"] for r in sealed)) != tuple(sorted(expected_cells())):
        raise RuntimeError("batch A070W khong du 12 cell")
    receipt = {
        "schema": "dt4n.a070_window_sealed_receipt.v1",
        "prereg_tag": PREREG_TAG,
        "manifest": manifest,
        "manifest_sha256": _sha256(manifest),
        "n_cells": len(sealed),
        "sealed_batch_sha256": _batch_digest(sealed),
        "cells": sealed,
    }
    _write_json_atomic(receipt_path, receipt)
    return receipt


def _verified_receipt(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        receipt = json.load(fh)
    cells = receipt.get("cells", [])
    if tuple(sorted(r["cell"] for r in cells)) != tuple(sorted(expected_cells())):
        raise RuntimeError("sealed receipt thieu/thua cell")
    if int(receipt.get("n_cells", -1)) != len(expected_cells()):
        raise RuntimeError("sealed receipt khong khai dung 12 cell")
    if _sha256(receipt["manifest"]) != receipt["manifest_sha256"]:
        raise RuntimeError("manifest digest lech sau khi seal")
    for row in cells:
        if _sha256(row["parquet"]) != row["parquet_sha256"]:
            raise RuntimeError(f"parquet digest lech: {row['cell']}")
        if _sha256(row["report"]) != row["report_sha256"]:
            raise RuntimeError(f"builder report digest lech: {row['cell']}")
    if _batch_digest(cells) != receipt["sealed_batch_sha256"]:
        raise RuntimeError("batch digest lech")
    return receipt


def score(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    common = []
    for rho in RHOS:
        pair = [r for r in rows if r["cell"].endswith(f"@{rho:.3f}")]
        if len(pair) == 2 and all(float(r["err_neo"]) >= ALIVE_ERR_FLOOR
                                  for r in pair):
            common.append(float(rho))
    bad_blocks = [r["cell"] for r in rows
                  if int(r["n_calib_blocks"]) != EXPECTED_CALIB_BLOCKS]
    slow = [r["cell"] for r in rows
            if float(r["build_seconds"]) > MAX_BUILD_SECONDS]
    valid = not bad_blocks and not slow
    m215 = bool(valid and len(common) >= 2)
    lo = min(common) if common else None
    hi = max(common) if common else None
    m216_parts = {
        "lower_in_band": bool(lo is not None and 0.744 <= lo <= 0.756),
        "upper_in_band": bool(hi is not None and 0.760 <= hi <= 0.770),
        "rho_0.760_both_alive": 0.760 in common,
    }
    m217_parts = {
        "poisson_0.744_dead": next(
            float(r["err_neo"]) < ALIVE_ERR_FLOOR for r in rows
            if r["cell"] == "poisson@0.744"
        ),
        "h2_0.770_dead": next(
            float(r["err_neo"]) < ALIVE_ERR_FLOOR for r in rows
            if r["cell"] == "h2@0.770"
        ),
    }
    return {
        "operational_stop": {
            "invalid_calib_blocks": bad_blocks,
            "slow_cells": slow,
            "branch_valid": valid,
        },
        "M_215": {
            "common_alive_rho": common,
            "n_common_alive_rho": len(common),
            "hit": m215,
            "stop_W": bool(valid and not m215),
        },
        "M_216": {
            "observed_interval": [lo, hi],
            **m216_parts,
            "hit": bool(valid and all(m216_parts.values())),
        },
        "M_217": {**m217_parts,
                   "hit": bool(valid and all(m217_parts.values()))},
    }


def reveal_allowlist(receipt_path: str = SEALED_RECEIPT,
                     report_path: str = REPORT) -> Dict[str, Any]:
    """Xac minh tron batch truoc, sau do moi doc ba outcome da ky."""
    receipt = _verified_receipt(receipt_path)
    rows = []
    for sealed in receipt["cells"]:
        frame = pd.read_parquet(
            sealed["parquet"], columns=["is_calib", "block_id", "wrong"]
        )
        calib = frame[frame["is_calib"]]
        test = frame[~frame["is_calib"]]
        row = {
            "cell": sealed["cell"],
            "err_neo": float(test["wrong"].mean()),
            "n_calib_blocks": int(calib["block_id"].nunique()),
            "build_seconds": float(sealed["build_seconds"]),
        }
        if set(row) != ({"cell"} | OUTCOME_ALLOWLIST):
            raise AssertionError("serializer allowlist A070W bi lech")
        rows.append(row)
    rows.sort(key=lambda r: r["cell"])
    out = {
        "schema": "dt4n.a070_window_allowlist.v1",
        "amendment": "23-70/23-70a",
        "prereg_tag": PREREG_TAG,
        "allowlist": sorted(OUTCOME_ALLOWLIST),
        "sealed_batch_sha256": receipt["sealed_batch_sha256"],
        "config": {
            "rho_grid": list(RHOS),
            "modes": list(MODES),
            "alive_err_floor": ALIVE_ERR_FLOOR,
            "expected_calib_blocks": EXPECTED_CALIB_BLOCKS,
            "max_build_seconds": MAX_BUILD_SECONDS,
            "manifest": receipt["manifest"],
            "manifest_sha256": receipt["manifest_sha256"],
        },
        "cells": rows,
        "scores": score(rows),
    }
    _write_json_atomic(report_path, out)
    return out


def print_allowlist(out: Mapping[str, Any]) -> None:
    print("cell             err_neo  n_calib_blocks  build_seconds")
    for row in out["cells"]:
        print("%-16s %8.6f %15d %14.2f" % (
            row["cell"], row["err_neo"], row["n_calib_blocks"],
            row["build_seconds"],
        ))
    s = out["scores"]
    print("M-215: %s  common_alive_rho=%s" %
          (s["M_215"]["hit"], s["M_215"]["common_alive_rho"]))
    print("M-216: %s  interval=%s  rho=.760=%s" %
          (s["M_216"]["hit"], s["M_216"]["observed_interval"],
           s["M_216"]["rho_0.760_both_alive"]))
    print("M-217: %s  poisson@.744_dead=%s  h2@.770_dead=%s" %
          (s["M_217"]["hit"], s["M_217"]["poisson_0.744_dead"],
           s["M_217"]["h2_0.770_dead"]))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--build-sealed", action="store_true")
    group.add_argument("--reveal-allowlist", action="store_true")
    ap.add_argument("--manifest", default=MANIFEST)
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--receipt", default=SEALED_RECEIPT)
    ap.add_argument("--report", default=REPORT)
    args = ap.parse_args(list(argv) if argv is not None else None)
    if args.build_sealed:
        receipt = build_all_sealed(args.manifest, args.out_dir, args.receipt)
        print("sealed 12/12 cell; batch sha256=%s" %
              receipt["sealed_batch_sha256"])
        print("outcome chua duoc mo; chay --reveal-allowlist rieng")
        return 0
    out = reveal_allowlist(args.receipt, args.report)
    print_allowlist(out)
    print("-> %s" % args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

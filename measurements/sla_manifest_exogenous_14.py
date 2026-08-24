#!/usr/bin/env python3
"""Manifest SLA S-B 14 cell cho live-region sweep (Lesson 23.21h).

Goi `sla_manifest_exogenous.build()` nguyen ven, loc 10 cell feasible, roi
noi 4 cell Dot 4 tu bao cao authoritative da co. Khong sua builder calib.

Chay:
    python -m measurements.sla_manifest_exogenous_14
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from measurements.sla_manifest_exogenous import (
    DERIVED_FROM_SLA,
    FIXPOINT_TRACES,
    W_LOSS,
    build,
    sha256_file,
)

SOURCE = "measurements/sla_manifest_exogenous_14.py"
WAVE4 = "results/LIVE/phase-23/sla_exogenous_wave4.json"
OUT = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_14cells.json"
LABEL = "exogenous_g114_S-B"

# Thong ke DO DUOI truc, khong phai DINH NGHIA truc. `sla_spec_source` duoc
# thay bang `sla_source` chuan ben duoi, khong mang nguyen ten cu vao manifest.
MEASURED_UNDER_AXIS = (
    "S_pivotal",
    "S_pivotal_ci",
    "S_collapsed",
    "S_trivial",
    "regime",
    "pivotal_steps",
    "mean_paths_violating",
    "cost_margin_pivotal_mean_ms",
    "percentile_of_t_delay",
    "percentile_of_t_loss",
    "sla_spec_source",
)

# Danh sach TRANG. Truong moi phai bi chan va duoc phan loai, khong lot im.
ALLOWED = {
    "mode",
    "rho_bar",
    "role",
    "feasible",
    "seed",
    "n",
    "dt",
    "tau_rho",
    "sigma_rho",
    "sigma_max",
    "a",
    "clip_fraction",
    "reliable_ceiling",
    "t_delay_ms",
    "t_loss",
    "w_loss",
    "loss_exchange",
    "sla_source",
    "sla_citation",
}


def clean_wave4_cell(cell: Dict[str, Any], citation: str) -> Dict[str, Any]:
    removed = set(FIXPOINT_TRACES) | set(DERIVED_FROM_SLA) | set(MEASURED_UNDER_AXIS)
    new = {key: value for key, value in cell.items() if key not in removed}
    new["sla_source"] = LABEL
    new["sla_citation"] = citation
    stray = sorted(set(new) - ALLOWED)
    missing = sorted(ALLOWED - set(new))
    if stray or missing:
        raise ValueError(
            "cell %s@%.3f whitelist mismatch: stray=%s missing=%s"
            % (cell["mode"], float(cell["rho_bar"]), stray, missing)
        )
    return new


def build_manifest(wave4_path: str = WAVE4) -> Dict[str, Any]:
    base = build()
    base_cells = [dict(cell) for cell in base["cells"] if cell.get("feasible")]
    if len(base_cells) != 10:
        raise ValueError("manifest base phai co dung 10 cell feasible, thay %d" % len(base_cells))

    have = {
        (str(cell["mode"]), round(float(cell["rho_bar"]), 12))
        for cell in base_cells
    }
    with open(wave4_path, encoding="utf-8") as handle:
        wave4 = json.load(handle)
    if len(wave4.get("cells", [])) != 4:
        raise ValueError("wave4 phai co dung 4 cell")

    citation = str(base_cells[0]["sla_citation"])
    added = []
    for cell in wave4["cells"]:
        key = (str(cell["mode"]), round(float(cell["rho_bar"]), 12))
        if key in have:
            raise ValueError("cell Dot 4 %s@%.3f da co trong base" % key)
        if not cell.get("feasible"):
            raise ValueError("cell Dot 4 %s@%.3f khong feasible" % key)
        added.append(clean_wave4_cell(dict(cell), citation))
        have.add(key)

    cells = base_cells + added
    if len(cells) != 14 or len(have) != 14:
        raise ValueError("manifest khong dat 14 cell duy nhat")
    ws = {float(cell["w_loss"]) for cell in cells}
    if ws != {W_LOSS}:
        raise ValueError("w_loss khong dong nhat: %s" % sorted(ws))

    wave4_sha = sha256_file(wave4_path)
    out = dict(base)
    out["script"] = SOURCE
    out["cells"] = cells
    out["lesson"] = "23.21h"
    out["prereg"] = "docs/phase-23/A062-amendment-62.md"
    out["summary"] = {
        "n_cells": 14,
        "n_feasible": 14,
        "n_from_base_feasible": 10,
        "n_from_wave4": 4,
        "endogenous": False,
    }
    out["inputs"] = dict(
        base["inputs"], wave4=wave4_path, wave4_sha256=wave4_sha
    )
    out["derived_statistics"] = dict(
        base["derived_statistics"],
        authoritative_sources=[
            base["derived_statistics"]["authoritative_source"],
            wave4_path,
        ],
    )
    validity = dict(base["validity"])
    validity["instrument"] = {
        "source_path": SOURCE,
        "source_sha256": sha256_file(SOURCE),
    }
    validity["inputs_sha256"] = dict(
        base["validity"]["inputs_sha256"], **{wave4_path: wave4_sha}
    )
    validity["sla_axis"] = dict(validity["sla_axis"], label=LABEL)
    validity["sla_source"] = LABEL
    out["validity"] = validity
    return out


def main() -> int:
    report = build_manifest()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print("[ok] 14 cell (10 feasible base + 4 Dot 4) -> %s" % OUT)
    print("     sha256 = %s" % sha256_file(OUT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

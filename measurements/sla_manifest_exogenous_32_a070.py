#!/usr/bin/env python3
"""Manifest SLA S-B 32 cell: 20 cell A069 + 12 cell cua so A070."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from measurements import decision_error_v2 as DE
from measurements.sla_manifest_exogenous import W_LOSS, sha256_file
from measurements.sla_manifest_exogenous_14 import ALLOWED, LABEL
from measurements.sla_manifest_exogenous_20_a069 import clean_extra

SOURCE = "measurements/sla_manifest_exogenous_32_a070.py"
BASE = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_20cells_A069.json"
OUT = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_32cells_A070.json"
PREREG = "docs/phase-23/A070-amendment-70.md"
RHOS = (0.744, 0.750, 0.756, 0.760, 0.764, 0.770)
MODES = ("poisson", "h2")


def build_manifest(base_path: str = BASE) -> Dict[str, Any]:
    with open(base_path, "r", encoding="utf-8") as fh:
        base = json.load(fh)
    cells = [dict(cell) for cell in base["cells"]]
    if len(cells) != 20:
        raise ValueError(f"manifest base phai co 20 cell, thay {len(cells)}")
    citation = str(cells[0]["sla_citation"])
    have = {(str(c["mode"]), round(float(c["rho_bar"]), 12)) for c in cells}
    extra = []
    for cell in DE.extra_calibrated_cells(RHOS, modes=MODES):
        cleaned = clean_extra(dict(cell), citation)
        key = (str(cleaned["mode"]), round(float(cleaned["rho_bar"]), 12))
        if key in have:
            raise ValueError(f"cell trung {key}")
        extra.append(cleaned)
        have.add(key)
    if len(extra) != 12 or len(have) != 32:
        raise ValueError(f"can 12 extra/32 total, thay {len(extra)}/{len(have)}")

    out = dict(base)
    out["script"] = SOURCE
    out["cells"] = cells + extra
    out["lesson"] = "23.22d WINDOW"
    out["prereg"] = PREREG
    out["summary"] = {
        "n_cells": 32,
        "n_feasible": 32,
        "n_from_base_20": 20,
        "n_from_a070_window": 12,
        "endogenous": False,
    }
    out["inputs"] = dict(
        base["inputs"], base_20=base_path, base_20_sha256=sha256_file(base_path)
    )
    validity = dict(base["validity"])
    validity["instrument"] = {
        "source_path": SOURCE,
        "source_sha256": sha256_file(SOURCE),
    }
    validity["inputs_sha256"] = dict(
        base["validity"]["inputs_sha256"],
        **{base_path: sha256_file(base_path)},
    )
    validity["sla_axis"] = dict(validity["sla_axis"], label=LABEL)
    validity["sla_source"] = LABEL
    validity["w_loss"] = W_LOSS
    return out


def main() -> int:
    report = build_manifest()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(f"[ok] 32 cell S-B -> {OUT}")
    print(f"     sha256 = {sha256_file(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

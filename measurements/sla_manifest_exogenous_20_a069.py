#!/usr/bin/env python3
"""Manifest SLA S-B 20 cell: 14 cell cu + 6 cell PILOT A069."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

from measurements import decision_error_v2 as DE
from measurements.sla_manifest_exogenous import W_LOSS, sha256_file
from measurements.sla_manifest_exogenous_14 import ALLOWED, LABEL

SOURCE = "measurements/sla_manifest_exogenous_20_a069.py"
BASE = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_14cells.json"
OUT = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B_20cells_A069.json"
PREREG = "docs/phase-23/A069c-amendment-69c.md"
RHOS = (0.740, 0.780, 0.820)
MODES = ("poisson", "h2")
T_DELAY_MS = 50.0
T_LOSS = 0.01


def clean_extra(cell: Dict[str, Any], citation: str) -> Dict[str, Any]:
    """Chi giu thiet ke regime; thay toan bo SLA bang hop dong S-B."""
    out = {key: cell[key] for key in ALLOWED if key in cell}
    out.update({
        "role": "gate",
        "t_delay_ms": T_DELAY_MS,
        "t_loss": T_LOSS,
        "w_loss": W_LOSS,
        "sla_source": LABEL,
        "sla_citation": citation,
    })
    stray = sorted(set(out) - ALLOWED)
    missing = sorted(ALLOWED - set(out))
    if stray or missing:
        raise ValueError(f"A069 whitelist mismatch: stray={stray} missing={missing}")
    return out


def build_manifest(base_path: str = BASE) -> Dict[str, Any]:
    with open(base_path, "r", encoding="utf-8") as fh:
        base = json.load(fh)
    cells = [dict(cell) for cell in base["cells"]]
    if len(cells) != 14:
        raise ValueError(f"manifest base phai co 14 cell, thay {len(cells)}")
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
    if len(extra) != 6 or len(have) != 20:
        raise ValueError(f"can 6 extra/20 total, thay {len(extra)}/{len(have)}")

    out = dict(base)
    out["script"] = SOURCE
    out["cells"] = cells + extra
    out["lesson"] = "23.22c PILOT"
    out["prereg"] = PREREG
    out["summary"] = {
        "n_cells": 20, "n_feasible": 20,
        "n_from_base_14": 14, "n_from_a069": 6,
        "endogenous": False,
    }
    out["inputs"] = dict(base["inputs"], base_14=base_path,
                         base_14_sha256=sha256_file(base_path))
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
    out["validity"] = validity
    return out


def main() -> int:
    report = build_manifest()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(f"[ok] 20 cell S-B -> {OUT}")
    print(f"     sha256 = {sha256_file(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

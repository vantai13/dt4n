"""20R2.4 E1 -- sinh LUOI 800 o va chay TIEN SANG realizability.

HAI LAN CHAY GATE, HAI CAU HOI KHAC NHAU
========================================
Bay trong chin tieu chi quyet duoc TU THAM SO THIET KE. Hai tieu chi con lai
can gia tri SINH RA tu lan chay (`clip_fraction`, `min_cell_blocks`). Nen gate
phai chay HAI lan:

  LAN 1  TIEN SANG (tool nay)   "toi DUOC PHEP chay o nao?"
         7 tieu chi. `not_evaluated` = 2 la DUNG va DUOC PHEP o buoc nay.
         O truot: KHONG chay, ghi ly do ra artifact.

  LAN 2  HAU KIEM (sau chien dich)  "o da chay co DOC DUOC khong?"
         9 tieu chi. `not_evaluated` PHAI = [].  <- gate 4-2 noi ve LAN NAY.

Vi sao phai tach: neu ap `assert not_evaluated == []` cho LAN 1 thi no khong
bao gio thoa duoc, va nguoi viet se bi cam do noi assert -- tuc mo lai dung
cai lo vua bit.

DEN XANH RONG MA TOOL NAY CHAN
==============================
`realizability_gate()` tinh verdict bang MOT dong:

    "verdict": "REALIZABLE" if not failed else "REJECTED"

No CHI nhin `failed`. Mot tieu chi KHONG CHAY co `pass = None`, khong bao gio
vao `failed`, nen khong bao gio doi duoc verdict. Gioi han: goi gate ma khong
truyen tieu chi nao ca -> 0 truot -> REALIZABLE, mot den xanh cho mot o CHUA
BAO GIO DUOC KIEM.

Do duoc 2026-09-10, CUNG mot o, CUNG ma, CUNG may:
    cbr@0.925, tau=3, dt=0.005, n=200000
      goi THIEU sigma -> REALIZABLE, not_evaluated = [censoring_ok,
                         mondrian_cells_populated, sigma_within_headroom]
      goi DU sigma     -> REJECTED,  failed = [sigma_within_headroom]
                         (sigma_max_regime(cbr, 0.925) = 0.0)

Nen tool nay KHONG chi doc `verdict`. No khang dinh ca PHAM VI cua verdict:
tap `not_evaluated` phai DUNG BANG hai tieu chi hau-kiem, khong hon.

GATE_VERSION -- 20R2-L8
=======================
Luoi thua ke results/PENDING/phase-T2/realizability_grid.json duoc sinh boi
gate v1 (do duoc: derived.gate_version = None, tieu chi ten `sigma_feasible`,
khong co derived.sigma_max_regime, 96/96 REALIZABLE voi 3/9 not_evaluated).
Gate v1 dung tieu chi MA `sigma > 0` -- khong bao gio fail duoc tren duong
chay that, va `cost_v2` la dead import (do duoc tren commit 54a05ddc:
`grep -c "C\\."` = 0). Nen tool nay assert gate_version == 2.

Chay:
    python -m tools.20r2_4_grid_and_gate --out results/PENDING/phase-20R2/grid_prescreen.json
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import json
import os
import pathlib

from cert.realizability_gate import GATE_VERSION, realizability_gate
from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
from twin import cost_v2 as C

REPO = pathlib.Path(__file__).resolve().parents[1]
CALIB_REL = "results/LIVE/phase-20R/sla_calibration.json"

TAUS = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0]
A_VALUES = [0.5, 0.9]
SEEDS = [101, 102, 103, 104, 105]

# Hai tieu chi CHI biet duoc sau khi chay. `not_evaluated` cua LAN 1 phai
# DUNG BANG tap nay -- nhieu hon la mot tieu chi bi bo quen im lang.
POST_RUN_ONLY = frozenset({"censoring_ok", "mondrian_cells_populated"})


def feasible_cells() -> list:
    """Doc phan hoach TU ARTIFACT, khong suy tu `role` va khong go tay."""
    with open(REPO / CALIB_REL, encoding="utf-8") as fh:
        calib = json.load(fh)
    out = []
    for c in calib["cells"]:
        if not c.get("feasible"):
            continue
        out.append({
            "mode": c["mode"],
            "rho_bar": float(c["rho_bar"]),
            "role": c.get("role"),
            "sigma_max_regime": float(C.sigma_max_regime(c["mode"], c["rho_bar"])),
        })
    return out


def prescreen() -> dict:
    cells = feasible_cells()
    rows = []
    for c in cells:
        for tau in TAUS:
            n = n_for_tau(tau, DEFAULT_DT)
            for a in A_VALUES:
                sigma = a * c["sigma_max_regime"]
                r = realizability_gate(
                    mode=c["mode"], rho_bar=c["rho_bar"], tau=tau,
                    dt=DEFAULT_DT, n=n, sigma=sigma)
                rows.append({
                    "mode": c["mode"], "rho_bar": c["rho_bar"], "role": c["role"],
                    "tau": tau, "a": a, "sigma": sigma, "n": n,
                    "t_sim_s": r["derived"]["t_sim_s"],
                    "cycles": r["derived"]["cycles"],
                    "gate_version": r["derived"]["gate_version"],
                    "verdict": r["verdict"],
                    "failed": r["failed"],
                    "not_evaluated": r["not_evaluated"],
                })

    rejected = [r for r in rows if r["verdict"] == "REJECTED"]
    by_reason: dict = collections.Counter()
    for r in rejected:
        for f in r["failed"]:
            by_reason[f] += 1
    ne_shapes = collections.Counter(tuple(r["not_evaluated"]) for r in rows)

    return {
        "schema": "dt4n.grid_prescreen.v1",
        "validity": _validity(),
        "generated_by": "tools/20r2_4_grid_and_gate.py",
        "gate_version": GATE_VERSION,
        "pass_number": 1,
        "pass_meaning": (
            "TIEN SANG: 7 tieu chi quyet duoc tu tham so thiet ke. Hai tieu "
            "chi hau-kiem (censoring_ok, mondrian_cells_populated) CHUA chay "
            "o buoc nay -- do la DUNG. Gate 4-2 (not_evaluated == []) noi ve "
            "LAN 2, chay sau chien dich."),
        "grid": {
            "cells_mode_rho": cells,
            "n_cells_mode_rho": len(cells),
            "taus": TAUS, "a_values": A_VALUES, "seeds": SEEDS,
            "dt": DEFAULT_DT,
            "n_combos_without_seed": len(rows),
            "n_grid_cells": len(rows) * len(SEEDS),
            "cell_definition": "mot o = (mode, rho_bar, tau, a, seed)",
        },
        "summary": {
            "n_realizable": len(rows) - len(rejected),
            "n_rejected": len(rejected),
            "rejected_by_reason": dict(sorted(by_reason.items())),
            "not_evaluated_shapes": {
                "|".join(k) if k else "(none)": v for k, v in ne_shapes.items()},
        },
        "rows": rows,
    }


def _check(doc: dict) -> None:
    """Khang dinh TRONG TOOL, khong doi test bat -- o REJECTED phai RAISE.

    Gate 4-1: mot o khong realizable KHONG duoc lot im lang vao chien dich.
    """
    if doc["gate_version"] != 2:
        raise SystemExit(
            "gate_version = %r, doi 2. Luoi thua ke la v1 (20R2-L8): tieu chi "
            "ma `sigma > 0`, dead import. KHONG duoc tai dung."
            % doc["gate_version"])

    bad_ver = [r for r in doc["rows"] if r["gate_version"] != 2]
    if bad_ver:
        raise SystemExit("%d hang khong mang gate_version = 2" % len(bad_ver))

    rejected = [r for r in doc["rows"] if r["verdict"] == "REJECTED"]
    if rejected:
        lines = ["%s@%.3f tau=%g a=%g -> %s" % (
            r["mode"], r["rho_bar"], r["tau"], r["a"], r["failed"])
            for r in rejected[:20]]
        raise SystemExit(
            "%d o KHONG realizable -- KHONG duoc chay chung [gate 4-1]:\n  %s"
            % (len(rejected), "\n  ".join(lines)))

    # PHAM VI cua den xanh: `verdict` chi nhin `failed`, nen mot verdict xanh
    # KHONG tu no bao dam da kiem du. Phai khang dinh rieng.
    for r in doc["rows"]:
        extra = set(r["not_evaluated"]) - POST_RUN_ONLY
        if extra:
            raise SystemExit(
                "%s@%.3f tau=%g a=%g: tieu chi CHUA CHAY ngoai du kien: %s.\n"
                "  -> verdict = %s la DEN XANH RONG: no chi nhin `failed`, ma "
                "mot tieu chi khong chay khong bao gio vao `failed`.\n"
                "  -> truyen du tham so cho cac tieu chi tien-sang."
                % (r["mode"], r["rho_bar"], r["tau"], r["a"],
                   sorted(extra), r["verdict"]))



def _validity() -> dict:
    """Artifact nay CHO gi de duoc promote khoi PENDING/.

    PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE. Khai chinh xac truc
    nao chua duyet, neu khong artifact se nam quen o day.
    """
    return {
        "schema": "dt4n.validity.v1",
        "axis_role": "grid_prescreen",
        "pending_on": ["aoi_axis", "sla_axis"],
        "aoi_axis": {
            "label": "UNREGISTERED",
            "z_grid_s": [],
            "note": "tien sang LAN 1: 7/9 tieu chi. Cho A5 (muc 3 prereg) VA cho 20R2-D3 -- luoi z 20R2 chua co trong decision_error_v2.py:76. Chua duoc promote khi con mot trong hai.",
        },
        "sla_axis": {
            "label": "UNREGISTERED",
            "match_method": "none",
            "note": "cho A5 (prereg muc 3) duoc KY; chua chay tren mot truc SLA nao",
        },
        "omega": None,
        "w_loss": None,
        "note": "tien sang LAN 1: 7/9 tieu chi. Cho A5 (muc 3 prereg) VA cho 20R2-D3 -- luoi z 20R2 chua co trong decision_error_v2.py:76. Chua duoc promote khi con mot trong hai.",
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    doc = prescreen()
    _check(doc)
    doc["generated_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=True)
        fh.write("\n")

    g, s = doc["grid"], doc["summary"]
    print("=== 20R2.4 E1: tien sang realizability (LAN 1/2) ===")
    print("gate_version      : %d" % doc["gate_version"])
    print("o (mode, rho_bar) : %d kha thi" % g["n_cells_mode_rho"])
    print("luoi              : %d x %d tau x %d a = %d to hop"
          % (g["n_cells_mode_rho"], len(g["taus"]), len(g["a_values"]),
             g["n_combos_without_seed"]))
    print("                    x %d seed = %d o"
          % (len(g["seeds"]), g["n_grid_cells"]))
    print("\nREALIZABLE        : %d" % s["n_realizable"])
    print("REJECTED          : %d" % s["n_rejected"])
    print("ly do truot       : %s" % (s["rejected_by_reason"] or "(khong co)"))
    for shape, cnt in s["not_evaluated_shapes"].items():
        print("not_evaluated     : %s -> %d hang" % (shape, cnt))
    print("                    (DUNG NHU MONG DOI -- hai tieu chi nay can chay moi biet)")
    print("\n-> %s" % os.path.relpath(args.out, REPO))


if __name__ == "__main__":
    main()

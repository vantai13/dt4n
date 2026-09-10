#!/usr/bin/env python3
"""Lesson 20R2.0 A1-A6 -- kiem toan truc AoI va truc SLA bang CONG CU.

Vi sao khong viet tay bang nay:
  mot bang viet tay la mot LOI KHAI. No dung luc viet va sai ngay khi ai do
  sua code. Cong cu doc MA NGUON tai thoi diem chay, nen no khong the lac
  hau ma khong bao.

Vi sao dung AST khong dung grep:
  mot docstring nhac ten `sawtooth_age_steps` KHONG phai la dung no.
  Cung ly do voi test/test_no_stale_axes.py.

MOI so trong artifact nay deu SUY RA luc chay: nhan AoI tu sha256 ma nguon,
moment truc tu chinh bo sinh, moment thuc nghiem parse tu bang do duoc,
ngan sach CPU tu run_log that. Khong co hang so nao duoc go tay.

Chay:
    python -m tools.20r2_0_axis_audit \
        --out results/PENDING/phase-20R2/axis_audit.json
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import glob
import json
import os
import re
import statistics
from datetime import datetime, timezone

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(REPO, "docs", "phase-23", "axis_registry.json")
# Bang AoI DO DUOC tren topology_v7 (Lesson 23.20 / amendment 44).
EMPIRICAL_DOC = os.path.join(REPO, "docs", "phase-23", "20-aoi-on-topology-v7.md")
GA020_DOC = os.path.join(REPO, "docs", "phase-G",
                         "76-amendment-G-A020-omega-reduction.md")
# run_log THAT dung de uoc luong CPU, thay cho con so doan.
RUN_LOGS = {
    "sweep_r2 (decision_error_v2 --run-fixed, 1 tau x 1 seed)":
        "results/PENDING/phase-T2/sweep_r2/run_log.jsonl",
    "sweep_r3 (cert.tau_sweep, 8 tau x 5 seed)":
        "results/PENDING/phase-T2/sweep_r3/run_log.jsonl",
}

# Harness ma 20R2 SE GOI. Danh sach nay la mot QUYET DINH, ghi vao prereg.
HARNESSES = {
    "measurements/decision_error_v2.py": "do err(z), d_sla -- ESTIMAND CHINH",
    "cert/build_calib_set_v3.py":        "dung tap calib conformal",
    "cert/tau_sweep.py":                 "quet tau (RMS_MARGIN_COST)",
    "cert/aoi_profiles.py":              "ho so Phase 22, doi chung legacy",
    "cert/cell_matrices.py":             "ma tran cac o, phan phoi axis",
    "cert/realizability_gate.py":        "gate kha thi",
    "measurements/aoi_model_v7.py":      "BO SINH truc do duoc",
    "measurements/decision_error.py":    "BO SINH truc ke thua",
}

# Ten ham SINH RA hoac PHAN PHOI truc tuoi.
AOI_GENERATORS = {
    "sawtooth_age_steps", "base_age_steps", "process_mode",
    "age_steps", "process_mode_steps", "instrument_mode", "_valid_rows",
}

TAUS = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------- A1 -------
def scan_calls(path: str) -> list[dict]:
    """Tim MOI loi goi bo sinh truc, va xem `axis` co TUONG MINH khong."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    found = []
    parents = {child: parent for parent in ast.walk(tree)
               for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = (fn.attr if isinstance(fn, ast.Attribute)
                else fn.id if isinstance(fn, ast.Name) else None)
        if name not in AOI_GENERATORS:
            continue
        kw = {k.arg for k in node.keywords if k.arg}
        enclosing = []
        ancestor = parents.get(node)
        while ancestor is not None:
            enclosing.append(ancestor)
            ancestor = parents.get(ancestor)
        owner = next((p.name for p in enclosing
                      if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
        axis_guards = [ast.unparse(p.test) for p in enclosing
                       if isinstance(p, ast.If)
                       and any(isinstance(x, ast.Name) and x.id == "axis"
                               for x in ast.walk(p.test))]
        found.append({
            "line": node.lineno,
            "callee": name,
            "axis_explicit": "axis" in kw,
            "enclosing_function": owner,
            "direct_generator_call": name != "_valid_rows",
            # Review evidence, not proof that arbitrary control flow is safe.
            "enclosing_axis_guards": axis_guards,
            "n_positional": len(node.args),
            "keywords": sorted(kw),
        })
    return sorted(found, key=lambda r: r["line"])


def axis_label_of_module(rel_path: str, registry: dict) -> str:
    """Nhan SUY RA tu sha256 file nguon -- cung co che validity.aoi_axis().

    LUU Y DOC BANG: chi MODULE BO SINH moi co mat trong registry. Mot harness
    chi GOI bo sinh (tau_sweep, build_calib_set_v3, ...) tra ve UNREGISTERED,
    va do la DUNG -- no khong dinh nghia truc nao ca. UNREGISTERED chi la
    LOI khi no xuat hien tren mot ARTIFACT (test_no_stale_axes).
    """
    sha = sha256_file(os.path.join(REPO, rel_path))
    entry = registry.get("aoi_axis", {}).get(sha)
    return entry["label"] if entry else "UNREGISTERED"


# --------------------------------------------------------------- A3 -------
def z_stats(axis: str, n: int = 20_000, dt: float = 0.005) -> dict:
    """A3 -- DO do lech giua hai truc tren chinh luoi z se dung.

    Tai lap DUNG duong loc cua cert/build_calib_set_v3._valid_rows:
    giu t >= age, roi bo z == 0.

    CANH BAO PHAM VI: day la MIEN CUA MO HINH (bo sinh ma pipeline goi),
    KHONG phai mien cua AoI do duoc tren mang. Xem `A3b_empirical` --
    mo hinh uniform-phase co CV thap hon thuc nghiem (MISS M-72) va duoi
    phai cua no ket thuc som hon nhieu.
    """
    from measurements.decision_error import (
        DEFAULT_D_SYNC_S, DEFAULT_SYNC_PERIOD_S, sawtooth_age_steps)
    from measurements.aoi_model_v7 import AoIModelV7, d_base_s

    if axis == "legacy":
        age = sawtooth_age_steps(n, dt, DEFAULT_SYNC_PERIOD_S, DEFAULT_D_SYNC_S)
        src = {"d_s": DEFAULT_D_SYNC_S, "T_s": DEFAULT_SYNC_PERIOD_S,
               "module": "measurements/decision_error.py"}
    else:
        # profile U0: offset = 0 cho ca 8 link -> d_base = D_SYNC_S
        aoi = AoIModelV7(d_s=d_base_s((0.0,) * 8, dt), profile="U0")
        age = aoi.base_age_steps(n, dt)
        src = {"d_s": aoi.d, "T_s": aoi.T,
               "module": "measurements/aoi_model_v7.py"}

    rows = np.arange(n)
    valid = rows >= age
    cur, old = rows[valid], rows[valid] - age[valid]
    keep = age[valid] != 0
    z = (cur[keep] - old[keep]) * dt
    return {
        "axis": axis, "source": src, "n_rows": int(z.size),
        "domain_kind": "MODEL_SUPPORT",
        "z_p05": float(np.percentile(z, 5)),
        "z_median": float(np.median(z)),
        "z_mean": float(z.mean()),
        "z_p95": float(np.percentile(z, 95)),
        "z_min": float(z.min()), "z_max": float(z.max()),
        "cv": float(z.std() / z.mean()),
    }


def empirical_axis() -> dict:
    """A3b -- moment AoI DO DUOC tren topology_v7, parse tu bang Lesson 23.20.

    Vi sao phai co muc nay: A3 do MO HINH. Registry ghi cho truc measured
    `p05=143.072ms, mean=368.924ms, CV=0.419529` -- do la so THUC NGHIEM,
    va no KHAC mo hinh. Bo qua khac biet nay la lap lai dung loai loi
    (lay hang so cua he A dung cho he B) ma S12 da mac.
    """
    with open(EMPIRICAL_DOC, encoding="utf-8") as fh:
        text = fh.read()
    out: dict = {"source_doc": os.path.relpath(EMPIRICAL_DOC, REPO),
                 "source_sha256": sha256_file(EMPIRICAL_DOC),
                 "domain_kind": "EMPIRICAL_MEASURED",
                 "modes": {}}
    # | CLEAN | 143.072 | 368.924 | 0.419529 | 358.278 | 587.935 | 627.510 | 1568.851 |
    pat = re.compile(
        r"^\|\s*(CLEAN|PROD)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*"
        r"\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|",
        re.M)
    for m in pat.finditer(text):
        out["modes"][m.group(1)] = {
            "p05_ms": float(m.group(2)), "mean_ms": float(m.group(3)),
            "cv": float(m.group(4)), "p50_ms": float(m.group(5)),
            "p95_ms": float(m.group(6)), "p99_ms": float(m.group(7)),
            "max_ms": float(m.group(8)),
        }
    # M-72: CV do duoc nam NGOAI bang du doan cua mo hinh -> MISS da ghi.
    out["locked_prediction_misses"] = re.findall(
        r"^\|\s*(M-7\d\w*)\s*\|\s*([^|]+?)\s*\|\s*\*\*MISS\*\*\s*\|", text, re.M)
    return out


# --------------------------------------------------------------- A6 -------
def grid_domain_check(grids: dict, axes: dict, empirical: dict) -> dict:
    """A6 -- luoi z co NAM TRONG mien cua truc khong, va co PHU duoc khong.

    Hai cau hoi khac nhau:
      (1) NGOAI SUY: co diem z nao nam ngoai [min, max] cua truc?  (NT 63)
      (2) PHU DUOI: diem z lon nhat co cham p95/p99/max cua truc?

    Kiem ca tren mien MO HINH lan mien THUC NGHIEM, vi hai mien khac nhau
    va mot luoi hop le tren mien nay co the ngoai suy tren mien kia.
    """
    out: dict = {}
    clean = empirical["modes"].get("CLEAN", {})
    emp = ({"z_min": clean["p05_ms"] / 1000.0,   # p05 la E1, khong phai min tuyet doi
            "z_p95": clean["p95_ms"] / 1000.0,
            "z_p99": clean["p99_ms"] / 1000.0,
            "z_max": clean["max_ms"] / 1000.0} if clean else {})
    for gname, grid in grids.items():
        row: dict = {"grid": [float(z) for z in grid]}
        for aname, a in axes.items():
            lo, hi = a["z_min"], a["z_max"]
            inside = [z for z in grid if lo - 1e-12 <= z <= hi + 1e-12]
            row["vs_model_" + aname] = {
                "domain": [lo, hi],
                "outside_domain": [z for z in grid if z not in inside],
                "max_grid_z": max(grid),
                "reaches_p95": max(grid) >= a["z_p95"] - 1e-12,
                "reaches_max": max(grid) >= hi - 1e-12,
            }
        if emp:
            row["vs_empirical_CLEAN"] = {
                "E1_p05_s": emp["z_min"], "p95_s": emp["z_p95"],
                "p99_s": emp["z_p99"], "max_s": emp["z_max"],
                "max_grid_z": max(grid),
                "reaches_p95": max(grid) >= emp["z_p95"] - 1e-12,
                "reaches_p99": max(grid) >= emp["z_p99"] - 1e-12,
                "reaches_max": max(grid) >= emp["z_max"] - 1e-12,
            }
        out[gname] = row
    return out


# --------------------------------------------------------------- A4 -------
def ga020_transfer_check() -> dict:
    """A4 -- dieu kien §4 cua G-A020 co chuyen giao sang 20R2 khong.

    §4 liet ke thiet lap ma ket luan quy gian omega duoc thiet lap tren, va
    noi ro: doi estimand / tap hanh dong / quy tac xep hang / >3 claim thi
    G-A020 TU DONG HET HIEU LUC cho phase do.
    """
    import measurements.decision_error_v2 as DE2
    with open(GA020_DOC, encoding="utf-8") as fh:
        text = fh.read()
    conditions = [
        {"dimension": "dt",
         "ga020": "0.1 s", "phase_20r2": "%g s" % DE2.DT,
         "match": abs(DE2.DT - 0.1) < 1e-12},
        {"dimension": "tau",
         "ga020": "co dinh 3 s", "phase_20r2": "TRUC QUET %s" % (list(TAUS),),
         "match": False},
        {"dimension": "estimand",
         "ga020": "rank-slot coverage/acceptance",
         "phase_20r2": DE2.ESTIMAND_ID + " (err(z), d_sla)",
         "match": False},
        {"dimension": "quy tac xep hang",
         "ga020": "4 hanh dong / 3 khe xep hang",
         "phase_20r2": "4 duong, argmin top-1, khong xep hang khe",
         "match": False},
        {"dimension": "so claim",
         "ga020": "<= 3 claim", "phase_20r2": "5 RQ (a-e)", "match": False},
        {"dimension": "alpha",
         "ga020": "0.10", "phase_20r2": "0.10", "match": True},
    ]
    return {
        "source_doc": os.path.relpath(GA020_DOC, REPO),
        "source_sha256": sha256_file(GA020_DOC),
        # G-A020 viet CO DAU. Doi chuoi khong dau se im lang tra False --
        # dung loai loi "kiem bang chuoi" ma AST duoc dung de tranh.
        "expiry_clause_present": "tự động hết hiệu lực" in text,
        "master_plan_v10_absent_per_amendment":
            "MASTER_PLAN_v10" in text and "không có trong checkout" in text,
        "conditions": conditions,
        "n_mismatch": sum(1 for c in conditions if not c["match"]),
        "verdict": ("FAIL -- G-A020 KHONG chuyen giao sang 20R2"
                    if any(not c["match"] for c in conditions) else "PASS"),
    }


# --------------------------------------------------------------- A7 -------
def feasible_grid() -> dict:
    """P2 -- kich thuoc luoi SUY TU bang kha thi, khong nhan bon so.

    `sigma = a * sigma_max`. O nao co `sigma_max = 0` thi sigma = 0 voi MOI a:
    truc sigma SUP xuong mot diem, va o do khong con la mot o cua thi nghiem nay.
    Do duoc 2026-09-09: cbr@0.925 va cbr@0.960 deu co sigma_max = 0 va
    role = "pc1_excluded_by_q8" -> 10/12 to hop (c_a, rho_bar) kha thi.
    Luu y: ten truong la `sigma_max`; chuoi "sigma_max_regime" chi nam trong
    van ban `reason`, khong phai mot khoa.
    """
    path = os.path.join(REPO, "results/LIVE/phase-20R/sla_calibration.json")
    with open(path, encoding="utf-8") as fh:
        cells = json.load(fh)["cells"]
    rows = []
    for c in cells:
        rows.append({
            "mode": c["mode"], "rho_bar": c.get("rho_bar", c.get("rho")),
            "feasible": bool(c["feasible"]),
            "sigma_max": c.get("sigma_max"),
            "sigma_rho": c.get("sigma_rho"),
            "role": c.get("role"),
            "reason": c.get("infeasible_reason") or c.get("reason") or None,
        })
    n_feasible = sum(r["feasible"] for r in rows)
    return {
        "source": "results/LIVE/phase-20R/sla_calibration.json",
        "cells_mode_rho": rows,
        "n_design_mode_rho": len(rows),
        "n_feasible_mode_rho": n_feasible,
        "axes": {"mode_rho": n_feasible, "tau": len(TAUS), "sigma_a": 2, "seed": 5},
        "n_grid_cells": n_feasible * len(TAUS) * 2 * 5,
        "n_grid_cells_if_all_mode_rho_used": len(rows) * len(TAUS) * 2 * 5,
        "cell_definition": "mot o = (rho_bar, c_a, tau, sigma, seed); seed LA MOT CHIEU",
    }


def cells_per_command(sweep_rel: str) -> dict:
    """P1 -- MOT LENH phu bao nhieu o? Dem tu chinh report, khong gia dinh.

    `decision_error_v2` lap qua toan bo `feasible_cells()` trong MOT tien trinh,
    nen 1 lenh != 1 o. Day la sai so lon nhat trong uoc tinh ngan sach cu.
    """
    root = os.path.join(REPO, sweep_rel)
    sets, rows_total, n_rep = set(), 0, 0
    for name in sorted(glob.glob(os.path.join(root, "*_report.json"))):
        with open(name, encoding="utf-8") as fh:
            rep = json.load(fh)
        sets.add(tuple(rep.get("cells", ())))
        rows_total += int(rep.get("n_rows") or 0)
        n_rep += 1
    uniform = len(sets) == 1
    return {
        "source_dir": sweep_rel, "n_reports": n_rep,
        "cells_per_command": len(next(iter(sets))) if uniform else None,
        "cell_lists_uniform": uniform,
        "cells": sorted(next(iter(sets))) if uniform else None,
        "total_rows": rows_total,
    }


def cpu_budget(n_cells: int | None = None) -> dict:
    """A7 -- ngan sach CPU tu run_log THAT, khong tu ti le n_for_tau.

    RT20-4 gia dinh n ~ tau nen ket luan tau=28 ton 56x. `n_for_tau` co SAN
    n_floor, nen ti le that la 1.4x. Nhung ti le n KHONG phai ngan sach:
    ngan sach phai do bang giay tren lenh THAT.
    """
    from measurements.sla_calib_v2 import n_for_tau, DEFAULT_DT
    grid = feasible_grid()
    if n_cells is None:
        n_cells = grid["n_grid_cells"]
    n_by_tau = {str(t): n_for_tau(t, DEFAULT_DT) for t in TAUS}
    out: dict = {
        "grid": grid,
        "n_for_tau": n_by_tau,
        "n_floor_dominates_upto_tau": max(
            [t for t in TAUS if n_for_tau(t, DEFAULT_DT) == min(n_by_tau.values())],
            default=None),
        "ratio_tau28_over_tau0p5":
            n_for_tau(28.0, DEFAULT_DT) / n_for_tau(0.5, DEFAULT_DT),
        "rt20_4_claimed_ratio": 56.0,
        "harness_seconds": {},
    }
    coverage = {}
    for label, rel in RUN_LOGS.items():
        if "sweep_r2" in rel:
            coverage[label] = cells_per_command(os.path.dirname(rel))
    out["cells_per_command"] = coverage
    for label, rel in RUN_LOGS.items():
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            continue
        secs = []
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    secs.append(float(json.loads(line)["seconds"]))
                except (ValueError, KeyError):
                    continue
        if not secs:
            continue
        entry = {
            "path": rel, "n_cmd": len(secs),
            "min": min(secs), "max": max(secs),
            "mean": statistics.mean(secs), "median": statistics.median(secs),
            "total_seconds": sum(secs),
            # ĐINH CHINH: uoc tinh CU coi 1 lenh = 1 o va luoi = 960 o. Giu lai
            # de doi chieu, KHONG dung de ky. Xem `corrected` ben duoi.
            "superseded_hours_for_960_cells_1cmd_per_cell":
                960 * statistics.mean(secs) / 3600.0,
            "superseded_hours_two_branches":
                2 * 960 * statistics.mean(secs) / 3600.0,
        }
        cov = coverage.get(label)
        if cov and cov.get("cells_per_command"):
            per_cmd = cov["cells_per_command"]
            non_canary = [float(json.loads(l)["seconds"])
                          for l in open(os.path.join(REPO, rel), encoding="utf-8")
                          if l.strip() and not json.loads(l).get("is_canary")]
            base = non_canary or secs
            grid_points = len(base) * per_cmd
            per_cell = sum(base) / grid_points
            entry["corrected"] = {
                "cells_per_command": per_cmd,
                "n_cmd_non_canary": len(base),
                "total_seconds_non_canary": sum(base),
                "grid_points_covered": grid_points,
                "seconds_per_cell": per_cell,
                "n_grid_cells": n_cells,
                "seconds_one_branch": n_cells * per_cell,
                "minutes_one_branch": n_cells * per_cell / 60.0,
                "minutes_two_branches": 2 * n_cells * per_cell / 60.0,
                "minutes_two_branches_plus_30pct": 2 * n_cells * per_cell * 1.3 / 60.0,
            }
        out["harness_seconds"][label] = entry
    return out


def sheppard(z: float, tau: float) -> float:
    """err(z, tau) = arccos(exp(-z/tau)) / pi  -- Sheppard 1898."""
    return float(np.arccos(np.exp(-float(z) / float(tau))) / np.pi)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-cells", type=int, default=None,
                    help="mac dinh: SUY TU bang kha thi (P2), khong go tay")
    args = ap.parse_args()

    with open(REGISTRY, encoding="utf-8") as fh:
        registry = json.load(fh)

    # ---- A1: harness nao goi bo sinh nao, axis co tuong minh khong -------
    a1 = []
    for rel, role in HARNESSES.items():
        calls = scan_calls(os.path.join(REPO, rel))
        a1.append({
            "harness": rel,
            "role": role,
            "source_sha256": sha256_file(os.path.join(REPO, rel)),
            "registry_label": axis_label_of_module(rel, registry),
            # module BO SINH (co trong registry) vs harness chi GOI bo sinh
            "is_generator_module": axis_label_of_module(rel, registry)
                                   != "UNREGISTERED",
            "calls": calls,
            "silent_default_sites": [c["line"] for c in calls
                                     if c["callee"] == "_valid_rows"
                                     and not c["axis_explicit"]],
        })

    # ---- A2: truc SLA -----------------------------------------------------
    a2 = []
    for path, entry in sorted(registry.get("sla_axis", {}).items()):
        full = os.path.join(REPO, path)
        exists = os.path.exists(full)
        a2.append({
            "path": path,
            "label": entry["label"],
            "status": entry.get("status"),
            "approved_for_live":
                entry["label"] in registry["approved_for_live"]["sla_axis"],
            "exists_on_disk": exists,
            "sha_matches": (sha256_file(full) == entry["content_sha256"])
                           if exists and "content_sha256" in entry else None,
        })

    # ---- A3: do lech hai truc AoI (MO HINH) ------------------------------
    a3 = {a: z_stats(a) for a in ("legacy", "measured")}
    a3["median_ratio_measured_over_legacy"] = (
        a3["measured"]["z_median"] / a3["legacy"]["z_median"])

    # ---- A3b: truc AoI THUC NGHIEM ---------------------------------------
    a3b = empirical_axis()
    clean = a3b["modes"].get("CLEAN")
    if clean:
        a3b["model_vs_empirical_CLEAN"] = {
            "cv_model": a3["measured"]["cv"], "cv_empirical": clean["cv"],
            "cv_rel_gap": a3["measured"]["cv"] / clean["cv"] - 1.0,
            "max_model_s": a3["measured"]["z_max"],
            "max_empirical_s": clean["max_ms"] / 1000.0,
            "p99_empirical_s": clean["p99_ms"] / 1000.0,
            "note": ("Mo hinh uniform-phase HEP HON thuc nghiem o CA HAI dau: "
                     "CV thap hon (MISS M-72) va duoi phai ket thuc som hon "
                     "p99 do duoc. Luoi z phu het mien MO HINH van KHONG phu "
                     "het mien THUC NGHIEM."),
        }

    # ---- A4: G-A020 chuyen giao ------------------------------------------
    a4 = ga020_transfer_check()

    # ---- A6: kiem mien cua cac luoi z ------------------------------------
    import measurements.decision_error_v2 as DE2
    from measurements.aoi_model_v7 import Z_EDGES_V7
    grids = {
        "Z_GRID_hien_tai (decision_error_v2.Z_GRID)": list(DE2.Z_GRID),
        "Z_GRID_20R2_MEASURED (de xuat)": [
            0.115, 0.170, 0.241, 0.305, 0.366, 0.430, 0.491, 0.555, 0.615],
        "Z_EDGES_V7 (da khoa)": list(Z_EDGES_V7),
    }
    a6 = grid_domain_check(
        grids, {"legacy": a3["legacy"], "measured": a3["measured"]}, a3b)

    # ---- A7: ngan sach CPU -----------------------------------------------
    a7 = cpu_budget(args.n_cells)

    # ---- Bang Sheppard tinh LAI tai z_median CUA TUNG TRUC ---------------
    sh = {}
    for axis in ("legacy", "measured"):
        zm = a3[axis]["z_median"]
        sh[axis] = {"z_median": zm,
                    "err": {str(t): sheppard(zm, t) for t in TAUS}}
    if clean:
        zme = clean["p50_ms"] / 1000.0
        sh["empirical_CLEAN_p50"] = {
            "z_median": zme, "err": {str(t): sheppard(zme, t) for t in TAUS},
            "note": "trung vi DO DUOC (358.278 ms), khac trung vi MO HINH.",
        }
    sh["plan_z_0.369_DO_NOT_COPY"] = {
        "z_median": 0.369,
        "err": {str(t): sheppard(0.369, t) for t in TAUS},
        "note": "MASTER_PLAN chep tu link_corr_matrix.py:62. "
                "CHI dung neu A5 chon truc co z_median = 0.369.",
    }

    # ---- validity: artifact nay CHO gi (test_no_stale_axes) --------------
    # KHONG dung duoc ba helper co san:
    #   validity_block          -> danh cho artifact CHAY TREN mot bo sinh
    #   sla_only_validity_block -> danh cho artifact khong cham truc AoI
    #   measurement_validity_block -> cam goi sawtooth_age_steps
    # Cong cu nay chay CA HAI bo sinh CO Y de so sanh chung, nen no khong
    # dieu kien theo truc nao. Nhan UNREGISTERED o ca hai truc la DUNG, khong
    # phai thieu sot: no khong muon nhan cua truc nao ca.
    validity = {
        "schema": "dt4n.validity.v1",
        "axis_role": "axis_audit",
        "aoi_axis": {
            "label": "UNREGISTERED",
            "note": "cong cu KIEM TOAN: chay CA HAI bo sinh de DO do lech "
                    "giua chung; ket qua khong dieu kien theo mot truc nao",
            "z_grid_s": [],
        },
        "sla_axis": {
            "label": "UNREGISTERED",
            "match_method": "none",
            "note": "chi LIET KE bang truc SLA tu registry; khong chay tren "
                    "mot truc SLA nao",
        },
        # A5 (quyet dinh truc cua 20R2) CHUA KY -> cho ca hai truc.
        "pending_on": ["aoi_axis", "sla_axis"],
        "note": "cho A5 trong docs/phase-20R2/00-preregistration.md muc 3. "
                "Khi A5 duoc ky, artifact nay van o PENDING/: no la kiem toan "
                "TIEN quyet dinh, khong phai ket qua cua quyet dinh do.",
        "w_loss": None,
        "omega": None,
    }

    payload = {
        "schema": "dt4n.axis_audit.20r2_0.v1",
        "validity": validity,
        "generated_utc": datetime.now(timezone.utc)
                          .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "A1_aoi_harness_table": a1,
        "A2_sla_axis_table": a2,
        "A3_axis_divergence_MODEL": a3,
        "A3b_axis_EMPIRICAL": a3b,
        "A4_ga020_transfer": a4,
        "A6_grid_domain_check": a6,
        "A7_cpu_budget": a7,
        "sheppard_recomputed": sh,
        "note": "Bang nay SINH BOI CONG CU (gate 0-1). Moi nhan AoI SUY RA "
                "tu sha256 ma nguon, khong go tay.",
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")

    # --- in ra man hinh cho nguoi doc ------------------------------------
    print("=== A1: harness x truc AoI ===")
    print("(UNREGISTERED tren mot harness KHONG phai loi: chi module BO SINH"
          " moi nam trong registry)")
    for r in a1:
        flag = ("  ⛔ MAC DINH IM LANG tai dong %s" % r["silent_default_sites"]
                if r["silent_default_sites"] else "")
        label = (r["registry_label"] if r["is_generator_module"]
                 else "- (chi goi, khong dinh nghia truc)")
        print("%-38s %-38s%s" % (r["harness"], label, flag))
    print("\n=== A3: do lech hai truc, MIEN MO HINH (dt=0.005) ===")
    for a in ("legacy", "measured"):
        s = a3[a]
        print("%-9s p05=%.4f med=%.4f mean=%.4f p95=%.4f  [%.3f, %.3f]  CV=%.4f"
              % (a, s["z_p05"], s["z_median"], s["z_mean"],
                 s["z_p95"], s["z_min"], s["z_max"], s["cv"]))
    print("ti le trung vi measured/legacy = %.4f"
          % a3["median_ratio_measured_over_legacy"])
    if clean:
        print("\n=== A3b: truc measured, MIEN THUC NGHIEM (CLEAN) ===")
        print("E1/p05=%.4f p50=%.4f p95=%.4f p99=%.4f max=%.4f CV=%.6f"
              % (clean["p05_ms"] / 1e3, clean["p50_ms"] / 1e3,
                 clean["p95_ms"] / 1e3, clean["p99_ms"] / 1e3,
                 clean["max_ms"] / 1e3, clean["cv"]))
        g = a3b["model_vs_empirical_CLEAN"]
        print("CV mo hinh %.6f vs thuc nghiem %.6f  (lech %+.2f%%)"
              % (g["cv_model"], g["cv_empirical"], 100 * g["cv_rel_gap"]))
        print("max mo hinh %.4f s  vs  p99 thuc nghiem %.4f s / max %.4f s"
              % (g["max_model_s"], g["p99_empirical_s"], g["max_empirical_s"]))
    print("\n=== A6: luoi z co nam trong mien cua truc khong ===")
    for gname, row in a6.items():
        print("  %s" % gname)
        print("    grid = %s" % [round(z, 4) for z in row["grid"]])
        for aname in ("legacy", "measured"):
            v = row["vs_model_" + aname]
            out_s = (("NGOAI SUY tai z=%s" % v["outside_domain"])
                     if v["outside_domain"] else "trong mien")
            print("    vs MO HINH %-9s [%.3f,%.3f]  %-28s p95:%s max:%s"
                  % (aname, v["domain"][0], v["domain"][1], out_s,
                     "cham" if v["reaches_p95"] else "KHONG",
                     "cham" if v["reaches_max"] else "KHONG"))
        e = row.get("vs_empirical_CLEAN")
        if e:
            print("    vs THUC NGHIEM CLEAN  p95:%s p99:%s max:%s"
                  % ("cham" if e["reaches_p95"] else "KHONG",
                     "cham" if e["reaches_p99"] else "KHONG",
                     "cham" if e["reaches_max"] else "KHONG"))

    print("\n=== A4: G-A020 §4 chuyen giao -> %s ===" % a4["verdict"])
    for c in a4["conditions"]:
        print("  %-18s ga020=%-28s 20R2=%-34s %s"
              % (c["dimension"], c["ga020"], c["phase_20r2"],
                 "OK" if c["match"] else "KHAC"))
    # `args.n_cells` la DAU VAO va co the la None (mac dinh = suy tu bang kha
    # thi). `a7["grid"]["n_grid_cells"]` la GIA TRI DA GIAI. In dau vao chua
    # giai la cung mot lop loi voi doc mot hang so chua import: ban in noi ve
    # mot thu KHAC voi thu da tinh. Do duoc 2026-09-10: tool thoat ma 1 ngay
    # tren lenh docstring cua chinh no, va so 800 o / 29.4 phut KHONG BAO GIO
    # duoc in ra vi dong crash chinh la dong in no.
    n_cells_resolved = a7["grid"]["n_grid_cells"]
    print("\n=== A7: ngan sach CPU (%d o) ===" % n_cells_resolved)
    print("n_for_tau ti le tau=28/tau=0.5 = %.3f  (RT20-4 ghi 56)"
          % a7["ratio_tau28_over_tau0p5"])
    for label, s in a7["harness_seconds"].items():
        # Khoa `hours_for_<N>_cells` KHONG con ton tai: no da doi ten thanh
        # `superseded_hours_for_960_cells_1cmd_per_cell` khi ngan sach chuyen
        # sang dem theo o-luoi (10 o/lenh) thay vi 1 lenh/o. Ban in nay bi bo
        # lai phia sau -- nen sua no phai theo LUOC DO THAT, khong phai theo
        # ten khoa cu. `corrected` chi co o harness da do duoc cells_per_command.
        c = s.get("corrected")
        if c:
            budget = "%.1f phut/2 nhanh (+30%%: %.1f)" % (
                c["minutes_two_branches"], c["minutes_two_branches_plus_30pct"])
        else:
            budget = "SUPERSEDED %.2f h (gia dinh 1 lenh/o, 960 o)" % s[
                "superseded_hours_for_960_cells_1cmd_per_cell"]
        print("  %-52s n=%3d  %.2f-%.2f s  mean=%.2f  -> %s"
              % (label, s["n_cmd"], s["min"], s["max"], s["mean"], budget))
    print("\n-> %s" % args.out)


if __name__ == "__main__":
    main()

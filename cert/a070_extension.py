#!/usr/bin/env python3
"""A070 nhanh E: NC-E-0, ba cell song moi, truc kappa va sensitivity."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd

from cert import recalibrate_transfer as RT
from cert import recalibration_cost as RC
from cert import transfer_matrix as TM
from cert.cell_matrices import git, json_clean, pin

AMENDMENT = "docs/phase-23/A070-amendment-70.md"
PREREG_TAG = "lesson-23-22d-a-prereg"
REFERENCE = "results/LIVE/phase-23/recalibrate_transfer.json"
A069_PILOT = "results/LIVE/phase-23/a069_pilot.json"
WIRING_OUT = "results/LIVE/phase-23/a070_extension_wiring.json"
OUTPUT = "results/LIVE/phase-23/a070_extension.json"
NEW_LIVE = ("h2@0.740", "poisson@0.780", "poisson@0.820")
N_NEW = 250
N_FULL = 500
A_STARS = (0.30, RT.A_STAR, 0.55)
FLOORS = (0.20, 0.30)
SENS_N_GRID = (30, 60, 120, 250)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(json_clean(value), indent=1, sort_keys=True).encode("utf-8")


def _scientific_payload(artifact: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in artifact.items() if k != "provenance"}


def compare_reference(reference: Mapping[str, Any], generated: Mapping[str, Any]
                      ) -> Dict[str, Any]:
    """So bit payload khoa hoc; timestamp/HEAD dong duoc bam rieng."""
    ref_payload = _canonical(_scientific_payload(reference))
    new_payload = _canonical(_scientific_payload(generated))
    ref_prov = _canonical(reference.get("provenance", {}))
    new_prov = _canonical(generated.get("provenance", {}))
    return {
        "scientific_payload_bit_exact": ref_payload == new_payload,
        "reference_payload_sha256": _sha256_bytes(ref_payload),
        "generated_payload_sha256": _sha256_bytes(new_payload),
        "reference_provenance_sha256": _sha256_bytes(ref_prov),
        "generated_provenance_sha256": _sha256_bytes(new_prov),
        "provenance_expected_to_differ": True,
    }


def run_wiring(reference_path: str = REFERENCE) -> Dict[str, Any]:
    """NC-E-0: chi dung 8 cell cu qua DUNG RT.run()."""
    with open(reference_path, "r", encoding="utf-8") as fh:
        reference = json.load(fh)
    generated = RT.run()
    check = compare_reference(reference, generated)
    return {
        "schema": "dt4n.a070_extension_wiring.v1",
        "amendment": "23-70",
        "prereg_tag": PREREG_TAG,
        "NC_E_0": {
            **check,
            "hit": bool(check["scientific_payload_bit_exact"]),
            "stop_E": not bool(check["scientific_payload_bit_exact"]),
            "scope": "8 live + 4 dead cell cu; toan bo scientific payload",
        },
        "reference": pin(reference_path),
        "provenance": {
            "script": "cert/a070_extension.py::run_wiring",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": git("git", "status", "--porcelain") != "",
            "utc": datetime.now(timezone.utc).isoformat(),
        },
    }


def _new_path(cell: str) -> str:
    mode, rho = cell.split("@")
    return (
        f"results/LIVE/phase-21R/calib_set_{mode}_{float(rho):.3f}_"
        "U3_measured_v7_A069.parquet"
    )


def load_any_cell(cell: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if cell not in NEW_LIVE:
        return TM.load_cell(cell)
    path = _new_path(cell)
    frame = pd.read_parquet(path)
    return (frame[frame["is_calib"]].reset_index(drop=True),
            frame[~frame["is_calib"]].reset_index(drop=True), path)


def load_all_kappa() -> Dict[str, float]:
    old = RT.load_kappa_A()
    with open(A069_PILOT, "r", encoding="utf-8") as fh:
        pilot = json.load(fh)
    by_cell = {row["cell"]: row for row in pilot["cells"]}
    for cell in NEW_LIVE:
        row = by_cell[cell]
        path = _new_path(cell)
        if pin(path)["sha256"] != row["parquet_sha256"]:
            raise RuntimeError(f"A069 parquet digest lech: {cell}")
        old[cell] = float(row["kappa_A"])
    return old


def _draws_at_n(calib: pd.DataFrame, n: int, seed: int = RT.SEED
                ) -> list[pd.DataFrame]:
    rng = np.random.default_rng(seed)
    return [RC.subsample_blocks(calib, int(n), rng).reset_index(drop=True)
            for _ in range(RT.N_DRAWS)]


def run_new_cells(old_live: Sequence[str], all_live: Sequence[str],
                  kappa: Mapping[str, float]) -> tuple[list, Dict[str, Any]]:
    """n=250 tren 3 B moi; A la 11 cell de cham M-218/M-219."""
    rows = []
    paths = {}
    for b in NEW_LIVE:
        calib, test, path = load_any_cell(b)
        paths[b] = pin(path)
        tv = RT.prepare_test(test)
        for draw, sub in enumerate(_draws_at_n(calib, N_NEW)):
            for a in all_live:
                row = RT.run_one(sub, tv, kappa[a], matched=True)
                row.update({"A": a, "B": b, "n": N_NEW, "draw": draw,
                            "branch": "A070-new-live"})
                rows.append(row)
    return rows, paths


def score_m218(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    cells = RT.cells_at_n(rows, N_NEW)
    c3 = RT._by_B(cells, "C3_err_given_accept", NEW_LIVE)
    b2 = RT._by_B(cells, "B2_err_given_accept", NEW_LIVE)
    anchor = RT._by_B(cells, "anchor_err", NEW_LIVE)
    c3_coef = {b: float(c3[b] / anchor[b]) for b in NEW_LIVE}
    b2_coef = {b: float(b2[b] / anchor[b]) for b in NEW_LIVE}
    c3_ratio = max(c3_coef.values()) / min(c3_coef.values())
    b2_ratio = max(b2_coef.values()) / min(b2_coef.values())
    return {
        "n": N_NEW,
        "n_new_B": len(NEW_LIVE),
        "n_A": len({r["A"] for r in rows}),
        "C3R_err_over_anchor": c3_coef,
        "B2R_err_over_anchor": b2_coef,
        "C3R_range_ratio": float(c3_ratio),
        "B2R_range_ratio": float(b2_ratio),
        "hit_C3R": bool(c3_ratio <= 1.60),
        "hit_B2R": bool(b2_ratio >= 1.80),
        "hit": bool(c3_ratio <= 1.60 and b2_ratio >= 1.80),
        "anchors_old_8": {"C3R_range_ratio": 1.22, "B2R_range_ratio": 2.39},
    }


def score_m219(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    levels = ["0.70", "0.50", "0.30", "0.15"]
    by_level = {}
    gaps = []
    all_c3_le_b2 = True
    for level in levels:
        c3 = np.asarray([r["matched"][level]["err_C3R"] for r in rows], float)
        b2 = np.asarray([r["matched"][level]["err_B2R"] for r in rows], float)
        gap = float(np.nanmedian(np.abs(c3 - b2)))
        med_c3, med_b2 = float(np.nanmedian(c3)), float(np.nanmedian(b2))
        gaps.append(gap)
        le = bool(med_c3 <= med_b2)
        all_c3_le_b2 = all_c3_le_b2 and le
        by_level[level] = {
            "median_abs_gap": gap,
            "median_err_C3R": med_c3,
            "median_err_B2R": med_b2,
            "C3R_le_B2R": le,
        }
    flags = [True] + [gaps[i] >= gaps[i - 1] for i in range(1, len(gaps))]
    n_nondecreasing = int(sum(flags))
    return {
        "n": N_NEW,
        "levels_descending_acceptance": levels,
        "by_level": by_level,
        "nondecreasing_flags_including_first": flags,
        "n_nondecreasing_of_4": n_nondecreasing,
        "all_C3R_le_B2R": all_c3_le_b2,
        "hit": bool(n_nondecreasing >= 3 and all_c3_le_b2),
    }


def run_full_kappa(all_live: Sequence[str], kappa: Mapping[str, float]
                  ) -> tuple[list, Dict[str, Any]]:
    rows = []
    paths = {}
    for b in all_live:
        calib, test, path = load_any_cell(b)
        paths[b] = pin(path)
        tv = RT.prepare_test(test)
        for a in all_live:
            row = RT.run_one(calib, tv, kappa[a])
            row.update({"A": a, "B": b, "n": N_FULL, "draw": 0,
                        "branch": "A070-kappa-11"})
            rows.append(row)
    return rows, paths


def score_m220(rows: Sequence[Mapping[str, Any]], kappa: Mapping[str, float]
              ) -> Dict[str, Any]:
    xs, ys, pairs = [], [], []
    for row in rows:
        a, b = row["A"], row["B"]
        if a == b:
            continue
        x = abs(float(np.log(kappa[a] / kappa[b])))
        y = abs(float(row["C3_acceptance_test"] - RT.A_STAR))
        xs.append(x)
        ys.append(y)
        pairs.append({"A": a, "B": b, "abs_log_kappa_ratio": x,
                      "abs_acceptance_error": y})
    spearman = TM._spearman(xs, ys)
    slope = float(np.polyfit(xs, ys, 1)[0])
    return {
        "n": N_FULL,
        "n_cells": len(kappa),
        "n_off_diagonal": len(xs),
        "max_abs_log_kappa_ratio": float(max(xs)),
        "spearman": float(spearman),
        "slope": slope,
        "hit_spearman": bool(spearman >= 0.90),
        "hit_slope": bool(0.40 <= slope <= 0.62),
        "hit": bool(spearman >= 0.90 and 0.40 <= slope <= 0.62),
        "pairs": pairs,
    }


def score_nc_e_1(reference: Mapping[str, Any]) -> Dict[str, Any]:
    dead = reference["cells_dead"]
    cells = RT.cells_at_n(reference["rows_dead"], N_NEW)
    err = RT._by_B(cells, "C3_err_given_accept", dead)
    anchor = RT._by_B(cells, "anchor_err", dead)
    ratios = {b: float(err[b] / anchor[b]) for b in dead}
    n_ge = sum(v >= 0.80 for v in ratios.values())
    return {
        "n": N_NEW,
        "threshold": 0.80,
        "ratios_C3R_err_over_anchor": ratios,
        "n_ge_threshold": int(n_ge),
        "n_cells": len(dead),
        "hit": bool(n_ge >= 3),
        "predicted_to_fail": True,
    }


def _score_n_star(rows: Sequence[Mapping[str, Any]], live: Sequence[str],
                  a_star: float, floor: float) -> Dict[str, Any]:
    n_c3 = n_b2 = None
    by_n = {}
    for n in SENS_N_GRID:
        cells = RT.cells_at_n(rows, n)
        viol = RT._by_B(cells, "C3_viol_given_accept", live)
        acc_c3 = RT._by_B(cells, "C3_acceptance_test", live)
        acc_b2 = RT._by_B(cells, "B2_acceptance_test", live)
        good_c3 = sum(np.isfinite(viol[b]) and viol[b] <= TM.ALPHA_FAMILY
                      and acc_c3[b] >= floor for b in live)
        good_b2 = sum(np.isfinite(acc_b2[b]) and abs(acc_b2[b] - a_star) <= .05
                      for b in live)
        by_n[str(n)] = {"good_C3R": int(good_c3), "good_B2R": int(good_b2)}
        if n_c3 is None and good_c3 >= 7:
            n_c3 = int(n)
        if n_b2 is None and good_b2 >= 7:
            n_b2 = int(n)
    ratio = float(n_c3 / n_b2) if n_c3 is not None and n_b2 else None
    return {
        "a_star": float(a_star), "acceptance_floor": float(floor),
        "n_star_C3R": n_c3, "n_star_B2R": n_b2, "ratio": ratio,
        "by_n": by_n,
        "hit": bool(n_c3 in (60, 120, 250) and ratio is not None and ratio >= 2),
    }


def _sensitivity_rows(live: Sequence[str], a_star: float) -> tuple[list, Dict[str, float]]:
    # a*=A_STAR doc lai artifact da duoc NC-E-0 xac minh; hai muc con lai
    # giai kappa va chay lai cung seed/N_DRAWS cua A068.
    kappa = {}
    loaded = {}
    for cell in live:
        calib, test, _path = load_any_cell(cell)
        loaded[cell] = (calib, test)
        kappa[cell] = float(RT.solve_kappa(calib, target=a_star)["kappa_A"])
    rows = []
    for b in live:
        calib, test = loaded[b]
        tv = RT.prepare_test(test)
        rng = np.random.default_rng(RT.SEED)
        for n in SENS_N_GRID:
            for draw in range(RT.N_DRAWS):
                sub = RC.subsample_blocks(calib, n, rng).reset_index(drop=True)
                for a in live:
                    # RT.run_one dung RT.A_STAR cho B2; C3 dung kappa truyen vao.
                    # B2 voi a* moi duoc thay truc tiep sau khi lay ket qua C3.
                    row = RT.run_one(sub, tv, kappa[a])
                    c = RC.fit_B2(sub, a_star)
                    acc_b2 = tv["m1"] >= c
                    row["c_B2"] = float(c)
                    row["B2_acceptance_test"] = float(acc_b2.mean())
                    row.update({"A": a, "B": b, "n": n, "draw": draw,
                                "branch": f"A070-sensitivity-{a_star:.5f}"})
                    rows.append(row)
    return rows, kappa


def score_m221(reference: Mapping[str, Any], old_live: Sequence[str]
              ) -> Dict[str, Any]:
    results = []
    for a_star in A_STARS:
        if a_star == RT.A_STAR:
            rows = reference["rows"]
            kappa = {k: float(v) for k, v in reference["config"]["kappa_A"].items()}
            source = "NC-E-0-verified-reference"
        else:
            rows, kappa = _sensitivity_rows(old_live, a_star)
            source = "fresh"
        for floor in FLOORS:
            scored = _score_n_star(rows, old_live, a_star, floor)
            scored["source"] = source
            scored["kappa_A"] = kappa
            results.append(scored)
    n_hit = sum(r["hit"] for r in results)
    return {
        "n_combinations": len(results),
        "n_hit": int(n_hit),
        "required_hit": 4,
        "hit": bool(n_hit >= 4),
        "combinations": results,
    }


def run_extension(wiring_path: str = WIRING_OUT,
                  reference_path: str = REFERENCE) -> Dict[str, Any]:
    with open(wiring_path, "r", encoding="utf-8") as fh:
        wiring = json.load(fh)
    if not wiring["NC_E_0"]["hit"]:
        raise RuntimeError("NC-E-0 FAIL: stop-rule E cam chay extension")
    with open(reference_path, "r", encoding="utf-8") as fh:
        reference = json.load(fh)
    old_live = tuple(reference["cells_live"])
    all_live = old_live + NEW_LIVE
    kappa = load_all_kappa()
    if set(kappa) != set(all_live):
        raise RuntimeError("kappa map khong dung 11 cell song")

    new_rows, new_paths = run_new_cells(old_live, all_live, kappa)
    full_rows, full_paths = run_full_kappa(all_live, kappa)
    m218 = score_m218(new_rows)
    m219 = score_m219(new_rows)
    m220 = score_m220(full_rows, kappa)
    nc1 = score_nc_e_1(reference)
    m221 = score_m221(reference, old_live)
    return {
        "schema": "dt4n.a070_extension.v1",
        "lesson": "23.22d",
        "amendment": AMENDMENT,
        "prereg_tag": PREREG_TAG,
        "cells_old": list(old_live),
        "cells_new": list(NEW_LIVE),
        "kappa_A": {k: float(v) for k, v in kappa.items()},
        "predictions": {"M_218": m218, "M_219": m219,
                        "M_220": m220, "M_221": m221},
        "controls": {"NC_E_0": wiring["NC_E_0"], "NC_E_1": nc1},
        "rows_new_n250": new_rows,
        "provenance": {
            "script": "cert/a070_extension.py::run_extension",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": git("git", "status", "--porcelain") != "",
            "utc": datetime.now(timezone.utc).isoformat(),
            "reference": pin(reference_path),
            "wiring": pin(wiring_path),
            "new_parquet": new_paths,
            "all_live_parquet": full_paths,
            "a069_pilot": pin(A069_PILOT),
        },
    }


def _write(path: str, out: Mapping[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(json_clean(out), fh, indent=1, sort_keys=True)


def print_extension(out: Mapping[str, Any]) -> None:
    p, c = out["predictions"], out["controls"]
    print("M-218: %s  C3 %.3fx [<=1.60]  B2 %.3fx [>=1.80]" % (
        p["M_218"]["hit"], p["M_218"]["C3R_range_ratio"],
        p["M_218"]["B2R_range_ratio"]))
    print("M-219: %s  nondecreasing=%d/4  C3<=B2 all=%s" % (
        p["M_219"]["hit"], p["M_219"]["n_nondecreasing_of_4"],
        p["M_219"]["all_C3R_le_B2R"]))
    print("M-220: %s  slope=%.4f  Spearman=%+.4f  max|log ratio|=%.4f" % (
        p["M_220"]["hit"], p["M_220"]["slope"],
        p["M_220"]["spearman"], p["M_220"]["max_abs_log_kappa_ratio"]))
    print("M-221: %s  %d/6 combination HIT" %
          (p["M_221"]["hit"], p["M_221"]["n_hit"]))
    print("NC-E-1: %s  %d/4 ratio >= .80 (du bao FAIL)" % (
        c["NC_E_1"]["hit"], c["NC_E_1"]["n_ge_threshold"]))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--wiring", action="store_true")
    group.add_argument("--run", action="store_true")
    ap.add_argument("--reference", default=REFERENCE)
    ap.add_argument("--wiring-out", default=WIRING_OUT)
    ap.add_argument("--out", default=OUTPUT)
    args = ap.parse_args(list(argv) if argv is not None else None)
    if args.wiring:
        out = run_wiring(args.reference)
        _write(args.wiring_out, out)
        c = out["NC_E_0"]
        print("NC-E-0: %s  payload ref=%s generated=%s" % (
            c["hit"], c["reference_payload_sha256"],
            c["generated_payload_sha256"]))
        print("-> %s" % args.wiring_out)
        return 0 if c["hit"] else 1
    out = run_extension(args.wiring_out, args.reference)
    _write(args.out, out)
    print_extension(out)
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

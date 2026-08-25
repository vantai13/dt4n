#!/usr/bin/env python3
"""Lesson 23.22 / Task B-3 -- tai hieu chuan qua che do, va menh de bao toan.

TRANG THAI HIEN TAI: **CHI CO PILOT**. Nhanh do luong chua ton tai.

`A068` muc 4 cho phep doc TRUOC khi ky muc 5 dung mot thu: gia tri `kappa_A`
cua tung cell, va cac co suy bien tai `kappa_A` tren CHINH cell A. Do la dai
luong PHIA HIEU CHUAN -- mot DAU VAO cua thiet ke, khong phai mot ket qua.
Tien le: `scale(cell)` cua Task B duoc lay tu Task A0 theo dung cach nay
(`A067` muc 5.1).

    a*      = hang so thiet ke toan cuc, acceptance trung binh cua 8 cell song
              tai `kappa = 0.5` (DA DO, `taxonomy_audit.json`)
    kappa_A = `kappa` sao cho C3 tren CALIB cua A dat acceptance = a*

Chay pilot:
    python -m cert.recalibrate_transfer --pilot
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import config_matrix as CM
from cert import transfer_matrix as TM
from cert.build_calib_set_v3 import AOI_V7, Z_EDGES_V7
from cert.cell_matrices import ALPHA_FAMILY, git, json_clean
from cert.taxonomy_audit import SLA_MANIFEST, W_LOSS
from measurements.validity import validity_block

AMENDMENT = "docs/phase-23/A068-amendment-68.md"
PILOT_OUT = "results/LIVE/phase-23/recalibrate_transfer_pilot.json"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POST_VARIANT = TM.POST_VARIANT           # "selective"
MULTIPLICITY = TM.MULTIPLICITY           # "bonferroni"
KAPPA_OP = TM.KAPPA_OP                   # 0.50 -- diem van hanh cua Task B

# `a*` -- MOT LUA CHON THIET KE, khai o `A068` muc 1.1 va muc 9 (`N2`).
# Bang so: `taxonomy_audit.json::cells[].variant_sweep[post=selective,
# kappa=0.5].acceptance`, trung binh tren 8 cell SONG.
A_STAR = 0.42679

# Bisection cho `kappa_A`. Can tren 8 la mot lua chon thiet ke: luoi
# `variant_sweep` chi den `kappa = 2`, va o cell CHET acceptance tai
# `kappa = 2` van gan 1.
KAPPA_LO, KAPPA_HI = 0.0, 8.0
KAPPA_TOL_ACC = 1e-4                     # dung sai tren ACCEPTANCE
KAPPA_TOL_WIDTH = 1e-6                   # dung sai tren be rong khoang
KAPPA_MAX_ITER = 45


# ---------------------------------------------------------------------------
# `kappa_A` -- giai tren CALIB cua A
# ---------------------------------------------------------------------------

def acceptance_at_kappa(calib: pd.DataFrame, kappa: float) -> Tuple[float, Dict[str, Any]]:
    """Acceptance cua C3 tren chinh `calib`, tai mot `kappa`.

    Dung DUNG duong ong cua `TM.fit_on_A`: `fit_config` roi `_q_rows` roi
    `_accept`. Viet lai mot phep do acceptance thu hai la cach tao ra hai
    duong ong co the lech nhau ma khong ai biet.
    """
    fit = CM.fit_config(calib, "C3", float(kappa), alpha=ALPHA_FAMILY,
                        post_variant=POST_VARIANT, multiplicity=MULTIPLICITY)
    keys = CM._keys(POST_VARIANT)
    q_rows = CM._q_rows(calib, keys, fit["_q"], len(CM.SIM_COLS))
    acc = float(CM._accept(calib, CM.MHAT_COLS, q_rows, float(kappa)).mean())
    return acc, fit


def solve_kappa(calib: pd.DataFrame, target: float = A_STAR,
                lo: float = KAPPA_LO, hi: float = KAPPA_HI) -> Dict[str, Any]:
    """Bisection tren `[lo, hi]` cho acceptance(kappa) = `target`.

    acceptance(kappa) la mot ham BAC THANG cua mau huu han, nen `1e-4` co the
    khong voi toi duoc. Bisection giu lai diem TOT NHAT da gap va dung khi
    khoang co be hon `KAPPA_TOL_WIDTH`; ca hai dieu kien dung deu duoc ghi.
    """
    a_lo, fit_lo = acceptance_at_kappa(calib, lo)
    a_hi, fit_hi = acceptance_at_kappa(calib, hi)
    trace = [{"kappa": float(lo), "acceptance": a_lo},
             {"kappa": float(hi), "acceptance": a_hi}]

    best = min(((abs(a_lo - target), float(lo), a_lo, fit_lo),
                (abs(a_hi - target), float(hi), a_hi, fit_hi)),
               key=lambda t: t[0])
    bracketed = bool((a_lo - target) * (a_hi - target) <= 0.0)

    n_iter = 0
    if bracketed:
        x_lo, x_hi, y_lo = float(lo), float(hi), a_lo
        for n_iter in range(1, KAPPA_MAX_ITER + 1):
            mid = 0.5 * (x_lo + x_hi)
            a_mid, fit_mid = acceptance_at_kappa(calib, mid)
            trace.append({"kappa": float(mid), "acceptance": a_mid})
            if abs(a_mid - target) < best[0]:
                best = (abs(a_mid - target), float(mid), a_mid, fit_mid)
            if abs(a_mid - target) <= KAPPA_TOL_ACC:
                break
            if (y_lo - target) * (a_mid - target) <= 0.0:
                x_hi = mid
            else:
                x_lo, y_lo = mid, a_mid
            if (x_hi - x_lo) <= KAPPA_TOL_WIDTH:
                break

    err, kappa, acc, fit = best
    return {
        "kappa_A": float(kappa),
        "acceptance_at_kappa_A": float(acc),
        "abs_error": float(err),
        "bracketed": bracketed,
        "converged_on_acceptance": bool(err <= KAPPA_TOL_ACC),
        "n_iter": int(n_iter),
        "acceptance_at_lo": float(a_lo),
        "acceptance_at_hi": float(a_hi),
        "qhat_source": fit.get("qhat_source"),
        "qhat_has_infinite": bool(fit.get("qhat_has_infinite", False)),
        "qhat_at_sample_max": bool(fit.get("qhat_at_sample_max", False)),
        "min_blocks_at_final_qhat": fit.get("min_blocks_at_final_qhat"),
        "degenerate": bool(fit.get("degenerate", False)),
        "n_iter_fit": int(fit.get("n_iter", 0)),
        "trace": trace,
    }


# ---------------------------------------------------------------------------
# PILOT
# ---------------------------------------------------------------------------

def pilot() -> Dict[str, Any]:
    """`A068` muc 4. Chay TRUOC khi ky muc 5; ket qua duoc commit vao muc 4."""
    live, dead = TM.cells_by_role()
    ref = TM._diag_reference()          # hang V-S @ kappa=0.5, DA DO
    rows: list[Dict[str, Any]] = []
    for role, cells in (("live", live), ("dead", dead)):
        for cell in cells:
            calib, _test, _p = TM.load_cell(cell)
            r = solve_kappa(calib)
            r["cell"] = cell
            r["role"] = role
            r["n_calib_blocks"] = int(calib["block_id"].nunique())
            r["n_calib_rows"] = int(len(calib))
            r["acceptance_at_kappa_0_50"] = (
                float(ref[cell]["acceptance"]) if cell in ref else float("nan"))
            rows.append(r)
            del calib

    # CHAN DUNG (`A068` muc 4): tren cell SONG, `kappa_A` phai ton tai trong
    # [0, 8] VA `fit_config` khong duoc sup ve `none` tai `kappa_A`.
    stop: list[str] = []
    for r in rows:
        if r["role"] != "live":
            continue
        if not r["bracketed"]:
            stop.append("%s: kappa_A khong ton tai trong [%.1f, %.1f] "
                        "(acc %.4f -> %.4f)" % (r["cell"], KAPPA_LO, KAPPA_HI,
                                                r["acceptance_at_lo"],
                                                r["acceptance_at_hi"]))
        if r["qhat_source"] == "degenerate_fallback_to_none":
            stop.append("%s: qhat_source = degenerate_fallback_to_none tai "
                        "kappa_A = %.6f (`L95`)" % (r["cell"], r["kappa_A"]))

    return {
        "schema": "dt4n.recalibrate_transfer_pilot.v1",
        "lesson": "23.22",
        "task": "B-3 PILOT",
        "amendment": AMENDMENT,
        "config": {
            "a_star": A_STAR, "kappa_lo": KAPPA_LO, "kappa_hi": KAPPA_HI,
            "kappa_tol_acceptance": KAPPA_TOL_ACC,
            "kappa_tol_width": KAPPA_TOL_WIDTH,
            "kappa_max_iter": KAPPA_MAX_ITER,
            "post_variant": POST_VARIANT, "multiplicity": MULTIPLICITY,
            "alpha_family": ALPHA_FAMILY,
        },
        "rows": rows,
        "stop_rule_violations": stop,
        "validity": validity_block(
            aoi_generator=AOI_V7,
            z_edges=Z_EDGES_V7,
            sla_path=SLA_MANIFEST,
            w_loss=W_LOSS,
        ),
        "provenance": {
            "script": "cert/recalibrate_transfer.py::pilot",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": git("git", "status", "--porcelain") != "",
            "utc": datetime.now(timezone.utc).isoformat(),
        },
    }


def print_pilot(out: Dict[str, Any]) -> None:
    print("a* = %.5f   (acceptance trung binh 8 cell song @ kappa=0.5)"
          % out["config"]["a_star"])
    print("%-16s %5s %10s %9s %11s %26s %11s"
          % ("cell", "role", "acc@k=.50", "kappa_A", "acc@kappa_A",
             "qhat_source@kappa_A", "min_blocks"))
    for r in out["rows"]:
        print("%-16s %5s %10.4f %9.4f %11.4f %26s %11s"
              % (r["cell"], r["role"], r["acceptance_at_kappa_0_50"],
                 r["kappa_A"], r["acceptance_at_kappa_A"],
                 str(r["qhat_source"]), str(r["min_blocks_at_final_qhat"])))
    ks = [r["kappa_A"] for r in out["rows"] if r["role"] == "live"]
    print("\nkappa_A tren 8 cell SONG: min %.4f  trung vi %.4f  max %.4f  "
          "ti so max/min %.2fx"
          % (min(ks), float(np.median(ks)), max(ks), max(ks) / max(min(ks), 1e-12)))
    if out["stop_rule_violations"]:
        print("\n!! CHAN DUNG:")
        for s in out["stop_rule_violations"]:
            print("   %s" % s)
    else:
        print("chan dung: KHONG co vi pham -- duoc phep ky muc 5")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pilot", action="store_true",
                    help="giai `kappa_A` tren 12 cell (`A068` muc 4)")
    ap.add_argument("--out", default=PILOT_OUT)
    args = ap.parse_args(list(argv) if argv is not None else None)
    if not args.pilot:
        ap.error("can --pilot (nhanh do luong chua ton tai)")
    out = pilot()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(json_clean(out), fh, indent=1, sort_keys=True)
    print_pilot(out)
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""T2.6-pre -- cua so BANG KHA THI cho tung o, suy tu bien thien GIUA SEED.

Mot bang chap nhan +/-b quanh mot du doan diem phai thoa hai rang buoc
nguoc chieu:

    b >= k*se        SAN   -- hep hon nhieu thi gate la TUNG XU
    b <  |effect|    TRAN  -- rong hon hieu ung thi du doan KHONG THE SAI

    => cua so kha thi = [ k*se , |effect| )
    => cua so RONG  => INSUFFICIENT_POWER (NT 56): khong doc theo CA HAI
       chieu. Phai biet TRUOC khi chay, khong phai sau.

Cong cu nay KHONG ky gi. No chi tinh cua so tu du lieu da commit, de nguoi
chiu trach nhiem khoa hoc ky mot con so DOC DUOC thay vi chon mot so tron.

`se` uoc tu bien thien GIUA SEED (ke thua ky luat Phase L, xem
docs/phase-L/00f-amendment-5.md:29), KHONG tu so mau trong mot lan chay.

    python3 tools/t2_band_window.py --print
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import subprocess
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = [
    "results/SUPERSEDED/phase-20R/decision_error_tau0.2.parquet",
    "results/SUPERSEDED/phase-20R/decision_error_tau1.0.parquet",
    "results/SUPERSEDED/phase-20R/decision_error_tau5.0.parquet",
]
OUT = ROOT / "docs/phase-T2/02-band-window.json"

K_SIGMA = 3.0            # he so san; ky truoc
N_SEED_T2 = 5            # prereg T2-4 dung 5 seed; se se co lai theo sqrt
BAND_FLOOR = 0.05        # san cung, chan bang vi mo
DEGENERATE_ERR = 0.01    # nguong o suy bien (mau so gan khong)
# |effect| cua nhanh B: du doan rms(28)/rms(0.5) ~ 0.20 => lech khoi 1.0
EFFECT_BRANCH_B = 0.80


def _f(x: float) -> float | None:
    """NaN -> None. JSON chuan KHONG co NaN; mot artifact cong bo ma parser
    chat che khong doc duoc la mot artifact hong."""
    return None if x is None or not math.isfinite(float(x)) else float(x)


def _git(*a: str) -> str:
    try:
        return subprocess.check_output(["git", *a], text=True, cwd=ROOT).strip()
    except Exception:
        return "unknown"


def load() -> pd.DataFrame:
    return pd.concat([pd.read_parquet(ROOT / p) for p in SRC], ignore_index=True)


def seed_dispersion(d: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """sd GIUA SEED cua ti so err(tau_hi)/err(tau_lo), theo tung o.

    Trung binh theo z/tau TRONG tung seed truoc, roi lay sd TREN cac seed.
    Thu tu do quan trong: dao lai se tron bien thien trong-seed vao.
    """
    lo = d[d["tau_rho"] == d["tau_rho"].min()]
    hi = d[d["tau_rho"] == d["tau_rho"].max()]
    key = ["mode", "rho_bar", "seed", "z_over_tau"]
    m = lo.merge(hi, on=key, suffixes=("_lo", "_hi"))
    m = m[m["err_total_lo"] > 0].copy()
    m["ratio"] = m["err_total_hi"] / m["err_total_lo"]

    out: Dict[str, Dict[str, Any]] = {}
    for (mode, rb), grp in m.groupby(["mode", "rho_bar"]):
        per_seed = grp.groupby("seed")["ratio"].mean()
        n = int(len(per_seed))
        sd = float(per_seed.std(ddof=1)) if n > 1 else float("nan")
        out["%s@%.3f" % (mode, rb)] = {
            "n_seed_observed": n,
            "seeds": [int(s) for s in per_seed.index],
            "ratio_mean": float(per_seed.mean()),
            "sd_between_seed": _f(sd),
            "se_observed": _f(sd / math.sqrt(n)) if n > 1 else None,
            "se_projected_n%d" % N_SEED_T2: _f(sd / math.sqrt(N_SEED_T2)) if n > 1 else None,
            "dof": n - 1,
        }
    return out


def baseline_err(d: pd.DataFrame) -> Dict[str, float]:
    g = d.groupby(["mode", "rho_bar"])["err_total"].mean()
    return {"%s@%.3f" % (m, r): float(v) for (m, r), v in g.items()}


def windows(disp: Dict[str, Dict[str, Any]], base: Dict[str, float],
            k: float = K_SIGMA, effect: float = EFFECT_BRANCH_B,
            floor: float = BAND_FLOOR) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for cell, v in disp.items():
        se = v["se_projected_n%d" % N_SEED_T2]
        lo = k * se if se is not None else None
        err = base.get(cell)
        degenerate = err is not None and err < DEGENERATE_ERR
        empty = lo is not None and lo >= effect
        band = max(lo, floor) if lo is not None else None
        if empty or degenerate:
            verdict = "INSUFFICIENT_POWER" if empty else "DEGENERATE"
            band = None
        else:
            verdict = "READABLE"
        out[cell] = {
            "err_baseline": _f(err),
            "se_used": se,
            "band_floor_from_noise": lo,
            "band_ceiling_from_effect": effect,
            "window_empty": bool(empty),
            "degenerate": bool(degenerate),
            "recommended_band": band,
            "verdict": verdict,
        }
    return out


def build(k: float = K_SIGMA) -> Dict[str, Any]:
    d = load()
    disp = seed_dispersion(d)
    base = baseline_err(d)
    win = windows(disp, base, k=k)
    readable = [c for c, v in win.items() if v["verdict"] == "READABLE"]
    return {
        "provenance": {
            "script": "tools/t2_band_window.py",
            "git_commit": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain")),
            "inputs": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                       for p in SRC},
            "se_source": ("bien thien GIUA SEED cua ti so err(tau_max)/err(tau_min) "
                          "tai z/tau co dinh; KHONG dung so mau trong mot lan chay "
                          "(docs/phase-L/00f-amendment-5.md:29)"),
            "caveat": ("sd uoc tu n=3 seed legacy => dof=2, bat dinh cua chinh sd "
                       "rat lon. Phai do lai o diem canh cua T2.6 va viet amendment "
                       "neu lech > 50%."),
        },
        "parameters": {"k_sigma": k, "n_seed_projected": N_SEED_T2,
                       "band_floor": BAND_FLOOR,
                       "effect_branch_B": EFFECT_BRANCH_B,
                       "degenerate_err_threshold": DEGENERATE_ERR},
        "dispersion": disp,
        "windows": win,
        "readable_cells": sorted(readable),
        "excluded_cells": sorted(c for c in win if c not in readable),
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT.relative_to(ROOT)))
    ap.add_argument("-k", type=float, default=K_SIGMA)
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args(argv)

    doc = build(k=a.k)
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True,
                              default=str, allow_nan=False) + "\n")
    print("-> %s" % out.relative_to(ROOT))
    print("   sha256 %s" % hashlib.sha256(out.read_bytes()).hexdigest())

    if a.print:
        print("\n%-18s %9s %9s %9s %10s  %s"
              % ("cell", "err_base", "se(n=5)", "k*se", "band", "verdict"))
        for c in sorted(doc["windows"]):
            w = doc["windows"][c]
            b = w["recommended_band"]
            print("%-18s %9.5f %9.4f %9.4f %10s  %s"
                  % (c, w["err_baseline"], w["se_used"],
                     w["band_floor_from_noise"],
                     "--" if b is None else "%.3f" % b,
                     w["verdict"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

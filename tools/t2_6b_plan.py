#!/usr/bin/env python3
"""T2.6 vong 3 (A-T2-3) -- KE HOACH. THUAN CO CHE, khong nguong nao.

Cung khuon voi tools/t2_6_plan.py: tach CO CHE khoi CHINH SACH. File nay
khong doc mot nguong nao va khong sinh cot verdict/pass/fail.

DON VI CHAY = (cell, a). Mot lenh cert.tau_sweep tinh CA 8 tau x 5 seed.
=> 9 cell x 2 muc a = 18 lenh, KHONG phai 720.

    python3 tools/t2_6b_plan.py --print
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from typing import Any, Dict, List

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/phase-T2/06-run-plan-v3.json"

TAUS = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0)
A_VALS = (0.5, 0.9)
SEEDS = (101, 102, 103, 104, 105)
ORDER_SEED = 7202                  # khac 7200 cua luot truoc
LEVEL_MATCHED_BLOCKS = 25          # (f2): min tren luoi, dat tai tau=20 va 28

# PHAM VI DOC DUOC -- khai TRUOC (A-T2-3 muc "PHAM VI DOC DUOC")
CELLS = {
    ("h2", 0.700):      "CONFIRMATORY",
    ("poisson", 0.850): "CONFIRMATORY",
    ("poisson", 0.925): "CONFIRMATORY",
    ("cbr", 0.700):     "NEGATIVE_CONTROL",
    ("h2", 0.850):      "EXPLORATORY",
    ("h2", 0.925):      "EXPLORATORY",
    ("h2", 0.960):      "EXPLORATORY",
    ("poisson", 0.700): "EXPLORATORY",
    ("poisson", 0.960): "EXPLORATORY",
}


def _git(*a: str) -> str:
    try:
        return subprocess.check_output(["git", *a], text=True, cwd=ROOT).strip()
    except Exception:
        return "unknown"


def plan() -> List[Dict[str, Any]]:
    """Thu tu NGAU NHIEN TOAN PHAN: drift he thong thanh NHIEU, khong thanh
    tin hieu gia trung khit voi truc tau."""
    runs = [{"mode": m, "rho_bar": float(rb), "a": float(a), "scope": sc}
            for (m, rb), sc in CELLS.items() for a in A_VALS]
    rng = np.random.default_rng(ORDER_SEED)
    rng.shuffle(runs)
    for i, r in enumerate(runs):
        r["run_index"] = i
    return runs


def command_for(run: Dict[str, Any], out_dir: str) -> List[str]:
    """Lenh cu the. Khong chua nguong nao.

    DUNG sys.executable, KHONG dung chuoi "python3": tren may nay `python3`
    tro toi miniforge base va KHONG co pandas, nen ca 18 lenh se chet ngay.
    Cung quy uoc voi luot 2 (sweep_r2/run_log.jsonl luu cmd bat dau bang -m).
    """
    return [sys.executable, "-m", "cert.tau_sweep",
            "--axis", "legacy_sawtooth_51ms",  # historical T2/22.6 design
            "--mode", run["mode"],
            "--rho-bar", "%g" % run["rho_bar"],
            "--taus", ",".join("%g" % t for t in TAUS),
            "--a", "%g" % run["a"],
            "--n-mode", "per_tau",
            "--level-matched-blocks", str(LEVEL_MATCHED_BLOCKS),
            "--seeds", *[str(s) for s in SEEDS],
            "--out", "%s/t2_6b_r%03d.json" % (out_dir, run["run_index"])]


def build() -> Dict[str, Any]:
    runs = plan()
    inputs = {}
    for p in ("docs/phase-T2/01-prediction-signed.json",
              "docs/phase-T2/04-estimand-descriptor.json",
              "docs/phase-T2/05-band-window-v2.json"):
        f = ROOT / p
        if f.is_file():
            inputs[p] = hashlib.sha256(f.read_bytes()).hexdigest()
    return {
        "provenance": {
            "script": "tools/t2_6b_plan.py",
            "amendment": "A-T2-3",
            "git_commit": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain")),
            "order_seed": ORDER_SEED,
            "inputs": inputs,
            "note": ("KE HOACH thuan co che. Khong chua k, san, lift_min hay "
                     "eps loai o -- tat ca deu la chinh sach."),
        },
        "estimand_id": "RMS_MARGIN_COST",
        "branch": "z_fixed",
        "grid": {"taus": list(TAUS), "a_values": list(A_VALS),
                 "seeds": list(SEEDS),
                 "level_matched_blocks": LEVEL_MATCHED_BLOCKS},
        "budget_measured_s": {
            "per_cell_per_a": 37.4,
            "total_estimate_s": 37.4 * len(runs),
            "source": "do lai boi chu repo tren poisson@0.925, 5 seed",
        },
        "n_runs": len(runs),
        "runs": runs,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT.relative_to(ROOT)))
    ap.add_argument("--print", action="store_true")
    args = ap.parse_args(argv)
    doc = build()
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True,
                              allow_nan=False) + "\n")
    print("-> %s" % out.relative_to(ROOT))
    print("   sha256 %s" % hashlib.sha256(out.read_bytes()).hexdigest())
    print("   %d lenh, uoc %.1f phut"
          % (doc["n_runs"], doc["budget_measured_s"]["total_estimate_s"] / 60))
    if args.print:
        for r in doc["runs"]:
            print("  %2d  %-8s %.3f  a=%.1f  %s"
                  % (r["run_index"], r["mode"], r["rho_bar"], r["a"], r["scope"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

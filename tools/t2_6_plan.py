#!/usr/bin/env python3
"""T2.6 luot 1 -- sinh KE HOACH chay. THUAN CO CHE, khong nguong nao.

Tach co che khoi chinh sach:

    CO CHE   (file nay)  thu tu chay, diem canh, so hang, provenance
    CHINH SACH (luot 2)  k, san, lift_min, eps loai o -- deu CHUA KY

File nay KHONG doc mot nguong nao va KHONG sinh cot verdict/pass/fail.
Neu ban thay minh muon them mot cot nhu the, do la chinh sach ro vao co
che: chan no o code review.

Hai dieu chinh so voi ban de xuat dau vao, ca hai deu do DO DUOC:

  (1) DON VI CHAY la (tau, branch, a, seed), KHONG phai tung o.
      Mot lenh `decision_error_v2 --run-fixed` tinh CA 10 o x 9 muc z
      trong mot lan (do duoc: 90 hang/lenh). Nen lap ke hoach theo o se
      dem sai so lenh: 7x2x2x5 = 140 lenh, khong phai 980.

  (2) O SUY BIEN VAN DUOC CHAY.
      Ban de xuat loc chung khoi ke hoach (`if is_live(c)`), nhung doi
      chung am V2 lai doi phai DO chung roi xac nhan suy bien. Hai dieu
      do mau thuan. Vi mot lenh dang nao cung tinh moi o, loc chung
      KHONG tiet kiem gi ca. Nen: CHAY het, GAN NHAN, loc o LUOT 2.

    python3 tools/t2_6_plan.py --print
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/phase-T2/03-run-plan.json"

# --- luoi da ky o prereg T2-4 ------------------------------------------
ORDER_SEED = 7200
TAUS: Sequence[float] = (1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0)
A_VALS: Sequence[float] = (0.5, 0.9)
SEEDS: Sequence[int] = (101, 102, 103, 104, 105)
BRANCHES: Sequence[str] = ("fixed", "scaled")

# Diem canh: mot lenh KHONG DOI, lap lai dinh ky. seed=999 nam NGOAI
# thiet ke de canary khong bao gio la mot o cua luoi.
CANARY = {"tau": 3.0, "branch": "fixed", "a": 0.9, "seed": 999}
CANARY_EVERY = 30

# Nguon cua bang nen. CHI de GAN NHAN, khong de loc.
SRC_ERR = [
    "results/SUPERSEDED/phase-20R/decision_error_tau0.2.parquet",
    "results/SUPERSEDED/phase-20R/decision_error_tau1.0.parquet",
    "results/SUPERSEDED/phase-20R/decision_error_tau5.0.parquet",
]
SRC_A = "results/SUPERSEDED/phase-22"


def _git(*a: str) -> str:
    try:
        return subprocess.check_output(["git", *a], text=True, cwd=ROOT).strip()
    except Exception:
        return "unknown"


def baseline_table() -> Dict[str, Dict[str, Any]]:
    """err_baseline va A theo o, doc tu artifact DA COMMIT.

    Day la DU LIEU, khong phai phan quyet: khong epsilon nao duoc ap o day.
    Luot 2 moi ap nguong da ky len bang nay.
    """
    d = pd.concat([pd.read_parquet(ROOT / p) for p in SRC_ERR], ignore_index=True)
    err = d.groupby(["mode", "rho_bar"])["err_total"].mean()
    out: Dict[str, Dict[str, Any]] = {}
    for (mode, rb), v in err.items():
        out["%s@%.3f" % (mode, rb)] = {
            "mode": str(mode), "rho_bar": float(rb),
            "err_baseline": float(v), "A": None,
        }
    for p in sorted((ROOT / SRC_A).glob("tau_sweep_*.json")):
        doc = json.loads(p.read_text())
        fits = [r["ar1_fit"] for r in doc["rows"]]
        key = doc["cell"].replace("@", "@")
        mode, rb = key.split("@")
        k = "%s@%.3f" % (mode, float(rb))
        out.setdefault(k, {"mode": mode, "rho_bar": float(rb),
                           "err_baseline": None, "A": None})
        out[k]["A"] = sum(f["A"] for f in fits) / len(fits)
    return out


def is_live(cell: Dict[str, Any], *, eps_err: float, eps_a: float) -> bool:
    """Vi tu loai o suy bien -- chay tren SO, khong tren TEN O.

    `eps_err` va `eps_a` KHONG co mac dinh: chung la QD-7 cua prereg va
    CHUA DUOC KY. Mot mac dinh im lang o day se lang le quyet dinh o nao
    vao ket qua chinh.

    !! KHONG duoc thay ham nay bang mot danh sach ten o. Bai hoc do duoc:
       de xuat "loai rho_bar=0.96 moi mode" loai nham poisson@0.960
       (err = 0.23132, khoe gap 135 lan nguong) trong khi h2@0.960 that
       su suy bien (err = 0.00171). CUNG rho_bar, KHAC phan quyet.
    """
    err, a = cell.get("err_baseline"), cell.get("A")
    if err is not None and err < float(eps_err):
        return False
    if a is not None and a < float(eps_a):
        return False
    return not (err is None and a is None)


def plan() -> List[Dict[str, Any]]:
    """Ke hoach chay: 140 lenh + diem canh, thu tu ngau nhien TOAN PHAN.

    Ngau nhien hoa de drift he thong (may nong len trong 29 phut) tro
    thanh NHIEU thay vi trung khit voi truc tau va thanh tin hieu gia.
    """
    runs = [
        {"tau": float(t), "branch": b, "a": float(a), "seed": int(s)}
        for t in TAUS for b in BRANCHES for a in A_VALS for s in SEEDS
    ]
    rng = np.random.default_rng(ORDER_SEED)
    rng.shuffle(runs)

    out: List[Dict[str, Any]] = []
    for i, r in enumerate(runs):
        if i % CANARY_EVERY == 0:
            out.append({**CANARY, "run_index": len(out), "is_canary": True})
        out.append({**r, "run_index": len(out), "is_canary": False})
    return out


def command_for(run: Dict[str, Any], out_dir: str) -> List[str]:
    """Lenh cu the cho mot muc ke hoach. Khong chua nguong nao."""
    cmd = ["python3", "-m", "measurements.decision_error_v2", "--run-fixed",
           "--tau", "%g" % run["tau"],
           "--z-mode", run["branch"],
           "--seeds", str(run["seed"]),
           "--out", "%s/t2_6_r%04d.parquet" % (out_dir, run["run_index"])]
    if run["a"] != 0.9:
        cmd += ["--a-override", "%g" % run["a"]]
    return cmd


def build() -> Dict[str, Any]:
    runs = plan()
    base = baseline_table()
    inputs = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
              for p in SRC_ERR}
    for p in sorted((ROOT / SRC_A).glob("tau_sweep_*.json")):
        inputs[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {
        "provenance": {
            "script": "tools/t2_6_plan.py",
            "git_commit": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain")),
            "order_seed": ORDER_SEED,
            "inputs": inputs,
            "note": ("KE HOACH thuan co che. Khong chua k, san, lift_min hay "
                     "eps loai o -- tat ca deu la chinh sach cua luot 2."),
        },
        "grid": {"taus": list(TAUS), "a_values": list(A_VALS),
                 "seeds": list(SEEDS), "branches": list(BRANCHES)},
        "canary": {**CANARY, "every": CANARY_EVERY,
                   "why": ("mot lenh KHONG DOI lap lai dinh ky; seed=999 nam "
                           "NGOAI luoi nen canary khong bao gio la mot o cua "
                           "thiet ke. Neu so cua no troi, moi truong troi -- "
                           "va ta biet KHI NAO.")},
        "baseline_table": base,
        "n_runs": sum(1 for r in runs if not r["is_canary"]),
        "n_canaries": sum(1 for r in runs if r["is_canary"]),
        "runs": runs,
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT.relative_to(ROOT)))
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args(argv)

    doc = build()
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print("-> %s" % out.relative_to(ROOT))
    print("   sha256 %s" % hashlib.sha256(out.read_bytes()).hexdigest())
    print("   %d lenh + %d diem canh" % (doc["n_runs"], doc["n_canaries"]))

    if a.print:
        print("\n=== bang nen (DU LIEU, chua ap nguong nao) ===")
        print("%-18s %13s %14s" % ("cell", "err_baseline", "A"))
        for k in sorted(doc["baseline_table"]):
            v = doc["baseline_table"][k]
            e = "--" if v["err_baseline"] is None else "%.5f" % v["err_baseline"]
            aa = "--" if v["A"] is None else "%.4g" % v["A"]
            print("%-18s %13s %14s" % (k, e, aa))
        print("\n=== 6 muc dau cua ke hoach ===")
        for r in doc["runs"][:6]:
            print("  %3d %-7s tau=%-5g a=%-4g seed=%-4d %s"
                  % (r["run_index"], r["branch"], r["tau"], r["a"], r["seed"],
                     "CANARY" if r["is_canary"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

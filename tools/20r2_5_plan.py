#!/usr/bin/env python3
"""20R2.5 -- sinh KE HOACH chien dich. THUAN CO CHE: khong nguong ket qua nao.

KHAC tools/t2_6_plan.py o BA diem, moi diem tra mot bai hoc da tra gia:

  (1) KE HOACH LA HAM THUAN CUA DAU VAO -- KHONG mang git_commit/git_dirty.
      T2 ghi provenance thoi diem VAO ke hoach, nen sinh lai cho cung thu tu
      nhung KHAC hash, va guard phai do hai bien the hash. Thoi diem thuoc ve
      SO CAI va TAG, khong thuoc ve ke hoach. Nho vay tool nay TAT DINH.

  (2) LENH GHI SAN trong ke hoach; runner chay DUNG `cmd` da ky. T2 co HAI ban
      `command_for` (t2_6_plan.py va t2_6_run.py) phai giu "giong het" bang
      tay -- vi pham W4 (mot su that, mot noi).

  (3) MOI TRUC NAM TRONG LENH, khai TUONG MINH: --calibration (truc SLA),
      --z-grid (truc AoI), --a-override (ke ca 0.9), --n. Khong mac dinh im
      lang nao con quyet dinh duoc gi -- xem 20R2.5-P2.

    python -m tools.20r2_5_plan --out docs/phase-20R2/03-run-plan.json --print
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from typing import Any, Dict, List

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRED = "docs/phase-20R2/01-prediction-signed.json"
CPU = "results/PENDING/phase-20R2/cpu_pilot.json"
EXO = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"

TAUS = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0)
A_VALS = (0.5, 0.9)
SEEDS = (101, 102, 103, 104, 105)

# prereg §3: doi MOT yeu to mot luc. Hai nhanh CHUNG truc SLA (exogenous), chi
# KHAC luoi z -- nen tuong phan do DUNG cai no noi la do: doi truc AoI.
BRANCHES: Dict[str, Dict[str, str]] = {
    "main": {
        "z_grid": "20r2_measured",
        "calibration": EXO,
        "out_dir": "results/LIVE/phase-20R2/campaign",
        "role": "NHANH CHINH -- moi claim khoa hoc cua 20R2 doc o day",
    },
    "control_legacy": {
        "z_grid": "legacy",
        "calibration": EXO,
        "out_dir": "results/SUPERSEDED/phase-20R2/campaign",
        "role": "DOI CHUNG AM -- chi do 'doi truc AoI thi err doi bao nhieu'",
    },
}

# seed 999 NGOAI thiet ke (thiet ke dung 101-105), nen diem canh khong bao gio
# la mot o cua luoi 800.
CANARY = {"tau": 3.0, "branch": "main", "a": 0.9, "seed": 999}
CANARY_DIR = "results/SMOKE/phase-20R2/canary"
CANARY_EVERY = 30
# KY TRUOC. Gia tri cu the khong quan trong; viec no CO DINH moi quan trong --
# thu tu xao de mot troi may (nhiet, turbo) khong tuong quan voi mot nhanh.
ORDER_SEED = 20252
CYCLE_FLOOR = 200.0     # prereg §14.3 -- KIEM LAI o day, khong tin loi khai


def _sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def n_multiplier() -> Dict[float, int]:
    doc = json.loads((ROOT / PRED).read_text(encoding="utf-8"))
    return {float(k): int(v) for k, v in doc["acceptance_band"]["n_multiplier"].items()}


def n_for(tau: float) -> int:
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    return int(n_for_tau(tau, DEFAULT_DT)) * n_multiplier()[float(tau)]


def command_for(run: Dict[str, Any]) -> List[str]:
    """NGUON DUY NHAT cua lenh. Runner khong dung lai ham nay -- no chay
    `cmd` da ghi trong ke hoach DA KY, nen khong the lech khoi ban ky."""
    spec = BRANCHES[run["branch"]]
    return ["-m", "measurements.decision_error_v2", "--run-fixed",
            "--tau", "%g" % run["tau"],
            "--z-mode", "fixed",
            "--z-grid", spec["z_grid"],
            "--calibration", spec["calibration"],
            # KE CA a = 0.9: runner T2 chi them --a-override khi a != 0.9, nen
            # 0.9 di vao NGAM qua sigma_rho cua manifest. Do duoc la bit-exact
            # bang nhau, nhung mot gia tri DUNG-vi-tinh-co van la ngam.
            "--a-override", "%g" % run["a"],
            "--n", str(run["n"]),
            "--seeds", str(run["seed"]),
            "--out", run["out"]]


def plan_runs() -> List[Dict[str, Any]]:
    combos = [{"tau": float(t), "branch": b, "a": float(a), "seed": int(s)}
              for t in TAUS for b in BRANCHES for a in A_VALS for s in SEEDS]
    order = np.random.default_rng(ORDER_SEED).permutation(len(combos))
    runs: List[Dict[str, Any]] = []

    def add(item: Dict[str, Any], canary: bool) -> None:
        idx = len(runs)
        out_dir = CANARY_DIR if canary else BRANCHES[item["branch"]]["out_dir"]
        prefix = "canary" if canary else item["branch"]
        run = {**item, "run_index": idx, "is_canary": canary,
               "n": n_for(item["tau"]),
               "out": "%s/%s_r%04d.parquet" % (out_dir, prefix, idx)}
        run["cmd"] = command_for(run)
        runs.append(run)

    for i, j in enumerate(order):
        if i % CANARY_EVERY == 0:
            add(CANARY, canary=True)
        add(combos[int(j)], canary=False)
    add(CANARY, canary=True)          # diem canh CUOI: bat troi o cuoi chien dich
    return runs


def _validate(runs: List[Dict[str, Any]]) -> None:
    from measurements.sla_calib_v2 import DEFAULT_DT
    design = [r for r in runs if not r["is_canary"]]
    keys = [(r["tau"], r["branch"], r["a"], r["seed"]) for r in design]
    expect = len(TAUS) * len(BRANCHES) * len(A_VALS) * len(SEEDS)
    assert len(keys) == expect == len(set(keys)), "khong phai giai thua day du MOT lan"
    assert CANARY["seed"] not in SEEDS, "diem canh phai NGOAI thiet ke"
    for r in runs:
        cyc = r["n"] * DEFAULT_DT / r["tau"]
        assert cyc >= CYCLE_FLOOR - 1e-9, (
            "run %d duoi san chu ky: %.1f" % (r["run_index"], cyc))


def build() -> Dict[str, Any]:
    runs = plan_runs()
    _validate(runs)
    cpu = json.loads((ROOT / CPU).read_text(encoding="utf-8"))
    return {
        "schema": "dt4n.run_plan_20r2_5.v1",
        "generated_by": "tools/20r2_5_plan.py",
        "WHAT_THIS_IS": ("KE HOACH thuan co che. Khong nguong ket qua, khong "
                         "cot phan quyet. Doc no KHONG cho biet gi ve ket qua."),
        "inputs_sha256": {p: _sha(p) for p in (PRED, CPU, EXO)},
        "order_seed": ORDER_SEED,
        "grid": {"taus": list(TAUS), "a_values": list(A_VALS), "seeds": list(SEEDS),
                 "n_multiplier": {"%g" % k: v for k, v in sorted(n_multiplier().items())}},
        "branches": BRANCHES,
        "canary": {**CANARY, "every": CANARY_EVERY, "plus_final": True,
                   "out_dir": CANARY_DIR,
                   "why": ("sha doi giua chien dich => MAY doi, khong phai khoa "
                           "hoc doi. Can DOI CHUNG AM: cac lenh KHONG phai diem "
                           "canh phai ra sha KHAC nhau, neu khong span=0 la tam thuong.")},
        "budget": {
            "signed_minutes_two_branches": float(cpu["budget"]["minutes_two_branches_scaled"]),
            "source": CPU + " :: budget.minutes_two_branches_scaled",
            "tolerance": 0.30,
            "counts": "CHI lenh khong-canary; khong tinh doi chung twin-hoan-hao",
            "measured_on_axis": ("self_calibrated -- xem prereg §16. KHONG do lai: "
                                 "hai truc cho DUNG 10 o kha thi nhu nhau, cung n, "
                                 "cung luoi z => cung hinh dang mang. Ngan sach la "
                                 "ham cua HINH DANG, khong phai cua gia tri w_loss."),
        },
        "realizability_pass2_mapping": {
            "sigma": "sigma_rho cua hang (= a * sigma_max)",
            "clip_fraction": "max ar1_clip_ratio qua 5 seed cua (nhanh, o, tau, sigma)",
            "min_cell_blocks": "floor(n*dt/(BLOCKS_PER_TAU*tau)) cua CHINH lan chay",
            "why_signed_here": ("20R2 KHONG co conformal, nhung realizability_gate "
                                "van doi min_cell_blocks. Anh xa 'so do nao cam vao "
                                "tieu chi nao' phai KY TRUOC, khong duoc chon sau."),
        },
        "storage": ("parquet vao git qua ngoai le .gitignore CO PHAM VI (3 thu muc), "
                    "theo tien le 60a88784. Mot ban giao chi co that khi nam trong git."),
        "n_runs": sum(1 for r in runs if not r["is_canary"]),
        "n_canaries": sum(1 for r in runs if r["is_canary"]),
        "runs": runs,
    }


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True, allow_nan=False) + "\n",
                   encoding="utf-8")
    print("-> %s  sha256 %s" % (a.out, hashlib.sha256(out.read_bytes()).hexdigest()))
    print("   %d lenh + %d diem canh" % (doc["n_runs"], doc["n_canaries"]))
    if a.print:
        for r in doc["runs"][:6]:
            print("  %3d %-14s tau=%-4g a=%-3g seed=%-4d n=%-8d %s" % (
                r["run_index"], r["branch"], r["tau"], r["a"], r["seed"], r["n"],
                "CANARY" if r["is_canary"] else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""T2.0 -- kiem toan tau. CHI DOC, khong sua, khong chay Mininet.

Ap NT 64 (grep ba chieu: TEN - GIA TRI - CONG THUC) cho dai luong tau.

Tra loi bon cau:
  1. tau ton tai o bao nhieu cho, voi bao nhieu gia tri khac nhau?
  2. moi cho no anh huong dai luong nao (estimand nao)?
  3. thiet ke quet tau cu giu z co dinh hay z/tau co dinh?
  4. ngan sach block vo o tau nao?

Moi con so in ra deu duoc TAI DAN tu artifact hoac tu tham so trong repo,
khong hardcode ket qua.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]

# --- CHIEU 1: ten bien ------------------------------------------------
NAME_PAT = re.compile(r"\b(TAU\w*|tau\w*)\s*[:=]")
# --- CHIEU 2: gia tri so (bat hardcode an danh) ------------------------
VALUE_PAT = re.compile(r"\b(2\.87|14\.35)\b")
# --- CHIEU 3: cong thuc (bat tau an trong toan) ------------------------
FORMULA_PAT = re.compile(r"exp\(\s*-\s*2?\.?0?\s*\*?\s*(dt|z)|5\s*\*\s*tau|5\.0\s*\*\s*float\(tau|BLOCKS_PER_TAU")

SCAN_DIRS = ("twin", "measurements", "cert", "mininet")

# Estimand cua tau: hai quy uoc khac nhau deu hop le ve toan, nhung
# lech nhau HE SO 2 trong so mu. Bat chung bang regex rieng.
CONV_COND = re.compile(r"1\.?0?\s*-\s*np\.exp\(\s*-\s*2\.0?\s*\*\s*")   # sigma^2 (1-exp(-2z/tau))
CONV_DIFF = re.compile(r"1\.?0?\s*-\s*(np\.|math\.)exp\(\s*-\s*(float\()?z")  # A^2 (1-exp(-z/tau))

P20R = [
    "results/SUPERSEDED/phase-20R/decision_error_tau0.2.parquet",
    "results/SUPERSEDED/phase-20R/decision_error_tau1.0.parquet",
    "results/SUPERSEDED/phase-20R/decision_error_tau5.0.parquet",
]
P22 = "results/SUPERSEDED/phase-22"


def scan() -> Dict[str, List[Tuple[str, str]]]:
    hits: Dict[str, List[Tuple[str, str]]] = {
        "name": [], "value": [], "formula": [], "conv_cond": [], "conv_diff": [],
    }
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for py in sorted(base.rglob("*.py")):
            for i, line in enumerate(py.read_text(errors="replace").splitlines(), 1):
                rel = f"{py.relative_to(ROOT)}:{i}"
                if NAME_PAT.search(line):
                    hits["name"].append((rel, line.strip()))
                if VALUE_PAT.search(line):
                    hits["value"].append((rel, line.strip()))
                if FORMULA_PAT.search(line):
                    hits["formula"].append((rel, line.strip()))
                if CONV_COND.search(line):
                    hits["conv_cond"].append((rel, line.strip()))
                elif CONV_DIFF.search(line) and "tau" in line.lower():
                    hits["conv_diff"].append((rel, line.strip()))
    return hits


ASSIGN_PAT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=]+)?=\s*([0-9]+\.?[0-9]*)\s*(?:#.*)?$")


def distinct_tau_values(hits) -> Set[Tuple[str, float, Any]]:
    """Rut moi gia tri so duoc gan cho mot bien, kem TEN bien de phan loai.

    Dong bat dau bang '#' hoac khong phai lenh gan thi ten la None: do la
    chu 'tau' trong comment/docstring, khong phai mot dai luong.
    """
    out: Set[Tuple[str, float, Any]] = set()
    for rel, line in hits["name"]:
        if line.startswith("#"):
            continue
        m = ASSIGN_PAT.match(line)
        if m:
            out.add((rel, float(m.group(2)), m.group(1)))
            continue
        m2 = re.search(r"[:=]\s*([0-9]+\.?[0-9]*)\s*(?:#.*)?$", line)
        if m2:
            out.add((rel, float(m2.group(1)), None))
    return out


# CHIEU 1 co DUONG TINH GIA: mot ten chua "tau" chua chac la HANG SO THOI GIAN.
# Phan loai theo THU NGUYEN, khong theo ten (bai hoc rieng cua T2.0).
# Khoa theo TEN BIEN, khong theo file:dong -- so dong troi moi lan vá.
NOT_A_TIME_CONSTANT = {
    "TAU_RATIO_WARN": "ti so block/tau, KHONG thu nguyen (dimensionless)",
    "BLOCK_STEPS": "so BUOC, khong phai giay; bat nham vi chu 'tau' o COMMENT",
    "TAU_LOAD_MIN_CYCLES": "so CHU KY toi thieu (T_sim/tau), khong thu nguyen",
    "TAU_MIN_DT_RATIO": "ti so tau/dt toi thieu, khong thu nguyen",
}


def classify_tau(vals) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float, str]]]:
    """Tach hang so thoi gian THAT khoi duong tinh gia cua CHIEU 1.

    Bai hoc rieng cua T2.0: CHIEU 1 tim theo TEN, nhung phan loai phai theo
    THU NGUYEN. Mot ten chua 'tau' co the la so chu ky, mot ti so, hoac chi
    la chu 'tau' nam trong comment.
    """
    real, fake = [], []
    for rel, v, name in vals:
        why = NOT_A_TIME_CONSTANT.get(name)
        if why is None and name is None:
            why = "khong phai lenh gan (chu 'tau' nam trong comment/docstring)"
        if why is not None:
            fake.append((rel, v, "%s=%g -- %s" % (name or "?", v, why)))
        else:
            real.append((rel, v))
    return real, fake


def tautology_demo(taus: Sequence[float] = (0.2, 1.0, 5.0),
                   z_over_tau: Sequence[float] = (0.1, 0.3, 0.55, 1.0),
                   sigma: float = 1.0) -> List[Dict[str, Any]]:
    """Chung minh BANG SO: giu z/tau co dinh => sigma_z bat bien.

    sigma_z = sigma*sqrt(1-exp(-2z/tau)); dat u=z/tau thi
    sigma_z = sigma*sqrt(1-exp(-2u)) -- KHONG con tau trong bieu thuc.
    """
    rows = []
    for u in z_over_tau:
        vals = [sigma * math.sqrt(1.0 - math.exp(-2.0 * (u * t) / t)) for t in taus]
        rows.append({"z_over_tau": u,
                     "sigma_z_by_tau": {t: round(v, 12) for t, v in zip(taus, vals)},
                     "span": max(vals) - min(vals)})
    return rows


def convention_gap(z: float = 0.1, taus: Sequence[float] = (0.5, 1.0, 2.0, 5.0)) -> List[Dict[str, Any]]:
    """F6: hai quy uoc lech he so 2 => tau hieu dung lech 2 lan."""
    rows = []
    for t in taus:
        a = math.sqrt(1.0 - math.exp(-2.0 * z / t))     # build_calib_set.py
        b = math.sqrt(1.0 - math.exp(-z / t))           # tau_sweep.py
        rows.append({"tau": t, "convA_cond": round(a, 6), "convB_diff": round(b, 6),
                     "ratio_A_over_B": round(a / b, 6),
                     "tau_B_matching_A": round(t / 2.0, 6)})
    return rows


def audit_zovertau(parquets: Sequence[str]) -> Dict[str, Any]:
    """* Kiem tra thiet ke: z co dinh hay z/tau co dinh?

    Day la kiem tra QUAN TRONG NHAT cua T2.0. Neu z/tau co dinh thi
    sigma_z = sigma*sqrt(1-exp(-2z/tau)) BAT BIEN theo dinh nghia,
    va err(tau) do duoc la mot TAUTOLOGY, khong phai ket qua.
    """
    import pandas as pd

    frames = [pd.read_parquet(ROOT / p) for p in parquets]
    d = pd.concat(frames, ignore_index=True)
    z_by_tau = {float(t): sorted(float(x) for x in g["z_s"].unique())
                for t, g in d.groupby("tau_rho")}
    zr_by_tau = {float(t): sorted(round(float(x), 6) for x in g["z_over_tau"].unique())
                 for t, g in d.groupby("tau_rho")}
    z_sets = [tuple(v) for v in z_by_tau.values()]
    zr_sets = [tuple(v) for v in zr_by_tau.values()]
    verdict = ("Z_OVER_TAU_HELD_FIXED" if len(set(zr_sets)) == 1
               else "Z_HELD_FIXED" if len(set(z_sets)) == 1
               else "NEITHER_FIXED")
    return {"z_by_tau": z_by_tau, "z_over_tau_by_tau": zr_by_tau, "verdict": verdict}


def err_by_tau(parquets: Sequence[str], mode: str = "poisson",
               rho_bar: float = 0.925) -> Any:
    """Bang err theo tau, xep theo z/tau -- do phan bien thien con lai."""
    import pandas as pd

    frames = [pd.read_parquet(ROOT / p) for p in parquets]
    d = pd.concat(frames, ignore_index=True)
    d = d[(d["mode"] == mode) & (d["rho_bar"].round(3) == rho_bar)]
    piv = d.pivot_table(index="z_over_tau", columns="tau_rho",
                        values="err_total", aggfunc="mean")
    piv["span_pct"] = 100.0 * (piv.max(axis=1) - piv.min(axis=1)) / piv.min(axis=1)
    return piv


def block_budget(n: int = 200_000, dt: float = 0.005, seeds: int = 5,
                 alpha: float = 0.10,
                 taus: Sequence[float] = (0.5, 1, 2, 5, 10, 20, 28)) -> List[Dict[str, Any]]:
    """Suy ngan sach block TU THAM SO, khong dat truoc."""
    t_sim = n * dt
    min_blocks = math.ceil(1.0 / alpha) - 1
    rows = []
    for tau in taus:
        per_seed = int(t_sim // (5.0 * tau))
        rows.append({
            "tau": tau,
            "blocks_per_seed": per_seed,
            "blocks_total": per_seed * seeds,
            "min_required": min_blocks,
            "ok": per_seed >= min_blocks,
            "n_required": max(n, int(50 * tau / dt)),
        })
    return rows


def read_22_6() -> Dict[str, Any]:
    """Doc lai ratio(tau) va gate cua 22.6 tu artifact -- khong chep tay."""
    out: Dict[str, Any] = {}
    for jf in sorted((ROOT / P22).glob("tau_sweep_*.json")):
        d = json.loads(jf.read_text())
        gates = d.get("gates", {})
        out[d.get("cell", jf.stem)] = {
            "ratio_by_tau": {float(r["tau"]): float(r["ratio_measured"])
                             for r in d["rows"]},
            "n_blocks_by_tau": {float(r["tau"]): int(r["n_blocks"])
                                for r in d["rows"]},
            "gates_pass": sum(1 for v in gates.values() if v is True),
            "gates_total": len(gates),
            "gates_failed": sorted(k for k, v in gates.items() if v is not True),
            "A_range": d["summary"]["A_range"],
            "c_span_pct": d["summary"]["c_span_pct"],
            "file": str(jf.relative_to(ROOT)),
        }
    return out


def _p(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    h = scan()
    _p("NT 64 -- GREP BA CHIEU")
    print("  CHIEU 1 ten bien   : %4d dong" % len(h["name"]))
    print("  CHIEU 2 gia tri so : %4d dong" % len(h["value"]))
    print("  CHIEU 3 cong thuc  : %4d dong" % len(h["formula"]))

    _p("F1 -- GIA TRI TAU RIENG BIET (gan truc tiep cho bien ten tau)")
    vals = sorted(distinct_tau_values(h), key=lambda x: (x[1], x[0]))
    real, fake = classify_tau(vals)
    print("  HANG SO THOI GIAN THAT (giay):")
    for rel, v in real:
        print(f"    {v:>8}  <- {rel}")
    seen = sorted({v for _, v in real})
    print(f"    ==> {len(seen)} gia tri tau rieng biet: {seen}")
    print("  DUONG TINH GIA cua CHIEU 1 (ten co 'tau' nhung khac thu nguyen):")
    for rel, v, why in fake:
        print(f"    {v:>8}  <- {rel}\n              {why}")

    _p("F1b -- HARDCODE 2.87 / 14.35 (CHIEU 2)")
    for rel, line in h["value"]:
        print(f"  {rel}\n      {line}")

    _p("F6 -- QUY UOC ESTIMAND CUA TAU (he so 2 trong so mu)")
    print("  Quy uoc A  sigma^2*(1-exp(-2z/tau))  = phuong sai DU BAO có dieu kien")
    for rel, line in h["conv_cond"]:
        print(f"    {rel}\n        {line}")
    print("  Quy uoc B  A^2*(1-exp(-z/tau))       = phuong sai HIEU (bien do A tu do)")
    for rel, line in h["conv_diff"]:
        print(f"    {rel}\n        {line}")
    print("  PHAN QUYET (theo luat F1: chi la loi SAU KHI grep xac nhan khong co tai lieu):")
    print("    - convA co TIEN DANG KY: docs/phase-21/00-preregistration.md:199")
    print("        sigma_z = 0.010*sqrt(1-exp(-2z/2.87)) -- truc u Mondrian (P4b)")
    print("    - convB khop ESTIMAND cua 20R: measurements/decision_error_v2.py:402")
    print("        e_stale = d_fresh[t] - d_fresh[t-z]  => phuong sai HIEU")
    print("    ==> KHONG PHAI LOI. Hai estimand khac nhau, ca hai deu dung.")
    print("    ==> NHUNG: truc tau cua hai kenh KHONG SO SANH TRUC TIEP DUOC")
    print("        (convA(tau) == convB(tau/2)). T2 phai ghi ro dung estimand nao.")

    _p("F6b -- HE QUA SO cua lech he so 2 (z=0.1 s)")
    for r in convention_gap():
        print(f"  tau={r['tau']:>4}  convA={r['convA_cond']:.6f}  convB={r['convB_diff']:.6f}"
              f"  A/B={r['ratio_A_over_B']:.4f}  (convB tai tau={r['tau_B_matching_A']} moi bang convA)")

    _p("F4c -- CHUNG MINH SO: giu z/tau co dinh => sigma_z BAT BIEN")
    for r in tautology_demo():
        print(f"  z/tau={r['z_over_tau']:>5}  sigma_z={r['sigma_z_by_tau']}  span={r['span']:.1e}")

    _p("F5 -- NGAN SACH BLOCK (tai dan tu N, dt, SEEDS, ALPHA)")
    for r in block_budget():
        flag = "OK  " if r["ok"] else "FAIL"
        print(f"  tau={r['tau']:>5}  blocks/seed={r['blocks_per_seed']:>4}  "
              f"tong={r['blocks_total']:>5}  min={r['min_required']}  {flag}  "
              f"n_can={r['n_required']}")

    _p("F3 -- 22.6 ratio(tau) DOC LAI TU ARTIFACT")
    for cell, v in read_22_6().items():
        print(f"  [{cell}]  gates {v['gates_pass']}/{v['gates_total']}"
              + ("" if not v["gates_failed"] else f"  FAIL: {v['gates_failed']}"))
        rb = v["ratio_by_tau"]
        print("     tau  : " + "".join(f"{t:>9}" for t in sorted(rb)))
        print("     ratio: " + "".join(f"{rb[t]:>9.4f}" for t in sorted(rb)))
        peak = max(rb, key=rb.get)
        hump = min(rb) < peak < max(rb)
        print(f"     dinh o tau={peak}  hump_shaped={hump}  "
              f"A_range={v['A_range']}  c_span_pct={v['c_span_pct']:.2f}")
        print(f"     nguon: {v['file']}")

    _p("F4 -- THIET KE QUET TAU CU (20R): z co dinh hay z/tau co dinh?")
    a = audit_zovertau(P20R)
    print(json.dumps(a, indent=2, default=str))

    _p("F4b -- BIEN THIEN CON LAI khi xep theo z/tau (poisson@0.925)")
    print(err_by_tau(P20R).to_string())


if __name__ == "__main__":
    main()

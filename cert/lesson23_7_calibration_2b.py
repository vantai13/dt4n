"""Lesson 23.7 buoc [2b] -- hai hieu chuan cuoi truoc Amendment 23-30.

  [2b-i]  M-D11: phan ra Delta acceptance thanh BA NHANH tai S1 va S2.
          M-6 dang do HAI thu cung luc:
            (i)  hieu ung RANG BUOC : bot slot, GIU alpha_each goc
            (ii) hieu ung NGAN SACH : giu 3 slot, NOI alpha_each
            (iii) ca hai            = muc thang that
          Kiem tinh cong duoc: |d(iii) - d(i) - d(ii)|.
          -> dai cho M-6 va M-6b.

  [2b-ii] M-D13: do `P(sua duoc)` khi cam P4, de DAN nguong
            r_crit = 1 + 1 / P(sua duoc)
          thay cho mot hang so tron. -> nguong cho M-13.

  [2b-iii] M-15: dai cho hai cell giu kin, hieu chuan tu 0.2261 (can duoi).

M-16 CO Y KHONG tinh o day: dai cua no dan duoc tu co che (`< 0.90`, duoi muc
danh nghia), nen no ky duoc ma khong can hieu chuan. Tinh no bay gio se ha no
xuong [MO TA] tren cell chinh ma khong duoc gi.

PHAM VI: chi cell chinh `poisson@0.925` -- day la PHONG HIEU CHUAN. Hai cell
giu kin la PHONG THI.

Chay:
    python -m cert.lesson23_7_calibration_2b \
        --out results/SUPERSEDED/phase-23/lesson23_7_calibration_2b.json
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert.cell_matrices import (
    ALPHA_EACH_NOMINAL,
    ALPHA_FAMILY,
    GAMMA_OP,
    HELD_OUT_CELLS,
    KAPPA_ANCHOR,
    LADDER,
    MAIN_CELL,
    N_PATHS,
    TRUTH_TABLE,
    acceptance_for as _acceptance,
    cell_matrices,
    git as _git,
    json_clean as _json_clean,
    load_json as _load_json,
    pin,
    prepare as _prepare,
)
from measurements.decision_error_v2 import TruthTable
from twin import topology_v7 as T7

M_NOMINAL = 3

# M-15: do duoc 0.2261 tren cell chinh, va la CAN DUOI (clip 40%).
M15_OBSERVED_MAIN = 0.22614444
M15_BAND_HELD_OUT = (0.10, 0.40)


# ---------------------------------------------------------------------------
# [2b-i] M-D11 -- phan ra ba nhanh
# ---------------------------------------------------------------------------

def decompose_M6(base: Mapping[str, np.ndarray], prep: Mapping[str, Any]) -> Dict[str, Any]:
    """M-D11: tach hieu ung RANG BUOC khoi hieu ung NGAN SACH alpha."""
    s0 = _acceptance(base, prep, (), ALPHA_EACH_NOMINAL)
    base_acc = s0["acceptance_test"]

    rows: List[Dict[str, Any]] = []
    for label, pruned in LADDER[1:]:
        m_eff = len(T7.PATH_NAMES) - len(pruned) - 1
        alpha_eff = ALPHA_FAMILY / m_eff

        # (i) bot slot NHUNG giu alpha_each goc -> chi hieu ung rang buoc
        br_i = _acceptance(base, prep, pruned, ALPHA_EACH_NOMINAL)
        # (ii) giu du 3 slot NHUNG noi alpha_each -> chi hieu ung ngan sach
        br_ii = _acceptance(base, prep, (), alpha_eff)
        # (iii) ca hai -> muc thang that
        br_iii = _acceptance(base, prep, pruned, alpha_eff)

        d_i = br_i["acceptance_test"] - base_acc
        d_ii = br_ii["acceptance_test"] - base_acc
        d_iii = br_iii["acceptance_test"] - base_acc
        interaction = d_iii - d_i - d_ii

        rows.append(
            {
                "level": label,
                "pruned": ["P%d" % (p + 1) for p in pruned],
                "m_effective": int(m_eff),
                "alpha_each_effective": float(alpha_eff),
                "branch_i_constraint_only": {**br_i, "delta_vs_S0": float(d_i)},
                "branch_ii_budget_only": {**br_ii, "delta_vs_S0": float(d_ii)},
                "branch_iii_both": {**br_iii, "delta_vs_S0": float(d_iii)},
                "M_6_delta_total": float(d_iii),
                "interaction_abs": float(abs(interaction)),
                "interaction_rel_to_total": float(abs(interaction) / abs(d_iii)) if d_iii else None,
                "additive": bool(abs(interaction) < 0.10 * abs(d_iii)) if d_iii else None,
                "M_6b_budget_share": float(d_ii / d_iii) if d_iii else None,
                "constraint_share": float(d_i / d_iii) if d_iii else None,
            }
        )

    s2 = rows[-1]
    total = s2["M_6_delta_total"]
    return {
        "definition": "M-D11: Delta acceptance tai kappa=%.2f, phan ra ba nhanh" % KAPPA_ANCHOR,
        "S0_acceptance": base_acc,
        "alpha_each_nominal": ALPHA_EACH_NOMINAL,
        "levels": rows,
        "M_6_band_from_S2": [
            float(np.floor(total * 0.65 * 100) / 100),
            float(np.ceil(total * 1.35 * 100) / 100),
        ],
        "M_6b_band_from_S2": [
            float(np.floor(s2["M_6b_budget_share"] * 20) / 20),
            float(np.ceil(s2["M_6b_budget_share"] * 20) / 20),
        ],
        "note": (
            "Dai mo +-35% quanh gia tri cell chinh de bao bien thien giua cell. "
            "Cell chinh la HIEU CHUAN; M-6/M-6b cham tren hai cell giu kin."
        ),
    }


# ---------------------------------------------------------------------------
# [2b-ii] M-D13 -- do P(sua duoc), dan r_crit
# ---------------------------------------------------------------------------

def calibrate_r_crit(base: Mapping[str, np.ndarray], prep: Mapping[str, Any]) -> Dict[str, Any]:
    """M-D13: nguong cua M-13 phai DAN tu so lieu, khong dat hang so tron.

    Ke toan chinh xac khi cam duong `p` -- CHI hang twin DANG chon `p` moi doi:
        a = fixable = #(a_twin = p, a* != p)   twin sai vi chon p -> co the sua
        b = broken  = #(a_twin = p, a* = p)    twin dang dung -> cam lam sai
        a + b = #(a_twin = p)                  (phan hoach, kiem duoc)
        gain  = a * P(sua duoc)                P(sua duoc) := fixed / a
        loss  = b
        co lai  <=>  a * P_fix > b  <=>  a/b > 1 / P_fix

    SUA MOT LOI DAI SO trong phac thao. Phac thao dat
        loss = P(a* = p)   va suy ra   r_crit = 1 + 1/P_fix  tren ti so BIEN
        r = P(a_twin=p)/P(a*=p).
    Nhung hang co `a* = p` ma twin KHONG chon p thi da sai san va cam hay khong
    deu sai -- chung KHONG phai chi phi cua viec cam. Do duoc: b = 2227 trong
    khi P(a*=p)*n = 6883, tuc phac thao thoi chi phi len 3.1 lan. Nguong dung
    nam tren TI SO CO DIEU KIEN a/b, khong tren ti so bien r.
    """
    a_star = prep["a_star_full"]
    y_hat = base["y_hat"]
    out: Dict[str, Any] = {"paths": []}

    for p in (3, 1):  # P4 truoc (dong M-13), roi P2 de doi chieu
        keep = [i for i in range(len(T7.PATH_NAMES)) if i != p]
        a_twin_full = y_hat.argmin(axis=1)
        a_twin_pruned = np.asarray(keep)[y_hat[:, keep].argmin(axis=1)]

        picked = a_twin_full == p
        star_is_p = a_star == p
        n = len(a_star)

        fixable = picked & ~star_is_p                 # twin sai vi chon p
        fixed = fixable & (a_twin_pruned == a_star)   # ... va lua chon moi dung
        broken = picked & star_is_p                   # twin dung, cam lam sai

        a = int(fixable.sum())
        b = int(broken.sum())
        p_fix = float(fixed.sum() / a) if a else None
        p_twin_p = float(picked.mean())
        p_star_p = float(star_is_p.mean())
        r_marginal = float(p_twin_p / p_star_p) if p_star_p else None
        r_cond = float(a / b) if b else None
        neutral = bool(a == 0 and b == 0)

        out["paths"].append(
            {
                "path": "P%d" % (p + 1),
                "P_a_twin_eq_p": p_twin_p,
                "P_a_star_eq_p": p_star_p,
                "marginal_ratio_r": r_marginal,
                "n_fixable_a": a,
                "n_broken_b": b,
                "partition_check_a_plus_b": bool(a + b == int(picked.sum())),
                "conditional_ratio_a_over_b": r_cond,
                "n_fixed": int(fixed.sum()),
                "P_sua_duoc": p_fix,
                "r_cond_crit_derived": (1.0 / p_fix) if p_fix else None,
                "gain_fraction": float(fixed.sum() / n),
                "loss_fraction": float(b / n),
                "net_err_change": float((b - fixed.sum()) / n),
                "profitable_exact": bool(fixed.sum() > b),
                "neutral": neutral,
                "r_cond_exceeds_crit": (
                    bool(r_cond > 1.0 / p_fix) if (r_cond is not None and p_fix) else None
                ),
                "sketch_r_crit_WRONG": (1.0 + 1.0 / p_fix) if p_fix else None,
                "sketch_verdict_WRONG": (
                    bool(r_marginal > 1.0 + 1.0 / p_fix)
                    if (r_marginal is not None and p_fix) else None
                ),
            }
        )

    p4 = out["paths"][0]
    out.update(
        {
            "definition": (
                "M-D13: nguong nam tren TI SO CO DIEU KIEN a/b, voi "
                "a/b_crit = 1 / P(sua duoc), do tren cell chinh"
            ),
            "M_13_threshold_r_cond_crit": p4["r_cond_crit_derived"],
            "consistency_check": {
                "claim": "a/b > 1/P_fix phai TUONG DUONG voi ke toan chinh xac",
                "r_cond_exceeds_crit": p4["r_cond_exceeds_crit"],
                "profitable_exact": p4["profitable_exact"],
                "agree": bool(p4["r_cond_exceeds_crit"] == p4["profitable_exact"]),
                "tautology_warning": (
                    "Tren CUNG mot cell, `a/b > 1/P_fix` DONG NHAT voi "
                    "`fixed > b` vi P_fix := fixed/a. Suc du doan cua M-13 den "
                    "tu gia thiet P_fix CHUYEN DUOC sang cell khac, khong tu "
                    "bat dang thuc nay."
                ),
            },
            "sketch_correction": {
                "sketch_threshold": "r_marginal > 1 + 1/P_fix  (SAI)",
                "sketch_says_profitable": p4["sketch_verdict_WRONG"],
                "exact_says_profitable": p4["profitable_exact"],
                "sketch_agrees_with_exact": bool(
                    p4["sketch_verdict_WRONG"] == p4["profitable_exact"]
                ),
                "why_wrong": (
                    "Phac thao lay chi phi = P(a*=p)*n = 6883, nhung chi phi "
                    "THAT la b = 2227 (hang twin DANG dung). Hang co a*=p ma "
                    "twin khong chon p thi da sai san. Phac thao thoi chi phi "
                    "len %.2f lan va do do dat nguong qua cao."
                ) % (p4["P_a_star_eq_p"] * n / max(p4["n_broken_b"], 1)),
            },
        }
    )
    return out


# ---------------------------------------------------------------------------
# [2b-iii] M-15 dai
# ---------------------------------------------------------------------------

def band_M15() -> Dict[str, Any]:
    return {
        "observed_main_cell": M15_OBSERVED_MAIN,
        "is_lower_bound": True,
        "lower_bound_reason": "clip loss tai 0 chiem 40.1% so lan danh gia",
        "main_cell_role": "[MO TA] -- da nhin so, khong tinh diem",
        "scored_on": ["poisson@0.850", "h2@0.700"],
        "band_held_out": list(M15_BAND_HELD_OUT),
        "rationale": (
            "Dai rong [0.10, 0.40] quanh 0.2261 vi hai cell kia co ranking va "
            "khe chi phi khac han; h2 co safety > 10 nen co the lat it hon "
            "NHIEU. Dai van bac bo duoc 'khong dang ke' (< 0.10)."
        ),
    }


# ---------------------------------------------------------------------------
# NT-v2-23 -- bang phai duoc SINH, khong chep tay
# ---------------------------------------------------------------------------

def markdown_tables(rep: Mapping[str, Any]) -> str:
    """Sinh bang markdown tu artifact. Doc phai `include` cai nay."""
    lines: List[str] = []
    d = rep["M_D11_decomposition"]
    lines.append("### M-D11 -- phan ra Delta acceptance (kappa = %.2f)\n" % KAPPA_ANCHOR)
    lines.append("S0 acceptance = `%.6f`, alpha_each danh nghia = `%.5f`\n"
                 % (d["S0_acceptance"], d["alpha_each_nominal"]))
    lines.append("| muc | cat | m | alpha_each | d(i) rang buoc | d(ii) ngan sach "
                 "| d(iii) tong | tuong tac | phan ngan sach |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in d["levels"]:
        lines.append(
            "| %s | %s | %d | %.5f | %+.6f | %+.6f | %+.6f | %.6f | %.4f |"
            % (
                r["level"], ",".join(r["pruned"]) or "-", r["m_effective"],
                r["alpha_each_effective"],
                r["branch_i_constraint_only"]["delta_vs_S0"],
                r["branch_ii_budget_only"]["delta_vs_S0"],
                r["branch_iii_both"]["delta_vs_S0"],
                r["interaction_abs"], r["M_6b_budget_share"],
            )
        )
    lines.append("")

    c = rep["M_D13_r_crit"]
    lines.append("### M-D13 -- nguong dan tu so lieu (ti so CO DIEU KIEN)\n")
    lines.append("| duong | a fixable | b broken | a/b | r bien | P(sua duoc) "
                 "| a/b_crit | sua duoc | co lai |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for r in c["paths"]:
        f = lambda v, s="%.3f": (s % v) if v is not None else "n/a"
        lines.append(
            "| %s | %d | %d | %s | %s | %s | %s | %d | %s |"
            % (
                r["path"], r["n_fixable_a"], r["n_broken_b"],
                f(r["conditional_ratio_a_over_b"]), f(r["marginal_ratio_r"]),
                f(r["P_sua_duoc"], "%.4f"), f(r["r_cond_crit_derived"]),
                r["n_fixed"],
                "trung tinh" if r["neutral"] else ("CO" if r["profitable_exact"] else "KHONG"),
            )
        )
    lines.append("")
    sk = c["sketch_correction"]
    lines.append("Sua dai so: nguong phac thao `%s` cho ket luan `%s`, "
                 "ke toan chinh xac cho `%s`. %s\n"
                 % (sk["sketch_threshold"], sk["sketch_says_profitable"],
                    sk["exact_says_profitable"], sk["why_wrong"]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def build(out_path: str) -> Dict[str, Any]:
    base = cell_matrices(TruthTable(TRUTH_TABLE))
    prep = _prepare(base)
    rep: Dict[str, Any] = {
        "lesson": "23.7",
        "step": "[2b] hieu chuan M-D11 / M-D13 / dai M-15",
        "signs_nothing": True,
        "cell": MAIN_CELL,
        "cell_role": "PHONG HIEU CHUAN -- da nhin so, khong cham diem",
        "held_out_cells": ["poisson@0.850", "h2@0.700"],
        "M16_computed_here": False,
        "M16_reason": (
            "Dai cua M-16 dan duoc tu co che (< 0.90, duoi muc danh nghia), nen "
            "no ky duoc ma khong can hieu chuan. Tinh bay gio chi ha no xuong "
            "[MO TA] tren cell chinh."
        ),
        "M_D11_decomposition": decompose_M6(base, prep),
        "M_D13_r_crit": calibrate_r_crit(base, prep),
        "M_15_band": band_M15(),
    }
    rep["provenance"] = {
        "script": "cert/lesson23_7_calibration_2b.py",
        "truth_table": TRUTH_TABLE,
        "pins_previous_step": pin(
            "results/SUPERSEDED/phase-23/lesson23_7_feasibility.json"
        ),
        "git_hash": _git("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_git("git", "status", "--porcelain", "--untracked-files=no")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "out": out_path,
    }
    return rep


def _print(rep: Mapping[str, Any]) -> None:
    p = print
    p("=" * 78)
    p("LESSON 23.7 -- BUOC [2b] HIEU CHUAN M-D11 / M-D13 / DAI M-15")
    p("cell = %s  (%s)" % (rep["cell"], rep["cell_role"]))
    p("=" * 78)

    d = rep["M_D11_decomposition"]
    p("\n--- [2b-i] M-D11: PHAN RA Delta ACCEPTANCE " + "-" * 34)
    p("S0 acceptance = %.6f   alpha_each danh nghia = %.5f" % (
        d["S0_acceptance"], d["alpha_each_nominal"]))
    p("%-4s %-8s %3s %9s %13s %13s %13s %11s" % (
        "muc", "cat", "m", "a_each", "d(i) rangbuoc", "d(ii) ngansach",
        "d(iii) tong", "tuong tac"))
    for r in d["levels"]:
        p("%-4s %-8s %3d %9.5f %+13.6f %+13.6f %+13.6f %11.6f" % (
            r["level"], ",".join(r["pruned"]), r["m_effective"],
            r["alpha_each_effective"],
            r["branch_i_constraint_only"]["delta_vs_S0"],
            r["branch_ii_budget_only"]["delta_vs_S0"],
            r["branch_iii_both"]["delta_vs_S0"],
            r["interaction_abs"]))
    for r in d["levels"]:
        p("  %s: phan NGAN SACH = %.4f, phan RANG BUOC = %.4f, cong duoc ? %s" % (
            r["level"], r["M_6b_budget_share"], r["constraint_share"], r["additive"]))
    p("dai de xuat M-6  (nhanh iii tai S2) = [%.2f, %.2f]" % tuple(d["M_6_band_from_S2"]))
    p("dai de xuat M-6b (phan ngan sach)   = [%.2f, %.2f]" % tuple(d["M_6b_band_from_S2"]))

    c = rep["M_D13_r_crit"]
    p("\n--- [2b-ii] M-D13: DAN r_crit " + "-" * 47)
    p("%-6s %10s %10s %7s %7s %8s %10s %9s %8s" % (
        "duong", "a fixable", "b broken", "a/b", "r bien", "P(sua)", "a/b_crit",
        "sua duoc", "co lai"))
    for r in c["paths"]:
        fmt = lambda v, f="%.3f": (f % v) if v is not None else "n/a"
        p("%-6s %10d %10d %7s %7s %8s %10s %9d %8s" % (
            r["path"], r["n_fixable_a"], r["n_broken_b"],
            fmt(r["conditional_ratio_a_over_b"]), fmt(r["marginal_ratio_r"]),
            fmt(r["P_sua_duoc"], "%.4f"), fmt(r["r_cond_crit_derived"]),
            r["n_fixed"],
            "trung tinh" if r["neutral"] else ("CO" if r["profitable_exact"] else "KHONG")))
    cc = c["consistency_check"]
    p("nguong M-13 dan duoc: a/b_crit = 1/P(sua duoc) = %.4f" % c["M_13_threshold_r_cond_crit"])
    p("kiem nhat quan: 'a/b > crit' = %s ; ke toan chinh xac = %s ; khop ? %s" % (
        cc["r_cond_exceeds_crit"], cc["profitable_exact"], cc["agree"]))
    p("  luu y: %s" % cc["tautology_warning"].replace("  ", " "))
    sk = c["sketch_correction"]
    p("SUA DAI SO: nguong phac thao '%s'" % sk["sketch_threshold"])
    p("  phac thao noi co lai = %s ; ke toan chinh xac = %s ; khop ? %s" % (
        sk["sketch_says_profitable"], sk["exact_says_profitable"],
        sk["sketch_agrees_with_exact"]))
    p("  %s" % sk["why_wrong"].replace("  ", " "))

    m = rep["M_15_band"]
    p("\n--- [2b-iii] DAI M-15 " + "-" * 55)
    p("do duoc cell chinh = %.6f (CAN DUOI: %s)" % (
        m["observed_main_cell"], m["lower_bound_reason"]))
    p("cell chinh = %s" % m["main_cell_role"])
    p("cham tren = %s ; dai = [%.2f, %.2f]" % (
        ", ".join(m["scored_on"]), m["band_held_out"][0], m["band_held_out"][1]))

    p("\n--- M-16 " + "-" * 67)
    p("KHONG tinh o buoc nay. %s" % rep["M16_reason"])

    p("\n" + "=" * 78)
    p("KHONG dong du doan nao duoc ky o day. Ky o Amendment 23-30.")
    p("=" * 78)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results/SUPERSEDED/phase-23/lesson23_7_calibration_2b.json")
    ap.add_argument("--markdown", default="results/SUPERSEDED/phase-23/lesson23_7_tables.md")
    args = ap.parse_args()
    rep = build(args.out)
    _print(rep)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(_json_clean(rep), fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(args.markdown, "w", encoding="utf-8") as fh:
        fh.write(markdown_tables(rep))
    print("\nartifact -> %s" % args.out)
    print("bang markdown (NT-v2-23, SINH ra chu khong chep) -> %s" % args.markdown)


if __name__ == "__main__":
    main()

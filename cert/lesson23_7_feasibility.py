"""Lesson 23.7 buoc [2a] -- kiem kha thi + ba hieu chuan dai con lai.

Ba viec, theo dung thu tu phu thuoc:

  A. KHA THI (quyet dinh M-12/M-15 co ky duoc khong)
     A1. sha256 cua ba input 20R co khop cai `breakdown_scan_cascade.json` ghi?
     A2. `band_v2` co sinh lai duoc bang tra bi bom, va co TAI LAP dung cu lat
         K4 `P1,P3,P4,P2 -> P3,P1,P4,P2` khong?
     A3. `a_star` trong parquet da commit co tai lap duoc tu stack hien tai?
         (`a_star` la cot THUA KE tu artifact Phase 21R, nen day la mot
         approval test that su, khong phai mot phep tu kiem.)

  B. HIEU CHUAN M-15 -- ti le hang doi `a_star` khi bom residual cascade.
  C. HIEU CHUAN M-6 / M-13 -- thang cat hanh dong S0/S1/S2 (M-D9).
  D. HIEU CHUAN M-11 -- chot dai quanh gia tri MOT PHIA da do o buoc [1].

PHAM VI: chi cell chinh `poisson@0.925`. Hai cell con lai giu kin (SCOPE_GUARD
tai `cert/lesson23_7_range_calibration.py`).

KHONG dong du doan nao duoc ky o day.

Chay:
    python -m cert.lesson23_7_feasibility \
        --out results/phase-23/lesson23_7_feasibility.json
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
    ALPHA_FAMILY,
    CHANNEL,
    GAMMA_OP,
    HELD_OUT_CELLS,
    KAPPA_ANCHOR,
    LADDER,
    MAIN_CALIB,
    MAIN_CELL,
    MODE,
    N_MHAT_BINS,
    N_PATHS,
    RESIDUAL,
    RHO_BAR,
    SCAN_20R,
    SLA_CALIB,
    TRUTH_TABLE,
    VARIANT,
    acceptance_for,
    cell_matrices,
    fit_and_accept as _fit_and_accept,
    git as _git,
    json_clean as _json_clean,
    load_json as _load_json,
    mhat_bin as _mhat_bin,
    pin,
    prepare,
    sha256_of as _sha256,
)
from cert import simultaneous_score as SS
from cert.build_calib_set_v2 import Z_EDGES_PRIMARY, assign_bin, split_by_block
from measurements import band_v2 as B
from measurements import residual_spec as RS
from measurements.decision_error_v2 import CALIBRATION, TruthTable, feasible_cells
from twin import topology_v7 as T7

# Ba diem tren truc residual, doc tu ho so 20R (khong hard-code ket qua).
R_STAR_LO = 0.008804852308259848      # do lon LON NHAT ma K4 con giu
R_STAR = 0.008868196569470351         # do lon dau tien lam VO K4
R_CI90_WORST = 0.010135081793680400   # bien xau CI90 cua residual DO DUOC

K4_BASE_EXPECTED = ("P1", "P3", "P4", "P2")
K4_PERT_EXPECTED = ("P3", "P1", "P4", "P2")

# ---------------------------------------------------------------------------
# A1. Chuoi input co nguyen ven khong
# ---------------------------------------------------------------------------

def verify_input_chain(scan_path: str = SCAN_20R) -> Dict[str, Any]:
    scan = _load_json(scan_path)
    pairs = (
        ("truth_table", TRUTH_TABLE, scan["truth_table_sha256"]),
        ("calibration", SLA_CALIB, scan["calibration_sha256"]),
        ("residual", RESIDUAL, scan["residual_sha256"]),
    )
    rows = []
    for label, path, recorded in pairs:
        exists = os.path.exists(path)
        actual = _sha256(path) if exists else None
        rows.append(
            {
                "input": label,
                "path": path,
                "exists": exists,
                "sha256_recorded": recorded,
                "sha256_actual": actual,
                "match": bool(exists and actual == recorded),
            }
        )
    return {
        "question": "A1: ba input cua scan 20R co con nguyen ven khong?",
        "rows": rows,
        "all_match": bool(all(r["match"] for r in rows)),
        "scan_git_commit": scan.get("git_commit"),
        "scan_git_dirty": scan.get("git_dirty"),
    }


# ---------------------------------------------------------------------------
# A2. band_v2 co tai lap duoc cu lat K4 khong
# ---------------------------------------------------------------------------

def _cells_at_rho_bar() -> List[Mapping[str, Any]]:
    cells = [c for c in feasible_cells(CALIBRATION, include_pc1=True) if str(c["mode"]) != "cbr"]
    return [c for c in cells if abs(float(c["rho_bar"]) - RHO_BAR) < 1e-9]


def reproduce_k4(residual_path: str = RESIDUAL) -> Dict[str, Any]:
    records = RS.load(residual_path)
    tt0 = TruthTable(TRUTH_TABLE)
    cells = _cells_at_rho_bar()
    baseline = {
        "rankings": {
            "%s@%.3f" % (c["mode"], c["rho_bar"]): list(
                B.path_ranking(tt0, str(c["mode"]), float(c["rho_bar"]), float(c["w_loss"]))
            )
            for c in cells
        }
    }
    rec = next(r for r in records if r.mode == MODE and r.channel == CHANNEL)
    key = "%s@%.3f" % (MODE, RHO_BAR)

    rows = []
    for label, ep in (
        ("r_star_lo (K4 con giu)", R_STAR_LO),
        ("r_star (K4 vo)", R_STAR),
        ("|CI90| bien xau", R_CI90_WORST),
    ):
        entry: Dict[str, Any] = {"label": label, "endpoint": float(ep), "signs": {}}
        for sign in (+1.0, -1.0):
            flags = B._k4_flags_for_variant(rec, VARIANT, float(ep), float(sign), cells, baseline, records=records)
            entry["signs"]["%+d" % int(sign)] = {
                "K4_preserved": bool(flags["K4_path_ranking_preserved"]),
                "ranking_main_cell": list(flags["rankings"][key]),
            }
        holds, _ = B.variant_k4_holds(rec, VARIANT, float(ep), cells, baseline, records=records)
        entry["variant_k4_holds"] = bool(holds)
        rows.append(entry)

    flip = rows[2]["signs"]["-1"]
    return {
        "question": "A2: band_v2 co sinh lai bang tra bi bom va tai lap cu lat K4?",
        "residual_record": {
            "mode": rec.mode, "channel": rec.channel, "level": rec.level,
            "point": float(rec.point), "se": float(rec.se),
            "ci90": [float(x) for x in rec.ci90],
        },
        "baseline_rankings": baseline["rankings"],
        "endpoints": rows,
        "published_base": list(K4_BASE_EXPECTED),
        "published_pert": list(K4_PERT_EXPECTED),
        "reproduces_published_base": bool(
            tuple(baseline["rankings"][key]) == K4_BASE_EXPECTED
        ),
        "reproduces_published_flip": bool(
            tuple(flip["ranking_main_cell"]) == K4_PERT_EXPECTED
            and not flip["K4_preserved"]
        ),
        "bracket_consistent": bool(
            rows[0]["variant_k4_holds"] and not rows[1]["variant_k4_holds"]
        ),
        "flip_sign": -1,
        "note": (
            "Dau AM la dau cua residual DO DUOC (point = -0.00952). Bom dau "
            "duong KHONG lat -- cu lat la mot chieu."
        ),
    }


# ---------------------------------------------------------------------------
# A3 + B. Tai lap a_star, roi do do nhay
# ---------------------------------------------------------------------------

def verify_astar_reproduces(mats: Mapping[str, np.ndarray]) -> Dict[str, Any]:
    """A3: `a_star` tai lap tu stack hien tai co khop cot DA COMMIT khong?"""
    ref = pd.read_parquet(MAIN_CALIB, columns=["a_star", "a_twin", "block_id", "z_s", "is_calib"])
    a_star_new = mats["y_true"].argmin(axis=1)
    a_twin_new = mats["y_hat"].argmin(axis=1)
    same_len = len(ref) == len(a_star_new)
    out: Dict[str, Any] = {
        "question": "A3: a_star trong parquet (cot THUA KE tu Phase 21R) co tai lap duoc?",
        "n_parquet": int(len(ref)),
        "n_rebuilt": int(len(a_star_new)),
        "same_length": bool(same_len),
    }
    if not same_len:
        out["verdict"] = "KHONG so sanh duoc -- do dai khac nhau"
        return out
    a_star_ref = ref["a_star"].to_numpy(np.int64)
    a_twin_ref = ref["a_twin"].to_numpy(np.int64)
    out.update(
        {
            "a_star_exact_match": bool(np.array_equal(a_star_new, a_star_ref)),
            "a_star_agreement": float(np.mean(a_star_new == a_star_ref)),
            "a_twin_exact_match": bool(np.array_equal(a_twin_new, a_twin_ref)),
            "a_twin_agreement": float(np.mean(a_twin_new == a_twin_ref)),
            "block_id_exact_match": bool(
                np.array_equal(mats["block_id"], ref["block_id"].to_numpy(np.int64))
            ),
            "z_s_max_abs_dev": float(
                np.max(np.abs(mats["z_s"] - ref["z_s"].to_numpy(np.float64)))
            ),
        }
    )
    out["verdict"] = (
        "TAI LAP DUOC" if out["a_star_exact_match"] else "KHONG tai lap chinh xac"
    )
    return out


def sensitivity_astar(
    base: Mapping[str, np.ndarray],
    endpoint: float,
    sign: float = -1.0,
) -> Dict[str, Any]:
    """B / M-15: bom residual vao bang tra, tinh lai a_star, dem hang doi."""
    records = RS.load(RESIDUAL)
    rec = next(r for r in records if r.mode == MODE and r.channel == CHANNEL)
    tt_pert = B.truth_table_for(rec, VARIANT, float(endpoint), sign=float(sign))
    pert = cell_matrices(tt_pert)
    # 20R ghi clip_ratio = 43.20% cho poisson/loss: loss bi chan tai 0 nen tac
    # dong that LON HON cai do duoc. Phai bao cao kem, neu khong M-15 bi doc
    # nhu mot uoc luong khong chech.
    clip = {
        "clip_events": int(getattr(tt_pert, "clip_events", 0)),
        "eval_count": int(getattr(tt_pert, "eval_count", 0)),
    }
    clip["clip_ratio"] = float(clip["clip_events"] / max(clip["eval_count"], 1))
    clip["is_lower_bound"] = bool(clip["clip_ratio"] > 0.01)

    a_star_0 = base["y_true"].argmin(axis=1)
    a_star_1 = pert["y_true"].argmin(axis=1)
    a_twin = base["y_hat"].argmin(axis=1)
    # y_hat KHONG doi: twin khong biet residual. Kiem tra bat bien nay.
    y_hat_unchanged = bool(np.array_equal(base["y_hat"], pert["y_hat"]))

    flip = a_star_0 != a_star_1
    err0 = float(np.mean(a_twin != a_star_0))
    err1 = float(np.mean(a_twin != a_star_1))

    # Hang doi theo cap nao? Dem VECTOR HOA tren TOAN BO hang bi lat -- mot
    # vong lap bi cat ngan se am tham dem thieu.
    n_paths = len(T7.PATH_NAMES)
    codes = a_star_0[flip] * n_paths + a_star_1[flip]
    vals, counts = np.unique(codes, return_counts=True)
    pairs: Dict[str, int] = {
        "%s->%s" % (T7.PATH_NAMES[int(v) // n_paths], T7.PATH_NAMES[int(v) % n_paths]): int(c)
        for v, c in zip(vals, counts)
    }
    assert sum(pairs.values()) == int(flip.sum())

    return {
        "endpoint": float(endpoint),
        "sign": float(sign),
        "clip": clip,
        "y_hat_unchanged_invariant": y_hat_unchanged,
        "n_rows": int(len(flip)),
        "n_flip": int(flip.sum()),
        "M_15_flip_fraction": float(flip.mean()),
        "err_neo_baseline": err0,
        "err_neo_perturbed": err1,
        "delta_err_neo": float(err1 - err0),
        "flip_pairs": dict(sorted(pairs.items(), key=lambda kv: -kv[1])),
        "a_star_dist_baseline": [float(np.mean(a_star_0 == p)) for p in range(len(T7.PATH_NAMES))],
        "a_star_dist_perturbed": [float(np.mean(a_star_1 == p)) for p in range(len(T7.PATH_NAMES))],
    }



def action_ladder(base: Mapping[str, np.ndarray]) -> Dict[str, Any]:
    """M-D9: bao cao ca thang, khong mot diem. -> hieu chuan M-6 va M-13."""
    y_true, y_hat = base["y_true"], base["y_hat"]
    z_bin = assign_bin(base["z_s"], Z_EDGES_PRIMARY)
    split = split_by_block(pd.DataFrame({"block_id": base["block_id"]}))
    is_calib = split["is_calib"].to_numpy(bool)
    block_id = base["block_id"]

    # Chan ly KHONG mat duong khi ta cat: a* van la argmin tren CA 4 duong.
    a_star_full = y_true.argmin(axis=1)

    rows: List[Dict[str, Any]] = []
    for label, pruned in LADDER:
        keep = [p for p in range(len(T7.PATH_NAMES)) if p not in pruned]
        yt, yh = y_true[:, keep], y_hat[:, keep]
        k_eff = len(keep)
        m = k_eff - 1
        alpha_each = ALPHA_FAMILY / m

        m_hat = SS.pair_margins_hat(yh)
        s_pair = SS.pair_scores(yt, yh)
        a_twin = np.asarray(keep)[yh.argmin(axis=1)]
        m_bin = _mhat_bin(m_hat[:, 0], is_calib)

        # SAN LOI: hang ma chan ly chon dung duong bi cat -> chac chan sai.
        floor = float(np.mean(np.isin(a_star_full, list(pruned)))) if pruned else 0.0
        err_all = float(np.mean(a_twin != a_star_full))

        # (i) kappa CO DINH -> M-6 do Delta acceptance
        acc_fixed = _fit_and_accept(
            z_bin, m_bin, block_id, is_calib, m_hat, s_pair, alpha_each, KAPPA_ANCHOR
        )
        # (ii) coverage KHOP 0.78 -> M-13 so err tren cung do bao phu
        lo, hi, best = 0.0, 50.0, 50.0
        for _ in range(45):
            mid = 0.5 * (lo + hi)
            cov = float(
                _fit_and_accept(
                    z_bin, m_bin, block_id, is_calib, m_hat, s_pair, alpha_each, mid
                )[~is_calib].mean()
            )
            if cov >= GAMMA_OP:
                lo, best = mid, mid
            else:
                hi = mid
        acc_m = _fit_and_accept(
            z_bin, m_bin, block_id, is_calib, m_hat, s_pair, alpha_each, best
        )
        test = ~is_calib
        acc_t = acc_m[test]
        wrong_t = (a_twin != a_star_full)[test]

        rows.append(
            {
                "level": label,
                "pruned_paths": ["P%d" % (p + 1) for p in pruned],
                "K_eff": k_eff,
                "m_slots": m,
                "alpha_each": float(alpha_each),
                "error_floor_from_pruning": floor,
                "err_system_all_rows": err_all,
                "acceptance_at_kappa_%.2f" % KAPPA_ANCHOR: float(acc_fixed[test].mean()),
                "kappa_for_coverage_078": float(best),
                "coverage_achieved": float(acc_t.mean()),
                "err_accept_at_078": float(wrong_t[acc_t].mean()),
                "err_reject_at_078": float(wrong_t[~acc_t].mean()),
            }
        )

    base_row = rows[0]
    key = "acceptance_at_kappa_%.2f" % KAPPA_ANCHOR
    for r in rows:
        r["M_6_delta_acceptance_vs_S0"] = float(r[key] - base_row[key])
        r["delta_err_accept_vs_S0"] = float(
            r["err_accept_at_078"] - base_row["err_accept_at_078"]
        )

    # DOI CHUNG: S0 la chinh C3 da chay o Lesson 23.1. Neu no khong tai lap
    # ti le chap nhan da commit thi CA thang deu vo nghia, va M-6/M-13 phai rut.
    committed = _load_json("results/phase-23/fallback_poisson_0.925_k0.5.json")
    ref_rate = float(committed["accept"]["rate"])
    got_rate = float(base_row[key])
    approval = {
        "reference_artifact": "results/phase-23/fallback_poisson_0.925_k0.5.json",
        "committed_accept_rate": ref_rate,
        "ladder_S0_accept_rate": got_rate,
        "abs_gap": float(abs(got_rate - ref_rate)),
        "tolerance": 1e-6,
        "matches": bool(abs(got_rate - ref_rate) < 1e-6),
        "note": (
            "S0 PHAI trung C3 da commit. Neu lech, thang cat khong so sanh duoc "
            "voi ket qua Phase 23 va M-6/M-13 phai rut."
        ),
    }

    s1, s2 = rows[1], rows[2]
    return {
        "definition": "M-D9 thang cat long nhau; a* van tinh tren CA 4 duong",
        "kappa_anchor": KAPPA_ANCHOR,
        "gamma": GAMMA_OP,
        "S0_approval_vs_committed_C3": approval,
        "levels": rows,
        "M_13_cutting_P4_profitable": {
            "question": "Cat them P4 (S1 -> S2) co CO LAI tai gamma = 0.78?",
            "delta_err_accept_S2_minus_S1": float(
                s2["err_accept_at_078"] - s1["err_accept_at_078"]
            ),
            "added_error_floor": float(
                s2["error_floor_from_pruning"] - s1["error_floor_from_pruning"]
            ),
            "delta_acceptance_S2_minus_S1": float(s2[key] - s1[key]),
            "profitable": bool(s2["err_accept_at_078"] < s1["err_accept_at_078"]),
        },
    }


# ---------------------------------------------------------------------------
# D. Chot dai M-11
# ---------------------------------------------------------------------------

def band_M11(prior_path: str = "results/phase-23/lesson23_7_range_calibration.json") -> Dict[str, Any]:
    prior = _load_json(prior_path)
    node = prior["calibration_2_M11"]["free_control_which_residual_definition"]["one_sided_M11"]
    all_test = float(node["ratio_q95_over_mean_mhat1"])
    accept = float(node["ratio_accept_only"])
    half = 0.15
    return {
        "headline_level": "all test rows (M-D10)",
        "one_sided_ratio_all_test": all_test,
        "one_sided_ratio_accept_only": accept,
        "M_14_ratio_accept_over_all": float(accept / all_test),
        "suggested_band_M11": [
            float(np.floor((all_test - half) * 100) / 100),
            float(np.ceil((all_test + half) * 100) / 100),
        ],
        "rationale": (
            "Dai dat quanh gia tri do duoc tren CELL CHINH +-0.15, du rong de "
            "bao bien thien giua cac cell nhung van bac bo duoc gia tri < 1 "
            "(nguong dien giai tu nhien) va gia tri > 2."
        ),
        "band_excludes_1": bool(all_test - half > 1.0),
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def build(out_path: str) -> Dict[str, Any]:
    chain = verify_input_chain()
    k4 = reproduce_k4()
    tt0 = TruthTable(TRUTH_TABLE)
    base = cell_matrices(tt0)
    astar = verify_astar_reproduces(base)

    feasible = bool(
        chain["all_match"]
        and k4["reproduces_published_flip"]
        and k4["reproduces_published_base"]
        and astar.get("a_star_exact_match", False)
    )

    out: Dict[str, Any] = {
        "lesson": "23.7",
        "step": "[2a] kiem kha thi + hieu chuan M-6 / M-11 / M-15",
        "signs_nothing": True,
        "cell": MAIN_CELL,
        "A1_input_chain": chain,
        "A2_k4_reproduction": k4,
        "A3_astar_reproduction": astar,
        "M12_M15_feasible": feasible,
        "feasibility_verdict": (
            "KY DUOC: ca ba mat xich tai lap duoc."
            if feasible
            else "RUT M-12/M-15: mot mat xich khong tai lap duoc (xem A1/A2/A3)."
        ),
    }
    if feasible:
        out["B_M15_sensitivity"] = {
            "at_r_star": sensitivity_astar(base, R_STAR, sign=-1.0),
            "at_ci90_worst": sensitivity_astar(base, R_CI90_WORST, sign=-1.0),
        }
    out["C_action_ladder"] = action_ladder(base)
    out["D_M11_band"] = band_M11()
    out["provenance"] = {
        "script": "cert/lesson23_7_feasibility.py",
        "truth_table": TRUTH_TABLE,
        "residual": RESIDUAL,
        "calib_parquet": MAIN_CALIB,
        "pins_previous_step": pin(
            "results/phase-23/lesson23_7_range_calibration.json"
        ),
        "git_hash": _git("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_git("git", "status", "--porcelain", "--untracked-files=no")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "out": out_path,
    }
    return out


def _print(rep: Mapping[str, Any]) -> None:
    p = print
    p("=" * 78)
    p("LESSON 23.7 -- BUOC [2a] KIEM KHA THI + HIEU CHUAN M-6 / M-11 / M-15")
    p("cell = %s" % rep["cell"])
    p("=" * 78)

    c = rep["A1_input_chain"]
    p("\n--- A1. CHUOI INPUT 20R " + "-" * 53)
    p("%-12s %-52s %s" % ("input", "sha256 (12 dau)", "khop"))
    for r in c["rows"]:
        p("%-12s %-52s %s" % (
            r["input"], (r["sha256_actual"] or "MISSING")[:52],
            "KHOP" if r["match"] else "LECH"))
    p("ca ba khop ? %s   (scan ghi git_commit=%s, dirty=%s)" % (
        c["all_match"], (c["scan_git_commit"] or "")[:12], c["scan_git_dirty"]))

    k = rep["A2_k4_reproduction"]
    p("\n--- A2. TAI LAP CU LAT K4 " + "-" * 51)
    rr = k["residual_record"]
    p("residual do duoc: point = %+.9f  se = %.9f" % (rr["point"], rr["se"]))
    p("                  CI90  = [%+.9f, %+.9f]  level = %s" % (
        rr["ci90"][0], rr["ci90"][1], rr["level"]))
    p("ranking goc (%s) = %s   khop ho so ? %s" % (
        "%s@%.3f" % (MODE, RHO_BAR),
        ",".join(k["baseline_rankings"]["%s@%.3f" % (MODE, RHO_BAR)]),
        k["reproduces_published_base"]))
    p("%-26s %14s %8s %-22s" % ("diem tren truc residual", "do lon", "dau", "ranking cell chinh"))
    for e in k["endpoints"]:
        for sg in ("+1", "-1"):
            d = e["signs"][sg]
            p("%-26s %14.9f %8s %-22s %s" % (
                e["label"] if sg == "+1" else "", e["endpoint"] if sg == "+1" else 0.0,
                sg, ",".join(d["ranking_main_cell"]),
                "" if d["K4_preserved"] else "<- K4 VO"))
    p("bracket nhat quan (giu o r_star_lo, vo o r_star) ? %s" % k["bracket_consistent"])
    p("tai lap DUNG cu lat da cong bo (%s -> %s) ? %s" % (
        ",".join(k["published_base"]), ",".join(k["published_pert"]),
        k["reproduces_published_flip"]))

    a = rep["A3_astar_reproduction"]
    p("\n--- A3. TAI LAP a_star " + "-" * 54)
    p("parquet %d hang, dung lai %d hang, cung do dai ? %s" % (
        a["n_parquet"], a["n_rebuilt"], a["same_length"]))
    if a["same_length"]:
        p("a_star khop TUYET DOI ? %s   (ti le khop %.9f)" % (
            a["a_star_exact_match"], a["a_star_agreement"]))
        p("a_twin khop TUYET DOI ? %s   (ti le khop %.9f)" % (
            a["a_twin_exact_match"], a["a_twin_agreement"]))
        p("block_id khop ? %s   max|lech z_s| = %.2e" % (
            a["block_id_exact_match"], a["z_s_max_abs_dev"]))
    p(">>> %s" % a["verdict"])
    p("\n>>> M-12 / M-15 CO KY DUOC KHONG: %s" % rep["feasibility_verdict"])

    if "B_M15_sensitivity" in rep:
        p("\n--- B. HIEU CHUAN M-15: DO NHAY CUA a_star " + "-" * 34)
        p("%-22s %10s %12s %12s %12s" % (
            "diem bom", "n_flip", "n_flip/n", "err_neo goc", "err_neo bom"))
        for label, s in rep["B_M15_sensitivity"].items():
            p("%-22s %10d %12.8f %12.8f %12.8f" % (
                label, s["n_flip"], s["M_15_flip_fraction"],
                s["err_neo_baseline"], s["err_neo_perturbed"]))
        s = rep["B_M15_sensitivity"]["at_ci90_worst"]
        p("bat bien 'twin khong biet residual' (y_hat khong doi) ? %s" % s["y_hat_unchanged_invariant"])
        p("clip tai bien xau: %d/%d = %.4f  -> M-15 la CAN DUOI ? %s" % (
            s["clip"]["clip_events"], s["clip"]["eval_count"],
            s["clip"]["clip_ratio"], s["clip"]["is_lower_bound"]))
        p("delta err_neo tai bien xau = %+.8f" % s["delta_err_neo"])
        p("cac cap a* bi doi: %s" % (s["flip_pairs"] or "khong co"))
        p("a* phan phoi goc : %s" % " ".join("%.6f" % x for x in s["a_star_dist_baseline"]))
        p("a* phan phoi bom : %s" % " ".join("%.6f" % x for x in s["a_star_dist_perturbed"]))

    L = rep["C_action_ladder"]
    p("\n--- C. THANG CAT HANH DONG S0/S1/S2 (M-D9) " + "-" * 34)
    ap_ = L["S0_approval_vs_committed_C3"]
    p("doi chung S0 vs C3 da commit: %.9f vs %.9f  |lech| = %.2e  -> %s" % (
        ap_["ladder_S0_accept_rate"], ap_["committed_accept_rate"],
        ap_["abs_gap"], "KHOP" if ap_["matches"] else "LECH -- thang KHONG dung duoc"))
    p("%-4s %-10s %4s %4s %8s %10s %11s %11s %11s %11s" % (
        "muc", "cat", "K'", "m", "a_each", "san loi", "acc@k0.5", "d_acc",
        "err|acc@.78", "err toan bo"))
    for r in L["levels"]:
        p("%-4s %-10s %4d %4d %8.4f %10.6f %11.6f %+11.6f %11.6f %11.6f" % (
            r["level"], ",".join(r["pruned_paths"]) or "-", r["K_eff"], r["m_slots"],
            r["alpha_each"], r["error_floor_from_pruning"],
            r["acceptance_at_kappa_0.50"], r["M_6_delta_acceptance_vs_S0"],
            r["err_accept_at_078"], r["err_system_all_rows"]))
    m13 = L["M_13_cutting_P4_profitable"]
    p("M-13: %s" % m13["question"])
    p("  d(err|accept) S2-S1 = %+.6f ; san loi them = %+.6f ; d(acc) = %+.6f" % (
        m13["delta_err_accept_S2_minus_S1"], m13["added_error_floor"],
        m13["delta_acceptance_S2_minus_S1"]))
    p("  CO LAI ? %s" % m13["profitable"])

    d = rep["D_M11_band"]
    p("\n--- D. CHOT DAI M-11 " + "-" * 56)
    p("muc headline = %s" % d["headline_level"])
    p("ti so MOT PHIA all-test = %.4f ; accept-only = %.4f ; M-14 = %.4f" % (
        d["one_sided_ratio_all_test"], d["one_sided_ratio_accept_only"],
        d["M_14_ratio_accept_over_all"]))
    p("dai de xuat M-11 = [%.2f, %.2f]   (loai tru 1.0 ? %s)" % (
        d["suggested_band_M11"][0], d["suggested_band_M11"][1], d["band_excludes_1"]))

    p("\n" + "=" * 78)
    p("KHONG dong du doan nao duoc ky o day. Ky o Amendment 23-30.")
    p("=" * 78)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results/phase-23/lesson23_7_feasibility.json")
    args = ap.parse_args()
    rep = build(args.out)
    _print(rep)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(_json_clean(rep), fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("\nartifact -> %s" % args.out)


if __name__ == "__main__":
    main()

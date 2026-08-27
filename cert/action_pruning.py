#!/usr/bin/env python3
"""Phase 23 / Lesson 23.24 -- khong gian hanh dong hieu dung.

Tien dang ky: docs/phase-23/A074-amendment-74.md
Sua truoc khi chay: docs/phase-23/A074b-amendment-74b.md
Ngan sach: 4 gate (`G23-297..300`).

TAI SAO module nay xay tren `cell_matrices` chu KHONG tren parquet
--------------------------------------------------------------------
`simultaneous_score.pair_scores` danh so cot theo HANG, khong theo DUONG:

    "The column index is a rank slot, never a path identity, so the slot is
     exchangeable across rows."

Muon "cat mot duong" thi phai CAT COT cua ma tran `(n, K)` roi XEP HANG LAI.
`build_calib_set_v3` parquet KHONG luu ma tran `y_hat`/`y_true` -- no chi luu
`a1`, `a2` va cac dai luong theo HANG. Tu parquet ta khong biet mot duong
dang o hang 3 hay hang 4, nen khong biet phai xoa cot nao. Mot module doc
parquet roi "xoa mot cot" van chay, van ra so, va so do SAI im lang.

TAI SAO module nay KHONG goi `cell_matrices.prepare()`
--------------------------------------------------------------------
`prepare()` ghim cung `assign_bin(z_s, Z_EDGES_PRIMARY)` -- truc LEGACY. Tren
truc DO (`measured_v7`, cau hinh song cua 23.23) `z_s` thuoc [0.115, 0.615]
con mien bin cua `Z_EDGES_PRIMARY` la [0.055, 0.5501], nen `prepare()` NEM.
Xem `L130` va `A074b` muc 3. Module nay tu bin bang `Z_EDGES_V7`.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd

from cert import cell_matrices as CMX
from cert import config_matrix as CM
from cert import simultaneous_score as SS
from cert.build_calib_set_v2 import assign_bin, split_by_block
from cert.build_calib_set_v3 import AOI_V7, AXIS_MEASURED, Z_EDGES_V7, _load_cell
from cert.cell_matrices import (
    ALPHA_FAMILY,
    DEAD_ACTION_THRESHOLD,
    MODE,
    N_PATHS,
    RHO_BAR,
    TRUTH_TABLE,
    git,
    json_clean,
    pin,
)
from cert.taxonomy_audit import SLA_MANIFEST, W_LOSS
from cert.transfer_matrix import KAPPA_OP, MULTIPLICITY, POST_VARIANT
from measurements.decision_error_v2 import TruthTable
from measurements.validity import validity_block

AMENDMENT = "docs/phase-23/A074-amendment-74.md"
AMENDMENT_B = "docs/phase-23/A074b-amendment-74b.md"
# `A074` muc 1 cap `results/PENDING/...`. Ca hai truc cua artifact nay
# (`measured_v7_uniform`, `exogenous_g114_S-B`) DA duoc duyet trong
# `axis_registry.json`, nen `test_pending_artifacts_declare_what_they_wait_for`
# bat promote len LIVE/ -- tang PENDING la tu don. Cung duong ma Lesson 23.23
# da di: `A072` muc 1 cung cap PENDING, va `baselines_lit.json` duoc promote
# o commit `6fa8365`. Xem doc 52 muc 9.
OUTPUT = "results/LIVE/phase-23/action_pruning.json"

# Truc DO -- cung truc voi `baselines_lit.json` cua 23.23. KHONG phai legacy.
AXIS = AXIS_MEASURED
AOI_PROFILE = "U0"

# Thang cat. Chi so = chi so DUONG (P1 = 0, P2 = 1, P3 = 2, P4 = 3),
# KHONG phai slot. `test_path_indices_are_zero_based` ghim dieu nay.
RUNGS: Dict[str, Tuple[int, ...]] = {
    "S0_K4": (),        # khong cat            m = 3   alpha_each = 0.033333
    "S1_K3": (1,),      # cat P2 (chet)        m = 2   alpha_each = 0.050000
    "S2_K2": (1, 3),    # cat P2+P4 (do nhay)  m = 1   alpha_each = 0.100000
    "NC_K3": (2,),      # cat P3 (SONG) -- doi chung am `G23-300`
}


def path_name(p: int) -> str:
    return "P%d" % (int(p) + 1)


# ---------------------------------------------------------------------------
# 1. Bac thang -> ngan sach alpha, va hai he qua GIAI TICH
# ---------------------------------------------------------------------------

def m_for(pruned: Sequence[int]) -> int:
    """So BIEN con lai = (so duong giu) - 1.

    Moi phat bieu la mot HIEU so doi voi `a_1`, nen ho co K-1 thanh vien.
    """
    return N_PATHS - len(tuple(pruned)) - 1


def alpha_each_for(pruned: Sequence[int]) -> float:
    """Bonferroni. KHONG doi sang Sidak -- `A074` N4."""
    return SS.alpha_bonferroni(ALPHA_FAMILY, m_for(pruned))


def ladder_analytics() -> Dict[str, Any]:
    """Hai he qua GIAI TICH cua viec cat. KHONG ton gate.

    (1) ngan sach `alpha_each` = alpha / m
    (2) san block toi thieu, `ceil((n+1)(1-alpha_each)) <= n`

    CAM trich dan nhu phat hien thuc nghiem -- day la dai so.
    Tien le `CL-10`, `CL-13`. Xem `A074` muc 7.
    """
    out: Dict[str, Any] = {}
    for name, pruned in RUNGS.items():
        a = alpha_each_for(pruned)
        out[name] = {
            "pruned": [path_name(p) for p in pruned],
            "m": m_for(pruned),
            "alpha_each": float(a),
            "min_blocks": int(CM.conformal_min_blocks(a)),
        }
    return out


# ---------------------------------------------------------------------------
# 2. Dung du lieu -- truc DO, tu bin (KHONG dung `cell_matrices.prepare`)
# ---------------------------------------------------------------------------

def resolve_w_loss() -> float:
    """DOC `w_loss` tu manifest SLA, KHONG nhan lam loi khai (`A075` R6).

    `L132`: ban dau tien cua module nay khong truyen `calibration_path` va
    `w_loss_override`, nen `cell_matrices` roi ve mac dinh `SLA_CALIB`
    (`sla_calibration.json`, self_calibrated, DEPRECATED, `S14`) voi
    `w_loss = 3222.244682` thay vi `5000.0`. Chi phi la
    `delay + w_loss * loss` (`decision_error_v2.py:204`), nen ca thang chi phi
    -- va do do `s`, `q_hat`, `m_hat` -- bi co lai 1/1.5517 = 0.6445 lan.

    Ham nay doc so tu CHINH file manifest bang `_load_cell`, tuc cung nguon
    ma `cell_matrices` dung. `W_LOSS` (hang so cua `taxonomy_audit`) duoc
    dung lam DUONG DOI CHIEU DOC LAP: hai duong phai chi ve cung mot so,
    neu khong thi nem. Mot khoi `validity` chi chep lai loi khai thi khong
    the phat hien lech (`L134`).
    """
    from_manifest = float(_load_cell(MODE, RHO_BAR,
                                     calibration_path=SLA_MANIFEST)["w_loss"])
    if from_manifest != float(W_LOSS):
        raise ValueError(
            "w_loss doc tu %s la %r nhung hang so W_LOSS la %r -- hai nguon "
            "lech nhau, khong duoc doan xem cai nao dung"
            % (SLA_MANIFEST, from_manifest, float(W_LOSS))
        )
    return from_manifest


def build_base() -> Dict[str, np.ndarray]:
    """Ma tran `(n, 4)` day du tren truc DO va truc SLA NGOAI SINH.

    CA HAI tham so duoi day phai TUONG MINH. Mac dinh cua `cell_matrices` la
    truc SLA self_calibrated da DEPRECATED -- xem `L132` / `A075`.
    """
    tt = TruthTable(TRUTH_TABLE)
    return CMX.cell_matrices(
        tt, mode=MODE, rho_bar=RHO_BAR, axis=AXIS, aoi_profile=AOI_PROFILE,
        calibration_path=SLA_MANIFEST, w_loss_override=resolve_w_loss(),
    )


def prepare_v7(base: Mapping[str, np.ndarray]) -> Dict[str, Any]:
    """Bin tuoi tren `Z_EDGES_V7` va chia calib/test theo BLOCK.

    Ban song song cua `cell_matrices.prepare()` nhung tren truc DO. Ly do
    khong tai dung ban goc: no ghim cung `Z_EDGES_PRIMARY` va NEM tren truc
    nay (`L130`, `A074b` muc 3).
    """
    return {
        "z_bin": np.asarray(assign_bin(base["z_s"], Z_EDGES_V7), dtype=np.int64),
        "is_calib": split_by_block(
            pd.DataFrame({"block_id": base["block_id"]})
        )["is_calib"].to_numpy(bool),
        "block_id": base["block_id"],
    }


# ---------------------------------------------------------------------------
# 3. `G23-297` / `M-233` -- hanh dong chet TREN CALIB
# ---------------------------------------------------------------------------
# Loi phai sua: artifact 23.7 ghi `definition_uses = "P(a* = a) on test rows"`.
# Ke hoach muc [4] cua chinh Lesson 23.24 CAM dieu do. Tap TEST vua duoc dung
# de CHON cai can cat vua duoc dung de DANH GIA loi ich -> winner's curse.

def dead_action_calib(base: Mapping[str, np.ndarray],
                      prep: Mapping[str, Any]) -> Dict[str, Any]:
    """Tieu chi HAI TANG cua `A074` muc 3.2, cham tren CALIB.

    TANG 1 ung vien :  P_calib(a* = a)      <  DEAD_ACTION_THRESHOLD (0.05)
    TANG 2 an toan  :  P_calib(a_twin = a) == 0

    Ham nay KHONG duoc doc mot hang TEST nao.
    `test_dead_action_uses_calib_only` quet AST de ep dieu do.
    """
    cal = np.asarray(prep["is_calib"], dtype=bool)
    n = int(cal.sum())
    a_star = base["y_true"][cal].argmin(axis=1)
    a_twin = base["y_hat"][cal].argmin(axis=1)

    p_star = np.bincount(a_star, minlength=N_PATHS) / n
    p_twin = np.bincount(a_twin, minlength=N_PATHS) / n

    tier1 = [p for p in range(N_PATHS) if p_star[p] < DEAD_ACTION_THRESHOLD]
    cut = [p for p in tier1 if p_twin[p] == 0.0]

    return {
        "n_calib_rows": n,
        "threshold": float(DEAD_ACTION_THRESHOLD),
        "P_calib_a_star": {path_name(p): float(p_star[p]) for p in range(N_PATHS)},
        "P_calib_a_twin": {path_name(p): float(p_twin[p]) for p in range(N_PATHS)},
        "tier1_candidates": [path_name(p) for p in tier1],
        "tier2_cut": [path_name(p) for p in cut],
        "cut_indices": [int(p) for p in cut],
        # `A074` N2 -- mot so KHONG tren mau huu han khong phai mot so KHONG
        # tuyet doi. Quy tac ba: chan tren mot phia cho xac suat that.
        "rule_of_three_upper_bound": float(3.0 / n),
        "M_233_hit": bool([int(p) for p in cut] == [1]),   # dai da ky: {P2}
        "note_A074_N2": (
            "`P_calib(a_twin = a) = 0` nghia la CHUA BAO GIO quan sat duoc, "
            "KHONG phai KHONG THE xay ra. Chan tren mot phia = 3/n_calib. "
            "PHAI in canh moi phat bieu ve tinh 'mien phi' cua viec cat."
        ),
    }


# ---------------------------------------------------------------------------
# 4. Cham diem mot bac thang
# ---------------------------------------------------------------------------

def _selective_m_bin(n: int) -> np.ndarray:
    """Thu truc `m_hat` ve MOT o.

    `cell_matrices.fit_and_accept` dung Mondrian HAI truc (`z_bin` x `m_bin`)
    -- cau hinh cua Lesson 23.7. Cau hinh SONG la `selective`, MOT truc
    (`CL-01`). Cach sach nhat de tai dung nguyen ham da dong: truyen `m_bin`
    toan 0. KHONG sua `cell_matrices` -- no la tang day, nhieu artifact da
    dong phu thuoc vao no.
    """
    return np.zeros(int(n), dtype=np.int64)


def qhat_by_zbin(prep: Mapping[str, Any], s_pair: np.ndarray,
                 alpha_each: float) -> Dict[int, np.ndarray]:
    """`q_hat` mot truc, fit TREN CALIB. Cung cong thuc voi `fit_and_accept`.

    `test_accept_matches_closed_path` chung minh no khop BIT voi duong da
    dong khi `m_bin` toan 0 -- nen o day chi co MOT nguon su that cho `q`,
    dung cho ca `accept` lan `viol`.
    """
    cal = np.asarray(prep["is_calib"], dtype=bool)
    z_bin = prep["z_bin"]
    n_slots = s_pair.shape[1]
    q: Dict[int, np.ndarray] = {}
    for zb in np.unique(z_bin):
        sel = cal & (z_bin == zb)
        if not sel.any():
            continue
        n_eff = int(pd.unique(prep["block_id"][sel]).size)
        lvl = SS.conformal_level(n_eff, float(alpha_each))
        q[int(zb)] = np.asarray(
            [SS.empirical_qhat(s_pair[sel, j], lvl) for j in range(n_slots)],
            dtype=np.float64,
        )
    return q


def _q_rows(prep: Mapping[str, Any], q: Mapping[int, np.ndarray],
            n_slots: int) -> np.ndarray:
    miss = np.full(n_slots, np.inf, dtype=np.float64)
    return np.vstack([q.get(int(zb), miss) for zb in prep["z_bin"]])


def score_rung(base: Mapping[str, np.ndarray], prep: Mapping[str, Any],
               pruned: Sequence[int], alpha_each: float | None = None,
               kappa: float = KAPPA_OP) -> Dict[str, Any]:
    """Cat cot -> XEP HANG LAI -> conformal -> chap nhan.

    Bon dong dau la TOAN BO phep cat, va chung phai lam tren ma tran DAY DU:
    xoa cot roi `top_k_by_twin` chay lai, nen slot duoc danh so lai theo tap
    duong con lai.
    """
    pruned = tuple(int(p) for p in pruned)
    keep = [p for p in range(N_PATHS) if p not in pruned]
    yt = base["y_true"][:, keep]
    yh = base["y_hat"][:, keep]
    m_hat = SS.pair_margins_hat(yh)
    s_pair = SS.pair_scores(yt, yh)

    a_each = alpha_each_for(pruned) if alpha_each is None else float(alpha_each)
    q = qhat_by_zbin(prep, s_pair, a_each)
    qrows = _q_rows(prep, q, s_pair.shape[1])

    accept = (m_hat >= float(kappa) * qrows).all(axis=1)
    viol = (s_pair > qrows).any(axis=1)

    kept = np.asarray(keep)
    wrong = kept[yh.argmin(axis=1)] != kept[yt.argmin(axis=1)]

    cal = np.asarray(prep["is_calib"], dtype=bool)
    tst = ~cal

    def _m(mask: np.ndarray, v: np.ndarray) -> float:
        return float(v[mask].mean()) if mask.any() else float("nan")

    # Co CHUAN DOAN cho `A074b` muc 4: bao nhieu hang bi DOI MO NEO.
    anchor_moved = np.isin(base["y_hat"].argmin(axis=1), pruned)

    return {
        "pruned": [path_name(p) for p in pruned],
        "m": int(s_pair.shape[1]),
        "alpha_each": float(a_each),
        "kappa": float(kappa),
        "min_blocks": int(CM.conformal_min_blocks(a_each)),
        "acceptance": _m(tst, accept.astype(float)),
        # `viol_marginal` la dai luong DUY NHAT co dinh ly chong do:
        # conformal bao dam `P(s <= q_hat) >= 1 - alpha` lay ky vong tren mot
        # diem test MOI, KHONG dieu kien gi. `viol_given_accept` la dai luong
        # SAU CHON LOC (post-selection): no dieu kien tren mot bien co phu
        # thuoc du lieu, nen khong bao dam bien nao chuyen sang no.
        # Xem `L135` va `L136`.
        "viol_marginal": _m(tst, viol.astype(float)),
        "viol_given_accept": _m(tst & accept, viol.astype(float)),
        "post_selection_gap": (_m(tst & accept, viol.astype(float))
                               - _m(tst, viol.astype(float))),
        "err_given_accept": _m(tst & accept, wrong.astype(float)),
        "err_anchor": _m(tst, wrong.astype(float)),
        "anchor_moved_rate_all": float(anchor_moved.mean()),
        "qhat_by_zbin": {"z%d" % k: [float(x) for x in v] for k, v in q.items()},
    }


def qhat_ratio(base: Mapping[str, np.ndarray], prep: Mapping[str, Any],
               num: Sequence[int] = (1,), den: Sequence[int] = ()) -> Dict[str, Any]:
    """`M-234`(a): ti so `q_hat(K=3, alpha/2) / q_hat(K=4, alpha/3)`.

    Chi lay cac SLOT CHUNG. Bac K=3 co 2 slot, bac K=4 co 3 slot, nen slot
    chung la 2 slot dau -- dung "2 slot chung" nhu `A074` muc 5 da ky.
    """
    def _s(pruned):
        keep = [p for p in range(N_PATHS) if p not in tuple(pruned)]
        return SS.pair_scores(base["y_true"][:, keep], base["y_hat"][:, keep])

    qn = qhat_by_zbin(prep, _s(num), alpha_each_for(num))
    qd = qhat_by_zbin(prep, _s(den), alpha_each_for(den))
    n_slot = min(min(len(v) for v in qn.values()), min(len(v) for v in qd.values()))

    per: Dict[str, Any] = {}
    vals = []
    for zb in sorted(qn):
        row = [float(qn[zb][j] / qd[zb][j]) for j in range(n_slot)]
        per["z%d" % zb] = row
        vals.extend(row)
    mean = float(np.mean(vals))
    return {
        "numerator": {"pruned": [path_name(p) for p in num],
                      "alpha_each": float(alpha_each_for(num))},
        "denominator": {"pruned": [path_name(p) for p in den],
                        "alpha_each": float(alpha_each_for(den))},
        "n_shared_slots": int(n_slot),
        "ratio_by_zbin": per,
        "ratio_mean": mean,
        "band": [0.88, 0.94],
        "M_234a_hit": bool(0.88 <= mean <= 0.94),
        "analytic_half_normal_ratio": 0.921016,
    }


# ---------------------------------------------------------------------------
# 5. `G23-299` / `M-235` -- phan ra hai kenh
# ---------------------------------------------------------------------------
# Thiet ke GIAI THUA 2x2, chi chay 3 o (o thu tu la S0):
#
#                    giu alpha cua S0      noi alpha_each
#   khong cat            S0  (goc)          nhanh (ii)  NGAN SACH
#   cat                  nhanh (i)          nhanh (iii) CA HAI
#                        RANG BUOC
#
#   tuong tac = (iii) - (i) - (ii) + S0

def decompose(base: Mapping[str, np.ndarray], prep: Mapping[str, Any],
              pruned: Sequence[int]) -> Dict[str, Any]:
    a0 = alpha_each_for(())            # 0.033333 -- ngan sach cua S0
    a1 = alpha_each_for(pruned)        # noi ra
    s0 = score_rung(base, prep, (), a0)["acceptance"]
    br_i = score_rung(base, prep, pruned, a0)["acceptance"]    # CHI rang buoc
    br_ii = score_rung(base, prep, (), a1)["acceptance"]       # CHI ngan sach
    br_iii = score_rung(base, prep, pruned, a1)["acceptance"]  # ca hai

    d_i, d_ii, d_tot = br_i - s0, br_ii - s0, br_iii - s0
    inter = d_tot - d_i - d_ii
    den = abs(d_tot) if abs(d_tot) > 1e-12 else float("nan")
    share = d_ii / den
    return {
        "pruned": [path_name(p) for p in pruned],
        "S0_acceptance": s0,
        "branch_i_constraint_only": {"acceptance": br_i, "delta": d_i,
                                     "alpha_each": a0},
        "branch_ii_budget_only": {"acceptance": br_ii, "delta": d_ii,
                                  "alpha_each": a1},
        "branch_iii_both": {"acceptance": br_iii, "delta": d_tot,
                            "alpha_each": a1},
        "interaction_abs": float(inter),
        "budget_share": float(share),
        "constraint_share": float(d_i / den),
        "interaction_share": float(inter / den),
        "M_235_hit": bool(np.isfinite(share) and share >= 0.90),
        "reading": (
            "`budget_share` cao => cau 'bo hanh dong chet thu ve X% "
            "acceptance' GAY HIEU NHAM: X% do gan nhu toan bo den tu viec tu "
            "noi `alpha_each`, KHONG tu viec don khong gian hanh dong."
        ),
    }


# ---------------------------------------------------------------------------
# 6. `G23-300` / `NC-23.24-1` -- cat mot hanh dong SONG  (BAN SUA `A074b`)
# ---------------------------------------------------------------------------

def negative_control(base: Mapping[str, np.ndarray], prep: Mapping[str, Any],
                     dead: Sequence[int],
                     live: Sequence[int] = (2,)) -> Dict[str, Any]:
    """Cat P3 (song) thay vi P2 (chet). Moi thu khac giu nguyen.

    BAN SUA (`A074b` muc 4): ve (i) `|Delta acceptance| <= 0.02` DA BO.
    `pair_scores` neo vao `a_1 = argmin y_hat`, nen cat mot duong ma twin CO
    chon lam DOI MO NEO. Ve (i) do luong ca hieu ung mo neo, tuc mot phep
    kiem bi nhieu -- cung lop benh voi `L119`. Kenh ngan sach da duoc co lap
    CHINH XAC boi nhanh (ii) cua `M-235`.

    GIU  ve (ii)  `Delta err|accept` >= +0.02          (tren TEST)
    THEM ve (iii) VE CHAN `P_calib(a_twin)`            (tren CALIB)
    """
    dead, live = tuple(dead), tuple(live)
    arm_d = score_rung(base, prep, dead)
    arm_l = score_rung(base, prep, live)

    cal = np.asarray(prep["is_calib"], dtype=bool)
    p_twin = (np.bincount(base["y_hat"][cal].argmin(axis=1), minlength=N_PATHS)
              / int(cal.sum()))

    guard = bool(all(p_twin[p] == 0.0 for p in dead)
                 and all(p_twin[p] > 0.05 for p in live))
    d_err = arm_l["err_given_accept"] - arm_d["err_given_accept"]
    return {
        "dead_arm": arm_d,
        "live_arm": arm_l,
        "delta_err_given_accept": float(d_err),
        "delta_acceptance_reported_not_scored": float(
            arm_l["acceptance"] - arm_d["acceptance"]),
        "anchor_moved_dead": arm_d["anchor_moved_rate_all"],
        "anchor_moved_live": arm_l["anchor_moved_rate_all"],
        "P_calib_a_twin": {path_name(p): float(p_twin[p]) for p in range(N_PATHS)},
        "leg_ii_hit": bool(d_err >= 0.02),
        "leg_iii_guard_pass": guard,
        "interpretable": guard,
        "leg_i_status": "DA BO -- `A074b` muc 4 (nhieu mo neo)",
        "note": (
            "neu `leg_iii_guard_pass` FALSE thi ve (ii) KHONG dien giai duoc: "
            "ta khong con biet minh dang cat mot duong 'song' hay khong."
        ),
    }


# ---------------------------------------------------------------------------
# 7. CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dead", action="store_true",
                    help="chi G23-297 (M-233). Chay TRUOC TIEN va DUNG lai doc.")
    ap.add_argument("--run", action="store_true", help="G23-298..300")
    ap.add_argument("--out", default=OUTPUT)
    args = ap.parse_args()
    if not (args.dead or args.run):
        ap.error("can --dead hoac --run")

    base = build_base()
    prep = prepare_v7(base)

    art: Dict[str, Any] = {
        "schema": "action_pruning/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "amendment": AMENDMENT,
        "amendment_revision": AMENDMENT_B,
        "cell": "%s@%.3f" % (MODE, RHO_BAR),
        "config": {
            "post_variant": POST_VARIANT,
            "multiplicity": MULTIPLICITY,
            "alpha_family": float(ALPHA_FAMILY),
            "kappa_op": float(KAPPA_OP),
            "n_paths": int(N_PATHS),
            "axis": AXIS,
            "aoi_profile": AOI_PROFILE,
            "z_edges": [float(x) for x in Z_EDGES_V7],
            "n_rows": int(len(base["z_s"])),
            # `A075` R6 -- doc tu nguon, khong khai. Test doi so nay khop
            # `validity.w_loss`, tuc hai duong doc lap cung chi mot so.
            "w_loss_used": resolve_w_loss(),
            "w_loss_source": "override",
            "sla_calibration_path": SLA_MANIFEST,
        },
        "ladder_analytics": ladder_analytics(),
        "provenance": {
            "git_head": git("git", "rev-parse", "HEAD"),
            "inputs": [pin(AMENDMENT), pin(AMENDMENT_B), pin(TRUTH_TABLE),
                       pin(SLA_MANIFEST)],
        },
        "validity": validity_block(
            aoi_generator=AOI_V7, z_edges=Z_EDGES_V7,
            sla_path=SLA_MANIFEST, w_loss=W_LOSS,
        ),
    }

    dead = dead_action_calib(base, prep)
    art["G23_297_dead_action"] = dead
    cut = tuple(dead["cut_indices"])

    if args.run:
        if not dead["M_233_hit"]:
            art["K3_scenario"] = (
                "tap CAT tren CALIB != {P2}; cau hinh chinh doi THEO tieu chi "
                "da ky, `A074` muc 6 kich ban K3"
            )
        art["G23_298_rungs"] = {k: score_rung(base, prep, v)
                                for k, v in RUNGS.items()}
        art["G23_298_qhat_ratio"] = qhat_ratio(base, prep, num=cut or (1,), den=())
        art["G23_299_decompose"] = {
            "S1": decompose(base, prep, cut or (1,)),
            "S2": decompose(base, prep, (1, 3)),
        }
        art["G23_300_negative_control"] = negative_control(base, prep, cut or (1,))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(json_clean(art), fh, indent=2, sort_keys=True)
    print("wrote %s" % args.out)


if __name__ == "__main__":
    main()

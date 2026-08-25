#!/usr/bin/env python3
"""Lesson 23.22 / Task B-2 -- chi phi tai hieu chuan cua C3 va B2.

Task B ket luan rang cai C3 co ma B2 khong la *"mot thu tuc da biet de tai lap
`qhat` tu du lieu co nhan cua che do moi, KEM YEU CAU CO MAU DO DUOC"*. Cho
den `A067` do van la mot khang dinh DINH TINH. Module nay do no.

    Tren moi cell, lay `n` block calib co nhan, `n` thuoc `N_GRID`:
        C3 :  hieu chuan lai `qhat(n)`  -> do `viol|accept` va `err` tren test
        B2 :  do lai `c(n)`             -> do `err` tren test

B2 KHONG co `viol|accept`: do no bang `s > qhat` la muon `qhat` cua C3 cho B2,
dung cai bay `A066` muc 3 da tu choi. O day no con te hon: khi `qhat = +inf`
(`n < 29`) thi `s > qhat` sai voi MOI hang, nen B2 hien ra "viol = 0.0000" --
mot con so hoan hao sinh ra tu mot cong cu do hong.

Diem mau chot, VA NO UU DAI B2: `C3` **biet truoc** khi no khong du du lieu --
`qhat = +inf` duoi san hop le (`L91`) hoac `qhat = max mau` duoi san on dinh
(`L93`), va ca hai deu co co trong artifact. `B2` **luon** tra ve mot `c` huu
han o moi `n`, ke ca `n = 1` block, va khong co dai luong nao noi rang so do
vo nghia.

`M-199` (`A067` muc 7, `G23-259`):
    Voi `n < 29` block, C3 gan co o >= 90% so lan lay mau; B2 tra `c` huu han
    o 100% so lan va KHONG co co nao.

Chay:
    python -m cert.recalibration_cost --run
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np
import pandas as pd

from cert import config_matrix as CM
from cert import transfer_matrix as TM
from cert.build_calib_set_v3 import AOI_V7, Z_EDGES_V7
from cert.cell_matrices import ALPHA_FAMILY, git, json_clean, pin
from cert.taxonomy_audit import SLA_MANIFEST, W_LOSS
from measurements.validity import validity_block

AMENDMENT = "docs/phase-23/A067-amendment-67.md"
OUTPUT = "results/LIVE/phase-23/recalibration_cost.json"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KAPPA_OP = TM.KAPPA_OP
POST_VARIANT = TM.POST_VARIANT
MULTIPLICITY = TM.MULTIPLICITY

# Luoi PHAI chua diem duoi san hop le 29 (`L91`), neu khong `M-199` khong cham
# duoc gi. 500 la toan bo so block calib cua mot cell.
N_GRID = (10, 20, 30, 60, 120, 250, 500)
N_DRAWS = 10
SEED = 232205


def subsample_blocks(calib: pd.DataFrame, n_blocks: int,
                     rng: np.random.Generator) -> pd.DataFrame:
    """Lay `n_blocks` block NGUYEN VEN, khong hoan lai.

    Don vi trao doi duoc la BLOCK: `_qhat` dung `block_id.nunique()` lam
    `n_eff`. Lay mot phan hang cua mot block se lam `n_eff` noi doi.
    """
    blocks = calib["block_id"].unique()
    n = int(min(n_blocks, len(blocks)))
    keep = rng.choice(blocks, size=n, replace=False)
    return calib[calib["block_id"].isin(keep)].reset_index(drop=True)


def fit_B2(calib_sub: pd.DataFrame, target_acceptance: float) -> float:
    """`c` = phan vi mau cua `m_hat_1`. LUON huu han, ke ca tu mot block.

    Do chinh la menh de: `c` khong co ly thuyet co mau, nen khong co nguong
    nao de no bao "toi khong du du lieu".
    """
    m1 = calib_sub["m_hat_1"].to_numpy(np.float64)
    q = float(np.clip(1.0 - float(target_acceptance), 0.0, 1.0))
    return float(np.quantile(m1, q, method="higher"))


def recalibrate_once(calib_sub: pd.DataFrame, test: pd.DataFrame,
                     target_acceptance: float | None = None) -> Dict[str, Any]:
    """Mot lan lay mau: hieu chuan lai CA HAI tren cung `calib_sub`.

    `target_acceptance` la DIEM VAN HANH mong muon -- mot lua chon thiet ke,
    khong phai thu hoc duoc tu `n` block. Can no vi duoi san hop le C3 co
    `qhat = +inf` va chap nhan 0 hang; neu B2 chi duoc khop voi acceptance cua
    C3 tren CUNG mau thi no cung bi keo ve 0, va cot B2 o `n` nho khong noi
    duoc gi ve B2.
    """
    fit = CM.fit_config(calib_sub, "C3", KAPPA_OP, alpha=ALPHA_FAMILY,
                        post_variant=POST_VARIANT, multiplicity=MULTIPLICITY)
    keys = CM._keys(POST_VARIANT)
    n_cols = len(CM.SIM_COLS)

    q_calib = CM._q_rows(calib_sub, keys, fit["_q"], n_cols)
    acc_calib = float(CM._accept(calib_sub, CM.MHAT_COLS, q_calib, KAPPA_OP).mean())

    q_test = CM._q_rows(test, keys, fit["_q"], n_cols)
    acc_c3 = CM._accept(test, CM.MHAT_COLS, q_test, KAPPA_OP)
    s = test[list(CM.SIM_COLS)].to_numpy(np.float64)
    viol = (s > q_test).any(axis=1)
    wrong = test["wrong"].to_numpy(bool)

    # B2 khop acceptance cua C3 tren CUNG `calib_sub` -- ca hai chi thay `n`
    # block do va khong gi khac. Lua chon nay KHONG anh huong `M-199`, von chi
    # noi ve CO; no chi anh huong cac so bao cao kem.
    c = fit_B2(calib_sub, acc_calib)
    m1_test = test["m_hat_1"].to_numpy(np.float64)
    acc_b2 = m1_test >= c

    # Bien the MUC TIEU CO DINH: `c` do tu `n` block de dat `target_acceptance`
    # tren `n` block do. Do la phep do "B2 dat `c` chinh xac den dau tu `n`
    # block", va no khong bi keo theo mot C3 suy bien.
    tgt = float(acc_calib if target_acceptance is None else target_acceptance)
    c_fix = fit_B2(calib_sub, tgt)
    acc_b2fix = m1_test >= c_fix

    def _mean(mask: np.ndarray, v: np.ndarray) -> float:
        return float(v[mask].mean()) if mask.any() else float("nan")

    inf_flag = bool(fit.get("qhat_has_infinite", False))
    max_flag = bool(fit.get("qhat_at_sample_max", False))
    # `L100`: co cua `L93` KEO theo `min_blocks_at_final_qhat`, ma truong do
    # la `None` DUNG trong truong hop cua `L95` (suy bien o vong 0). Nen mot
    # lan chay vua chay `none` duoi nhan `selective` VUA o che do max-mau se
    # KHONG duoc mot co nao bat. `qhat_source` bat duoc; ghi rieng, va KHONG
    # tron vao `C3_flagged` -- dai cua `M-199` da ky voi HAI co, khong ba.
    collapsed = fit.get("qhat_source") == "degenerate_fallback_to_none"
    return {
        "n_blocks": int(calib_sub["block_id"].nunique()),
        "n_rows_calib": int(len(calib_sub)),
        # -- C3: co khai bao, do duoc TRUOC khi nhin test
        "C3_qhat_has_infinite": inf_flag,
        "C3_qhat_at_sample_max": max_flag,
        "C3_flagged": bool(inf_flag or max_flag),
        "C3_collapsed_to_none": bool(collapsed),
        "C3_flagged_incl_source": bool(inf_flag or max_flag or collapsed),
        "C3_qhat_source": fit.get("qhat_source"),
        "C3_degenerate": bool(fit.get("degenerate", False)),
        "C3_min_blocks_at_final_qhat": fit.get("min_blocks_at_final_qhat"),
        "C3_acceptance_calib": acc_calib,
        "C3_acceptance_test": float(acc_c3.mean()),
        "C3_acceptance_drift": float(abs(acc_c3.mean() - float(
            acc_calib if target_acceptance is None else target_acceptance))),
        "C3_viol_given_accept": _mean(acc_c3, viol),
        "C3_err_given_accept": _mean(acc_c3, wrong),
        # -- B2: KHONG co truong nao tuong ung. O trong nay la ket qua.
        #
        # KHONG ghi `B2_viol_given_accept`. Dai luong do se phai do bang
        # `s > qhat` -- tuc MUON `qhat` cua C3 cho B2, dung cai bay ma `A066`
        # muc 3 da tu choi. No con te hon o day: khi `qhat = +inf` (n < 29)
        # thi `s > qhat` sai voi MOI hang, nen B2 se hien ra "viol = 0.0000"
        # o n = 10 -- mot con so hoan hao sinh ra tu mot cong cu do hong.
        # Dai luong so sanh duoc cua B2 la `err|accept`, khong can `qhat`.
        "c_B2": float(c),
        "c_B2_finite": bool(np.isfinite(c)),
        "B2_flagged": False,
        "B2_has_no_coverage_claim": True,
        "B2_acceptance_test": float(acc_b2.mean()),
        "B2_err_given_accept": _mean(acc_b2, wrong),
        "c_B2_fixed": float(c_fix),
        "B2fix_target_acceptance": tgt,
        "B2fix_acceptance_test": float(acc_b2fix.mean()),
        "B2fix_acceptance_drift": float(abs(acc_b2fix.mean() - tgt)),
        "B2fix_err_given_accept": _mean(acc_b2fix, wrong),
        "anchor_err": float(wrong.mean()),
    }


def score_M199(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """`A067` muc 7: nguong 90% cho co cua C3, 100% huu han cho B2."""
    floor = CM.conformal_min_blocks(
        CM._alpha_each(ALPHA_FAMILY, len(CM.SIM_COLS), True, MULTIPLICITY))
    low = [r for r in rows if int(r["n_blocks"]) < floor]
    n = len(low)
    c3 = sum(1 for r in low if r["C3_flagged"]) / n if n else float("nan")
    b2f = sum(1 for r in low if r["c_B2_finite"]) / n if n else float("nan")
    b2g = sum(1 for r in low if r["B2_flagged"]) / n if n else float("nan")
    return {
        "validity_floor": int(floor),
        "n_draws_below_floor": int(n),
        "C3_flag_rate_below_floor": float(c3),
        "B2_finite_rate_below_floor": float(b2f),
        "B2_flag_rate_below_floor": float(b2g),
        "hit": bool(n > 0 and c3 >= 0.90 and b2f == 1.0 and b2g == 0.0),
        "label": ("C3 BIET truoc khi no khong du du lieu (`L91`/`L93`); "
                  "B2 luon tra mot `c` huu han va khong co cach nao biet"),
    }


def summarise_by_n(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Bao cao KEM, KHONG cham diem -- chua co dai da ky cho cac so nay."""
    out: Dict[str, Any] = {}
    for n in N_GRID:
        sub = [r for r in rows if int(r["n_blocks"]) == int(n)]
        if not sub:
            continue

        def _med(key: str) -> float:
            v = np.asarray([r[key] for r in sub], np.float64)
            v = v[np.isfinite(v)]
            return float(np.median(v)) if v.size else float("nan")

        def _sd(key: str) -> float:
            v = np.asarray([r[key] for r in sub], np.float64)
            v = v[np.isfinite(v)]
            return float(v.std(ddof=1)) if v.size > 1 else float("nan")

        out[str(n)] = {
            "n_draws": len(sub),
            "C3_flag_rate": float(sum(1 for r in sub if r["C3_flagged"]) / len(sub)),
            "C3_flag_rate_incl_source": float(
                sum(1 for r in sub if r["C3_flagged_incl_source"]) / len(sub)),
            "C3_collapsed_rate": float(
                sum(1 for r in sub if r["C3_collapsed_to_none"]) / len(sub)),
            "C3_median_viol": _med("C3_viol_given_accept"),
            "C3_median_err": _med("C3_err_given_accept"),
            "B2fix_median_err": _med("B2fix_err_given_accept"),
            "C3_median_acceptance_drift": _med("C3_acceptance_drift"),
            "B2fix_median_acceptance_drift": _med("B2fix_acceptance_drift"),
            # do TAN cua quyet dinh theo `n` -- cot thu ba cua `A067` muc 7
            "C3_sd_acceptance": _sd("C3_acceptance_test"),
            "B2fix_sd_acceptance": _sd("B2fix_acceptance_test"),
            "C3_sd_viol": _sd("C3_viol_given_accept"),
        }
    return out


def smallest_n_reaching_alpha(rows: Sequence[Mapping[str, Any]],
                              key: str) -> Any:
    """`n` nho nhat ma TRUNG VI cua `viol|accept` <= alpha. Bao cao kem."""
    for n in N_GRID:
        sub = [r[key] for r in rows if int(r["n_blocks"]) == int(n)]
        v = np.asarray(sub, np.float64)
        v = v[np.isfinite(v)]
        if v.size and float(np.median(v)) <= ALPHA_FAMILY:
            return int(n)
    return None


def run() -> Dict[str, Any]:
    live, _dead = TM.cells_by_role()
    rows: List[Dict[str, Any]] = []
    by_cell: Dict[str, Any] = {}
    paths: Dict[str, Any] = {}

    for cell in live:
        calib, test, path = TM.load_cell(cell)
        paths[cell] = pin(path)
        # Diem van hanh MONG MUON cua cell: acceptance ma C3 dat khi co TOAN
        # BO calib. Do la mot lua chon THIET KE (dich den), khong phai thu hoc
        # duoc tu `n` block, nen dua no vao khong lam ro ri du lieu vao `c(n)`.
        target = float(TM.fit_on_A(calib)["acceptance_on_A"])
        rng = np.random.default_rng(SEED)
        cell_rows: List[Dict[str, Any]] = []
        for n in N_GRID:
            # `n = 500` la TOAN BO tap calib: moi lan lay mau cho cung ket
            # qua, nen mot lan la du va chin lan kia chi ton may.
            draws = 1 if int(n) >= calib["block_id"].nunique() else N_DRAWS
            for _ in range(draws):
                r = recalibrate_once(subsample_blocks(calib, n, rng), test,
                                     target_acceptance=target)
                r["cell"] = cell
                cell_rows.append(r)
        rows.extend(cell_rows)
        by_cell[cell] = {
            "target_acceptance": target,
            "M_199": score_M199(cell_rows),
            "by_n": summarise_by_n(cell_rows),
            "smallest_n_C3_viol_le_alpha":
                smallest_n_reaching_alpha(cell_rows, "C3_viol_given_accept"),
            }
        del calib, test

    return {
        "schema": "dt4n.recalibration_cost.v1",
        "lesson": "23.22",
        "task": "B-2",
        "amendment": AMENDMENT,
        "config": {
            "kappa_op": KAPPA_OP, "post_variant": POST_VARIANT,
            "multiplicity": MULTIPLICITY, "alpha_family": ALPHA_FAMILY,
            "n_grid": list(N_GRID), "n_draws": N_DRAWS, "seed": SEED,
        },
        "cells": list(live),
        "M_199": score_M199(rows),
        "by_cell": by_cell,
        "pooled_by_n": summarise_by_n(rows),
        "rows": rows,
        "validity": validity_block(
            aoi_generator=AOI_V7,
            z_edges=Z_EDGES_V7,
            sla_path=SLA_MANIFEST,
            w_loss=W_LOSS,
        ),
        "provenance": {
            "script": "cert/recalibration_cost.py::run",
            "git_hash": git("git", "rev-parse", "HEAD"),
            "git_dirty": git("git", "status", "--porcelain") != "",
            "utc": datetime.now(timezone.utc).isoformat(),
            "parquet": paths,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--out", default=OUTPUT,
                    help="KHONG duoc mac dinh vao results/RAW hay "
                         "results/SUPERSEDED (`L96`)")
    args = ap.parse_args(list(argv) if argv is not None else None)
    if not args.run:
        ap.error("can --run")
    out = run()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(json_clean(out), fh, indent=1, sort_keys=True)

    m = out["M_199"]
    print("M-199: %s   san hop le = %d block" % (m["hit"], m["validity_floor"]))
    print("  duoi san: %d lan lay mau | C3 gan co %.1f%% | B2 huu han %.1f%% "
          "| B2 co %.1f%%"
          % (m["n_draws_below_floor"], 100 * m["C3_flag_rate_below_floor"],
             100 * m["B2_finite_rate_below_floor"],
             100 * m["B2_flag_rate_below_floor"]))
    print("\n%5s %7s %8s %8s %9s %9s %9s %9s %9s" % (
        "n", "co C3", "+source", "sup none", "viol C3", "err C3",
        "err B2fix", "dr C3", "dr B2fix"))
    for n, v in out["pooled_by_n"].items():
        print("%5s %6.0f%% %7.0f%% %7.0f%% %9.4f %9.4f %9.4f %9.4f %9.4f" % (
            n, 100 * v["C3_flag_rate"], 100 * v["C3_flag_rate_incl_source"],
            100 * v["C3_collapsed_rate"], v["C3_median_viol"],
            v["C3_median_err"], v["B2fix_median_err"],
            v["C3_median_acceptance_drift"],
            v["B2fix_median_acceptance_drift"]))
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

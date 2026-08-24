#!/usr/bin/env python3
"""Sinh SLA manifest NGOAI SINH cung schema voi `sla_calibration.json`.

VI SAO THIET KE NHU NAY (day la diem then chot, doc ky)
-------------------------------------------------------
Cach A (BI LOAI): them `--sla-spec` vao `cert/build_calib_set_v3.py`
    -> phai sua nhanh dieu kien TRONG builder
    -> doi chung am ("chay voi SLA cu phai ra ket qua cu") se di qua MOT
       DUONG CODE KHAC voi duong da sinh ra ket qua cu
    -> NC khong con la NC. No chi chung minh hai NHANH MOI giong nhau.

Cach B (CHON): sinh mot FILE cung schema, truyen qua `--calibration`
    -> builder KHONG DOI MOT DONG NAO
    -> doi chung am tro thanh TAM THUONG dung nghia: truyen file CU thi
       PHAI ra ket qua CU bit-exact, va no di qua DUNG duong code cu.

Nguyen tac tong quat: **sua DU LIEU, dung sua DUONG CODE, khi ban can mot
doi chung am di qua dung duong code cu.**

Ba rang buoc (amendment 23-57 muc 4)
------------------------------------
(1) KHONG sua `build_calib_set_v3.py`. Diem nap `--calibration` da co san.
(2) GIU NGUYEN moi truong khac. CHI ba truong doi: `t_delay_ms`, `t_loss`,
    `w_loss`. Mot thi nghiem doi DUNG MOT THU.
(3) XOA dau vet cua vong tu hieu chuan (`fixpoint_*`, `percentile`,
    `target_viol`). De lai thi sau nay se bi doc nham la nguong VAN noi sinh
    -- dung cai "nap nghia moi vao truong cu" da cam o amendment 23-52 muc 8.

Khoa boi: docs/phase-23/00zzt-amendment-57.md (tag amendment-57).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from typing import Any, Dict

from measurements.sla_exogenous import PRIMARY_SPEC, SLA_SPECS

LEGACY = "results/LIVE/phase-20R/sla_calibration.json"
OUT_TMPL = "results/LIVE/phase-20R/sla_manifest_exogenous_%s.json"

# Khoa o CONSTANTS.md `K06` -- KHONG duoc go tay lai o day.
# Gia tri phai bang `T_delay / T_loss` cua spec; `build()` kiem lai.
W_LOSS = 5000.0

# Bo may cua vong diem bat dong (S14) -- xoa theo TEN.
FIXPOINT_TRACES = (
    "fixpoint_history", "fixpoint_rounds", "fixpoint_converged",
    "percentile", "target_viol",
)

# `NT 50` (amendment 23-58): XOA THEO NGHIA, khong theo TEN.
# Nam truong duoi day KHONG mang tien to `fixpoint_` nhung VAN la san pham
# cua vong do. Cach kiem doc lap duy nhat: chay lai phep tinh duoi gia tri
# MOI (`sla_exogenous_S-B.json`) va so tung truong -- truong nao doi thi
# truong do LA phai sinh. Do duoc: `opt_viol_rate` cua `poisson@0.925` la
# 0.15000 trong manifest nhung 0.99131 duoi `S-B`. Sai 6.6 lan.
DERIVED_FROM_SLA = (
    "opt_viol_rate",          # dau ra cua bisection, bi EP ve `target_viol`
    "in_band",                # suy tu `opt_viol_rate`
    "cost_margin_mean_ms",    # phu thuoc `w_loss`
    "cost_margin_p10_ms",     # phu thuoc `w_loss`
    "opt_path_share",         # argmin cost -> DANH TINH duong toi uu doi theo
)

# `config` cung mang bo may fixpoint. `endogenous: false` canh
# `target_viol: 0.15` la mot file TU MAU THUAN.
CONFIG_FIXPOINT_KEYS = (
    "n_bisect", "n_fixpoint", "p_hi", "p_lo",
    "target_viol", "tol_w", "viol_band",
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(spec_id: str = PRIMARY_SPEC, legacy: str = LEGACY,
          w_loss_override: float | None = None) -> Dict[str, Any]:
    """Doc manifest NOI SINH cu, thay DUNG ba truong, xoa dau vet fixpoint.

    `w_loss_override` (amendment 23-60, cho `M-136`): dat `w_loss` DOC LAP voi
    ty gia equal-budget, GIU NGUYEN `t_delay_ms` va `t_loss`. Day la cach duy
    nhat de queo DUNG MOT THU -- `S-A`/`S-C` doi ca nguong lan ty gia nen chung
    KHONG phuc vu duoc mot phep kiem bat bien theo `w_loss`.

    Khi override duoc dung, `loss_exchange` KHONG con bang `t_loss`: dang thuc
    `w = t_delay / loss_exchange` duoc giu bang cach suy `loss_exchange` tu `w`,
    de khong co hai dinh nghia `w` mau thuan trong cung mot file.
    """
    spec = SLA_SPECS[spec_id]
    w = float(spec["t_delay_ms"]) / float(spec["t_loss"])
    if w_loss_override is not None:
        w = float(w_loss_override)
    elif spec_id == PRIMARY_SPEC and abs(w - W_LOSS) > 1e-9:
        raise ValueError(
            "w_loss suy tu spec (%r) khac `K06` (%r) -- mot trong hai sai"
            % (w, W_LOSS))

    with open(legacy, "r", encoding="utf-8") as fh:
        old = json.load(fh)

    cells = []
    for c in old["cells"]:
        new = dict(c)                       # GIU nguyen moi thu khac
        new["t_delay_ms"] = float(spec["t_delay_ms"])
        new["t_loss"] = float(spec["t_loss"])
        new["w_loss"] = w
        # `loss_exchange` GIU dang thuc `w = t_delay / loss_exchange`
        # (amendment 23-52 muc 2b) -- no khong bi nap nghia moi.
        new["loss_exchange"] = (float(spec["t_loss"]) if w_loss_override is None
                                else float(spec["t_delay_ms"]) / w)
        for k in FIXPOINT_TRACES + DERIVED_FROM_SLA:
            new.pop(k, None)
        new["sla_source"] = "exogenous_g114_%s" % spec_id
        new["sla_citation"] = spec["source"]
        cells.append(new)

    return {
        "phase": "20R",
        "script": "measurements/sla_manifest_exogenous.py",
        "prereg": "docs/phase-23/00zzt-amendment-57.md",
        "generated_date": datetime.date.today().isoformat(),
        "config": dict({k: v for k, v in old.get("config", {}).items()
                        if k not in CONFIG_FIXPOINT_KEYS}, endogenous=False,
                       sla_spec_id=spec_id, w_loss=w,
                       t_delay_ms=float(spec["t_delay_ms"]),
                       t_loss=float(spec["t_loss"]),
                       w_loss_rule="equal_budget: w = T_delay / T_loss"),
        # MOT nguon su that cho thong ke duoi SLA moi. Manifest nay DINH NGHIA
        # truc SLA; no KHONG bao cao thong ke.
        "derived_statistics": {
            "_note": ("Manifest nay DINH NGHIA truc SLA, KHONG bao cao thong "
                      "ke. Cac truong %s duoi SLA ngoai sinh nam o file duoi. "
                      "Chung DA BI XOA khoi day de khong ai doc nham gia tri "
                      "cua vong tu hieu chuan cu (`L70`, `NT 50`)."
                      % ", ".join(DERIVED_FROM_SLA)),
            "authoritative_source":
                "results/PENDING/phase-23/sla_exogenous_S-B.json",
            "removed_fields": list(DERIVED_FROM_SLA),
            "removed_config_keys": list(CONFIG_FIXPOINT_KEYS),
        },
        "inputs": {"derived_from": legacy,
                   "derived_from_sha256": sha256_file(legacy)},
        # `L68`: manifest PHAI mang truong `validity` chuan de
        # `test_no_stale_axes` kiem duoc no.
        "validity": {
            # Vai tro DO truc (amendment 23-45a): manifest nay DINH NGHIA truc
            # SLA, no khong TIEU THU truc do. Va no hoan toan doc lap voi truc
            # tuoi -- khong goi mot bo sinh `z` nao.
            "axis_role": "measures_axis",
            "instrument": {
                "source_path": "measurements/sla_manifest_exogenous.py",
                "source_sha256": sha256_file(
                    "measurements/sla_manifest_exogenous.py"),
            },
            "inputs_sha256": {legacy: sha256_file(legacy)},
            "sla_axis": {"label": "exogenous_g114_%s" % spec_id,
                         "citation": spec["source"]},
            "aoi_axis": {"label": None,
                         "note": "manifest z-independent: khong goi bo sinh z nao"},
            "sla_source": "exogenous_g114_%s" % spec_id,
            "w_loss": w,
            "endogenous": False,
        },
        "summary": {"n_cells": len(cells), "endogenous": False,
                    "n_feasible": sum(1 for c in cells if c.get("feasible"))},
        "cells": cells,
    }


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spec", default=PRIMARY_SPEC, choices=sorted(SLA_SPECS))
    p.add_argument("--out", default=None)
    p.add_argument("--w-loss", type=float, default=None,
                   help="dat w_loss DOC LAP voi ty gia equal-budget, giu nguyen "
                        "t_delay_ms/t_loss. Chi dung cho phep kiem BAT BIEN "
                        "M-136. Mac dinh None = ty gia equal-budget (K06).")
    a = p.parse_args()

    rep = build(a.spec, w_loss_override=a.w_loss)
    out = a.out or (OUT_TMPL % a.spec)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("[ok] %s  n_cells=%d  w_loss=%g  sha=%s"
          % (out, len(rep["cells"]), rep["config"]["w_loss"],
             sha256_file(out)[:16]))


if __name__ == "__main__":
    main()

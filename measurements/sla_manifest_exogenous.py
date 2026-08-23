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

# Dau vet cua vong diem bat dong (S14). Phai bi XOA khoi manifest ngoai sinh.
FIXPOINT_TRACES = (
    "fixpoint_history", "fixpoint_rounds", "fixpoint_converged",
    "percentile", "target_viol",
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(spec_id: str = PRIMARY_SPEC, legacy: str = LEGACY) -> Dict[str, Any]:
    """Doc manifest NOI SINH cu, thay DUNG ba truong, xoa dau vet fixpoint."""
    spec = SLA_SPECS[spec_id]
    w = float(spec["t_delay_ms"]) / float(spec["t_loss"])
    if spec_id == PRIMARY_SPEC and abs(w - W_LOSS) > 1e-9:
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
        new["loss_exchange"] = float(spec["t_loss"])
        for k in FIXPOINT_TRACES:
            new.pop(k, None)
        new["sla_source"] = "exogenous_g114_%s" % spec_id
        new["sla_citation"] = spec["source"]
        cells.append(new)

    return {
        "phase": "20R",
        "script": "measurements/sla_manifest_exogenous.py",
        "prereg": "docs/phase-23/00zzt-amendment-57.md",
        "generated_date": datetime.date.today().isoformat(),
        "config": dict(old.get("config", {}), endogenous=False,
                       sla_spec_id=spec_id, w_loss=w,
                       t_delay_ms=float(spec["t_delay_ms"]),
                       t_loss=float(spec["t_loss"]),
                       w_loss_rule="equal_budget: w = T_delay / T_loss"),
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
    a = p.parse_args()

    rep = build(a.spec)
    out = a.out or (OUT_TMPL % a.spec)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rep, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("[ok] %s  n_cells=%d  w_loss=%g  sha=%s"
          % (out, len(rep["cells"]), rep["config"]["w_loss"],
             sha256_file(out)[:16]))


if __name__ == "__main__":
    main()

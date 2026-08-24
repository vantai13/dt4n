#!/usr/bin/env python3
"""`G23-212a` -- DOI CHUNG AM TUNG PHAN cho Viec 3 (Lesson 23.21h).

Vi sao ton tai
--------------
`G23-212` (NC am day du) doi tai tao `eight_cell_sweep_U3_measured_v7_slaB.json`
tren CA 8 cell. Khong chay duoc: 4/8 calib parquet da mat (`L51`), va ban thn
artifact do dang bi grandfather vi provenance khai sai nguon (`L75`).

Nhung hay hoi lai `G23-212` BAO VE menh de gi:

    KHONG phai:  "so moi trung so LICH SU"
    Ma la:       "thay prepare_sla() bang NAP FILE khong doi gi khac trong
                  duong ong"

Menh de thu hai la ve TUONG DUONG DUONG CODE. No can CUNG MOT tap du lieu o
hai ve, KHONG can tap do la ban goc lich su.

Duong di: KHONG dung parquet Phase 22
-------------------------------------
Y dinh ban dau la dung 3-4 cell Phase 22 con song tren dia. DA THU va DA BO,
vi hai phat hien do duoc:

(1) Chi 3/4 file con song la BAN GOC. Doi chieu digest LICH SU -- von KHONG
    mat, chung nam trong `provenance.inputs` cua
    `results/SUPERSEDED/phase-23/eight_cell_sweep_U3_measured_v7.json`
    (git_hash 05b597f5):

        calib_set_v3.parquet               (poisson@0.925)  KHOP
        calib_set_v3_h2_0.700.parquet      (h2@0.700)       KHOP
        calib_set_v3_poisson_0.850.parquet (poisson@0.850)  KHOP
        calib_set_v3_poisson_0.700.parquet (poisson@0.700)  ★ KHAC

(2) Nhung ngay ca 3 file GOC do cung KHONG dung duoc: chung duoc dung duoi
    SLA NOI SINH (`w_loss` 1245..4722 tuy cell), nen ghep voi manifest NGOAI
    SINH (`w_loss = 5000`) lam `_objective_curve` dung o `parity fail`.
    Do duoc: poisson@0.925 -> parity 6.312e-03. Dung co che `L77`.

Nen dung bo `results/LIVE/phase-21R/calib_set_*_U0_measured_v7.parquet`: no
duoc dung O `w_loss = 5000` nen TU NHAT QUAN voi manifest S-B, va ca 8/8 file
co `parquet_sha256` ghim san trong sidecar (`G23-198`/`G23-199`).

Phu song
--------
8/8 cell -- DAY DU, khong con la "tung phan" ve du lieu. Ten `212a` duoc giu
vi no van khac `G23-212`: `G23-212` doi tai tao artifact LICH SU
`eight_cell_sweep_U3_measured_v7_slaB.json` (bat kha thi -- `L75` + `L51`),
con `212a` chi khang dinh TUONG DUONG DUONG CODE truoc/sau patch Viec 3, tren
mot tap du lieu duoc ghim digest o ca hai ve.

Cach dung
---------
    # TRUOC khi patch Viec 3
    python -m tools.g23_212a_partial_nc --capture --out results/RAW/phase-23/g23_212a_before.json
    # SAU khi patch Viec 3
    python -m tools.g23_212a_partial_nc --compare results/RAW/phase-23/g23_212a_before.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from typing import Any, Dict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"

# ★ DUNG bo calib phase-21R chu KHONG dung phase-22. Ly do do duoc:
# parquet phase-22 duoc dung duoi SLA NOI SINH (w_loss 1245..4722 tuy cell),
# nen ghep chung voi manifest NGOAI SINH (w_loss = 5000) lam `_objective_curve`
# dung o `parity fail` -- dung co che `L77` (`w_loss` la tham so SINH). Do
# duoc: poisson@0.925 -> parity 6.312e-03.
#
# Bo phase-21R `_U0_measured_v7` duoc dung O w_loss = 5000, nen no TU NHAT
# QUAN voi manifest S-B. Va moi file co `parquet_sha256` ghim san trong sidecar
# (thanh qua cua `G23-198`/`G23-199`) -- du de bao dam HAI VE dung y het mot
# tap du lieu, von la dieu kien tien quyet cua moi doi chung am.
CALIB_TEMPLATE = ("results/LIVE/phase-21R/"
                  "calib_set_{mode}_{rho:.3f}_U0_measured_v7.parquet")
AXIS = "measured_v7"
AOI_PROFILE = "U0"
ALIVE_VERIFIED = ("poisson@0.700", "poisson@0.850", "poisson@0.925",
                  "poisson@0.960", "h2@0.700", "h2@0.850", "h2@0.925",
                  "h2@0.960")

# Cot di qua PHEP THU GON tren mang 2-D -> KHONG bit-exact kha chuyen.
# Xem `G23-219`: dung sai 32*eps*sqrt(n)*|gia tri|, khong phai == 0.
REDUCED_FIELDS = ("rms_e_model", "rms_e_stale", "cov_e")
EPS = 2.220446049250313e-16
N_ROWS = 200_000
TOL_REDUCED = 32.0 * EPS * (N_ROWS ** 0.5)      # nhan voi |gia tri| khi so


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_inputs_pinned() -> Dict[str, str]:
    """Ghim digest INPUT. Neu parquet doi thi phep so hai ve VO NGHIA.

    Day la dieu kien TIEN QUYET, khong phai mot buoc kiem tra them: mot doi
    chung am tren hai tap du lieu KHAC nhau khong chung minh duoc gi.
    """
    from cert import eight_cell_sweep as E

    used = {}
    for cell in ALIVE_VERIFIED:
        spec = E.CELL_SPECS[cell]
        rel = CALIB_TEMPLATE.format(mode=spec["mode"], rho=float(spec["rho_bar"]))
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            raise SystemExit("thieu calib set: %s" % rel)
        side = path[: -len(".parquet")] + "_report.json"
        if not os.path.exists(side):
            raise SystemExit("thieu sidecar digest: %s" % side)
        with open(side, "r", encoding="utf-8") as fh:
            pinned = json.load(fh).get("parquet_sha256")
        cur = _sha256(path)
        if pinned and cur != pinned:
            raise SystemExit(
                "%s: sha256 tren dia KHAC ban ghim trong sidecar -- hai ve se "
                "khong dung cung du lieu, phep so vo nghia (L51)." % rel)
        used[cell] = cur
    return used


def capture() -> Dict[str, Any]:
    from cert import eight_cell_sweep as E

    inputs = assert_inputs_pinned()
    cells = {
        cell: E.analyze_cell(cell, spec=E.CELL_SPECS[cell], sla_artifact=MANIFEST,
                             calib_template=CALIB_TEMPLATE, axis=AXIS,
                             aoi_profile=AOI_PROFILE)
        for cell in ALIVE_VERIFIED
    }
    return {
        "schema": "dt4n.g23_212a.v1",
        "gate": "G23-212a",
        "note": ("Tuong duong DUONG CODE truoc/sau patch Viec 3, tren 8/8 cell "
                 "dung bo calib phase-21R (tu nhat quan voi manifest S-B, "
                 "digest ghim o ca hai ve). KHONG dung parquet Phase 22: chung "
                 "duoc dung duoi SLA noi sinh nen gay parity fail (L77)."),
        "manifest": MANIFEST,
        "manifest_sha256": _sha256(os.path.join(REPO, MANIFEST)),
        "cells_used": list(ALIVE_VERIFIED),
        "calib_template": CALIB_TEMPLATE,
        "input_parquet_sha256": inputs,
        "cells": cells,
    }


def _flat(o: Any, path: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(_flat(v, "%s/%s" % (path, k)))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(_flat(v, "%s[%d]" % (path, i)))
    else:
        out[path] = o
    return out


def compare(before_path: str) -> int:
    with open(before_path, "r", encoding="utf-8") as fh:
        before = json.load(fh)
    after = capture()

    if before["input_parquet_sha256"] != after["input_parquet_sha256"]:
        print("DUNG: parquet dau vao DA DOI giua hai ve -- phep so vo nghia.")
        return 2

    a, b = _flat(before["cells"]), _flat(after["cells"])
    only = sorted(set(a) ^ set(b))
    exact_bad, reduced_bad = [], []
    for k in sorted(set(a) & set(b)):
        x, y = a[k], b[k]
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) \
                and not isinstance(x, bool):
            d = abs(float(x) - float(y))
            if d == 0.0:
                continue
            if any(k.endswith("/" + f) for f in REDUCED_FIELDS):
                if d > TOL_REDUCED * max(abs(float(x)), 1.0):
                    reduced_bad.append((k, x, y, d))
            else:
                exact_bad.append((k, x, y, d))
        elif x != y:
            exact_bad.append((k, x, y, None))

    print("G23-212a  cell: %s" % ", ".join(after["cells_used"]))
    print("G23-212a  truong so sanh: %d" % len(set(a) & set(b)))
    print("G23-212a  truong chi co mot ve: %d" % len(only))
    print("G23-212a  NHOM A (bit-exact bat buoc) lech: %d" % len(exact_bad))
    print("G23-212a  NHOM B (qua thu gon, dung sai %.2e*|v|) lech: %d"
          % (TOL_REDUCED, len(reduced_bad)))
    for k, x, y, d in (exact_bad + reduced_bad)[:10]:
        print("    %-58s %r -> %r  (d=%s)" % (k, x, y, d))
    ok = not only and not exact_bad and not reduced_bad
    print("G23-212a  %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--capture", action="store_true")
    ap.add_argument("--compare", default=None)
    ap.add_argument("--out", default="results/RAW/phase-23/g23_212a_before.json")
    args = ap.parse_args()
    if args.compare:
        return compare(args.compare)
    if args.capture:
        rep = capture()
        os.makedirs(os.path.dirname(os.path.join(REPO, args.out)), exist_ok=True)
        with open(os.path.join(REPO, args.out), "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print("ve A -> %s  (%d cell)" % (args.out, len(rep["cells"])))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

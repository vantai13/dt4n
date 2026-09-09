#!/usr/bin/env python3
"""T2.6 vong 3 -- BA KIEM CO HOC. Chay TRUOC khi mo bat ky duong cong nao.

Ba kiem nay KHONG doc mot du doan vat ly nao. Chung chi tra loi: "may do co
dang hoat dong dung khong?" Neu mot trong ba do, moi so xuoi dong deu khong
doc duoc, va viec doc chung se la mot loi.

    python3 tools/t2_6b_hygiene.py
"""
from __future__ import annotations

import glob
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from cert.conformal_v2 import conformal_level          # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SWEEP = ROOT / "results/PENDING/phase-T2/sweep_r3"
OUT = SWEEP / "hygiene_r3.json"

# D-T2.6-8: bang DA KY o A-T2-3 muc (L3), voi ERRATUM A-T2-3.1 tai tau=3.
#
# tau=3 la o DUY NHAT co 200000/3000 = 66.67 khong nguyen => 67 block id moi
# seed => 335 block, SO LE => 167 calib / 168 test = 0.4985, khong the 50/50.
# Bang da ky ghi 166 (level 0.9096386); so DUNG suy tu (n, dt, tau) la 167
# (level 0.9101796). Xem 00-preregistration.md muc ERRATUM A-T2-3.1.
# Day la LAN SUA CO HOC DUY NHAT theo nhanh (b); ngan sach sua gio = 0.
EXPECTED_CALIB = {0.5: 1000, 1.0: 500, 2.0: 250, 3.0: 167,
                  5.0: 100, 10.0: 50, 20.0: 25, 28.0: 25}


def main() -> int:
    files = sorted(glob.glob(str(SWEEP / "t2_6b_r*.json")))
    if not files:
        print("khong tim thay artifact luoi chinh"); return 2

    lvl_bad, gate_rej, gate_ne, matched_worst = [], [], [], (0.0, None)
    for p in files:
        d = json.loads(pathlib.Path(p).read_text())
        for r in d["rows"]:
            tau = float(r["tau"])
            # (1) D-T2.6-8 -- muc conformal khop bang da ky
            exp = conformal_level(EXPECTED_CALIB[tau], d["alpha"])
            got = r["conformal_level_used"]
            if exp is None or got is None or abs(got - exp) > 1e-9:
                lvl_bad.append({"cell": d["cell"], "tau": tau,
                                "got": got, "expected": exp,
                                "min_calib_blocks": r["min_calib_blocks"]})
            # (2) gate -- moi o REALIZABLE va khong con not_evaluated
            g = r["realizability"]
            if g["verdict"] != "REALIZABLE":
                gate_rej.append({"cell": d["cell"], "tau": tau,
                                 "failed": g["failed"]})
            if g["not_evaluated"]:
                gate_ne.append({"cell": d["cell"], "tau": tau,
                                "not_evaluated": g["not_evaluated"]})
            # (3) D-T2.6-10 -- R(tau) day du vs khop muc
            m = r.get("level_matched")
            if m and r["ratio_measured"]:
                rel = abs(m["ratio_measured"] / r["ratio_measured"] - 1.0)
                if rel > matched_worst[0]:
                    matched_worst = (rel, {"cell": d["cell"], "tau": tau})

    res = {
        "n_artifacts": len(files),
        "D-T2.6-8_level_matches_signed_table": {
            "pass": not lvl_bad, "violations": lvl_bad[:10],
            "n_violations": len(lvl_bad),
            "note": "FAIL => loi CO HOC (chia calib/test lech ti le). Dung ngay.",
        },
        "gate": {
            "pass": (not gate_rej) and (not gate_ne),
            "n_rejected": len(gate_rej), "rejected": gate_rej[:10],
            "n_still_not_evaluated": len(gate_ne), "not_evaluated": gate_ne[:10],
            "note": "not_evaluated PHAI rong: A-T2-3 (d3) doi hoi gate nhan du 9 tham so.",
        },
        "D-T2.6-10_level_matching_cancels_in_the_ratio": {
            "max_rel_diff": matched_worst[0], "driver": matched_worst[1],
            "threshold": 0.01,
            "pass": matched_worst[0] < 0.01,
            "note": ("FAIL KHONG phai loi: no co nghia gia thuyet 'muc triet "
                     "tieu trong ti so' SAI => phai bao cao va chuyen MOI phep "
                     "doc R(tau) sang ban khop muc."),
        },
    }
    ok = (res["D-T2.6-8_level_matches_signed_table"]["pass"]
          and res["gate"]["pass"])
    res["may_open_outcome_curves"] = bool(ok)
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")

    print(json.dumps(res, indent=1, sort_keys=True))
    print("\n>>> %s" % ("DUOC PHEP mo duong cong ket qua." if ok else
                        "KHONG duoc mo duong cong. Sua kiem co hoc truoc."))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

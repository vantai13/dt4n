"""20R2.4 E2 -- bang `em/A`, tieu chi DOC DUOC cua truc tuoi.

`em/A` la ti so giua SAN MO HINH (`em = rms_e_model`, sai so twin khong bao gio
triet tieu duoc) va BIEN DO (`A`). No tra loi: duong cong theo tuoi ma toi sap
ve co bi san mo hinh chi phoi khong?

MAU SO KHONG TUY TIEN. Dat `em = 0` trong luat RMS thi `A` va `c` TRIET TIEU
CHINH XAC, con lai mot duong tau THUAN giong nhau o moi o -- do la GIOI HAN CUA
CHINH CONG THUC, khong phai mot chuan hoa do nguoi chon. Voi z_rep = [0.077,
0.425], span cua no = 0.3391513597629414.

HAI TRUC, KHONG MOT  [RT2-4 thieu mot truc]
===========================================
Phan quyet phu thuoc `sigma`, KHONG chi phu thuoc `mode`:
    h2@0.700, a = 0.9 -> span/pure = 0.9375  DOC DUOC
    h2@0.700, a = 0.5 -> span/pure = 1.5691  BI CHI PHOI
CUNG o, khac `a`, khac ket luan. Nen bang nay co 20 DONG (10 o x 2 a), khong
phai 10. Lap bang theo `mode` roi ket luan cho ca o la lap lai dung loi T2.

DANH DAU, KHONG LOAI  [gate 4-4]
================================
O co `em/A` cao duoc DANH DAU TRUOC, KHONG bi loai. Loai chung la chon du lieu
theo mot tinh chat lien quan toi ket qua => selection bias. Danh dau truoc thi
khi h2@0.960 cho duong cong phang, do la dieu DA DU DOAN (span/pure = 2.19),
khong phai mot "phat hien".

NGUON SO -- va vi sao chung la KE THUA
======================================
`em` va `A` chua do duoc tren dieu kien 20R2 (chien dich chua chay). Bang nay
dung so cua T2 (results/PENDING/phase-T2/rt24_bias_decomposition.json), do tren
truc SLA self_calibrated va luoi z legacy. 20R2 chay tren exogenous SLA.
=> Moi hang deu mang `source` = "inherited_T2" hoac "MISSING". KHONG hang nao
   duoc ghi la do cua thi nghiem nay cho toi khi 20R2.5 chay xong.
Day la cung ky luat voi ngan sach CPU: mot hang so khong duoc ke thua qua ranh
gioi dieu kien ma khong do lai.

Chay:
    python -m tools.20r2_4_em_over_a --out results/PENDING/phase-20R2/em_over_a.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import pathlib

from twin import cost_v2 as C

REPO = pathlib.Path(__file__).resolve().parents[1]
CALIB_REL = "results/LIVE/phase-20R/sla_calibration.json"
T2_REL = "results/PENDING/phase-T2/rt24_bias_decomposition.json"

A_VALUES = [0.5, 0.9]

# Nguong DANH DAU (khong phai nguong LOAI). Lay tu quan sat cua T2:
# span/pure ~ 1.0 la "khop duong tau thuan"; cang xa 1 cang bi chi phoi.
BAND_READABLE = 1.25     # span/pure <= 1.25 -> doc duoc
BAND_DOMINATED = 1.75    # span/pure >= 1.75 -> bi chi phoi


def _flag(span_ratio: float | None, degenerate: bool) -> str:
    if degenerate:
        return "SUY_BIEN"
    if span_ratio is None:
        return "CHUA_BIET"
    if span_ratio <= BAND_READABLE:
        return "DOC_DUOC"
    if span_ratio >= BAND_DOMINATED:
        return "BI_CHI_PHOI"
    return "TRUNG_GIAN"


def build() -> dict:
    with open(REPO / CALIB_REL, encoding="utf-8") as fh:
        calib = json.load(fh)
    with open(REPO / T2_REL, encoding="utf-8") as fh:
        t2 = json.load(fh)

    t2_by_key = {(c["cell"], float(c["a"])): c for c in t2["cells"]}

    rows = []
    for c in calib["cells"]:
        if not c.get("feasible"):
            continue
        key_cell = "%s@%.3f" % (c["mode"], c["rho_bar"])
        for a in A_VALUES:
            src = t2_by_key.get((key_cell, a))
            row = {
                "cell": key_cell,
                "mode": c["mode"],
                "rho_bar": float(c["rho_bar"]),
                "role": c.get("role"),
                "a": a,
                "sigma": a * float(C.sigma_max_regime(c["mode"], c["rho_bar"])),
            }
            if src is None:
                row.update({
                    "source": "MISSING",
                    "em_bar": None, "A_bar": None, "em_over_A": None,
                    "span_ratio_to_pure": None, "degenerate": None,
                    "flag": "CHUA_BIET",
                    "note": ("T2 khong do o nay -- KHONG duoc suy tu o khac. "
                             "Phai do trong pilot hoac chien dich."),
                })
            else:
                row.update({
                    "source": "inherited_T2",
                    "em_bar": src["em_bar"],
                    "A_bar": src["A_bar"],
                    "em_over_A": src["em_over_A"],
                    "span_ratio_to_pure": src["span_ratio_to_pure"],
                    "drift_contribution": src["drift_contribution"],
                    "degenerate": src["degenerate"],
                    "flag": _flag(src["span_ratio_to_pure"], src["degenerate"]),
                })
            rows.append(row)

    rows.sort(key=lambda r: (r["em_over_A"] is None, r["em_over_A"] or 0.0))

    n_missing = sum(1 for r in rows if r["source"] == "MISSING")
    n_degen = sum(1 for r in rows if r.get("degenerate"))
    by_flag: dict = {}
    for r in rows:
        by_flag[r["flag"]] = by_flag.get(r["flag"], 0) + 1

    return {
        "schema": "dt4n.em_over_a.v1",
        "validity": _validity(),
        "generated_by": "tools/20r2_4_em_over_a.py",
        "question": ("Duong cong theo tuoi cua o nay co bi SAN MO HINH (em) "
                     "chi phoi khong?"),
        "denominator": {
            "pure_tau_span": t2["pure_tau_span"],
            "z_rep": t2["z_rep"],
            "why_not_arbitrary": (
                "Dat em = 0 trong luat RMS thi A va c TRIET TIEU CHINH XAC, "
                "con lai mot duong tau thuan giong nhau o moi o. Do la gioi han "
                "cua CHINH cong thuc, khong phai mot chuan hoa do nguoi chon."),
        },
        "policy": {
            "mark_do_not_exclude": (
                "O co em/A cao duoc DANH DAU, KHONG bi loai. Loai chung la chon "
                "du lieu theo tinh chat lien quan toi ket qua => selection bias."),
            "bands": {"DOC_DUOC": "<= %g" % BAND_READABLE,
                      "BI_CHI_PHOI": ">= %g" % BAND_DOMINATED,
                      "TRUNG_GIAN": "giua hai nguong"},
            "two_axes": (
                "Phan quyet phu thuoc sigma (a), KHONG chi mode. Bang co 20 dong "
                "= 10 o x 2 a. Lap theo mode roi ket luan cho ca o la lap lai "
                "loi RT2-4."),
        },
        "provenance_warning": (
            "em/A o day KE THUA tu T2 (truc SLA self_calibrated, luoi z legacy). "
            "20R2 chay tren exogenous SLA. Day la UOC TINH KE THUA, khong phai "
            "phep do cua thi nghiem nay. Do lai sau 20R2.5."),
        "correlation_T2": t2["correlation_em_over_A_vs_span_ratio"],
        "summary": {
            "n_rows": len(rows),
            "n_expected": 20,
            "n_missing": n_missing,
            "n_degenerate": n_degen,
            "by_flag": dict(sorted(by_flag.items())),
        },
        "rows": rows,
    }


def _check(doc: dict) -> None:
    s = doc["summary"]
    if s["n_rows"] != s["n_expected"]:
        raise SystemExit(
            "bang co %d dong, doi %d (10 o kha thi x 2 a). Lap bang theo `mode` "
            "roi ket luan cho ca o la lap lai loi RT2-4."
            % (s["n_rows"], s["n_expected"]))



def _validity() -> dict:
    """Artifact nay CHO gi de duoc promote khoi PENDING/.

    PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE. Khai chinh xac truc
    nao chua duyet, neu khong artifact se nam quen o day.
    """
    return {
        "schema": "dt4n.validity.v1",
        "axis_role": "em_over_a_table",
        "pending_on": ["aoi_axis", "sla_axis"],
        "aoi_axis": {
            "label": "UNREGISTERED",
            "z_grid_s": [],
            "note": "em/A KE THUA tu T2 (SLA self_calibrated, luoi z legacy). 20R2 chay exogenous SLA. Day la UOC TINH, khong phai phep do cua thi nghiem nay; do lai sau 20R2.5.",
        },
        "sla_axis": {
            "label": "UNREGISTERED",
            "match_method": "none",
            "note": "cho A5 (prereg muc 3) duoc KY; chua chay tren mot truc SLA nao",
        },
        "omega": None,
        "w_loss": None,
        "note": "em/A KE THUA tu T2 (SLA self_calibrated, luoi z legacy). 20R2 chay exogenous SLA. Day la UOC TINH, khong phai phep do cua thi nghiem nay; do lai sau 20R2.5.",
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    doc = build()
    _check(doc)
    doc["generated_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=True)
        fh.write("\n")

    print("=== 20R2.4 E2: bang em/A (%d dong = 10 o x 2 a) ==="
          % doc["summary"]["n_rows"])
    print("mau so: span duong tau THUAN = %.10f  (z_rep = %s)"
          % (doc["denominator"]["pure_tau_span"], doc["denominator"]["z_rep"]))
    print("\n%-16s %-4s %-6s %-11s %-11s %-9s %-10s %s"
          % ("cell", "a", "role", "em_bar", "A_bar", "em/A", "span/pure", "DANH DAU"))
    for r in doc["rows"]:
        if r["source"] == "MISSING":
            print("%-16s %-4.1f %-6s %-11s %-11s %-9s %-10s %s"
                  % (r["cell"], r["a"], r["role"], "-", "-", "-", "-", r["flag"]))
        else:
            print("%-16s %-4.1f %-6s %-11.5g %-11.5g %-9.4f %-10.4f %s"
                  % (r["cell"], r["a"], r["role"], r["em_bar"], r["A_bar"],
                     r["em_over_A"], r["span_ratio_to_pure"], r["flag"]))
    print("\nphan bo: %s" % doc["summary"]["by_flag"])
    print("thieu   : %d dong (T2 khong do)" % doc["summary"]["n_missing"])
    print("\n-> %s" % os.path.relpath(args.out, REPO))


if __name__ == "__main__":
    main()

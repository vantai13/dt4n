#!/usr/bin/env python3
"""Lesson 23.24b -- kiem toan CHIEU DO cua `rho` tren chien dich AoI 23.8.

Tien dang ky: docs/phase-23/A076-amendment-76.md
KHONG do moi. Doc du lieu da co.

BA NHIEM VU:
    R2  `rho` tu SO SACH BO SINH TAI (`meta_*.json`, TRACKED trong git)
        -> nhac cu DOC LAP hoan toan voi `/proc/net/dev`
    R3  `rho` tu BO DEM NHAN (`rho_measured_*.csv`, local, gitignore)
        -> nhac cu DANG BI NGHI NGO
    R4  doi chieu R2 vs R3 -> phan quyet CLEAN / BROKEN tung link

VI SAO KHONG DUNG PHEP KIEM BAO TOAN LUU LUONG (`A076` N3):
    `mininet/traffic_v7.py::LOAD_CHANNELS` nap moi link bang MOT luong
    MOT-CHANG rieng (`uA`: hsrc->hA; `ac`: hA->hC). Byte vao `uA` KHONG chay
    tiep sang `ac`. Nen `tp(uA) != tp(ac) + tp(ad)` va bao toan KHONG dung o
    testbed nay. Do chinh la `S13` o dang vat ly: testbed hien tai la
    `omega = 0` THEO THIET KE. Mot doi chung SAI con te hon khong co doi chung.

Chay:
    python measurements/link_rho_audit.py \\
        --campaign results/RAW/phase-23/aoi_v7_campaign \\
        --out results/LIVE/phase-23/link_rho_audit.json
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

from twin import link_direction as LD
from twin import topology_v7 as T7

# --- HANG SO KHOA o `A076` muc 3 / N5. KHONG phai co dong lenh. -----------
# Neu la `--zero-eps` thi se thu 1e-6, 1e-4, 1e-3 cho toi khi ket luan doi.
# Do la p-hacking va no KHONG de lai dau vet trong git. La hang so module thi
# viec doi BAT BUOC phai sua code + commit + amendment.
OVERHEAD_BYTES = 42        # Eth 14 + IPv4 20 + UDP 8. `/proc/net/dev` KHONG
                           # dem FCS(4) va preamble+IFG(20). Do nhay: `A076` N4.
ZERO_RHO_EPS = 1e-9        # `rho <=` nguong nay thi tinh la KHONG
BROKEN_ZERO_SHARE = 0.50   # `>=` nua so mau bang 0 -> hong chieu
CLEAN_ZERO_SHARE = 0.05    # `<=` 5% mau bang 0 -> binh thuong
AGREE_LO, AGREE_HI = 0.85, 1.15    # dai dong thuan hai nhac cu (`M-239`)

RUN_KEY = re.compile(r"(clean|prod)_rho([0-9.]+)_rep([0-9]+)")
LINKS = tuple(T7.LINK_NAMES)


# --------------------------------------------------------------- tien ich
def run_key(path: str) -> str:
    m = RUN_KEY.search(os.path.basename(path))
    return m.group(0) if m else os.path.basename(path)


def parse_key(key: str) -> tuple[str, float, int]:
    m = RUN_KEY.search(key)
    if m is None:
        raise ValueError("ten file khong dung khuon chien dich: %r" % key)
    return m.group(1), float(m.group(2)), int(m.group(3))


def cell_of(path: str) -> str:
    mode, rho, _rep = parse_key(run_key(path))
    return "%s@%.3f" % (mode, rho)


# ------------------------------------------------------------------- R2
def generator_rho(meta_paths: list[str]) -> dict:
    """R2 -- `rho` suy tu SO SACH cua bo sinh tai.

    `flow_engine[link].packets_sent` la so goi bo sinh TU DEM da ban ra. No
    KHONG doc `/proc/net/dev` va KHONG biet `canonical_link_key` ton tai, nen
    day la nhac cu DOC LAP -- dieu kien de no lam doi chung duoc.

    NHAN: `A076` muc 2 -- ket qua nay DA duoc tinh TRUOC khi ky amendment,
    nen no la [MO TA], KHONG duoc cham diem nhu mot du doan.
    """
    per_link = defaultdict(list)
    per_cell = defaultdict(list)
    ratio = defaultdict(list)

    for path in sorted(meta_paths):
        with open(path, encoding="utf-8") as fh:
            meta = json.load(fh)
        dur = float(meta["duration_s"])
        payload = float(meta["payload_bytes"])
        cell = cell_of(path)
        for link, fe in meta.get("flow_engine", {}).items():
            pk = fe.get("packets_sent")
            if pk is None:
                continue
            mbps = float(pk) * (payload + OVERHEAD_BYTES) * 8.0 / dur / 1e6
            rho = mbps / float(fe["cap_mbps"])
            per_link[link].append(rho)
            per_cell[(cell, link)].append(rho)
            tgt = fe.get("rho_target")
            if tgt:
                ratio[link].append(rho / float(tgt))

    out: dict = {"per_link": {}, "per_cell": {},
                 "label": "[MO TA -- DA DO TRUOC KHI KY] A076 muc 2"}
    for link in LINKS:
        v = np.asarray(per_link.get(link, []), dtype=float)
        r = np.asarray(ratio.get(link, []), dtype=float)
        out["per_link"][link] = {
            "n_runs": int(v.size),
            "rho_gen_mean": float(v.mean()) if v.size else None,
            "rho_gen_sd": float(v.std(ddof=1)) if v.size > 1 else None,
            "rho_gen_over_target": float(r.mean()) if r.size else None,
        }
    for (cell, link), v in sorted(per_cell.items()):
        a = np.asarray(v, dtype=float)
        out["per_cell"].setdefault(cell, {})[link] = {
            "n_runs": int(a.size),
            "rho_gen_mean": float(a.mean()),
            "rho_gen_sd": float(a.std(ddof=1)) if a.size > 1 else None,
        }
    return out


# ------------------------------------------------------------------- R3
def measured_rho(csv_paths: list[str]) -> dict:
    """R3 -- `rho` tu BO DEM NHAN (`rho_measured_*.csv`, do `RhoLogger` ghi)."""
    per_link = defaultdict(list)
    per_cell = defaultdict(list)
    n_files = 0

    for path in sorted(csv_paths):
        n_files += 1
        cell = cell_of(path)
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                link = row["link"]
                rho = float(row["rho"])
                per_link[link].append(rho)
                per_cell[(cell, link)].append(rho)

    out: dict = {"n_files": n_files, "per_link": {}, "per_cell": {}}
    for link in LINKS:
        v = np.asarray(per_link.get(link, []), dtype=float)
        if v.size == 0:
            out["per_link"][link] = {"n_samples": 0, "rho_mean": None,
                                     "rho_p50": None, "rho_sd": None,
                                     "zero_share": None}
            continue
        out["per_link"][link] = {
            "n_samples": int(v.size),
            "rho_mean": float(v.mean()),
            "rho_p50": float(np.median(v)),
            "rho_sd": float(v.std(ddof=1)),
            "zero_share": float(np.mean(v <= ZERO_RHO_EPS)),
        }
    for (cell, link), v in sorted(per_cell.items()):
        a = np.asarray(v, dtype=float)
        out["per_cell"].setdefault(cell, {})[link] = {
            "n_samples": int(a.size),
            "rho_mean": float(a.mean()),
            "zero_share": float(np.mean(a <= ZERO_RHO_EPS)),
        }
    return out


# ------------------------------------------------------------------- R4
def adjudicate(gen: dict, meas: dict) -> dict:
    """R4 -- phan quyet tung link + tinh dong thuan hai nhac cu."""
    per_link: dict[str, str] = {}
    broken: list[str] = []
    ambiguous: list[str] = []

    for link in LINKS:
        zs = meas["per_link"][link]["zero_share"]
        if zs is None:
            per_link[link] = "NO_DATA"
            continue
        if zs >= BROKEN_ZERO_SHARE:
            per_link[link] = "BROKEN_DIRECTION"
            broken.append(link)
        elif zs <= CLEAN_ZERO_SHARE:
            per_link[link] = "CLEAN"
        else:
            per_link[link] = "AMBIGUOUS"
            ambiguous.append(link)

    agree: dict[str, float | None] = {}
    for link in LINKS:
        g = gen["per_link"][link]["rho_gen_mean"]
        m = meas["per_link"][link]["rho_mean"]
        agree[link] = None if (not g or m is None) else float(m / g)

    pairs_g: list[float] = []
    pairs_m: list[float] = []
    for cell, links in sorted(meas["per_cell"].items()):
        for link, mv in sorted(links.items()):
            gv = gen["per_cell"].get(cell, {}).get(link)
            if gv is None:
                continue
            pairs_g.append(gv["rho_gen_mean"])
            pairs_m.append(mv["rho_mean"])

    corr = (float(np.corrcoef(pairs_g, pairs_m)[0, 1])
            if len(pairs_g) >= 3 else None)

    n_clean = sum(1 for l in LINKS if per_link.get(l) == "CLEAN")
    if n_clean == len(LINKS):
        overall = "CSV_CLEAN"
    elif broken:
        overall = "CSV_BROKEN"
    else:
        overall = "CSV_PARTIAL"

    in_band = [l for l in LINKS
               if agree[l] is not None and AGREE_LO <= agree[l] <= AGREE_HI]

    return {
        "per_link_verdict": per_link,
        "links_broken": sorted(broken),
        "links_ambiguous": sorted(ambiguous),
        "n_clean": n_clean,
        "overall": overall,
        "agreement_csv_over_generator": agree,
        "n_links_agreement_in_band": len(in_band),
        "corr_csv_vs_generator_over_cells": corr,
        "n_cell_link_pairs": len(pairs_g),
        # Dau ngon tay cua `L30` tren nhanh DITTO -- de doi chieu, KHONG phai
        # ket qua cua lesson nay. Nhanh Ditto da biet la hong tu truoc.
        "alphabetical_side_a_correct": {
            l: LD.alphabetical_side_a_is_correct(l) for l in LINKS},
    }


# ----------------------------------------------------------- provenance
def _git(*args: str) -> str:
    try:
        return subprocess.run(args, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return ""


def _provenance(script: str, argv_extra: dict) -> dict:
    return {
        "script": script,
        "git_hash": _git("git", "rev-parse", "HEAD"),
        "git_dirty": bool(_git("git", "status", "--porcelain")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "argv": argv_extra,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv-glob", default="rho_measured_*.csv",
                    help="doi duoc de chay PC-24b-1 tren du lieu gia lap")
    a = ap.parse_args()

    metas = sorted(glob.glob(os.path.join(a.campaign, "**", "meta_*.json"),
                             recursive=True))
    csvs = sorted(glob.glob(os.path.join(a.campaign, "**", a.csv_glob),
                            recursive=True))
    if not metas:
        raise SystemExit("khong tim thay meta_*.json trong %s" % a.campaign)

    gen = generator_rho(metas)
    if csvs:
        meas = measured_rho(csvs)
        adj = adjudicate(gen, meas)
        status = "MEASUREMENT_ESTIMATE"
    else:
        # `L78`: fail loud, khong fail quiet. Script chay duoc tren clone sach
        # (de CI xanh) nhung artifact TU KHAI la no chua du.
        meas = {"n_files": 0, "per_link": {}, "per_cell": {}}
        adj = {"overall": "CSV_MISSING",
               "note": ("Khong tim thay rho_measured_*.csv. Chung bi gitignore "
                        "(.gitignore:174) nen KHONG co tren ban clone sach. "
                        "Chay lesson nay tren MAY TAC GIA. Xem G23-74 / L87.")}
        status = "INCOMPLETE_NO_CSV"

    import measurements.link_rho_audit as _self
    from measurements import validity as V

    report = {
        "schema": "dt4n.link.rho_audit.v1",
        "lesson": "23.24b",
        "prereg": "docs/phase-23/A076-amendment-76.md",
        "status": status,
        "locked_constants": {
            "OVERHEAD_BYTES": OVERHEAD_BYTES,
            "ZERO_RHO_EPS": ZERO_RHO_EPS,
            "BROKEN_ZERO_SHARE": BROKEN_ZERO_SHARE,
            "CLEAN_ZERO_SHARE": CLEAN_ZERO_SHARE,
            "AGREE_BAND": [AGREE_LO, AGREE_HI],
        },
        "n_meta_files": len(metas),
        "n_csv_files": len(csvs),
        "R2_generator_rho": gen,
        "R3_measured_rho": meas,
        "R4_adjudication": adj,
        "provenance": _provenance("measurements/link_rho_audit.py",
                                  {"campaign": a.campaign, "out": a.out,
                                   "csv_glob": a.csv_glob}),
        "validity": V.measurement_validity_block(
            instrument_module=_self,
            inputs=metas[:1] + csvs[:1],
            note=("Artifact DO chinh nhac cu do rho (vai tro MEASURES). No "
                  "khong tieu thu truc AoI va khong tieu thu truc SLA, nen "
                  "khong phai cho `approved_for_live`. Xem A076 muc 5."),
        ),
    }

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("[link_rho_audit] %s -> %s" % (adj.get("overall"), a.out))


if __name__ == "__main__":
    main()

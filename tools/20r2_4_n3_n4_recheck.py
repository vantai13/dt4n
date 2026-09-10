"""20R2.4 E5 -- kiem lai N3/N4 tren luoi 20R2. KHONG ke thua gia dinh.

HAI GIA DINH DUOC BAN GIAO TU T2, CA HAI DEU DA VO MOT PHAN
===========================================================
N3  Luat RMS AR(1) mat hieu luc o sigma lon.
    gate: `ar1_rms_total_fit_within_2pct` = moi hang co
          ar1_fit.max_rel_err_vs_measured < 0.02   (cert/tau_sweep.py:394)
    T2 ghi: hong o poisson@0.850.
    DO LAI 2026-09-10 tren 18 artifact sweep_r3: 14 PASS / 4 FAIL, va 4 FAIL
    do trai tren BA o (poisson@0.850 x2, poisson@0.700, h2@0.850), khong phai
    mot. => pham vi hong RONG HON cau chu cua N3.

N4  Gia dinh "A, c, em doc lap voi tau" -- NEN CUA luat RMS -- khong vung.
    tieu chi: ratio_span_over_spread (bien thien GIUA cac tau so voi bien
    thien TRONG cung mot tau). Khong thu nguyen, tu hieu chuan, khong can ky
    nguong.
    T2 do: 7 PASS / 11 FAIL tren 18 arm, chu yeu o `em`.

VI SAO KHONG DUOC CHEP KET QUA T2
=================================
T2 do tren LUOI CUA T2: truc SLA self_calibrated, luoi z legacy, luoi tau cua
T2. 20R2 chay tren exogenous SLA. Mot gia dinh vo 11/18 o dieu kien A co the
vo 3/18 hoac 17/18 o dieu kien B -- va khong ai biet cho toi khi do.

=> Bang ma tool nay sinh LA MOT DONG GOP, khong phai mot thu tuc: "gia dinh X
   vo o bao nhieu phan tram mien, va vo theo huong nao" la mot ket qua trich
   dan duoc.

TRANG THAI
==========
Tool nay do duoc BASELINE T2 ngay bay gio (de ghim moc so sanh). Phan 20R2
CHUA do duoc: no can `cert/tau_sweep.py` chay tren luoi 20R2, tuc mot chien
dich thu hai (~53 phut theo run_log cua sweep_r3). Chay sau 20R2.5.

    python -m tools.20r2_4_n3_n4_recheck --out results/PENDING/phase-20R2/n3_n4_baseline.json
    python -m tools.20r2_4_n3_n4_recheck --out ... --sweep-dir <thu muc 20R2>
"""
from __future__ import annotations

import argparse
import collections
import datetime as _dt
import glob
import json
import os
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
T2_SWEEP_REL = "results/PENDING/phase-T2/sweep_r3"
T2_ADJ_REL = "results/PENDING/phase-T2/sweep_r3/adjudication_r3.json"

N3_GATE = "ar1_rms_total_fit_within_2pct"
N3_ROW_FIELD = "max_rel_err_vs_measured"
N3_THRESHOLD = 0.02

# Moc T2, GHIM de so sanh. Neu do lai ma lech, tool bao -- vi mot moc troi
# lam moi so sanh sau do vo nghia.
T2_BASELINE = {"n3_pass": 14, "n3_fail": 4, "n4_pass": 7, "n4_fail": 11}


# Arm CHINH cua T2.6b. Thu muc con chua ca `legacy_*.json` (doi chung tren
# truc cu) va `adjudication_*.json`. Gop chung vao se cho 26 arm thay vi 18 --
# do la mot MAU KHAC, va moc 14/4 se khong con doi chieu duoc.
PRIMARY_ARM_GLOB = "t2_6b_*.json"


def scan_n3(sweep_dir: pathlib.Path, pattern: str = PRIMARY_ARM_GLOB) -> dict:
    """Doc gate N3 tu tung artifact tau_sweep (CHI arm chinh)."""
    per_arm, by_cell = [], collections.Counter()
    for f in sorted(glob.glob(str(sweep_dir / pattern))):
        try:
            d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        gates = d.get("gates")
        if not isinstance(gates, dict) or N3_GATE not in gates:
            continue
        ok = bool(gates[N3_GATE])
        worst = None
        for r in d.get("rows", []):
            v = r.get("ar1_fit", {}).get(N3_ROW_FIELD)
            if v is not None:
                worst = v if worst is None else max(worst, float(v))
        per_arm.append({
            "artifact": os.path.relpath(f, REPO),
            "cell": d.get("cell"),
            "passes": ok,
            "worst_max_rel_err_vs_measured": worst,
        })
        if not ok:
            by_cell[d.get("cell")] += 1
    return {
        "gate": N3_GATE,
        "arm_glob": pattern,
        "criterion": "moi hang: ar1_fit.%s < %g" % (N3_ROW_FIELD, N3_THRESHOLD),
        "n_arms": len(per_arm),
        "n_pass": sum(1 for a in per_arm if a["passes"]),
        "n_fail": sum(1 for a in per_arm if not a["passes"]),
        "fail_by_cell": dict(sorted(by_cell.items())),
        "per_arm": per_arm,
    }


def scan_n4(adjudication: pathlib.Path) -> dict:
    """Doc D-T2.6-4: gia dinh A, c, em doc lap voi tau."""
    d = json.loads(adjudication.read_text(encoding="utf-8"))
    v = d["verdicts"]["D-T2.6-4"]
    by_param = collections.Counter()
    by_cell = collections.Counter()
    for cell, arms in v.get("per_cell", {}).items():
        for a_key, params in arms.items():
            for p, res in params.items():
                if isinstance(res, dict) and res.get("passes") is False:
                    by_param[p] += 1
                    by_cell[cell] += 1
    return {
        "prediction": "D-T2.6-4",
        "assumption": "A, c, em doc lap voi tau (NEN cua luat RMS)",
        "criterion": ("ratio_span_over_spread: bien thien GIUA cac tau so voi "
                      "bien thien TRONG cung mot tau. Khong thu nguyen, tu hieu "
                      "chuan -- khong can ky nguong."),
        "n_pass": v["n_pass"],
        "n_fail": v["n_fail"],
        "n_total": v["n_pass"] + v["n_fail"],
        "fail_by_parameter": dict(sorted(by_param.items())),
        "fail_by_cell": dict(sorted(by_cell.items())),
    }


def build(sweep_dir: pathlib.Path, adjudication: pathlib.Path,
          label: str) -> dict:
    n3 = scan_n3(sweep_dir)
    n3_all = scan_n3(sweep_dir, "*.json")
    n4 = scan_n4(adjudication)
    drift = []
    if label == "T2_baseline":
        for key, got in (("n3_pass", n3["n_pass"]), ("n3_fail", n3["n_fail"]),
                         ("n4_pass", n4["n_pass"]), ("n4_fail", n4["n_fail"])):
            if got != T2_BASELINE[key]:
                drift.append("%s: ghim %d, do duoc %d"
                             % (key, T2_BASELINE[key], got))
    return {
        "schema": "dt4n.n3_n4_recheck.v1",
        "validity": _validity(),
        "generated_by": "tools/20r2_4_n3_n4_recheck.py",
        "label": label,
        "source_sweep_dir": os.path.relpath(sweep_dir, REPO),
        "N3": n3,
        "N3_including_controls": {
            "arm_glob": "*.json",
            "n_arms": n3_all["n_arms"],
            "n_pass": n3_all["n_pass"],
            "n_fail": n3_all["n_fail"],
            "note": ("gop ca legacy_*.json (doi chung truc cu). Ghi ra de minh "
                     "bach, KHONG dung de doi chieu moc: moc 14/4 la cua arm "
                     "CHINH. Hai tap khac nhau thi khong so duoc."),
        },
        "N4": n4,
        "T2_baseline_pinned": T2_BASELINE,
        "baseline_drift": drift,
        "n3_scope_correction": (
            "N4 cua handoff viet 'chu yeu o poisson@0.850'. Do lai: %d FAIL "
            "trai tren %d o khac nhau (%s). Pham vi hong RONG HON cau chu."
            % (n3["n_fail"], len(n3["fail_by_cell"]),
               ", ".join(sorted(k for k in n3["fail_by_cell"] if k)))),
        "status_20r2": {
            "measured": False,
            "why": ("can cert/tau_sweep.py chay tren luoi 20R2 (exogenous SLA) "
                    "-- mot chien dich thu hai, ~53 phut theo run_log sweep_r3. "
                    "Chay SAU 20R2.5."),
            "must_not": ("KHONG duoc chep ket qua T2 sang 20R2. Mot gia dinh vo "
                         "11/18 o dieu kien A co the vo 3/18 hoac 17/18 o dieu "
                         "kien B."),
        },
    }



def _validity() -> dict:
    """Artifact nay CHO gi de duoc promote khoi PENDING/.

    PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE. Khai chinh xac truc
    nao chua duyet, neu khong artifact se nam quen o day.
    """
    return {
        "schema": "dt4n.validity.v1",
        "axis_role": "n3_n4_baseline",
        "pending_on": ["aoi_axis", "sla_axis"],
        "aoi_axis": {
            "label": "UNREGISTERED",
            "z_grid_s": [],
            "note": "moc T2, KHONG phai ket qua 20R2. Phan 20R2 can tau_sweep chay tren luoi 20R2 -- chien dich thu hai, sau 20R2.5.",
        },
        "sla_axis": {
            "label": "UNREGISTERED",
            "match_method": "none",
            "note": "cho A5 (prereg muc 3) duoc KY; chua chay tren mot truc SLA nao",
        },
        "omega": None,
        "w_loss": None,
        "note": "moc T2, KHONG phai ket qua 20R2. Phan 20R2 can tau_sweep chay tren luoi 20R2 -- chien dich thu hai, sau 20R2.5.",
    }

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sweep-dir", default=None)
    ap.add_argument("--adjudication", default=None)
    args = ap.parse_args()

    sweep = pathlib.Path(args.sweep_dir) if args.sweep_dir else REPO / T2_SWEEP_REL
    adj = pathlib.Path(args.adjudication) if args.adjudication else REPO / T2_ADJ_REL
    label = "T2_baseline" if args.sweep_dir is None else "20R2"

    doc = build(sweep, adj, label)
    doc["generated_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=True)
        fh.write("\n")

    n3, n4 = doc["N3"], doc["N4"]
    print("=== 20R2.4 E5: kiem lai N3/N4  [%s] ===" % doc["label"])
    print("\nN3  %s" % n3["gate"])
    print("    %d arm: %d PASS / %d FAIL" % (n3["n_arms"], n3["n_pass"], n3["n_fail"]))
    print("    FAIL theo o: %s" % (n3["fail_by_cell"] or "(khong co)"))
    print("\nN4  gia dinh: %s" % n4["assumption"])
    print("    %d muc: %d PASS / %d FAIL" % (n4["n_total"], n4["n_pass"], n4["n_fail"]))
    print("    FAIL theo tham so: %s" % n4["fail_by_parameter"])
    if doc["baseline_drift"]:
        print("\n/!\\ MOC DA TROI: %s" % "; ".join(doc["baseline_drift"]))
    else:
        print("\nmoc T2 khop ban ghim: %s" % doc["T2_baseline_pinned"])
    print("\nDINH CHINH PHAM VI:\n  %s" % doc["n3_scope_correction"])
    print("\n20R2 da do chua? %s -- %s"
          % (doc["status_20r2"]["measured"], doc["status_20r2"]["why"]))
    print("\n-> %s" % os.path.relpath(args.out, REPO))


if __name__ == "__main__":
    main()

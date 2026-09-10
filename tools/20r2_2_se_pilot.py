"""20R2.2 -- do se_rel(tau) tu pilot va KHOP LUAT GOP se_rel = C/sqrt(chu ky).

VI SAO KHONG DUNG TUNG UOC LUONG 5-SEED
=======================================
`se` uoc tu 5 seed co ~35% do bat dinh danh nghia, va DO DUOC con te hon. Bang
chung la mot phep DOI CHUNG: nang n gap 4 thi se PHAI giam 2 lan.

    tau=20   se 0.003381 -> 0.001699   GIAM 1.99x   dung huong
    tau=28   se 0.000908 -> 0.001569   TANG 1.73x   NGUOC huong

Mot dai luong ma phep do khong theo kip HUONG DA BIET thi khong dung lam tham
so cua bang duoc. (F(4,4) cho ti so phuong sai nay p ~ 0.02 -- hiem nhung
khong bat kha.)

=> Gop 10 phep do de uoc MOT tham so C. On dinh hon han 10 uoc luong doc lap.
   So mu do duoc -0.532 so voi -0.5 cua ly thuyet, tren 10 diem.

SEED 201-205, KHONG PHAI 101-105
================================
Chien dich dung seed 101-105. Neu pilot dung chung seed thi bang chap nhan se
duoc chon tu CHINH du lieu se duoc cham -- mot dang vong tron. Pilot phai doc
lap voi chien dich.

DU LIEU THO KHONG NAM TRONG GIT
==============================
Parquet cua pilot o results/RAW/phase-20R2/se_pilot/ KHONG duoc commit:
.gitignore:64 chi cho qua json/md/csv/png/sha256 trong results/, vi results/
co the chua tep nang. Tren mot clone sach thu muc do RONG.

=> Tool nay KHONG tai lap duoc tren clone sach neu khong chay lai phep do.
   Cung tinh chat voi docs/phase-20R2/baseline_failures.txt ("Mot clone sach
   KHONG cho cung con so"). Vi vay no KHONG nam trong bang TOOLS cua
   test/test_20r2_tools_run_and_reproduce.py ma nam o REQUIRES_LOCAL_RAW,
   kem ly do -- de khong ai "sua" bang cach them no vao roi thay do tren CI.

Chay:
    python -m tools.20r2_2_se_pilot --out docs/phase-20R2/02-se-pilot.json
    python -m tools.20r2_2_se_pilot --out ... --measure   # chay lai phep do (~20 phut)
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
RAW_REL = "results/RAW/phase-20R2/se_pilot"

SEEDS = [201, 202, 203, 204, 205]
TAUS = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0]
CONTROL_TAUS = [20.0, 28.0]        # chay them x4 lam DOI CHUNG cho luat
CONTROL_MULTIPLIER = 4

# Diem luoi 20r2_measured gan z tham chieu 0.3650 nhat (lech 0.001).
# Luoi khong chua dung 0.3650.
Z_REFERENCE_GRID_POINT = 0.366


def _measure(out_dir: pathlib.Path) -> None:
    """Chay lai phep do. ~20 phut. Chi khi --measure."""
    import measurements.decision_error_v2 as DE
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    out_dir.mkdir(parents=True, exist_ok=True)
    for tau in TAUS:
        DE.run_fixed_grid(tau=tau, seeds=SEEDS,
                          out_path=str(out_dir / ("se_%s.parquet" % tau)),
                          z_values=list(DE.Z_ALL_20R2),
                          n=n_for_tau(tau, DEFAULT_DT))
    for tau in CONTROL_TAUS:
        DE.run_fixed_grid(tau=tau, seeds=SEEDS,
                          out_path=str(out_dir / ("se4_%s.parquet" % tau)),
                          z_values=list(DE.Z_ALL_20R2),
                          n=n_for_tau(tau, DEFAULT_DT) * CONTROL_MULTIPLIER)


def _campaign_multiplier(tau: float) -> int:
    """He so nang n ma CHIEN DICH se dung (san 200 chu ky) -- de biet mot quan
    sat co phai cau hinh THAT hay chi la diem pilot."""
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    cycles = n_for_tau(tau, DEFAULT_DT) * DEFAULT_DT / float(tau)
    mul = 1
    while cycles * mul < 200.0:
        mul *= 2
    return mul


def _one(path: str) -> tuple:
    """(err_bar, se) tren o GATE tai z tham chieu. cbr LOAI -- no suy bien."""
    import pandas as pd
    df = pd.read_parquet(path)
    d = df[(df["z_s"] == Z_REFERENCE_GRID_POINT) & (df["mode"] != "cbr")]
    if d.empty:
        raise LookupError("khong co hang gate tai z = %g trong %s"
                          % (Z_REFERENCE_GRID_POINT, path))
    per_seed = d.groupby("seed")["err_total"].mean()
    return (float(per_seed.mean()),
            float(per_seed.std(ddof=1) / math.sqrt(len(per_seed))))


def build(raw_dir: pathlib.Path) -> dict:
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    obs = []
    for path in sorted(glob.glob(str(raw_dir / "*.parquet"))):
        name = os.path.basename(path)
        m = re.match(r"^se(4)?_([0-9.]+)\.parquet$", name)
        if not m:
            continue
        mul = CONTROL_MULTIPLIER if m.group(1) else 1
        tau = float(m.group(2))
        err_bar, se = _one(path)
        cycles = n_for_tau(tau, DEFAULT_DT) * mul * DEFAULT_DT / tau
        obs.append({"tau": tau, "n_multiplier": mul, "cycles": cycles,
                    "err_bar": err_bar, "se": se, "se_rel": se / err_bar,
                    "source": os.path.relpath(path, REPO)})
    obs.sort(key=lambda o: (o["n_multiplier"], o["tau"]))
    if len(obs) < 8:
        raise SystemExit(
            "chi thay %d parquet pilot trong %s.\n"
            "  Parquet KHONG duoc commit: .gitignore:64 chi cho qua "
            "json/md/csv/png/sha256 trong results/ (results/ co the chua tep "
            "nang). Nen tren mot clone sach thu muc nay RONG -- do la CO Y.\n"
            "  -> chay lai phep do:  python -m tools.20r2_2_se_pilot --out ... "
            "--measure   (~20 phut)\n"
            "  -> hoac tro toi thu muc co san: --raw-dir <duong dan>"
            % (len(obs), os.path.relpath(raw_dir, REPO)))

    C = [o["se_rel"] * math.sqrt(o["cycles"]) for o in obs]
    n = len(C)
    c_mean = sum(C) / n
    c_sd = math.sqrt(sum((x - c_mean) ** 2 for x in C) / (n - 1))

    # khop so mu bang binh phuong toi thieu tren thang log
    xs = [math.log(o["cycles"]) for o in obs]
    ys = [math.log(o["se_rel"]) for o in obs]
    xb = sum(xs) / n
    yb = sum(ys) / n
    sxy = sum((x - xb) * (y - yb) for x, y in zip(xs, ys))
    sxx = sum((x - xb) ** 2 for x in xs)
    slope = sxy / sxx

    # --- DO PHU cua C_upper. Khai TRUOC, khong giai thich sau.
    c_upper = c_mean + c_sd
    uncovered = []
    for o, cv in zip(obs, C):
        if cv > c_upper:
            campaign = (o["n_multiplier"] == _campaign_multiplier(o["tau"]))
            uncovered.append({
                "tau": o["tau"], "n_multiplier": o["n_multiplier"],
                "cycles": o["cycles"], "C": cv,
                "is_campaign_config": campaign,
                "note": ("CAU HINH CHIEN DICH" if campaign
                         else "cau hinh PILOT, khong con dung"),
                "se_rel_measured": o["se_rel"],
                "three_sigma": 3 * o["se_rel"],
            })

    ctrl = {}
    for tau in CONTROL_TAUS:
        a = next(o for o in obs if o["tau"] == tau and o["n_multiplier"] == 1)
        b = next(o for o in obs if o["tau"] == tau and o["n_multiplier"] == CONTROL_MULTIPLIER)
        ctrl["tau_%g" % tau] = {
            "se_x1": a["se"], "se_x4": b["se"],
            "ratio_observed": a["se"] / b["se"],
            "ratio_expected": math.sqrt(CONTROL_MULTIPLIER),
            "direction_ok": b["se"] < a["se"],
        }

    return {
        "schema": "dt4n.se_pilot.v2",
        "generated_by": "tools/20r2_2_se_pilot.py",
        "seeds": SEEDS,
        "why_fresh_seeds": (
            "seed 201-205, KHONG phai 101-105 cua chien dich. Dung chung seed se "
            "lam bang chap nhan duoc chon tu CHINH du lieu se duoc cham -- mot "
            "dang vong tron."),
        "z_reference_grid_point": Z_REFERENCE_GRID_POINT,
        "why_this_z": (
            "diem luoi 20r2_measured gan z tham chieu 0.3650 nhat (lech 0.001). "
            "Luoi khong chua dung 0.3650."),
        "population": "8 o gate (poisson x4, h2 x4); cbr LOAI vi suy bien",
        "estimator": (
            "trung binh err_total tren o gate cho TUNG seed, roi se qua 5 seed"),
        "observations": obs,
        "law": {
            "form": "se_rel = C / sqrt(so chu ky doc lap)",
            "C_mean": c_mean,
            "C_sd": c_sd,
            "C_upper": c_mean + c_sd,
            "which_C_is_used": "C_upper (= trung binh + 1sd), bao thu vua phai",
            "fitted_exponent": slope,
            "theoretical_exponent": -0.5,
            "n_points": n,
            "C_observed_range": [min(C), max(C)],
            "C_spread_ratio": max(C) / min(C),
            "why_pool": (
                "se uoc tu 5 seed co ~35% do bat dinh; gop de uoc MOT tham so "
                "on dinh hon 10 uoc luong doc lap."),
        },
        "C_coverage": {
            "n_observations": n,
            "n_covered_by_C_upper": n - len(uncovered),
            "uncovered": uncovered,
            "why_accepted": (
                "C_upper = trung binh + 1sd CO CHU DICH. Bam theo max quan sat "
                "duoc la KHOP THEO NHIEU -- chinh cai ma luat gop sinh ra de "
                "tranh (C tu no bat dinh ~35% o 5 seed). Doi lai: o cau hinh "
                "chien dich khong duoc phu, bang HEP HON 3 sigma rieng cua o do."),
            "if_an_uncovered_cell_fails_the_band": (
                "KIEM C_coverage TRUOC khi dien giai. Mot truot rieng o o nam "
                "trong danh sach nay, trong pham vi da ghi, la UNG VIEN CUA "
                "NHIEU BANG -- khong phai mot phat hien. Cach giai thich canh "
                "tranh nay duoc KY TRUOC, nen dung no khong phai la HARKing."),
        },
        "control_check": {
            "question": "nang n x4 co lam se giam sqrt(4) = 2 lan khong?",
            "per_tau": ctrl,
            "verdict": (
                "tau=20 giam DUNG huong; tau=28 TANG -- NGUOC huong da biet. "
                "Day la bang chung truc tiep rang uoc luong se tu 5 seed KHONG "
                "dung lam san bang duoc, va vi sao phai dung LUAT GOP."),
        },
        "limitation": (
            "Do tai MOT diem z (%g) va MOT gia tri a (mac dinh 0.9). Luat "
            "C/sqrt(N) gia dinh C khong doi theo z va a -- CHUA KIEM [20R2-D6]."
            % Z_REFERENCE_GRID_POINT),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw-dir", default=None)
    ap.add_argument("--measure", action="store_true",
                    help="chay lai phep do (~20 phut) truoc khi khop luat")
    args = ap.parse_args()

    raw = pathlib.Path(args.raw_dir) if args.raw_dir else REPO / RAW_REL
    if args.measure:
        _measure(raw)

    doc = build(raw)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=True)
        fh.write("\n")

    law = doc["law"]
    print("=== 20R2.2: se pilot va luat gop ===")
    print("%d phep do, seed %s, z = %g"
          % (len(doc["observations"]), doc["seeds"], doc["z_reference_grid_point"]))
    print("\ntau   mul   chu ky    se_rel    C = se_rel*sqrt(chu ky)")
    for o in doc["observations"]:
        print("%5.1f  x%-3d %8.1f   %6.3f%%   %.4f"
              % (o["tau"], o["n_multiplier"], o["cycles"], o["se_rel"] * 100,
                 o["se_rel"] * math.sqrt(o["cycles"])))
    print("\nC: trung binh %.4f  sd %.4f  -> DUNG %.4f (trung binh + 1sd)"
          % (law["C_mean"], law["C_sd"], law["C_upper"]))
    print("so mu do duoc %.3f  (ly thuyet %.1f)  tren %d diem"
          % (law["fitted_exponent"], law["theoretical_exponent"], law["n_points"]))
    cov = doc["C_coverage"]
    print("\nDO PHU C_upper: %d/%d quan sat"
          % (cov["n_covered_by_C_upper"], cov["n_observations"]))
    for u in cov["uncovered"]:
        print("  tau=%-5g x%-2d %5.0f chu ky  C=%.4f  %s%s"
              % (u["tau"], u["n_multiplier"], u["cycles"], u["C"], u["note"],
                 "  <- 3sigma = %.3f%%" % (u["three_sigma"] * 100)
                 if u["is_campaign_config"] else ""))
    print("\nDOI CHUNG (nang n x4 -> se phai giam 2 lan):")
    for k, v in doc["control_check"]["per_tau"].items():
        print("  %-10s se %.6f -> %.6f  ti so %.2f (mong doi %.2f)  %s"
              % (k, v["se_x1"], v["se_x4"], v["ratio_observed"],
                 v["ratio_expected"], "OK" if v["direction_ok"] else "NGUOC HUONG"))
    print("\n-> %s" % os.path.relpath(args.out, REPO))


if __name__ == "__main__":
    main()

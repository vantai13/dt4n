#!/usr/bin/env python3
"""20R2.6 -- PHAN QUYET cac du doan da ky. CHI DOC artifact, khong mo phong.

THU TU BAT BUOC (blind analysis, prereg §17-P):
  1. §17 (cach doc) + tool nay + test tren du lieu GIA -> commit -> tag
     phase-20R2-adjudicator-frozen -> push. CHUA doc mot o chien dich nao.
  2. Chay tool. Guard doi: tag co tren REMOTE; tool/test/du doan/prereg KHONG
     doi tu tag; hygiene 05 = PASS (gate VALIDITY truoc gate OUTCOME, NT 56).
  3. Commit artifact + bao cao. MOI MISS giu nguyen, cung do chi tiet nhu HIT.

MOI HANG SO PHAN QUYET DOC TU ARTIFACT DA KY [W4]:
  Sheppard, z ky, band_rel, se_rel   <- 01-prediction-signed.json
  z diem luoi                        <- 02-se-pilot.json
Hai hang so chi co trong VAN BAN ky (sigma >= 3, >= 6/7 cap) duoc CHEP, va co
test khoa ban chep voi chuoi goc trong reading_policy.

    python -m tools.20r2_6_adjudicate --out docs/phase-20R2/06-adjudication.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import subprocess
from typing import Any, Dict, List

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRED = "docs/phase-20R2/01-prediction-signed.json"
SEP = "docs/phase-20R2/02-se-pilot.json"
PLAN = "docs/phase-20R2/03-run-plan.json"
LOG = "docs/phase-20R2/04-campaign-log.jsonl"
HYG = "docs/phase-20R2/05-hygiene.json"
PREREG = "docs/phase-20R2/00-preregistration.md"
TAG = "phase-20R2-adjudicator-frozen"
FROZEN = ("tools/20r2_6_adjudicate.py", "test/test_20r2_6_adjudicator.py",
          PRED, SEP, PREREG)

GATE_MODES = ("poisson", "h2")   # POPULATION §12.2 -- 8 o gate
DIAG_MODE = "cbr"                # chan doan, bao cao RIENG (§13.5, §17-G6)
PRIMARY_A = 0.9                  # §17-G1: dieu kien DA DO luat se
SIGMA_READABLE = 3.0             # reading_policy.SECONDARY_shape.statistic
MIN_PAIRS = 6                    # reading_policy.SECONDARY_shape.pass_rule


def _git(*a: str) -> str:
    try:
        return subprocess.check_output(["git", *a], text=True, cwd=ROOT,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _sha(rel: str) -> str:
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def sheppard(z: float, tau: float) -> float:
    return math.acos(math.exp(-float(z) / float(tau))) / math.pi


def classify(rel: float, band: float) -> str:
    """BA muc [§17-G2]. Gop thanh HAI (HIT/MISS) la cho su that bi giau --
    cung bai hoc voi den xanh rong: lam phang logic ba gia tri thanh hai."""
    if rel >= 0.0:
        return "AT_OR_ABOVE"
    if rel >= -band:
        return "BELOW_WITHIN_BAND"
    return "BELOW_BEYOND_BAND"


def signed_inputs() -> Dict[str, Any]:
    pred = json.loads((ROOT / PRED).read_text(encoding="utf-8"))
    sep = json.loads((ROOT / SEP).read_text(encoding="utf-8"))
    per_tau = pred["acceptance_band"]["per_tau"]
    inp = {
        "taus": [float(t) for t in pred["taus"]],
        "sheppard": {float(r["tau"]): float(r["err"]) for r in pred["sheppard"]},
        "band": {float(r["tau"]): float(r["band_rel"]) for r in per_tau},
        "se_rel": {float(r["tau"]): float(r["se_rel_from_law"]) for r in per_tau},
        "z_signed": float(pred["z_reference_s"]),
        "z_grid": float(sep["z_reference_grid_point"]),
        "z_legacy_signed": float(pred["z_legacy_contrast"]),
    }
    # DOI CHUNG CHO CHINH BO CHAM: bang da ky phai TAI LAP tu cong thuc.
    for t in inp["taus"]:
        if abs(sheppard(inp["z_signed"], t) - inp["sheppard"][t]) > 1e-12:
            raise AssertionError("bang Sheppard da ky KHONG tai lap tai tau=%g" % t)
    # §17-G2: nguong ba muc PHAI la 3-sigma, tuc band == K_MC * se.
    k = float(pred["acceptance_band"]["K_MC"])
    for t in inp["taus"]:
        if abs(inp["band"][t] - k * inp["se_rel"][t]) > 1e-12:
            raise AssertionError("band != K_MC*se tai tau=%g -> §17-G2 khong con dung" % t)
    return inp


def guard() -> None:
    """Chan TRUOC khi doc mot byte du lieu chien dich nao."""
    if not _git("ls-remote", "--tags", "origin", TAG):
        raise SystemExit("DUNG: chua co tag %s tren REMOTE -- bo cham chua dong bang." % TAG)
    changed = _git("diff", "--name-only", TAG, "HEAD", "--", *FROZEN)
    dirty = _git("status", "--porcelain", "--", *FROZEN)
    if changed or dirty:
        raise SystemExit("DUNG: bo cham/du doan/prereg doi SAU khi dong bang:\n%s%s"
                         % (changed, dirty))
    hyg = json.loads((ROOT / HYG).read_text(encoding="utf-8"))
    if hyg.get("verdict") != "PASS":
        raise SystemExit("DUNG: hygiene khong PASS -- khong mo ket qua tren du lieu "
                         "chua chung minh la hop le [NT 56].")


def load_campaign() -> pd.DataFrame:
    """Doc parquet chien dich, KIEM sha voi so cai truoc khi dung.

    Lap lai H3 co chu dich: hygiene chung minh du lieu hop le TAI THOI DIEM DO.
    Bo cham chay SAU, va no la thu doc ra con so di vao bao cao -- no phai tu
    chung minh doc dung file, khong thua ke niem tin tu mot buoc truoc.
    """
    plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
    log = [json.loads(x) for x in (ROOT / LOG).read_text(encoding="utf-8").splitlines()
           if x.strip()]
    sha_of = {e["out"]: e["sha256"] for e in log
              if e["kind"] == "run" and e["returncode"] == 0}
    frames = []
    for r in plan["runs"]:
        if r["is_canary"]:
            continue
        if _sha(r["out"]) != sha_of.get(r["out"]):
            raise SystemExit("DUNG: %s khong khop so cai." % r["out"])
        d = pd.read_parquet(ROOT / r["out"])
        d["branch"] = r["branch"]
        d["a"] = float(r["a"])
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def pooled(d: pd.DataFrame, *, branch: str, z: float, a: float, modes,
           col: str = "err_total"):
    """Estimator DA KY: trung binh qua O cho TUNG seed, ROI qua seed."""
    s = d[(d["branch"] == branch) & (d["a"] == a) & (d["mode"].isin(modes))
          & np.isclose(d["z_s"].to_numpy(float), z, rtol=0.0, atol=1e-9)]
    out = {}
    for tau, g in s.groupby("tau_rho"):
        per_seed = g.groupby("seed")[col].mean()
        out[float(tau)] = {
            "mean": float(per_seed.mean()),
            "per_seed": {int(k): float(v) for k, v in per_seed.items()},
            "se_5seed": (float(per_seed.std(ddof=1) / math.sqrt(len(per_seed)))
                         if len(per_seed) > 1 else float("nan")),
            "n_seeds": int(len(per_seed)),
            "cells_per_seed": sorted({int(x) for x in g.groupby("seed").size()}),
        }
    return out


def primary_rows(est, inp) -> List[Dict[str, Any]]:
    rows = []
    for t in inp["taus"]:
        e, sh, band = est[t]["mean"], inp["sheppard"][t], inp["band"][t]
        rel = e / sh - 1.0
        sh_g = sheppard(inp["z_grid"], t)          # §17-G3 kiem do vung
        rel_g = e / sh_g - 1.0
        lvl, lvl_g = classify(rel, band), classify(rel_g, band)
        rows.append({
            "tau": t, "err_hat": e, "sheppard_signed": sh, "rel": rel, "band_rel": band,
            "level": lvl,
            "directional": "MISS" if lvl == "BELOW_BEYOND_BAND" else "HIT",  # §17-G2
            "literal_point_reading": "HIT" if rel >= 0.0 else "MISS",        # BAT BUOC kem
            "match_rq20r2d": "WITHIN" if abs(rel) <= band else "OUTSIDE",
            "robust_z_grid": {"z": inp["z_grid"], "sheppard": sh_g, "rel": rel_g,
                              "level": lvl_g, "verdict_changes": lvl_g != lvl},
            "se_rel_law": inp["se_rel"][t], "se_5seed_diagnostic": est[t]["se_5seed"],
        })
    return rows


def pair_rows(rows, se_rel) -> List[Dict[str, Any]]:
    out = []
    for r1, r2 in zip(rows[:-1], rows[1:]):
        e1, e2 = r1["err_hat"], r2["err_hat"]
        s = math.hypot(se_rel[r1["tau"]] * e1, se_rel[r2["tau"]] * e2)
        sig = abs(e1 - e2) / s if s > 0 else float("inf")
        if sig < SIGMA_READABLE:
            st = "UNREADABLE"
        elif e1 > e2:
            st = "DECREASING"
        else:
            st = "INCREASING"
        out.append({"pair": [r1["tau"], r2["tau"]], "diff": e1 - e2,
                    "sigma": sig, "status": st})
    return out


def shape_verdict(pairs) -> Dict[str, Any]:
    n = {k: sum(p["status"] == k for p in pairs)
         for k in ("DECREASING", "INCREASING", "UNREADABLE")}
    if n["INCREASING"] >= 2:
        v = "HOLD_SUSPECT_ESTIMATOR"     # reading_policy: vo >= 2 cap -> doi chung TRUOC
    elif n["DECREASING"] >= MIN_PAIRS:
        v = "PASS"
    else:
        v = "FAIL"
    return {"counts": n, "denominator": len(pairs), "verdict": v,
            "unreadable_counts_as": "KHONG don dieu (§17-G4: vang bang chung != bang chung)",
            "sigma_is_conservative": ("CRN qua tau lam se_diff that NHO hon gia dinh doc "
                                      "lap, nen sigma la uoc luong THAP [§17-G4]")}


def cbr_diagnostic(d, inp, a) -> List[Dict[str, Any]]:
    s = d[(d["branch"] == "main") & (d["a"] == a)
          & np.isclose(d["z_s"].to_numpy(float), inp["z_grid"], rtol=0.0, atol=1e-9)]
    cell = s.groupby(["tau_rho", "mode", "rho_bar"])[["err_total", "err_model"]].mean().reset_index()
    out = []
    for t in inp["taus"]:
        c = cell[cell["tau_rho"] == t]
        gate = c[c["mode"].isin(GATE_MODES)]
        lo, hi = float(gate["err_total"].min()), float(gate["err_total"].max())
        for _, r in c[c["mode"] == DIAG_MODE].iterrows():
            e = float(r["err_total"])
            pos = ("BELOW_ALL_GATE" if e < lo else
                   ("ABOVE_ALL_GATE" if e > hi else "INSIDE_GATE_RANGE"))
            mech = {"BELOW_ALL_GATE": "co che 1 (cbr deu theo thoi gian -> twin cu van dung)",
                    "ABOVE_ALL_GATE": "co che 2 (bien ~ 0 -> argmin tuy y)",
                    "INSIDE_GATE_RANGE": "KHONG xac dinh"}[pos]
            out.append({"tau": t, "cell": "cbr@%.3f" % r["rho_bar"], "err_total": e,
                        "err_model": float(r["err_model"]), "gate_range": [lo, hi],
                        "position": pos, "mechanism_reading": mech})
    return out


def axis_contrast(d, inp, a, z_legacy_grid) -> List[Dict[str, Any]]:
    """RQ-20R2e -- MO TA, khong phan quyet (§17-G5). Ghep cap theo seed (CRN)."""
    m = pooled(d, branch="main", z=inp["z_grid"], a=a, modes=GATE_MODES)
    c = pooled(d, branch="control_legacy", z=z_legacy_grid, a=a, modes=GATE_MODES)
    out = []
    for t in inp["taus"]:
        diffs = [c[t]["per_seed"][s] - m[t]["per_seed"][s] for s in m[t]["per_seed"]]
        out.append({"tau": t, "err_main": m[t]["mean"], "err_legacy": c[t]["mean"],
                    "rel_legacy_vs_main": c[t]["mean"] / m[t]["mean"] - 1.0,
                    "paired_diff_mean": float(np.mean(diffs)),
                    "paired_diff_range": [float(min(diffs)), float(max(diffs))],
                    "sheppard_ref_rel": (sheppard(inp["z_legacy_signed"], t)
                                         / inp["sheppard"][t] - 1.0)})
    return out


def exploratory(d, inp, a) -> List[Dict[str, Any]]:
    """§17-H: gia thuyet DA DANG KY truoc khi mo. EXPLORATORY, khong vao gate."""
    tot = pooled(d, branch="main", z=inp["z_grid"], a=a, modes=GATE_MODES, col="err_total")
    stale = pooled(d, branch="main", z=inp["z_grid"], a=a, modes=GATE_MODES, col="err_stale")
    model = pooled(d, branch="main", z=inp["z_grid"], a=a, modes=GATE_MODES, col="err_model")
    out = []
    for t in inp["taus"]:
        sh = inp["sheppard"][t]
        out.append({"tau": t,
                    "HB_err_stale_over_sheppard": stale[t]["mean"] / sh,
                    "HB_holds": bool(stale[t]["mean"] < sh),
                    "HA_floor_share": (model[t]["mean"] / tot[t]["mean"]
                                       if tot[t]["mean"] > 0 else float("nan")),
                    "HA_total_over_sheppard": tot[t]["mean"] / sh,
                    "HA_total_above_sheppard": bool(tot[t]["mean"] > sh)})
    return out


def adjudicate(d: pd.DataFrame, inp: Dict[str, Any]) -> Dict[str, Any]:
    import measurements.decision_error_v2 as DE
    est = pooled(d, branch="main", z=inp["z_grid"], a=PRIMARY_A, modes=GATE_MODES)
    for t in inp["taus"]:
        if est[t]["n_seeds"] != 5 or est[t]["cells_per_seed"] != [8]:
            raise AssertionError("tau=%g: can 5 seed x 8 o gate, co %r" % (t, est[t]))
    rows = primary_rows(est, inp)
    pairs = pair_rows(rows, inp["se_rel"])
    est05 = pooled(d, branch="main", z=inp["z_grid"], a=0.5, modes=GATE_MODES)
    z_leg = min(DE.Z_ALL, key=lambda z: abs(z - inp["z_legacy_signed"]))
    levels = [r["level"] for r in rows]
    return {
        "primary_directional": {
            "rows": rows, "denominator": len(rows),
            "n_hit": sum(r["directional"] == "HIT" for r in rows),
            "levels": {k: levels.count(k) for k in
                       ("AT_OR_ABOVE", "BELOW_WITHIN_BAND", "BELOW_BEYOND_BAND")},
            "n_hit_literal_point_reading": sum(r["literal_point_reading"] == "HIT"
                                               for r in rows),
            "any_verdict_changes_at_z_grid": any(r["robust_z_grid"]["verdict_changes"]
                                                 for r in rows),
            "reading": "§17-G2 ba muc; HIT = khong BELOW_BEYOND_BAND (3-sigma co huong)",
        },
        "secondary_shape": {"pairs": pairs, **shape_verdict(pairs)},
        "secondary_a05": {"rows": primary_rows(est05, inp),
                          "caveat": "bang CHUA kiem o a=0.5 (20R2-D6) -- MO TA, khong phan quyet"},
        "cbr_diagnostic": cbr_diagnostic(d, inp, PRIMARY_A),
        "rq20r2e_axis_contrast": {"z_legacy_grid": z_leg,
                                  "z_legacy_signed": inp["z_legacy_signed"],
                                  "rows": axis_contrast(d, inp, PRIMARY_A, z_leg),
                                  "status": "DESCRIPTIVE -- khong co luat phan quyet da ky"},
        "exploratory_registered": {"rows": exploratory(d, inp, PRIMARY_A),
                                   "status": "EXPLORATORY -- dang ky §17-H TRUOC khi mo; khong vao gate"},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    guard()
    inp = signed_inputs()
    doc = {"schema": "dt4n.adjudication_20r2_6.v1",
           "generated_by": "tools/20r2_6_adjudicate.py",
           "WHAT_THIS_IS": ("PHAN QUYET gate OUTCOME. Doc theo §17 da khoa TRUOC khi mo. "
                            "MOI MISS duoc giu, mau so CO DINH."),
           "frozen_tag_commit": _git("rev-parse", TAG + "^{commit}"),
           "inputs_sha256": {p: _sha(p) for p in (PRED, SEP, PLAN, LOG, HYG)},
           **adjudicate(load_campaign(), inp)}
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, sort_keys=True, default=float) + "\n",
                   encoding="utf-8")
    p = doc["primary_directional"]
    print("PRIMARY  %d/%d HIT  %s  (doc nguyen van: %d/%d)" % (
        p["n_hit"], p["denominator"], p["levels"],
        p["n_hit_literal_point_reading"], p["denominator"]))
    for r in p["rows"]:
        print("  tau=%-5g err=%.4f sh=%.4f rel=%+.2f%% band=%.2f%%  %s" % (
            r["tau"], r["err_hat"], r["sheppard_signed"], 100 * r["rel"],
            100 * r["band_rel"], r["level"]))
    s = doc["secondary_shape"]
    print("SHAPE    %s  %s" % (s["verdict"], s["counts"]))
    print("-> %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Lesson 23.18 [T1][T2] -- giai phau chu ky stall trong chien dich AoI 23.8.

Doc cycles_*.jsonl va aoi_*.jsonl. KHONG do moi.
Phan xu H1 (transient khoi dong) vs H2 (tinh chat that) vs H3 (reconcile).

Preregistration: docs/phase-23/00zy-amendment-45.md

Chay:
    python measurements/aoi_stall_anatomy.py \
        --campaign results/RAW/phase-23/aoi_v7_campaign \
        --out results/LIVE/phase-23/aoi_stall_anatomy.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import defaultdict

import numpy as np

# --- HANG SO KHOA o amendment 23-45 muc 5. KHONG phai co dong lenh. --------
# Neu la --warmup thi se thu 10, 20, 30, 50 cho toi khi CV lot dai M-79.
# Do la p-hacking. La hang so module, viec doi no phai la mot hanh dong
# CO Y THUC: sua code + viet amendment moi.
WARMUP_CYCLES = 20      # chu ky 1..19 bi cat; moc la t_cycle_start cua cycle 20
LONG_CYCLE_S = 0.55     # nguong "chu ky dai"
TAIL_CYCLES = 5         # amendment 23-45b muc 9(a): transient TAT MAY

RUN_KEY = re.compile(r"(clean|prod)_rho([0-9.]+)_rep([0-9]+)")


def load_jsonl(path: str) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def run_key(path: str) -> str:
    m = RUN_KEY.search(os.path.basename(path))
    return m.group(0) if m else os.path.basename(path)


def parse_key(key: str) -> tuple[str, float, int]:
    m = RUN_KEY.search(key)
    return m.group(1), float(m.group(2)), int(m.group(3))


# ----------------------------------------------------------------- T1
def stall_positions(cycle_files: list[str]) -> dict:
    """M-78 / M-78b / M-78c / M-78d / M-82 / M-88.

    Chu ky duoc danh so tu 1 (kiem tren du lieu). "Cycle < 20" nghia la
    19 chu ky dau tien.
    """
    per_run, all_pos, all_frac = [], [], []
    n_reconcile_overrun = n_overrun = 0
    comp = {"lock_wait_ms": [], "cycle_scan_ms": [], "other_ms": []}
    n_long = n_cycles_tot = 0

    for path in sorted(cycle_files):
        rows = load_jsonl(path)
        if not rows:
            continue
        mode, rho, rep = parse_key(run_key(path))
        cycles = [r["cycle"] for r in rows]
        lo, hi = min(cycles), max(cycles)
        span = max(hi - lo, 1)

        over = [r for r in rows if r.get("overrun")]
        n_overrun += len(over)
        n_reconcile_overrun += sum(1 for r in over if r.get("is_reconcile"))

        pos = sorted(r["cycle"] for r in over)
        over_rec = sum(1 for r in over if r.get("is_reconcile"))
        n_rec = sum(1 for r in rows if r.get("is_reconcile"))
        all_pos.extend(pos)
        all_frac.extend((c - lo) / span for c in pos)

        elapsed = np.array([r["cycle_elapsed_ms"] for r in rows], float)
        med = float(np.median(elapsed))
        n_long += int((elapsed > LONG_CYCLE_S * 1000).sum())
        n_cycles_tot += len(rows)

        for r in rows:
            lw, sc, el = (r.get("lock_wait_ms", 0.0), r.get("cycle_scan_ms", 0.0),
                          r["cycle_elapsed_ms"])
            comp["lock_wait_ms"].append(lw)
            comp["cycle_scan_ms"].append(sc)
            comp["other_ms"].append(el - lw - sc)   # chu yeu la vong PATCH

        per_run.append({
            "run": run_key(path), "mode": mode, "rho_bar": rho, "repeat": rep,
            "n_cycles": len(rows), "cycle_lo": lo, "cycle_hi": hi,
            "n_overrun": len(over), "overrun_cycles": pos,
            "min_overrun_cycle": pos[0] if pos else None,
            "n_reconcile": n_rec,
            "n_overrun_that_are_reconcile": over_rec,
            "base_reconcile_rate": n_rec / len(rows),
            "median_elapsed_ms": med,
            "max_elapsed_ms": float(elapsed.max()),
            # M-82
            "overrun_over_median": (
                float(max(r["cycle_elapsed_ms"] for r in over) / med) if over else None
            ),
        })

    runs_with = [r for r in per_run if r["n_overrun"] > 0]
    runs_early = [r for r in runs_with if r["min_overrun_cycle"] < WARMUP_CYCLES]
    share_early = len(runs_early) / len(runs_with) if runs_with else 0.0

    # muc 4 amendment 23-45: phan xu bang CONG THUC, khong bang mat
    if share_early >= 0.80:
        verdict = "H1_STARTUP_TRANSIENT"
        action = "cat warm-up; trong so cua stall duoi ~0.15%"
    elif share_early <= 0.50:
        verdict = "H2_INTRINSIC"
        action = "giu duoi ~1.2%; dua stall vao mo hinh AoI"
    else:
        verdict = "AMBIGUOUS"
        action = ("KHONG duoc chon. Chay them 5 run 600 s "
                  "(amendment 23-45 muc 4)")

    prod = [r for r in per_run if r["mode"] == "prod"]

    # --- CHAN DOAN HAU NGHIEM (post-hoc), KHONG phai du doan da khoa -------
    # M-78c nhu da ky la KHONG PHAN BIET DUOC: o CLEAN, reconcile_every = 1
    # nen MOI chu ky deu is_reconcile -> "chu ky overrun co phai reconcile
    # khong" luon = True bat ke H3 dung hay sai. Phep kiem co suc phan biet
    # chi ton tai o PROD (reconcile_every = 30, ty le nen ~1/30).
    p_over = sum(r["n_overrun"] for r in prod)
    p_over_rec = sum(r["n_overrun_that_are_reconcile"] for r in prod)
    p_base = float(np.mean([r["base_reconcile_rate"] for r in prod])) if prod else None
    prod_diag = {
        "_note": ("HAU NGHIEM, khong phai du doan da khoa. M-78c nhu ky ra "
                  "MISS vi o CLEAN moi chu ky deu la reconcile -> phep kiem "
                  "khong co suc phan biet. Chi PROD moi phan biet duoc H3."),
        "n_overrun_prod": p_over,
        "n_overrun_prod_that_are_reconcile": p_over_rec,
        "observed_rate": (p_over_rec / p_over) if p_over else None,
        "base_reconcile_rate": p_base,
        "H3_supported": (
            bool(p_over and p_base and (p_over_rec / p_over) > 3 * p_base)),
    }
    clean = [r for r in per_run if r["mode"] == "clean"]
    clean_diag = {
        "n_overrun_clean": sum(r["n_overrun"] for r in clean),
        "n_overrun_clean_that_are_reconcile": sum(
            r["n_overrun_that_are_reconcile"] for r in clean),
        "base_reconcile_rate": float(np.mean(
            [r["base_reconcile_rate"] for r in clean])) if clean else None,
    }
    ratios = [r["overrun_over_median"] for r in per_run
              if r["overrun_over_median"] is not None]

    return {
        "M_78_share_runs_first_overrun_before_cycle_20": share_early,
        "M_78_hit": share_early >= 0.80,
        "M_78_n_runs_with_overrun": len(runs_with),
        "M_78b_overrun_per_run": [r["n_overrun"] for r in per_run],
        "M_78b_range": [int(min(r["n_overrun"] for r in per_run)),
                        int(max(r["n_overrun"] for r in per_run))],
        "M_78b_hit": all(1 <= r["n_overrun"] <= 2 for r in per_run),
        "M_78c_reconcile_share_of_overrun": (
            n_reconcile_overrun / n_overrun if n_overrun else None),
        "M_78c_hit": ((n_reconcile_overrun / n_overrun) < 0.5) if n_overrun else None,
        "H3_prod_only_diagnostic_posthoc": prod_diag,
        "H3_clean_reference_posthoc": clean_diag,
        "M_78d_prod_reconcile_per_run": [r["n_reconcile"] for r in prod],
        "M_78d_hit": bool(prod) and all(6 <= r["n_reconcile"] <= 10 for r in prod),
        "M_82_overrun_over_median": {
            "median": float(np.median(ratios)) if ratios else None,
            "min": float(np.min(ratios)) if ratios else None,
            "max": float(np.max(ratios)) if ratios else None,
        },
        "M_82_hit": bool(ratios) and 2.5 <= float(np.median(ratios)) <= 3.5,
        "M_88_long_cycle_share": n_long / max(n_cycles_tot, 1),
        "M_88_hit": 0.0040 <= n_long / max(n_cycles_tot, 1) <= 0.0085,
        # MO TA (khong phai du doan duoc cham): thanh phan nao chi phoi
        "component_breakdown_ms_median": {
            k: float(np.median(v)) for k, v in comp.items()},
        "component_dominant": max(comp, key=lambda k: float(np.median(comp[k]))),
        "position_histogram_fraction_of_run": np.histogram(
            all_frac, bins=10, range=(0.0, 1.0))[0].tolist(),
        "all_overrun_cycles": sorted(all_pos),
        "verdict": verdict,
        "action": action,
        "per_run": per_run,
    }


# ----------------------------------------------------------------- T2
def recompute_without_warmup(aoi_files: list[str], cycle_files: list[str]) -> dict:
    """M-79 / M-80 / M-86: cat WARMUP_CYCLES chu ky dau, tinh lai thong ke.

    Neo theo THOI GIAN, khong theo chi so probe: chu ky sync (0.5 s) va luot
    probe (0.1 s) la HAI DONG HO khac nhau; cat "20 probe dau" != cat "20
    chu ky dau".
    """
    cutoff, tail_cut = {}, {}
    for path in cycle_files:
        rows = load_jsonl(path)
        starts = {r["cycle"]: r["t_cycle_start"] for r in rows
                  if r.get("t_cycle_start") is not None}
        cutoff[run_key(path)] = starts.get(WARMUP_CYCLES)
        # cat doi xung: bo them TAIL_CYCLES chu ky CUOI
        hi = max(starts) if starts else None
        tail_cut[run_key(path)] = starts.get(hi - TAIL_CYCLES) if hi else None

    by_mode = defaultdict(lambda: {"full": [], "trimmed": [], "sym": [],
                                   "rho_trim": [], "aoi_trim": []})
    per_run = []
    for path in sorted(aoi_files):
        key = run_key(path)
        mode, rho_bar, rep = parse_key(key)
        rows = load_jsonl(path)
        t_cut = cutoff.get(key)
        full, trim, rr, aa, sym = [], [], [], [], []
        t_tail = tail_cut.get(key)
        for r in rows:
            if r.get("record") != "probe":
                continue
            for v in r["links"].values():
                if v.get("aoi_s") is None:
                    continue
                full.append(v["aoi_s"])
                if t_cut is None or v["t_obs"] >= t_cut:
                    trim.append(v["aoi_s"])
                    if v.get("rho") is not None:
                        rr.append(v["rho"]); aa.append(v["aoi_s"])
                    if t_tail is None or v["t_obs"] < t_tail:
                        sym.append(v["aoi_s"])
        by_mode[mode]["full"].extend(full)
        by_mode[mode]["trimmed"].extend(trim)
        by_mode[mode]["sym"].extend(sym)
        by_mode[mode]["rho_trim"].extend(rr)
        by_mode[mode]["aoi_trim"].extend(aa)
        a = np.asarray(trim, float)
        per_run.append({
            "run": key, "mode": mode, "rho_bar": rho_bar, "repeat": rep,
            "n_full": len(full), "n_trimmed": len(trim),
            "p05_ms": float(np.percentile(a, 5) * 1000),
            "mean_ms": float(a.mean() * 1000),
            "cv": float(a.std(ddof=1) / a.mean()),
            "corr_aoi_rho": (float(np.corrcoef(aa, rr)[0, 1])
                             if len(rr) > 2 and np.std(rr) > 0 else None),
        })

    def sawtooth_null(st: dict, sample=None) -> dict:
        """Null rang cua thuan, tinh DUNG.  (amendment 23-45b)

        BUG cu: dung p05 lam `d`. Voi Uniform[d, d+T] thi
        p05 = d + 0.05 T, tuc p05 LON HON d mot khoang 0.05*500 = 25 ms.
        Dung p05 lam d thoi MEAN null len 25 ms va keo CV null xuong.

        Cach dung: uoc luong ca hai tham so bang PHUONG PHAP MOMENT
            T_hat = sd * sqrt(12)
            d_hat = mean - T_hat/2
        """
        sd, mean = st["sd_ms"], st["mean_ms"]
        T_hat = sd * np.sqrt(12.0)
        d_hat = mean - T_hat / 2.0
        out = {
            "T_hat_ms": float(T_hat), "d_hat_ms": float(d_hat),
            "sd_uniform_T500_ms": float(500.0 / np.sqrt(12.0)),
            "sd_ratio_observed_over_uniform": float(sd / (500.0 / np.sqrt(12.0))),
            "cv_null": float((500.0 / np.sqrt(12.0)) / mean),
            "cv_observed": float(st["cv"]),
            # giu lai gia tri SAI de doi chieu duoc voi ban ghi cu
            "cv_null_BUGGED_p05_as_d": float(
                0.5 / np.sqrt(12) / (st["p05_ms"] / 1000 + 0.25)),
            # M-92: hai duong suy T
            "T_from_quantiles_ms": float((st["p95_ms"] - st["p05_ms"]) / 0.90),
            "d_from_p05_ms": float(st["p05_ms"] - 25.0),
        }
        out["cv_gap"] = out["cv_observed"] - out["cv_null"]
        out["M_92_T_disagreement_ms"] = abs(
            out["T_hat_ms"] - out["T_from_quantiles_ms"])
        out["M_92_hit"] = out["M_92_T_disagreement_ms"] < 20.0
        if sample is not None and len(sample):
            # M-91: KHOP MOMENT KHONG CHUNG MINH LA UNIFORM. Phai kiem HINH DANG.
            from scipy import stats as _st
            a = np.asarray(sample, float) * 1000.0
            ks = _st.kstest(a, "uniform", args=(d_hat, T_hat))
            out["M_91_ks_statistic"] = float(ks.statistic)
            out["M_91_ks_pvalue"] = float(ks.pvalue)
            out["M_91_hit"] = float(ks.statistic) < 0.03
            out["quantile_comparison_ms"] = {
                q: {"observed": st["p%02d_ms" % q],
                    "uniform_null": float(d_hat + (q / 100.0) * T_hat),
                    "delta": float(st["p%02d_ms" % q] - (d_hat + (q / 100.0) * T_hat))}
                for q in (5, 50, 95)
            }
        return out

    def stats(a):
        a = np.asarray(a, float)
        if a.size == 0:
            return None
        return {"n": int(a.size), "mean_ms": float(a.mean() * 1000),
                "sd_ms": float(a.std(ddof=1) * 1000),
                "cv": float(a.std(ddof=1) / a.mean()),
                "p05_ms": float(np.percentile(a, 5) * 1000),
                "p50_ms": float(np.percentile(a, 50) * 1000),
                "p95_ms": float(np.percentile(a, 95) * 1000),
                "max_ms": float(a.max() * 1000)}

    out = {}
    for mode, d in by_mode.items():
        full, trim = stats(d["full"]), stats(d["trimmed"])
        rr, aa = d["rho_trim"], d["aoi_trim"]
        symst = stats(d["sym"])
        out[mode] = {
            "full": full, "trimmed": trim, "symmetric_trim": symst,
            "cv_before": full["cv"], "cv_after": trim["cv"],
            # null cu: rang cua Uniform[d, d+T], T = 0.5 s, d uoc bang p05
            "sawtooth_null": sawtooth_null(trim, d["trimmed"]),
            "sawtooth_null_symmetric": (sawtooth_null(symst, d["sym"])
                                        if symst else None),
            "corr_aoi_rho_trimmed": (float(np.corrcoef(aa, rr)[0, 1])
                                     if len(rr) > 2 else None),
        }

    cln = out.get("clean", {})
    cv_after = cln.get("cv_after")
    corr = cln.get("corr_aoi_rho_trimmed")
    return {
        "warmup_cycles_trimmed": WARMUP_CYCLES,
        "trim_anchor": "t_cycle_start cua cycle %d (bo chu ky 1..%d)"
                       % (WARMUP_CYCLES, WARMUP_CYCLES - 1),
        "by_mode": out,
        "per_run": per_run,
        "M_79_cv_clean_trimmed": cv_after,
        "M_79_hit": bool(cv_after is not None and 0.375 <= cv_after <= 0.400),
        "M_80_mean_clean_trimmed_ms": cln.get("trimmed", {}).get("mean_ms"),
        "M_80_hit": bool(cln.get("trimmed") and
                         360 <= cln["trimmed"]["mean_ms"] <= 372),
        "M_86_corr_aoi_rho_clean_trimmed": corr,
        "M_86_hit": bool(corr is not None and -0.10 <= corr <= -0.02),
        "M_91_ks_statistic": cln.get("sawtooth_null", {}).get("M_91_ks_statistic"),
        "M_91_hit": cln.get("sawtooth_null", {}).get("M_91_hit"),
        "M_92_T_disagreement_ms": cln.get("sawtooth_null", {}).get(
            "M_92_T_disagreement_ms"),
        "M_92_hit": cln.get("sawtooth_null", {}).get("M_92_hit"),
        "M_97_symmetric_trim": {
            "tail_cycles_dropped": TAIL_CYCLES,
            "cv_warmup_only": cln.get("cv_after"),
            "cv_symmetric": (cln.get("symmetric_trim") or {}).get("cv"),
            "delta_cv": ((cln.get("symmetric_trim") or {}).get("cv", 0)
                         - (cln.get("cv_after") or 0)),
            "max_ms_warmup_only": (cln.get("trimmed") or {}).get("max_ms"),
            "max_ms_symmetric": (cln.get("symmetric_trim") or {}).get("max_ms"),
        },
        "M_97_hit": abs((cln.get("symmetric_trim") or {}).get("cv", 0)
                        - (cln.get("cv_after") or 0)) < 0.005,
    }


def _provenance(script: str, argv_extra: dict) -> dict:
    """Khoi provenance chuan cua repo (NT33): ai/luc nao/bang gi tao ra file."""
    import subprocess
    from datetime import datetime, timezone

    def git(*args):
        try:
            return subprocess.run(args, capture_output=True, text=True,
                                  check=True).stdout.strip()
        except Exception:
            return ""
    return {
        "script": script,
        "git_hash": git("git", "rev-parse", "HEAD"),
        "git_dirty": bool(git("git", "status", "--porcelain")),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "argv": argv_extra,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cyc = sorted(glob.glob(os.path.join(a.campaign, "**", "cycles_*.jsonl"),
                           recursive=True))
    aoi = sorted(glob.glob(os.path.join(a.campaign, "**", "aoi_*.jsonl"),
                           recursive=True))
    if not cyc or not aoi:
        raise SystemExit("khong tim thay du lieu trong %s" % a.campaign)

    t1 = stall_positions(cyc)
    t2 = recompute_without_warmup(aoi, cyc)

    from measurements import validity as V
    import measurements.aoi_stall_anatomy as _self
    report = {
        "schema": "dt4n.aoi.stall_anatomy.v1",
        "lesson": "23.18",
        "prereg": "docs/phase-23/00zy-amendment-45.md",
        "status": "MEASUREMENT_ESTIMATE",
        "locked_constants": {"WARMUP_CYCLES": WARMUP_CYCLES,
                             "LONG_CYCLE_S": LONG_CYCLE_S},
        "n_cycle_files": len(cyc), "n_aoi_files": len(aoi),
        "T1_stall_positions": t1,
        "T2_warmup_trim": t2,
        "provenance": _provenance("measurements/aoi_stall_anatomy.py", {"campaign": a.campaign, "out": a.out,
                                 "WARMUP_CYCLES": WARMUP_CYCLES,
                                 "LONG_CYCLE_S": LONG_CYCLE_S}),
        "validity": V.measurement_validity_block(
            instrument_module=_self,
            inputs=cyc[:1] + aoi[:1],
            note=("Artifact DO chinh truc tuoi z (vai tro MEASURES). Khong "
                  "dung sawtooth_age_steps nen khong the bi d_sync=51ms lam "
                  "sai. inputs_sha256 chi ghim 2 file dai dien; toan bo "
                  "chien dich duoc ghim boi archive sha256 trong "
                  "amendment 23-45."),
        ),
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)

    c = t2["by_mode"]["clean"]
    print("=" * 68)
    print("T1  GIAI PHAU STALL")
    print("-" * 68)
    print(f"  M-78   run co overrun dau tien o cycle < {WARMUP_CYCLES}"
          f"  : {t1['M_78_share_runs_first_overrun_before_cycle_20']:6.1%}"
          f"   HIT={t1['M_78_hit']}")
    print(f"  M-78b  so overrun / run                     : "
          f"{t1['M_78b_range']}            HIT={t1['M_78b_hit']}")
    print(f"  M-78c  ty le overrun la reconcile           : "
          f"{t1['M_78c_reconcile_share_of_overrun']:6.3f}   HIT={t1['M_78c_hit']}")
    pd_ = t1["H3_prod_only_diagnostic_posthoc"]
    print(f"    [hau nghiem] chi PROD: {pd_['n_overrun_prod_that_are_reconcile']}"
          f"/{pd_['n_overrun_prod']} overrun la reconcile, "
          f"ty le nen {pd_['base_reconcile_rate']:.4f}"
          f"  -> H3 duoc ung ho = {pd_['H3_supported']}")
    print(f"  M-78d  PROD reconcile / run                 : "
          f"{sorted(set(t1['M_78d_prod_reconcile_per_run']))}        HIT={t1['M_78d_hit']}")
    print(f"  M-82   overrun / trung vi                   : "
          f"{t1['M_82_overrun_over_median']['median']:6.2f}x  HIT={t1['M_82_hit']}")
    print(f"  M-88   ty le chu ky dai (>{LONG_CYCLE_S}s)          : "
          f"{t1['M_88_long_cycle_share']:6.4%}   HIT={t1['M_88_hit']}")
    print(f"  thanh phan chi phoi cycle_elapsed_ms        : "
          f"{t1['component_dominant']}  {t1['component_breakdown_ms_median']}")
    print(f"  >> PHAN XU : {t1['verdict']}")
    print(f"     {t1['action']}")
    print("-" * 68)
    print("T2  CAT WARM-UP")
    print("-" * 68)
    n = c["sawtooth_null"]
    print(f"  M-79   CV CLEAN  {c['cv_before']:.4f} -> "
          f"{t2['M_79_cv_clean_trimmed']:.4f}   HIT={t2['M_79_hit']}")
    print(f"  null rang cua DUNG (amendment 45b)          : {n['cv_null']:.6f}"
          f"   khoang cach {n['cv_gap']:+.6f}")
    print(f"    (null CU bi BUG, p05 lam d               : "
          f"{n['cv_null_BUGGED_p05_as_d']:.6f}   khoang cach "
          f"{n['cv_observed'] - n['cv_null_BUGGED_p05_as_d']:+.6f})")
    print(f"  sd quan sat / sd Uniform[d,d+500]           : "
          f"{n['sd_ratio_observed_over_uniform']:.6f}  (lech "
          f"{abs(n['sd_ratio_observed_over_uniform']-1)*100:.2f}%)")
    print(f"  MOMENT: T = {n['T_hat_ms']:.3f} ms,  d = {n['d_hat_ms']:.3f} ms")
    print(f"  M-91   KS vs Uniform[d,d+T]                 : D="
          f"{n['M_91_ks_statistic']:.5f}  HIT={n['M_91_hit']}")
    print(f"  M-92   T tu sd vs T tu phan vi lech         : "
          f"{n['M_92_T_disagreement_ms']:7.2f} ms   HIT={n['M_92_hit']}")
    sy = t2["M_97_symmetric_trim"]
    print(f"  M-97   cat doi xung (bo {TAIL_CYCLES} chu ky cuoi)  : CV "
          f"{sy['cv_warmup_only']:.6f} -> {sy['cv_symmetric']:.6f}"
          f"  delta {sy['delta_cv']:+.6f}  HIT={t2['M_97_hit']}")
    print(f"         max AoI {sy['max_ms_warmup_only']:.1f} -> "
          f"{sy['max_ms_symmetric']:.1f} ms")
    print(f"  M-80   mean CLEAN sau cat                   : "
          f"{t2['M_80_mean_clean_trimmed_ms']:7.2f} ms  HIT={t2['M_80_hit']}")
    print(f"  M-86   corr(AoI, rho) CLEAN sau cat         : "
          f"{t2['M_86_corr_aoi_rho_clean_trimmed']:7.4f}     HIT={t2['M_86_hit']}")
    print("=" * 68)


if __name__ == "__main__":
    main()

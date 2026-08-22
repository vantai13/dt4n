#!/usr/bin/env python3
r"""Lesson 23.18 [T3][T4][T5][T6] -- phan ra AoI thanh d_transport + phase.

Nen tang (doc tu code sinh du lieu, da SUA so voi ban ke hoach 23.18):
    collector.py:585/592/608  t_source RIENG tung Thing (Amendment 23-42b)
    sync_agent.py:123         vong PATCH TUAN TU

=> AoI(link, t_obs) = [t_obs - t_visible(link)] + [t_visible(link) - t_source(link)]
                       \______ phase ______/       \____ d_transport(link) ____/

Vi t_source la dau RIENG, do lech SCAN do duoc TRUC TIEP:
    scan_offset(link) = t_source(link) - t_cycle_start(chu ky chua no)

Preregistration: docs/phase-23/00zy-amendment-45.md

Chay:
    python measurements/aoi_decompose.py \
        --campaign results/RAW/phase-23/aoi_v7_campaign \
        --estimates results/LIVE/phase-23/aoi_v7_estimates.json \
        --out results/LIVE/phase-23/aoi_decomposition.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy import stats

from measurements.aoi_stall_anatomy import (
    LONG_CYCLE_S, WARMUP_CYCLES, load_jsonl, parse_key, run_key,
)

PROBE_INTERVAL_S = 0.1          # tu header cua chien dich
PROBE_BIAS_MS = PROBE_INTERVAL_S * 1000 / 2.0     # +50 ms, bias HE THONG


# ------------------------------------------------------------------ T3
def decompose_run(aoi_path: str, cycle_path: str) -> dict:
    rows = load_jsonl(aoi_path)
    crows = load_jsonl(cycle_path)
    starts = np.array(sorted(r["t_cycle_start"] for r in crows), float)
    t_cut = next((r["t_cycle_start"] for r in crows
                  if r["cycle"] == WARMUP_CYCLES), None)

    # (link, t_source) -> t_obs SOM NHAT nhin thay t_source do
    all_src: dict[str, set] = defaultdict(set)     # KHONG cat -- de do length bias
    first_vis: dict[tuple[str, float], float] = {}
    epochs: dict[str, list[float]] = defaultdict(list)
    seen: dict[str, float] = {}
    samples = []                       # sau khi cat warm-up
    samples_all = []                   # toan bo run, de do length bias

    for r in rows:
        if r.get("record") != "probe":
            continue
        for link, v in r["links"].items():
            ts, to = v.get("t_source"), v.get("t_obs")
            if ts is None or to is None or v.get("aoi_s") is None:
                continue
            trimmed_out = t_cut is not None and to < t_cut
            ts, to = float(ts), float(to)
            all_src[link].add(ts)
            samples_all.append((link, ts, to, float(v["aoi_s"]), v.get("rho")))
            if trimmed_out:
                continue                       # cat warm-up, cung moc voi T2
            key = (link, ts)
            if key not in first_vis or to < first_vis[key]:
                first_vis[key] = to
            if seen.get(link) != ts:
                epochs[link].append(ts)
                seen[link] = ts
            samples.append((link, ts, to, float(v["aoi_s"]), v.get("rho")))

    # d_transport, scan_offset
    d_by_link, scan_by_link = defaultdict(list), defaultdict(list)
    t_eff_by_src: dict[tuple[str, float], float] = {}
    for link, srcs in epochs.items():
        arr = np.asarray(srcs, float)
        idx = np.searchsorted(starts, arr, side="right") - 1
        for i, ts in enumerate(arr):
            if (link, ts) in first_vis:
                d_by_link[link].append(first_vis[(link, ts)] - ts)
            if 0 <= idx[i] < starts.size:
                scan_by_link[link].append(ts - starts[idx[i]])
        for i in range(arr.size - 1):
            t_eff_by_src[(link, float(arr[i]))] = float(arr[i + 1] - arr[i])

    t_eff_full_by_src: dict[tuple[str, float], float] = {}
    for link, sset in all_src.items():
        arr = np.array(sorted(sset), float)
        for i in range(arr.size - 1):
            t_eff_full_by_src[(link, float(arr[i]))] = float(arr[i + 1] - arr[i])

    d_med = {k: float(np.median(v)) for k, v in d_by_link.items() if v}

    # phase = AoI - d_transport(link); PC: phase thuoc [0, T_eff]
    n_phase = n_in = n_in_deb = n_neg = 0
    phases, long_samples, n_teff_samples = [], 0, 0
    for link, ts, to, aoi, _rho in samples:
        if link not in d_med:
            continue
        ph = aoi - d_med[link]
        phases.append(ph)
        n_phase += 1
        if ph < 0:
            n_neg += 1
        te = t_eff_by_src.get((link, ts))
        if te is not None:
            n_teff_samples += 1
            if 0.0 <= ph <= te:
                n_in += 1
            if 0.0 <= ph + PROBE_BIAS_MS / 1000.0 <= te:
                n_in_deb += 1
            if te > LONG_CYCLE_S:
                long_samples += 1

    t_eff = np.array(list(t_eff_by_src.values()), float)
    # length bias tren TOAN BO run (khong cat warm-up), de cau hoi
    # "chu ky dai lam lech mau bao nhieu" duoc tra loi chu khong bi cat mat
    te_full, n_s_full, n_s_long_full = [], 0, 0
    for link, sset in all_src.items():
        arr = np.array(sorted(sset), float)
        te_full.extend(np.diff(arr).tolist())
    te_full = np.array(te_full, float)
    for link, ts, to, aoi, _r in samples_all:
        te = t_eff_full_by_src.get((link, ts))
        if te is None:
            continue
        n_s_full += 1
        if te > LONG_CYCLE_S:
            n_s_long_full += 1
    d_flat = np.array([x for v in d_by_link.values() for x in v], float)
    ph = np.asarray(phases, float)
    mode, rho_bar, rep = parse_key(run_key(aoi_path))

    return {
        "run": run_key(aoi_path), "mode": mode, "rho_bar": rho_bar, "repeat": rep,
        "n_samples": len(samples),
        "d_transport_ms_by_link": {k: v * 1000 for k, v in d_med.items()},
        "scan_offset_ms_by_link": {
            k: float(np.median(v) * 1000) for k, v in scan_by_link.items() if v},
        "d_transport_all_ms": {
            "median": float(np.median(d_flat) * 1000),
            "mean": float(d_flat.mean() * 1000),
            "p95": float(np.percentile(d_flat, 95) * 1000),
        },
        "phase_ms": {
            "n": n_phase,
            "min": float(ph.min() * 1000), "median": float(np.median(ph) * 1000),
            "max": float(ph.max() * 1000),
            "n_negative": n_neg,
            "frac_in_range": n_in / max(n_teff_samples, 1),
            "frac_in_range_debiased": n_in_deb / max(n_teff_samples, 1),
        },
        "t_eff_ms": {
            "n": int(t_eff.size),
            "median": float(np.median(t_eff) * 1000),
            "max": float(t_eff.max() * 1000),
            # M-88 tren truc T_eff (khac M-88 tren truc chu ky o T1)
            "frac_intervals_long": float((t_eff > LONG_CYCLE_S).mean()),
            "frac_samples_long": long_samples / max(n_teff_samples, 1),
            "untrimmed": {
                "n_intervals": int(te_full.size),
                "max_ms": float(te_full.max() * 1000),
                "frac_intervals_long": float((te_full > LONG_CYCLE_S).mean()),
                "frac_samples_long": n_s_long_full / max(n_s_full, 1),
            },
        },
    }


def order_check(runs: list[dict], alpha_ms: dict) -> dict:
    """M-78e / M-78f / M-78g -- H4a (scan) va H4b (patch)."""
    links = sorted(alpha_ms)

    def mat(field):
        return np.array([[r[field].get(l, np.nan) for l in links] for r in runs])

    def rank_stability(m):
        rk = np.argsort(np.argsort(m, axis=1), axis=1).astype(float)
        cors = [float(np.corrcoef(rk[i], rk[j])[0, 1])
                for i in range(len(rk)) for j in range(i + 1, len(rk))]
        return float(np.mean(cors)), float(np.min(cors))

    scan, dtr = mat("scan_offset_ms_by_link"), mat("d_transport_ms_by_link")
    s_mean, s_min = rank_stability(scan)
    d_mean, d_min = rank_stability(dtr)
    a_vec = np.array([alpha_ms[l] for l in links])
    s_vec, d_vec = np.nanmedian(scan, axis=0), np.nanmedian(dtr, axis=0)

    c_scan = float(np.corrcoef(a_vec, s_vec)[0, 1])
    c_dtr = float(np.corrcoef(a_vec, d_vec)[0, 1])

    # PHEP KIEM DONG NHAT THUC.
    # O trang thai on dinh, gia tri cua link l nhin thay duoc tu
    #     t_visible(l) = t_source(l) + d_transport(l)
    # va giu den lan refresh sau (sau T). Probe roi deu tren cua so do, nen
    #     E[AoI(l)] = d_transport(l) + T/2
    # => alpha(l) := E[AoI(l)] - trung binh  ==  d_transport(l) - mean(d_transport)
    # Do lech RMS cua dong nhat thuc nay la BANG CHUNG dinh luong cho H4,
    # manh hon mot he so tuong quan.
    pred = d_vec - d_vec.mean()
    resid = a_vec - pred
    rms = float(np.sqrt(np.mean(resid ** 2)))
    spread_alpha = float(a_vec.max() - a_vec.min())

    # M-78g MISS co phai do CO CHE hay do DO PHAN GIAI? So sd giua run voi
    # khoang cach ke nhau: sd >> khoang cach => thu hang KHONG THE on dinh
    # du co che dung. Day la van de CONG SUAT, khong phai co che.
    per_link_sd = {}
    for i, l in enumerate(links):
        col = np.array([r["d_transport_ms_by_link"].get(l, np.nan) for r in runs])
        per_link_sd[l] = float(np.nanstd(col, ddof=1))
    spacing = float((d_vec.max() - d_vec.min()) / max(len(links) - 1, 1))

    return {
        "links": links,
        "alpha_ms_by_link": {k: alpha_ms[k] for k in links},
        "scan_offset_median_ms_by_link": dict(zip(links, s_vec.round(4).tolist())),
        "d_transport_median_ms_by_link": dict(zip(links, d_vec.round(4).tolist())),
        "identity_prediction_ms_by_link": dict(zip(links, pred.round(4).tolist())),
        "M_78e_scan_rank_stability_mean_corr": s_mean,
        "M_78e_scan_rank_stability_min_corr": s_min,
        "M_78e_hit": s_mean > 0.8,
        "M_78f_corr_alpha_vs_scan_offset": c_scan,
        "M_78f_hit": abs(c_scan) > 0.8,
        "M_78g_patch_rank_stability_mean_corr": d_mean,
        "M_78g_patch_rank_stability_min_corr": d_min,
        "M_78g_hit": d_mean > 0.8,
        "corr_alpha_vs_d_transport": c_dtr,
        "identity_test": {
            "claim": "alpha(l) == d_transport(l) - mean(d_transport)",
            "derivation": "E[AoI(l)] = d_transport(l) + T/2 khi probe roi deu",
            "rms_residual_ms": rms,
            "alpha_spread_ms": spread_alpha,
            "rms_over_spread": rms / spread_alpha if spread_alpha else None,
            "residual_ms_by_link": dict(zip(links, resid.round(4).tolist())),
        },
        "M_78g_power_diagnostic": {
            "_note": ("M-78g do ON DINH THU HANG. Neu sd giua run >> khoang "
                      "cach ke nhau thi thu hang khong the on dinh DU CO CHE "
                      "DUNG -- day la gioi han CONG SUAT, khong phai bac bo H4."),
            "adjacent_spacing_ms": spacing,
            "per_link_sd_across_runs_ms": per_link_sd,
            "min_sd_over_spacing": float(min(per_link_sd.values()) / spacing),
            "rank_unstable_by_construction": bool(
                min(per_link_sd.values()) > spacing),
        },
        "interpretation": (
            ("H4 UNG HO. Dong nhat thuc alpha(l) = d_transport(l) - "
             "mean(d_transport) giai thich %.0f%% bien do alpha (RMS du "
             "%.2f ms / %.2f ms). Bien dieu khien la VI TRI TRONG VONG PATCH "
             "tuan tu cua twin, khong phai bat doi xung mang. scan_offset "
             "tuong quan %.3f voi alpha nhung KHONG vao dong nhat thuc -- no "
             "cong tuyen voi vi tri vong lap, la bien di kem chu khong phai "
             "nguyen nhan."
             % (100 * (1 - rms / spread_alpha), rms, spread_alpha, c_scan))
            if c_dtr > 0.8 else
            "H4 KHONG duoc ung ho boi du lieu nay -- phai dieu tra nguon khac."
        ),
    }


# ------------------------------------------------------------------ T4
def d_confidence_interval(per_run: list[dict], field: str) -> dict:
    """M-84 / M-90: CI theo THIET KE LONG NHAU (5 rho x 3 rep), df = 4."""
    by_rho = defaultdict(list)
    for r in per_run:
        by_rho[r["rho_bar"]].append(r[field])
    groups = [np.asarray(v, float) for v in by_rho.values()]
    k = len(groups)
    n = float(np.mean([g.size for g in groups]))
    gmeans = np.array([g.mean() for g in groups])

    ms_between = n * gmeans.var(ddof=1)
    ms_within = float(np.mean([g.var(ddof=1) for g in groups]))
    s2_between = max((ms_between - ms_within) / n, 0.0)

    mu = float(gmeans.mean())
    se = float(np.sqrt(ms_between / (k * n)))
    tcrit = float(stats.t.ppf(0.975, df=k - 1))

    flat = np.concatenate(groups)
    se_iid = float(flat.std(ddof=1) / np.sqrt(flat.size))
    t_iid = float(stats.t.ppf(0.975, df=flat.size - 1))
    icc = s2_between / (s2_between + ms_within) if (s2_between + ms_within) else 0.0

    return {
        "value_ms": mu,
        "ci95_nested": [mu - tcrit * se, mu + tcrit * se],
        "se_ms": se, "df": k - 1, "k_rho_levels": k, "n_per_level": n,
        "s2_between_rho": s2_between, "s2_within_rho": ms_within, "icc": icc,
        "ci95_naive_iid": [mu - t_iid * se_iid, mu + t_iid * se_iid],
        "df_iid": int(flat.size - 1),
        "width_ratio_nested_over_iid": (tcrit * se) / (t_iid * se_iid),
        "note": ("CI long nhau dung df = so muc rho - 1 = %d, khong phai %d. "
                 "ICC = phan phuong sai den tu MUC RHO." % (k - 1, flat.size - 1)),
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
    ap.add_argument("--estimates", required=True,
                    help="aoi_v7_estimates.json -- nguon cua alpha, doc chu khong go tay")
    ap.add_argument("--stall", required=True,
                    help="aoi_stall_anatomy.json -- nguon cua p05/cycle_elapsed")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    est = json.load(open(a.estimates, encoding="utf-8"))
    alpha_ms = est["modes"]["clean"]["offset_regression"]["offset_ms"]
    stall = json.load(open(a.stall, encoding="utf-8"))

    def pair(mode):
        out = []
        for f in sorted(glob.glob(os.path.join(
                a.campaign, "**", "aoi_%s_*.jsonl" % mode), recursive=True)):
            c = os.path.join(os.path.dirname(f),
                             os.path.basename(f).replace("aoi_", "cycles_"))
            if os.path.exists(c):
                out.append((f, c))
        return out

    clean = [decompose_run(f, c) for f, c in pair("clean")]
    prod = [decompose_run(f, c) for f, c in pair("prod")]
    if not clean:
        raise SystemExit("khong tim thay cap aoi_clean_*/cycles_clean_*")

    for r in clean + prod:
        r["_d_ms"] = r["d_transport_all_ms"]["median"]

    order = order_check(clean, alpha_ms)
    d_ci = d_confidence_interval(clean, "_d_ms")

    # --- M-81b: kiem cheo hai DONG HO doc lap -----------------------------
    cyc_med = float(np.median([r["median_elapsed_ms"]
                               for r in stall["T1_stall_positions"]["per_run"]
                               if r["mode"] == "clean"]))
    d_probe = d_ci["value_ms"]
    cross_gap = abs(d_probe - (cyc_med + PROBE_BIAS_MS))

    # --- M-84 / M-85: tam giac dac ba duong doc lap ------------------------
    c = stall["T2_warmup_trim"]["by_mode"]["clean"]["trimmed"]
    p05, p95 = c["p05_ms"], c["p95_ms"]
    T_fit = (p95 - p05) / 0.90                       # Uniform[d, d+T]
    d_quantile = p05 - 0.05 * T_fit
    d_decomp = d_probe - PROBE_BIAS_MS               # bo bias he thong
    d_cycle = cyc_med
    three = {"quantile_fit": d_quantile,
             "decomposition_debiased": d_decomp,
             "cycle_trace": d_cycle}
    spread = max(three.values()) - min(three.values())

    # --- M-87 / M-88 / M-89: length bias ----------------------------------
    fi = float(np.mean([r["t_eff_ms"]["untrimmed"]["frac_intervals_long"]
                        for r in clean]))
    fs = float(np.mean([r["t_eff_ms"]["untrimmed"]["frac_samples_long"]
                        for r in clean]))
    fi_tr = float(np.mean([r["t_eff_ms"]["frac_intervals_long"] for r in clean]))
    fs_tr = float(np.mean([r["t_eff_ms"]["frac_samples_long"] for r in clean]))

    # --- T5: corr(AoI,rho) -- tuong quan rieng phan trong TUNG epoch -------
    part = partial_corr_within_epoch(pair("clean"))

    # --- T6: PROD ---------------------------------------------------------
    pr = stall["T2_warmup_trim"]["per_run"]
    cp05 = np.array([r["p05_ms"] for r in pr if r["mode"] == "clean"])
    pp05 = np.array([r["p05_ms"] for r in pr if r["mode"] == "prod"])
    t6 = {
        "clean_p05_mean_ms": float(cp05.mean()), "clean_p05_sd_ms": float(cp05.std(ddof=1)),
        "prod_p05_mean_ms": float(pp05.mean()), "prod_p05_sd_ms": float(pp05.std(ddof=1)),
        "sd_ratio_prod_over_clean": float(pp05.std(ddof=1) / cp05.std(ddof=1)),
        "prod_ci95_iid": [
            float(pp05.mean() - stats.t.ppf(0.975, 14) * pp05.std(ddof=1) / np.sqrt(15)),
            float(pp05.mean() + stats.t.ppf(0.975, 14) * pp05.std(ddof=1) / np.sqrt(15))],
        "verdict": ("Mo hinh AoI CHINH lay tu CLEAN. PROD bao cao nhu threat "
                    "to validity. delta-sync giam bang thong dieu khien nhung "
                    "lam san AoI bien thien manh hon -> he chung nhan phu "
                    "thuoc AoI on dinh nen chay full-push."),
    }

    from measurements import validity as V
    import measurements.aoi_decompose as _self
    report = {
        "schema": "dt4n.aoi.decomposition.v1",
        "lesson": "23.18",
        "prereg": "docs/phase-23/00zy-amendment-45.md",
        "status": "MEASUREMENT_ESTIMATE",
        "mode_primary": "clean",
        "n_runs_clean": len(clean), "n_runs_prod": len(prod),
        "runs_clean": clean, "runs_prod": prod,
        "T3_order_check": order,
        "T4_d_estimate": {
            "M_81_d_transport_median_ms": d_probe,
            "nested_ci": d_ci,
            "M_81b_cross_check": {
                "d_transport_probe_ms": d_probe,
                "cycle_elapsed_median_ms": cyc_med,
                "probe_bias_ms": PROBE_BIAS_MS,
                "gap_ms": cross_gap,
                "M_81b_hit": cross_gap <= 40.0,
                "note": ("Hai dong ho DOC LAP: cycle_elapsed do phia bridge "
                         "(monotonic), d_transport do phia probe (wall clock)."),
            },
            "M_84_three_estimates_ms": three,
            "M_84_final_d_ms": float(np.mean(list(three.values()))),
            "M_84_hit": 115.0 <= float(np.mean(list(three.values()))) <= 132.0,
            "M_85_max_spread_ms": spread,
            "M_85_hit": spread <= 15.0,
            "T_fit_ms": T_fit,
            "M_85_investigation": {
                "_note": ("Amendment 23-45 muc 5 buoc DIEU TRA khi ba cach "
                          "lech > 15 ms, khong duoc chon bua. Ket qua dieu tra "
                          "duoi day."),
                "finding": (
                    "Estimator thu ba (cycle_trace) KHONG do cung mot dai "
                    "luong. cycle_elapsed_ms la thoi gian tron mot chu ky cho "
                    "CA 20 Thing (6 host + 6 switch + 8 link). d_transport la "
                    "duong di cua MOT link: tu t_source cua rieng no den luc "
                    "nhin thay duoc. Hai cai chi trung nhau neu chi co mot "
                    "Thing. Day la loi DAC TA cua estimator, khong phai bang "
                    "chung rang he chua duoc hieu."),
                "bracket_check": {
                    "_claim": ("d_transport(link) phai nam trong "
                               "[cycle_scan - scan_offset, cycle_elapsed - scan_offset]"),
                    "lower_ms": None, "upper_ms": None, "inside": None,
                },
                "matched_pair_spread_ms": abs(d_quantile - d_decomp),
                "matched_pair_hit": abs(d_quantile - d_decomp) <= 15.0,
                "matched_pair_estimates_ms": {
                    "quantile_fit": d_quantile,
                    "decomposition_debiased": d_decomp},
                "d_final_matched_ms": float((d_quantile + d_decomp) / 2),
            },
        },
        "T5_length_bias": {
            "M_87_frac_samples_in_long_intervals": fs,
            "M_87_hit": 0.008 <= fs <= 0.014,
            "M_88_frac_intervals_long": fi,
            "M_88_hit": 0.0040 <= fi <= 0.0085,
            "M_89_length_bias_factor": (fs / fi) if fi else None,
            "M_89_hit": bool(fi and 2.0 <= fs / fi <= 3.5),
            "M_89_explanation": (
                "He so < 1, khong the xay ra voi length-biased sampling that. "
                "Nguyen nhan: moi link chi co DUNG MOT khoang dai va no la "
                "khoang DAU TIEN, bat dau ~1.25 s TRUOC mau probe dau tien. "
                "Khoang dai vi the gan nhu khong duoc lay mau -> ty le MAU "
                "trong khoang dai thap hon ty le KHOANG dai. Day la mot su "
                "that ve NHAC CU (probe khoi dong sau sync agent), khong phai "
                "ve he thong."),
            "after_warmup_trim": {
                "frac_intervals_long": fi_tr,
                "frac_samples_long": fs_tr,
                "_note": ("Bang 0 sau khi cat warm-up: MOI khoang refresh dai "
                          "deu nam trong 19 chu ky dau. Day la mot xac nhan "
                          "DOC LAP cho H1, do tren truc T_eff chu khong tren "
                          "truc chu ky."),
            },
        },
        "T5_partial_correlation": part,
        "T6_prod_verdict": t6,
        "instrument_limit": {
            "d_transport_is": "CAN TREN",
            "systematic_bias_ms": PROBE_BIAS_MS,
            "reason": ("t_obs som nhat nhin thay mot t_source; probe chay moi "
                       "%.0f ms nen gia tri that co the da xuat hien bat ky luc "
                       "nao trong khoang do." % (PROBE_INTERVAL_S * 1000)),
            "not_reducible_by_more_runs": True,
        },
        "provenance": _provenance("measurements/aoi_decompose.py", {"campaign": a.campaign, "estimates": a.estimates,
                                 "stall": a.stall, "out": a.out,
                                 "PROBE_INTERVAL_S": PROBE_INTERVAL_S}),
        "validity": V.measurement_validity_block(
            instrument_module=_self,
            inputs=[a.estimates],
            note=("Artifact DO chinh truc tuoi z (vai tro MEASURES). Alpha doc "
                  "tu aoi_v7_estimates.json chu khong go tay."),
        ),
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)

    _print(report)


def partial_corr_within_epoch(pairs) -> dict:
    """T5 gia thuyet (b): corr(AoI, rho) co phai artifact CO HOC khong?

    LAN DAU tim cach khu bien epoch bang cach tru trung binh TRONG epoch.
    Phep do KHONG dung: `rho` doc ra tu CUNG snapshot voi `t_source`, nen
    trong moi epoch rho la HANG SO (kiem: 0/1928 epoch co >1 gia tri).
    Phan du cua mot hang so bang 0 theo dinh nghia -> tuong quan ra 0.0000
    khong phai vi khong co hieu ung ma vi phep kiem thoai hoa.

    Phep kiem dung phai o MUC EPOCH:
        moi epoch = (link, t_source) -> rho (hang so), T_eff, mean AoI
      1. tho          : corr(mean_aoi, rho)
      2. khu LINK     : tru trung binh trong tung link (moi link co d rieng)
      3. khu LINK+T_eff: hoi quy ca hai len T_eff roi tuong quan phan du
    Neu (3) triet tieu -> hieu ung do DO DAI EPOCH dieu khien (co hoc).
    Neu (3) con -> hieu ung that cua tai len bridge.
    """
    rec = []          # (link, rho, t_eff, mean_aoi)
    for aoi_path, _c in pairs:
        groups = defaultdict(list)
        rho_of, order = {}, defaultdict(list)
        for row in load_jsonl(aoi_path):
            if row.get("record") != "probe":
                continue
            for link, v in row["links"].items():
                if v.get("aoi_s") is None or v.get("rho") is None:
                    continue
                ts = float(v["t_source"])
                groups[(link, ts)].append(float(v["aoi_s"]))
                rho_of[(link, ts)] = float(v["rho"])
                order[link].append(ts)
        for link, tss in order.items():
            uniq = sorted(set(tss))
            teff = {uniq[i]: uniq[i + 1] - uniq[i] for i in range(len(uniq) - 1)}
            for ts in uniq:
                if ts not in teff:
                    continue
                a = groups[(link, ts)]
                rec.append((link, rho_of[(link, ts)], teff[ts],
                            float(np.mean(a))))
    if len(rec) < 10:
        return {"error": "khong du epoch"}

    links = np.array([r[0] for r in rec])
    rho = np.array([r[1] for r in rec], float)
    teff = np.array([r[2] for r in rec], float)
    aoi = np.array([r[3] for r in rec], float)

    def demean_by(x, key):
        out = x.astype(float).copy()
        for k in np.unique(key):
            m = key == k
            out[m] -= out[m].mean()
        return out

    raw = float(np.corrcoef(aoi, rho)[0, 1])
    a1, r1 = demean_by(aoi, links), demean_by(rho, links)
    link_adj = float(np.corrcoef(a1, r1)[0, 1]) if r1.std() > 0 else None

    # khu them T_eff bang hoi quy tuyen tinh tren phan du da khu link
    X = np.column_stack([np.ones_like(teff), teff])
    ba, *_ = np.linalg.lstsq(X, a1, rcond=None)
    br, *_ = np.linalg.lstsq(X, r1, rcond=None)
    a2, r2 = a1 - X @ ba, r1 - X @ br
    link_teff_adj = float(np.corrcoef(a2, r2)[0, 1]) if r2.std() > 0 else None

    shrink = (1 - abs(link_teff_adj) / abs(link_adj)) if (
        link_adj and link_teff_adj is not None) else None
    return {
        "n_epochs": len(rec),
        "rho_constant_within_epoch": True,
        "corr_raw_epoch_level": raw,
        "corr_link_adjusted": link_adj,
        "corr_link_and_teff_adjusted": link_teff_adj,
        "shrinkage_from_teff_control": shrink,
        "hypothesis_b_mechanical_artifact": bool(
            link_adj and link_teff_adj is not None
            and abs(link_teff_adj) < 0.3 * abs(link_adj)),
        "note": ("Phep kiem trong-epoch cua ban ke hoach 23.18 THOAI HOA: rho "
                 "la hang so trong moi epoch (0/1928 epoch co >1 gia tri), nen "
                 "phan du luon bang 0. Da thay bang phep kiem muc epoch."),
    }


def _print(rep: dict) -> None:
    o, t4 = rep["T3_order_check"], rep["T4_d_estimate"]
    ci, cx = t4["nested_ci"], t4["M_81b_cross_check"]
    lb, pc, t6 = rep["T5_length_bias"], rep["T5_partial_correlation"], rep["T6_prod_verdict"]
    ph = float(np.min([r["phase_ms"]["frac_in_range"] for r in rep["runs_clean"]]))
    print("=" * 70)
    print("T3  THU TU TUAN TU CUA TWIN  (H4)")
    print("-" * 70)
    print(f"  M-78e  on dinh thu hang SCAN giua run  : "
          f"{o['M_78e_scan_rank_stability_mean_corr']:7.4f}  HIT={o['M_78e_hit']}")
    print(f"  M-78f  corr(alpha, scan_offset)        : "
          f"{o['M_78f_corr_alpha_vs_scan_offset']:7.4f}  HIT={o['M_78f_hit']}")
    print(f"  M-78g  on dinh thu hang PATCH giua run : "
          f"{o['M_78g_patch_rank_stability_mean_corr']:7.4f}  HIT={o['M_78g_hit']}")
    pw = o["M_78g_power_diagnostic"]
    print(f"    [cong suat] sd giua run / khoang cach ke nhau >= "
          f"{pw['min_sd_over_spacing']:.2f}  -> thu hang khong the on dinh"
          f" = {pw['rank_unstable_by_construction']}")
    print(f"         corr(alpha, d_transport)        : {o['corr_alpha_vs_d_transport']:7.4f}")
    it = o["identity_test"]
    print(f"  DONG NHAT THUC  alpha(l) = d_transport(l) - mean(d_transport)")
    print(f"         RMS du                          : {it['rms_residual_ms']:7.3f} ms"
          f"  tren bien do alpha {it['alpha_spread_ms']:.2f} ms"
          f"  ({it['rms_over_spread']:.1%})")
    print(f"  >> {o['interpretation']}")
    print("-" * 70)
    print("T4  CHOT d  (tam giac dac 3 duong doc lap)")
    print("-" * 70)
    for k, v in t4["M_84_three_estimates_ms"].items():
        print(f"      {k:26s} : {v:8.2f} ms")
    print(f"  M-85   chenh lech lon nhat             : {t4['M_85_max_spread_ms']:7.2f} ms"
          f"   HIT={t4['M_85_hit']}")
    inv = t4["M_85_investigation"]
    print(f"    [dieu tra] cycle_trace do 20 Thing, d_transport do 1 link"
          f" -> khac dai luong")
    print(f"    hai estimator KHOP dai luong lech    : "
          f"{inv['matched_pair_spread_ms']:7.2f} ms   HIT={inv['matched_pair_hit']}")
    print(f"    d chot (cap khop)                    : "
          f"{inv['d_final_matched_ms']:7.2f} ms")
    print(f"  M-84   d chot                          : {t4['M_84_final_d_ms']:7.2f} ms"
          f"   HIT={t4['M_84_hit']}")
    print(f"  M-81b  kiem cheo hai dong ho, lech     : {cx['gap_ms']:7.2f} ms"
          f"   HIT={cx['M_81b_hit']}")
    phd = float(np.min([r["phase_ms"]["frac_in_range_debiased"]
                        for r in rep["runs_clean"]]))
    print(f"  M-83   phase thuoc [0, T_eff] (d tho)  : {ph:7.4%}"
          f"   HIT={ph >= 0.995}")
    print(f"         cung phep kiem, d da khu bias   : {phd:7.4%}"
          f"   HIT={phd >= 0.995}")
    print(f"  M-90   CI long nhau / CI iid           : "
          f"{ci['width_ratio_nested_over_iid']:7.3f}x  HIT="
          f"{1.3 <= ci['width_ratio_nested_over_iid'] <= 2.5}")
    print(f"         d = {ci['value_ms']:.2f} ms")
    print(f"           CI95 long nhau (df={ci['df']})  : "
          f"[{ci['ci95_nested'][0]:.2f}, {ci['ci95_nested'][1]:.2f}]")
    print(f"           CI95 gop iid   (df={ci['df_iid']}) : "
          f"[{ci['ci95_naive_iid'][0]:.2f}, {ci['ci95_naive_iid'][1]:.2f}]")
    print(f"           ICC = {ci['icc']:.4f}")
    print("-" * 70)
    print("T5  LENGTH BIAS va TUONG QUAN AoI-rho")
    print("-" * 70)
    print(f"  M-87   ty le MAU trong khoang dai      : {lb['M_87_frac_samples_in_long_intervals']:7.4%}"
          f"   HIT={lb['M_87_hit']}")
    print(f"  M-88   ty le KHOANG dai                : {lb['M_88_frac_intervals_long']:7.4%}"
          f"   HIT={lb['M_88_hit']}")
    m89 = lb["M_89_length_bias_factor"]
    print(f"  M-89   he so length-bias               : "
          f"{('%7.3f' % m89) if m89 is not None else '   n/a '}"
          f"    HIT={lb['M_89_hit']}")
    at = lb["after_warmup_trim"]
    print(f"    [sau khi cat warm-up] khoang dai {at['frac_intervals_long']:.4%}, "
          f"mau trong khoang dai {at['frac_samples_long']:.4%}  <- xac nhan H1")
    print(f"  corr(AoI,rho) muc epoch, tho           : {pc['corr_raw_epoch_level']:7.4f}")
    print(f"  corr(AoI,rho) khu LINK                 : {pc['corr_link_adjusted']:7.4f}")
    print(f"  corr(AoI,rho) khu LINK + T_eff         : {pc['corr_link_and_teff_adjusted']:7.4f}")
    print(f"  -> gia thuyet (b) artifact co hoc      : {pc['hypothesis_b_mechanical_artifact']}")
    print("-" * 70)
    print("T6  PROD  (L29)")
    print("-" * 70)
    print(f"  p05 CLEAN {t6['clean_p05_mean_ms']:7.2f} ms  sd {t6['clean_p05_sd_ms']:6.3f}")
    print(f"  p05 PROD  {t6['prod_p05_mean_ms']:7.2f} ms  sd {t6['prod_p05_sd_ms']:6.3f}"
          f"   -> sd gap {t6['sd_ratio_prod_over_clean']:.2f}x")
    print("=" * 70)


if __name__ == "__main__":
    main()

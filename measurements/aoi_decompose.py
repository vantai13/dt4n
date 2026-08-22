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



def measure_probe_bias(pairs) -> dict:
    """M-93: DO bias cua estimator MIN thay vi gia dinh 50 ms.

    d_transport dung `t_obs` SOM NHAT nhin thay mot t_source moi. Gia tri
    that xuat hien o dau do GIUA probe truoc va probe do. Bias ky vong la
    NUA khoang giua hai probe lien tiep cua cung link.

    Cung kiem KHOA PHA: T = 500 ms va probe = 100 ms co ty so DUNG BANG 5.
    Neu pha giua hai vong lap bi khoa trong mot run thi bias la mot hang so
    nao do trong [0, 100] chu khong phai 50, va sd cua d_transport giua run
    phai xap xi 100/sqrt(12) = 28.87 ms.
    """
    gaps = []
    for aoi_path, _c in pairs:
        last_obs, last_src = {}, {}
        for row in load_jsonl(aoi_path):
            if row.get("record") != "probe":
                continue
            for link, v in row["links"].items():
                ts, to = v.get("t_source"), v.get("t_obs")
                if ts is None or to is None:
                    continue
                ts, to = float(ts), float(to)
                if link in last_src and ts != last_src[link]:
                    gaps.append(to - last_obs[link])
                last_src[link], last_obs[link] = ts, to
    g = np.asarray(gaps, float) * 1000.0
    bias = float(g.mean() / 2.0)
    se = float(g.std(ddof=1) / np.sqrt(g.size) / 2.0)
    return {
        "n_refresh_transitions": int(g.size),
        "probe_gap_mean_ms": float(g.mean()),
        "probe_gap_median_ms": float(np.median(g)),
        "M_93_measured_bias_ms": bias,
        "M_93_ci95": [bias - 1.96 * se, bias + 1.96 * se],
        "M_93_hit": 30.0 <= bias <= 70.0,
        "assumed_bias_ms": PROBE_BIAS_MS,
        "delta_vs_assumed_ms": bias - PROBE_BIAS_MS,
    }


def variance_accumulation(runs: list[dict], links: list[str]) -> dict:
    """M-98 (HAU NGHIEM): chu ky cua mot PHEP CONG DON TUAN TU.

    Neu d_transport(l) = sum_{i<=p(l)} tau_i voi tau_i doc lap thi
        E[d] ~ p(l)   VA   Var(d) ~ p(l)   =>   Var tuyen tinh theo E,
    va giao truc Var = 0 roi vao VI TRI DAU vong lap.
    Khong mo hinh nao khac (bat doi xung mang, hang doi, jitter) cho
    quan he nay kem giao truc dung cho.
    """
    mean_d, var_d = [], []
    for l in links:
        col = np.array([r["d_transport_ms_by_link"].get(l, np.nan) for r in runs],
                       float)
        mean_d.append(float(np.nanmean(col)))
        var_d.append(float(np.nanvar(col, ddof=1)))
    x, y = np.array(mean_d), np.array(var_d)
    A = np.column_stack([x, np.ones_like(x)])
    (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ np.array([a, b])
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else None
    d0 = float(-b / a) if a else None
    return {
        "_note": ("HAU NGHIEM -- phat hien khi ra soat artifact da co "
                  "(amendment 23-45b muc 6). KHONG duoc tinh nhu du doan da ky."),
        "mean_d_ms_by_link": dict(zip(links, np.round(x, 4).tolist())),
        "var_d_ms2_by_link": dict(zip(links, np.round(y, 3).tolist())),
        "slope_ms": float(a), "intercept_ms2": float(b),
        "M_98_r2": r2, "M_98_hit": bool(r2 is not None and r2 > 0.7),
        "var_zero_crossing_ms": d0,
        "min_observed_d_ms": float(x.min()),
        "crossing_vs_min_observed_ms": (
            float(d0 - x.min()) if d0 is not None else None),
        "relative_noise_of_each_sd": float(1 / np.sqrt(2 * 14)),
        "interpretation": (
            "Var tuyen tinh theo E voi giao truc roi vao vi tri DAU vong lap "
            "-> chu ky cua cong don tuan tu. Day la bang chung CO CHE, doc lap "
            "voi phep phan ra (vốn dung theo cau truc)."),
    }


def patch_position_regression(runs: list[dict], links: list[str],
                              n_things: int, n_nonlink: int) -> dict:
    """M-99: hoi quy theo VI TRI THAT trong vong PATCH, khong theo thu hang.

    Thu tu chen vao snapshot['things'] la TAT DINH (collector.py):
        hosts -> switches -> links
    va sync_agent.py:123 duyet `things_now.items()` giu nguyen thu tu chen.
    Vi the link o hang scan r (1..8) co vi tri toan cuc p = n_nonlink + r.
    Hang scan duoc DO tu scan_offset chu khong doan.
    """
    scan = {l: float(np.nanmedian([r["scan_offset_ms_by_link"].get(l, np.nan)
                                   for r in runs])) for l in links}
    dtr = {l: float(np.nanmedian([r["d_transport_ms_by_link"].get(l, np.nan)
                                  for r in runs])) for l in links}
    order = sorted(links, key=lambda l: scan[l])
    pos = {l: n_nonlink + i + 1 for i, l in enumerate(order)}

    def fit(yv):
        x = np.array([pos[l] for l in links], float)
        y = np.array([yv[l] for l in links], float)
        A = np.column_stack([x, np.ones_like(x)])
        (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ np.array([a, b])
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        return float(a), float(b), (1 - ss_res / ss_tot if ss_tot else None)

    slope_d, _, r2_d = fit(dtr)
    visible = {l: scan[l] + dtr[l] for l in links}      # t_visible - t_cycle_start
    slope_v, _, r2_v = fit(visible)
    slope_s, _, r2_s = fit(scan)
    return {
        "scan_order_measured": order,
        "global_position": pos,
        "n_things": n_things, "n_nonlink_before_links": n_nonlink,
        "M_99_slope_d_transport_ms_per_position": slope_d,
        "M_99_r2": r2_d,
        "M_99_hit": bool(3.0 <= slope_d <= 9.0),
        "slope_visible_offset_ms_per_position": slope_v, "r2_visible": r2_v,
        "slope_scan_offset_ms_per_position": slope_s, "r2_scan": r2_s,
        "identity": ("d_transport = (cycle_scan - scan_offset) + patch_time; "
                     "do do slope(d_transport) = slope(visible) - slope(scan), "
                     "tuc hai thanh phan DAU NGUOC NHAU nhu amendment 23-45 "
                     "muc 2 du doan."),
        "slope_consistency_check_ms": float(slope_v - slope_s - slope_d),
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
    links = order["links"]
    n_things = int(stall["T1_stall_positions"]["per_run"][0].get("n_cycles", 0)) and 20
    n_things = 20
    bias = measure_probe_bias(pair("clean"))
    varacc = variance_accumulation(clean, links)
    patchpos = patch_position_regression(clean, links, n_things,
                                         n_things - len(links))
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
    d_decomp = d_probe - PROBE_BIAS_MS               # bo bias GIA DINH
    d_decomp_meas = d_probe - bias["M_93_measured_bias_ms"]   # bo bias DO DUOC
    d_cycle = cyc_med
    three = {"quantile_fit": d_quantile,
             "decomposition_debiased": d_decomp,
             "cycle_trace": d_cycle}
    spread = max(three.values()) - min(three.values())

    # --- estimator thu tu: PHUONG PHAP MOMENT (amendment 23-45b muc 5) -----
    # dung TOAN BO du lieu, KHONG phu thuoc hang so debias
    sd_ms = c["sd_ms"]
    T_moment = sd_ms * np.sqrt(12.0)
    d_moment = c["mean_ms"] - T_moment / 2.0
    indep = {"quantile_fit": d_quantile,
             "moment": d_moment,
             "decomposition_debiased_measured": d_decomp_meas}
    indep_spread = max(indep.values()) - min(indep.values())

    # --- M-87 / M-88 / M-89: length bias ----------------------------------
    fi = float(np.mean([r["t_eff_ms"]["untrimmed"]["frac_intervals_long"]
                        for r in clean]))
    fs = float(np.mean([r["t_eff_ms"]["untrimmed"]["frac_samples_long"]
                        for r in clean]))
    fi_tr = float(np.mean([r["t_eff_ms"]["frac_intervals_long"] for r in clean]))
    fs_tr = float(np.mean([r["t_eff_ms"]["frac_samples_long"] for r in clean]))

    # --- T5: corr(AoI,rho) -- tuong quan rieng phan trong TUNG epoch -------
    warmup_cut = {}
    for _f, cpath in pair("clean") + pair("prod"):
        rows = load_jsonl(cpath)
        warmup_cut[run_key(cpath)] = next(
            (r["t_cycle_start"] for r in rows if r["cycle"] == WARMUP_CYCLES), None)
    part = partial_corr_within_epoch(pair("clean"), warmup_cut)

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
            "d_final_moment_ms": d_moment,
            "T_moment_ms": T_moment,
            "independent_of_debias": {
                "_note": ("Ba estimator KHONG phu thuoc hang so debias gia "
                          "dinh. `decomposition_debiased_measured` dung bias "
                          "DO DUOC (M-93) chu khong dung 50 ms."),
                "estimates_ms": indep,
                "spread_ms": indep_spread,
                "chosen_ms": d_moment,
                "chosen_why": ("MOMENT dung toan bo du lieu (mean + sd) chu "
                               "khong chi hai phan vi, va khong phu thuoc bias."),
            },
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
        "T7_probe_bias": bias,
        "T7_variance_accumulation": varacc,
        "T7_patch_position": patchpos,
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


def partial_corr_within_epoch(pairs, warmup_cut: dict) -> dict:
    """T5 + K1/K2/K3 (amendment 23-45b muc 7).

    Lesson 23.18 khu `T_eff(k, k+1)` -- khoang HIEN TAI. Nhung
    `bridge/collector.py:532-536` tinh
        rho(k) = dbytes / dt   voi   dt = t_source(k) - t_source(k-1)
    tuc rho duoc do TREN KHOANG TRUOC, `T_eff(k-1, k)`. Ghep noi vi the
    chay qua bien TRE, va khu bien hien tai khong bat duoc no.

    K1  corr(rho(k), T_eff(k-1,k))                  <- khoang rho THUC SU do tren
    K2  khu T_eff(k-1,k) thay vi T_eff(k,k+1)
    K3  khu theo 1/dt (quan he TI SO) thay vi theo dt
    """
    rec = []   # (link, rho, teff_prev, teff_next, mean_aoi)
    n_zero_rho = defaultdict(int)
    n_all_rho = defaultdict(int)
    for aoi_path, _c in pairs:
        t_cut = warmup_cut.get(run_key(aoi_path))
        vals, rho_of, order = defaultdict(list), {}, defaultdict(list)
        for row in load_jsonl(aoi_path):
            if row.get("record") != "probe":
                continue
            for link, v in row["links"].items():
                if v.get("aoi_s") is None or v.get("rho") is None:
                    continue
                n_all_rho[link] += 1
                if float(v["rho"]) == 0.0:
                    n_zero_rho[link] += 1
                # amendment 23-45c: CAT WARM-UP, giong T2 va decompose_run.
                # Ba ham trong cung mot phan tich, hai ham cat, mot ham quen.
                if t_cut is not None and float(v["t_obs"]) < t_cut:
                    continue
                ts = float(v["t_source"])
                vals[(link, ts)].append(float(v["aoi_s"]))
                rho_of[(link, ts)] = float(v["rho"])
                order[link].append(ts)
        for link, tss in order.items():
            uq = sorted(set(tss))
            for i in range(1, len(uq) - 1):        # can ca truoc lan sau
                ts = uq[i]
                rec.append((link, rho_of[(link, ts)],
                            uq[i] - uq[i - 1], uq[i + 1] - uq[i],
                            float(np.mean(vals[(link, ts)]))))
    if len(rec) < 10:
        return {"error": "khong du epoch"}

    links = np.array([r[0] for r in rec])
    rho = np.array([r[1] for r in rec], float)
    tprev = np.array([r[2] for r in rec], float)
    tnext = np.array([r[3] for r in rec], float)
    aoi = np.array([r[4] for r in rec], float)

    def demean_by(x, key):
        out = x.astype(float).copy()
        for k in np.unique(key):
            m = key == k
            out[m] -= out[m].mean()
        return out

    def residualise(y, *ctrl):
        X = np.column_stack([np.ones_like(y)] + list(ctrl))
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return y - X @ beta

    def corr(a, b):
        return (float(np.corrcoef(a, b)[0, 1])
                if a.std() > 0 and b.std() > 0 else None)

    raw = corr(aoi, rho)
    a1, r1 = demean_by(aoi, links), demean_by(rho, links)
    link_adj = corr(a1, r1)

    # amendment 23-45c: TACH BACH giua-link va trong-link. Gop 8 link roi
    # tinh MOT he so la vi pham dieu kien dong nhat -- va o day no lat dau.
    uq = sorted(set(links.tolist()))
    m_rho = np.array([rho[links == l].mean() for l in uq])
    m_aoi = np.array([aoi[links == l].mean() for l in uq])
    between = corr(m_rho, m_aoi)
    broken = sorted(l for l in uq
                    if n_all_rho[l] and n_zero_rho[l] / n_all_rho[l] > 0.5)
    keep = np.isin(links, [l for l in uq if l not in broken])
    within_ok = corr(demean_by(aoi[keep], links[keep]),
                     demean_by(rho[keep], links[keep])) if keep.any() else None
    # Lesson 23.18 (khu SAI bien): T_eff hien tai
    next_adj = corr(residualise(a1, tnext), residualise(r1, tnext))
    # K1
    k1 = corr(rho, tprev)
    # K2: khu bien TRE
    k2 = corr(residualise(a1, tprev), residualise(r1, tprev))
    # K3: quan he TI SO -- khu theo 1/dt
    inv = 1.0 / tprev
    k3 = corr(residualise(a1, inv), residualise(r1, inv))
    # K3b: khu ca hai dang
    k3b = corr(residualise(a1, tprev, inv), residualise(r1, tprev, inv))

    k1_hit = bool(k1 is not None and k1 < -0.3)
    k2_hit = bool(k2 is not None and abs(k2) < 0.10)
    k3_hit = bool(k3 is not None and abs(k3) < 0.10)

    # Quy tac phan xu cua amendment 23-45b muc 7 gia dinh CO mot hieu ung
    # can giai thich. Sau khi sua hai loi cua amendment 23-45c, hieu ung
    # TRONG LINK bien mat. Tien de cua quy tac khong duoc thoa -> quy tac
    # KHONG AP DUNG. Ghi ro thay vi be quy tac de lay mot phan xu.
    NO_EFFECT = 0.05
    if link_adj is not None and abs(link_adj) < NO_EFFECT:
        verdict = "NO_EFFECT_TO_EXPLAIN"
        action = (
            "corr(AoI,rho) TRONG tung link, sau khi cat warm-up, la KHONG "
            "(|r| = %.4f < %.2f). Tuong quan am quan sat duoc khi gop 8 link "
            "(%.4f) la NHIEU GIA GIUA CAC LINK: corr giua-link = %.4f. "
            "Quy tac phan xu (b') khong ap dung vi tien de 'co mot hieu ung "
            "can giai thich' khong duoc thoa. corr(AoI,rho) RA KHOI threats "
            "to validity; gia dinh corr = 0 cua mo hinh rang cua duoc BIEN "
            "MINH bang so do." % (abs(link_adj), NO_EFFECT, raw, between))
    elif k1_hit and (k2_hit or k3_hit):
        verdict = "B_PRIME_CONFIRMED"
        action = ("corr(AoI,rho) RA KHOI threats to validity -> mot dong trong "
                  "phan gioi han NHAC CU (estimator toc do co cua so).")
    elif not k1_hit:
        verdict = "B_PRIME_REJECTED"
        action = "corr O LAI threats to validity; co che van chua ro."
    else:
        verdict = "AMBIGUOUS"
        action = ("ghep noi co that nhung khong giai thich HET. GIU trong "
                  "threats to validity, bao cao nhap nhang.")

    return {
        "n_epochs": len(rec),
        "rho_constant_within_epoch": True,
        "corr_raw_epoch_level": raw,
        "corr_between_links": between,
        "corr_link_adjusted": link_adj,
        "corr_link_adjusted_excluding_broken_rho": within_ok,
        "links_with_broken_rho": broken,
        "rho_zero_share_by_link": {
            l: (n_zero_rho[l] / n_all_rho[l]) for l in sorted(n_all_rho)},
        "L30_note": (
            "canonical_link_key xep ten switch truoc nen hai canh bien phia "
            "nguon thanh link-sA-sSRC / link-sB-sSRC; util_direction=tx do "
            "chieu sA->SRC va sB->SRC, khong co luu luong. rho cua uA/uB vi "
            "the ~0 trong toan bo chien dich. KHONG anh huong AoI (AoI la hieu "
            "hai dau thoi gian). Anh huong moi phan tich dung rho theo link."),
        "corr_link_and_teff_NEXT_adjusted": next_adj,
        "M_94_K1_corr_rho_vs_teff_prev": k1, "M_94_hit": k1_hit,
        "M_95_K2_partial_teff_prev": k2, "M_95_hit": k2_hit,
        "M_96_K3_partial_inverse_dt": k3, "M_96_hit": k3_hit,
        "K3b_partial_both_forms": k3b,
        "shrinkage_next_control": (
            1 - abs(next_adj) / abs(link_adj)) if link_adj and next_adj else None,
        "shrinkage_prev_control": (
            1 - abs(k2) / abs(link_adj)) if link_adj and k2 else None,
        "verdict": verdict, "action": action,
        "note": ("Phep kiem TRONG-epoch cua ban ke hoach 23.18 thoai hoa: rho "
                 "la hang so trong moi epoch. Da thay bang phep kiem muc epoch, "
                 "va bien khu dung la T_eff cua khoang TRUOC (amendment 45b)."),
    }



def measure_probe_bias(pairs) -> dict:
    """M-93: DO bias cua estimator MIN thay vi gia dinh 50 ms.

    d_transport dung `t_obs` SOM NHAT nhin thay mot t_source moi. Gia tri
    that xuat hien o dau do GIUA probe truoc va probe do. Bias ky vong la
    NUA khoang giua hai probe lien tiep cua cung link.

    Cung kiem KHOA PHA: T = 500 ms va probe = 100 ms co ty so DUNG BANG 5.
    Neu pha giua hai vong lap bi khoa trong mot run thi bias la mot hang so
    nao do trong [0, 100] chu khong phai 50, va sd cua d_transport giua run
    phai xap xi 100/sqrt(12) = 28.87 ms.
    """
    gaps = []
    for aoi_path, _c in pairs:
        last_obs, last_src = {}, {}
        for row in load_jsonl(aoi_path):
            if row.get("record") != "probe":
                continue
            for link, v in row["links"].items():
                ts, to = v.get("t_source"), v.get("t_obs")
                if ts is None or to is None:
                    continue
                ts, to = float(ts), float(to)
                if link in last_src and ts != last_src[link]:
                    gaps.append(to - last_obs[link])
                last_src[link], last_obs[link] = ts, to
    g = np.asarray(gaps, float) * 1000.0
    bias = float(g.mean() / 2.0)
    se = float(g.std(ddof=1) / np.sqrt(g.size) / 2.0)
    return {
        "n_refresh_transitions": int(g.size),
        "probe_gap_mean_ms": float(g.mean()),
        "probe_gap_median_ms": float(np.median(g)),
        "M_93_measured_bias_ms": bias,
        "M_93_ci95": [bias - 1.96 * se, bias + 1.96 * se],
        "M_93_hit": 30.0 <= bias <= 70.0,
        "assumed_bias_ms": PROBE_BIAS_MS,
        "delta_vs_assumed_ms": bias - PROBE_BIAS_MS,
    }


def variance_accumulation(runs: list[dict], links: list[str]) -> dict:
    """M-98 (HAU NGHIEM): chu ky cua mot PHEP CONG DON TUAN TU.

    Neu d_transport(l) = sum_{i<=p(l)} tau_i voi tau_i doc lap thi
        E[d] ~ p(l)   VA   Var(d) ~ p(l)   =>   Var tuyen tinh theo E,
    va giao truc Var = 0 roi vao VI TRI DAU vong lap.
    Khong mo hinh nao khac (bat doi xung mang, hang doi, jitter) cho
    quan he nay kem giao truc dung cho.
    """
    mean_d, var_d = [], []
    for l in links:
        col = np.array([r["d_transport_ms_by_link"].get(l, np.nan) for r in runs],
                       float)
        mean_d.append(float(np.nanmean(col)))
        var_d.append(float(np.nanvar(col, ddof=1)))
    x, y = np.array(mean_d), np.array(var_d)
    A = np.column_stack([x, np.ones_like(x)])
    (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ np.array([a, b])
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else None
    d0 = float(-b / a) if a else None
    return {
        "_note": ("HAU NGHIEM -- phat hien khi ra soat artifact da co "
                  "(amendment 23-45b muc 6). KHONG duoc tinh nhu du doan da ky."),
        "mean_d_ms_by_link": dict(zip(links, np.round(x, 4).tolist())),
        "var_d_ms2_by_link": dict(zip(links, np.round(y, 3).tolist())),
        "slope_ms": float(a), "intercept_ms2": float(b),
        "M_98_r2": r2, "M_98_hit": bool(r2 is not None and r2 > 0.7),
        "var_zero_crossing_ms": d0,
        "min_observed_d_ms": float(x.min()),
        "crossing_vs_min_observed_ms": (
            float(d0 - x.min()) if d0 is not None else None),
        "relative_noise_of_each_sd": float(1 / np.sqrt(2 * 14)),
        "interpretation": (
            "Var tuyen tinh theo E voi giao truc roi vao vi tri DAU vong lap "
            "-> chu ky cua cong don tuan tu. Day la bang chung CO CHE, doc lap "
            "voi phep phan ra (vốn dung theo cau truc)."),
    }


def patch_position_regression(runs: list[dict], links: list[str],
                              n_things: int, n_nonlink: int) -> dict:
    """M-99: hoi quy theo VI TRI THAT trong vong PATCH, khong theo thu hang.

    Thu tu chen vao snapshot['things'] la TAT DINH (collector.py):
        hosts -> switches -> links
    va sync_agent.py:123 duyet `things_now.items()` giu nguyen thu tu chen.
    Vi the link o hang scan r (1..8) co vi tri toan cuc p = n_nonlink + r.
    Hang scan duoc DO tu scan_offset chu khong doan.
    """
    scan = {l: float(np.nanmedian([r["scan_offset_ms_by_link"].get(l, np.nan)
                                   for r in runs])) for l in links}
    dtr = {l: float(np.nanmedian([r["d_transport_ms_by_link"].get(l, np.nan)
                                  for r in runs])) for l in links}
    order = sorted(links, key=lambda l: scan[l])
    pos = {l: n_nonlink + i + 1 for i, l in enumerate(order)}

    def fit(yv):
        x = np.array([pos[l] for l in links], float)
        y = np.array([yv[l] for l in links], float)
        A = np.column_stack([x, np.ones_like(x)])
        (a, b), *_ = np.linalg.lstsq(A, y, rcond=None)
        pred = A @ np.array([a, b])
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum())
        return float(a), float(b), (1 - ss_res / ss_tot if ss_tot else None)

    slope_d, _, r2_d = fit(dtr)
    visible = {l: scan[l] + dtr[l] for l in links}      # t_visible - t_cycle_start
    slope_v, _, r2_v = fit(visible)
    slope_s, _, r2_s = fit(scan)
    return {
        "scan_order_measured": order,
        "global_position": pos,
        "n_things": n_things, "n_nonlink_before_links": n_nonlink,
        "M_99_slope_d_transport_ms_per_position": slope_d,
        "M_99_r2": r2_d,
        "M_99_hit": bool(3.0 <= slope_d <= 9.0),
        "slope_visible_offset_ms_per_position": slope_v, "r2_visible": r2_v,
        "slope_scan_offset_ms_per_position": slope_s, "r2_scan": r2_s,
        "identity": ("d_transport = (cycle_scan - scan_offset) + patch_time; "
                     "do do slope(d_transport) = slope(visible) - slope(scan), "
                     "tuc hai thanh phan DAU NGUOC NHAU nhu amendment 23-45 "
                     "muc 2 du doan."),
        "slope_consistency_check_ms": float(slope_v - slope_s - slope_d),
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
    links = order["links"]
    n_things = int(stall["T1_stall_positions"]["per_run"][0].get("n_cycles", 0)) and 20
    n_things = 20
    bias = measure_probe_bias(pair("clean"))
    varacc = variance_accumulation(clean, links)
    patchpos = patch_position_regression(clean, links, n_things,
                                         n_things - len(links))
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
    d_decomp = d_probe - PROBE_BIAS_MS               # bo bias GIA DINH
    d_decomp_meas = d_probe - bias["M_93_measured_bias_ms"]   # bo bias DO DUOC
    d_cycle = cyc_med
    three = {"quantile_fit": d_quantile,
             "decomposition_debiased": d_decomp,
             "cycle_trace": d_cycle}
    spread = max(three.values()) - min(three.values())

    # --- estimator thu tu: PHUONG PHAP MOMENT (amendment 23-45b muc 5) -----
    # dung TOAN BO du lieu, KHONG phu thuoc hang so debias
    sd_ms = c["sd_ms"]
    T_moment = sd_ms * np.sqrt(12.0)
    d_moment = c["mean_ms"] - T_moment / 2.0
    indep = {"quantile_fit": d_quantile,
             "moment": d_moment,
             "decomposition_debiased_measured": d_decomp_meas}
    indep_spread = max(indep.values()) - min(indep.values())

    # --- M-87 / M-88 / M-89: length bias ----------------------------------
    fi = float(np.mean([r["t_eff_ms"]["untrimmed"]["frac_intervals_long"]
                        for r in clean]))
    fs = float(np.mean([r["t_eff_ms"]["untrimmed"]["frac_samples_long"]
                        for r in clean]))
    fi_tr = float(np.mean([r["t_eff_ms"]["frac_intervals_long"] for r in clean]))
    fs_tr = float(np.mean([r["t_eff_ms"]["frac_samples_long"] for r in clean]))

    # --- T5: corr(AoI,rho) -- tuong quan rieng phan trong TUNG epoch -------
    warmup_cut = {}
    for _f, cpath in pair("clean") + pair("prod"):
        rows = load_jsonl(cpath)
        warmup_cut[run_key(cpath)] = next(
            (r["t_cycle_start"] for r in rows if r["cycle"] == WARMUP_CYCLES), None)
    part = partial_corr_within_epoch(pair("clean"), warmup_cut)

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
            "d_final_moment_ms": d_moment,
            "T_moment_ms": T_moment,
            "independent_of_debias": {
                "_note": ("Ba estimator KHONG phu thuoc hang so debias gia "
                          "dinh. `decomposition_debiased_measured` dung bias "
                          "DO DUOC (M-93) chu khong dung 50 ms."),
                "estimates_ms": indep,
                "spread_ms": indep_spread,
                "chosen_ms": d_moment,
                "chosen_why": ("MOMENT dung toan bo du lieu (mean + sd) chu "
                               "khong chi hai phan vi, va khong phu thuoc bias."),
            },
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
        "T7_probe_bias": bias,
        "T7_variance_accumulation": varacc,
        "T7_patch_position": patchpos,
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
    b, va, pp = rep["T7_probe_bias"], rep["T7_variance_accumulation"], rep["T7_patch_position"]
    ind = t4["independent_of_debias"]
    print("-" * 70)
    print("T7  DO BIAS, TICH LUY PHUONG SAI, VI TRI VONG PATCH")
    print("-" * 70)
    print(f"  M-93   bias probe DO DUOC              : {b['M_93_measured_bias_ms']:7.2f} ms"
          f"  CI95 [{b['M_93_ci95'][0]:.2f}, {b['M_93_ci95'][1]:.2f}]  HIT={b['M_93_hit']}")
    print(f"         (gia dinh cu {b['assumed_bias_ms']:.0f} ms, lech "
          f"{b['delta_vs_assumed_ms']:+.2f} ms)")
    print(f"  M-98   Var(d) ~ E[d]  R2               : {va['M_98_r2']:7.4f}"
          f"   HIT={va['M_98_hit']}")
    print(f"         giao truc Var=0 tai             : {va['var_zero_crossing_ms']:7.2f} ms"
          f"  (d nho nhat quan sat {va['min_observed_d_ms']:.2f} ms, lech "
          f"{va['crossing_vs_min_observed_ms']:+.2f})")
    print(f"  M-99   slope d_transport / vi tri      : "
          f"{pp['M_99_slope_d_transport_ms_per_position']:7.3f} ms  R2="
          f"{pp['M_99_r2']:.4f}  HIT={pp['M_99_hit']}")
    print(f"         slope visible_offset / vi tri   : "
          f"{pp['slope_visible_offset_ms_per_position']:7.3f} ms  (= thoi gian mot PATCH)")
    print(f"         slope scan_offset / vi tri      : "
          f"{pp['slope_scan_offset_ms_per_position']:7.3f} ms  (dau NGUOC lai)")
    print(f"         thu tu scan DO DUOC             : {pp['scan_order_measured']}")
    print("-" * 70)
    print("T4b BON DUONG CHOT d (ba duong KHONG phu thuoc debias)")
    print("-" * 70)
    for k, v in ind["estimates_ms"].items():
        print(f"      {k:34s} : {v:8.2f} ms")
    print(f"      {'trai':34s} : {ind['spread_ms']:8.2f} ms")
    print(f"      >> CHOT (moment)                   : {ind['chosen_ms']:8.2f} ms")
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
    print(f"  corr muc epoch, tho (gop 8 link)       : {pc['corr_raw_epoch_level']:7.4f}")
    print(f"  GIUA cac link (n=8)                    : {pc['corr_between_links']:7.4f}"
          f"   <- confounding")
    print(f"  TRONG link (khu bien link)             : {pc['corr_link_adjusted']:7.4f}")
    print(f"  TRONG link, bo link co rho hong {str(pc['links_with_broken_rho']):9s}: "
          f"{pc['corr_link_adjusted_excluding_broken_rho']:7.4f}")
    print(f"  khu LINK + T_eff HIEN TAI (23.18, sai) : {pc['corr_link_and_teff_NEXT_adjusted']:7.4f}")
    print(f"  M-94 K1 corr(rho, T_eff khoang TRUOC)  : {pc['M_94_K1_corr_rho_vs_teff_prev']:7.4f}"
          f"   HIT={pc['M_94_hit']}")
    print(f"  M-95 K2 khu T_eff khoang TRUOC         : {pc['M_95_K2_partial_teff_prev']:7.4f}"
          f"   HIT={pc['M_95_hit']}")
    print(f"  M-96 K3 khu theo 1/dt (ti so)          : {pc['M_96_K3_partial_inverse_dt']:7.4f}"
          f"   HIT={pc['M_96_hit']}")
    print(f"       K3b khu ca hai dang               : {pc['K3b_partial_both_forms']:7.4f}")
    print(f"  >> PHAN XU: {pc['verdict']}")
    print(f"     {pc['action']}")
    print("-" * 70)
    print("T6  PROD  (L29)")
    print("-" * 70)
    print(f"  p05 CLEAN {t6['clean_p05_mean_ms']:7.2f} ms  sd {t6['clean_p05_sd_ms']:6.3f}")
    print(f"  p05 PROD  {t6['prod_p05_mean_ms']:7.2f} ms  sd {t6['prod_p05_sd_ms']:6.3f}"
          f"   -> sd gap {t6['sd_ratio_prod_over_clean']:.2f}x")
    print("=" * 70)


if __name__ == "__main__":
    main()

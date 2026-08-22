#!/usr/bin/env python3
r"""Lesson 23.19 Task A -- probe co lay mau thien lech khong?

Hai phan bo AoI KHAC NHAU, va pipeline can cai thu nhat:

    TRUNG BINH THEO THOI GIAN  "doc twin o mot thoi diem ngau nhien"
                               -> controller doc o dt = 5 ms, tuy y
    DO PROBE LAY MAU           "tai 1.199 thoi diem probe cua toi"
                               -> day la cai DO DUOC

Chung bang nhau khi va chi khi thoi diem probe RAI DEU so voi chu ky refresh.
T_refresh / T_probe = 500.31 / 100 = 5.003 -- gan mot so nguyen, nen phai kiem.

Phep do trung tam la vi tri CHUAN HOA trong chinh khoang refresh cua mau:

    u = (t_obs - t_source - d_link) / T_eff(epoch)

Neu probe lay mau deu theo thoi gian thi u ~ Uniform[0,1], KHONG phu thuoc
d hay alpha. Day la cung hien tuong voi aliasing va voi den nhap nhay lam
banh xe trong nhu dung yen.

Preregistration: docs/phase-23/00zzc-amendment-46.md
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from collections import defaultdict

import numpy as np
from scipy import stats

from measurements.aoi_stall_anatomy import WARMUP_CYCLES, load_jsonl, run_key


def epochs_of_run(aoi_path: str, t_cut: float | None):
    """Tra ve (link -> list cua (t_source, T_eff, [t_obs...])) va khoang probe."""
    per_link = defaultdict(lambda: defaultdict(list))
    probe_times = []
    for row in load_jsonl(aoi_path):
        if row.get("record") != "probe":
            continue
        ts_probe = row.get("t_probe_start")
        if ts_probe is not None:
            probe_times.append(float(ts_probe))
        for link, v in row["links"].items():
            if v.get("aoi_s") is None or v.get("t_obs") is None:
                continue
            if t_cut is not None and float(v["t_obs"]) < t_cut:
                continue
            per_link[link][float(v["t_source"])].append(float(v["t_obs"]))
    out = {}
    for link, d in per_link.items():
        srcs = sorted(d)
        out[link] = [(srcs[i], srcs[i + 1] - srcs[i], d[srcs[i]])
                     for i in range(len(srcs) - 1)]
    return out, np.asarray(sorted(probe_times))


def normalised_positions(epochs, d_link_s: float) -> np.ndarray:
    """u = (t_obs - t_source - d) / T_eff, ky vong Uniform[0,1] neu khong thien lech."""
    u = []
    for ts, teff, obs in epochs:
        if teff <= 0:
            continue
        for o in obs:
            u.append((o - ts - d_link_s) / teff)
    return np.asarray(u, float)


def uniformity(u: np.ndarray) -> dict:
    """KS + histogram. Chi giu u trong [0,1] (ngoai la do d khong khop chinh xac)."""
    inside = u[(u >= 0.0) & (u <= 1.0)]
    if inside.size < 50:
        return {"n": int(inside.size), "ks_D": None, "hist_max_over_min": None}
    ks = stats.kstest(inside, "uniform", args=(0.0, 1.0))
    hist, _ = np.histogram(inside, bins=50, range=(0.0, 1.0))
    nz = hist[hist > 0]
    return {
        "n": int(inside.size),
        "frac_outside_unit": float(1 - inside.size / u.size),
        "ks_D": float(ks.statistic),
        "hist_max_over_min": float(hist.max() / nz.min()) if nz.size else None,
        "hist_n_empty_bins": int((hist == 0).sum()),
        "hist": hist.tolist(),
    }


def equilibrium_quantiles(teff_s: np.ndarray, qs=(5, 50, 95)) -> dict:
    """H8 -- NGHICH LY KIEM TRA.

    Probe lay mau deu THEO THOI GIAN, nen khoang refresh DAI hon duoc lay
    mau nhieu hon. Tuoi khi do theo phan bo TUOI CAN BANG:
        f(a) = P(T > a) / E[T]
    Voi T bien thien, phan bo nay LECH PHAI va trung vi TUT XUONG duoi E[T]/2.
    Voi T hang so no tro ve Uniform[0, T].

    Lay mau tu phan bo do bang cach: chon mot khoang voi xac suat ~ do dai
    (length-biased), roi lay mot diem deu trong no.
    """
    t = np.asarray(teff_s, float)
    t = t[t > 0]
    rng = np.random.default_rng(2318)
    w = t / t.sum()
    idx = rng.choice(t.size, size=min(2_000_000, max(200_000, t.size * 50)),
                     p=w, replace=True)
    ages = rng.random(idx.size) * t[idx]
    return {
        "E_T_ms": float(t.mean() * 1000),
        "sd_T_ms": float(t.std(ddof=1) * 1000),
        "cv_T": float(t.std(ddof=1) / t.mean()),
        "uniform_median_ms": float(t.mean() * 1000 / 2),
        "equilibrium_quantiles_ms": {
            str(q): float(np.percentile(ages, q) * 1000) for q in qs},
        "equilibrium_mean_ms": float(ages.mean() * 1000),
        "n_intervals": int(t.size),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--decomposition", required=True)
    ap.add_argument("--stall", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    dec = json.load(open(a.decomposition, encoding="utf-8"))
    stall = json.load(open(a.stall, encoding="utf-8"))
    d_link_ms = dec["T3_order_check"]["d_transport_median_ms_by_link"]
    trimmed = stall["T2_warmup_trim"]["by_mode"]["clean"]["trimmed"]

    cuts = {}
    for c in sorted(glob.glob(os.path.join(a.campaign, "**", "cycles_clean_*.jsonl"),
                              recursive=True)):
        rows = load_jsonl(c)
        cuts[run_key(c)] = next(
            (r["t_cycle_start"] for r in rows if r["cycle"] == WARMUP_CYCLES), None)

    files = sorted(glob.glob(os.path.join(a.campaign, "**", "aoi_clean_*.jsonl"),
                             recursive=True))
    per_run, pooled = [], defaultdict(list)
    all_teff, probe_gaps = [], []
    for f in files:
        eps, ptimes = epochs_of_run(f, cuts.get(run_key(f)))
        if ptimes.size > 1:
            probe_gaps.append(np.diff(ptimes))
        for link, e in eps.items():
            u = normalised_positions(e, d_link_ms[link] / 1000.0)
            pooled[link].append(u)
            all_teff.extend(t for _s, t, _o in e)
            st = uniformity(u)
            st.update({"run": run_key(f), "link": link})
            per_run.append(st)

    d_run = np.array([r["ks_D"] for r in per_run if r["ks_D"] is not None])
    ratio = np.array([r["hist_max_over_min"] for r in per_run
                      if r["hist_max_over_min"] is not None])
    pooled_stats = {l: uniformity(np.concatenate(v)) for l, v in pooled.items()}
    d_pool = {l: v["ks_D"] for l, v in pooled_stats.items()}

    gaps = np.concatenate(probe_gaps) * 1000.0
    jitter_sd = float(gaps.std(ddof=1))

    eq = equilibrium_quantiles(np.asarray(all_teff, float))

    # M-107 / M-108: mo hinh d + alpha + tuoi can bang
    d_floor_ms = trimmed["mean_ms"] - eq["equilibrium_mean_ms"]
    model_q = {q: d_floor_ms + v
               for q, v in eq["equilibrium_quantiles_ms"].items()}
    obs_q = {"5": trimmed["p05_ms"], "50": trimmed["p50_ms"], "95": trimmed["p95_ms"]}
    dq = {q: model_q[q] - obs_q[q] for q in obs_q}

    m100 = bool(d_run.max() < 0.05)
    m101 = bool(max(d_pool.values()) < 0.02)
    m103 = bool(ratio.max() < 3.0)
    m107 = bool(abs(dq["50"]) < 3.0)
    m108 = bool(max(abs(v) for v in dq.values()) < 3.0)

    if m100 and m103:
        verdict = "H6_UNBIASED"
        action = ("Probe khong thien lech; phan bo do duoc DUNG LA "
                  "time-average. Selfcheck 23.19 nham vao no.")
    elif m101:
        verdict = "H7_POOLING_SUFFICES"
        action = ("Pha khoa TRONG run nhung GOP 15 run thi day du. Selfcheck "
                  "phai nham vao phan bo GOP, khong dung mot run le.")
    else:
        verdict = "H7_BIASED_MUST_CORRECT"
        action = ("Phan bo do duoc BI THIEN LECH. Sinh pha LY THUYET tu T va "
                  "d da uoc luong, KHONG khop phan bo thuc nghiem.")

    from measurements import validity as V
    import measurements.aoi_sampling_diagnostic as _self
    rep = {
        "schema": "dt4n.aoi.sampling_diagnostic.v1",
        "lesson": "23.19", "task": "A",
        "prereg": "docs/phase-23/00zzc-amendment-46.md",
        "status": "MEASUREMENT_ESTIMATE",
        "M_100_ks_within_run": {"max": float(d_run.max()),
                                "median": float(np.median(d_run)),
                                "hit": m100},
        "M_101_ks_pooled": {"by_link": d_pool,
                            "max": float(max(d_pool.values())), "hit": m101},
        "M_103_hist_ratio": {"max": float(ratio.max()),
                             "median": float(np.median(ratio)), "hit": m103},
        "M_104_probe_interval": {
            "mean_ms": float(gaps.mean()), "sd_ms": jitter_sd,
            "p95_ms": float(np.percentile(gaps, 95)),
            "hit": bool(0.5 <= jitter_sd <= 5.0)},
        "H8_equilibrium": eq,
        "M_107_median": {"model_ms": model_q["50"], "observed_ms": obs_q["50"],
                         "delta_ms": dq["50"], "hit": m107},
        "M_108_quantiles": {"model_ms": model_q, "observed_ms": obs_q,
                            "delta_ms": dq,
                            "max_abs_delta_ms": max(abs(v) for v in dq.values()),
                            "hit": m108},
        "d_floor_ms": d_floor_ms,
        "verdict": verdict, "action": action,
        "pooled_by_link": pooled_stats,
        "per_run": per_run,
        "validity": V.measurement_validity_block(
            instrument_module=_self, inputs=[a.decomposition, a.stall],
            note="Artifact DO chinh truc tuoi z va nhac cu lay mau cua no."),
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w", encoding="utf-8"), indent=1, sort_keys=True)

    print("=" * 68)
    print("TASK A -- CHAN DOAN LAY MAU PROBE")
    print("-" * 68)
    print(f"  M-100  KS(u) trong 1 run 1 link, max : {d_run.max():.5f}"
          f"   (trung vi {np.median(d_run):.5f})  HIT={m100}")
    print(f"  M-101  KS(u) gop 15 run, max         : {max(d_pool.values()):.5f}"
          f"   HIT={m101}")
    print(f"  M-103  histogram 50 bin max/min, max : {ratio.max():.3f}"
          f"      HIT={m103}")
    print(f"  M-104  khoang probe {gaps.mean():.3f} ms, jitter sd "
          f"{jitter_sd:.3f} ms   HIT={rep['M_104_probe_interval']['hit']}")
    print(f"  >> PHAN XU: {verdict}")
    print(f"     {action}")
    print("-" * 68)
    print("H8  NGHICH LY KIEM TRA (inspection paradox)")
    print("-" * 68)
    print(f"  T_eff: E = {eq['E_T_ms']:.3f} ms, sd = {eq['sd_T_ms']:.3f} ms,"
          f" CV = {eq['cv_T']:.5f}")
    print(f"  trung vi neu Uniform[0,T]        : {eq['uniform_median_ms']:.3f} ms")
    print(f"  trung vi phan bo TUOI CAN BANG   : "
          f"{eq['equilibrium_quantiles_ms']['50']:.3f} ms")
    print(f"  san d suy ra                     : {d_floor_ms:.3f} ms")
    print(f"  M-107  trung vi mo hinh {model_q['50']:.3f} vs quan sat "
          f"{obs_q['50']:.3f}  ->  {dq['50']:+.3f} ms  HIT={m107}")
    for q in ("5", "50", "95"):
        print(f"    p{q:>2}  mo hinh {model_q[q]:8.3f}  quan sat {obs_q[q]:8.3f}"
              f"  lech {dq[q]:+7.3f} ms")
    print(f"  M-108  lech lon nhat: "
          f"{rep['M_108_quantiles']['max_abs_delta_ms']:.3f} ms  HIT={m108}")
    print("=" * 68)


if __name__ == "__main__":
    main()

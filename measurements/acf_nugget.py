#!/usr/bin/env python3
"""Lesson 23.25d -- do nugget va thoi gian tuong quan that cua tung link."""
from __future__ import annotations

import argparse
import glob
import json
import os

import numpy as np

from measurements import validity as V
from measurements.link_corr_matrix import (
    DT_MEASURED_S, LINKS, _provenance, load_run, tau_from_meta)

FIT_LAGS = (1, 2, 3, 4, 5, 6, 8, 10, 15, 20)
PLOT_LAGS = tuple(range(21))
N_BOOT = 2000
BOOT_SEED = 23880
ACF_FIT_MIN = 0.02
EDGE_LINKS = ("uA", "uB", "vC", "vD")


def acf(x: np.ndarray, lags=PLOT_LAGS) -> np.ndarray:
    x = np.asarray(x, dtype=float) - float(np.mean(x))
    den = float(x @ x)
    if den <= 0.0:
        return np.full(len(lags), np.nan)
    return np.asarray([1.0 if lag == 0
                       else float((x[:-lag] @ x[lag:]) / den)
                       for lag in lags], dtype=float)


def fit_nugget(acf_values: np.ndarray, lags=FIT_LAGS) -> dict:
    lags_arr = np.asarray(lags, dtype=float)
    values = np.asarray(acf_values, dtype=float)
    ok = np.isfinite(values) & (values > ACF_FIT_MIN)
    if int(ok.sum()) < 3:
        return {"valid": False, "reason": "fewer_than_3_positive_fit_lags",
                "n_fit_lags": int(ok.sum())}
    slope, intercept = np.polyfit(
        lags_arr[ok] * DT_MEASURED_S, np.log(values[ok]), 1)
    signal_fraction_raw = float(np.exp(intercept))
    tau_s = float(-1.0 / slope) if slope < 0.0 else None
    valid = bool(slope < 0.0 and 0.0 < signal_fraction_raw <= 1.0)
    return {
        "valid": valid,
        "reason": ("ok" if valid else "nonnegative_slope_or_signal_outside_0_1"),
        "n_fit_lags": int(ok.sum()),
        "fit_lags_used": [int(x) for x in lags_arr[ok]],
        "slope_per_s": float(slope), "log_intercept": float(intercept),
        "signal_fraction_raw": signal_fraction_raw,
        "signal_fraction": (signal_fraction_raw if valid else None),
        "lambda_nugget": (float(1.0 - signal_fraction_raw) if valid else None),
        "tau_measured_s": tau_s,
    }


def _mean_acf(mats, link_index: int, lags) -> np.ndarray:
    curves = np.asarray([acf(X[:, link_index], lags) for X in mats])
    return np.nanmean(curves, axis=0)


def bootstrap_fit(mats, link_index: int, rng: np.random.Generator) -> dict:
    values = {"signal_fraction": [], "lambda_nugget": [], "tau_measured_s": []}
    n = len(mats)
    for _ in range(N_BOOT):
        sample = [mats[i] for i in rng.integers(0, n, size=n)]
        fit = fit_nugget(_mean_acf(sample, link_index, FIT_LAGS))
        if not fit["valid"]:
            continue
        for key in values:
            values[key].append(float(fit[key]))
    out = {"n_boot_requested": N_BOOT,
           "n_boot_valid": len(values["signal_fraction"])}
    for key, vals in values.items():
        out[key + "_ci95"] = ([float(np.percentile(vals, 2.5)),
                                float(np.percentile(vals, 97.5))]
                               if vals else None)
    return out


def measure(mats, tau_pred: dict) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    per_link = {}
    for i, link in enumerate(LINKS):
        curve = _mean_acf(mats, i, PLOT_LAGS)
        lookup = {lag: float(curve[PLOT_LAGS.index(lag)]) for lag in FIT_LAGS}
        fit = fit_nugget(np.asarray([lookup[k] for k in FIT_LAGS]))
        fit.update(bootstrap_fit(mats, i, rng))
        fit["tau_pred_s"] = float(tau_pred[link])
        fit["acf_by_lag"] = {str(k): float(v) for k, v in zip(PLOT_LAGS, curve)}
        per_link[link] = fit

    valid = all(v["valid"] for v in per_link.values())
    edge_signal = [per_link[l]["signal_fraction"] for l in EDGE_LINKS
                   if per_link[l]["signal_fraction"] is not None]
    all_signal = [v["signal_fraction"] for v in per_link.values()
                  if v["signal_fraction"] is not None]
    median_edge = float(np.median(edge_signal)) if edge_signal else None
    min_all = float(min(all_signal)) if all_signal else None
    if valid and median_edge is not None and median_edge <= 0.50:
        branch = "N_NUGGET"
    elif valid and min_all is not None and min_all >= 0.85:
        branch = "T_TAU_PRED_WRONG"
    else:
        branch = "DEFAULT_MIXED_OR_INVALID"
    return {
        "per_link": per_link,
        "adjudication": {
            "branch": branch, "all_fits_valid": bool(valid),
            "median_edge_signal_fraction": median_edge,
            "min_all_signal_fraction": min_all,
            "rules": {"N_max_median_edge_signal_fraction": 0.50,
                      "T_min_all_signal_fraction": 0.85},
        },
    }


def save_plot(result: dict, path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 4, figsize=(13, 6.5), sharex=True, sharey=True)
    t = np.asarray(PLOT_LAGS, dtype=float) * DT_MEASURED_S
    for ax, link in zip(axes.flat, LINKS):
        row = result["per_link"][link]
        curve = np.asarray([row["acf_by_lag"][str(k)] for k in PLOT_LAGS])
        ax.plot(t, curve, "o-", ms=3, lw=1.2, label="ACF measured")
        if row["valid"]:
            fit = row["signal_fraction"] * np.exp(-t / row["tau_measured_s"])
            ax.plot(t, fit, "--", lw=1.4, label="fit lag>=1")
        ax.axhline(0.0, color="0.75", lw=0.7)
        if row["valid"]:
            title = "%s: lambda=%.3f, tau=%.2fs" % (
                link, row["lambda_nugget"], row["tau_measured_s"])
        else:
            title = "%s: invalid fit" % link
        ax.set_title(title)
        ax.grid(alpha=0.25)
    axes[0, 0].legend(fontsize=8)
    for ax in axes[-1]:
        ax.set_xlabel("lag (s)")
    for ax in axes[:, 0]:
        ax.set_ylabel("ACF")
    fig.suptitle("Lesson 23.25d: empirical link ACF and nugget fit")
    fig.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--plot", required=True)
    a = ap.parse_args()

    paths = sorted(glob.glob(os.path.join(
        a.campaign, "**", "rho_measured_clean_*.csv"), recursive=True))
    mats = [load_run(p) for p in paths]
    mats = [X for X in mats if X.shape[0] >= 40]
    if not mats:
        raise SystemExit("khong tim thay run CLEAN hop le")
    result = measure(mats, tau_from_meta(a.campaign))

    import measurements.acf_nugget as _self
    report = {
        "schema": "dt4n.acf_nugget.v1", "lesson": "23.25d",
        "prereg": "docs/phase-23/A080-amendment-80.md",
        "status": "MEASUREMENT_ESTIMATE", "n_runs": len(mats),
        "locked_constants": {"DT_MEASURED_S": DT_MEASURED_S,
                             "FIT_LAGS": list(FIT_LAGS), "N_BOOT": N_BOOT,
                             "BOOT_SEED": BOOT_SEED,
                             "ACF_FIT_MIN": ACF_FIT_MIN},
        **result,
        "plot": a.plot,
        "provenance": _provenance("measurements/acf_nugget.py",
                                  {"campaign": a.campaign, "out": a.out,
                                   "plot": a.plot}),
        "validity": V.measurement_validity_block(
            instrument_module=_self, inputs=paths[:1],
            note="Do ACF/nugget tu 15 run CLEAN; khong dung AoI/SLA."),
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    save_plot(report, a.plot)

    print("%-5s %8s %8s %8s %8s %10s %9s %9s %10s" %
          ("link", "acf(1)", "acf(2)", "acf(5)", "acf(10)",
           "1-lambda", "lambda", "tau_do", "tau_pred"))
    for link in LINKS:
        row = report["per_link"][link]
        d = row["acf_by_lag"]
        tail = ("%10.4f %9.4f %9.2f" %
                (row["signal_fraction"], row["lambda_nugget"],
                 row["tau_measured_s"]) if row["valid"]
                else "%10s %9s %9s" % ("INVALID", "-", "-"))
        print("%-5s %8.4f %8.4f %8.4f %8.4f %s %10.2f" %
              (link, d["1"], d["2"], d["5"], d["10"], tail,
               row["tau_pred_s"]))
    med_edge = report["adjudication"]["median_edge_signal_fraction"]
    print("[acf_nugget] branch=%s median_edge_signal=%s plot=%s" %
          (report["adjudication"]["branch"],
           ("%.4f" % med_edge if med_edge is not None else "-"), a.plot))


if __name__ == "__main__":
    main()

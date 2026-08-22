#!/usr/bin/env python3
"""Measure sigma and decorrelation time tau from Phase 20 rho traces.

The analysis order is deliberate:

1. drop warm-up and check stationarity drift,
2. compute the sample ACF and tau at ACF = 1/e,
3. compare guarded one-piece exponential and power-law decay fits.

The Pareto-flow ACF is piecewise, so these one-piece fits are only a diagnostic.
The classifier refuses low-quality or ambiguous fits instead of reporting a
spurious ``kappa_hat``.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np

from mininet.traffic_v7 import traffic_profile
from twin import topology_v7 as T7


ACF_WINDOW_S = 60.0
DEFAULT_DECAY_WINDOWS_S = (6.0, 60.0)
DECAY_R2_FLOOR = 0.80
DECAY_RESID_RATIO = 1.0 / 3.0
DECAY_RESID_TOL = 1e-3


def drop_warmup(rho, frac: float = 0.2):
    """Drop warm-up and return ``(remaining_series, stationarity_drift)``."""
    arr = np.asarray(rho, dtype=float)
    if len(arr) == 0:
        raise ValueError("rho series is empty")
    start = int(len(arr) * float(frac))
    x = arr[start:]
    if len(x) < 4:
        raise ValueError("rho series is too short after warm-up drop")
    h = len(x) // 2
    drift = abs(float(x[:h].mean()) - float(x[h:].mean())) / (float(x.std()) + 1e-12)
    return x, drift


def stationarity(x, tau_s: Optional[float], dt_s: float):
    """Return drift and a tau-based SE scale for the two-half mean difference."""
    arr = np.asarray(x, dtype=float)
    h = len(arr) // 2
    drift = abs(float(arr[:h].mean()) - float(arr[h:].mean())) / (float(arr.std()) + 1e-12)
    if tau_s is None or tau_s <= 0.0 or not math.isfinite(float(tau_s)):
        return drift, None, False, None

    T_half_s = h * float(dt_s)
    if T_half_s <= 0.0:
        return drift, None, False, None

    se_sigma = 2.0 * math.sqrt(float(tau_s) / T_half_s)
    correlation_cycles = (2.0 * T_half_s) / float(tau_s)
    return drift, se_sigma, bool(drift <= 3.0 * se_sigma), correlation_cycles


def acf(x, max_lag: int):
    """Sample autocorrelation with ACF(0) normalized to 1.

    This uses an FFT implementation but keeps the same biased normalization as
    the direct formula in Lesson 20.1b: dot(x[:-k], x[k:]) / dot(x, x).
    """
    y = np.asarray(x, dtype=float) - float(np.mean(x))
    denom = float(np.dot(y, y))
    if denom <= 0.0:
        return np.ones(int(max_lag) + 1, dtype=float)

    n = len(y)
    size = 1 << (2 * n - 1).bit_length()
    freq = np.fft.rfft(y, size)
    corr = np.fft.irfft(freq * np.conjugate(freq), size)[: int(max_lag) + 1]
    return corr / denom


def tau_one_over_e(a, dt_s: float):
    """First lag where ACF drops below 1/e, with linear interpolation."""
    arr = np.asarray(a, dtype=float)
    thr = 1.0 / np.e
    below = np.where(arr < thr)[0]
    if len(below) == 0:
        return None
    k = int(below[0])
    if k == 0:
        return 0.0
    a0, a1 = float(arr[k - 1]), float(arr[k])
    if abs(a0 - a1) < 1e-12:
        return k * float(dt_s)
    return (k - 1 + (a0 - thr) / (a0 - a1)) * float(dt_s)


TAU_WHITE_OVER_DT = 1.0 - 1.0 / math.e


def resolution_check(tau_s, dt_s: float) -> Dict[str, object]:
    """Classify whether tau is resolved above the sampling floor."""
    if tau_s is None:
        return {"status": "TOO_SHORT", "tau_over_dt": None, "ok": False}
    ratio = float(tau_s) / float(dt_s)
    if ratio < 1.5:
        status = "RESOLUTION_FLOOR"
    elif ratio < 5.0:
        status = "UNRESOLVED"
    elif ratio < 10.0:
        status = "MARGINAL"
    else:
        status = "OK"
    return {
        "status": status,
        "tau_over_dt": float(ratio),
        "white_noise_tau_over_dt": float(TAU_WHITE_OVER_DT),
        "ok": bool(status == "OK"),
    }


def within_factor(measured, predicted, factor: float = 2.0):
    """Symmetric positive-scale comparison using log ratio."""
    if measured is None or measured <= 0 or predicted <= 0:
        return False, float("inf")
    dev = abs(math.log2(float(measured) / float(predicted)))
    return bool(dev <= math.log2(float(factor))), float(dev)


def _r2_and_slope(xx, yy) -> Tuple[float, float]:
    p = np.polyfit(xx, yy, 1)
    pred = np.polyval(p, xx)
    var = float(np.var(yy))
    if var <= 0.0:
        return 0.0, float(p[0])
    return 1.0 - float(np.var(yy - pred)) / var, float(p[0])


def classify_decay(
    r2_exp: float,
    r2_power: float,
    r2_floor: float = DECAY_R2_FLOOR,
    resid_ratio: float = DECAY_RESID_RATIO,
    resid_tol: float = DECAY_RESID_TOL,
) -> Dict[str, object]:
    """Guard one-piece ACF decay classification with fit quality checks."""
    r2e = float(r2_exp)
    r2p = float(r2_power)
    if max(r2e, r2p) < float(r2_floor):
        return {
            "decay_kind": "no_fit",
            "classification_reason": "both one-piece fits are below the R2 floor",
            "decay_r2_floor": float(r2_floor),
            "decay_resid_ratio_threshold": float(resid_ratio),
            "decay_resid_ratio_tolerance": float(resid_tol),
        }

    res_exp = max(0.0, 1.0 - r2e)
    res_power = max(0.0, 1.0 - r2p)
    threshold = float(resid_ratio) + float(resid_tol)
    if res_exp <= threshold * res_power:
        return {
            "decay_kind": "exp",
            "classification_reason": "exponential residual is decisively smaller",
            "decay_residual_exp": float(res_exp),
            "decay_residual_power": float(res_power),
            "decay_residual_ratio": None if res_power == 0.0 else float(res_exp / res_power),
            "decay_r2_floor": float(r2_floor),
            "decay_resid_ratio_threshold": float(resid_ratio),
            "decay_resid_ratio_tolerance": float(resid_tol),
        }
    if res_power <= threshold * res_exp:
        return {
            "decay_kind": "power",
            "classification_reason": "power-law residual is decisively smaller",
            "decay_residual_exp": float(res_exp),
            "decay_residual_power": float(res_power),
            "decay_residual_ratio": None if res_exp == 0.0 else float(res_power / res_exp),
            "decay_r2_floor": float(r2_floor),
            "decay_resid_ratio_threshold": float(resid_ratio),
            "decay_resid_ratio_tolerance": float(resid_tol),
        }
    return {
        "decay_kind": "ambiguous",
        "classification_reason": "one-piece fits have comparable residuals",
        "decay_residual_exp": float(res_exp),
        "decay_residual_power": float(res_power),
        "decay_residual_ratio": None
        if max(res_exp, res_power) == 0.0
        else float(min(res_exp, res_power) / max(res_exp, res_power)),
        "decay_r2_floor": float(r2_floor),
        "decay_resid_ratio_threshold": float(resid_ratio),
        "decay_resid_ratio_tolerance": float(resid_tol),
    }


def decay_shape(
    a,
    dt_s: float,
    lo: float = 0.6,
    hi: float = 0.05,
    min_points: int = 20,
    fit_window_s: Optional[float] = None,
):
    """Compare exponential and power-law ACF decay fits.

    Returns a fit dict or ``None`` when too few points lie in the requested ACF
    and physical-time range.
    """
    arr = np.asarray(a, dtype=float)
    lags = np.arange(len(arr))
    lag_s_all = lags * float(dt_s)
    m = (arr < lo) & (arr > hi) & (lags > 0)
    if fit_window_s is not None:
        m &= lag_s_all <= float(fit_window_s)
    if int(m.sum()) < int(min_points):
        return None

    lag_s = lag_s_all[m]
    log_acf = np.log(arr[m])
    r2_exp, _slope_exp = _r2_and_slope(lag_s, log_acf)
    r2_power, slope_power = _r2_and_slope(np.log(lag_s), log_acf)
    kappa_hat = 1.0 - slope_power
    hurst_hat = (3.0 - kappa_hat) / 2.0
    classification = classify_decay(r2_exp, r2_power)
    result = {
        "fit_window_s": None if fit_window_s is None else float(fit_window_s),
        "fit_lag_min_s": float(lag_s.min()),
        "fit_lag_max_s": float(lag_s.max()),
        "decay_r2_exp": float(r2_exp),
        "decay_r2_power": float(r2_power),
        "decay_fit_points": int(m.sum()),
    }
    result.update(classification)
    if result["decay_kind"] == "power":
        result["kappa_hat"] = float(kappa_hat)
        result["hurst_hat"] = float(hurst_hat)
    return result


def _window_key(window_s: float) -> str:
    if float(window_s).is_integer():
        return "%ds" % int(window_s)
    return ("%gs" % float(window_s)).replace(".", "p")


def analyse(
    rho_series,
    dt_s: float,
    label: str = "",
    warmup_frac: float = 0.2,
    max_lag: Optional[int] = None,
    acf_window_s: float = ACF_WINDOW_S,
    decay_windows_s: Iterable[float] = DEFAULT_DECAY_WINDOWS_S,
    verbose: bool = True,
):
    x, _old_drift = drop_warmup(rho_series, frac=warmup_frac)
    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")

    if max_lag is None:
        physical_lag_cap = int(float(acf_window_s) / float(dt_s))
        lag_cap = min(len(x) // 4, physical_lag_cap)
    else:
        lag_cap = int(max_lag)
    lag_cap = max(1, min(lag_cap, len(x) - 1))
    a = acf(x, max_lag=lag_cap)
    tau = tau_one_over_e(a, dt_s)
    resolution = resolution_check(tau, dt_s)
    decay_windows = sorted({float(window_s) for window_s in decay_windows_s if float(window_s) > 0.0})
    decay_fits: Dict[str, Dict[str, object]] = {}
    for window_s in decay_windows:
        fit = None
        if resolution["status"] not in {"RESOLUTION_FLOOR", "UNRESOLVED"}:
            fit = decay_shape(a, dt_s, fit_window_s=window_s)
        if fit is None:
            fit = {
                "fit_window_s": float(window_s),
                "decay_kind": "undetermined",
                "decay_fit_points": 0,
            }
        decay_fits[_window_key(window_s)] = fit

    valid_fits = [
        fit
        for fit in decay_fits.values()
        if fit.get("decay_kind") != "undetermined"
    ]
    primary_shape = max(valid_fits, key=lambda fit: float(fit["fit_window_s"])) if valid_fits else None
    drift, se_sigma, stationary, correlation_cycles = stationarity(x, tau_s=tau, dt_s=dt_s)

    result = {
        "label": label,
        "n": int(len(x)),
        "dt_s": float(dt_s),
        "kept_s": float(len(x) * dt_s),
        "rho_mean": float(x.mean()),
        "sigma": float(x.std()),
        "stationarity_drift_sigma": float(drift),
        "stationarity_se_sigma": None if se_sigma is None else float(se_sigma),
        "stationarity_assumption": "tau-based",
        "correlation_cycles": None if correlation_cycles is None else float(correlation_cycles),
        "stationary": bool(stationary),
        "tau_s": None if tau is None else float(tau),
        "tau_resolution": resolution["status"],
        "tau_over_dt": resolution["tau_over_dt"],
        "white_noise_tau_over_dt": resolution.get("white_noise_tau_over_dt"),
        "tau_resolved": bool(resolution["ok"]),
        "acf_max_lag": int(lag_cap),
        "acf_max_time_s": float(lag_cap * dt_s),
        "acf_window_s": float(acf_window_s),
        "decay_fit_windows_s": decay_windows,
        "decay_fits": decay_fits,
    }
    if primary_shape:
        result.update(
            {
                "decay_r2_exp": float(primary_shape["decay_r2_exp"]),
                "decay_r2_power": float(primary_shape["decay_r2_power"]),
                "decay_fit_points": int(primary_shape["decay_fit_points"]),
                "decay_kind": str(primary_shape["decay_kind"]),
                "decay_classification_reason": str(primary_shape["classification_reason"]),
                "decay_fit_window_s": float(primary_shape["fit_window_s"]),
                "decay_fit_lag_min_s": float(primary_shape["fit_lag_min_s"]),
                "decay_fit_lag_max_s": float(primary_shape["fit_lag_max_s"]),
            }
        )
        if primary_shape.get("decay_residual_ratio") is not None:
            result["decay_residual_ratio"] = float(primary_shape["decay_residual_ratio"])
        if primary_shape.get("decay_kind") == "power":
            result["kappa_hat"] = float(primary_shape["kappa_hat"])
            result["hurst_hat"] = float(primary_shape["hurst_hat"])
    else:
        result["decay_kind"] = "undetermined"

    if verbose:
        print_analysis(result)
    return result


def print_analysis(result: Mapping[str, object]) -> None:
    label = result.get("label") or "rho"
    print("\n=== %s ===" % label)
    print(
        "  n = %d samples, dt = %.3f ms, kept = %.1f s"
        % (
            int(result["n"]),
            float(result["dt_s"]) * 1000.0,
            int(result["n"]) * float(result["dt_s"]),
        )
    )
    print(
        "  rho_mean = %.4f   sigma = %.4f"
        % (float(result["rho_mean"]), float(result["sigma"]))
    )
    print(
        "  ACF window = %.1f s (%d lags)"
        % (float(result["acf_max_time_s"]), int(result["acf_max_lag"]))
    )
    se_sigma = result.get("stationarity_se_sigma")
    cycles = result.get("correlation_cycles")
    if se_sigma is None:
        print(
            "  drift first-half vs second-half = %.3f sigma; SE=n/a (tau unavailable)  %s"
            % (
                float(result["stationarity_drift_sigma"]),
                "NOT STATIONARY; run longer",
            )
        )
    else:
        print(
            "  drift first-half vs second-half = %.3f sigma; SE=%.3f sigma "
            "(tau-based, cycles=%.1f)  %s"
            % (
                float(result["stationarity_drift_sigma"]),
                float(se_sigma),
                float(cycles),
                "STATIONARY" if result["stationary"] else "NOT STATIONARY; run longer",
            )
        )
        if cycles is not None and float(cycles) < 30.0:
            print("  correlation cycles < 30; run longer before relying on edge tau")
    if result.get("tau_s") is None:
        print("  tau(ACF=1/e) = n/a; ACF did not drop below 1/e")
    else:
        print(
            "  tau(ACF=1/e) = %.4f s; tau/dt = %.2f -> %s"
            % (
                float(result["tau_s"]),
                float(result["tau_over_dt"]),
                str(result["tau_resolution"]),
            )
        )
        if result.get("tau_resolution") in {"RESOLUTION_FLOOR", "UNRESOLVED"}:
            print(
                "  white-noise floor is %.2f*dt; do not classify decay here"
                % float(result["white_noise_tau_over_dt"])
            )

    decay_fits = result.get("decay_fits") or {}
    if decay_fits:
        print("  decay fits:")
        for key, fit in decay_fits.items():
            if fit.get("decay_kind") == "undetermined":
                print("    %s: undetermined (%d points)" % (key, int(fit.get("decay_fit_points", 0))))
                continue
            print(
                "    %s: R2_exp = %.3f | R2_power = %.3f -> %s "
                "[fit %.2f-%.2f s, %d points]"
                % (
                    key,
                    float(fit["decay_r2_exp"]),
                    float(fit["decay_r2_power"]),
                    str(fit["decay_kind"]).upper(),
                    float(fit["fit_lag_min_s"]),
                    float(fit["fit_lag_max_s"]),
                    int(fit["decay_fit_points"]),
                )
            )
            if fit.get("decay_kind") in {"no_fit", "ambiguous"}:
                print("      %s" % str(fit.get("classification_reason")))
            if fit.get("decay_kind") == "power":
                print(
                    "      kappa_hat = %.2f   Hurst H = %.2f"
                    % (float(fit["kappa_hat"]), float(fit["hurst_hat"]))
                )
        if result.get("decay_kind") in {"power", "ambiguous", "no_fit"}:
            print("  tau is local/descriptive; one-piece decay fits are diagnostics.")


def _median_dt(rows: List[Mapping[str, str]], fallback: Optional[float]) -> float:
    values = []
    for row in rows:
        try:
            value = float(row.get("dt_s", ""))
        except (TypeError, ValueError):
            continue
        if value > 0:
            values.append(value)
    if values:
        return float(np.median(values))
    if fallback is None:
        raise ValueError("--dt is required when input has no dt_s column")
    return float(fallback)


def read_trace(path: str, dt_s: Optional[float] = None):
    """Read long or wide rho CSV.

    Long format is produced by ``mininet.run_sync_v7`` and has columns
    ``sample_index, timestamp_s, link, rho, ...``. Wide format may have one
    numeric column per link.
    """
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("%s has no rows" % path)

    if {"link", "rho"} <= set(rows[0]):
        by_link: Dict[str, List[float]] = {link: [] for link in T7.LINK_NAMES}
        for row in rows:
            link = row.get("link")
            if link not in by_link:
                continue
            by_link[link].append(float(row["rho"]))
        by_link = {link: vals for link, vals in by_link.items() if vals}
        return by_link, _median_dt(rows, dt_s)

    ignore = {"sample_index", "timestamp_s", "time_s", "t", "dt_s"}
    fields = [field for field in rows[0] if field not in ignore]
    by_link = {field: [float(row[field]) for row in rows] for field in fields}
    return by_link, _median_dt(rows, dt_s)


def compare_to_prediction(
    measured: Mapping[str, Mapping[str, object]],
    sigma_target: float,
    edge_sigma_target: Optional[float],
    kappa: float,
    size_min_kb: float,
) -> Dict[str, Dict[str, object]]:
    profile = traffic_profile(
        sigma_target=sigma_target,
        edge_sigma_target=edge_sigma_target,
        kappa=kappa,
        size_min_kb=size_min_kb,
    )
    out: Dict[str, Dict[str, object]] = {}
    for link, result in measured.items():
        cfg = profile.get(link)
        if cfg is None:
            continue
        sigma_meas = float(result["sigma"])
        tau_meas = result.get("tau_s")
        sigma_ok, sigma_log2_dev = within_factor(sigma_meas, cfg.sigma_target)
        tau_ok, tau_log2_dev = within_factor(tau_meas, cfg.tau_pred_s)
        out[link] = {
            "sigma_pred": float(cfg.sigma_target),
            "tau_pred_s": float(cfg.tau_pred_s),
            "sigma_log2_deviation": float(sigma_log2_dev),
            "tau_log2_deviation": float(tau_log2_dev),
            "sigma_within_2x": bool(sigma_ok),
            "tau_within_2x": bool(tau_ok),
            "tau_resolution": result.get("tau_resolution"),
            "tau_resolved": bool(result.get("tau_resolved")),
        }
    return out


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def parse_windows_s(text: str) -> Tuple[float, ...]:
    values = []
    for part in str(text).split(","):
        item = part.strip()
        if not item:
            continue
        value = float(item)
        if value <= 0.0:
            raise ValueError("ACF windows must be positive seconds")
        values.append(value)
    if not values:
        raise ValueError("--acf-windows must contain at least one positive value")
    return tuple(values)


def parse_args():
    p = argparse.ArgumentParser(description="Measure tau/sigma from Phase 20 rho trace")
    p.add_argument("--input", default="results/SUPERSEDED/phase-20/rho_offered.csv")
    p.add_argument("--dt", type=float, default=None)
    p.add_argument("--warmup-frac", type=float, default=0.2)
    p.add_argument("--max-lag", type=int, default=None)
    p.add_argument(
        "--acf-window-s",
        type=float,
        default=ACF_WINDOW_S,
        help="physical ACF horizon in seconds when --max-lag is not set",
    )
    p.add_argument(
        "--acf-windows",
        default=",".join("%g" % v for v in DEFAULT_DECAY_WINDOWS_S),
        help="comma-separated physical windows, in seconds, used for decay fits",
    )
    p.add_argument("--sigma-target", "--core-sigma-target", dest="sigma_target", type=float, default=0.10)
    p.add_argument("--edge-sigma-target", type=float, default=0.03)
    p.add_argument("--kappa", type=float, default=2.5)
    p.add_argument("--size-min-kb", type=float, default=20.0)
    p.add_argument("--out", default="results/SUPERSEDED/phase-20/tau_summary.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    by_link, dt_s = read_trace(args.input, dt_s=args.dt)
    decay_windows_s = parse_windows_s(args.acf_windows)
    measured = {}
    for link in T7.LINK_NAMES:
        if link not in by_link:
            continue
        measured[link] = analyse(
            by_link[link],
            dt_s=dt_s,
            label=link,
            warmup_frac=args.warmup_frac,
            max_lag=args.max_lag,
            acf_window_s=args.acf_window_s,
            decay_windows_s=decay_windows_s,
            verbose=True,
        )

    predictions = compare_to_prediction(
        measured,
        sigma_target=args.sigma_target,
        edge_sigma_target=args.edge_sigma_target,
        kappa=args.kappa,
        size_min_kb=args.size_min_kb,
    )
    print("\n=== prediction check ===")
    for link in T7.LINK_NAMES:
        if link not in predictions:
            continue
        item = predictions[link]
        print(
            "  %s: sigma |log2(m/p)|=%.2f (%s), tau |log2(m/p)|=%.2f (%s, %s)"
            % (
                link,
                float(item["sigma_log2_deviation"]),
                "OK" if item["sigma_within_2x"] else "MISS",
                float(item["tau_log2_deviation"]),
                "OK" if item["tau_within_2x"] else "MISS",
                item["tau_resolution"],
            )
        )

    write_json(
        args.out,
        {
            "input": args.input,
            "dt_s": float(dt_s),
            "warmup_frac": float(args.warmup_frac),
            "acf_window_s": float(args.acf_window_s),
            "decay_windows_s": list(decay_windows_s),
            "measured": measured,
            "prediction_check": predictions,
        },
    )
    print("\nwrote %s" % args.out)


if __name__ == "__main__":
    main()

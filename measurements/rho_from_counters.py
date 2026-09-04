#!/usr/bin/env python3
"""Recover per-window load from the intervals actually observed by a sampler."""
from __future__ import annotations

import numpy as np


def actual_sample_times(
    tick_lateness_s: np.ndarray,
    dt_s: float,
    *,
    epoch_s: float = 0.0,
) -> np.ndarray:
    """Return actual boundary instants from nominal deadlines plus lateness."""
    lateness = np.asarray(tick_lateness_s, dtype=float)
    if lateness.ndim != 1 or lateness.size < 2:
        raise ValueError("tick_lateness_s must be a series of >= 2 windows")
    if not np.isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError("dt_s must be finite and positive")
    if not np.isfinite(epoch_s):
        raise ValueError("epoch_s must be finite")
    if np.any(~np.isfinite(lateness)) or np.any(lateness < 0.0):
        raise ValueError("tick lateness must be finite and non-negative")
    nominal = epoch_s + (np.arange(lateness.size) + 1.0) * float(dt_s)
    return nominal + lateness


def rho_from_counters(
    cumulative_wire_bytes: np.ndarray,
    tick_lateness_s: np.ndarray,
    cap_bps: np.ndarray,
    dt_s: float,
) -> dict[str, np.ndarray]:
    """Normalize cumulative byte-counter increments by observed intervals.

    The counter matrix has shape ``(link, boundary)`` and uses the same
    boundary grid as ``tick_lateness_s``. The first boundary opens the first
    recoverable interval, so all returned per-window arrays have ``W-1``
    columns. Counter resets and non-monotone sample times are refused.
    """
    counters = np.asarray(cumulative_wire_bytes, dtype=float)
    capacity = np.asarray(cap_bps, dtype=float)
    if counters.ndim != 2:
        raise ValueError("cumulative_wire_bytes must be (link, window)")
    if capacity.ndim != 1 or counters.shape[0] != capacity.size:
        raise ValueError("link dimension disagrees with cap_bps")
    if np.any(~np.isfinite(counters)) or np.any(~np.isfinite(capacity)):
        raise ValueError("counters and capacities must be finite")
    if np.any(capacity <= 0.0):
        raise ValueError("capacities must be positive")

    times = actual_sample_times(tick_lateness_s, dt_s)
    if times.size != counters.shape[1]:
        raise ValueError("lateness series and counter series differ in length")
    dt_actual = np.diff(times)
    if np.any(dt_actual <= 0.0):
        raise ValueError("non-monotone sample instants: refuse rather than clip")

    delta_bits = np.diff(counters, axis=1) * 8.0
    if np.any(delta_bits < 0.0):
        raise ValueError("counter went backwards: wrap or reset, refuse")
    rho_corrected = delta_bits / (capacity[:, None] * dt_actual[None, :])
    rho_nominal = delta_bits / (capacity[:, None] * float(dt_s))
    return {
        "rho": rho_corrected,
        "rho_nominal": rho_nominal,
        "dt_actual_s": dt_actual,
        "correction_rho": rho_corrected - rho_nominal,
    }


def sampling_grid_diagnostics(
    dt_actual_s: np.ndarray, dt_s: float
) -> dict[str, float]:
    """Report observed-grid jitter that bounds corrected-series readings."""
    values = np.asarray(dt_actual_s, dtype=float)
    if values.ndim != 1 or values.size < 2:
        raise ValueError("dt_actual_s must contain at least two intervals")
    if np.any(~np.isfinite(values)) or np.any(values <= 0.0):
        raise ValueError("observed intervals must be finite and positive")
    if not np.isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError("dt_s must be finite and positive")
    relative = values / float(dt_s) - 1.0
    return {
        "dt_actual_mean_s": float(values.mean()),
        "dt_actual_sd_s": float(values.std(ddof=1)),
        "grid_jitter_relative_sd": float(relative.std(ddof=1)),
        "grid_jitter_max_abs": float(np.abs(relative).max()),
        "dt_actual_min_s": float(values.min()),
        "dt_actual_max_s": float(values.max()),
    }


def emit4_prime(
    rho_result: dict[str, np.ndarray],
    sigma_per_link: np.ndarray,
    *,
    gate_common_mode_ratio: float = 0.05,
) -> dict[str, float | str]:
    """Gate common-mode timing correction relative to designed signal SD."""
    correction = np.asarray(rho_result["correction_rho"], dtype=float)
    sigma = np.asarray(sigma_per_link, dtype=float)
    if correction.ndim != 2 or correction.shape[0] != sigma.size:
        raise ValueError("correction and sigma link dimensions disagree")
    if correction.shape[1] < 2 or np.any(~np.isfinite(correction)):
        raise ValueError("correction must contain finite window observations")
    if np.any(~np.isfinite(sigma)) or np.any(sigma <= 0.0):
        raise ValueError("sigma_per_link must be finite and positive")
    if not np.isfinite(gate_common_mode_ratio) or gate_common_mode_ratio < 0.0:
        raise ValueError("gate_common_mode_ratio must be finite and non-negative")
    common = correction.mean(axis=0)
    common_sd = float(common.std(ddof=1))
    residual = correction - common[None, :]
    ratio = common_sd / float(np.mean(sigma))
    return {
        "common_mode_sd_rho": common_sd,
        "common_mode_ratio": ratio,
        "per_link_residual_sd_rho": float(residual.std(ddof=1)),
        "gate": float(gate_common_mode_ratio),
        "verdict": "PASS" if ratio <= gate_common_mode_ratio else "FAIL",
    }

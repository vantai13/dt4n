#!/usr/bin/env python3
"""Phase G.1 packet-counter quantisation models.

This module is the single source of truth for the two mechanisms used in the
repository.  They must not be conflated:

``independent_round`` (the preregistered G.0 modulator)
    Each window rounds its requested packet count independently.  With a
    mixed fractional phase, the error is uniform on [-1/2, 1/2], hence its
    variance is 1/12 packet^2 and it is approximately white.

``cumulative_floor`` (the static cumulative pacer/counter model)
    Packet conservation couples adjacent windows.  Under independently mixed
    cumulative phases the residual is a difference of two uniforms, hence
    variance 1/6 and lag-one correlation -1/2.  With fixed CBR phase its exact
    variance is instead f(1-f), f=frac(rate*dt), and is quasi-periodic.

The explicit mode split prevents a 1/6 formula from being applied to the G.0
``round()`` pipeline, whose preregistration states "no carry accumulator".
"""
from __future__ import annotations

import math

import numpy as np


WIRE_OVERHEAD_BYTES = 42.0
WIRE_BYTES_DEFAULT = 1442.0

QUANT_VAR_PACKETS_INDEPENDENT_ROUND = 1.0 / 12.0
QUANT_ACF1_INDEPENDENT_ROUND = 0.0
QUANT_VAR_PACKETS_CUMULATIVE_MIXED = 1.0 / 6.0
QUANT_ACF1_CUMULATIVE_MIXED = -0.5


def acf1_predicted_mechanism_a(step_packets: float, *, terms: int = 256) -> float:
    """Predict lag-one rounding-error ACF for independent-window rounding.

    ``step_packets`` is the standard deviation of the target increment between
    adjacent windows, measured in packet quanta.  With mixed fractional phase,
    the rounded sawtooth has the Fourier autocorrelation

        6/pi^2 * sum(exp(-2*pi^2*k^2*step^2) / k^2, k=1..infinity).

    The result is one at zero movement, decreases monotonically, and approaches
    zero for steps large enough to mix the fractional packet phase.  In
    particular it is not generally zero for a persistent target process.
    """
    step = float(step_packets)
    if not math.isfinite(step) or step < 0.0:
        raise ValueError("step_packets must be finite and non-negative")
    if not isinstance(terms, int) or terms <= 0:
        raise ValueError("terms must be a positive integer")
    if step == 0.0:
        return 1.0
    k = np.arange(1, terms + 1, dtype=float)
    covariance = np.sum(
        np.exp(-2.0 * math.pi**2 * k * k * step * step) / (k * k)
    )
    return float(6.0 * covariance / math.pi**2)


def packet_rho_quantum(wire_bytes: float, dt_s: float, cap_bps: float) -> float:
    """Rho represented by exactly one packet in one measurement window."""
    if wire_bytes <= 0 or dt_s <= 0 or cap_bps <= 0:
        raise ValueError("wire_bytes, dt_s, and cap_bps must be positive")
    return float(wire_bytes * 8.0 / (dt_s * cap_bps))


def quant_var_rho_independent_round(
    wire_bytes: float, dt_s: float, cap_bps: float
) -> float:
    """Quantisation variance for independent per-window ``round()``."""
    q = packet_rho_quantum(wire_bytes, dt_s, cap_bps)
    return float(q * q * QUANT_VAR_PACKETS_INDEPENDENT_ROUND)


def quant_var_rho_cumulative_mixed(
    wire_bytes: float, dt_s: float, cap_bps: float
) -> float:
    """Quantisation variance for cumulative counting with mixed phase."""
    q = packet_rho_quantum(wire_bytes, dt_s, cap_bps)
    return float(q * q * QUANT_VAR_PACKETS_CUMULATIVE_MIXED)


def quant_var_rho_static(
    rate_pps: float, wire_bytes: float, dt_s: float, cap_bps: float
) -> float:
    """Exact fixed-grid CBR staircase variance, ``q^2*f*(1-f)``."""
    f = float(rate_pps * dt_s) - math.floor(float(rate_pps * dt_s))
    q = packet_rho_quantum(wire_bytes, dt_s, cap_bps)
    return float(q * q * f * (1.0 - f))


def quant_var_rho(
    wire_bytes: float, dt_s: float, cap_bps: float, *, mode: str
) -> float:
    """Dispatch a modulated quantisation model with an explicit mode."""
    if mode == "independent_round":
        return quant_var_rho_independent_round(wire_bytes, dt_s, cap_bps)
    if mode == "cumulative_mixed":
        return quant_var_rho_cumulative_mixed(wire_bytes, dt_s, cap_bps)
    raise ValueError("mode must be 'independent_round' or 'cumulative_mixed'")


def sigma_quant_floor_rho(
    wire_bytes: float, dt_s: float, cap_bps: float, *, mode: str
) -> float:
    """Standard-deviation floor in rho units for the selected mechanism."""
    return float(np.sqrt(quant_var_rho(wire_bytes, dt_s, cap_bps, mode=mode)))


def sigma_min_for_sf(
    wire_bytes: float,
    dt_s: float,
    cap_bps: float,
    *,
    sf_target: float = 0.85,
    v_path: float = 0.0,
    mode: str,
) -> float:
    """Invert ``sf=sigma^2/(sigma^2+v)`` for the chosen instrument."""
    if not 0.0 < sf_target < 1.0:
        raise ValueError("sf_target must be in (0, 1)")
    if v_path < 0.0:
        raise ValueError("v_path must be non-negative")
    v = quant_var_rho(wire_bytes, dt_s, cap_bps, mode=mode) + float(v_path)
    return float(np.sqrt(sf_target * v / (1.0 - sf_target)))


def acf(x: np.ndarray, lag: int) -> float:
    """Biased sample autocorrelation matching the Phase-G diagnostics."""
    values = np.asarray(x, dtype=float)
    if lag < 1 or lag >= values.size:
        return float("nan")
    values = values - values.mean()
    denominator = float(np.dot(values, values))
    if denominator <= 0.0:
        return float("nan")
    return float(np.dot(values[:-lag], values[lag:]) / denominator)


def _base_estimate(x: np.ndarray) -> tuple[float, float, float, float]:
    values = np.asarray(x, dtype=float)
    return (
        float(np.var(values, ddof=1)),
        acf(values, 1),
        acf(values, 2),
        acf(values, 3),
    )


def estimate_white_round(x: np.ndarray) -> dict[str, object]:
    """Separate AR(1) signal from independent-round white quantisation.

    Lags 1 and 2 identify ``phi`` and signal variance; lag 3 is held out as a
    positive control.  Invalid physical decompositions are refused, not
    clipped.
    """
    total, a1, a2, a3 = _base_estimate(x)
    out: dict[str, object] = {
        "model": "independent_round_white",
        "var_total": total,
        "acf1": a1,
        "acf2": a2,
        "acf3": a3,
        "valid": False,
        "reason": "",
    }
    if not np.isfinite(a1) or a1 <= 1e-6:
        out["reason"] = "acf1_nonpositive_no_persistent_signal"
        return out
    phi = a2 / a1
    if not 0.0 < phi < 1.0:
        out["reason"] = "phi_out_of_range(%.4f)" % phi
        return out
    sigma2 = total * a1 / phi
    noise = total - sigma2
    if sigma2 <= 0.0 or noise < -0.05 * total:
        out["reason"] = "decomposition_outside_physical_domain"
        return out
    noise = max(noise, 0.0)
    acf3_predicted = sigma2 * phi**3 / total if total > 0.0 else float("nan")
    out.update(
        {
            "phi_hat": float(phi),
            "sigma2_hat": float(sigma2),
            "sigma_hat": float(np.sqrt(sigma2)),
            "v_hat": float(noise),
            "sf_hat": float(sigma2 / total),
            "acf3_predicted": float(acf3_predicted),
            "acf3_control_error": float(abs(acf3_predicted - a3)),
            "valid": True,
        }
    )
    return out


def estimate_cumulative_ma1(x: np.ndarray) -> dict[str, object]:
    """Separate AR(1) signal from the cumulative mixed-phase MA(1) model."""
    total, a1, a2, a3 = _base_estimate(x)
    out: dict[str, object] = {
        "model": "cumulative_mixed_ma1",
        "var_total": total,
        "acf1": a1,
        "acf2": a2,
        "acf3": a3,
        "valid": False,
        "reason": "",
    }
    if not np.isfinite(a2) or a2 <= 1e-6:
        out["reason"] = "acf2_nonpositive_no_persistent_signal"
        return out
    phi = a3 / a2
    if not 0.0 < phi < 1.0:
        out["reason"] = "phi_out_of_range(%.4f)" % phi
        return out
    sigma2 = total * a2 / phi**2
    noise = total - sigma2
    if sigma2 <= 0.0 or noise < -0.05 * total:
        out["reason"] = "decomposition_outside_physical_domain"
        return out
    noise = max(noise, 0.0)
    acf1_predicted = (
        (sigma2 * phi + QUANT_ACF1_CUMULATIVE_MIXED * noise) / total
        if total > 0.0
        else float("nan")
    )
    out.update(
        {
            "phi_hat": float(phi),
            "sigma2_hat": float(sigma2),
            "sigma_hat": float(np.sqrt(sigma2)),
            "v_hat": float(noise),
            "sf_hat": float(sigma2 / total),
            "acf1_predicted": float(acf1_predicted),
            "acf1_control_error": float(abs(acf1_predicted - a1)),
            "valid": True,
        }
    )
    return out

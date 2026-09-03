#!/usr/bin/env python3
"""G-A014: certificate-renewal gates for the first physical G.3 run.

The G.1 conditional certificate expires on "pacing process changes".  The
modulated emitter replaces the static batch pacer, so the certificate does
not transfer automatically.  This module owns the three renewal gates:

    G3-V  quantization VARIANCE still equals the certified 1/12 packet^2
    G3-F  per-link sigma/quantization-floor HEADROOM still reaches 5
    G3-C  infrastructure timing correlation inside Mininet stays below 0.10

G3-Q (mechanism sign) already exists in the signed ``31-prereg-g3.md`` and is
not restated here.  Neither are the three constants these gates renew: the
1/12 packet variance, the headroom of 5, and the EMIT-3 correlation gate are
imported from the modules that own them, so a renewal gate can never drift
away from the quantity it claims to renew.

These functions are pure: they take arrays and return verdicts.  They read no
files and start no processes, so every gate is testable on synthetic data
before any network time is spent.
"""
from __future__ import annotations

import numpy as np

from tools.g0_feasibility import HEADROOM_MIN
from tools.g1_quant_model import (
    QUANT_VAR_PACKETS_INDEPENDENT_ROUND,
    WIRE_BYTES_DEFAULT,
    packet_rho_quantum as _packet_rho_quantum_scalar,
    sigma_quant_floor_rho as _sigma_quant_floor_rho_scalar,
)
from tools.g2_topology import CAP_BPS, LINKS
from tools.g3_dryrun import DT_S
from tools.g3_emitter_dryrun import (
    GATE_TIMING_CORRELATION,
    mean_correlation_then_max,
)

GATE_V_REL_ERROR = 0.15
GATE_F_HEADROOM = HEADROOM_MIN
GATE_C_CORRELATION = GATE_TIMING_CORRELATION
QUANT_MODE = "independent_round"


def packet_rho_quantum(
    cap_bps: np.ndarray = CAP_BPS,
    dt_s: float = DT_S,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
) -> np.ndarray:
    """Load contributed by exactly one packet in one measurement window."""
    capacities = np.asarray(cap_bps, dtype=float)
    if capacities.ndim != 1:
        raise ValueError("cap_bps must be one-dimensional")
    return np.asarray(
        [
            _packet_rho_quantum_scalar(wire_bytes, dt_s, float(capacity))
            for capacity in capacities
        ],
        dtype=float,
    )


def sigma_quant_floor(
    cap_bps: np.ndarray = CAP_BPS,
    dt_s: float = DT_S,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
) -> np.ndarray:
    """Independent-round quantization noise floor in rho units."""
    capacities = np.asarray(cap_bps, dtype=float)
    if capacities.ndim != 1:
        raise ValueError("cap_bps must be one-dimensional")
    return np.asarray(
        [
            _sigma_quant_floor_rho_scalar(
                wire_bytes, dt_s, float(capacity), mode=QUANT_MODE
            )
            for capacity in capacities
        ],
        dtype=float,
    )


def _check_link_window_matrix(values: np.ndarray, cap_bps: np.ndarray) -> np.ndarray:
    matrix = np.atleast_2d(np.asarray(values, dtype=float))
    if matrix.ndim != 2:
        raise ValueError("expected a (link, window) matrix")
    if matrix.shape[0] != len(np.asarray(cap_bps, dtype=float)):
        raise ValueError("first axis must be links")
    if matrix.shape[1] < 2:
        raise ValueError("need at least two windows to estimate a second moment")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("non-finite load values cannot be adjudicated")
    return matrix


def gate_g3v_quantization_variance(
    rho_target: np.ndarray,
    rho_sent: np.ndarray,
    cap_bps: np.ndarray = CAP_BPS,
    dt_s: float = DT_S,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
) -> dict[str, object]:
    """G3-V: renew the certified 1/12 packet^2 quantization variance."""
    target = _check_link_window_matrix(rho_target, cap_bps)
    sent = _check_link_window_matrix(rho_sent, cap_bps)
    if target.shape != sent.shape:
        raise ValueError("rho_target and rho_sent must have the same shape")

    quantum = packet_rho_quantum(cap_bps, dt_s, wire_bytes)
    residual_packets = (sent - target) / quantum[:, None]
    variance = residual_packets.var(axis=1, ddof=1)
    ratio = variance / QUANT_VAR_PACKETS_INDEPENDENT_ROUND
    relative_error = np.abs(ratio - 1.0)
    per_link = [
        {
            "link": LINKS[index],
            "var_packets": float(variance[index]),
            "ratio_to_one_twelfth": float(ratio[index]),
            "relative_error": float(relative_error[index]),
            "verdict": "PASS" if relative_error[index] <= GATE_V_REL_ERROR else "FAIL",
        }
        for index in range(target.shape[0])
    ]
    worst = float(np.max(relative_error))
    return {
        "id": "G3-V",
        "description": "quantization variance renews certified 1/12 packet^2",
        "value": worst,
        "gate": GATE_V_REL_ERROR,
        "verdict": "PASS" if worst <= GATE_V_REL_ERROR else "FAIL",
        "expected_var_packets": QUANT_VAR_PACKETS_INDEPENDENT_ROUND,
        "windows": int(target.shape[1]),
        "per_link": per_link,
    }


def gate_g3f_headroom(
    rho_target: np.ndarray,
    cap_bps: np.ndarray = CAP_BPS,
    dt_s: float = DT_S,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
) -> dict[str, object]:
    """G3-F: renew the per-link sigma/quantization-floor headroom of at least 5.

    It is evaluated on ``rho_target`` because a headroom loss there is a
    generator defect, not an instrument defect.
    """
    target = _check_link_window_matrix(rho_target, cap_bps)
    floor = sigma_quant_floor(cap_bps, dt_s, wire_bytes)
    sigma = target.std(axis=1, ddof=1)
    headroom = sigma / floor
    per_link = [
        {
            "link": LINKS[index],
            "sigma_measured": float(sigma[index]),
            "sigma_quant_floor": float(floor[index]),
            "headroom": float(headroom[index]),
            "verdict": "PASS" if headroom[index] >= GATE_F_HEADROOM else "FAIL",
        }
        for index in range(target.shape[0])
    ]
    worst = float(np.min(headroom))
    return {
        "id": "G3-F",
        "description": "per-link sigma/quantization-floor headroom",
        "value": worst,
        "gate": GATE_F_HEADROOM,
        "verdict": "PASS" if worst >= GATE_F_HEADROOM else "FAIL",
        "windows": int(target.shape[1]),
        "per_link": per_link,
    }


def gate_g3c_infrastructure_correlation(
    lateness_by_replicate: list[np.ndarray],
) -> dict[str, object]:
    """G3-C: repeat EMIT-3 inside Mininet with the doc-41 reduction order.

    ``lateness_by_replicate`` holds one ``(n_links, n_windows)`` array of
    per-window maximum deadline lateness for every replicate.  The reduction
    is mean-of-matrices first, pairwise maximum second; reversing that order
    would inflate the statistic through multiple comparison (G-L85).  It is
    delegated to ``tools.g3_emitter_dryrun.mean_correlation_then_max`` so the
    bench gate and the deployment gate cannot drift apart.
    """
    if not lateness_by_replicate:
        raise ValueError("G3-C needs at least one replicate")
    stacked = []
    for replicate in lateness_by_replicate:
        array = np.asarray(replicate, dtype=float)
        if array.ndim != 2 or array.shape[0] != len(LINKS):
            raise ValueError("every replicate must have shape (link, window)")
        if array.shape[1] < 2:
            raise ValueError("need at least two windows to estimate a correlation")
        if not np.all(np.isfinite(array)):
            raise ValueError("non-finite lateness cannot be adjudicated")
        if np.any(array.std(axis=1) <= 0.0):
            raise ValueError(
                "a link has zero lateness variance; correlation is undefined "
                "and must be refused rather than imputed"
            )
        stacked.append(array)
    shapes = {array.shape for array in stacked}
    if len(shapes) != 1:
        raise ValueError("every replicate must cover the same window count")
    worst, mean_matrix = mean_correlation_then_max(np.asarray(stacked))
    return {
        "id": "G3-C",
        "description": "Mininet infrastructure timing correlation (EMIT-3 repeat)",
        "value": worst,
        "gate": GATE_C_CORRELATION,
        "verdict": "PASS" if worst <= GATE_C_CORRELATION else "FAIL",
        "replicates": len(stacked),
        "windows": int(stacked[0].shape[1]),
        "reduction": "mean_of_matrices_then_pairwise_max",
        "mean_correlation_matrix": mean_matrix,
    }


def renewal_verdict(checks: list[dict[str, object]]) -> dict[str, object]:
    """Combine the renewal gates into a single certificate decision."""
    if not checks:
        raise ValueError("a certificate decision needs at least one gate")
    failed = [check["id"] for check in checks if check["verdict"] != "PASS"]
    renewed = not failed
    return {
        "certificate_renewed": renewed,
        "failed_gates": failed,
        "consequence": (
            "G.1 conditional certificate transfers to the modulated emitter"
            if renewed
            else "RECOMPUTE the G.0 feasibility grid and the G.2 a0 window "
                 "before running any second cell"
        ),
    }

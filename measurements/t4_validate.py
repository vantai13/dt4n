#!/usr/bin/env python3
"""Phase T / T.4 -- validation gates and synthetic analysis oracles.

The functions here are pure. They validate one Phase T row and provide
known-answer oracles for the analysis layer before any live Mininet run.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence

from mininet.load_spec import (
    DESIGN_CA,
    FRAME_BG,
    PROBE_PPS,
    background_pps,
    capacity_bytes_per_s,
)
from mininet.rho_schedule import ca_pooled_predicted, intensity
from mininet.rho_spec import RhoTrajectory


V_T5_MODES = ("h2", "poisson")
DEFAULT_WARMUP_S = 15.0


def _mean(xs: Sequence[float]) -> float:
    return sum(float(x) for x in xs) / len(xs)


def decompose(
    model,
    mode: str,
    bw: float,
    q: int,
    traj: RhoTrajectory,
    q_pkt_mean_ms: float,
) -> Dict[str, float]:
    """Decompose measured packet-average delay into Phase T error terms.

    ``traj`` must be the designed rho trajectory from ``rho_spec``. Do not
    replace it with rho estimated from packet counts: that creates a shared
    data-source tautology where both q_i and rho_hat come from the same
    packets, pulling ``err_qs`` spuriously toward zero.
    """
    lam = intensity(traj, bw)
    fs = [model.predict_delay(mode, bw, q, rho) for rho in traj.rho]

    w = sum(lam)
    q_psa_load = sum(l * f for l, f in zip(lam, fs)) / w
    q_psa_time = _mean(fs)
    q_ssa = model.predict_delay(mode, bw, q, _mean(traj.rho))

    var_f = sum(l * (f - q_psa_load) ** 2 for l, f in zip(lam, fs)) / w
    n_pkt = int(sum(l * traj.dt for l in lam))
    se_err_qs = math.sqrt(var_f / max(n_pkt, 1))

    return {
        "q_psa_load_ms": q_psa_load,
        "q_psa_time_ms": q_psa_time,
        "q_ssa_ms": q_ssa,
        "err_qs_ms": float(q_pkt_mean_ms) - q_psa_load,
        "err_jensen_ms": q_psa_time - q_ssa,
        "d_sampling_ms": q_psa_load - q_psa_time,
        "err_total_ms": float(q_pkt_mean_ms) - q_ssa,
        "se_err_qs_ms": se_err_qs,
        "n_pkt": n_pkt,
    }


def classify_err_qs(err_qs_ms: float, sigma_ref_ms: float, se_ms: float) -> str:
    """Classify ``err_qs`` with both the T6 band and the RT8 resolution floor."""
    err = abs(float(err_qs_ms))
    if err < 2.0 * float(se_ms):
        return "khong_phan_biet_duoc_o_phan_giai_nay"

    ratio = err / max(float(sigma_ref_ms), 1e-9)
    if ratio < 0.10:
        return "bo_qua_duoc"
    if ratio <= 1.00:
        return "cong_vao_band_21R"
    return "quasi_static_khong_dung"


def rho_bias_sd(
    mode: str,
    rho_bar: float,
    bw_mbps: float,
    warm_s: float,
    meas_s: float,
    probe_pps: float = PROBE_PPS,
) -> float:
    """Expected sd of ``rho_bias`` from renewal variation at warm-up.

    The Phase T schedule uses all packets generated for ``[0, duration]``, so
    the final count is pinned by construction. The count before warm-up is not
    pinned; for a renewal process, ``sd(N(u)-u) = c_a * sqrt(u)`` in operational
    time. That irreducible boundary variation is the noise floor for V-T6b.
    """
    c_a = DESIGN_CA.get(str(mode))
    if c_a is None:
        return float("nan")
    warm = float(warm_s)
    meas = float(meas_s)
    if warm < 0.0 or meas <= 0.0:
        return float("nan")
    lam = background_pps(float(rho_bar), float(bw_mbps), float(probe_pps))
    u = max(lam * warm, 0.0)
    return (FRAME_BG / capacity_bytes_per_s(float(bw_mbps))) * math.sqrt(
        float(c_a) * float(c_a) * u + 1.0
    ) / meas


def gate_rho_bias_aggregate(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Aggregate V-T6b gate: under pure renewal noise, z should look N(0, 1)."""
    z = [
        float(row["rho_bias_z"])
        for row in rows
        if "rho_bias_z" in row and math.isfinite(float(row["rho_bias_z"]))
    ]
    n = len(z)
    if n == 0:
        return {
            "n": 0,
            "mean_z": float("nan"),
            "sd_z": float("nan"),
            "pass_mean": False,
            "pass_sd": False,
        }

    mean_z = _mean(z)
    sd_z = math.sqrt(sum((x - mean_z) ** 2 for x in z) / n)
    return {
        "n": n,
        "mean_z": mean_z,
        "sd_z": sd_z,
        "pass_mean": abs(mean_z) < 3.0 / math.sqrt(n),
        "pass_sd": 0.6 < sd_z < 1.6 if n > 1 else False,
    }


def oracle_quasistatic(
    model,
    mode: str,
    bw: float,
    q: int,
    traj: RhoTrajectory,
    send_times: Sequence[float],
) -> float:
    """Oracle 1: exact quasi-static system, q_i = f(rho(t_i))."""
    n = len(traj.rho)
    vals: List[float] = []
    for t in send_times:
        k = min(max(int(float(t) / traj.dt), 0), n - 1)
        vals.append(model.predict_delay(mode, bw, q, traj.rho[k]))
    return _mean(vals)


def oracle_frozen(
    model,
    mode: str,
    bw: float,
    q: int,
    traj: RhoTrajectory,
    send_times: Sequence[float],
) -> float:
    """Oracle 2: fully inert system, q_i = f(mean(rho))."""
    del send_times
    return model.predict_delay(mode, bw, q, _mean(traj.rho))


def gate_row(
    row: Dict[str, object],
    traj: RhoTrajectory,
    sched,
    model,
    sigma_ref_ms: float,
) -> Dict[str, bool]:
    """Evaluate software and operational gates for one Phase T row."""
    del model, sigma_ref_ms
    mode = str(row["mode"])
    bw = float(row["bw"])
    c_design = DESIGN_CA.get(mode)
    lam = intensity(traj, bw)
    duration_s = float(row.get("duration_s", traj.duration_s))
    warmup_s = float(row.get("warmup_s", min(DEFAULT_WARMUP_S, duration_s / 2.0)))
    meas_s = float(row.get("meas_s", max(duration_s - warmup_s, 1e-9)))
    rho_bar = float(row.get("rho_bar", _mean(traj.rho)))
    bias_sd = rho_bias_sd(mode, rho_bar, bw, warmup_s, meas_s)
    rho_bias = float(row["rho_bias"])
    row["rho_bias_sd_pred"] = bias_sd
    row["rho_bias_z"] = rho_bias / bias_sd if bias_sd > 0.0 else float("nan")

    out = {
        "V-T0_digest_khop": row["trajectory_digest"] == traj.digest(),
        "V-T3_clamp": traj.clamp_ratio < 0.01,
        "V-T6a_rate_ratio": abs(sched.rate_ratio() - 1.0) < 0.001,
        "V-T6b_rho_bias": math.isfinite(bias_sd) and abs(rho_bias) < 3.0 * bias_sd,
        "A5-7_socket_drops": int(row["socket_drops"]) == 0,
        "A5-7_n_foreign": int(row["n_foreign"]) == 0,
        "A5-7_n_late": float(row["n_late_ratio"]) < 0.001,
    }

    if c_design is not None:
        out["V-T4a_ca_operational"] = (
            abs(sched.ca_operational() - c_design) < 0.02
        )
        pred = ca_pooled_predicted(lam, c_design)
        if pred > 0.005:
            out["V-T4b_ca_pooled"] = abs(sched.ca_pooled() / pred - 1.0) < 0.05
    return out

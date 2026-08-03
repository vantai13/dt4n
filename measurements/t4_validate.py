#!/usr/bin/env python3
"""Phase T / T.4 -- validation gates and synthetic analysis oracles.

The functions here are pure. They validate one Phase T row and provide
known-answer oracles for the analysis layer before any live Mininet run.
"""

from __future__ import annotations

from functools import lru_cache
import math
from typing import Dict, List, Optional, Sequence, Tuple

from mininet.load_spec import (
    DESIGN_CA,
    FRAME_BG,
    PROBE_PPS,
    background_pps,
    build_schedule,
    capacity_bytes_per_s,
    schedule_digest,
)
from mininet.rho_schedule import ca_pooled_predicted, intensity
from mininet.rho_spec import RhoTrajectory


V_T5_MODES = ("h2", "poisson")
DEFAULT_WARMUP_S = 15.0
CA_OPERATIONAL_REF_GAPS = 400_000
PhaseLQRefs = Dict[Tuple[str, float], Dict[str, float]]
PhaseLSeedRefs = Dict[Tuple[str, float, int], Dict[str, object]]


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


@lru_cache(maxsize=None)
def _ca_reference_moments(mode: str, n_ref: int = CA_OPERATIONAL_REF_GAPS):
    """Return (c_a, skewness, excess kurtosis) for the Phase L gap generator."""
    gaps = build_schedule(str(mode), int(n_ref), 1.0, 7)
    mean = _mean(gaps)
    centered = [float(x) - mean for x in gaps]
    var = sum(x * x for x in centered) / len(centered)
    sd = math.sqrt(var)
    if sd <= 0.0 or mean <= 0.0:
        return 0.0, 0.0, 0.0
    skew = sum(x ** 3 for x in centered) / len(centered) / (sd ** 3)
    excess_kurt = sum(x ** 4 for x in centered) / len(centered) / (sd ** 4) - 3.0
    return sd / mean, skew, excess_kurt


@lru_cache(maxsize=None)
def ca_operational_se(
    mode: str,
    n_gaps: int,
    n_ref: int = CA_OPERATIONAL_REF_GAPS,
) -> float:
    """Expected SE of the operational ``c_a`` estimate via the delta method."""
    n = int(n_gaps)
    if n <= 1:
        return float("nan")
    c_a, skew, excess_kurt = _ca_reference_moments(str(mode), int(n_ref))
    if c_a <= 0.0:
        return 0.0
    var = (c_a * c_a / n) * (
        (excess_kurt + 2.0) / 4.0 + c_a * c_a - c_a * skew
    )
    return math.sqrt(max(var, 0.0))


def ca_operational_threshold(
    mode: str,
    n_gaps: int,
    k: float = 4.0,
    floor: float = 0.005,
) -> float:
    """V-T4a threshold: noise-scaled, with a small floor for CBR jitter."""
    se = ca_operational_se(str(mode), int(n_gaps))
    if not math.isfinite(se):
        return float("nan")
    return max(float(k) * se, float(floor))


def gate_vt5a_delegation(
    row: Dict[str, object],
    traj: RhoTrajectory,
    probe_pps: float = PROBE_PPS,
) -> Optional[bool]:
    """V-T5a: sigma=0 h2/poisson schedules must delegate to Phase L exactly.

    CBR is skipped because the constant schedule is not diagnostic for the
    normalization path; that limitation is recorded in the Phase T amendments.
    """
    mode = str(row["mode"])
    if mode not in V_T5_MODES:
        return None
    if getattr(traj, "kind", None) != "const":
        return None

    rho_bar = float(row.get("rho_bar", row.get("rho", traj.rho[0])))
    bw = float(row["bw"])
    duration_s = float(row.get("duration_s", traj.duration_s))
    pps = background_pps(rho_bar, bw, float(probe_pps))
    n_bg = max(1, int(pps * duration_s))
    want = schedule_digest(build_schedule(mode, n_bg, 1.0 / pps, int(row["seed"])))
    return str(row["schedule_digest"]) == want


def phase_l_q_refs(
    rows: Sequence[Dict[str, object]],
    bw: float,
    q: int,
    probe_pps: float = PROBE_PPS,
) -> PhaseLQRefs:
    """Return Phase L q_mean reference moments keyed by (mode, rho)."""
    grouped: Dict[Tuple[str, float], List[float]] = {}
    for row in rows:
        if row.get("gate_fail"):
            continue
        if "q_mean_ms" not in row:
            continue
        if abs(float(row.get("bw", float("nan"))) - float(bw)) > 1e-9:
            continue
        if int(row.get("q", -1)) != int(q):
            continue
        if abs(float(row.get("probe_pps", probe_pps)) - float(probe_pps)) > 1e-9:
            continue
        mode = str(row["mode"])
        if mode not in DESIGN_CA:
            continue
        key = (mode, round(float(row["rho"]), 6))
        grouped.setdefault(key, []).append(float(row["q_mean_ms"]))

    refs: PhaseLQRefs = {}
    for key, values in grouped.items():
        mean = _mean(values)
        if len(values) > 1:
            var = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
            sd = math.sqrt(var)
        else:
            sd = 0.0
        refs[key] = {"mean_ms": mean, "sd_ms": sd, "n": float(len(values))}
    return refs


def phase_l_seed_refs(
    rows: Sequence[Dict[str, object]],
    bw: float,
    q: int,
    probe_pps: float = PROBE_PPS,
) -> PhaseLSeedRefs:
    """Return same-seed Phase L references keyed by (mode, rho, seed)."""
    refs: PhaseLSeedRefs = {}
    for row in rows:
        if row.get("gate_fail"):
            continue
        if "q_mean_ms" not in row:
            continue
        if abs(float(row.get("bw", float("nan"))) - float(bw)) > 1e-9:
            continue
        if int(row.get("q", -1)) != int(q):
            continue
        if abs(float(row.get("probe_pps", probe_pps)) - float(probe_pps)) > 1e-9:
            continue
        mode = str(row["mode"])
        if mode not in DESIGN_CA:
            continue
        key = (mode, round(float(row["rho"]), 6), int(row["seed"]))
        refs[key] = {
            "q_mean_ms": float(row["q_mean_ms"]),
            "schedule_digest": str(row.get("schedule_digest", "")),
        }
    return refs


def gate_vt5b_q_matches_phase_l(
    row: Dict[str, object],
    phase_l_ref: PhaseLQRefs,
) -> Optional[Dict[str, float]]:
    """Legacy V-T5b diagnostic: expose z for aggregate gate, not per-row fail."""
    if "q_mean_ms" not in row:
        return None
    key = (str(row["mode"]), round(float(row.get("rho_bar", row.get("rho"))), 6))
    ref = phase_l_ref.get(key)
    if ref is None:
        return None

    q_mean = float(row["q_mean_ms"])
    ref_mean = float(ref["mean_ms"])
    ref_sd = float(ref["sd_ms"])
    z = (q_mean - ref_mean) / max(ref_sd, 1e-9)
    return {
        "z": z,
        "ref_n": float(ref["n"]),
    }


def gate_vt5a_same_seed(
    row: Dict[str, object],
    phase_l_seed_ref: PhaseLSeedRefs,
) -> Optional[bool]:
    """V-T5a': same-seed controls must match Phase L schedule digest."""
    mode = str(row["mode"])
    if mode not in V_T5_MODES:
        return None
    key = (mode, round(float(row.get("rho_bar", row.get("rho"))), 6), int(row["seed"]))
    ref = phase_l_seed_ref.get(key)
    if ref is None:
        return None
    return str(row["schedule_digest"]) == str(ref.get("schedule_digest", ""))


def vt5b_same_seed_row(
    row: Dict[str, object],
    phase_l_seed_ref: PhaseLSeedRefs,
) -> Optional[Dict[str, float | bool]]:
    """V-T5b': same-seed ratio r_i = q_T/q_L - 1; cbr@0.98 is descriptive."""
    if "q_mean_ms" not in row:
        return None
    key = (
        str(row["mode"]),
        round(float(row.get("rho_bar", row.get("rho"))), 6),
        int(row["seed"]),
    )
    ref = phase_l_seed_ref.get(key)
    if ref is None:
        return None
    q_ref = float(ref["q_mean_ms"])
    rel = float(row["q_mean_ms"]) / q_ref - 1.0 if q_ref != 0.0 else float("inf")
    exempt = str(row["mode"]) == "cbr" and abs(float(row.get("rho_bar", 0.0)) - 0.98) < 1e-9
    return {
        "rel": rel,
        "gate_exempt": bool(exempt),
    }


def gate_vt5b_z_aggregate(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Legacy 105s V-T5b aggregate z gate using all z values."""
    return gate_aggregate_z(rows, "vt5b_z", group_by=None)


def gate_vt5b_same_seed_aggregate(rows: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """V-T5b' aggregate gate; excludes cbr@0.98 critical-region rows."""
    rels = [
        float(row["vt5b_same_seed_rel"])
        for row in rows
        if "vt5b_same_seed_rel" in row
        and not bool(row.get("vt5b_same_seed_gate_exempt", False))
        and math.isfinite(float(row["vt5b_same_seed_rel"]))
    ]
    if not rels:
        return {
            "n": 0,
            "mean_rel": float("nan"),
            "sd_rel": float("nan"),
            "pass_mean": False,
            "pass_sd": False,
            "pass": False,
        }
    mean = _mean(rels)
    sd = math.sqrt(sum((x - mean) ** 2 for x in rels) / len(rels))
    pass_mean = abs(mean) < 0.005
    pass_sd = sd < 0.010
    return {
        "n": len(rels),
        "mean_rel": mean,
        "sd_rel": sd,
        "pass_mean": pass_mean,
        "pass_sd": pass_sd,
        "pass": bool(pass_mean and pass_sd),
    }


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
    group_by = "seed" if any("seed" in row for row in rows) else None
    return gate_aggregate_z(rows, "rho_bias_z", group_by=group_by)


def gate_aggregate_z(
    rows: Sequence[Dict[str, object]],
    key: str,
    group_by: Optional[str] = "seed",
) -> Dict[str, object]:
    """Aggregate z gate with a design-correlation-aware effective N."""
    z = [
        float(row[key])
        for row in rows
        if key in row and math.isfinite(float(row[key]))
    ]
    n = len(z)
    if n == 0:
        return {
            "n": 0,
            "n_eff": 0,
            "mean_z": float("nan"),
            "sd_z": float("nan"),
            "pass_mean": False,
            "pass_sd": False,
            "sd_between": float("nan"),
            "sd_within": float("nan"),
        }

    mean_z = _mean(z)
    sd_z = math.sqrt(sum((x - mean_z) ** 2 for x in z) / n)
    n_eff = n
    sd_between = float("nan")
    sd_within = float("nan")
    if group_by is not None:
        by: Dict[object, List[float]] = {}
        for row in rows:
            if key not in row or not math.isfinite(float(row[key])):
                continue
            by.setdefault(row.get(group_by), []).append(float(row[key]))
        means = [_mean(values) for values in by.values()]
        if len(means) > 1:
            m_between = _mean(means)
            sd_between = math.sqrt(
                sum((x - m_between) ** 2 for x in means) / len(means)
            )
        within = []
        for values in by.values():
            if len(values) > 1:
                m = _mean(values)
                within.append(math.sqrt(sum((x - m) ** 2 for x in values) / len(values)))
        sd_within = _mean(within) if within else 0.0
        if by and sd_between > 1.5 * sd_within:
            n_eff = len(by)

    return {
        "n": n,
        "n_eff": n_eff,
        "mean_z": mean_z,
        "sd_z": sd_z,
        "pass_mean": abs(mean_z) < 3.0 / math.sqrt(max(n_eff, 1)),
        "pass_sd": 0.6 < sd_z < 1.6 if n > 1 else False,
        "sd_between": sd_between,
        "sd_within": sd_within,
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
    phase_l_ref: Optional[PhaseLQRefs] = None,
    phase_l_seed_ref: Optional[PhaseLSeedRefs] = None,
) -> Dict[str, bool]:
    """Evaluate software and operational gates for one Phase T row."""
    del model, sigma_ref_ms
    mode = str(row["mode"])
    bw = float(row["bw"])
    c_design = DESIGN_CA.get(mode)
    lam = intensity(traj, bw)
    ca_op = sched.ca_operational()
    n_ca_gaps = max(len(getattr(sched, "send_times", [])) - 1, 1)
    ca_se = ca_operational_se(mode, n_ca_gaps)
    ca_thr = ca_operational_threshold(mode, n_ca_gaps)
    row["ca_operational"] = ca_op
    row["ca_operational_se"] = ca_se
    row["ca_operational_thr"] = ca_thr
    row["ca_operational_z"] = (
        (ca_op - float(c_design)) / max(ca_thr / 4.0, 1e-12)
        if c_design is not None and math.isfinite(ca_thr)
        else float("nan")
    )
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
        "A5-7_n_late": float(row["n_late_ratio"]) < 0.01,
        "A5-7_max_late": float(row.get("max_late_ms", 0.0)) < 100.0,
    }

    if c_design is not None:
        out["V-T4a_ca_operational"] = math.isfinite(ca_thr) and (
            abs(ca_op - c_design) < ca_thr
        )
        pred = ca_pooled_predicted(lam, c_design)
        if pred > 0.005:
            out["V-T4b_ca_pooled"] = abs(sched.ca_pooled() / pred - 1.0) < 0.05

    if str(row.get("block", "")).startswith("C") and float(row.get("a", 0.0)) == 0.0:
        vt5a = gate_vt5a_delegation(row, traj)
        if vt5a is not None:
            row["vt5a_delegation"] = bool(vt5a)
            out["V-T5a_delegation"] = bool(vt5a)
        if phase_l_ref is not None:
            vt5b = gate_vt5b_q_matches_phase_l(row, phase_l_ref)
            if vt5b is not None:
                row["vt5b_z"] = float(vt5b["z"])
                row["vt5b_ref_n"] = int(vt5b["ref_n"])
        if phase_l_seed_ref is not None:
            vt5a_same = gate_vt5a_same_seed(row, phase_l_seed_ref)
            if vt5a_same is not None:
                row["vt5a_phase_l_digest"] = bool(vt5a_same)
                out["V-T5a_phase_l_digest"] = bool(vt5a_same)
            vt5b_same = vt5b_same_seed_row(row, phase_l_seed_ref)
            if vt5b_same is not None:
                row["vt5b_same_seed_rel"] = float(vt5b_same["rel"])
                row["vt5b_same_seed_gate_exempt"] = bool(vt5b_same["gate_exempt"])
    return out

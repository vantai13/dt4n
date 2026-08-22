#!/usr/bin/env python3
"""Phase 20 decision-error measurement.

The only input interface is a rho trace shaped as ``rho[t, link]``. The same
logic can therefore run on simulated traces, offered-load Mininet traces, and
counter-based measured traces.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from twin import topology_v7 as T7
from twin.link_model import (
    CRITICAL_CEILING_FRACTION,
    CRITICAL_TO_FULL_RHO_OFFERED,
    LOW_TO_CRITICAL_RHO_OFFERED,
    OVERHEAD_FACTOR,
    RHO_CAP,
    loss_rate,
    queue_ceiling_ms,
    total_delay_ms,
)


EPS = 1e-9
EPS_REGRET = 1e-9
DEFAULT_Z_LIST_S = (0.0, 0.05, 0.10, 0.20, 0.298, 0.50, 1.0, 2.0, 4.0)
DEFAULT_SYNC_PERIOD_S = 0.5
DEFAULT_D_SYNC_S = 0.051
DEFAULT_T_LOSS = 0.010
DEFAULT_TAU_CORE_S = 2.87
DEFAULT_OPERATIONAL_REFERENCE_DT_S = 0.010
DEFAULT_BOOTSTRAPS = 2000
DEFAULT_SEEDS = (100, 101, 102)
FAMILY_ALPHA = 0.05


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def read_json(path: str) -> object:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_float_list(text: str) -> Tuple[float, ...]:
    vals = []
    for part in str(text).split(","):
        item = part.strip()
        if item:
            vals.append(float(item))
    if not vals:
        raise ValueError("expected at least one float")
    return tuple(vals)


def parse_int_list(text: str) -> Tuple[int, ...]:
    vals = []
    for part in str(text).split(","):
        item = part.strip()
        if item:
            vals.append(int(item))
    if not vals:
        raise ValueError("expected at least one integer seed")
    return tuple(vals)


def load_frozen_calibration(path: str) -> Dict[str, object]:
    """Read a frozen SLA calibration from a previous decision-error output."""
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError("frozen calibration file %s must contain a JSON object" % path)

    calibration = None
    if isinstance(data.get("calibration"), dict):
        calibration = data["calibration"]
    elif isinstance(data.get("config"), dict) and isinstance(data["config"].get("calibration"), dict):
        calibration = data["config"]["calibration"]
    elif {"w_loss", "t_delay_ms", "t_loss"} <= set(data):
        calibration = data

    if calibration is None:
        raise ValueError(
            "could not find calibration in %s; expected top-level calibration, "
            "config.calibration, or raw w_loss/t_delay_ms/t_loss fields" % path
        )
    missing = [key for key in ("w_loss", "t_delay_ms", "t_loss") if key not in calibration]
    if missing:
        raise ValueError("frozen calibration %s is missing %s" % (path, missing))

    out = dict(calibration)
    out["w_loss"] = float(out["w_loss"])
    out["t_delay_ms"] = float(out["t_delay_ms"])
    out["t_loss"] = float(out["t_loss"])
    return out


def _median_dt(values: Sequence[float], fallback: Optional[float]) -> float:
    vals = [float(v) for v in values if float(v) > 0.0]
    if vals:
        return float(np.median(vals))
    if fallback is None:
        raise ValueError("--dt is required when input has no dt_s column")
    return float(fallback)


def read_trace_matrix(path: str, dt_s: Optional[float] = None) -> Tuple[np.ndarray, float]:
    """Read long or wide rho CSV into ``(n, len(LINK_NAMES))`` order."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("%s has no header" % path)
        fields = set(reader.fieldnames)

        if {"link", "rho"} <= fields:
            by_link: Dict[str, List[float]] = {link: [] for link in T7.LINK_NAMES}
            dts: List[float] = []
            for row in reader:
                link = row.get("link")
                if link not in by_link:
                    continue
                by_link[link].append(float(row["rho"]))
                try:
                    dts.append(float(row.get("dt_s", "")))
                except (TypeError, ValueError):
                    pass
            lengths = {link: len(vals) for link, vals in by_link.items()}
            missing = [link for link, n in lengths.items() if n == 0]
            if missing:
                raise ValueError("trace %s is missing links %s" % (path, missing))
            if len(set(lengths.values())) != 1:
                raise ValueError("trace %s has unequal link lengths: %s" % (path, lengths))
            arr = np.column_stack([by_link[link] for link in T7.LINK_NAMES])
            return arr.astype(float, copy=False), _median_dt(dts, dt_s)

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("%s has no rows" % path)
    ignore = {"sample_index", "timestamp_s", "time_s", "t", "dt_s"}
    fields = [field for field in rows[0] if field not in ignore]
    missing = [link for link in T7.LINK_NAMES if link not in fields]
    if missing:
        raise ValueError("wide trace %s is missing links %s" % (path, missing))
    arr = np.array([[float(row[link]) for link in T7.LINK_NAMES] for row in rows], dtype=float)
    dts = []
    for row in rows:
        try:
            dts.append(float(row.get("dt_s", "")))
        except (TypeError, ValueError):
            pass
    return arr, _median_dt(dts, dt_s)


def drop_warmup_matrix(rho: np.ndarray, frac: float) -> np.ndarray:
    start = int(len(rho) * float(frac))
    out = np.asarray(rho, dtype=float)[start:]
    if len(out) < 4:
        raise ValueError("rho trace is too short after warm-up drop")
    return out


def _loss_rate_vec(rho_offered) -> np.ndarray:
    offered = np.maximum(np.asarray(rho_offered, dtype=float), 0.0)
    inflated = OVERHEAD_FACTOR * offered
    out = np.zeros_like(offered)
    mask = inflated > 1.0
    out[mask] = np.minimum(1.0 - 1.0 / inflated[mask], 1.0)
    return out


def _total_delay_ms_vec(base_delay_ms: float, rho_offered, bw_mbps: float, queue_pkts: int) -> np.ndarray:
    offered = np.maximum(np.asarray(rho_offered, dtype=float), 0.0)
    measured = np.minimum(OVERHEAD_FACTOR * offered, RHO_CAP)
    ceiling = queue_ceiling_ms(bw_mbps, queue_pkts)
    q_delay = np.empty_like(offered)

    low = offered <= LOW_TO_CRITICAL_RHO_OFFERED
    high = offered >= CRITICAL_TO_FULL_RHO_OFFERED
    mid = ~(low | high)

    q_delay[low] = np.minimum(float(base_delay_ms) * measured[low], ceiling)
    q_delay[mid] = CRITICAL_CEILING_FRACTION * ceiling
    q_delay[high] = ceiling
    return float(base_delay_ms) + q_delay


def build_cost_tables(rho: np.ndarray, w_loss: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(delay_ms, loss, cost)`` arrays with shape ``(n, K)``."""
    n = int(rho.shape[0])
    idx = {link: i for i, link in enumerate(T7.LINK_NAMES)}
    delay = np.zeros((n, T7.K), dtype=float)
    keep = np.ones((n, T7.K), dtype=float)
    for a, path in enumerate(T7.PATH_NAMES):
        for link in T7.PATHS[path]:
            bw, base, queue_pkts = T7.LINKS[link]
            r = rho[:, idx[link]]
            delay[:, a] += _total_delay_ms_vec(base, r, bw_mbps=bw, queue_pkts=queue_pkts)
            keep[:, a] *= 1.0 - _loss_rate_vec(r)
    loss = 1.0 - keep
    return delay, loss, delay + float(w_loss) * loss


def decide(cost: np.ndarray, eps: float = EPS) -> Tuple[np.ndarray, np.ndarray]:
    """Return deterministic argmin actions and tie flags using an EPS band."""
    arr = np.asarray(cost, dtype=float)
    best = arr.min(axis=1)
    tied = arr <= best[:, None] + float(eps)
    return np.argmax(tied, axis=1).astype(int), tied.sum(axis=1) > 1


def sawtooth_age_steps(
    n: int,
    dt_s: float,
    sync_period_s: float = DEFAULT_SYNC_PERIOD_S,
    d_sync_s: float = DEFAULT_D_SYNC_S,
) -> np.ndarray:
    """Return deterministic sawtooth AoI in integer trace steps."""
    t = np.arange(int(n), dtype=float) * float(dt_s)
    age_s = ((t - float(d_sync_s)) % float(sync_period_s)) + float(d_sync_s)
    return np.round(age_s / float(dt_s)).astype(int)


def z_to_steps(z_s: float, dt_s: float) -> int:
    return int(np.floor(float(z_s) / float(dt_s) + 0.5))


def sawtooth_age_level_count(
    dt_s: float,
    sync_period_s: float = DEFAULT_SYNC_PERIOD_S,
    d_sync_s: float = DEFAULT_D_SYNC_S,
) -> int:
    n = max(1, int(math.ceil(float(sync_period_s) / float(dt_s))) * 4)
    return int(len(set(sawtooth_age_steps(n, dt_s, sync_period_s, d_sync_s).tolist())))


def reference_sawtooth_mean_age_s(
    sync_period_s: float = DEFAULT_SYNC_PERIOD_S,
    d_sync_s: float = DEFAULT_D_SYNC_S,
    reference_dt_s: float = DEFAULT_OPERATIONAL_REFERENCE_DT_S,
) -> float:
    n = max(1, int(round(float(sync_period_s) / float(reference_dt_s))))
    age = sawtooth_age_steps(n, reference_dt_s, sync_period_s, d_sync_s)
    return float(age.mean() * float(reference_dt_s))


def check_z_grid(
    z_list_s: Sequence[float],
    dt_s: float,
    sync_period_s: float = DEFAULT_SYNC_PERIOD_S,
    d_sync_s: float = DEFAULT_D_SYNC_S,
    require_sawtooth_age: bool = True,
    min_age_levels: int = 10,
) -> Dict[str, object]:
    """Guard against AoI aliasing when fixed-z points collapse onto one lag.

    Phase 20 L8 hit this bug with 200 ms measured telemetry: the default z-list
    was designed for a 10 ms offered trace, so several adjacent z values mapped
    to the same integer lag. G3 then failed deterministically because the paired
    error deltas were exactly zero.
    """
    steps = [z_to_steps(z, dt_s) for z in z_list_s]
    duplicates = []
    by_step: Dict[int, float] = {}
    for z_s, step in zip(z_list_s, steps):
        if step in by_step:
            duplicates.append(
                {
                    "lo_z_s": float(by_step[step]),
                    "hi_z_s": float(z_s),
                    "z_steps": int(step),
                }
            )
        by_step[step] = float(z_s)
    if duplicates:
        raise ValueError(
            "AoI aliasing: dt=%.9gs is too coarse for this z-list; "
            "distinct z values collapse to the same z_steps: %s. "
            "Use z values representable on the trace grid, or record a finer trace."
            % (float(dt_s), duplicates)
        )

    age_levels = sawtooth_age_level_count(dt_s, sync_period_s, d_sync_s)
    if require_sawtooth_age and age_levels < int(min_age_levels):
        raise ValueError(
            "AoI aliasing: dt=%.9gs gives only %d distinct sawtooth age levels "
            "within sync_period=%.9gs; need >= %d. Use --operational-mode bracket "
            "or record a finer trace."
            % (float(dt_s), int(age_levels), float(sync_period_s), int(min_age_levels))
        )
    return {
        "dt_s": float(dt_s),
        "z_list_s": [float(z) for z in z_list_s],
        "z_steps": [int(s) for s in steps],
        "effective_z_s": [float(s * dt_s) for s in steps],
        "sawtooth_age_levels": int(age_levels),
        "min_age_levels": int(min_age_levels),
        "require_sawtooth_age": bool(require_sawtooth_age),
    }


def z_key(z_s: float) -> str:
    return "%.3f" % float(z_s)


def _viol_flags(delay: np.ndarray, loss: np.ndarray, t_delay_ms: float, t_loss: float) -> np.ndarray:
    return (delay > float(t_delay_ms)) | (loss > float(t_loss))


def interpolate_per_z_metric(per_z: Mapping[str, Mapping[str, object]], metric: str, target_s: float) -> Dict[str, object]:
    """Linearly interpolate a fixed-z metric at an effective age in seconds."""
    points = sorted(
        (float(row["effective_z_s"]), float(row[metric]), key)
        for key, row in per_z.items()
    )
    if not points:
        raise ValueError("cannot interpolate %s with no fixed-z points" % metric)
    xs = np.array([p[0] for p in points], dtype=float)
    ys = np.array([p[1] for p in points], dtype=float)
    target = float(target_s)
    value = float(np.interp(target, xs, ys))
    idx = int(np.searchsorted(xs, target, side="right"))
    lo_idx = max(0, min(idx - 1, len(points) - 1))
    hi_idx = max(0, min(idx, len(points) - 1))
    return {
        "metric": metric,
        "target_s": target,
        "value": value,
        "lo_z_s": float(points[lo_idx][0]),
        "hi_z_s": float(points[hi_idx][0]),
        "lo_key": points[lo_idx][2],
        "hi_key": points[hi_idx][2],
    }


def effective_z_bracket(
    per_z: Mapping[str, Mapping[str, object]],
    target_s: float,
) -> Dict[str, object]:
    points = sorted(
        (float(row["effective_z_s"]), key)
        for key, row in per_z.items()
    )
    if not points:
        raise ValueError("cannot bracket target age with no fixed-z points")
    xs = np.asarray([p[0] for p in points], dtype=float)
    target = float(target_s)
    idx = int(np.searchsorted(xs, target, side="right"))
    lo_idx = max(0, min(idx - 1, len(points) - 1))
    hi_idx = max(0, min(idx, len(points) - 1))
    lo_z, lo_key = points[lo_idx]
    hi_z, hi_key = points[hi_idx]
    if abs(hi_z - lo_z) <= 1e-12:
        weight_hi = 0.0
    else:
        weight_hi = float((target - lo_z) / (hi_z - lo_z))
        weight_hi = float(np.clip(weight_hi, 0.0, 1.0))
    return {
        "target_s": target,
        "lo_key": lo_key,
        "hi_key": hi_key,
        "lo_z_s": float(lo_z),
        "hi_z_s": float(hi_z),
        "weight_hi": weight_hi,
        "weight_lo": float(1.0 - weight_hi),
    }


def calibrate_sla(
    rho: np.ndarray,
    t_loss: float = DEFAULT_T_LOSS,
    delay_percentile: float = 85.0,
    initial_w_loss: float = T7.W_LOSS_DEFAULT,
    max_rounds: int = 3,
    action_change_stop: float = 0.10,
) -> Dict[str, object]:
    """Apply Q1/Q2: iterate ``w_loss = T_delay / T_loss`` before measuring err."""
    history = []
    w_loss = float(initial_w_loss)
    prev_opt = None
    for round_idx in range(int(max_rounds)):
        delay, loss, cost = build_cost_tables(rho, w_loss)
        opt, tie = decide(cost)
        rows = np.arange(len(rho))
        opt_delay = delay[rows, opt]
        t_delay = float(np.percentile(opt_delay, float(delay_percentile)))
        opt_viol = _viol_flags(delay, loss, t_delay, t_loss)[rows, opt]
        action_change = None if prev_opt is None else float(np.mean(opt != prev_opt))
        new_w_loss = t_delay / float(t_loss)
        history.append(
            {
                "round": round_idx,
                "w_loss_input": float(w_loss),
                "t_delay_ms": float(t_delay),
                "w_loss_next": float(new_w_loss),
                "optimal_violation": float(opt_viol.mean()),
                "tie_rate": float(tie.mean()),
                "action_change": action_change,
            }
        )
        if action_change is not None and action_change <= float(action_change_stop):
            w_loss = new_w_loss
            break
        prev_opt = opt
        w_loss = new_w_loss

    delay, loss, cost = build_cost_tables(rho, w_loss)
    opt, tie = decide(cost)
    rows = np.arange(len(rho))
    t_delay = float(np.percentile(delay[rows, opt], float(delay_percentile)))
    final_w_loss = t_delay / float(t_loss)
    if abs(final_w_loss - w_loss) > 1e-9:
        w_loss = final_w_loss
        delay, loss, cost = build_cost_tables(rho, w_loss)
        opt, tie = decide(cost)
    opt_viol = _viol_flags(delay, loss, t_delay, t_loss)[rows, opt]
    return {
        "w_loss": float(w_loss),
        "t_delay_ms": float(t_delay),
        "t_loss": float(t_loss),
        "delay_percentile": float(delay_percentile),
        "optimal_violation": float(opt_viol.mean()),
        "tie_rate": float(tie.mean()),
        "history": history,
    }


def _action_metrics(
    actions: np.ndarray,
    opt: np.ndarray,
    cost: np.ndarray,
    viol: np.ndarray,
    rows: np.ndarray,
    base_viol_flags: np.ndarray,
) -> Dict[str, object]:
    regret = cost[rows, actions] - cost[rows, opt]
    wrong = (actions != opt) & (regret > EPS_REGRET)
    twin_viol = viol[rows, actions]
    return {
        "wrong": wrong,
        "twin_viol": twin_viol,
        "err": float(wrong.mean()),
        "d_sla": float(twin_viol.mean() - base_viol_flags.mean()),
        "twin_violation": float(twin_viol.mean()),
        "mean_regret_ms": float(np.maximum(regret, 0.0).mean()),
        "mean_regret_on_error_ms": float(regret[wrong].mean()) if wrong.any() else 0.0,
    }


def evaluate(
    rho: np.ndarray,
    dt_s: float,
    w_loss: float,
    t_delay_ms: float,
    t_loss: float,
    z_list_s: Sequence[float],
    sync_period_s: float = DEFAULT_SYNC_PERIOD_S,
    d_sync_s: float = DEFAULT_D_SYNC_S,
    operational_mode: str = "sawtooth",
    operational_age_s: Optional[float] = None,
    operational_reference_dt_s: float = DEFAULT_OPERATIONAL_REFERENCE_DT_S,
) -> Dict[str, object]:
    """Measure fixed-z and operational sawtooth-AoI decision error."""
    n = int(rho.shape[0])
    operational_mode = str(operational_mode)
    if operational_mode not in {"sawtooth", "bracket"}:
        raise ValueError("unknown operational_mode %r" % operational_mode)
    grid_check = check_z_grid(
        z_list_s,
        dt_s,
        sync_period_s=sync_period_s,
        d_sync_s=d_sync_s,
        require_sawtooth_age=(operational_mode == "sawtooth"),
    )
    z_steps = [int(z) for z in grid_check["z_steps"]]
    age = (
        sawtooth_age_steps(n, dt_s, sync_period_s=sync_period_s, d_sync_s=d_sync_s)
        if operational_mode == "sawtooth"
        else np.zeros(n, dtype=int)
    )
    z_max = max(max(z_steps), int(age.max()) if operational_mode == "sawtooth" else 0)
    if z_max >= n:
        raise ValueError("max age/lag exceeds trace length")

    rows = np.arange(z_max, n)
    sl = slice(z_max, n)
    delay, loss, cost = build_cost_tables(rho, w_loss)
    opt_all, tie = decide(cost)
    opt = opt_all[sl]
    viol = _viol_flags(delay, loss, t_delay_ms, t_loss)
    base_viol_flags = viol[rows, opt]
    base_violation = float(base_viol_flags.mean())

    per_z: Dict[str, Dict[str, object]] = {}
    arrays: Dict[str, np.ndarray] = {"base_violation": base_viol_flags.astype(float)}
    wrong_flags: Dict[str, np.ndarray] = {}
    twin_viol_flags: Dict[str, np.ndarray] = {}
    for z_s, z in zip(z_list_s, z_steps):
        actions = opt_all[rows - z]
        m = _action_metrics(actions, opt, cost, viol, rows, base_viol_flags)
        key = z_key(z_s)
        per_z[key] = {
            "z_s": float(z_s),
            "z_steps": int(z),
            "effective_z_s": float(z * dt_s),
            "err": m["err"],
            "d_sla": m["d_sla"],
            "twin_violation": m["twin_violation"],
            "mean_regret_ms": m["mean_regret_ms"],
            "mean_regret_on_error_ms": m["mean_regret_on_error_ms"],
        }
        wrong_flags[key] = m["wrong"]
        twin_viol_flags[key] = m["twin_viol"]
        arrays["err:" + key] = m["wrong"].astype(float)
        arrays["twin_violation:" + key] = m["twin_viol"].astype(float)

    if operational_mode == "sawtooth":
        op_actions = opt_all[rows - age[sl]]
        op = _action_metrics(op_actions, opt, cost, viol, rows, base_viol_flags)
        op_wrong = op["wrong"].astype(float)
        op_twin_viol = op["twin_viol"].astype(float)
        operational = {
            "mode": "sawtooth",
            "err": op["err"],
            "d_sla": op["d_sla"],
            "twin_violation": op["twin_violation"],
            "mean_age_s": float(age[sl].mean() * dt_s),
            "min_age_s": float(age[sl].min() * dt_s),
            "max_age_s": float(age[sl].max() * dt_s),
            "mean_regret_ms": op["mean_regret_ms"],
            "mean_regret_on_error_ms": op["mean_regret_on_error_ms"],
        }
    else:
        target_age_s = (
            float(operational_age_s)
            if operational_age_s is not None
            else reference_sawtooth_mean_age_s(sync_period_s, d_sync_s, operational_reference_dt_s)
        )
        bracket = effective_z_bracket(per_z, target_age_s)
        lo_key = str(bracket["lo_key"])
        hi_key = str(bracket["hi_key"])
        w_hi = float(bracket["weight_hi"])
        w_lo = float(bracket["weight_lo"])
        op_wrong = w_lo * wrong_flags[lo_key].astype(float) + w_hi * wrong_flags[hi_key].astype(float)
        op_twin_viol = (
            w_lo * twin_viol_flags[lo_key].astype(float)
            + w_hi * twin_viol_flags[hi_key].astype(float)
        )
        operational = {
            "mode": "bracket_interpolation",
            "err": float(op_wrong.mean()),
            "d_sla": float(op_twin_viol.mean() - base_viol_flags.mean()),
            "twin_violation": float(op_twin_viol.mean()),
            "mean_age_s": target_age_s,
            "min_age_s": float(bracket["lo_z_s"]),
            "max_age_s": float(bracket["hi_z_s"]),
            "mean_regret_ms": None,
            "mean_regret_on_error_ms": None,
            "bracket": bracket,
            "operational_reference_dt_s": float(operational_reference_dt_s),
        }
    wrong_flags["operational"] = op_wrong
    twin_viol_flags["operational"] = op_twin_viol
    arrays["err:operational"] = np.asarray(op_wrong, dtype=float)
    arrays["twin_violation:operational"] = np.asarray(op_twin_viol, dtype=float)

    age_ref_s = float(operational["mean_age_s"])
    jensen_err = interpolate_per_z_metric(per_z, "err", age_ref_s)
    jensen_d_sla = interpolate_per_z_metric(per_z, "d_sla", age_ref_s)
    jensen_gap_err = float(jensen_err["value"] - operational["err"])
    jensen_gap_d_sla = float(jensen_d_sla["value"] - operational["d_sla"])
    z_star = z_key(0.298)
    nominal_gap_err = None
    nominal_gap_d_sla = None
    if z_star in per_z:
        nominal_gap_err = float(per_z[z_star]["err"] - operational["err"])
        nominal_gap_d_sla = float(per_z[z_star]["d_sla"] - operational["d_sla"])

    return {
        "summary": {
            "n_eval": int(len(rows)),
            "t0": int(z_max),
            "common_window_start_s": float(z_max * dt_s),
            "grid_check": grid_check,
            "operational_mode": operational_mode,
            "base_violation": base_violation,
            "tie_rate": float(tie[sl].mean()),
            "jensen_gap_method": "linear_interpolation_at_mean_operational_age",
            "jensen_reference_age_s": age_ref_s,
            "jensen_reference_err": float(jensen_err["value"]),
            "jensen_reference_d_sla": float(jensen_d_sla["value"]),
            "jensen_gap_err": jensen_gap_err,
            "jensen_gap_d_sla": jensen_gap_d_sla,
            "nominal_z_star_key": z_star if z_star in per_z else None,
            "nominal_z_star_gap_err": nominal_gap_err,
            "nominal_z_star_gap_d_sla": nominal_gap_d_sla,
        },
        "per_z": per_z,
        "operational": operational,
        "_arrays": arrays,
        "_wrong_flags": wrong_flags,
        "_twin_viol_flags": twin_viol_flags,
        "_opt_all": opt_all,
        "_cost": cost,
        "_viol": viol,
        "_rows": rows,
        "_age": age,
    }


def _moving_block_sums(arrays: Mapping[str, np.ndarray], block_len: int) -> Tuple[List[str], np.ndarray]:
    keys = list(arrays)
    mat = np.column_stack([np.asarray(arrays[k], dtype=float) for k in keys])
    csum = np.vstack([np.zeros((1, mat.shape[1])), np.cumsum(mat, axis=0)])
    sums = csum[block_len:] - csum[:-block_len]
    return keys, sums


def block_bootstrap(
    arrays: Mapping[str, np.ndarray],
    tau_core_s: float,
    dt_s: float,
    n_boot: int = DEFAULT_BOOTSTRAPS,
    seed: int = 0,
) -> Dict[str, object]:
    """Moving paired block bootstrap for err levels, d_sla, and adjacent deltas."""
    first = next(iter(arrays.values()))
    n = len(first)
    block_len = max(1, int(round(5.0 * float(tau_core_s) / float(dt_s))))
    n_blocks = n // block_len
    if n_blocks < 50:
        raise ValueError("only %d blocks; need >= 50" % n_blocks)
    keys, block_sums = _moving_block_sums(arrays, block_len)
    key_index = {key: i for i, key in enumerate(keys)}
    rng = np.random.default_rng(seed)
    used_n = n_blocks * block_len
    draws = np.empty((int(n_boot), len(keys)), dtype=float)
    starts_max = block_sums.shape[0] - 1
    for i in range(int(n_boot)):
        starts = rng.integers(0, starts_max + 1, size=n_blocks)
        draws[i] = block_sums[starts].sum(axis=0) / used_n

    def ci(values, alpha: float = 0.05) -> Dict[str, float]:
        lo_pct = 100.0 * alpha / 2.0
        hi_pct = 100.0 * (1.0 - alpha / 2.0)
        lo, hi = np.percentile(values, [lo_pct, hi_pct])
        return {"ci_lo": float(lo), "ci_hi": float(hi)}

    def ci_named(values, alpha: float) -> Dict[str, float]:
        lo_pct = 100.0 * alpha / 2.0
        hi_pct = 100.0 * (1.0 - alpha / 2.0)
        lo, hi = np.percentile(values, [lo_pct, hi_pct])
        return {"lo": float(lo), "hi": float(hi), "alpha": float(alpha), "level": float(1.0 - alpha)}

    def se(values) -> float:
        return float(np.asarray(values, dtype=float).std(ddof=1))

    out: Dict[str, object] = {
        "seed": int(seed),
        "n_boot": int(n_boot),
        "block_len_samples": int(block_len),
        "block_len_s": float(block_len * dt_s),
        "n_blocks": int(n_blocks),
        "used_samples_per_draw": int(used_n),
        "err": {},
        "d_sla": {},
        "pairwise_err_delta": {},
    }

    base_idx = key_index["base_violation"]
    for key in keys:
        if key.startswith("err:"):
            name = key.split(":", 1)[1]
            vals = draws[:, key_index[key]]
            out["err"][name] = {"mean": float(np.asarray(arrays[key]).mean()), "se": se(vals), **ci(vals)}
        if key.startswith("twin_violation:"):
            name = key.split(":", 1)[1]
            vals = draws[:, key_index[key]] - draws[:, base_idx]
            point = float(np.asarray(arrays[key]).mean() - np.asarray(arrays["base_violation"]).mean())
            out["d_sla"][name] = {"mean": point, "se": se(vals), **ci(vals)}

    z_keys = [key.split(":", 1)[1] for key in keys if key.startswith("err:") and key != "err:operational"]
    z_keys = sorted(z_keys, key=float)
    pairwise_alpha = FAMILY_ALPHA / max(1, len(z_keys) - 1)
    for a, b in zip(z_keys, z_keys[1:]):
        vals = draws[:, key_index["err:" + b]] - draws[:, key_index["err:" + a]]
        point = float(np.asarray(arrays["err:" + b]).mean() - np.asarray(arrays["err:" + a]).mean())
        se_val = se(vals)
        out["pairwise_err_delta"][b + "-" + a] = {
            "mean": point,
            "se": se_val,
            "z_score": float(point / se_val) if se_val > 0.0 else None,
            **ci(vals),
            "ci_bonferroni": ci_named(vals, pairwise_alpha),
        }
    return out


def _rankdata(xs: Sequence[float]) -> np.ndarray:
    arr = np.asarray(xs, dtype=float)
    order = np.argsort(arr)
    ranks = np.empty(len(arr), dtype=float)
    i = 0
    while i < len(arr):
        j = i + 1
        while j < len(arr) and arr[order[j]] == arr[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + j - 1) / 2.0
        i = j
    return ranks


def spearman_one_sided(xs: Sequence[float], ys: Sequence[float]) -> Dict[str, float]:
    """Legacy exact rank test, kept for diagnostics only.

    Phase 20 G3 no longer uses this p-value because fixed-z points are computed
    on the same trace and are therefore dependent observations.
    """
    rx = _rankdata(xs)
    ry = _rankdata(ys)
    rho = float(np.corrcoef(rx, ry)[0, 1])
    n = len(rx)
    if n <= 9:
        count = 0
        total = 0
        base = np.arange(n, dtype=float)
        for perm in itertools.permutations(base):
            r = float(np.corrcoef(rx, np.asarray(perm, dtype=float))[0, 1])
            if r >= rho - 1e-12:
                count += 1
            total += 1
        p = count / total
    else:
        if abs(rho) >= 1.0:
            p = 0.0 if rho > 0 else 1.0
        else:
            t = rho * math.sqrt((n - 2.0) / max(1e-12, 1.0 - rho * rho))
            p = 0.5 * math.erfc(t / math.sqrt(2.0))
    return {"rho": rho, "p_one_sided": float(p), "n": int(n)}


def spearman_rho(xs: Sequence[float], ys: Sequence[float]) -> Dict[str, float]:
    rx = _rankdata(xs)
    ry = _rankdata(ys)
    return {"rho": float(np.corrcoef(rx, ry)[0, 1]), "n": int(len(rx))}


def pairwise_g3_summary(bootstrap: Mapping[str, object]) -> Dict[str, object]:
    deltas = bootstrap.get("pairwise_err_delta", {})
    out = {}
    all_positive = True
    for key, row in deltas.items():
        bonf = row.get("ci_bonferroni", {})
        lo = bonf.get("lo")
        positive = bool(lo is not None and float(lo) > 0.0)
        all_positive = bool(all_positive and positive)
        out[key] = {
            "mean": float(row["mean"]),
            "se": float(row["se"]),
            "z_score": row.get("z_score"),
            "ci95": {"lo": float(row["ci_lo"]), "hi": float(row["ci_hi"])},
            "ci_bonferroni": bonf,
            "positive_after_bonferroni": positive,
        }
    n_tests = len(out)
    return {
        "method": "paired_moving_block_bootstrap_adjacent_err_deltas",
        "family_alpha": FAMILY_ALPHA,
        "n_tests": int(n_tests),
        "per_test_alpha": float(FAMILY_ALPHA / max(1, n_tests)),
        "all_positive_after_bonferroni": bool(n_tests > 0 and all_positive),
        "deltas": out,
    }


def mechanism_from_crossed(crossed: np.ndarray, wrong: np.ndarray) -> Dict[str, object]:
    crossed = np.asarray(crossed, dtype=bool)
    wrong = np.asarray(wrong, dtype=bool)
    correct = ~wrong
    p_e_c = float(wrong[crossed].mean()) if crossed.any() else 0.0
    p_e_n = float(wrong[~crossed].mean()) if (~crossed).any() else 0.0
    risk_ratio = p_e_c / max(p_e_n, 1e-12)
    return {
        "p_crossed": float(crossed.mean()),
        "p_crossed_given_error": float(crossed[wrong].mean()) if wrong.any() else 0.0,
        "p_crossed_given_correct": float(crossed[correct].mean()) if correct.any() else 0.0,
        "p_error_given_crossed": p_e_c,
        "p_error_given_not_crossed": p_e_n,
        "risk_ratio": float(risk_ratio),
        "share_errors_with_crossing": float((wrong & crossed).sum() / max(int(wrong.sum()), 1)),
        "P3_prime_pass": bool(risk_ratio >= 3.0 and p_e_n <= 0.10),
    }


def crossed_fixed_z(rho: np.ndarray, rows: np.ndarray, z_steps: int) -> np.ndarray:
    if z_steps <= 0:
        return np.zeros(len(rows), dtype=bool)
    cur = rho[rows]
    old = rho[rows - int(z_steps)]
    crossed = np.zeros(len(rows), dtype=bool)
    for jump in T7.JUMPS:
        crossed |= (((cur > jump) & (old <= jump)) | ((cur <= jump) & (old > jump))).any(axis=1)
    return crossed


def crossed_operational(rho: np.ndarray, rows: np.ndarray, age_steps: np.ndarray) -> np.ndarray:
    cur = rho[rows]
    old = rho[rows - age_steps[rows]]
    crossed = np.zeros(len(rows), dtype=bool)
    for jump in T7.JUMPS:
        crossed |= (((cur > jump) & (old <= jump)) | ((cur <= jump) & (old > jump))).any(axis=1)
    return crossed


def r_jump_base_rates(rho: np.ndarray, rows: np.ndarray, wrong: np.ndarray) -> Dict[str, object]:
    cur = rho[rows]
    dist = np.full(len(rows), np.inf)
    for jump in T7.JUMPS:
        dist = np.minimum(dist, np.min(np.abs(cur - jump), axis=1))
    out = {}
    for threshold in (0.005, 0.010, 0.020):
        near = dist < threshold
        p_base = float(near.mean())
        p_cond = float(near[wrong].mean()) if wrong.any() else 0.0
        out["r_jump_lt_%.3f" % threshold] = {
            "p_base": p_base,
            "p_given_error": p_cond,
            "lift": p_cond / max(p_base, 1e-12),
        }
    return out


def mechanism_tests(rho: np.ndarray, evaluation: Mapping[str, object]) -> Dict[str, object]:
    rows = evaluation["_rows"]
    age = evaluation["_age"]
    wrong_flags = evaluation["_wrong_flags"]
    out: Dict[str, object] = {}
    if "0.298" in wrong_flags:
        z_steps = int(evaluation["per_z"]["0.298"]["z_steps"])
        wrong = wrong_flags["0.298"]
        out["z_star"] = mechanism_from_crossed(crossed_fixed_z(rho, rows, z_steps), wrong)
        out["z_star"]["r_jump_base_rate_checks"] = r_jump_base_rates(rho, rows, wrong)
    op = evaluation.get("operational", {})
    if isinstance(op, Mapping) and op.get("mode") == "bracket_interpolation":
        bracket = op.get("bracket", {})
        endpoint_keys = []
        endpoint_rows = []
        for key in (bracket.get("lo_key"), bracket.get("hi_key")):
            if key is None or key in endpoint_keys or key not in wrong_flags:
                continue
            z_steps = int(evaluation["per_z"][key]["z_steps"])
            wrong = np.asarray(wrong_flags[key], dtype=bool)
            row = mechanism_from_crossed(crossed_fixed_z(rho, rows, z_steps), wrong)
            row["r_jump_base_rate_checks"] = r_jump_base_rates(rho, rows, wrong)
            endpoint_keys.append(str(key))
            endpoint_rows.append(row)
        out["operational_bracket_endpoints"] = {
            key: row for key, row in zip(endpoint_keys, endpoint_rows)
        }
        if endpoint_rows:
            out["operational"] = {
                "mode": "bracket_endpoint_conservative",
                "endpoint_keys": endpoint_keys,
                "risk_ratio": float(min(row["risk_ratio"] for row in endpoint_rows)),
                "p_error_given_crossed": float(min(row["p_error_given_crossed"] for row in endpoint_rows)),
                "p_error_given_not_crossed": float(max(row["p_error_given_not_crossed"] for row in endpoint_rows)),
                "p_crossed": float(min(row["p_crossed"] for row in endpoint_rows)),
                "p_crossed_given_error": float(min(row["p_crossed_given_error"] for row in endpoint_rows)),
                "p_crossed_given_correct": float(min(row["p_crossed_given_correct"] for row in endpoint_rows)),
                "share_errors_with_crossing": float(min(row["share_errors_with_crossing"] for row in endpoint_rows)),
                "P3_prime_pass": bool(all(row["P3_prime_pass"] for row in endpoint_rows)),
            }
        else:
            out["operational"] = {"mode": "bracket_endpoint_conservative", "P3_prime_pass": False}
    else:
        wrong_op = np.asarray(wrong_flags["operational"], dtype=bool)
        out["operational"] = mechanism_from_crossed(crossed_operational(rho, rows, age), wrong_op)
        out["operational"]["r_jump_base_rate_checks"] = r_jump_base_rates(rho, rows, wrong_op)
    return out


def negative_controls(
    rho: np.ndarray,
    w_loss: float,
    t_delay_ms: float,
    t_loss: float,
    tau_core_s: float,
    dt_s: float,
    seed: int = 0,
) -> Dict[str, object]:
    delay, loss, cost = build_cost_tables(rho, w_loss)
    opt, _tie = decide(cost)
    rows = np.arange(len(rho))
    viol = _viol_flags(delay, loss, t_delay_ms, t_loss)
    base_viol = viol[rows, opt]
    rng = np.random.default_rng(seed)

    nc: Dict[str, object] = {}
    same = _action_metrics(opt, opt, cost, viol, rows, base_viol)
    nc["NC1_zero_age"] = {
        "err": same["err"],
        "expect": 0.0,
        "pass": bool(same["err"] == 0.0),
    }

    cost_tiny = cost + rng.normal(0.0, 1e-12, size=cost.shape)
    opt_tiny, _ = decide(cost_tiny)
    tiny = _action_metrics(opt_tiny, opt, cost, viol, rows, base_viol)
    nc["NC2_tiny_noise"] = {
        "err": tiny["err"],
        "expect": 0.0,
        "pass": bool(tiny["err"] == 0.0),
    }

    block_len = max(1, int(round(5.0 * float(tau_core_s) / float(dt_s))))
    n_blocks = max(1, len(rho) // block_len)
    perm = rng.permutation(n_blocks)
    idx = np.concatenate([np.arange(p * block_len, (p + 1) * block_len) for p in perm])
    m = len(idx)
    permuted = _action_metrics(opt[idx], opt[:m], cost[:m], viol[:m], np.arange(m), base_viol[:m])
    share = np.array([(opt == a).mean() for a in range(T7.K)], dtype=float)
    opt_cost = cost[rows, opt]
    independent_expect = np.zeros(len(rho), dtype=float)
    for action in range(T7.K):
        independent_expect += share[action] * ((cost[:, action] - opt_cost) > EPS_REGRET)
    independent_err = float(independent_expect.mean())
    nc["NC3_block_permute"] = {
        "err": permuted["err"],
        "err_independent_expected": independent_err,
        "block_len_samples": int(block_len),
        "n_blocks": int(n_blocks),
        "pass": bool(abs(permuted["err"] - independent_err) < 0.05),
    }

    random_actions = rng.integers(0, T7.K, size=len(rho))
    random = _action_metrics(random_actions, opt, cost, viol, rows, base_viol)
    uniform_expect = np.mean(
        np.sum((cost - opt_cost[:, None]) > EPS_REGRET, axis=1) / float(T7.K)
    )
    nc["NC4_random_twin"] = {
        "err": random["err"],
        "expect_exact": float(uniform_expect),
        "expect_approx": float(1.0 - 1.0 / T7.K),
        "pass": bool(abs(random["err"] - uniform_expect) < 0.02),
    }
    nc["all_pass"] = bool(all(item.get("pass", False) for item in nc.values() if isinstance(item, dict)))
    return nc


def attach_bootstrap_to_evaluation(evaluation: Dict[str, object], bootstrap: Mapping[str, object]) -> None:
    for key, row in evaluation["per_z"].items():
        if key in bootstrap["err"]:
            row["err_ci95"] = {
                "lo": bootstrap["err"][key]["ci_lo"],
                "hi": bootstrap["err"][key]["ci_hi"],
            }
        if key in bootstrap["d_sla"]:
            row["d_sla_ci95"] = {
                "lo": bootstrap["d_sla"][key]["ci_lo"],
                "hi": bootstrap["d_sla"][key]["ci_hi"],
            }
    op = evaluation["operational"]
    if "operational" in bootstrap["err"]:
        op["err_ci95"] = {
            "lo": bootstrap["err"]["operational"]["ci_lo"],
            "hi": bootstrap["err"]["operational"]["ci_hi"],
        }
    if "operational" in bootstrap["d_sla"]:
        op["d_sla_ci95"] = {
            "lo": bootstrap["d_sla"]["operational"]["ci_lo"],
            "hi": bootstrap["d_sla"]["operational"]["ci_hi"],
        }


def gate_summary(
    evaluation: Mapping[str, object],
    bootstrap: Mapping[str, object],
    nc: Mapping[str, object],
    mechanism: Mapping[str, object],
) -> Dict[str, object]:
    op_err = bootstrap["err"].get("operational")
    op_d = bootstrap["d_sla"].get("operational")
    z_vals = []
    err_vals = []
    for key, row in sorted(evaluation["per_z"].items(), key=lambda kv: float(kv[0])):
        z_vals.append(float(row["z_s"]))
        err_vals.append(float(row["err"]))
    spearman = spearman_rho(z_vals, err_vals)
    g3_pairwise = pairwise_g3_summary(bootstrap)
    g1 = bool(op_err and op_err["ci_lo"] >= 0.05 and op_err["ci_hi"] <= 0.40)
    g2 = bool(op_d and op_d["ci_lo"] >= 0.03)
    g3 = bool(g3_pairwise["all_positive_after_bonferroni"])
    g4 = bool(nc.get("all_pass"))
    p3 = mechanism.get("operational", {})
    g5 = bool(p3.get("P3_prime_pass", False))
    return {
        "G1_operational_err_ci_inside_005_040": g1,
        "G2_operational_d_sla_lower_ge_003": g2,
        "G3_pairwise_err_delta_bonferroni_positive": g3,
        "G4_negative_controls": g4,
        "G5_P3_prime_operational": g5,
        "G6_sim_vs_real": "pass_model_validation_lesson_20_3",
        "G6_scope": "AR1 model validation, not cross-testbed validation",
        "spearman_descriptive_only": spearman,
        "G3_pairwise": g3_pairwise,
        "pass_without_G6": bool(g1 and g2 and g3 and g4 and g5),
        "pass_with_G6": bool(g1 and g2 and g3 and g4 and g5),
    }


def strip_private(evaluation: Mapping[str, object]) -> Dict[str, object]:
    return {k: v for k, v in evaluation.items() if not k.startswith("_")}


def run_for_seed(
    rho: np.ndarray,
    dt_s: float,
    config: Mapping[str, object],
    seed: int,
    nc_only: bool = False,
) -> Dict[str, object]:
    calibration = config["calibration"]
    nc = negative_controls(
        rho,
        w_loss=float(calibration["w_loss"]),
        t_delay_ms=float(calibration["t_delay_ms"]),
        t_loss=float(calibration["t_loss"]),
        tau_core_s=float(config["tau_core_s"]),
        dt_s=dt_s,
        seed=seed,
    )
    out: Dict[str, object] = {"seed": int(seed), "negative_controls": nc}
    if nc_only:
        return out

    evaluation = evaluate(
        rho,
        dt_s=dt_s,
        w_loss=float(calibration["w_loss"]),
        t_delay_ms=float(calibration["t_delay_ms"]),
        t_loss=float(calibration["t_loss"]),
        z_list_s=config["z_list_s"],
        sync_period_s=float(config["sync_period_s"]),
        d_sync_s=float(config["d_sync_s"]),
        operational_mode=str(config.get("operational_mode", "sawtooth")),
        operational_age_s=config.get("operational_age_s"),
        operational_reference_dt_s=float(
            config.get("operational_reference_dt_s", DEFAULT_OPERATIONAL_REFERENCE_DT_S)
        ),
    )
    bootstrap = block_bootstrap(
        evaluation["_arrays"],
        tau_core_s=float(config["tau_core_s"]),
        dt_s=dt_s,
        n_boot=int(config["n_boot"]),
        seed=seed,
    )
    mechanism = mechanism_tests(rho, evaluation)
    attach_bootstrap_to_evaluation(evaluation, bootstrap)
    out.update(
        {
            "evaluation": strip_private(evaluation),
            "bootstrap": bootstrap,
            "mechanism": mechanism,
            "gate": gate_summary(evaluation, bootstrap, nc, mechanism),
        }
    )
    return out


def print_run_report(result: Mapping[str, object]) -> None:
    print("\n=== decision_error seed %s ===" % result["seed"])
    nc = result["negative_controls"]
    print("  NC all_pass = %s" % nc.get("all_pass"))
    for key in ("NC1_zero_age", "NC2_tiny_noise", "NC3_block_permute", "NC4_random_twin"):
        item = nc[key]
        print("  %s: err=%.6f pass=%s" % (key, float(item["err"]), item["pass"]))
    if "evaluation" not in result:
        return
    op = result["evaluation"]["operational"]
    gate = result["gate"]
    mech = result["mechanism"]["operational"]
    print(
        "  operational: err=%.4f CI[%.4f, %.4f] | d_sla=%.4f CI[%.4f, %.4f]"
        % (
            float(op["err"]),
            float(op["err_ci95"]["lo"]),
            float(op["err_ci95"]["hi"]),
            float(op["d_sla"]),
            float(op["d_sla_ci95"]["lo"]),
            float(op["d_sla_ci95"]["hi"]),
        )
    )
    print(
        "  P3': risk_ratio=%.2f | P(err|cross)=%.4f | P(err|no_cross)=%.4f | pass=%s"
        % (
            float(mech["risk_ratio"]),
            float(mech["p_error_given_crossed"]),
            float(mech["p_error_given_not_crossed"]),
            mech["P3_prime_pass"],
        )
    )
    print("  gate pass_without_G6 = %s" % gate["pass_without_G6"])


def parse_args():
    p = argparse.ArgumentParser(description="Measure Phase 20 decision error from a rho trace")
    p.add_argument("--trace", default="results/SUPERSEDED/phase-20/rho_offered_long.csv")
    p.add_argument("--dt", type=float, default=None)
    p.add_argument("--warmup-frac", type=float, default=0.2)
    p.add_argument("--z-list", default=",".join("%g" % z for z in DEFAULT_Z_LIST_S))
    p.add_argument("--tau-core", type=float, default=DEFAULT_TAU_CORE_S)
    p.add_argument("--sync-period", type=float, default=DEFAULT_SYNC_PERIOD_S)
    p.add_argument("--d-sync", type=float, default=DEFAULT_D_SYNC_S)
    p.add_argument("--operational-mode", choices=("sawtooth", "bracket"), default="sawtooth")
    p.add_argument(
        "--operational-age-s",
        type=float,
        default=None,
        help="Target age for --operational-mode bracket; default is the 10 ms sawtooth mean age.",
    )
    p.add_argument(
        "--operational-reference-dt",
        type=float,
        default=DEFAULT_OPERATIONAL_REFERENCE_DT_S,
        help="Reference dt used to compute the default bracket target age.",
    )
    p.add_argument("--t-loss", type=float, default=DEFAULT_T_LOSS)
    p.add_argument("--delay-percentile", type=float, default=85.0)
    p.add_argument("--initial-w-loss", type=float, default=T7.W_LOSS_DEFAULT)
    p.add_argument("--w-loss-rounds", type=int, default=3)
    p.add_argument(
        "--freeze-calibration",
        default=None,
        help="Read w_loss/T_delay/T_loss from a prior decision_error JSON instead of recalibrating on this trace.",
    )
    p.add_argument("--n-boot", type=int, default=DEFAULT_BOOTSTRAPS)
    p.add_argument("--seeds", default=",".join(str(s) for s in DEFAULT_SEEDS))
    p.add_argument("--nc-only", action="store_true")
    p.add_argument("--out", default="results/SUPERSEDED/phase-20/decision_error_offered.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rho_raw, dt_s = read_trace_matrix(args.trace, dt_s=args.dt)
    rho = drop_warmup_matrix(rho_raw, args.warmup_frac)
    z_list_s = parse_float_list(args.z_list)
    seeds = parse_int_list(args.seeds)
    if args.freeze_calibration:
        calibration = load_frozen_calibration(args.freeze_calibration)
        calibration_mode = "frozen"
    else:
        calibration = calibrate_sla(
            rho,
            t_loss=args.t_loss,
            delay_percentile=args.delay_percentile,
            initial_w_loss=args.initial_w_loss,
            max_rounds=args.w_loss_rounds,
        )
        calibration_mode = "self_calibrated"
    config = {
        "trace": args.trace,
        "dt_s": float(dt_s),
        "warmup_frac": float(args.warmup_frac),
        "n_raw": int(len(rho_raw)),
        "n_after_warmup": int(len(rho)),
        "z_list_s": list(z_list_s),
        "tau_core_s": float(args.tau_core),
        "sync_period_s": float(args.sync_period),
        "d_sync_s": float(args.d_sync),
        "operational_mode": str(args.operational_mode),
        "operational_age_s": None if args.operational_age_s is None else float(args.operational_age_s),
        "operational_reference_dt_s": float(args.operational_reference_dt),
        "n_boot": int(args.n_boot),
        "calibration_mode": calibration_mode,
        "freeze_calibration": args.freeze_calibration,
        "calibration": calibration,
    }
    print("\n=== SLA calibration (%s) ===" % calibration_mode)
    print(
        "  w_loss=%.3f | T_delay=%.3f ms | T_loss=%.4f | optimal_violation=%.4f"
        % (
            float(calibration["w_loss"]),
            float(calibration["t_delay_ms"]),
            float(calibration["t_loss"]),
            float(calibration["optimal_violation"]),
        )
    )
    runs = {}
    for seed in seeds:
        run = run_for_seed(rho, dt_s, config, seed=seed, nc_only=args.nc_only)
        runs[str(seed)] = run
        print_run_report(run)
    result = {"config": config, "nc_only": bool(args.nc_only), "runs": runs}
    write_json(args.out, result)
    print("\nwrote %s" % args.out)


if __name__ == "__main__":
    main()

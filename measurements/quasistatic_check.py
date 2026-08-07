#!/usr/bin/env python3
"""Phase 20R.6 -- decision-level quasistatic analyzer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from measurements.additivity_check import DELTA_MS, parse_int_list, stable_digest, tost_equivalence, write_json


MODE = "poisson"
RHO_BAR = 0.925
SEEDS = (101, 102, 103)
DURATION_S = 600.0
WINDOW_S = 60.0
OUT = "results/phase-20R/quasistatic_check.json"
STATE = "results/phase-20R/quasistatic_state.json"
RAW = "results/phase-20R/raw_quasistatic"
POINT_TIMEOUT_S = 150.0
PROBE_RATE_PPS = 5.0
PROBE_SIZE_BYTES = 1470


def build_plan(
    mode: str = MODE,
    rho_bar: float = RHO_BAR,
    seeds: Sequence[int] = SEEDS,
    duration_s: float = DURATION_S,
    window_s: float = WINDOW_S,
) -> Dict[str, Any]:
    rows = [
        {
            "mode": str(mode),
            "rho_bar": float(rho_bar),
            "seed": int(seed),
            "duration_s": float(duration_s),
            "window_s": float(window_s),
            "n_windows": int(round(float(duration_s) / float(window_s))),
        }
        for seed in seeds
    ]
    return {
        "phase": "20R.6",
        "kind": "quasistatic_design",
        "mode": str(mode),
        "rho_bar": float(rho_bar),
        "duration_s": float(duration_s),
        "window_s": float(window_s),
        "seeds": [int(seed) for seed in seeds],
        "rows": rows,
        "plan_digest": stable_digest(rows),
    }


def _load_rows(paths: Sequence[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for path in paths:
        if not path:
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rows = data if isinstance(data, list) else data.get("rows", [])
        for row in rows:
            if "windows" in row:
                for win in row["windows"]:
                    merged = {k: v for k, v in row.items() if k != "windows"}
                    merged.update(win)
                    out.append(merged)
            else:
                out.append(dict(row))
    return out


def _value(row: Mapping[str, Any], names: Sequence[str]) -> Optional[float]:
    for name in names:
        if row.get(name) is not None:
            return float(row[name])
    return None


def _frame(rows: Sequence[Mapping[str, Any]]) -> pd.DataFrame:
    flat = []
    for row in rows:
        measured = _value(row, ("measured_cost_ms", "dynamic_cost_ms", "observed_cost_ms", "cost_ms"))
        table = _value(row, ("table_cost_ms", "static_cost_ms", "predicted_cost_ms"))
        if measured is None or table is None:
            continue
        flat.append(
            {
                **dict(row),
                "seed": int(row["seed"]),
                "window_idx": int(row.get("window_idx", row.get("window", 0))),
                "measured_cost_ms": measured,
                "table_cost_ms": table,
                "diff_ms": measured - table,
            }
        )
    return pd.DataFrame(flat)


def _digest_report(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty or "trajectory_digest" not in df.columns:
        return {"available": False, "pass": False, "reason": "missing trajectory_digest"}
    per_seed = df.groupby("seed")["trajectory_digest"].nunique(dropna=True)
    bad = per_seed[per_seed != 1]
    return {
        "available": True,
        "pass": bool(bad.empty),
        "n_problem": int(len(bad)),
        "problems": [{"seed": int(seed), "n_digest": int(n)} for seed, n in bad.items()],
    }


def analyze(
    rows: Sequence[Mapping[str, Any]],
    mode: str = MODE,
    rho_bar: float = RHO_BAR,
    seeds: Sequence[int] = SEEDS,
    duration_s: float = DURATION_S,
    window_s: float = WINDOW_S,
    delta_ms: float = DELTA_MS,
) -> Dict[str, Any]:
    plan = build_plan(mode=mode, rho_bar=rho_bar, seeds=seeds, duration_s=duration_s, window_s=window_s)
    df = _frame(rows)
    report: Dict[str, Any] = {
        "phase": "20R.6",
        "script": "measurements.quasistatic_check",
        "kind": "decision_quasistatic_analysis",
        "delta_ms": float(delta_ms),
        "plan_digest": plan["plan_digest"],
        "summary": {
            "n_input_rows": int(len(rows)),
            "n_windows": int(len(df)),
            "evaluated": bool(not df.empty),
        },
        "checks": [],
    }
    if df.empty:
        report["summary"].update({"pass": False, "reason": "no rows with measured/table cost fields"})
        return report

    max_abs = float(np.max(np.abs(df["diff_ms"])))
    report["summary"].update(
        {
            "mean_diff_ms": float(np.mean(df["diff_ms"])),
            "max_abs_diff_ms": max_abs,
            "threshold_ms": float(delta_ms),
            "pass": bool(max_abs <= float(delta_ms)),
        }
    )
    for seed, group in df.groupby("seed", sort=True):
        report["checks"].append(
            {
                "seed": int(seed),
                "n_windows": int(len(group)),
                "mean_diff_ms": float(np.mean(group["diff_ms"])),
                "max_abs_diff_ms": float(np.max(np.abs(group["diff_ms"]))),
                **tost_equivalence(group["diff_ms"], delta_ms=delta_ms),
            }
        )
    report["paired_schedule"] = _digest_report(df)
    return report


def _save_state(path: str, state: Mapping[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def _load_state(path: str, plan: Mapping[str, Any]) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        state.setdefault("rows", [])
        state.setdefault("done_seeds", [])
        state.setdefault("failed_windows", [])
        state.setdefault("timeout_history", [])
        return state
    return {
        "phase": "20R.6",
        "kind": "quasistatic_live_state",
        "runner": "measurements.quasistatic_check",
        "plan_digest": str(plan["plan_digest"]),
        "rows": [],
        "done_seeds": [],
        "failed_windows": [],
        "timeout_history": [],
    }


def _calibration_cell(mode: str, rho_bar: float, calibration_path: str) -> Mapping[str, Any]:
    for cell in __import__("measurements.decision_error_v2", fromlist=["feasible_cells"]).feasible_cells(calibration_path, include_pc1=False):
        if str(cell["mode"]) == str(mode) and round(float(cell["rho_bar"]), 12) == round(float(rho_bar), 12):
            return cell
    raise KeyError("khong tim thay calibration cell mode=%s rho_bar=%.3f" % (mode, float(rho_bar)))


def _rho_windows(
    mode: str,
    rho_bar: float,
    seed: int,
    tau: float,
    n_windows: int,
    window_s: float,
    calibration_path: str,
) -> Tuple[np.ndarray, Mapping[str, Any]]:
    from measurements import decision_error_v2 as D

    cell = _calibration_cell(mode, rho_bar, calibration_path)
    sigma, sigma_source = D.resolve_sigma(cell)
    rho_mat = D.rho_matrix_from_cell(
        mode,
        float(rho_bar),
        float(sigma),
        int(seed),
        tau=float(tau),
        n=int(n_windows),
        dt=float(window_s),
    )
    return rho_mat, {**dict(cell), "sigma_rho": float(sigma), "sigma_rho_source": sigma_source}


def _tandem_table_cost(tt: Any, mode: str, rho_by_idx: Mapping[int, float], w_loss: float) -> Dict[str, float]:
    from mininet.topology_tandem import TANDEM_LINKS

    delay_sum = 0.0
    keep = 1.0
    for idx, (_name, t7_link, _bw, _q, _base) in enumerate(TANDEM_LINKS, start=1):
        delay, loss = tt.delay_loss(str(mode), t7_link, np.asarray([float(rho_by_idx[idx])], dtype=float))
        delay_sum += float(delay[0])
        keep *= 1.0 - float(loss[0])
    loss_path = 1.0 - keep
    return {"table_delay_ms": delay_sum, "table_loss": loss_path, "table_cost_ms": delay_sum + float(w_loss) * loss_path}


def _rho_by_tandem_idx(rho_row: np.ndarray) -> Dict[int, float]:
    from mininet.topology_tandem import TANDEM_LINKS
    from twin import topology_v7 as T7

    idx_of = {link: i for i, link in enumerate(T7.LINK_NAMES)}
    return {
        idx: float(rho_row[idx_of[t7_link]])
        for idx, (_name, t7_link, _bw, _q, _base) in enumerate(TANDEM_LINKS, start=1)
    }


def _live_arg_namespace(args: argparse.Namespace, seed: int) -> argparse.Namespace:
    return argparse.Namespace(
        raw_dir=args.raw_dir,
        duration=float(args.window_s),
        warmup=min(10.0, max(0.0, float(args.window_s) / 6.0)),
        calibration=args.calibration,
        modes=str(args.mode),
        rho_bar=str(args.rho_bar),
        seeds=str(seed),
        probe_rate=float(args.probe_rate),
        probe_size=int(args.probe_size),
    )


def run_live(args: argparse.Namespace) -> None:
    from measurements import additivity_live as AL
    from measurements import decision_error_v2 as D
    from mininet.link import Link
    from mininet.net import Mininet
    from mininet.node import OVSBridge
    from mininet.topology_tandem import TandemTopo, configure_qdiscs

    seeds = parse_int_list(args.seeds)
    plan = build_plan(args.mode, args.rho_bar, seeds, args.duration_s, args.window_s)
    state = _load_state(args.state, plan)
    n_windows = int(round(float(args.duration_s) / float(args.window_s)))
    done = set(int(seed) for seed in state.get("done_seeds", []))
    todo = [seed for seed in seeds if int(seed) not in done]
    print(
        "Ke hoach %d seed x %d cua so | da xong %d seed | phien nay %d seed (~%.1f phut)"
        % (
            len(seeds),
            n_windows,
            len(done),
            len(todo),
            len(todo) * n_windows * (float(args.window_s) + 13.0) / 60.0,
        )
    )
    if args.plan_only_live:
        return

    os.makedirs(args.raw_dir, exist_ok=True)
    tt = D.TruthTable(args.truth_table)
    saved_sysctl = AL.disable_ipv6_on_new_links()
    net = None
    try:
        net = Mininet(topo=TandemTopo(), link=Link, switch=OVSBridge, controller=None)
        net.start()
        state["qdisc_proof"] = configure_qdiscs(net)
        state["qdisc_proof"]["sysctl_saved"] = saved_sysctl
        qdisc_ifaces = AL.measured_qdisc_ifaces_from_proof(state["qdisc_proof"])
        _save_state(args.state, state)
        t0 = time.time()
        for seed_i, seed in enumerate(todo, start=1):
            rho_mat, cell = _rho_windows(args.mode, args.rho_bar, int(seed), args.tau, n_windows, args.window_s, args.calibration)
            windows = []
            trace_window_digests = []
            for window_idx in range(n_windows):
                rho_by_idx = _rho_by_tandem_idx(rho_mat[window_idx])
                point = {
                    "idx": int(seed) * 100 + int(window_idx) + 1,
                    "pid": "20r6_qs_s%d_w%02d_%s_r%04d" % (
                        int(seed),
                        int(window_idx),
                        str(args.mode),
                        int(round(float(args.rho_bar) * 1000)),
                    ),
                    "branch": "C",
                    "mode": str(args.mode),
                    "rho_bar": float(args.rho_bar),
                    "seed": int(seed),
                    "path": "T123",
                    "link_idx": None,
                    "rho_by_link_idx": rho_by_idx,
                }
                largs = _live_arg_namespace(args, int(seed))
                try:
                    with AL.deadline(args.point_timeout, "quasistatic seed=%d window=%d" % (int(seed), int(window_idx))):
                        live = AL.measure_point(net, point, largs, qdisc_ifaces=qdisc_ifaces)
                except AL.PointTimeout as exc:
                    AL.cleanup_live_processes()
                    timeout_row = {
                        **point,
                        "reason": str(exc),
                        "timeout_s": float(args.point_timeout),
                        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    state.setdefault("timeout_history", []).append(timeout_row)
                    _save_state(args.state, state)
                    raise SystemExit(3)
                live["gate_fail"] = AL.gate_live(live)
                live["attempt"] = 1
                if live["gate_fail"] and AL.retryable_gate_fail(live["gate_fail"]):
                    print("      * fail: %s -> chay lai 1 lan" % ",".join(live["gate_fail"]))
                    with AL.deadline(args.point_timeout, "quasistatic retry seed=%d window=%d" % (int(seed), int(window_idx))):
                        live2 = AL.measure_point(net, point, largs, qdisc_ifaces=qdisc_ifaces)
                    live2["gate_fail"] = AL.gate_live(live2)
                    live2["attempt"] = 2
                    live2["attempt1_fail"] = live["gate_fail"]
                    live = live2
                elif live["gate_fail"]:
                    print("      * fail: %s -> khong retry vi la validity gate" % ",".join(live["gate_fail"]))
                table = _tandem_table_cost(tt, args.mode, rho_by_idx, float(cell["w_loss"]))
                trace_window_digests.append(str(live["trajectory_digest"]))
                win = {
                    "window_idx": int(window_idx),
                    "t_lo_s": float(window_idx) * float(args.window_s),
                    "t_hi_s": float(window_idx + 1) * float(args.window_s),
                    "rho_by_link_idx": rho_by_idx,
                    "measured_cost_ms": float(live["cost_ms"]),
                    "measured_delay_ms": float(live["q_mean_ms"]),
                    "measured_loss": float(live["loss"]),
                    "table_cost_ms": float(table["table_cost_ms"]),
                    "table_delay_ms": float(table["table_delay_ms"]),
                    "table_loss": float(table["table_loss"]),
                    "diff_ms": float(live["cost_ms"]) - float(table["table_cost_ms"]),
                    "gate_fail": list(live.get("gate_fail", [])),
                    "window_trajectory_digest": str(live["trajectory_digest"]),
                    "probe_intrusion_ratio": float(live["probe_intrusion_ratio"]),
                    "max_abs_rate_error": float(live["max_abs_rate_error"]),
                    "direct_packets_before": dict(live.get("direct_packets_before", {})),
                    "direct_packets_after": dict(live.get("direct_packets_after", {})),
                    "direct_packets_delta": dict(live.get("direct_packets_delta", {})),
                    "vl1g_run_pass": bool(live.get("vl1g_run_pass", True)),
                    "socket_drops": int(live["socket_drops"]),
                    "n_foreign": int(live["n_foreign"]),
                }
                windows.append(win)
                if win["gate_fail"]:
                    state.setdefault("failed_windows", []).append({**point, **win})
                eta = (time.time() - t0) / max(seed_i - 1 + (window_idx + 1) / float(n_windows), 1e-9)
                eta = eta * (len(todo) - seed_i + (n_windows - window_idx - 1) / float(n_windows)) / 60.0
                print(
                    "[seed %d/%d w%02d/%02d] cost=%.3f table=%.3f diff=%+.3f | %-4s (con %.1f phut)"
                    % (
                        seed_i,
                        len(todo),
                        window_idx + 1,
                        n_windows,
                        win["measured_cost_ms"],
                        win["table_cost_ms"],
                        win["diff_ms"],
                        "OK" if not win["gate_fail"] else "FAIL",
                        eta,
                    )
                )
                _save_state(args.state, state)
            seed_row = {
                "mode": str(args.mode),
                "rho_bar": float(args.rho_bar),
                "seed": int(seed),
                "tau_rho": float(args.tau),
                "duration_s": float(args.duration_s),
                "window_s": float(args.window_s),
                "sigma_rho": float(cell["sigma_rho"]),
                "sigma_rho_source": str(cell["sigma_rho_source"]),
                "w_loss": float(cell["w_loss"]),
                "trajectory_digest": stable_digest(trace_window_digests),
                "windows": windows,
                "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            state.setdefault("rows", []).append(seed_row)
            state.setdefault("done_seeds", []).append(int(seed))
            _save_state(args.state, state)
    finally:
        if net is not None:
            AL.stop_net_best_effort(net, args.stop_timeout)
        AL.restore_sysctl(saved_sysctl)
        _save_state(args.state, state)
    print("state -> %s" % args.state)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-state", default="", help="comma-separated JSON state/result files containing quasistatic rows")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--state", default=STATE)
    ap.add_argument("--truth-table", default="results/phase-20R/truth_table.parquet")
    ap.add_argument("--calibration", default="results/phase-20R/sla_calibration.json")
    ap.add_argument("--mode", default=MODE)
    ap.add_argument("--rho-bar", type=float, default=RHO_BAR)
    ap.add_argument("--seeds", default=",".join(str(seed) for seed in SEEDS))
    ap.add_argument("--duration-s", "--duration", dest="duration_s", type=float, default=DURATION_S)
    ap.add_argument("--window-s", "--window", dest="window_s", type=float, default=WINDOW_S)
    ap.add_argument("--tau", type=float, default=1.0)
    ap.add_argument("--raw-dir", default=RAW)
    ap.add_argument("--probe-rate", type=float, default=PROBE_RATE_PPS)
    ap.add_argument("--probe-size", type=int, default=PROBE_SIZE_BYTES)
    ap.add_argument("--point-timeout", type=float, default=POINT_TIMEOUT_S)
    ap.add_argument("--stop-timeout", type=float, default=20.0)
    ap.add_argument("--delta-ms", type=float, default=DELTA_MS)
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--plan-only-live", action="store_true")
    ap.add_argument("--write-plan", default="")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    args = ap.parse_args(argv)

    seeds = parse_int_list(args.seeds)
    plan = build_plan(args.mode, args.rho_bar, seeds, args.duration_s, args.window_s)
    if args.live:
        run_live(args)
        return 0
    if args.plan_only:
        print(json.dumps({"plan_digest": plan["plan_digest"], "rows": len(plan["rows"]), "n_windows": plan["rows"][0]["n_windows"]}, indent=2, sort_keys=True))
        return 0
    if args.write_plan:
        write_json(args.write_plan, plan)
        print("plan rows=%d -> %s" % (len(plan["rows"]), args.write_plan))
        return 0
    paths = tuple(part.strip() for part in str(args.from_state).split(",") if part.strip())
    if args.analyze and not paths:
        paths = (args.state,)
    report = analyze(_load_rows(paths), args.mode, args.rho_bar, seeds, args.duration_s, args.window_s, args.delta_ms)
    write_json(args.out, report)
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    print("quasistatic -> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

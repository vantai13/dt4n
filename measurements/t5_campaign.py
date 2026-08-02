#!/usr/bin/env python3
"""Phase T / T.5 -- live campaign runner with checkpoint/resume."""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from typing import Any, Dict, List, Optional, Sequence

from measurements.gate_specs import gate_names_by_kind
from measurements.provenance import env_fingerprint
from measurements.t4_validate import gate_row, phase_l_q_refs, phase_l_seed_refs
from mininet.load_spec import (
    FRAME_BG,
    FRAME_PROBE,
    PROBE_PPS,
    capacity_bytes_per_s,
)
from mininet.rho_schedule import build_varying_schedule
from mininet.rho_spec import DT_DEFAULT, ou_trajectory, sigma_from_a
from twin.link_model_v2 import LinkModelV2


MODES2 = ("h2", "poisson")
RHO_BAR = (0.70, 0.85, 0.925, 0.98)
A_LEVELS = (0.20, 0.90)
TAUS = (0.2, 1.0, 5.0)
SEEDS = (11, 12, 13, 14, 15)
BW, Q = 6.0, 13
DUR, WARM, DT = 105.0, 15.0, DT_DEFAULT
PHASE_L_DUR, PHASE_L_WARM = 70.0, 10.0
PORT = 5555
RAW = "results/phase-T/raw"
STATE = "results/phase-T/campaign_state.json"
SEALED = "results/phase-T/sealed"
ORDER_SEED = 7000
SENTINEL_EVERY = 30
SENTINEL = {
    "mode": "h2",
    "rho_bar": 0.85,
    "a": 0.90,
    "tau_rho": 1.0,
    "seed": 999,
    "block": "S",
}
RG = "python3 -m measurements.rho_gen"
PB = "python3 -m measurements.owd_probe"
MODEL_PATH = "results/phase-L/link_model_v2_fit.json"
PHASE_L_STATE = "results/phase-L/campaign_state.json"

GATES_TRANSIENT = set(gate_names_by_kind("transient"))
GATES_DETERMINISTIC = set(gate_names_by_kind("deterministic"))
GATE_FIELDS = {
    "idx",
    "pid",
    "block",
    "mode",
    "rho_bar",
    "a",
    "tau_rho",
    "seed",
    "bw",
    "q",
    "dt",
    "duration_s",
    "warmup_s",
    "meas_s",
    "attempt",
    "attempt1_fail",
    "env",
    "wall_utc",
    "gates",
    "gate_fail",
    "trajectory_digest",
    "schedule_digest",
    "ca_operational",
    "ca_operational_se",
    "ca_operational_thr",
    "ca_operational_z",
    "rho_bias",
    "rho_bias_sd_pred",
    "rho_bias_z",
    "vt5a_delegation",
    "vt5a_phase_l_digest",
    "vt5b_ref_n",
    "vt5b_z",
    "vt5b_same_seed_gate_exempt",
    "vt5b_same_seed_rel",
    "socket_drops",
    "n_foreign",
    "n_late_ratio",
    "max_late_ms",
    "n_recv_unique",
    "loss",
}


Point = Dict[str, Any]
State = Dict[str, Any]


def _pid(point: Point, idx: int, stage: str) -> str:
    return "t5_%s_%04d_%s_%s_r%04d_a%03d_t%04d_s%d" % (
        stage,
        idx,
        point["block"],
        point["mode"],
        int(round(float(point["rho_bar"]) * 1000)),
        int(round(float(point["a"]) * 100)),
        int(round(float(point["tau_rho"]) * 1000)),
        int(point["seed"]),
    )


def _finalize(
    points: List[Point],
    stage: str,
    duration_s: float = DUR,
    warmup_s: float = WARM,
) -> List[Point]:
    for idx, point in enumerate(points):
        point["idx"] = idx
        point["pid"] = _pid(point, idx, stage)
        point["bw"] = BW
        point["q"] = Q
        point["duration_s"] = float(duration_s)
        point["warmup_s"] = float(warmup_s)
        point["dt"] = DT
    return points


def build_smoke_plan() -> List[Point]:
    points: List[Point] = []
    for mode in ("h2", "poisson", "cbr"):
        for a in A_LEVELS:
            points.append(
                {
                    "mode": mode,
                    "rho_bar": 0.98 if mode == "cbr" else 0.85,
                    "a": a,
                    "tau_rho": 1.0,
                    "seed": 101 + len(points),
                    "block": "Z",
                }
            )
    return _finalize(points, "smoke")


def build_controls_plan() -> List[Point]:
    points: List[Point] = []
    for mode in ("h2", "poisson", "cbr"):
        rhos = RHO_BAR if mode != "cbr" else (0.98,)
        for rho_bar in rhos:
            for seed in SEEDS:
                points.append(
                    {
                        "mode": mode,
                        "rho_bar": rho_bar,
                        "a": 0.0,
                        "tau_rho": 1.0,
                        "seed": seed,
                        "block": "C",
                    }
                )
    random.Random(ORDER_SEED + 1).shuffle(points)
    return _finalize(points, "controls")


def build_controls_sameseed_plan() -> List[Point]:
    """C' controls: Phase-L duration/warm-up for same-seed V-T5."""
    points: List[Point] = []
    for mode in ("h2", "poisson", "cbr"):
        rhos = RHO_BAR if mode != "cbr" else (0.98,)
        for rho_bar in rhos:
            for seed in SEEDS:
                points.append(
                    {
                        "mode": mode,
                        "rho_bar": rho_bar,
                        "a": 0.0,
                        "tau_rho": 1.0,
                        "seed": seed,
                        "block": "Cprime",
                    }
                )
    random.Random(ORDER_SEED + 2).shuffle(points)
    return _finalize(
        points,
        "controls_sameseed",
        duration_s=PHASE_L_DUR,
        warmup_s=PHASE_L_WARM,
    )


def build_main_plan() -> List[Point]:
    regular: List[Point] = []
    for mode in MODES2:
        for rho_bar in RHO_BAR:
            for a in A_LEVELS:
                for tau in TAUS:
                    for seed in SEEDS:
                        regular.append(
                            {
                                "mode": mode,
                                "rho_bar": rho_bar,
                                "a": a,
                                "tau_rho": tau,
                                "seed": seed,
                                "block": "A",
                            }
                        )
    for a in A_LEVELS:
        for tau in TAUS:
            for seed in SEEDS:
                regular.append(
                    {
                        "mode": "cbr",
                        "rho_bar": 0.98,
                        "a": a,
                        "tau_rho": tau,
                        "seed": seed,
                        "block": "B",
                    }
                )
    random.Random(ORDER_SEED).shuffle(regular)

    out: List[Point] = []
    for i, point in enumerate(regular, 1):
        out.append(point)
        if i % SENTINEL_EVERY == 0:
            out.append(dict(SENTINEL))
    return _finalize(out, "main")


def build_plan(stage: str) -> List[Point]:
    if stage == "smoke":
        return build_smoke_plan()
    if stage == "controls":
        return build_controls_plan()
    if stage in ("controls-sameseed", "controls-samesed"):
        return build_controls_sameseed_plan()
    if stage == "main":
        return build_main_plan()
    raise ValueError("stage khong hop le: %s" % stage)


def load_state(path: str = STATE) -> State:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"done_idx": [], "rows": [], "sentinels": []}


def save_state(state: State, path: str = STATE) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def should_retry(gate_fail: Sequence[str]) -> bool:
    """Retry only failures that can change across identical reruns."""
    fail = set(str(name) for name in gate_fail)
    return bool(fail) and fail <= GATES_TRANSIENT


def public_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Visible checkpoint row: gate/provenance only, no sealed response metrics."""
    return {key: row[key] for key in sorted(GATE_FIELDS) if key in row}


def sealed_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Fields withheld until unblinding."""
    return {key: value for key, value in row.items() if key not in GATE_FIELDS}


def save_sealed_row(row: Dict[str, Any], sealed_dir: str = SEALED) -> None:
    os.makedirs(sealed_dir, exist_ok=True)
    pid = str(row["pid"])
    payload = {"pid": pid, "sealed": sealed_row(row)}
    tmp = os.path.join(sealed_dir, pid + ".json.tmp")
    out = os.path.join(sealed_dir, pid + ".json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
    os.replace(tmp, out)


def record_row(
    state: State,
    row: Dict[str, Any],
    state_path: str,
    sealed_dir: str,
    complete: bool,
) -> None:
    save_sealed_row(row, sealed_dir)
    idx = int(row["idx"])
    state["rows"] = [
        old for old in state.get("rows", []) if int(old.get("idx", -1)) != idx
    ]
    state["failed_rows"] = [
        old for old in state.get("failed_rows", []) if int(old.get("idx", -1)) != idx
    ]
    target = "rows" if complete else "failed_rows"
    state.setdefault(target, []).append(public_row(row))
    if complete:
        done = set(int(i) for i in state.get("done_idx", []))
        if idx not in done:
            state.setdefault("done_idx", []).append(idx)
        if row.get("block") == "S":
            state.setdefault("sentinels", []).append(
                {
                    "idx": row["idx"],
                    "pid": row["pid"],
                    "t": row["wall_utc"],
                    "gate_fail": list(row.get("gate_fail", [])),
                }
            )
    else:
        state["done_idx"] = [
            old for old in state.get("done_idx", []) if int(old) != idx
        ]
    save_state(state, state_path)


def select_todo(
    plan: Sequence[Point],
    state: State,
    session: Optional[int] = None,
    n_sessions: int = 3,
    max_points: Optional[int] = None,
) -> List[Point]:
    done = set(int(i) for i in state.get("done_idx", []))
    todo = [p for p in plan if int(p["idx"]) not in done]
    if session is not None:
        per = int(math.ceil(len(plan) / float(n_sessions)))
        lo = (int(session) - 1) * per
        hi = int(session) * per
        todo = [p for p in todo if lo <= int(p["idx"]) < hi]
    return todo[: int(max_points)] if max_points is not None else todo


def make_traj(point: Point):
    sigma = 0.0 if float(point["a"]) == 0.0 else sigma_from_a(point["rho_bar"], point["a"])
    n_steps = int(round(float(point["duration_s"]) / float(point["dt"])))
    return ou_trajectory(
        point["rho_bar"],
        sigma,
        point["tau_rho"],
        n_steps,
        point["seed"],
        dt=point["dt"],
    )


def load_phase_l_refs(path: str = PHASE_L_STATE):
    with open(path, "r", encoding="utf-8") as f:
        phase_l_state = json.load(f)
    rows = phase_l_state.get("rows", [])
    return (
        phase_l_q_refs(rows, BW, Q, PROBE_PPS),
        phase_l_seed_refs(rows, BW, Q, PROBE_PPS),
    )


def rho_bias_from_bgtx(
    tx_path: str,
    traj,
    bw_mbps: float,
    probe_pps: float = PROBE_PPS,
    warmup_s: float = WARM,
    window_s: float = 0.100,
) -> float:
    from measurements.owd_analyze import REC_TX, load

    rows = load(tx_path, REC_TX)
    if not rows:
        return float("nan")
    t0 = float(rows[0][1])
    rel = [float(row[1]) - t0 for row in rows]
    cap = capacity_bytes_per_s(bw_mbps)
    n_bins = int((traj.duration_s - float(warmup_s)) // float(window_s))
    if n_bins <= 0:
        return float("nan")

    diffs: List[float] = []
    pos = 0
    for j in range(n_bins):
        lo = float(warmup_s) + j * float(window_s)
        hi = lo + float(window_s)
        while pos < len(rel) and rel[pos] < lo:
            pos += 1
        k = pos
        while k < len(rel) and rel[k] < hi:
            k += 1
        bg_pps = (k - pos) / float(window_s)
        rho_hat = (bg_pps * FRAME_BG + float(probe_pps) * FRAME_PROBE) / cap
        i0 = max(0, int(lo / traj.dt))
        i1 = min(traj.n_steps, max(i0 + 1, int(hi / traj.dt)))
        rho_design = sum(traj.rho[i0:i1]) / (i1 - i0)
        diffs.append(rho_hat - rho_design)
    return sum(diffs) / len(diffs)


def sentinel_summary(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "n": len(rows),
        "n_fail": sum(1 for row in rows if row.get("gate_fail")),
    }


def campaign_summary(state: State, plan: Sequence[Point]) -> Dict[str, Any]:
    rows = state.get("rows", [])
    failed_rows = state.get("failed_rows", [])
    fails = [row for row in rows if row.get("gate_fail")]
    done = len(set(int(i) for i in state.get("done_idx", [])))
    return {
        "n_plan": len(plan),
        "n_done": done,
        "n_rows": len(rows),
        "n_fail": len(fails) + len(failed_rows),
        "n_failed_rows": len(failed_rows),
        "coverage": done / len(plan) if plan else 0.0,
        "sentinel": sentinel_summary(state.get("sentinels", [])),
    }


def measure(net: Any, point: Point, model, phase_l_ref=None, phase_l_seed_ref=None) -> Dict[str, Any]:
    from measurements.owd_analyze import analyze

    h1, h2 = net.get("h1"), net.get("h2")
    cwd = os.getcwd()
    prefix = "%s/%s" % (RAW, point["pid"])
    duration_s = float(point.get("duration_s", DUR))
    warmup_s = float(point.get("warmup_s", WARM))
    h1.cmd("pkill -f 'measurements.rho_gen' 2>/dev/null")
    h2.cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
    time.sleep(0.2)
    h2.cmd(
        "cd %s && %s recv --port %d --duration %g --out-prefix %s >/dev/null 2>&1 &"
        % (cwd, PB, PORT, duration_s + 6.0, prefix)
    )
    time.sleep(0.8)
    h1.cmd(
        "cd %s && %s --dst 10.0.0.2 --port %d --bw %g --mode %s "
        "--duration %g --seed %d --run-id %d --out-prefix %s "
        "--rho-bar %g --a %g --tau-rho %g --dt %g "
        ">/dev/null 2>&1"
        % (
            cwd,
            RG,
            PORT,
            BW,
            point["mode"],
            duration_s,
            point["seed"],
            point["idx"],
            prefix,
            point["rho_bar"],
            point["a"],
            point["tau_rho"],
            DT,
        )
    )
    time.sleep(6.5)

    bg = analyze(prefix + "_bg.bin", prefix + "_bgtx.bin", warmup_s=warmup_s)
    probe = None
    if os.path.getsize(prefix + "_probe.bin") > 0:
        probe = analyze(prefix + "_probe.bin", prefix + "_prtx.bin", warmup_s=warmup_s)
    with open(prefix + "_tx.meta.json", "r", encoding="utf-8") as f:
        tx = json.load(f)
    with open(prefix + "_rx.meta.json", "r", encoding="utf-8") as f:
        rx = json.load(f)

    traj = make_traj(point)
    sched = build_varying_schedule(point["mode"], traj, BW, point["seed"])
    row = {
        **point,
        "warmup_s": warmup_s,
        "meas_s": duration_s - warmup_s,
        "trajectory_digest": tx["trajectory"]["trajectory_digest"],
        "schedule_digest": tx["schedule"]["schedule_digest"],
        "rho_bias": rho_bias_from_bgtx(prefix + "_bgtx.bin", traj, BW, warmup_s=warmup_s),
        "q_mean_ms": bg["owd_ms"]["mean"],
        "q_sd_ms": bg["owd_ms"]["sd"],
        "q_p50_ms": bg["owd_ms"]["p50"],
        "q_p90_ms": bg["owd_ms"]["p90"],
        "q_p95_ms": bg["owd_ms"]["p95"],
        "q_p99_ms": bg["owd_ms"]["p99"],
        "loss": bg["loss_rate"],
        "n_recv_unique": bg["counts"]["n_recv_unique"],
        "probe_mean_ms": probe["owd_ms"]["mean"] if probe else None,
        "delta_pasta_ms": bg["owd_ms"]["mean"] - probe["owd_ms"]["mean"] if probe else None,
        "se_batch_ms": bg["steady_state"].get("se_batch_means_ms"),
        "se_naive_ms": bg["steady_state"].get("se_naive_ms"),
        "n_late_ratio": tx["counts"]["n_late"]
        / max(tx["counts"]["n_bg_sent"] + tx["counts"]["n_probe_sent"], 1),
        "max_late_ms": tx["counts"]["max_late_ms"],
        "socket_drops": rx["socket_drops_delta"],
        "n_foreign": rx["n_foreign_packets"],
        "env": env_fingerprint(),
        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    gates = gate_row(
        row,
        traj,
        sched,
        model,
        model.sigma(point["mode"], BW, Q, point["rho_bar"]),
        phase_l_ref=phase_l_ref,
        phase_l_seed_ref=phase_l_seed_ref,
    )
    row["gate_fail"] = [name for name, ok in gates.items() if not ok]
    row["gates"] = gates
    return row


def run_live(args: argparse.Namespace) -> None:
    plan = build_plan(args.stage)
    state = load_state(args.state)
    if args.force_idx is not None:
        if args.session is not None:
            raise SystemExit("--force-idx khong di cung --session")
        by_idx = {int(point["idx"]): point for point in plan}
        if int(args.force_idx) not in by_idx:
            raise SystemExit("--force-idx khong co trong plan: %s" % args.force_idx)
        todo = [by_idx[int(args.force_idx)]]
    else:
        todo = select_todo(plan, state, args.session, args.n_sessions, args.max_points)
    print(
        "T5 %s plan %d diem | da xong %d | phien nay %d diem (~%.1f gio)"
        % (
            args.stage,
            len(plan),
            len(set(int(i) for i in state.get("done_idx", []))),
            len(todo),
            sum(float(point.get("duration_s", DUR)) + 12.0 for point in todo) / 3600.0,
        )
    )
    if args.plan_only:
        for point in todo:
            print(
                "%04d %-7s rho=%.3f a=%.2f tau=%g seed=%d block=%s"
                % (
                    point["idx"],
                    point["mode"],
                    point["rho_bar"],
                    point["a"],
                    point["tau_rho"],
                    point["seed"],
                    point["block"],
                )
            )
        return

    from mininet.link import Link
    from mininet.net import Mininet
    from mininet.node import OVSBridge
    from mininet.topology_split_qdisc import (
        SplitQdiscTopo,
        intf_toward,
        setup_measure_qdisc,
        setup_return_qdisc,
    )

    model = LinkModelV2.load(MODEL_PATH)
    phase_l_ref = phase_l_seed_ref = None
    if args.stage in ("controls", "controls-sameseed", "controls-samesed"):
        phase_l_ref, phase_l_seed_ref = load_phase_l_refs()
        if args.stage == "controls":
            phase_l_seed_ref = None
    os.makedirs(RAW, exist_ok=True)
    net = Mininet(topo=SplitQdiscTopo(), link=Link, switch=OVSBridge, controller=None)
    net.start()
    try:
        s1, s2 = net.get("s1"), net.get("s2")
        setup_return_qdisc(intf_toward(s2, "s1"), 3.0)
        setup_measure_qdisc(intf_toward(s1, "s2"), BW, Q)
        t0 = time.time()
        for k, point in enumerate(todo, 1):
            row = measure(net, point, model, phase_l_ref=phase_l_ref, phase_l_seed_ref=phase_l_seed_ref)
            row["attempt"] = 1
            if row["gate_fail"]:
                if should_retry(row["gate_fail"]):
                    print(
                        "      * gate fail transient: %s -> chay lai 1 lan"
                        % ",".join(row["gate_fail"])
                    )
                    row2 = measure(
                        net,
                        point,
                        model,
                        phase_l_ref=phase_l_ref,
                        phase_l_seed_ref=phase_l_seed_ref,
                    )
                    row2["attempt"] = 2
                    row2["attempt1_fail"] = row["gate_fail"]
                    row = row2
                else:
                    record_row(state, row, args.state, args.sealed_dir, complete=False)
                    raise SystemExit(
                        "gate deterministic fail: %s; dung chien dich"
                        % ",".join(row["gate_fail"])
                    )

            if row["gate_fail"]:
                record_row(state, row, args.state, args.sealed_dir, complete=False)
                raise SystemExit(
                    "gate van fail sau retry: %s; dung chien dich"
                    % ",".join(row["gate_fail"])
                )

            record_row(state, row, args.state, args.sealed_dir, complete=True)

            eta = (time.time() - t0) / k * (len(todo) - k) / 3600.0
            tag = " [CANH]" if point["block"] == "S" else ""
            print(
                "[%4d/%4d] %-7s rho=%.3f a=%.2f tau=%g seed=%3d | %s (con %.1f h)%s"
                % (
                    k,
                    len(todo),
                    point["mode"],
                    point["rho_bar"],
                    point["a"],
                    point["tau_rho"],
                    point["seed"],
                    "OK" if not row["gate_fail"] else "FAIL",
                    eta,
                    tag,
                )
            )
    finally:
        try:
            net.get("h1").cmd("pkill -f 'measurements.rho_gen' 2>/dev/null")
            net.get("h2").cmd("pkill -f 'measurements.owd_probe' 2>/dev/null")
        except Exception:
            pass
        net.stop()
        save_state(state, args.state)

    summary = campaign_summary(state, plan)
    print(
        "\nTONG KET %s: %d/%d diem, fail sau rerun=%d"
        % (args.stage, summary["n_done"], summary["n_plan"], summary["n_fail"])
    )
    print("state -> %s" % args.state)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase T / T.5 campaign")
    parser.add_argument(
        "--stage",
        choices=("smoke", "controls", "controls-sameseed", "controls-samesed", "main"),
        required=True,
    )
    parser.add_argument("--state", default=STATE)
    parser.add_argument("--session", type=int, default=None)
    parser.add_argument("--n-sessions", type=int, default=3)
    parser.add_argument("--max-points", type=int, default=None)
    parser.add_argument("--force-idx", type=int, default=None)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--sealed-dir", default=SEALED)
    args = parser.parse_args()
    if args.session is not None and not (1 <= args.session <= args.n_sessions):
        raise SystemExit("--session phai nam trong 1..%d" % args.n_sessions)
    run_live(args)


if __name__ == "__main__":
    main()

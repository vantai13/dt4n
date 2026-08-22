#!/usr/bin/env python3
"""Phase 20R.4 -- fine rho-grid Mininet campaign with checkpoint/resume.

This reuses the Phase L live measurement primitive, but changes the design:
only rho levels missing from Phase L are measured, the run order is shuffled
with a fixed seed, and a Phase L sentinel is inserted every 30 regular rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from measurements import l6_campaign as L6
from measurements.provenance import env_fingerprint
from twin import cost_v2 as C
from twin import topology_v7 as T7


STEP = {"cbr": 0.05, "poisson": 0.02, "h2": 0.02}
SEEDS = (21, 22, 23, 24, 25)
CONTINUITY_SEED = 31
PHASE_L_RHO = (0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.925, 0.95, 0.98, 1.00, 1.02, 1.05)
SHUFFLE_SEED = 20260804
SIGMA_MARGIN = 3.5
NOISE_FLOOR_MS = 0.4646
INTERP_BUDGET_MS = 0.10 * NOISE_FLOOR_MS

CALIBRATION = "results/LIVE/phase-20R/sla_calibration.json"
STATE = "results/SUPERSEDED/phase-20R/campaign_state.json"
SMOKE_STATE = "results/SMOKE/phase-20R/smoke_state.json"
CONTINUITY_STATE = "results/SUPERSEDED/phase-20R/continuity_state.json"
RAW = "results/RAW/phase-20R/raw"
RUNLOG = "results/SUPERSEDED/phase-20R/RUNLOG.md"

DUR = L6.DUR
WARM = L6.WARM
DELAY_MS = L6.DELAY_MS
PORT = L6.PORT
REF = L6.REF
SENTINEL = L6.SENTINEL
SENTINEL_REF = L6.SENTINEL_REF
SENTINEL_EVERY = L6.SENTINEL_EVERY

Point = Dict[str, Any]
State = Dict[str, Any]


class PointTimeout(RuntimeError):
    """Raised when one live measurement point exceeds its wall-clock budget."""

CONTINUITY_POINTS: Tuple[Tuple[str, float, int, float], ...] = (
    ("cbr", 4.0, 10, 0.70),
    ("cbr", 6.0, 13, 0.80),
    ("cbr", 8.0, 18, 0.80),
    ("poisson", 4.0, 10, 0.90),
    ("poisson", 6.0, 13, 0.90),
    ("poisson", 8.0, 18, 0.90),
    ("h2", 6.0, 13, 0.90),
    ("h2", 8.0, 18, 0.85),
)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_digest(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def git_status_porcelain() -> List[str]:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    except Exception:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _status_path(line: str) -> str:
    path = line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip()


def is_campaign_output_path(path: str) -> bool:
    """Return whether a dirty path is an expected live-output file."""
    allowed_exact = {
        "logs/20r4_00_smoke.log",
        "logs/20r4_01_continuity.log",
        "logs/20r4_02_full.log",
        "results/SUPERSEDED/phase-20R/RUNLOG.md",
        "results/SMOKE/phase-20R/smoke_state.json",
        "results/SUPERSEDED/phase-20R/continuity_state.json",
        "results/SUPERSEDED/phase-20R/continuity_check.json",
        "results/SUPERSEDED/phase-20R/campaign_state.json",
        "results/SUPERSEDED/phase-20R/sentinel_control.json",
        "results/SUPERSEDED/phase-20R/truth_table.csv",
        "results/LIVE/phase-20R/truth_table.parquet",
    }
    if path in allowed_exact:
        return True
    return path.startswith("results/RAW/phase-20R/raw/")


def campaign_clean_status() -> Dict[str, Any]:
    """Git cleanliness for provenance, ignoring this campaign's outputs.

    Raw ``git status`` becomes dirty as soon as ``campaign_state.json`` is
    written. For row provenance we need to know whether code/config changed, not
    whether the checkpoint advanced. Both views are recorded.
    """
    raw = git_status_porcelain()
    relevant = [line for line in raw if not is_campaign_output_path(_status_path(line))]
    return {
        "git_dirty_raw": bool(raw),
        "git_status_raw": raw,
        "git_dirty": bool(relevant),
        "git_status_relevant": relevant,
        "ignored_campaign_output": [line for line in raw if is_campaign_output_path(_status_path(line))],
    }


def run_environment_fingerprint() -> Dict[str, Any]:
    env = env_fingerprint()
    clean = campaign_clean_status()
    env["git_dirty_raw"] = clean["git_dirty_raw"]
    env["git_status_raw"] = clean["git_status_raw"]
    env["git_dirty"] = clean["git_dirty"]
    env["git_status_relevant"] = clean["git_status_relevant"]
    env["ignored_campaign_output"] = clean["ignored_campaign_output"]
    return env


def _timeout_handler(_signum: int, _frame: object) -> None:
    raise PointTimeout("live measurement exceeded deadline")


class deadline:
    """Signal-based wall-clock deadline for blocking Mininet host.cmd calls."""

    def __init__(self, seconds: float, label: str):
        self.seconds = float(seconds)
        self.label = label
        self._old_handler = None
        self._old_timer = None

    def __enter__(self) -> None:
        self._old_handler = signal.getsignal(signal.SIGALRM)
        self._old_timer = signal.setitimer(signal.ITIMER_REAL, self.seconds)
        signal.signal(signal.SIGALRM, _timeout_handler)

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        if self._old_handler is not None:
            signal.signal(signal.SIGALRM, self._old_handler)
        if self._old_timer and self._old_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, self._old_timer[0], self._old_timer[1])
        if exc_type is PointTimeout and exc is not None:
            exc.args = ("%s timed out after %.1f s" % (self.label, self.seconds),)
        return False


def cleanup_live_processes() -> None:
    """Kill leftover point-level helpers without using Mininet's PTY shell."""
    for pattern in ("measurements.load_gen", "measurements.owd_probe"):
        try:
            subprocess.run(
                ["pkill", "-f", pattern],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5.0,
                check=False,
            )
        except Exception:
            pass


def stop_net_best_effort(net: Any, timeout_s: float) -> None:
    cleanup_live_processes()
    try:
        with deadline(timeout_s, "net.stop"):
            net.stop()
    except PointTimeout as exc:
        print("WARNING: %s; run `sudo mn -c` before resume" % exc, file=sys.stderr)
    except Exception as exc:
        print("WARNING: net.stop failed: %s; run `sudo mn -c` before resume" % exc, file=sys.stderr)


def load_calibration(path: str = CALIBRATION) -> List[Mapping[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(json.load(f)["cells"])


def required_rho_ranges(calib: Sequence[Mapping[str, Any]]) -> Dict[Tuple[str, float, int], List[float]]:
    """Return required measured rho domain per ``(mode, bw, q)``.

    The domain is the union of ``rho_bar + link_offset +/- 3.5 sigma`` for all
    feasible Phase 20R cells. CBR is capped at its reliable ceiling.
    """
    need: Dict[Tuple[str, float, int], List[float]] = {}
    for cell in calib:
        if not cell.get("feasible"):
            continue
        mode = str(cell["mode"])
        rho_bar = float(cell["rho_bar"])
        sigma = float(cell["sigma_rho"])
        hi_reliable = min(float(C.RELIABLE_CEILING[mode]), C.RHO_MAX)
        for link in T7.LINK_NAMES:
            bw, _base, q = T7.LINKS[link]
            mu = rho_bar + C.LINK_OFFSET[link]
            lo = max(C.RHO_MIN, mu - SIGMA_MARGIN * sigma)
            hi = min(hi_reliable, mu + SIGMA_MARGIN * sigma)
            key = (mode, float(bw), int(q))
            if key not in need:
                need[key] = [lo, hi]
            need[key][0] = min(need[key][0], lo)
            need[key][1] = max(need[key][1], hi)
    return need


def rho_grid(mode: str, lo: float, hi: float) -> List[float]:
    h = STEP[mode]
    hi_reliable = min(float(C.RELIABLE_CEILING[mode]), C.RHO_MAX)
    start = math.floor(float(lo) / h) * h
    stop = math.ceil(float(hi) / h) * h
    vals = np.round(np.arange(start, stop + 0.5 * h, h), 4)
    out = []
    for val in vals:
        rho = float(val)
        if C.RHO_MIN - 1e-9 <= rho <= hi_reliable + 1e-9:
            out.append(rho)
    return out


def is_phase_l_rho(rho: float) -> bool:
    return any(abs(float(rho) - ref) < 1e-9 for ref in PHASE_L_RHO)


def grid_summary(calib: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for (mode, bw, q), (lo, hi) in sorted(required_rho_ranges(calib).items()):
        grid = rho_grid(mode, lo, hi)
        new_grid = [rho for rho in grid if not is_phase_l_rho(rho)]
        rows.append(
            {
                "mode": mode,
                "bw": float(bw),
                "q": int(q),
                "lo": float(lo),
                "hi": float(hi),
                "step": float(STEP[mode]),
                "n_levels": len(grid),
                "n_new_levels": len(new_grid),
                "rho_min_grid": float(min(grid)),
                "rho_max_grid": float(max(grid)),
            }
        )
    return rows


def _pid(point: Point, idx: int, stage: str) -> str:
    return "20r4_%s_%04d_%s_%s_b%g_q%d_r%04d_s%d_p%g" % (
        stage,
        idx,
        point["block"],
        point["mode"],
        float(point["bw"]),
        int(point["q"]),
        int(round(float(point["rho"]) * 1000)),
        int(point["seed"]),
        float(point["probe_pps"]),
    )


def _finalize(points: List[Point], stage: str) -> List[Point]:
    for idx, point in enumerate(points):
        point["idx"] = idx
        point["pid"] = _pid(point, idx, stage)
        point["duration_s"] = float(DUR)
        point["warmup_s"] = float(WARM)
    return points


def _regular_full_points(calib: Sequence[Mapping[str, Any]]) -> List[Point]:
    pts: List[Point] = []
    for row in grid_summary(calib):
        mode = row["mode"]
        for rho in rho_grid(mode, row["lo"], row["hi"]):
            if is_phase_l_rho(rho):
                continue
            for seed in SEEDS:
                pts.append(
                    {
                        "mode": mode,
                        "bw": float(row["bw"]),
                        "q": int(row["q"]),
                        "rho": float(rho),
                        "seed": int(seed),
                        "probe_pps": 20.0,
                        "block": "F",
                    }
                )
    random.Random(SHUFFLE_SEED).shuffle(pts)
    return pts


def build_full_plan(calib: Optional[Sequence[Mapping[str, Any]]] = None) -> List[Point]:
    if calib is None:
        calib = load_calibration()
    regular = _regular_full_points(calib)
    out: List[Point] = []
    for i, point in enumerate(regular, 1):
        out.append(point)
        if i % SENTINEL_EVERY == 0:
            out.append({**SENTINEL, "block": "E"})
    return _finalize(out, "full")


def build_smoke_plan(calib: Optional[Sequence[Mapping[str, Any]]] = None) -> List[Point]:
    if calib is None:
        calib = load_calibration()
    by_key = {(row["mode"], row["bw"], row["q"]): row for row in grid_summary(calib)}
    selected = [
        ("cbr", 4.0, 10, 0.65, 21),
        ("cbr", 6.0, 13, 0.55, 22),
        ("cbr", 8.0, 18, 0.55, 23),
        ("poisson", 4.0, 10, 0.62, 21),
        ("poisson", 6.0, 13, 0.52, 22),
        ("poisson", 8.0, 18, 0.52, 23),
        ("h2", 4.0, 10, 0.62, 21),
        ("h2", 6.0, 13, 0.52, 22),
        ("h2", 8.0, 18, 0.52, 23),
    ]
    points: List[Point] = []
    for mode, bw, q, rho, seed in selected:
        if (mode, bw, q) not in by_key:
            raise ValueError("smoke point outside grid: %s bw=%s q=%s" % (mode, bw, q))
        points.append(
            {
                "mode": mode,
                "bw": float(bw),
                "q": int(q),
                "rho": float(rho),
                "seed": int(seed),
                "probe_pps": 20.0,
                "block": "Z",
            }
        )
    points.append({**SENTINEL, "block": "E"})
    return _finalize(points, "smoke")


def build_continuity_plan() -> List[Point]:
    points = [
        {
            "mode": mode,
            "bw": float(bw),
            "q": int(q),
            "rho": float(rho),
            "seed": CONTINUITY_SEED,
            "probe_pps": 20.0,
            "block": "G",
        }
        for mode, bw, q, rho in CONTINUITY_POINTS
    ]
    return _finalize(points, "continuity")


def build_plan(stage: str, calib: Optional[Sequence[Mapping[str, Any]]] = None) -> List[Point]:
    if stage == "smoke":
        return build_smoke_plan(calib)
    if stage == "continuity":
        return build_continuity_plan()
    if stage == "full":
        return build_full_plan(calib)
    raise ValueError("unknown stage %r" % stage)


def default_state_path(stage: str) -> str:
    return {"smoke": SMOKE_STATE, "continuity": CONTINUITY_STATE, "full": STATE}[stage]


def new_state(stage: str, plan: Sequence[Point], calibration_path: str) -> State:
    return {
        "phase": "20R.4",
        "stage": stage,
        "order_seed": SHUFFLE_SEED,
        "sentinel_every": SENTINEL_EVERY,
        "duration_s": DUR,
        "warmup_s": WARM,
        "raw_dir": RAW,
        "calibration_path": calibration_path,
        "calibration_sha256": sha256_file(calibration_path) if os.path.exists(calibration_path) else None,
        "plan_digest": stable_digest(plan),
        "done_idx": [],
        "rows": [],
        "sentinels": [],
        "failed_rows": [],
        "timeout_history": [],
    }


def load_state(path: str, stage: str, plan: Sequence[Point], calibration_path: str) -> State:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        state.setdefault("failed_rows", [])
        state.setdefault("timeout_history", [])
        return state
    return new_state(stage, plan, calibration_path)


def save_state(state: State, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def select_todo(
    plan: Sequence[Point],
    state: State,
    session: Optional[int] = None,
    n_sessions: int = 4,
    max_points: Optional[int] = None,
) -> List[Point]:
    done = set(int(i) for i in state.get("done_idx", []))
    todo = [point for point in plan if int(point["idx"]) not in done]
    if session is not None:
        per = int(math.ceil(len(plan) / float(n_sessions)))
        lo = (int(session) - 1) * per
        hi = int(session) * per
        todo = [point for point in todo if lo <= int(point["idx"]) < hi]
    if max_points is not None:
        todo = todo[: int(max_points)]
    return todo


def gate_20r(row: Mapping[str, Any]) -> List[str]:
    bad: List[str] = []
    if int(row.get("socket_drops", 0)) != 0:
        bad.append("socket_drops=%d" % int(row["socket_drops"]))
    if int(row.get("n_foreign", 0)) != 0:
        bad.append("foreign=%d" % int(row["n_foreign"]))
    if abs(float(row["rate_ratio"]) - 1.0) > 1e-4:
        bad.append("rate=%.7f" % float(row["rate_ratio"]))
    if abs(float(row["rho_actual"]) - float(row["rho"])) > 0.002:
        bad.append("rho lech")
    if float(row.get("n_late_ratio", 0.0)) > 0.001:
        bad.append("late=%.4f" % float(row["n_late_ratio"]))
    if float(row.get("max_late_ms", 0.0)) > 50.0:
        bad.append("maxlate=%.0f" % float(row["max_late_ms"]))
    if row.get("se_batch_ms") is None:
        bad.append("missing_se_batch")
    if row.get("se_naive_ms") is None:
        bad.append("missing_se_naive")
    if float(row.get("probe_pps", 20.0)) != 20.0:
        bad.append("probe_pps=%.3f" % float(row.get("probe_pps", 0.0)))
    return bad


def sentinel_summary(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    summary = L6.sentinel_summary(rows)
    if summary.get("n", 0) and summary.get("sd_ms") is not None:
        summary["cv"] = float(summary["sd_ms"]) / max(abs(float(summary["mean_ms"])), 1e-12)
        summary["cv_pass_0p2pct"] = bool(summary["cv"] < 0.002)
    else:
        summary["cv"] = None
        summary["cv_pass_0p2pct"] = None
    return summary


def campaign_summary(state: State, plan: Sequence[Point]) -> Dict[str, Any]:
    rows = state.get("rows", [])
    fails = [row for row in rows if row.get("gate_fail")]
    sent = sentinel_summary(state.get("sentinels", []))
    done_unique = len(set(int(i) for i in state.get("done_idx", [])))
    rate_errors = [abs(float(row["rate_ratio"]) - 1.0) for row in rows if "rate_ratio" in row]
    return {
        "phase": "20R.4",
        "stage": state.get("stage"),
        "n_plan": len(plan),
        "n_done": done_unique,
        "n_rows": len(rows),
        "n_regular_plan": sum(1 for point in plan if point.get("block") != "E"),
        "n_sentinel_plan": sum(1 for point in plan if point.get("block") == "E"),
        "n_fail": len(fails),
        "n_timeout_history": len(state.get("timeout_history", [])),
        "coverage": done_unique / len(plan) if plan else 0.0,
        "coverage_pass": bool(done_unique == len(plan)) if plan else False,
        "fail_pass": bool(len(fails) == 0),
        "max_abs_rate_error": max(rate_errors) if rate_errors else None,
        "rate_pass_1e_minus_4": bool(max(rate_errors) < 1e-4) if rate_errors else None,
        "n_socket_drop_rows": sum(1 for row in rows if int(row.get("socket_drops", 0)) != 0),
        "n_foreign_rows": sum(1 for row in rows if int(row.get("n_foreign", 0)) != 0),
        "sentinel": sent,
    }


def print_plan(plan: Sequence[Point], todo: Sequence[Point], state: State) -> None:
    print(
        "Ke hoach %d diem | da xong %d | phien nay %d diem (~%.1f gio)"
        % (
            len(plan),
            len(set(int(i) for i in state.get("done_idx", []))),
            len(todo),
            len(todo) * 77.0 / 3600.0,
        )
    )
    print("plan_digest=%s" % stable_digest(plan))
    print("order_seed=%d" % SHUFFLE_SEED)
    for point in todo:
        print(
            "%04d %-7s bw=%g q=%d rho=%.3f seed=%d probe=%g block=%s"
            % (
                point["idx"],
                point["mode"],
                point["bw"],
                point["q"],
                point["rho"],
                point["seed"],
                point["probe_pps"],
                point["block"],
            )
        )


def _annotate_row(
    row: Dict[str, Any],
    args: argparse.Namespace,
    stage: str,
    plan_digest: str,
    run_env: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        **row,
        "phase": "20R.4",
        "stage": stage,
        "runner": "measurements.l6_campaign_fine",
        "argv": list(sys.argv),
        "process_pid": os.getpid(),
        "git_hash": run_env.get("git_commit") or git_commit(),
        "env": dict(run_env),
        "plan_digest": plan_digest,
        "state_path": args.state,
        "raw_dir": RAW,
    }


def run_live(args: argparse.Namespace) -> None:
    calib = load_calibration(args.calibration)
    plan = build_plan(args.stage, calib)
    state = load_state(args.state, args.stage, plan, args.calibration)
    todo = select_todo(plan, state, args.session, args.n_sessions, args.max_points)
    state.setdefault("plan_digest", stable_digest(plan))
    state.setdefault("stage", args.stage)
    state.setdefault("raw_dir", RAW)

    if args.plan_only:
        print_plan(plan, todo, state)
        return
    if args.summary:
        print(json.dumps(campaign_summary(state, plan), indent=2, sort_keys=True))
        return

    from mininet.link import Link
    from mininet.net import Mininet
    from mininet.node import OVSBridge
    from mininet.topology_split_qdisc import (
        SplitQdiscTopo,
        change_measure_qdisc,
        intf_toward,
        setup_measure_qdisc,
        setup_return_qdisc,
    )

    os.makedirs(RAW, exist_ok=True)
    os.makedirs(os.path.dirname(RUNLOG), exist_ok=True)
    L6.RAW = RAW
    run_env = run_environment_fingerprint()
    if run_env.get("git_dirty"):
        print("WORKTREE RELEVANT DIRTY -- dung truoc khi do:", file=sys.stderr)
        for line in run_env.get("git_status_relevant", []):
            print(line, file=sys.stderr)
        raise SystemExit(2)

    print(
        "Ke hoach %d diem | da xong %d | phien nay %d diem (~%.1f gio)"
        % (
            len(plan),
            len(set(int(i) for i in state.get("done_idx", []))),
            len(todo),
            len(todo) * 77.0 / 3600.0,
        )
    )
    print("state=%s raw=%s plan_digest=%s" % (args.state, RAW, stable_digest(plan)))
    print(
        "git_commit=%s git_dirty=%s git_dirty_raw=%s"
        % (
            str(run_env.get("git_commit", ""))[:12],
            run_env.get("git_dirty"),
            run_env.get("git_dirty_raw"),
        )
    )

    net = Mininet(topo=SplitQdiscTopo(), link=Link, switch=OVSBridge, controller=None)
    net.start()
    try:
        s1, s2 = net.get("s1"), net.get("s2")
        if_measure = intf_toward(s1, "s2")
        setup_return_qdisc(intf_toward(s2, "s1"), DELAY_MS)
        setup_measure_qdisc(if_measure, REF[0], REF[1])
        current = REF
        t0 = time.time()
        plan_digest = stable_digest(plan)

        for k, point in enumerate(todo, 1):
            if (float(point["bw"]), int(point["q"])) != current:
                change_measure_qdisc(if_measure, point["bw"], point["q"])
                current = (float(point["bw"]), int(point["q"]))
                time.sleep(0.2)

            try:
                with deadline(args.point_timeout, "point idx=%d" % int(point["idx"])):
                    row = _annotate_row(L6.measure(net, point), args, args.stage, plan_digest, run_env)
            except PointTimeout as exc:
                cleanup_live_processes()
                timeout_row = {
                    **point,
                    "phase": "20R.4",
                    "stage": args.stage,
                    "runner": "measurements.l6_campaign_fine",
                    "state_path": args.state,
                    "raw_dir": RAW,
                    "plan_digest": plan_digest,
                    "git_hash": run_env.get("git_commit") or git_commit(),
                    "env": dict(run_env),
                    "attempt": 1,
                    "timeout_s": float(args.point_timeout),
                    "reason": str(exc),
                    "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                state.setdefault("timeout_history", []).append(timeout_row)
                save_state(state, args.state)
                print(
                    "TIMEOUT idx=%d after %.1f s; khong danh dau done, hay resume bang process moi"
                    % (int(point["idx"]), float(args.point_timeout)),
                    file=sys.stderr,
                )
                raise SystemExit(3)
            row["gate_fail"] = gate_20r(row)
            row["attempt"] = 1
            if row["gate_fail"]:
                print("      * fail: %s -> chay lai 1 lan" % ",".join(row["gate_fail"]))
                try:
                    with deadline(args.point_timeout, "retry idx=%d" % int(point["idx"])):
                        row2 = _annotate_row(L6.measure(net, point), args, args.stage, plan_digest, run_env)
                except PointTimeout as exc:
                    cleanup_live_processes()
                    timeout_row = {
                        **point,
                        "phase": "20R.4",
                        "stage": args.stage,
                        "runner": "measurements.l6_campaign_fine",
                        "state_path": args.state,
                        "raw_dir": RAW,
                        "plan_digest": plan_digest,
                        "git_hash": run_env.get("git_commit") or git_commit(),
                        "env": dict(run_env),
                        "attempt": 2,
                        "attempt1_fail": row["gate_fail"],
                        "timeout_s": float(args.point_timeout),
                        "reason": str(exc),
                        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    state.setdefault("timeout_history", []).append(timeout_row)
                    save_state(state, args.state)
                    print(
                        "TIMEOUT retry idx=%d after %.1f s; khong danh dau done, hay resume bang process moi"
                        % (int(point["idx"]), float(args.point_timeout)),
                        file=sys.stderr,
                    )
                    raise SystemExit(3)
                row2["gate_fail"] = gate_20r(row2)
                row2["attempt"] = 2
                row2["attempt1_fail"] = row["gate_fail"]
                row = row2

            state.setdefault("rows", []).append(row)
            state.setdefault("done_idx", []).append(point["idx"])
            if row["gate_fail"]:
                state.setdefault("failed_rows", []).append(row)
            if point["block"] == "E":
                state.setdefault("sentinels", []).append(
                    {
                        "idx": point["idx"],
                        "t": row["wall_utc"],
                        "q_mean_ms": row["q_mean_ms"],
                        "gate_fail": row["gate_fail"],
                    }
                )
            save_state(state, args.state)

            tag = ""
            if point["block"] == "E":
                z = (row["q_mean_ms"] - SENTINEL_REF["mean_ms"]) / SENTINEL_REF["sd_ms"]
                tag = " [CANH z=%+.2f%s]" % (
                    z,
                    " *NGOAI KIEM SOAT" if abs(z) > 3.0 else "",
                )
            eta = (time.time() - t0) / k * (len(todo) - k) / 3600.0
            print(
                "[%4d/%4d] %-8s bw=%g q=%2d rho=%.3f s=%3d p=%2g | "
                "q=%7.3f p95=%7.3f loss=%.4f | %-4s (con %.1f h)%s"
                % (
                    k,
                    len(todo),
                    point["mode"],
                    point["bw"],
                    point["q"],
                    point["rho"],
                    point["seed"],
                    point["probe_pps"],
                    row["q_mean_ms"],
                    row["q_p95_ms"],
                    row["loss"],
                    "OK" if not row["gate_fail"] else "FAIL",
                    eta,
                    tag,
                )
            )
    finally:
        stop_net_best_effort(net, args.stop_timeout)
        save_state(state, args.state)

    print("\n=== TONG KET ===")
    print(json.dumps(campaign_summary(state, plan), indent=2, sort_keys=True))
    print("\nstate -> %s" % args.state)


def write_grid_doc(path: str = "docs/phase-20R/04-campaign-grid.md") -> None:
    calib = load_calibration()
    rows = grid_summary(calib)
    full = build_full_plan(calib)
    smoke = build_smoke_plan(calib)
    continuity = build_continuity_plan()
    text = [
        "# Phase 20R.4 -- Campaign Grid",
        "",
        "Ngay ky: 2026-08-04",
        "Commit prereg prediction: b3d11a7c1bb1455fc7a77f9cea893db3776a378d",
        "",
        "File nay chot luoi do Mininet truoc khi chay chien dich 20R.4.",
        "",
        "## Nguyen Tac",
        "",
        "- Ground truth la bang tra tua tinh, khong phai trace dong.",
        "- Khong luong tu hoa quy dao `rho(t)`; Lesson 20R.5 se noi suy bang do that.",
        "- Buoc luoi duoc chon bang ngan sach sai so noi suy <= 10% san nhieu.",
        "- `cbr` dung `h = 0.05`; `poisson`/`h2` dung `h = 0.02`.",
        "- Moi muc rho moi chay 5 seed: `%s`." % ", ".join(str(s) for s in SEEDS),
        "- Thu tu full campaign xao tron bang seed co dinh `%d`." % SHUFFLE_SEED,
        "- Sentinel giu nguyen Phase L: `h2|bw=6|q=13|rho=0.90|seed=999`, moi 30 diem.",
        "",
        "## Bang Luoi",
        "",
        "```text",
        "mode     bw q   domain_used       h      levels  new",
    ]
    for row in rows:
        text.append(
            "%-8s %3g %-2d [%.3f, %.3f]   %.2f   %5d  %3d"
            % (
                row["mode"],
                row["bw"],
                row["q"],
                row["rho_min_grid"],
                row["rho_max_grid"],
                row["step"],
                row["n_levels"],
                row["n_new_levels"],
            )
        )
    text.extend(
        [
            "```",
            "",
            "Tong muc moi: `%d`; full regular runs: `%d`; sentinel: `%d`; tong: `%d`."
            % (
                sum(int(row["n_new_levels"]) for row in rows),
                sum(1 for point in full if point["block"] != "E"),
                sum(1 for point in full if point["block"] == "E"),
                len(full),
            ),
            "",
            "Ghi chu: cbr bi cat tai reliable ceiling `rho <= 0.95`; so muc moi van",
            "giu dung ngan sach 118 muc / 590 run.",
            "",
            "## Stages",
            "",
            "```text",
            "smoke      %3d diem -> results/SMOKE/phase-20R/smoke_state.json" % len(smoke),
            "continuity %3d diem -> results/SUPERSEDED/phase-20R/continuity_state.json" % len(continuity),
            "full       %3d diem -> results/SUPERSEDED/phase-20R/campaign_state.json" % len(full),
            "```",
            "",
            "## Gate Chay Song",
            "",
            "```text",
            "socket_drops == 0",
            "n_foreign == 0",
            "abs(rate_ratio - 1) <= 1e-4",
            "abs(rho_actual - rho) <= 0.002",
            "n_late_ratio <= 0.001",
            "max_late_ms <= 50",
            "se_batch_ms va se_naive_ms deu co mat",
            "probe_pps == 20.0",
            "```",
            "",
            "## Bit Chot",
            "",
            "```text",
            "full_plan_digest = %s" % stable_digest(full),
            "smoke_plan_digest = %s" % stable_digest(smoke),
            "continuity_plan_digest = %s" % stable_digest(continuity),
            "calibration_sha256 = %s" % sha256_file(CALIBRATION),
            "```",
        ]
    )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(text) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("smoke", "continuity", "full"), default="full")
    parser.add_argument("--smoke", action="store_true", help="alias for --stage smoke")
    parser.add_argument("--continuity", action="store_true", help="alias for --stage continuity")
    parser.add_argument("--full", action="store_true", help="alias for --stage full")
    parser.add_argument("--state", default=None)
    parser.add_argument("--calibration", default=CALIBRATION)
    parser.add_argument("--session", type=int, default=None)
    parser.add_argument("--n-sessions", type=int, default=4)
    parser.add_argument("--max-points", type=int, default=None)
    parser.add_argument("--limit", dest="max_points", type=int, default=None, help="alias for --max-points")
    parser.add_argument("--point-timeout", type=float, default=240.0)
    parser.add_argument("--stop-timeout", type=float, default=30.0)
    parser.add_argument("--resume", action="store_true", help="resume is the default behavior")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--dry-run", dest="plan_only", action="store_true", help="alias for --plan-only")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--write-grid-doc", action="store_true")
    args = parser.parse_args(argv)

    if args.smoke:
        args.stage = "smoke"
    if args.continuity:
        args.stage = "continuity"
    if args.full:
        args.stage = "full"
    if args.state is None:
        args.state = default_state_path(args.stage)
    if args.session is not None and not (1 <= args.session <= args.n_sessions):
        raise SystemExit("--session phai nam trong 1..%d" % args.n_sessions)

    if args.write_grid_doc:
        write_grid_doc()
        print("WROTE docs/phase-20R/04-campaign-grid.md")
        return 0

    run_live(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

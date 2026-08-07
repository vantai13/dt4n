#!/usr/bin/env python3
"""Phase 20R.6 -- live A'/B/C tandem additivity runner.

The runner owns orchestration only. Qdisc setup comes from
``mininet.topology_tandem.configure_qdiscs``; traffic and probes reuse the
Phase L ``load_gen``, ``owd_probe``, and ``owd_analyze`` modules.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from measurements import decision_error_v2 as D
from measurements.additivity_check import (
    B_RHO_BARS,
    C_RHO_BARS,
    DELTA_MS,
    MODES,
    PROBE_INTRUSION_MAX,
    SEEDS,
    calibration_by_cell,
    parse_float_list,
    parse_int_list,
    parse_list,
    stable_digest,
)
from measurements.provenance import env_fingerprint
from mininet.load_spec import FRAME_OVERHEAD_BYTES, PAYLOAD_PROBE, PROBE_PPS, capacity_bytes_per_s
from mininet.topology_tandem import TANDEM_BY_IDX, TANDEM_LINKS
from twin import cost_v2 as C


BRANCHES = ("Aprime", "B", "C")
RAW = "results/phase-20R/raw_additivity"
DEFAULT_STATE = {
    "Aprime": "results/phase-20R/additivity_branch_a_state.json",
    "B": "results/phase-20R/additivity_branch_b_state.json",
    "C": "results/phase-20R/additivity_branch_c_state.json",
}
DUR = 70.0
WARM = 10.0
LOAD_PORT_BASE = 5750
PROBE_PORT_BASE = 5850
PATH_PROBE_PORT = 5899
PATH_NAME = "T123"
DEFAULT_PROBE_RATE_PPS = PROBE_PPS
DEFAULT_PROBE_SIZE_BYTES = PAYLOAD_PROBE
LG = "python3 -m measurements.load_gen"
PB = "python3 -m measurements.owd_probe"


class PointTimeout(RuntimeError):
    """Raised when a live point exceeds its wall-clock budget."""


def _timeout_handler(_signum: int, _frame: object) -> None:
    raise PointTimeout("live point exceeded deadline")


class deadline:
    """Signal deadline for blocking Mininet host.cmd calls."""

    def __init__(self, seconds: float, label: str):
        self.seconds = float(seconds)
        self.label = str(label)
        self._old_handler = None
        self._old_timer = None

    def __enter__(self) -> None:
        self._old_handler = signal.getsignal(signal.SIGALRM)
        self._old_timer = signal.setitimer(signal.ITIMER_REAL, self.seconds)
        signal.signal(signal.SIGALRM, _timeout_handler)

    def __exit__(self, exc_type: object, exc: object, _tb: object) -> bool:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        if self._old_handler is not None:
            signal.signal(signal.SIGALRM, self._old_handler)
        if self._old_timer and self._old_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, self._old_timer[0], self._old_timer[1])
        if exc_type is PointTimeout and exc is not None:
            exc.args = ("%s timed out after %.1f s" % (self.label, self.seconds),)
        return False


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return dict(json.load(f))


def write_json_atomic(path: str, data: object) -> None:
    ensure_parent(path)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def cleanup_live_processes() -> None:
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


def _sysctl_get(key: str) -> Optional[str]:
    p = subprocess.run(
        ["sysctl", "-n", key],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return p.stdout.strip() or None


def _sysctl_set(key: str, value: str) -> None:
    subprocess.run(
        ["sysctl", "-qw", "%s=%s" % (key, value)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def disable_ipv6_on_new_links() -> Dict[str, Optional[str]]:
    """Disable IPv6 only for interfaces created after this call."""
    key = "net.ipv6.conf.default.disable_ipv6"
    saved = {key: _sysctl_get(key)}
    _sysctl_set(key, "1")
    return saved


def restore_sysctl(saved: Mapping[str, Optional[str]]) -> None:
    for key, value in saved.items():
        if value is not None:
            _sysctl_set(str(key), str(value))


def stop_net_best_effort(net: Any, timeout_s: float) -> None:
    cleanup_live_processes()
    try:
        with deadline(timeout_s, "net.stop"):
            net.stop()
    except PointTimeout as exc:
        print("WARNING: %s; hay chay `sudo mn -c` truoc khi resume" % exc, file=sys.stderr)
    except Exception as exc:
        print("WARNING: net.stop failed: %s; hay chay `sudo mn -c` truoc khi resume" % exc, file=sys.stderr)


def run_env() -> Dict[str, Any]:
    env = env_fingerprint()
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL)
        env["git_status_porcelain"] = [line for line in out.splitlines() if line.strip()]
    except Exception:
        env["git_status_porcelain"] = []
    return env


def _default_rhos(branch: str) -> Tuple[float, ...]:
    return C_RHO_BARS if branch == "C" else B_RHO_BARS


def _pid(branch: str, idx: int, mode: str, rho_bar: float, seed: int, link_idx: Optional[int]) -> str:
    tag = "path" if link_idx is None else "L%d" % int(link_idx)
    return "20r6_%s_%04d_%s_r%04d_s%d_%s" % (
        str(branch).lower(),
        int(idx),
        str(mode),
        int(round(float(rho_bar) * 1000)),
        int(seed),
        tag,
    )


def build_plan(
    branch: str,
    modes: Sequence[str] = MODES,
    rho_bars: Sequence[float] = (),
    seeds: Sequence[int] = SEEDS,
) -> List[Dict[str, Any]]:
    if branch not in BRANCHES:
        raise ValueError("branch phai la mot trong %s" % (BRANCHES,))
    rhos = tuple(float(x) for x in (rho_bars or _default_rhos(branch)))
    rows: List[Dict[str, Any]] = []
    for mode in modes:
        for rho_bar in rhos:
            for seed in seeds:
                if branch == "C":
                    rows.append(
                        {
                            "branch": branch,
                            "mode": str(mode),
                            "rho_bar": float(rho_bar),
                            "seed": int(seed),
                            "path": PATH_NAME,
                            "link_idx": None,
                        }
                    )
                else:
                    for link_idx in range(1, len(TANDEM_LINKS) + 1):
                        rows.append(
                            {
                                "branch": branch,
                                "mode": str(mode),
                                "rho_bar": float(rho_bar),
                                "seed": int(seed),
                                "link_idx": int(link_idx),
                                "link": TANDEM_BY_IDX[int(link_idx)][0],
                            }
                        )
    for idx, row in enumerate(rows, start=1):
        row["idx"] = idx
        row["pid"] = _pid(branch, idx, row["mode"], row["rho_bar"], row["seed"], row.get("link_idx"))
    return rows


def select_todo(plan: Sequence[Mapping[str, Any]], state: Mapping[str, Any], max_points: Optional[int]) -> List[Dict[str, Any]]:
    done = set(int(idx) for idx in state.get("done_idx", []))
    todo = [dict(point) for point in plan if int(point["idx"]) not in done]
    return todo[: int(max_points)] if max_points is not None else todo


def new_state(branch: str, plan: Sequence[Mapping[str, Any]], args: argparse.Namespace) -> Dict[str, Any]:
    return {
        "phase": "20R.6",
        "kind": "additivity_live_state",
        "branch": str(branch),
        "runner": "measurements.additivity_live",
        "plan_digest": stable_digest(list(plan)),
        "argv": list(sys.argv),
        "raw_dir": args.raw_dir,
        "duration_s": float(args.duration),
        "warmup_s": float(args.warmup),
        "probe_rate_pps": float(args.probe_rate),
        "probe_size_bytes": int(args.probe_size),
        "delta_ms": float(DELTA_MS),
        "done_idx": [],
        "rows": [],
        "failed_rows": [],
        "timeout_history": [],
        "env": run_env(),
    }


def load_state(path: str, branch: str, plan: Sequence[Mapping[str, Any]], args: argparse.Namespace) -> Dict[str, Any]:
    if os.path.exists(path):
        state = read_json(path)
        state.setdefault("rows", [])
        state.setdefault("done_idx", [])
        state.setdefault("failed_rows", [])
        state.setdefault("timeout_history", [])
        state.setdefault("plan_digest", stable_digest(list(plan)))
        return state
    return new_state(branch, plan, args)


def _rho_by_link(rho_bar: float) -> Dict[int, float]:
    vec = C.rho_vector(float(rho_bar))
    return {idx: float(vec[t7_link]) for idx, (_name, t7_link, _bw, _q, _base) in enumerate(TANDEM_LINKS, start=1)}


def rho_by_link_from_point(point: Mapping[str, Any]) -> Dict[int, float]:
    override = point.get("rho_by_link_idx")
    if override:
        return {int(k): float(v) for k, v in dict(override).items()}
    return _rho_by_link(float(point["rho_bar"]))


def _w_loss(mode: str, rho_bar: float, calibration_path: str) -> float:
    cells = calibration_by_cell(calibration_path)
    return float(cells[(str(mode), round(float(rho_bar), 12))]["w_loss"])


def _static_link_ms(link_idx: int) -> float:
    _name, t7_link, _bw, _q, _base = TANDEM_BY_IDX[int(link_idx)]
    return float(C.static_link_ms(t7_link))


def _static_path_ms() -> float:
    return sum(_static_link_ms(idx) for idx in range(1, len(TANDEM_LINKS) + 1))


def _load_seed(seed: int, link_idx: int) -> int:
    return int(seed) * 100 + int(link_idx)


def _probe_seed(seed: int, link_idx: Optional[int]) -> int:
    return int(seed) * 1000 + 700 + (0 if link_idx is None else int(link_idx))


def _run_id(point: Mapping[str, Any], salt: int) -> int:
    return int(point["idx"]) * 100 + int(salt)


def _load_links(point: Mapping[str, Any]) -> Tuple[int, ...]:
    return (int(point["link_idx"]),) if point["branch"] == "Aprime" else tuple(range(1, len(TANDEM_LINKS) + 1))


def probe_links_for_point(point: Mapping[str, Any]) -> Tuple[int, ...]:
    if point["branch"] == "C":
        return tuple(range(1, len(TANDEM_LINKS) + 1))
    return (int(point["link_idx"]),)


def probe_frame_bytes_on_wire(probe_size_bytes: int) -> int:
    return int(probe_size_bytes) + int(FRAME_OVERHEAD_BYTES)


def probe_load_share(
    link_idx: int,
    args: argparse.Namespace,
    rate_pps: Optional[float] = None,
    frame_bytes: Optional[int] = None,
) -> float:
    _name, _t7_link, bw, _q, _base = TANDEM_BY_IDX[int(link_idx)]
    rate = float(args.probe_rate if rate_pps is None else rate_pps)
    frame = int(probe_frame_bytes_on_wire(args.probe_size) if frame_bytes is None else frame_bytes)
    return rate * frame / capacity_bytes_per_s(float(bw))


def _load_prefix(raw_dir: str, point: Mapping[str, Any], link_idx: int) -> str:
    return os.path.join(raw_dir, "%s_load_L%d" % (point["pid"], int(link_idx)))


def _probe_prefix(raw_dir: str, point: Mapping[str, Any]) -> str:
    suffix = "path" if point["branch"] == "C" else "L%d" % int(point["link_idx"])
    return os.path.join(raw_dir, "%s_probe_%s" % (point["pid"], suffix))


def _host_cmd(host: Any, cmd: str) -> str:
    return host.cmd(cmd)


def measured_qdisc_ifaces_from_proof(proof: Mapping[str, Any]) -> Dict[str, str]:
    return {str(row["link"]): str(row["if_fwd"]) for row in proof.get("measured", [])}


def direct_packet_snapshot(ifaces: Mapping[str, str]) -> Dict[str, int]:
    from mininet.topology_split_qdisc import read_direct_packets

    return {str(name): int(read_direct_packets(str(ifname))) for name, ifname in ifaces.items()}


def attach_direct_packet_delta(
    row: Dict[str, Any],
    direct_before: Mapping[str, int],
    direct_after: Mapping[str, int],
) -> Dict[str, Any]:
    direct_delta = {
        str(name): int(direct_after.get(name, 0)) - int(before)
        for name, before in direct_before.items()
    }
    row["direct_packets_before"] = {str(k): int(v) for k, v in direct_before.items()}
    row["direct_packets_after"] = {str(k): int(v) for k, v in direct_after.items()}
    row["direct_packets_delta"] = direct_delta
    row["vl1g_run_pass"] = bool(all(int(v) == 0 for v in direct_delta.values()))
    return row


def retryable_gate_fail(fails: Sequence[str]) -> bool:
    return bool(fails) and not any(str(fail).startswith("V-L1g-run") for fail in fails)


def start_background_loads(net: Any, point: Mapping[str, Any], args: argparse.Namespace) -> Dict[int, Dict[str, Any]]:
    cwd = os.getcwd()
    rhos = rho_by_link_from_point(point)
    probe_links = set(probe_links_for_point(point))
    specs: Dict[int, Dict[str, Any]] = {}
    for link_idx in _load_links(point):
        name, _t7_link, bw, _q, _base = TANDEM_BY_IDX[int(link_idx)]
        prefix = _load_prefix(args.raw_dir, point, int(link_idx))
        ensure_parent(prefix)
        recv = net.get("hsink%d" % int(link_idx))
        port = LOAD_PORT_BASE + int(link_idx)
        rho_target_total = float(rhos[int(link_idx)])
        rho_probe_share = probe_load_share(int(link_idx), args) if int(link_idx) in probe_links else 0.0
        rho_bg = rho_target_total - rho_probe_share
        if rho_bg <= 0.0:
            raise ValueError(
                "probe load %.6f leaves non-positive background rho %.6f on L%d"
                % (rho_probe_share, rho_bg, int(link_idx))
            )
        seed = _load_seed(int(point["seed"]), int(link_idx))
        run_id = _run_id(point, int(link_idx))
        _host_cmd(
            recv,
            "cd %s && %s recv --port %d --duration %g --out-prefix %s >/dev/null 2>&1 &"
            % (cwd, PB, port, float(args.duration) + 6.0, prefix),
        )
        specs[int(link_idx)] = {
            "link": name,
            "bw": float(bw),
            "rho": float(rho_bg),
            "rho_bg": float(rho_bg),
            "rho_target_total": float(rho_target_total),
            "rho_probe_share": float(rho_probe_share),
            "probe_traverses_link": bool(int(link_idx) in probe_links),
            "seed": int(seed),
            "run_id": int(run_id),
            "port": int(port),
            "prefix": prefix,
        }
    time.sleep(0.8)
    for link_idx, spec in specs.items():
        send = net.get("hload%d" % int(link_idx))
        _host_cmd(
            send,
            (
                "cd %s && %s --dst %s --port %d --bw %g --rho %g --mode %s "
                "--duration %g --seed %d --run-id %d --probe-pps 0 --out-prefix %s "
                ">/dev/null 2>&1 &"
            )
            % (
                cwd,
                LG,
                net.get("hsink%d" % int(link_idx)).IP(),
                int(spec["port"]),
                float(spec["bw"]),
                float(spec["rho_bg"]),
                str(point["mode"]),
                float(args.duration),
                int(spec["seed"]),
                int(spec["run_id"]),
                spec["prefix"],
            ),
        )
    return specs


def run_measure_probe(net: Any, point: Mapping[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    cwd = os.getcwd()
    prefix = _probe_prefix(args.raw_dir, point)
    ensure_parent(prefix)
    rx_path = prefix + ".bin"
    tx_path = prefix + "_tx.bin"
    if point["branch"] == "C":
        recv = net.get("hdst")
        send = net.get("hsrc")
        dst_ip = recv.IP()
        port = PATH_PROBE_PORT
        link_idx = None
        min_bw = min(float(row[2]) for row in TANDEM_LINKS)
    else:
        link_idx = int(point["link_idx"])
        recv = net.get("hpb%d" % link_idx)
        send = net.get("hpa%d" % link_idx)
        dst_ip = recv.IP()
        port = PROBE_PORT_BASE + link_idx
        min_bw = float(TANDEM_BY_IDX[link_idx][2])
    run_id = _run_id(point, 90 if link_idx is None else 90 + int(link_idx))
    _host_cmd(
        recv,
        "cd %s && %s recv --port %d --duration %g --out %s >/dev/null 2>&1 &"
        % (cwd, PB, int(port), float(args.duration) + 6.0, rx_path),
    )
    time.sleep(0.8)
    _host_cmd(
        send,
        (
            "cd %s && %s send --dst %s --port %d --mode poisson --rate %g --size %d "
            "--duration %g --run-id %d --seed %d --out %s >/dev/null 2>&1"
        )
        % (
            cwd,
            PB,
            dst_ip,
            int(port),
            float(args.probe_rate),
            int(args.probe_size),
            float(args.duration),
            int(run_id),
            _probe_seed(int(point["seed"]), link_idx),
            tx_path,
        ),
    )
    time.sleep(6.5)
    from measurements.owd_analyze import analyze

    rx_meta = read_json(rx_path + ".meta.json")
    tx_meta = read_json(tx_path + ".meta.json")
    owd = analyze(rx_path, tx_path, warmup_s=float(args.warmup))
    frame_bytes = int(tx_meta.get("frame_bytes_on_wire", int(args.probe_size) + 42))
    rate_pps = float(tx_meta.get("rate_pps_actual", float(args.probe_rate)))
    intrusion = rate_pps * frame_bytes / capacity_bytes_per_s(min_bw)
    return {
        "prefix": prefix,
        "rx_path": rx_path,
        "tx_path": tx_path,
        "run_id": int(run_id),
        "rx_meta": rx_meta,
        "tx_meta": tx_meta,
        "analysis": owd,
        "probe_intrusion_ratio": float(intrusion),
        "probe_frame_bytes_on_wire": int(frame_bytes),
        "probe_rate_pps_actual": rate_pps,
    }


def _wait_for_load_meta(specs: Mapping[int, Mapping[str, Any]]) -> Dict[int, Dict[str, Any]]:
    out: Dict[int, Dict[str, Any]] = {}
    for link_idx, spec in specs.items():
        prefix = str(spec["prefix"])
        out[int(link_idx)] = {
            "tx": read_json(prefix + "_tx.meta.json"),
            "rx": read_json(prefix + "_rx.meta.json"),
        }
    return out


def _path_loss_from_links(load_rows: Sequence[Mapping[str, Any]]) -> float:
    keep = 1.0
    for row in load_rows:
        keep *= 1.0 - float(row.get("loss", 0.0))
    return 1.0 - keep


def _row_from_measurement(
    point: Mapping[str, Any],
    args: argparse.Namespace,
    load_specs: Mapping[int, Mapping[str, Any]],
    load_meta: Mapping[int, Mapping[str, Any]],
    probe: Mapping[str, Any],
) -> Dict[str, Any]:
    owd = dict(probe["analysis"])
    owd_ms = dict(owd["owd_ms"])
    counts = dict(owd["counts"])
    probe_rx = dict(probe["rx_meta"])
    probe_tx = dict(probe["tx_meta"])
    probe_links = set(probe_links_for_point(point))
    probe_frame = int(probe["probe_frame_bytes_on_wire"])
    probe_rate = float(probe["probe_rate_pps_actual"])
    probe_share_actual_by_idx = {
        int(link_idx): (
            probe_load_share(int(link_idx), args, rate_pps=probe_rate, frame_bytes=probe_frame)
            if int(link_idx) in probe_links
            else 0.0
        )
        for link_idx in load_specs
    }
    load_rows: List[Dict[str, Any]] = []
    schedule_map: Dict[str, str] = {}
    rho_bg_actual_by_link: Dict[str, float] = {}
    rho_target_total_by_link: Dict[str, float] = {}
    rho_probe_share_by_link: Dict[str, float] = {}
    rho_total_actual_by_link: Dict[str, float] = {}
    rate_ratio_by_link: Dict[str, float] = {}
    load_socket_drops = 0
    load_foreign = 0
    load_late_ratios = []
    load_max_late = 0.0
    for link_idx in sorted(load_specs):
        spec = load_specs[link_idx]
        tx = dict(load_meta[link_idx]["tx"])
        rx = dict(load_meta[link_idx]["rx"])
        sent_total = max(int(tx["counts"]["n_bg_sent"]) + int(tx["counts"].get("n_probe_sent", 0)), 1)
        late_ratio = int(tx["counts"].get("n_late", 0)) / float(sent_total)
        link_name = str(spec["link"])
        schedule = str(tx["schedule"]["digest_bg"])
        rho_bg_actual = float(tx["rates"]["rho_actual"])
        rho_probe_actual = float(probe_share_actual_by_idx[int(link_idx)])
        rho_total_actual = rho_bg_actual + rho_probe_actual
        rho_target_total = float(spec["rho_target_total"])
        schedule_map[link_name] = schedule
        rho_bg_actual_by_link[link_name] = rho_bg_actual
        rho_target_total_by_link[link_name] = rho_target_total
        rho_probe_share_by_link[link_name] = rho_probe_actual
        rho_total_actual_by_link[link_name] = rho_total_actual
        rate_ratio_by_link[link_name] = float(tx["rates"]["rate_ratio"])
        load_socket_drops += int(rx.get("socket_drops_delta", 0))
        load_foreign += int(rx.get("n_foreign_packets", 0))
        load_late_ratios.append(late_ratio)
        load_max_late = max(load_max_late, float(tx["counts"].get("max_late_ms", 0.0)))
        load_rows.append(
            {
                "link_idx": int(link_idx),
                "link": link_name,
                "rho": rho_target_total,
                "rho_bg": float(spec["rho_bg"]),
                "rho_bg_actual": rho_bg_actual,
                "rho_target_total": rho_target_total,
                "rho_probe_share": rho_probe_actual,
                "rho_total_actual": rho_total_actual,
                "probe_traverses_link": bool(spec["probe_traverses_link"]),
                "rho_actual": rho_total_actual,
                "rate_ratio": float(tx["rates"]["rate_ratio"]),
                "schedule_digest": schedule,
                "n_bg_sent": int(tx["counts"]["n_bg_sent"]),
                "n_bg_recv": int(rx.get("n_bg", 0)),
                "socket_drops": int(rx.get("socket_drops_delta", 0)),
                "n_foreign": int(rx.get("n_foreign_packets", 0)),
                "n_late_ratio": float(late_ratio),
                "max_late_ms": float(tx["counts"].get("max_late_ms", 0.0)),
            }
        )
    trajectory_digest = stable_digest(schedule_map)
    target_link_idx = point.get("link_idx")
    target_link_name = None if target_link_idx is None else str(TANDEM_BY_IDX[int(target_link_idx)][0])
    static_ms = _static_path_ms() if point["branch"] == "C" else _static_link_ms(int(target_link_idx))
    delay_ms = float(static_ms) + float(owd_ms["mean"])
    w_loss = _w_loss(str(point["mode"]), float(point["rho_bar"]), args.calibration)
    loss = float(owd["loss_rate"])
    cost_ms = delay_ms + w_loss * loss
    max_abs_rate_error = max((abs(float(v) - 1.0) for v in rate_ratio_by_link.values()), default=0.0)
    max_abs_bg_rho_error = max(
        (abs(float(row["rho_bg_actual"]) - float(row["rho_bg"])) for row in load_rows),
        default=0.0,
    )
    max_abs_total_rho_error = max(
        (abs(float(row["rho_total_actual"]) - float(row["rho_target_total"])) for row in load_rows),
        default=0.0,
    )
    row = {
        **dict(point),
        "phase": "20R.6",
        "runner": "measurements.additivity_live",
        "raw_dir": args.raw_dir,
        "plan_branch_digest": stable_digest(build_plan(point["branch"], parse_list(args.modes), parse_float_list(args.rho_bar) if args.rho_bar else _default_rhos(point["branch"]), parse_int_list(args.seeds))),
        "w_loss": float(w_loss),
        "queue_mean_ms": float(owd_ms["mean"]),
        "queue_sd_ms": float(owd_ms["sd"]),
        "q_mean_ms": float(delay_ms),
        "q_sd_ms": float(owd_ms["sd"]),
        "q_p50_ms": float(static_ms) + float(owd_ms["p50"]),
        "q_p90_ms": float(static_ms) + float(owd_ms["p90"]),
        "q_p95_ms": float(static_ms) + float(owd_ms["p95"]),
        "q_p99_ms": float(static_ms) + float(owd_ms["p99"]),
        "delay_ms": float(delay_ms),
        "static_ms": float(static_ms),
        "loss": loss,
        "cost_ms": float(cost_ms),
        "n_recv_unique": int(counts["n_recv_unique"]),
        "n_sent": int(counts["n_sent"]),
        "probe_loss": loss,
        "probe_intrusion_ratio": float(probe["probe_intrusion_ratio"]),
        "probe_rate_pps_actual": float(probe["probe_rate_pps_actual"]),
        "probe_frame_bytes_on_wire": int(probe["probe_frame_bytes_on_wire"]),
        "probe_socket_drops": int(probe_rx.get("socket_drops_delta", 0)),
        "probe_n_foreign": int(probe_rx.get("n_foreign_packets", 0)),
        "probe_run_ids_seen": list(probe_rx.get("run_ids_seen", [])),
        "load_rows": load_rows,
        "load_schedule_digests": schedule_map,
        "schedule_digest": schedule_map.get(target_link_name) if target_link_name is not None else trajectory_digest,
        "trajectory_digest": trajectory_digest,
        "rho_actual_by_link": rho_total_actual_by_link,
        "rho_bg_actual_by_link": rho_bg_actual_by_link,
        "rho_target_total_by_link": rho_target_total_by_link,
        "rho_probe_share_by_link": rho_probe_share_by_link,
        "rho_total_actual_by_link": rho_total_actual_by_link,
        "rate_ratio_by_link": rate_ratio_by_link,
        "rate_ratio": rate_ratio_by_link.get(target_link_name, max(rate_ratio_by_link.values()) if rate_ratio_by_link else 1.0),
        "max_abs_rate_error": float(max_abs_rate_error),
        "max_abs_bg_rho_error": float(max_abs_bg_rho_error),
        "max_abs_total_rho_error": float(max_abs_total_rho_error),
        "max_abs_rho_error": float(max_abs_total_rho_error),
        "n_late_ratio": float(max(load_late_ratios) if load_late_ratios else 0.0),
        "max_late_ms": float(load_max_late),
        "socket_drops": int(load_socket_drops + int(probe_rx.get("socket_drops_delta", 0))),
        "n_foreign": int(load_foreign + int(probe_rx.get("n_foreign_packets", 0))),
        "load_socket_drops": int(load_socket_drops),
        "load_n_foreign": int(load_foreign),
        "probe_sender_meta": probe_tx,
        "probe_receiver_meta": probe_rx,
        "owd_counts": counts,
        "owd_steady_state": dict(owd.get("steady_state", {})),
        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "env": run_env(),
    }
    return row


def gate_live(row: Mapping[str, Any]) -> List[str]:
    bad: List[str] = []
    if int(row.get("socket_drops", 0)) != 0:
        bad.append("socket_drops=%d" % int(row.get("socket_drops", 0)))
    if int(row.get("n_foreign", 0)) != 0:
        bad.append("foreign=%d" % int(row.get("n_foreign", 0)))
    if float(row.get("max_abs_rate_error", 0.0)) > 1e-4:
        bad.append("rate=%.7f" % float(row.get("max_abs_rate_error", 0.0)))
    if float(row.get("max_abs_rho_error", 0.0)) > 0.002:
        bad.append("rho=%.5f" % float(row.get("max_abs_rho_error", 0.0)))
    if float(row.get("n_late_ratio", 0.0)) > 0.001:
        bad.append("late=%.4f" % float(row.get("n_late_ratio", 0.0)))
    if float(row.get("max_late_ms", 0.0)) > 50.0:
        bad.append("maxlate=%.1f" % float(row.get("max_late_ms", 0.0)))
    if float(row.get("probe_intrusion_ratio", 1.0)) > PROBE_INTRUSION_MAX:
        bad.append(
            "probe_intrusion=%.4f>%.4f"
            % (float(row.get("probe_intrusion_ratio", 1.0)), float(PROBE_INTRUSION_MAX))
        )
    if row.get("vl1g_run_pass") is False:
        bad.append("V-L1g-run")
    if not math.isfinite(float(row.get("q_mean_ms", float("nan")))):
        bad.append("q_mean_nan")
    if int(row.get("n_recv_unique", 0)) <= 0:
        bad.append("probe_empty")
    return bad


def measure_point(
    net: Any,
    point: Mapping[str, Any],
    args: argparse.Namespace,
    qdisc_ifaces: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    cleanup_live_processes()
    time.sleep(0.2)
    direct_before = direct_packet_snapshot(qdisc_ifaces or {})
    load_specs = start_background_loads(net, point, args)
    probe = run_measure_probe(net, point, args)
    load_meta = _wait_for_load_meta(load_specs)
    direct_after = direct_packet_snapshot(qdisc_ifaces or {})
    return attach_direct_packet_delta(
        _row_from_measurement(point, args, load_specs, load_meta, probe),
        direct_before,
        direct_after,
    )


def summarize_state(state: Mapping[str, Any], plan: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    rows = list(state.get("rows", []))
    fails = [row for row in rows if row.get("gate_fail")]
    rate_errors = [float(row.get("max_abs_rate_error", 0.0)) for row in rows]
    intrusions = [float(row.get("probe_intrusion_ratio", 0.0)) for row in rows]
    direct_deltas = [
        int(v)
        for row in rows
        for v in dict(row.get("direct_packets_delta", {})).values()
    ]
    return {
        "phase": "20R.6",
        "branch": state.get("branch"),
        "n_plan": int(len(plan)),
        "n_done": int(len(set(int(idx) for idx in state.get("done_idx", [])))),
        "n_rows": int(len(rows)),
        "n_fail": int(len(fails)),
        "n_timeout_history": int(len(state.get("timeout_history", []))),
        "coverage_pass": bool(len(set(int(idx) for idx in state.get("done_idx", []))) == len(plan)) if plan else False,
        "fail_pass": bool(not fails),
        "max_abs_rate_error": max(rate_errors) if rate_errors else None,
        "max_probe_intrusion_ratio": max(intrusions) if intrusions else None,
        "max_direct_packets_delta": max(direct_deltas) if direct_deltas else None,
        "n_vl1g_run_fail_rows": sum(1 for row in rows if row.get("vl1g_run_pass") is False),
        "n_socket_drop_rows": sum(1 for row in rows if int(row.get("socket_drops", 0)) != 0),
        "n_foreign_rows": sum(1 for row in rows if int(row.get("n_foreign", 0)) != 0),
    }


def print_plan(plan: Sequence[Mapping[str, Any]], todo: Sequence[Mapping[str, Any]], state: Mapping[str, Any], args: argparse.Namespace) -> None:
    print(
        "Ke hoach %d diem | da xong %d | phien nay %d diem (~%.1f phut)"
        % (
            len(plan),
            len(set(int(i) for i in state.get("done_idx", []))),
            len(todo),
            len(todo) * (float(args.duration) + 13.0) / 60.0,
        )
    )
    print("branch=%s state=%s raw=%s plan_digest=%s" % (args.branch, args.state, args.raw_dir, stable_digest(list(plan))))
    for point in todo:
        target = point.get("path") or point.get("link")
        print(
            "%04d %-6s %-7s rho_bar=%.3f seed=%d target=%s"
            % (int(point["idx"]), point["branch"], point["mode"], float(point["rho_bar"]), int(point["seed"]), target)
        )


def run_smoke_topo(args: argparse.Namespace) -> None:
    from mininet.link import Link
    from mininet.net import Mininet
    from mininet.node import OVSBridge
    from mininet.topology_tandem import TandemTopo, configure_qdiscs

    saved_sysctl = disable_ipv6_on_new_links()
    net = None
    try:
        net = Mininet(topo=TandemTopo(), link=Link, switch=OVSBridge, controller=None)
        net.start()
        proof = configure_qdiscs(net)
        qdisc_ifaces = measured_qdisc_ifaces_from_proof(proof)
        direct_before = direct_packet_snapshot(qdisc_ifaces)
        checks = {
            "hsrc_to_hdst": net.ping([net.get("hsrc"), net.get("hdst")], timeout="1"),
            "link_probes": {},
        }
        for idx in range(1, len(TANDEM_LINKS) + 1):
            checks["link_probes"]["L%d" % idx] = net.ping([net.get("hpa%d" % idx), net.get("hpb%d" % idx)], timeout="1")
        direct_after = direct_packet_snapshot(qdisc_ifaces)
        direct_delta = {
            name: int(direct_after[name]) - int(before)
            for name, before in direct_before.items()
        }
        out = {
            "phase": "20R.6",
            "smoke": "tandem_topology",
            "n_measured_links": len(proof["measured"]),
            "measured_links": [
                {
                    "idx": row["idx"],
                    "link": row["link"],
                    "if_fwd": row["if_fwd"],
                    "if_rev": row["if_rev"],
                    "bw": row["bw"],
                    "q": row["q"],
                    "base_ms": row["base_ms"],
                    "kinds": row["measure_assert"]["kinds"],
                    "bfifo_limit_bytes": row["measure_assert"]["bfifo_limit_bytes"],
                }
                for row in proof["measured"]
            ],
            "n_access_checked": len(proof["access"]),
            "ping_loss_percent": checks,
            "direct_packets_before": direct_before,
            "direct_packets_after": direct_after,
            "direct_packets_delta": direct_delta,
            "vl1g_run_pass": bool(all(v == 0 for v in direct_delta.values())),
            "qdisc_reinstall_log": list(proof.get("qdisc_reinstall_log", [])),
            "sysctl_saved": saved_sysctl,
            "pass": bool(
                checks["hsrc_to_hdst"] == 0.0
                and all(v == 0.0 for v in checks["link_probes"].values())
                and all(v == 0 for v in direct_delta.values())
            ),
        }
        print(json.dumps(out, indent=2, sort_keys=True))
    finally:
        if net is not None:
            stop_net_best_effort(net, args.stop_timeout)
        restore_sysctl(saved_sysctl)


def run_live(args: argparse.Namespace) -> None:
    rhos = parse_float_list(args.rho_bar) if args.rho_bar else _default_rhos(args.branch)
    modes = parse_list(args.modes)
    seeds = parse_int_list(args.seeds)
    plan = build_plan(args.branch, modes=modes, rho_bars=rhos, seeds=seeds)
    state = load_state(args.state, args.branch, plan, args)
    todo = select_todo(plan, state, args.max_points)

    if args.summary:
        print(json.dumps(summarize_state(state, plan), indent=2, sort_keys=True))
        return
    if args.plan_only:
        print_plan(plan, todo, state, args)
        return

    from mininet.link import Link
    from mininet.net import Mininet
    from mininet.node import OVSBridge
    from mininet.topology_tandem import TandemTopo, configure_qdiscs

    os.makedirs(args.raw_dir, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    state.setdefault("plan_digest", stable_digest(list(plan)))
    state.setdefault("raw_dir", args.raw_dir)
    write_json_atomic(args.state, state)
    print_plan(plan, todo, state, args)

    saved_sysctl = disable_ipv6_on_new_links()
    net = None
    try:
        net = Mininet(topo=TandemTopo(), link=Link, switch=OVSBridge, controller=None)
        net.start()
        proof = configure_qdiscs(net)
        proof["sysctl_saved"] = saved_sysctl
        state["qdisc_proof"] = proof
        qdisc_ifaces = measured_qdisc_ifaces_from_proof(proof)
        write_json_atomic(args.state, state)
        t0 = time.time()
        for k, point in enumerate(todo, start=1):
            try:
                with deadline(args.point_timeout, "point idx=%d" % int(point["idx"])):
                    row = measure_point(net, point, args, qdisc_ifaces=qdisc_ifaces)
            except PointTimeout as exc:
                cleanup_live_processes()
                timeout_row = {
                    **dict(point),
                    "reason": str(exc),
                    "timeout_s": float(args.point_timeout),
                    "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                state.setdefault("timeout_history", []).append(timeout_row)
                write_json_atomic(args.state, state)
                print(
                    "TIMEOUT idx=%d after %.1f s; khong danh dau done, resume bang process moi"
                    % (int(point["idx"]), float(args.point_timeout)),
                    file=sys.stderr,
                )
                raise SystemExit(3)
            row["gate_fail"] = gate_live(row)
            row["attempt"] = 1
            if row["gate_fail"] and retryable_gate_fail(row["gate_fail"]):
                print("      * fail: %s -> chay lai 1 lan" % ",".join(row["gate_fail"]))
                try:
                    with deadline(args.point_timeout, "retry idx=%d" % int(point["idx"])):
                        row2 = measure_point(net, point, args, qdisc_ifaces=qdisc_ifaces)
                except PointTimeout as exc:
                    cleanup_live_processes()
                    timeout_row = {
                        **dict(point),
                        "attempt": 2,
                        "attempt1_fail": row["gate_fail"],
                        "reason": str(exc),
                        "timeout_s": float(args.point_timeout),
                        "wall_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }
                    state.setdefault("timeout_history", []).append(timeout_row)
                    write_json_atomic(args.state, state)
                    print(
                        "TIMEOUT retry idx=%d after %.1f s; khong danh dau done, resume bang process moi"
                        % (int(point["idx"]), float(args.point_timeout)),
                        file=sys.stderr,
                    )
                    raise SystemExit(3)
                row2["gate_fail"] = gate_live(row2)
                row2["attempt"] = 2
                row2["attempt1_fail"] = row["gate_fail"]
                row = row2
            elif row["gate_fail"]:
                print("      * fail: %s -> khong retry vi la validity gate" % ",".join(row["gate_fail"]))

            state.setdefault("rows", []).append(row)
            state.setdefault("done_idx", []).append(point["idx"])
            if row.get("gate_fail"):
                state.setdefault("failed_rows", []).append(row)
            write_json_atomic(args.state, state)
            eta = (time.time() - t0) / float(k) * (len(todo) - k) / 60.0
            target = row.get("path") or row.get("link")
            print(
                "[%3d/%3d] %-6s %-7s rho_bar=%.3f seed=%d target=%s | "
                "cost=%7.3f q=%7.3f p95=%7.3f loss=%.4f intr=%.4f | %-4s (con %.1f phut)"
                % (
                    k,
                    len(todo),
                    row["branch"],
                    row["mode"],
                    float(row["rho_bar"]),
                    int(row["seed"]),
                    target,
                    float(row["cost_ms"]),
                    float(row["q_mean_ms"]),
                    float(row["q_p95_ms"]),
                    float(row["loss"]),
                    float(row["probe_intrusion_ratio"]),
                    "OK" if not row.get("gate_fail") else "FAIL",
                    eta,
                )
            )
    finally:
        if net is not None:
            stop_net_best_effort(net, args.stop_timeout)
        restore_sysctl(saved_sysctl)
        write_json_atomic(args.state, state)
    print("\n=== TONG KET ===")
    print(json.dumps(summarize_state(state, plan), indent=2, sort_keys=True))
    print("state -> %s" % args.state)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch", choices=BRANCHES, default="Aprime")
    ap.add_argument("--modes", default=",".join(MODES))
    ap.add_argument("--rho-bar", default="", help="comma-separated rho_bar values; default depends on branch")
    ap.add_argument("--seeds", default=",".join(str(seed) for seed in SEEDS))
    ap.add_argument("--state", default="", help="checkpoint path; default depends on branch")
    ap.add_argument("--raw-dir", default=RAW)
    ap.add_argument("--calibration", default=D.CALIBRATION)
    ap.add_argument("--duration", type=float, default=DUR)
    ap.add_argument("--warmup", type=float, default=WARM)
    ap.add_argument("--probe-rate", type=float, default=DEFAULT_PROBE_RATE_PPS)
    ap.add_argument("--probe-size", type=int, default=DEFAULT_PROBE_SIZE_BYTES)
    ap.add_argument("--point-timeout", type=float, default=180.0)
    ap.add_argument("--stop-timeout", type=float, default=20.0)
    ap.add_argument("--max-points", type=int, default=None)
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--smoke-topo", action="store_true")
    args = ap.parse_args(argv)

    if not args.state:
        args.state = DEFAULT_STATE[args.branch]
    if args.probe_rate <= 0.0:
        ap.error("--probe-rate phai > 0")
    if args.probe_size < 32:
        ap.error("--probe-size qua nho")
    if args.smoke_topo:
        run_smoke_topo(args)
        return 0
    run_live(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

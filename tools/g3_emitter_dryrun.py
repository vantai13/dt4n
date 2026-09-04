#!/usr/bin/env python3
"""Real-time, no-Mininet dry-run for the Phase-G packet emitter."""
from __future__ import annotations

import argparse
import gc
import glob
import hashlib
import json
import multiprocessing as mp
import os
import queue
import socket
import subprocess
import time
import traceback
from pathlib import Path

import numpy as np

from mininet.modulated_emitter import (
    SPIN_THRESHOLD_S,
    EmitterState,
    atomic_int64_array,
    deadline_phase_fraction,
    emit_window,
    pin_current_process,
)
from mininet.tick_sampler import sample_at
from measurements.rho_from_counters import (
    emit4_prime as evaluate_emit4_prime,
    rho_from_counters,
    sampling_grid_diagnostics,
)
from tools.g1_quant_model import WIRE_BYTES_DEFAULT
from tools.g2_topology import CAP_BPS, LINKS, a0_from_sigma_at, sigma_per_link
from tools.g3_dryrun import acf, physical_trace, quantization_step_packets
from tools.g1_quant_model import acf1_predicted_mechanism_a


SEED = 20260908
DT_S = 0.2
DURATION_S = 60.0
REPLICATES = 16
N_WINDOWS = int(DURATION_S / DT_S)
PAYLOAD_BYTES = 1400
WIRE_BYTES = WIRE_BYTES_DEFAULT
REQUIRED_ROLES = 10
MIN_LADDER_CPUS = 8
START_DELAY_S = 1.0
JOIN_SLACK_S = 10.0
PREREG_TAG = "phase-G-g3-emitter-run-2-prereg"
A016_PREREG_TAG = "phase-G-g3-a016-prereg"
A016_DURATION_S = 30.0
A016_REPLICATES = 8
A016_N_WINDOWS = int(A016_DURATION_S / DT_S)
CELLS = (
    {"name": "anchor", "sigma_ref": 0.030348837209302317, "tau_s": 3.0},
    {"name": "stress", "sigma_ref": 0.020232558139534878, "tau_s": 30.0},
)

GATE_OVERRUN_FRACTION = 0.001
GATE_QUANT_SIGN = -0.05
GATE_QUANT_PREDICTION = 0.05
GATE_TIMING_CORRELATION = 0.10
GATE_SNAPSHOT_P99_S = 0.001
# G-A015. Neither constant below is new. The sampler is held to the same
# tolerance as the emitter because both are one-process timing failures, and
# the alignment tolerance is their union bound: a mismatch requires the
# emitter to finish late OR the sampler to read late.
GATE_SAMPLER_LATE_FRACTION = GATE_OVERRUN_FRACTION
GATE_ALIGNMENT_MISMATCH = GATE_OVERRUN_FRACTION + GATE_SAMPLER_LATE_FRACTION
EMIT3_NULL_TRIALS = 3000
EMIT3_NULL_SEED = 20260909
EMIT3_SAFETY_FACTOR = 1.957
EMIT3_PRIME_NULL_TRIALS = 3000
EMIT3_PRIME_NULL_SEED = 20260911
EMIT3_PRIME_NULL_WINDOWS = N_WINDOWS - 1
GATE_COMMON_MODE_RATIO = 0.05
GATE_P_STALL = 0.02
DEFAULT_HOST_JITTER_ARTIFACT = Path(
    "results/SMOKE/phase-G/host_jitter_after_quiesce.json"
)


def git_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() or "unknown"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_cpu_map(text: str) -> tuple[tuple[int, ...], int, int]:
    """Parse eight emitter CPUs followed by sampler and sink CPUs."""
    try:
        values = tuple(int(item.strip()) for item in text.split(","))
    except ValueError as exc:
        raise ValueError("cpu-map must contain comma-separated integers") from exc
    if len(values) != REQUIRED_ROLES:
        raise ValueError("cpu-map must contain 8 emitter, 1 sampler, 1 sink CPU")
    if min(values) < 0:
        raise ValueError("cpu-map CPUs must be non-negative")
    emitter_cpus, sampler_cpu, sink_cpu = values[:8], values[8], values[9]
    if sampler_cpu == sink_cpu or sampler_cpu in emitter_cpus or sink_cpu in emitter_cpus:
        raise ValueError("sampler and sink CPUs must be isolated from emitters")
    return emitter_cpus, sampler_cpu, sink_cpu


def physical_core_map() -> dict[int, int]:
    """Return ``{logical_cpu: physical_core_id}`` from sysfs, empty if absent."""
    mapping: dict[int, int] = {}
    for path in sorted(glob.glob("/sys/devices/system/cpu/cpu[0-9]*/topology/core_id")):
        name = path.split("/")[5]
        try:
            with open(path, encoding="utf-8") as handle:
                mapping[int(name[3:])] = int(handle.read().strip())
        except (OSError, ValueError):
            continue
    return mapping


def host_pressure_snapshot(
    *,
    pressure_path: str = "/proc/pressure/cpu",
    stat_path: str = "/proc/stat",
) -> dict[str, object]:
    """Read PSI and cumulative steal time for mechanical host evidence."""
    psi: dict[str, dict[str, float]] = {}
    try:
        with open(pressure_path, encoding="utf-8") as handle:
            for line in handle:
                fields = line.split()
                if not fields:
                    continue
                psi[fields[0]] = {
                    key: float(value)
                    for key, value in (
                        field.split("=", 1) for field in fields[1:] if "=" in field
                    )
                }
    except OSError:
        psi = {}
    steal_ticks = None
    steal_fraction_since_boot = None
    load1 = None
    try:
        with open(stat_path, encoding="utf-8") as handle:
            fields = handle.readline().split()
        if fields and fields[0] == "cpu" and len(fields) > 8:
            ticks = [int(value) for value in fields[1:]]
            steal_ticks = ticks[7]
            total = sum(ticks)
            steal_fraction_since_boot = steal_ticks / total if total else 0.0
    except (OSError, ValueError):
        pass
    try:
        with open("/proc/loadavg", encoding="utf-8") as handle:
            load1 = float(handle.read().split()[0])
    except (OSError, ValueError, IndexError):
        pass
    return {
        "cpu_psi": psi,
        "steal_ticks_since_boot": steal_ticks,
        "steal_fraction_since_boot": steal_fraction_since_boot,
        "load1": load1,
        "load1_diagnostic_reference": 0.10,
        "load1_below_diagnostic_reference": (
            load1 is not None and load1 <= 0.10
        ),
    }


def host_jitter_admission(path: Path) -> dict[str, object]:
    """Admit on measured >=1 ms stall-window rate; keep load1 diagnostic."""
    result: dict[str, object] = {
        "artifact": str(path),
        "gate_p_stall_1ms": GATE_P_STALL,
        "available": path.is_file(),
        "pass": False,
    }
    if not path.is_file():
        result["reason"] = "after-quiesce host jitter artifact is missing"
        return result
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        p_stall = float(payload["p_stall_1ms"])
        duration_s = float(payload["scheduled_duration_s"])
        threshold_s = float(payload["stall_threshold_s"])
        tool_path = Path(str(payload["tool_path"]))
        declared_sha = str(payload["tool_sha256"])
        commit = str(payload["git_hash"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        result["reason"] = f"invalid host jitter artifact: {exc}"
        return result
    commit_probe = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{tool_path.as_posix()}"],
        capture_output=True,
        check=False,
    )
    checks = {
        "schema": payload.get("schema") == "dt4n.phase_g.host_jitter_probe.v1",
        "scenario_after_quiesce": payload.get("scenario") == "after_quiesce",
        "duration_at_least_60s": duration_s >= 60.0,
        "threshold_is_1ms": threshold_s == 1e-3,
        "p_stall_in_domain": 0.0 <= p_stall <= 1.0,
        "tool_path_expected": tool_path.as_posix() == "tools/host_jitter_probe.py",
        "tool_exists": tool_path.is_file(),
        "tool_sha256_matches": (
            tool_path.is_file() and sha256(tool_path) == declared_sha
        ),
        "commit_contains_tool": commit_probe.returncode == 0,
    }
    passed = all(checks.values()) and p_stall <= GATE_P_STALL
    result.update({
        "p_stall_1ms": p_stall,
        "scenario": payload.get("scenario"),
        "scheduled_duration_s": duration_s,
        "checks": checks,
        "verdict": "PASS" if passed else "FAIL",
        "pass": passed,
    })
    if not passed:
        result["reason"] = "integrity/shape check failed or p_stall exceeds gate"
    return result


def cpu_preflight(cpu_map: tuple[int, ...]) -> dict[str, object]:
    allowed = set(os.sched_getaffinity(0))
    requested = set(cpu_map)
    missing = sorted(requested - allowed)
    emitter_cpus = cpu_map[:8]
    sampler_cpu, sink_cpu = cpu_map[8], cpu_map[9]
    role_isolation = (
        sampler_cpu != sink_cpu
        and sampler_cpu not in emitter_cpus
        and sink_cpu not in emitter_cpus
    )
    cores = physical_core_map()
    emitter_cores = {cores[cpu] for cpu in emitter_cpus if cpu in cores}
    physical = {
        "available": bool(cores),
        "physical_core_count": len(set(cores.values())) or None,
        "smt_threads_per_core": (
            len(cores) / len(set(cores.values())) if cores else None
        ),
        "emitter_physical_core_count": len(emitter_cores) or None,
        "emitters_per_physical_core": (
            len(emitter_cpus) / len(emitter_cores) if emitter_cores else None
        ),
        # role_isolation above is a LOGICAL check. On an SMT host a sampler
        # can sit on a logical CPU that shares its physical core with an
        # emitter, which logical isolation cannot see. REPORTED, not gated:
        # gating it now, with this host's topology already known, would be an
        # outcome-based change.
        "sampler_shares_core_with_emitter": (
            cores.get(sampler_cpu) in emitter_cores if cores else None
        ),
        "sink_shares_core_with_emitter": (
            cores.get(sink_cpu) in emitter_cores if cores else None
        ),
    }
    return {
        "allowed_cpus": sorted(allowed),
        "requested_cpus": list(cpu_map),
        "emitter_core_count": len(set(emitter_cpus)),
        "emitters_per_core": len(emitter_cpus) / len(set(emitter_cpus)),
        "sampler_cpu": sampler_cpu,
        "sink_cpu": sink_cpu,
        "role_isolation": role_isolation,
        "physical": physical,
        "host_pressure": host_pressure_snapshot(),
        "missing": missing,
        "pass": role_isolation and not missing,
    }


def build_ladder_cpu_maps(
    allowed_cpus: tuple[int, ...] | None = None,
) -> dict[str, tuple[int, ...]]:
    """Build the preregistered L0/L1/L2 mappings on an eight-CPU cpuset."""
    allowed = tuple(sorted(
        os.sched_getaffinity(0) if allowed_cpus is None else allowed_cpus
    ))
    if len(allowed) < MIN_LADDER_CPUS:
        raise RuntimeError("emitter ladder requires at least eight allowed CPUs")
    emitter_pool = allowed[:6]
    sampler_cpu, sink_cpu = allowed[-2], allowed[-1]

    def assign(width: int) -> tuple[int, ...]:
        emitters = tuple(emitter_pool[index % width] for index in range(8))
        return emitters + (sampler_cpu, sink_cpu)

    return {"L0": assign(6), "L1": assign(3), "L2": assign(1)}


def sampler_margin_s(window_sent: np.ndarray, dt_s: float = DT_S) -> np.ndarray:
    """Per-window slack the sampler has before the NEXT window's first packet.

    The sampler must read at ``t_end`` of window ``w`` before the emitter of
    window ``w+1`` sends, whose first deadline is ``t_end + 0.5*dt/n``. The
    binding link is the one sending the most packets in that next window, and
    ``n`` is read from the ledger rather than assumed from the mean load, so
    the margin tightens automatically wherever the modulated rate is highest.
    Returns one margin per window boundary that has a successor.
    """
    counts = np.asarray(window_sent, dtype=float)
    if counts.ndim != 2 or counts.shape[1] < 2:
        raise ValueError("window_sent must be (link, window) with two windows")
    busiest_next = counts[:, 1:].max(axis=0)
    if np.any(busiest_next <= 0.0):
        raise ValueError("a window sends no packet on any link; margin undefined")
    return 0.5 * dt_s / busiest_next


def remote_provenance(prereg_tag: str = PREREG_TAG) -> dict[str, object]:
    head = git_hash()
    result = subprocess.run(
        [
            "git", "ls-remote", "origin", "refs/heads/main",
            f"refs/tags/{prereg_tag}^{{}}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    refs = {}
    for line in result.stdout.splitlines():
        object_id, ref = line.split(maxsplit=1)
        refs[ref] = object_id
    remote_main = refs.get("refs/heads/main")
    remote_tag = refs.get(f"refs/tags/{prereg_tag}^{{}}")
    return {
        "local_head": head,
        "remote_main": remote_main,
        "remote_prereg_tag_commit": remote_tag,
        "command_exit": result.returncode,
        "pass": result.returncode == 0 and remote_main == head and remote_tag == head,
    }


def _ready(ready_queue, role: str) -> None:
    ready_queue.put(("ready", role, os.getpid()))


def _failed(error_queue, role: str) -> None:
    error_queue.put((role, traceback.format_exc()))


def _receiver_worker(
    bound_socket,
    receiver_counts,
    stop_event,
    start_event,
    cpu,
    ready_queue,
    error_queue,
) -> None:
    role = "sink"
    try:
        pin_current_process(cpu)
        bound_socket.settimeout(0.05)
        _ready(ready_queue, role)
        start_event.wait()
        quiet_after_stop = 0
        while quiet_after_stop < 3:
            try:
                payload, _address = bound_socket.recvfrom(PAYLOAD_BYTES + 64)
                if not payload:
                    continue
                link_index = int(payload[0])
                if not 0 <= link_index < len(LINKS):
                    raise RuntimeError(f"invalid link marker {link_index}")
                receiver_counts[link_index] += 1
                quiet_after_stop = 0
            except socket.timeout:
                if stop_event.is_set():
                    quiet_after_stop += 1
        bound_socket.close()
    except BaseException:
        _failed(error_queue, role)
        raise


def _emitter_worker(
    link_index,
    cpu,
    rates_pps,
    destination,
    epoch_value,
    start_event,
    shared_sent_cumulative,
    window_sent,
    window_lateness_ns,
    overrun_counts,
    overrun_max_ns,
    ready_queue,
    error_queue,
    dt_s=DT_S,
) -> None:
    role = f"emitter-{link_index}"
    sock = None
    try:
        pin_current_process(cpu)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(destination)
        payload = bytes([link_index]) + bytes(PAYLOAD_BYTES - 1)
        _ready(ready_queue, role)
        start_event.wait()
        state = EmitterState()
        phase = deadline_phase_fraction(link_index, len(LINKS))
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            for window_index, rate_pps in enumerate(rates_pps):
                row = emit_window(
                    window_index,
                    epoch_value.value,
                    dt_s,
                    float(rate_pps),
                    sock,
                    payload,
                    shared_sent_cumulative,
                    link_index,
                    state,
                    phase_fraction=phase,
                )
                offset = link_index * len(rates_pps) + window_index
                window_sent[offset] = row.sent_packets
                window_lateness_ns[offset] = int(round(
                    row.max_deadline_lateness_s * 1e9
                ))
        finally:
            if gc_was_enabled:
                gc.enable()
        overrun_counts[link_index] = state.overrun_windows
        overrun_max_ns[link_index] = int(round(state.overrun_max_s * 1e9))
    except BaseException:
        _failed(error_queue, role)
        raise
    finally:
        if sock is not None:
            sock.close()


def _sampler_worker(
    cpu,
    target_cumulative,
    epoch_value,
    start_event,
    sent_cumulative,
    receiver_counts,
    snapshot_sent,
    snapshot_measured,
    snapshot_spans_ns,
    tick_lateness_ns,
    ready_queue,
    error_queue,
    dt_s=DT_S,
) -> None:
    role = "sampler"
    try:
        pin_current_process(cpu)
        _ready(ready_queue, role)
        start_event.wait()
        n_windows = target_cumulative.shape[1]
        for window_index in range(n_windows):
            row = sample_at(
                window_index,
                epoch_value.value + (window_index + 1) * dt_s,
                target_cumulative[:, window_index],
                sent_cumulative,
                lambda: receiver_counts,
            )
            for link_index in range(len(LINKS)):
                offset = link_index * n_windows + window_index
                snapshot_sent[offset] = row.sent_cumulative_packets[link_index]
                snapshot_measured[offset] = row.measured_cumulative_packets[
                    link_index
                ]
            snapshot_spans_ns[window_index] = int(round(row.snapshot_span_s * 1e9))
            tick_lateness_ns[window_index] = int(round(row.tick_lateness_s * 1e9))
    except BaseException:
        _failed(error_queue, role)
        raise


def _wait_ready(ready_queue, processes: list[mp.Process], timeout_s: float = 10.0):
    roles = []
    deadline = time.monotonic() + timeout_s
    while len(roles) < len(processes):
        remaining = deadline - time.monotonic()
        if remaining <= 0.0:
            raise RuntimeError(f"worker readiness timeout; ready={roles}")
        try:
            kind, role, _pid = ready_queue.get(timeout=remaining)
        except queue.Empty as exc:
            raise RuntimeError(f"worker readiness timeout; ready={roles}") from exc
        if kind == "ready":
            roles.append(role)
    return roles


def run_replicate(
    target: np.ndarray,
    emitter_cpus: tuple[int, ...],
    sampler_cpu: int,
    sink_cpu: int,
    *,
    dt_s: float = DT_S,
) -> dict[str, object]:
    """Run one eight-emitter UDP-loopback replicate on an absolute grid."""
    if target.ndim != 2 or target.shape[0] != len(LINKS) or target.shape[1] < 2:
        raise ValueError("target must have shape (link, >=2 windows)")
    if not np.isfinite(dt_s) or dt_s <= 0.0:
        raise ValueError("dt_s must be finite and positive")
    n_windows = target.shape[1]
    context = mp.get_context("fork")
    sent_cumulative = atomic_int64_array(len(LINKS))
    receiver_counts = atomic_int64_array(len(LINKS))
    window_sent = atomic_int64_array(len(LINKS) * n_windows)
    window_lateness_ns = atomic_int64_array(len(LINKS) * n_windows)
    snapshot_sent = atomic_int64_array(len(LINKS) * n_windows)
    snapshot_measured = atomic_int64_array(len(LINKS) * n_windows)
    snapshot_spans_ns = atomic_int64_array(n_windows)
    tick_lateness_ns = atomic_int64_array(n_windows)
    overrun_counts = atomic_int64_array(len(LINKS))
    overrun_max_ns = atomic_int64_array(len(LINKS))
    epoch_value = context.Value("d", 0.0, lock=False)
    start_event = context.Event()
    stop_event = context.Event()
    ready_queue = context.Queue()
    error_queue = context.Queue()

    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
    receiver_socket.bind(("127.0.0.1", 0))
    destination = receiver_socket.getsockname()
    target_packets = target * CAP_BPS[:, None] * dt_s / (WIRE_BYTES * 8.0)
    target_cumulative = np.cumsum(target_packets, axis=1)
    rates_pps = target * CAP_BPS[:, None] / (WIRE_BYTES * 8.0)

    processes = [context.Process(
        target=_receiver_worker,
        args=(receiver_socket, receiver_counts, stop_event, start_event, sink_cpu,
              ready_queue, error_queue),
        name="g3-sink",
    )]
    processes.append(context.Process(
        target=_sampler_worker,
        args=(sampler_cpu, target_cumulative, epoch_value, start_event,
              sent_cumulative, receiver_counts, snapshot_sent, snapshot_measured,
              snapshot_spans_ns, tick_lateness_ns, ready_queue, error_queue,
              dt_s),
        name="g3-sampler",
    ))
    for link_index, cpu in enumerate(emitter_cpus):
        processes.append(context.Process(
            target=_emitter_worker,
            args=(link_index, cpu, rates_pps[link_index].tolist(), destination,
                  epoch_value, start_event, sent_cumulative, window_sent,
                  window_lateness_ns, overrun_counts, overrun_max_ns,
                  ready_queue, error_queue, dt_s),
            name=f"g3-emitter-{LINKS[link_index]}",
        ))
    for process in processes:
        process.start()
    try:
        ready_roles = _wait_ready(ready_queue, processes)
        epoch_value.value = time.perf_counter() + START_DELAY_S
        start_event.set()
        deadline = n_windows * dt_s + START_DELAY_S + JOIN_SLACK_S
        for process in processes[1:]:
            process.join(timeout=deadline)
            if process.is_alive():
                raise RuntimeError(f"worker timeout: {process.name}")
        stop_event.set()
        processes[0].join(timeout=2.0)
        if processes[0].is_alive():
            raise RuntimeError("sink timeout")
        failures = [p for p in processes if p.exitcode != 0]
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get_nowait())
        if failures or errors:
            raise RuntimeError(
                f"worker failures={[p.name for p in failures]} errors={errors}"
            )
    finally:
        stop_event.set()
        start_event.set()
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(timeout=1.0)
        receiver_socket.close()

    def matrix(values):
        return np.fromiter(values, dtype=np.int64).reshape(len(LINKS), n_windows)

    return {
        "ready_roles": ready_roles,
        "target_packets": target_packets,
        "window_sent": matrix(window_sent),
        "window_lateness_s": matrix(window_lateness_ns) / 1e9,
        "snapshot_sent": matrix(snapshot_sent),
        "snapshot_measured": matrix(snapshot_measured),
        "snapshot_spans_s": np.fromiter(snapshot_spans_ns, dtype=np.int64) / 1e9,
        "tick_lateness_s": np.fromiter(tick_lateness_ns, dtype=np.int64) / 1e9,
        "overrun_counts": np.fromiter(overrun_counts, dtype=np.int64),
        "overrun_max_s": np.fromiter(overrun_max_ns, dtype=np.int64) / 1e9,
        "final_sent": np.fromiter(sent_cumulative, dtype=np.int64),
        "final_received": np.fromiter(receiver_counts, dtype=np.int64),
    }


def _correlation_max_abs(pooled: np.ndarray) -> tuple[float, list[list[float]]]:
    if pooled.shape[0] != len(LINKS):
        raise ValueError("pooled timing residual has wrong link dimension")
    if np.any(np.std(pooled, axis=1) <= 0.0):
        return float("inf"), np.full((len(LINKS), len(LINKS)), np.nan).tolist()
    matrix = np.corrcoef(pooled)
    upper = matrix[np.triu_indices(len(LINKS), 1)]
    return float(np.max(np.abs(upper))), matrix.tolist()


def mean_correlation_then_max(
    replicates: np.ndarray,
) -> tuple[float, list[list[float]]]:
    """Average replicate correlation matrices before maximizing over pairs."""
    values = np.asarray(replicates, dtype=float)
    if values.ndim != 3 or values.shape[1] != len(LINKS):
        raise ValueError("replicates must have shape (replicate, link, window)")
    matrices = []
    for replicate in values:
        if np.any(np.std(replicate, axis=1) <= 0.0):
            return (
                float("inf"),
                np.full((len(LINKS), len(LINKS)), np.nan).tolist(),
            )
        matrices.append(np.corrcoef(replicate))
    mean_matrix = np.mean(np.asarray(matrices), axis=0)
    upper = mean_matrix[np.triu_indices(len(LINKS), 1)]
    return float(np.max(np.abs(upper))), mean_matrix.tolist()


def simulate_emit3_null(
    *,
    trials: int = EMIT3_NULL_TRIALS,
    replicates: int = REPLICATES,
    windows: int = N_WINDOWS,
    seed: int = EMIT3_NULL_SEED,
    batch_size: int = 25,
) -> dict[str, float | int]:
    """Calibrate mean-matrix-then-max under eight independent white series."""
    if min(trials, replicates, windows, batch_size) <= 0:
        raise ValueError("null simulation dimensions must be positive")
    rng = np.random.default_rng(seed)
    maxima = np.empty(trials, dtype=float)
    upper = np.triu_indices(len(LINKS), 1)
    offset = 0
    while offset < trials:
        count = min(batch_size, trials - offset)
        values = rng.standard_normal(
            (count, replicates, len(LINKS), windows)
        )
        values -= values.mean(axis=-1, keepdims=True)
        norms = np.sqrt(np.sum(values * values, axis=-1))
        covariance = np.einsum("brin,brjn->brij", values, values)
        correlations = covariance / (
            norms[:, :, :, None] * norms[:, :, None, :]
        )
        mean_matrices = correlations.mean(axis=1)
        maxima[offset:offset + count] = np.max(
            np.abs(mean_matrices[:, upper[0], upper[1]]), axis=1
        )
        offset += count
    return {
        "trials": trials,
        "replicates": replicates,
        "windows": windows,
        "seed": seed,
        "median": float(np.quantile(maxima, 0.50)),
        "p95": float(np.quantile(maxima, 0.95)),
        "p99": float(np.quantile(maxima, 0.99)),
        "gate": GATE_TIMING_CORRELATION,
        "gate_over_p99": float(
            GATE_TIMING_CORRELATION / np.quantile(maxima, 0.99)
        ),
    }


def simulate_emit3_prime_null(
    *,
    trials: int = EMIT3_PRIME_NULL_TRIALS,
    replicates: int = REPLICATES,
    windows: int = EMIT3_PRIME_NULL_WINDOWS,
    seed: int = EMIT3_PRIME_NULL_SEED,
    batch_size: int = 25,
) -> dict[str, float | int]:
    """Calibrate EMIT-3' under its exact W-1 reduction operator."""
    result = simulate_emit3_null(
        trials=trials,
        replicates=replicates,
        windows=windows,
        seed=seed,
        batch_size=batch_size,
    )
    result["safety_factor"] = EMIT3_SAFETY_FACTOR
    result["gate"] = EMIT3_SAFETY_FACTOR * float(result["p99"])
    result["gate_over_p99"] = EMIT3_SAFETY_FACTOR
    return result


def emit3_prime_null_p99() -> float:
    """Return the signed deterministic p99 for tests and artifact builders."""
    return float(simulate_emit3_prime_null()["p99"])


def load_residual(run: dict[str, object], cap_bps: np.ndarray = CAP_BPS) -> np.ndarray:
    """Return measured-minus-sent load on actual sampler intervals."""
    measured_packets = np.asarray(run["snapshot_measured"], dtype=float)
    sent_packets = np.asarray(run["window_sent"], dtype=float)
    lateness = np.asarray(run["tick_lateness_s"], dtype=float)
    capacity = np.asarray(cap_bps, dtype=float)
    if measured_packets.shape != sent_packets.shape:
        raise ValueError("measured and sent ledgers must have identical shapes")
    if measured_packets.ndim != 2 or measured_packets.shape[0] != capacity.size:
        raise ValueError("ledger shape disagrees with cap_bps")
    wire_bytes = measured_packets * float(WIRE_BYTES)
    rho_result = rho_from_counters(wire_bytes, lateness, capacity, DT_S)
    rho_sent = (
        sent_packets[:, 1:]
        * (WIRE_BYTES * 8.0)
        / (capacity[:, None] * DT_S)
    )
    return rho_result["rho"] - rho_sent


def emit3_prime(
    cell_runs: list[dict[str, object]], cap_bps: np.ndarray = CAP_BPS
) -> tuple[float, list[list[float]]]:
    """Apply the doc-41 reduction to load residuals, not timing proxies."""
    replicates = np.asarray([
        load_residual(run, cap_bps) for run in cell_runs
    ])
    return mean_correlation_then_max(replicates)


def emit4_prime_for_run(
    run: dict[str, object],
    a0: float,
    cap_bps: np.ndarray = CAP_BPS,
) -> dict[str, object]:
    """Evaluate EMIT-4' and sampling-grid limits for one physical run."""
    measured_packets = np.asarray(run["snapshot_measured"], dtype=float)
    wire_bytes = measured_packets * float(WIRE_BYTES)
    rho_result = rho_from_counters(
        wire_bytes,
        np.asarray(run["tick_lateness_s"], dtype=float),
        cap_bps,
        DT_S,
    )
    gate = evaluate_emit4_prime(
        rho_result,
        sigma_per_link(a0),
        gate_common_mode_ratio=GATE_COMMON_MODE_RATIO,
    )
    return {
        **gate,
        "grid": sampling_grid_diagnostics(rho_result["dt_actual_s"], DT_S),
    }


def analyze(
    cells: list[dict[str, object]],
    cpu_detail,
    provenance,
    *,
    emit3_prime_null: dict[str, float | int] | None = None,
    legacy_emit3_null: dict[str, float | int] | None = None,
) -> dict[str, object]:
    checks = []
    diagnostics = []

    def record(check_id, value, gate, passed, description, **extra):
        checks.append({
            "id": check_id, "value": value, "gate": gate,
            "verdict": "PASS" if passed else "FAIL",
            "description": description, **extra,
        })

    def diagnose(check_id, value, description, **extra):
        diagnostics.append({
            "id": check_id,
            "value": value,
            "status": "REPORTED_NOT_GATING",
            "description": description,
            **extra,
        })

    l0_cells = [cell for cell in cells if cell["level"] == "L0"]
    stress_cells = [cell for cell in cells if cell["name"] == "stress"]
    if len(l0_cells) != len(CELLS) or len(stress_cells) not in {1, 3}:
        raise ValueError("design must contain L0 anchor/stress; ladder is optional")
    replicate_count = len(l0_cells[0]["runs"])
    if replicate_count <= 0 or any(
        len(cell["runs"]) != replicate_count for cell in l0_cells
    ):
        raise ValueError("L0 cells must have the same positive replicate count")
    window_count = np.asarray(l0_cells[0]["runs"][0]["window_sent"]).shape[1]
    if window_count < 2:
        raise ValueError("runs must contain at least two windows")

    total_overruns = sum(
        int(np.sum(run["overrun_counts"]))
        for cell in l0_cells for run in cell["runs"]
    )
    total_windows = len(l0_cells) * replicate_count * len(LINKS) * window_count
    overrun_fraction = total_overruns / total_windows
    overrun_rows = []
    for cell in l0_cells:
        for index, link in enumerate(LINKS):
            count = sum(int(run["overrun_counts"][index]) for run in cell["runs"])
            windows = len(cell["runs"]) * window_count
            overrun_rows.append({
                "level": cell["level"], "cell": cell["name"],
                "link": link, "count": count,
                "windows": windows, "fraction": count / windows,
            })
    record("EMIT-1", overrun_fraction, GATE_OVERRUN_FRACTION,
           overrun_fraction <= GATE_OVERRUN_FRACTION,
           "socket pacing does not overrun into the next window",
           rows=overrun_rows)

    quant_rows = []
    emit2_pass = True
    for cell in l0_cells:
        acfs = np.asarray([
            [acf(run["window_sent"][i] - run["target_packets"][i])
             for i in range(len(LINKS))]
            for run in cell["runs"]
        ])
        observed = np.median(acfs, axis=0)
        steps = quantization_step_packets(
            cell["a0"], 0.0, cell["tau_s"], cell["tau_s"]
        )
        predicted = np.asarray([acf1_predicted_mechanism_a(x) for x in steps])
        for index, link in enumerate(LINKS):
            error = abs(observed[index] - predicted[index])
            passed = observed[index] >= GATE_QUANT_SIGN and error <= GATE_QUANT_PREDICTION
            emit2_pass = emit2_pass and passed
            quant_rows.append({
                "level": cell["level"], "cell": cell["name"], "link": link,
                "acf1_median": float(observed[index]),
                "acf1_predicted": float(predicted[index]),
                "prediction_abs_error": float(error),
                "verdict": "PASS" if passed else "FAIL",
            })
    diagnose(
        "EMIT-2",
        max(row["prediction_abs_error"] for row in quant_rows),
        "deterministic independent-round packet-step prediction",
        legacy_gate=GATE_QUANT_PREDICTION,
        legacy_verdict="PASS" if emit2_pass else "FAIL",
        rows=quant_rows,
        reduction=f"median of {replicate_count} replicates",
    )

    timing_rows = []
    for cell in stress_cells:
        timing_replicates = np.asarray([
            run["window_lateness_s"] for run in cell["runs"]
        ])
        timing_corr, timing_matrix = mean_correlation_then_max(
            timing_replicates
        )
        timing_rows.append({
            "level": cell["level"], "cell": cell["name"],
            "emitter_core_count": cpu_detail[cell["level"]][
                "emitter_core_count"
            ],
            "emitters_per_core": cpu_detail[cell["level"]][
                "emitters_per_core"
            ],
            "max_abs_offdiag": timing_corr,
            "correlation": timing_matrix,
        })
    l0_timing = next(row for row in timing_rows if row["level"] == "L0")
    diagnose(
        "EMIT-3",
        l0_timing["max_abs_offdiag"],
        "deadline-lateness shared-stall dose response",
        legacy_gate=GATE_TIMING_CORRELATION,
        legacy_verdict=(
            "PASS"
            if l0_timing["max_abs_offdiag"] <= GATE_TIMING_CORRELATION
            else "FAIL"
        ),
        l0_row=l0_timing,
        reduction=(
            f"mean of {replicate_count} within-replicate 8x8 matrices, "
            "then max 28 pairs"
        ),
    )

    prime_rows = []
    for cell in l0_cells:
        value, matrix = emit3_prime(cell["runs"])
        prime_rows.append({
            "level": cell["level"],
            "cell": cell["name"],
            "max_abs_offdiag": value,
            "correlation": matrix,
        })
    if emit3_prime_null is None:
        emit3_prime_null = simulate_emit3_prime_null(
            replicates=replicate_count, windows=window_count - 1
        )
    prime_gate = float(emit3_prime_null["gate"])
    prime_value = max(float(row["max_abs_offdiag"]) for row in prime_rows)
    record(
        "EMIT-3'",
        prime_value,
        prime_gate,
        prime_value <= prime_gate,
        "cross-link correlation of measured load residual",
        rows=prime_rows,
        calibration=emit3_prime_null,
        reduction="per L0 cell: mean replicate matrices, then max 28 pairs",
    )

    spans = np.concatenate([
        run["snapshot_spans_s"] for cell in l0_cells for run in cell["runs"]
    ])
    snap_p99 = float(np.quantile(spans, 0.99))
    record("EMIT-4a", snap_p99, GATE_SNAPSHOT_P99_S,
           snap_p99 <= GATE_SNAPSHOT_P99_S,
           "shared-tick snapshot read width",
           note="width of the read, not the lateness of the tick")

    emit4_prime_rows = []
    for cell in l0_cells:
        for replicate, run in enumerate(cell["runs"]):
            emit4_prime_rows.append({
                "level": cell["level"],
                "cell": cell["name"],
                "replicate": replicate,
                **emit4_prime_for_run(run, float(cell["a0"])),
            })
    emit4_prime_value = max(
        float(row["common_mode_ratio"]) for row in emit4_prime_rows
    )
    record(
        "EMIT-4'",
        emit4_prime_value,
        GATE_COMMON_MODE_RATIO,
        emit4_prime_value <= GATE_COMMON_MODE_RATIO,
        "sampler common-mode correction relative to designed signal",
        rows=emit4_prime_rows,
        reduction="maximum run-level ratio across L0 cells",
    )

    late_windows = 0
    total_windows = 0
    under = over = 0
    mismatch_cells = 0
    delivery_ok = True
    for cell in l0_cells:
        for run in cell["runs"]:
            margins = sampler_margin_s(run["window_sent"])
            lateness = run["tick_lateness_s"][:-1]
            late_windows += int(np.count_nonzero(lateness > margins))
            total_windows += int(margins.size)
            expected_cumulative = np.cumsum(run["window_sent"], axis=1)
            difference = run["snapshot_sent"] - expected_cumulative
            under += int(np.count_nonzero(difference < 0))
            over += int(np.count_nonzero(difference > 0))
            mismatch_cells += int(np.count_nonzero(difference))
            delivery_ok = delivery_ok and bool(np.array_equal(
                run["final_sent"], run["final_received"]
            ))
    sampler_late_fraction = late_windows / total_windows
    mismatch_fraction = mismatch_cells / (
        len(l0_cells) * replicate_count * len(LINKS) * window_count
    )
    diagnose(
        "EMIT-4b",
        sampler_late_fraction,
        "sampler punctuality before the next first-packet deadline",
        legacy_gate=GATE_SAMPLER_LATE_FRACTION,
        legacy_verdict=(
            "PASS"
            if sampler_late_fraction <= GATE_SAMPLER_LATE_FRACTION
            else "FAIL"
        ),
        late_windows=late_windows,
        windows=total_windows,
        margin_rule="0.5 * dt / max_link_packets(next window)",
    )
    diagnose(
        "EMIT-4c",
        mismatch_fraction,
        "L2 ledger alignment mismatch fraction, split by sign",
        legacy_gate=GATE_ALIGNMENT_MISMATCH,
        legacy_verdict=(
            "PASS"
            if mismatch_fraction <= GATE_ALIGNMENT_MISMATCH and delivery_ok
            else "FAIL"
        ),
        undershoot=under,
        overshoot=over,
        final_udp_delivery_exact=delivery_ok,
        tolerance_rule="GATE_OVERRUN_FRACTION + GATE_SAMPLER_LATE_FRACTION",
    )

    emit3_null = (
        simulate_emit3_null() if legacy_emit3_null is None else legacy_emit3_null
    )
    overall = all(row["verdict"] == "PASS" for row in checks)
    return {
        "schema": "dt4n.phase_g.g3_emitter_dryrun.v4",
        "status": "REALTIME_LOOPBACK_NO_MININET",
        "git_hash": git_hash(),
        "prereg": "docs/phase-G/51-amendment-G-A016.md",
        "provenance": provenance,
        "cpu_preflight": cpu_detail,
        "design": {
            "seed": SEED, "dt_s": DT_S,
            "duration_s": window_count * DT_S,
            "replicates": replicate_count, "payload_bytes": PAYLOAD_BYTES,
            "windows": window_count,
            "wire_bytes": WIRE_BYTES, "spin_threshold_s": SPIN_THRESHOLD_S,
            "cells": [{key: value for key, value in cell.items() if key != "runs"}
                      for cell in cells],
        },
        "checks": checks,
        "diagnostics": diagnostics,
        "emitter_core_ladder": {
            "status": "REPORTED_DOSE_RESPONSE",
            "rows": timing_rows,
            "gate_applies_only_to": "L0",
        },
        "emit3_null": emit3_null,
        "emit3_prime_null": emit3_prime_null,
        "overall": "PASS" if overall else "FAIL",
        "mininet_authorized": bool(overall),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--execute", action="store_true",
                        help="run the approximately 64-minute real-time ladder")
    parser.add_argument(
        "--a016",
        action="store_true",
        help="use the preregistered reduced L0-only 8x30-second design",
    )
    parser.add_argument(
        "--host-jitter-artifact",
        type=Path,
        default=DEFAULT_HOST_JITTER_ARTIFACT,
        help="after-quiesce no-socket probe used by the A016 admission gate",
    )
    args = parser.parse_args()
    try:
        ladder_maps = build_ladder_cpu_maps()
    except RuntimeError as exc:
        raise SystemExit(f"REFUSED: {exc}") from exc
    levels = ("L0",) if args.a016 else ("L0", "L1", "L2")
    replicates = A016_REPLICATES if args.a016 else REPLICATES
    n_windows = A016_N_WINDOWS if args.a016 else N_WINDOWS
    prereg_tag = A016_PREREG_TAG if args.a016 else PREREG_TAG
    cpu_detail = {
        level: cpu_preflight(ladder_maps[level]) for level in levels
    }
    provenance = remote_provenance(prereg_tag)
    jitter_admission = (
        host_jitter_admission(args.host_jitter_artifact) if args.a016 else None
    )
    preflight_artifact = {
        "schema": "dt4n.phase_g.g3_a016_preflight.v1",
        "status": "PREFLIGHT_ONLY",
        "cpu_preflight": cpu_detail,
        "cpu_maps": {key: list(ladder_maps[key]) for key in levels},
        "design": {
            "a016": args.a016,
            "replicates": replicates,
            "windows": n_windows,
            "duration_s": n_windows * DT_S,
            "git_tag_to_create": prereg_tag,
        },
        "provenance": provenance,
        "host_jitter_admission": jitter_admission,
        "environment_pass": all(
            row["pass"] for row in cpu_detail.values()
        ) and (not args.a016 or bool(jitter_admission["pass"])),
        "mininet_authorized": False,
    }
    print(json.dumps(preflight_artifact, indent=2))
    if not args.execute:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(preflight_artifact, indent=2) + "\n", encoding="utf-8"
        )
        print("PREFLIGHT ONLY: pass --execute after prereg tag is on origin")
        print(f"artifact = {output}")
        return
    if not all(row["pass"] for row in cpu_detail.values()):
        raise SystemExit("REFUSED: ladder CPU roles are unavailable or not isolated")
    if not provenance["pass"]:
        raise SystemExit("REFUSED: origin main/prereg tag do not match local HEAD")
    if args.a016 and not preflight_artifact["environment_pass"]:
        raise SystemExit(
            "REFUSED: G-A016 requires a valid after-quiesce p_stall <= 0.02"
        )

    rng = np.random.default_rng(SEED)
    cells = []
    for level in levels:
        cpu_map = ladder_maps[level]
        emitter_cpus, sampler_cpu, sink_cpu = cpu_map[:8], cpu_map[8], cpu_map[9]
        designs = CELLS if level == "L0" else (CELLS[1],)
        for design in designs:
            a0 = a0_from_sigma_at("uA", design["sigma_ref"])
            cell = {**design, "level": level, "a0": a0, "runs": []}
            for replicate in range(replicates):
                trace = physical_trace(
                    0.0, design["tau_s"], design["tau_s"], n_windows, rng, a0=a0
                )
                print(
                    f"running {level}/{design['name']} "
                    f"replicate {replicate + 1}/{replicates}"
                )
                cell["runs"].append(run_replicate(
                    trace["rho_target"], emitter_cpus, sampler_cpu, sink_cpu,
                    dt_s=DT_S,
                ))
            cells.append(cell)
    artifact = analyze(cells, cpu_detail, provenance)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    for row in artifact["checks"]:
        print(f"{row['id']}: {row['value']} {row['verdict']} {row['description']}")
    print(f"G.3 EMITTER DRY-RUN: {artifact['overall']}")
    raise SystemExit(0 if artifact["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()

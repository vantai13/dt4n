#!/usr/bin/env python3
"""Real-time, no-Mininet dry-run for the Phase-G packet emitter."""
from __future__ import annotations

import argparse
import gc
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
    emit_window,
    pin_current_process,
)
from mininet.tick_sampler import sample_at
from tools.g1_quant_model import WIRE_BYTES_DEFAULT
from tools.g2_topology import CAP_BPS, LINKS, a0_from_sigma_at
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
PREREG_TAG = "phase-G-g3-emitter-reduction-prereg"
CELLS = (
    {"name": "anchor", "sigma_ref": 0.030348837209302317, "tau_s": 3.0},
    {"name": "stress", "sigma_ref": 0.020232558139534878, "tau_s": 30.0},
)

GATE_OVERRUN_FRACTION = 0.001
GATE_QUANT_SIGN = -0.05
GATE_QUANT_PREDICTION = 0.05
GATE_TIMING_CORRELATION = 0.10
GATE_SNAPSHOT_P99_S = 0.001
EMIT3_NULL_TRIALS = 3000
EMIT3_NULL_SEED = 20260909


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
    return {
        "allowed_cpus": sorted(allowed),
        "requested_cpus": list(cpu_map),
        "emitter_core_count": len(set(emitter_cpus)),
        "emitters_per_core": len(emitter_cpus) / len(set(emitter_cpus)),
        "sampler_cpu": sampler_cpu,
        "sink_cpu": sink_cpu,
        "role_isolation": role_isolation,
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


def remote_provenance() -> dict[str, object]:
    head = git_hash()
    result = subprocess.run(
        [
            "git", "ls-remote", "origin", "refs/heads/main",
            f"refs/tags/{PREREG_TAG}^{{}}",
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
    remote_tag = refs.get(f"refs/tags/{PREREG_TAG}^{{}}")
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
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            for window_index, rate_pps in enumerate(rates_pps):
                row = emit_window(
                    window_index,
                    epoch_value.value,
                    DT_S,
                    float(rate_pps),
                    sock,
                    payload,
                    shared_sent_cumulative,
                    link_index,
                    state,
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
    ready_queue,
    error_queue,
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
                epoch_value.value + (window_index + 1) * DT_S,
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
) -> dict[str, object]:
    """Run one 60 s eight-emitter UDP-loopback replicate."""
    if target.shape != (len(LINKS), N_WINDOWS):
        raise ValueError(f"target must have shape {(len(LINKS), N_WINDOWS)}")
    context = mp.get_context("fork")
    sent_cumulative = atomic_int64_array(len(LINKS))
    receiver_counts = atomic_int64_array(len(LINKS))
    window_sent = atomic_int64_array(len(LINKS) * N_WINDOWS)
    window_lateness_ns = atomic_int64_array(len(LINKS) * N_WINDOWS)
    snapshot_sent = atomic_int64_array(len(LINKS) * N_WINDOWS)
    snapshot_measured = atomic_int64_array(len(LINKS) * N_WINDOWS)
    snapshot_spans_ns = atomic_int64_array(N_WINDOWS)
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
    target_packets = target * CAP_BPS[:, None] * DT_S / (WIRE_BYTES * 8.0)
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
              snapshot_spans_ns, ready_queue, error_queue),
        name="g3-sampler",
    ))
    for link_index, cpu in enumerate(emitter_cpus):
        processes.append(context.Process(
            target=_emitter_worker,
            args=(link_index, cpu, rates_pps[link_index].tolist(), destination,
                  epoch_value, start_event, sent_cumulative, window_sent,
                  window_lateness_ns, overrun_counts, overrun_max_ns,
                  ready_queue, error_queue),
            name=f"g3-emitter-{LINKS[link_index]}",
        ))
    for process in processes:
        process.start()
    try:
        ready_roles = _wait_ready(ready_queue, processes)
        epoch_value.value = time.perf_counter() + START_DELAY_S
        start_event.set()
        deadline = DURATION_S + START_DELAY_S + JOIN_SLACK_S
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
        return np.fromiter(values, dtype=np.int64).reshape(len(LINKS), N_WINDOWS)

    return {
        "ready_roles": ready_roles,
        "target_packets": target_packets,
        "window_sent": matrix(window_sent),
        "window_lateness_s": matrix(window_lateness_ns) / 1e9,
        "snapshot_sent": matrix(snapshot_sent),
        "snapshot_measured": matrix(snapshot_measured),
        "snapshot_spans_s": np.fromiter(snapshot_spans_ns, dtype=np.int64) / 1e9,
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


def analyze(cells: list[dict[str, object]], cpu_detail, provenance) -> dict[str, object]:
    checks = []

    def record(check_id, value, gate, passed, description, **extra):
        checks.append({
            "id": check_id, "value": value, "gate": gate,
            "verdict": "PASS" if passed else "FAIL",
            "description": description, **extra,
        })

    l0_cells = [cell for cell in cells if cell["level"] == "L0"]
    stress_cells = [cell for cell in cells if cell["name"] == "stress"]
    if len(l0_cells) != len(CELLS) or len(stress_cells) != 3:
        raise ValueError("ladder must contain L0 anchor/stress and L1/L2 stress")

    total_overruns = sum(
        int(np.sum(run["overrun_counts"]))
        for cell in l0_cells for run in cell["runs"]
    )
    total_windows = len(l0_cells) * REPLICATES * len(LINKS) * N_WINDOWS
    overrun_fraction = total_overruns / total_windows
    overrun_rows = []
    for cell in l0_cells:
        for index, link in enumerate(LINKS):
            count = sum(int(run["overrun_counts"][index]) for run in cell["runs"])
            windows = len(cell["runs"]) * N_WINDOWS
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
    record("EMIT-2", max(row["prediction_abs_error"] for row in quant_rows),
           GATE_QUANT_PREDICTION, emit2_pass,
           "independent-round sign and packet-step prediction", rows=quant_rows,
           reduction="median of 16 replicates")

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
    record("EMIT-3", l0_timing["max_abs_offdiag"], GATE_TIMING_CORRELATION,
           l0_timing["max_abs_offdiag"] <= GATE_TIMING_CORRELATION,
           "deadline lateness has no shared CPU-noise regression",
           l0_row=l0_timing,
           reduction="mean of 16 within-replicate 8x8 matrices, then max 28 pairs")

    spans = np.concatenate([
        run["snapshot_spans_s"] for cell in l0_cells for run in cell["runs"]
    ])
    snap_p99 = float(np.quantile(spans, 0.99))
    alignment_ok = True
    delivery_ok = True
    for cell in l0_cells:
        for run in cell["runs"]:
            expected_cumulative = np.cumsum(run["window_sent"], axis=1)
            alignment_ok = alignment_ok and bool(np.array_equal(
                expected_cumulative, run["snapshot_sent"]
            ))
            alignment_ok = alignment_ok and bool(np.array_equal(
                expected_cumulative[:, -1], run["final_sent"]
            ))
            delivery_ok = delivery_ok and bool(np.array_equal(
                run["final_sent"], run["final_received"]
            ))
    record("EMIT-4", snap_p99, GATE_SNAPSHOT_P99_S,
           snap_p99 <= GATE_SNAPSHOT_P99_S and alignment_ok and delivery_ok,
           "shared-tick snapshot span and exact L2 ledger alignment",
           alignment_exact=alignment_ok, final_udp_delivery_exact=delivery_ok)

    emit3_null = simulate_emit3_null()
    overall = all(row["verdict"] == "PASS" for row in checks)
    return {
        "schema": "dt4n.phase_g.g3_emitter_dryrun.v3",
        "status": "REALTIME_LOOPBACK_NO_MININET",
        "git_hash": git_hash(),
        "prereg": "docs/phase-G/41-amendment-g3-emitter-reduction.md",
        "provenance": provenance,
        "cpu_preflight": cpu_detail,
        "design": {
            "seed": SEED, "dt_s": DT_S, "duration_s": DURATION_S,
            "replicates": REPLICATES, "payload_bytes": PAYLOAD_BYTES,
            "wire_bytes": WIRE_BYTES, "spin_threshold_s": SPIN_THRESHOLD_S,
            "cells": [{key: value for key, value in cell.items() if key != "runs"}
                      for cell in cells],
        },
        "checks": checks,
        "emitter_core_ladder": {
            "status": "REPORTED_DOSE_RESPONSE",
            "rows": timing_rows,
            "gate_applies_only_to": "L0",
        },
        "emit3_null": emit3_null,
        "overall": "PASS" if overall else "FAIL",
        "mininet_authorized": bool(overall),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--execute", action="store_true",
                        help="run the approximately 64-minute real-time ladder")
    args = parser.parse_args()
    try:
        ladder_maps = build_ladder_cpu_maps()
    except RuntimeError as exc:
        raise SystemExit(f"REFUSED: {exc}") from exc
    cpu_detail = {
        level: cpu_preflight(cpu_map) for level, cpu_map in ladder_maps.items()
    }
    provenance = remote_provenance()
    print(json.dumps({
        "cpu_preflight": cpu_detail,
        "cpu_maps": {key: list(value) for key, value in ladder_maps.items()},
        "provenance": provenance,
    }, indent=2))
    if not args.execute:
        print("PREFLIGHT ONLY: pass --execute after prereg tag is on origin")
        return
    if not all(row["pass"] for row in cpu_detail.values()):
        raise SystemExit("REFUSED: ladder CPU roles are unavailable or not isolated")
    if not provenance["pass"]:
        raise SystemExit("REFUSED: origin main/prereg tag do not match local HEAD")

    rng = np.random.default_rng(SEED)
    cells = []
    for level in ("L0", "L1", "L2"):
        cpu_map = ladder_maps[level]
        emitter_cpus, sampler_cpu, sink_cpu = cpu_map[:8], cpu_map[8], cpu_map[9]
        designs = CELLS if level == "L0" else (CELLS[1],)
        for design in designs:
            a0 = a0_from_sigma_at("uA", design["sigma_ref"])
            cell = {**design, "level": level, "a0": a0, "runs": []}
            for replicate in range(REPLICATES):
                trace = physical_trace(
                    0.0, design["tau_s"], design["tau_s"], N_WINDOWS, rng, a0=a0
                )
                print(
                    f"running {level}/{design['name']} "
                    f"replicate {replicate + 1}/{REPLICATES}"
                )
                cell["runs"].append(run_replicate(
                    trace["rho_target"], emitter_cpus, sampler_cpu, sink_cpu
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

#!/usr/bin/env python3
"""Measure shared-stall probability with emitter pacing and no socket.

``floor`` runs one pacing process and measures the host's idle-noise floor.
It is the instrument for before/after intervention comparisons.

``ladder`` runs the signed L0 population: eight emitter-cadence processes,
one sampler-labelled process, and one sink-labelled process on the same CPUs
used by the reduced benchmark. It removes sockets while retaining the CPU
population and affinity pressure. The sampler and sink labels use the
fastest-link cadence only to resolve stalls; this is not a simulation of
their production duty cycles. Ladder mode is the admission instrument.
"""
from __future__ import annotations

import argparse
import gc
import json
import multiprocessing as mp
import os
import queue
import time
from pathlib import Path

import numpy as np

from mininet.modulated_emitter import (
    SPIN_THRESHOLD_S,
    deadline_phase_fraction,
    pin_current_process,
    sleep_until,
)
from tools.g1_quant_model import WIRE_BYTES_DEFAULT
from tools.g2_topology import CAP_BPS, LINKS
from tools.g3_emitter_dryrun import (
    DT_S,
    build_ladder_cpu_maps,
    git_hash,
    sha256,
)


RHO_ANCHOR = 0.857
STALL_THRESHOLD_S = 1e-3
WARMUP_S = 0.5
DEFAULT_DURATION_S = 300.0
SCHEMA = "dt4n.phase_g.host_jitter_probe.v2"
BOOT_ID_PATH = "/proc/sys/kernel/random/boot_id"


def read_psi_totals(path: str = "/proc/pressure/cpu") -> dict[str, int]:
    """Return cumulative PSI stall microseconds for each available class.

    Only cumulative totals are used. Across the 2026-09-04 quiesce, the
    measured stall rate fell 26-fold while PSI ``some`` rose by 15 percent;
    PSI is therefore context, never an admission input.
    """
    totals: dict[str, int] = {}
    try:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                fields = line.split()
                if not fields:
                    continue
                values = dict(
                    field.split("=", 1) for field in fields[1:] if "=" in field
                )
                if "total" in values:
                    totals[fields[0]] = int(values["total"])
    except (OSError, ValueError):
        return {}
    return totals


def read_steal_ticks(path: str = "/proc/stat") -> int | None:
    """Return the cumulative guest steal counter from the aggregate CPU row."""
    try:
        with open(path, encoding="utf-8") as handle:
            fields = handle.readline().split()
        if fields and fields[0] == "cpu" and len(fields) > 8:
            return int(fields[8])
    except (OSError, ValueError):
        pass
    return None


def read_boot_id(path: str = BOOT_ID_PATH) -> str | None:
    """Return the kernel boot identifier, which changes on every reboot."""
    try:
        return Path(path).read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def _psi_delta_rate(
    before: dict[str, int], after: dict[str, int], elapsed_s: float
) -> dict[str, float]:
    if elapsed_s <= 0.0:
        raise ValueError("elapsed_s must be positive")
    return {
        key: (after[key] - before[key]) / (elapsed_s * 1e6)
        for key in sorted(before.keys() & after.keys())
        if after[key] >= before[key]
    }


def wilson_upper_95(successes: int, trials: int) -> float:
    """Return the 95% Wilson upper endpoint for a binomial rate."""
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("invalid binomial counts")
    z = 1.959963985
    p = successes / trials
    denominator = 1.0 + z * z / trials
    center = p + z * z / (2.0 * trials)
    radius = z * np.sqrt(
        p * (1.0 - p) / trials + z * z / (4.0 * trials**2)
    )
    return float((center + radius) / denominator)


# Backward-compatible name for v1 notebooks/tests.
_wilson_upper_95 = wilson_upper_95


def link_rates_pps() -> np.ndarray:
    """Return the signed anchor packet cadence for each link."""
    return (
        RHO_ANCHOR
        * np.asarray(CAP_BPS, dtype=float)
        / (WIRE_BYTES_DEFAULT * 8.0)
    )


def pacing_lateness(
    duration_s: float,
    rate_pps: float,
    epoch_s: float,
    *,
    phase_fraction: float = 0.0,
) -> np.ndarray:
    """Run the emitter absolute-deadline loop, omitting only socket sends."""
    if not np.isfinite(duration_s) or duration_s <= 0.0:
        raise ValueError("duration_s must be finite and positive")
    if not np.isfinite(rate_pps) or rate_pps <= 0.0:
        raise ValueError("rate_pps must be finite and positive")
    if not 0.0 <= phase_fraction < 0.5:
        raise ValueError("phase_fraction must be in [0, 0.5)")
    packets_per_window = int(round(rate_pps * DT_S))
    windows = int(duration_s / DT_S)
    if packets_per_window < 1 or windows < 2:
        raise ValueError("probe needs at least one packet and two windows")

    lateness = np.empty((windows, packets_per_window), dtype=float)
    gap = DT_S / packets_per_window
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        for window in range(windows):
            t_start = epoch_s + window * DT_S
            for packet in range(packets_per_window):
                deadline = t_start + (packet + 0.5 + phase_fraction) * gap
                sleep_until(deadline, spin_threshold_s=SPIN_THRESHOLD_S)
                lateness[window, packet] = max(
                    0.0, time.perf_counter() - deadline
                )
    finally:
        if gc_was_enabled:
            gc.enable()
    return lateness


def summarise(
    lateness: np.ndarray,
    role: str,
    cpu: int,
    rate_pps: float,
) -> dict[str, object]:
    """Reduce one role's packet lateness to auditable window statistics."""
    window_max = lateness.max(axis=1)
    windows = int(window_max.size)
    stall_windows = int(np.count_nonzero(window_max >= STALL_THRESHOLD_S))
    return {
        "role": role,
        "cpu": cpu,
        "rate_pps": float(rate_pps),
        "packets_per_window": int(lateness.shape[1]),
        "windows": windows,
        "lateness_median_s": float(np.median(lateness)),
        "lateness_p99_s": float(np.quantile(lateness, 0.99)),
        "lateness_p999_s": float(np.quantile(lateness, 0.999)),
        "lateness_max_s": float(lateness.max()),
        "window_max_median_s": float(np.median(window_max)),
        "window_max_p99_s": float(np.quantile(window_max, 0.99)),
        "stall_windows": stall_windows,
        "p_stall_1ms": stall_windows / windows,
        "p_stall_1ms_wilson_upper_95": wilson_upper_95(
            stall_windows, windows
        ),
        # Retained only in memory for the single-replicate A1 diagnostic.
        "window_max_s": window_max.tolist(),
    }


def _worker(
    role: str,
    cpu: int,
    rate_pps: float,
    phase_fraction: float,
    duration_s: float,
    epoch_value,
    start_event,
    result_queue,
    error_queue,
) -> None:
    try:
        pin_current_process(cpu)
        result_queue.put(("ready", role, None))
        start_event.wait()
        lateness = pacing_lateness(
            duration_s,
            rate_pps,
            epoch_value.value,
            phase_fraction=phase_fraction,
        )
        result_queue.put(
            ("result", role, summarise(lateness, role, cpu, rate_pps))
        )
    except BaseException as exc:  # noqa: BLE001 - child error crosses process
        error_queue.put((role, repr(exc)))
        raise


def _emit3_timing(rows: list[dict[str, object]]) -> dict[str, object]:
    """Report doc-46 branch A1 timing correlation for one replicate.

    This is diagnostic only. The doc-41 null averages sixteen replicate
    matrices before maximising, so its threshold does not apply here.
    """
    emitters = [
        row for row in rows if str(row["role"]).startswith("emitter-")
    ]
    if len(emitters) != len(LINKS):
        raise ValueError("ladder mode must produce one row per link")
    series = np.asarray(
        [row["window_max_s"] for row in emitters], dtype=float
    )
    if np.any(np.std(series, axis=1) <= 0.0):
        return {
            "status": "DEGENERATE_NO_VARIATION",
            "replicates": 1,
            "max_abs_offdiag": None,
            "median_abs_offdiag": None,
            "note": "single replicate; the doc-41 null does not apply",
        }
    matrix = np.corrcoef(series)
    upper = matrix[np.triu_indices(len(LINKS), 1)]
    return {
        "status": "REPORTED_NOT_GATING",
        "replicates": 1,
        "max_abs_offdiag": float(np.max(np.abs(upper))),
        "median_abs_offdiag": float(np.median(np.abs(upper))),
        "note": "single replicate; the doc-41 null does not apply",
    }


def probe(
    mode: str,
    duration_s: float,
    *,
    floor_cpu: int = 0,
) -> dict[str, object]:
    """Run ``floor`` or the full signed L0 no-socket role population."""
    if mode not in {"floor", "ladder"}:
        raise ValueError("mode must be 'floor' or 'ladder'")
    if not np.isfinite(duration_s) or duration_s <= 0.0:
        raise ValueError("duration_s must be finite and positive")

    rates = link_rates_pps()
    fastest = float(rates.max())
    ladder = build_ladder_cpu_maps()["L0"]
    if mode == "floor":
        roles = [(f"floor-cpu{floor_cpu}", floor_cpu, fastest, 0.0)]
    else:
        roles = [
            (
                f"emitter-{LINKS[index]}",
                ladder[index],
                float(rates[index]),
                deadline_phase_fraction(index, len(LINKS)),
            )
            for index in range(len(LINKS))
        ]
        roles.extend((
            ("sampler", ladder[8], fastest, 0.0),
            ("sink", ladder[9], fastest, 0.0),
        ))

    context = mp.get_context("fork")
    epoch_value = context.Value("d", 0.0, lock=False)
    start_event = context.Event()
    result_queue = context.Queue()
    error_queue = context.Queue()
    processes = [
        context.Process(
            target=_worker,
            args=(
                role, cpu, rate, phase, duration_s, epoch_value,
                start_event, result_queue, error_queue,
            ),
            name=f"jitter-{role}",
        )
        for role, cpu, rate, phase in roles
    ]

    psi_before = read_psi_totals()
    steal_before = read_steal_ticks()
    rows: dict[str, dict[str, object]] = {}
    try:
        for process in processes:
            process.start()
        ready: set[str] = set()
        ready_deadline = time.monotonic() + 30.0
        while len(ready) < len(processes):
            remaining = ready_deadline - time.monotonic()
            if remaining <= 0.0:
                raise RuntimeError(
                    f"worker readiness timeout; ready={sorted(ready)}"
                )
            try:
                kind, role, payload = result_queue.get(
                    timeout=min(1.0, remaining)
                )
            except queue.Empty:
                failed = [
                    process.name for process in processes
                    if process.exitcode not in (None, 0)
                ]
                if failed:
                    raise RuntimeError(
                        f"workers failed before readiness: {failed}"
                    )
                continue
            if kind == "ready":
                ready.add(role)
            elif kind == "result":
                rows[role] = payload

        epoch_value.value = time.perf_counter() + WARMUP_S
        start_event.set()
        result_deadline = time.monotonic() + duration_s + WARMUP_S + 30.0
        while len(rows) < len(processes):
            remaining = result_deadline - time.monotonic()
            if remaining <= 0.0:
                raise RuntimeError(
                    f"worker result timeout; results={sorted(rows)}"
                )
            try:
                kind, role, payload = result_queue.get(
                    timeout=min(5.0, remaining)
                )
            except queue.Empty:
                failed = [
                    process.name for process in processes
                    if process.exitcode not in (None, 0)
                ]
                if failed:
                    raise RuntimeError(
                        f"workers failed before results: {failed}"
                    )
                continue
            if kind == "result":
                rows[role] = payload
        observed_elapsed_s = time.perf_counter() - epoch_value.value
        for process in processes:
            process.join(timeout=10.0)
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get_nowait())
        failures = [
            process.name for process in processes
            if process.is_alive() or process.exitcode != 0
        ]
        if errors or failures:
            raise RuntimeError(
                f"worker failures={failures} errors={errors}"
            )
    finally:
        start_event.set()
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(timeout=2.0)
        result_queue.close()
        error_queue.close()

    psi_after = read_psi_totals()
    steal_after = read_steal_ticks()
    ordered = [rows[role] for role, _cpu, _rate, _phase in roles]
    binding = max(
        ordered,
        key=lambda row: float(row["p_stall_1ms_wilson_upper_95"]),
    )
    result: dict[str, object] = {
        "mode": mode,
        "roles": [
            {key: value for key, value in row.items() if key != "window_max_s"}
            for row in ordered
        ],
        "binding_role": binding["role"],
        "binding_cpu": binding["cpu"],
        "p_stall_1ms": binding["p_stall_1ms"],
        "p_stall_1ms_wilson_upper_95": binding[
            "p_stall_1ms_wilson_upper_95"
        ],
        "stall_threshold_s": STALL_THRESHOLD_S,
        "windows": binding["windows"],
        "scheduled_duration_s": float(binding["windows"]) * DT_S,
        "observed_elapsed_s": observed_elapsed_s,
        "psi_total_us_before": psi_before,
        "psi_total_us_after": psi_after,
        "psi_delta_rate": _psi_delta_rate(
            psi_before, psi_after, observed_elapsed_s
        ),
        "steal_ticks_before": steal_before,
        "steal_ticks_after": steal_after,
        "steal_ticks_delta": (
            None if steal_before is None or steal_after is None
            else steal_after - steal_before
        ),
    }
    if mode == "ladder":
        result["emit3_timing_no_socket"] = _emit3_timing(ordered)
    return result


def measure_artifact(
    mode: str,
    duration_s: float,
    scenario: str,
    *,
    floor_cpu: int = 0,
) -> dict[str, object]:
    """Measure and wrap a v2 artifact with time, boot, and tool identity."""
    if scenario not in {"before_quiesce", "after_quiesce", "live_admission"}:
        raise ValueError("invalid host jitter scenario")
    started = time.perf_counter()
    loadavg_at_start = float(os.getloadavg()[0])
    result = probe(mode, duration_s, floor_cpu=floor_cpu)
    return {
        "schema": SCHEMA,
        "status": "NO_SOCKET_HOST_MEASUREMENT",
        "scenario": scenario,
        "git_hash": git_hash(),
        "tool_path": "tools/host_jitter_probe.py",
        "tool_sha256": sha256(Path(__file__)),
        "measured_at_unix": time.time(),
        "boot_id": read_boot_id(),
        "loadavg_at_start": loadavg_at_start,
        **result,
        "runtime_s": time.perf_counter() - started,
    }


def write_artifact(path: Path, artifact: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--mode", choices=("floor", "ladder"), required=True)
    parser.add_argument(
        "--cpu", type=int, default=0,
        help="CPU probed in floor mode; ignored in ladder mode",
    )
    parser.add_argument("--duration-s", type=float, default=DEFAULT_DURATION_S)
    parser.add_argument(
        "--label",
        choices=("before_quiesce", "after_quiesce", "live_admission"),
        required=True,
    )
    args = parser.parse_args()

    artifact = measure_artifact(
        args.mode, args.duration_s, args.label, floor_cpu=args.cpu
    )
    write_artifact(args.out, artifact)
    print(
        "mode={mode} binding={binding_role}(cpu{binding_cpu}) "
        "p_stall={p_stall_1ms:.6f} "
        "wilson95={p_stall_1ms_wilson_upper_95:.6f}".format(**artifact)
    )
    for row in artifact["roles"]:
        print(
            "  {role:14s} cpu{cpu} stalls={stall_windows:4d}/{windows} "
            "p99={window_max_p99_s:.6f}s".format(**row)
        )
    if "emit3_timing_no_socket" in artifact:
        print(
            "  EMIT-3 timing (A1, no socket, 1 replicate) =",
            artifact["emit3_timing_no_socket"]["max_abs_offdiag"],
        )
    print("artifact =", args.out)


if __name__ == "__main__":
    main()

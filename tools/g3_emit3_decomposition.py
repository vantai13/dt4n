#!/usr/bin/env python3
"""Diagnostic decomposition of the EMIT-3 cross-link timing correlation.

STATUS: DIAGNOSTIC_NOT_ADJUDICATED.  This tool adjudicates nothing, renews no
certificate, and authorizes no downstream step.  It exists to separate the
candidate causes of the ~0.45 cross-link background observed in
`results/SMOKE/phase-G/g3_emitter_dryrun.json` before any 64-minute rerun is
attempted.

All four arms drive the SAME signed ``emit_window`` from
``mininet/modulated_emitter.py`` and build their per-window rates through the
SAME ``physical_trace`` path and rate conversion the real runner uses, on the
stress cell whose L0 row produced the observed 0.9179.  The arms differ only
in arguments:

    A0 baseline      real socket, one shared sink, aligned window epochs
    A1 no_send       null socket, no sink at all, aligned window epochs
    A2 split_sink    real socket, eight private sinks, aligned window epochs
    A3 staggered     real socket, one shared sink, epoch shifted by i*dt/8

Every arm sees the identical rate series for a given replicate index, so the
four arms differ only in the mechanism under test.  No pacing code and no rate
code is reimplemented here: a forked loop would measure a different emitter
than the one under test.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import queue
import socket
import subprocess
import time
from pathlib import Path

import numpy as np

from mininet.modulated_emitter import (
    EmitterState,
    atomic_int64_array,
    emit_window,
    pin_current_process,
)
from tools.g2_topology import CAP_BPS, LINKS, a0_from_sigma_at
from tools.g3_dryrun import DT_S, physical_trace
from tools.g3_emitter_dryrun import (
    CELLS,
    PAYLOAD_BYTES,
    WIRE_BYTES,
    build_ladder_cpu_maps,
    mean_correlation_then_max,
    simulate_emit3_null,
)

# --------------------------------------------------------------- diagnostic
DIAG_DURATION_S = 20.0
DIAG_WINDOWS = int(DIAG_DURATION_S / DT_S)
DIAG_REPLICATES = 8
DIAG_SEED = 20260903
DIAG_NULL_TRIALS = 2000
DIAG_NULL_SEED = 20260903
START_DELAY_S = 1.0
JOIN_SLACK_S = 10.0
SPIKE_QUANTILE = 0.90
SPIKE_MIN_LINKS = 6
DIAG_CELL = CELLS[1]          # stress: the cell whose L0 row produced 0.9179

ARMS = (
    {"name": "A0_baseline", "send": True, "split_sink": False, "stagger": False,
     "kills": "none; reproduces the observed background"},
    {"name": "A1_no_send", "send": False, "split_sink": False, "stagger": False,
     "kills": "network path (conclusive only if it stays high)"},
    {"name": "A2_split_sink", "send": True, "split_sink": True, "stagger": False,
     "kills": "shared sink process contention"},
    {"name": "A3_staggered", "send": True, "split_sink": False, "stagger": True,
     "kills": "synchronised window boundaries"},
)

LIMITS = [
    "A1 removes the send syscall cost as well as the network path; a drop in "
    "A1 is confounded and is NOT evidence that the network path is the cause. "
    "Only a HIGH A1 is conclusive, and it rules the network path out.",
    "A3 shifts each emitter onto its own window grid, which mechanically "
    "decorrelates the measurement even if the underlying stalls are shared; "
    "windows overlap 87.5 percent, so the mechanical component is partial "
    "but not zero.",
    "A2 separates sink processes but places eight of them on the same two "
    "sink CPUs, so it separates process contention while leaving CPU count "
    "and the shared loopback softirq path unchanged.",
    "No sampler process runs in any arm. The 64-minute run had one pinned to "
    "the first sink CPU waking at every window boundary; a synchronised "
    "wake-up on that CPU is therefore a candidate cause this experiment does "
    "NOT test.",
    "co_spike_fraction thresholds each link at its OWN empirical 90th "
    "percentile, so a shared stall occupying more than about a tenth of the "
    "windows raises the threshold it must cross and hides itself. Values near "
    "or above 0.10 must be read as saturation, not as absence of coupling.",
    "Twenty-second replicates give 100 windows each; the null is recalibrated "
    "for this shape and must not be compared against the 300-window EMIT-3 "
    "null of doc 41. A0 is not a bit-comparable reproduction of the EMIT-3 "
    "row: same cell, rate path and reduction, but shorter windows and no "
    "sampler.",
]


class _NullSocket:
    """Send-shaped no-op so arm A1 can reuse the signed emit_window unchanged."""

    def send(self, payload: bytes) -> int:
        return len(payload)


def git_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() or "unknown"


def _ready(ready_queue, role: str) -> None:
    ready_queue.put(("ready", role, 0))


def _failed(error_queue, role: str) -> None:
    error_queue.put(role)


def replicate_rates(index: int) -> np.ndarray:
    """Per-window pps for one replicate, via the runner's own rate path."""
    a0 = a0_from_sigma_at("uA", DIAG_CELL["sigma_ref"])
    rng = np.random.default_rng(DIAG_SEED + index)
    trace = physical_trace(
        0.0, DIAG_CELL["tau_s"], DIAG_CELL["tau_s"], DIAG_WINDOWS, rng, a0=a0
    )
    return trace["rho_target"] * CAP_BPS[:, None] / (WIRE_BYTES * 8.0)


# ------------------------------------------------------------------ workers
def _diag_sink(bound_socket, cpu, stop_event, start_event, ready_queue,
               error_queue) -> None:
    role = f"sink-{cpu}"
    try:
        pin_current_process(cpu)
        bound_socket.settimeout(0.05)
        _ready(ready_queue, role)
        start_event.wait()
        quiet = 0
        while quiet < 3:
            try:
                if not bound_socket.recvfrom(PAYLOAD_BYTES + 64)[0]:
                    continue
                quiet = 0
            except socket.timeout:
                if stop_event.is_set():
                    quiet += 1
        bound_socket.close()
    except BaseException:
        _failed(error_queue, role)
        raise


def _diag_emitter(link_index, cpu, rates_pps, destination, epoch_value,
                  epoch_offset_s, start_event, shared_cumulative,
                  window_lateness_ns, overrun_counts, ready_queue,
                  error_queue) -> None:
    role = f"emitter-{link_index}"
    sock = None
    try:
        pin_current_process(cpu)
        if destination is None:
            sock = _NullSocket()
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(destination)
        payload = bytes([link_index]) + bytes(PAYLOAD_BYTES - 1)
        _ready(ready_queue, role)
        start_event.wait()
        state = EmitterState()
        epoch = epoch_value.value + epoch_offset_s
        for window_index, rate_pps in enumerate(rates_pps):
            row = emit_window(
                window_index, epoch, DT_S, float(rate_pps), sock, payload,
                shared_cumulative, link_index, state,
            )
            window_lateness_ns[link_index * len(rates_pps) + window_index] = int(
                round(row.max_deadline_lateness_s * 1e9)
            )
        overrun_counts[link_index] = state.overrun_windows
    except BaseException:
        _failed(error_queue, role)
        raise
    finally:
        if isinstance(sock, socket.socket):
            sock.close()


def _wait_ready(ready_queue, n: int, timeout_s: float = 15.0) -> None:
    deadline = time.monotonic() + timeout_s
    seen = 0
    while seen < n:
        remaining = deadline - time.monotonic()
        if remaining <= 0.0:
            raise RuntimeError(f"worker readiness timeout; ready={seen}/{n}")
        try:
            kind, _role, _pid = ready_queue.get(timeout=remaining)
        except queue.Empty as exc:
            raise RuntimeError("worker readiness timeout") from exc
        if kind == "ready":
            seen += 1


# ------------------------------------------------------------------ one run
def run_arm_replicate(arm: dict, rates_pps: np.ndarray,
                      emitter_cpus: tuple[int, ...],
                      sink_cpus: tuple[int, ...]) -> tuple[np.ndarray, list[int]]:
    """Return (n_links, n_windows) max deadline lateness and overrun counts."""
    if rates_pps.shape != (len(LINKS), DIAG_WINDOWS):
        raise ValueError("rates_pps must have shape (links, windows)")
    context = mp.get_context("fork")
    n_links = len(LINKS)
    shared_cumulative = atomic_int64_array(n_links)
    window_lateness_ns = atomic_int64_array(n_links * DIAG_WINDOWS)
    overrun_counts = atomic_int64_array(n_links)
    epoch_value = context.Value("d", 0.0, lock=False)
    start_event = context.Event()
    stop_event = context.Event()
    ready_queue = context.Queue()
    error_queue = context.Queue()

    processes: list[mp.Process] = []
    sockets: list[socket.socket] = []

    if not arm["send"]:
        destinations: list[tuple[str, int] | None] = [None] * n_links
    else:
        n_sinks = n_links if arm["split_sink"] else 1
        for index in range(n_sinks):
            bound = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            bound.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 << 20)
            bound.bind(("127.0.0.1", 0))
            sockets.append(bound)
            processes.append(context.Process(
                target=_diag_sink,
                args=(bound, sink_cpus[index % len(sink_cpus)], stop_event,
                      start_event, ready_queue, error_queue),
                name=f"diag-sink-{index}",
            ))
        destinations = [
            sockets[link_index % n_sinks].getsockname()
            for link_index in range(n_links)
        ]

    n_sink_procs = len(processes)
    for link_index, cpu in enumerate(emitter_cpus):
        offset = (link_index * DT_S / n_links) if arm["stagger"] else 0.0
        processes.append(context.Process(
            target=_diag_emitter,
            args=(link_index, cpu, rates_pps[link_index].tolist(),
                  destinations[link_index], epoch_value, offset, start_event,
                  shared_cumulative, window_lateness_ns, overrun_counts,
                  ready_queue, error_queue),
            name=f"diag-emitter-{LINKS[link_index]}",
        ))

    for process in processes:
        process.start()
    try:
        _wait_ready(ready_queue, len(processes))
        epoch_value.value = time.perf_counter() + START_DELAY_S
        start_event.set()
        deadline = DIAG_DURATION_S + START_DELAY_S + DT_S + JOIN_SLACK_S
        for process in processes[n_sink_procs:]:
            process.join(timeout=deadline)
            if process.is_alive():
                raise RuntimeError(f"worker timeout: {process.name}")
        stop_event.set()
        for process in processes[:n_sink_procs]:
            process.join(timeout=5.0)
            if process.is_alive():
                raise RuntimeError(f"sink timeout: {process.name}")
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get_nowait())
        failures = [p.name for p in processes if p.exitcode != 0]
        if errors or failures:
            raise RuntimeError(f"worker failures={failures} errors={errors}")
    finally:
        stop_event.set()
        start_event.set()
        for process in processes:
            if process.is_alive():
                process.terminate()
            process.join(timeout=1.0)
        for bound in sockets:
            try:
                bound.close()
            except OSError:
                pass

    lateness = np.fromiter(window_lateness_ns, dtype=np.int64).reshape(
        n_links, DIAG_WINDOWS
    ) / 1e9
    if np.any(lateness < 0.0):
        raise RuntimeError("negative lateness recorded; ledger is corrupt")
    return lateness, [int(v) for v in overrun_counts]


# ---------------------------------------------------------------- reduction
def _rank(matrix: np.ndarray) -> np.ndarray:
    return matrix.argsort(axis=1).argsort(axis=1).astype(float)


def co_spike_fraction(matrix: np.ndarray) -> float:
    """Windows where at least SPIKE_MIN_LINKS links sit in their own upper tail."""
    thresholds = np.quantile(matrix, SPIKE_QUANTILE, axis=1, keepdims=True)
    hot = matrix >= thresholds
    return float(np.mean(hot.sum(axis=0) >= SPIKE_MIN_LINKS))


def co_spike_null() -> float:
    from math import comb
    p = 1.0 - SPIKE_QUANTILE
    n = len(LINKS)
    return float(sum(
        comb(n, k) * p**k * (1.0 - p) ** (n - k)
        for k in range(SPIKE_MIN_LINKS, n + 1)
    ))


def staggered_overlap_baseline(
    aligned_correlation_targets: tuple[float, ...] = (0.10, 0.15, 0.20),
    stall_bins_grid: tuple[int, ...] = (1, 10, 20, 40),
    replicates: int = 300,
    windows: int = DIAG_WINDOWS,
    bins_per_window: int = 80,
    seed: int = DIAG_SEED,
) -> list[dict[str, object]]:
    """Calibrate the staggered/aligned correlation ratio under a pure null.

    The naive predictor for that ratio is the window overlap coefficient
    ``1 - |i-j|/n_links``.  That coefficient is BIASED for a maximum
    statistic: a per-window maximum does not lose covariance linearly in the
    probability that two windows co-contain a shared event.

    This routine therefore measures the ratio directly under a null that has
    NO synchronisation component at all: shared stalls arrive on a fine time
    grid independently of every window boundary, and the only difference
    between the aligned and staggered arms is the grid offset.  Any residual
    of the observed ratio ABOVE this baseline cannot be evidence for a
    synchronisation mechanism, because the null already produces it.
    """
    if bins_per_window % len(LINKS) != 0:
        raise ValueError("bins_per_window must divide evenly by the link count")
    n_links = len(LINKS)
    total_bins = windows * bins_per_window + bins_per_window
    offsets = [index * bins_per_window // n_links for index in range(n_links)]
    overlap = np.array([
        [1.0 - abs(i - j) / n_links for j in range(n_links)]
        for i in range(n_links)
    ])

    def per_window_max(fine: np.ndarray, stagger: bool) -> np.ndarray:
        out = np.empty((n_links, windows), dtype=float)
        for index in range(n_links):
            start = offsets[index] if stagger else 0
            block = fine[index, start:start + windows * bins_per_window]
            out[index] = block.reshape(windows, bins_per_window).max(axis=1)
        return out

    rows = []
    for stall_bins in stall_bins_grid:
      for amplitude in aligned_correlation_targets:
        aligned_mats, staggered_mats = [], []
        for replicate in range(replicates):
            rng = np.random.default_rng(seed + replicate)
            shared = np.abs(rng.standard_normal(total_bins))
            spikes = rng.random(total_bins) < 0.004 / stall_bins
            magnitude = spikes * rng.exponential(6.0, total_bins)
            if stall_bins > 1:
                magnitude = np.convolve(
                    magnitude, np.ones(stall_bins), mode="same"
                )
            shared = shared + magnitude
            private = np.abs(rng.standard_normal((n_links, total_bins)))
            fine = private + amplitude * shared[None, :]
            aligned_mats.append(np.corrcoef(per_window_max(fine, False)))
            staggered_mats.append(np.corrcoef(per_window_max(fine, True)))
        aligned = np.abs(np.mean(aligned_mats, axis=0))
        staggered = np.abs(np.mean(staggered_mats, axis=0))
        upper = np.triu_indices(n_links, 1)
        ratio = staggered[upper] / aligned[upper]
        residual = ratio - overlap[upper]
        rows.append({
            "shared_amplitude": float(amplitude),
            "stall_bins": int(stall_bins),
            "stall_duration_ms": float(stall_bins * DT_S * 1e3 / bins_per_window),
            "aligned_offdiag_median": float(np.median(aligned[upper])),
            "staggered_offdiag_median": float(np.median(staggered[upper])),
            "ratio_median": float(np.median(ratio)),
            "overlap_median": float(np.median(overlap[upper])),
            "residual_median": float(np.median(residual)),
            "residual_se": float(residual.std(ddof=1) / np.sqrt(residual.size)),
            "pairs": int(residual.size),
            "replicates": int(replicates),
        })
    return rows


def summarise_arm(name: str, replicates: list[np.ndarray], overruns: list[list[int]],
                  emitter_cpus: tuple[int, ...]) -> dict[str, object]:
    stacked = np.asarray(replicates)
    degenerate = bool(np.any(stacked.std(axis=2) <= 0.0))
    pearson_max, pearson_matrix = mean_correlation_then_max(stacked)
    spearman_max, _spearman_matrix = mean_correlation_then_max(
        np.asarray([_rank(r) for r in replicates])
    )
    matrix = np.asarray(pearson_matrix)
    same, diff = [], []
    for i in range(len(LINKS)):
        for j in range(i + 1, len(LINKS)):
            value = abs(float(matrix[i, j]))
            (same if emitter_cpus[i] == emitter_cpus[j] else diff).append(value)
    lateness = np.concatenate(replicates, axis=1)
    total_windows = len(overruns) * DIAG_WINDOWS
    return {
        "arm": name,
        "degenerate_zero_variance_link": degenerate,
        "pearson_max_abs_offdiag": pearson_max,
        "spearman_max_abs_offdiag": spearman_max,
        "same_cpu_pairs": {"n": len(same), "values": [round(v, 4) for v in same]},
        "diff_cpu_pairs": {
            "n": len(diff),
            "min": round(min(diff), 4) if diff else None,
            "median": round(float(np.median(diff)), 4) if diff else None,
            "max": round(max(diff), 4) if diff else None,
        },
        "co_spike_fraction": float(np.mean(
            [co_spike_fraction(r) for r in replicates]
        )),
        "overrun_fraction_max": max(
            sum(row[i] for row in overruns) / total_windows
            for i in range(len(LINKS))
        ),
        "lateness_s": {
            "median": float(np.median(lateness)),
            "p99": float(np.quantile(lateness, 0.99)),
            "max": float(lateness.max()),
        },
        "pearson_matrix": matrix.tolist(),
    }


# --------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--arms", default="")
    parser.add_argument("--replicates", type=int, default=DIAG_REPLICATES)
    args = parser.parse_args()

    selected = [a for a in ARMS
                if not args.arms or a["name"] in args.arms.split(",")]
    if not selected:
        raise SystemExit("REFUSED: no arm selected")

    maps = build_ladder_cpu_maps()
    emitter_cpus = tuple(maps["L0"][:len(LINKS)])
    sink_cpus = tuple(maps["L0"][-2:])
    rates = [replicate_rates(index) for index in range(args.replicates)]

    started = time.time()
    results = []
    for arm in selected:
        replicates, overruns = [], []
        for index in range(args.replicates):
            print(f"running {arm['name']} replicate {index + 1}/{args.replicates}",
                  flush=True)
            lateness, overrun = run_arm_replicate(
                arm, rates[index], emitter_cpus, sink_cpus
            )
            replicates.append(lateness)
            overruns.append(overrun)
        row = summarise_arm(arm["name"], replicates, overruns, emitter_cpus)
        row["kills"] = arm["kills"]
        row["config"] = {k: arm[k] for k in ("send", "split_sink", "stagger")}
        results.append(row)

    null = simulate_emit3_null(
        trials=DIAG_NULL_TRIALS,
        replicates=args.replicates,
        windows=DIAG_WINDOWS,
        seed=DIAG_NULL_SEED,
    )
    artifact = {
        "schema": "dt4n.phase_g.g3_emit3_decomposition.v1",
        "status": "DIAGNOSTIC_NOT_ADJUDICATED",
        "adjudicates": None,
        "authorizes": None,
        "git_hash": git_hash(),
        "elapsed_s": round(time.time() - started, 1),
        "design": {
            "cell": DIAG_CELL,
            "duration_s": DIAG_DURATION_S,
            "windows": DIAG_WINDOWS,
            "replicates": args.replicates,
            "dt_s": DT_S,
            "payload_bytes": PAYLOAD_BYTES,
            "wire_bytes": WIRE_BYTES,
            "emitter_cpus": list(emitter_cpus),
            "sink_cpus": list(sink_cpus),
            "rate_seed": DIAG_SEED,
            "rate_path": "tools.g3_dryrun.physical_trace, omega=0, same as runner",
            "reduction": "mean of within-replicate 8x8 matrices, then max 28 pairs",
            "spike_quantile": SPIKE_QUANTILE,
            "spike_min_links": SPIKE_MIN_LINKS,
        },
        "null_recalibrated_for_this_shape": null,
        "co_spike_null_independent": co_spike_null(),
        "arms": results,
        "limits": LIMITS,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("\narm             pearson  spearman  co_spike  diffCPU_med  overrun  sameCPU")
    for row in results:
        print("%-14s  %7.4f  %8.4f  %8.5f  %11s  %7.5f  %s" % (
            row["arm"], row["pearson_max_abs_offdiag"],
            row["spearman_max_abs_offdiag"], row["co_spike_fraction"],
            row["diff_cpu_pairs"]["median"], row["overrun_fraction_max"],
            row["same_cpu_pairs"]["values"]))
    print("\nnull p99 (this shape): %.5f   co_spike null: %.3e" % (
        null["p99"], co_spike_null()))
    print("DIAGNOSTIC ONLY - adjudicates nothing")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Phase L / L.4 -- pure load-generation specification.

No socket, no Mininet, no file I/O. The intended traffic schedule is a pure
function of the seed, so tests can lock rate accounting, c_a, and digests
before any live experiment runs.
"""

from __future__ import annotations

import hashlib
import math
import random
import struct
from typing import Dict, List, Optional, Sequence, Tuple


FRAME_OVERHEAD_BYTES = 42
PAYLOAD_BG = 1470
PAYLOAD_PROBE = 64
FRAME_BG = PAYLOAD_BG + FRAME_OVERHEAD_BYTES
FRAME_PROBE = PAYLOAD_PROBE + FRAME_OVERHEAD_BYTES
PROBE_PPS = 20.0

MODES = ("cbr", "poisson", "h2", "onoff")
H2_TARGET_CA = 2.0
ONOFF_DEFAULT = {
    "peak_factor": 1.35,
    "alpha": 1.5,
    "xm_on_s": 0.005,
    "tmax_s": 1.0,
}
DESIGN_CA = {"cbr": 0.0, "poisson": 1.0, "h2": H2_TARGET_CA, "onoff": None}


def capacity_bytes_per_s(bw_mbps: float) -> float:
    return float(bw_mbps) * 1e6 / 8.0


def background_pps(
    rho: float,
    bw_mbps: float,
    probe_pps: float = PROBE_PPS,
) -> float:
    """Background packet rate needed so background plus probe equals rho."""
    return (
        float(rho) * capacity_bytes_per_s(bw_mbps)
        - float(probe_pps) * FRAME_PROBE
    ) / FRAME_BG


def rho_from_rates(bg_pps: float, probe_pps: float, bw_mbps: float) -> float:
    return (
        float(bg_pps) * FRAME_BG + float(probe_pps) * FRAME_PROBE
    ) / capacity_bytes_per_s(bw_mbps)


def cv(xs: Sequence[float]) -> float:
    """Coefficient of variation: population sd divided by mean."""
    n = len(xs)
    if n < 2:
        return float("nan")
    m = sum(xs) / n
    if m == 0:
        return float("nan")
    return math.sqrt(sum((x - m) ** 2 for x in xs) / n) / m


def h2_params(mean_gap: float, ca: float = H2_TARGET_CA) -> Tuple[float, float, float]:
    """Balanced-means two-phase hyperexponential parameters."""
    mean_gap = float(mean_gap)
    ca = float(ca)
    if mean_gap <= 0:
        raise ValueError("mean_gap phai > 0")
    if ca <= 1.0:
        raise ValueError("H2 chi tao duoc c_a > 1; dung poisson cho c_a = 1")
    s = math.sqrt((ca * ca - 1.0) / (ca * ca + 1.0))
    p = 0.5 * (1.0 - s)
    return p, 2.0 * p / mean_gap, 2.0 * (1.0 - p) / mean_gap


def _trunc_pareto(rng: random.Random, alpha: float, xm: float, tmax: float) -> float:
    if alpha <= 0:
        raise ValueError("alpha phai > 0")
    if xm <= 0 or tmax <= xm:
        raise ValueError("can 0 < xm < tmax cho Pareto cat tren")
    fmax = 1.0 - (xm / tmax) ** alpha
    return xm * (1.0 - rng.random() * fmax) ** (-1.0 / alpha)


def _gaps_onoff(
    n: int,
    mean_gap: float,
    rng: random.Random,
    peak_factor: float,
    alpha: float,
    xm_on_s: float,
    tmax_s: float,
) -> List[float]:
    """Single ON-OFF source; ON sends at peak_factor times mean rate."""
    P = float(peak_factor)
    if P <= 1.0:
        raise ValueError("peak_factor phai > 1")
    tau = float(mean_gap) / P
    xm_off = float(xm_on_s) * (P - 1.0)
    t = 0.0
    sends: List[float] = []
    on = rng.random() < 1.0 / P
    d = _trunc_pareto(rng, alpha, xm_on_s if on else xm_off, tmax_s) * rng.random()
    while len(sends) < int(n) + 1:
        if on:
            end = t + d
            while t < end and len(sends) < int(n) + 1:
                sends.append(t)
                t += tau
            on = False
            d = _trunc_pareto(rng, alpha, xm_off, tmax_s)
        else:
            t += d
            on = True
            d = _trunc_pareto(rng, alpha, xm_on_s, tmax_s)
    return [sends[i + 1] - sends[i] for i in range(int(n))]


def normalize_rate(gaps: Sequence[float], mean_gap: float) -> List[float]:
    """Scale every gap so the mean rate is exact while c_a is unchanged."""
    if not gaps:
        return []
    m = sum(gaps) / len(gaps)
    if m <= 0:
        raise ValueError("khoang cach trung binh <= 0")
    k = float(mean_gap) / m
    return [float(g) * k for g in gaps]


def build_schedule(
    mode: str,
    n_packets: int,
    mean_gap: float,
    seed: int,
    ca: float = H2_TARGET_CA,
    onoff: Optional[Dict[str, float]] = None,
) -> List[float]:
    """Pure function: mode, n, mean gap, seed -> normalized gap schedule."""
    if mode not in MODES:
        raise ValueError("mode phai thuoc %s" % (MODES,))
    n = int(n_packets)
    if n < 0:
        raise ValueError("n_packets phai >= 0")
    mean_gap = float(mean_gap)
    if mean_gap <= 0:
        raise ValueError("mean_gap phai > 0")
    rng = random.Random(int(seed))

    if mode == "cbr":
        return [mean_gap] * n
    if mode == "poisson":
        gaps = [rng.expovariate(1.0 / mean_gap) for _ in range(n)]
    elif mode == "h2":
        p, l1, l2 = h2_params(mean_gap, ca)
        gaps = [
            rng.expovariate(l1) if rng.random() < p else rng.expovariate(l2)
            for _ in range(n)
        ]
    else:
        opt = dict(ONOFF_DEFAULT)
        opt.update(onoff or {})
        gaps = _gaps_onoff(n, mean_gap, rng, **opt)
    return normalize_rate(gaps, mean_gap)


def schedule_digest(gaps: Sequence[float]) -> str:
    h = hashlib.sha256()
    for gap in gaps:
        h.update(struct.pack("<d", float(gap)))
    return h.hexdigest()


def merge_schedules(
    bg_gaps: Sequence[float],
    probe_gaps: Sequence[float],
    t0: float = 0.0,
) -> List[Tuple[float, bool]]:
    """Merge background and probe gaps into sorted (relative_time, is_probe)."""
    events: List[Tuple[float, bool]] = []
    t = float(t0)
    for gap in bg_gaps:
        t += float(gap)
        events.append((t, False))
    t = float(t0)
    for gap in probe_gaps:
        t += float(gap)
        events.append((t, True))
    events.sort(key=lambda row: row[0])
    return events


def aggregate_ca(events: Sequence[Tuple[float, bool]]) -> float:
    ts = [float(t) for t, _is_probe in events]
    return cv([b - a for a, b in zip(ts, ts[1:])])

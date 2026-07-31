#!/usr/bin/env python3
"""Phase T / T.3 -- pure time-varying packet schedule.

This module couples the flow-time load trajectory ``rho(t)`` from
``rho_spec`` to the packet-time arrival shape from Phase L by time-rescaling.
It is intentionally pure: no sockets, no Mininet, no clock.
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from mininet.load_spec import (
    DESIGN_CA,
    H2_TARGET_CA,
    PROBE_PPS,
    background_pps,
    build_schedule,
    cv,
    merge_schedules,
    schedule_digest,
)
from mininet.rho_spec import RhoTrajectory


def intensity(
    traj: RhoTrajectory,
    bw_mbps: float,
    probe_pps: float = PROBE_PPS,
) -> List[float]:
    """Return background intensity lambda(t), in packets/s, for each rho step."""
    lam = [background_pps(rho, bw_mbps, probe_pps) for rho in traj.rho]
    if min(lam) <= 0.0:
        raise ValueError("rho(t) qua nho so voi probe: lambda <= 0 tai mot buoc")
    return lam


def cumulative_intensity(lam: Sequence[float], dt: float) -> List[float]:
    """Piecewise-linear Lambda(t) on the rho grid, returned at n+1 grid points."""
    out = [0.0]
    step = float(dt)
    for v in lam:
        out.append(out[-1] + float(v) * step)
    return out


def invert_cumulative(cum: Sequence[float], dt: float, u: float) -> float:
    """Return Lambda^{-1}(u) by exact linear interpolation inside a rho step."""
    if len(cum) < 2:
        raise ValueError("cum phai co it nhat 2 diem")
    k = bisect.bisect_right(cum, float(u)) - 1
    k = min(max(k, 0), len(cum) - 2)
    span = cum[k + 1] - cum[k]
    frac = 0.0 if span <= 0.0 else (float(u) - cum[k]) / span
    return (k + frac) * float(dt)


@dataclass
class VaryingSchedule:
    send_times: List[float]
    bg_gaps: List[float]
    cum: List[float]
    dt: float
    mode: str
    path: str
    design: Dict[str, object]

    def digest(self) -> str:
        """Digest over real-time background gaps, using Phase L's hash contract."""
        return schedule_digest(self.bg_gaps)

    def ca_pooled(self) -> float:
        """Pooled real-time c_a. This inflates when lambda(t) varies."""
        return cv(self.bg_gaps)

    def operational_times(self) -> List[float]:
        """Map send times back to operational time, u_i = Lambda(T_i)."""
        out: List[float] = []
        for t in self.send_times:
            x = float(t) / self.dt
            k = min(max(int(x), 0), len(self.cum) - 2)
            frac = x - k
            out.append(self.cum[k] + frac * (self.cum[k + 1] - self.cum[k]))
        return out

    def ca_operational(self) -> float:
        """V-T4a/V-T6a: c_a measured after transforming to operational time."""
        u = self.operational_times()
        return cv([b - a for a, b in zip(u, u[1:])])

    def rate_ratio(self) -> float:
        """Actual background count divided by Lambda_total."""
        if self.path == "phase_l_const":
            return 1.0
        return len(self.send_times) / self.design["total_operational"]

    def as_dict(self) -> Dict[str, object]:
        return {
            "mode": self.mode,
            "path": self.path,
            "n_bg": len(self.send_times),
            "schedule_digest": self.digest(),
            "c_a_design": DESIGN_CA.get(self.mode),
            "c_a_operational": self.ca_operational(),
            "c_a_pooled": self.ca_pooled(),
            "rate_ratio": self.rate_ratio(),
            "design": dict(self.design),
        }


def ca_pooled_predicted(lam: Sequence[float], c_design: float) -> float:
    """Closed-form pooled real-time c_a after time-rescaling."""
    n = len(lam)
    if n <= 0:
        raise ValueError("lam khong duoc rong")
    el = sum(lam) / n
    eil = sum(1.0 / v for v in lam) / n
    return math.sqrt(max((1.0 + float(c_design) ** 2) * el * eil - 1.0, 0.0))


def ca_thinning_predicted(c_design: float, p_keep: float) -> float:
    """Closed-form c_a after independent thinning, used as a negative control."""
    p = float(p_keep)
    return math.sqrt(max(p * float(c_design) ** 2 + (1.0 - p), 0.0))


def build_varying_schedule(
    mode: str,
    traj: RhoTrajectory,
    bw_mbps: float,
    seed: int,
    ca: float = H2_TARGET_CA,
    probe_pps: float = PROBE_PPS,
) -> VaryingSchedule:
    """Build a background packet schedule from rho(t) by time-rescaling."""
    dur = traj.duration_s

    if traj.kind == "const":
        rho = traj.rho[0]
        pps = background_pps(rho, bw_mbps, probe_pps)
        n_bg = max(1, int(pps * dur))
        gaps = build_schedule(mode, n_bg, 1.0 / pps, seed, ca=ca)
        t = 0.0
        times: List[float] = []
        for gap in gaps:
            t += gap
            times.append(t)
        lam = [pps] * traj.n_steps
        return VaryingSchedule(
            times,
            gaps,
            cumulative_intensity(lam, traj.dt),
            traj.dt,
            mode,
            "phase_l_const",
            {
                "rho": rho,
                "bw_mbps": float(bw_mbps),
                "n_bg": n_bg,
                "total_operational": pps * dur,
            },
        )

    lam = intensity(traj, bw_mbps, probe_pps)
    cum = cumulative_intensity(lam, traj.dt)
    total = cum[-1]
    n_base = int(total)
    if n_base < 2:
        raise ValueError("qua it goi: Lambda_total = %.3f" % total)

    # Normalize in operational time before projecting through Lambda^{-1}.
    g_op = build_schedule(mode, n_base, 1.0, seed, ca=ca)

    times: List[float] = []
    u = 0.0
    for gap in g_op:
        u += gap
        if u > total:
            break
        times.append(invert_cumulative(cum, traj.dt, u))
    gaps = [b - a for a, b in zip([0.0] + times, times)]

    return VaryingSchedule(
        times,
        gaps,
        cum,
        traj.dt,
        mode,
        "rescale",
        {
            "bw_mbps": float(bw_mbps),
            "n_base": n_base,
            "total_operational": total,
            "c_design": DESIGN_CA.get(mode),
        },
    )


def merge_with_probe(
    sched: VaryingSchedule,
    probe_pps: float,
    duration_s: float,
    seed: int,
) -> List[Tuple[float, bool]]:
    """Merge varying background traffic with an unchanged constant Poisson probe."""
    n_pr = max(0, int(float(probe_pps) * float(duration_s))) if probe_pps > 0 else 0
    pr_gaps = (
        build_schedule("poisson", n_pr, 1.0 / float(probe_pps), int(seed) + 500000)
        if n_pr > 0
        else []
    )
    return merge_schedules(sched.bg_gaps, pr_gaps)

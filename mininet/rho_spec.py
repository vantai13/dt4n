#!/usr/bin/env python3
"""Phase T / T.2 -- pure rho(t) specification.

No socket, no Mininet, no file I/O, no wall clock. The intended load
trajectory is a pure function of (rho_bar, sigma_rho, tau_rho, seed), so tests
can lock sigma, tau, clamp counts and digests before any live run.

Design notes that matter for reproduction:

* Normals come from an explicit Box-Muller transform on ``rng.random()``, not
  from ``random.gauss``. ``random.gauss`` caches a second variate on the Random
  instance, so its call pattern depends on history; Box-Muller written out here
  consumes exactly two uniforms per normal, forever.
* The chain starts from its stationary distribution, not from rho_bar. Starting
  at the mean gives a variance transient of length around 3*tau_rho.
* Clamping is to the measured domain of link_model_v2, [0.50, 1.05], because
  f(rho) is undefined outside it and predict_delay(strict=True) raises there.
"""

from __future__ import annotations

import hashlib
import math
import random
import struct
from dataclasses import dataclass
from typing import Dict, List, Sequence


RHO_MIN, RHO_MAX = 0.50, 1.05
DT_DEFAULT = 0.005
Z_FEASIBLE = 2.58


def sub_seed(master_seed: int, label: str) -> int:
    """Derive an independent random stream by label, not by offset arithmetic."""
    h = hashlib.sha256()
    h.update(struct.pack("<q", int(master_seed)))
    h.update(b"|")
    h.update(label.encode("utf-8"))
    return int.from_bytes(h.digest()[:8], "little", signed=False)


def _standard_normals(rng: random.Random, n: int) -> List[float]:
    """Return n N(0,1) samples using Box-Muller, two uniforms per normal."""
    out: List[float] = []
    for _ in range(int(n)):
        u1 = rng.random()
        while u1 <= 0.0:
            u1 = rng.random()
        u2 = rng.random()
        out.append(math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2))
    return out


def sigma_max_feasible(
    rho_bar: float,
    z: float = Z_FEASIBLE,
    lo: float = RHO_MIN,
    hi: float = RHO_MAX,
) -> float:
    """Largest sigma_rho allowed by the two-sided clamp feasibility rule."""
    return min(float(rho_bar) - float(lo), float(hi) - float(rho_bar)) / float(z)


def sigma_from_a(rho_bar: float, a: float) -> float:
    """Phase T design axis: sigma_rho = a * sigma_max_feasible(rho_bar)."""
    return float(a) * sigma_max_feasible(rho_bar)


@dataclass
class RhoTrajectory:
    rho: List[float]
    dt: float
    n_clamped: int
    kind: str
    design: Dict[str, float]

    @property
    def n_steps(self) -> int:
        return len(self.rho)

    @property
    def duration_s(self) -> float:
        return self.n_steps * self.dt

    @property
    def clamp_ratio(self) -> float:
        return self.n_clamped / max(self.n_steps, 1)

    def digest(self) -> str:
        """SHA-256 over version, kind, dt, and the whole rho series as f64 LE."""
        h = hashlib.sha256()
        h.update(("rho_spec_v1|%s|%.17g|" % (self.kind, self.dt)).encode("utf-8"))
        for x in self.rho:
            h.update(struct.pack("<d", float(x)))
        return h.hexdigest()

    def as_dict(self) -> Dict[str, object]:
        """Provenance record suitable for measurement metadata."""
        return {
            "kind": self.kind,
            "dt": self.dt,
            "n_steps": self.n_steps,
            "duration_s": self.duration_s,
            "n_clamped": self.n_clamped,
            "clamp_ratio": self.clamp_ratio,
            "trajectory_digest": self.digest(),
            "design": dict(self.design),
            "measured": {
                "rho_bar": measure_mean(self.rho),
                "sigma_rho": measure_sigma(self.rho),
                "tau_rho_s": measure_tau(self.rho, self.dt),
            },
        }


def ou_trajectory(
    rho_bar: float,
    sigma_rho: float,
    tau_rho: float,
    n_steps: int,
    seed: int,
    dt: float = DT_DEFAULT,
    lo: float = RHO_MIN,
    hi: float = RHO_MAX,
) -> RhoTrajectory:
    """Exact discrete OU/AR(1), stationary-initialized, then clamped to [lo, hi]."""
    rho_bar = float(rho_bar)
    sigma_rho = float(sigma_rho)
    dt = float(dt)
    n = int(n_steps)
    if n <= 0:
        raise ValueError("n_steps phai > 0")
    if sigma_rho < 0:
        raise ValueError("sigma_rho phai >= 0")
    if sigma_rho > 0 and float(tau_rho) <= 0:
        raise ValueError("tau_rho phai > 0 khi sigma_rho > 0")
    if not (lo <= rho_bar <= hi):
        raise ValueError("rho_bar %.4f ngoai mien [%.2f, %.2f]" % (rho_bar, lo, hi))

    if sigma_rho == 0.0:
        return RhoTrajectory(
            [rho_bar] * n,
            dt,
            0,
            "const",
            {"rho_bar": rho_bar, "sigma_rho": 0.0, "tau_rho": 0.0},
        )

    phi = math.exp(-dt / float(tau_rho))
    sd_eps = sigma_rho * math.sqrt(max(1.0 - phi * phi, 0.0))
    rng = random.Random(sub_seed(seed, "rho_ou"))
    z = _standard_normals(rng, n)

    out: List[float] = []
    n_clamped = 0
    x = rho_bar + sigma_rho * z[0]
    for k in range(n):
        if k > 0:
            x = rho_bar + phi * (x - rho_bar) + sd_eps * z[k]
        if x < lo:
            x = lo
            n_clamped += 1
        elif x > hi:
            x = hi
            n_clamped += 1
        out.append(x)
    return RhoTrajectory(
        out,
        dt,
        n_clamped,
        "ou",
        {"rho_bar": rho_bar, "sigma_rho": sigma_rho, "tau_rho": float(tau_rho)},
    )


def step_trajectory(
    rho_a: float,
    rho_b: float,
    hold_s: float,
    n_cycles: int,
    dt: float = DT_DEFAULT,
    lo: float = RHO_MIN,
    hi: float = RHO_MAX,
) -> RhoTrajectory:
    """Deterministic square-wave A->B->A trajectory for T.5 step response."""
    rho_a = float(rho_a)
    rho_b = float(rho_b)
    hold_s = float(hold_s)
    dt = float(dt)
    cycles = int(n_cycles)
    if hold_s <= 0.0:
        raise ValueError("hold_s phai > 0")
    if dt <= 0.0:
        raise ValueError("dt phai > 0")
    if cycles <= 0:
        raise ValueError("n_cycles phai > 0")
    if not (lo <= rho_a <= hi) or not (lo <= rho_b <= hi):
        raise ValueError("rho_a/rho_b ngoai mien [%.2f, %.2f]" % (lo, hi))

    n_hold = int(round(hold_s / dt))
    if n_hold <= 0:
        raise ValueError("hold_s qua ngan so voi dt")

    rho: List[float] = []
    for _ in range(cycles):
        rho.extend([rho_a] * n_hold)
        rho.extend([rho_b] * n_hold)
    return RhoTrajectory(
        rho,
        dt,
        0,
        "step",
        {
            "rho_a": rho_a,
            "rho_b": rho_b,
            "hold_s": hold_s,
            "n_cycles": cycles,
        },
    )


def measure_mean(xs: Sequence[float]) -> float:
    return float(sum(xs) / len(xs))


def measure_sigma(xs: Sequence[float]) -> float:
    """Population standard deviation, matching the designed sigma_rho."""
    n = len(xs)
    if n < 2:
        return float("nan")
    m = measure_mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / n)


def measure_tau(xs: Sequence[float], dt: float) -> float:
    """Estimate tau from lag-1 autocorrelation: r1 = exp(-dt/tau)."""
    n = len(xs)
    if n < 3:
        return float("nan")
    m = measure_mean(xs)
    d = [x - m for x in xs]
    v = sum(y * y for y in d)
    if v <= 0:
        return float("nan")
    r1 = sum(d[i] * d[i + 1] for i in range(n - 1)) / v
    if not (0.0 < r1 < 1.0):
        return float("nan")
    return -float(dt) / math.log(r1)


def expected_sigma_hat(
    sigma_rho: float,
    tau_rho: float,
    duration_s: float,
    dt: float = DT_DEFAULT,
) -> float:
    """Expected finite-window sigma_hat for an AR(1) sample with sample mean removed."""
    n = int(round(float(duration_s) / float(dt)))
    if n < 2 or float(tau_rho) <= 0:
        return float(sigma_rho)
    phi = math.exp(-float(dt) / float(tau_rho))
    s = 0.0
    p = 1.0
    for k in range(1, n):
        p *= phi
        if p < 1e-15:
            break
        s += (1.0 - k / n) * p
    return float(sigma_rho) * math.sqrt(max(1.0 - (1.0 + 2.0 * s) / n, 0.0))


def mminf_trajectory(
    rho_bar: float,
    sigma_rho: float,
    tau_rho: float,
    n_steps: int,
    seed: int,
    dt: float = DT_DEFAULT,
    lo: float = RHO_MIN,
    hi: float = RHO_MAX,
) -> RhoTrajectory:
    """Physical control: rho(t) from the occupancy of an M/M/infinity system."""
    rho_bar = float(rho_bar)
    sigma_rho = float(sigma_rho)
    tau_rho = float(tau_rho)
    dt = float(dt)
    n = int(n_steps)
    if sigma_rho <= 0:
        raise ValueError("mminf can sigma_rho > 0; dung ou_trajectory cho hang so")
    if tau_rho <= 0:
        raise ValueError("tau_rho phai > 0")
    if n <= 0:
        raise ValueError("n_steps phai > 0")
    if not (lo <= rho_bar <= hi):
        raise ValueError("rho_bar %.4f ngoai mien [%.2f, %.2f]" % (rho_bar, lo, hi))

    n_mean = (rho_bar / sigma_rho) ** 2
    rate_per_flow = rho_bar / n_mean
    lam_f = n_mean / tau_rho
    p_leave = 1.0 - math.exp(-dt / tau_rho)

    rng = random.Random(sub_seed(seed, "rho_mminf"))
    n_act = _poisson(rng, n_mean)
    out: List[float] = []
    n_clamped = 0
    for _ in range(n):
        x = n_act * rate_per_flow
        if x < lo:
            x = lo
            n_clamped += 1
        elif x > hi:
            x = hi
            n_clamped += 1
        out.append(x)
        n_act -= _binomial(rng, n_act, p_leave)
        n_act += _poisson(rng, n_mean * p_leave)
    return RhoTrajectory(
        out,
        dt,
        n_clamped,
        "mminf",
        {
            "rho_bar": rho_bar,
            "sigma_rho": sigma_rho,
            "tau_rho": tau_rho,
            "n_flows_mean": n_mean,
            "rate_per_flow": rate_per_flow,
            "flow_arrival_rate": lam_f,
        },
    )


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth for small lambda; normal approximation for large lambda."""
    lam = float(lam)
    if lam <= 0.0:
        return 0
    if lam < 30.0:
        target = math.exp(-lam)
        k, p = 0, 1.0
        while True:
            p *= rng.random()
            if p <= target:
                return k
            k += 1
    z = _standard_normals(rng, 1)[0]
    return max(0, int(round(lam + math.sqrt(lam) * z)))


def _binomial(rng: random.Random, n: int, p: float) -> int:
    n = int(n)
    p = float(p)
    if n <= 0 or p <= 0.0:
        return 0
    if p >= 1.0:
        return n
    if n * p < 30.0:
        return sum(1 for _ in range(n) if rng.random() < p)
    z = _standard_normals(rng, 1)[0]
    return min(n, max(0, int(round(n * p + math.sqrt(n * p * (1.0 - p)) * z))))

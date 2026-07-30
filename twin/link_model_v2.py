#!/usr/bin/env python3
"""link_model v2 -- measured Phase L queue-delay model.

The model has three runtime outputs:

* ``predict_delay``: mean q-delay in ms, additive across path links.
* ``sigma``: local residual scale for normalized conformal prediction.
* ``domain``: measured rho interval. Strict prediction rejects extrapolation.

Traffic-family conditioning is intentional. Amendment 7 shows that ``c_a`` is
not sufficient: onoff can have higher ``c_a`` than h2 while producing much less
delay. Keep separate curves per ``mode|bw|q`` unless a future model proves a
stronger invariant.
"""

from __future__ import annotations

import bisect
import json
import math
from typing import Dict, Iterable, List, Sequence, Tuple


def kingman_ceiling(rho: float, k: float, w_max: float, floor: float = 0.0) -> float:
    """Return ``floor + min(k * rho / (1-rho), w_max)``.

    This curve is explanatory, not the deployment predictor. For ``rho`` near
    or above 1 the Kingman term diverges, so the finite-buffer ceiling applies.
    """
    rho = float(rho)
    if rho >= 0.999:
        return float(floor) + float(w_max)
    return float(floor) + min(float(k) * rho / max(1.0 - rho, 1e-12), float(w_max))


def _pchip_endpoint(h0: float, h1: float, d0: float, d1: float) -> float:
    m = ((2.0 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if m * d0 <= 0.0:
        return 0.0
    if d0 * d1 < 0.0 and abs(m) > abs(3.0 * d0):
        return 3.0 * d0
    return m


def _pchip_slopes(x: Sequence[float], y: Sequence[float]) -> List[float]:
    """Fritsch-Carlson/PCHIP node derivatives preserving monotone shape."""
    n = len(x)
    if n == 1:
        return [0.0]
    h = [x[i + 1] - x[i] for i in range(n - 1)]
    d = [(y[i + 1] - y[i]) / h[i] for i in range(n - 1)]
    if n == 2:
        return [d[0], d[0]]

    m = [0.0] * n
    m[0] = _pchip_endpoint(h[0], h[1], d[0], d[1])
    m[-1] = _pchip_endpoint(h[-1], h[-2], d[-1], d[-2])
    for i in range(1, n - 1):
        if d[i - 1] == 0.0 or d[i] == 0.0 or d[i - 1] * d[i] < 0.0:
            m[i] = 0.0
        else:
            w1 = 2.0 * h[i] + h[i - 1]
            w2 = h[i] + 2.0 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    return m


class MonotonePchip:
    """Piecewise cubic Hermite interpolation.

    The caller is responsible for passing nondecreasing ``ys`` when a monotone
    curve is required. Outside the measured domain the value is clamped; the
    public ``LinkModelV2`` API rejects outside-domain calls by default.
    """

    def __init__(self, xs: Iterable[float], ys: Iterable[float]):
        pairs = sorted((float(x), float(y)) for x, y in zip(xs, ys))
        if not pairs:
            raise ValueError("PCHIP needs at least one point")
        for (a, _), (b, _) in zip(pairs, pairs[1:]):
            if not b > a:
                raise ValueError("PCHIP x values must be strictly increasing")
        self.x = [x for x, _y in pairs]
        self.y = [y for _x, y in pairs]
        self.m = _pchip_slopes(self.x, self.y)

    def __call__(self, t: float) -> float:
        t = float(t)
        x, y, m = self.x, self.y, self.m
        if len(x) == 1:
            return y[0]
        if t <= x[0]:
            return y[0]
        if t >= x[-1]:
            return y[-1]
        i = bisect.bisect_right(x, t) - 1
        h = x[i + 1] - x[i]
        s = (t - x[i]) / h
        h00 = 2.0 * s**3 - 3.0 * s**2 + 1.0
        h10 = s**3 - 2.0 * s**2 + s
        h01 = -2.0 * s**3 + 3.0 * s**2
        h11 = s**3 - s**2
        return h00 * y[i] + h10 * h * m[i] + h01 * y[i + 1] + h11 * h * m[i + 1]


class LinkModelV2:
    """Runtime wrapper around ``results/phase-L/link_model_v2_fit.json``."""

    def __init__(self, fit: Dict):
        self.fit = fit
        self._delay: Dict[str, MonotonePchip] = {}
        self._loss: Dict[str, MonotonePchip] = {}
        self._sigma: Dict[str, MonotonePchip] = {}
        for key, link in fit.get("links", {}).items():
            self._delay[key] = MonotonePchip(link["rho_train"], link["delay_train"])
            self._loss[key] = MonotonePchip(link["rho_train"], link["loss_train"])
            self._sigma[key] = MonotonePchip(link["rho_train"], link["sigma_train"])

    @classmethod
    def load(cls, path: str) -> "LinkModelV2":
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    @staticmethod
    def key(mode: str, bw: float, q: int) -> str:
        return "%s|%g|%d" % (mode, float(bw), int(q))

    def _link(self, mode: str, bw: float, q: int) -> Dict:
        key = self.key(mode, bw, q)
        try:
            return self.fit["links"][key]
        except KeyError as exc:
            raise KeyError("unknown link_model_v2 key %s" % key) from exc

    def domain(self, mode: str, bw: float, q: int) -> Tuple[float, float]:
        dom = self._link(mode, bw, q)["domain"]
        return float(dom[0]), float(dom[1])

    def _check_domain(self, mode: str, bw: float, q: int, rho: float, strict: bool) -> None:
        lo, hi = self.domain(mode, bw, q)
        if strict and not (lo <= float(rho) <= hi):
            raise ValueError(
                "rho=%.4f outside measured domain [%.2f, %.2f] for %s|%g|%d"
                % (float(rho), lo, hi, mode, float(bw), int(q))
            )

    def predict_delay(self, mode: str, bw: float, q: int, rho: float, strict: bool = True) -> float:
        self._check_domain(mode, bw, q, rho, strict)
        return float(self._delay[self.key(mode, bw, q)](rho))

    def predict_loss(self, mode: str, bw: float, q: int, rho: float, strict: bool = True) -> float:
        self._check_domain(mode, bw, q, rho, strict)
        return max(0.0, min(1.0, float(self._loss[self.key(mode, bw, q)](rho))))

    def sigma(self, mode: str, bw: float, q: int, rho: float, strict: bool = True) -> float:
        self._check_domain(mode, bw, q, rho, strict)
        return max(1e-6, float(self._sigma[self.key(mode, bw, q)](rho)))

    def explain(self, mode: str, bw: float, q: int, rho: float) -> Dict[str, float]:
        params = self._link(mode, bw, q)["kingman"]
        return {
            "delay_ms": kingman_ceiling(rho, params["K"], params["w_max"], params["floor"]),
            **params,
        }

    def irreducible_floor_ms(self, mode: str, bw: float, q: int) -> float:
        return float(self._link(mode, bw, q)["sigma_schedule"])

    def model_efficiency(self, mode: str, bw: float, q: int) -> float:
        link = self._link(mode, bw, q)
        return float(link["sigma_schedule"]) / max(float(link["resid_sd"]), 1e-9)


def is_non_decreasing(values: Sequence[float], tol: float = 0.0) -> bool:
    return all(float(a) <= float(b) + float(tol) for a, b in zip(values, values[1:]))


def finite_or_none(value: float) -> float | None:
    value = float(value)
    return value if math.isfinite(value) else None

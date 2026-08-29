#!/usr/bin/env python3
"""Phase G: packet-level rho(t) modulation with independent sigma and tau.

Unlike ``flow_engine.py``, this module has no synthetic flow population and
therefore no M/G/infinity shot-noise coupling.  A normalized AR(1) process
defines the offered load; packet quantization and pacing are explicit,
separate steps.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

HEADROOM_MIN = 5.0
DT_TAU_RATIO = 10.0


@dataclass(frozen=True)
class ModulatorConfig:
    cap_bps: float
    rho_bar: float
    sigma: float
    tau_s: float
    dt_s: float = 0.05
    mode: str = "poisson"
    payload_bits: int = 1400 * 8
    rho_max: float = 0.995
    rho_min: float = 0.0

    def __post_init__(self) -> None:
        if self.dt_s > self.tau_s / DT_TAU_RATIO:
            raise ValueError(
                f"dt_s={self.dt_s} > tau/{DT_TAU_RATIO:.0f}="
                f"{self.tau_s / DT_TAU_RATIO:.4f}: modulation step is too "
                "coarse to resolve tau"
            )
        if self.sigma_headroom < HEADROOM_MIN:
            raise ValueError(
                f"sigma_headroom={self.sigma_headroom:.2f} < {HEADROOM_MIN}: "
                f"sigma={self.sigma} is below quantization floor "
                f"{self.sigma_quant_floor:.5f} at dt={self.dt_s}; "
                f"need tau >= {self.tau_floor_packet_s:.3f} s or a smaller payload"
            )

    @property
    def phi(self) -> float:
        return float(np.exp(-self.dt_s / self.tau_s))

    @property
    def sigma_quant_floor(self) -> float:
        """Absolute standard-deviation floor in rho units (no rho_bar factor)."""
        return float(
            self.payload_bits / (self.cap_bps * self.dt_s * np.sqrt(12.0))
        )

    @property
    def sigma_headroom(self) -> float:
        return float(self.sigma / self.sigma_quant_floor)

    @property
    def tau_floor_packet_s(self) -> float:
        k = DT_TAU_RATIO * HEADROOM_MIN / np.sqrt(12.0)
        return float(k * self.payload_bits / (self.cap_bps * self.sigma))

    @property
    def n_pkt_per_window(self) -> float:
        return float(
            self.rho_bar * self.cap_bps * self.dt_s / self.payload_bits
        )


def modulate(
    cfg: ModulatorConfig, n_steps: int, rng: np.random.Generator
) -> dict[str, object]:
    """Generate normalized AR(1) offered load and its diagnostics."""
    phi = cfg.phi
    innovation_scale = np.sqrt(1.0 - phi * phi)

    u = np.empty(n_steps)
    u[0] = rng.standard_normal()
    eps = rng.standard_normal(n_steps)
    for index in range(1, n_steps):
        u[index] = phi * u[index - 1] + innovation_scale * eps[index]

    rho_raw = cfg.rho_bar + cfg.sigma * u
    rho = np.clip(rho_raw, cfg.rho_min, cfg.rho_max)
    clip_fraction = float(
        np.mean((rho_raw < cfg.rho_min) | (rho_raw > cfg.rho_max))
    )

    return {
        "rho_offered": rho,
        "rho_unclipped": rho_raw,
        "clip_fraction": clip_fraction,
        "sigma_realized": float(rho.std(ddof=1)),
        "sigma_target": cfg.sigma,
        "sigma_quant_floor": cfg.sigma_quant_floor,
        "sigma_headroom": cfg.sigma_headroom,
        "tau_floor_packet_s": cfg.tau_floor_packet_s,
        "n_pkt_per_window": cfg.n_pkt_per_window,
        "phi": phi,
    }


def quantize(rho_series: np.ndarray, cfg: ModulatorConfig) -> dict[str, object]:
    """Convert offered load to an integer packet count in each time window."""
    wanted = rho_series * cfg.cap_bps * cfg.dt_s / cfg.payload_bits
    sent = np.round(wanted)
    rho_measured = sent * cfg.payload_bits / (cfg.cap_bps * cfg.dt_s)
    return {
        "n_pkt": sent,
        "rho_measured": rho_measured,
        "nugget_var_theory": float(cfg.sigma_quant_floor**2),
        "signal_fraction_theory": float(
            cfg.sigma**2 / (cfg.sigma**2 + cfg.sigma_quant_floor**2)
        ),
    }


def pace(
    rho_series: np.ndarray, cfg: ModulatorConfig, rng: np.random.Generator
) -> np.ndarray:
    """Convert a rho series into packet send times for one traffic mode."""
    times: list[np.ndarray] = []
    t0 = 0.0
    for rho in rho_series:
        rate_pps = rho * cfg.cap_bps / cfg.payload_bits
        if rate_pps <= 0:
            t0 += cfg.dt_s
            continue
        n_packets = int(round(rate_pps * cfg.dt_s))
        if n_packets <= 0:
            t0 += cfg.dt_s
            continue

        if cfg.mode == "cbr":
            offsets = (np.arange(n_packets) + 0.5) / n_packets * cfg.dt_s
        elif cfg.mode == "poisson":
            offsets = np.sort(rng.uniform(0.0, cfg.dt_s, n_packets))
        elif cfg.mode == "h2":
            fast = rng.random(n_packets) < 0.1
            gaps = np.where(
                fast,
                rng.exponential(0.1 / rate_pps, n_packets),
                rng.exponential(1.9 / rate_pps, n_packets),
            )
            offsets = np.cumsum(gaps)
            offsets = offsets[offsets < cfg.dt_s]
        else:
            raise ValueError(f"unsupported mode: {cfg.mode}")

        times.append(t0 + offsets)
        t0 += cfg.dt_s
    return np.concatenate(times) if times else np.array([])

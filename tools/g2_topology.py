#!/usr/bin/env python3
"""Topology-derived algebra for the physically wireable Phase G.2 omega axis.

All topology, path, and capacity information comes from ``topology_v7``.
The shared path amplitude is expressed in bit/s, so one path process has the
same amplitude on every link it traverses.
"""
from __future__ import annotations

import itertools

import numpy as np

from twin import topology_v7 as T7


LINKS = tuple(T7.LINK_NAMES)
PATHS = tuple(T7.PATH_NAMES)
IDX = {link: index for index, link in enumerate(LINKS)}
CAP_BPS = np.asarray([T7.LINKS[link][0] for link in LINKS], dtype=float) * 1e6

INCIDENCE = np.zeros((len(LINKS), len(PATHS)), dtype=float)
for path_index, path in enumerate(PATHS):
    for link in T7.PATHS[path]:
        INCIDENCE[IDX[link], path_index] = 1.0

DEGREE = INCIDENCE.sum(axis=1)
if np.any(DEGREE <= 0.0):
    raise RuntimeError("topology contains a link unused by every path")
SHARED = INCIDENCE @ INCIDENCE.T
K_TOPO = SHARED / np.sqrt(np.outer(DEGREE, DEGREE))
PAIRS = tuple(itertools.combinations(range(len(LINKS)), 2))
K_VEC = np.asarray([K_TOPO[i, j] for i, j in PAIRS], dtype=float)
SUM_K2 = float(K_VEC @ K_VEC)
STRUCTURED_PAIRS = tuple(
    (LINKS[i], LINKS[j]) for i, j in PAIRS if K_TOPO[i, j] > 0.0
)
NULL_PAIRS = tuple(
    (LINKS[i], LINKS[j]) for i, j in PAIRS if K_TOPO[i, j] == 0.0
)


def sigma_per_link(a0: float) -> np.ndarray:
    """Return ``sigma_l=a0*sqrt(d_l)/C_l``, invariant in omega."""
    if a0 < 0.0:
        raise ValueError("a0 must be non-negative")
    return float(a0) * np.sqrt(DEGREE) / CAP_BPS


def a0_from_sigma_at(link: str, sigma: float) -> float:
    """Invert the per-link relation at one explicitly named reference link."""
    if link not in IDX:
        raise ValueError("unknown link %r" % link)
    if sigma < 0.0:
        raise ValueError("sigma must be non-negative")
    index = IDX[link]
    return float(sigma * CAP_BPS[index] / np.sqrt(DEGREE[index]))


def design_covariance(a0: float, omega: float) -> np.ndarray:
    """Return the closed-form covariance of the path-plus-link generator."""
    if not 0.0 <= omega <= 1.0:
        raise ValueError("omega must be in [0, 1]")
    a = float(a0) * np.sqrt(omega)
    shared = a**2 * SHARED / np.outer(CAP_BPS, CAP_BPS)
    independent = (
        (1.0 - omega) * float(a0) ** 2 * DEGREE / CAP_BPS**2
    )
    return shared + np.diag(independent)


def design_correlation(a0: float, omega: float) -> np.ndarray:
    covariance = design_covariance(a0, omega)
    sigma = np.sqrt(np.diag(covariance))
    if np.any(sigma <= 0.0):
        raise ValueError("a0 must be positive to define correlation")
    return covariance / np.outer(sigma, sigma)


def estimate_omega(correlation: np.ndarray) -> float:
    """Estimate omega by the one-parameter LS contrast ``<r,k>/<k,k>``.

    Null pairs remain explicit negative controls, but have zero numerical
    weight in this contrast because their topology coefficient is zero.
    """
    matrix = np.asarray(correlation, dtype=float)
    if matrix.shape != (len(LINKS), len(LINKS)):
        raise ValueError("correlation must have shape (%d, %d)" % (len(LINKS), len(LINKS)))
    r_vector = np.asarray([matrix[i, j] for i, j in PAIRS], dtype=float)
    return float((r_vector @ K_VEC) / SUM_K2)


def simulate(
    a0: float,
    omega: float,
    tau_s: float,
    dt_s: float,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate one ``(8,n)`` trace from path and independent-link AR(1)s."""
    if tau_s <= 0.0 or dt_s <= 0.0 or n < 2:
        raise ValueError("tau_s, dt_s, and n must be positive (n >= 2)")
    if not 0.0 <= omega <= 1.0:
        raise ValueError("omega must be in [0, 1]")
    phi = float(np.exp(-dt_s / tau_s))
    innovation_scale = float(np.sqrt(1.0 - phi * phi))

    def ar1(n_processes: int) -> np.ndarray:
        values = np.empty((n_processes, n), dtype=float)
        values[:, 0] = rng.standard_normal(n_processes)
        for index in range(1, n):
            values[:, index] = (
                phi * values[:, index - 1]
                + innovation_scale * rng.standard_normal(n_processes)
            )
        return values

    path_scale = float(a0) * np.sqrt(omega)
    link_scale = (
        float(a0) * np.sqrt((1.0 - omega) * DEGREE) / CAP_BPS
    )
    path_component = path_scale * (INCIDENCE @ ar1(len(PATHS)))
    path_component = path_component / CAP_BPS[:, None]
    return path_component + link_scale[:, None] * ar1(len(LINKS))


def simulate_correlations(
    a0: float,
    omega: float,
    tau_s: float,
    dt_s: float,
    n: int,
    n_replicates: int,
    rng: np.random.Generator,
    *,
    keep_link: int | None = None,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Batch simulation with online moments, preserving path/link wiring.

    Returns one correlation matrix per replicate. If ``keep_link`` is given,
    that link's full trace is retained for the tau diagnostic only.
    """
    if n_replicates < 1:
        raise ValueError("n_replicates must be positive")
    if keep_link is not None and not 0 <= keep_link < len(LINKS):
        raise ValueError("keep_link is outside the link index")
    if tau_s <= 0.0 or dt_s <= 0.0 or n < 2:
        raise ValueError("tau_s, dt_s, and n must be positive (n >= 2)")
    if not 0.0 <= omega <= 1.0:
        raise ValueError("omega must be in [0, 1]")

    phi = float(np.exp(-dt_s / tau_s))
    innovation_scale = float(np.sqrt(1.0 - phi * phi))
    paths = rng.standard_normal((n_replicates, len(PATHS)))
    independent = rng.standard_normal((n_replicates, len(LINKS)))
    path_scale = float(a0) * np.sqrt(omega)
    link_scale = (
        float(a0) * np.sqrt((1.0 - omega) * DEGREE) / CAP_BPS
    )

    sums = np.zeros((n_replicates, len(LINKS)), dtype=float)
    cross = np.zeros((n_replicates, len(LINKS), len(LINKS)), dtype=float)
    traces = (
        np.empty((n_replicates, n), dtype=float)
        if keep_link is not None
        else None
    )
    for index in range(n):
        if index:
            paths = (
                phi * paths
                + innovation_scale * rng.standard_normal(paths.shape)
            )
            independent = (
                phi * independent
                + innovation_scale * rng.standard_normal(independent.shape)
            )
        values = path_scale * (paths @ INCIDENCE.T) / CAP_BPS
        values += independent * link_scale
        sums += values
        cross += values[:, :, None] * values[:, None, :]
        if traces is not None:
            traces[:, index] = values[:, keep_link]

    centered = cross - sums[:, :, None] * sums[:, None, :] / float(n)
    variances = np.diagonal(centered, axis1=1, axis2=2)
    denominator = np.sqrt(variances[:, :, None] * variances[:, None, :])
    correlations = np.divide(
        centered,
        denominator,
        out=np.zeros_like(centered),
        where=denominator > 0.0,
    )
    diagonal = np.arange(len(LINKS))
    correlations[:, diagonal, diagonal] = 1.0
    return correlations, traces


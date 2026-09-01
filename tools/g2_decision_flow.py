#!/usr/bin/env python3
"""Trace the G.2 omega axis into a pairwise decision quantity.

The central closed-form result is deliberately a negative result: with one
common AR(1) time scale and a linear contrast, omega changes decision variance
but cancels exactly from the sign-flip probability.  The tool then evaluates
three mechanisms that can break that cancellation.

This is analytic/synthetic only.  It starts no Mininet process and creates no
RAW network data.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

import numpy as np

from tools.g2_feasibility_omega import (
    DEFAULT_G1_CERTIFICATE,
    DEFAULT_G1_MEASUREMENT,
    load_g1_contract,
)
from tools.g2_topology import (
    CAP_BPS,
    DEGREE,
    INCIDENCE,
    LINKS,
    a0_from_sigma_at,
    sigma_per_link,
)
from twin import topology_v7 as T7
from twin.cost_v2 import CostV2, RHO_MAX, RHO_MIN


PATH_LINKS = {path: tuple(T7.PATHS[path]) for path in T7.PATH_NAMES}
IDX = {link: index for index, link in enumerate(LINKS)}
PATH_IDX = {path: index for index, path in enumerate(T7.PATH_NAMES)}

SIGMA_REF = 0.030348837209302317
RHO_BAR_UNIFORM = 0.857
OMEGA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
DT_S = 0.2
Z_S = 2.0
TAU_G_S = 3.0
KAPPA_GRID = (1.0, 10.0)
MODE = "poisson"
W_LOSS = 5000.0

GATE_EXACT = 1e-12
GATE_NUGGET_NEGLIGIBLE = 0.01
GATE_TWO_TIMESCALES_FIRE = 0.10


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


def contrast(path: str, other: str, gamma: np.ndarray) -> np.ndarray:
    """Return the link-level linear contrast for two paths."""
    sensitivity = np.asarray(gamma, dtype=float)
    if sensitivity.shape != (len(LINKS),):
        raise ValueError("gamma must contain one sensitivity per link")
    values = np.zeros(len(LINKS), dtype=float)
    for link in PATH_LINKS[path]:
        values[IDX[link]] += sensitivity[IDX[link]]
    for link in PATH_LINKS[other]:
        values[IDX[link]] -= sensitivity[IDX[link]]
    return values


def quad_forms(c_vector: np.ndarray, a0: float) -> tuple[float, float]:
    """Return path-shared and link-private decision variance coefficients."""
    path_covariance = (
        a0**2 * (INCIDENCE @ INCIDENCE.T) / np.outer(CAP_BPS, CAP_BPS)
    )
    link_covariance = np.diag(a0**2 * DEGREE / CAP_BPS**2)
    return (
        float(c_vector @ path_covariance @ c_vector),
        float(c_vector @ link_covariance @ c_vector),
    )


def p_flip(
    omega: float,
    path_variance: float,
    link_variance: float,
    phi_path: float,
    phi_link: float,
    nugget: float = 0.0,
) -> float:
    """Return the Sheppard sign-disagreement probability."""
    variance = omega * path_variance + (1.0 - omega) * link_variance
    lag_covariance = (
        omega * path_variance * phi_path
        + (1.0 - omega) * link_variance * phi_link
    )
    if variance <= 0.0 or nugget < 0.0:
        raise ValueError("decision variance must be positive and nugget non-negative")
    correlation = lag_covariance / np.sqrt(variance * (variance + nugget))
    return float(np.arccos(np.clip(correlation, -1.0, 1.0)) / np.pi)


def simulate_two_tau(
    a0: float,
    omega: float,
    tau_path_s: float,
    tau_link_s: float,
    dt_s: float,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate a physical path-rate/link-private trace with two time scales."""
    if tau_path_s <= 0.0 or tau_link_s <= 0.0 or dt_s <= 0.0 or n < 2:
        raise ValueError("time scales and dt must be positive; n must be >=2")

    def ar1(n_processes: int, tau_s: float) -> np.ndarray:
        phi = float(np.exp(-dt_s / tau_s))
        innovation_scale = float(np.sqrt(1.0 - phi * phi))
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
    path_component = (
        path_scale * (INCIDENCE @ ar1(len(PATH_LINKS), tau_path_s))
        / CAP_BPS[:, None]
    )
    return path_component + link_scale[:, None] * ar1(len(LINKS), tau_link_s)


def load_nugget_vector(
    certificate_path: Path = DEFAULT_G1_CERTIFICATE,
    measurement_path: Path = DEFAULT_G1_MEASUREMENT,
) -> tuple[np.ndarray, dict[str, object]]:
    """Load per-link independent-round variance after verifying the G.1 pin."""
    _sigma_min, provenance = load_g1_contract(certificate_path, measurement_path)
    measurement = json.loads(measurement_path.read_text(encoding="utf-8"))
    per_link: dict[str, float] = {}
    for run in measurement["runs"]:
        for row in run["links"]:
            link = str(row["link"])
            value = float(row["v_pack_future_independent_round"])
            per_link[link] = max(per_link.get(link, 0.0), value)
    missing = set(LINKS) - set(per_link)
    if missing:
        raise SystemExit("REFUSED: G.1 nugget vector misses %s" % sorted(missing))
    provenance = {
        **provenance,
        "nugget_source_field": "v_pack_future_independent_round",
        "nugget_reduction_across_runs": "per_link_max",
    }
    return np.asarray([per_link[link] for link in LINKS]), provenance


def _flip_from_series(values: np.ndarray, lag: int) -> float:
    if values.ndim != 1 or not 0 < lag < values.size:
        raise ValueError("values must be 1-D and lag inside the series")
    return float(np.mean(np.sign(values[lag:]) != np.sign(values[:-lag])))


def _nonlinear_profile(
    a0: float,
    mean_load: np.ndarray,
    mc_n: int,
    rng: np.random.Generator,
) -> dict[str, object]:
    """Evaluate current CostV2 after removing the deterministic base margin."""
    model = CostV2(strict_reliable=False)
    lag = int(round(Z_S / DT_S))
    mean_dict = dict(zip(LINKS, mean_load.tolist()))
    baseline_cost = model.tables(mean_dict, MODE, W_LOSS)[2]
    baseline_margin = float(
        baseline_cost[PATH_IDX["P1"]] - baseline_cost[PATH_IDX["P2"]]
    )
    c_vector = contrast("P1", "P2", np.ones(len(LINKS)))
    rows = []
    for omega in OMEGA_GRID:
        perturbation = simulate_two_tau(
            a0, omega, TAU_G_S, TAU_G_S, DT_S, mc_n, rng
        )
        offered_unclipped = mean_load[:, None] + perturbation
        offered = np.clip(offered_unclipped, RHO_MIN, RHO_MAX)
        clipping_fraction = float(np.mean(offered != offered_unclipped))
        _delay, _loss, cost = model.tables_batch(offered.T, MODE, W_LOSS)
        nonlinear_margin = (
            cost[:, PATH_IDX["P1"]]
            - cost[:, PATH_IDX["P2"]]
            - baseline_margin
        )
        raw_margin = (
            cost[:, PATH_IDX["P1"]] - cost[:, PATH_IDX["P2"]]
        )
        linear_margin = c_vector @ perturbation
        rows.append(
            {
                "omega": omega,
                "p_flip_linear_centered": _flip_from_series(linear_margin, lag),
                "p_flip_cost_v2_centered": _flip_from_series(nonlinear_margin, lag),
                "p_flip_cost_v2_raw": _flip_from_series(raw_margin, lag),
                "clipping_fraction": clipping_fraction,
            }
        )
    centered = [row["p_flip_cost_v2_centered"] for row in rows]
    raw = [row["p_flip_cost_v2_raw"] for row in rows]
    return {
        "mode": MODE,
        "w_loss": W_LOSS,
        "mean_load": dict(zip(LINKS, mean_load.tolist())),
        "baseline_margin_cost": baseline_margin,
        "rows": rows,
        "centered_spread": max(centered) - min(centered),
        "raw_spread": max(raw) - min(raw),
        "max_clipping_fraction": max(row["clipping_fraction"] for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--mc-n", type=int, default=40000)
    parser.add_argument("--g1-certificate", default=str(DEFAULT_G1_CERTIFICATE))
    parser.add_argument("--g1-measurement", default=str(DEFAULT_G1_MEASUREMENT))
    parser.add_argument(
        "--g2-feasibility",
        default="results/SMOKE/phase-G/g2_feasibility_omega.json",
    )
    args = parser.parse_args()
    if args.mc_n <= int(round(Z_S / DT_S)):
        raise SystemExit("REFUSED: mc-n is too short for the signed lag")

    g2_path = Path(args.g2_feasibility)
    g2 = json.loads(g2_path.read_text(encoding="utf-8"))
    if g2.get("schema") != "dt4n.phase_g.g2_feasibility_omega.v1":
        raise SystemExit("REFUSED: unsupported G.2 feasibility schema")
    if not any(
        cell["feasible"]
        and cell["quant_mode"] == "independent_round"
        and abs(float(cell["rho_bar"]) - RHO_BAR_UNIFORM) <= 1e-12
        and abs(float(cell["sigma_ref_at_uA"]) - SIGMA_REF) <= 1e-12
        for cell in g2["cells"]
    ):
        raise SystemExit("REFUSED: signed anchor is absent from G.2 feasibility")

    nugget_vector, g1_provenance = load_nugget_vector(
        Path(args.g1_certificate), Path(args.g1_measurement)
    )
    a0 = a0_from_sigma_at("uA", SIGMA_REF)
    sigma = sigma_per_link(a0)
    gamma = np.ones(len(LINKS), dtype=float)
    checks: list[dict[str, object]] = []

    def record(
        check_id, description, value, gate, passed=True, *, required=True, **extra
    ):
        checks.append(
            {
                "id": check_id,
                "description": description,
                "value": value,
                "gate": gate,
                "required": required,
                "verdict": (
                    "PASS" if passed else "FAIL"
                ) if required else "REPORTED",
                **extra,
            }
        )

    cancellation = {}
    for path, other in itertools.combinations(PATH_LINKS, 2):
        shared = sorted(set(PATH_LINKS[path]) & set(PATH_LINKS[other]))
        c_vector = contrast(path, other, gamma)
        cancellation["%s-%s" % (path, other)] = {
            "shared_links": shared,
            "c_on_shared": [float(c_vector[IDX[link]]) for link in shared],
            "n_nonzero": int(np.count_nonzero(c_vector)),
        }
    cancellation_error = max(
        (
            abs(value)
            for row in cancellation.values()
            for value in row["c_on_shared"]
        ),
        default=0.0,
    )
    record(
        "DEC-0", "shared links cancel from every pairwise contrast",
        cancellation_error, GATE_EXACT, cancellation_error <= GATE_EXACT,
        pairs=cancellation,
    )

    phi = float(np.exp(-Z_S / TAU_G_S))
    single_tau_rows = {}
    single_tau_spread = 0.0
    for path, other in itertools.combinations(PATH_LINKS, 2):
        c_vector = contrast(path, other, gamma)
        path_variance, link_variance = quad_forms(c_vector, a0)
        values = [
            p_flip(omega, path_variance, link_variance, phi, phi)
            for omega in OMEGA_GRID
        ]
        spread = max(values) - min(values)
        single_tau_spread = max(single_tau_spread, spread)
        single_tau_rows["%s-%s" % (path, other)] = {
            "path_variance_coefficient": path_variance,
            "link_variance_coefficient": link_variance,
            "var_ratio_omega1_over_omega0": path_variance / link_variance,
            "p_flip": values,
            "spread": spread,
        }
    record(
        "DEC-1", "one common tau, linear contrast, no noise: omega cancels",
        single_tau_spread, GATE_EXACT, single_tau_spread <= GATE_EXACT,
        by_pair=single_tau_rows,
    )

    c_vector = contrast("P1", "P2", gamma)
    path_variance, link_variance = quad_forms(c_vector, a0)
    decision_nugget = float(np.sum(c_vector**2 * nugget_vector))
    nugget_rows = {}
    for z_over_tau in (0.2, 1.0):
        decay = float(np.exp(-z_over_tau))
        values = [
            p_flip(
                omega,
                path_variance,
                link_variance,
                decay,
                decay,
                nugget=decision_nugget,
            )
            for omega in OMEGA_GRID
        ]
        nugget_rows["z_over_tau=%g" % z_over_tau] = {
            "p_flip": values,
            "spread": max(values) - min(values),
        }
    nugget_spread = max(row["spread"] for row in nugget_rows.values())
    record(
        "DEC-2", "G.1 per-link independent-round nugget effect",
        nugget_spread, GATE_NUGGET_NEGLIGIBLE,
        nugget_spread <= GATE_NUGGET_NEGLIGIBLE,
        note="upper-bound gate: PASS means this mechanism is negligible",
        nugget_variance_per_link=dict(zip(LINKS, nugget_vector.tolist())),
        decision_nugget=decision_nugget,
        link_decision_variance_over_nugget=link_variance / decision_nugget,
        detail=nugget_rows,
    )

    two_tau_rows = {}
    for kappa in KAPPA_GRID:
        cases = ((TAU_G_S * kappa, TAU_G_S),)
        if kappa != 1.0:
            cases += ((TAU_G_S, TAU_G_S * kappa),)
        for tau_path, tau_link in cases:
            phi_path = float(np.exp(-Z_S / tau_path))
            phi_link = float(np.exp(-Z_S / tau_link))
            values = [
                p_flip(
                    omega,
                    path_variance,
                    link_variance,
                    phi_path,
                    phi_link,
                )
                for omega in OMEGA_GRID
            ]
            two_tau_rows["tau_p=%g,tau_g=%g" % (tau_path, tau_link)] = {
                "kappa": tau_path / tau_link,
                "phi_path": phi_path,
                "phi_link": phi_link,
                "p_flip": values,
                "spread": max(values) - min(values),
                "monotone": bool(
                    np.all(np.diff(values) >= -GATE_EXACT)
                    or np.all(np.diff(values) <= GATE_EXACT)
                ),
            }
    two_tau_spread = max(row["spread"] for row in two_tau_rows.values())
    kappa_one_spread = max(
        row["spread"] for row in two_tau_rows.values()
        if abs(float(row["kappa"]) - 1.0) <= GATE_EXACT
    )
    record(
        "DEC-3", "two time scales make omega select inherited persistence",
        two_tau_spread, ">=%.2f" % GATE_TWO_TIMESCALES_FIRE,
        two_tau_spread >= GATE_TWO_TIMESCALES_FIRE,
        detail=two_tau_rows,
    )
    record(
        "DEC-3-NC", "kappa=1 must recover the exactly flat omega curve",
        kappa_one_spread, GATE_EXACT, kappa_one_spread <= GATE_EXACT,
    )

    rng = np.random.default_rng(20260904)
    uniform = np.full(len(LINKS), RHO_BAR_UNIFORM, dtype=float)
    core_near_transition = uniform.copy()
    for link in ("ac", "ad", "bc", "bd"):
        core_near_transition[IDX[link]] = 0.90
    nonlinear_profiles = {
        "uniform_anchor": _nonlinear_profile(a0, uniform, args.mc_n, rng),
        "core_0p90": _nonlinear_profile(
            a0, core_near_transition, args.mc_n, rng
        ),
    }
    nonlinear_spread = max(
        profile["centered_spread"] for profile in nonlinear_profiles.values()
    )
    mc_se_single = float(np.sqrt(0.25 / args.mc_n))
    mc_se_spread = float(np.sqrt(0.5 / args.mc_n))
    record(
        "DEC-4", "current CostV2 nonlinearity after baseline-margin removal",
        nonlinear_spread, "reported only", required=False,
        mc_se_single_probability_upper=mc_se_single,
        mc_se_spread_upper=mc_se_spread,
        model="twin.cost_v2.CostV2",
        profiles=nonlinear_profiles,
    )

    overall = all(
        not check["required"] or check["verdict"] == "PASS"
        for check in checks
    )
    artifact = {
        "schema": "dt4n.phase_g.g2_decision_flow.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "inputs": {
            "g1_contract": g1_provenance,
            "g2_feasibility": {
                "path": str(g2_path),
                "sha256": sha256(g2_path),
            },
        },
        "sigma_ref_at_uA": SIGMA_REF,
        "a0": a0,
        "sigma_per_link": dict(zip(LINKS, sigma.tolist())),
        "dt_s": DT_S,
        "z_s": Z_S,
        "tau_g_s": TAU_G_S,
        "omega_grid": list(OMEGA_GRID),
        "kappa_grid": list(KAPPA_GRID),
        "mc_n": args.mc_n,
        "checks": checks,
        "conclusion": {
            "omega_is_null_axis_under_single_tau_linear_model": True,
            "dominant_measured_mechanism": "two_timescales",
            "effect_ratio_two_tau_over_nugget": (
                two_tau_spread / nugget_spread if nugget_spread > 0.0 else None
            ),
            "required_design_change": "record tau_p and tau_g; add kappa=tau_p/tau_g",
            "free_negative_control": "kappa=1 predicts an exactly flat omega curve",
            "deferred": "DEC-5: full K=4 argmin error",
        },
        "overall": "PASS" if overall else "FAIL",
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print(
        f"a0={a0:,.0f} sigma_ref(uA)={SIGMA_REF:.8f} "
        f"z={Z_S:g}s tau_g={TAU_G_S:g}s"
    )
    print("\n%-11s %12s  %-8s %s" % ("id", "value", "verdict", "description"))
    for check in checks:
        print("%-11s %12.6f  %-8s %s" % (
            check["id"], check["value"], check["verdict"], check["description"]
        ))
    print("\nDEC-1 P(flip) across omega, common tau:")
    for pair, row in single_tau_rows.items():
        print(
            "  %-5s %s  Var(1)/Var(0)=%.3f"
            % (
                pair,
                " ".join("%.6f" % value for value in row["p_flip"]),
                row["var_ratio_omega1_over_omega0"],
            )
        )
    print("\nDEC-3 P(flip) across omega, two time scales:")
    for case, row in two_tau_rows.items():
        print(
            "  %-22s %s  spread=%.5f"
            % (
                case,
                " ".join("%.5f" % value for value in row["p_flip"]),
                row["spread"],
            )
        )
    print("\nDEC-4 CostV2 (centered nonlinear margin):")
    for name, profile in nonlinear_profiles.items():
        print(
            "  %-20s spread=%.5f raw_spread=%.5f clip_max=%.6f"
            % (
                name,
                profile["centered_spread"],
                profile["raw_spread"],
                profile["max_clipping_fraction"],
            )
        )
    print("\ntwo-timescale/nugget effect ratio = %.1fx" % (
        artifact["conclusion"]["effect_ratio_two_tau_over_nugget"]
    ))
    print("G.2 DECISION FLOW: %s" % artifact["overall"])
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()


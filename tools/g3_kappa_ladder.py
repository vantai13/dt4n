#!/usr/bin/env python3
"""G-A014: analytic kappa ladder and campaign run-time budget for G.3.

This tool is SYNTHETIC_NO_NETWORK.  It reads no RAW data, starts no Mininet
process, and produces no experimental outcome.  It answers one design
question: which time-scale ratio kappa is the cheapest that still gives the
omega axis a preregistered decision effect, and what does the resulting
campaign cost in wall-clock hours?

The pairwise flip algebra is not restated here.  It is imported from
``tools.g2_decision_flow``, the same single source that produced the signed
``DRY-D-PC`` value, so the kappa=10 row of the ladder reproduces that
artifact number by construction rather than by agreement.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np

from tools.g2_decision_flow import contrast, p_flip, quad_forms
from tools.g2_topology import (
    CAP_BPS,
    DEGREE,
    INCIDENCE,
    LINKS,
    estimate_omega,
)
from tools.g3_dryrun import (
    A0,
    DT_S,
    GATE_PC_FLIP_SPREAD,
    OMEGA_GRID,
    SIGMA_REF,
    T_OVER_SLOW_TAU,
    Z_STALE_S,
    ar1,
    mixture_acf,
)

# ---------------------------------------------------------------- constants
TAU_LINK_S = 3.0                       # tau_g stays fixed; only kappa moves
KAPPA_LADDER = (1, 2, 3, 4, 5, 6, 8, 10)
SAFETY_FACTOR = 1.5                    # design margin, fixed before the table
SELECTION_RULE = (
    "smallest kappa on KAPPA_LADDER whose analytic pairwise flip spread is at "
    "least SAFETY_FACTOR * GATE_PC_FLIP_SPREAD"
)
GATE_OMEGA_BIAS = 0.05                 # inherited from 31-prereg-g3
GATE_OMEGA_SD = 0.05                   # inherited from 31-prereg-g3
GATE_KAPPA1_FLAT = 1e-12
MC_SEED = 20260910
MC_REPLICATES = 40
REPLICATES_PRIMARY = 3                 # physical replicates per (regime, omega)
REPLICATES_SYMMETRY = 1
PER_RUN_OVERHEAD_S = 60.0              # burn-in + Mininet setup/teardown
BUDGET_CEILING_HOURS = 24.0            # must leave slack inside the 6-day rule


def git_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() or "unknown"


# ------------------------------------------------------------ margin algebra
def margin_weights(
    path_a: str = "P1", path_b: str = "P2", a0: float = A0
) -> tuple[np.ndarray, float, float]:
    """Return the contrast vector and its path/link decision variances.

    ``quad_forms`` is the signed single source for both quadratic forms; the
    shared link uA cancels inside ``contrast`` exactly as DEC-0 requires.
    """
    c_vector = contrast(path_a, path_b, np.ones(len(LINKS)))
    path_variance, link_variance = quad_forms(c_vector, a0)
    if path_variance <= 0.0 or link_variance <= 0.0:
        raise ValueError("degenerate contrast: a decision variance is non-positive")
    return c_vector, float(path_variance), float(link_variance)


def flip_curve(
    tau_path_s: float,
    tau_link_s: float,
    path_variance: float,
    link_variance: float,
    z_s: float = Z_STALE_S,
) -> tuple[list[float], float]:
    """Return the stale-margin flip probability over the omega grid."""
    if tau_path_s <= 0.0 or tau_link_s <= 0.0 or z_s <= 0.0:
        raise ValueError("time scales and the stale lag must be positive")
    phi_path = float(np.exp(-z_s / tau_path_s))
    phi_link = float(np.exp(-z_s / tau_link_s))
    values = [
        p_flip(omega, path_variance, link_variance, phi_path, phi_link)
        for omega in OMEGA_GRID
    ]
    return values, float(max(values) - min(values))


# ------------------------------------------------------- Monte Carlo control
def omega_roundtrip(
    omega: float,
    tau_path_s: float,
    tau_link_s: float,
    n: int,
    replicates: int,
    seed: int,
    a0: float = A0,
) -> dict[str, object]:
    """Recover omega from simulated link loads; no quantization, no nugget.

    This is a control on the selected regime only.  Packet rounding and the
    measurement path are already exercised by the signed ``DRY-O`` gate and
    are deliberately not re-simulated here.
    """
    if n < 2 or replicates < 1:
        raise ValueError("n must be at least 2 and replicates at least 1")
    path_scale = a0 * np.sqrt(omega) / CAP_BPS
    private_scale = a0 * np.sqrt((1.0 - omega) * DEGREE) / CAP_BPS
    estimates = []
    for offset in range(replicates):
        rng = np.random.default_rng(seed + offset)
        path = ar1(INCIDENCE.shape[1], tau_path_s, n, rng)
        private = ar1(len(LINKS), tau_link_s, n, rng)
        rho = (
            path_scale[:, None] * (INCIDENCE @ path)
            + private_scale[:, None] * private
        )
        if np.any(rho.std(axis=1) <= 0.0):
            raise ValueError("a link has zero load variance; omega is undefined")
        estimates.append(estimate_omega(np.corrcoef(rho)))
    values = np.asarray(estimates, dtype=float)
    return {
        "omega_true": float(omega),
        "omega_hat_median": float(np.median(values)),
        "omega_hat_bias": float(np.median(values) - omega),
        "omega_hat_sd": float(values.std(ddof=1)),
        "replicates": int(replicates),
    }


def mixture_monotonicity_violation(tau_path_s: float, tau_link_s: float) -> float:
    """Largest decrease of the mixture ACF along the omega grid at lags 1--3.

    PC-G2-3 reads the mixture ACF as a monotone function of omega between the
    link endpoint and the path endpoint.  A non-physical value, or any
    decrease along the grid, would make that reading invalid at the selected
    regime, so both are refused here rather than reported as a small number.
    """
    worst = 0.0
    for lag in (1, 2, 3):
        previous = None
        for omega in OMEGA_GRID:
            value = mixture_acf(omega, tau_path_s, tau_link_s, lag)
            if not -1.0 <= value <= 1.0:
                return float("inf")
            if previous is not None and value < previous:
                worst = max(worst, previous - value)
            previous = value
    return float(worst)


# ------------------------------------------------------------------- budget
def campaign_budget(kappa_selected: int) -> dict[str, object]:
    """Wall-clock cost of the amended three-regime campaign at one kappa."""
    if kappa_selected < 1:
        raise ValueError("kappa must be a positive integer")
    tau_pc = TAU_LINK_S * kappa_selected
    t_nc = T_OVER_SLOW_TAU * TAU_LINK_S
    t_pc = T_OVER_SLOW_TAU * max(tau_pc, TAU_LINK_S)
    t_sym = T_OVER_SLOW_TAU * max(TAU_LINK_S, tau_pc)   # inverse (tau_g slow)
    runs_nc = len(OMEGA_GRID) * REPLICATES_PRIMARY
    runs_pc = len(OMEGA_GRID) * REPLICATES_PRIMARY
    runs_sym = len(OMEGA_GRID) * REPLICATES_SYMMETRY
    seconds = (
        runs_nc * (t_nc + PER_RUN_OVERHEAD_S)
        + runs_pc * (t_pc + PER_RUN_OVERHEAD_S)
        + runs_sym * (t_sym + PER_RUN_OVERHEAD_S)
    )
    return {
        "kappa": int(kappa_selected),
        "tau_link_s": TAU_LINK_S,
        "tau_path_pc_s": float(tau_pc),
        "t_run_nc_s": float(t_nc),
        "t_run_pc_s": float(t_pc),
        "t_run_symmetry_s": float(t_sym),
        "runs_nc": runs_nc,
        "runs_pc": runs_pc,
        "runs_symmetry": runs_sym,
        "per_run_overhead_s": PER_RUN_OVERHEAD_S,
        "total_seconds": float(seconds),
        "total_hours": float(seconds / 3600.0),
    }


# --------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--mc-seed", type=int, default=MC_SEED)
    parser.add_argument("--mc-replicates", type=int, default=MC_REPLICATES)
    args = parser.parse_args()
    if args.mc_seed != MC_SEED or args.mc_replicates != MC_REPLICATES:
        raise SystemExit("REFUSED: ladder seed and replicate count are preregistered")

    started = time.time()
    contrast_vector, path_variance, link_variance = margin_weights()
    threshold = SAFETY_FACTOR * GATE_PC_FLIP_SPREAD

    ladder = []
    for kappa in KAPPA_LADDER:
        tau_path = TAU_LINK_S * kappa
        curve, spread = flip_curve(
            tau_path, TAU_LINK_S, path_variance, link_variance
        )
        budget = campaign_budget(kappa)
        ladder.append({
            "kappa": int(kappa),
            "tau_path_s": float(tau_path),
            "t_run_pc_s": budget["t_run_pc_s"],
            "flip_curve": curve,
            "flip_spread": spread,
            "meets_inherited_gate": bool(spread >= GATE_PC_FLIP_SPREAD),
            "meets_selection_threshold": bool(spread >= threshold),
            "campaign_hours": budget["total_hours"],
        })

    eligible = [row for row in ladder if row["meets_selection_threshold"]]
    if not eligible:
        raise SystemExit("REFUSED: no kappa on the ladder meets the design margin")
    selected = min(eligible, key=lambda row: row["kappa"])
    kappa_selected = int(selected["kappa"])
    tau_path_selected = float(selected["tau_path_s"])
    budget = campaign_budget(kappa_selected)

    # KAP-2: kappa=1 must stay exactly flat (quantitative negative control)
    _nc_curve, nc_spread = flip_curve(
        TAU_LINK_S, TAU_LINK_S, path_variance, link_variance
    )

    # KAP-3: omega round trip at the selected regime
    n_pc = int(round(float(budget["t_run_pc_s"]) / DT_S))
    roundtrip = [
        omega_roundtrip(
            omega, tau_path_selected, TAU_LINK_S,
            n_pc, args.mc_replicates, args.mc_seed,
        )
        for omega in OMEGA_GRID
    ]
    max_bias = max(abs(row["omega_hat_bias"]) for row in roundtrip)
    max_sd = max(row["omega_hat_sd"] for row in roundtrip)

    # KAP-4: mixture ACF stays physical and monotone at lags 1..3
    monotonicity_violation = mixture_monotonicity_violation(
        tau_path_selected, TAU_LINK_S
    )

    checks = [
        {"id": "KAP-1", "description": "selected kappa flip spread",
         "value": selected["flip_spread"], "gate": threshold,
         "verdict": "PASS" if selected["flip_spread"] >= threshold else "FAIL"},
        {"id": "KAP-2", "description": "kappa=1 negative control flat",
         "value": nc_spread, "gate": GATE_KAPPA1_FLAT,
         "verdict": "PASS" if nc_spread <= GATE_KAPPA1_FLAT else "FAIL"},
        {"id": "KAP-3a", "description": "omega round-trip max abs median bias",
         "value": max_bias, "gate": GATE_OMEGA_BIAS,
         "verdict": "PASS" if max_bias <= GATE_OMEGA_BIAS else "FAIL"},
        {"id": "KAP-3b", "description": "omega round-trip max sd",
         "value": max_sd, "gate": GATE_OMEGA_SD,
         "verdict": "PASS" if max_sd <= GATE_OMEGA_SD else "FAIL"},
        {"id": "KAP-4", "description": "mixture ACF monotonicity violation",
         "value": monotonicity_violation, "gate": 0.0,
         "verdict": "PASS" if monotonicity_violation <= 0.0 else "FAIL"},
        {"id": "KAP-5", "description": "campaign wall-clock hours",
         "value": budget["total_hours"], "gate": BUDGET_CEILING_HOURS,
         "verdict": "PASS" if budget["total_hours"] <= BUDGET_CEILING_HOURS else "FAIL"},
    ]
    overall = all(check["verdict"] == "PASS" for check in checks)

    artifact = {
        "schema": "dt4n.phase_g.g3_kappa_ladder.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "amendment": "G-A014",
        "prereg": "docs/phase-G/42-amendment-G-A014-certificate-renewal.md",
        "git_hash": git_hash(),
        "elapsed_s": round(time.time() - started, 3),
        "design": {
            "tau_link_s": TAU_LINK_S,
            "kappa_ladder": list(KAPPA_LADDER),
            "omega_grid": list(OMEGA_GRID),
            "z_stale_s": Z_STALE_S,
            "dt_s": DT_S,
            "t_over_slow_tau": T_OVER_SLOW_TAU,
            "selection_rule": SELECTION_RULE,
            "safety_factor": SAFETY_FACTOR,
            "inherited_gate": GATE_PC_FLIP_SPREAD,
            "inherited_gate_source": "DRY-D-PC in docs/phase-G/31a-prereg-g3-dryrun.md",
            "sigma_ref_anchor": SIGMA_REF,
            "a0_bps": A0,
            "contrast": dict(zip(LINKS, contrast_vector.tolist())),
            "path_decision_variance": path_variance,
            "link_decision_variance": link_variance,
            "link_over_path_variance_ratio": link_variance / path_variance,
            "mc_seed": args.mc_seed,
            "mc_replicates": args.mc_replicates,
        },
        "ladder": ladder,
        "selected_kappa": kappa_selected,
        "selected_regimes": {
            "NC": [TAU_LINK_S, TAU_LINK_S],
            "PC": [tau_path_selected, TAU_LINK_S],
            "SYMMETRY": [TAU_LINK_S, tau_path_selected],
        },
        "budget": budget,
        "budget_at_kappa_10": campaign_budget(10),
        "omega_roundtrip": roundtrip,
        "checks": checks,
        "overall": "PASS" if overall else "FAIL",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("kappa | tau_p |   T_pc  | flip spread | campaign h | selected")
    for row in ladder:
        mark = "  <==" if row["kappa"] == kappa_selected else ""
        print("%5d | %5.0f | %6.0fs |   %.5f   |   %6.2f   |%s" % (
            row["kappa"], row["tau_path_s"], row["t_run_pc_s"],
            row["flip_spread"], row["campaign_hours"], mark))
    print()
    for row in roundtrip:
        print("omega %.2f  median %8.4f  bias %8.4f  sd %7.4f" % (
            row["omega_true"], row["omega_hat_median"],
            row["omega_hat_bias"], row["omega_hat_sd"]))
    print()
    for check in checks:
        print("%-7s %14.6f  gate %12.6f  %s  %s" % (
            check["id"], check["value"], check["gate"],
            check["verdict"], check["description"]))
    print("\nG3 KAPPA LADDER: %s" % artifact["overall"])
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()

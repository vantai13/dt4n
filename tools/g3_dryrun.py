#!/usr/bin/env python3
"""NumPy ground-truth dry-run for the preregistered Phase-G G.3 pipeline."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from tools.g1_quant_model import (
    WIRE_BYTES_DEFAULT,
    acf1_predicted_mechanism_a,
)
from tools.g2_decision_flow import contrast, p_flip, quad_forms
from tools.g2_feasibility_omega import (
    DEFAULT_G1_CERTIFICATE,
    DEFAULT_G1_MEASUREMENT,
    load_g1_contract,
)
from tools.g2_topology import (
    CAP_BPS,
    DEGREE,
    INCIDENCE,
    K_TOPO,
    K_VEC,
    LINKS,
    PAIRS,
    SUM_K2,
    a0_from_sigma_at,
    design_correlation,
    design_covariance,
)


SEED = 20260905
SIGMA_REF = 0.030348837209302317
A0 = a0_from_sigma_at("uA", SIGMA_REF)
QUANT_STRESS_SIGMA_REF = 0.020232558139534878
QUANT_STRESS_A0 = a0_from_sigma_at("uA", QUANT_STRESS_SIGMA_REF)
QUANT_STRESS_TAU_S = 30.0
QUANT_STRESS_N = 30_000
QUANT_STRESS_SEED = 20260906
RHO_BAR = 0.857
DT_S = 0.2
OMEGA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
REGIMES = ((3.0, 3.0), (30.0, 3.0))
T_OVER_SLOW_TAU = 200.0
REPLICATES = 16
WIRE_BYTES = WIRE_BYTES_DEFAULT
RHO_MIN = 0.0
RHO_MAX = 0.995
PATH_BASELINE_MULTIPLIER = 3.25
RHO_EPS_TRUE = 0.10
MEASUREMENT_SD_FLOOR = 1e-6
Z_STALE_S = 2.0

GATE_EXACT = 1e-12
GATE_COMPONENT_CLIP = 0.01
GATE_TARGET_CLIP = 0.01
GATE_QUANT_INDEPENDENT_MIN = -0.05
GATE_QUANT_CUMULATIVE_MAX = -0.25
GATE_QUANT_PRED_ERROR = 0.05
GATE_WHITE_ACF1 = 0.10
GATE_RESIDUAL_CORR_ERROR = 0.06
GATE_OMEGA = 0.05
GATE_MIXTURE_ACF = 0.05
GATE_PC_FLIP_SPREAD = 0.10


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


def acf(values: np.ndarray, lag: int = 1) -> float:
    series = np.asarray(values, dtype=float)
    if series.ndim != 1 or not 0 < lag < series.size:
        return float("nan")
    centered = series - series.mean()
    denominator = float(centered @ centered)
    if denominator <= 0.0:
        return float("nan")
    return float(centered[:-lag] @ centered[lag:] / denominator)


def classify_quantization(acf1_value: float) -> str:
    if float(acf1_value) >= GATE_QUANT_INDEPENDENT_MIN:
        return "INDEPENDENT_ROUND"
    if float(acf1_value) <= GATE_QUANT_CUMULATIVE_MAX:
        return "CUMULATIVE"
    return "INCONCLUSIVE"


def quantization_step_packets(
    a0: float,
    omega: float,
    tau_path_s: float,
    tau_link_s: float,
) -> np.ndarray:
    """Per-link SD of adjacent target increments in packet quanta."""
    variance_fraction = (
        omega * (1.0 - np.exp(-DT_S / tau_path_s))
        + (1.0 - omega) * (1.0 - np.exp(-DT_S / tau_link_s))
    )
    sigma_rho = a0 * np.sqrt(DEGREE) / CAP_BPS
    sigma_packets = sigma_rho * CAP_BPS * DT_S / (WIRE_BYTES * 8.0)
    return sigma_packets * np.sqrt(2.0 * variance_fraction)


def omega_batch(correlations: list[np.ndarray]) -> np.ndarray:
    estimates = []
    for matrix in correlations:
        r_vector = np.asarray([matrix[i, j] for i, j in PAIRS])
        estimates.append(float((r_vector @ K_VEC) / SUM_K2))
    return np.asarray(estimates)


def mixture_acf(omega: float, tau_path_s: float, tau_link_s: float, lag: int) -> float:
    return float(
        omega * np.exp(-lag * DT_S / tau_path_s)
        + (1.0 - omega) * np.exp(-lag * DT_S / tau_link_s)
    )


def component_baselines(a0: float = A0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return path bases, private-link bases, and reconstructed mean loads."""
    path_base = np.full(INCIDENCE.shape[1], PATH_BASELINE_MULTIPLIER * a0)
    desired_link_bps = RHO_BAR * CAP_BPS
    private_base = desired_link_bps - INCIDENCE @ path_base
    if np.any(private_base <= 0.0):
        raise ValueError("path baselines leave a non-positive private-link baseline")
    reconstructed = (INCIDENCE @ path_base + private_base) / CAP_BPS
    return path_base, private_base, reconstructed


def _ar1(
    n_processes: int, tau_s: float, n: int, rng: np.random.Generator
) -> np.ndarray:
    phi = float(np.exp(-DT_S / tau_s))
    innovation_scale = float(np.sqrt(1.0 - phi * phi))
    values = np.empty((n_processes, n), dtype=float)
    values[:, 0] = rng.standard_normal(n_processes)
    for index in range(1, n):
        values[:, index] = (
            phi * values[:, index - 1]
            + innovation_scale * rng.standard_normal(n_processes)
        )
    return values


def physical_trace(
    omega: float,
    tau_path_s: float,
    tau_link_s: float,
    n: int,
    rng: np.random.Generator,
    a0: float = A0,
) -> dict[str, object]:
    """Generate nonnegative physical components and aggregate link targets."""
    path_base, private_base, reconstructed = component_baselines(a0)
    path_rate_raw = (
        path_base[:, None]
        + a0 * np.sqrt(omega) * _ar1(len(path_base), tau_path_s, n, rng)
    )
    private_amplitude = a0 * np.sqrt((1.0 - omega) * DEGREE)
    private_rate_raw = (
        private_base[:, None]
        + private_amplitude[:, None] * _ar1(len(LINKS), tau_link_s, n, rng)
    )
    path_rate = np.maximum(path_rate_raw, 0.0)
    private_rate = np.maximum(private_rate_raw, 0.0)
    path_clip = float(np.mean(path_rate != path_rate_raw))
    private_clip = float(np.mean(private_rate != private_rate_raw))
    target_raw = (INCIDENCE @ path_rate + private_rate) / CAP_BPS[:, None]
    target = np.clip(target_raw, RHO_MIN, RHO_MAX)
    target_clip = float(np.mean(target != target_raw))
    return {
        "rho_target": target,
        "component_clip_fraction": max(path_clip, private_clip),
        "path_clip_fraction": path_clip,
        "private_clip_fraction": private_clip,
        "target_clip_fraction": target_clip,
        "reconstructed_mean": reconstructed,
        "path_baseline_bps": path_base,
        "private_baseline_bps": private_base,
    }


def quantize_target(target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    wanted_packets = target * CAP_BPS[:, None] * DT_S / (WIRE_BYTES * 8.0)
    sent_packets = np.round(wanted_packets)
    sent = sent_packets * (WIRE_BYTES * 8.0) / (CAP_BPS[:, None] * DT_S)
    return sent, sent_packets


def quantization_stress(replicates: int) -> dict[str, object]:
    """Exercise the low-sigma, tau=30 cell that invalidates the old abs gate."""
    rng = np.random.default_rng(QUANT_STRESS_SEED)
    independent_acfs = []
    cumulative_acfs = []
    for _replicate in range(replicates):
        trace = physical_trace(
            0.0,
            QUANT_STRESS_TAU_S,
            QUANT_STRESS_TAU_S,
            QUANT_STRESS_N,
            rng,
            a0=QUANT_STRESS_A0,
        )
        target = trace["rho_target"]
        sent, _sent_packets = quantize_target(target)
        independent_acfs.append([
            acf(sent[index] - target[index]) for index in range(len(LINKS))
        ])

        wanted = target * CAP_BPS[:, None] * DT_S / (WIRE_BYTES * 8.0)
        cumulative_total = np.floor(np.cumsum(wanted, axis=1))
        cumulative_packets = np.diff(
            np.concatenate([np.zeros((len(LINKS), 1)), cumulative_total], axis=1),
            axis=1,
        )
        cumulative_error = cumulative_packets - wanted
        cumulative_acfs.append([
            acf(cumulative_error[index]) for index in range(len(LINKS))
        ])

    independent = np.asarray(independent_acfs)
    cumulative = np.asarray(cumulative_acfs)
    observed = np.median(independent, axis=0)
    cumulative_observed = np.median(cumulative, axis=0)
    steps = quantization_step_packets(
        QUANT_STRESS_A0, 0.0, QUANT_STRESS_TAU_S, QUANT_STRESS_TAU_S
    )
    predicted = np.asarray([
        acf1_predicted_mechanism_a(step) for step in steps
    ])
    return {
        "sigma_ref_uA": QUANT_STRESS_SIGMA_REF,
        "a0": QUANT_STRESS_A0,
        "tau_p_s": QUANT_STRESS_TAU_S,
        "tau_g_s": QUANT_STRESS_TAU_S,
        "omega": 0.0,
        "n": QUANT_STRESS_N,
        "replicates": replicates,
        "seed": QUANT_STRESS_SEED,
        "per_link": {
            link: {
                "step_packets": float(steps[index]),
                "acf1_independent_median": float(observed[index]),
                "acf1_independent_min_replicate": float(independent[:, index].min()),
                "acf1_independent_max_replicate": float(independent[:, index].max()),
                "acf1_independent_predicted": float(predicted[index]),
                "prediction_abs_error": float(abs(observed[index] - predicted[index])),
                "acf1_cumulative_median": float(cumulative_observed[index]),
                "independent_classification": classify_quantization(observed[index]),
                "cumulative_classification": classify_quantization(
                    cumulative_observed[index]
                ),
            }
            for index, link in enumerate(LINKS)
        },
        "independent_acf1_min_median": float(observed.min()),
        "independent_prediction_max_abs_error": float(
            np.max(np.abs(observed - predicted))
        ),
        "cumulative_acf1_max_abs_error_from_minus_half": float(
            np.max(np.abs(cumulative_observed + 0.5))
        ),
    }


def load_measurement_scales(
    certificate_path: Path, measurement_path: Path
) -> tuple[np.ndarray, dict[str, object]]:
    _sigma_min, provenance = load_g1_contract(certificate_path, measurement_path)
    measurement = json.loads(measurement_path.read_text(encoding="utf-8"))
    variances: dict[str, float] = {}
    for run in measurement["runs"]:
        for row in run["links"]:
            link = str(row["link"])
            value = float(row["v_nonquantized_raw"])
            variances[link] = max(variances.get(link, 0.0), value)
    scales = np.sqrt(
        np.asarray([
            max(variances[link], MEASUREMENT_SD_FLOOR**2) for link in LINKS
        ])
    )
    return scales, {
        **provenance,
        "measurement_variance_field": "v_nonquantized_raw",
        "measurement_variance_reduction": "per_link_max",
        "measurement_sd_floor": MEASUREMENT_SD_FLOOR,
    }


def residual_correlation() -> np.ndarray:
    return np.eye(len(LINKS)) + RHO_EPS_TRUE * (K_TOPO - np.eye(len(LINKS)))


def add_measurement_residual(
    sent: np.ndarray,
    scales: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    target_corr = residual_correlation()
    eigenvalues, eigenvectors = np.linalg.eigh(target_corr)
    if float(eigenvalues.min()) < -1e-12:
        raise ValueError("synthetic residual correlation is not PSD")
    square_root = eigenvectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0.0)))
    standardized = square_root @ rng.standard_normal(sent.shape)
    residual = scales[:, None] * standardized
    return sent + residual, residual


def _pflip(series: np.ndarray, lag: int) -> float:
    return float(np.mean(np.sign(series[lag:]) != np.sign(series[:-lag])))


def _analytic_checks() -> dict[str, float]:
    _path_base, _private_base, reconstructed = component_baselines()
    mean_error = float(np.max(np.abs(reconstructed - RHO_BAR)))
    covariance_error = 0.0
    correlation_error = 0.0
    for omega in OMEGA_GRID:
        expected_variance = A0**2 * DEGREE / CAP_BPS**2
        covariance_error = max(
            covariance_error,
            float(np.max(np.abs(np.diag(design_covariance(A0, omega)) - expected_variance))),
        )
        expected_corr = np.eye(len(LINKS)) + omega * (K_TOPO - np.eye(len(LINKS)))
        correlation_error = max(
            correlation_error,
            float(np.max(np.abs(design_correlation(A0, omega) - expected_corr))),
        )
    return {
        "mean_reconstruction_max_abs_error": mean_error,
        "covariance_max_abs_error": covariance_error,
        "correlation_max_abs_error": correlation_error,
        "max_error": max(mean_error, covariance_error, correlation_error),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--g1-certificate", default=str(DEFAULT_G1_CERTIFICATE))
    parser.add_argument("--g1-measurement", default=str(DEFAULT_G1_MEASUREMENT))
    args = parser.parse_args()
    if args.replicates != REPLICATES or args.seed != SEED:
        raise SystemExit("REFUSED: dry-run replicates and seed are preregistered")

    certificate_path = Path(args.g1_certificate)
    measurement_path = Path(args.g1_measurement)
    measurement_scales, g1_provenance = load_measurement_scales(
        certificate_path, measurement_path
    )
    rng = np.random.default_rng(args.seed)
    c_vector = contrast("P1", "P2", np.ones(len(LINKS)))
    stale_lag = int(round(Z_STALE_S / DT_S))
    checks: list[dict[str, object]] = []

    def record(check_id, description, value, gate, passed, **extra):
        checks.append(
            {
                "id": check_id,
                "description": description,
                "value": value,
                "gate": gate,
                "verdict": "PASS" if passed else "FAIL",
                **extra,
            }
        )

    analytic = _analytic_checks()
    record(
        "DRY-0", "analytic mean/covariance reconstruction",
        analytic["max_error"], GATE_EXACT,
        analytic["max_error"] <= GATE_EXACT, detail=analytic,
    )

    cells = []
    max_component_clip = 0.0
    max_target_clip = 0.0
    max_quant_acf_replicate = 0.0
    min_quant_acf_median = float("inf")
    max_quant_prediction_error = 0.0
    max_path_acf = 0.0
    mixture_error = 0.0
    residual_correlations = []

    for tau_path_s, tau_link_s in REGIMES:
        duration = T_OVER_SLOW_TAU * max(tau_path_s, tau_link_s)
        n = int(round(duration / DT_S))
        for omega in OMEGA_GRID:
            omega_correlations = []
            omega_estimates = []
            acf_samples = []
            tau_eff_samples = []
            pflip_samples = []
            quant_acf_samples = []
            path_acf_samples = []
            clip_component_samples = []
            clip_target_samples = []
            for _replicate in range(args.replicates):
                trace = physical_trace(
                    omega, tau_path_s, tau_link_s, n, rng
                )
                target = trace["rho_target"]
                sent, _sent_packets = quantize_target(target)
                measured, path_residual = add_measurement_residual(
                    sent, measurement_scales, rng
                )
                quant_residual = sent - target
                quant_acfs = [acf(quant_residual[index]) for index in range(len(LINKS))]
                path_acfs = [acf(path_residual[index]) for index in range(len(LINKS))]
                quant_acf_samples.append(quant_acfs)
                path_acf_samples.extend(path_acfs)
                max_quant_acf_replicate = max(
                    max_quant_acf_replicate,
                    max(abs(value) for value in quant_acfs),
                )
                max_path_acf = max(max_path_acf, max(abs(value) for value in path_acfs))
                residual_correlations.append(np.corrcoef(path_residual))
                measured_corr = np.corrcoef(measured)
                omega_correlations.append(measured_corr)
                omega_estimates.append(omega_batch([measured_corr])[0])

                per_link_acf = np.asarray([
                    [acf(target[index], lag) for lag in (1, 2, 3)]
                    for index in range(len(LINKS))
                ])
                acf_samples.append(per_link_acf)
                phi1 = np.clip(per_link_acf[:, 0], 1e-9, 1.0 - 1e-12)
                tau_eff_samples.append(-DT_S / np.log(phi1))
                margin = c_vector @ (target - RHO_BAR)
                pflip_samples.append(_pflip(margin, stale_lag))
                clip_component_samples.append(trace["component_clip_fraction"])
                clip_target_samples.append(trace["target_clip_fraction"])
                max_component_clip = max(
                    max_component_clip, float(trace["component_clip_fraction"])
                )
                max_target_clip = max(
                    max_target_clip, float(trace["target_clip_fraction"])
                )

            acf_median = np.median(np.asarray(acf_samples), axis=0)
            quant_acf_array = np.asarray(quant_acf_samples)
            quant_acf_median = np.median(quant_acf_array, axis=0)
            quant_steps = quantization_step_packets(
                A0, omega, tau_path_s, tau_link_s
            )
            quant_acf_predicted = np.asarray([
                acf1_predicted_mechanism_a(step) for step in quant_steps
            ])
            quant_prediction_error = float(
                np.max(np.abs(quant_acf_median - quant_acf_predicted))
            )
            min_quant_acf_median = min(
                min_quant_acf_median, float(quant_acf_median.min())
            )
            max_quant_prediction_error = max(
                max_quant_prediction_error, quant_prediction_error
            )
            expected_acf = np.asarray([
                mixture_acf(omega, tau_path_s, tau_link_s, lag)
                for lag in (1, 2, 3)
            ])
            cell_mixture_error = float(np.max(np.abs(acf_median - expected_acf)))
            mixture_error = max(mixture_error, cell_mixture_error)
            omega_values = np.asarray(omega_estimates)
            cells.append(
                {
                    "tau_p_s": tau_path_s,
                    "tau_g_s": tau_link_s,
                    "kappa": tau_path_s / tau_link_s,
                    "omega_true": omega,
                    "duration_s": duration,
                    "n": n,
                    "replicates": args.replicates,
                    "omega_hat_median": float(np.median(omega_values)),
                    "omega_hat_sd": float(np.std(omega_values)),
                    "omega_abs_median_error": float(abs(np.median(omega_values) - omega)),
                    "acf_mixture_expected_lag1_3": expected_acf.tolist(),
                    "acf_median_per_link_lag1_3": dict(zip(LINKS, acf_median.tolist())),
                    "acf_mixture_max_abs_error": cell_mixture_error,
                    "tau_eff_median_s": float(np.median(tau_eff_samples)),
                    "pflip_median": float(np.median(pflip_samples)),
                    "quant_acf1_max_abs_replicate": float(
                        np.max(np.abs(quant_acf_array))
                    ),
                    "quant_acf1_median_per_link": dict(
                        zip(LINKS, quant_acf_median.tolist())
                    ),
                    "quant_step_packets_per_link": dict(
                        zip(LINKS, quant_steps.tolist())
                    ),
                    "quant_acf1_predicted_per_link": dict(
                        zip(LINKS, quant_acf_predicted.tolist())
                    ),
                    "quant_acf1_prediction_max_abs_error": quant_prediction_error,
                    "path_acf1_max_abs": float(max(abs(value) for value in path_acf_samples)),
                    "component_clip_fraction_max": float(max(clip_component_samples)),
                    "target_clip_fraction_max": float(max(clip_target_samples)),
                }
            )

    record(
        "DRY-C", "component and aggregate target clipping",
        {"component": max_component_clip, "target": max_target_clip},
        {"component": GATE_COMPONENT_CLIP, "target": GATE_TARGET_CLIP},
        max_component_clip <= GATE_COMPONENT_CLIP and max_target_clip <= GATE_TARGET_CLIP,
    )
    quant_stress = quantization_stress(args.replicates)
    min_quant_acf_median = min(
        min_quant_acf_median,
        quant_stress["independent_acf1_min_median"],
    )
    max_quant_prediction_error = max(
        max_quant_prediction_error,
        quant_stress["independent_prediction_max_abs_error"],
    )
    stress_classes_a = [
        row["independent_classification"]
        for row in quant_stress["per_link"].values()
    ]
    stress_classes_b = [
        row["cumulative_classification"]
        for row in quant_stress["per_link"].values()
    ]
    record(
        "DRY-Q",
        "target-to-sent residual has independent-round sign",
        {
            "min_cell_link_median": min_quant_acf_median,
            "max_abs_single_replicate": max_quant_acf_replicate,
        },
        {"acf1_min": GATE_QUANT_INDEPENDENT_MIN},
        min_quant_acf_median >= GATE_QUANT_INDEPENDENT_MIN
        and all(value == "INDEPENDENT_ROUND" for value in stress_classes_a),
        reduction="minimum of per-cell per-link replicate medians",
    )
    record(
        "DRY-Q-PC",
        "independent-round ACF matches the packet-step prediction",
        max_quant_prediction_error,
        GATE_QUANT_PRED_ERROR,
        max_quant_prediction_error <= GATE_QUANT_PRED_ERROR,
    )
    cumulative_error = quant_stress[
        "cumulative_acf1_max_abs_error_from_minus_half"
    ]
    record(
        "DRY-Q-B",
        "cumulative-floor negative control is separated by sign",
        cumulative_error,
        GATE_QUANT_PRED_ERROR,
        cumulative_error <= GATE_QUANT_PRED_ERROR
        and all(value == "CUMULATIVE" for value in stress_classes_b),
    )
    record(
        "DRY-W", "sent-to-measured residual is temporally white",
        max_path_acf, GATE_WHITE_ACF1, max_path_acf <= GATE_WHITE_ACF1,
    )

    pooled_residual_corr = np.mean(np.asarray(residual_correlations), axis=0)
    residual_corr_error = float(
        np.max(np.abs(
            pooled_residual_corr[np.triu_indices(len(LINKS), 1)]
            - residual_correlation()[np.triu_indices(len(LINKS), 1)]
        ))
    )
    record(
        "DRY-R", "known residual correlation is recovered",
        residual_corr_error, GATE_RESIDUAL_CORR_ERROR,
        residual_corr_error <= GATE_RESIDUAL_CORR_ERROR,
        rho_eps_true=RHO_EPS_TRUE,
        target_correlation=residual_correlation().tolist(),
        estimated_correlation=pooled_residual_corr.tolist(),
        pooling="mean of within-replicate correlations",
    )

    worst_omega_bias = max(cell["omega_abs_median_error"] for cell in cells)
    worst_omega_sd = max(cell["omega_hat_sd"] for cell in cells)
    record(
        "DRY-O", "omega round trip through packetization and measurement",
        {"max_abs_median_error": worst_omega_bias, "max_sd": worst_omega_sd},
        GATE_OMEGA,
        worst_omega_bias <= GATE_OMEGA and worst_omega_sd <= GATE_OMEGA,
    )

    monotone = True
    tau_rows = {}
    for tau_path_s, tau_link_s in REGIMES:
        regime_cells = [
            cell for cell in cells
            if cell["tau_p_s"] == tau_path_s and cell["tau_g_s"] == tau_link_s
        ]
        tau_values = [cell["tau_eff_median_s"] for cell in regime_cells]
        if tau_path_s > tau_link_s:
            this_monotone = bool(np.all(np.diff(tau_values) >= 0.0))
        elif tau_path_s < tau_link_s:
            this_monotone = bool(np.all(np.diff(tau_values) <= 0.0))
        else:
            this_monotone = True
        monotone = monotone and this_monotone
        tau_rows["tau_p=%g,tau_g=%g" % (tau_path_s, tau_link_s)] = {
            "tau_eff_median_by_omega": tau_values,
            "monotone_in_expected_direction": this_monotone,
        }
    record(
        "DRY-T", "two-exponential ACF mixture and persistence direction",
        mixture_error, GATE_MIXTURE_ACF,
        mixture_error <= GATE_MIXTURE_ACF and monotone,
        monotone=monotone, regimes=tau_rows,
    )

    nc_cells = [cell for cell in cells if cell["tau_p_s"] == cell["tau_g_s"]]
    nc_pflip = [cell["pflip_median"] for cell in nc_cells]
    nc_n = min(cell["n"] for cell in nc_cells)
    nc_gate = 6.0 * float(np.sqrt(0.25 / (nc_n - stale_lag)))
    nc_spread = max(nc_pflip) - min(nc_pflip)
    record(
        "DRY-D-NC", "kappa=1 simulated pairwise flip curve is flat",
        nc_spread, nc_gate, nc_spread <= nc_gate,
        pflip_by_omega=nc_pflip,
    )

    pc_cells = [
        cell for cell in cells
        if cell["tau_p_s"] == 30.0 and cell["tau_g_s"] == 3.0
    ]
    pc_pflip = [cell["pflip_median"] for cell in pc_cells]
    path_variance, link_variance = quad_forms(c_vector, A0)
    phi_path = float(np.exp(-Z_STALE_S / 30.0))
    phi_link = float(np.exp(-Z_STALE_S / 3.0))
    analytic_pflip = [
        p_flip(
            omega, path_variance, link_variance, phi_path, phi_link
        )
        for omega in OMEGA_GRID
    ]
    analytic_spread = max(analytic_pflip) - min(analytic_pflip)
    endpoint_direction = pc_pflip[-1] < pc_pflip[0]
    record(
        "DRY-D-PC", "kappa=10 pairwise decision mechanism fires",
        analytic_spread, GATE_PC_FLIP_SPREAD,
        analytic_spread >= GATE_PC_FLIP_SPREAD and endpoint_direction,
        analytic_pflip_by_omega=analytic_pflip,
        simulated_pflip_by_omega=pc_pflip,
        simulated_endpoint_direction_correct=endpoint_direction,
    )

    overall = all(check["verdict"] == "PASS" for check in checks)
    path_base, private_base, reconstructed = component_baselines()
    artifact = {
        "schema": "dt4n.phase_g.g3_dryrun.v2",
        "status": "SYNTHETIC_NO_NETWORK",
        "git_hash": git_hash(),
        "prereg": "docs/phase-G/33-amendment-G-A011.md",
        "inputs": {
            "g1_contract": g1_provenance,
            "g2_decision_flow": {
                "path": "results/SMOKE/phase-G/g2_decision_flow.json",
                "sha256": sha256(Path("results/SMOKE/phase-G/g2_decision_flow.json")),
            },
        },
        "design": {
            "seed": args.seed,
            "replicates": args.replicates,
            "sigma_ref_uA": SIGMA_REF,
            "a0": A0,
            "rho_bar_per_link": dict.fromkeys(LINKS, RHO_BAR),
            "dt_s": DT_S,
            "omega_grid": list(OMEGA_GRID),
            "regimes": [
                {"tau_p_s": tau_path, "tau_g_s": tau_link}
                for tau_path, tau_link in REGIMES
            ],
            "T_over_slowest_tau": T_OVER_SLOW_TAU,
            "wire_bytes": WIRE_BYTES,
            "quantization_stress": {
                "sigma_ref_uA": QUANT_STRESS_SIGMA_REF,
                "tau_s": QUANT_STRESS_TAU_S,
                "n": QUANT_STRESS_N,
                "seed": QUANT_STRESS_SEED,
            },
            "path_baseline_bps": dict(zip(range(len(path_base)), path_base.tolist())),
            "private_baseline_bps": dict(zip(LINKS, private_base.tolist())),
            "reconstructed_mean": dict(zip(LINKS, reconstructed.tolist())),
            "rho_eps_true": RHO_EPS_TRUE,
            "measurement_sd_per_link": dict(zip(LINKS, measurement_scales.tolist())),
        },
        "checks": checks,
        "cells": cells,
        "quantization_stress": quant_stress,
        "overall": "PASS" if overall else "FAIL",
        "network_authorized_by_dryrun": bool(overall),
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("%-11s %22s  %-8s %s" % ("id", "value", "verdict", "description"))
    for check in checks:
        value = check["value"]
        if isinstance(value, dict):
            rendered = ",".join("%s=%.5f" % item for item in value.items())
        else:
            rendered = "%.6f" % value
        print("%-11s %22s  %-8s %s" % (
            check["id"], rendered, check["verdict"], check["description"]
        ))
    print("\nomega round trip:")
    for cell in cells:
        print(
            "  tau_p=%2.0f tau_g=%2.0f omega=%.2f  hat=%.3f sd=%.3f "
            "tau_eff=%.2f pflip=%.3f"
            % (
                cell["tau_p_s"], cell["tau_g_s"], cell["omega_true"],
                cell["omega_hat_median"], cell["omega_hat_sd"],
                cell["tau_eff_median_s"], cell["pflip_median"],
            )
        )
    print("\nG.3 DRY-RUN: %s" % artifact["overall"])
    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Phase 20R.3 -- numeric predictions before the measurement campaign.

This is not a post-hoc explanation. It is the first term of the subtraction:

    measured_err - predicted_err = model-error contribution

The main prediction sets ``y_true := link_model_v2(rho(t))`` and therefore
contains staleness error only. A separate frozen residual-field calculation
adds a coarse model-error stress test for the Phase 21R case study.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

import numpy as np

from measurements import sla_calib_v2 as SLA
from twin import cost_v2 as C
from twin import topology_v7 as T7


Z_GRID = (0.0, 0.05, 0.10, 0.20, 0.30, 0.55)
Z_EXTRAP = (1.0, 2.0, 4.0)
Z_ALL = Z_GRID + Z_EXTRAP
DT = 0.005
TAU_MAIN = 1.0
TAU_SENS = (0.2, 1.0, 5.0)
A_SENS = (0.2, 0.9)
SCALING_RATIOS = (0.10, 0.30, 0.55, 1.00)
N = 200_000
FIT_PATH = "results/LIVE/phase-L/link_model_v2_fit.json"
CAL_PATH = "results/LIVE/phase-20R/sla_calibration.json"
OUT_PATH = "results/SUPERSEDED/phase-20R/prediction_pre_campaign.json"
DOC_PATH = "docs/phase-20R/02-prediction.md"
AMENDMENT_PATH = "docs/phase-20R/00d-amendment-3.md"
FIGURE_PATH = "docs/phase-20R/figures/err_scaling_z_over_tau.svg"
RESIDUAL_FIELD_STEP = 0.01
RESIDUAL_FIELD_SEED = 12345


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_calibration(path: str = CAL_PATH) -> Tuple[Dict[Tuple[str, float], Mapping[str, object]], Mapping[str, object]]:
    with open(path, "r", encoding="utf-8") as f:
        report = json.load(f)
    cells = {}
    for cell in report["cells"]:
        cells[(str(cell["mode"]), float(cell["rho_bar"]))] = cell
    return cells, report


def load_fit(path: str = FIT_PATH) -> Mapping[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def z_key(z_s: float) -> str:
    return "%.3f" % float(z_s)


def average_ranks(values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    order = np.argsort(arr, kind="mergesort")
    ranks = np.empty(len(arr), dtype=float)
    i = 0
    while i < len(arr):
        j = i + 1
        while j < len(arr) and arr[order[j]] == arr[order[i]]:
            j += 1
        ranks[order[i:j]] = 0.5 * (i + j - 1) + 1.0
        i = j
    return ranks


def spearman_rho(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 2:
        return None
    rx = average_ranks(x)
    ry = average_ranks(y)
    if float(rx.std()) <= 0.0 or float(ry.std()) <= 0.0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


def residual_field_by_link(mode: str, fit: Mapping[str, object]) -> Dict[str, np.ndarray]:
    """Frozen residual field on the 0.01 rho grid used for measurement lookup."""
    rng = np.random.default_rng(RESIDUAL_FIELD_SEED)
    grid = np.arange(C.RHO_MIN, C.RHO_MAX + 1e-9, RESIDUAL_FIELD_STEP)
    out = {}
    for link in T7.LINK_NAMES:
        bw, _base, q = T7.LINKS[link]
        key = "%s|%g|%d" % (mode, bw, q)
        sd = float(fit["links"][key]["resid_sd_cv_interior_ms"])
        out[link] = rng.standard_normal(len(grid)) * sd
    return out


def add_residual_field(
    rho_mat: np.ndarray,
    mode: str,
    fit: Mapping[str, object],
) -> np.ndarray:
    """Return additive path-delay residuals with shape ``(n, K)``."""
    fields = residual_field_by_link(mode, fit)
    n = rho_mat.shape[0]
    add = np.zeros((n, T7.K), dtype=float)
    grid_len = len(next(iter(fields.values())))
    for link_idx, link in enumerate(T7.LINK_NAMES):
        idx = np.clip(
            np.round((rho_mat[:, link_idx] - C.RHO_MIN) / RESIDUAL_FIELD_STEP).astype(int),
            0,
            grid_len - 1,
        )
        values = fields[link][idx]
        for action, path in enumerate(T7.PATH_NAMES):
            if link in T7.PATHS[path]:
                add[:, action] += values
    return add


def prediction_from_arrays(
    c_hat: np.ndarray,
    c_true: np.ndarray,
    viol: np.ndarray,
    dt: float,
    z_values: Sequence[float],
) -> Dict[str, Dict[str, object]]:
    n = c_hat.shape[0]
    true_opt = np.argmin(c_true, axis=1)
    out: Dict[str, Dict[str, object]] = {}
    for z_s in z_values:
        steps = int(round(float(z_s) / float(dt)))
        if steps == 0:
            twin = np.argmin(c_hat, axis=1)
            true = true_opt
            rows = np.arange(n)
        else:
            if steps >= n:
                raise ValueError("z %.3f exceeds trace length" % z_s)
            twin = np.argmin(c_hat[:-steps], axis=1)
            true = true_opt[steps:]
            rows = np.arange(n - steps)
        wrong = twin != true
        v_twin = viol[steps:][rows, twin] if steps else viol[rows, twin]
        v_true = viol[steps:][rows, true] if steps else viol[rows, true]
        out[z_key(z_s)] = {
            "z_s": float(z_s),
            "z_steps": int(steps),
            "err": float(wrong.mean()),
            "d_sla": float(v_twin.mean() - v_true.mean()),
            "extrapolated": bool(float(z_s) in Z_EXTRAP),
        }
    return out


def predict_cell(
    cv2: C.CostV2,
    cal_cell: Mapping[str, object],
    fit: Mapping[str, object],
    tau: float = TAU_MAIN,
    a: float | None = None,
    n: int = N,
    z_values: Sequence[float] = Z_ALL,
    with_model_err: bool = False,
) -> Dict[str, object]:
    mode = str(cal_cell["mode"])
    rho_bar = float(cal_cell["rho_bar"])
    sigma = float(cal_cell["sigma_rho"])
    if a is not None:
        sigma = C.sigma_from_a_regime(mode, rho_bar, float(a))
    rho_mat = SLA.ar1_matrix(
        mode,
        rho_bar,
        sigma,
        tau=float(tau),
        dt=DT,
        n=int(n),
        seed=int(cal_cell["seed"]),
    )
    delay_hat, loss_hat, cost_hat = cv2.tables_batch(rho_mat, mode, float(cal_cell["w_loss"]))
    if with_model_err:
        delay_true = delay_hat + add_residual_field(rho_mat, mode, fit)
    else:
        delay_true = delay_hat
    cost_true = delay_true + float(cal_cell["w_loss"]) * loss_hat
    viol = (delay_true > float(cal_cell["t_delay_ms"])) | (loss_hat > float(cal_cell["t_loss"]))
    per_z = prediction_from_arrays(cost_hat, cost_true, viol, DT, z_values)
    if all(z_key(z) in per_z for z in Z_GRID):
        rho = spearman_rho([float(z) for z in Z_GRID], [per_z[z_key(z)]["err"] for z in Z_GRID])
    else:
        rho = None
    return {
        "mode": mode,
        "rho_bar": rho_bar,
        "tau_rho": float(tau),
        "a": float(a) if a is not None else float(cal_cell["a"]),
        "sigma_rho": float(sigma),
        "with_model_err": bool(with_model_err),
        "per_z": per_z,
        "spearman": {
            "rho": rho,
            "note": "constant curve" if rho is None else "rank correlation over non-extrapolated z grid",
        },
    }


def model_error_summary(fit: Mapping[str, object]) -> Dict[str, object]:
    rows = {}
    by_mode: Dict[str, List[float]] = {"cbr": [], "poisson": [], "h2": []}
    eff_by_mode: Dict[str, List[float]] = {"cbr": [], "poisson": [], "h2": []}
    weighted_resid_by_mode: Dict[str, List[float]] = {"cbr": [], "poisson": [], "h2": []}
    for key, link in sorted(fit["links"].items()):
        mode, _bw, _q = key.split("|")
        if mode not in by_mode:
            continue
        resid = float(link["resid_sd_cv_interior_ms"])
        sigma_sched = float(link["sigma_schedule"])
        pure = math.sqrt(max(resid * resid - sigma_sched * sigma_sched, 0.0))
        row = {
            "bias_rms_ms": float(link["bias_rms_interior_ms"]),
            "resid_sd_ms": resid,
            "sigma_schedule_ms": sigma_sched,
            "e_model_pure_ms": pure,
            "model_efficiency": float(link["model_efficiency"]),
        }
        rows[key] = row
        by_mode[mode].append(pure)
        eff_by_mode[mode].append(row["model_efficiency"])
    for mode in weighted_resid_by_mode:
        for link in T7.LINK_NAMES:
            bw, _base, q = T7.LINKS[link]
            key = "%s|%g|%d" % (mode, bw, q)
            weighted_resid_by_mode[mode].append(float(fit["links"][key]["resid_sd_cv_interior_ms"]))
    mode_summary = {}
    for mode in by_mode:
        mode_summary[mode] = {
            "e_model_pure_min_ms": float(min(by_mode[mode])),
            "e_model_pure_max_ms": float(max(by_mode[mode])),
            "efficiency_min": float(min(eff_by_mode[mode])),
            "efficiency_max": float(max(eff_by_mode[mode])),
            "topology_mean_resid_sd_ms_per_link": float(np.mean(weighted_resid_by_mode[mode])),
        }
    return {"links": rows, "by_mode": mode_summary}


def zero_pc1_prediction(cal_cell: Mapping[str, object]) -> Dict[str, object]:
    per_z = {}
    for z_s in Z_ALL:
        per_z[z_key(z_s)] = {
            "z_s": float(z_s),
            "z_steps": int(round(float(z_s) / DT)),
            "err": 0.0,
            "d_sla": 0.0,
            "extrapolated": bool(float(z_s) in Z_EXTRAP),
            "note": "PC1 prediction: cbr deterministic/no queueing error expected",
        }
    return {
        "mode": str(cal_cell["mode"]),
        "rho_bar": float(cal_cell["rho_bar"]),
        "tau_rho": TAU_MAIN,
        "a": float(cal_cell.get("a", 0.9)),
        "sigma_rho": float(cal_cell.get("sigma_rho", 0.0)),
        "with_model_err": False,
        "per_z": per_z,
        "spearman": {"rho": None, "note": "constant curve"},
    }


def run_predictions(
    n: int = N,
    cal_path: str = CAL_PATH,
    fit_path: str = FIT_PATH,
) -> Dict[str, object]:
    cal, cal_report = load_calibration(cal_path)
    fit = load_fit(fit_path)
    cv2 = C.CostV2(strict_reliable=True)
    main: Dict[str, object] = {}
    model_err: Dict[str, object] = {}
    sensitivity_tau: Dict[str, object] = {}
    sensitivity_a: Dict[str, object] = {}

    for key in sorted(cal):
        mode, rho_bar = key
        cell = cal[key]
        cell_key = "%s@%.3f" % (mode, rho_bar)
        if not cell["feasible"]:
            main[cell_key] = {
                "mode": mode,
                "rho_bar": rho_bar,
                "feasible": False,
                "role": cell.get("role"),
                "reason": cell.get("reason"),
                "prediction": zero_pc1_prediction(cell) if mode == "cbr" else None,
            }
            continue
        if mode == "cbr":
            main[cell_key] = {
                "mode": mode,
                "rho_bar": rho_bar,
                "feasible": True,
                "role": cell.get("role"),
                "prediction": zero_pc1_prediction(cell),
            }
            continue
        pred = predict_cell(cv2, cell, fit, n=n, with_model_err=False)
        main[cell_key] = {"mode": mode, "rho_bar": rho_bar, "feasible": True, "role": cell.get("role"), "prediction": pred}
        model_pred = predict_cell(cv2, cell, fit, n=n, with_model_err=True)
        model_err[cell_key] = model_pred

        tau_rows = {}
        for tau in TAU_SENS:
            tau_rows["%.1f" % tau] = predict_cell(
                cv2,
                cell,
                fit,
                tau=tau,
                n=n,
                z_values=(0.55,),
                with_model_err=False,
            )["per_z"]["0.550"]["err"]
        sensitivity_tau[cell_key] = tau_rows

        a_rows = {}
        for a in A_SENS:
            a_rows["%.1f" % a] = predict_cell(
                cv2,
                cell,
                fit,
                a=a,
                n=n,
                z_values=(0.55,),
                with_model_err=False,
            )["per_z"]["0.550"]["err"]
        sensitivity_a[cell_key] = a_rows

    scaling_cell = cal[("poisson", 0.925)]
    scaling: Dict[str, object] = {
        "mode": "poisson",
        "rho_bar": 0.925,
        "ratios": list(SCALING_RATIOS),
        "taus": list(TAU_SENS),
        "rows": [],
    }
    for ratio in SCALING_RATIOS:
        vals = []
        for tau in TAU_SENS:
            z = float(ratio) * float(tau)
            pred = predict_cell(
                cv2,
                scaling_cell,
                fit,
                tau=tau,
                n=n,
                z_values=(z,),
                with_model_err=False,
            )
            vals.append(
                {
                    "tau_rho": float(tau),
                    "z_s": float(z),
                    "z_over_tau": float(ratio),
                    "err": float(pred["per_z"][z_key(z)]["err"]),
                }
            )
        spread = max(v["err"] for v in vals) - min(v["err"] for v in vals)
        scaling["rows"].append({"z_over_tau": float(ratio), "values": vals, "spread": float(spread)})
    scaling["max_spread"] = float(max(row["spread"] for row in scaling["rows"]))
    scaling["pass_threshold"] = 0.05
    scaling["h6_pre_campaign_pass"] = bool(scaling["max_spread"] < scaling["pass_threshold"])

    return {
        "phase": "20R.3",
        "generated_date": "2026-08-04",
        "script": "measurements.predict_err_quick",
        "config": {
            "n": int(n),
            "dt": DT,
            "tau_main": TAU_MAIN,
            "z_grid": list(Z_GRID),
            "z_extrap": list(Z_EXTRAP),
            "tau_sens": list(TAU_SENS),
            "a_sens": list(A_SENS),
            "residual_field_step": RESIDUAL_FIELD_STEP,
            "residual_field_seed": RESIDUAL_FIELD_SEED,
            "calibration_path": cal_path,
            "fit_path": fit_path,
            "git_tag_to_create": "phase-20R-prediction",
        },
        "inputs": {
            "measurements/predict_err_quick.py": sha256_file("measurements/predict_err_quick.py"),
            "measurements/sla_calib_v2.py": sha256_file("measurements/sla_calib_v2.py"),
            "twin/cost_v2.py": sha256_file("twin/cost_v2.py"),
            "results/LIVE/phase-20R/sla_calibration.json": sha256_file(cal_path),
            "results/LIVE/phase-L/link_model_v2_fit.json": sha256_file(fit_path),
        },
        "sla_calibration_summary": cal_report["summary"],
        "main": main,
        "model_error_summary": model_error_summary(fit),
        "with_model_error": model_err,
        "sensitivity": {"tau": sensitivity_tau, "a": sensitivity_a},
        "scaling_law": scaling,
        "stopping_rules": {
            "ratio_gt_2": "STOP: investigate measurement pipeline before trusting the number",
            "ratio_1p2_to_2": "record and explain in text, then continue",
            "ratio_lt_1p2": "understanding confirmed",
            "err_z0_gt_0p20": "STOP: likely quantization or measured-lookup bug",
        },
    }


def _cell_prediction(report: Mapping[str, object], key: str) -> Mapping[str, object]:
    row = report["main"][key]
    return row["prediction"]


def main_prediction_lines(report: Mapping[str, object]) -> List[str]:
    lines = [
        "mode     rho_bar | z=0.05  z=0.10  z=0.20  z=0.30  z=0.55 | d_sla(0.55)",
        "-" * 83,
    ]
    for key in sorted(report["main"]):
        row = report["main"][key]
        pred = row.get("prediction")
        mode = row["mode"]
        rho_bar = float(row["rho_bar"])
        if pred is None:
            lines.append("%-8s %.3f   | LOAI: %s" % (mode, rho_bar, row.get("reason", "")))
            continue
        per_z = pred["per_z"]
        lines.append(
            "%-8s %.3f   | %.4f  %.4f  %.4f  %.4f  %.4f | %+.4f%s"
            % (
                mode,
                rho_bar,
                float(per_z["0.050"]["err"]),
                float(per_z["0.100"]["err"]),
                float(per_z["0.200"]["err"]),
                float(per_z["0.300"]["err"]),
                float(per_z["0.550"]["err"]),
                float(per_z["0.550"]["d_sla"]),
                "   <- PC1" if mode == "cbr" else "",
            )
        )
    return lines


def model_error_lines(report: Mapping[str, object]) -> List[str]:
    lines = [
        "mode     rho_bar | resid_sd/link | err(z=0) | err(0.55) no-model | err(0.55) with-model | ratio",
        "-" * 96,
    ]
    by_mode = report["model_error_summary"]["by_mode"]
    for key in sorted(report["with_model_error"]):
        pred_model = report["with_model_error"][key]
        pred_nom = report["main"][key]["prediction"]
        mode = pred_model["mode"]
        rho_bar = float(pred_model["rho_bar"])
        e0 = float(pred_model["per_z"]["0.000"]["err"])
        e55_nom = float(pred_nom["per_z"]["0.550"]["err"])
        e55_model = float(pred_model["per_z"]["0.550"]["err"])
        ratio = e0 / max(e55_model, 1e-12)
        lines.append(
            "%-8s %.3f   |    %.4f    |  %.4f  |      %.4f        |       %.4f        | %.2f"
            % (
                mode,
                rho_bar,
                float(by_mode[mode]["topology_mean_resid_sd_ms_per_link"]),
                e0,
                e55_nom,
                e55_model,
                ratio,
            )
        )
    return lines


def sensitivity_lines(report: Mapping[str, object]) -> List[str]:
    lines = [
        "mode     rho_bar | tau=0.2  tau=1.0  tau=5.0 | a=0.2   a=0.9",
        "-" * 75,
    ]
    for key in sorted(report["sensitivity"]["tau"]):
        tau = report["sensitivity"]["tau"][key]
        amp = report["sensitivity"]["a"][key]
        mode, rho = key.split("@")
        lines.append(
            "%-8s %.3f   | %.4f   %.4f   %.4f | %.4f  %.4f"
            % (
                mode,
                float(rho),
                float(tau["0.2"]),
                float(tau["1.0"]),
                float(tau["5.0"]),
                float(amp["0.2"]),
                float(amp["0.9"]),
            )
        )
    return lines


def scaling_lines(report: Mapping[str, object]) -> List[str]:
    lines = ["tau    z      z/tau    err"]
    for row in report["scaling_law"]["rows"]:
        for val in row["values"]:
            lines.append(
                "%3.1f  %6.3f   %.2f    %.4f"
                % (
                    float(val["tau_rho"]),
                    float(val["z_s"]),
                    float(val["z_over_tau"]),
                    float(val["err"]),
                )
            )
        lines.append("")
    lines.append("max_spread = %.4f" % float(report["scaling_law"]["max_spread"]))
    return lines


def gate_prediction_summary(report: Mapping[str, object]) -> Dict[str, object]:
    out = {}
    for key, row in report["main"].items():
        pred = row.get("prediction")
        if pred is None or row["mode"] == "cbr":
            continue
        e55 = float(pred["per_z"]["0.550"]["err"])
        d55 = float(pred["per_z"]["0.550"]["d_sla"])
        rho = pred["spearman"]["rho"]
        out[key] = {
            "G1_err_in_band": bool(0.05 <= e55 <= 0.40),
            "G2_d_sla_ge_003": bool(d55 >= 0.03),
            "G3_monotone": bool(rho is not None and rho > 0.0),
            "err_0p55": e55,
            "d_sla_0p55": d55,
            "spearman_rho": rho,
        }
    return out


def write_json(report: Mapping[str, object], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, indent=2, sort_keys=True, separators=(",", ": ")) + "\n",
        encoding="utf-8",
    )


def write_doc(report: Mapping[str, object], path: str) -> None:
    gate = gate_prediction_summary(report)
    passing = [
        key for key, row in gate.items()
        if row["G1_err_in_band"] and row["G2_d_sla_ge_003"] and row["G3_monotone"]
    ]
    text = [
        "# DU DOAN TRUOC CHIEN DICH -- Phase 20R",
        "",
        "Ngay ky: 2026-08-04",
        "Git tag: phase-20R-prediction",
        "BAT BUOC: file nay phai duoc COMMIT TRUOC commit dau tien cua Lesson 20R.4.",
        "",
        "## 0. Vai Tro",
        "",
        "Day khong phai phong doan. Day la ve thu nhat cua phep tru:",
        "",
        "```text",
        "err_do_that - err_du_doan = dong gop cua e_model",
        "```",
        "",
        "Du doan chay tren `link_model_v2` voi `y_true := f2(rho(t))`, tuc gia",
        "vo mo hinh dung tuyet doi va chi con `e_staleness`.",
        "",
        "## 1. Du Doan Chinh",
        "",
        "```text",
        *main_prediction_lines(report),
        "```",
        "",
        "Tom tat gate tai `z = 0.55 s`: %d o du doan qua G1+G2+G3."
        % len(passing),
        "",
        "```text",
        *[
            "%-14s err=%.4f d_sla=%+.4f spearman=%s"
            % (
                key,
                float(gate[key]["err_0p55"]),
                float(gate[key]["d_sla_0p55"]),
                "%.3f" % float(gate[key]["spearman_rho"]) if gate[key]["spearman_rho"] is not None else "constant",
            )
            for key in sorted(gate)
        ],
        "```",
        "",
        "## 2. Du Doan e_model",
        "",
        "Tu `link_model_v2_fit.json`: `e_model_thuan = sqrt(resid_sd^2 - sigma_schedule^2)`.",
        "",
        "```text",
        "poisson %.3f - %.3f ms/link   efficiency %.3f - %.3f"
        % (
            float(report["model_error_summary"]["by_mode"]["poisson"]["e_model_pure_min_ms"]),
            float(report["model_error_summary"]["by_mode"]["poisson"]["e_model_pure_max_ms"]),
            float(report["model_error_summary"]["by_mode"]["poisson"]["efficiency_min"]),
            float(report["model_error_summary"]["by_mode"]["poisson"]["efficiency_max"]),
        ),
        "h2      %.3f - %.3f ms/link   efficiency %.3f - %.3f"
        % (
            float(report["model_error_summary"]["by_mode"]["h2"]["e_model_pure_min_ms"]),
            float(report["model_error_summary"]["by_mode"]["h2"]["e_model_pure_max_ms"]),
            float(report["model_error_summary"]["by_mode"]["h2"]["efficiency_min"]),
            float(report["model_error_summary"]["by_mode"]["h2"]["efficiency_max"]),
        ),
        "cbr     %.3f - %.3f ms/link   efficiency %.3f - %.3f  (vung tri han, da loai)"
        % (
            float(report["model_error_summary"]["by_mode"]["cbr"]["e_model_pure_min_ms"]),
            float(report["model_error_summary"]["by_mode"]["cbr"]["e_model_pure_max_ms"]),
            float(report["model_error_summary"]["by_mode"]["cbr"]["efficiency_min"]),
            float(report["model_error_summary"]["by_mode"]["cbr"]["efficiency_max"]),
        ),
        "```",
        "",
        "```text",
        *model_error_lines(report),
        "```",
        "",
        "D1: `err(z=0)` se nam trong `[0.000, 0.10]` o moi o vao gate. Neu",
        "do that cho `err(z=0) > 0.20`, dung va kiem tra thuoc do.",
        "",
        "D2: `err(z=0)/err(0.55) < 0.50` o moi o vao gate, nen ky vong",
        "`e_staleness` chi phoi va G3 pass.",
        "",
        "D3: o nhay nhat voi e_model la o co ti so lon nhat trong bang tren;",
        "neu do that khac, cap nhat case study 21R bang amendment.",
        "",
        "## 3. H6 -- Dinh Luat Ti Le",
        "",
        "`err(z | che do)` chi phu thuoc z qua ti so khong thu nguyen",
        "`z/tau_rho`. Kiem tren `poisson@0.925`:",
        "",
        "```text",
        *scaling_lines(report),
        "```",
        "",
        "Nguong pass da chot: do tan giua ba duong `< 0.05` tuyet doi tren",
        "toan luoi `z/tau`. Hinh: `docs/phase-20R/figures/err_scaling_z_over_tau.svg`.",
        "",
        "## 4. Do Nhay",
        "",
        "```text",
        *sensitivity_lines(report),
        "```",
        "",
        "`tau_rho` va `a` la hai bac tu do da co dinh, khong phai tham so vo hai.",
        "Lesson 20R.6 se chay chung nhu doi chung do nhay.",
        "",
        "## 5. Luat Dung",
        "",
        "```text",
        "lech > 2.0x     -> DUNG. Dieu tra thuoc do truoc khi tin con so.",
        "lech 1.2 - 2.0x -> ghi lai, tim giai thich bang van ban, di tiep.",
        "lech < 1.2x     -> xac nhan hieu biet, di tiep.",
        "err(z=0) > 0.20 -> DUNG. Gan nhu chac chan co bug o luong tu hoa hoac bang tra do that.",
        "```",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(text) + "\n", encoding="utf-8")


def write_amendment(report: Mapping[str, object], path: str, previous_commit: str) -> None:
    text = """# AMENDMENT 3 -- Phase 20R: bo sung H6 va khai bao tau/a

Ngay: 2026-08-04
Commit truoc thay doi: %s

## Toi Da Thay Gi

Khi chay du doan truoc chien dich, hai bac tu do `tau_rho` va `a` co anh
huong lon hon du kien. Tren nhieu o, doi `tau_rho` tu 1.0 sang 0.2 hoac 5.0
lam `err(0.55)` doi nhieu lan; doi `a` tu 0.2 sang 0.9 co the doi `err` tu
gan 0 sang muc co y nghia.

Dong thoi, tren `poisson@0.925`, cac duong theo `tau in {0.2,1.0,5.0}` gop
lai khi ve theo bien khong thu nguyen `z/tau_rho`; max spread tien chien dich
= %.4f.

## Toi Doi Gi

Bo sung gia thuyet H6:

```text
H6  err(z | che do) chi phu thuoc z qua ti so khong thu nguyen z/tau_rho.
    Kiem: chay tau in {0.2, 1.0, 5.0} tren mot o,
          gop duong cong theo z/tau.
    PASS neu do tan giua ba duong < 0.05 tuyet doi tren toan luoi z/tau.
    Neu bi bac bo, bao cao ket qua am.
```

Khai bao `tau_rho = 1.0` va `a = 0.9` la hai bac tu do thiet ke da chot.
Lesson 20R.6 se chay doi chung do nhay voi `a = 0.2` va
`tau_rho in {0.2, 5.0}`.

## Toi Khong Doi Gi

Q1-Q8, Q2', Q5', gate G1-G7, va ngan sach lap giu nguyen. `z = 0.55 s`
van la diem doc gate; `z in {1,2,4}` van la ngoai suy.
""" % (previous_commit, float(report["scaling_law"]["max_spread"]))
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def write_scaling_svg(report: Mapping[str, object], path: str) -> None:
    rows = report["scaling_law"]["rows"]
    width, height = 760, 420
    left, top, plot_w, plot_h = 80, 55, 560, 290
    colors = {0.2: "#2563eb", 1.0: "#16a34a", 5.0: "#dc2626"}
    max_err = max(v["err"] for row in rows for v in row["values"])
    max_ratio = max(float(row["z_over_tau"]) for row in rows)

    def sx(ratio: float) -> float:
        return left + plot_w * ratio / max_ratio

    def sy(err: float) -> float:
        return top + plot_h * (1.0 - err / max_err)

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
        % (width, height, width, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="24" y="28" font-family="Arial, sans-serif" font-size="18" font-weight="700">Phase 20R.3 scaling law: err vs z/tau</text>',
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#111827" stroke-width="1"/>'
        % (left, top + plot_h, left + plot_w, top + plot_h),
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#111827" stroke-width="1"/>'
        % (left, top, left, top + plot_h),
    ]
    by_tau: Dict[float, List[Tuple[float, float]]] = {tau: [] for tau in TAU_SENS}
    for row in rows:
        for val in row["values"]:
            by_tau[float(val["tau_rho"])].append((float(val["z_over_tau"]), float(val["err"])))
    for tau, pts in by_tau.items():
        pts = sorted(pts)
        poly = " ".join("%.2f,%.2f" % (sx(r), sy(e)) for r, e in pts)
        lines.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>' % (poly, colors[tau]))
        for r, e in pts:
            lines.append('<circle cx="%.2f" cy="%.2f" r="4" fill="%s"/>' % (sx(r), sy(e), colors[tau]))
    for tick in SCALING_RATIOS:
        lines.append(
            '<text x="%.2f" y="%d" font-family="Arial, sans-serif" font-size="11" text-anchor="middle">%.2f</text>'
            % (sx(tick), top + plot_h + 18, tick)
        )
    for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
        val = max_err * frac
        lines.append(
            '<text x="%d" y="%.2f" font-family="Arial, sans-serif" font-size="11" text-anchor="end">%.2f</text>'
            % (left - 8, sy(val) + 4, val)
        )
    lines.append(
        '<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="12" text-anchor="middle">z / tau_rho</text>'
        % (left + plot_w // 2, height - 28)
    )
    lines.append(
        '<text x="20" y="%d" font-family="Arial, sans-serif" font-size="12" transform="rotate(-90 20 %d)">err</text>'
        % (top + plot_h // 2, top + plot_h // 2)
    )
    lx, ly = left + plot_w + 30, top + 20
    for tau in TAU_SENS:
        lines.append('<rect x="%d" y="%d" width="12" height="12" fill="%s"/>' % (lx, ly, colors[tau]))
        lines.append(
            '<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="12">tau=%.1f</text>'
            % (lx + 18, ly + 11, tau)
        )
        ly += 22
    lines.append(
        '<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="12">max spread %.4f</text>'
        % (lx, ly + 12, float(report["scaling_law"]["max_spread"]))
    )
    lines.append("</svg>")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--cal", default=CAL_PATH)
    ap.add_argument("--fit", default=FIT_PATH)
    ap.add_argument("--out", default=OUT_PATH)
    ap.add_argument("--doc", default=DOC_PATH)
    ap.add_argument("--amendment", default=AMENDMENT_PATH)
    ap.add_argument("--figure", default=FIGURE_PATH)
    ap.add_argument("--previous-commit", default="f282a07f0c6bce4eeb702078a097eaa8129afe53")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    report = run_predictions(n=args.n, cal_path=args.cal, fit_path=args.fit)
    print("\n".join(main_prediction_lines(report)))
    print()
    print("\n".join(model_error_lines(report)))
    print()
    print("\n".join(scaling_lines(report)))
    print()
    print("H6 max spread = %.4f" % float(report["scaling_law"]["max_spread"]))

    if args.write:
        write_json(report, args.out)
        write_doc(report, args.doc)
        write_amendment(report, args.amendment, args.previous_commit)
        write_scaling_svg(report, args.figure)
        print()
        print("WROTE %s" % args.out)
        print("WROTE %s" % args.doc)
        print("WROTE %s" % args.amendment)
        print("WROTE %s" % args.figure)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Summarize Phase 20 decision-error replicate JSON files."""

from __future__ import annotations

import argparse
import json
import math
import os
from typing import Dict, List, Mapping, Optional, Sequence


T_CRIT_975 = {
    1: 12.706204736432095,
    2: 4.302652729911275,
    3: 3.182446305284263,
    4: 2.7764451051977987,
    5: 2.570581835636314,
    6: 2.4469118487916806,
    7: 2.3646242510102993,
    8: 2.306004135204166,
    9: 2.2621571627409915,
    10: 2.2281388519649385,
    11: 2.200985160091638,
    12: 2.178812829667228,
    13: 2.1603686564610127,
    14: 2.1447866879169273,
    15: 2.131449545559323,
    16: 2.1199052992210112,
    17: 2.1098155778331806,
    18: 2.10092204024096,
    19: 2.093024054408263,
    20: 2.0859634472658364,
    21: 2.079613844727662,
    22: 2.0738730679040147,
    23: 2.068657610419048,
    24: 2.0638985616280205,
    25: 2.059538552753294,
    26: 2.055529438642871,
    27: 2.0518305164802833,
    28: 2.048407141795244,
    29: 2.045229642132703,
    30: 2.0422724563012373,
}


CHI2_025_975 = {
    1: (0.0009820691171752555, 5.023886187314888),
    2: (0.05063561596857975, 7.3777589082278725),
    3: (0.21579528262389785, 9.348403604496148),
    4: (0.4844185570879299, 11.143286781877796),
    5: (0.8312116134866625, 12.832501994030027),
    6: (1.237344245791203, 14.44937533544792),
    7: (1.689869180677355, 16.012764274629326),
    8: (2.1797307472526497, 17.534546139484647),
    9: (2.7003894999803584, 19.02276779864163),
    10: (3.2469727802368413, 20.483177350807388),
    11: (3.8157482522361, 21.9200492610212),
    12: (4.4037885069817015, 23.33666415864534),
    13: (5.008750511810331, 24.73560488493155),
    14: (5.628726103039734, 26.11894804503737),
    15: (6.262137795043253, 27.488392863442975),
    16: (6.907664353318578, 28.845350723404753),
    17: (7.564186449577567, 30.19100912163982),
    18: (8.230746194756495, 31.526378439519596),
    19: (8.906516481987971, 32.85232686172969),
    20: (9.590777392264867, 34.16960690283834),
    21: (10.282898881541918, 35.47887550812858),
    22: (10.982325073456622, 36.78071096170883),
    23: (11.688561061331023, 38.0756272503558),
    24: (12.40116029915735, 39.36407702660391),
    25: (13.11971458650333, 40.64646924545303),
    26: (13.843846211447316, 41.92317060454853),
    27: (14.573201067356548, 43.19451085385857),
    28: (15.307443408570753, 44.46078550644606),
    29: (16.046251169516126, 45.72225828783795),
    30: (16.789311056669887, 46.979163016092),
}


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


def read_json(path: str) -> object:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: object) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def parse_inputs(text: str) -> List[str]:
    paths = [part.strip() for part in str(text).split(",") if part.strip()]
    if not paths:
        raise ValueError("expected at least one input JSON")
    return paths


def choose_run(data: Mapping[str, object], run_seed: Optional[str]) -> Mapping[str, object]:
    runs = data.get("runs")
    if not isinstance(runs, dict) or not runs:
        raise ValueError("decision-error JSON has no runs object")
    def sort_key(value: object) -> tuple:
        text = str(value)
        return (0, int(text)) if text.isdigit() else (1, text)

    key = str(run_seed) if run_seed is not None else sorted(runs, key=sort_key)[0]
    if key not in runs:
        raise ValueError("run seed %s not found; available: %s" % (key, sorted(runs)))
    run = runs[key]
    if not isinstance(run, dict):
        raise ValueError("run %s is not an object" % key)
    return run


def ci_to_se(row: Mapping[str, object]) -> float:
    if "se" in row:
        return float(row["se"])
    return float(float(row["ci_hi"]) - float(row["ci_lo"])) / (2.0 * 1.96)


def sample_sd(values: Sequence[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))


def rms(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(x * x for x in values) / len(values))


def t_crit_975(df: int) -> float:
    if df <= 0:
        return math.inf
    if df in T_CRIT_975:
        return T_CRIT_975[df]
    return 1.959963984540054


def sd_chi_square_ci95(sd: float, df: int) -> Optional[Dict[str, float]]:
    if df <= 0 or sd <= 0.0:
        return None
    if df not in CHI2_025_975:
        return None
    chi_lo, chi_hi = CHI2_025_975[df]
    variance = float(sd) * float(sd)
    return {
        "lo": math.sqrt(df * variance / chi_hi),
        "hi": math.sqrt(df * variance / chi_lo),
        "df": int(df),
        "level": 0.95,
    }


def summarize_metric(name: str, rows: Sequence[Mapping[str, object]], threshold: Optional[float] = None) -> Dict[str, object]:
    points = [float(row[name]) for row in rows]
    within_ses = [float(row[name + "_within_se"]) for row in rows]
    n = len(points)
    df = max(0, n - 1)
    center = sum(points) / len(points)
    sd_between = sample_sd(points)
    within_rms = rms(within_ses)
    se_single = math.sqrt(within_rms * within_rms + sd_between * sd_between)
    se_mean = se_single / math.sqrt(n)
    tcrit = t_crit_975(df)
    mean_lower = center - tcrit * se_mean
    mean_upper = center + tcrit * se_mean
    single_lower = center - 1.96 * se_single
    single_upper = center + 1.96 * se_single
    out: Dict[str, object] = {
        "points": points,
        "point_mean": center,
        "within_trace_se_rms": within_rms,
        "between_trace_sd": sd_between,
        "between_over_within_se": sd_between / within_rms if within_rms > 0.0 else None,
        "se_single_measurement": se_single,
        "se_mean": se_mean,
        "t_crit_975": tcrit,
        "ci95_mean_t": {"lo": mean_lower, "hi": mean_upper, "df": df},
        "ci95_single_measurement_normal": {"lo": single_lower, "hi": single_upper},
        "sd_between_ci95_chi_square": sd_chi_square_ci95(sd_between, df),
        # Backward-compatible aliases from Amendment 7 draft. These describe
        # one future trace, not uncertainty of the population mean.
        "se_total": se_single,
        "ci95_total": {"lo": single_lower, "hi": single_upper},
    }
    if threshold is not None:
        out["mean_t_lower_ge_threshold"] = bool(mean_lower >= threshold)
        out["single_measurement_lower_ge_threshold"] = bool(single_lower >= threshold)
        out["lower_ge_threshold"] = bool(mean_lower >= threshold)
        out["threshold"] = float(threshold)
    return out


def extract_row(path: str, run_seed: Optional[str]) -> Dict[str, object]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError("%s must contain a JSON object" % path)
    run = choose_run(data, run_seed)
    evaluation = run.get("evaluation")
    bootstrap = run.get("bootstrap")
    if not isinstance(evaluation, dict) or not isinstance(bootstrap, dict):
        raise ValueError("%s run has no evaluation/bootstrap; rerun without --nc-only" % path)
    op = evaluation["operational"]
    err_boot = bootstrap["err"]["operational"]
    d_boot = bootstrap["d_sla"]["operational"]
    return {
        "path": path,
        "trace": data.get("config", {}).get("trace"),
        "calibration_mode": data.get("config", {}).get("calibration_mode"),
        "run_seed": run["seed"],
        "err": float(op["err"]),
        "d_sla": float(op["d_sla"]),
        "err_within_se": ci_to_se(err_boot),
        "d_sla_within_se": ci_to_se(d_boot),
        "err_ci95_within": {"lo": float(err_boot["ci_lo"]), "hi": float(err_boot["ci_hi"])},
        "d_sla_ci95_within": {"lo": float(d_boot["ci_lo"]), "hi": float(d_boot["ci_hi"])},
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Summarize Phase 20 decision-error replicate outputs")
    p.add_argument("--inputs", required=True, help="Comma-separated decision_error JSON files")
    p.add_argument("--run-seed", default=None, help="Run seed to read from each JSON; default is the first run")
    p.add_argument("--out", default="results/SUPERSEDED/phase-20/decision_error_replicates_summary.json")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rows = [extract_row(path, args.run_seed) for path in parse_inputs(args.inputs)]
    result = {
        "n_traces": len(rows),
        "run_seed": args.run_seed,
        "traces": rows,
        "err": summarize_metric("err", rows),
        "d_sla": summarize_metric("d_sla", rows, threshold=0.03),
    }
    result["gates"] = {
        "G1_err_mean_t_ci_inside_005_040": bool(
            result["err"]["ci95_mean_t"]["lo"] >= 0.05 and result["err"]["ci95_mean_t"]["hi"] <= 0.40
        ),
        "G2_d_sla_mean_t_lower_ge_003": bool(result["d_sla"]["ci95_mean_t"]["lo"] >= 0.03),
        "G1_err_single_measurement_ci_inside_005_040": bool(
            result["err"]["ci95_total"]["lo"] >= 0.05 and result["err"]["ci95_total"]["hi"] <= 0.40
        ),
        "G2_d_sla_single_measurement_lower_ge_003": bool(result["d_sla"]["ci95_total"]["lo"] >= 0.03),
    }
    write_json(args.out, result)
    print("wrote %s" % args.out)
    print(
        "err: mean=%.5f SD_between=%.5f SE_mean=%.5f CI95_t[%.5f, %.5f]"
        % (
            result["err"]["point_mean"],
            result["err"]["between_trace_sd"],
            result["err"]["se_mean"],
            result["err"]["ci95_mean_t"]["lo"],
            result["err"]["ci95_mean_t"]["hi"],
        )
    )
    print(
        "d_sla: mean=%.5f SD_between=%.5f SE_mean=%.5f CI95_t[%.5f, %.5f] G2=%s"
        % (
            result["d_sla"]["point_mean"],
            result["d_sla"]["between_trace_sd"],
            result["d_sla"]["se_mean"],
            result["d_sla"]["ci95_mean_t"]["lo"],
            result["d_sla"]["ci95_mean_t"]["hi"],
            result["gates"]["G2_d_sla_mean_t_lower_ge_003"],
        )
    )


if __name__ == "__main__":
    main()

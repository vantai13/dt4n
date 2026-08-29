#!/usr/bin/env python3
"""Analyze Phase D Cell C/C' measured traces with the signed estimator."""
from __future__ import annotations

import argparse
import glob
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


LINKS = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
EDGE = ("uA", "uB", "vC", "vD")
PAIRS = ("uA-uB", "vC-vD", "ac-ad", "bc-bd", "uA-vC")
EXPECTED = {
    "cellC": {"core_sigma": 0.10, "edge_sigma": 0.10, "duration": 240, "seeds": [11, 12, 13]},
    "cellCp": {"core_sigma": 0.10, "edge_sigma": 0.05, "duration": 400, "seeds": [21, 22, 23]},
}


def acf_tau(values: np.ndarray, dt: float) -> tuple[float, int]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    centered = values - values.mean()
    variance = float(centered @ centered / len(centered))
    if variance <= 0:
        return 0.5 * dt, 0
    nlag = min(len(centered) // 10, 20_000)
    curve = np.array(
        [centered[: len(centered) - lag] @ centered[lag:] / len(centered) / variance
         for lag in range(nlag + 1)]
    )
    cut = nlag
    for lag in range(1, len(curve)):
        if curve[lag] <= 0:
            cut = lag - 1
            break
    return float(dt * (0.5 + curve[1 : cut + 1].sum())), int(cut)


def wide_trace(path: Path) -> tuple[pd.DataFrame, float, float, int]:
    frame = pd.read_csv(path)
    missing = sorted(set(LINKS) - set(frame["link"].unique()))
    if missing:
        raise ValueError(f"{path}: missing links {missing}")
    if bool((frame["tx_bytes_delta"] < 0).any()):
        raise ValueError(f"{path}: negative tx_bytes_delta (counter reset)")
    wide = frame.pivot(index="sample_index", columns="link", values="rho").dropna()
    times = frame.groupby("sample_index")["timestamp_s"].first().loc[wide.index]
    dt = float(np.median(np.diff(times.to_numpy())))
    duration = float(times.iloc[-1] - times.iloc[0] + dt)
    return wide, dt, duration, int(len(frame) - len(wide) * len(LINKS))


def fisher_pool(values: list[float]) -> float:
    return float(np.tanh(np.mean(np.arctanh(np.clip(values, -0.999999, 0.999999)))))


def baseline_edge_tau() -> dict[str, float]:
    per_link: dict[str, list[float]] = {link: [] for link in EDGE}
    pattern = "results/RAW/phase-23/aoi_v7_campaign/rho_measured_clean_*.csv"
    for filename in sorted(glob.glob(pattern)):
        wide, dt, _duration, _missing = wide_trace(Path(filename))
        for link in EDGE:
            per_link[link].append(acf_tau(wide[link].to_numpy(), dt)[0])
    return {link: float(np.median(values)) for link, values in per_link.items()}


def read_infra(pattern: str) -> tuple[list[dict[str, object]], bool]:
    rows = [json.loads(Path(path).read_text(encoding="utf-8")) for path in sorted(glob.glob(pattern))]
    flag_names = (
        "flag_cpu_saturated", "flag_swapping", "flag_packet_drops", "flag_clock_jump"
    )
    clean = len(rows) == 3 and all(not bool(row.get(flag)) for row in rows for flag in flag_names)
    return rows, clean


def analyze(args: argparse.Namespace) -> dict[str, object]:
    config = EXPECTED[args.cell_name]
    cell_dir = Path(args.cell_dir)
    measured = sorted(cell_dir.glob("rho_measured_rep*.csv"))
    metadata = sorted(cell_dir.glob("meta_rep*.json"))
    if len(measured) != 3 or len(metadata) != 3:
        raise ValueError(f"expected 3 measured and 3 meta files, got {len(measured)}/{len(metadata)}")

    runs: list[dict[str, object]] = []
    pair_values: dict[str, list[float]] = {pair: [] for pair in PAIRS}
    all_neff_pass = True
    all_burn_pass = True
    counter_clean = True
    for rep, (trace_path, meta_path) in enumerate(zip(measured, metadata), 1):
        wide, dt, duration, missing_rows = wide_trace(trace_path)
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        taus = {link: acf_tau(wide[link].to_numpy(), dt)[0] for link in LINKS}
        pair_results: dict[str, dict[str, object]] = {}
        for pair in PAIRS:
            first, second = pair.split("-")
            tau_pair = max(taus[first], taus[second])
            burn_samples = int(math.ceil(5.0 * tau_pair / dt))
            window = wide.iloc[burn_samples:]
            rho = float(np.corrcoef(window[first], window[second])[0, 1]) if len(window) >= 3 else float("nan")
            after_s = max(0.0, duration - burn_samples * dt)
            n_eff = after_s / (2.0 * tau_pair)
            neff_pass = bool(np.isfinite(rho) and n_eff >= 25.0)
            burn_pass = bool(burn_samples * dt + 1e-12 >= 5.0 * tau_pair)
            all_neff_pass &= neff_pass
            all_burn_pass &= burn_pass
            pair_values[pair].append(rho)
            pair_results[pair] = {
                "r": round(rho, 6),
                "tau_pair_s": round(tau_pair, 6),
                "burn_samples": burn_samples,
                "burn_s": round(burn_samples * dt, 6),
                "samples_after_burn": len(window),
                "n_eff": round(n_eff, 3),
                "n_eff_pass": neff_pass,
                "burn_pass": burn_pass,
            }

        flows = meta["flow_engine"]
        edge_warm = {link: int(flows[link]["warm_start_active"]) for link in EDGE}
        expected_warm = {
            link: int(round(float(flows[link]["rho_target"]) ** 2 / float(flows[link]["sigma_target"]) ** 2))
            for link in EDGE
        }
        pc1 = all(abs(edge_warm[link] - expected_warm[link]) <= 1 for link in EDGE)
        pc3 = (
            abs(float(meta["core_sigma_target"]) - config["core_sigma"]) < 1e-12
            and abs(float(meta["edge_sigma_target"]) - config["edge_sigma"]) < 1e-12
            and abs(float(meta["duration_s"]) - config["duration"]) < 1e-12
            and int(meta["seed"]) == config["seeds"][rep - 1]
        )
        counter_clean &= missing_rows == 0
        runs.append(
            {
                "rep": rep,
                "seed": int(meta["seed"]),
                "trace": str(trace_path),
                "meta": str(meta_path),
                "dt_s": round(dt, 9),
                "duration_observed_s": round(duration, 6),
                "missing_or_incomplete_rows": missing_rows,
                "tau_by_link_s": {key: round(value, 6) for key, value in taus.items()},
                "edge_warm_start_active": edge_warm,
                "edge_warm_start_expected": expected_warm,
                "PC_C1_warm_start": pc1,
                "PC_C3_metadata": pc3,
                "pairs": pair_results,
            }
        )

    pooled = {pair: round(fisher_pool(values), 6) for pair, values in pair_values.items()}
    controls = {
        "NC_C1_ac_ad": -0.10 <= pooled["ac-ad"] <= 0.15,
        "NC_C1_bc_bd": -0.10 <= pooled["bc-bd"] <= 0.15,
        "NC_C2_uA_vC": -0.10 <= pooled["uA-vC"] <= 0.15,
    }
    baseline = baseline_edge_tau()
    current = {link: float(np.median([run["tau_by_link_s"][link] for run in runs])) for link in EDGE}
    ratios = {link: baseline[link] / current[link] for link in EDGE}
    required = 5.0 if args.cell_name == "cellC" else 2.0
    pc2 = bool(float(np.median(list(ratios.values()))) >= required)
    infra, infra_clean = read_infra(args.infra_glob)
    metadata_pass = all(bool(run["PC_C1_warm_start"] and run["PC_C3_metadata"]) for run in runs)
    valid = bool(
        all_neff_pass and all_burn_pass and all(controls.values()) and pc2
        and infra_clean and counter_clean and metadata_pass
    )
    return {
        "schema": "dt4n.phase_d.cell_analysis.v1",
        "status": "VALID" if valid else "INVALID_RUN",
        "cell": args.cell_name,
        "signed_estimator_tag": "phase-D-cellC-start",
        "runs": runs,
        "pooled_fisher_r": pooled,
        "controls": controls,
        "PC_C2_tau_reduction": {
            "baseline_edge_tau_s": {k: round(v, 6) for k, v in baseline.items()},
            "cell_edge_tau_s": {k: round(v, 6) for k, v in current.items()},
            "reduction_ratio": {k: round(v, 3) for k, v in ratios.items()},
            "required_median_ratio": required,
            "pass": pc2,
        },
        "validity": {
            "all_pairs_all_reps_n_eff_ge_25": all_neff_pass,
            "all_burn_ge_5tau": all_burn_pass,
            "controls_pass": all(controls.values()),
            "metadata_and_warm_start_pass": metadata_pass,
            "infra_all_four_flags_false": infra_clean,
            "counter_and_completeness_clean": counter_clean,
            "overall": valid,
        },
        "infra_summaries": infra,
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/phase_d_cell_analysis.py",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell-name", choices=tuple(EXPECTED), required=True)
    parser.add_argument("--cell-dir", required=True)
    parser.add_argument("--infra-glob", required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact = analyze(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": artifact["status"],
        "pooled_fisher_r": artifact["pooled_fisher_r"],
        "controls": artifact["controls"],
        "PC_C2": artifact["PC_C2_tau_reduction"],
        "validity": artifact["validity"],
    }, indent=2))


if __name__ == "__main__":
    main()

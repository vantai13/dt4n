#!/usr/bin/env python3
"""PC-C3: read pairwise r on cellA_long, the one single-variable experiment.

Signed design: ``docs/phase-D/00c-prereg-pc-c3.md``.

cellA_long holds sigma_edge = 0.03, so N_bar = 817 and the shared hsrc
endpoint are UNCHANGED from the phase-23 campaign that produced r = +0.5986.
The only thing that changed is the telemetry bundle (ditto sync agent, AoI
probe, cycle trace, reconcile_every 1 -> 30), which drops the measured nugget
from 0.632 to 0.136.  H4 predicts r survives; H6 and H0 predict it collapses.

No Mininet is run.  Nothing here reads Cell C frozen outcomes.

    python -m tools.phase_d_pc_c3
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from mininet.traffic_v7 import LOAD_CHANNELS

LINKS = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
PRIMARY = ("uA-uB", "vC-vD")
NC_C1 = ("ac-ad", "bc-bd")
NC_C2 = ("uA-vC",)

MEASURED = Path("results/RAW/phase-D/cellA_long/rho_measured_rep1.csv")
OFFERED = Path("results/RAW/phase-D/cellA_long/rho_offered_rep1.csv")
META = Path("results/RAW/phase-D/cellA_long/meta_rep1.json")
INFRA = Path("results/SMOKE/phase-D/infra_cellA_long_summary.json")
NUGGET = Path("results/SMOKE/phase-D/nugget_origin.json")
OUT = Path("results/SMOKE/phase-D/pc_c3_cellA_long.json")

# --- constants locked in 00c-prereg-pc-c3.md.  Not command-line flags. -----
NLAG_DIVISOR = 4
NLAG_CAP = 50_000
BURN_TAU_MULT = 5.0
N_EFF_MIN = 25.0
Z_CRIT = 1.959964
LOW_SIGMA = 0.03
NC_BAND = (-0.10, 0.15)
NC_C3_ABS_MAX = 0.15
# signed partition, applied per primary pair; exhaustive over the real line
BANDS = (
    (-np.inf, -0.10, "UNRESOLVED_OUT_OF_BAND"),
    (-0.10, 0.00, "H0"),
    (0.00, 0.10, "H6_H0_NOT_SEPARATED"),
    (0.10, 0.25, "H6"),
    (0.25, 0.45, "UNRESOLVED_GAP"),
    (0.45, 0.75, "H4"),
    (0.75, np.inf, "UNRESOLVED_OUT_OF_BAND"),
)
POINT_PREDICTIONS = {"H4": 0.60, "H6": 0.13, "H0": 0.0}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def band_label(r: float) -> str:
    """Signed partition of 00c section 3.  Exhaustive over the real line."""
    if not np.isfinite(r):
        return "UNRESOLVED_OUT_OF_BAND"
    if r < -0.10:
        return "UNRESOLVED_OUT_OF_BAND"
    if r < 0.00:
        return "H0"
    if r <= 0.10:
        return "H6_H0_NOT_SEPARATED"      # H6 and H0 bands overlap here
    if r <= 0.25:
        return "H6"
    if r < 0.45:
        return "UNRESOLVED_GAP"
    if r <= 0.75:
        return "H4"
    return "UNRESOLVED_OUT_OF_BAND"


def acf_prefix(values: np.ndarray, nlag: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    centered = values - float(values.mean())
    denominator = float(centered @ centered)
    if denominator <= 0:
        return np.concatenate(([1.0], np.zeros(nlag)))
    fft_len = 1 << (2 * len(centered) - 1).bit_length()
    spectrum = np.fft.rfft(centered, fft_len)
    autocov = np.fft.irfft(spectrum * np.conjugate(spectrum), fft_len)[: nlag + 1]
    return np.asarray(autocov / denominator, dtype=float)


def tau_int(values: np.ndarray, dt: float) -> float:
    nlag = min(len(values) // NLAG_DIVISOR, NLAG_CAP)
    curve = acf_prefix(values, nlag)
    cut = nlag
    for lag in range(1, len(curve)):
        if curve[lag] <= 0:
            cut = lag - 1
            break
    return float(dt * (0.5 + curve[1 : cut + 1].sum()))


def load_wide(path: Path, value_col: str) -> tuple[pd.DataFrame, float, float, int]:
    frame = pd.read_csv(path)
    if value_col not in frame:
        raise ValueError(f"{path}: no column {value_col}")
    missing = sorted(set(LINKS) - set(frame["link"].unique()))
    if missing:
        raise ValueError(f"{path}: missing links {missing}")
    if "tx_bytes_delta" in frame and bool((frame["tx_bytes_delta"] < 0).any()):
        raise ValueError(f"{path}: negative tx_bytes_delta (counter reset)")
    wide = frame.pivot(index="sample_index", columns="link", values=value_col).dropna()
    times = frame.groupby("sample_index")["timestamp_s"].first().loc[wide.index]
    dt = float(np.median(np.diff(times.to_numpy())))
    duration = float(times.iloc[-1] - times.iloc[0] + dt)
    dropped = int(len(frame) - len(wide) * len(LINKS))
    return wide, dt, duration, dropped


def all_pairs(
    wide: pd.DataFrame, dt: float, duration: float, design: dict[str, float]
) -> tuple[dict[str, float], dict[str, dict[str, object]]]:
    taus = {link: tau_int(wide[link].to_numpy(), dt) for link in LINKS}
    pairs: dict[str, dict[str, object]] = {}
    for i, first in enumerate(LINKS):
        for second in LINKS[i + 1 :]:
            tau_pair = max(taus[first], taus[second])
            burn_samples = int(math.ceil(BURN_TAU_MULT * tau_pair / dt))
            window = wide.iloc[burn_samples:]
            r = (
                float(np.corrcoef(window[first], window[second])[0, 1])
                if len(window) >= 3
                else float("nan")
            )
            burn_s = burn_samples * dt
            n_eff = (duration - burn_s) / (2.0 * tau_pair)
            if np.isfinite(r) and n_eff > 3.0:
                z = float(np.arctanh(np.clip(r, -0.999999, 0.999999)))
                se = 1.0 / math.sqrt(n_eff - 3.0)
                ci = [float(np.tanh(z - Z_CRIT * se)), float(np.tanh(z + Z_CRIT * se))]
            else:
                se, ci = float("nan"), [float("nan"), float("nan")]
            shared = sorted(set(LOAD_CHANNELS[first]) & set(LOAD_CHANNELS[second]))
            n_low = int(np.isclose(design[first], LOW_SIGMA)) + int(
                np.isclose(design[second], LOW_SIGMA)
            )
            pairs[f"{first}-{second}"] = {
                "r": r,
                "tau_pair_s": tau_pair,
                "burn_s": burn_s,
                "samples_after_burn": int(len(window)),
                "n_eff": n_eff,
                "n_eff_pass": bool(n_eff >= N_EFF_MIN),
                "diagnostic_only": bool(n_eff < N_EFF_MIN),
                "fisher_se_z": se,
                "ci95": ci,
                "shared_host": bool(shared),
                "shared_host_names": shared,
                "n_low_sigma": n_low,
            }
    return taus, pairs


def factorial(pairs: dict[str, dict[str, object]]) -> dict[str, dict[str, object]]:
    cells: dict[str, list[tuple[str, float]]] = {}
    for name, row in pairs.items():
        key = f"nlow{row['n_low_sigma']}_shared{int(bool(row['shared_host']))}"
        cells.setdefault(key, []).append((name, float(row["r"])))
    out = {}
    for key in sorted(cells, reverse=True):
        rows = cells[key]
        values = np.asarray([r for _, r in rows], dtype=float)
        fisher = np.arctanh(np.clip(values, -0.999999, 0.999999))
        out[key] = {
            "n": len(rows),
            "mean_r": float(values.mean()),
            "fisher_pooled_r": float(np.tanh(fisher.mean())),
            "min_r": float(values.min()),
            "max_r": float(values.max()),
            "pairs": [name for name, _ in rows],
        }
    return out


def main() -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    design = {link: float(meta["profile"][link]["sigma_target"]) for link in LINKS}
    infra = json.loads(INFRA.read_text(encoding="utf-8"))
    infra_clean = not any(v for k, v in infra.items() if k.startswith("flag_"))

    measured_wide, m_dt, m_dur, m_dropped = load_wide(MEASURED, "rho")
    taus, pairs = all_pairs(measured_wide, m_dt, m_dur, design)
    cells = factorial(pairs)

    offered_wide, o_dt, o_dur, o_dropped = load_wide(OFFERED, "rho_offered")
    _o_taus, offered_pairs = all_pairs(offered_wide, o_dt, o_dur, design)

    # ---------------------------------------------------------- controls
    nc_c1 = {p: pairs[p]["r"] for p in NC_C1}
    nc_c2 = {p: pairs[p]["r"] for p in NC_C2}
    nc_c1_pass = all(NC_BAND[0] <= v <= NC_BAND[1] for v in nc_c1.values())
    nc_c2_pass = all(NC_BAND[0] <= v <= NC_BAND[1] for v in nc_c2.values())
    nc_c3 = {p: offered_pairs[p]["r"] for p in PRIMARY + NC_C1 + NC_C2}
    nc_c3_pass = all(abs(v) <= NC_C3_ABS_MAX for v in nc_c3.values())

    # ------------------------------------------------------ adjudication
    per_primary = {}
    for pair in PRIMARY:
        row = pairs[pair]
        per_primary[pair] = {
            "r": row["r"],
            "ci95": row["ci95"],
            "n_eff": row["n_eff"],
            "diagnostic_only": row["diagnostic_only"],
            "band": band_label(float(row["r"])),
        }
    usable = [p for p in PRIMARY if not per_primary[p]["diagnostic_only"]]
    labels = {per_primary[p]["band"] for p in usable}
    if not usable:
        verdict = "UNDERPOWERED_NO_VERDICT"
    elif len(labels) == 1 and next(iter(labels)) in {"H4", "H6", "H0"}:
        verdict = next(iter(labels))
    elif len(labels) > 1:
        verdict = "PRIMARY_REPLICATES_DISAGREE"
    else:
        verdict = "UNRESOLVED"

    controls_pass = bool(
        infra_clean and nc_c1_pass and nc_c2_pass and nc_c3_pass
        and m_dropped == 0 and o_dropped == 0
    )
    if not controls_pass:
        verdict_final = "REANALYSIS_INVALID_OR_INCOMPLETE"
    else:
        verdict_final = verdict

    nugget = json.loads(NUGGET.read_text(encoding="utf-8"))
    artifact = {
        "schema": "dt4n.phase_d.pc_c3.v1",
        "status": "CONFIRMATORY_SECONDARY_ANALYSIS",
        "preregistration": "docs/phase-D/00c-prereg-pc-c3.md",
        "signed_tag": "phase-D-pc-c3-start",
        "no_correlation_computed_before_signing": True,
        "no_new_mininet": True,
        "design_contrast": {
            "note": (
                "sigma_edge, N_bar and the shared hsrc endpoint are held fixed "
                "against the phase-23 campaign; only the telemetry bundle changed"
            ),
            "edge_sigma": LOW_SIGMA,
            "edge_N_bar": {
                link: round(meta["profile"][link]["n_concurrent"])
                for link in ("uA", "uB", "vC", "vD")
            },
            "ditto": meta["ditto"],
            "reconcile_every": meta["reconcile_every"],
            "aoi_probe": meta["aoi_probe_out"],
            "sf_phase23": nugget["comparison"]["sf_cellA_phase23_T120_ditto_on"],
            "sf_cellA_long": nugget["comparison"]["sf_cellA_long_T1505_ditto_off"],
            "phase23_reference_r": {"uA-uB": 0.5986, "vC-vD": 0.6376},
        },
        "locked_constants": {
            "nlag": f"min(n//{NLAG_DIVISOR}, {NLAG_CAP})",
            "burn_tau_mult": BURN_TAU_MULT,
            "n_eff_min": N_EFF_MIN,
            "bands": [[None if np.isinf(lo) else lo, None if np.isinf(hi) else hi, lab]
                      for lo, hi, lab in BANDS],
            "point_predictions": POINT_PREDICTIONS,
            "nc_band": list(NC_BAND),
            "nc_c3_abs_max": NC_C3_ABS_MAX,
        },
        "measured": {
            "path": str(MEASURED), "dt_s": m_dt, "duration_s": m_dur,
            "n_samples": int(len(measured_wide)), "dropped_rows": m_dropped,
            "tau_by_link_s": taus, "pairs": pairs, "factorial_cells": cells,
        },
        "offered_control": {
            "path": str(OFFERED), "dt_s": o_dt, "duration_s": o_dur,
            "n_samples": int(len(offered_wide)), "dropped_rows": o_dropped,
            "pairs": offered_pairs,
        },
        "controls": {
            "infra_all_flags_false": infra_clean,
            "NC_C1": {"values": nc_c1, "band": list(NC_BAND), "pass": nc_c1_pass},
            "NC_C2": {"values": nc_c2, "band": list(NC_BAND), "pass": nc_c2_pass},
            "NC_C3_offered": {"values": nc_c3, "abs_max": NC_C3_ABS_MAX, "pass": nc_c3_pass},
            "all_pass": controls_pass,
        },
        "adjudication": {
            "per_primary": per_primary,
            "verdict": verdict_final,
            "raw_verdict_before_controls": verdict,
            "H4_survives": bool(verdict_final == "H4"),
            "H4_refuted": bool(verdict_final in {"H6", "H0", "H6_H0_NOT_SEPARATED"}),
            "cell_C_status_unchanged": "INVALID_RUN",
            "note": (
                "PC-C3 has power to confirm or refute H4; it has NO power to "
                "separate H6 from H0 (D-L29)."
            ),
        },
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/phase_d_pc_c3.py",
            "inputs_sha256": {str(p): sha256(p) for p in (MEASURED, OFFERED, META)},
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("=" * 74)
    print("PC-C3  |  cellA_long  |  sigma=0.03, N_bar=817, hsrc chung  (H4 nguyen ven)")
    print("       |  bundle telemetry TAT -> nugget 0.632 -> 0.136     (H6 doi)")
    print("=" * 74)
    print("%-8s %9s %9s %20s %8s  %s" % ("pair", "r", "n_eff", "CI95", "diag", "band"))
    for pair in PRIMARY + NC_C1 + NC_C2:
        row, pp = pairs[pair], per_primary.get(pair)
        ci = row["ci95"]
        print("%-8s %+9.4f %9.2f  [%+.4f,%+.4f] %8s  %s"
              % (pair, row["r"], row["n_eff"], ci[0], ci[1],
                 row["diagnostic_only"], pp["band"] if pp else "-"))
    print()
    print("moc phase-23 cung sigma, bundle BAT:  uA-uB +0.5986   vC-vD +0.6376")
    print()
    print("doi chung OFFERED (cung run, NC-C3):")
    for pair in PRIMARY + NC_C1 + NC_C2:
        print("   %-8s r = %+.4f" % (pair, offered_pairs[pair]["r"]))
    print()
    print("giai thua 2x2 tren rho_measured:")
    print("   %-16s %4s %10s %10s" % ("cell", "n", "mean_r", "fisher_r"))
    for key, cell in cells.items():
        print("   %-16s %4d %+10.4f %+10.4f" % (key, cell["n"], cell["mean_r"], cell["fisher_pooled_r"]))
    print()
    print("controls: infra=%s NC-C1=%s NC-C2=%s NC-C3=%s -> all_pass=%s"
          % (infra_clean, nc_c1_pass, nc_c2_pass, nc_c3_pass, controls_pass))
    print(">>> PHAN QUYET PC-C3 = %s" % verdict_final)
    print("artifact: %s" % OUT)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""D-A002 post-hoc diagnosis: where does the measured-rho nugget come from?

`acf_nugget` (A080) measured median edge signal fraction 0.3696 on the
phase-23 campaign, i.e. ~63% of measured variance is nugget.  That number
anchors D-L20 and H6.  The new `cellA_long` run has the SAME edge sigma but a
different runner configuration, and returns ~0.86.

Two candidate explanations are separated here:

  (a) trace length -- 120 s vs 1505 s;
  (b) the phase-23 instrumentation bundle -- ditto sync agent with
      reconcile_every=1, AoI probe and cycle trace, all absent from cellA_long.

(a) is testable with no new data at all: cut `cellA_long` into 120 s windows
and re-run the signed A080 estimator on them.

STATUS: POST_HOC_DIAGNOSIS.  Adjudicates nothing, changes no threshold, and is
not a control for any signed gate.

    python -m tools.phase_d_nugget_origin
"""
from __future__ import annotations

import glob
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from measurements import acf_nugget as N
from measurements import link_corr_matrix as L

EDGE = ("uA", "uB", "vC", "vD")
OUT = Path("results/SMOKE/phase-D/nugget_origin.json")
DT = L.DT_MEASURED_S
WINDOW_DURATIONS_S = (120, 240, 400, 750)
REPORT_LAGS = (1, 2, 3, 5, 10, 20, 30, 50, 100, 200, 300)

TRACES = {
    "cellA_long": {
        "glob": "results/RAW/phase-D/cellA_long/rho_measured_rep1.csv",
        "edge_sigma": 0.03, "duration_s": 1505, "ditto": False,
        "aoi_probe": False, "reconcile_every": 30,
    },
    "cellA_phase23": {
        "glob": "results/RAW/phase-23/aoi_v7_campaign/rho_measured_clean_rho0.925_rep*.csv",
        "edge_sigma": 0.03, "duration_s": 120, "ditto": True,
        "aoi_probe": True, "reconcile_every": 1,
    },
    "cellC": {
        "glob": "results/RAW/phase-D/cellC/rho_measured_rep*.csv",
        "edge_sigma": 0.10, "duration_s": 240, "ditto": False,
        "aoi_probe": False, "reconcile_every": 30,
    },
}


def a080_edge_fits(matrices: list[np.ndarray]) -> dict[str, object]:
    """The A080 estimator exactly as signed: FIT_LAGS 1..20, no clamping."""
    per_link = {}
    for link in EDGE:
        curve = N._mean_acf(matrices, L.IDX[link], N.FIT_LAGS)
        fit = N.fit_nugget(curve, N.FIT_LAGS)
        per_link[link] = {
            "signal_fraction_raw": float(fit["signal_fraction_raw"]),
            "valid_under_A080": bool(fit["valid"]),
            "tau_measured_s": fit["tau_measured_s"],
        }
    raws = [per_link[link]["signal_fraction_raw"] for link in EDGE]
    return {
        "per_link": per_link,
        "median_edge_signal_fraction_raw": float(np.median(raws)),
    }


def main() -> None:
    traces: dict[str, object] = {}
    for name, spec in TRACES.items():
        paths = sorted(glob.glob(spec["glob"]))
        if not paths:
            raise FileNotFoundError(spec["glob"])
        matrices = [L.load_run(path) for path in paths]
        curves = {
            link: {
                str(lag): float(value)
                for lag, value in zip(REPORT_LAGS, N._mean_acf(matrices, L.IDX[link], REPORT_LAGS))
            }
            for link in EDGE
        }
        traces[name] = {
            "config": {k: v for k, v in spec.items() if k != "glob"},
            "paths": paths,
            "n_samples_per_rep": [int(m.shape[0]) for m in matrices],
            "acf_by_lag": curves,
            "acf_lag1_by_link": {link: curves[link]["1"] for link in EDGE},
            **a080_edge_fits(matrices),
        }

    # ---- control (a): same trace, shorter windows.  No new data involved.
    long_matrix = L.load_run(TRACES["cellA_long"]["glob"])
    windows = {}
    for duration in WINDOW_DURATIONS_S:
        size = int(round(duration / DT))
        chunks = [
            long_matrix[start : start + size]
            for start in range(0, long_matrix.shape[0] - size + 1, size)
        ]
        if not chunks:
            continue
        per_window = [a080_edge_fits([chunk])["median_edge_signal_fraction_raw"] for chunk in chunks]
        windows[f"{duration}s"] = {
            "window_duration_s": duration,
            "n_windows": len(chunks),
            "samples_per_window": size,
            "pooled_median_signal_fraction_raw": a080_edge_fits(chunks)[
                "median_edge_signal_fraction_raw"
            ],
            "per_window_median": float(np.median(per_window)),
            "per_window_min": float(min(per_window)),
            "per_window_max": float(max(per_window)),
        }

    sf_long = traces["cellA_long"]["median_edge_signal_fraction_raw"]
    sf_p23 = traces["cellA_phase23"]["median_edge_signal_fraction_raw"]
    sf_120_windows = windows["120s"]["pooled_median_signal_fraction_raw"]
    trace_length_explains = bool(abs(sf_120_windows - sf_p23) < 0.15)

    artifact = {
        "schema": "dt4n.phase_d.nugget_origin.v1",
        "status": "POST_HOC_DIAGNOSIS_NOT_CONFIRMATORY",
        "amendment": "docs/phase-D/A002-amendment-pc-c2-prime.md",
        "question": (
            "Is the 0.3696 phase-23 nugget caused by trace length, or by the "
            "phase-23 instrumentation bundle (ditto + AoI probe + reconcile_every=1)?"
        ),
        "locked_constants": {
            "estimator": "measurements.acf_nugget.fit_nugget, FIT_LAGS 1..20, unclamped",
            "dt_measured_s": DT,
            "window_durations_s": list(WINDOW_DURATIONS_S),
        },
        "traces": traces,
        "cellA_long_windowed": windows,
        "comparison": {
            "sf_cellA_phase23_T120_ditto_on": sf_p23,
            "sf_cellA_long_T1505_ditto_off": sf_long,
            "sf_cellA_long_cut_to_T120_ditto_off": sf_120_windows,
            "trace_length_explains_phase23_nugget": trace_length_explains,
            "conclusion": (
                "trace length explains it"
                if trace_length_explains
                else "trace length does NOT explain it; the difference tracks the "
                     "phase-23 instrumentation bundle, which stays confounded "
                     "(ditto + probe + cycle trace + reconcile_every all differ)"
            ),
        },
        "provenance": {
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/phase_d_nugget_origin.py",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("%-16s %7s %7s %7s %9s   %s" % ("trace", "sigma_e", "T(s)", "ditto", "ACF(0.2s)", "sf(A080)"))
    for name, row in traces.items():
        lag1 = float(np.median(list(row["acf_lag1_by_link"].values())))
        print("%-16s %7.2f %7d %7s %9.3f   %.4f"
              % (name, row["config"]["edge_sigma"], row["config"]["duration_s"],
                 row["config"]["ditto"], lag1, row["median_edge_signal_fraction_raw"]))
    print()
    print("control (a) -- cellA_long cut into shorter windows, ditto still OFF:")
    for key, row in windows.items():
        print("  window %-6s x%-3d  pooled sf = %.4f   per-window median = %.4f  [%.3f, %.3f]"
              % (key, row["n_windows"], row["pooled_median_signal_fraction_raw"],
                 row["per_window_median"], row["per_window_min"], row["per_window_max"]))
    print()
    print("phase-23 (T=120 s, ditto ON)  sf = %.4f" % sf_p23)
    print("cellA_long cut to T=120 s     sf = %.4f" % sf_120_windows)
    print("=> trace length explains the phase-23 nugget: %s" % trace_length_explains)
    print("artifact: %s" % OUT)


if __name__ == "__main__":
    main()

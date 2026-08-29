#!/usr/bin/env python3
"""D.3/L141 sensitivity of the live SNR decision to traffic family.

The live load-bearing claim that passes through ``link_model_v2`` is T6's
SNR-based D1/D2/D3 budget decision.  Sweep categorical traffic family rather
than treating ``c_a`` as a sufficient scalar statistic.
"""
from __future__ import annotations

import glob
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from measurements import link_corr_matrix as L
from twin import cost_v2 as C
from twin import topology_v7 as T7
from twin.link_model_v2 import LinkModelV2


FIT = "results/LIVE/phase-L/link_model_v2_fit.json"
BASELINE_ARTIFACT = "results/LIVE/phase-23/link_corr_matrix.json"
OUT = Path("results/SMOKE/phase-D/family_sensitivity.json")
CAMPAIGN = "results/RAW/phase-23/aoi_v7_campaign"
MODES = ("cbr", "poisson", "h2")
BASELINE = "poisson"


def load_campaign() -> tuple[list[np.ndarray], list[str]]:
    paths = sorted(glob.glob(f"{CAMPAIGN}/rho_measured_clean_*.csv"))
    if len(paths) != 15:
        raise ValueError(f"expected 15 CLEAN measured traces, found {len(paths)}")
    return [L.load_run(path) for path in paths], [L.cell_of(path) for path in paths]


def snr_for_mode(mats: list[np.ndarray], cells: list[str], mode: str) -> dict[str, object]:
    model = C.CostV2(strict_reliable=False)
    accum: dict[str, list[float]] = defaultdict(list)
    for matrix, cell in zip(mats, cells):
        clipped = np.clip(matrix, C.RHO_MIN, C.RHO_MAX)
        _delay, _loss, cost = model.tables_batch(clipped, mode, L.W_LOSS)
        for first, second in L.PATH_PAIRS:
            margin = (
                cost[:, T7.PATH_NAMES.index(first)] - cost[:, T7.PATH_NAMES.index(second)]
            )
            sd = float(margin.std(ddof=1))
            if sd > 0:
                accum[f"{cell}|m({first},{second})"].append(abs(float(margin.mean())) / sd)
    values = {key: float(np.mean(reps)) for key, reps in sorted(accum.items())}
    finite = list(values.values())
    median = float(np.median(finite))
    cell_values: dict[str, list[float]] = defaultdict(list)
    for key, value in values.items():
        cell_values[key.split("|", 1)[0]].append(value)
    cell_medians = {key: float(np.median(vals)) for key, vals in sorted(cell_values.items())}
    selected = max(cell_medians, key=cell_medians.get)
    other_max = max(value for key, value in cell_medians.items() if key != "clean@0.960")
    claims = {
        "above_D1_boundary": median - L.SNR_FLAT,
        "below_D2_boundary": L.SNR_STRONG - median,
        "clean_0.960_is_highest_cell": cell_medians["clean@0.960"] - other_max,
    }
    if median <= L.SNR_FLAT:
        decision = "D1_DO_NOT_OPEN_23_26_AS_MININET_CAMPAIGN"
    elif median >= L.SNR_STRONG:
        decision = "D2_OPEN_23_26_FULL"
    else:
        decision = "D3_OPEN_23_26_REDUCED_HIGHEST_SNR_CELL_ONLY"
    return {
        "snr_by_cell_and_pair": values,
        "snr_median": median,
        "snr_min": min(finite),
        "snr_max": max(finite),
        "snr_cell_median": cell_medians,
        "selected_highest_cell": selected,
        "decision": decision,
        "signed_claim_margins": claims,
    }


def main() -> None:
    mats, cells = load_campaign()
    sweep = {mode: snr_for_mode(mats, cells, mode) for mode in MODES}
    old = json.loads(Path(BASELINE_ARTIFACT).read_text(encoding="utf-8"))["T6_snr_and_decision"]
    current = sweep[BASELINE]
    baseline_exact = (
        current["snr_by_cell_and_pair"] == old["snr_by_cell_and_pair"]
        and current["snr_median"] == old["snr_median"]
        and current["decision"] == old["decision_for_lesson_23_26"]
    )

    claims: dict[str, dict[str, object]] = {}
    for claim in current["signed_claim_margins"]:
        values = {mode: float(sweep[mode]["signed_claim_margins"][claim]) for mode in MODES}
        signs = {int(np.sign(value)) for value in values.values() if abs(value) > 1e-12}
        claims[claim] = {
            "values": {mode: round(value, 6) for mode, value in values.items()},
            "sign_stable": len(signs) <= 1,
            "verdict": "ROBUST" if len(signs) <= 1 else "FRAGILE_SIGN_CHANGE",
        }

    lm = LinkModelV2.load(FIT)
    pc_delays = {mode: lm.predict_delay(mode, 6, 13, 0.90) for mode in MODES}
    pc_pass = pc_delays["cbr"] < pc_delays["poisson"] < pc_delays["h2"]
    onoff = lm.predict_delay("onoff", 6, 13, 0.90)
    decisions = {mode: sweep[mode]["decision"] for mode in MODES}
    robust = bool(
        baseline_exact
        and pc_pass
        and all(row["sign_stable"] for row in claims.values())
        and len(set(decisions.values())) == 1
        and set(row["selected_highest_cell"] for row in sweep.values()) == {"clean@0.960"}
    )
    artifact = {
        "schema": "dt4n.phase_d.family_sensitivity.v1",
        "status": "SENSITIVITY_ANALYSIS",
        "note": "Sweep MODE, not scalar c_a; Amendment 7 shows c_a is not sufficient.",
        "load_bearing_source": "link_corr_matrix.json::T6_snr_and_decision",
        "modes_full_grid": list(MODES),
        "modes_spot_only": {"onoff": "only onoff|6|13 exists"},
        "theory_prior": {
            "palm_khintchine": "N_bar in [95,875] superposed flows implies approximately Poisson",
            "kingman_factor": {"cbr": 0.40, "poisson": 0.90, "h2": 2.40},
            "c_s_pareto_2.5": 0.894,
        },
        "PC_D3_1": {
            "rho": 0.90,
            "delays_ms": {key: round(value, 6) for key, value in pc_delays.items()},
            "expect": "cbr < poisson < h2",
            "pass": pc_pass,
        },
        "NC_D3_1": {
            "mode": BASELINE,
            "bit_exact_full_30_values_median_and_decision": baseline_exact,
        },
        "claims": claims,
        "sweep": sweep,
        "decisions": decisions,
        "spot_check": {"onoff": {"delay_at_0.90_ms": round(onoff, 6)}},
        "verdict": {
            "all_load_bearing_claims_robust": robust,
            "L141": "CLOSED_BY_SENSITIVITY" if robust else "REMAINS_OPEN",
            "limitation": (
                "Three full-grid families do not prove invariance over every possible family; "
                "onoff is only a 6 Mbps/queue-13 spot check."
            ),
        },
        "provenance": {
            "fit_path": FIT,
            "git_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
            ).stdout.strip(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "script": "tools/phase_d_family_sensitivity.py",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "PC": artifact["PC_D3_1"],
        "NC": artifact["NC_D3_1"],
        "claims": claims,
        "decisions": decisions,
        "spot": artifact["spot_check"],
        "verdict": artifact["verdict"],
    }, indent=2))


if __name__ == "__main__":
    main()

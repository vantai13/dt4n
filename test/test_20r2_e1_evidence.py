"""E1 evidence: provenance, actual flip witnesses and controls of the bounds."""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import numpy as np
import pytest

from measurements.decision_error_v2 import TruthTable
from twin import topology_v7 as T7

ROOT = Path(__file__).resolve().parents[1]
MECH = importlib.import_module("tools.20r2_9_e1_mechanics")


@pytest.mark.parametrize("name", ["E1-mechanics", "E1b-partition-invariance"])
def test_evidence_pins_actual_inputs_and_source(name):
    data = json.loads((ROOT / "docs/phase-20R2" / (name + ".json")).read_text())
    assert "generated_utc" not in data and "git_commit" not in data
    assert "results/LIVE/phase-20R/truth_table.parquet" in data["inputs_sha256"]
    for section in ("inputs_sha256", "source_sha256"):
        for rel, expected in data[section].items():
            assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == expected, rel


def test_h2_positive_control_has_recomputable_different_winners():
    data = json.loads((ROOT / "docs/phase-20R2/E1-mechanics.json").read_text())
    control = data["C_cbr_mechanism"]["flip_analysis"]["h2"]
    assert control["argmin_can_flip"]
    assert not control["delay_only_bound_applies_to_full_cost"]
    tt = TruthTable(str(MECH.TRUTH))
    winners = set()
    for w in control["flip_witnesses"]:
        rho = np.array([[w["rho_by_link"][link] for link in T7.LINK_NAMES]])
        _, _, cost = tt.path_tables("h2", rho, MECH.W_LOSS)
        np.testing.assert_array_equal(cost[0], w["path_cost_ms"])
        winner = T7.PATH_NAMES[int(cost[0].argmin())]
        assert winner == w["winner"]
        winners.add(winner)
    assert len(winners) > 1


@pytest.mark.parametrize("mutation", ["none", "varying_loss", "large_delay_span"])
def test_cbr_certificate_rejects_violated_bound_assumptions(mutation):
    tt = TruthTable(str(MECH.TRUTH))
    for key, (grid, delay, loss, se) in list(tt.curves.items()):
        if key[0] != "cbr":
            continue
        if mutation == "varying_loss":
            loss = np.linspace(0.0, 0.1, len(loss))
        elif mutation == "large_delay_span":
            delay = delay + np.linspace(0.0, 100.0, len(delay))
        tt.curves[key] = (grid, delay, loss, se)
    c = MECH.block_c(tt)["flip_analysis"]["cbr"]
    assert c["argmin_invariance_certified"] == (mutation == "none")


def test_quasi_static_screen_depends_on_declared_convention(monkeypatch):
    baseline = MECH.block_d()["verdict_by_rho_bar"]
    monkeypatch.setattr(MECH, "QS_MARGIN", 10.0)
    stricter = MECH.block_d()["verdict_by_rho_bar"]
    for rho, row in baseline.items():
        assert stricter[rho]["T_relax_worst_s"] == row["T_relax_worst_s"]
        assert stricter[rho]["tau_min_safe_s"] == 2 * row["tau_min_safe_s"]
        assert set(row["tau_violating_quasi_static"]) <= set(
            stricter[rho]["tau_violating_quasi_static"])
    assert stricter["0.925"]["n_tau_violating"] > baseline["0.925"]["n_tau_violating"]


def test_cost_share_is_composition_of_all_path_means():
    data = json.loads((ROOT / "docs/phase-20R2/E1-mechanics.json").read_text())
    block = data["E_cost_composition"]
    assert len(block["rows"]) == 16
    for r in block["rows"]:
        d, loss = r["delay_ms_mean"], r["w_loss_term_ms_mean"]
        assert r["loss_share_of_cost"] == pytest.approx(loss / (d + loss))
    assert sum(r["loss_share_of_cost"] >= 0.5 for r in block["rows"]) == 14


def test_partition_keeps_roles_while_criterion_changes():
    p = json.loads((ROOT / "docs/phase-20R2/E1b-partition-invariance.json").read_text())
    assert p["P1_role_is_carried_verbatim_into_exogenous"]["verdict"] == "CARRIED"
    assert p["P2_partition_equals_axis_free_predicate"]["n_match"] == 12
    flips = [r["cell"] for r in p["rows"] if r["feasible"]
             and r["in_band_self_calibrated"] != r["in_band_exogenous"]]
    assert len(flips) == 8
    assert p["P3_negative_control_in_band_is_NOT_invariant"]["flipped_cells"] == flips

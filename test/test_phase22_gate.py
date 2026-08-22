"""Golden tests for cert.gate_report_22 -- Phase 22 Lesson 22.8."""

import os

import pytest

from cert import gate_report_22 as G


MAIN = "results/SUPERSEDED/phase-22/config_matrix_poisson_0.925.json"
pytestmark = pytest.mark.skipif(not os.path.exists(MAIN), reason="thieu Phase 22 artifacts")


@pytest.fixture(scope="module")
def rep():
    return G.build_report("poisson_0.925")


def test_GG1_missing_artifacts_are_not_run_not_pass():
    report = G.build_report("poisson_0.925", artifacts={})
    assert {row["status"] for row in report["gates"]} == {"NOT_RUN"}
    assert report["gate_summary"]["decision"] == "INCOMPLETE"
    assert report["gate_summary"]["gates_not_run_count"] == len(G.GATE_SPECS)


def test_GG2_main_gate_report_passes_all_17(rep):
    assert len(rep["gates"]) == 17
    assert rep["gate_summary"]["gates_pass"] == 17
    assert rep["gate_summary"]["gates_total"] == 17
    assert rep["gate_summary"]["decision"] == "GO"


def test_GG3_no_blocking_or_not_run_gates(rep):
    assert rep["gate_summary"]["gates_blocking"] == []
    assert rep["gate_summary"]["gates_not_run"] == []
    assert {row["status"] for row in rep["gates"]} == {"PASS"}


def test_GG4_missed_predictions_are_still_in_the_table(rep):
    ids = {row["id"] for row in rep["scorecard"]}
    assert {"M%d" % i for i in range(1, 11)} <= ids
    assert len(rep["scorecard"]) == 32
    assert rep["prediction_summary"]["n_hit"] == 21
    assert rep["prediction_summary"]["n_miss"] == 11


def test_GG5_prediction_hit_rate_is_reported_not_a_gate():
    gates = [{"id": "G", "status": "PASS"}]
    prediction_summary = {"n_hit": 0, "n_miss": 32, "n_scored": 32, "hit_rate": 0.0}
    decision = G.decision_from_gate_rows(gates, prediction_summary)
    assert decision["decision"] == "GO"
    assert decision["predictions_hit"] == 0


def test_GG6_prediction_hit_rates_by_lesson_are_locked(rep):
    assert rep["prediction_summary"]["hit_rate"] == pytest.approx(21 / 32)
    assert rep["prediction_summary"]["hit_rate_by_lesson"] == {
        "22.3": "4/7",
        "22.4": "5/6",
        "22.5": "2/7",
        "22.6": "7/7",
        "22.7": "3/5",
    }


def test_GG7_phase_statement_and_conditions_are_serialized(rep):
    op = rep["phase_statement"]["operating_point"]
    assert op["acceptance"] == pytest.approx(0.4911, abs=2e-3)
    assert op["err_given_accept"] == pytest.approx(0.0809, abs=2e-3)
    assert op["risk_ratio_vs_anchor"] == pytest.approx(0.364, abs=0.01)
    assert op["violation_given_accept"] == pytest.approx(0.0794, abs=2e-3)
    m4 = next(row for row in rep["scorecard"] if row["id"] == "M4")
    assert m4["observed"] == pytest.approx(1.2980, abs=2e-3)
    assert [row["id"] for row in rep["go_conditions"]] == ["GO-1", "GO-2", "GO-3"]
    assert rep["go_conditions"][2]["status"] == "FUTURE_WORK"

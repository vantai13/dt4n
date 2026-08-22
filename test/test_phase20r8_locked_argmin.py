#!/usr/bin/env python3
"""Guard tests for Lesson 20R.8 locked-argmin mechanism."""

import pytest

pd = pytest.importorskip("pandas")

from measurements import locked_argmin_check as LA


@pytest.fixture(scope="module")
def report():
    return LA.run(
        [0.635, 0.650, 0.700, 0.850, 0.925],
        ["poisson", "h2"],
        [101, 102],
        n=40_000,
    )


def test_every_measured_zero_error_cell_has_a_locking_mechanism(report):
    df = pd.read_parquet("results/SUPERSEDED/phase-20R/decision_error_unimodal.parquet")
    df = df[df.z_key == "0.550"]
    zero = df.groupby(["mode", "rho_bar"])["err_total"].mean()
    zero = zero[zero == 0.0]

    by_cell = {}
    for row in report["rows"]:
        if row.get("feasible"):
            by_cell.setdefault((row["mode"], round(row["rho_bar"], 3)), []).append(
                row["argmin_locked"]
            )

    for mode, rho_bar in zero.index:
        key = (str(mode), round(float(rho_bar), 3))
        if key not in by_cell:
            continue
        assert all(by_cell[key]), (
            "cell %s@%.3f has err = 0 but argmin is not locked" % key
        )


def test_locked_cells_have_one_optimal_path(report):
    locked = [row for row in report["rows"] if row.get("feasible") and row["argmin_locked"]]
    for row in locked:
        assert row["n_distinct_optimal_paths"] == 1


def test_lock_ratio_matches_definition(report):
    for row in report["rows"]:
        if not row.get("feasible"):
            continue
        expect = row["min_cost_gap_ms"] / max(row["max_abs_twin_error_ms"], 1e-12)
        assert row["lock_ratio"] == pytest.approx(expect, rel=1e-9)
        assert row["argmin_locked"] == (row["lock_ratio"] > 1.0)


def test_report_does_not_drop_cells_silently(report):
    assert report["summary"]["n_cells"] > 0
    assert (
        report["summary"]["n_locked"] + report["summary"]["n_unlocked"]
        == report["summary"]["n_cells"]
    )

#!/usr/bin/env python3
"""Tests for Phase 20 replicate-summary statistics."""

import pytest

from measurements import summarize_decision_error_replicates as SR


def test_summarize_metric_reports_single_trace_and_mean_uncertainty():
    rows = [
        {"d_sla": 0.07286908077994428, "d_sla_within_se": 0.004304077875395108},
        {"d_sla": 0.08552228412256269, "d_sla_within_se": 0.005001894747925632},
        {"d_sla": 0.0843941504178273, "d_sla_within_se": 0.00508392297336062},
    ]

    result = SR.summarize_metric("d_sla", rows, threshold=0.03)

    assert result["between_trace_sd"] == pytest.approx(0.00700242185061072)
    assert result["within_trace_se_rms"] == pytest.approx(0.0048093766133063985)
    assert result["se_single_measurement"] == pytest.approx(0.00849494056380202)
    assert result["se_mean"] == pytest.approx(0.004904556221260968)
    assert result["t_crit_975"] == pytest.approx(4.302652729911275)
    assert result["ci95_mean_t"]["lo"] == pytest.approx(0.05982590289236625)
    assert result["ci95_mean_t"]["hi"] == pytest.approx(0.10203110732118992)
    assert result["mean_t_lower_ge_threshold"] is True


def test_sd_chi_square_ci95_for_df2():
    result = SR.sd_chi_square_ci95(0.00700242185061072, df=2)

    assert result["lo"] == pytest.approx(0.003645868823432902)
    assert result["hi"] == pytest.approx(0.044008363563960574)

#!/usr/bin/env python3
"""Guard tests for Lesson 20R.8 QS-LOSS closure."""

import json

import pytest

from measurements import qs_loss_residual as QL


def test_qs_loss_reconstructs_the_phase_t_trajectory():
    rows = json.load(open("results/phase-T/campaign_state.json", encoding="utf-8"))["rows"]
    row = next(
        r
        for r in rows
        if r.get("block") != "S"
        and str(r.get("mode")) == "poisson"
        and float(r.get("a")) == 0.9
    )

    terms = QL.LossResidualCalculator().row_terms(row)

    assert terms["trajectory_digest_ok"]
    assert 0.0 <= terms["packet_weighted_qs_loss"] <= 1.0
    assert terms["packet_weighted_qs_loss"] != pytest.approx(
        terms["time_weighted_qs_loss"]
    )


def test_qs_loss_artifact_closes_poisson_but_not_h2():
    report = json.load(open("results/phase-20R/qs_loss_residual.json", encoding="utf-8"))
    poisson = report["summary"]["headline"]["poisson_a0p9"]
    h2 = report["summary"]["headline"]["h2_a0p9"]

    assert report["summary"]["n_digest_fail"] == 0
    assert poisson["verdict"] == "PASS"
    assert h2["verdict"] == "KHONG_KET_LUAN_DUOC"

    lo, hi = poisson["seed_cluster_packet_weighted_normal"]["ci95_normal"]
    assert lo >= QL.LOSS_SUP_NEG
    assert hi <= QL.LOSS_SUP_POS

    h2_lo, _h2_hi = h2["seed_cluster_packet_weighted_normal"]["ci95_normal"]
    assert h2_lo < QL.LOSS_SUP_NEG


def test_qs_loss_a09_is_larger_than_a02_for_poisson():
    report = json.load(open("results/phase-20R/qs_loss_residual.json", encoding="utf-8"))
    mode_a = report["summary"]["mode_a"]
    a02 = mode_a["mode=poisson,a=0.2"]["seed_cluster_packet_weighted_normal"]["mean"]
    a09 = mode_a["mode=poisson,a=0.9"]["seed_cluster_packet_weighted_normal"]["mean"]

    assert abs(a09) > 20.0 * abs(a02)

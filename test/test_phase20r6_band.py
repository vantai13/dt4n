#!/usr/bin/env python3
"""Guard tests for Lesson 20R.6-v2."""

import json
import math
from pathlib import Path

import numpy as np
import pytest

from measurements import cascade_residual as CR
from measurements import band_v2 as B2
from measurements import decision_error_v2 as D
from measurements import residual_spec as RS
from tools import pilot_power_only as PPO
from twin import cost_v2 as C
from twin import topology_v7 as T7


def test_residual_requires_written_estimand():
    with pytest.raises(ValueError, match="estimand"):
        RS.ResidualRecord(
            estimand="G6",
            source="cascade",
            channel="loss",
            level="per_path",
            mode="h2",
            point=0.0,
            se=0.001,
        )


def test_empty_join_raises_not_returns_empty():
    with pytest.raises(ValueError, match="RC8|rong"):
        RS.pool_inverse_variance([], [])


def test_missing_branch_raises(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"rows": [{"branch": "Aprime"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="RC8"):
        CR.load_rows([str(path)], "C")


def test_structural_invariant_rejects_mismatched_probe_size():
    b = [{"_probe_size": 64, "_probe_rate": 20.0, "_carve_out_fraction": 0.25, "mode": "h2", "rho_bar": 0.925, "seed": 101}]
    c = [{"_probe_size": 1470, "_probe_rate": 20.0, "_carve_out_fraction": 0.25, "mode": "h2", "rho_bar": 0.925, "seed": 101}]
    with pytest.raises(AssertionError, match="BAT BIEN CAU TRUC"):
        CR.assert_structural_invariant(b, c)


def test_power_gate_blocks_underpowered_claim():
    rec = RS.ResidualRecord(
        estimand="phan du ghep C tru tong B, kenh loss, cung topology",
        source="cascade",
        channel="loss",
        level="per_path",
        mode="h2",
        point=-0.010,
        se=0.010,
    )
    assert rec.power_ok(0.005) is False
    assert rec.power_ok(0.050) is True


def test_pooled_se_is_inverse_variance_not_mean_over_sqrt_k():
    vals, ses = [1.0, 1.0, 1.0], [0.01, 0.10, 0.10]
    got = RS.pool_inverse_variance(vals, ses)["se"]
    want = math.sqrt(1.0 / sum(1.0 / s**2 for s in ses))
    naive = float(np.mean(ses)) / math.sqrt(3)
    assert abs(got - want) < 1e-12
    assert abs(got - naive) > 1e-3


def test_loss_composes_multiplicatively():
    keep = 1.0
    for p in [0.05, 0.05, 0.05]:
        keep *= 1.0 - p
    assert abs((1.0 - keep) - 0.142625) < 1e-9
    assert abs((1.0 - keep) - 0.15) > 1e-3


def test_cascade_loss_uses_probe_estimator_not_background_loss():
    b = []
    c = []
    for seed in [101, 102, 103]:
        digests = {link: "sched-%d-%s" % (seed, link) for link in CR.TANDEM_LINKS}
        for link in CR.TANDEM_LINKS:
            b.append(
                {
                    "branch": "B",
                    "mode": "h2",
                    "rho_bar": 0.925,
                    "seed": seed,
                    "link": link,
                    "probe_loss": 0.01,
                    "q_mean_ms": 1.0,
                    "load_schedule_digests": digests,
                    "load_rows": [{"link": link, "n_bg_sent": 1000, "n_bg_recv": 500}],
                }
            )
        c.append(
            {
                "branch": "C",
                "mode": "h2",
                "rho_bar": 0.925,
                "seed": seed,
                "probe_loss": 0.05,
                "q_mean_ms": 3.0,
                "n_sent": 1000,
                "n_recv_unique": 950,
                "load_schedule_digests": digests,
            }
        )

    diffs, _seeds = CR.paired_residuals(b, c, "h2", 0.925, "loss")

    probe_composed = 1.0 - (0.99 ** 3)
    assert np.allclose(diffs, 0.05 - probe_composed)
    assert not np.allclose(diffs, 0.05 - (1.0 - 0.5 ** 3))


def test_pairing_checks_traversed_link_only():
    b = []
    c = []
    n_diff_nontarget = 0
    for seed in [101, 102, 103]:
        c_digests = {link: "%d-C-%s" % (seed, link) for link in CR.TANDEM_LINKS}
        for link in CR.TANDEM_LINKS:
            b_digests = {
                other: (c_digests[other] if other == link else "%d-Bonly-%s-%s" % (seed, link, other))
                for other in CR.TANDEM_LINKS
            }
            n_diff_nontarget += sum(
                1 for other in CR.TANDEM_LINKS
                if other != link and b_digests[other] != c_digests[other]
            )
            b.append(
                {
                    "branch": "B",
                    "mode": "h2",
                    "rho_bar": 0.925,
                    "seed": seed,
                    "link": link,
                    "q_mean_ms": 1.0,
                    "load_schedule_digests": b_digests,
                    "load_rows": [{"link": link, "n_bg_sent": 1000, "n_bg_recv": 999}],
                }
            )
        c.append(
            {
                "branch": "C",
                "mode": "h2",
                "rho_bar": 0.925,
                "seed": seed,
                "q_mean_ms": 3.0 + 0.01 * (seed - 101),
                "n_sent": 1000,
                "n_recv_unique": 997,
                "load_schedule_digests": c_digests,
            }
        )

    diffs, seeds = CR.paired_residuals(b, c, "h2", 0.925, "delay_ms")

    assert list(seeds) == [101, 102, 103]
    assert diffs.shape == (3,)
    assert n_diff_nontarget > 0


def test_pairing_rejects_traversed_link_mismatch():
    b = [
        {
            "branch": "B",
            "mode": "h2",
            "rho_bar": 0.925,
            "seed": 101,
            "link": link,
            "q_mean_ms": 1.0,
            "load_schedule_digests": {other: "ok-%s" % other for other in CR.TANDEM_LINKS},
            "load_rows": [{"link": link, "n_bg_sent": 1000, "n_bg_recv": 999}],
        }
        for link in CR.TANDEM_LINKS
    ]
    b[1]["load_schedule_digests"]["L2"] = "wrong"
    c = [
        {
            "branch": "C",
            "mode": "h2",
            "rho_bar": 0.925,
            "seed": 101,
            "q_mean_ms": 3.0,
            "n_sent": 1000,
            "n_recv_unique": 997,
            "load_schedule_digests": {link: "ok-%s" % link for link in CR.TANDEM_LINKS},
        }
    ]
    with pytest.raises(AssertionError, match="lich link L2"):
        CR.paired_residuals(b, c, "h2", 0.925, "delay_ms")


def test_common_mode_delay_leaves_err_bitwise_unchanged():
    cell = [c for c in D.feasible_cells(D.CALIBRATION, include_pc1=True)
            if c["mode"] == "poisson" and abs(float(c["rho_bar"]) - 0.925) < 1e-9][0]
    cv2 = C.CostV2()
    base = B2.cell_metrics(D.TruthTable(), cv2, cell, seeds=[101], n=400)
    rec = RS.ResidualRecord(
        estimand="common mode delay residual applied equally to every measured link class",
        source="test",
        channel="delay_ms",
        level="per_link",
        mode="poisson",
        point=0.5,
        se=0.0,
        per_unit={"L1": 0.5, "L2": 0.5, "L3": 0.5},
    )
    shifted = B2.cell_metrics(B2.truth_table_for(rec, "common_mode", 0.5), cv2, cell, seeds=[101], n=400)

    assert shifted["err_total"] == base["err_total"]


def test_variant_decomposition_is_exact():
    per_link = {"L1": 1.0, "L2": 2.0, "L3": -6.0}
    for endpoint in (-2.0, -0.5, 3.0):
        vecs = B2.variant_vectors(per_link, endpoint, point=-1.0)
        for link in per_link:
            assert vecs["full"][link] == pytest.approx(
                vecs["common_mode"][link] + vecs["differential"][link],
                abs=1e-12,
            )


def test_path_level_residual_rejects_differential():
    """Cascade residuals at path level must not silently inject differential=0."""
    with pytest.raises(ValueError, match="muc DUONG|per_path|BOM RONG"):
        B2.variant_vectors({}, r_endpoint=-0.013, point=-0.01, level="per_path")


def test_path_level_residual_only_supports_common_mode():
    records = [
        RS.ResidualRecord(
            estimand="cascade path-level loss residual",
            source="cascade",
            channel="loss",
            level="per_path",
            mode="h2",
            point=-0.01,
            se=0.002,
            per_unit={},
        ),
        RS.ResidualRecord(
            estimand="cascade path-level loss residual peer",
            source="cascade",
            channel="loss",
            level="per_path",
            mode="poisson",
            point=-0.02,
            se=0.002,
            per_unit={},
        ),
    ]

    assert B2.variant_supported(records[0], "common_mode", records)
    assert not B2.variant_supported(records[0], "differential", records)
    assert not B2.variant_supported(records[0], "full", records)
    assert not B2.variant_supported(records[0], "joint", records)


def test_residual_applied_by_link_CLASS_not_by_name():
    tt = B2.LinkShiftTruthTable(
        B2.expand_tandem_shifts({"L1": 0.01, "L2": 0.0, "L3": 0.0}),
        channel="loss",
        mode="h2",
    )
    rho = np.array([0.9])
    base = D.TruthTable()

    _d_u_a, l_u_a = tt.delay_loss("h2", "uA", rho)
    _d_v_c, l_v_c = tt.delay_loss("h2", "vC", rho)
    _d_b_u_a, b_u_a = base.delay_loss("h2", "uA", rho)
    _d_b_v_c, b_v_c = base.delay_loss("h2", "vC", rho)

    assert float(l_u_a[0] - b_u_a[0]) == pytest.approx(0.01, abs=1e-12)
    assert float(l_v_c[0] - b_v_c[0]) == pytest.approx(0.01, abs=1e-12)


def test_full_equals_differential_on_err_for_delay_channel():
    assert all(len(path) == 3 for path in T7.PATHS.values())
    cell = [c for c in D.feasible_cells(D.CALIBRATION, include_pc1=True)
            if c["mode"] == "h2" and abs(float(c["rho_bar"]) - 0.925) < 1e-9][0]
    cv2 = C.CostV2()
    rec = RS.ResidualRecord(
        estimand="per-link delay residual from transfer smoke used for algebraic invariant",
        source="test",
        channel="delay_ms",
        level="per_path",
        mode="h2",
        point=-0.4414766679896438,
        se=0.0,
        per_unit={
            "L1": -0.1337893573260147,
            "L2": -0.06444702325844487,
            "L3": -0.2432402874051891,
        },
    )

    diff = B2.cell_metrics(B2.truth_table_for_endpoint(rec, "differential", -0.7435243972479476), cv2, cell, seeds=[101], n=800)
    full = B2.cell_metrics(B2.truth_table_for_endpoint(rec, "full", -0.7435243972479476), cv2, cell, seeds=[101], n=800)

    assert full["err_total"] == diff["err_total"]


def test_differential_injection_changes_err_more_than_common_mode():
    cell = [c for c in D.feasible_cells(D.CALIBRATION, include_pc1=True)
            if c["mode"] == "poisson" and abs(float(c["rho_bar"]) - 0.925) < 1e-9][0]
    cv2 = C.CostV2()
    base = B2.cell_metrics(D.TruthTable(), cv2, cell, seeds=[101], n=5000)
    rec = RS.ResidualRecord(
        estimand="per-link delay residual with large differential component on L3",
        source="test",
        channel="delay_ms",
        level="per_link",
        mode="poisson",
        point=100.0,
        se=0.0,
        per_unit={"L1": 0.0, "L2": 0.0, "L3": 300.0},
    )
    common = B2.cell_metrics(B2.truth_table_for(rec, "common_mode", 100.0), cv2, cell, seeds=[101], n=5000)
    differential = B2.cell_metrics(B2.truth_table_for(rec, "differential", 100.0), cv2, cell, seeds=[101], n=5000)

    common_delta = abs(common["err_total"] - base["err_total"])
    differential_delta = abs(differential["err_total"] - base["err_total"])
    assert common_delta == 0.0
    assert differential_delta > common_delta


def test_bisection_brackets_grid_result():
    got = B2.refine_r_star(lambda x: x < 0.37, 0.2, 0.5, tol=0.01)

    assert got["r_star_lo"] < 0.37 <= got["r_star_hi"]
    assert got["bracket_width"] <= 0.01


def test_paired_err_contrast_counts_integer_flips():
    base = np.zeros(10_000, dtype=bool)
    pert = np.zeros(10_000, dtype=bool)
    pert[:9] = True

    got = B2.paired_binary_contrast(base, pert)

    assert got["b"] == 9
    assert got["c"] == 0
    assert got["n_discordant"] == 9
    assert got["d_err"] * got["n_total"] == pytest.approx(got["b"] - got["c"], abs=1e-12)


def test_paired_se_is_much_smaller_than_unpaired_for_sparse_flips():
    base = np.zeros(10_000, dtype=bool)
    pert = np.zeros(10_000, dtype=bool)
    pert[:9] = True

    got = B2.paired_binary_contrast(base, pert)

    assert got["se_paired"] < 0.1 * got["se_unpaired_for_reference"]


def test_small_discordance_uses_exact_sign_test():
    base = np.zeros(3, dtype=bool)
    pert = np.ones(3, dtype=bool)

    got = B2.paired_binary_contrast(base, pert)

    assert got["p_mcnemar_method"] == "exact_binomial"
    assert got["p_mcnemar_exact"] == pytest.approx(0.25)
    assert got["mc_resolvable"] is False


def test_common_mode_delay_identity_is_not_a_mc_claim():
    rec = RS.ResidualRecord(
        estimand="common mode delay residual is an algebraic argmin identity",
        source="test",
        channel="delay_ms",
        level="per_link",
        mode="h2",
        point=0.5,
        se=0.0,
        per_unit={"L1": 0.5, "L2": 0.5, "L3": 0.5},
    )

    assert B2.is_algebraic_identity_case(rec, "common_mode") is True
    assert B2.is_algebraic_identity_case(rec, "differential") is False


def test_block_len_constant_matches_g7():
    assert B2.BLOCK_LEN_G7 == int(round(D.BLOCK_S / D.DT))


def test_block_bootstrap_se_exposes_clustered_flips():
    signed = np.zeros(10_000, dtype=float)
    signed[:100] = 1.0
    iid_se = math.sqrt(float(np.sum(signed != 0.0))) / signed.size
    block = B2.block_bootstrap_mean([D._block_means(signed, 100)], n_boot=1000, seed=123)

    assert block["se"] > 3.0 * iid_se


def test_potency_uses_rms_injected_vector():
    rec = RS.ResidualRecord(
        estimand="loss residual with known vector rms for potency",
        source="test",
        channel="loss",
        level="per_link",
        mode="h2",
        point=2.0,
        se=0.0,
        per_unit={"L1": 1.0, "L2": 2.0, "L3": 2.0},
    )

    assert B2.injection_rms(rec, "full", 2.0) == pytest.approx(math.sqrt(3.0), abs=1e-12)


def test_pilot_power_only_prints_sd_and_seed_count_not_mean(tmp_path, capsys):
    state_b = {
        "probe_size_bytes": 64,
        "probe_rate_pps": 20.0,
        "carve_out_fraction": 0.25,
        "rows": [],
    }
    state_c = {
        "probe_size_bytes": 64,
        "probe_rate_pps": 20.0,
        "carve_out_fraction": 0.25,
        "rows": [],
    }
    for idx, seed in enumerate([101, 102, 103]):
        digests = {link: "sched-%d-%s" % (seed, link) for link in CR.TANDEM_LINKS}
        for link in CR.TANDEM_LINKS:
            state_b["rows"].append(
                {
                    "branch": "B",
                    "mode": "h2",
                    "rho_bar": 0.925,
                    "seed": seed,
                    "link": link,
                    "q_mean_ms": 1.0 + 0.02 * idx,
                    "probe_loss": 0.001,
                    "n_sent": 1000,
                    "load_schedule_digests": digests,
                    "load_rows": [{"link": link, "n_bg_sent": 100000, "n_bg_recv": 99900 - idx}],
                }
            )
        state_c["rows"].append(
            {
                "branch": "C",
                "mode": "h2",
                "rho_bar": 0.925,
                "seed": seed,
                "q_mean_ms": 3.1 + 0.1 * idx,
                "n_sent": 100000,
                "n_recv_unique": 99700 - 2 * idx,
                "load_schedule_digests": digests,
            }
        )
    path_b = tmp_path / "b.json"
    path_c = tmp_path / "c.json"
    path_b.write_text(json.dumps(state_b), encoding="utf-8")
    path_c.write_text(json.dumps(state_c), encoding="utf-8")

    summary = PPO.summarize([str(path_b)], [str(path_c)], ["h2"], 0.925, [0.005])
    PPO.print_summary(summary)
    out = capsys.readouterr().out

    assert "sd(d_s)" in out
    assert "n_seed_required_conservative" in out
    assert "mean" not in out.lower()
    assert all("point" not in row for row in summary["rows"])
    row = summary["rows"][0]
    assert row["sd_d_s_upper_95"] > row["sd_d_s"]
    assert row["n_seed_required_conservative_95"]["delta_0.005"] >= row["n_seed_required"]["delta_0.005"]


def test_joint_qt3_uses_dimensionless_anchor_symmetric_lambda():
    records = [
        RS.ResidualRecord(
            estimand="anchor h2 delay residual for joint scaling rule test",
            source="test",
            channel="delay_ms",
            level="per_link",
            mode="h2",
            point=2.0,
            se=0.0,
            per_unit={"L1": 1.0, "L2": 2.0, "L3": 3.0},
        ),
        RS.ResidualRecord(
            estimand="poisson delay residual must also be applied by joint mode",
            source="test",
            channel="delay_ms",
            level="per_link",
            mode="poisson",
            point=4.0,
            se=0.0,
            per_unit={"L1": 0.1, "L2": 0.2, "L3": 0.3},
        ),
    ]
    tt_h2 = B2.truth_table_for_joint(records, records[0], magnitude=4.0)
    tt_poisson = B2.truth_table_for_joint(records, records[1], magnitude=4.0)
    base = D.TruthTable()
    rho = np.array([0.8])

    d_base, _loss_base = base.delay_loss("poisson", "uA", rho)
    d_joint_h2, _loss_joint_h2 = tt_h2.delay_loss("poisson", "uA", rho)
    d_joint_poisson, _loss_joint_poisson = tt_poisson.delay_loss("poisson", "uA", rho)

    assert float(d_joint_h2[0] - d_base[0]) == pytest.approx(0.4, abs=1e-12)
    assert float(d_joint_poisson[0]) == pytest.approx(float(d_joint_h2[0]), abs=1e-12)


def test_joint_equals_full_in_band_mode_by_construction():
    cell = [c for c in D.feasible_cells(D.CALIBRATION, include_pc1=True)
            if c["mode"] == "h2" and abs(float(c["rho_bar"]) - 0.925) < 1e-9][0]
    cv2 = C.CostV2()
    records = [
        RS.ResidualRecord(
            estimand="h2 loss residual for band joint identity test",
            source="test",
            channel="loss",
            level="per_link",
            mode="h2",
            point=-0.01,
            se=0.0,
            per_unit={"L1": -0.01, "L2": -0.02, "L3": -0.03},
        ),
        RS.ResidualRecord(
            estimand="poisson loss residual should not affect h2 per-cell band metric",
            source="test",
            channel="loss",
            level="per_link",
            mode="poisson",
            point=0.04,
            se=0.0,
            per_unit={"L1": 0.04, "L2": 0.08, "L3": 0.12},
        ),
    ]
    full = B2.cell_metrics(B2.truth_table_for_endpoint(records[0], "full", -0.02), cv2, cell, seeds=[101], n=600)
    joint = B2.cell_metrics(
        B2.truth_table_for_variant(records[0], "joint", -0.02, records=records, joint_scale_rule="qt1"),
        cv2,
        cell,
        seeds=[101],
        n=600,
    )

    assert joint == full


def test_broken_detail_records_path_ranking_cell():
    baseline = {
        "per_cell": {"h2@0.925": {"err_total": 0.1, "d_sla": 0.1}},
        "rankings": {"h2@0.925": ["P1", "P3", "P4", "P2"]},
    }
    flags = {
        "K1_err_in_g1_band": True,
        "K2_d_sla_floor": True,
        "K3_spearman_err_z_positive": True,
        "K4_path_ranking_preserved": False,
        "K5_family_order_preserved": True,
        "per_cell": {"h2@0.925": {"err_total": 0.1, "d_sla": 0.1}},
        "rankings": {"h2@0.925": ["P1", "P3", "P2", "P4"]},
        "spearman_err_z": {"h2@0.925": {"rho": 1.0}},
    }

    detail = B2.broken_detail(flags, baseline)

    assert B2.first_broken_cells(["K4_path_ranking_preserved"], detail) == ["h2@0.925"]
    assert detail["K4_path_ranking_preserved"]["h2@0.925"]["base"] == ["P1", "P3", "P4", "P2"]


def test_joint_differs_from_full_in_scan_smoke_when_inter_mode_terms_matter():
    path = Path("results/phase-20R/breakdown_scan_transfer_smoke.json")
    if not path.exists():
        pytest.skip("scan smoke artifact not present")
    scans = json.loads(path.read_text(encoding="utf-8"))["scans"]
    by_key = {}
    for scan in scans:
        by_key.setdefault((scan["mode"], scan["channel"]), {})[scan["variant"]] = scan.get("r_star")

    differs = [
        key for key, vals in by_key.items()
        if vals.get("joint") is not None and vals.get("joint") != vals.get("full")
    ]
    assert differs


def test_independent_variants_canonicalize_joint_only_for_band():
    variants = ["common_mode", "differential", "full", "joint"]

    assert tuple(variants) == B2.DEFAULT_VARIANTS
    assert B2.independent_variants("band", variants) == ["common_mode", "differential", "full"]
    assert B2.independent_variants("scan", variants) == variants


def test_run_band_marks_d_sla_and_joint_fields():
    cell = [c for c in D.feasible_cells(D.CALIBRATION, include_pc1=True)
            if c["mode"] == "h2" and abs(float(c["rho_bar"]) - 0.925) < 1e-9][0]
    rec = RS.ResidualRecord(
        estimand="common mode delay residual exposes d_sla paired standard error fields",
        source="test",
        channel="delay_ms",
        level="per_link",
        mode="h2",
        point=0.4,
        se=0.0,
        per_unit={"L1": 0.4, "L2": 0.4, "L3": 0.4},
    )

    row = B2.run_band([rec], C.CostV2(), D.TruthTable(), [cell], seeds=[101], n=600, variants=["common_mode"])[0]

    assert row["is_algebraic_identity"] is True
    assert row["worst_endpoint_resolvable"] is None
    assert row["d_sla_se_method"] == "block_bootstrap_paired_samplewise_d_sla_delta"
    assert row["block_len_requested"] == B2.BLOCK_LEN_G7
    assert row["block_len_truncated"] is True
    assert isinstance(row["d_sla_resolvable"], bool)
    assert row["paired_err_endpoints"][0]["d_sla_se_method"] == "paired_sd_of_samplewise_d_sla_delta"
    assert "d_sla_se_block" in row["paired_err_endpoints"][0]


def test_band_artifact_records_full_provenance(tmp_path):
    residual = tmp_path / "residual.json"
    residual.write_text('{"schema":"residual_spec/v1","records":[]}\n', encoding="utf-8")

    report = B2.build_report(
        "band",
        {"rows": []},
        str(residual),
        seeds=[101, 102],
        n=2000,
        rho_bar_filter=0.925,
        variants=["common_mode", "differential", "full"],
    )

    for key in (
        "seeds",
        "n",
        "residual_sha256",
        "truth_table_sha256",
        "calibration_sha256",
        "git_commit",
        "is_smoke",
        "wall_utc",
        "n_independent_variants",
        "independent_variants",
    ):
        assert key in report
    assert report["is_smoke"] is True

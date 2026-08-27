import itertools

import numpy as np
import pytest

from measurements import lesson_23_25_final_audit as F
from measurements.link_corr_matrix import IDX, LINKS, K_PAIR, structured_matrix


def test_t0_t8_block_does_not_confuse_t10_with_t1():
    report = {"T0_inputs": 0, "T5b_cov": 5, "T8_last": 8,
              "T9_new": 9, "T10_new": 10, "metadata": 11}
    assert F.t0_t8_block(report) == {
        "T0_inputs": 0, "T5b_cov": 5, "T8_last": 8}


def test_output_must_not_alias_either_source(tmp_path):
    corr = tmp_path / "corr.json"
    nugget = tmp_path / "nugget.json"
    F.validate_separate_output(str(tmp_path / "new.json"), str(corr), str(nugget))
    with pytest.raises(ValueError, match="artifact rieng"):
        F.validate_separate_output(str(corr), str(corr), str(nugget))


def test_t5b_uses_target_covariance_and_recovers_analytic_ratios():
    sd = {link: (0.03 if link in F.EDGE_LINKS else 0.10)
          for link in LINKS}
    got = F.var_margin_cov(structured_matrix(1.0), 1.0, sd)
    adjacent = [row["ratio_at_omega_1_analytic"]
                for name, row in got.items()
                if name.startswith("m(") and row["shared_link"]]
    crossed = [row["ratio_at_omega_1_analytic"]
               for name, row in got.items()
               if name.startswith("m(") and not row["shared_link"]]
    assert adjacent == pytest.approx([1.389233090561402] * 4)
    assert crossed == pytest.approx([1.719091641884624] * 2)
    for name, row in got.items():
        if name.startswith("m("):
            assert row["ratio_measured_over_identity"] == pytest.approx(
                row["ratio_at_omega_1_analytic"])


def test_attenuation_ceiling_detects_correlated_lag0_residual():
    R = np.eye(len(LINKS))
    R[IDX["uA"], IDX["uB"]] = R[IDX["uB"], IDX["uA"]] = 0.60
    nugget = {"per_link": {
        link: {"signal_fraction": (0.40 if link in ("uA", "uB") else None)}
        for link in LINKS}}
    got = F.attenuation_ceiling_check(R, nugget)
    assert got["pairs_violating_independent_residual_ceiling"] == ["uA-uB"]
    assert got["per_pair"]["uA-uB"][
        "ceiling_if_lag0_residual_independent"] == pytest.approx(0.4)
    assert got["verdict"] == "LAG0_RESIDUAL_IS_CROSS_CORRELATED_PROVEN"
    assert set(got["projected_to_1_links"]) == set(F.CORE_LINKS) | {"vC", "vD"}


def test_host_dose_reports_both_predefined_dose_metrics():
    nconc = {link: float(i + 1) for i, link in enumerate(LINKS)}
    R = np.eye(len(LINKS))
    for a, b in itertools.combinations(LINKS, 2):
        if K_PAIR[(a, b)] == 0.0:
            R[IDX[a], IDX[b]] = R[IDX[b], IDX[a]] = (
                nconc[a] + nconc[b]) / 100.0
    got = F.host_dose_response(R, nconc)
    assert got["n_pairs"] == 6
    assert got["spearman_log_pair_process_dose_vs_r"] == pytest.approx(1.0)
    assert got["total_endpoint_dose_by_host"] == {
        "hA": 8.0, "hB": 13.0, "hC": 15.0, "hD": 18.0,
        "hdst": 15.0, "hsrc": 3.0}


def test_contrast_2x2_has_all_28_pairs_and_known_cells():
    got = F.contrast_2x2(structured_matrix(0.25))
    assert len(got["all_28_pairs"]) == 28
    assert got["table"]["k=0.5|shared_host=False"]["n"] == 4
    assert got["table"]["k=0.7071|shared_host=True"]["n"] == 8
    assert got["omega_descriptive_no_shared_host_contrast"] == pytest.approx(0.25)

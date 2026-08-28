import itertools

import numpy as np
import pytest

from measurements import lesson_23_25_closeout as C
from measurements.link_corr_matrix import IDX, K_PAIR, LINKS, err_bivariate, structured_matrix


def _ar1_runs(ramp=0.0, n_runs=20, n=600):
    rng = np.random.default_rng(20260828)
    runs = []
    for _ in range(n_runs):
        X = np.zeros((n, len(LINKS)))
        eps = rng.standard_normal(X.shape)
        for t in range(1, n):
            X[t] = 0.7 * X[t - 1] + eps[t]
        if ramp:
            X[:n // 3] += np.linspace(-ramp, ramp, n // 3)[:, None]
        runs.append(X)
    return runs


def test_clean_pair_counts_are_four_signal_ten_baseline():
    signal, baseline = C.clean_pairs()
    assert len(signal) == 4
    assert len(baseline) == 10


def test_clean_pairs_remain_nonempty_after_every_link_drop():
    for link in LINKS:
        signal, baseline = C.clean_pairs(link)
        assert signal and baseline


@pytest.mark.parametrize("omega", [0.0, 0.25, 0.5, 1.0])
def test_omega_contrast_recovers_injected_omega(omega):
    assert C.omega_contrast(structured_matrix(omega))["omega"] == pytest.approx(omega)


def test_omega_contrast_immune_to_shared_host_confound():
    R = structured_matrix(0.3)
    for a, b in itertools.combinations(LINKS, 2):
        if C.shares_host(a, b):
            R[IDX[a], IDX[b]] = R[IDX[b], IDX[a]] = R[IDX[a], IDX[b]] + 0.6
    assert C.omega_contrast(R)["omega"] == pytest.approx(0.3)


def test_identity_has_zero_omega_contrast():
    assert C.omega_contrast(np.eye(len(LINKS)))["omega"] == pytest.approx(0.0)


def test_jackknife_is_stable_on_exact_structured_matrix():
    got = C.jackknife_by_link(structured_matrix(0.4))
    assert got["omega_full"] == pytest.approx(0.4)
    assert list(got["leave_one_out"].values()) == pytest.approx([0.4] * 8)
    assert got["sign_flips_under_loo"] is False


def test_robust_null_level_resists_two_large_outliers():
    R = np.eye(len(LINKS))
    for a, b in C.NULL_PAIRS:
        R[IDX[a], IDX[b]] = R[IDX[b], IDX[a]] = 0.02
    for a, b in (("uA", "uB"), ("vC", "vD")):
        R[IDX[a], IDX[b]] = R[IDX[b], IDX[a]] = 0.9
    assert C._robust_null_level(R) == pytest.approx(0.02)


def test_time_slice_detects_injected_warmup():
    got = C.time_slice_audit(_ar1_runs(ramp=8.0))
    assert got["_summary"]["warmup_detected"] is True
    assert got["_summary"]["verdict"] == "WARMUP_TRANSIENT_SUSPECTED_MUST_TRIM"


def test_time_slice_quiet_on_stationary_series():
    got = C.time_slice_audit(_ar1_runs(ramp=0.0))
    assert got["_summary"]["warmup_detected"] is False


def test_null_partners_are_all_nohost_null_pairs():
    for a, b in C.S_PAIRS:
        groups = C.null_partners(a, b)
        for pair in groups["hold_a"] + groups["hold_b"]:
            assert K_PAIR[pair] == 0.0
            assert C.shares_host(*pair) is False


def test_paired_null_table_all_survive_on_pure_structure():
    got = C.paired_null_table(structured_matrix(0.5))
    assert got["n_survives_strict_null"] == got["n_structured_pairs"] == 12
    assert got["verdict"] == "STRUCTURE_SURVIVES_NULLS"
    assert got["by_shared_host"]["shared_host=False"][
        "mean_excess_over_k"] == pytest.approx(0.5)


def test_paired_null_table_cancels_per_link_artifact():
    R = np.eye(len(LINKS))
    for candidate in LINKS:
        if candidate == "bd":
            continue
        pair = C._pair_key("bd", candidate)
        R[IDX[pair[0]], IDX[pair[1]]] = R[IDX[pair[1]], IDX[pair[0]]] = 0.30
    got = C.paired_null_table(R)
    row = next(row for row in got["rows"] if row["structured_pair"] == "bd-vD")
    assert row["survives_strict_null"] is False
    assert row["r_null_max"] == pytest.approx(0.30)
    assert row["excess_over_max_per_k"] == pytest.approx(0.0)


def test_err_bivariate_at_zero_matches_sheppard():
    r = 0.87
    assert err_bivariate(0.0, r) == pytest.approx(np.arccos(r) / np.pi, abs=1e-8)


def test_err_grid_starts_at_unit_ratio_and_increases():
    got = C.err_grid(0.5, 0.86, 1.719091641884624)
    assert got["omega_0.00"]["ratio_to_omega0"] == pytest.approx(1.0)
    assert got["omega_1.00"]["ratio_to_omega0"] > 1.0


def test_ratio_is_insensitive_to_r_but_level_is_not():
    low = C.err_grid(0.375, 0.8514, 1.719091641884624)
    high = C.err_grid(0.375, 0.98675, 1.719091641884624)
    level = low["omega_0.00"]["err"] / high["omega_0.00"]["err"]
    delta = abs(low["omega_1.00"]["ratio_to_omega0"]
                - high["omega_1.00"]["ratio_to_omega0"])
    assert level > 3.0
    assert delta < 0.01

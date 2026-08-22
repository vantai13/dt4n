"""Golden tests for Phase 20R cost_v2."""

import numpy as np
import pytest

from twin import cost_v2 as C
from twin import topology_v7 as T7


FIT = "results/LIVE/phase-L/link_model_v2_fit.json"
W_LOSS = 2500.0


def _load_mean_rho():
    return {link: float(T7.LOAD_MEAN[link]) for link in T7.LINK_NAMES}


def test_gc1_static_path_golden_values_include_serialization():
    assert C.static_path_ms("P1") == pytest.approx(12.040, abs=1e-12)
    assert C.static_path_ms("P2") == pytest.approx(14.052, abs=1e-12)
    assert C.static_path_ms("P3") == pytest.approx(13.544, abs=1e-12)
    assert C.static_path_ms("P4") == pytest.approx(13.548, abs=1e-12)


def test_gc1b_serialization_formula_uses_bits_and_milliseconds():
    assert C.serialization_ms(8.0) == pytest.approx(1.512, abs=1e-12)
    assert C.serialization_ms(6.0) == pytest.approx(2.016, abs=1e-12)
    assert C.serialization_ms(4.0) == pytest.approx(3.024, abs=1e-12)


def test_gc2_forgetting_serialization_is_phase_sized_error():
    for path in T7.PATH_NAMES:
        without = sum(T7.LINKS[link][1] for link in T7.PATHS[path])
        assert C.static_path_ms(path) - without >= 4.0


def test_gc3_path_loss_uses_product_not_sum():
    cv2 = C.CostV2(FIT)
    rho = _load_mean_rho()
    _delay, loss, _cost = cv2.tables(rho, "poisson", W_LOSS)
    p1 = T7.PATH_NAMES.index("P1")
    link_losses = [cv2.link_loss("poisson", link, rho[link]) for link in T7.PATHS["P1"]]
    product_loss = 1.0 - np.prod([1.0 - x for x in link_losses])
    additive_loss = sum(link_losses)
    assert loss[p1] == pytest.approx(product_loss, abs=1e-15)
    assert loss[p1] < additive_loss


def test_gc3b_path_loss_golden_at_load_mean():
    cv2 = C.CostV2(FIT)
    _delay, loss, cost = cv2.tables(_load_mean_rho(), "poisson", W_LOSS)
    assert loss.tolist() == pytest.approx(
        [
            0.008535747125192228,
            0.01890543326494354,
            0.008518972858031715,
            0.011333131099104832,
        ],
        abs=1e-15,
    )
    assert cost[T7.PATH_NAMES.index("P1")] == pytest.approx(44.12254759545746)


def test_gc4_unreliable_region_raises():
    cv2 = C.CostV2(FIT, strict_reliable=True)
    with pytest.raises(ValueError, match="unreliable region"):
        cv2.link_delay_ms("cbr", "ac", 0.98)
    assert cv2.link_delay_ms("cbr", "ac", 0.90) > 0.0


def test_gc4b_domain_extrapolation_raises():
    cv2 = C.CostV2(FIT, strict_reliable=True)
    with pytest.raises(ValueError, match="outside measured domain"):
        cv2.link_delay_ms("poisson", "ac", 1.06)
    with pytest.raises(ValueError, match="rho ngoai mien"):
        cv2.tables_batch(np.full((2, len(T7.LINK_NAMES)), 1.06), "poisson", W_LOSS)


def test_gc5_batch_matches_single_with_linear_interpolation():
    rng = np.random.default_rng(201)
    rho_mat = rng.uniform(0.55, 1.00, size=(300, len(T7.LINK_NAMES)))
    cv2 = C.CostV2(FIT)
    delay_b, loss_b, cost_b = cv2.tables_batch(rho_mat, "poisson", W_LOSS)
    rows = [{link: rho_mat[i, j] for j, link in enumerate(T7.LINK_NAMES)} for i in range(len(rho_mat))]
    single = [cv2.tables(row, "poisson", W_LOSS) for row in rows]
    delay_s = np.vstack([x[0] for x in single])
    loss_s = np.vstack([x[1] for x in single])
    cost_s = np.vstack([x[2] for x in single])
    assert np.max(np.abs(delay_b - delay_s)) < 0.002
    assert np.max(np.abs(loss_b - loss_s)) < 5e-6
    assert np.max(np.abs(cost_b - cost_s)) < 0.01


def test_gc6_cost_is_monotone_in_uniform_rho():
    cv2 = C.CostV2(FIT, strict_reliable=False)
    for mode in ("cbr", "poisson", "h2"):
        vals = []
        for rho_value in np.arange(0.60, 0.941, 0.01):
            rho = {link: float(rho_value) for link in T7.LINK_NAMES}
            _delay, _loss, cost = cv2.tables(rho, mode, W_LOSS)
            vals.append(float(cost[T7.PATH_NAMES.index("P1")]))
        assert all(a <= b + 1e-10 for a, b in zip(vals, vals[1:]))


def test_gc7_q7_offsets_are_frozen_and_sum_to_zero():
    assert sum(C.LINK_OFFSET.values()) == pytest.approx(0.0, abs=1e-15)
    assert C.LINK_OFFSET == pytest.approx(
        {
            "uA": -0.0675,
            "uB": -0.0475,
            "ac": 0.0525,
            "ad": 0.0625,
            "bc": 0.0475,
            "bd": 0.0575,
            "vC": -0.0675,
            "vD": -0.0375,
        },
        abs=1e-15,
    )


def test_gc7b_clip_fraction_justifies_rho_bar_max_096():
    assert C.clip_fraction(0.98)["ad"] == pytest.approx(0.22662735237686848, rel=1e-6)
    assert C.clip_fraction(0.96)["ad"] == pytest.approx(0.002979763235054555, rel=1e-6)
    assert C.clip_fraction(0.925)["ad"] < 1e-9


def test_gc8_uniform_rho_locks_argmin():
    cv2 = C.CostV2(FIT, strict_reliable=False)
    for mode in ("cbr", "poisson", "h2"):
        winners = set()
        for r in np.arange(0.60, 1.001, 0.01):
            rho = {link: float(r) for link in T7.LINK_NAMES}
            _delay, _loss, cost = cv2.tables(rho, mode, W_LOSS)
            winners.add(T7.PATH_NAMES[int(np.argmin(cost))])
        assert winners == {"P1"}, (mode, winners)


def test_gc8b_mean_ranking_is_locked_by_design():
    cv2 = C.CostV2(FIT, strict_reliable=False)
    rankings = set()
    for rho_bar in np.arange(0.60, 0.961, 0.01):
        _delay, _loss, cost = cv2.tables(C.rho_vector(float(rho_bar)), "poisson", W_LOSS)
        rankings.add(tuple(np.argsort(cost).tolist()))
    assert rankings == {(0, 2, 3, 1)}


def test_gc8c_fluctuations_can_flip_argmin():
    cv2 = C.CostV2(FIT)
    rng = np.random.default_rng(20)
    rho_bar = 0.925
    sigma = C.sigma_from_a_regime("poisson", rho_bar, 0.9)
    center = np.array([C.rho_vector(rho_bar)[link] for link in T7.LINK_NAMES])
    rho_mat = np.clip(
        center + rng.normal(0.0, sigma, size=(5000, len(T7.LINK_NAMES))),
        C.RHO_MIN,
        C.RHO_MAX,
    )
    _delay, _loss, cost = cv2.tables_batch(rho_mat, "poisson", W_LOSS)
    winners = {T7.PATH_NAMES[int(x)] for x in np.argmin(cost, axis=1)}
    assert "P1" in winners
    assert len(winners) > 1


def test_gc9_sigma_max_regime_respects_family_reliability():
    assert C.sigma_max_regime("cbr", 0.85) == pytest.approx(0.0375 / 2.58)
    assert C.sigma_max_regime("cbr", 0.925) == 0.0
    assert C.sigma_max_regime("cbr", 0.96) == 0.0
    assert C.sigma_max_regime("poisson", 0.96) == pytest.approx(0.0275 / 2.58)


def test_gc9b_sigma_binding_switches_from_floor_to_ceiling():
    assert C.sigma_max_regime("poisson", 0.70) == pytest.approx(0.1325 / 2.58)
    assert C.sigma_max_regime("poisson", 0.85) == pytest.approx(0.1375 / 2.58)
    assert C.sigma_max_regime("poisson", 0.925) == pytest.approx(0.0625 / 2.58)
    assert C.sigma_max_regime("poisson", 0.96) == pytest.approx(0.0275 / 2.58)
    assert C.sigma_max_regime("poisson", 0.70) < C.sigma_max_regime("poisson", 0.85)
    assert C.sigma_max_regime("poisson", 0.96) < C.sigma_max_regime("poisson", 0.925)

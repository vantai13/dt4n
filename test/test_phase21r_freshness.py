import numpy as np
import pandas as pd
import pytest

from cert import freshness_requirement as F


def _table(
    zs=(0.0, 0.05, 0.10, 0.20, 0.40),
    err=(0.04, 0.10, 0.14, 0.19, 0.26),
    acc=(0.84, 0.60, 0.49, 0.34, 0.20),
):
    return pd.DataFrame({"z": zs, "err_anchor": err, "k1_acceptance": acc})


def test_S1_max_interpretation_is_double_mean_interpretation():
    z = 0.100
    f_mean = F.sync_rate_from_z(z, d_sync=0.051, interpretation="mean")
    f_max = F.sync_rate_from_z(z, d_sync=0.051, interpretation="max")
    assert f_max == pytest.approx(2.0 * f_mean)


def test_S2_below_physical_floor_has_no_sync_rate():
    assert F.sync_rate_from_z(0.040, d_sync=0.051) is None
    assert F.sync_rate_from_z(0.051, d_sync=0.051) is None
    assert F.sync_rate_from_z(None, d_sync=0.051) is None


def test_S3_current_system_recovers_2hz():
    assert F.sync_rate_from_z(0.301, 0.051, "mean") == pytest.approx(2.0, rel=1e-6)
    assert F.sync_rate_from_z(0.551, 0.051, "max") == pytest.approx(2.0, rel=1e-6)


def test_S4_bad_interpretation_raises():
    with pytest.raises(ValueError):
        F.sync_rate_from_z(0.1, interpretation="median")


def test_S5_invert_interpolates():
    result = F.invert_for_z(_table(), "err_anchor", 0.12)
    assert result["status"] == "interpolated"
    assert 0.05 < result["z_star"] < 0.10


def test_S6_invert_flags_infeasible_below_d_sync():
    result = F.invert_for_z(_table(), "err_anchor", 0.09, d_sync=0.051)
    assert result["z_star"] < 0.051
    assert not result["feasible_vs_d_sync"]


def test_S7_invert_flags_model_floor():
    result = F.invert_for_z(_table(), "err_anchor", 0.02)
    assert result["z_star"] is None
    assert result["status"] == "infeasible_even_at_z0"


def test_S8_invert_increasing_direction():
    result = F.invert_for_z(_table(), "k1_acceptance", 0.55, decreasing_is_good=False)
    assert 0.05 < result["z_star"] < 0.10


def test_S9_jensen_order_for_concave_curve():
    z_levels = np.linspace(0.055, 0.400, 70)
    result = F.aoi_averaging_check(_table(), z_levels)
    assert result["jensen_order_holds"]
    assert result["E_of_f"] < result["f_of_max"]


def test_S10_jensen_equality_for_linear_curve():
    linear = pd.DataFrame({"z": [0.0, 0.5], "err_anchor": [0.0, 0.5]})
    result = F.aoi_averaging_check(linear, np.linspace(0.055, 0.45, 80))
    assert result["E_of_f"] == pytest.approx(result["f_of_E"], abs=1e-9)


def test_S11_measured_closest_value_is_identified():
    z_levels = np.linspace(0.055, 0.400, 70)
    result = F.aoi_averaging_check(_table(), z_levels, measured_sawtooth_err=0.1701)
    assert result["closest_to"] in ("E_of_f", "f_of_E")


def _synth(z, n_block=220, per_block=80, seed=0):
    rng = np.random.default_rng(seed + int(1000 * z))
    scale = 3.0 + 40.0 * float(z)
    m_hat = rng.uniform(0.0, 40.0, n_block * per_block)
    s_margin = np.abs(rng.normal(0.0, scale, n_block * per_block))
    wrong = s_margin > m_hat
    return pd.DataFrame(
        {
            "block_id": np.repeat(np.arange(n_block), per_block),
            "m_hat": m_hat,
            "s_margin": s_margin,
            "wrong": wrong,
            "m_true": m_hat - np.where(wrong, s_margin + 0.1, -s_margin),
            "regret": np.where(wrong, s_margin, 0.0),
            "d_sla": wrong.astype(float),
        }
    )


def test_S12_frontier_kappa_star_increases_with_z():
    tables = {z: _synth(z) for z in (0.055, 0.150, 0.300)}
    frontier = F.iso_quality_frontier(tables, target_err=0.02)
    assert frontier["kappa_star"].is_monotonic_increasing
    assert frontier["acceptance_rate"].is_monotonic_decreasing


def test_S13_frontier_hits_target():
    tables = {z: _synth(z) for z in (0.055, 0.150)}
    frontier = F.iso_quality_frontier(tables, target_err=0.02)
    assert (frontier["err_check"] <= 0.02 + 1e-6).all()


def test_S14_knee_is_inside_grid():
    tables = {z: _synth(z) for z in (0.055, 0.100, 0.150, 0.200, 0.300)}
    knee = F.knee_of_frontier(F.iso_quality_frontier(tables, target_err=0.02))
    assert 0.055 <= knee["knee_z"] <= 0.300

import numpy as np

from rl.a2.state_a2 import (
    A2_STATE_DIM,
    AOI_DIMS,
    AOI_NORM_DIVISOR_S,
    aoi_features,
    build_a2_state,
    mask_aoi,
)


def test_dim():
    assert A2_STATE_DIM == 11


def test_aoi_features_fresh():
    norm, fresh = aoi_features(0.0)
    assert norm == 0.0
    assert fresh == 1.0


def test_aoi_features_stale():
    norm, fresh = aoi_features(3.0)
    assert abs(norm - 3.0 / AOI_NORM_DIVISOR_S) < 1e-6
    assert fresh == 0.0


def test_aoi_no_saturation_in_range():
    norm, _fresh = aoi_features(5 * 1.1)
    assert norm < 1.0


def test_mask_only_touches_aoi():
    vec = build_a2_state(
        0.5, 8.0, 6.0, 10.0, 8.0, 20.0, 0.3, 1, 3, aoi_s=3.0)
    masked = mask_aoi(vec)
    for idx in range(A2_STATE_DIM):
        if idx in AOI_DIMS:
            assert masked[idx] == 0.0
        else:
            assert masked[idx] == vec[idx]


def test_mask_does_not_mutate_original():
    vec = build_a2_state(
        0.5, 8.0, 6.0, 10.0, 8.0, 20.0, 0.3, 1, 3, aoi_s=3.0)
    before = vec.copy()
    _ = mask_aoi(vec)
    assert np.array_equal(vec, before)


def test_stale_demand_creates_sat_illusion():
    true_vec = build_a2_state(
        0.5, 5.0, 10.0, 15.0, 5.0, 20.0, 0.3, 0, 3)
    observed_vec = build_a2_state(
        0.5, 5.0, 10.0, 5.0, 5.0, 20.0, 0.3, 0, 3)
    assert true_vec[5] < 0.4
    assert observed_vec[5] == 1.0

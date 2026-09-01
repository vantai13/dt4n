"""Unit locks for the G.3 synthetic pipeline before the expensive dry-run."""
import numpy as np
import pytest

from tools.g3_dryrun import (
    A0,
    CAP_BPS,
    DT_S,
    K_TOPO,
    LINKS,
    RHO_BAR,
    WIRE_BYTES,
    acf,
    classify_quantization,
    component_baselines,
    mixture_acf,
    quantize_target,
    residual_correlation,
)


def test_component_baselines_reconstruct_the_anchor_mean():
    path_base, private_base, reconstructed = component_baselines(A0)
    assert np.all(path_base > 0.0)
    assert np.all(private_base > 0.0)
    assert np.allclose(reconstructed, RHO_BAR, atol=1e-15)


def test_quantize_target_is_independent_per_window_rounding():
    rng = np.random.default_rng(1)
    target = rng.uniform(0.7, 0.9, size=(len(LINKS), 10000))
    sent, packets = quantize_target(target)
    wanted = target * CAP_BPS[:, None] * DT_S / (WIRE_BYTES * 8.0)
    assert np.array_equal(packets, np.round(wanted))
    assert max(abs(acf(sent[i] - target[i])) for i in range(len(LINKS))) < 0.05


@pytest.mark.parametrize(
    "value,expected",
    [(0.02, "INDEPENDENT_ROUND"), (-0.08, "INDEPENDENT_ROUND"),
     (-0.50, "CUMULATIVE"), (-0.20, "INCONCLUSIVE"), (0.20, "INCONCLUSIVE")],
)
def test_quantization_classifier(value, expected):
    assert classify_quantization(value) == expected


def test_mixture_acf_has_the_signed_endpoints():
    for lag in (1, 2, 3):
        assert mixture_acf(0.0, 30.0, 3.0, lag) == pytest.approx(
            np.exp(-lag * DT_S / 3.0), abs=1e-15
        )
        assert mixture_acf(1.0, 30.0, 3.0, lag) == pytest.approx(
            np.exp(-lag * DT_S / 30.0), abs=1e-15
        )


def test_residual_correlation_is_psd_and_preserves_null_pairs():
    correlation = residual_correlation()
    assert np.linalg.eigvalsh(correlation).min() >= -1e-12
    assert np.allclose(np.diag(correlation), 1.0)
    for i in range(len(LINKS)):
        for j in range(i + 1, len(LINKS)):
            if K_TOPO[i, j] == 0.0:
                assert correlation[i, j] == 0.0


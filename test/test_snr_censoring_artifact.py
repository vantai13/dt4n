#!/usr/bin/env python3
"""Golden test cho Lesson 23.25f (A082)."""
import numpy as np
import pytest

from measurements import snr_censoring_artifact as S
from twin import cost_v2 as C


def test_hard_ceiling_detects_framing_overhead():
    rng = np.random.default_rng(0)
    X = np.minimum(0.95 + 0.1 * rng.standard_normal((600, 8)), 1.0094)
    out = S.measure_hard_ceiling([X])
    assert out["hard_ceiling_measured"] == pytest.approx(1.0094, abs=2e-3)
    assert out["framing_overhead_percent"] == pytest.approx(0.94, abs=0.25)


def test_hard_ceiling_falls_back_when_no_saturation():
    rng = np.random.default_rng(1)
    X = 0.70 + 0.03 * rng.standard_normal((600, 8))
    out = S.measure_hard_ceiling([X])
    assert out["n_saturated_link_runs"] == 0
    assert out["hard_ceiling_measured"] == 1.0


def test_snr_by_pair_reports_clip_share():
    X = np.full((50, 8), 1.20)
    out = S.snr_by_pair(X)
    assert out["_clip_share"] == pytest.approx(1.0)


def test_snr_changes_when_denominator_is_censored():
    rng = np.random.default_rng(7)
    base = 0.93 + 0.06 * rng.standard_normal((4000, 8))
    base = np.clip(base, C.RHO_MIN, C.RHO_MAX)
    censored = np.minimum(base, 1.0094)
    pairs = ["m(%s,%s)" % pair for pair in S.PATH_PAIRS]
    original, capped = S.snr_by_pair(base), S.snr_by_pair(censored)
    ratios = [capped[pair]["snr"] / original[pair]["snr"] for pair in pairs
              if original[pair]["snr"] and capped[pair]["snr"]]
    assert len(ratios) == 6
    assert max(abs(ratio - 1.0) for ratio in ratios) > 0.01


def test_negative_control_gate_blocks_reading_m275():
    verdict, _action, m275, m276 = S.adjudicate(R_hi=1.0, R_nc=1.20)
    assert m275 is True and m276 is False
    assert verdict == "NEGATIVE_CONTROL_FAILED_STOP"
    assert S.NC_LO < 1.0 < S.NC_HI
    assert S.R_HIT_LO < 1.0 < S.R_HIT_HI
    assert S.CLEAN_CELL_MAX_P_CENSORED == 0.20


def test_t0_t11_regex_excludes_t12(tmp_path):
    path = tmp_path / "source.json"
    path.write_text('{"T11_old": 11, "T12_new": 12, "T2b_old": 2}')
    assert S.t0_t11_canonical((str(path),)) == {"T11_old": 11, "T2b_old": 2}

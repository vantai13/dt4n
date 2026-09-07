"""L2.1 -- lock the additivity decomposition. No root, no network."""
from __future__ import annotations

import json

import pytest

from tools.l2_1_additivity_recheck import (
    SIGNED_R_PATH,
    TANDEM_CLASS,
    cbr_floor_ms,
    decompose,
)
from twin.link_model_v2 import LinkModelV2


@pytest.fixture(scope="module")
def result():
    return decompose(subtract_floor=True)


def test_reproduces_signed_r_path(result):
    """The recomputation must reproduce Amendment 14 section 42 exactly."""
    for mode, signed in SIGNED_R_PATH.items():
        got = -result[mode]["summary"]["e_add_ms"]["mean"]
        assert abs(got - signed) < 1e-5, (mode, got, signed)


def test_e_add_is_positive_all_modes(result):
    """Signed prediction: sum of links >= path (pay bursts only once)."""
    for mode in result:
        summary = result[mode]["summary"]["e_add_ms"]
        assert summary["mean"] > 0.0
        assert summary["ci90"][0] > 0.0, "CI90 must exclude zero"


def test_e_add_positive_every_seed(result):
    for mode in result:
        signs = [row["e_add_ms"] > 0 for row in result[mode]["per_seed"]]
        assert all(signs), (mode, signs)


def test_interaction_is_algebraic_identity(result):
    """e_total = e_add + e_model holds by algebra on paired data, not physics."""
    for mode in result:
        assert result[mode]["summary"]["interaction_ms"] < 1e-9


def test_gate_l24_5_poisson_passes_h2_fires(result):
    """Headline operating point is clean; h2 exceeds the 15 % threshold."""
    assert result["poisson"]["summary"]["e_total_ms_pct_of_path"] < 15.0
    assert result["h2"]["summary"]["e_total_ms_pct_of_path"] > 15.0


def test_conclusion_survives_floor_convention():
    """Neither headline flips if the cbr floor is not subtracted."""
    raw = decompose(subtract_floor=False)
    assert raw["poisson"]["summary"]["e_total_ms_pct_of_path"] < 15.0
    assert raw["h2"]["summary"]["e_total_ms_pct_of_path"] > 15.0
    for mode in raw:
        assert raw[mode]["summary"]["e_add_ms"]["mean"] > 0.0


def test_e_add_identical_under_both_floor_conventions(result):
    """e_add is measured-minus-measured, so any floor cancels."""
    raw = decompose(subtract_floor=False)
    for mode in result:
        a = result[mode]["summary"]["e_add_ms"]["mean"]
        b = raw[mode]["summary"]["e_add_ms"]["mean"]
        assert abs(a - b) < 1e-12


def test_irreducible_floor_is_not_an_offset():
    """Guard the trap: irreducible_floor_ms returns sigma_schedule, an SD."""
    model = LinkModelV2.load("results/LIVE/phase-L/link_model_v2_fit.json")
    with open("results/LIVE/phase-L/link_model_v2_fit.json", encoding="utf-8") as fh:
        fit = json.load(fh)
    for link, (bw, q) in TANDEM_CLASS.items():
        sd = model.irreducible_floor_ms("poisson", bw, q)
        floor = cbr_floor_ms(fit, bw, q)
        assert sd > floor, (link, sd, floor)
        assert sd == pytest.approx(
            fit["links"]["poisson|%g|%d" % (bw, q)]["sigma_schedule"]
        )


def test_tandem_classes_exist_in_phase_l_fit():
    model = LinkModelV2.load("results/LIVE/phase-L/link_model_v2_fit.json")
    for mode in ("poisson", "h2"):
        for bw, q in TANDEM_CLASS.values():
            lo, hi = model.domain(mode, bw, q)
            assert lo <= 0.925 <= hi

"""Omitted choices fail at the API boundary, before IO or a campaign starts."""
import inspect
import pytest
from measurements import decision_error_v2 as DE
from measurements.explicit_choice import MUST_CHOOSE
from twin import cost_v2 as C

@pytest.mark.parametrize('fn', [DE.load_calibration, DE.feasible_cells,
                              DE.measurement_cells, C.CostV2])
def test_missing_artifact_choice_fails_before_io(fn):
    with pytest.raises(ValueError, match='explicit'):
        fn()

def test_sentinel_cannot_be_silently_coerced():
    with pytest.raises(TypeError, match='omitted'):
        bool(MUST_CHOOSE)

def test_explicit_exogenous_population_still_has_eight_gate_cells():
    cells = DE.feasible_cells('results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json',
                              include_pc1=False)
    assert len(cells) == 8

@pytest.mark.parametrize("fn", [DE.load_calibration, DE.feasible_cells])
def test_none_is_not_a_calibration_choice(fn):
    with pytest.raises(ValueError, match="calibration_path"):
        fn(None)

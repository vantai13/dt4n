"""G23-229 must distinguish observed F6=F2 from an unwired selector."""
from __future__ import annotations

import pytest

from tools import g23_229_family_selection_control as C


@pytest.fixture(scope="module")
def report() -> dict:
    return C.run()


def test_nondefault_family_reaches_selected_probability_path(report: dict) -> None:
    assert report["selection_exercised_nondefault_F6"] is True
    assert set(report["selected_families_by_fold"].values()) == {"F2", "F6"}
    assert report["selected_minus_F2"] == 0.0
    assert report["observed_F6_equals_F2"] is True


def test_forced_action_family_is_a_positive_control(report: dict) -> None:
    assert report["forced_family"] == "F2b_constant_P3"
    assert report["forced_F2b_minus_F2"] == pytest.approx(
        0.012923831842096334, abs=1e-15
    )
    assert report["forced_family_changes_risk"] is True
    assert report["pass"] is True

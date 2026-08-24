"""Wave-4 M-125 extension is locked to four paired U0 cells."""
from tools import wave4_axis_remeasure_impact as W


def test_exact_four_new_cells_and_paired_paths() -> None:
    assert len(W.CELLS) == len(set(W.CELLS)) == 4
    for cell in W.CELLS:
        assert "U0_legacy_sawtooth_51ms" in W.input_path(cell, W.runner.AX_LEG)
        assert "U0_measured_v7" in W.input_path(cell, W.runner.AX_MEA)


def test_preregistered_bands_unchanged() -> None:
    assert W.M125A_BAND == (0.05, 0.13)
    assert W.M125B_MAX_ABS == 0.25
    assert W.BETA == 0.431

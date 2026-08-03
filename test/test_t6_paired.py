"""Phase T / T.6e -- paired-by-seed analysis guards."""

import pytest

from measurements.t6_analyze import (
    assert_paired_mean_invariant,
    paired_cell_rows,
)


def _paired_fixture():
    main = []
    control = []
    dyn_by_seed = {
        11: -0.050,
        12: -0.040,
        13: -0.030,
        14: -0.020,
        15: -0.010,
    }
    tau_by_j = (0.2, 1.0, 5.0, 0.2, 1.0, 5.0)
    a_by_j = (0.2, 0.2, 0.2, 0.9, 0.9, 0.9)
    centered = (-0.003, -0.002, -0.001, 0.001, 0.002, 0.003)

    for seed, dyn in dyn_by_seed.items():
        schedule_offset = seed * 0.100
        control.append(
            {
                "block": "C",
                "mode": "h2",
                "rho_bar": 0.7,
                "seed": seed,
                "a": 0.0,
                "err_qs_corrected_ms": schedule_offset,
            }
        )
        for j, noise in enumerate(centered):
            main.append(
                {
                    "block": "A",
                    "mode": "h2",
                    "rho_bar": 0.7,
                    "seed": seed,
                    "a": a_by_j[j],
                    "tau_rho": tau_by_j[j],
                    "err_qs_corrected_ms": schedule_offset + dyn + noise,
                }
            )
    return main, control


def test_ghep_cap_khong_doi_gia_tri_trung_binh():
    """A18 changes only the error bar, not the point estimate."""
    main, control = _paired_fixture()
    paired = paired_cell_rows(main, control)
    t6d_cells = [
        {
            "mode": "h2",
            "rho_bar": 0.7,
            "mean_err_dyn_ms": -0.030,
        }
    ]

    invariant = assert_paired_mean_invariant(paired, t6d_cells)

    assert invariant["pass"] is True
    assert invariant["max_abs_diff_ms"] == pytest.approx(0.0, abs=1e-12)
    assert paired[0]["mean_dyn"] == pytest.approx(-0.030, abs=1e-12)
    assert paired[0]["n_seed"] == 5
    assert paired[0]["se_paired"] < 0.010

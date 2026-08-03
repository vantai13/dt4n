"""Phase T / T.6e -- paired-by-seed analysis guards."""

import pytest

from measurements.t6_analyze import (
    assert_paired_mean_invariant,
    paired_cell_rows,
    split_by_dynamics,
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


def test_t6f_split_phang_nghieng_ve_thiet_bi_va_loai_cbr():
    rows = []
    for a in (0.2, 0.9):
        for tau in (0.2, 1.0, 5.0):
            for seed in (11, 12, 13, 14, 15):
                rows.append(
                    {
                        "block": "A",
                        "mode": "h2",
                        "rho_bar": 0.85,
                        "a": a,
                        "tau_rho": tau,
                        "seed": seed,
                        "err_dyn_ms": -0.020 + 0.0001 * (seed - 13),
                    }
                )
    rows.append(
        {
            "block": "B",
            "mode": "cbr",
            "rho_bar": 0.98,
            "a": 0.9,
            "tau_rho": 1.0,
            "seed": 11,
            "err_dyn_ms": -0.5,
        }
    )

    out = split_by_dynamics(rows)

    assert out["stable_n"] == 30
    assert out["cbr_excluded_n"] == 1
    assert out["a_ratio_abs_0p9_over_0p2"] == pytest.approx(1.0)
    assert out["tau_abs_dynamic_monotonic"] is False
    assert out["instrumentation_support"] is True
    assert out["ket_luan_nghieng_ve"] == "thiet_bi"


def test_t6f_ratio_lon_gia_khong_duoc_goi_la_dong_luc():
    rows = []
    noise = (-0.001, -0.0005, 0.0, 0.0005, 0.001)
    a_effect = {0.2: 0.000001, 0.9: 0.000006}
    tau_effect = {0.2: 0.000003, 1.0: 0.000002, 5.0: 0.000001}
    for a in (0.2, 0.9):
        for tau in (0.2, 1.0, 5.0):
            for seed, eps in zip((11, 12, 13, 14, 15), noise):
                rows.append(
                    {
                        "block": "A",
                        "mode": "poisson",
                        "rho_bar": 0.85,
                        "a": a,
                        "tau_rho": tau,
                        "seed": seed,
                        "err_dyn_ms": a_effect[a] + tau_effect[tau] + eps,
                    }
                )

    out = split_by_dynamics(rows)

    assert out["a_ratio_abs_0p9_over_0p2"] > 2.0
    assert out["tau_abs_dynamic_monotonic"] is True
    assert out["max_a_pairwise_abs_z"] < 2.0
    assert out["max_tau_pairwise_abs_z"] < 2.0
    assert out["dynamic_support"] is False
    assert out["ket_luan_nghieng_ve"] == "thiet_bi"

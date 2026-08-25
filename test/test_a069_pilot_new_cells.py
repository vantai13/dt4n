import subprocess

from tools import a069_pilot_new_cells as P


def test_pilot_grid_is_exact_and_has_two_families_per_rho() -> None:
    assert P.RHOS == (0.740, 0.780, 0.820)
    assert P.MODES == ("poisson", "h2")
    assert len({(m, r) for m in P.MODES for r in P.RHOS}) == 6


def test_pilot_report_cell_allowlist_is_exact() -> None:
    assert P.ALLOWED_CELL_FIELDS == {
        "cell", "mode", "rho_bar", "err_neo", "n_calib_blocks",
        "n_test_blocks", "kappa_A", "build_seconds", "parquet_sha256",
        "builder_report_sha256",
    }


def test_pilot_never_overwrites_the_frozen_calibration() -> None:
    assert P.PILOT_CALIBRATION != P.BASE_CALIBRATION
    assert "A069" in P.PILOT_CALIBRATION


def test_builder_stdout_is_suppressed_before_any_pilot_outcome_is_printed(
    monkeypatch,
) -> None:
    seen = {}

    def fake_run(cmd, **kwargs):
        seen.update(kwargs)

    monkeypatch.setattr(P.subprocess, "run", fake_run)
    monkeypatch.setattr(P.time, "monotonic", iter((10.0, 12.0)).__next__)
    P._run_builder("poisson", 0.740, "sidecar.json", "out")
    assert seen["stdout"] is subprocess.DEVNULL
    assert seen["stderr"] is subprocess.PIPE
    assert seen["text"] is True


def test_stop_rules_require_common_alive_rho_and_capacity_and_cost() -> None:
    rows = [
        {"cell": f"{m}@{r:.3f}", "mode": m, "rho_bar": r,
         "err_neo": (0.06 if r == 0.780 else 0.01),
         "n_calib_blocks": 500, "build_seconds": 10.0}
        for m in P.MODES for r in P.RHOS
    ]
    out = P.score_stop_rules(rows)
    assert out["common_alive_rho"] == [0.780]
    assert out["may_proceed_to_prereg"] is True
    rows[0]["n_calib_blocks"] = 499
    assert P.score_stop_rules(rows)["may_proceed_to_prereg"] is False

import copy
import json

from cert import a070_extension as E


def test_load_all_kappa_returns_exactly_live_cells_not_dead_ones(
        monkeypatch, tmp_path) -> None:
    """RT.load_kappa_A() tra ve CA 4 cell CHET vi RT.run() cham ma tran dead.

    `M-220` duoc ky tren DUNG 11 cell song va `score_m220` bao cao
    `n_cells = len(kappa)`, nen kappa map LOT cell chet se ghi mot con so
    SAI vao artifact da ky.
    """
    pilot = tmp_path / "pilot.json"
    pilot.write_text(json.dumps({"cells": [
        {"cell": c, "kappa_A": 0.5, "parquet_sha256": "digest"}
        for c in E.NEW_LIVE]}))
    monkeypatch.setattr(E, "A069_PILOT", str(pilot))
    monkeypatch.setattr(E, "pin", lambda path: {"sha256": "digest"})
    monkeypatch.setattr(E.RT, "load_kappa_A", lambda: {
        "h2@0.650": 1.0, "poisson@0.960": 2.0,
        "h2@0.850": 9.0, "poisson@0.700": 9.0,
    })
    live = ("h2@0.650", "poisson@0.960") + E.NEW_LIVE
    kappa = E.load_all_kappa(live)
    assert set(kappa) == set(live)
    assert "h2@0.850" not in kappa
    assert "poisson@0.700" not in kappa
    assert len(kappa) == len(live)


def test_load_all_kappa_refuses_a_live_cell_it_has_no_kappa_for(
        monkeypatch, tmp_path) -> None:
    pilot = tmp_path / "pilot.json"
    pilot.write_text(json.dumps({"cells": [
        {"cell": c, "kappa_A": 0.5, "parquet_sha256": "digest"}
        for c in E.NEW_LIVE]}))
    monkeypatch.setattr(E, "A069_PILOT", str(pilot))
    monkeypatch.setattr(E, "pin", lambda path: {"sha256": "digest"})
    monkeypatch.setattr(E.RT, "load_kappa_A", lambda: {"h2@0.650": 1.0})
    try:
        E.load_all_kappa(("h2@0.650", "poisson@0.960") + E.NEW_LIVE)
    except RuntimeError as exc:
        assert "poisson@0.960" in str(exc)
    else:
        raise AssertionError("phai tu choi khi thieu kappa_A cua cell song")


def test_new_live_cells_are_exact_and_were_blind_at_prereg() -> None:
    assert E.NEW_LIVE == ("h2@0.740", "poisson@0.780", "poisson@0.820")
    assert E.A_STARS == (0.30, 0.42679, 0.55)
    assert E.FLOORS == (0.20, 0.30)


def test_nc_e_0_compares_all_scientific_bits_but_not_dynamic_provenance() -> None:
    ref = {"rows": [{"x": 1.25}], "predictions": {"hit": True},
           "provenance": {"utc": "old", "git_hash": "a"}}
    new = copy.deepcopy(ref)
    new["provenance"] = {"utc": "new", "git_hash": "b"}
    assert E.compare_reference(ref, new)["scientific_payload_bit_exact"] is True
    new["rows"][0]["x"] = 1.2500000000001
    assert E.compare_reference(ref, new)["scientific_payload_bit_exact"] is False


def test_m219_uses_signed_four_step_rule() -> None:
    rows = []
    for i in range(3):
        matched = {}
        for level, c3, b2 in (
            ("0.70", .10, .11), ("0.50", .08, .10),
            ("0.30", .05, .09), ("0.15", .03, .06),
        ):
            matched[level] = {"err_C3R": c3, "err_B2R": b2}
        rows.append({"matched": matched})
    out = E.score_m219(rows)
    assert out["n_nondecreasing_of_4"] == 3
    assert out["all_C3R_le_B2R"] is True
    assert out["hit"] is True


def test_m220_scores_slope_and_rank_on_off_diagonal_only() -> None:
    kappa = {"a": 1.0, "b": 2.0, "c": 4.0}
    rows = []
    for a in kappa:
        for b in kappa:
            x = abs(__import__("math").log(kappa[a] / kappa[b]))
            rows.append({"A": a, "B": b,
                         "C3_acceptance_test": E.RT.A_STAR + 0.5 * x})
    out = E.score_m220(rows, kappa)
    assert out["n_off_diagonal"] == 6
    assert abs(out["slope"] - 0.5) < 1e-12
    assert out["spearman"] >= 0.90
    assert out["hit"] is True

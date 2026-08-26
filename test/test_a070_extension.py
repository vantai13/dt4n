import copy

from cert import a070_extension as E


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

"""Golden tests for Phase 20R measured decision-error helpers."""

import json

import numpy as np
import pandas as pd
import pytest

from measurements import decision_error_v2 as D
from twin import cost_v2 as C
from twin import topology_v7 as T7


def _mini_truth(tmp_path):
    rows = []
    for mode in ("poisson", "h2", "cbr"):
        for bw, q in {(float(v[0]), int(v[2])) for v in T7.LINKS.values()}:
            for rho in (0.5, 0.6, 0.7):
                rows.append(
                    {
                        "mode": mode,
                        "bw": bw,
                        "q": q,
                        "rho": rho,
                        "delay_mean_ms": 10.0 * rho + bw + q * 0.01,
                        "loss": 0.001 * rho,
                        "se_mean_ms": 0.01,
                        "source": "test",
                        "n_seed": 5,
                    }
                )
    table = pd.DataFrame(rows)
    table.attrs["truth_field"] = "q_mean_ms"
    path = tmp_path / "truth.parquet"
    table.to_parquet(path, index=False)
    return path, table


def test_truth_table_delay_loss_returns_exact_grid_value_plus_static_terms(tmp_path):
    path, table = _mini_truth(tmp_path)
    tt = D.TruthTable(str(path))
    link = "uA"
    bw, base, q = T7.LINKS[link]
    rho = 0.6
    delay, loss = tt.delay_loss("poisson", link, np.array([rho]))
    expected = table[
        (table["mode"] == "poisson")
        & (table["bw"] == float(bw))
        & (table["q"] == int(q))
        & (table["rho"] == rho)
    ].iloc[0]

    assert delay[0] - float(base) - C.serialization_ms(bw) == pytest.approx(expected["delay_mean_ms"], abs=1e-9)
    assert loss[0] == pytest.approx(expected["loss"], abs=1e-12)


def test_truth_table_clip_fraction_records_out_of_domain_rate(tmp_path):
    path, _table = _mini_truth(tmp_path)
    tt = D.TruthTable(str(path))

    tt.delay_loss("poisson", "uA", np.array([0.4, 0.55, 0.8]))

    assert tt.clip_log["poisson|uA"] == pytest.approx(2.0 / 3.0)


def test_error_decomposition_is_exact_identity():
    d_true = np.array([[3.0, 5.0], [4.0, 6.0], [7.0, 9.0], [9.0, 10.0]])
    d_fresh = np.array([[2.5, 4.0], [3.5, 5.5], [6.0, 8.0], [8.0, 9.5]])

    e_model, e_stale, total = D._decomposition(d_true, d_fresh, k=1)

    assert np.allclose(e_model + e_stale, total, atol=1e-9)


def test_check_z_grid_rejects_duplicate_lags_at_dt_0p2():
    with pytest.raises(ValueError, match="AoI aliasing"):
        D.check_z_grid([0.05, 0.10, 0.20], 0.2, require_sawtooth_age=False)


def test_scaled_z_values_follow_tau_ratios():
    assert D.z_values_for(tau=2.0, scaled=True) == pytest.approx((0.20, 0.60, 1.10, 2.00))


def test_parse_float_list_accepts_empty_and_values():
    assert D.parse_float_list("") == ()
    assert D.parse_float_list("0.65, 0.78,0.88") == pytest.approx((0.65, 0.78, 0.88))

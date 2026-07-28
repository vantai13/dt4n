import numpy as np
import pandas as pd

from cert.usefulness import bootstrap_frontier, build_gates, fit_qhat_B, gate_metrics


def _toy_frame(n_blocks=40, rows_per_block=10):
    rows = []
    for block in range(n_blocks):
        z_bin = block % 2
        for i in range(rows_per_block):
            score = 10 + 5 * z_bin + i + 0.1 * block
            gap = 30 - score + (i % 3)
            wrong = bool(z_bin and i >= 6)
            rows.append(
                {
                    "block_full": True,
                    "block_id": block,
                    "z_bin": z_bin,
                    "s_vs_a1": score,
                    "gap_twin": gap,
                    "wrong": wrong,
                    "viol_twin": float(wrong),
                    "viol_opt": 0.0,
                    "regret": float(i if wrong else 0),
                }
            )
    return pd.DataFrame(rows)


def test_fit_qhat_B_returns_ordered_finite_bins():
    df = _toy_frame()

    qhat = fit_qhat_B(df)

    assert sorted(qhat) == [0, 1]
    assert np.isfinite(qhat[0])
    assert np.isfinite(qhat[1])
    assert qhat[1] > qhat[0]


def test_gates_and_bootstrap_have_expected_shapes():
    df = _toy_frame()
    calib = df[df.block_id < 20].reset_index(drop=True)
    test = df[df.block_id >= 20].reset_index(drop=True)
    qhat = fit_qhat_B(calib)

    gates = build_gates(calib, test, qhat, eps_grid=[0, 20], seed=123)
    metrics = gate_metrics(test, gates[-1]["adaptive"])
    draws = bootstrap_frontier(test, gates, n_boot=7, seed=456)

    assert len(gates) == 2
    assert 0.0 <= metrics["coverage"] <= 1.0
    assert draws["adaptive"]["err"].shape == (7, 2)
    assert draws["const"]["cov"].shape == (7, 2)

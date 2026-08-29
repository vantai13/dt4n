import json
from pathlib import Path

import numpy as np
import pytest

from tools.phase_d_factorial_audit import build_artifact
from tools.phase_d_pc_c2_prime import acf_prefix
from tools.phase_d_scaling_test import autocorrelation_fft, fisher_ci, tau_integral
from tools.summarize_infra import summarize
from tools.trust_gate_bench import run_benchmark


def test_tau_integral_for_white_noise_is_finite():
    values = np.random.default_rng(7).normal(size=4096)
    tau_s, cut = tau_integral(values, 0.01)
    assert np.isfinite(tau_s)
    assert tau_s >= 0.005
    assert cut >= 0


def test_fft_acf_starts_at_one():
    acf = autocorrelation_fft(np.arange(32, dtype=float), 4)
    assert acf.shape == (5,)
    assert acf[0] == 1.0


def test_pc_c2_prime_fft_matches_direct_acf():
    values = np.random.default_rng(19).normal(size=257)
    centered = values - values.mean()
    direct = np.array([
        1.0 if lag == 0 else centered[:-lag] @ centered[lag:] / (centered @ centered)
        for lag in range(33)
    ])
    assert acf_prefix(values, 32) == pytest.approx(direct, abs=1e-12)


def test_fisher_ci_requires_effective_samples():
    assert fisher_ci(0.5, 4.0) == (None, None)
    low, high = fisher_ci(0.5, 30.0)
    assert low < 0.5 < high


def test_infra_summary_flags_are_emitted(tmp_path):
    source = tmp_path / "infra.jsonl"
    rows = [
        {"_header": True, "interval_s": 0.1},
        {"cpu_percent": 10, "cpu_percent_max_core": 20, "ctx_switches_delta": 10,
         "clock_skew_ms": 0.0, "swap_percent": 0, "drop_in": 1, "drop_out": 2, "load_1m": 0.5},
        {"cpu_percent": 20, "cpu_percent_max_core": 30, "ctx_switches_delta": 20,
         "clock_skew_ms": 0.1, "swap_percent": 0, "drop_in": 1, "drop_out": 2, "load_1m": 0.6},
    ]
    source.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    result = summarize(source)
    assert result["samples"] == 2
    assert result["net_drops"] == 0
    assert result["flag_cpu_saturated"] is False
    assert result["flag_clock_jump"] is False


def test_trust_gate_microbenchmark_smoke():
    result = run_benchmark(2, 10, m_hat=8.0, z_bin=2, kappa=1.0)
    assert result["accepted"] is True
    assert result["n"] == 10
    assert result["p99_ms"] >= 0


def test_factorial_audit_uses_all_pairs_and_locks_cells():
    artifact = build_artifact(
        source=Path("results/LIVE/phase-23/link_corr_matrix.json"),
        campaign=Path("results/RAW/phase-23/aoi_v7_campaign"),
        design_meta=Path(
            "results/RAW/phase-23/aoi_v7_campaign/meta_clean_rho0.925_rep3.json"
        ),
    )
    assert artifact["n_pairs_analyzed"] == 28
    assert {key: value["n"] for key, value in artifact["cells"].items()} == {
        "nlow2_shared1": 2,
        "nlow2_shared0": 4,
        "nlow1_shared1": 8,
        "nlow1_shared0": 8,
        "nlow0_shared1": 4,
        "nlow0_shared0": 2,
    }
    assert artifact["cells"]["nlow2_shared1"]["mean_r"] == pytest.approx(0.618089464, abs=1e-6)
    assert artifact["cells"]["nlow2_shared0"]["mean_r"] == pytest.approx(0.036415139, abs=1e-6)
    assert artifact["cells"]["nlow0_shared1"]["mean_r"] == pytest.approx(0.017149527, abs=1e-6)
    assert artifact["verdict"]["H4_endpoint_x_load_interaction"]["descriptively_supported"] is True

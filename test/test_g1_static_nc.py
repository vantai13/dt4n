import math

import numpy as np
import pandas as pd
import pytest

from mininet.run_sync_v7 import MEASURED_CSV_FIELDS
from mininet.static_emitter import StaticConfig
from mininet.traffic_static import static_profile
from tools.g1_static_nc import LINKS, certify, discriminate, nugget_direct, pair_table


def test_locked_static_geometry_matches_lesson_reference():
    cfg = StaticConfig(8.0, 0.857)
    assert cfg.rate_pps == pytest.approx(612.142857, rel=1e-6)
    assert cfg.gap_s * 1e3 == pytest.approx(1.633605, rel=1e-6)
    assert cfg.n_pkt_per_window(0.2) == pytest.approx(122.428571, rel=1e-6)
    assert cfg.sigma_quant_floor(0.2) == pytest.approx(0.0023577, rel=1e-4)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cap_mbps": 0, "rho_target": 0.5},
        {"cap_mbps": 8, "rho_target": 0},
        {"cap_mbps": 8, "rho_target": 1},
        {"cap_mbps": 8, "rho_target": 0.5, "payload_bytes": 0},
    ],
)
def test_static_config_rejects_invalid_physical_domain(kwargs):
    with pytest.raises(ValueError):
        StaticConfig(**kwargs)


def test_static_profile_declares_zero_true_sigma():
    caps = {link: 8.0 for link in LINKS}
    targets = {link: 0.5 for link in LINKS}
    profile = static_profile(caps, targets)
    assert all(row.as_dict()["sigma_true"] == 0.0 for row in profile.values())


def test_measured_schema_is_backward_compatible_and_adds_rx_diagnostics():
    old = {"sample_index", "timestamp_s", "link", "rho", "throughput_mbps", "tx_bytes_delta", "dt_s"}
    assert old <= set(MEASURED_CSV_FIELDS)
    assert {"rx_bytes_delta", "rho_rx", "read_duration_us"} <= set(MEASURED_CSV_FIELDS)


def test_white_direct_measurement_and_pair_table_are_finite():
    rng = np.random.default_rng(123)
    common = rng.normal(size=10000)
    data = {link: common + rng.normal(size=10000) for link in LINKS}
    direct = nugget_direct(data["uA"])
    assert direct["white_ratio"] == pytest.approx(1.0, abs=0.04)
    pairs = pair_table(pd.DataFrame(data))
    assert len(pairs) == math.comb(len(LINKS), 2)
    assert all(np.isfinite(row["rho_eps_level"]) for row in pairs)
    assert discriminate(pairs)["same_tx_node"]["n_in"] == 3


def test_certificate_never_certifies_an_invalid_cell():
    invalid = {
        "cell": "A",
        "status": "INVALID",
        "telemetry_config": {},
        "validity": {"G1S-2_white_all_links": False},
    }
    cert = certify([invalid], [0.01, 0.02])
    assert cert["A"]["status"] == "INVALID"
    assert "v_worst_link" not in cert["A"]

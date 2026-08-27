import csv

import numpy as np

from measurements import host_confound_probe as H
from measurements import link_corr_matrix as A
from mininet import traffic_v7


def test_load_channel_map_matches_real_generator():
    assert A.LOAD_CHANNELS == traffic_v7.LOAD_CHANNELS


def test_load_offered_reads_rho_column_not_timestamp(tmp_path):
    # Timestamp tang manh va co the tuong quan gia; rho la cot thu ba moi dung.
    for j, link in enumerate(A.LINKS):
        path = tmp_path / ("rho_offered_%s.csv" % link)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["sample_index", "timestamp_s", "rho_offered",
                         "n_active", "rate_sum_bps"])
            for i in range(40):
                wr.writerow([i, 1000 + i, j + (0.0 if i < 20 else 2.0), 1, 1])
    got = H.load_offered(str(tmp_path), n_target=2)
    assert got.shape == (2, len(A.LINKS))
    assert np.allclose(got[0], np.arange(len(A.LINKS)))
    assert np.allclose(got[1], np.arange(len(A.LINKS)) + 2.0)


def test_probe_scenario_partition():
    base = {"uA-uB": {"r_offered": 0.1, "r_measured": 0.6,
                       "r_shortfall": 0.5}}
    assert H.adjudicate(base)["verdict"] == "HOST_SHORTFALL_SUPPORTED"
    base["uA-uB"]["r_shortfall"] = 0.1
    assert H.adjudicate(base)["verdict"] == "SWITCH_OR_MEASUREMENT_INSTRUMENT"
    base["uA-uB"]["r_offered"] = 0.6
    assert H.adjudicate(base)["verdict"] == "GENERATOR_DESIGN_OR_SHARED_RNG"

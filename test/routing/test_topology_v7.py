#!/usr/bin/env python3
"""Tests for the Phase 20 topology-v7 stage."""

import sys

sys.path.insert(0, ".")

from twin import topology_v7 as T7  # noqa: E402


def test_bandwidths_stay_inside_calibrated_set():
    assert {cfg[0] for cfg in T7.LINKS.values()} <= {4.0, 6.0, 8.0}


def test_every_link_is_used_by_a_proper_subset():
    sharing = T7.sharing_matrix()
    assert sharing["uA"] == ("P1", "P2")
    assert sharing["uB"] == ("P3", "P4")
    assert sharing["vC"] == ("P1", "P3")
    assert sharing["vD"] == ("P2", "P4")
    for users in sharing.values():
        assert 0 < len(users) < T7.K


def test_each_path_has_a_core_link_near_jump_targets():
    core = {"ac", "ad", "bc", "bd"}
    for path, links in T7.PATHS.items():
        hot_links = [link for link in links if link in core]
        assert hot_links, path
        assert any(
            abs(T7.LOAD_MEAN[link] - jump) <= 0.0125
            for link in hot_links
            for jump in T7.JUMPS
        )


def test_decide_uses_lowest_index_for_exact_tie(monkeypatch):
    tied_costs = {"P1": 1.0, "P2": 1.0, "P3": 2.0, "P4": 3.0}
    monkeypatch.setattr(T7, "path_cost", lambda _rho, path, _w_loss: tied_costs[path])

    best, _costs, has_tie = T7.decide({}, w_loss=0.0)
    assert has_tie is True
    assert best == 0


def test_r_jump_uses_distance_to_link_model_steps():
    rho = {link: 0.80 for link in T7.LINK_NAMES}
    rho["ac"] = T7.JUMPS[0] + 0.004
    rho["bd"] = T7.JUMPS[1] - 0.002
    assert abs(T7.r_jump(rho) - 0.002) < 1e-12

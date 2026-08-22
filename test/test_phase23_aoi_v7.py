import json
import types

import pytest

from bridge import sync_agent as SYNC
from bridge.topology_v7_map import link_thing_ids
from measurements import aoi_probe_v7 as PROBE
from measurements import aoi_estimate_v7 as ESTIMATE
from measurements import run_aoi_campaign_v7 as CAMPAIGN
from twin import topology_v7 as T7
from mininet.run_sync_v7 import feasible_traffic_rho_targets


def test_probe_counterbalances_order_and_records_individual_observation(monkeypatch):
    ids = link_thing_ids()
    calls = []

    def fake_get(_session, thing_id):
        calls.append(thing_id)
        return {"features": {
            "meta": {"properties": {"tSource": 100.0}},
            "traffic": {"properties": {"txRate": 500000.0}},
            "capacity": {"properties": {"bwMbps": 8.0}},
        }}, True

    tick = iter(100.5 + i * 0.001 for i in range(100))
    monkeypatch.setattr(PROBE, "_get_one", fake_get)
    monkeypatch.setattr(PROBE.time, "time", lambda: next(tick))

    forward = PROBE.probe_once(object(), ids, 0)
    forward_calls = list(calls)
    calls.clear()
    reverse = PROBE.probe_once(object(), ids, 1)

    assert forward["probe_order"] == "fwd"
    assert reverse["probe_order"] == "rev"
    assert forward_calls == [ids[name] for name in T7.LINK_NAMES]
    assert calls == [ids[name] for name in reversed(T7.LINK_NAMES)]
    assert [forward["links"][name]["read_pos"] for name in T7.LINK_NAMES] == list(range(8))
    assert [reverse["links"][name]["read_pos"] for name in T7.LINK_NAMES] == list(reversed(range(8)))
    assert len({forward["links"][name]["t_obs"] for name in T7.LINK_NAMES}) == 8
    assert forward["links"]["uA"]["rho"] == 0.5


def test_probe_does_not_clip_negative_aoi(monkeypatch):
    ids = link_thing_ids()
    monkeypatch.setattr(
        PROBE,
        "_get_one",
        lambda _session, _thing_id: (
            {"features": {"meta": {"properties": {"tSource": 101.0}}}},
            True,
        ),
    )
    monkeypatch.setattr(PROBE.time, "time", lambda: 100.0)
    row = PROBE.probe_once(object(), ids, 0)
    assert all(value["aoi_s"] == -1.0 for value in row["links"].values())


def test_probe_writes_frozen_header_schema(tmp_path):
    out = tmp_path / "aoi.jsonl"
    count = PROBE.run(
        duration_s=0.0,
        interval_s=0.1,
        out_path=str(out),
        meta={
            "mode": "clean",
            "rho_bar": 0.925,
            "repeat": 1,
            "sync_period_s": 0.5,
            "tol": 0.0,
            "reconcile_every": 1,
            "probe_interval_s": 0.1,
            "duration_s": 0.0,
        },
    )
    header = json.loads(out.read_text(encoding="utf-8"))
    assert count == 0
    assert header["schema"] == "dt4n.aoi.v7.v1"
    assert header["record"] == "header"
    assert header["spec_sha256"]
    assert header["mode"] == "clean"


def test_sync_filter_excludes_unregistered_access_links(tmp_path, monkeypatch):
    class FakeCollector:
        def __init__(self, *_args, **_kwargs):
            pass

        def collect_all(self):
            now = SYNC.time.time()
            return {
                "t_cycle_start": now,
                "cycle_scan_ms": 0.0,
                "things": {
                    "host-h1": {
                        "attributes": {"type": "host"},
                        "features": {"status": {"state": "up"}},
                        "t_source": now,
                    },
                    "link-h1-s1": {
                        "attributes": {"type": "link", "endpointA": "h1", "endpointB": "s1"},
                        "features": {"status": {"state": "up"}},
                        "t_source": now,
                    },
                },
            }

    pushed = []
    monkeypatch.setattr(SYNC, "Collector", FakeCollector)
    monkeypatch.setattr(SYNC, "make_session", lambda: object())
    monkeypatch.setattr(
        SYNC, "patch_thing", lambda thing_id, *_args, **_kwargs: pushed.append(thing_id) or True
    )
    trace = tmp_path / "cycles.jsonl"
    SYNC.run(
        types.SimpleNamespace(),
        period=0.001,
        max_cycles=1,
        measurement_mode="clean",
        thing_ids={"org.dt4n:host-h1"},
        cycle_trace_path=str(trace),
    )
    row = json.loads(trace.read_text(encoding="utf-8"))
    assert pushed == ["org.dt4n:host-h1"]
    assert row["n_things"] == row["n_pushed"] == 1


def test_counterbalanced_regression_recovers_link_offsets_and_read_cost():
    alpha_s = {
        name: (index - 3.5) * 0.001
        for index, name in enumerate(T7.LINK_NAMES)
    }
    beta_s = 0.002
    probes = []
    for k in range(20):
        order = list(T7.LINK_NAMES)
        if k % 2:
            order.reverse()
        links = {}
        for pos, logical in enumerate(order):
            links[logical] = {
                "aoi_s": 0.3 + alpha_s[logical] + beta_s * pos,
                "read_pos": pos,
                "t_source": 100.0 + k,
                "rho": 0.8 + 0.01 * pos,
            }
        probes.append({"links": links})

    fitted = ESTIMATE.estimate_offsets(probes)

    assert fitted["design_rank"] == fitted["design_columns"] == 9
    assert fitted["beta_ms_per_pos"] == pytest.approx(2.0)
    for logical in T7.LINK_NAMES:
        assert fitted["offset_ms"][logical] == pytest.approx(alpha_s[logical] * 1000.0)


def test_campaign_schedule_is_frozen_randomized_full_factorial():
    schedule = CAMPAIGN.frozen_schedule()
    cells = {
        (row["mode"], row["rho_bar"], row["repeat"])
        for row in schedule
    }
    assert len(schedule) == len(cells) == 30
    assert [row["order"] for row in schedule] == list(range(1, 31))
    assert schedule == CAMPAIGN.frozen_schedule()
    assert schedule[0]["tag"] == "prod_rho0.700_rep3"


def test_high_rho_projection_preserves_campaign_mean_and_generator_domain():
    targets = feasible_traffic_rho_targets(0.960)
    assert sum(targets.values()) / len(targets) == pytest.approx(0.960)
    assert max(targets.values()) == pytest.approx(0.995)
    assert all(0.0 < value < 1.0 for value in targets.values())


def test_feasible_rho_projection_is_identity_when_raw_vector_is_valid():
    targets = feasible_traffic_rho_targets(0.925)
    assert targets == pytest.approx({
        "uA": 0.8575, "uB": 0.8775, "ac": 0.9775, "ad": 0.9875,
        "bc": 0.9725, "bd": 0.9825, "vC": 0.8575, "vD": 0.8875,
    })

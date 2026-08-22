import json
from pathlib import Path
import types

from bridge import collector as COL
from bridge import pusher as PUSH
from bridge import sync_agent as SYNC


class _Node:
    def __init__(self, name):
        self.name = name


class _Intf:
    def __init__(self, node, name):
        self.node = node
        self.name = name
        self.params = {}

    def isUp(self):
        return True


class _Link:
    def __init__(self, a, b):
        self.intf1 = _Intf(a, f"{a.name}-eth1")
        self.intf2 = _Intf(b, f"{b.name}-eth1")


def test_collector_records_per_thing_timestamps_and_cycle_span(monkeypatch):
    host = _Node("h1")
    switch = _Node("s1")
    net = types.SimpleNamespace(hosts=[host], switches=[switch], links=[_Link(host, switch)])
    collector = COL.Collector(net)
    collector.collect_host = lambda _host, _now: {
        "attributes": {"type": "host"}, "features": {}
    }
    collector.collect_switch = lambda _switch: {
        "attributes": {"type": "switch"}, "features": {}
    }
    collector.collect_link = lambda link, _now: {
        "attributes": {
            "type": "link",
            "endpointA": link.intf1.node.name,
            "endpointB": link.intf2.node.name,
        },
        "features": {},
    }
    times = iter([100.0, 100.001, 100.003, 100.006, 100.010])
    monkeypatch.setattr(COL.time, "time", lambda: next(times))

    snapshot = collector.collect_all()

    assert snapshot["t_cycle_start"] == 100.0
    assert snapshot["t_source"] == 100.0
    assert snapshot["things"]["host-h1"]["t_source"] == 100.001
    assert snapshot["things"]["switch-s1"]["t_source"] == 100.003
    assert snapshot["things"]["link-h1-s1"]["t_source"] == 100.006
    assert snapshot["t_cycle_end"] == 100.010
    assert abs(snapshot["cycle_scan_ms"] - 10.0) < 1e-9


def test_pusher_trace_contains_source_send_ack(tmp_path, monkeypatch):
    trace = tmp_path / "push.jsonl"
    monkeypatch.setattr(PUSH, "PUSH_TRACE_PATH", str(trace))
    monkeypatch.setattr(PUSH, "_do_patch", lambda *_args, **_kwargs: True)
    times = iter([200.0, 200.012])
    monkeypatch.setattr(PUSH.time, "time", lambda: next(times))

    ok = PUSH.patch_thing(
        "org.dt4n:link-a-b",
        {"features": {"meta": {"properties": {"tSource": 199.9}}}},
    )

    row = json.loads(trace.read_text(encoding="utf-8"))
    assert ok is True
    assert row["t_source"] == 199.9
    assert row["t_send"] == 200.0
    assert row["t_ack"] == 200.012
    assert abs(row["push_ms"] - 12.0) < 1e-9
    assert row["ok"] is True


def test_clean_mode_forces_full_push_and_writes_cycle_trace(tmp_path, monkeypatch):
    class FakeCollector:
        def __init__(self, *_args, **_kwargs):
            pass

        def collect_all(self):
            return {
                "t_cycle_start": SYNC.time.time(),
                "cycle_scan_ms": 0.1,
                "things": {
                    "host-h1": {
                        "attributes": {"type": "host"},
                        "features": {"status": {"state": "up"}},
                        "t_source": SYNC.time.time(),
                    }
                },
            }

    trace = tmp_path / "cycles.jsonl"
    monkeypatch.setattr(SYNC, "Collector", FakeCollector)
    monkeypatch.setattr(SYNC, "make_session", lambda: object())
    monkeypatch.setattr(SYNC, "patch_thing", lambda *_args, **_kwargs: True)
    net = types.SimpleNamespace()

    SYNC.run(
        net,
        period=0.001,
        max_cycles=2,
        measurement_mode="clean",
        reconcile_every=30,
        cycle_trace_path=str(trace),
    )

    rows = [json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert all(row["mode"] == "clean" for row in rows)
    assert all(row["is_reconcile"] for row in rows)
    assert all(row["n_pushed"] == row["n_things"] == 1 for row in rows)
    assert all("lock_wait_ms" in row and "cycle_scan_ms" in row for row in rows)

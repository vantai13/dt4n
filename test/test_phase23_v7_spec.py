import json

from bridge.topology_v7_map import SPEC_PATH, link_thing_ids
from twin import topology_v7 as T7


def test_v7_spec_matches_topology_module():
    with open(SPEC_PATH, encoding="utf-8") as handle:
        spec = json.load(handle)
    logical = tuple(link["logical"] for link in spec["links"])
    assert logical == T7.LINK_NAMES, "sai ten hoac sai thu tu link"
    for link in spec["links"]:
        bw, delay, queue = T7.LINKS[link["logical"]]
        assert link["bwMbps"] == bw
        assert link["delayMs"] == delay
        assert link["maxQueuePkts"] == queue


def test_v7_thing_ids_unique_and_ordered():
    ids = link_thing_ids()
    assert tuple(ids) == T7.LINK_NAMES
    assert len(set(ids.values())) == len(T7.LINK_NAMES) == 8


def test_v7_spec_node_sets_match_runner():
    from mininet.run_sync_v7 import HOST_IPS, SWITCHES

    with open(SPEC_PATH, encoding="utf-8") as handle:
        spec = json.load(handle)
    assert tuple(item["name"] for item in spec["switches"]) == SWITCHES
    assert {item["name"]: item["ip"] for item in spec["hosts"]} == HOST_IPS

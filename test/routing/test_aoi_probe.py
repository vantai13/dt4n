#!/usr/bin/env python3
"""Tests for Lesson 9.0c AoI probe helpers."""

import os
import sys
import tempfile

sys.path.insert(0, ".")

import measurements.aoi_probe as probe  # noqa: E402


def test_read_tx_bytes_kernel_uses_tx_column():
    old_path = probe.PROC_NET_DEV
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        path = f.name
        f.write(
            "Inter-|   Receive                                                |  Transmit\n"
        )
        f.write(
            " face |bytes    packets errs drop fifo frame compressed multicast|"
            "bytes    packets errs drop fifo colls carrier compressed\n"
        )
        f.write("sC-eth3: 10 1 0 0 0 0 0 0 12345 9 0 0 0 0 0 0\n")
    try:
        probe.PROC_NET_DEV = path
        assert probe.read_tx_bytes_kernel("sC-eth3") == 12345
        assert probe.read_tx_bytes_kernel("missing0") is None
    finally:
        probe.PROC_NET_DEV = old_path
        os.unlink(path)


def test_kernel_meter_converts_counter_delta_to_utilization():
    old_read = probe.read_tx_bytes_kernel
    old_time = probe.time.time
    values = iter([0, 250000])
    times = iter([10.0, 11.0])
    try:
        probe.read_tx_bytes_kernel = lambda _ifname: next(values)
        probe.time.time = lambda: next(times)
        meter = probe.KernelUtilMeter("sC-eth3", 4.0)
        util0, _ts0 = meter.sample()
        util1, _ts1 = meter.sample()
        assert util0 is None
        assert util1 == 0.5
    finally:
        probe.read_tx_bytes_kernel = old_read
        probe.time.time = old_time


def test_read_ditto_link_returns_util_and_aoi():
    old_get_one = probe._get_one
    old_time = probe.time.time
    body = {
        "features": {
            "meta": {"properties": {"tSource": 100.0}},
            "traffic": {"properties": {"txRate": 250000.0}},
            "capacity": {"properties": {"bwMbps": 4.0}},
        },
    }
    try:
        probe._get_one = lambda _session, thing_id: (body, True)
        probe.time.time = lambda: 100.5
        util, t_source, t_read, aoi, ok = probe.read_ditto_link(
            object(),
            "sC",
            "sE",
        )
        assert ok is True
        assert util == 0.5
        assert t_source == 100.0
        assert t_read == 100.5
        assert abs(aoi - 0.5) < 1e-9
    finally:
        probe._get_one = old_get_one
        probe.time.time = old_time


def _run_as_script():
    tests = [
        test_read_tx_bytes_kernel_uses_tx_column,
        test_kernel_meter_converts_counter_delta_to_utilization,
        test_read_ditto_link_returns_util_and_aoi,
    ]
    for test in tests:
        test()
        print("  PASS  %s" % test.__name__)
    print("\n%d/%d passed" % (len(tests), len(tests)))


if __name__ == "__main__":
    _run_as_script()

#!/usr/bin/env python3
"""Phase L / L.3 -- unit tests for pure qdisc specification."""

import pytest

from mininet import topology_split_qdisc as SQ
from mininet.tc_spec import (
    CONFIGS,
    DEFAULT_BURST_BYTES,
    FRAME_BYTES_1470,
    capacity_pps,
    check_measure_text,
    fit_staircase,
    measure_cmds,
    parse_qdisc_tree,
    queue_bytes,
    queue_ceiling_ms,
    staircase_delays_ms,
)


GOOD_QDISC = """qdisc htb 1: root refcnt 9 r2q 10 default 0x10 direct_packets_stat 0 direct_qlen 1000
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
qdisc bfifo 10: parent 1:10 limit 19656b
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0"""

GOOD_CLASS = """class htb 1:10 root leaf 10: prio 0 rate 6Mbit ceil 6Mbit burst 1600b cburst 1600b
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
 lended: 0 borrowed: 0 giants: 0
 tokens: 33334 ctokens: 33334"""

TCLINK_QDISC = """qdisc htb 5: root refcnt 2 r2q 10 default 0x1 direct_packets_stat 0
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
qdisc netem 10: parent 5:1 limit 13
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0"""

NO_LEAF_QDISC = """qdisc htb 1: root refcnt 9 r2q 10 default 0x10 direct_packets_stat 0
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0"""

PFIFO_QDISC = GOOD_QDISC.replace(
    "bfifo 10: parent 1:10 limit 19656b",
    "pfifo 10: parent 1:10 limit 13p",
)


def test_queue_bytes_va_ceiling_khoa_gia_tri():
    assert queue_bytes(13) == 19656
    assert queue_ceiling_ms(13, 6.0) == pytest.approx(26.208, abs=1e-3)
    assert queue_ceiling_ms(18, 8.0) == pytest.approx(27.216, abs=1e-3)
    assert queue_ceiling_ms(10, 4.0) == pytest.approx(30.240, abs=1e-3)


def test_ceiling_ti_le_thuan_q_ti_le_nghich_bw():
    assert queue_ceiling_ms(26, 6.0) == pytest.approx(2 * queue_ceiling_ms(13, 6.0))
    assert queue_ceiling_ms(13, 3.0) == pytest.approx(2 * queue_ceiling_ms(13, 6.0))


def test_capacity_pps_dinh_nghia_rho_cua_lesson_L4():
    assert capacity_pps(6.0) == pytest.approx(496.0317, abs=1e-3)


def test_lenh_bfifo_dung_don_vi_byte_khong_phai_goi():
    cmds = measure_cmds("s1-eth2", 6.0, 13)
    leaf = [cmd for cmd in cmds if "bfifo" in cmd][0]
    assert leaf.endswith("bfifo limit 19656")
    assert "pfifo" not in " ".join(cmds)


def test_khong_lenh_nao_tao_netem_o_chieu_do():
    assert "netem" not in " ".join(measure_cmds("s1-eth2", 6.0, 13))


def test_live_shell_helper_khong_dung_login_shell(monkeypatch):
    calls = []

    def fake_run(args, **_kwargs):
        calls.append(args)
        return SQ.subprocess.CompletedProcess(args, 0, stdout="")

    monkeypatch.setattr(SQ.subprocess, "run", fake_run)

    assert SQ.sh("true") == ""
    assert calls == [["sh", "-c", "true"]]


def test_tc_batch_goi_nhieu_lenh_trong_mot_process(monkeypatch):
    seen = {}

    def fake_run(args, **kwargs):
        seen["args"] = args
        seen["input"] = kwargs.get("input")
        return SQ.subprocess.CompletedProcess(args, 0, stdout="")

    monkeypatch.setattr(SQ.subprocess, "run", fake_run)

    SQ.sh_tc_batch(["tc qdisc add dev s0-eth1 root handle 1: htb default 10", "tc class add dev s0-eth1 parent 1: classid 1:10 htb rate 6mbit"])

    assert seen["args"] == ["tc", "-batch", "-"]
    assert seen["input"].splitlines() == [
        "qdisc add dev s0-eth1 root handle 1: htb default 10",
        "class add dev s0-eth1 parent 1: classid 1:10 htb rate 6mbit",
    ]


def test_qdisc_setup_retry_ghi_provenance(monkeypatch):
    calls = []

    def fake_setup(*_args, **_kwargs):
        calls.append("setup")

    def fake_assert(*_args, **_kwargs):
        if len(calls) == 1:
            raise AssertionError("V-L1 FAIL tren s0-eth1:\nV-L1g: direct_packets_stat=1")
        return {"ifname": "s0-eth1"}

    monkeypatch.setattr(SQ, "setup_measure_qdisc", fake_setup)
    monkeypatch.setattr(SQ, "assert_measure_qdisc", fake_assert)
    monkeypatch.setattr(SQ.time, "sleep", lambda _seconds: None)

    log = []
    proof = SQ.setup_and_verify_measure_qdisc("s0-eth1", 6.0, 13, log_sink=log)

    assert len(calls) == 2
    assert proof["install_attempts"] == 2
    assert proof["install_history"] == ["V-L1g: direct_packets_stat=1"]
    assert log == [
        {
            "event": "qdisc_reinstall",
            "ifname": "s0-eth1",
            "attempt": 2,
            "reason": "V-L1g: direct_packets_stat=1",
        }
    ]


def test_burst_it_nhat_bang_mot_khung_mtu():
    assert DEFAULT_BURST_BYTES >= FRAME_BYTES_1470


def test_parse_output_that_cua_may():
    layers = parse_qdisc_tree(GOOD_QDISC)
    assert [layer["kind"] for layer in layers] == ["htb", "bfifo"]
    assert layers[0]["is_root"] is True
    assert layers[0]["direct_packets_stat"] == 0
    assert layers[1]["limit_bytes"] == 19656
    assert layers[1]["limit_pkts"] is None


def test_parse_netem_limit_khong_hau_to_la_goi():
    layer = parse_qdisc_tree("qdisc netem 1: root refcnt 9 limit 1000 delay 3ms")[0]
    assert layer["kind"] == "netem"
    assert layer["limit_pkts"] == 1000
    assert layer["limit_bytes"] is None
    assert layer["delay_ms"] == 3.0


def test_cau_hinh_dung_thi_khong_co_loi():
    assert check_measure_text(GOOD_QDISC, GOOD_CLASS, 13) == []


@pytest.mark.parametrize(
    ("qdisc_text", "error_fragment"),
    [
        (TCLINK_QDISC, "V-L1b"),
        (NO_LEAF_QDISC, "V-L1c"),
        (PFIFO_QDISC, "V-L1c"),
    ],
)
def test_cac_cau_hinh_sai_deu_bi_bat(qdisc_text, error_fragment):
    errs = check_measure_text(qdisc_text, GOOD_CLASS, 13)
    assert any(error_fragment in err for err in errs), errs


def test_sai_kich_thuoc_buffer_bi_bat():
    errs = check_measure_text(GOOD_QDISC, GOOD_CLASS, queue_pkts=5)
    assert any("bfifo limit" in err for err in errs)


def test_burst_15k_cua_mininet_bi_bat():
    bad = GOOD_CLASS.replace("burst 1600b cburst 1600b", "burst 15000b cburst 15000b")
    assert any("V-L1d" in err for err in check_measure_text(GOOD_QDISC, bad, 13))


def test_bac_thang_khop_bang_da_tien_dang_ky():
    assert staircase_delays_ms(8, 6.0) == pytest.approx(
        [0, 0, 1.8987, 3.9147, 5.9307, 7.9467, 9.9627, 11.9787],
        abs=1e-3,
    )
    assert staircase_delays_ms(8, 4.0)[2] == pytest.approx(2.848, abs=1e-3)
    assert staircase_delays_ms(8, 8.0)[2] == pytest.approx(1.424, abs=1e-3)


def test_hai_goi_dau_luon_bang_khong_vi_burst_lon_hon_mtu():
    for bw, _queue in CONFIGS:
        delays = staircase_delays_ms(8, bw)
        assert delays[0] == 0.0 and delays[1] == 0.0


def test_fit_bac_thang_khoi_phuc_dung_c_va_burst():
    for bw, _queue in CONFIGS:
        fit = fit_staircase(staircase_delays_ms(8, bw))
        assert fit["C_mbps"] == pytest.approx(bw, rel=1e-9)
        assert fit["burst_bytes"] == pytest.approx(DEFAULT_BURST_BYTES, abs=1e-6)
        assert fit["r2"] == pytest.approx(1.0, abs=1e-12)

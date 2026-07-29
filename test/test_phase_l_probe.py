#!/usr/bin/env python3
"""Phase L / L.3 -- packet and raw-record format tests."""

import struct

import pytest

from measurements.owd_probe import (
    HDR,
    KIND_BG,
    KIND_PROBE,
    MAGIC,
    PKT_VERSION,
    REC_RX,
    REC_TX,
    pack_packet,
    unpack_packet,
)


def test_kich_thuoc_dinh_dang_bi_khoa():
    assert HDR.size == 32
    assert REC_RX.size == 24
    assert REC_TX.size == 16


@pytest.mark.parametrize("kind", [KIND_BG, KIND_PROBE])
@pytest.mark.parametrize("size", [64, 1470])
def test_round_trip(kind, size):
    buf = pack_packet(kind, 123456789, 1234.567890123, 42, size)
    assert len(buf) == size
    assert unpack_packet(buf) == (kind, 123456789, 1234.567890123, 42)


def test_timestamp_giu_du_do_chinh_xac_micro_giay():
    timestamp = 987654.321098765
    assert unpack_packet(pack_packet(KIND_PROBE, 1, timestamp, 1, 64))[2] == timestamp


def test_goi_la_bi_tu_choi():
    assert unpack_packet(b"") is None
    assert unpack_packet(b"\x00" * 64) is None
    assert unpack_packet(b"XXXX" + b"\x00" * 60) is None
    bad_ver = struct.pack("<4sBBHQdQ", MAGIC, PKT_VERSION + 1, 1, 0, 1, 1.0, 1)
    assert unpack_packet(bad_ver + b"\x00" * 32) is None


def test_goi_nho_hon_header_bi_tu_choi_khong_crash():
    assert unpack_packet(MAGIC + b"\x01") is None


def test_size_nho_hon_header_thi_nem_loi_ro_rang():
    with pytest.raises(ValueError):
        pack_packet(KIND_PROBE, 0, 0.0, 0, 16)

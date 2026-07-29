#!/usr/bin/env python3
"""Phase L / L.3 -- analyzer tests on synthetic data with known answers."""

import pytest

from measurements.owd_analyze import REC_RX, REC_TX, analyze, pctl


def _write(tmp_path, sent, received):
    tx = tmp_path / "tx.bin"
    rx = tmp_path / "rx.bin"
    tx.write_bytes(b"".join(REC_TX.pack(seq, t_send) for seq, t_send in sent))
    rx.write_bytes(
        b"".join(REC_RX.pack(seq, t_send, t_recv) for seq, t_send, t_recv in received)
    )
    return str(rx), str(tx)


def _scenario(tmp_path):
    sent = [(i, 100.0 + i) for i in range(21)]
    received = []
    for i in range(21):
        if i == 15:
            continue
        owd = 3.000 if i == 20 else 0.001
        received.append((i, 100.0 + i, 100.0 + i + owd))
    return _write(tmp_path, sent, received)


def test_cua_so_cat_theo_t_send_khong_theo_t_recv(tmp_path):
    rx, tx = _scenario(tmp_path)
    res = analyze(rx, tx, warmup_s=10.0)
    assert res["window"]["cut_on"] == "t_send"
    assert res["owd_ms"]["mean"] == pytest.approx(300.9, abs=1e-6)
    assert res["owd_ms"]["mean"] > 100.0


def test_dem_mat_goi_dung(tmp_path):
    rx, tx = _scenario(tmp_path)
    res = analyze(rx, tx, warmup_s=10.0)
    counts = res["counts"]
    assert counts["n_sent"] == 11
    assert counts["n_recv_unique"] == 10
    assert counts["n_duplicate"] == 0
    assert counts["n_reorder"] == 0
    assert res["loss_rate"] == pytest.approx(1 / 11)


def test_percentile_nearest_rank_dung_dinh_nghia(tmp_path):
    rx, tx = _scenario(tmp_path)
    owd = analyze(rx, tx, warmup_s=10.0)["owd_ms"]
    assert owd["p50"] == pytest.approx(1.0)
    assert owd["p95"] == pytest.approx(3000.0)
    assert owd["p99"] == pytest.approx(3000.0)
    assert owd["min"] <= owd["p50"] <= owd["p90"] <= owd["p95"] <= owd["p99"] <= owd["max"]
    assert owd["percentile_method"] == "nearest-rank"


def test_pctl_bien():
    assert pctl([1.0, 2.0, 3.0, 4.0], 0.50) == 2.0
    assert pctl([1.0, 2.0, 3.0, 4.0], 1.00) == 4.0
    assert pctl([5.0], 0.99) == 5.0


def test_c_a_bang_khong_khi_gui_deu(tmp_path):
    rx, tx = _scenario(tmp_path)
    arrival = analyze(rx, tx, warmup_s=10.0)["arrival"]
    assert arrival["c_a_measured"] == pytest.approx(0.0, abs=1e-12)
    assert arrival["rate_pps_actual"] == pytest.approx(1.1, rel=0.05)


def test_owd_am_bi_lo_ra_chu_khong_bi_loc(tmp_path):
    sent = [(i, 100.0 + i) for i in range(21)]
    received = [
        (i, 100.0 + i, 100.0 + i + (-0.001 if i == 12 else 0.001))
        for i in range(21)
    ]
    rx, tx = _write(tmp_path, sent, received)
    res = analyze(rx, tx, warmup_s=10.0)
    assert res["counts"]["n_owd_negative"] == 1
    assert res["owd_ms"]["min"] < 0


def test_trung_lap_va_dao_thu_tu_duoc_dem_rieng(tmp_path):
    sent = [(i, 100.0 + i) for i in range(21)]
    received = [(i, 100.0 + i, 100.0 + i + 0.001) for i in range(21)]
    received.append((12, 112.0, 112.002))
    moved = next(row for row in received if row[0] == 19)
    received.remove(moved)
    received.insert(0, moved)
    rx, tx = _write(tmp_path, sent, received)
    counts = analyze(rx, tx, warmup_s=10.0)["counts"]
    assert counts["n_duplicate"] == 1
    assert counts["n_reorder"] >= 1


def test_file_tho_hong_bi_bat_ngay(tmp_path):
    rx, tx = _scenario(tmp_path)
    with open(rx, "ab") as f:
        f.write(b"\x00" * 7)
    with pytest.raises(ValueError, match="HONG"):
        analyze(rx, tx, warmup_s=10.0)

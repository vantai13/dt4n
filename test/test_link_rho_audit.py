"""Lesson 23.24b -- test cho nhac cu kiem toan chieu do `rho`.

Bao gom `PC-24b-1` (doi chung DUONG): nhac cu PHAI bat duoc mot CSV hong.
Mot kiem toan luon bao "sach" thi khong phai kiem toan -- cung hinh dang
`L101` (nguong khong the fail).
"""
import csv
import inspect
import json

import numpy as np
import pytest

from measurements import link_rho_audit as A
from mininet.run_sync_v7 import LINK_ENDPOINTS
from twin import link_direction as LD
from twin import topology_v7 as T7


# ---------------------------------------------------- ban do co huong
def test_direction_map_matches_topology():
    """`link_direction` va `run_sync_v7` phai la CUNG mot ban do.

    Hai noi giu cung mot su that thi mot trong hai se troi. `twin/` KHONG
    duoc import `mininet/`, nen rang buoc duoc ghim bang test chu khong bang
    import.
    """
    assert LD.UPSTREAM_OF == LINK_ENDPOINTS


def test_direction_map_covers_every_link():
    assert set(LD.UPSTREAM_OF) == set(T7.LINK_NAMES)


def test_l30_is_reproducible_as_an_expression():
    """★ `L30` phai la mot BIEU THUC CHAY DUOC, khong phai mot doan van.

    Bang chu cai TINH CO dung o 6 link va TINH CO sai o `uA`/`uB`. Neu ai do
    doi ten node, test nay do va chi thang vao co che.
    """
    wrong = sorted(l for l in T7.LINK_NAMES
                   if not LD.alphabetical_side_a_is_correct(l))
    assert wrong == ["uA", "uB"]


def test_upstream_lookup_accepts_both_name_forms():
    assert LD.upstream_node("uA") == "sSRC"
    assert LD.upstream_node("link-sA-sSRC") == "sSRC"
    assert LD.upstream_node("link-khong-ton-tai") is None


def test_canonical_key_matches_collector():
    """Ban sao trong `twin/` phai khop ban goc trong `bridge/`."""
    from bridge.collector import canonical_link_key
    for a, b in LD.UPSTREAM_OF.values():
        assert LD.canonical_key(a, b) == canonical_link_key(a, b)


# ---------------------------------------------------- tien ich lam gia
def _write_campaign(tmp_path, *, break_links=(), n_samples=200, seed=0):
    """Sinh mot chien dich gia: 1 meta + 1 CSV, co the co chu dich lam hong."""
    rng = np.random.default_rng(seed)
    targets = {l: 0.90 for l in T7.LINK_NAMES}
    duration, payload = 120.0, 1400.0

    flow_engine = {}
    for link in T7.LINK_NAMES:
        cap = float(T7.LINKS[link][0])
        want_mbps = targets[link] * cap
        pk = int(round(want_mbps * 1e6 * duration
                       / (8.0 * (payload + A.OVERHEAD_BYTES))))
        flow_engine[link] = {"cap_mbps": cap, "packets_sent": pk,
                             "rho_target": targets[link]}

    meta = {"duration_s": duration, "payload_bytes": payload,
            "rho_bar": 0.925, "measurement_mode": "clean",
            "flow_engine": flow_engine}
    (tmp_path / "meta_clean_rho0.925_rep1.json").write_text(
        json.dumps(meta), encoding="utf-8")

    fields = ("sample_index", "timestamp_s", "link", "rho",
              "throughput_mbps", "tx_bytes_delta", "dt_s")
    with open(tmp_path / "rho_measured_clean_rho0.925_rep1.csv",
              "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for i in range(n_samples):
            for link in T7.LINK_NAMES:
                if link in break_links:
                    # mo phong `L30`: doc chieu nguoc -> gan nhu luon bang 0
                    rho = 0.0 if rng.random() < 0.98 else 0.01
                else:
                    rho = max(0.0, targets[link] + rng.normal(0, 0.01))
                w.writerow({"sample_index": i, "timestamp_s": i * 0.2,
                            "link": link, "rho": "%.8f" % rho,
                            "throughput_mbps": "%.8f" % rho,
                            "tx_bytes_delta": 0, "dt_s": "0.2"})
    return tmp_path


def _run(d):
    metas = [str(d / "meta_clean_rho0.925_rep1.json")]
    csvs = [str(d / "rho_measured_clean_rho0.925_rep1.csv")]
    gen = A.generator_rho(metas)
    meas = A.measured_rho(csvs)
    return gen, meas, A.adjudicate(gen, meas)


# ---------------------------------------------------- R2 / R3 / R4
def test_generator_rho_recovers_the_target(tmp_path):
    """R2 phai tai dung lai `rho_target` tu `packets_sent` (vong kin)."""
    d = _write_campaign(tmp_path)
    gen = A.generator_rho([str(d / "meta_clean_rho0.925_rep1.json")])
    for link in T7.LINK_NAMES:
        assert gen["per_link"][link]["rho_gen_mean"] == pytest.approx(
            0.90, abs=0.01)


def test_generator_rho_is_labelled_as_pre_measured(tmp_path):
    """`A076` muc 2: R2 KHONG duoc trinh bay nhu mot du doan."""
    d = _write_campaign(tmp_path)
    gen = A.generator_rho([str(d / "meta_clean_rho0.925_rep1.json")])
    assert "DA DO TRUOC KHI KY" in gen["label"]


def test_clean_csv_is_adjudicated_clean(tmp_path):
    d = _write_campaign(tmp_path, break_links=())
    _gen, _meas, adj = _run(d)
    assert adj["overall"] == "CSV_CLEAN"
    assert adj["links_broken"] == []
    assert adj["n_clean"] == len(T7.LINK_NAMES)


def test_PC_24b_1_audit_catches_a_broken_csv(tmp_path):
    """★ `PC-24b-1` -- DOI CHUNG DUONG, gate `G23-306`.

    Cho nhac cu an mot CSV da biet TRUOC la hong o `uA`/`uB`. No PHAI ket
    luan `CSV_BROKEN` va chi DUNG hai link do.
    """
    d = _write_campaign(tmp_path, break_links=("uA", "uB"))
    _gen, meas, adj = _run(d)

    assert adj["overall"] == "CSV_BROKEN"
    assert adj["links_broken"] == ["uA", "uB"]
    assert meas["per_link"]["uA"]["zero_share"] > 0.90
    assert meas["per_link"]["ac"]["zero_share"] < 0.05
    # dong thuan SUP o link hong, GIU o link lanh
    assert adj["agreement_csv_over_generator"]["uA"] < 0.05
    assert adj["agreement_csv_over_generator"]["ac"] == pytest.approx(
        1.0, abs=0.05)


def test_audit_discriminates_between_clean_and_broken(tmp_path):
    """Cai chan phai PHAN BIET duoc, khong chi 'bao hong khi hong'."""
    (tmp_path / "c").mkdir()
    (tmp_path / "b").mkdir()
    clean = _write_campaign(tmp_path / "c", break_links=())
    broken = _write_campaign(tmp_path / "b", break_links=("uA",))
    assert _run(clean)[2]["overall"] == "CSV_CLEAN"
    assert _run(broken)[2]["overall"] == "CSV_BROKEN"


def test_NC_24b_1_audit_is_deterministic(tmp_path):
    """`NC-24b-1` -- chay hai lan tren cung dau vao -> ket qua giong het."""
    d = _write_campaign(tmp_path, break_links=("uA",))
    a1 = _run(d)[2]
    a2 = _run(d)[2]
    assert json.dumps(a1, sort_keys=True) == json.dumps(a2, sort_keys=True)


def test_locked_constants_are_not_command_line_flags():
    """Chong p-hacking (`A076` N5): nguong phai la HANG SO MODULE."""
    src = inspect.getsource(A.main)
    for forbidden in ("--zero-eps", "--broken-share", "--clean-share",
                      "--agree-lo", "--agree-hi", "--overhead"):
        assert forbidden not in src

"""Tests for Phase 20R truth-table assembly helpers."""

import pytest

from measurements import build_truth_table as B


def row(**kw):
    base = {
        "idx": 0,
        "block": "A",
        "mode": "h2",
        "bw": 6.0,
        "q": 13,
        "rho": 0.9,
        "seed": 1,
        "probe_pps": 20.0,
        "q_mean_ms": 10.0,
        "loss": 0.0,
        "se_batch_ms": 0.3,
        "se_naive_ms": 0.03,
        "n_recv_unique": 1000,
        "gate_fail": [],
        "schedule_digest": "abc",
    }
    base.update(kw)
    return base


def test_merge_states_excludes_controls_sentinels_failures_and_aggregates_seed_sd():
    phase_l = {
        "rows": [
            row(seed=1, q_mean_ms=10.0),
            row(seed=2, q_mean_ms=12.0),
            row(seed=999, block="E", q_mean_ms=99.0),
            row(seed=3, probe_pps=0.0, q_mean_ms=99.0),
            row(seed=4, mode="onoff", q_mean_ms=99.0),
            row(seed=5, gate_fail=["rate"], q_mean_ms=99.0),
        ]
    }
    phase20r = {"rows": [row(seed=21, rho=0.92, q_mean_ms=20.0)]}

    table = B.merge_states(phase_l, phase20r).sort_values(["rho"]).reset_index(drop=True)

    assert table.attrs["truth_field"] == "q_mean_ms"
    assert len(table) == 2
    first = table.iloc[0]
    assert first["rho"] == pytest.approx(0.9)
    assert first["delay_mean_ms"] == pytest.approx(11.0)
    assert first["delay_sd_ms"] == pytest.approx(2**0.5)
    assert first["se_mean_ms"] == pytest.approx(1.0)
    assert int(first["n_seed"]) == 2
    assert int(first["n_pkt"]) == 2000


def test_continuity_report_uses_two_se_combined_tolerance():
    phase_l = {"rows": [row(seed=11, q_mean_ms=10.0), row(seed=12, q_mean_ms=10.2)]}
    continuity = {"rows": [row(block="G", seed=31, q_mean_ms=10.25, se_batch_ms=0.2)]}

    report = B.continuity_report(phase_l, continuity)

    assert report["n"] == 1
    assert report["n_pass"] == 1
    assert report["all_pass"] is True
    check = report["checks"][0]
    assert check["phase_l_mean_ms"] == pytest.approx(10.1)
    assert check["diff_ms"] == pytest.approx(0.15)


def test_truth_table_parquet_records_truth_field_metadata(tmp_path):
    phase_l_path = tmp_path / "phase_l.json"
    phase20r_path = tmp_path / "phase20r.json"
    out = tmp_path / "truth.parquet"
    phase_l_path.write_text('{"rows": []}\n')
    phase20r_path.write_text(
        '{"rows": [%s]}\n'
        % B.json.dumps(row(q_mean_ms=7.0, probe_mean_ms=3.0), sort_keys=True),
        encoding="utf-8",
    )

    table = B.write_truth_table(str(phase_l_path), str(phase20r_path), str(out), None)

    assert table["delay_mean_ms"].iloc[0] == pytest.approx(7.0)
    try:
        import pyarrow.parquet as pq
    except Exception:
        meta = B.json.loads((tmp_path / "truth.parquet.meta.json").read_text())
        assert meta["truth_field"] == "q_mean_ms"
    else:
        md = pq.read_metadata(out).metadata
        assert md[b"truth_field"] == b"q_mean_ms"
        assert b"probe_mean_ms" in md[b"truth_field_note"]


def test_write_truth_table_keeps_only_phase20r_preregistered_grid(tmp_path):
    phase_l_path = tmp_path / "phase_l.json"
    phase20r_path = tmp_path / "phase20r.json"
    out = tmp_path / "truth.parquet"
    phase_l_path.write_text(
        '{"rows": [%s]}\n' % B.json.dumps(row(mode="cbr", bw=4.0, q=10, rho=1.02), sort_keys=True),
        encoding="utf-8",
    )
    phase20r_path.write_text(
        '{"rows": [%s]}\n' % B.json.dumps(row(mode="h2", bw=6.0, q=13, rho=0.52), sort_keys=True),
        encoding="utf-8",
    )

    table = B.write_truth_table(str(phase_l_path), str(phase20r_path), str(out), None)

    assert len(table) == 1
    assert table["mode"].iloc[0] == "h2"
    assert table["rho"].iloc[0] == pytest.approx(0.52)

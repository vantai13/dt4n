import json
from pathlib import Path

import pytest

from tools import a070_window as W


def test_grid_and_allowlist_are_exact() -> None:
    assert W.RHOS == (0.744, 0.750, 0.756, 0.760, 0.764, 0.770)
    assert W.MODES == ("poisson", "h2")
    assert len(W.expected_cells()) == 12
    assert W.OUTCOME_ALLOWLIST == {
        "err_neo", "n_calib_blocks", "build_seconds"
    }


def test_build_phase_finishes_all_cells_without_reading_outcomes(
    monkeypatch, tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "cells": [
            {"mode": mode, "rho_bar": rho, "w_loss": 5000.0}
            for mode in W.MODES for rho in W.RHOS
        ]
    }))
    seen = []

    def fake_builder(mode, rho, manifest, out_dir):
        seen.append((mode, rho))
        return {
            "cell": W._cell_name(mode, rho),
            "parquet": f"{mode}-{rho}.parquet",
            "report": f"{mode}-{rho}.json",
            "parquet_sha256": "a" * 64,
            "report_sha256": "b" * 64,
            "build_seconds": 1.0,
        }

    monkeypatch.setattr(W, "_run_builder", fake_builder)
    monkeypatch.setattr(W.pd, "read_parquet", lambda *a, **k: pytest.fail(
        "build phase khong duoc doc outcome"))
    receipt = W.build_all_sealed(
        str(manifest), str(tmp_path), str(tmp_path / "receipt.json")
    )
    assert len(seen) == receipt["n_cells"] == 12


def _rows(common=(0.750, 0.756, 0.760, 0.764)):
    return [
        {
            "cell": W._cell_name(mode, rho),
            "err_neo": 0.06 if rho in common else 0.01,
            "n_calib_blocks": 500,
            "build_seconds": 9.0,
        }
        for mode in W.MODES for rho in W.RHOS
    ]


def test_scores_signed_predictions_and_independent_stops() -> None:
    out = W.score(_rows())
    assert out["M_215"]["hit"] is True
    assert out["M_216"]["hit"] is True
    assert out["M_217"]["hit"] is True
    bad = _rows(common=(0.750,))
    assert W.score(bad)["M_215"]["stop_W"] is True
    bad[0]["n_calib_blocks"] = 499
    invalid = W.score(bad)
    assert invalid["operational_stop"]["branch_valid"] is False
    assert invalid["M_215"]["stop_W"] is False


def test_verified_receipt_rejects_digest_change_before_reveal(
    tmp_path: Path, monkeypatch,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}")
    cells = []
    for cell in W.expected_cells():
        p = tmp_path / (cell.replace("@", "-") + ".parquet")
        r = tmp_path / (cell.replace("@", "-") + ".json")
        p.write_text("sealed")
        r.write_text("report")
        cells.append({
            "cell": cell, "parquet": str(p), "report": str(r),
            "parquet_sha256": W._sha256(p), "report_sha256": W._sha256(r),
            "build_seconds": 1.0,
        })
    receipt = {
        "manifest": str(manifest), "manifest_sha256": W._sha256(manifest),
        "n_cells": 12, "cells": cells,
        "sealed_batch_sha256": W._batch_digest(cells),
    }
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt))
    Path(cells[0]["parquet"]).write_text("tampered")
    monkeypatch.setattr(W.pd, "read_parquet", lambda *a, **k: pytest.fail(
        "digest phai chan truoc khi doc parquet"))
    with pytest.raises(RuntimeError, match="digest lech"):
        W.reveal_allowlist(str(path), str(tmp_path / "out.json"))

import json
from pathlib import Path

import numpy as np

from cert.build_calib_set_v2 import (
    Z_EDGES_PRIMARY,
    Z_EDGES_SECONDARY,
    Z_STEP_OFFSETS_PRIMARY,
    Z_STEP_OFFSETS_SECONDARY,
    assign_bin,
    z_edges_for,
)
from cert.build_calib_set_v3 import DT, N, _valid_rows
from cert.dsync_sensitivity import D_SYNC_VALUES, labelled_payload


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "results/phase-23/dsync_sensitivity.json"


def _shares(d_sync: float) -> np.ndarray:
    cur, old, _ = _valid_rows(N, DT, d_sync)
    z_s = (cur - old) * DT
    edges = z_edges_for(d_sync, N, DT, offsets=Z_STEP_OFFSETS_PRIMARY)
    bins = assign_bin(z_s, edges)
    return np.asarray([(bins == i).mean() for i in range(4)])


def test_z_edges_reproduce_committed_constants():
    assert z_edges_for(0.051, N, DT, offsets=Z_STEP_OFFSETS_PRIMARY) == Z_EDGES_PRIMARY
    assert z_edges_for(0.051, N, DT, offsets=Z_STEP_OFFSETS_SECONDARY) == Z_EDGES_SECONDARY


def test_bin_shares_invariant_to_dsync():
    base = _shares(0.051)
    for d_sync in D_SYNC_VALUES[1:]:
        assert np.max(np.abs(_shares(d_sync) - base)) <= 1e-4


def test_dsync_changes_absolute_age_but_not_number_of_primary_bins():
    extrema = []
    for d_sync in D_SYNC_VALUES:
        cur, old, _ = _valid_rows(N, DT, d_sync)
        z_s = (cur - old) * DT
        bins = assign_bin(
            z_s,
            z_edges_for(d_sync, N, DT, offsets=Z_STEP_OFFSETS_PRIMARY),
        )
        assert sorted(np.unique(bins).tolist()) == [0, 1, 2, 3]
        extrema.append((float(z_s.min()), float(z_s.max())))
    assert len(set(extrema)) == len(D_SYNC_VALUES)


def test_sensitivity_label_is_enforced_by_constructor():
    assert labelled_payload()["status"] == "SENSITIVITY_ONLY"
    assert labelled_payload()["closes_P23A"] is False


def test_completed_artifact_is_labelled_if_present():
    if not ARTIFACT.exists():
        return
    report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert report["status"] == "SENSITIVITY_ONLY"
    assert report["closes_P23A"] is False
    assert all(row["status"] == "SENSITIVITY_ONLY" for row in report["rows"])
    assert all(row["closes_P23A"] is False for row in report["rows"])

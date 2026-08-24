"""M-180 figure data must preserve the observed family split."""
from __future__ import annotations

import json

from cert import live_region_sweep as L
from tools import fig3_live_region_by_family as F


def test_family_rows_cover_all_twelve_cells_and_observed_directions() -> None:
    with open(L.OUTPUT, "r", encoding="utf-8") as handle:
        report = json.load(handle)
    poisson = F.family_rows(report, "poisson")
    h2 = F.family_rows(report, "h2")
    assert len(poisson) == len(h2) == 6
    assert [row["direction"] for row in poisson if row["regime"] == "LIVE"] == [
        "harmful",
        "harmful",
        "harmful",
    ]
    assert [row["direction"] for row in h2 if row["regime"] == "LIVE"] == [
        "helpful",
        "helpful",
        "helpful",
    ]
    assert next(row for row in poisson if row["rho_bar"] == 0.700)["direction"] == "helpful"

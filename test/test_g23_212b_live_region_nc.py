"""G23-212b must exercise the exact helper used by live_region_sweep."""
from pathlib import Path

from tools import g23_212b_live_region_nc as N


def test_nc_is_pinned_to_10_cell_semantics_and_old_side_A() -> None:
    assert N.BASELINE.endswith("g23_212a_before.json")
    assert N.L.SLA_EXOGENOUS_10.endswith("sla_manifest_exogenous_S-B.json")
    assert len(N.A.ALIVE_VERIFIED) == 8


def test_nc_source_calls_shared_live_region_helper() -> None:
    source = Path("tools/g23_212b_live_region_nc.py").read_text(encoding="utf-8")
    assert "L.analyze_base_cells(" in source
    assert "sla_path=L.SLA_EXOGENOUS_10" in source
    assert "calib_template=A.CALIB_TEMPLATE" in source

"""A-T2-2: cua so cham diem phai DOC LAP VOI NHANH.

Bo test nay bao ve mot QUAN HE, khong mot con so. Neu no do, cua so cham
diem lai phu thuoc nhanh -- va moi phep so sanh giua hai nhanh (NC-T2-2)
lai tro nen vo nghia, mot cach IM LANG: khong co exception nao duoc nem.
"""
from __future__ import annotations

import pytest

from measurements.decision_error_v2 import DT, scoring_window_start, z_values_for

TAUS = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0)   # luoi da ky o T2-4


@pytest.mark.parametrize("tau", TAUS)
def test_scoring_window_is_branch_independent(tau):
    """Mot cua so, du cho MOI muc z cua CA HAI nhanh."""
    f = z_values_for(tau, scaled=False)
    s = z_values_for(tau, scaled=True)
    start = scoring_window_start(tau, DT)
    assert start >= max(int(round(z / DT)) for z in f), "khong du cho nhanh fixed"
    assert start >= max(int(round(z / DT)) for z in s), "khong du cho nhanh scaled"
    assert start == max(int(round(z / DT)) for z in set(f) | set(s)), \
        "phai la HOP hai luoi, khong duoc rong hon (phi hang) hay hep hon (lag am)"


def test_window_would_have_differed_under_the_old_rule():
    """Ghim CHINH XAC cai loi cu, de khong ai vo tinh khoi phuc no.

    Neu ai do quay lai quy tac 'max cua luoi nhanh dang chay', test nay do.
    """
    old_f = max(int(round(z / DT)) for z in z_values_for(1.0, scaled=False))
    old_s = max(int(round(z / DT)) for z in z_values_for(1.0, scaled=True))
    assert (old_f, old_s) == (800, 200), "hai luoi z da doi -- xem lai A-T2-2"
    assert scoring_window_start(1.0, DT) == 800


def test_old_rule_offset_reverses_sign_across_the_tau_axis():
    """Ly do goc: do lech DOI DAU theo tau.

    Mot doi chung co do lech doi dau theo chinh truc dang quet thi khong
    doc duoc -- khong the noi mot xu huong la vat ly hay la tao tac.
    """
    d1 = (max(int(round(z / DT)) for z in z_values_for(1.0, scaled=True))
          - max(int(round(z / DT)) for z in z_values_for(1.0, scaled=False)))
    d28 = (max(int(round(z / DT)) for z in z_values_for(28.0, scaled=True))
           - max(int(round(z / DT)) for z in z_values_for(28.0, scaled=False)))
    assert d1 < 0 < d28, "do lech phai doi dau -- do la ly do ton tai cua A-T2-2"


@pytest.mark.parametrize("dt", (0.005, 0.01))
def test_run_cell_scores_common_rows(dt):
    from measurements import decision_error_v2 as D
    cell = D.measurement_cells()[0]
    tt, cv = D.TruthTable(), D.C.CostV2(strict_reliable=False)
    results = [D.run_cell(tt, cv, cell, seed=101, tau=1.0, n=2000, dt=dt,
                         z_values=D.z_values_for(1.0, scaled=scaled))
               for scaled in (False, True)]
    for z in set(results[0]["per_z"]) & set(results[1]["per_z"]):
        assert results[0]["per_z"][z] == results[1]["per_z"][z]


def test_summary_entry_point_scores_common_rows(monkeypatch, tmp_path):
    from measurements import decision_error_v2 as D
    cell = D.measurement_cells()[0]
    monkeypatch.setattr(D, "feasible_cells", lambda *a, **kw: [cell])
    frames = [D.fixed_summary_with_bootstrap(
        out_path=str(tmp_path / (str(scaled) + ".parquet")), n=2000,
        seeds=(101, 102), tau=1.0, z_values=D.z_values_for(1.0, scaled=scaled),
        block_s=0.1, n_boot=10) for scaled in (False, True)]
    left, right = [f.set_index("z_s") for f in frames]
    common = left.index.intersection(right.index)
    import pandas as pd
    pd.testing.assert_frame_equal(left.loc[common], right.loc[common])

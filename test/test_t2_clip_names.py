"""A-T2-1: hai loai kep phai la HAI COT, khong mot.

`clip_fraction_max` cu gop:
    kep AR(1)         rho ngoai [RHO_MIN, RELIABLE_CEILING]  -- cai R5 noi
    kep mien bang     rho ngoai mien luoi truth-table        -- cai parquet ghi
Gop lai la NT 64. Va no DA gay hieu nham: KIEM 2 luot 1 doc 8.56% roi so
voi nguong 0.09% cua R5 -- hai so khong so sanh duoc.
"""
from __future__ import annotations

import numpy as np
import pytest

from measurements.decision_error_v2 import TruthTable
from twin import cost_v2 as C
from twin import topology_v7 as T7


def test_the_two_clip_domains_are_genuinely_different():
    """Neu hai mien trung nhau thi hai cot la thua. Chung KHONG trung."""
    tt = TruthTable()
    for mode in ("poisson", "h2"):
        his = {tt.domain(mode, bw, q)[1] for bw, _base, q in T7.LINKS.values()}
        assert his == {0.96, 1.04}
        hi_gen = float(C.RELIABLE_CEILING[mode])
        assert all(hi < hi_gen for hi in his)
        bw, _base, q = T7.LINKS["ad"]
        assert hi_gen - tt.domain(mode, bw, q)[1] == pytest.approx(0.01, abs=1e-9)



def test_run_cell_emits_both_clip_columns_and_they_differ():
    """Do THAT tren mot o da biet la co ngoai suy."""
    from measurements.decision_error_v2 import (
        TRUTH_TABLE, flatten_cell_result, measurement_cells, run_cell,
        z_values_for, CALIBRATION)
    tt = TruthTable(TRUTH_TABLE)
    cv2 = C.CostV2(strict_reliable=False)
    cells = [c for c in measurement_cells(CALIBRATION, include_pc1=True)
             if c["mode"] == "poisson" and abs(float(c["rho_bar"]) - 0.96) < 1e-9]
    assert cells, "khong tim thay o poisson@0.960"
    rows = flatten_cell_result(run_cell(
        tt, cv2, cells[0], seed=104, tau=28.0, n=280_000,
        z_values=z_values_for(28.0, scaled=False)))
    r = rows[0]
    assert "tt_domain_clip_max" in r and "ar1_clip_ratio" in r
    assert "clip_fraction_max" not in r, "ten cu phai bien mat, khong ton tai song song"
    # Hai dai luong lech ~700 lan o o nay. Ghim MOT BAC DO LON, khong ghim so.
    assert r["tt_domain_clip_max"] > 50.0 * r["ar1_clip_ratio"], (
        "hai cot gan bang nhau => nghi da noi nham vao cung mot nguon")


def test_ar1_clip_is_the_quantity_R5_bounds():
    """R5 noi ve kep AR(1). Ghim rang no NHO -- khong ghim con so chinh xac,
    vi o tau=28 chi co 50 chu ky doc lap nen uoc luong rat nhieu (A-T2-1(d)).
    """
    from measurements import sla_calib_v2 as SLA
    s = C.sigma_from_a_regime("poisson", 0.96, 0.9)
    vals = []
    for seed in (101, 102, 103, 104, 105):
        _, d = SLA.ar1_matrix("poisson", 0.96, s, tau=28.0, dt=0.005,
                              n=SLA.n_for_tau(28.0, 0.005), seed=seed,
                              return_diagnostics=True)
        vals.append(d["n_clipped_ratio"])
    assert float(np.median(vals)) < 0.01, "kep AR(1) phai duoi 1%% o o nay"
    assert float(np.median(vals)) < 100 * 0.0009, "va duoi 100x nguong R5"

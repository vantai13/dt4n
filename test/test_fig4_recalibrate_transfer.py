"""Hinh Task B-3 phai NOI DUNG cai artifact noi -- neu lech, bat o day.

Hinh la thu duy nhat reviewer nhin ky. Mot hinh tinh lai so bang mot duong
ong khac voi gate la mot cho de sai IM LANG. Test nay ep hai ben trung nhau.
"""
from __future__ import annotations

import json

from cert import recalibrate_transfer as RT
from tools import fig4_recalibrate_transfer as F


def _report() -> dict:
    with open(RT.OUTPUT, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_panel_a_reports_full_coverage_not_the_and_criterion() -> None:
    """`F1`/`L104`: ve BAO PHU la 64/64; ve ACCEPTANCE moi la 60/64."""
    A = F.panel_a_matrix(_report())
    assert A["n_cells"] == 64
    assert A["n_over_alpha"] == 0            # KHONG mot o nao vuot alpha
    assert A["max_viol"] < F.ALPHA
    assert len(A["below_floor"]) == 4        # dung bon o duoi san acceptance


def test_panel_a_is_ordered_by_kappa_descending() -> None:
    """Cau truc DAU cua panel (a) den tu thu tu hang/cot. Sai thu tu -> mat hinh."""
    order = F.cells_by_kappa(_report())
    kap = [k for _, k in order]
    assert kap == sorted(kap, reverse=True)
    assert order[0][0] == "h2@0.700"         # de nhat -> kappa_A lon nhat
    assert order[-1][0] == "poisson@0.850"   # kho nhat -> kappa_A nho nhat


def test_panel_b_slope_matches_the_scored_gate() -> None:
    """Do doc trong hinh phai la CHINH con so cua `G23-263`, khong phai mot
    uoc luong khac tinh co gan bang."""
    rep = _report()
    B = F.panel_b_points(rep)
    assert B["n"] == 56
    scored = float(rep["predictions"]["M_202"]["slope"])
    assert abs(B["slope"] - scored) < 1e-9


def test_panel_c_matches_the_scored_conservation_numbers() -> None:
    """Bon cot cua panel (c) phai trung `M-201` va `M-206` den 1e-9."""
    rep = _report()
    C = F.panel_c_bars(rep)
    m201 = rep["predictions"]["M_201"]
    m206 = rep["predictions"]["M_206"]
    assert abs(C["C3_sd_viol"] - float(m201["sd_viol"])) < 1e-9
    assert abs(C["C3_sd_acceptance"] - float(m201["sd_acceptance"])) < 1e-9
    assert abs(C["B2_sd_err"] - float(m206["sd_err_B2R"])) < 1e-9
    # menh de bao toan: moi ben GIU mot dai luong va DE TROI dai luong kia
    assert C["C3_sd_viol"] < C["C3_sd_acceptance"]
    assert C["B2_sd_acceptance"] < C["B2_sd_err"]

"""20R2.7 -- doi chung cho bo cham d_sla, tren du lieu GIA.

KHONG doc mot parquet chien dich nao: nguoi viet bo cham cung phai bi che mat.
"""
from __future__ import annotations

import importlib

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def T():
    return importlib.import_module("tools.20r2_7_dsla")


CLS = {("poisson@0.850", 0.9): "INFORMATIVE", ("h2@0.960", 0.9): "DEGENERATE"}


def fake(d_inf=0.01, d_deg=0.0, err=0.1):
    rows = []
    for cell, dv in (("poisson@0.850", d_inf), ("h2@0.960", d_deg)):
        m, rb = cell.split("@")
        for t in (0.5, 28.0):
            for s in (101, 102):
                rows.append({"mode": m, "rho_bar": float(rb), "a": 0.9, "tau_rho": t,
                             "seed": s, "z_s": 0.366, "d_sla": dv, "err_total": err})
    return pd.DataFrame(rows)


def test_clean_synthetic_passes_all(T):
    out = T.adjudicate(fake(), CLS)
    assert out["S0_instrument"]["verdict"] == "PASS"
    assert out["S1_degenerate_near_zero"]["verdict"] == "PASS"
    assert out["S2_informative_positive"]["verdict"] == "PASS"


def test_dsla_larger_than_err_is_an_instrument_failure(T):
    """S0 la HE QUA DAI SO cua dinh nghia, nen vi pham = loi DUNG CU."""
    assert T.adjudicate(fake(d_inf=0.2, err=0.1), CLS)["S0_instrument"]["verdict"] == "FAIL"


def test_nonzero_dsla_in_degenerate_cell_fails_S1(T):
    assert T.adjudicate(fake(d_deg=0.05), CLS)["S1_degenerate_near_zero"]["verdict"] == "FAIL"


def test_negative_dsla_in_informative_cell_fails_S2(T):
    assert T.adjudicate(fake(d_inf=-0.01), CLS)["S2_informative_positive"]["verdict"] == "FAIL"


def test_delta_cond_is_dsla_over_err(T):
    """Dong nhat thuc §20.2: d_sla = err_total * Delta_cond."""
    r = [x for x in T.adjudicate(fake(d_inf=0.03, err=0.1), CLS)["rows"]
         if x["class"] == "INFORMATIVE"][0]
    assert abs(r["delta_cond"] - 0.3) < 1e-12


def test_S0_checks_every_row_not_just_the_scored_z(T):
    """S0 phai quet MOI z. Neu no chi quet z = 0.366 thi mot vi pham o z khac se
    di qua im lang -- va do la dung loai loi ma S0 sinh ra de bat."""
    d = fake()
    other = d.iloc[[0]].copy()
    other["z_s"] = 4.0
    other["d_sla"] = 0.9          # >> err_total = 0.1
    assert T.adjudicate(pd.concat([d, other], ignore_index=True), CLS)["S0_instrument"]["verdict"] == "FAIL"

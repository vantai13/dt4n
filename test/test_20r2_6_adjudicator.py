"""20R2.6 -- DOI CHUNG cho CHINH BO CHAM, tren du lieu GIA.

Mot bo cham chua tung cho ra mot phan quyet BIET TRUOC thi chua chung minh duoc
gi (mutation testing, DeMillo/Lipton/Sayward 1978). File nay KHONG doc mot
parquet chien dich nao -- nguoi viet bo cham cung phai bi che mat.
"""
from __future__ import annotations

import importlib
import json
import pathlib

import numpy as np
import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CELLS = ([(m, r) for m in ("poisson", "h2") for r in (0.7, 0.85, 0.925, 0.96)]
         + [("cbr", 0.7), ("cbr", 0.85)])


@pytest.fixture(scope="module")
def ADJ():
    return importlib.import_module("tools.20r2_6_adjudicate")


@pytest.fixture(scope="module")
def INP(ADJ):
    # signed_inputs TU kiem: bang Sheppard phai tai lap, va band == K_MC*se.
    return ADJ.signed_inputs()


def fake(inp, delta=None, cbr=None, a05=None, legacy=None, stale=None, model=None):
    """Bang GIA co dap an BIET TRUOC. delta[tau] = do lech tuong doi so voi Sheppard."""
    rows = []
    for t in inp["taus"]:
        base = inp["sheppard"][t] * (1.0 + (delta or {}).get(t, 0.0))
        # Nhanh legacy duoc phat o CA z_grid: neu chi phat o 0.30 thi bo loc z
        # da loai no roi, va test "legacy khong vao PRIMARY" se RONG -- mutation
        # bo loc nhanh van xanh. Da gap that khi cay loi, nen ep truong hop kho.
        for branch, z in (("main", inp["z_grid"]),
                          ("control_legacy", 0.30), ("control_legacy", inp["z_grid"])):
            for a in (0.5, 0.9):
                for s in (101, 102, 103, 104, 105):
                    for m, r in CELLS:
                        v = base
                        if m == "cbr" and cbr is not None:
                            v = cbr
                        if a == 0.5 and a05 is not None:
                            v = a05
                        if branch == "control_legacy" and legacy is not None:
                            v = legacy
                        rows.append({"branch": branch, "a": a, "mode": m, "rho_bar": r,
                                     "seed": s, "tau_rho": t, "z_s": z,
                                     "err_total": v,
                                     "err_model": 0.0 if model is None else model,
                                     "err_stale": v if stale is None else stale,
                                     "sigma_rho": 0.01})
    return pd.DataFrame(rows)


def test_three_levels_are_not_collapsed(ADJ):
    assert ADJ.classify(+0.01, 0.03) == "AT_OR_ABOVE"
    assert ADJ.classify(-0.02, 0.03) == "BELOW_WITHIN_BAND"
    assert ADJ.classify(-0.04, 0.03) == "BELOW_BEYOND_BAND"


def test_exact_sheppard_gives_eight_hits_and_monotone(ADJ, INP):
    out = ADJ.adjudicate(fake(INP), INP)
    assert out["primary_directional"]["n_hit"] == 8
    assert out["secondary_shape"]["verdict"] == "PASS"
    assert out["secondary_shape"]["counts"]["DECREASING"] == 7


def test_shortfall_beyond_band_is_a_miss_exactly_there(ADJ, INP):
    t = INP["taus"][0]
    out = ADJ.adjudicate(fake(INP, delta={t: -2.0 * INP["band"][t]}), INP)
    miss = [r["tau"] for r in out["primary_directional"]["rows"]
            if r["directional"] == "MISS"]
    assert miss == [t]


def test_shortfall_within_band_is_hit_but_still_visible(ADJ, INP):
    """Trong bang = HIT, NHUNG ban doc nguyen van VAN phai lo ra."""
    t = INP["taus"][0]
    out = ADJ.adjudicate(fake(INP, delta={t: -0.5 * INP["band"][t]}), INP)
    p = out["primary_directional"]
    assert p["n_hit"] == 8
    assert p["levels"]["BELOW_WITHIN_BAND"] == 1
    assert p["n_hit_literal_point_reading"] == 7


def test_cbr_cannot_move_the_population(ADJ, INP):
    """AGGREGATION_FALLACY_GUARD: cbr KHONG duoc chay vao trung binh 8 o gate."""
    a = ADJ.adjudicate(fake(INP), INP)["primary_directional"]["rows"]
    b = ADJ.adjudicate(fake(INP, cbr=0.99), INP)["primary_directional"]["rows"]
    assert [r["err_hat"] for r in a] == [r["err_hat"] for r in b]


def test_a05_rows_do_not_enter_primary(ADJ, INP):
    a = ADJ.adjudicate(fake(INP), INP)["primary_directional"]["rows"]
    b = ADJ.adjudicate(fake(INP, a05=0.99), INP)["primary_directional"]["rows"]
    assert [r["err_hat"] for r in a] == [r["err_hat"] for r in b]


def test_legacy_branch_does_not_enter_primary(ADJ, INP):
    """Nhanh legacy phat o CA z_grid (xem `fake`), nen CHI bo loc branch moi
    loai duoc no. Neu khong ep the, test nay RONG."""
    a = ADJ.adjudicate(fake(INP), INP)["primary_directional"]["rows"]
    b = ADJ.adjudicate(fake(INP, legacy=0.99), INP)["primary_directional"]["rows"]
    assert [r["err_hat"] for r in a] == [r["err_hat"] for r in b]


def test_reversed_curve_cannot_pass_shape(ADJ, INP):
    """MUTATION: dao nguoc duong cong theo tau -> hinh dang PHAI truot."""
    taus = INP["taus"]
    rev = {t: INP["sheppard"][taus[-1 - i]] / INP["sheppard"][t] - 1.0
           for i, t in enumerate(taus)}
    out = ADJ.adjudicate(fake(INP, delta=rev), INP)
    assert out["secondary_shape"]["verdict"] != "PASS"


def test_unreadable_pair_is_not_counted_as_monotone(ADJ, INP):
    """§17-G4: vang bang chung != bang chung. Mau so GIU 7."""
    t1, t2 = INP["taus"][-2], INP["taus"][-1]
    out = ADJ.adjudicate(
        fake(INP, delta={t2: INP["sheppard"][t1] / INP["sheppard"][t2] - 1.0}), INP)
    s = out["secondary_shape"]
    assert s["counts"]["UNREADABLE"] == 1
    assert s["counts"]["DECREASING"] == 6
    assert s["denominator"] == 7


def test_registered_exploratory_reads_err_stale_not_err_total(ADJ, INP):
    """§17-H: H-B phai doc err_stale. Neu no doc nham err_total thi cot err_stale
    co doi the nao ket qua cung khong nhuc nhich -- test nay bat dung dieu do."""
    lo = ADJ.adjudicate(fake(INP, stale=1e-6), INP)["exploratory_registered"]["rows"]
    hi = ADJ.adjudicate(fake(INP, stale=0.99), INP)["exploratory_registered"]["rows"]
    assert all(r["HB_holds"] for r in lo)
    assert not any(r["HB_holds"] for r in hi)


def test_copied_constants_match_the_signed_text(ADJ):
    """Hai hang so chi song trong VAN BAN ky -> ban chep phai bi khoa voi goc."""
    rp = json.loads((ROOT / ADJ.PRED).read_text(encoding="utf-8"))["reading_policy"]["SECONDARY_shape"]
    assert "sigma >= 3" in rp["statistic"] and ADJ.SIGMA_READABLE == 3.0
    assert ">= 6/7" in rp["pass_rule"] and ADJ.MIN_PAIRS == 6


def test_harness_links_are_independent_so_omega0_is_zero():
    """§17-W: omega_0 = 0 THEO CAU TAO. Kiem HANH VI, khong kiem docstring."""
    from measurements.sla_calib_v2 import ar1_matrix
    x = ar1_matrix("poisson", 0.70, 0.04, tau=0.1, dt=0.005, n=200_000, seed=7)
    r = np.corrcoef(x, rowvar=False)
    off = np.abs(r[~np.eye(r.shape[0], dtype=bool)])
    assert off.max() < 0.05, "cac link KHONG doc lap: max |r| = %.3f" % off.max()

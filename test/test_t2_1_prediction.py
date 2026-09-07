"""T2.5b -- du doan T2 phai TAI LAP duoc tu artifact 22.6 da commit.

Bo test nay bao ve DAU VET, khong bao ve khoa hoc. Neu no do, du doan da ky
cua Phase T2 khong con suy ra duoc tu nen ma no tuyen bo dua vao -- va do la
loi nghiem trong hon mot du doan sai, vi mot du doan sai van la mot phep do.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib

import pytest

from tools.t2_1_prediction import (
    SRC,
    TAU_GRID_T2,
    Z_FIXED_S,
    build,
    rms,
    tau_knee,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "docs/phase-T2/01-prediction-signed.json"
PREREG = ROOT / "docs/phase-T2/00-preregistration.md"


@pytest.fixture(scope="module")
def doc():
    return json.loads(ARTIFACT.read_text())


def test_artifact_exists_and_prereg_points_at_it():
    """Prereg phai TRO VAO artifact, khong chep so."""
    assert ARTIFACT.is_file()
    text = PREREG.read_text()
    assert "docs/phase-T2/01-prediction-signed.json" in text
    assert "tools/t2_1_prediction.py" in text


def test_prereg_quotes_the_current_artifact_hash():
    """Hash trong prereg phai khop artifact tren dia.

    Do o day = nen du doan da doi ma prereg chua duoc cap nhat. Do dung la
    tinh huong ma cach "tro vao artifact" sinh ra de bat.
    """
    want = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    assert want in PREREG.read_text(), (
        "prereg khong trich hash hien tai cua artifact: %s" % want)


def test_inputs_recorded_in_provenance_still_match_disk(doc):
    """Moi input 22.6 phai con nguyen hash da ghi."""
    inputs = doc["provenance"]["inputs"]
    assert inputs, "provenance khong ghi input nao"
    for rel, want in inputs.items():
        f = ROOT / rel
        assert f.is_file(), "input bien mat: %s" % rel
        got = hashlib.sha256(f.read_bytes()).hexdigest()
        assert got == want, "input da doi: %s" % rel


def test_derivation_reproduces_22_6_own_prediction(doc):
    """Doi chung noi: tai tao `ratio_pred_finite` cua chinh 22.6."""
    for name, cell in doc["cells"].items():
        sc = cell["self_check"]
        assert sc["pass"], (name, sc)
        assert sc["max_abs_diff_vs_22_6_ratio_pred"] < 1e-9


def test_rebuilding_from_source_gives_the_same_predictions(doc):
    """Chay lai script phai cho DUNG cung so. Khong co nguon ngau nhien."""
    again = build()
    for name in doc["cells"]:
        a = doc["cells"][name]["branch_B_operational"]["rms_curves"]
        b = again["cells"][name]["branch_B_operational"]["rms_curves"]
        assert a == b, name


def test_branch_b_is_monotone_decreasing_in_tau(doc):
    """D-T2.6-1. z co dinh, tau tang => (1-exp(-z/tau)) giam => rms giam."""
    for name, cell in doc["cells"].items():
        assert cell["branch_B_operational"]["monotone_decreasing_in_tau"], name


def test_branch_a_is_flat_in_tau_by_construction(doc):
    """z/tau co dinh => rms KHONG phu thuoc tau. Day la tautology F4 duoc
    phat bieu thanh mot du doan kiem duoc, khong phai mot ket qua."""
    for name, cell in doc["cells"].items():
        for u, span in cell["branch_A_mechanism"]["relative_span_across_tau"].items():
            assert span == pytest.approx(0.0, abs=1e-12), (name, u, span)


def test_law_matches_the_closed_form():
    """Ham `rms` phai dung DUNG luat da ghi trong prereg."""
    A, c, em, z, tau = 26.07, 0.8922, 2.142, 0.30, 5.0
    want = math.sqrt(em ** 2 + c * A ** 2 * (1.0 - math.exp(-z / tau)))
    assert rms(z, tau, A, c, em) == pytest.approx(want, rel=1e-15)


def test_tau_knee_inverts_the_law():
    """tau_knee(z) phai la nghiem that: rms tai do bang (1+tol)*em."""
    A, c, em, z, tol = 26.07, 0.8922, 2.142, 0.30, 0.05
    t = tau_knee(z, A, c, em, tol=tol)
    assert math.isfinite(t) and t > 0
    assert rms(z, t, A, c, em) == pytest.approx((1.0 + tol) * em, rel=1e-9)


def test_dead_cell_is_kept_as_a_negative_control(doc):
    """QD-3: cbr bi loai khoi ket qua chinh NHUNG giu lam doi chung am."""
    dead = doc["cells"]["cbr@0.700"]
    assert dead["role"] == "negative_control"
    assert dead["fit"]["A"] < 1e-3
    live = [v for v in doc["cells"].values() if v["role"] == "live"]
    assert len(live) == 3
    assert all(v["fit"]["A"] > 1.0 for v in live)


def test_span_driver_is_named_not_orphaned(doc):
    """Mot con so bat thuong phai chi ra o nao sinh ra no."""
    d = doc["signed_predictions"]["D-T2.6-4"]["driver"]
    assert d["cell"] == "poisson@0.850"
    assert d["quantity"] == "rms_em_span_pct"
    assert d["span_pct"] > 5.0


def test_predicted_knees_mostly_fall_outside_the_signed_tau_grid(doc):
    """D-T2.6-6 noi truoc rang T2.6 se KHONG thay knee tren luoi.

    Mot du doan "se khong thay gi" van la mot du doan, va chinh no chan
    viec mo rong luoi de di tim knee (T2-6c).
    """
    grid_max = max(TAU_GRID_T2)
    knees = [k for v in doc["cells"].values() if v["role"] == "live"
             for k in v["branch_B_operational"]["tau_knee_s"].values()]
    assert knees and min(knees) < grid_max < max(knees) or min(knees) > grid_max
    assert sum(k > grid_max for k in knees) >= len(knees) - 1


# --- D-T2.6-4 dang khong thu nguyen -------------------------------------

def test_independence_criterion_has_teeth_on_committed_data(doc):
    """Mot du doan khong the sai la trang tri. Dang moi phai VI PHAM DUOC.

    Do duoc tren 22.6: 3/9 FAIL o cac o song.
    """
    p = doc["signed_predictions"]["D-T2.6-4"]
    assert p["n_checks"] == 9
    assert p["n_fail_on_22_6"] == 3


def test_independence_failures_land_where_22_6_already_failed(doc):
    """Hai FAIL cua `em` phai roi vao poisson@0.850 -- o ma gate
    `rms_em_independent_of_tau` cua 22.6 da FAIL (F3 / rui ro R4).
    Ba duong doc lap cham cung mot cho."""
    per = doc["signed_predictions"]["D-T2.6-4"]["per_cell"]
    fails = {(c, q) for c, qs in per.items()
             for q, v in qs.items() if not v["passes"]}
    assert ("poisson@0.850", "em") in fails
    assert ("poisson@0.850", "c") in fails
    assert ("h2@0.700", "em") in fails
    assert ("poisson@0.925", "A") not in fails


def test_a_three_percent_band_would_have_been_vacuous(doc):
    """Bang '+/-3%' rong hon HIEU UNG => du doan khong the sai.

    span giua-tau do duoc chi 0.12-0.83%; mot bang 3% bao trum het.
    """
    per = doc["signed_predictions"]["D-T2.6-4"]["per_cell"]
    spans = [v["span_between_tau_pct"] for qs in per.values()
             for k, v in qs.items() if k in ("A", "c")]
    assert max(spans) < 3.0, "bang 3% se bao trum moi span => khong the sai"


# --- D-T2.6-3 pham vi doc duoc, khai TRUOC ------------------------------

def test_hump_power_scope_is_declared_before_the_run(doc):
    """Khai INSUFFICIENT_POWER TRUOC, de no khong thanh loi bien minh sau."""
    scope = doc["signed_predictions"]["D-T2.6-3"]["power_scope_declared_before_run"]
    assert scope["poisson@0.925"]["declared_scope"] == "READABLE"
    assert scope["h2@0.700"]["declared_scope"] == "INSUFFICIENT_POWER"
    assert scope["poisson@0.925"]["amplitude_over_noise"] > 5.0
    assert scope["h2@0.700"]["amplitude_over_noise"] < 2.0


# --- BIEN THAI: quan he giua f(x) va f(T(x)), khong phai gia tri --------
# Hang so hard-code KHONG phan ung voi T, nen bi lo. Day la thuoc giai
# truc tiep cho "kiem luat, khong kiem truong hop".

def test_metamorphic_rms_monotone_in_z():
    """z lon hon -> rms lon hon, o MOI tau. Bat sai dau trong exp(-z/tau)."""
    A, c, em = 26.07, 0.8922, 2.142
    for tau in (0.5, 5.0, 28.0):
        v = [rms(z, tau, A, c, em) for z in (0.05, 0.15, 0.30, 0.50)]
        assert all(x < y for x, y in zip(v, v[1:])), tau


def test_metamorphic_rms_decreasing_in_tau_at_fixed_z():
    """tau lon hon -> rms nho hon, o z co dinh. Day la D-T2.6-1 dang bien the."""
    A, c, em = 26.07, 0.8922, 2.142
    for z in (0.05, 0.30, 0.50):
        v = [rms(z, t, A, c, em) for t in (1.0, 5.0, 28.0)]
        assert all(x > y for x, y in zip(v, v[1:])), z


def test_metamorphic_tau_knee_scales_with_z():
    """Gap doi z -> gap doi tau_knee (vi z/tau la bien duy nhat).

    Bat mot cai dat ghim tau_knee vao mot hang so.
    """
    A, c, em = 26.07, 0.8922, 2.142
    for z in (0.05, 0.15):
        assert tau_knee(2 * z, A, c, em) == pytest.approx(
            2 * tau_knee(z, A, c, em), rel=1e-9)


def test_metamorphic_rms_floor_is_em_as_z_goes_to_zero():
    """z -> 0 thi rms -> em, bat ke tau. Bat viec bo quen so hang em."""
    A, c, em = 26.07, 0.8922, 2.142
    for tau in (0.5, 28.0):
        assert rms(1e-12, tau, A, c, em) == pytest.approx(em, rel=1e-6)

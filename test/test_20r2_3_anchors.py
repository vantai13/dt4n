r"""20R2.3 -- NEO B: bat bien TAT DINH cho ma MOI cua G4.

VI SAO CAN NEO THU HAI
======================
Doi chung hoi quy (NEO A, tools/20r2_3_bit_exact_regression.py) neo CHINH XAC
nhung doan ma ban KHONG doi:

    NEO A di qua      Z_ALL (9 diem legacy) - nhanh SLA cu - lag cu
    CHIEN DICH di qua Z_ALL_20R2 (13 diem) - SLA exogenous - dispatch --z-grid

    giao cua hai = phan KHONG doi
    => ma MOI cua G4 KHONG duoc NEO A phu

"bit-exact PASS" la mot phat bieu DUNG dan toi mot ket luan SAI neu khong khai
do phu. Ma moi vua duoc viet, tuc la cho rui ro cao nhat, va no KHONG co
artifact lich su nao de so.

NEO B khong dua vao QUA KHU -- no dua vao RANG BUOC TAT DINH: nhung dieu dung
theo suy luan, bat ke lich su. Ba loai:

  1. doi chung twin-hoan-hao: err = 0 CHINH XAC (docstring dong 6 bao dam)
  2. z = 0 cho SAN MO HINH, va san do KHONG phu thuoc luoi z
  3. z chung giua HAI luoi phai cho CUNG ket qua -- lag k = round(z/dt)
     khong biet minh den tu luoi nao

Cai thu ba manh nhat va re nhat: bon diem z nam trong CA HAI luoi
(0.0, 1.0, 2.0, 4.0), du de bat moi ro ri o dispatch.

NGUYEN TAC MANG DI DUOC: khi them mot nhanh MOI song song nhanh cu, tim nhung
diem HAI NHANH PHAI TRUNG va khoa chung lai. Mot nhanh moi it khi sai o cho
moi -- no sai o cho no KHAC nhanh cu trong khi le ra phai giong.
"""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def DE():
    import measurements.decision_error_v2 as _DE
    return _DE


# ------------------------------------------------- diem chung giua hai luoi

def test_the_two_grids_share_exactly_four_z_points(DE):
    """Ghim TAP diem chung. Neu no doi, cac test duoi mat luc ma khong ai biet."""
    shared = sorted(set(DE.Z_ALL) & set(DE.Z_ALL_20R2))
    assert shared == [0.0, 1.0, 2.0, 4.0], (
        "tap diem z chung da doi: %s. Cac phep kiem noi hai nhanh dua vao no."
        % shared)


@pytest.mark.parametrize("tau", [3.0])
def test_shared_z_points_agree_across_grids(DE, tau, tmp_path):
    """★ NEO B manh nhat: z chung phai cho CUNG ket qua tren CA HAI luoi.

    Lag la k = round(z/dt) -- no khong biet minh den tu luoi nao. Neu hai luoi
    cho hai so tai CUNG mot z thi dispatch --z-grid da lam ro ri thu gi do
    NGOAI z, va do la dung loai loi ma NEO A (bit-exact vs qua khu) khong the
    bat: NEO A chi chay nhanh legacy.

    Day KHONG phai mot phep so voi qua khu -- no la mot rang buoc TAT DINH.
    """
    import subprocess
    import sys

    import pandas as pd

    shared = sorted(set(DE.Z_ALL) & set(DE.Z_ALL_20R2))
    assert shared, "hai luoi khong co diem chung -- khong noi duoc"

    out = {}
    for grid in ("legacy", "20r2_measured"):
        p = tmp_path / ("%s.parquet" % grid)
        r = subprocess.run(
            [sys.executable, "-m", "measurements.decision_error_v2",
             "--run-fixed", "--tau", "%g" % tau, "--z-mode", "fixed",
             "--z-grid", grid,
             # [20R2.5-P2] --calibration khong con mac dinh. NEO B doi MOT yeu
             # to (luoi z) nen truc SLA phai GIONG NHAU o hai nhanh, va phai la
             # truc DA KY o §3 -- dung truc cua chien dich.
             "--calibration",
             "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json",
             "--seeds", "101", "--out", str(p)],
            cwd=str(ROOT), capture_output=True, text=True)
        assert r.returncode == 0, grid + ":\n" + r.stderr[-1200:]
        out[grid] = pd.read_parquet(p)

    key = ["mode", "rho_bar", "seed", "z_s"]
    cols = ["err_total", "err_model", "err_stale", "d_sla",
            "rms_e_model", "rms_e_stale", "cov_e"]
    a = out["legacy"]
    b = out["20r2_measured"]
    a = a[a["z_s"].isin(shared)].sort_values(key).reset_index(drop=True)
    b = b[b["z_s"].isin(shared)].sort_values(key).reset_index(drop=True)

    assert len(a) == len(b) > 0, "so hang tai diem chung lech: %d vs %d" % (len(a), len(b))
    for c in key:
        assert (a[c].values == b[c].values).all(), "khoa lech o cot " + c
    for c in cols:
        diff = (a[c].values != b[c].values)
        assert not diff.any(), (
            "cot %r LECH tai %d/%d hang o diem z CHUNG.\n"
            "  Lag k = round(z/dt) khong phu thuoc luoi, nen hai luoi PHAI "
            "trung tai z chung.\n"
            "  Lech o day nghia la dispatch --z-grid lam ro ri thu gi do "
            "NGOAI z -- va NEO A khong bat duoc vi no chi chay nhanh legacy."
            % (c, int(diff.sum()), len(a)))


def test_scoring_window_is_identical_for_both_grids(DE):
    """Cua so cham diem lay max cua luoi. Hai luoi cung max => cung cua so.

    Neu khac, hai luoi cham tren HAI DAI HANG khac nhau va ket qua khong so
    duoc -- dung loi ma docstring scoring_window_start canh bao ("do lech DOI
    DAU theo tau").
    """
    assert max(DE.Z_ALL) == max(DE.Z_ALL_20R2) == 4.0
    for tau in (0.5, 3.0, 28.0):
        k_legacy = max(int(round(z / DE.DT)) for z in DE.Z_ALL)
        k_20r2 = max(int(round(z / DE.DT)) for z in DE.Z_ALL_20R2)
        assert k_legacy == k_20r2, (
            "tau=%g: cua so cham diem lech (%d vs %d)" % (tau, k_legacy, k_20r2))


# ------------------------------------------------- bat bien cua chinh luoi

def test_the_20r2_grid_covers_the_measured_domain_not_the_legacy_one(DE):
    """Ly do ton tai cua luoi moi, viet thanh assert.

    Luoi legacy phu KHIT mien LEGACY [0.055, 0.550]; luoi 20R2 phai phu mien
    MEASURED [0.115, 0.615]. Neu ai do "sua" luoi moi ve gan luoi cu thi ly do
    ton tai cua no bien mat -- va no se bien mat IM LANG.
    """
    op = [z for z in DE.Z_GRID_20R2_MEASURED]
    assert min(op) == 0.115, "san that cua truc measured"
    assert max(op) == 0.615, "max cua truc mo hinh measured"
    legacy_op = [z for z in DE.Z_GRID if z > 0]
    assert max(legacy_op) == 0.55, "luoi legacy da doi -- 166 parquet neo theo no"
    assert min(op) > max(legacy_op) - 0.5, "hai luoi khong con phan biet duoc"


def test_z_control_point_is_in_both_grids(DE):
    """z = 0 la DIEM NOI: no co trong ca hai luoi.

    Tai z = 0 khong co tuoi, nen err phai bang SAN MO HINH -- va san mo hinh
    KHONG phu thuoc luoi z. Do la mot rang buoc tat dinh, kiem duoc ma khong
    can bat ky artifact lich su nao.
    """
    assert 0.0 in DE.Z_ALL and 0.0 in DE.Z_ALL_20R2
    assert DE.Z_CONTROL_20R2 == (0.0,)


def test_extrapolated_flag_covers_the_same_points_on_both_grids(DE):
    """`extrapolated` doc tu Z_EXTRAP, mot hang so DUNG CHUNG cho hai luoi.

    Neu mot luoi co diem ngoai suy ma khong duoc gan co, nguoi doc se tuong do
    la diem van hanh that.
    """
    for grid in (DE.Z_ALL, DE.Z_ALL_20R2):
        for z in DE.Z_EXTRAP:
            assert z in grid, "luoi thieu diem ngoai suy %g" % z
    assert set(DE.Z_EXTRAP) == {1.0, 2.0, 4.0}


# ------------------------------------------------- doi chung tat dinh

def test_perfect_twin_control_is_guaranteed_exactly_zero_in_the_contract(DE):
    """Phep kiem DUNG CU that su cua 20R2 -- va no TAT DINH.

    Khac doi chung `cbr` (phu thuoc che do luu luong, va da bi rut vi suy bien),
    rang buoc nay khong the bi suy bien lam hong: neu twin = su that thi moi
    argmin trung nhau, KE CA luoi z nao.
    """
    src = (ROOT / "measurements/decision_error_v2.py").read_text(encoding="utf-8")
    assert "perfect-twin control is required to be exactly zero" in src, (
        "hop dong doi chung twin-hoan-hao da bien mat khoi docstring -- "
        "phep kiem dung cu cua 20R2 mat cho dua")


def test_perfect_twin_control_actually_runs_through_run_cell(DE):
    """[20R2.5-P4] Test tren CHI kiem mot CAU VAN co trong ma. Mot cau van
    khong bao gio do duoc.

    Ban cu cua doi chung (NC1b) so `c_true.argmin` voi CHINH `a_true =
    c_true.argmin` -- luon bang 0, va khong goi run_cell. Kill test (cay loi
    lech-mot `lag_rows = current - k - 1`) cho: NC1b 0.0 (MU), doi chung qua
    run_cell 0.026315 (BAT duoc).

    Test nay kiem HANH VI, khong kiem van ban.
    """
    n = 20000
    rep = DE.perfect_twin_control(
        "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json",
        tau=3.0, n=n, seed=999, z_values=DE.Z_ALL_20R2, a_override=0.9)

    assert rep["violations"] == [], (
        "hop dong twin-hoan-hao vo: %r" % rep["violations"][:3])
    # DOI CHUNG CUA DOI CHUNG: neu khong o dau co err > 0 tai z > 0 thi lag
    # khong lam gi ca, va "0 vi pham" thoa mot cach TAM THUONG -- den xanh rong.
    assert rep["max_err_total_z_positive"] > 0.0, (
        "doi chung thoa TAM THUONG: khong diem z > 0 nao cho err > 0")
    assert rep["n_checked"] >= 10 * len(DE.Z_ALL_20R2)


def test_perfect_twin_control_is_not_a_tautology(DE):
    """Doi chung phai DO cai gi do: neu duong ong bi cay loi lech-mot thi no
    PHAI do. Day la mutation testing (DeMillo, Lipton & Sayward 1978) -- mot
    test chua tung do truoc mot loi that thi chua chung minh duoc gi."""
    import types
    src = (ROOT / "measurements/decision_error_v2.py").read_text(encoding="utf-8")
    marker = "        lag_rows = current - k\n"
    assert src.count(marker) == 1, "diem cay loi da doi -- cap nhat test nay"
    mod = types.ModuleType("de_mutant_offbyone")
    mod.__file__ = str(ROOT / "measurements/decision_error_v2.py")
    exec(compile(src.replace(marker, "        lag_rows = current - k - 1\n"),
                 mod.__file__, "exec"), mod.__dict__)

    rep = mod.perfect_twin_control(
        "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json",
        tau=3.0, n=20000, seed=999, z_values=mod.Z_ALL_20R2, a_override=0.9)
    assert rep["violations"], (
        "doi chung KHONG bat duoc loi lech-mot -- no la mot den xanh rong")


# ------------------------------------------------- do phu duoc KHAI

def test_the_regression_artifact_declares_what_it_does_not_anchor():
    """gate 3-4: 'bit-exact PASS' ma khong khai do phu la mot phat bieu DUNG
    dan toi mot ket luan SAI."""
    import json
    p = ROOT / "results/PENDING/phase-20R2/bit_exact_regression.json"
    if not p.is_file():
        pytest.skip("chua chay doi chung hoi quy")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert "WHAT_THIS_IS" in d and "KHONG phai" in d["WHAT_THIS_IS"]
    cov = d["coverage"]
    assert cov["NOT_anchored"], "khong khai phan KHONG duoc neo"
    joined = " ".join(cov["NOT_anchored"])
    assert "Z_GRIDS" in joined or "Z_ALL_20R2" in joined
    assert "--z-grid" in joined


def test_regression_is_labelled_as_regression_not_science():
    """gate 3-3 [S26]: mot dong 'bit-exact PASS' khong kem nhan se duoc doc
    thanh 'ket qua da duoc xac nhan'. Hai chuyen khac han."""
    import json
    p = ROOT / "results/PENDING/phase-20R2/bit_exact_regression.json"
    if not p.is_file():
        pytest.skip("chua chay doi chung hoi quy")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert "golden chep lai ca loi" in d["WHAT_THIS_IS"]
    assert d["validity"]["pending_on"], "artifact PENDING phai khai pending_on"

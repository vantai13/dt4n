"""NC-T2-1: cong duong chan sinh tu cua Phase T2.

Bo test nay bao ve HOP DONG, khong bao ve khoa hoc. Neu no do, gan nhu
chac chan ban da doi thu tu rut RNG hoac doi kieu tra ve -- khong phai
ban da phat hien dieu gi ve tai mang.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

import numpy as np
import pytest

from measurements import decision_error_v2 as D
from measurements import sla_calib_v2 as S

# Quy uoc golden cua repo: results/RAW/<phase>/golden/*.json (xem
# tools/freeze_l2_golden.py). RAW la Hang 1: chi doc, khong ghi de.
#
# Luu DIGEST chu khong luu mang: `.gitignore:64` bo qua results/**/* tru
# *.json, va mot mang 200k x 8 float64 la 12.8 MB. Digest van cho doi chung
# BIT-EXACT -- va quan trong hon, no CHAY DUOC TREN CLONE SACH. Mot golden
# khong nam trong git la mot doi chung khong ton tai voi nguoi khac.
GOLDEN = "results/RAW/phase-T2/golden/ar1_tau1.0_poisson_0.925_s101.json"

SIGMA_925 = 0.0218


def _golden():
    return json.loads((pathlib.Path(__file__).resolve().parents[1]
                       / GOLDEN).read_text())


def _digest(arr) -> str:
    return hashlib.sha256(arr.tobytes(order="C")).hexdigest()


def test_golden_is_tracked_by_git_so_it_exists_on_a_clean_clone():
    """Mot doi chung hoi quy khong nam trong git la mot doi chung khong
    ton tai voi bat ky ai khac. Repo nay co tap quan kiem chung clean-clone,
    nen dieu do phai duoc ghim."""
    root = pathlib.Path(__file__).resolve().parents[1]
    assert (root / GOLDEN).is_file()
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", GOLDEN],
        cwd=root, capture_output=True, text=True)
    assert tracked.returncode == 0, (
        "%s khong duoc git theo doi -- test nay se do tren clone sach" % GOLDEN)


def test_golden_records_the_exact_generator_arguments():
    """Mot digest khong kem tham so sinh ra no thi khong tai lap duoc."""
    g = _golden()
    assert g["args"] == {"mode": "poisson", "rho_bar": 0.925, "sigma": 0.0218,
                         "tau": 1.0, "dt": 0.005, "n": 200000, "seed": 101}
    assert g["shape"] == [200000, 8] and g["dtype"] == "float64"


def test_ar1_bit_exact_at_legacy_tau():
    """Sinh lai voi code MOI tai tau=1.0 phai TRUNG TUNG BIT voi ban vang.

    FAIL o day gan nhu chac chan la THU TU RUT RNG doi. Kiem theo thu tu:
      (1) co them/bot loi goi rng.standard_normal() nao khong?
      (2) hinh dang (shape) cua lenh rut co doi khong?
      (3) vong lap theo link co doi thu tu khong?
    """
    g = _golden()
    got = S.ar1_matrix(**{k: v for k, v in g["args"].items()
                          if k not in ("mode", "rho_bar", "sigma")},
                       mode=g["args"]["mode"], rho_bar=g["args"]["rho_bar"],
                       sigma=g["args"]["sigma"])
    assert _digest(got) == g["sha256_tobytes_C"]
    assert list(got.shape) == g["shape"]
    assert got.mean() == pytest.approx(g["mean"], rel=1e-15)
    assert got.std() == pytest.approx(g["std"], rel=1e-15)


def test_diagnostics_flag_does_not_change_the_array():
    """Them chan doan la OPT-IN: duong tra ve cu KHONG duoc doi kieu."""
    a = S.ar1_matrix("poisson", 0.925, SIGMA_925,
                     tau=1.0, dt=0.005, n=20_000, seed=101)
    b, diag = S.ar1_matrix("poisson", 0.925, SIGMA_925,
                           tau=1.0, dt=0.005, n=20_000, seed=101,
                           return_diagnostics=True)
    assert isinstance(a, np.ndarray)          # KHONG phai tuple
    assert np.array_equal(a, b)
    assert diag["n_clipped_ratio"] < 0.01     # V-T2-3
    assert diag["cycles"] == pytest.approx(20_000 * 0.005 / 1.0)


def test_tau_has_no_silent_default_anywhere():
    """Hang so mac dinh im lang la cach tau=1.0 len vao bon phase."""
    assert not hasattr(S, "DEFAULT_TAU")
    with pytest.raises(TypeError):
        S.ar1_matrix("poisson", 0.925, SIGMA_925, dt=0.005, n=100, seed=1)


def test_ar1_rejects_unusable_tau():
    """tau phai duong va du phan giai so voi dt."""
    with pytest.raises(ValueError):
        S.ar1_matrix("poisson", 0.925, SIGMA_925,
                     tau=0.0, dt=0.005, n=100, seed=1)
    with pytest.raises(ValueError):
        # tau = 10*dt < 20*dt -> khong du phan giai
        S.ar1_matrix("poisson", 0.925, SIGMA_925,
                     tau=0.05, dt=0.005, n=100, seed=1)


def test_block_scales_with_tau():
    """Kenh (c): block conformal PHAI la 5*tau, khong phai 5 giay."""
    assert D.block_s_for_tau(1.0) == pytest.approx(5.0)
    assert D.block_s_for_tau(2.87) == pytest.approx(14.35)
    assert D.block_s_for_tau(28.0) == pytest.approx(140.0)


def test_legacy_block_s_still_derives_from_the_rule():
    """BLOCK_S cu (band_v2 doc no) gio TU DAN ra tu 5*tau, khong roi tu troi."""
    assert D.BLOCK_S == pytest.approx(D.BLOCKS_PER_TAU * D.TAU_LOAD_LEGACY)
    assert D.BLOCK_S == pytest.approx(5.0)
    assert D.TAU == D.TAU_LOAD_LEGACY          # bi danh giu hop dong import


def test_n_scales_with_tau_to_keep_ten_blocks():
    """Ngan sach suy TU tham so, khong dat truoc."""
    for tau in (1.0, 5.0, 20.0, 28.0):
        n = S.n_for_tau(tau, dt=0.005)
        blocks_per_seed = (n * 0.005) / D.block_s_for_tau(tau)
        assert blocks_per_seed >= 10.0, (tau, n, blocks_per_seed)


def test_n_for_tau_reproduces_the_t2_0_budget_table():
    """Doi chieu voi bang F5 cua T2.0: tau=28 can n=280_000, khong phai 200_000."""
    assert S.n_for_tau(1.0, dt=0.005) == 200_000
    assert S.n_for_tau(20.0, dt=0.005) == 200_000
    assert S.n_for_tau(28.0, dt=0.005) == 280_000

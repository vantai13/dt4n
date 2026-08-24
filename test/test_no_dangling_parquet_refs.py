#!/usr/bin/env python3
"""Khong script nao duoc tro toi parquet khong ton tai mot cach IM LANG.

Doi chung duong DA CHAY: `cert/live_region_sweep.py` tro toi bon file
`results/SUPERSEDED/phase-22/calib_set_v3_*.parquet` khong con tren dia, tu
Lesson 23.16 den 23.21 ma khong test nao keu. `M-136` bi chan vi chuyen do --
va bi chan NHAM, vi `M-136` la mot phep kiem BAT BIEN, no khong can du lieu
lich su (xem `39-l51-adjudication.md`).

Day la lint tinh (AST), khong phai runtime: no bat duong dan CHET ngay ca khi
nhanh code chua duoc chay bao gio. Cung tinh than voi
`test_cli_flags_are_wired.py` (amendment 23-59).
                                                        (amendment 23-60)
"""
from __future__ import annotations

import ast
import glob
import hashlib
import json
import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Muc DA BIET, moi muc kem ly do va lesson so huu. CHI DUOC NGAN DI.
KNOWN_DANGLING: dict[str, str] = {
    # `L51`: tam parquet Phase 22 (~1.9 GB) khong duoc commit (gioi han kich
    # thuoc kho) va digest cua chung khong duoc luu trong bao cao cung thoi.
    # Bon file duoi day la bon cell Dot 4 ma `live_region_sweep` can. Viec 3
    # (Lesson 23.21h) so huu chung: chung se duoc SINH LAI tu seed, KHONG duoc
    # "tim thay ban thay the".
    "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.875.parquet": "L41/L51 - Dot 4, Viec 3",
    "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.900.parquet": "L41/L51 - Dot 4, Viec 3",
    "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.650.parquet": "L41/L51 - Dot 4, Viec 3",
    "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.675.parquet": "L41/L51 - Dot 4, Viec 3",
    # `L51`: bon cell cua luoi 8 cell goc, mat cung dot. Chan viec SINH LAI
    # `eight_cell_sweep_U3_measured_v7_slaB.json` (xem `L75`).
    "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.960.parquet": "L51 - chan sinh lai eight_cell",
    "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.850.parquet": "L51 - chan sinh lai eight_cell",
    "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.925.parquet": "L51 - chan sinh lai eight_cell",
    "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.960.parquet": "L51 - chan sinh lai eight_cell",
}


def _string_constants(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value


def _is_concrete_path(s: str) -> bool:
    """Chi giu chuoi la mot DUONG DAN CU THE, khong phai mau hay duoi.

    Bon dang bi loai, va deu la duong ong hop le chu khong phai no:
      "{mode}"      mau str.format  -> `_calib_path` thay o runtime
      "%s" / "%.3f" mau printf       -> nhu tren
      "*"           glob             -> giai o runtime
      ".parquet"    duoi don thuan   -> mot manh de noi chuoi, khong phai duong
    """
    if "{" in s or "%" in s or "*" in s:
        return False
    return "/" in s


# Duong dan GHI RA (output). Chung KHONG can ton tai truoc khi chay -- co mat
# hay khong la ket qua, khong phai dieu kien. Danh sach nay ngan va tuong minh
# thay vi mot heuristic doan "input hay output".
OUTPUT_PATHS: dict[str, str] = {
    # amendment 23-60: file da HA xuong SUPERSEDED/. HANG SO nay CO Y GIU
    # nguyen duong LIVE de mot lan chay KHONG CO CO se ghi ra LIVE/ va bi
    # `test_every_live_parquet_has_a_validity_sidecar` +
    # `test_live_artifact_has_approved_axes` bat NGAY (fail loud). Doi no sang
    # SUPERSEDED/ se lang le GHI DE bang chung da dong -- vi pham `MAP.md` muc 4.
    "results/LIVE/phase-20R/decision_error_by_age_by_regime.parquet":
        "FIXED_OUT cua decision_error_v2 -- duong GHI RA, co y de fail loud",
    # `tools/tier_results.py` la BAN DO DI DOI: no liet ke duong CU (truoc khi
    # phan tang) de anh xa sang duong MOI. Duong cu KHONG con ton tai la dung
    # muc dich cua no.
    # `OUT_PARQUET` cua builder v2 (da bi v3 thay the). Duong GHI RA; khong
    # con ban dung nao vi khong ai chay v2 nua.
    "results/SUPERSEDED/phase-21R/calib_set.parquet":
        "OUT_PARQUET cua build_calib_set_v2 -- duong GHI RA, builder da bi v3 thay",
    "results/phase-20R/truth_table.parquet": "ban do di doi tier_results",
    "results/phase-20R/decision_error_by_age_by_regime.parquet": "ban do di doi tier_results",
}


# File CON tren dia tac gia nhung KHONG trong git. Moi muc PHAI co digest
# trong SURVIVING_CALIB_DIGESTS.json -- `test_local_only_entries_have_pinned_digests`
# ep dieu do. Khong digest = mot loi khai, khong phai bang chung.
DIGEST_PIN = "results/RAW/phase-22/SURVIVING_CALIB_DIGESTS.json"
LOCAL_ONLY: dict[str, str] = {
    "results/SUPERSEDED/phase-22/calib_set_v3.parquet": "L80 - VERIFIED_ORIGINAL",
    "results/SUPERSEDED/phase-22/calib_set_v3_h2_0.700.parquet": "L80 - VERIFIED_ORIGINAL",
    "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.850.parquet": "L80 - VERIFIED_ORIGINAL",
    # ★ KHAC digest lich su -> KHONG phai ban goc. Duoc phep TON TAI nhung
    # KHONG duoc dung lam moc doi chung (xem `G23-212a`, chi 3 cell).
    "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.700.parquet":
        "L80 - NOT_ORIGINAL_DO_NOT_REUSE",
    # Khong nam trong `provenance.inputs` lich su nen KHONG doi chieu duoc.
    # Ton tai != duoc phep tai dung (`G23-174`).
    "results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.925.parquet":
        "L80 - NO_HISTORICAL_DIGEST",
}


def _tracked_files() -> set[str]:
    """File git THUC SU theo doi -- day la thu ban CLONE SACH nhan duoc.

    Vi sao KHONG dung `os.path.exists`: no tra loi "co tren MAY TOI", trong khi
    cau can bao ve la "co tren BAN CLONE SACH". Va hai cau do NGHICH nhau --
    file rac local LAM IM cai chan. Do duoc 2026-08-24: 7 tham chieu di qua
    tren may tac gia, do ngay tren clone sach. Cung lop loi voi PASS RONG
    (`37-pending-tier-adjudication.md` muc 2), lan nay nan nhan la nguoi viet.
    """
    import subprocess

    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return set(out.splitlines())


def _scan_all() -> list[tuple[str, str]]:
    """Moi tham chieu parquet cu the -- KHONG loc theo dia."""
    found = []
    for pattern in ("cert/*.py", "measurements/*.py", "tools/*.py"):
        for py in sorted(glob.glob(os.path.join(REPO, pattern))):
            rel_py = os.path.relpath(py, REPO).replace(os.sep, "/")
            for s in _string_constants(py):
                if s.endswith(".parquet") and _is_concrete_path(s):
                    found.append((rel_py, s))
    return found


def test_no_hardcoded_untracked_parquet():
    """Ban KHA CHUYEN: cham theo `git ls-files`, khong theo dia.

    Ba loi thoat TUONG MINH, va chi ba:
        KNOWN_DANGLING  da mat, co lesson so huu
        OUTPUT_PATHS    duong GHI RA
        LOCAL_ONLY      con tren dia tac gia, khong trong git, DA ghim digest
    """
    tracked = _tracked_files()
    bad = [
        "%s -> %s" % (py, s)
        for py, s in _scan_all()
        if s not in KNOWN_DANGLING
        and s not in OUTPUT_PATHS
        and s not in LOCAL_ONLY
        and s not in tracked
    ]
    assert not bad, (
        "tham chieu parquet KHONG duoc git theo doi (clone sach se chet):\n"
        "  %s\n"
        "  -> them vao KNOWN_DANGLING/OUTPUT_PATHS/LOCAL_ONLY KEM LY DO, "
        "hoac commit file." % "\n  ".join(bad)
    )


def test_local_only_entries_have_pinned_digests():
    """Muc LOCAL_ONLY khong co digest la mot LOI KHAI, khong phai bang chung."""
    pin = os.path.join(REPO, DIGEST_PIN)
    assert os.path.exists(pin), "chua ghim digest: " + DIGEST_PIN
    with open(pin, "r", encoding="utf-8") as fh:
        have = json.load(fh)["files"]
    missing = sorted(s for s in LOCAL_ONLY if s not in have)
    assert not missing, (
        "muc LOCAL_ONLY khong co digest trong %s:\n  %s"
        % (DIGEST_PIN, "\n  ".join(missing))
    )


def test_pinned_digests_still_match_disk():
    """Digest da ghim phai con khop BYTE tren dia.

    Neu mot file doi noi dung ma digest khong doi, moi ket luan dung no thanh
    vo nghia mot cach IM LANG -- dung dieu `L51` canh bao.
    """
    pin = os.path.join(REPO, DIGEST_PIN)
    if not os.path.exists(pin):
        pytest.skip("chua ghim digest")
    with open(pin, "r", encoding="utf-8") as fh:
        files = json.load(fh)["files"]
    drift = []
    for rel, meta in sorted(files.items()):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            drift.append("%s: DA BIEN MAT khoi dia" % rel)
            continue
        h = hashlib.sha256()
        with open(p, "rb") as fh2:
            for chunk in iter(lambda: fh2.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != meta["sha256"]:
            drift.append("%s: sha256 DA DOI" % rel)
    assert not drift, "digest da ghim khong con khop:\n  %s" % "\n  ".join(drift)


def _scan() -> list[tuple[str, str]]:
    found = []
    for pattern in ("cert/*.py", "measurements/*.py", "tools/*.py"):
        for py in sorted(glob.glob(os.path.join(REPO, pattern))):
            rel_py = os.path.relpath(py, REPO).replace(os.sep, "/")
            for s in _string_constants(py):
                if not s.endswith(".parquet") or not _is_concrete_path(s):
                    continue
                if not os.path.exists(os.path.join(REPO, s)):
                    found.append((rel_py, s))
    return found


def test_no_hardcoded_missing_parquet():
    """Duong dan parquet CHET (hang so cung, file khong ton tai)."""
    bad = [
        (py, s)
        for py, s in _scan()
        if s not in KNOWN_DANGLING and s not in OUTPUT_PATHS
    ]
    assert not bad, (
        "duong dan parquet CHET (hang so cung, file khong ton tai):\n  %s\n"
        "  -> doi sang mau {mode}/{rho}, xoa neu da bo, hoac them vao "
        "KNOWN_DANGLING KEM LY DO va lesson so huu."
        % "\n  ".join("%s -> %s" % (py, s) for py, s in bad)
    )


def test_known_dangling_only_shrinks():
    """Muc nao trong KNOWN_DANGLING da duoc phuc hoi thi phai bi XOA khoi list.

    Danh sach no chet dan, khong phinh ra -- cung khuon voi `LEGACY_EXEMPT` va
    `KNOWN_DEAD`.
    """
    revived = sorted(
        s for s in KNOWN_DANGLING if os.path.exists(os.path.join(REPO, s))
    )
    assert not revived, (
        "parquet DA co lai tren dia nhung van nam trong KNOWN_DANGLING:\n  %s\n"
        "  -> xoa muc do (danh sach nay chi duoc NGAN DI)." % "\n  ".join(revived)
    )

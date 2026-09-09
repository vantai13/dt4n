"""Artifact khong duoc chua duong dan tuyet doi cua may da sinh ra no.

Ba ly do, khong phai mot (do duoc 2026-09-09 tren phase-20R2):

 1. TAI LAP. Lesson 20R2.3 doi doi chung GOLDEN bit-exact. Mot artifact chua
    "/home/<ai do>/..." cho DUNG MOI CON SO tren may khac nhung KHAC BYTE, nen
    no khong bao gio lam golden duoc -- no se do moi lan CI chay.
 2. RO THONG TIN. Ten nguoi dung va bo cuc thu muc di theo artifact vao thu se
    duoc cong bo.
 3. NHAT QUAN. `tools/20r2_0_axis_audit.py` da lam DUNG tu dau
    (os.path.relpath(..., REPO)); hai cong cu 20R2 moi thi khong -- do duoc
    2026-09-09, 3 truong lech khi chay lai tren may khac. Mot phase co hai quy
    uoc la mot phase chua co quy uoc nao.

HAI TANG, VI SAO KHONG PHAI MOT:

  TANG 1 (CHAN)     phase-20R2 -- phase dang mo. Bat ky duong dan tuyet doi nao
                    cung lam DO test. Day la noi quy uoc duoc thuc thi.
  TANG 2 (BANH COC) 39 artifact thua ke tu phase 20R / 23 / G2 / T2, DO DUOC
                    2026-09-09. Chung co truoc quy uoc nay. Ghim thanh DANH
                    SACH -- danh sach CHI DUOC NGAN DI: them mot tep moi vao se
                    lam do test `..._only_shrinks`.

Vi sao khong bat ca 39 do ngay: sua chung doi sinh lai artifact cua bon phase
khac, va 7 trong so do o LIVE/ (sha duoc trich dan noi khac) nen phai qua
amendment. Bien no thanh 39 dong do thuong truc chi lam ca bo test bi lo di --
dung loi "DO THUONG TRUC thi da chet" ma Phu luc B ghi.

Day la INVARIANT TEST: tang 1 khong ghim ten tep nao, chi ghim tinh chat
"khong co duong dan tuyet doi". Them artifact 20R2 moi thi test tu dong phu.
"""
import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# Tien to cho biet mot chuoi la duong dan tuyet doi cua MOT MAY CU THE.
ABSOLUTE_PREFIXES = ('/home/', '/Users/', '/root/', 'C:\\', '/mnt/c/')

# Phase dang mo: quy uoc duoc THUC THI o day.
ENFORCED_PREFIX = 'phase-20R2'

# Mien tru trong phase dang mo PHAI noi VI SAO. Mot allowlist khong giai thich
# la dung hinh dang PASS RONG ma test_no_stale_axes.py da canh bao.
GRANDFATHERED = {
    'SMOKE/phase-20R2/verification.json':
        'truong `python` ghi DUONG DAN INTERPRETER da chay -- do la provenance '
        'that (chay bang python nao), khong phai duong dan du lieu. Nam o SMOKE/ '
        'nen khong bao gio lam golden. Sinh lai truoc khi promote khoi SMOKE/.',
}

# No thua ke, DO DUOC 2026-09-09. CHI DUOC NGAN DI.
INHERITED_ABSOLUTE_PATHS = {
    'LIVE/phase-23/rho_grid_main.json',
    'LIVE/phase-23/rho_grid_sigma_fixed.json',
    'LIVE/phase-23/rho_grid_sigma_low.json',
    'LIVE/phase-23/sigma_rho_plane.json',
    'LIVE/phase-23/sla_exogenous_S-B.json',
    'LIVE/phase-23/sla_exogenous_S-B_ci.json',
    'LIVE/phase-23/sla_exogenous_wave4.json',
    'PENDING/phase-23/a_sweep.json',
    'PENDING/phase-23/sla_exogenous_S-A.json',
    'PENDING/phase-23/sla_exogenous_S-C.json',
    'PENDING/phase-23/t_loss_fine.json',
    'PENDING/phase-23/t_loss_local_fine.json',
    'PENDING/phase-23/t_loss_sweep.json',
    'PENDING/phase-23/w_loss_sensitivity.json',
    'PENDING/phase-T2/calib_p0925_tau10_report.json',
    'PENDING/phase-T2/calib_p0925_tau10_v3_report.json',
    'PENDING/phase-T2/conformal_u_cond.json',
    'PENDING/phase-T2/conformal_u_cond_load.json',
    'PENDING/phase-T2/conformal_u_main.json',
    'SMOKE/phase-20R/additivity_branch_a_state_bg.json',
    'SMOKE/phase-20R/additivity_branch_a_state_budgetfix_bg.json',
    'SMOKE/phase-20R/additivity_branch_a_state_inband_FAILED_race.json',
    'SMOKE/phase-20R/additivity_branch_a_state_inband_bg.json',
    'SMOKE/phase-20R/branch_b_fixed_pilot3.json',
    'SMOKE/phase-20R/branch_b_fixed_preflight120.json',
    'SMOKE/phase-20R/branch_b_tmux_preflight.json',
    'SMOKE/phase-20R/branch_b_tmux_preflight120.json',
    'SMOKE/phase-20R/branch_b_v2_smoke.json',
    'SMOKE/phase-20R/branch_c_fixed_pilot3.json',
    'SMOKE/phase-20R/branch_c_fixed_preflight120.json',
    'SMOKE/phase-20R/branch_c_tmux_preflight.json',
    'SMOKE/phase-20R/branch_c_tmux_preflight120.json',
    'SMOKE/phase-20R/branch_c_v2_smoke.json',
    'SMOKE/phase-20R/smoke_state.json',
    'SMOKE/phase-G2/g3b_continuation_review/verification.json',
    'SMOKE/phase-G2/g5c_monotone.json',
    'SMOKE/phase-G2/g_closeout_clean_clone.json',
    'SMOKE/phase-G2/g_closeout_custody_repair.json',
    'SMOKE/phase-G2/g_closeout_final_remote_verification.json',
}


def _artifacts():
    out = []
    for tier in ('LIVE', 'PENDING', 'SMOKE'):
        root = REPO / 'results' / tier
        if root.is_dir():
            out += sorted(root.rglob('*.json'))
    return out


def _rel(path: Path) -> str:
    return os.path.relpath(path, REPO / 'results').replace(os.sep, '/')


def _has_absolute(path: Path):
    try:
        blob = path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        return None
    return sorted({p for p in ABSOLUTE_PREFIXES if p in blob})


@pytest.mark.parametrize(
    'path', [p for p in _artifacts() if ENFORCED_PREFIX in _rel(p)], ids=_rel)
def test_phase_20r2_artifact_has_no_absolute_path(path):
    """TANG 1: phase dang mo -- chan tuyet doi."""
    rel = _rel(path)
    if rel in GRANDFATHERED:
        pytest.skip(GRANDFATHERED[rel])
    hits = _has_absolute(path)
    if hits is None:
        pytest.skip('khong doc duoc dang text')
    assert not hits, (
        rel + ': chua duong dan tuyet doi ' + repr(hits) + '.\n'
        '  -> ghi duong dan TUONG DOI voi goc repo '
        '(os.path.relpath(abspath(p), REPO)), nhu tools/20r2_0_axis_audit.py.\n'
        '  -> artifact chua duong dan tuyet doi KHONG tai lap bit-exact lien may,\n'
        '     nen khong dung lam golden cho 20R2.3 duoc.')


def test_inherited_absolute_path_debt_only_shrinks():
    """TANG 2: banh coc. No cu duoc phep ton tai; no MOI thi khong."""
    actual = {_rel(p) for p in _artifacts()
              if ENFORCED_PREFIX not in _rel(p) and _has_absolute(p)}
    new = sorted(actual - INHERITED_ABSOLUTE_PATHS)
    assert not new, (
        'artifact MOI mang duong dan tuyet doi (khong duoc phep):\n  '
        + '\n  '.join(new)
        + '\n-> ghi duong dan tuong doi voi goc repo khi sinh artifact.')
    fixed = sorted(INHERITED_ABSOLUTE_PATHS - actual)
    assert not fixed, (
        'TIN TOT: ' + str(len(fixed)) + ' tep da duoc sua. Xoa chung khoi '
        'INHERITED_ABSOLUTE_PATHS de banh coc siet lai:\n  ' + '\n  '.join(fixed))


def test_grandfather_list_only_names_files_that_exist():
    """Mot mien tru cho tep da bien mat la mot mien tru khong ai go -- no se
    am tham cho qua mot tep MOI trung ten sau nay."""
    for rel in GRANDFATHERED:
        assert (REPO / 'results' / rel).exists(), (
            rel + ': co trong danh sach mien tru nhung tep khong ton tai -> xoa dong do')

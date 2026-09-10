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
                    /!\ 39 la so TRONG PHAM VI ba tang, KHONG phai tong cay:
                    toan cay results/ co 100 tep mang duong dan tuyet doi, 60
                    trong so do nam o RAW/ va SUPERSEDED/ va bi loai CO CHU
                    DICH. Xem khoi PHAM VI ngay tren `_artifacts()`.

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


# PHAM VI CUA CAI CHAN NAY -- ba tang, va CHI ba tang.
#
# Do duoc 2026-09-10 tren toan cay results/ voi CHINH ABSOLUTE_PREFIXES duoi
# day: 100 tep JSON mang duong dan tuyet doi.
#
#     TRONG pham vi (LIVE/ PENDING/ SMOKE/)                40
#         SMOKE/phase-20R    15      PENDING/phase-23        7
#         LIVE/phase-23       7      PENDING/phase-T2        5
#         SMOKE/phase-G2      5      SMOKE/phase-20R2        1  <- GRANDFATHERED
#                                                          ----
#                              39 no thua ke  +  1 mien tru co ly do
#
#     NGOAI pham vi (KHONG ai canh)                        60
#         RAW/phase-23       37      SUPERSEDED/phase-21    14
#         SUPERSEDED/phase-20R 8     results/DATA_MANIFEST.json  1
#
# LOAI HAI TANG DUOI DAY LA CO CHU DICH, khong phai bo sot:
#   RAW/         log tho. Duong dan may O DAY LA PROVENANCE THAT (chay o dau),
#                khong phai duong dan du lieu. Sua chung la XOA bang chung.
#   SUPERSEDED/  da nghi huu, khong ai duoc trich dan. Sinh lai chung khong
#                mang lai gia tri nao ma lai lam trong chuoi custody.
#
# VI SAO PHAI GHI RA: khong ghi thi con so 39 trong docstring doc NHU LA TONG
# SO, trong khi no la tong so TRONG PHAM VI. Nguoi dem doc lap ra 100 va
# khong doi chieu duoc voi 39 -- do la mot khoang toi, va khoang toi trong
# mot cai chan la thu bien no thanh PASS RONG.
#
# /!\ PROMOTE mot tep tu RAW/ hoac SUPERSEDED/ len ba tang tren = no BUOC VAO
#     pham vi, va test_..._only_shrinks se do voi mot tep ma khong ai biet vi
#     sao no xuat hien. SINH LAI voi duong dan tuong doi TRUOC KHI promote.
IN_SCOPE_TIERS = ('LIVE', 'PENDING', 'SMOKE')
OUT_OF_SCOPE_TIERS = ('RAW', 'SUPERSEDED')


def _artifacts():
    out = []
    for tier in IN_SCOPE_TIERS:
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


def test_the_guard_declares_which_tiers_it_does_not_watch():
    """Mot cai chan phai noi ro no KHONG canh cai gi.

    Day khong phai test hinh thuc. `_artifacts()` quet ba tang; hai tang RAW/
    va SUPERSEDED/ bi loai CO CHU DICH. Neu ai do them mot tang moi vao
    results/ ma khong quyet dinh no thuoc ben nao, test nay do va bat ho
    quyet -- thay vi de tang moi roi vao khoang toi khong ai canh.
    """
    present = {p.name for p in (REPO / 'results').iterdir() if p.is_dir()}
    declared = set(IN_SCOPE_TIERS) | set(OUT_OF_SCOPE_TIERS)
    undecided = sorted(present - declared)
    assert not undecided, (
        'tang moi trong results/ chua duoc phan loai: ' + str(undecided)
        + '\n-> them vao IN_SCOPE_TIERS (duoc trich dan => phai sach) hoac '
        'OUT_OF_SCOPE_TIERS (log tho / da nghi huu), KEM LY DO.'
    )
    assert not (set(IN_SCOPE_TIERS) & set(OUT_OF_SCOPE_TIERS)), (
        'mot tang khong the vua trong vua ngoai pham vi')


def test_the_inherited_debt_list_is_the_in_scope_count_not_the_tree_count():
    """39 la con so TRONG PHAM VI. Ghim no de khoi doc nham thanh tong cay.

    Neu ai do mo rong pham vi sang RAW/ hoac SUPERSEDED/ ma quen cap nhat
    danh sach thua ke, test nay do TRUOC khi ca bo test ngap trong 60 loi do
    thuong truc -- dung loi "DO THUONG TRUC thi da chet" ma Phu luc B ghi.
    """
    assert len(INHERITED_ABSOLUTE_PATHS) == 39, (
        'danh sach no thua ke da doi kich thuoc: %d (ky la 39). '
        'Danh sach CHI DUOC NGAN DI.' % len(INHERITED_ABSOLUTE_PATHS))
    in_scope_hits = {_rel(p) for p in _artifacts() if _has_absolute(p)}
    assert len(in_scope_hits) == 40, (
        'so tep TRONG PHAM VI mang duong dan tuyet doi = %d (ky la 40 = 39 no '
        'thua ke + 1 mien tru SMOKE/phase-20R2). Neu con so nay TANG, mot '
        'artifact moi da mang duong dan tuyet doi vao.' % len(in_scope_hits))

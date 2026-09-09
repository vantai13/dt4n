"""20R2: kich thuoc luoi va ngan sach CPU phai SUY TU artifact, khong go tay.

Hai con so nay da tung sai cung chieu va nhan len 12 lan:
    (1) coi 1 LENH decision_error_v2 = 1 O   -- thuc te 1 lenh phu 10 o
    (2) coi luoi = 960 o                     -- thuc te 800 o, vi cbr@0.925 va
        cbr@0.960 co sigma_max_regime = 0 nen truc sigma SUP xuong mot diem
Tich 10 x 1.2 = 12.0, dung bang ty le lech giua 2.95 h va 14.7 phut moi nhanh.

Day la INVARIANT TEST chu khong phai VALUE TEST: no khong ghim "800", no ghim
QUAN HE giua bang kha thi, danh sach o trong report, va con so trong audit.
Doi mot tham so hop le (them mot tau, mot seed) thi value test chet, con test
nay van dung.
"""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CALIB = REPO / 'results/LIVE/phase-20R/sla_calibration.json'
AUDIT = REPO / 'results/PENDING/phase-20R2/axis_audit.json'
SWEEP = REPO / 'results/PENDING/phase-T2/sweep_r2'


def _calib():
    return json.loads(CALIB.read_text())


def _audit():
    return json.loads(AUDIT.read_text())['A7_cpu_budget']


def test_feasible_cells_are_ten_and_the_two_dropped_ones_have_zero_sigma():
    """Bang kha thi la NGUON, khong phai mot con so chep lai."""
    cells = _calib()['cells']
    infeasible = [c for c in cells if not c['feasible']]
    assert len(cells) == 12 and len(infeasible) == 2
    for c in infeasible:
        assert c['mode'] == 'cbr' and c.get('rho_bar') in (0.925, 0.96)
        # Ten truong THAT la `sigma_max` (va `sigma_rho`); chuoi
        # "sigma_max_regime" chi xuat hien trong van ban `reason`. Doc dung ten
        # truong, dung doc theo cau chu.
        assert c['sigma_max'] == 0 and c['sigma_rho'] == 0, (
            'o bi loai phai vi sigma_max = 0 (truc sigma = a*sigma_max SUP '
            'xuong mot diem), khong vi mot ly do khac')
        assert c['role'] == 'pc1_excluded_by_q8', (
            'chinh artifact hieu chuan da ghi vai tro loai tru cho o nay')
    assert _calib()['summary']['n_feasible'] == 12 - len(infeasible)


def test_the_166_reports_only_ever_used_the_feasible_cells():
    """Doi chung doc lap: harness xua nay VAN chi chay 10 o, khong phai 12."""
    feasible = {'%s@%.3f' % (c['mode'], c['rho_bar'])
                for c in _calib()['cells'] if c['feasible']}
    seen = {tuple(json.loads(p.read_text())['cells'])
            for p in sorted(SWEEP.glob('*_report.json'))}
    assert len(seen) == 1, 'cac report khong dung chung mot danh sach o: %r' % seen
    assert set(next(iter(seen))) == feasible


def test_audit_grid_size_is_derived_not_typed():
    grid = _audit()['grid']
    ax = grid['axes']
    assert grid['n_grid_cells'] == ax['mode_rho'] * ax['tau'] * ax['sigma_a'] * ax['seed']
    assert ax['mode_rho'] == _calib()['summary']['n_feasible']
    assert grid['n_grid_cells_if_all_mode_rho_used'] > grid['n_grid_cells'], (
        'neu hai so bang nhau thi bang kha thi da khong duoc tra cuu')


def test_one_command_covers_many_cells_not_one():
    """Sai so (1). Neu cells_per_command == 1 thi ngan sach cu da dung."""
    cov = _audit()['cells_per_command']
    assert cov, 'audit khong ghi cells_per_command -> khong ket luan duoc ngan sach'
    for label, entry in cov.items():
        assert entry['cell_lists_uniform'], label
        assert entry['cells_per_command'] > 1, (
            '%s: 1 lenh = 1 o la gia dinh da lam ngan sach sai 10 lan' % label)


def test_corrected_budget_is_consistent_and_far_below_the_old_estimate():
    entries = [v for v in _audit()['harness_seconds'].values() if 'corrected' in v]
    assert entries, 'khong harness nao co khoi `corrected`'
    for e in entries:
        c = e['corrected']
        assert c['grid_points_covered'] == c['n_cmd_non_canary'] * c['cells_per_command']
        assert c['seconds_per_cell'] == pytest.approx(
            c['total_seconds_non_canary'] / c['grid_points_covered'], rel=1e-12)
        assert c['minutes_two_branches'] == pytest.approx(2 * c['minutes_one_branch'], rel=1e-12)
        old_hours = e['superseded_hours_for_960_cells_1cmd_per_cell']
        ratio = (old_hours * 3600) / (c['minutes_one_branch'] * 60)
        assert ratio > 5, (
            'uoc tinh cu chi lech %.1fx -- neu gan 1 thi mot trong hai sai so '
            'da bien mat va tai lieu can doc lai' % ratio)
        assert c['minutes_two_branches'] < 8 * 60, (
            'ngan sach vuot tran 8 h -> ket luan "khong can fractional design" '
            'trong prereg §5.2 khong con dung')

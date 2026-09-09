#!/usr/bin/env python3
"""20R2.4 gate 4-2: is an inherited REALIZABLE verdict actually earned?

Run: python -m tools.20r2_4_realizability_audit --out results/PENDING/phase-20R2/realizability_audit.json

Mot verdict PASS chi co nghia khi biet BAO NHIEU tieu chi da THUC SU CHAY.
`failed == []` doc la "khong tieu chi nao TRUOT" -- nhung mot tieu chi KHONG
CHAY thi khong the truot, nen no cung khong the fail. Verdict xanh vi KHONG AI
HOI, khong phai vi DA TRA LOI. Do la `vacuous pass` (dat rong), cung lop loi ma
test_no_stale_axes.py canh bao.

Cong cu nay do `not_evaluated` tren tung o, va doi chieu cheo tieu chi
`sigma_feasible` voi bang kha thi that (sla_calibration.json) de dem CHINH XAC
bao nhieu o duoc gan REALIZABLE trong khi du lieu da co san noi rang khong.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import os

from measurements.validity import ROLE_AXIS_FREE

REPO = Path(__file__).resolve().parents[1]
GRID = Path('results/PENDING/phase-T2/realizability_grid.json')
CALIB = Path('results/LIVE/phase-20R/sla_calibration.json')


def rel(path) -> str:
    """Duong dan TUONG DOI voi goc repo, de ghi VAO artifact.

    Vi sao bat buoc: mot artifact chua "/home/<ai do>/..." khong tai lap
    bit-exact tren may khac, nen no khong bao gio lam GOLDEN duoc (20R2.3 doi
    bit-exact), va no ro bo cuc may vao thu se cong bo. `20r2_0_axis_audit.py`
    da lam dung tu dau (os.path.relpath(..., REPO)); hai cong cu nay thi khong
    -- do duoc 2026-09-09, 3 truong lech khi chay lai tren may khac.
    """
    return os.path.relpath(os.path.abspath(str(path)), REPO).replace(os.sep, '/')



def audit(grid_path: Path, calib_path: Path) -> dict:
    grid = json.loads(grid_path.read_text())
    rows = grid['rows']

    criteria = sorted({name for r in rows for name in r.get('checks', {})})
    per_criterion = {}
    for name in criteria:
        states = Counter()
        for r in rows:
            states[str(r['checks'].get(name, {}).get('pass'))] += 1
        per_criterion[name] = {
            'n_pass': states.get('True', 0),
            'n_fail': states.get('False', 0),
            'n_not_evaluated': states.get('None', 0),
            'evaluated_on_any_cell': states.get('None', 0) < len(rows),
        }

    never_run = sorted(n for n, v in per_criterion.items() if not v['evaluated_on_any_cell'])
    ne_patterns = Counter(tuple(sorted(r.get('not_evaluated', []))) for r in rows)

    # Doi chung cheo: sigma_feasible LE RA phai bat duoc nhung o co
    # sigma_max_regime = 0. Bang kha thi da co san tu truoc.
    calib = json.loads(calib_path.read_text())
    infeasible = {(c['mode'], c.get('rho_bar', c.get('rho')))
                  for c in calib['cells'] if not c['feasible']}
    mislabelled = [r for r in rows
                   if (r['cell']['mode'], r['cell']['rho_bar']) in infeasible
                   and r.get('verdict') == 'REALIZABLE']

    n_criteria = len(criteria)
    return {
        'schema': 'dt4n.realizability_audit.v1',
        'audit_kind': 'vacuous_pass_detection',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'source': rel(grid_path),
        'cross_checked_against': rel(calib_path),
        'headline_counts': {k: grid.get(k) for k in
                            ('n_cells', 'n_realizable', 'n_rejected', 'rejected_by_reason')},
        'n_rows': len(rows),
        'n_criteria': n_criteria,
        'per_criterion': per_criterion,
        'criteria_never_evaluated_on_any_cell': never_run,
        'n_criteria_never_evaluated': len(never_run),
        'not_evaluated_patterns': {', '.join(k) or '<none>': v for k, v in ne_patterns.items()},
        'all_cells_share_one_not_evaluated_pattern': len(ne_patterns) == 1,
        'verdict_counts': dict(Counter(r.get('verdict') for r in rows)),
        'cross_check_sigma_feasible': {
            'infeasible_mode_rho_per_calibration': sorted(map(list, infeasible)),
            'n_rows_marked_realizable_but_infeasible': len(mislabelled),
            'examples': [r['cell'] for r in mislabelled[:3]],
            'why': 'sigma = a * sigma_max; sigma_max = 0 lam truc sigma SUP xuong mot '
                   'diem, nen o do khong con la mot o cua thi nghiem. (Ten truong la '
                   '`sigma_max`; "sigma_max_regime" chi la van ban trong `reason`.)',
        },
        'validity': {
            'schema': 'dt4n.validity.v1',
            'axis_role': ROLE_AXIS_FREE,
            'aoi_axis': {
                'label': ROLE_AXIS_FREE,
                'note': 'audit so sach cua gate; khong dung truc tuoi z, khong goi bo sinh AoI nao',
            },
            'sla_axis': {
                'label': 'self_calibrated',
                'source_path': rel(CALIB),
                'source_sha256': hashlib.sha256((REPO / CALIB).read_bytes()).hexdigest(),
            },
            'pending_on': ['sla_axis'],
            'w_loss': None,
            'omega': None,
            'note': 'Bang kha thi doi chieu den tu sla_calibration.json (truc SLA '
                    'DEPRECATED, loi S14), nen ket luan kha thi cua audit nay cung '
                    'cho truc SLA duoc thay.',
        },
        'gate_4_2_not_evaluated_is_empty': not never_run,
        'verdict': ('VACUOUS_GREEN' if never_run else 'EARNED_GREEN'),
        'note': ('%d/%d tieu chi KHONG CHAY o BAT KY o nao; verdict xanh vi khong ai hoi. '
                 'KHONG ke thua ket luan kha thi cua T2.' % (len(never_run), n_criteria)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--grid', default=str(GRID))
    ap.add_argument('--calib', default=str(CALIB))
    args = ap.parse_args()
    payload = audit(REPO / args.grid, REPO / args.calib)
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + '\n')
    h = payload['headline_counts']
    print('tieu de artifact: n_cells=%s n_realizable=%s n_rejected=%s' % (
        h['n_cells'], h['n_realizable'], h['n_rejected']))
    print('tieu chi KHONG CHAY o moi o (%d/%d): %s' % (
        payload['n_criteria_never_evaluated'], payload['n_criteria'],
        ', '.join(payload['criteria_never_evaluated_on_any_cell'])))
    x = payload['cross_check_sigma_feasible']
    print('o duoc gan REALIZABLE nhung bang kha thi noi KHONG: %d' %
          x['n_rows_marked_realizable_but_infeasible'])
    print('gate 4-2 (not_evaluated == []): %s' % payload['gate_4_2_not_evaluated_is_empty'])
    print('verdict: %s' % payload['verdict'])
    print('-> %s' % out)


if __name__ == '__main__':
    main()

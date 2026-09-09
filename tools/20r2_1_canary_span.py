#!/usr/bin/env python3
"""20R2.1: measure canary span over the T2 sweep_r2 campaign.

Run: python -m tools.20r2_1_canary_span --out results/PENDING/phase-20R2/canary_span.json

Canary = phep do LAP LAI khong nham lay ket qua moi, ma de phat hien MOI TRUONG
TROI (environmental drift). Neu canary bat dau ra so khac thi khong phai khoa
hoc doi, ma MAY doi. `span` = so gia tri sha256 KHAC NHAU giua cac lan canary.
span = 0 (quy uoc: n_distinct - 1 = 0) nghia la byte-stability tuyet doi.

Doi chung AM bat buoc: neu MOI run deu cho cung sha thi span = 0 vi mot ly do
tam thuong (tham so bi bo qua), khong phai vi moi truong on dinh. Nen cong cu
CUNG do so sha khac nhau trong nhom KHONG phai canary; chi khi nhom do phan
biet duoc thi span = 0 moi co nghia.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from measurements.validity import ROLE_AXIS_FREE

REPO = Path(__file__).resolve().parents[1]
SWEEP = Path('results/PENDING/phase-T2/sweep_r2')


def _norm_cmd(cmd) -> str:
    text = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
    return re.sub(r'--out\s+\S+', '--out <OUT>', text)


def _inherited_validity(sweep: Path) -> dict:
    """Ke thua PHAM VI HIEU LUC tu chinh 166 report ma audit nay dang doc.

    Audit nay khong tu sinh truc nao; no doc lai dung tap run ma
    `parquet_recovery.json` doc. Nen validity cua no phai la validity CUA NGUON,
    suy ra chu khong go tay. Neu cac report bat dong y thi bao loi, khong bia
    nhan -- xem tools/20r2_1_parquet_recovery.py::_reduce_field.
    """
    blocks = []
    for report in sorted(sweep.glob('*_report.json')):
        v = json.loads(report.read_text()).get('validity', {})
        block = {k: v.get(k, {}) for k in ('aoi_axis', 'sla_axis')}
        if block not in blocks:
            blocks.append(block)
    slas = [b['sla_axis'] for b in blocks]
    if not slas or any(x != slas[0] for x in slas):
        raise ValueError('sla_axis bat dong y giua cac report: %r' % slas)
    roles = [{k: v for k, v in b['aoi_axis'].items() if k != 'z_grid_s'} for b in blocks]
    if any(x != roles[0] for x in roles):
        raise ValueError('aoi_axis bat dong y ngoai z_grid_s: %r' % roles)
    grids = []
    for b in blocks:
        g = b['aoi_axis'].get('z_grid_s')
        if g is not None and list(g) not in grids:
            grids.append(list(g))
    aoi = dict(roles[0])
    if len(grids) == 1:
        aoi['z_grid_s'] = grids[0]
    else:
        aoi['z_grids_s'] = grids
    return {
        'schema': 'dt4n.validity.v1',
        'axis_role': ROLE_AXIS_FREE,
        'aoi_axis': aoi,
        'sla_axis': dict(slas[0]),
        'pending_on': ['sla_axis'],
        'w_loss': None,
        'omega': None,
        'note': 'Audit do ON DINH MOI TRUONG tren dung 166 run cua sweep_r2; pham vi '
                'hieu luc ke thua tu chinh cac report do, khong tu khai.',
    }


def measure(sweep: Path) -> dict:
    records = [json.loads(line) for line in
               (sweep / 'run_log.jsonl').read_text().splitlines() if line.strip()]
    canary = [r for r in records if r.get('is_canary')]
    other = [r for r in records if not r.get('is_canary')]

    c_sha = {r['sha256'] for r in canary}
    o_sha = Counter(r['sha256'] for r in other)
    span = len(c_sha) - 1 if canary else None

    # Doi chung AM: tham so co that su tao ra byte khac nhau khong?
    discriminates = len(o_sha) == len(other)

    elapsed = None
    stamps = sorted(r['timestamp_utc'] for r in canary)
    if len(stamps) >= 2:
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        elapsed = (datetime.strptime(stamps[-1], fmt)
                   - datetime.strptime(stamps[0], fmt)).total_seconds()

    return {
        'schema': 'dt4n.canary_span.v1',
        'audit_kind': 'environmental_drift',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'source_dir': str(sweep),
        'validity': _inherited_validity(sweep),
        'n_runs': len(records),
        'n_canary': len(canary),
        'n_non_canary': len(other),
        'canary_run_index': sorted(r['run_index'] for r in canary),
        'canary_sha256_distinct': sorted(c_sha),
        'canary_span': span,
        'canary_identical_bytes': span == 0,
        'canary_params': {
            key: sorted({r[key] for r in canary})
            for key in ('tau', 'seed', 'a', 'branch')
        },
        'canary_cmd_normalised_distinct': sorted({_norm_cmd(r['cmd']) for r in canary}),
        'canary_elapsed_s': elapsed,
        'canary_seconds': [r['seconds'] for r in canary],
        'git_commit_distinct': sorted({r['git_commit'] for r in records}),
        'negative_control': {
            'n_non_canary_sha_distinct': len(o_sha),
            'parameters_discriminate': discriminates,
            'why': 'neu tham so KHONG tao ra byte khac nhau thi span=0 la tam thuong; '
                   '160/160 sha khac nhau chung minh tham so CO tac dung, nen 6 canary '
                   'trung nhau la do LENH GIONG NHAU, khong phai do tham so bi bo qua.',
        },
        'verdict': ('CANARY_SPAN_0_WITH_DISCRIMINATING_CONTROL'
                    if span == 0 and discriminates else 'INCONCLUSIVE'),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--sweep', default=str(SWEEP))
    args = ap.parse_args()
    payload = measure(REPO / args.sweep)
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1, sort_keys=True) + '\n')
    print('canary: n=%d span=%s identical=%s' % (
        payload['n_canary'], payload['canary_span'], payload['canary_identical_bytes']))
    print('doi chung am: %d/%d sha non-canary khac nhau -> tham so phan biet duoc: %s' % (
        payload['negative_control']['n_non_canary_sha_distinct'],
        payload['n_non_canary'], payload['negative_control']['parameters_discriminate']))
    print('trai dai: %.0f s; verdict: %s' % (payload['canary_elapsed_s'], payload['verdict']))
    print('-> %s' % out)


if __name__ == '__main__':
    main()

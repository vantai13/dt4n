#!/usr/bin/env python3
"""20R2.1: verify the 166 historical parquet files, without regenerating them.

Run: python -m tools.20r2_1_parquet_recovery --out results/PENDING/phase-20R2/parquet_recovery.json
SHA equality establishes integrity; it does not approve reuse on new axes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq
from measurements.validity import ROLE_AXIS_FREE

REPO = Path(__file__).resolve().parents[1]
SWEEP = Path('results/PENDING/phase-T2/sweep_r2')
EXPECTED_REPORTS = 166


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def audit(repo: Path = REPO) -> dict:
    rows = []
    source_axes = []
    for report_path in sorted((repo / SWEEP).glob('t2_6_r*_report.json')):
        rep = json.loads(report_path.read_text())
        rel, want = rep.get('parquet'), rep.get('parquet_sha256')
        path = (repo / rel).resolve() if rel else None
        row = dict(report=str(report_path.relative_to(repo)), parquet=rel,
                   sha_expected=want, sha_actual=None, bytes=0,
                   n_rows=rep.get('n_rows'), n_rows_actual=None)
        if path is not None and not path.is_relative_to((repo / SWEEP).resolve()):
            row['status'] = 'INVALID_PATH'
        elif path is None or not path.is_file():
            row['status'] = 'MISSING'
        else:
            row['bytes'] = path.stat().st_size
            row['sha_actual'] = sha256_file(path)
            if row['sha_actual'] != want:
                row['status'] = 'SHA_MISMATCH'
            else:
                try:
                    table = pq.read_table(path)  # Decode payload, not just footer.
                    row['n_rows_actual'] = table.num_rows
                    row['status'] = ('OK' if table.num_rows == row['n_rows']
                                     else 'ROW_COUNT_MISMATCH')
                except Exception as exc:
                    row['status'] = 'UNREADABLE'
                    row['error'] = str(exc)
        v = rep.get('validity', {})
        axes = {key: v.get(key, {}) for key in ('aoi_axis', 'sla_axis')}
        if axes not in source_axes:
            source_axes.append(axes)
        rows.append(row)
    counts = {s: sum(r['status'] == s for r in rows) for s in (
        'OK', 'MISSING', 'SHA_MISMATCH', 'ROW_COUNT_MISMATCH', 'UNREADABLE', 'INVALID_PATH')}
    total = sum(r['bytes'] for r in rows if r['status'] == 'OK')
    n_unique = len({r['parquet'] for r in rows if r['parquet']})
    summary = dict(n_reports=len(rows), expected_reports=EXPECTED_REPORTS,
                   n_ok=counts['OK'], n_missing=counts['MISSING'],
                   n_sha_mismatch=counts['SHA_MISMATCH'], status_counts=counts,
                   total_bytes_ok=total, total_mb_ok=round(total / 1e6, 6),
                   total_rows_reported=sum(r['n_rows'] or 0 for r in rows),
                   total_rows_read_ok=sum(r['n_rows_actual'] or 0 for r in rows if r['status'] == 'OK'),
                   n_unique_parquet_paths=n_unique,
                   gate_1_2_full_recovery=(len(rows) == EXPECTED_REPORTS
                                         and n_unique == EXPECTED_REPORTS
                                         and counts['OK'] == EXPECTED_REPORTS),
                   reusable_for_main_grid=False)
    # Inherit source scope, not an invented approval for new measurements.
    validity = {
        'schema': 'dt4n.validity.v1', 'axis_role': ROLE_AXIS_FREE,
        'aoi_axis': source_axes[0]['aoi_axis'] if len(source_axes) == 1 else {'label': 'MIXED_OR_MISSING'},
        'sla_axis': source_axes[0]['sla_axis'] if len(source_axes) == 1 else {'label': 'MIXED_OR_MISSING'},
        'pending_on': ['sla_axis'], 'w_loss': None, 'omega': None,
        'note': 'Source scope inherited from reports; this audit checks bytes and readability only. '
                'A5 proposes exogenous SLA; recovered self_calibrated outcomes cannot supply that grid.',
    }
    return dict(schema='dt4n.parquet_recovery.v1', audit_kind='artifact_integrity',
                generated_utc=datetime.now(timezone.utc).isoformat(),
                source_dir=str(SWEEP), scope='current checkout; original parquet bytes only',
                summary=summary, rows=rows, source_axes=source_axes, validity=validity)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', required=True)
    ap.add_argument('--sample-out', help='optional exact historical rows, not a new grid')
    args = ap.parse_args()
    payload = audit()
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + '\n')
    s = payload['summary']
    print('reports={n_reports} OK={n_ok} MISSING={n_missing} SHA_MISMATCH={n_sha_mismatch}'.format(**s))
    print('rows={total_rows_read_ok} bytes={total_bytes_ok} MB={total_mb_ok}'.format(**s))
    print('gate 1-2 (166/166):', 'PASS' if s['gate_1_2_full_recovery'] else 'FAIL')
    print('reuse for main grid: NO (SLA axis differs from A5)')
    print('->', out)
    if args.sample_out:
        if not s['gate_1_2_full_recovery']:
            raise SystemExit('sample export requires full verified recovery')
        import pandas as pd
        for row in payload['rows']:
            frame = pd.read_parquet(REPO / row['parquet'])
            sample = frame[(frame['mode'] == 'poisson') & (frame['rho_bar'] == .925)
                           & (frame['seed'] == 101) & (frame['tau_rho'] == .5)].copy()
            if sample.empty:
                continue
            sample['source_parquet'] = row['parquet']
            sample['aoi_axis'] = payload['validity']['aoi_axis']['label']
            sample['sla_axis'] = payload['validity']['sla_axis']['label']
            sample['scope'] = 'historical example; not reusable for A5 main grid'
            sample_out = REPO / args.sample_out
            sample_out.parent.mkdir(parents=True, exist_ok=True)
            sample.to_csv(sample_out, index=False)
            print('historical sample ->', sample_out)
            break
        else:
            raise SystemExit('requested historical sample not found')


if __name__ == '__main__':
    main()

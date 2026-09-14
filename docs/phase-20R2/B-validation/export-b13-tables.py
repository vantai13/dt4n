"""Readable exports from frozen S1/S3 results; no simulation or re-estimation."""
import csv
import io
import json
from pathlib import Path

base = Path('docs/phase-20R2')
s1 = json.loads((base/'B1-omega-sensitivity.json').read_text())
s3 = json.loads((base/'B3-axis-marginal.json').read_text())

def write(name, rows):
    f = io.StringIO(newline='')
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
    save(name, f.getvalue())

def save(name, text):
    path = base/'B-validation'/name
    if path.exists():
        assert path.read_bytes() == text.encode(), 'existing export differs'
    else:
        with path.open('x', newline='') as f:
            f.write(text)

write('S1-per-cell-tau.csv', [{k:v for k,v in r.items() if k not in ('by_omega','path_pair')}
    | {'path_pair': '-'.join(r['path_pair'])} for r in s1['rows']])
write('S3-per-cell-tau.csv', [
    {'cell':r['cell'], 'tau':r['tau'], 'a':r['a'], 'n_seeds':r['n_seeds']}
    | {axis+'_'+k:v for axis in ('legacy','measured') for k,v in r[axis].items()}
    | {'decomposition_'+k:v for k,v in r['decomposition'].items() if k!='reading'}
    for r in s3['rows']])

lines = ['| Ô | S1: ratio tại ω=.10, min–max qua 8 τ | Nhạy / 8 τ | S3: E_err legacy → measured tại τ=3 | Tỷ số trục |',
         '|---|---:|---:|---:|---:|']
for cell in sorted({r['cell'] for r in s1['rows']}):
    a = [r for r in s1['rows'] if r['cell']==cell]
    b = next(r for r in s3['rows'] if r['cell']==cell and r['tau']==3)
    lines.append(f"| {cell} | {min(r['ratio_ref'] for r in a):.6f}–{max(r['ratio_ref'] for r in a):.6f} | {sum(r['status']=='SENSITIVE' for r in a)}/8 | {b['legacy']['E_err']:.8f} → {b['measured']['E_err']:.8f} | {b['decomposition']['total']:.6f} |")
save('S1-S3-display.md', '\n'.join(lines)+'\n')
print('\n'.join(lines))
print('S3 shared control:', s3['shared_z_control'])
for axis in ('legacy','measured'):
    print(axis, 'max mass_outside=', max(r[axis]['mass_outside'] for r in s3['rows']),
        'max absolute available seed-mean relative Jensen gap=', max(abs(r[axis]['jensen_gap_relative']) for r in s3['rows'] if r[axis]['jensen_gap_relative'] is not None),
        'undefined relative gap rows=', [(r['cell'],r['tau']) for r in s3['rows'] if r[axis]['jensen_gap_relative'] is None])
print('S3 max absolute aggregate identity error=', max(abs(r['decomposition']['identity_error']) for r in s3['rows']))
print('S3 max absolute defined seed identity error=', max(abs(s['decomposition']['identity_error']) for r in s3['rows'] for s in r['seeds'] if 'identity_error' in s['decomposition']))
print('S3 undefined seed decomposition=', [(r['cell'],r['tau'],s['seed']) for r in s3['rows'] for s in r['seeds'] if 'identity_error' not in s['decomposition']])
print('SNR* at tau=3=', next(r['SNR_star'] for r in s1['rows'] if r['tau']==3))

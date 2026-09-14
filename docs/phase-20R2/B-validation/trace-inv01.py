"""Trace current G23-17c arithmetic; diagnose, never update published numbers."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd()))
from cert import phase23_cell_margins as CM

BASE = Path('docs/phase-20R2/B-validation')
OLD = Path('results/SUPERSEDED/phase-23/g23_17c_scale_and_sla.json')
old = json.loads(OLD.read_text())
current = CM.run_scale_sla_report(CM.DEFAULT_CELLS, rowset='test')
u = np.finfo(np.float64).eps / 2

def gamma(k):
    return k * u / (1 - k * u)

rows = []
for historical, now in zip(old['rows'], current['rows']):
    path = now['artifact']
    d = CM._select_rowset(pd.read_parquet(path), 'test')
    actions = d.a_twin.to_numpy(np.int64)
    x = CM.FB.loss_of(d, actions, 'regret')
    n = len(x)
    abs_mean = math.fsum(map(float, np.abs(x))) / n
    methods = {'numpy_mean': float(x.mean()),
               'numpy_reversed_mean': float(x[::-1].mean()),
               'python_sequential_sum_over_n': sum(map(float, x)) / n,
               'math_fsum_over_n': math.fsum(map(float, x)) / n}
    # Bound includes final division; assumes fixed exact binary64 input values,
    # round-to-nearest, no overflow/underflow, and the stated reduction tree.
    bounds = {name: (gamma(depth) + u * (1 + gamma(depth))) * abs_mean
              for name, depth in [('sequential', n-1), ('balanced_pairwise', math.ceil(math.log2(n)))]}
    err = now['err_neo']
    median = now['median_m_true_1']
    propagated = {}
    for name, b in bounds.items():
        # Conditional error budget for regret path only; err and median held
        # fixed. Each division adds its own rounding term.
        bp = b / err + u * (abs(now['regret_neo']) + b) / err
        bn = bp / median + u * (abs(now['penalty_per_error']) + bp) / median
        propagated[name] = {'penalty_error_budget': bp, 'normpen_error_budget': bn}
    rows.append({'cell': now['cell'], 'n': n,
        'historical_raw_sha256': historical['artifact_sha256'],
        'current_raw_sha256': now['artifact_sha256'],
        'same_raw_bytes': historical['artifact_sha256'] == now['artifact_sha256'],
        'regret_array_sha256': hashlib.sha256(np.asarray(x, dtype='<f8').tobytes()).hexdigest(),
        'chain': {'err_neo': err, 'regret_neo_methods': methods,
            'median_m_true_1': median, 'penalty_per_error': now['penalty_per_error'],
            'normpen_per_margin': now['normpen_per_margin'],
            'published_regret_neo': historical['regret_neo'],
            'published_regret_matches_current_method': [k for k,v in methods.items() if v == historical['regret_neo']]},
        'mean_absolute_error_bounds': bounds,
        'conditional_propagation_holding_err_and_median_fixed': propagated})

diff = json.loads(Path('docs/phase-20R2/A-validation/g23-17c-diff.json').read_text())
leaves = []
for pointer, (a, b) in diff['numeric_diff'].items():
    spacing = math.ulp(a)
    leaves.append({'field': pointer, 'published': a, 'current': b,
        'absolute_difference': abs(b-a), 'ulp_at_published_value': spacing,
        'difference_in_local_ulps': abs(b-a)/spacing,
        'note': 'A residual moving to zero has no useful relative-ULP interpretation.' if b == 0 else ''})

inputs = [str(OLD), 'docs/phase-20R2/A-validation/g23-17c-diff.json',
          'docs/phase-20R2/B0-reading-signed.md', *CM.DEFAULT_CELLS.values()]
sources = ['cert/phase23_cell_margins.py', 'cert/fallback.py', str(Path(__file__).relative_to(Path.cwd()))]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out = {'schema': 'dt4n.inv01.arithmetic_trace.v1', 'status': 'OPEN',
    'inputs_sha256': {p: sha(p) for p in inputs}, 'source_sha256': {p: sha(p) for p in sources},
    'validity': {'scope': 'diagnostic on current inputs, not historical bitwise reconstruction'},
    'unit_roundoff': float(u), 'epsilon': float(2*u),
    'operation_chain': [
        'filter is_calib == false, preserve row order',
        'FB.loss_of: select regret using current a_twin and true margins',
        'regret_neo = numpy.mean(regret_array); err_neo = numpy.mean(error_array)',
        'median = numpy.median(m_true_1)',
        'penalty = regret_neo / max(err_neo, 1e-12)',
        'normpen = penalty / max(median, 1e-12)',
        'normalize regret, err, median, normpen against poisson@0.925',
        'multiply err_ratio * normpen_ratio * median_ratio; subtract regret_ratio; abs'],
    'bounds_assumptions': 'Fixed binary64 inputs; no under/overflow; nearest rounding; sequential depth n-1 or balanced pairwise depth ceil(log2(n)). Actual NumPy tree is not established here. Bounds concern arithmetic only, not changed input, RNG, or sampling error.',
    'formula': '(gamma_k + u*(1+gamma_k))*sum(abs(x))/n, gamma_k=k*u/(1-k*u)',
    'tolerance_policy': 'No test tolerance is changed. A fieldwise tolerance needs historical-input reconstruction and a complete operation/denominator budget; sqrt(n)*epsilon is not a deterministic pairwise bound.',
    'keep_zero_tolerance': ['RNG stream and action identities under a pinned environment',
        'S2 original fields with sla_grid=None vs pre-patch code',
        'S2 signed-threshold identity at identical samples',
        'S3 shared-z identities at matching cell/tau/seed', 'Frozen file digests'],
    'rows': rows, 'changed_leaves': leaves,
    'conclusion': 'Different reduction orders can produce drift of this scale. They do not establish the historical cause: poisson@0.925 has a different raw digest. INV-01 remains open.'}
with (BASE/'INV01-floating-point-trace.json').open('x') as f:
    json.dump(out, f, indent=2, allow_nan=False)
    f.write('\n')
for row in rows:
    print(row['cell'], 'n=', row['n'], row['chain'], row['mean_absolute_error_bounds'])
print('INV-01 OPEN; exact regression test unchanged')

"""Controlled diagnostic: change only current regret reduction to fsum/n."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd()))
from cert import phase23_cell_margins as CM

original = CM.cell_scale_sla_row

def fsum_row(cell, path, rowset='test'):
    row = original(cell, path, rowset)
    d = CM._select_rowset(pd.read_parquet(path), rowset)
    loss = CM.FB.loss_of(d, d.a_twin.to_numpy(np.int64), 'regret')
    row['regret_neo'] = math.fsum(map(float, loss)) / len(loss)
    row['penalty_per_error'] = row['regret_neo'] / max(row['err_neo'], 1e-12)
    row['normpen_per_margin'] = row['penalty_per_error'] / max(row['median_m_true_1'], 1e-12)
    return row

try:
    CM.cell_scale_sla_row = fsum_row
    alternative = CM.run_scale_sla_report(CM.DEFAULT_CELLS, rowset='test')
finally:
    CM.cell_scale_sla_row = original

base = Path('docs/phase-20R2')
diff_path = base/'A-validation/g23-17c-diff.json'
diff = json.loads(diff_path.read_text())
leaves = []
for pointer, (published, current) in diff['numeric_diff'].items():
    _, _, index, key = pointer.split('/')
    alt = alternative['rows'][int(index)][key]
    leaves.append({'field': pointer, 'published': published, 'numpy_current': current,
                   'fsum_diagnostic': alt, 'matches_published_exactly': alt == published})
inputs = [str(diff_path), *CM.DEFAULT_CELLS.values()]
sources = ['cert/phase23_cell_margins.py', 'cert/fallback.py', str(Path(__file__).relative_to(Path.cwd()))]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
out = {'schema': 'dt4n.inv01.reduction_propagation.v1', 'status': 'OPEN',
    'inputs_sha256': {p: sha(p) for p in inputs}, 'source_sha256': {p: sha(p) for p in sources},
    'validity': {'scope': 'controlled arithmetic diagnostic on current inputs'},
    'intervention': 'Only regret reduction changed to math.fsum/n in this isolated diagnostic process; dependent fields use unchanged production arithmetic. Source files and tests are unchanged.',
    'changed_leaves': leaves, 'n_matches': sum(x['matches_published_exactly'] for x in leaves),
    'n_previously_changed_leaves': len(leaves),
    'conclusion': 'Reproducing published values this way demonstrates a sufficient numerical explanation, not evidence of the historical reduction algorithm or unchanged historical input.'}
with (base/'B-validation/INV01-reduction-propagation.json').open('x') as f:
    json.dump(out, f, indent=2, allow_nan=False)
    f.write('\n')
print(json.dumps(out, indent=2))

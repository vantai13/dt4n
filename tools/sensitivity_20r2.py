"""Shared provenance and fixed constants for the signed 20R2.9-B replication."""
from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
from measurements.validity import sla_only_validity_block

ROOT = pathlib.Path(__file__).resolve().parents[1]
READING = 'docs/phase-20R2/B0-reading-signed.md'
READING_TAG = 'phase-20R2-B-reading-signed'
EXO = 'results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json'
PRED = 'docs/phase-20R2/01-prediction-signed.json'
OLD_PLAN = 'docs/phase-20R2/03-run-plan.json'
OLD_LOG = 'docs/phase-20R2/04-campaign-log.jsonl'
TAUS = (.5, 1., 2., 3., 5., 10., 20., 28.)
SEEDS = (101, 102, 103, 104, 105)
TD = (14., 18., 22., 26., 30., 35., 40., 45., 50.)
TL = (.00002, .00005, .0001, .0005, .002, .005, .01, .02, .05, .10, .15, .20)
GRID = tuple((d, l) for d in TD for l in TL)
S2_DIR = 'results/PENDING/phase-20R2-B/S2'

def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def read(path):
    return json.loads((ROOT/path).read_text())

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def require_reading():
    raw = subprocess.check_output(['git', 'show', READING_TAG+':'+READING], cwd=ROOT)
    assert raw == (ROOT/READING).read_bytes(), 'reading differs from signed version'
    return git('rev-parse', READING_TAG+'^{commit}')

def provenance(module, inputs, z_grid):
    require_reading()
    paths = sorted(set([READING, EXO, *inputs]))
    sources = sorted(set([module, 'tools/sensitivity_20r2.py',
                          'measurements/validity.py']))
    return {'generated_by': module, 'reading_tag': READING_TAG,
            'reading_commit': require_reading(),
            'inputs_sha256': {p: sha(p) for p in paths},
            'source_sha256': {p: sha(p) for p in sources},
            'validity': sla_only_validity_block(sla_path=str(ROOT/EXO), w_loss=5000.,
                z_grid=z_grid, note='Exploratory sensitivity under B0; does not revise the signed 5/8 decision.')}

def write(path, doc):
    p = ROOT/path
    p.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite an existing scientific artifact with a new run.
    with p.open('x') as f:
        f.write(json.dumps(doc, indent=2, sort_keys=True, allow_nan=False)+'\n')

def campaign(a=.9):
    plan = read(OLD_PLAN)
    log = [json.loads(x) for x in (ROOT/OLD_LOG).read_text().splitlines()]
    done = {r['run_index']: r for r in log if r.get('kind')=='run' and r.get('returncode')==0}
    runs = [r for r in plan['runs'] if not r['is_canary'] and r['a']==a]
    for r in runs:
        e = done[r['run_index']]
        assert sha(r['out']) == e['sha256'], 'campaign parquet hash differs'
        assert sha(e['sidecar']) == e['sidecar_sha256'], 'campaign sidecar hash differs'
    return runs

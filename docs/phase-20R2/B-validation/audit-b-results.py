"""Verify B provenance, signed tags, complete campaign and pre-B preservation."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path.cwd()
BASE = '1de19e1cbbf47951e4b718e7100777848c0eab3c'
CLOSED = '042c58f4dd20dc6f7b78cdfe7f3473a6e3745ffb'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
git = lambda *a: subprocess.check_output(['git', *a], text=True).strip()

def audit():
    changed = git('diff', '--name-status', '--diff-filter=DMRTUXB', BASE, '--',
                  'docs/phase-20R2', 'results')
    assert not changed, 'pre-B evidence changed: '+changed
    assert git('rev-parse','phase-20R2-closed^{commit}') == CLOSED
    signed = {}
    for tag, path in [
        ('phase-20R2-B-reading-signed','docs/phase-20R2/B0-reading-signed.md'),
        ('phase-20R2-B2-plan-signed','docs/phase-20R2/B2-run-plan.json')]:
        commit = git('rev-parse',tag+'^{commit}')
        remote = git('ls-remote','--tags','origin',tag+'^{}').split()[0]
        assert remote == commit
        raw = subprocess.check_output(['git','show',tag+':'+path])
        assert raw == Path(path).read_bytes()
        signed[tag] = {'commit':commit,'remote_commit':remote,'file':path,'sha256':sha(path)}

    artifacts = []
    paths = sorted(Path('docs/phase-20R2').glob('B*.json'))
    paths += sorted(Path('results/PENDING/phase-20R2-B/S2').glob('*_report.json'))
    assert len([p for p in paths if p.name.endswith('_report.json')]) == 320
    for path in paths:
        d = json.loads(path.read_text())
        assert d.get('validity') and d.get('inputs_sha256') and d.get('source_sha256')
        for p, wanted in d['inputs_sha256'].items():
            assert sha(p) == wanted, f'{path}: changed input {p}'
        source_versions = {}
        for p, wanted in d['source_sha256'].items():
            if sha(p) == wanted:
                source_versions[p] = 'current bytes'
            else:
                # S1 was deliberately run before the signed S2 production patch.
                assert path.name == 'B1-omega-sensitivity.json' and p == 'measurements/decision_error_v2.py'
                first = git('log','--diff-filter=A','--format=%H','--',str(path)).splitlines()[-1]
                historical = subprocess.check_output(['git','show',first+':'+p])
                assert hashlib.sha256(historical).hexdigest() == wanted
                source_versions[p] = first
        if d.get('parquet') and d.get('parquet_sha256'):
            assert sha(d['parquet']) == d['parquet_sha256']
        artifacts.append({'artifact':str(path),'sha256':sha(path),
            'input_count':len(d['inputs_sha256']),'source_versions':source_versions})

    summary_path = Path('docs/phase-20R2/B2-sla-threshold-map.json')
    summary = json.loads(summary_path.read_text())
    assert summary['n_runs']==320 and summary['n_raw_rows']==449280
    assert summary['n_seed_mean_rows']==89856
    assert sha(summary['table']) == summary['table_sha256']
    for p,want in summary['figures'].items(): assert sha(p) == want
    ledger = [json.loads(x) for x in Path('docs/phase-20R2/B2-campaign-log.jsonl').read_text().splitlines()]
    completions = [r for r in ledger if r['kind']=='run']
    assert len(completions)==320 and all(r['returncode']==0 for r in completions)
    assert all(r['git_commit']==signed['phase-20R2-B2-plan-signed']['commit'] for r in completions)
    assert all(sha(r['out'])==r['sha256'] and sha(r['sidecar'])==r['sidecar_sha256'] for r in completions)
    previous_files = git('ls-tree','-r','--name-only',BASE,'--','docs/phase-20R2','results').splitlines()
    return {'schema':'dt4n.b.provenance_and_preservation.v1','status':'PASS',
        'baseline_before_B':BASE,'original_closed_tag_commit':CLOSED,
        'pre_B_scientific_files_checked':len(previous_files),
        'pre_B_modified_or_deleted_scientific_files':[], 'signed_tags':signed,
        'artifacts':artifacts,'n_completed_runs':len(completions),
        'summary_controls':summary['controls'],
        'scope':'B raw/report/input/source/plan/figure integrity and preservation; does not close inherited scientific gates or INV-01.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    report=audit()
    with Path(args.out).open('x') as f:
        json.dump(report,f,indent=2,allow_nan=False)
        f.write('\n')
    print('PASS',report['pre_B_scientific_files_checked'],'pre-B files;',
          len(report['artifacts']),'B artifacts;',report['n_completed_runs'],'completed runs')

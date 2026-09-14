#!/usr/bin/env python3
"""S2 execution reuses the campaign runner's fsynced ledger and guard infrastructure."""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import importlib
import json
import pathlib
import subprocess
import sys
import time
from tools import sensitivity_20r2 as C

LEGACY=importlib.import_module('tools.20r2_5_run')
TAG='phase-20R2-B2-plan-signed'
PLAN='docs/phase-20R2/B2-run-plan.json'
LOG='docs/phase-20R2/B2-campaign-log.jsonl'
INSTRUMENT=('measurements','twin','cert','tools','test',C.READING,PLAN)
OWNED=(':(exclude)'+C.S2_DIR,':(exclude)'+LOG,
       ':(exclude)docs/phase-20R2/B-validation')

@contextlib.contextmanager
def backend():
    replacements={'PLAN':C.ROOT/PLAN,'LOG':C.ROOT/LOG,'TAG':TAG,
                  'INSTRUMENT':INSTRUMENT,'CAMPAIGN_OWNED':OWNED}
    previous={k:getattr(LEGACY,k) for k in replacements}
    try:
        for k,v in replacements.items():setattr(LEGACY,k,v)
        yield LEGACY
    finally:
        for k,v in previous.items():setattr(LEGACY,k,v)

def guard():
    with backend() as b:
        b.guard()  # inherited missing-local-tag, missing-remote-tag, dirty, changed-instrument gates
        signed=b._git('rev-parse',TAG+'^{commit}')
        remote=b._git('ls-remote','--tags','origin',TAG+'^{}')
        if not remote or remote.split()[0]!=signed:
            raise SystemExit('DUNG: remote signed tag target differs')
        if b._git('rev-parse','HEAD')!=signed:
            raise SystemExit('DUNG: run must start at the exact signed plan commit')
    doc=C.read(PLAN)
    for path,want in doc['inputs_sha256'].items():
        if C.sha(path)!=want:raise SystemExit('DUNG: plan input changed: '+path)
    C.require_reading()

def verify_completed(run,entry):
    p=C.ROOT/run['out'];side=LEGACY.sidecar_of(p)
    if LEGACY._sha(p)!=entry['sha256'] or LEGACY._sha(side)!=entry['sidecar_sha256']:
        raise SystemExit('DUNG: completed output differs from ledger: '+run['out'])

def quarantine_orphans(run,b):
    for p in (C.ROOT/run['out'],LEGACY.sidecar_of(C.ROOT/run['out'])):
        if p.exists():
            dest=C.ROOT/'docs/phase-20R2/B-validation/orphans'/str(time.time_ns())/p.name
            dest.parent.mkdir(parents=True,exist_ok=True)
            b.append_log({'kind':'orphan_quarantine','out':run['out'],'path':str(p.relative_to(C.ROOT)),
                'sha256':LEGACY._sha(p),'moved_to':str(dest.relative_to(C.ROOT)),'timestamp_utc':b._now()})
            p.rename(dest)

def execute(plan):
    with backend() as b:
        fp={**b.env_fingerprint(),'guard_skipped':False,'plan_sha256':C.sha(PLAN)}
        log=b.read_log();envs=[x for x in log if x['kind']=='env']
        if envs:
            previous={k:v for k,v in envs[0].items() if k not in ('kind','timestamp_utc')}
            if previous!=fp:raise SystemExit('DUNG: environment/commit changed since previous session')
        else:b.append_log({'kind':'env',**fp,'timestamp_utc':b._now()})
        done={x['run_index']:x for x in log if x['kind']=='run' and x['returncode']==0}
        for r in plan['runs']:
            if r['run_index'] in done:
                verify_completed(r,done[r['run_index']]);continue
            quarantine_orphans(r,b)
            b.append_log({'kind':'run_start','run_index':r['run_index'],'cmd':r['cmd'],
                          'out':r['out'],'timestamp_utc':b._now(),'git_commit':fp['git_commit']})
            t=time.monotonic()
            proc=subprocess.run([sys.executable,*r['cmd']],cwd=C.ROOT,capture_output=True,text=True)
            p=C.ROOT/r['out'];side=LEGACY.sidecar_of(p)
            ok=proc.returncode==0 and p.is_file() and side.is_file()
            entry={'kind':'run',**r,'returncode':proc.returncode if not (proc.returncode==0 and not ok) else -2,
                'seconds':time.monotonic()-t,'sha256':b._sha(p),'sidecar_sha256':b._sha(side),
                'sidecar':str(side.relative_to(C.ROOT)),'git_commit':fp['git_commit'],
                'timestamp_utc':b._now(),'stderr_tail':b._clean(proc.stderr[-2000:])}
            b.append_log(entry)
            print(f"[{r['run_index']+1}/320] {r['cell']} tau={r['tau']} seed={r['seed']} {entry['seconds']:.2f}s {'ok' if ok else 'FAIL'}",flush=True)
            if not ok:raise SystemExit('DUNG: worker failed; see fsynced ledger')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plan',required=True)
    ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
    if a.plan!=PLAN:raise SystemExit('DUNG: plan path must be the signed canonical path')
    plan=C.read(a.plan)
    if a.dry_run:
        print('320 sequential calls, 449280 threshold rows; no execution');return 0
    lock=C.ROOT/'docs/phase-20R2/B-validation/S2-run.lock';lock.parent.mkdir(parents=True,exist_ok=True)
    with lock.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        guard();execute(plan)
    return 0
if __name__=='__main__':raise SystemExit(main())

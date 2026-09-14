#!/usr/bin/env python3
"""Recompute T2 round-1 hygiene and gate-v1 grid using their historical design."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, subprocess
import numpy as np
import pandas as pd
from measurements.legacy_pending_validity import pending_validity
ROOT=pathlib.Path(__file__).resolve().parents[1]
GATE_REF='576e360f'

def hygiene():
    log=[json.loads(x) for x in (ROOT/'results/PENDING/phase-T2/sweep/run_log.jsonl').read_text().splitlines()]
    assert len(log)==166 and all(e['returncode']==0 for e in log)
    for e in log:assert hashlib.sha256((ROOT/e['out']).read_bytes()).hexdigest()==e['sha256']
    frames=[pd.read_parquet(ROOT/e['out']) for e in log];d=pd.concat(frames,ignore_index=True)
    can=[(e,f) for e,f in zip(log,frames) if e['is_canary']];cols=can[0][1].select_dtypes('number').columns
    span=max(float(np.ptp(np.array([f[c].to_numpy() for e,f in can]),axis=0).max()) for c in cols)
    clips=d.groupby(['mode','rho_bar','tau_rho']).clip_fraction_max.max()
    s=d[(d.tau_rho==1.) & (d.z_s.round(6)==.1)]
    g=s.groupby(['mode','rho_bar','sigma_rho','seed']).err_total.agg(['min','max'])
    relative=(g['max']-g['min'])/g['min']
    out={'phase':'T2.6 luot 1 -- KIEM VE SINH, chay TRUOC khi doc err(tau)',
         'signed_tag':'phase-T2-prereg-signed','minutes':round(sum(e['seconds'] for e in log)/60,1),
         'n_commands':len(log),'n_ok':sum(e['returncode']==0 for e in log),'n_rows':len(d),
         'KIEM_1_canary_NC_T2_4':{'n_canary':len(can),'n_distinct_sha256':len({e['sha256'] for e,f in can}),
             'max_span_any_numeric_column':span,'verdict':'PASS' if span==0 else 'FAIL'},
         'KIEM_2_clip_V_T2_3':{'max_clip':float(clips.max()),'n_cells':len(clips),
             'n_cells_violating':int((clips>.01).sum()),'prereg_R5_claimed':.0009,
             'ratio_vs_claim':float(clips.max()/.0009),'threshold':.01,
             'verdict':'FAIL' if (clips>.01).any() else 'PASS',
             'worst':{str(tuple(float(v) if isinstance(v,(np.floating,)) else v for v in k)):float(v)
                      for k,v in clips.sort_values(ascending=False).head(5).items()}},
         'KIEM_3_branch_join_NC_T2_2':{'max_rel_span':float(relative.max()),'n_groups':len(g),
             'n_groups_violating':int((relative>.01).sum()),'threshold':.01,
             'verdict':'FAIL' if (relative>.01).any() else 'PASS',
             'mechanical_cause':'measurements/decision_error_v2.py:418 -- common_start = max(z_s)/dt, nen CUA SO CHAM DIEM phu thuoc z LON NHAT cua lan chay. fixed dung Z_ALL (max 4.0s -> hang 800); scaled tai tau=1.0 max 1.0s -> hang 200. Hai nhanh cham diem tren HAI DAI HANG KHAC NHAU.'}}
    return out

def grid():
    # Read the actual v1 implementation; do not reinterpret a v1 verdict using v2.
    source=subprocess.check_output(['git','show',GATE_REF+':cert/realizability_gate.py'],cwd=ROOT)
    scope={};exec(compile(source,'historical/realizability_gate_v1.py','exec'),scope)
    cells=[dict(mode=mode,rho_bar=rho,tau=tau,dt=.005,n=max(200000,int(50*tau/.005)))
           for tau in (.5,1.,2.,3.,5.,10.,20.,28.)
           for mode in ('poisson','h2','cbr') for rho in (.7,.85,.925,.96)]
    return scope['gate_grid'](cells)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kind',choices=['hygiene','grid'],required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args();out=hygiene() if a.kind=='hygiene' else grid()
    out['validity']=pending_validity('historical_'+a.kind,
        'Historical T2 fixed/scaled age choices or a pre-screen with no age axis; '
        'not an approved measured-v7 AoI certificate. Retain in PENDING until the '
        'corresponding age/certificate axis is specified and reviewed.')
    if a.kind=='grid':
        out['validity']['historical_gate_ref']=GATE_REF
        out['validity']['strict_reading']={'n_incomplete':sum(bool(r['not_evaluated']) for r in out['rows']),
                                          'note':'The 96 legacy REALIZABLE labels do not certify completeness.'}
    p=ROOT/a.out;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('->',a.out)
    return 0
if __name__=='__main__':raise SystemExit(main())

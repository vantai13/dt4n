#!/usr/bin/env python3
"""Execute one signed S2 cell; verify old per-z values before accepting output."""
from __future__ import annotations
import argparse
import json
import resource
import time
import pandas as pd
from tools import sensitivity_20r2 as C
from measurements import decision_error_v2 as DE

def produce(run,plan_path):
    start=time.monotonic()
    cells=DE.feasible_cells(C.EXO,include_pc1=False)
    cell=next(c for c in cells if c['mode']==run['mode'] and float(c['rho_bar'])==run['rho_bar'])
    assert (cell['t_delay_ms'],cell['t_loss'],cell['w_loss'])==(50.,.01,5000.)
    tt=DE.TruthTable(DE.TRUTH_TABLE)
    cv=DE.C.CostV2(fit_path='results/LIVE/phase-L/link_model_v2_fit.json',strict_reliable=False)
    zs=tuple(C.read(plan_path)['grid']['z_values'])
    result=DE.run_cell(tt,cv,cell,seed=run['seed'],tau=run['tau'],n=run['n'],dt=.005,
                       z_values=zs,a_override=.9,sla_grid=C.GRID)
    original=pd.read_parquet(C.ROOT/run['original_parquet'])
    original=original[(original['mode']==run['mode']) & (original['rho_bar']==run['rho_bar'])]
    assert len(original)==13 and original['seed'].unique().tolist()==[run['seed']]
    compared=[]
    for z,row in result['per_z'].items():
        match=original[original['z_s']==row['z_s']]
        assert len(match)==1
        for key,value in row.items():
            if key in match.columns:
                assert value==match.iloc[0][key], f'old campaign field differs: {key}, z={z}'
                compared.append(key)
    grid=result.pop('sla_grid'); identity=[]
    for r in grid:
        if (r['t_delay_ms'],r['t_loss'])==(50.,.01):
            difference=r['d_sla_at_threshold']-result['per_z'][DE.z_key(r['z_s'])]['d_sla']
            assert difference==0, 'SLA identity control failed'
            identity.append(difference)
        r.update(cell=run['cell'],mode=run['mode'],rho_bar=run['rho_bar'],tau=run['tau'],seed=run['seed'],a=.9)
    assert len(grid)==1404 and len(identity)==13
    out=C.ROOT/run['out'];side=out.with_name(out.stem+'_report.json')
    assert not out.exists() and not side.exists(), 'worker refuses to overwrite evidence'
    out.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(grid).to_parquet(out,index=False)
    report={**C.provenance('tools/20r2_9_s2_worker.py',[plan_path,run['original_parquet'],
        DE.TRUTH_TABLE,'results/LIVE/phase-L/link_model_v2_fit.json'],zs),
        'schema':'dt4n.s2_cell.v1','run_index':run['run_index'],'cell':run['cell'],
        'tau':run['tau'],'seed':run['seed'],'n':run['n'],'n_rows':len(grid),
        'parquet_sha256':C.sha(run['out']), 'per_z':result['per_z'],
        'controls':{'original_campaign_fields_exact':True,'fields_compared':sorted(set(compared)),
                    'signed_threshold_identity_max_abs_diff':max(identity),'n_identity_rows':len(identity)},
        'seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    report['validity']['decision_cost_sla_axis']=report['validity']['sla_axis']
    report['validity']['sla_axis']={'label':'UNREGISTERED','note':'Fixed sensitivity threshold grid, not an approved operating SLA. Cost/action selection still uses the signed exogenous manifest.',
        'T_delay_ms':list(C.TD),'T_loss':list(C.TL),'reading_sha256':C.sha(C.READING)}
    report['validity']['pending_on']=['sla_axis']
    report['source_sha256']['measurements/decision_error_v2.py']=C.sha('measurements/decision_error_v2.py')
    C.write(str(side.relative_to(C.ROOT)),report)
    print(run['cell'],run['tau'],run['seed'],'rows',len(grid),'identity=0','old fields exact')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--plan',required=True);ap.add_argument('--run-index',required=True,type=int)
    a=ap.parse_args();plan=C.read(a.plan);run=plan['runs'][a.run_index]
    assert run['run_index']==a.run_index
    produce(run,a.plan);return 0
if __name__=='__main__':raise SystemExit(main())

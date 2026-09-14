#!/usr/bin/env python3
"""S3: integrate seed-specific err(z) over the actual scalar age generators."""
from __future__ import annotations
import argparse
import numpy as np
import pandas as pd
from tools import sensitivity_20r2 as C
from measurements.validity import aoi_axis

def age_distributions(n=1000000,dt=.005):
    from measurements.decision_error import sawtooth_age_steps
    from measurements.aoi_model_v7 import AoIModelV7
    generators={'legacy':sawtooth_age_steps,'measured':AoIModelV7().base_age_steps}
    result={}
    for name,fn in generators.items():
        values=fn(n,dt)*dt; levels,counts=np.unique(values,return_counts=True)
        result[name]={'levels':levels.tolist(),'weights':(counts/n).tolist(),
            'mean_s':float(values.mean()),'cv':float(values.std()/values.mean()),
            'support_s':[float(values.min()),float(values.max())],
            'generator':aoi_axis(fn),'n_age':n,'dt':dt}
    return result

def integrate(levels,weights,zs,errs):
    lv,w,z,e=map(lambda x:np.asarray(x,float),(levels,weights,zs,errs))
    if len(z)<2 or np.any(np.diff(z)<=0) or not np.all(np.isfinite(e)):
        raise ValueError('curve must be finite and strictly ordered')
    if len(lv)!=len(w) or np.any(w<0) or not np.isclose(w.sum(),1,rtol=0,atol=1e-12):
        raise ValueError('invalid age probabilities')
    inside=(lv>=z[0]-1e-12)&(lv<=z[-1]+1e-12); mass=float(w[~inside].sum())
    partial=float(np.dot(w[inside],np.interp(lv[inside],z,e))); mean=float(np.dot(lv,w))
    at_mean=float(np.interp(mean,z,e)) if z[0]<=mean<=z[-1] else None
    full=partial if mass==0 else None
    status='READABLE' if mass==0 and at_mean is not None else ('PARTIAL_BOUNDED' if mass<=.01 and at_mean is not None else 'UNREADABLE')
    gap=full-at_mean if full is not None and at_mean is not None else None
    return {'E_err':full,'err_at_E_Z':at_mean,'E_Z':mean,'jensen_gap':gap,
        'jensen_gap_relative':gap/at_mean if gap is not None and at_mean else None,
        'mass_outside':mass,'in_domain_integral':partial,'E_err_bounds':[partial,partial+mass],
        'status':status}

def decompose(leg,mea):
    if any(x[k] is None or x[k]<=0 for x in (leg,mea) for k in ('E_err','err_at_E_Z')):
        return {'status':'UNREADABLE_ZERO_OR_PARTIAL'}
    total=mea['E_err']/leg['E_err']; mean=mea['err_at_E_Z']/leg['err_at_E_Z']
    shape=(mea['E_err']/mea['err_at_E_Z'])/(leg['E_err']/leg['err_at_E_Z'])
    error=mean*shape-total
    assert abs(error)<=1e-12
    return {'mean_shift':mean,'shape':shape,'total':total,'identity_error':error,
        'reading':'Algebraic decomposition; shape term is not an independently identified causal effect.'}

def join_curves(d):
    keys=['mode','rho_bar','tau_rho','seed','z_s']
    left=d[d.branch=='main']; right=d[d.branch=='control_legacy']
    common=left.merge(right,on=keys,suffixes=('_main','_legacy'),validate='one_to_one')
    assert len(common)>0, 'no shared z control'
    delta=np.abs(common.err_total_main.to_numpy()-common.err_total_legacy.to_numpy())
    assert np.array_equal(common.err_total_main.to_numpy(),common.err_total_legacy.to_numpy()), 'shared-z raw values differ'
    merged=d.sort_values('branch').drop_duplicates(keys).sort_values(keys)
    return merged,{'n_seed_rows_compared':len(common),'max_abs_diff':float(delta.max()),'bit_exact_raw_values':True}

def build():
    C.require_reading(); runs=C.campaign(); frames=[]
    for r in runs:
        f=pd.read_parquet(C.ROOT/r['out']);f=f[f['mode']!='cbr'].copy();f['branch']=r['branch'];frames.append(f)
    curves,h6=join_curves(pd.concat(frames,ignore_index=True)); ages=age_distributions(); rows=[]
    assert len(curves.groupby(['mode','rho_bar','tau_rho','seed']))==320
    for (mode,rho,tau),group in curves.groupby(['mode','rho_bar','tau_rho']):
        seeds=[]
        for seed,g in group.groupby('seed'):
            g=g.sort_values('z_s');rec={'seed':int(seed)}
            for name,dist in ages.items():rec[name]=integrate(dist['levels'],dist['weights'],g.z_s,g.err_total)
            rec['decomposition']=decompose(rec['legacy'],rec['measured']);seeds.append(rec)
        assert [x['seed'] for x in seeds]==list(C.SEEDS)
        row={'cell':'%s@%.3f'%(mode,rho),'tau':float(tau),'a':.9,'n_seeds':5,'seeds':seeds}
        for name in ages:
            row[name]={}
            for key in ('E_err','err_at_E_Z','E_Z','jensen_gap','jensen_gap_relative','mass_outside'):
                vals=[x[name][key] for x in seeds]
                row[name][key]=float(np.mean(vals)) if all(x is not None for x in vals) else None
            row[name]['status']='READABLE' if all(x[name]['status']=='READABLE' for x in seeds) else 'UNREADABLE_OR_PARTIAL'
        row['decomposition']=decompose(row['legacy'],row['measured']);rows.append(row)
    doc={**C.provenance('tools/20r2_9_axis_marginal.py',[C.OLD_PLAN,C.OLD_LOG,
             *[r['out'] for r in runs]],[]),
        'schema':'dt4n.s3_axis_marginal.v1','estimand_id':'DECISION_ERR_BY_AXIS',
        'age_distributions':ages,'shared_z_control':h6,'rows':rows,
        'reading':'Per cell and tau. Piecewise-linear interpolation of stored err(z) using scalar base age distributions. Jensen gap is not a proof of global curvature.'}
    doc['validity']['axis_role']='consumes_axis'
    doc['validity']['aoi_axis']={'label':'COMPARISON_LEGACY_AND_MEASURED','axes':{k:v['generator'] for k,v in ages.items()},
        'note':'Legacy is a named comparison, not approved as a new operating axis.'}
    doc['source_sha256'].update({p:C.sha(p) for p in ['measurements/decision_error.py','measurements/aoi_model_v7.py']})
    return doc

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True)
    a=ap.parse_args();d=build();C.write(a.out,d);print(d['shared_z_control'])
    for name,x in d['age_distributions'].items():print(name,'mean',x['mean_s'],'CV',x['cv'],'support',x['support_s'])
    for r in d['rows']:
        if r['tau']==3: print(r['cell'],'tau=3','legacy',r['legacy']['E_err'],'measured',r['measured']['E_err'],r['decomposition'])
    return 0
if __name__=='__main__':raise SystemExit(main())

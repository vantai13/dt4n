#!/usr/bin/env python3
"""S1: deterministic conditional Gaussian sensitivity, reported per cell and tau."""
from __future__ import annotations
import argparse
import math
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from tools import sensitivity_20r2 as C

PER = 'docs/phase-20R2/06b-per-cell.json'
LINK = 'results/LIVE/phase-23/link_corr_matrix.json'
OMEGAS = (0., .05, .10, .25, .50, 1.)

def err_bivariate(snr, r):
    if not math.isfinite(snr) or not -1 <= r <= 1:
        raise ValueError('invalid Gaussian parameters')
    if r == 1: return 0.
    # Integrate the bivariate density with respect to correlation from r to 1.
    # t=cos(theta) removes its endpoint singularity. No randomized CDF.
    def f(theta):
        den = 1.+math.cos(theta)
        return math.exp(-snr*snr/den) if den>0 else float(snr==0)
    return quad(f, 0., math.acos(r), epsabs=1e-14, epsrel=1e-12)[0]/math.pi

def ratio(s, r, v1, omega=.10):
    return err_bivariate(s/math.sqrt(1+omega*(v1-1)), r)/err_bivariate(s,r)

def threshold(r, v1):
    return brentq(lambda s: ratio(s,r,v1)-1.25, 0., 8., xtol=1e-12)

def classify(snr, star, value, stable=True):
    if not stable or abs(abs(snr)/star-1)<=.10: return 'UNREADABLE'
    return 'SENSITIVE' if value>1.25 else 'NOT_SENSITIVE'

def measure_pairs():
    from measurements import decision_error_v2 as DE
    from twin import topology_v7 as T7
    tt=DE.TruthTable(DE.TRUTH_TABLE); result={}
    for c in DE.feasible_cells(C.EXO, include_pc1=True):
        if c['mode']=='cbr': continue
        sig,_=DE.resolve_sigma(c,a_override=.9); samples=[]
        for seed in (101,102,103):
            rho=DE.rho_matrix_from_cell(c['mode'],float(c['rho_bar']),sig,seed,
                    tau=3.,n=200000,dt=DE.DT,source=DE.RHO_SOURCE)
            _,_,ct=tt.path_tables(c['mode'],rho,float(c['w_loss']))
            v,cnt=np.unique(ct.argmin(axis=1),return_counts=True); order=np.argsort(-cnt)
            pair=None; snr=None
            if len(order)>=2:
                pair=sorted([T7.PATH_NAMES[v[order[0]]],T7.PATH_NAMES[v[order[1]]]])
                m=ct[:,v[order[1]]]-ct[:,v[order[0]]]
                snr=float(m.mean()/m.std())
            samples.append({'seed':seed,'pair':pair,'snr':snr,
                'winning_shares':{T7.PATH_NAMES[k]:float(n/cnt.sum()) for k,n in zip(v,cnt)}})
        pairs=[x['pair'] for x in samples]
        result['%s@%.3f'%(c['mode'],c['rho_bar'])]={'samples':samples,
            'pair':pairs[0], 'stable':all(p is not None and p==pairs[0] for p in pairs)}
    return result

def build():
    C.require_reading(); per=C.read(PER); link=C.read(LINK); pred=C.read(C.PRED)
    pairs=measure_pairs(); rows=[]; by_cell={}
    assert set(pairs)==set(per['margin_structure']) and len(pairs)==8
    for cell,info in sorted(pairs.items()):
        s=abs(float(per['margin_structure'][cell]['m_mean']))
        recomputed=[x['snr'] for x in info['samples'] if x['snr'] is not None]
        if info['stable']:
            assert len(recomputed)==3 and abs(abs(float(np.mean(recomputed)))-s)<1e-12
        for tau in pred['taus']:
            row={'cell':cell,'tau':float(tau),'z_s':float(pred['z_reference_s']),
                 'snr0':s,'path_pair':info['pair'],'status':'UNREADABLE'}
            if info['stable'] and math.isfinite(s):
                v1=float(link['T5_var_margin']['m(%s,%s)'%tuple(info['pair'])]['ratio_at_omega_1_analytic'])
                r=math.exp(-row['z_s']/row['tau']); star=threshold(r,v1)
                vals={format(w,'.2f'):{'err':err_bivariate(s/math.sqrt(1+w*(v1-1)),r),
                                      'ratio':ratio(s,r,v1,w)} for w in OMEGAS}
                row.update(r=r,V1=v1,SNR_star=star,snr_relative_distance=s/star-1,
                    by_omega=vals,ratio_ref=vals['0.10']['ratio'],
                    status=classify(s,star,vals['0.10']['ratio']))
            rows.append(row)
        sub=[r for r in rows if r['cell']==cell]
        by_cell[cell]={'n_tau':len(sub),'n_sensitive':sum(r['status']=='SENSITIVE' for r in sub),
            'n_unreadable':sum(r['status']=='UNREADABLE' for r in sub),
            'ratio_ref_range':[min(r.get('ratio_ref',0) for r in sub),max(r.get('ratio_ref',0) for r in sub)]}
    doc={**C.provenance('tools/20r2_9_omega_sensitivity.py',[PER,LINK,C.PRED,
        'results/LIVE/phase-20R/truth_table.parquet'],[pred['z_reference_s']]),
        'schema':'dt4n.s1_omega.v1','rows':rows,'by_cell':by_cell,'path_pairs':pairs,
        'constants':{'omega_ref':.10,'sensitive_ratio':1.25,'omega_grid':OMEGAS},
        'limitation':'Conditional two-path Gaussian model; not a proven bound or measured network correlation. SNR inherited at tau=3. Old T4 CI is invalid as a conservative upper bound.'}
    doc['source_sha256'].update({p:C.sha(p) for p in ['measurements/decision_error_v2.py','measurements/sla_calib_v2.py','twin/topology_v7.py']})
    return doc

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True)
    a=ap.parse_args();d=build();C.write(a.out,d)
    for cell,r in d['by_cell'].items(): print(cell,r)
    return 0
if __name__=='__main__': raise SystemExit(main())

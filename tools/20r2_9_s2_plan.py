#!/usr/bin/env python3
"""Build the deterministic 320-cell S2 plan from the original main a=.9 design."""
import argparse
import numpy as np
from tools import sensitivity_20r2 as C
from measurements import decision_error_v2 as DE
PLAN='docs/phase-20R2/B2-run-plan.json'

def build():
    originals=[r for r in C.campaign() if r['branch']=='main']
    cells=DE.feasible_cells(C.EXO,include_pc1=False)
    assert len(cells)==8 and len(originals)==40
    rows=[{'cell':'%s@%.3f'%(c['mode'],c['rho_bar']),'mode':c['mode'],'rho_bar':float(c['rho_bar']),
           'tau':r['tau'],'seed':r['seed'],'n':r['n'],'a':.9,'original_parquet':r['out']}
          for r in originals for c in cells]
    runs=[]
    for index,j in enumerate(np.random.default_rng(20260914).permutation(len(rows))):
        r={**rows[j],'run_index':index,'out':f'{C.S2_DIR}/cell_{index:04d}.parquet'}
        r['cmd']=['-m','tools.20r2_9_s2_worker','--plan',PLAN,'--run-index',str(index)];runs.append(r)
    assert len({(r['cell'],r['tau'],r['seed']) for r in runs})==320
    return {**C.provenance('tools/20r2_9_s2_plan.py',[C.OLD_PLAN,C.OLD_LOG,C.PRED,
        *[r['out'] for r in originals]],DE.Z_ALL_20R2),
        'schema':'dt4n.s2_plan.v1','runs':runs,'n_runs':320,'n_rows':449280,
        'grid':{'z_values':list(DE.Z_ALL_20R2),'T_delay_ms':list(C.TD),'T_loss':list(C.TL),'a':.9,
                'taus':list(C.TAUS),'seeds':list(C.SEEDS)},
        'budget':{'estimate_minutes_from_supplied_pilot':68.,'status':'ESTIMATE_NOT_MEASUREMENT','execution':'sequential'},
        'order_seed':20260914,'controls':'Every call compares all shared per_z fields to its original campaign parquet and 13 signed-threshold identities with zero tolerance.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True)
    a=ap.parse_args();d=build();C.write(a.out,d);print('320 calls; 449280 rows;',a.out);return 0
if __name__=='__main__':raise SystemExit(main())

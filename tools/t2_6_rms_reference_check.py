#!/usr/bin/env python3
"""Replay a signed Phase 22.6 reference cell and audit RMS estimands; run from repo root."""
import hashlib,json,math,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from cert import tau_sweep as TS
source=Path('results/SUPERSEDED/phase-22/tau_sweep_poisson_0.925.json')
ref=json.loads(source.read_text());cfg=ref['provenance'];tau=ref['rows'][0]['tau']
df=TS.build_at_tau('poisson',.925,tau,seeds=cfg['seeds'],n=cfg['n'],dt=cfg['dt'],sigma=cfg['sigma_rho'])
dec=TS.decompose(df)
computed=np.sqrt(dec.rms_e_model**2+2*dec.cov_e+dec.rms_e_stale**2)
max_diff=float(np.max(np.abs(computed-dec.rms_total)))
fit=TS.fit_ar1(dec,tau)
fit_diff={k:float(fit[k]-ref['rows'][0]['ar1_fit'][k]) for k in ('A','c','rms_e_model')}
assert max_diff<1e-10
assert all(abs(x)<1e-8 for x in fit_diff.values()),fit_diff
out={'formula':'sqrt(rms_e_model**2 + 2*cov_e + rms_e_stale**2)',
 'formula_verdict':'PASS','reference_source':str(source),'reference_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'reference_tau':tau,'reference_provenance':cfg,'n_decomposition_rows':len(dec),'max_abs_formula_error':max_diff,
 'reference_fit_difference':fit_diff,'example':{**dec.iloc[0].to_dict(),'rms_total_reconstructed':float(computed.iloc[0])},
 'cross_phase_estimand_verdict':'INCOMPATIBLE',
 'phase22_quantity':'RMS of cost margin error between two actions ranked by stale twin; cost includes w_loss * loss',
 't2_quantity':'RMS of delay error over all actions; delay excludes w_loss * loss',
 'phase22_code':'cert/tau_sweep.py:build_at_tau + decompose',
 't2_code':'measurements/decision_error_v2.py:run_cell',
 'consequence':'Algebraic identity passes, but it does not make the two estimands equal. Do not adjudicate signed RMS predictions or infer conformal lift from T2 delay RMS.'}
Path('results/PENDING/phase-T2/rms_reference_check_r2.json').write_text(json.dumps(out,indent=2)+'\n')
dec.to_csv('results/PENDING/phase-T2/rms_reference_decomposition_r2.csv',index=False)
print(json.dumps(out,indent=2))

"""Issue a clean-worktree certificate with explicit observed/predicted scope."""
from __future__ import annotations
import argparse
import json
import platform
import subprocess
from pathlib import Path

import numpy as np

from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g2_topology import CAP_BPS, LINKS
from tools.g4_nugget_model import BASE, GATE_SF_RMS, adjudicate, sf_model, v_model


def sigma_min_feasible(cap_bps, dt, kappa, rho_eps, target_bias=.10):
    """Pair-correlation contamination proxy, NOT an omega-estimator bound."""
    return np.sqrt(v_model(cap_bps,dt,kappa)*max(rho_eps/target_bias-1,0))


def sigma_min_claim_c(cap_bps,dt,kappa=2.,sf_floor=.8264):
    return np.sqrt(v_model(cap_bps,dt,kappa)*sf_floor/(1-sf_floor))


def require_clean():
    state=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True)
    if state.strip():
        raise RuntimeError('REFUSING: commit tracked changes before issuing certificate')
    # A clean tracked tree must not hide untracked executable analysis code.
    for path in ('tools/g4_certify.py','tools/g4_nugget_model.py'):
        subprocess.run(['git','ls-files','--error-unmatch',path],check=True,stdout=subprocess.DEVNULL)


def validate_model(model):
    if model['overall']!='PASS' or not all(model['gates'].values()):
        raise ValueError('REFUSING: source model did not pass')
    if model['model']['kappa_theory']!=2.:
        raise ValueError('theory coefficient must not be fitted')
    for name,digest in model['sources'].items():
        if sha256_of(name)!=digest:
            raise ValueError(f'changed evidence: {name}')
    errors=[]
    for row in model['cells']:
        if row['dataset']=='G3b':
            pred=sf_model(row['sigma_target_per_link'],row['cap_bps'],row['dt_s'])
            errors.extend(pred-np.asarray(row['sf_measured']))
    rms=float(np.sqrt(np.mean(np.asarray(errors)**2)))
    gates,overall=adjudicate(model['cells'],rms)
    if overall!='PASS' or gates!=model['gates'] or not np.isfinite(rms) or rms>GATE_SF_RMS:
        raise ValueError('REFUSING: recomputed gates/self-test failed')
    return {'rms':rms,'max_abs_error':float(np.max(np.abs(errors))),
            'n_values':len(errors),'threshold_rms':GATE_SF_RMS,'passed':True,
            'source':'actual 40 G3b link/cell medians; fixed kappa=2'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--model',type=Path,default=BASE/'g4_nugget_model.json')
    ap.add_argument('--out',type=Path,default=Path('results/LIVE/phase-G2/measurement_path_cert_v2.json'))
    args=ap.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    require_clean()
    subprocess.run(['git','ls-files','--error-unmatch',str(args.model)],check=True,stdout=subprocess.DEVNULL)
    model=json.loads(args.model.read_text())
    self_test=validate_model(model)
    rho_max=max(r['rho_eps_run_max'] for r in model['cells'])
    table={}
    for dt in (.05,.1,.15,.2,.25,.5,1.,1.5):
        table[str(dt)]={'evidence_level':'OBSERVED_CONFIGURATION' if dt==.1 else 'UNVALIDATED_MODEL_PREDICTION',
                        'v_per_link':v_model(CAP_BPS,dt).tolist(),
                        'sigma_min_claim_c_proxy':sigma_min_claim_c(CAP_BPS,dt).tolist(),
                        'sigma_min_pair_bias_conditional_on_observed_rho_eps':sigma_min_feasible(CAP_BPS,dt,2.,rho_max).tolist()}
    evidence={str(args.model):sha256_of(args.model),**model['sources']}
    for name in ('tools/g4_certify.py','tools/g4_nugget_model.py','test/test_g4_reanalysis.py'):
        evidence[name]=sha256_of(name)
    payload={'schema':'dt4n.phase_g2.measurement_path_cert.v2','status':'PASS',
             'scope':'conditional model validation at measured configurations; not universal portability',
             'provenance':provenance(),'environment':{'kernel':platform.release(),'host':platform.node(),
                'python':platform.python_version(),'numpy':np.__version__},
             'certifies':{'form':'v(C,dt,L)=2*(8*L/(C*dt))^2/12','kappa':2.,'kappa_theory':2.,
                'empirical_kappa_by_dataset':{k:v['kappa_median'] for k,v in model['summary'].items()},
                'wire_bytes':1442.,'links':list(LINKS),'cap_bps':CAP_BPS.tolist(),
                'observed_dt_s':[.1],'rho_eps_max':rho_max,'rho_eps_statistic':'max observed absolute correlation over all 28 pairs and 13 runs; not a population upper confidence bound',
                'assumptions':['byte conservation','independent uniform sub-frame remainders at window boundaries']},
             'lookup_table':table,'self_test':self_test,'gates':model['gates'],'evidence_sha256':evidence,
             'expires_or_requires_revalidation_if':['drops/underrun or nonconserving shaper appears',
                'frame size or sampler elapsed-time normalisation changes',
                'kernel, driver, host or datapath changes',
                'dt/C moves outside measured configurations: formula extrapolates, empirical rho_eps bound does not'],
             'does_not_certify':['tau estimator','physical NIC or Internet','omega>0 residual model',
                'population confidence bound on residual cross-correlation',
                'an omega bias bound from a single pair-correlation proxy','all telemetry configurations'],
             'not_retroactive':'G3b estimates and verdicts remain unchanged'}
    digest=write_contract_artifact(args.out,payload)
    print(f"PASS: kappa=2 (fixed theory); max observed |rho_eps|={rho_max:.6f}; sf RMS={self_test['rms']:.6f}")
    print(f'{args.out}\nSHA256={digest}')


if __name__=='__main__': main()

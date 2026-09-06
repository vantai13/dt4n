"""Frozen synthetic link -> path -> Phase22 rank-slot transfer experiment."""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

import numpy as np
from scipy.signal import lfilter
from scipy.stats import t

from cert import simultaneous_score as S
from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g2_topology import CAP_BPS, INCIDENCE, LINKS, a0_from_sigma_at, design_covariance
from tools.g5_parameters import KAPPA_NUGGET, KAPPA_ACCEPT, nugget_variance, signal_fraction

BASE=Path('results/SMOKE/phase-G2')
CERT=Path('results/LIVE/phase-G2/measurement_path_cert_v2.json')
OMEGAS=(0.,.25,.5,.75,1.)
REPLICATES=200
SEED=20260907
DT=.1
TAU=3.
DURATION=600.
A0=a0_from_sigma_at('uA',.028)
PROTECTED=('cert/simultaneous_score.py','cert/margin_score.py','test/test_phase22_simscore.py')
PROCEDURES=('uncorrected','bonferroni','sidak','maxscore')


def verify_protected():
    for path in PROTECTED:
        frozen=subprocess.check_output(['git','show',f'phase-G2-g5-prereg:{path}'])
        if frozen!=Path(path).read_bytes():
            raise RuntimeError(f'protected Phase22 source changed: {path}')
    cert=json.loads(CERT.read_text())
    if cert['status']!='PASS' or cert['certifies']['kappa']!=KAPPA_NUGGET:
        raise RuntimeError('certified fixed nugget model unavailable')
    for path,h in cert['evidence_sha256'].items():
        if sha256_of(path)!=h: raise RuntimeError(f'certificate evidence changed: {path}')
    return {p:sha256_of(p) for p in (*PROTECTED,str(CERT))}


def covariance_factor(omega, null_pair=False):
    covariance=design_covariance(A0,omega)
    if null_pair:
        canonical=design_covariance(A0,0.)[:2,:2]
        np.testing.assert_allclose(covariance[:2,:2],canonical,rtol=1e-12,atol=1e-15)
        # Avoid omega-dependent roundoff in an analytically identical block.
        masked=np.zeros_like(covariance); masked[:2,:2]=canonical; covariance=masked
    vals,vec=np.linalg.eigh(covariance)
    if vals.min() < -1e-12: raise ValueError('covariance is not positive semidefinite')
    factor=vec*np.sqrt(np.maximum(vals,0))
    np.testing.assert_allclose(factor@factor.T,covariance,atol=1e-15,rtol=1e-12)
    return factor


def measured_errors(omega,n,dt,rng,*,null_pair=False,noise='uniform_ma1',variance='cert',tau=TAU):
    """Stationary AR1 signal plus independent, correctly normalised nugget."""
    factor=covariance_factor(omega,null_pair)
    phi=np.exp(-dt/tau)
    start=rng.standard_normal(8)
    z=rng.standard_normal((n,8))
    latent,_=lfilter([np.sqrt(1-phi*phi)],[1,-phi],z,axis=0,zi=(phi*start)[None,:])
    signal=latent@factor.T
    sigma2=np.diag(design_covariance(A0,omega))
    v=nugget_variance(CAP_BPS,dt) if variance=='cert' else sigma2*(1/.85-1)
    if noise=='white': eps=rng.standard_normal((n,8))*np.sqrt(v)
    elif noise=='gaussian_ma1':
        w=rng.standard_normal((n+1,8))*np.sqrt(v/2); eps=-np.diff(w,axis=0)
    elif noise=='uniform_ma1':
        w=rng.uniform(-.5,.5,(n+1,8))*np.sqrt(6*v); eps=-np.diff(w,axis=0)
    else: raise ValueError('unknown noise family')
    if null_pair: eps[:,2:]=0
    return signal+eps


def make_inputs(omega,rep,split,*,null_pair=False,n=None):
    n=int(DURATION/DT) if n is None else n
    rng=np.random.default_rng(np.random.SeedSequence([SEED,rep,split]))
    truth=rng.uniform(10,110,(n,4))
    err=measured_errors(omega,n,DT,rng,null_pair=null_pair)
    estimate=truth+100*(err@INCIDENCE)
    return truth,estimate


def evaluate(cal_true,cal_hat,test_true,test_hat):
    cal=S.pair_scores(cal_true,cal_hat)
    test=S.pair_scores(test_true,test_hat)
    quantiles={'uncorrected':S.qhat_per_slot(cal,.10),
               'bonferroni':S.qhat_bonferroni(cal,.10),
               'sidak':S.qhat_sidak(cal,.10),
               'maxscore':S.qhat_maxscore(cal.max(axis=1),.10)}
    mhat=S.pair_margins_hat(test_hat)
    failure=S.decision_failure(S.pair_margins_true(test_true,test_hat))
    corr=np.corrcoef(test.T)[np.triu_indices(3,1)]
    output={}
    for name,q in quantiles.items():
        accepted=S.accept_simultaneous(mhat,q,kappa=KAPPA_ACCEPT)
        output[name]={'coverage':S.coverage_simultaneous(test,q),
                      'marginal':S.coverage_pointwise(test,q).tolist(),
                      'qhat':np.broadcast_to(q,(3,)).tolist(),
                      'acceptance':float(accepted.mean()),
                      'accepted_failure_rate':float(failure[accepted].mean()) if accepted.any() else None,
                      'score_correlations':corr.tolist()}
    return output


def summarize(samples):
    summaries={}
    for procedure in PROCEDURES:
        cov=np.array([[r[procedure]['coverage'] for r in omega] for omega in samples])
        marg=np.array([[r[procedure]['marginal'] for r in omega] for omega in samples])
        means=cov.mean(axis=1); sd=cov.std(axis=1,ddof=1)
        amplitude=float(np.ptp(means)); pooled=float(np.sqrt(np.mean(sd**2)))
        differences=[]
        for i in range(5):
            for j in range(i+1,5):
                delta=cov[j]-cov[i]
                half=float(t.ppf(1-.05/(2*10),len(delta)-1)*delta.std(ddof=1)/np.sqrt(len(delta)))
                differences.append({'omega_pair':[OMEGAS[i],OMEGAS[j]],'delta':float(delta.mean()),
                                    'ci95_bonferroni':[float(delta.mean()-half),float(delta.mean()+half)]})
        summaries[procedure]={'amplitude':amplitude,'single_trace_sd':pooled,
            'snr':amplitude/pooled if pooled>0 else 0.,'worst_step':float(np.diff(means).min()),
            'marginal_drift':float(np.max(abs(marg.mean(axis=1)-marg[0].mean(axis=0)))),
            'nc3_signed':float(means[0]-np.prod(marg[0].mean(axis=0))),
            'nc3_abs':float(abs(means[0]-np.prod(marg[0].mean(axis=0)))),
            'pair_contrasts':differences,
            'finite_grid_amplitude_upper95':max(max(abs(x) for x in d['ci95_bonferroni']) for d in differences),
            'rows':[{'omega':w,'coverage':float(means[i]),'sd':float(sd[i]),'mc_se':float(sd[i]/np.sqrt(cov.shape[1])),
                     'marginal':marg[i].mean(axis=0).tolist(),
                     'qhat':np.mean([r[procedure]['qhat'] for r in samples[i]],axis=0).tolist(),
                     'acceptance':float(np.mean([r[procedure]['acceptance'] for r in samples[i]])),
                     'score_correlations':np.mean([r[procedure]['score_correlations'] for r in samples[i]],axis=0).tolist()}
                    for i,w in enumerate(OMEGAS)]}
    return summaries


def adjudicate(primary,null):
    p=primary['uncorrected']
    gates={'T-1':p['amplitude']>=.020,'T-2':p['snr']>=3.,'T-3':p['worst_step']>=-.002,
           'NC-1':p['marginal_drift']<=.005,'NC-2':null['uncorrected']['amplitude']<=.005}
    if not(gates['NC-1'] and gates['NC-2']): diagnostic='STOP_GENERATOR'
    elif not gates['T-1']: diagnostic='TRANSFER_FAILS'
    elif not(gates['T-2'] and gates['T-3']): diagnostic='ADOPT_WEAK_DIAGNOSTIC'
    else: diagnostic='ADOPT_DIAGNOSTIC'
    runtime=primary['maxscore']['amplitude']>=.02 and primary['maxscore']['marginal_drift']<=.005
    adopt=diagnostic=='ADOPT_DIAGNOSTIC' and runtime
    return {'gates':{k:bool(v) for k,v in gates.items()},'diagnostic_verdict':diagnostic,
            'runtime_transfer_pass':bool(runtime),'retire_kappa_time':bool(adopt),
            'overall':'ADOPT' if adopt else 'TRANSFER_FAILS_RUNTIME' if diagnostic.startswith('ADOPT') else diagnostic}


def transfer():
    results={}
    for name,null_pair in [('primary',False),('null_uA_uB',True)]:
        all_samples=[]
        for omega in OMEGAS:
            samples=[]
            for rep in range(REPLICATES):
                cal=make_inputs(omega,rep,0,null_pair=null_pair)
                tst=make_inputs(omega,rep,1,null_pair=null_pair)
                samples.append(evaluate(*cal,*tst))
            all_samples.append(samples)
            print(f"{name} omega={omega:.2f}: uncorrected={np.mean([r['uncorrected']['coverage'] for r in samples]):.6f}; maxscore={np.mean([r['maxscore']['coverage'] for r in samples]):.6f}",flush=True)
        results[name]={'summary':summarize(all_samples),'replicates':all_samples}
    decision=adjudicate(results['primary']['summary'],results['null_uA_uB']['summary'])
    return {'results':results,**decision}


def recompute_doc47():
    from tools import g3_omega_coverage_dryrun as legacy
    from tools import g3_dryrun
    if legacy.DT_S!=.2 or g3_dryrun.DT_S!=.2:
        raise RuntimeError('legacy module dt changed; cannot reproduce signed baseline')
    baseline=legacy.sweep(.85,(2,4,8),600.,60)
    original=json.loads(Path('results/SMOKE/phase-G/g3_omega_coverage_dryrun.json').read_text())
    for got,want in zip(baseline,original['primary']):
        for key in got: np.testing.assert_allclose(got[key],want[key],rtol=1e-12,atol=1e-12)
    print('Historical doc47 primary reproduced at rtol=atol=1e-12',flush=True)
    cases=[]
    for dt in (.2,.1):
        for variance in ('sf85','cert'):
            for noise in ('white','gaussian_ma1','uniform_ma1'):
                rows=[]
                for omega in OMEGAS:
                    values=[]
                    for rep in range(REPLICATES):
                        rng=np.random.default_rng(np.random.SeedSequence([SEED,rep,47]))
                        matrix=measured_errors(omega,int(DURATION/dt),dt,rng,noise=noise,variance=variance).T
                        values.append(legacy.coverage(matrix,(2,8)))
                    joint=np.array([v[8] for v in values])
                    rows.append({'omega':omega,'marginal':float(np.mean([v[0] for v in values])),
                                 'joint_k8':float(joint.mean()),'sd':float(joint.std(ddof=1)),
                                 'joint_k2':float(np.mean([v[2] for v in values])),
                                 'replicates':values})
                amp=float(np.ptp([r['joint_k8'] for r in rows]))
                case={'dt_s':dt,'variance':variance,'noise':noise,'rows':rows,'amplitude_k8':amp,
                      'amplitude_k2':float(np.ptp([r['joint_k2'] for r in rows])),
                      'evidence_level':'SYNTHETIC_AT_CERTIFIED_DT' if dt==.1 else 'SYNTHETIC_EXTRAPOLATION'}
                cases.append(case)
                print(f'doc47 dt={dt} {variance:4s} {noise:12s}: K8 amplitude={amp:.6f}',flush=True)
    return {'legacy_primary_reproduced':True,'legacy_primary':baseline,'cases':cases,'overall':'REPORTED_NOT_GATED'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--recompute-doc47',action='store_true')
    ap.add_argument('--out',type=Path)
    args=ap.parse_args()
    out=args.out or BASE/('g5_doc47_recomputed.json' if args.recompute_doc47 else 'g5_estimand_transfer.json')
    if out.exists(): raise FileExistsError(out)
    sources=verify_protected(); started=time.monotonic()
    payload=recompute_doc47() if args.recompute_doc47 else transfer()
    if sources!=verify_protected(): raise RuntimeError('protected source changed during execution')
    payload.update(schema='dt4n.phase_g2.g5_estimand_transfer.v1',status='SYNTHETIC_NO_NETWORK',
        provenance=provenance(),elapsed_s=time.monotonic()-started,
        source_sha256={**sources,'tools/g5_estimand_transfer.py':sha256_of(__file__),
                      'tools/g5_parameters.py':sha256_of('tools/g5_parameters.py'),
                      'docs/phase-G/69-prereg-g5-estimand-transfer.md':sha256_of('docs/phase-G/69-prereg-g5-estimand-transfer.md')},
        design={'omega_grid':OMEGAS,'replicates':REPLICATES,'seed':SEED,'dt_s':DT,'tau_s':TAU,
                'duration_each_calibration_test_s':DURATION,'sigma_ref':.028,'cost_scale_ms_per_rho':100,
                'kappa_nugget':KAPPA_NUGGET,'kappa_time_simulated':1,'kappa_accept':KAPPA_ACCEPT,
                'sf_certified_formula':signal_fraction(np.sqrt(np.diag(design_covariance(A0,0))),CAP_BPS,DT).tolist()})
    write_contract_artifact(out,payload)
    print(json.dumps({k:payload[k] for k in ('overall','gates','retire_kappa_time','elapsed_s') if k in payload},indent=2));print(out)


if __name__=='__main__':main()

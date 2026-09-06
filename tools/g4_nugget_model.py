"""Validate the fixed conserving-frame hypothesis on saved G3b and G2 data."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g2_topology import CAP_BPS, LINKS
from tools.measurement_path_calib import estimate_nugget

BASE = Path('results/SMOKE/phase-G2')
WIRE_BYTES = 1442.0
KAPPA_THEORY = 2.0
GATE_SF_RMS = .02


def v_q(cap_bps, dt, wire_bytes=WIRE_BYTES):
    caps = np.asarray(cap_bps, float)
    if not np.isfinite(caps).all() or np.any(caps <= 0) or not np.isfinite(dt) or dt <= 0 or wire_bytes <= 0:
        raise ValueError('positive finite capacity, dt and frame size required')
    return (8 * wire_bytes / (caps * dt)) ** 2 / 12


def v_model(cap_bps, dt, kappa=KAPPA_THEORY, wire_bytes=WIRE_BYTES):
    if not np.isfinite(kappa) or kappa <= 0:
        raise ValueError('positive finite kappa required')
    return kappa * v_q(cap_bps, dt, wire_bytes)


def sf_model(sigma_link, cap_bps, dt, kappa=KAPPA_THEORY):
    s = np.asarray(sigma_link, float)
    if not np.isfinite(s).all() or np.any(s < 0):
        raise ValueError('nonnegative finite sigma required')
    return s*s / (s*s + v_model(cap_bps, dt, kappa))


def alignment_check(rho, target, max_lag=3):
    """Shift target relative to fixed measured indices, on equal-length support."""
    rho, target = np.asarray(rho), np.asarray(target)
    if rho.ndim != 1 or rho.shape != target.shape or len(rho) <= 2*max_lag+2:
        raise ValueError('matching sufficiently long vectors required')
    if not np.isfinite(rho).all() or not np.isfinite(target).all():
        raise ValueError('finite series required')
    stop = len(rho)-max_lag
    variances = {str(lag): float(np.var(rho[max_lag:stop] - target[max_lag+lag:stop+lag], ddof=1))
                 for lag in range(-max_lag, max_lag+1)}
    best = min(variances, key=variances.get)
    unique = sum(v == variances[best] for v in variances.values()) == 1
    return {'var_by_lag': variances, 'argmin_lag': int(best),
            'aligned': bool(best == '0' and unique),
            'side_asymmetry_relative': abs(variances['-1']-variances['1']) /
                max(variances['-1']+variances['1'], np.finfo(float).tiny)}


def analyse_series(rho, target, dt, cap_bps):
    rho, target = np.asarray(rho, float), np.asarray(target, float)
    if rho.ndim != 3 or rho.shape != target.shape or rho.shape[2] != len(cap_bps):
        raise ValueError('expected matching (replicate, window, link) arrays')
    if not np.isfinite(rho).all() or not np.isfinite(target).all():
        raise ValueError('nonfinite observations')
    eps = rho-target
    n_rep, n_win, n_link = eps.shape
    pairs = np.triu_indices(n_link, 1)
    vq = v_q(cap_bps, dt)
    runs = []
    for r in range(n_rep):
        centered = eps[r]-eps[r].mean(axis=0)
        den = np.sum(centered**2, axis=0)
        if np.any(den <= 0):
            raise ValueError('residual correlation undefined for zero variance')
        acf = [np.sum(centered[:-lag]*centered[lag:], axis=0)/den for lag in range(1,9)]
        corr = np.corrcoef(eps[r].T)[pairs]
        variance = eps[r].var(axis=0, ddof=1)
        runs.append({'replicate': r, 'v_direct_per_link': variance.tolist(),
                     'kappa_per_link': (variance/vq).tolist(),
                     'acf_lags_1_to_8': np.asarray(acf).T.tolist(),
                     'rho_eps_pairs': corr.tolist(),
                     'rho_eps_max': float(np.max(np.abs(corr))),
                     'alignment_per_link': [alignment_check(rho[r,:,i], target[r,:,i]) for i in range(n_link)]})
    direct = np.mean([r['v_direct_per_link'] for r in runs], axis=0)
    acf = np.mean([r['acf_lags_1_to_8'] for r in runs], axis=0)
    pair_values = np.array([r['rho_eps_pairs'] for r in runs])
    pooled = np.tanh(np.mean(np.arctanh(np.clip(pair_values, -.999999999, .999999999)), axis=0))
    return {'n_rep': n_rep, 'n_win': n_win, 'dt_s': dt,
            'cap_bps': np.asarray(cap_bps).tolist(), 'v_q_per_link': vq.tolist(),
            'v_direct_per_link': direct.tolist(), 'kappa_per_link': (direct/vq).tolist(),
            'kappa_median': float(np.median(direct/vq)),
            'acf1_per_link': acf[:,0].tolist(), 'acf1_median': float(np.median(acf[:,0])),
            'acf_lags_1_to_8': acf.tolist(),
            'rho_eps_pairs': pooled.tolist(), 'rho_eps_max': float(np.max(np.abs(pooled))),
            'rho_eps_run_max': max(r['rho_eps_max'] for r in runs),
            'pair_labels': [[LINKS[i], LINKS[j]] for i,j in zip(*pairs)],
            'aligned': all(a['aligned'] for r in runs for a in r['alignment_per_link']),
            'replicates': runs}


def adjudicate(rows, sf_rms):
    finite = all(np.isfinite(np.asarray(r[k])).all() for r in rows
                 for k in ('v_direct_per_link','kappa_per_link','acf1_per_link','rho_eps_pairs'))
    datasets = sorted({r['dataset'] for r in rows})
    gates = {
        'M-1_aligned': all(r['aligned'] for r in rows),
        'M-2_finite': bool(finite and np.isfinite(sf_rms)),
        'M-3_rho_eps_within_B2': all(max(r['rho_eps_max'],r['rho_eps_run_max']) <= .15 for r in rows),
        'M-4_kappa_in_band': all(1.5 <= np.median([v for r in rows if r['dataset']==d for v in r['kappa_per_link']]) <= 2.5 for d in datasets),
        'M-5_acf1_matches_theory': all(abs(np.median([v for r in rows if r['dataset']==d for v in r['acf1_per_link']])+.5) <= .05 for d in datasets),
        'M-6_sf_rms': bool(sf_rms <= GATE_SF_RMS),
    }
    gates = {k: bool(v) for k,v in gates.items()}
    overall = ('STOP_ALIGNMENT' if not gates['M-1_aligned'] else
               'DIAG_CONTAMINATION' if not gates['M-3_rho_eps_within_B2'] else
               'PASS' if all(gates.values()) else 'FAIL')
    return gates, overall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, default=BASE/'g4_nugget_model.json')
    args = ap.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    sources = [BASE/'g3b_sigma_tau_series.npz', BASE/'g3b_sigma_tau.json',
               BASE/'g2_kill_series.npz', BASE/'g2_kill_test_run3_instrumented.json',
               Path('docs/phase-G/67-prereg-g4-nugget-model.md')]
    manifest = json.loads((BASE/'g3b_artifact_manifest.json').read_text())['sha256']
    for path in sources[:2]:
        if sha256_of(path) != manifest[str(path)]:
            raise ValueError(f'source hash mismatch: {path}')
    if sha256_of(sources[2]) != '64279ffe1610858383003587ef53a64eba2096f7c8083d8f7b8e8c00b48f986b':
        raise ValueError('G2 source differs from doc 61')
    if sha256_of(sources[3]) != '567b5ddb1faeae7855422f567628e94c02cbcea24a274dd782a278822f4776b5':
        raise ValueError('G2 JSON differs from doc 61')
    results = json.loads(sources[1].read_text())
    rows, estimates = [], []
    with np.load(sources[0], allow_pickle=False) as raw:
        caps, dt = raw['cap_bps'], float(raw['dt_s'])
        np.testing.assert_array_equal(caps, CAP_BPS)
        from tools.g2_kill_test import IFACE
        np.testing.assert_array_equal(raw['ifaces'], IFACE)
        assert float(raw['omega']) == 0 and dt == results['design']['dt_s']
        for cell in results['cells']:
            t,s = cell['tau_s'],cell['sigma_ref']; key=f't{t:g}_s{s:g}'
            rho,target = raw['rho_'+key],raw['tgt_'+key]
            row = analyse_series(rho,target,dt,caps)
            row.update(dataset='G3b',cell=key,tau_s=t,sigma_ref=s)
            fits=[]
            for rep in range(len(rho)):
                repfits=[]
                for i,link in enumerate(LINKS):
                    f=estimate_nugget(rho[rep,:,i],dt,cell['n_lags'],lag_lo=2)
                    stored=cell['replicates'][rep]
                    for k,field in [('sf','sf_per_link'),('tau_from_fit_s','tau_hat_per_link'),('sigma_true','sigma_hat_per_link')]:
                        np.testing.assert_allclose(f[k],stored[field][i],rtol=1e-12,atol=1e-12)
                    estimates.append({'tau_s':t,'sigma_ref':s,'replicate':rep,'link':link,
                                      'link_index':i,'tau_hat_s':f['tau_from_fit_s'],
                                      'sigma_ratio':f['sigma_true']/stored['sigma_target_per_link'][i],
                                      'sf':f['sf'],'v_indirect':f['v'],
                                      'kappa_indirect':f['v']/vq_value(caps[i],dt),
                                      'sigma_target':stored['sigma_target_per_link'][i]})
                    repfits.append(f['sf'])
                fits.append(repfits)
            sig=np.array(cell['replicates'][0]['sigma_target_per_link'])
            pred=sf_model(sig,caps,dt)
            measured=np.median(fits,axis=0)
            row.update(sf_predicted=pred.tolist(),sf_measured=measured.tolist(),
                       sf_error=(pred-measured).tolist(),sigma_target_per_link=sig.tolist())
            rows.append(row)
    with np.load(sources[2],allow_pickle=False) as raw:
        np.testing.assert_array_equal(raw['cap_bps'],CAP_BPS)
        from tools.g2_kill_test import IFACE
        np.testing.assert_array_equal(raw['ifaces'],IFACE)
        assert float(raw['omega'])==0
        row=analyse_series(raw['rho_measured'],raw['rho_target'],float(raw['dt_s']),raw['cap_bps'])
        row.update(dataset='G2',cell='g2_run3',tau_s=float(raw['tau_s']))
        rows.append(row)
    errors=np.array([r['sf_error'] for r in rows if r['dataset']=='G3b'])
    sf_rms=float(np.sqrt(np.mean(errors**2)))
    gates,overall=adjudicate(rows,sf_rms)
    summary={}
    for dataset in ('G3b','G2'):
        rr=[r for r in rows if r['dataset']==dataset]
        k=np.array([v for r in rr for v in r['kappa_per_link']])
        summary[dataset]={'kappa_median':float(np.median(k)),'kappa_iqr':np.percentile(k,[25,75]).tolist(),
                          'kappa_range':[float(k.min()),float(k.max())],
                          'acf1_median':float(np.median([v for r in rr for v in r['acf1_per_link']])),
                          'rho_eps_max':max(r['rho_eps_max'] for r in rr),
                          'rho_eps_run_max':max(r['rho_eps_run_max'] for r in rr),
                          'n_link_runs':sum(r['n_rep']*8 for r in rr)}
    payload={'schema':'dt4n.phase_g2.g4_nugget_model.v1','status':'REANALYSIS_NO_NETWORK',
             'created_utc':datetime.now(timezone.utc).isoformat(),'provenance':provenance(),
             'model':{'form':'v = 2*(8*L/(C*dt))^2/12','kappa_theory':2.,'acf1_theory':-.5,'wire_bytes':WIRE_BYTES},
             'sources':{str(p):sha256_of(p) for p in sources},'cells':rows,'g3b_estimates':estimates,
             'summary':summary,'sf_self_test':{'rms':sf_rms,'max_abs':float(np.max(abs(errors))),
                'median_predicted_minus_measured':float(np.median(errors)), 'n':int(errors.size),'gate':GATE_SF_RMS},
             'indirect_kappa_median':float(np.median([e['kappa_indirect'] for e in estimates])),
             'gates':gates,'overall':overall}
    write_contract_artifact(args.out,payload)
    print('cell                kappa      ACF1  max|rho_eps| run_max aligned')
    for r in rows:
        print(f"{r['cell']:18s} {r['kappa_median']:7.4f} {r['acf1_median']:9.5f} {r['rho_eps_max']:12.5f} {r['rho_eps_run_max']:7.5f} {r['aligned']}")
    print(json.dumps({'summary':summary,'sf_self_test':payload['sf_self_test'],'gates':gates,'overall':overall},indent=2))
    print(args.out)


def vq_value(cap,dt):
    return float(v_q(cap,dt))


if __name__=='__main__':
    main()

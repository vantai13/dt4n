"""G'.5b -- can the POWER channel carry the omega axis without kappa_time?

Doc 70a settled the coverage question: omega reaches the rank-slot estimand as
a near-uniform scale factor plus a re-ranking, and both are absorbed, so
coverage is invariant. Doc 70 section 4 then observed -- descriptively, outside
its signed gates -- that the same scale inflates qhat 32 percent and costs 19
percent of accepted windows at ONE time scale. That observation generated a
hypothesis and cannot also test it, so this retests it on a fresh seed under
docs/phase-G/72-prereg-g5b-power-axis.md.

The control that matters multiplies the SCORE MATRIX by the measured scale
factor, never the twin error. Doc 70a section 4 measured why: scaling the twin
error re-ranks 9.1 percent of rows at c = 1.3131 and 77.7 percent at c = 7.5,
so it mixes the two channels and cannot isolate either.

    python -m tools.g5b_power_axis
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from cert import simultaneous_score as S
from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g2_topology import INCIDENCE
from tools.g5_estimand_transfer import DT, DURATION, OMEGAS, REPLICATES, TAU, measured_errors, verify_protected
from tools.g5_parameters import KAPPA_ACCEPT

OUT = Path('results/SMOKE/phase-G2/g5b_power_axis.json')
SEED = 20260908          # fresh: G5 used 20260907 and generated the hypothesis
ALPHA = .10
PROCEDURES = ('maxscore', 'uncorrected')


def make_inputs(omega, rep, split, *, null_pair=False):
    """Same error model as G5, new seed. Ranking sees y_hat only."""
    n = int(DURATION / DT)
    rng = np.random.default_rng(np.random.SeedSequence([SEED, rep, split]))
    truth = rng.uniform(10, 110, (n, 4))
    err = measured_errors(omega, n, DT, rng, null_pair=null_pair, tau=TAU)
    return truth, truth + 100 * (err @ INCIDENCE)


def quantiles(cal_scores):
    return {'maxscore': S.qhat_maxscore(cal_scores.max(axis=1), ALPHA),
            'uncorrected': S.qhat_per_slot(cal_scores, ALPHA)}


def measure(cal_true, cal_hat, test_true, test_hat):
    cal = S.pair_scores(cal_true, cal_hat)
    test = S.pair_scores(test_true, test_hat)
    m_hat = S.pair_margins_hat(test_hat)
    out = {}
    for name, q in quantiles(cal).items():
        out[name] = {'qhat': np.broadcast_to(np.asarray(q, float), (3,)).tolist(),
                     'coverage': S.coverage_simultaneous(test, q),
                     'acceptance': float(S.accept_simultaneous(m_hat, q, kappa=KAPPA_ACCEPT).mean())}
    out['slot_score_sd'] = cal.std(axis=0, ddof=1).tolist()
    return out, cal, m_hat


def scale_surrogate(cal_scores, m_hat_ref, c):
    """Pure scale channel: inflate the SCORE MATRIX, hold the twin margins.

    Acceptance then falls only because qhat grew. Whatever omega costs beyond
    this is the part its scale factor does not explain.
    """
    out = {}
    for name, q in quantiles(cal_scores * c).items():
        out[name] = float(S.accept_simultaneous(m_hat_ref, q, kappa=KAPPA_ACCEPT).mean())
    return out


def sweep(null_pair=False):
    rows, reference = [], {}
    for i, omega in enumerate(OMEGAS):
        samples, surrogate, reranked = [], [], []
        for rep in range(REPLICATES):
            cal_true, cal_hat = make_inputs(omega, rep, 0, null_pair=null_pair)
            test_true, test_hat = make_inputs(omega, rep, 1, null_pair=null_pair)
            stats, cal_scores, m_hat = measure(cal_true, cal_hat, test_true, test_hat)
            samples.append(stats)
            if i == 0:
                reference.setdefault('cal_scores', []).append(cal_scores)
                reference.setdefault('m_hat', []).append(m_hat)
                reference.setdefault('order', []).append(S.top_k_by_twin(test_hat))
            else:
                reranked.append(float((S.top_k_by_twin(test_hat) != reference['order'][rep]).any(axis=1).mean()))
        base = np.mean([s['uncorrected']['qhat'] for s in
                        (samples if i == 0 else rows[0]['samples'])], axis=0)
        ratio = np.mean([s['uncorrected']['qhat'] for s in samples], axis=0) / base
        c = float(ratio.mean())
        if i > 0:
            surrogate = [scale_surrogate(reference['cal_scores'][rep], reference['m_hat'][rep], c)
                         for rep in range(REPLICATES)]
        rows.append({'omega': omega, 'samples': samples, 'scale_factor': ratio.tolist(),
                     'mean_scale': c, 'scale_spread_fraction': float(np.ptp(ratio) / ratio.mean()),
                     'surrogate': surrogate,
                     'rows_reranked': float(np.mean(reranked)) if reranked else 0.})
    return rows


def summarize(rows):
    summary = {}
    for procedure in PROCEDURES:
        acc = np.array([[s[procedure]['acceptance'] for s in r['samples']] for r in rows])
        cov = np.array([[s[procedure]['coverage'] for s in r['samples']] for r in rows])
        means, sd = acc.mean(axis=1), acc.std(axis=1, ddof=1)
        pooled = float(np.sqrt(np.mean(sd ** 2)))
        surrogate = [float(np.mean([x[procedure] for x in r['surrogate']])) if r['surrogate'] else None
                     for r in rows]
        summary[procedure] = {
            'amplitude': float(np.ptp(means)), 'single_trace_sd': pooled,
            'snr': float(np.ptp(means) / pooled) if pooled else 0.,
            'worst_step': float(np.diff(means).min()),
            'coverage_amplitude': float(np.ptp(cov.mean(axis=1))),
            'acceptance_by_omega': means.tolist(),
            'acceptance_mc_se': (sd / np.sqrt(acc.shape[1])).tolist(),
            'coverage_by_omega': cov.mean(axis=1).tolist(),
            'surrogate_acceptance': surrogate,
            'irreducible_remainder': None if surrogate[-1] is None else float(means[-1] - surrogate[-1]),
            'qhat_inflation': float(np.mean([s[procedure]['qhat'] for s in rows[-1]['samples']])
                                    / np.mean([s[procedure]['qhat'] for s in rows[0]['samples']])),
        }
    summary['scale_channel'] = {'mean_scale': rows[-1]['mean_scale'],
                                'scale_spread_fraction': rows[-1]['scale_spread_fraction'],
                                'scale_factor': rows[-1]['scale_factor']}
    summary['rows_reranked'] = [r['rows_reranked'] for r in rows]
    return summary


def adjudicate(primary, null):
    p = primary['maxscore']
    gates = {'P-1': p['amplitude'] >= .050, 'P-2': p['snr'] >= 5.,
             'P-3': p['worst_step'] >= -.005,
             'NC-1': p['coverage_amplitude'] <= .005,
             'NC-2': null['maxscore']['amplitude'] <= .010}
    if not (gates['NC-1'] and gates['NC-2']):
        verdict = 'STOP_GENERATOR'
    elif not gates['P-1']:
        verdict = 'POWER_TOO_WEAK'
    elif not (gates['P-2'] and gates['P-3']):
        verdict = 'ADOPT_WEAK'
    else:
        verdict = 'POWER_AXIS_HOLDS'
    remainder = p['irreducible_remainder']
    classification = None
    if verdict == 'POWER_AXIS_HOLDS':
        classification = 'REDUCIBLE_TO_EFFECTIVE_SIGMA' if abs(remainder) < .03 else 'IRREDUCIBLE'
    return {'gates': {k: bool(v) for k, v in gates.items()}, 'verdict': verdict,
            'classification': classification, 'irreducible_remainder': remainder}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    sources = verify_protected()
    started = time.monotonic()
    primary = summarize(sweep(null_pair=False))
    null = summarize(sweep(null_pair=True))
    for name, block in (('primary', primary), ('null_uA_uB', null)):
        print(f"{name}: acceptance {[round(x, 5) for x in block['maxscore']['acceptance_by_omega']]}"
              f" amplitude={block['maxscore']['amplitude']:.6f}"
              f" coverage_amp={block['maxscore']['coverage_amplitude']:.6f}", flush=True)
    decision = adjudicate(primary, null)
    if sources != verify_protected():
        raise RuntimeError('protected source changed during execution')
    payload = {'schema': 'dt4n.phase_g2.g5b_power_axis.v1', 'status': 'SYNTHETIC_NO_NETWORK',
               'results': {'primary': primary, 'null_uA_uB': null}, **decision,
               'design': {'seed': SEED, 'omega_grid': list(OMEGAS), 'replicates': REPLICATES,
                          'dt_s': DT, 'tau_s': TAU, 'kappa_time_simulated': 1,
                          'kappa_accept': KAPPA_ACCEPT, 'alpha': ALPHA,
                          'surrogate': 'score matrix scaled by measured c; twin margins held at omega=0'},
               'provenance': provenance(), 'elapsed_s': time.monotonic() - started,
               'source_sha256': {**sources, 'tools/g5b_power_axis.py': sha256_of(__file__),
                                 'docs/phase-G/72-prereg-g5b-power-axis.md':
                                     sha256_of('docs/phase-G/72-prereg-g5b-power-axis.md')}}
    write_contract_artifact(OUT, payload)
    print(json.dumps({k: payload[k] for k in ('verdict', 'classification', 'gates',
                                              'irreducible_remainder', 'elapsed_s')}, indent=2))


if __name__ == '__main__':
    main()

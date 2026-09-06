"""Audit why omega moves link coverage but not rank-slot coverage.

Doc 70 section 3 answered "because 22R makes 3 simultaneous statements
instead of 8". That answer is confounded: the K=2 row it rested on is
`inside[:2]` of `tools/g3_omega_coverage_dryrun.coverage`, and the first two
links in LINKS order are `uA, uB`, whose K_TOPO entry is 0. It is the
topological null pair doc 47 section 4 already named, so it measures "cannot
couple", not "few statements".

This tool measures the two things that were conflated, then tests the
mechanism that actually holds. It changes no verdict: every G5 gate stands.

    python -m tools.g5a_mechanism_audit
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from cert import simultaneous_score as S
from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g2_topology import K_TOPO, LINKS
from tools.g3_omega_coverage_dryrun import Z
from tools.g5_estimand_transfer import (DURATION, DT, OMEGAS, REPLICATES, SEED,
                                        make_inputs, measured_errors, verify_protected)

OUT = Path('results/SMOKE/phase-G2/g5a_mechanism_audit.json')
KT = np.asarray(K_TOPO)
INDEX = {name: i for i, name in enumerate(LINKS)}
SUBSETS = (('uA', 'uB'), ('uA', 'ac'), ('ac', 'vC'), ('uA', 'vC'),
           ('ac', 'ad', 'bc', 'bd'), ('uA', 'uB', 'ac', 'ad'),
           ('uA', 'uB', 'ac', 'ad', 'bc', 'bd'), tuple(LINKS))
SCALES = (1.3131, 2.0, 7.5)


def coupling_sum(subset):
    """Sum of off-diagonal K_TOPO inside the subset: the omega coupling budget."""
    j = [INDEX[name] for name in subset]
    return float(sum(KT[a, b] for pos, a in enumerate(j) for b in j[pos + 1:]))


def subset_amplitude(subset):
    """Link-space simultaneous coverage over the omega grid, for one subset."""
    j = [INDEX[name] for name in subset]
    means = []
    for omega in OMEGAS:
        values = []
        for rep in range(REPLICATES):
            rng = np.random.default_rng(np.random.SeedSequence([SEED, rep, 470]))
            matrix = measured_errors(omega, int(DURATION / DT), DT, rng).T[j]
            sd = matrix.std(axis=1, keepdims=True)
            values.append(float((np.abs(matrix) <= Z * sd).all(axis=0).mean()))
        means.append(float(np.mean(values)))
    return {'subset': list(subset), 'K': len(subset), 'coupling_sum': coupling_sum(subset),
            'coverage_by_omega': means, 'amplitude': float(np.ptp(means))}


def scale_channel(transfer_json):
    """Per-slot scale factor omega=0 -> omega=1, read from the frozen G5 run."""
    reps = json.loads(Path(transfer_json).read_text())['results']['primary']['replicates']
    per_slot = {}
    for procedure in ('uncorrected', 'maxscore'):
        low = np.mean([r[procedure]['qhat'] for r in reps[0]], axis=0)
        high = np.mean([r[procedure]['qhat'] for r in reps[-1]], axis=0)
        ratio = np.atleast_1d(high / low)
        per_slot[procedure] = {'qhat_omega0': np.atleast_1d(low).tolist(),
                               'qhat_omega1': np.atleast_1d(high).tolist(),
                               'scale_factor': ratio.tolist(),
                               'mean_scale': float(ratio.mean()),
                               'spread_fraction_of_mean': float(np.ptp(ratio) / ratio.mean())}
    return per_slot


def equivariance():
    """Two experiments that separate the exact channel from the inexact one.

    (a) multiply the SCORE MATRIX by c: this is the mathematical property, and
        qhat must scale by exactly c with coverage bit-identical.
    (b) multiply the TWIN ERROR by c: this is what a naive 'pure scale
        surrogate' does, and it is NOT pure -- larger error re-ranks rows, so
        the rank slots are reassigned and the scaling stops being exact.
    """
    cal_true, cal_hat = make_inputs(0., 0, 0)
    test_true, test_hat = make_inputs(0., 0, 1)
    cal_s, test_s = S.pair_scores(cal_true, cal_hat), S.pair_scores(test_true, test_hat)
    base_q = S.qhat_maxscore(cal_s.max(axis=1), .10)
    base_cov = S.coverage_simultaneous(test_s, base_q)
    on_scores, on_twin = [], []
    for c in SCALES:
        q = S.qhat_maxscore((cal_s * c).max(axis=1), .10)
        cov = S.coverage_simultaneous(test_s * c, q)
        on_scores.append({'c': c, 'qhat_ratio': float(q / base_q), 'coverage': float(cov),
                          'bit_identical_to_base': bool(cov == base_cov)})
        hat_c = test_true + (test_hat - test_true) * c
        cal_c = cal_true + (cal_hat - cal_true) * c
        q_twin = S.qhat_maxscore(S.pair_scores(cal_true, cal_c).max(axis=1), .10)
        on_twin.append({'c': c, 'qhat_ratio': float(q_twin / base_q),
                        'coverage': float(S.coverage_simultaneous(S.pair_scores(test_true, hat_c), q_twin)),
                        'rows_reranked': float((S.top_k_by_twin(hat_c) != S.top_k_by_twin(test_hat)).any(axis=1).mean())})
    reranked = [{'omega': w,
                 'rows_reranked_vs_omega0':
                     float((S.top_k_by_twin(make_inputs(w, 0, 1)[1]) != S.top_k_by_twin(test_hat)).any(axis=1).mean())}
                for w in OMEGAS]
    return {'base_qhat': float(base_q), 'base_coverage': float(base_cov),
            'scaling_the_score_matrix': on_scores, 'scaling_the_twin_error': on_twin,
            'omega_reranking': reranked}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    sources = verify_protected()
    started = time.monotonic()
    subsets = [subset_amplitude(s) for s in SUBSETS]
    for row in subsets:
        print(f"{','.join(row['subset']):<40} K={row['K']} sum_k={row['coupling_sum']:6.3f} "
              f"amplitude={row['amplitude']:.6f}", flush=True)
    payload = {'schema': 'dt4n.phase_g2.g5a_mechanism_audit.v1', 'status': 'SYNTHETIC_NO_NETWORK',
               'corrects': 'docs/phase-G/70-g5-results.md section 3 explanation, not its verdict',
               'link_subsets': subsets,
               'scale_channel': scale_channel('results/SMOKE/phase-G2/g5_estimand_transfer.json'),
               'equivariance': equivariance(),
               'provenance': provenance(), 'elapsed_s': time.monotonic() - started,
               'source_sha256': {**sources, 'tools/g5a_mechanism_audit.py': sha256_of(__file__)}}
    write_contract_artifact(OUT, payload)
    print(json.dumps({'out': str(OUT), 'elapsed_s': round(payload['elapsed_s'], 1)}, indent=2))


if __name__ == '__main__':
    main()

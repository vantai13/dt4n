"""G'.6: exact fixed-path contrast SDs; approximate rank-slot scale proxy.

No fitted parameters and no new simulation. A covariance projection is exact
for fixed path identities. Its mean SD ratio is NOT a theorem for quantiles
of scores selected by a data-dependent ranking.

    python -m tools.g6_sigma_eff
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g2_topology import (
    CAP_BPS, INCIDENCE, PATHS, a0_from_sigma_at, design_covariance,
)
from tools.g5_parameters import nugget_variance

OUT = Path('results/SMOKE/phase-G2/g6_sigma_eff.json')
OMEGAS = (0., .25, .5, .75, 1.)


def contrast_sd(covariance, incidence=INCIDENCE, reference=0):
    """SD of each fixed path error minus one fixed reference path error."""
    covariance = np.asarray(covariance, dtype=float)
    incidence = np.asarray(incidence, dtype=float)
    if (incidence.ndim != 2 or incidence.shape[1] < 2 or
            not np.isfinite(incidence).all()):
        raise ValueError('incidence must contain at least two finite path columns')
    if (covariance.shape != (incidence.shape[0], incidence.shape[0]) or
            not np.isfinite(covariance).all() or
            not np.allclose(covariance, covariance.T, atol=1e-14, rtol=1e-12)):
        raise ValueError('covariance must be finite, symmetric, and match links')
    if not isinstance(reference, (int, np.integer)) or not 0 <= reference < incidence.shape[1]:
        raise ValueError('reference must be a valid path index')
    scale = max(float(np.max(np.abs(covariance))), np.finfo(float).tiny)
    if np.linalg.eigvalsh(covariance).min() < -1e-12 * scale:
        raise ValueError('covariance must be positive semidefinite')
    others = [i for i in range(incidence.shape[1]) if i != reference]
    contrasts = incidence[:, others] - incidence[:, [reference]]
    variance = np.einsum('ij,ik,kj->j', contrasts, covariance, contrasts)
    return np.sqrt(np.maximum(variance, 0.))


def effective_sigma(omega, sigma_ref=.028, dt=.1, reference=0):
    """Compute a non-fitted scale proxy for the current topology/nugget model.

    sigma_eff is a reporting coordinate. Feeding it into the original signal
    generator does not in general reproduce omega's joint score distribution.
    """
    if not np.isfinite(sigma_ref) or sigma_ref <= 0:
        raise ValueError('sigma_ref must be positive and finite')
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError('dt must be positive and finite')
    a0 = a0_from_sigma_at('uA', sigma_ref)
    nugget = np.diag(nugget_variance(CAP_BPS, dt))
    sd0 = contrast_sd(design_covariance(a0, 0.) + nugget, reference=reference)
    sd = contrast_sd(design_covariance(a0, omega) + nugget, reference=reference)
    if np.any(sd0 <= 0):
        raise ValueError('baseline contrasts must have positive variance')
    ratios = sd / sd0
    c = float(ratios.mean())
    return {'omega': float(omega), 'reference_path': PATHS[reference],
            'fixed_contrast_sd': sd.tolist(), 'fixed_contrast_sd_ratio': ratios.tolist(),
            'c_analytic_proxy': c, 'sigma_eff_proxy': float(sigma_ref * c),
            'spread_fraction': float(np.ptp(ratios) / c)}


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    rows = [effective_sigma(w) for w in OMEGAS]
    comparisons, evidence = {}, {}
    for name in ('g5b_power_axis', 'g5c_monotone'):
        path = Path(f'results/SMOKE/phase-G2/{name}.json')
        artifact = json.loads(path.read_text())
        primary = artifact['results']['primary']
        measured = primary['scale_channel']['mean_scale']
        q_ratio = primary['maxscore']['qhat_inflation']
        c = rows[-1]['c_analytic_proxy']
        comparisons[name] = {
            'measured_slot_mean_qhat_ratio': measured,
            'measured_maxscore_qhat_ratio': q_ratio,
            'relative_gap_to_slot_mean': (measured - c) / c,
            'relative_gap_to_maxscore': (q_ratio - c) / c,
            'measured_slot_spread_fraction': primary['scale_channel']['scale_spread_fraction'],
        }
        evidence[str(path)] = sha256_of(path)
    sources = ('tools/g6_sigma_eff.py', 'tools/g2_topology.py',
               'twin/topology_v7.py', 'tools/g5_parameters.py', 'tools/g4_nugget_model.py')
    payload = {
        'schema': 'dt4n.phase_g2.g6_sigma_eff.v1',
        'status': 'ANALYTIC_DIAGNOSTIC_NO_NEW_MEASUREMENT',
        'interpretation': 'exact fixed-identity contrast SD; approximate ranked-score quantile proxy',
        'design': {'sigma_ref': .028, 'reference_link': 'uA', 'dt_s': .1,
                   'reference_path_index': 0, 'omega_grid': list(OMEGAS)},
        'rows': rows, 'comparison_existing_measurements': comparisons,
        'evidence_sha256': evidence, 'source_sha256': {p: sha256_of(p) for p in sources},
        'provenance': provenance(),
    }
    write_contract_artifact(OUT, payload)
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()

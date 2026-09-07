"""Export the frozen G5c measurement to CSV and PNG without rerunning it.

    python -m tools.g5c_report
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from tools.artifact_guard import sha256_of


def main():
    base = Path('results/SMOKE/phase-G2')
    source = base / 'g5c_monotone.json'
    csv_path, png_path = base / 'g5c_by_omega.csv', base / 'g5c_monotone.png'
    for path in (csv_path, png_path):
        if path.exists():
            raise FileExistsError(path)
    artifact = json.loads(source.read_text())
    omega = artifact['design']['omega_grid']
    rows = []
    for case, block in artifact['results'].items():
        for procedure in ('maxscore', 'uncorrected'):
            p = block[procedure]
            for i, w in enumerate(omega):
                surrogate = p['surrogate_acceptance'][i]
                rows.append({
                    'case': case, 'procedure': procedure, 'omega': w,
                    'acceptance': p['acceptance_by_omega'][i],
                    'acceptance_mc_se': p['acceptance_mc_se'][i],
                    'coverage': p['coverage_by_omega'][i],
                    'surrogate_acceptance': surrogate,
                    'remainder': None if surrogate is None else p['acceptance_by_omega'][i] - surrogate,
                    'rows_reranked': block['rows_reranked'][i],
                    'source_sha256': sha256_of(source),
                })
    with csv_path.open('x', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    primary = artifact['results']['primary']['maxscore']
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), constrained_layout=True)
    axes[0].errorbar(omega, primary['acceptance_by_omega'],
                     yerr=np.asarray(primary['acceptance_mc_se']) * 1.96,
                     marker='o', capsize=4, label='Measured (±1.96 MC SE)')
    axes[0].plot(omega, [primary['acceptance_by_omega'][0]] + primary['surrogate_acceptance'][1:],
                 '--s', label='Score-scale surrogate')
    axes[0].set(ylabel='Acceptance', title='Power decreases with coupling')
    axes[1].plot(omega, primary['coverage_by_omega'], 'o-', label='Primary max-score')
    axes[1].plot(omega, artifact['results']['null_uA_uB']['maxscore']['coverage_by_omega'],
                 's--', label='Null pair')
    axes[1].axhline(.9, color='gray', linestyle=':', label='Nominal 0.90')
    axes[1].set(ylabel='Simultaneous coverage', ylim=(.895, .905), title='Coverage amplitude = %.6f' % primary['coverage_amplitude'])
    for ax in axes:
        ax.set(xlabel='Coupling ω', xticks=omega)
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.suptitle('G5c | seed 20260909 | 200 replicates | synthetic, no network', fontsize=12)
    fig.savefig(png_path, dpi=180)
    plt.close(fig)
    print(f"{artifact['verdict']} / {artifact['classification']}")
    print('omega    acceptance    MC_SE       coverage    surrogate')
    for i, w in enumerate(omega):
        s = primary['surrogate_acceptance'][i]
        print(f"{w:5.2f}    {primary['acceptance_by_omega'][i]:.8f}    "
              f"{primary['acceptance_mc_se'][i]:.8f}  {primary['coverage_by_omega'][i]:.8f}  "
              + ('—' if s is None else f'{s:.8f}'))
    print(f'CSV: {csv_path}\nPNG: {png_path}\nSource SHA256: {sha256_of(source)}')


if __name__ == '__main__':
    main()

"""Render frozen G5 artifacts as CSV and a figure. Reads only; adds no analysis.

The experiment tool is hash-referenced by its own output, so tables and plots
live here instead of being appended to it after the run.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from tools.artifact_guard import sha256_of

BASE = Path('results/SMOKE/phase-G2')
TRANSFER = BASE / 'g5_estimand_transfer.json'
DOC47 = BASE / 'g5_doc47_recomputed.json'
PROCEDURES = ('uncorrected', 'bonferroni', 'sidak', 'maxscore')


def slot_rows(transfer):
    for family, block in transfer['results'].items():
        for procedure in PROCEDURES:
            summary = block['summary'][procedure]
            for row in summary['rows']:
                yield {'family': family, 'procedure': procedure, 'omega': row['omega'],
                       'coverage_simultaneous': row['coverage'], 'replicate_sd': row['sd'],
                       'mc_se': row['mc_se'], 'marginal_slot1': row['marginal'][0],
                       'marginal_slot2': row['marginal'][1], 'marginal_slot3': row['marginal'][2],
                       'qhat_mean': sum(row['qhat']) / len(row['qhat']),
                       'acceptance': row['acceptance'],
                       'amplitude': summary['amplitude'], 'snr': summary['snr'],
                       'worst_step': summary['worst_step'],
                       'marginal_drift': summary['marginal_drift'],
                       'nc3_signed': summary['nc3_signed']}


def link_rows(doc47):
    for case in doc47['cases']:
        for row in case['rows']:
            yield {'dt_s': case['dt_s'], 'variance': case['variance'], 'noise': case['noise'],
                   'evidence_level': case['evidence_level'], 'omega': row['omega'],
                   'marginal': row['marginal'], 'joint_k2': row['joint_k2'],
                   'joint_k8': row['joint_k8'], 'joint_k8_sd': row['sd'],
                   'amplitude_k2': case['amplitude_k2'], 'amplitude_k8': case['amplitude_k8']}


def write_csv(path, rows):
    rows = list(rows)
    with open(path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return sha256_of(path)


def figure(transfer, doc47, path):
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.0))
    summary = transfer['results']['primary']['summary']
    omegas = [r['omega'] for r in summary['maxscore']['rows']]

    for procedure in PROCEDURES:
        rows = summary[procedure]['rows']
        axes[0].errorbar(omegas, [r['coverage'] for r in rows],
                         yerr=[1.96 * r['mc_se'] for r in rows], marker='o', capsize=3,
                         label=f"{procedure} (amp={summary[procedure]['amplitude']:.4f})")
    axes[0].axhline(.90, color='grey', ls=':', lw=1)
    axes[0].set_title('rank-slot simultaneous coverage (22R estimand)')
    axes[0].set_xlabel('omega'); axes[0].set_ylabel('coverage')
    axes[0].legend(fontsize=7)

    for case in doc47['cases']:
        if case['dt_s'] != .1 or case['noise'] != 'uniform_ma1':
            continue
        label = 'sf=0.85 (doc47)' if case['variance'] == 'sf85' else 'certified nugget'
        axes[1].plot(omegas, [r['joint_k8'] for r in case['rows']], marker='s',
                     label=f"K=8 {label} (amp={case['amplitude_k8']:.4f})")
        axes[1].plot(omegas, [r['joint_k2'] for r in case['rows']], marker='^', ls='--',
                     label=f"K=2 {label} (amp={case['amplitude_k2']:.4f})")
    axes[1].set_title('link-space simultaneous coverage, dt=0.1 s')
    axes[1].set_xlabel('omega'); axes[1].set_ylabel('coverage')
    axes[1].legend(fontsize=7)

    for procedure in ('uncorrected', 'maxscore'):
        rows = summary[procedure]['rows']
        axes[2].plot(omegas, [r['acceptance'] for r in rows], marker='o', label=f'{procedure} acceptance')
    axes[2].set_title('certificate acceptance rate (power)')
    axes[2].set_xlabel('omega'); axes[2].set_ylabel('fraction of windows accepted')
    axes[2].legend(fontsize=7)

    for axis in axes:
        axis.grid(alpha=.3)
    fig.suptitle('G5: omega moves link-space coverage, not rank-slot coverage', fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return sha256_of(path)


def main():
    transfer = json.loads(TRANSFER.read_text())
    doc47 = json.loads(DOC47.read_text())
    outputs = {
        str(BASE / 'g5_slot_coverage.csv'): write_csv(BASE / 'g5_slot_coverage.csv', slot_rows(transfer)),
        str(BASE / 'g5_link_coverage.csv'): write_csv(BASE / 'g5_link_coverage.csv', link_rows(doc47)),
        str(BASE / 'g5_transfer.png'): figure(transfer, doc47, BASE / 'g5_transfer.png'),
    }
    for path, digest in outputs.items():
        print(f'{digest}  {path}')


if __name__ == '__main__':
    main()

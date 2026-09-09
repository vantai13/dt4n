#!/usr/bin/env python3
"""Measure the metadata fix against pre-change code; no 20R2 grid is run."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import types

import numpy as np
import pandas as pd

from cert import build_calib_set_v3 as B
from cert import tau_sweep as TS
from measurements.validity import validity_block

BASELINE = '665bebe9'


def old_module(path):
    source = subprocess.check_output(['git', 'show', BASELINE + ':' + path], text=True)
    module = types.ModuleType('cert._20r2_baseline_' + Path(path).stem)
    module.__file__ = str(Path(path).resolve())
    exec(compile(source, path, 'exec'), module.__dict__)
    return module


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    old = old_module('cert/build_calib_set_v3.py')
    old_ts = old_module('cert/tau_sweep.py')
    old_ts.V3 = old
    rows = []
    cell = B._load_cell('poisson', .925)
    tt, cv = B.TruthTable(B.TRUTH_TABLE), B.C.CostV2(strict_reliable=False)
    for axis, profile in [(B.AXIS_LEGACY, 'U0'), (B.AXIS_MEASURED, 'U0'),
                          (B.AXIS_MEASURED, 'U1'), (B.AXIS_MEASURED, 'U3')]:
        kwargs = dict(n=20000, dt=.005, axis=axis, aoi_profile=profile)
        before, bm = old.build_one_v3(cell, 101, tt, cv, **kwargs)
        after, am = B.build_one_v3(cell, 101, tt, cv, **kwargs)
        pd.testing.assert_frame_equal(before, after, check_exact=True)
        validity = validity_block(
            aoi_generator=B.AOI_V7 if axis == B.AXIS_MEASURED else B.sawtooth_age_steps,
            z_edges=am['z_edges_primary'], sla_path=B.CALIBRATION, w_loss=am['w_loss'])
        rows.append(dict(axis=axis, profile=profile, n_rows=len(after),
                         data_bit_exact=True, before_k_min=bm['z_step_k_min'],
                         before_k_max=bm['z_step_k_max'], after_k_min=am['z_step_k_min'],
                         after_k_max=am['z_step_k_max'], z_min_s=am['z_min_realised_s'],
                         z_max_s=am['z_max_realised_s'], z_shift_ms=am['z_shift_ms'],
                         validity=validity))
    kwargs = dict(seeds=(101,), n=20000, dt=.005, sigma=.0096)
    before = old_ts.build_at_tau('poisson', .925, 1., **kwargs)
    after = TS.build_at_tau('poisson', .925, 1., axis=B.AXIS_LEGACY, **kwargs)
    pd.testing.assert_frame_equal(before, after, check_exact=True)
    tau = dict(axis=B.AXIS_LEGACY, tau=1., n_rows=len(after), data_bit_exact=True,
               dataframe_sha256=hashlib.sha256(pd.util.hash_pandas_object(after, index=True).values.tobytes()).hexdigest())
    source_hashes = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                     for path in ('cert/build_calib_set_v3.py', 'cert/tau_sweep.py')}
    baseline_commit = subprocess.check_output(['git', 'rev-parse', BASELINE], text=True).strip()
    payload = dict(schema='dt4n.20r2.remediation_smoke.v1', baseline_commit=baseline_commit,
                   source_sha256=source_hashes,
                   scope='Regression smoke on inherited self_calibrated SLA; not a 20R2 outcome grid.',
                   builder_rows=rows, tau_sweep=tau)
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    for row in rows:
        print('{axis:24s} {profile} k={before_k_min}..{before_k_max} -> {after_k_min}..{after_k_max}; '
              'z={z_min_s:.6f}..{z_max_s:.6f}s; data bit-exact={data_bit_exact}'.format(**row))
    print('tau legacy bit-exact:', tau['data_bit_exact'], 'rows=', tau['n_rows'])
    print('->', out)


if __name__ == '__main__':
    main()

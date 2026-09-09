"""20R2: axis names, real metadata and fail-loud propagation stay consistent."""
import ast
import importlib
import inspect
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from cert import build_calib_set_v3 as B
from cert import tau_sweep as TS
from measurements.validity import validity_block

CODE_TO_REGISTRY = {
    'measured_v7': 'measured_v7_uniform',
    'legacy_sawtooth_51ms': 'assumed_sawtooth_51ms',
}


@pytest.fixture(scope='module', params=[
    (B.AXIS_LEGACY, 'U0'), (B.AXIS_MEASURED, 'U0'),
    (B.AXIS_MEASURED, 'U1'), (B.AXIS_MEASURED, 'U3')])
def artifact(request):
    axis, profile = request.param
    df, meta = B.build_one_v3(
        B._load_cell('poisson', .925), 101, B.TruthTable(B.TRUTH_TABLE),
        B.C.CostV2(strict_reliable=False), n=20000, aoi_profile=profile, axis=axis)
    validity = validity_block(
        aoi_generator=B.AOI_V7 if axis == B.AXIS_MEASURED else B.sawtooth_age_steps,
        z_edges=meta['z_edges_primary'], sla_path=B.CALIBRATION,
        w_loss=meta['w_loss'])
    return {'meta': meta, 'validity': validity, 'data': df}


def test_axis_names_map_one_to_one(artifact):
    assert len(set(CODE_TO_REGISTRY.values())) == len(CODE_TO_REGISTRY)
    assert CODE_TO_REGISTRY[artifact['meta']['axis']] == artifact['validity']['aoi_axis']['label']


def test_metadata_age_steps_agree_with_generated_rows(artifact):
    m, df = artifact['meta'], artifact['data']
    shift = m['z_shift_ms'] / 1000
    for bound in ('min', 'max'):
        # k describes base age; z includes the mean per-link offset.
        predicted = m['z_step_k_' + bound] * B.DT + shift
        assert predicted == pytest.approx(m['z_' + bound + '_realised_s'], abs=1e-12)
        assert predicted == pytest.approx(getattr(df.z_s, bound)(), abs=1e-7)


def test_axis_is_required_and_keyword_only():
    p = inspect.signature(B._valid_rows).parameters['axis']
    assert p.default is inspect.Parameter.empty
    assert p.kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError, match='axis'):
        B._valid_rows(1000, B.DT)
    with pytest.raises(TypeError):
        B._valid_rows(1000, B.DT, B.D_SYNC, B.AXIS_LEGACY)


def test_all_production_valid_rows_calls_have_axis():
    root = Path(__file__).resolve().parents[1]
    missing = []
    for folder in ('cert', 'measurements', 'tools'):
        for path in (root / folder).glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Call):
                    name = getattr(node.func, 'attr', getattr(node.func, 'id', None))
                    if name == '_valid_rows' and not any(k.arg == 'axis' for k in node.keywords):
                        missing.append(f'{path}:{node.lineno}')
    assert not missing, missing


def test_tau_sweep_requires_axis_and_rejects_unregistered_measured_design():
    with pytest.raises(TypeError, match='axis'):
        TS.build_at_tau('poisson', .925, 1, sigma=.0096)
    with pytest.raises(ValueError, match='prereg'):
        TS.build_at_tau('poisson', .925, 1, sigma=.0096, axis=B.AXIS_MEASURED)
    run = subprocess.run([sys.executable, '-m', 'cert.tau_sweep', '--mode', 'poisson',
                          '--rho-bar', '.925', '--out', '/tmp/unused-20r2.json', '--a', '.9'],
                         capture_output=True, text=True)
    assert run.returncode == 2
    assert '--axis' in run.stderr


def test_audit_distinguishes_direct_generator_and_axis_guard():
    audit = importlib.import_module('tools.20r2_0_axis_audit')
    calls = audit.scan_calls(str(Path(B.__file__)))
    calls = [c for c in calls if c['enclosing_function'] == 'build_one_v3'
             and c['callee'] in ('sawtooth_age_steps', 'base_age_steps')]
    assert len(calls) == 2
    assert all(c['direct_generator_call'] and c['enclosing_axis_guards'] for c in calls)

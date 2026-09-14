"""A1: pin resolution, actual axis leaves, and visible debt for unpinned documents."""
import importlib
from pathlib import Path
import pytest
T=importlib.import_module('tools.20r2_9_axis_chain')
ROOT=Path(__file__).resolve().parents[1]

def test_pin_bearing_artifacts_resolve_to_their_expected_axis_contexts():
    result=T.audit(ROOT)
    assert result['summary']['n_pin_bearing']==4
    assert result['summary']['n_without_canonical_pins']==9
    assert result['summary']['gate_20R2_6a'].startswith('FAIL')
    adjudication=next(r for r in result['derived'] if r['artifact'].endswith('/06-adjudication.json'))
    log=next(r for r in adjudication['inputs'] if r['path'].endswith('.jsonl'))
    assert log['campaign_noncanary_count']==160
    assert len(log['campaign_axis_contexts'])==2

@pytest.mark.parametrize('name',sorted(T.NO_PINS_YET))
def test_missing_canonical_pins_are_declared_as_debt(name):
    assert (ROOT/'docs/phase-20R2'/name).is_file()
    pytest.skip('20R2-D11: frozen source has no canonical inputs_sha256; tracked in 99b-gate-ledger.md')

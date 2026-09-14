"""A3: exemptions expire when their precise blocker is removed."""
import json
from pathlib import Path
import pytest
from test_no_stale_axes import PENDING_NO_VALIDITY_GRANDFATHERED as GF
ROOT = Path(__file__).resolve().parents[1]

def has_validity(rel):
    p=ROOT/'results/PENDING'/rel
    return p.is_file() and bool(json.loads(p.read_text()).get('validity'))

def tau_registered():
    reg=json.loads((ROOT/'docs/phase-23/axis_registry.json').read_text())
    return 'tau_axis' in reg

def tool_restored(name):
    return (ROOT/'tools'/name).is_file()

R3_FILES = ['phase-T2/sweep_r3/adjudication_r3.json', 'phase-T2/sweep_r3/hygiene_r3.json', 'phase-T2/sweep_r3/hygiene_r3_FAIL_before_table_erratum.json', 'phase-T2/sweep_r3/legacy_cbr_0.700.json', 'phase-T2/sweep_r3/legacy_h2_0.700.json', 'phase-T2/sweep_r3/legacy_poisson_0.850.json', 'phase-T2/sweep_r3/legacy_poisson_0.925.json', 'phase-T2/sweep_r3/level_probe_posthoc.json', 'phase-T2/sweep_r3/sigmaprobe_cbr_0.700.json', 'phase-T2/sweep_r3/sigmaprobe_h2_0.700.json', 'phase-T2/sweep_r3/sigmaprobe_poisson_0.850.json', 'phase-T2/sweep_r3/sigmaprobe_poisson_0.925.json', 'phase-T2/sweep_r3/t2_6b_r000.json', 'phase-T2/sweep_r3/t2_6b_r001.json', 'phase-T2/sweep_r3/t2_6b_r002.json', 'phase-T2/sweep_r3/t2_6b_r003.json', 'phase-T2/sweep_r3/t2_6b_r004.json', 'phase-T2/sweep_r3/t2_6b_r005.json', 'phase-T2/sweep_r3/t2_6b_r006.json', 'phase-T2/sweep_r3/t2_6b_r007.json', 'phase-T2/sweep_r3/t2_6b_r008.json', 'phase-T2/sweep_r3/t2_6b_r009.json', 'phase-T2/sweep_r3/t2_6b_r010.json', 'phase-T2/sweep_r3/t2_6b_r011.json', 'phase-T2/sweep_r3/t2_6b_r012.json', 'phase-T2/sweep_r3/t2_6b_r013.json', 'phase-T2/sweep_r3/t2_6b_r014.json', 'phase-T2/sweep_r3/t2_6b_r015.json', 'phase-T2/sweep_r3/t2_6b_r016.json', 'phase-T2/sweep_r3/t2_6b_r017.json']  # Filled once from the existing registry, never inferred at test time.
EXPIRY = {rel: (lambda rel=rel: has_validity(rel) or tau_registered()) for rel in R3_FILES}
EXPIRY['phase-T2/gate_v2_retro_audit.json'] = lambda: has_validity('phase-T2/gate_v2_retro_audit.json') or tau_registered()
EXPIRY['phase-23/eight_cell_sweep_U3_measured_v7_slaB.json'] = lambda: has_validity('phase-23/eight_cell_sweep_U3_measured_v7_slaB.json')
PRODUCERS = {
 'phase-T2/clip_direction_r2.json':'t2_clip_direction.py',
 'phase-T2/preservation_r2.json':'t2_preservation.py',
 'phase-T2/conformal_u_main.json':'t2_conformal_u.py',
 'phase-T2/conformal_u_cond.json':'t2_conformal_u.py',
 'phase-T2/conformal_u_cond_load.json':'t2_conformal_u.py',
 'phase-T2/calib_p0925_tau10_report.json':'t2_calib_report.py',
 'phase-T2/calib_p0925_tau10_v3_report.json':'t2_calib_report.py',
}
for rel, tool in PRODUCERS.items():
    EXPIRY[rel] = lambda rel=rel, tool=tool: has_validity(rel) or tool_restored(tool)
EXPIRY['phase-T2/adjudication_r2.json'] = lambda: has_validity('phase-T2/adjudication_r2.json')

def test_every_grandfather_entry_has_a_machine_checkable_expiry():
    assert not set(GF)-set(EXPIRY), 'new exemption needs an explicit expiry predicate'

@pytest.mark.parametrize('rel',sorted(EXPIRY))
def test_grandfather_entry_is_removed_once_its_condition_is_met(rel):
    if rel not in GF:
        return
    assert not EXPIRY[rel](), 'expiry satisfied; remove exemption: '+rel

def test_cleanup_fails_when_replacement_producer_appears(tmp_path,monkeypatch):
    monkeypatch.setitem(globals(),'ROOT',tmp_path)
    (tmp_path/'tools').mkdir()
    rel='phase-T2/calib_p0925_tau10_report.json'
    assert not EXPIRY[rel]()
    (tmp_path/'tools/t2_calib_report.py').write_text('# replacement producer')
    with pytest.raises(AssertionError,match='remove exemption'):
        test_grandfather_entry_is_removed_once_its_condition_is_met(rel)

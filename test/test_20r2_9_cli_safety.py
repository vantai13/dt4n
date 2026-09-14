"""CLI selection and imports must not start or perturb another experiment."""
import importlib
import subprocess
import sys
import pytest

MODULES = ['tools.g2_kill_test', 'tools.g3a_omega_sweep', 'tools.g3b_sigma_tau_grid']
@pytest.mark.parametrize('module', MODULES)
@pytest.mark.parametrize('args', [[], ['--setup', '--run']])
def test_no_or_conflicting_mode_fails_before_any_action(module, args, monkeypatch):
    m = importlib.import_module(module)
    def forbidden(*a, **kw):
        pytest.fail('a campaign action ran before a valid mode was selected')
    for name in ['setup','teardown','_run']:
        monkeypatch.setattr(m, name, forbidden)
    monkeypatch.setattr(sys, 'argv', [module, *args])
    with pytest.raises(SystemExit) as exc:
        m.main()
    assert exc.value.code == 2

@pytest.mark.parametrize('module', MODULES)
def test_run_flag_dispatches_once_without_starting_network_in_test(module, monkeypatch):
    m = importlib.import_module(module); seen=[]
    monkeypatch.setattr(m, '_run', lambda *a, **kw: seen.append((a,kw)))
    monkeypatch.setattr(sys, 'argv', [module,'--run'])
    m.main()
    assert len(seen)==1

def test_all_foreign_global_imports_are_inert_in_both_orders():
    mods=MODULES+['tools.g2_kill_null','tools.g3a_gate_calibration','tools.g5c_monotone']
    for order in (mods, list(reversed(mods))):
        script=('import importlib\nfrom tools import g3_dryrun as g3, g5b_power_axis as g5\n'
                'before=(g3.DT_S,g5.SEED)\n'
                f'for name in {order!r}: importlib.import_module(name)\n'
                'assert (g3.DT_S,g5.SEED)==before\n')
        r=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True)
        assert r.returncode==0,r.stderr

def test_g5_seed_scope_restores_after_exception():
    from tools import g5c_monotone as m
    before=m.g5b.SEED
    with pytest.raises(RuntimeError):
        with m._seed_c():
            assert m.g5b.SEED==m.SEED_C
            raise RuntimeError('injected failure')
    assert m.g5b.SEED==before

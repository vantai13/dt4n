"""S2 controls: original source replay, nonzero identity, threshold mutation and runner guards."""
import importlib
import json
import subprocess
import types
import numpy as np
import pytest
from measurements import decision_error_v2 as DE
from tools import sensitivity_20r2 as C
R=importlib.import_module('tools.20r2_9_s2_run')

def test_grid_addition_preserves_every_original_value_and_identity():
    source=subprocess.check_output(['git','show','1de19e1c:measurements/decision_error_v2.py'],cwd=C.ROOT,text=True)
    old=types.ModuleType('historical_de');old.__file__=str(C.ROOT/'measurements/decision_error_v2.py')
    exec(compile(source,old.__file__,'exec'),old.__dict__)
    cell=next(c for c in DE.feasible_cells(C.EXO) if c['mode']=='h2' and c['rho_bar']==.85)
    cv=DE.C.CostV2(fit_path='results/LIVE/phase-L/link_model_v2_fit.json',strict_reliable=False)
    kw=dict(seed=101,tau=3.,n=200000,z_values=DE.Z_ALL_20R2,a_override=.9)
    before=old.run_cell(DE.TruthTable(DE.TRUTH_TABLE),cv,cell,**kw)
    no_grid=DE.run_cell(DE.TruthTable(DE.TRUTH_TABLE),cv,cell,**kw,sla_grid=None)
    grid=DE.run_cell(DE.TruthTable(DE.TRUTH_TABLE),cv,cell,**kw,sla_grid=C.GRID)
    extra=grid.pop('sla_grid')
    assert json.dumps(before,sort_keys=True)==json.dumps(no_grid,sort_keys=True)==json.dumps(grid,sort_keys=True)
    assert len(extra)==1404
    assert any(r['d_sla_at_threshold']!=0 for r in extra)
    for r in extra:
        if (r['t_delay_ms'],r['t_loss'])==(50.,.01):
            assert r['d_sla_at_threshold']==grid['per_z'][DE.z_key(r['z_s'])]['d_sla']

def test_identity_control_is_not_only_zero_on_a_saturated_cell(monkeypatch):
    n=1000;d=np.tile([[60.,40.]],(n,1));l=np.zeros_like(d)
    def arrays(*a,**kw):return dict(d_true=d,d_fresh=d,a_true=np.zeros(n,dtype=int),
        a_fresh=np.ones(n,dtype=int),l_true=l,viol=d>50,tt_domain_clip={},ar1_clip_ratio=0.,ar1_cycles=1.)
    monkeypatch.setattr(DE,'_cell_arrays',arrays)
    monkeypatch.setattr(DE,'resolve_sigma',lambda *a,**kw:(.01,'test'))
    monkeypatch.setattr(DE,'scoring_window_start',lambda *a:1)
    c=dict(mode='h2',rho_bar=.85,w_loss=5000.,t_delay_ms=50.,t_loss=.01)
    r=DE.run_cell(None,None,c,seed=101,n=n,z_values=(0.,),sla_grid=((50.,.01),))
    assert r['sla_grid'][0]['d_sla_at_threshold']==r['per_z']['0.000']['d_sla']==-1.

@pytest.mark.parametrize('grid',[[],[(50.,.01),(50.,.01)],[(float('nan'),.1)],[(50.,2.)]])
def test_invalid_grid_rejected_before_io(grid):
    with pytest.raises(ValueError,match='sla_grid'):DE.run_cell(None,None,{},seed=1,sla_grid=grid)

@pytest.mark.parametrize('failure',['local_tag','remote_tag','dirty','instrument','remote_target','head'])
def test_six_guard_failures_stop_before_work(failure,monkeypatch):
    def git(*args):
        if args[:2]==('tag','-l'):return '' if failure=='local_tag' else R.TAG
        if args[0]=='ls-remote':
            if args[-1].endswith('^{}'):return ('moved' if failure=='remote_target' else 'signed')+'\tref'
            return '' if failure=='remote_tag' else 'tag ref'
        if args[0]=='status':return ' M code.py' if failure=='dirty' else ''
        if args[0]=='diff':return 'code.py' if failure=='instrument' else ''
        if args[0]=='rev-parse':return 'different' if args[-1]=='HEAD' and failure=='head' else 'signed'
        return ''
    monkeypatch.setattr(R.LEGACY,'_git',git)
    with pytest.raises(SystemExit):R.guard()

def test_resume_detects_hash_tampering_and_orphans_are_preserved(tmp_path,monkeypatch):
    monkeypatch.setattr(C,'ROOT',tmp_path)
    p=tmp_path/'cell.parquet';p.write_bytes(b'original')
    s=tmp_path/'cell_report.json';s.write_bytes(b'{}')
    run={'out':'cell.parquet'};e={'sha256':R.LEGACY._sha(p),'sidecar_sha256':R.LEGACY._sha(s)}
    R.verify_completed(run,e);p.write_bytes(b'changed')
    with pytest.raises(SystemExit):R.verify_completed(run,e)
    entries=[];b=types.SimpleNamespace(append_log=entries.append,_now=lambda:'test')
    R.quarantine_orphans(run,b)
    assert len(entries)==2 and not p.exists() and not s.exists()
    assert (tmp_path/entries[0]['moved_to']).read_bytes()==b'changed'

def test_plan_is_deterministic_and_has_exact_signed_factorial():
    P=importlib.import_module('tools.20r2_9_s2_plan')
    first=P.build();second=P.build()
    assert first==second
    assert len(first['runs'])==320
    assert len({(r['cell'],r['tau'],r['seed']) for r in first['runs']})==320
    assert first['grid']['T_delay_ms']==list(C.TD) and first['grid']['T_loss']==list(C.TL)
    assert all(r['a']==.9 and r['n']*.005/r['tau']>=200 for r in first['runs'])

def test_seed_aggregation_does_not_conflate_saturated_and_zero_effect():
    import pandas as pd
    S=importlib.import_module('tools.20r2_9_s2_summarize')
    rows=[]
    for td,truth in [(14.,1.),(50.,0.),(40.,.5)]:
        for seed in C.SEEDS:
            rows.append(dict(cell='h2@0.850',tau=3.,z_s=.366,t_delay_ms=td,t_loss=.01,
                seed=seed,d_sla_at_threshold=0.,viol_rate_truth=truth,viol_rate_twin=truth))
    out=S.aggregate(pd.DataFrame(rows)).set_index('t_delay_ms')
    assert out.loc[14.,'truth_region']=='ALL_SEEDS_TRUTH_ONE'
    assert out.loc[50.,'truth_region']=='ALL_SEEDS_TRUTH_ZERO'
    assert out.loc[40.,'truth_region']=='TRUTH_INTERIOR_OR_SEED_MIXED'
    assert set(out.effect_region)=={'ALL_SEEDS_ZERO'}

def test_reused_ledger_flushes_and_fsyncs_each_record(tmp_path,monkeypatch):
    monkeypatch.setattr(C,'ROOT',tmp_path);calls=[]
    monkeypatch.setattr(R.LEGACY.os,'fsync',lambda fd:calls.append(fd))
    original=R.LEGACY.LOG
    with R.backend() as b:
        b.append_log({'kind':'test','value':1})
        assert b.read_log()==[{'kind':'test','value':1}]
    assert len(calls)==1 and R.LEGACY.LOG==original

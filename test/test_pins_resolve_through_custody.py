"""Custody entries must reproduce historical bytes and reject prediction mutations."""
import copy,importlib,json
from pathlib import Path
import pytest
from tools import artifact_custody as C
ROOT=Path(__file__).resolve().parents[1]
D=importlib.import_module('tools.20r2_9_custody_diff')

def test_prediction_custody_event_reproduces_and_changes_only_documented_metadata():
    e=C.load_events(ROOT)[0]
    C.validate_event(ROOT,e)
    assert e['numeric_fields_total']==149
    assert len(e['numeric_diff'])==5
    assert set(e['numeric_diff'])==C.CODE_LINES
    assert C.resolve_pin(ROOT,e['path'],e['sha_before'],[e])['status']=='CUSTODY'

@pytest.mark.parametrize('mutation',['missing','after_hash','approval','numeric_count'])
def test_forged_or_missing_custody_does_not_resolve(mutation):
    e=copy.deepcopy(C.load_events(ROOT)[0]);events=[e]
    if mutation=='missing':events=[]
    elif mutation=='after_hash':e['sha_after']='0'*64
    elif mutation=='approval':e['verdict_affected']=None
    else:e['numeric_fields_changed']=0
    with pytest.raises(AssertionError):C.resolve_pin(ROOT,e['path'],e['sha_before'],events)

@pytest.mark.parametrize('change',[{'prediction':2},{'prediction':True},{'prediction':None},{'prediction':'1'}])
def test_diff_does_not_lose_numeric_boolean_null_or_type_changes(change):
    result=D.compare(b'{"prediction":1}',json.dumps(change).encode())
    assert '/prediction' in result['all_field_diff']

def test_prediction_change_cannot_be_excused_by_a_false_verdict_flag(tmp_path,monkeypatch):
    old=b'{"prediction":1}';new=b'{"prediction":2}'
    e={'path':C.PRED,'commit_before':'old','commit_after':'new','sha_before':C.sha(old),
       'sha_after':C.sha(new),**D.compare(old,new),'verdict_affected':False,'review':{'text':'approved'}}
    monkeypatch.setattr(C.DIFF,'at',lambda root,commit,path:old if commit=='old' else new)
    with pytest.raises(AssertionError,match='prediction content changed'):C.validate_event(tmp_path,e)

"""Regeneration must reject changed evidence and restore an overwritten original."""
import importlib,json,shlex,sys
import pytest
T=importlib.import_module('tools.20r2_9_backfill_validity')

@pytest.mark.parametrize('case',['ok','numeric_change','nested_validity_change','no_validity','bad_json','failure','overwrite'])
def test_backfill_transaction(case,tmp_path):
    before={'value':17,'nested':{'validity':{'value':1}}}
    p=tmp_path/'artifact.json';raw=json.dumps(before).encode();p.write_bytes(raw)
    after={**before,'validity':{'schema':'dt4n.validity.v1'}}
    if case=='numeric_change':after['value']=18
    if case=='nested_validity_change':after['nested']={'validity':{'value':2}}
    if case=='no_validity':after.pop('validity')
    payload='invalid JSON' if case=='bad_json' else json.dumps(after)
    code=f'from pathlib import Path; import sys; Path(sys.argv[1]).write_text({payload!r})'
    if case=='failure':code+='; sys.exit(1)'
    if case=='overwrite':code+=f'; Path({str(p)!r}).write_text("corrupted")'
    cmd=shlex.join([sys.executable,'-c',code,'{out}'])
    if case=='ok':
        assert T.backfill(tmp_path,'artifact.json',cmd)['non_validity_canonical_bytes_identical']
        assert T.scientific_bytes(p.read_bytes())==T.scientific_bytes(raw)
    else:
        with pytest.raises((AssertionError,ValueError)):
            T.backfill(tmp_path,'artifact.json',cmd)
        assert p.read_bytes()==raw

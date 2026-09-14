"""Resolve pins through checked historical bytes, never through a bare approval flag."""
from __future__ import annotations
import hashlib
import importlib
import json
import pathlib

DIFF=importlib.import_module('tools.20r2_9_custody_diff')
PRED='docs/phase-20R2/01-prediction-signed.json'
CODE_LINES={
 '/estimands/DECISION_ERR_BY_AGE/ARTIFACT_FIELD_LINE',
 '/estimands/DECISION_ERR_BY_AGE/DECOMPOSITION/per_z[<z_key>].err_model',
 '/estimands/DECISION_ERR_BY_AGE/DECOMPOSITION/per_z[<z_key>].err_stale',
 '/estimands/DECISION_ERR_BY_AGE/DECOMPOSITION/per_z[<z_key>].extrapolated',
 '/estimands/SLA_VIOL_BY_AGE/ARTIFACT_FIELD_LINE',
}
TEXT_METADATA={'/generated_utc'}|{
 '/estimands/SLA_VIOL_BY_AGE/'+k for k in ('CORRECTED','IDENTITY','SCALE','UNIT')}

def sha(data):return hashlib.sha256(data).hexdigest()

def validate_event(root, event):
    old=DIFF.at(root,event['commit_before'],event['path'])
    new=DIFF.at(root,event['commit_after'],event['path'])
    assert sha(old)==event['sha_before'] and sha(new)==event['sha_after'], 'custody historical hash mismatch'
    actual=DIFF.compare(old,new)
    for key in actual:assert actual[key]==event[key], 'custody diff was not reproduced: '+key
    assert event['path']==PRED, 'unreviewed custody artifact'
    assert set(actual['all_field_diff']) <= CODE_LINES|TEXT_METADATA, 'prediction content changed'
    assert set(actual['numeric_diff']) <= CODE_LINES, 'numeric prediction changed'
    assert event.get('verdict_affected') is False and event.get('review'), 'missing explicit review'
    return new

def resolve_pin(root, rel, expected, events):
    path=(root/rel).resolve()
    assert path.is_relative_to(root.resolve()), 'pin escapes repository'
    assert path.is_file(), 'missing pinned file: '+rel
    current=path.read_bytes()
    if sha(current)==expected:return {'status':'CURRENT','bytes':current}
    matches=[e for e in events if e['path']==rel and e['sha_before']==expected]
    assert len(matches)==1, 'unexplained or ambiguous dangling pin: '+rel
    event=matches[0];new=validate_event(root,event)
    assert new==current, 'custody after-version differs from current bytes'
    return {'status':'CUSTODY','bytes':DIFF.at(root,event['commit_before'],rel)}

def load_events(root):
    return json.loads((root/'docs/CUSTODY_LEDGER.json').read_text())['events']

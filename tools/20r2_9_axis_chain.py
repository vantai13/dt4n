#!/usr/bin/env python3
"""Audit frozen derived artifacts, historical pins and actual campaign axis leaves."""
from __future__ import annotations
import argparse,json,pathlib
from tools.artifact_custody import load_events,resolve_pin,sha
ROOT=pathlib.Path(__file__).resolve().parents[1]
NO_PINS_YET={
 '01-prediction-signed.json','02-se-pilot.json','05-hygiene.json','06b-per-cell.json',
 '06c-g4-predictions.json','06c-g4-score.json','07-dsla.json','07a-dsla-structure.json',
 '08-handoff-measurements.json'}

def audit(root):
    events=load_events(root)
    registry=json.loads((root/'docs/phase-23/axis_registry.json').read_text())['sla_axis']
    docs=[];edge_cache={}
    def walk(rel,want,stack):
        assert rel not in stack, 'cycle in input pins: '+rel
        key=(rel,want)
        if key in edge_cache:return edge_cache[key]
        pinned=resolve_pin(root,rel,want,events)
        raw=pinned['bytes'];out={'path':rel,'pin_status':pinned['status'],'sla_labels':[],
                                 'unresolved_leaves':[],'children':[]}
        if rel in registry:
            assert sha(raw)==registry[rel]['content_sha256'], 'registered axis hash mismatch'
            out['sla_labels']=[registry[rel]['label']]
        elif rel.endswith('.jsonl'):
            runs=[json.loads(x) for x in raw.splitlines() if x.strip()]
            runs=[e for e in runs if e.get('kind')=='run' and e.get('returncode')==0]
            assert runs, 'empty campaign ledger'
            axes=[]
            for e in runs:
                resolve_pin(root,e['out'],e['sha256'],events)
                side=str(pathlib.Path(e['out']).with_name(pathlib.Path(e['out']).stem+'_report.json'))
                sidebytes=resolve_pin(root,side,e['sidecar_sha256'],events)['bytes']
                if e.get('is_canary'):continue
                v=json.loads(sidebytes)['validity'];s=v['sla_axis']
                leaf=walk(s['source_path'],s['source_sha256'],stack+(rel,))
                assert leaf['sla_labels']==[s['label']], 'sidecar SLA declaration disagrees with its pinned source'
                assert v['aoi_axis']['label']=='aoi_axis_free'
                expected='20r2_measured' if e['branch']=='main' else 'legacy'
                assert v['z_grid_id']==expected, 'branch age-grid identity mismatch'
                axes.append({'branch':e['branch'],'sla':s['label'],'aoi':v['aoi_axis']['label'],'z_grid':v['z_grid_id']})
            out['campaign_noncanary_count']=len(axes)
            out['campaign_axis_contexts']=[dict(zip(('branch','sla','aoi','z_grid'),x))
                for x in sorted({tuple(a[k] for k in ('branch','sla','aoi','z_grid')) for a in axes})]
            out['sla_labels']=sorted({a['sla'] for a in axes})
        elif rel.endswith('.json'):
            obj=json.loads(raw);pins=obj.get('inputs_sha256',{}) if isinstance(obj,dict) else {}
            if pins:
                out['children']=[walk(p,h,stack+(rel,)) for p,h in pins.items()]
                out['sla_labels']=sorted({x for c in out['children'] for x in c['sla_labels']})
                out['unresolved_leaves']=sorted({x for c in out['children'] for x in c['unresolved_leaves']})
            else:
                out['unresolved_leaves']=[rel]
                if isinstance(obj,dict) and obj.get('validity'):
                    out['declared_validity']=obj['validity']
        # Truth-table parquet is environmental input, not an SLA declaration.
        edge_cache[key]=out
        return out
    for p in sorted((root/'docs/phase-20R2').glob('*.json')):
        obj=json.loads(p.read_text());pins=obj.get('inputs_sha256',{})
        if not pins:
            assert p.name in NO_PINS_YET, 'new derived artifact lacks source pins: '+p.name
            docs.append({'artifact':str(p.relative_to(root)),'status':'DEBT_D11_NO_CANONICAL_PINS'})
            continue
        children=[walk(rel,want,(str(p.relative_to(root)),)) for rel,want in pins.items()]
        labels=sorted({label for c in children for label in c['sla_labels']})
        expected=['exogenous_g114_S-B','self_calibrated'] if p.name=='E1b-partition-invariance.json' else ['exogenous_g114_S-B']
        assert labels==expected, 'unexpected or conflicting SLA lineage: '+p.name+repr(labels)
        docs.append({'artifact':str(p.relative_to(root)),'status':'PINS_RESOLVED',
                     'sla_labels':labels,'comparison_control_exception':p.name=='E1b-partition-invariance.json',
                     'all_artifact_axes_explicit':False,'inputs':children})
    return {'schema':'dt4n.axis_chain_20r2_a1.v1','derived':docs,
            'summary':{'n_derived':len(docs),'n_pin_bearing':sum(d['status']=='PINS_RESOLVED' for d in docs),
                       'n_without_canonical_pins':sum(d['status']!='PINS_RESOLVED' for d in docs),
                       'gate_20R2_6a':'FAIL_WITH_PARTIAL_LINEAGE_REPAIR',
                       'note':'Resolvable pinned SLA evidence does not make every frozen artifact explicitly declare all axes. D11 remains open.'}}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True)
    a=ap.parse_args();out=audit(ROOT);p=ROOT/a.out;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps(out['summary'],ensure_ascii=False))
    return 0
if __name__=='__main__':raise SystemExit(main())

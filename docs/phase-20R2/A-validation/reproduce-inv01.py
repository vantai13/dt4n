# Run from repository root; writes only INV-01 evidence in A-validation.
import hashlib,importlib,json,runpy,subprocess
from pathlib import Path
root=Path.cwd();out=root/'docs/phase-20R2/A-validation'
t=runpy.run_path('test/test_phase23_cell_margins.py');CM=t['CM'];strip=t['_without_artifact_identity']
p=Path(t['HISTORICAL_REPORTS']['g23-17c'][1]);old=json.loads(p.read_text());new=CM.run_scale_sla_report(CM.DEFAULT_CELLS,rowset='test')
(out/'g23-17c-current.json').write_text(json.dumps(new,indent=2)+'\n')
d=importlib.import_module('tools.20r2_9_custody_diff').compare(json.dumps(strip(old)).encode(),json.dumps(strip(new)).encode())
for k,v in d['all_field_diff'].items():
 a,b=v['before'],v['after']
 if type(a) in (int,float) and type(b) in (int,float):
  v['absolute_error']=abs(b-a);v['sign_changed']=a*b<0
  v['classification']='rounding_le_1e-12' if abs(b-a)<=1e-12 else 'meaningful_numeric_difference'
files=[str(p),'cert/phase23_cell_margins.py',*CM.DEFAULT_CELLS.values()]
files += [str(CM._meta_path(x)) for x in CM.DEFAULT_CELLS.values()]
d['input_sha256']={f:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in files}
d['published_provenance']=old.get('provenance');d['current_provenance']=new.get('provenance')
d['investigation_status']='OPEN';d['comparison']='Exact published-number regression comparator, excluding only artifact identity fields already excluded by the unchanged test.'
(out/'g23-17c-diff.json').write_text(json.dumps(d,indent=2)+'\n')
with (out/'g23-17c-history.txt').open('w') as f:
 for path in files:
  f.write('\nPATH '+path+'\n');f.write(subprocess.check_output(['git','log','--all','--follow','--format=%h %ad %s','--date=iso','--',path],text=True))
r=subprocess.run(['rg','-n','-i','g23[-_]17c','docs','--glob','!A-validation/**'],text=True,capture_output=True)
(out/'g23-17c-doc-references.txt').write_text(r.stdout)
print(json.dumps(d['all_field_diff'],indent=2));print('files',files)

import ast,hashlib,importlib,json,platform,subprocess,sys
from pathlib import Path
import numpy,pandas,pyarrow
out=Path('docs/phase-20R2/A-validation');d=json.loads((out/'g23-17c-diff.json').read_text());old=json.loads(Path('results/SUPERSEDED/phase-23/g23_17c_scale_and_sla.json').read_text());current=json.loads((out/'g23-17c-current.json').read_text())
r={'python':sys.version,'numpy':numpy.__version__,'pandas':pandas.__version__,'pyarrow':pyarrow.__version__,'platform':platform.platform(),'checks_identical':old['checks']==current['checks'],'rows':[]}
for a,b in zip(old['rows'],current['rows']):
 r['rows'].append({'cell':a['cell'],'published_artifact':a.get('artifact'),'current_artifact':b.get('artifact'),'published_sha256':a.get('artifact_sha256'),'current_sha256':b.get('artifact_sha256'),'same_raw_hash':a.get('artifact_sha256')==b.get('artifact_sha256')})
source=subprocess.check_output(['git','show','ab2ffb2fde2c05abccc28275756c33b55b2a2e8f:cert/phase23_cell_margins.py'],text=True)
now=Path('cert/phase23_cell_margins.py').read_text()
functions=lambda s:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
a,b=functions(source),functions(now)
r['functions_changed_since_published_source']=[k for k in set(a)|set(b) if a.get(k)!=b.get(k)]
(out/'g23-17c-provenance-check.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
# Exclude this evidence folder from reference capture to avoid self references.
r=subprocess.run(['rg','-n','-i','g23[-_]17c','docs','--glob','!**/A-validation/**','--glob','!**/INV-01*'],capture_output=True,text=True)
(out/'g23-17c-doc-references.txt').write_text(r.stdout)

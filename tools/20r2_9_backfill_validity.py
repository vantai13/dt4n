#!/usr/bin/env python3
"""Regenerate into a temporary output; replace only after an exact payload check."""
from __future__ import annotations
import argparse,hashlib,json,pathlib,shlex,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]

def scientific_bytes(data):
    # Strip only the new TOP-LEVEL validity block. No recursive/number exclusions.
    obj=json.loads(data)
    assert isinstance(obj,dict), 'expected an object artifact'
    return json.dumps({k:v for k,v in obj.items() if k!='validity'},
                      sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def backfill(root, artifact, command):
    art=(root/artifact).resolve()
    assert art.is_relative_to(root.resolve())
    before=art.read_bytes()
    assert '{out}' in command or '{csv}' in command, 'generator must use a temporary-output placeholder'
    try:
        with tempfile.TemporaryDirectory(prefix='20r2-a3-') as td:
            output=pathlib.Path(td)/art.name
            csv=output.with_name(output.name.replace('.meta.json','.csv'))
            argv=[x.replace('{out}',str(output)).replace('{csv}',str(csv)) for x in shlex.split(command)]
            proc=subprocess.run(argv,cwd=root,capture_output=True,text=True)
            assert proc.returncode==0, 'generator failed: '+proc.stderr[-3000:]
            assert art.read_bytes()==before, 'generator overwrote the evidence instead of temporary output'
            after=output.read_bytes()
            assert scientific_bytes(before)==scientific_bytes(after), 'non-validity content changed'
            assert json.loads(after).get('validity'), 'generator did not emit validity'
            # Traces must also regenerate the exact CSV, not merely its metadata.
            if art.name.endswith('.meta.json'):
                stored_csv=art.with_name(art.name.replace('.meta.json','.csv'))
                assert csv.read_bytes()==stored_csv.read_bytes(), 'trace CSV changed'
            art.write_bytes(after)
            return {'artifact':artifact,'generator_argv':argv,'returncode':proc.returncode,
                    'sha_before':hashlib.sha256(before).hexdigest(),
                    'sha_after':hashlib.sha256(after).hexdigest(),
                    'non_validity_canonical_bytes_identical':True,
                    'generator_stdout':proc.stdout,'generator_stderr':proc.stderr}
    except BaseException:
        if art.read_bytes()!=before:art.write_bytes(before)
        raise

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--artifact',required=True)
    ap.add_argument('--cmd',required=True)
    ap.add_argument('--out',required=True,help='audit receipt, separate from the artifact')
    a=ap.parse_args();out=backfill(ROOT,a.artifact,a.cmd)
    p=ROOT/a.out;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(a.artifact+': only top-level validity changed; receipt -> '+a.out)
    return 0
if __name__=='__main__':raise SystemExit(main())

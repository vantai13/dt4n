#!/usr/bin/env python3
"""Compare historical JSON bytes and emit evidence; scientific approval stays unset."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
ROOT = pathlib.Path(__file__).resolve().parents[1]

def flat(obj, path=''):
    if isinstance(obj, dict) and obj:
        return {k2:v2 for k,v in obj.items() for k2,v2 in flat(v,path+'/'+str(k)).items()}
    if isinstance(obj, list) and obj:
        return {k2:v2 for i,v in enumerate(obj) for k2,v2 in flat(v,path+'/'+str(i)).items()}
    return {path:obj}

def compare(before: bytes, after: bytes):
    a,b=flat(json.loads(before)),flat(json.loads(after))
    keys=sorted(a.keys()|b.keys())
    diff={k:{'before_present':k in a,'after_present':k in b,
             'before':a.get(k),'after':b.get(k)} for k in keys
          if k not in a or k not in b or type(a[k]) is not type(b[k]) or a[k]!=b[k]}
    numeric=lambda v:isinstance(v,(int,float)) and not isinstance(v,bool)
    numeric_keys=[k for k in keys if numeric(a.get(k)) or numeric(b.get(k))]
    nums={k:[a.get(k),b.get(k)] for k in numeric_keys if k in diff}
    return {'numeric_fields_total':len(numeric_keys),'numeric_fields_changed':len(nums),
            'numeric_diff':nums,'all_field_diff':diff,
            'string_fields_changed':[k for k in diff if isinstance(a.get(k),str) or isinstance(b.get(k),str)]}

def at(root, commit, path):
    return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=root)

def entry(root, path, before, after, reason):
    old=at(root,before,path)
    new=(root/path).read_bytes() if after=='WORKTREE' else at(root,after,path)
    return {'path':path,'sha_before':hashlib.sha256(old).hexdigest(),
            'sha_after':hashlib.sha256(new).hexdigest(),'commit_before':before,
            'commit_after':after,'reason':reason,**compare(old,new),'verdict_affected':None}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--path',required=True)
    ap.add_argument('--before',required=True)
    ap.add_argument('--after',required=True)
    ap.add_argument('--reason',required=True)
    ap.add_argument('--out')
    a=ap.parse_args()
    out=entry(ROOT,a.path,a.before,a.after,a.reason)
    text=json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+'\n'
    if a.out:
        p=ROOT/a.out;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    else:print(text,end='')
    print('Review all_field_diff; verdict_affected is deliberately unset.',file=sys.stderr)
    return 0
if __name__=='__main__':raise SystemExit(main())

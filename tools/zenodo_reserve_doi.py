"""Prepare a Zenodo draft request; reserve only with explicit CLI and auth.

Never uploads files, publishes a record, or treats a reserved DOI as archived.
https://developers.zenodo.org/ documents POST {} returning prereserve_doi.
"""
from __future__ import annotations
import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from tools.artifact_guard import write_contract_artifact,sha256_of

BASE=Path('results/SMOKE/phase-G2')


def reservation_receipt(response):
    record_id=response.get('id')
    doi=response.get('metadata',{}).get('prereserve_doi',{}).get('doi')
    if not isinstance(record_id,int):raise ValueError('Zenodo response has no draft ID')
    if doi is not None and not doi.startswith('10.5281/zenodo.'):
        raise ValueError('refusing non-production Zenodo DOI')
    return {'schema':'dt4n.zenodo_reservation.v1','status':'RESERVED_NOT_PUBLISHED' if doi else 'DRAFT_CREATED_DOI_NOT_RETURNED',
            'draft_id':record_id,'reserved_doi':doi,'published_doi':None,
            'draft_url':f'https://zenodo.org/uploads/{record_id}',
            'public_archival_gate_pass':False,'files_uploaded':False}


def main():
    ap=argparse.ArgumentParser()
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--reserve',action='store_true')
    args=ap.parse_args()
    if args.prepare:
        inventory=BASE/'g4_data_manifest.json'
        m=json.loads(inventory.read_text())
        payload={'schema':'dt4n.zenodo_draft_request.v1','status':'READY_LOCALLY_AUTHENTICATION_REQUIRED',
                 'method':'POST','endpoint':'https://zenodo.org/api/deposit/depositions','body':{},
                 'expected_response_field':'metadata.prereserve_doi.doi','credential_env':'ZENODO_ACCESS_TOKEN',
                 'inventory':{'path':str(inventory),'sha256':sha256_of(inventory),'n_files':m['n_files'],'total_bytes':m['total_bytes']},
                 'draft_metadata_proposal':{'title':'DT4N: measured network traces and reproducible certification experiments',
                    'description':'Raw data inventory and evidence for DT4N network measurement and certification studies.',
                    'upload_type':'dataset'},
                 'metadata_still_required_before_publication':['creator names','licence/access terms','archive files'],
                 'public_doi':None,'reserved_doi':None,'network_action_performed':False,
                 'official_documentation':['https://developers.zenodo.org/','https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/']}
        path=BASE/'g5_zenodo_draft_request.json';write_contract_artifact(path,payload);print(path);return
    assert args.reserve
    path=BASE/'zenodo_reservation_receipt.json'
    if path.exists():raise FileExistsError('A receipt already exists; inspect it rather than creating a duplicate draft')
    token=next((os.environ[k] for k in ('ZENODO_ACCESS_TOKEN','ZENODO_TOKEN','ZENODO_API_TOKEN') if os.environ.get(k)),None)
    if not token:raise SystemExit('No Zenodo credential configured; no network request sent')
    request=urllib.request.Request('https://zenodo.org/api/deposit/depositions',data=b'{}',method='POST',
                headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
    try:
        with urllib.request.urlopen(request,timeout=30) as response:
            result=json.load(response)
    except urllib.error.HTTPError as e:
        raise SystemExit(f'Zenodo returned HTTP {e.code}; no automatic retry') from None
    receipt=reservation_receipt(result)
    write_contract_artifact(path,receipt)
    # Preserve public DOI semantics. A draft is not evidence of public archival.
    manifest=Path('results/DATA_MANIFEST.json')
    data=json.loads(manifest.read_text())
    data['reserved_doi']=receipt['reserved_doi']
    data['doi_reservation']={'draft_id':receipt['draft_id'],'receipt':str(path),'published':False}
    manifest.write_text(json.dumps(data,indent=1)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()

"""Seal a hash-verified local backup of the evidence tree and the repository.

The Phase G custody gate has been open on `USER_ATTESTED_OFFSITE_BACKUP_WAIVER`
since 2026-08-30: a statement that a copy exists somewhere, with
`checksum_verified_in_workspace` false. This tool produces the stronger thing
the gate actually wants -- a copy whose every recorded hash was re-read and
re-checked at seal time, so a later silent edit of an evidence file is
detectable rather than merely improbable.

It is NOT a DOI and never sets one. A DOI is a public, citable, third-party
held record; this is a private copy on hardware the user controls. It clears
the local execution gate only.

    python -m tools.local_custody_backup --create
    python -m tools.local_custody_backup --verify
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from tools.artifact_guard import sha256_of

DEFAULT_ROOT = Path.home() / 'backups' / 'dt4n'
MANIFESTS = (Path('results/DATA_MANIFEST.json'), Path('results/SMOKE/phase-G2/g4_data_manifest.json'))
SEAL_NAME = 'SEAL.json'
SCHEMA = 'dt4n.local_custody_seal.v1'


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def verify_manifests():
    """Re-read every hash-referenced evidence file. This is the whole point."""
    checked, mismatched, missing, total_bytes = {}, [], [], 0
    for manifest_path in MANIFESTS:
        manifest = json.loads(manifest_path.read_text())
        for record in manifest['files']:
            path = record['path']
            if path in checked:
                continue
            target = Path(path)
            if not target.exists():
                missing.append(path)
                continue
            digest = sha256_of(target)
            checked[path] = digest
            total_bytes += target.stat().st_size
            if digest != record['sha256']:
                mismatched.append({'path': path, 'recorded': record['sha256'], 'found': digest})
    return {'manifests': {str(p): sha256_of(p) for p in MANIFESTS},
            'n_files_verified': len(checked), 'bytes_verified': total_bytes,
            'n_mismatched': len(mismatched), 'mismatched': mismatched,
            'n_missing': len(missing), 'missing': missing,
            'all_recorded_hashes_reproduced': not mismatched and not missing}


def git_state():
    def run(*args):
        return subprocess.check_output(['git', *args], text=True).strip()
    return {'head': run('rev-parse', 'HEAD'),
            'branch': run('rev-parse', '--abbrev-ref', 'HEAD'),
            'dirty': bool(run('status', '--porcelain')),
            'n_tags': len(run('tag').splitlines())}


def build(destination):
    destination.mkdir(parents=True, exist_ok=True)
    bundle = destination / 'repo.bundle'
    subprocess.run(['git', 'bundle', 'create', str(bundle), '--all'], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['git', 'bundle', 'verify', str(bundle)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    archive = destination / 'results.tar.zst'
    with open(archive, 'wb') as handle:
        tar = subprocess.Popen(['tar', '--numeric-owner', '-cf', '-', 'results'], stdout=subprocess.PIPE)
        zstd = subprocess.Popen(['zstd', '-T0', '-3', '-q'], stdin=tar.stdout, stdout=handle)
        tar.stdout.close()
        if zstd.wait() or tar.wait():
            raise RuntimeError('archiving results/ failed')
    listing = subprocess.run(['tar', '--use-compress-program=zstd -d', '-tf', str(archive)],
                             check=True, capture_output=True, text=True).stdout.splitlines()
    return {'repo_bundle': {'path': str(bundle), 'bytes': bundle.stat().st_size,
                            'sha256': sha256_of(bundle), 'git_bundle_verify': 'PASS'},
            'results_archive': {'path': str(archive), 'bytes': archive.stat().st_size,
                                'sha256': sha256_of(archive), 'n_entries': len(listing),
                                'readback': 'FULL_LISTING_OK'}}


def create(root):
    started = time.monotonic()
    verification = verify_manifests()
    if not verification['all_recorded_hashes_reproduced']:
        raise SystemExit('refusing to seal: evidence files do not match their recorded hashes\n'
                         + json.dumps({k: verification[k] for k in ('mismatched', 'missing')}, indent=2))
    destination = root / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    if destination.exists():
        raise FileExistsError(destination)
    seal = {'schema': SCHEMA, 'sealed_utc': utc_now(), 'host': os.uname().nodename,
            'workspace': str(Path.cwd()), 'git': git_state(), 'manifest_verification': verification,
            'artifacts': build(destination),
            'basis': 'VERIFIED_LOCAL_BACKUP_SEAL',
            'public_archival_gate_pass': False, 'doi': None, 'published_doi': None,
            'is_doi_equivalent': False,
            'scope': ['Phase G local execution, including G-prime.7 and G-prime.8 measurement runs'],
            'forbidden': ['claiming a public Version DOI exists',
                          'claiming public reproducibility or third-party archival custody',
                          'untracking, deleting or rewriting historical evidence'],
            'known_limits': ['same-host copy: does not survive loss of this machine',
                             'not third-party held, not citable, not immutable against this account',
                             'seals the tree as of sealed_utc only; later data needs a later seal']}
    seal['elapsed_s'] = time.monotonic() - started
    path = destination / SEAL_NAME
    path.write_text(json.dumps(seal, indent=2) + '\n')
    for item in (path, destination / 'repo.bundle', destination / 'results.tar.zst'):
        item.chmod(0o444)
    latest = root / 'latest'
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(destination.name)
    return path, seal


def verify(seal_path):
    seal = json.loads(Path(seal_path).read_text())
    rows = []
    for name, record in seal['artifacts'].items():
        target = Path(record['path'])
        found = sha256_of(target) if target.exists() else None
        rows.append({'artifact': name, 'path': record['path'], 'present': target.exists(),
                     'sha256_matches': found == record['sha256']})
    bundle = Path(seal['artifacts']['repo_bundle']['path'])
    bundle_ok = bundle.exists() and subprocess.run(['git', 'bundle', 'verify', str(bundle)],
                                                   capture_output=True).returncode == 0
    live = verify_manifests()
    return {'seal': str(seal_path), 'sealed_utc': seal['sealed_utc'],
            'artifacts': rows, 'git_bundle_verify': 'PASS' if bundle_ok else 'FAIL',
            'archive_intact': all(r['present'] and r['sha256_matches'] for r in rows) and bundle_ok,
            'workspace_still_matches_manifests': live['all_recorded_hashes_reproduced'],
            'workspace_mismatched': live['mismatched'], 'workspace_missing': live['missing']}


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--create', action='store_true')
    mode.add_argument('--verify', action='store_true')
    ap.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    ap.add_argument('--seal', type=Path)
    args = ap.parse_args()
    if args.verify and args.create:
        raise SystemExit('choose one mode')
    if args.create:
        free = shutil.disk_usage(args.root.parent if args.root.exists() else Path.home()).free
        if free < 20 << 30:
            raise SystemExit(f'refusing to seal: only {free >> 30} GiB free')
        path, seal = create(args.root)
        print(json.dumps({'seal': str(path), 'sha256': sha256_of(path),
                          'files_verified': seal['manifest_verification']['n_files_verified'],
                          'bytes_verified': seal['manifest_verification']['bytes_verified'],
                          'archive_bytes': seal['artifacts']['results_archive']['bytes'],
                          'bundle_bytes': seal['artifacts']['repo_bundle']['bytes'],
                          'doi': seal['doi'], 'public_archival_gate_pass': seal['public_archival_gate_pass'],
                          'elapsed_s': round(seal['elapsed_s'], 1)}, indent=2))
    elif args.verify:
        seal = args.seal or (args.root / 'latest' / SEAL_NAME)
        result = verify(seal)
        print(json.dumps(result, indent=2))
        return 0 if result['archive_intact'] else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

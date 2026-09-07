#!/usr/bin/env python3
"""Check the narrowly scoped custody gate for local Phase G work.

Three bases, strongest first. A real public Version DOI is the only one that
permits a public archival claim; the other two open local execution only.

The seal basis is re-verified here rather than trusted from the manifest: the
seal file must still exist and still hash to the value the manifest recorded,
and it must report that every hash-referenced evidence file was reproduced.
That is the difference between this basis and the attestation it supersedes.

Re-reading the sealed archive itself is `--deep`, not the default. The archive
is multi-GB and grows with every campaign, so hashing it on every gate check
would make the routine check cost scale with the data it guards. The default
check is the cheap half that still cannot be faked from the manifest alone;
`python -m tools.local_custody_backup --verify` is the full re-read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


MANIFEST = Path("results/DATA_MANIFEST.json")
WAIVER_STATUS = "OPEN_BY_USER_CUSTODY_WAIVER"
SEAL_STATUS = "VERIFIED_LOCAL_BACKUP_SEAL"
PHASE_G_TAG = re.compile(r"(?<![\w-])phase-G(?:2)?-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")


def referenced_phase_g_tags(repo: Path) -> dict[str, list[str]]:
    """Find Phase G tag references independently of which tags exist locally."""
    documents = sorted((repo / "docs/phase-G").glob("*.md"))
    if not documents:
        raise ValueError("no Phase G documents found; cannot certify an empty scan")
    references: dict[str, list[str]] = {}
    for path in documents:
        for tag in sorted(set(PHASE_G_TAG.findall(path.read_text(encoding="utf-8")))):
            references.setdefault(tag, []).append(str(path.relative_to(repo)))
    if not references:
        raise ValueError("no Phase G tag references found")
    return dict(sorted(references.items()))


def _tag_refs(output: str) -> dict[str, str]:
    refs = {}
    for line in output.splitlines():
        oid, ref = line.split()
        if ref.startswith("refs/tags/") and not ref.endswith("^{}"):
            refs[ref.removeprefix("refs/tags/")] = oid
    return refs


def check_remote_tags(repo: Path = Path(".")) -> dict[str, object]:
    """Require every documented Phase G tag on origin with the same object ID.

    Read origin live, not a cached tracking ref. No fetching, rewriting, or
    pushing occurs here. Annotated tags compare tag-object IDs, not counts.
    """
    repo = Path(repo)
    try:
        references = referenced_phase_g_tags(repo)
        def git(*args):
            return subprocess.run(["git", *args], cwd=repo, text=True,
                                  capture_output=True, check=True, timeout=30).stdout
        local = _tag_refs(git("for-each-ref", "--format=%(objectname) %(refname)", "refs/tags/"))
        remote = _tag_refs(git("ls-remote", "--tags", "origin"))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {"pass": False, "checked": False, "error": str(exc),
                "scope": "documented Phase G tags on origin"}
    missing_local = sorted(set(references) - local.keys())
    missing_remote = sorted(set(references) - remote.keys())
    mismatches = {tag: {"local": local[tag], "origin": remote[tag]}
                  for tag in references if tag in local and tag in remote
                  and local[tag] != remote[tag]}
    return {
        "pass": not (missing_local or missing_remote or mismatches), "checked": True,
        "scope": "documented Phase G tags on origin; exact tag object IDs",
        "referenced_tag_count": len(references), "local_tag_count": len(local),
        "remote_tag_count": len(remote), "missing_local": missing_local,
        "missing_remote": missing_remote, "mismatches": mismatches,
        "references": references,
        "verified_object_ids": {tag: local[tag] for tag in references
                                if tag in local and remote.get(tag) == local[tag]},
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _seal_holds(record: dict, deep: bool = False) -> tuple[bool, str]:
    """Re-read the seal. A declared seal that cannot be read does not count."""
    if record.get("status") != SEAL_STATUS:
        return False, "no seal recorded"
    if record.get("allows_claim_of_public_archival") is not False:
        return False, "seal must not claim public archival"
    path = Path(str(record.get("seal_path", "")))
    if not path.is_file():
        return False, f"seal file missing: {path}"
    if _sha256(path) != record.get("seal_sha256"):
        return False, "seal file changed since it was recorded"
    seal = json.loads(path.read_text(encoding="utf-8"))
    if seal.get("doi") is not None or seal.get("public_archival_gate_pass") is not False:
        return False, "seal misrepresents itself as public archival"
    verification = seal.get("manifest_verification", {})
    if not verification.get("all_recorded_hashes_reproduced"):
        return False, "seal did not reproduce every recorded hash"
    for artifact in seal.get("artifacts", {}).values():
        target = Path(artifact["path"])
        if not target.is_file():
            return False, f"sealed artifact missing: {target}"
        if artifact["bytes"] != target.stat().st_size:
            return False, f"sealed artifact resized: {target}"
        if deep and _sha256(target) != artifact["sha256"]:
            return False, f"sealed artifact changed: {target}"
    return True, "ok (deep)" if deep else "ok (shallow; --deep re-reads the archive)"


def evaluate(deep: bool = False) -> dict[str, object]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    doi = manifest.get("doi")
    custody = manifest.get("custody", {})
    backup = custody.get("offsite_backup", {})
    local = custody.get("phase_g_local_gate", {})

    public_archive = bool(isinstance(doi, str) and doi.startswith("10."))
    seal, seal_detail = _seal_holds(custody.get("local_backup_seal", {}), deep=deep)
    waiver = bool(
        backup.get("status") == "USER_ATTESTED_PRESENT"
        and local.get("status") == WAIVER_STATUS
        and local.get("public_doi_equivalent") is False
        and local.get("allows_historical_data_cleanup") is False
        and local.get("allows_claim_of_public_archival") is False
    )
    if public_archive:
        basis = "PUBLIC_VERSION_DOI"
    elif seal:
        basis = SEAL_STATUS
    elif waiver:
        basis = "USER_ATTESTED_OFFSITE_BACKUP_WAIVER"
    else:
        basis = "NONE"
    return {
        "pass": public_archive or seal or waiver,
        "basis": basis,
        "doi": doi,
        "phase_g_local_work_allowed": public_archive or seal or waiver,
        "campaign_execution_allowed": public_archive or seal,
        "public_archival_claim_allowed": public_archive,
        "historical_cleanup_allowed": public_archive,
        "seal_detail": seal_detail,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deep", action="store_true",
                        help="also re-hash the sealed archive (multi-GB, slow)")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--tags-only", action="store_true",
                       help="check origin tag custody without requiring this host's backup")
    modes.add_argument("--local-only", action="store_true",
                       help="offline legacy backup check; does not certify remote tag custody")
    args = parser.parse_args()
    if args.tags_only:
        result = check_remote_tags()
    else:
        result = evaluate(deep=args.deep)
        result["local_backup_pass"] = result["pass"]
        result["remote_tags"] = ({"checked": False, "pass": None, "reason": "--local-only"}
                                 if args.local_only else check_remote_tags())
        if not args.local_only:
            tags_pass = result["remote_tags"]["pass"]
            for key in ("pass", "phase_g_local_work_allowed", "campaign_execution_allowed"):
                result[key] = bool(result[key] and tags_pass)
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

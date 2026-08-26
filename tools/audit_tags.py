#!/usr/bin/env python3
"""Ra soat MOI tag duoc claim trong doc va artifact, doi chieu voi git.

Vi sao ton tai: toan bo phuong phap luan custody dung tren tien de "co mot
trang thai bat bien, chi vao bang mot cai ten". Mot cai ten khong ton tai
lam moi tuyen bo custody khac thanh giay. Script nay tim MOI cai ten do.

    python -m tools.audit_tags
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import Dict, List, Sequence, Set

# Cac dang claim tag da gap trong repo. Them dang moi thi them regex.
DOC_PATTERNS = (
    re.compile(r"Tag dong(?:\s+bang)?\s*:?\s*`([^`]+)`"),
    re.compile(r"Git tag\s*:\s*`([^`]+)`"),
    re.compile(r"git tag(?:\s+--list|\s+-f)?\s+([A-Za-z0-9][\w.\-]+)"),
    re.compile(r"tag\s+`([a-z][\w.\-]*(?:-(?:complete|prereg|start|frozen|fix|grid))[\w.\-]*)`"),
)
# Khoa KHANG DINH mot tag ton tai. Mot artifact mang mot trong cac khoa nay
# la mot CHUNG CU tro toi mot cai ten; cai ten do phai co that.
JSON_KEYS = ("prereg_tag", "closure_tag")

# Khoa khai bao Y DINH tao tag, khong khang dinh no da co. Bao cao rieng,
# KHONG tinh la thieu: `prediction_pre_campaign.json` ghi
# `git_tag_to_create: phase-20R-prediction` truoc mot chien dich chua chay.
JSON_INTENT_KEYS = ("git_tag_to_create",)

# Khoa `"tag"` TRAN CO Y BI LOAI. Do duoc 2026-08-26: cho duy nhat dung no
# trong `results/` la `RAW/phase-23/aoi_v7_campaign/campaign_manifest.json`,
# noi `runs[].tag` la NHAN MOT LAN CHAY chien dich (`prod_rho0.700_rep1`),
# mot khong gian ten KHAC HAN tag git. Quet no lam 30 nhan chien dich hien
# ra nhu 30 tag git bi mat -- mot bao dong gia lam chim 18 tag that.
BLOCKLIST = {"--list", "-f", "-a", "-m", "origin", "main"}


def _git_tags() -> Set[str]:
    out = subprocess.run(["git", "tag"], capture_output=True, text=True, check=True)
    return {t.strip() for t in out.stdout.splitlines() if t.strip()}


def _scan_docs(root: pathlib.Path) -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {}
    for p in sorted(root.rglob("*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        for pat in DOC_PATTERNS:
            for name in pat.findall(text):
                name = name.strip()
                if not name or name in BLOCKLIST:
                    continue
                found.setdefault(name, []).append(str(p))
    return found


def _scan_json(root: pathlib.Path,
               keys: Sequence[str] = JSON_KEYS) -> Dict[str, List[str]]:
    found: Dict[str, List[str]] = {}
    for p in sorted(root.rglob("*.json")):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for key in keys:
            for name in re.findall(r'"%s"\s*:\s*"([^"]+)"' % key, text):
                found.setdefault(name.strip(), []).append(str(p))
    return found


def _scan_json_intent(root: pathlib.Path) -> Dict[str, List[str]]:
    """Tag duoc KHAI la se tao. Khong phai mot khang dinh ton tai."""
    return _scan_json(root, JSON_INTENT_KEYS)


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs")
    ap.add_argument("--artifacts", default="results")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args(argv)

    have = _git_tags()
    from_docs = _scan_docs(pathlib.Path(args.docs))
    from_json = _scan_json(pathlib.Path(args.artifacts))
    intent = _scan_json_intent(pathlib.Path(args.artifacts))

    all_claims = sorted(set(from_docs) | set(from_json))
    missing = [t for t in all_claims if t not in have]

    print("=" * 74)
    print("TAG DANG CO TRONG GIT : %d" % len(have))
    for t in sorted(have):
        print("   OK   %s" % t)
    print("-" * 74)
    print("TAG DUOC CLAIM        : %d   (THIEU: %d)" % (len(all_claims), len(missing)))
    for t in all_claims:
        mark = "OK  " if t in have else "MISS"
        src = from_json.get(t, [])
        sev = "  [ARTIFACT]" if src else ""
        print("   %s %s%s" % (mark, t, sev))
        for f in (from_docs.get(t, []) + src)[:4]:
            print("           <- %s" % f)
    print("-" * 74)
    print("TAG KHAI SE TAO (y dinh, khong tinh la thieu): %d" % len(intent))
    for t in sorted(intent):
        print("   %s %s" % ("OK  " if t in have else "CHUA", t))
        for f in intent[t][:2]:
            print("           <- %s" % f)
    print("=" * 74)

    if args.json_out:
        pathlib.Path(args.json_out).write_text(json.dumps({
            "tags_in_git": sorted(have),
            "claimed": {t: {"docs": from_docs.get(t, []),
                            "artifacts": from_json.get(t, [])}
                        for t in all_claims},
            "missing": missing,
            "intent_only": {t: intent[t] for t in sorted(intent)},
        }, indent=1), encoding="utf-8")

    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())

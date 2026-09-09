#!/usr/bin/env python3
"""Dan `pending_on: ["sla_axis"]` vao artifact PENDING/phase-T2 KHONG bi dong
bang. Metadata-only: KHONG mot truong SO nao duoc phep doi.

Vi sao day KHONG phai "sinh lai": khong RNG nao chay, khong phep tinh nao lap
lai, khong ket qua nao duoc doc lai roi ghi de. Chi mot NHAN duoc dan len mot
ban ghi da co. De dieu do khong chi la loi hua, script TU CHUNG MINH: bam
sha256 cua artifact SAU KHI XOA khoi `validity`, truoc va sau. Lech mot bit
=> abort, khong ghi gi.

Nhan `sla_axis` khong phai suy doan: no doc THANG tu `validity.sla_axis.label`
cua chinh artifact, va duoc doi chieu voi docs/phase-23/axis_registry.json.
Duong du lieu: tools/t2_sla_axis_provenance.py

    python3 tools/t2_backfill_pending_on.py --dry-run
    python3 tools/t2_backfill_pending_on.py --apply
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "results" / "PENDING" / "phase-T2"
SIDECAR = BASE / "FROZEN_PENDING_ON.json"
REG = ROOT / "docs" / "phase-23" / "axis_registry.json"


def frozen_set() -> set[pathlib.Path]:
    """Nguon su that DUY NHAT ve "bi dong bang" la sidecar  [W4: mot nguon]."""
    doc = json.loads(SIDECAR.read_text())
    out: set[pathlib.Path] = set()
    for e in doc["entries"]:
        out |= set(BASE.glob(e["glob"]))
    return out


def body_digest(doc: dict) -> str:
    """sha256 cua artifact SAU KHI XOA khoi `validity`.

    Day la bang chung "khong doi so": neu digest nay giu nguyen thi moi truong
    ngoai `validity` deu y nguyen.
    """
    body = {k: v for k, v in doc.items() if k != "validity"}
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=True,
                   default=str).encode()).hexdigest()


def patch(doc: dict, approved: list[str]) -> tuple[dict, str]:
    """Tra ve (doc moi, ly do bo qua hoac '')."""
    v = doc.get("validity")
    if v is None:
        return doc, ("khong co khoi validity -- can validity_block() tu script "
                     "sinh, khong phai mot truong don le dan tay")
    if v.get("pending_on"):
        return doc, "da co pending_on"
    label = (v.get("sla_axis") or {}).get("label")
    if label is None:
        return doc, "validity khong khai sla_axis.label -- khong suy duoc"
    if label in approved:
        return doc, ("sla_axis DA duoc duyet -> phai PROMOTE len LIVE/, khong "
                     "phai dan pending_on")
    out = copy.deepcopy(doc)
    out["validity"]["pending_on"] = ["sla_axis"]
    out["validity"]["pending_on_source"] = (
        "T2 backfill: suy TU validity.sla_axis.label = %r, la nhan DEPRECATED "
        "(S14) va khong nam trong approved_for_live.sla_axis. Duong du lieu: "
        "tools/t2_sla_axis_provenance.py. Metadata-only, khong doi mot so nao."
        % label)
    return out, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.apply == args.dry_run:
        raise SystemExit("chon DUNG MOT trong hai: --apply hoac --dry-run")

    approved = json.loads(REG.read_text())["approved_for_live"]["sla_axis"]
    frozen = frozen_set()

    n_ok = n_skip = 0
    skips: dict[str, int] = {}
    for p in sorted(BASE.rglob("*.json")):
        if p in frozen or p == SIDECAR:
            continue
        try:
            doc = json.loads(p.read_text())
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        before = body_digest(doc)
        new, why = patch(doc, approved)
        if why:
            n_skip += 1
            skips[why] = skips.get(why, 0) + 1
            continue
        after = body_digest(new)
        if before != after:
            raise SystemExit(
                "ABORT: %s -- than artifact DOI. Day la ban va metadata-only; "
                "mot thay doi ngoai `validity` la LOI, khong phai tinh nang." % p)
        if args.apply:
            p.write_text(json.dumps(new, indent=1, sort_keys=True,
                                    ensure_ascii=True) + "\n", encoding="utf-8")
        n_ok += 1

    print("%s: %d tep %s | %d bo qua | %d dong bang (sidecar)"
          % ("APPLY" if args.apply else "DRY-RUN", n_ok,
             "da va" if args.apply else "se va", n_skip, len(frozen)))
    for why, k in sorted(skips.items(), key=lambda x: -x[1]):
        print("   bo qua %3d: %s" % (k, why))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

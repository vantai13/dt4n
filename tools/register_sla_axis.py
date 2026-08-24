#!/usr/bin/env python3
"""Dang ky truc SLA ngoai sinh vao `axis_registry.json` (amendment 23-57 muc 5).

Vi sao can script rieng: `sha256` cua manifest phai duoc tinh TU FILE THAT.
Go tay mot sha la cach chac chan nhat de tao ra mot cai chan KHONG BAO GIO
bat duoc gi.

Thu tu BAT BUOC: sinh manifest TRUOC, roi moi chay script nay.
"""
from __future__ import annotations

import hashlib
import json
import sys
import argparse

REGISTRY = "docs/phase-23/axis_registry.json"
MANIFEST = "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"
LABEL = "exogenous_g114_S-B"
AOI_LABEL = "measured_v7_uniform"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default=MANIFEST)
    parser.add_argument("--label", default=LABEL)
    parser.add_argument("--registered-in", default="amendment-57")
    parser.add_argument("--note", default=None)
    args = parser.parse_args(argv)

    digest = sha256_file(args.manifest)
    with open(REGISTRY, encoding="utf-8") as fh:
        reg = json.load(fh)

    note = args.note or (
        "T_delay = 50 ms (ITU-T G.114, MOT chang), T_loss = 1%, "
        "w_loss = 5000 (equal-budget, K06). Thay `self_calibrated` "
        "(loi cau truc S14). Sinh boi `measurements/sla_manifest_exogenous.py`."
    )
    reg["sla_axis"][args.manifest] = {
        "content_sha256": digest,
        "label": args.label,
        "note": note,
        "registered_in": args.registered_in,
        "status": "ACTIVE",
        "source_path": args.manifest,
    }
    # DUYET ca hai truc -> mo khoa tang LIVE. Mot artifact hop le khi MOI truc
    # hop le (amendment 23-49c muc 3).
    approved = set(reg["approved_for_live"].get("sla_axis", []))
    approved.add(args.label)
    reg["approved_for_live"]["sla_axis"] = sorted(approved)
    reg["approved_for_live"]["aoi_axis"] = [AOI_LABEL]

    with open(REGISTRY, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("[ok] dang ky %s  sha=%s..." % (args.label, digest[:16]))
    print("     approved_for_live =", reg["approved_for_live"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

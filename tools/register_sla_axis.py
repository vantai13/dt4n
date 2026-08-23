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


def main() -> int:
    digest = sha256_file(MANIFEST)
    with open(REGISTRY, encoding="utf-8") as fh:
        reg = json.load(fh)

    reg["sla_axis"][MANIFEST] = {
        "content_sha256": digest,
        "label": LABEL,
        "note": ("T_delay = 50 ms (ITU-T G.114, MOT chang), T_loss = 1%, "
                 "w_loss = 5000 (equal-budget, K06). Thay `self_calibrated` "
                 "(loi cau truc S14). Sinh boi "
                 "`measurements/sla_manifest_exogenous.py`."),
        "registered_in": "amendment-57",
        "status": "ACTIVE",
        "source_path": MANIFEST,
    }
    # DUYET ca hai truc -> mo khoa tang LIVE. Mot artifact hop le khi MOI truc
    # hop le (amendment 23-49c muc 3).
    reg["approved_for_live"]["sla_axis"] = [LABEL]
    reg["approved_for_live"]["aoi_axis"] = [AOI_LABEL]

    with open(REGISTRY, "w", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("[ok] dang ky %s  sha=%s..." % (LABEL, digest[:16]))
    print("     approved_for_live =", reg["approved_for_live"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

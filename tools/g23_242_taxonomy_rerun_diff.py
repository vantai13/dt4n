#!/usr/bin/env python3
"""`G23-242` -- doi chieu BIT-EXACT hai lan chay `taxonomy_audit`.

Amendment 23-65 muc 1.1 khai TRUOC pham vi anh huong cua phep sua `L91`:

    KHONG DOI : census, spread, mhat_concentration
    KHONG DOI : moi khoa CU cua bootstrap (M_188 la khoa MOI, duoc bo qua)
    KHONG DOI : moi hang V-M va V-N cua variant_sweep
    CO THE DOI: hang V-S cua variant_sweep

Cong cu nay ep loi khai do. Neu mot muc "KHONG DOI" thay doi -> phep sua da
cham vao thu khac -> DUNG dong lesson, revert, tim nguyen nhan tren ban cu.

    python -m tools.g23_242_taxonomy_rerun_diff --old A.json --new B.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from typing import Any, Dict, List, Mapping, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cay PHAI trung bit. `bootstrap` xu ly rieng vi no co khoa MOI `M_188`.
FROZEN_TREES = ("census", "spread", "mhat_concentration")
# Khoa MOI duoc phep xuat hien; moi khoa khac cua `bootstrap` phai trung.
BOOTSTRAP_NEW_KEYS = ("M_188",)
# Truong MOI duoc phep xuat hien trong moi hang cua `variant_sweep`.
# `L91`: qhat_has_infinite, min_blocks_floor
# `L93`: qhat_at_sample_max, min_blocks_stable, min_blocks_at_final_qhat
SWEEP_NEW_KEYS = ("qhat_has_infinite", "min_blocks_floor",
                  "qhat_at_sample_max", "min_blocks_stable",
                  "min_blocks_at_final_qhat",
                  # `L95` (amendment 23-65d): NHAN, khong phai phep do.
                  "qhat_source", "procedure_actually_run",
                  "L95_collapsed_to_none")
# Bien the duoc phep doi.
MUTABLE_VARIANTS = ("selective",)


def _flat(o: Any, path: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(_flat(v, "%s/%s" % (path, k)))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(_flat(v, "%s[%d]" % (path, i)))
    else:
        out[path] = o
    return out


def _cmp(a: Mapping[str, Any], b: Mapping[str, Any], label: str,
         allow_new: Tuple[str, ...] = ()) -> List[str]:
    bad: List[str] = []
    fa, fb = _flat(a), _flat(b)
    for k in sorted(set(fa) | set(fb)):
        if k not in fa:
            if not any(("/%s" % n) in k for n in allow_new):
                bad.append("%s: khoa MOI khong duoc khai truoc: %s" % (label, k))
            continue
        if k not in fb:
            bad.append("%s: khoa BIEN MAT: %s" % (label, k))
            continue
        if fa[k] != fb[k]:
            bad.append("%s: %s  %r -> %r" % (label, k, fa[k], fb[k]))
    return bad


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_old(path: str | None, git_ref: str | None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Nap ban CU. Uu tien git ref.

    Mot git blob TU CHUNG MINH noi dung cua no (SHA-1 la ham cua noi dung, va
    co mat o MOI ban sao repo). Mot duong dan chi la mot LOI HUA rang ai do da
    chep dung.

    Va no tranh mot cai bay: ghim ban cu vao `results/RAW/` doi phai `chmod`
    nguoc lai mot tang DA KHOA custody (amendment 23-61 dong 70), tuc pha chinh
    hang rao dang bao ve bang chung. Them nua, bit `chmod` KHONG duoc git theo
    doi, nen hang rao do la CUC BO THEO MAY -- mot ly do nua de dung git blob.
    """
    if git_ref:
        raw = subprocess.check_output(["git", "show", git_ref], text=True)
        blob = subprocess.check_output(["git", "rev-parse", git_ref], text=True).strip()
        return json.loads(raw), {"kind": "git", "ref": git_ref, "blob": blob}
    if not path:
        raise SystemExit("can --old hoac --old-git-ref")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh), {"kind": "file",
                               "path": os.path.relpath(path, REPO),
                               "sha256": _sha256(path)}


def diff(old_path: str | None, new_path: str,
         old_git_ref: str | None = None) -> Dict[str, Any]:
    old, old_prov = load_old(old_path, old_git_ref)
    with open(new_path, "r", encoding="utf-8") as fh:
        new = json.load(fh)

    co = {c["cell"]: c for c in old["cells"]}
    cn = {c["cell"]: c for c in new["cells"]}
    bad: List[str] = []
    if set(co) != set(cn):
        bad.append("tap cell doi: %s" % sorted(set(co) ^ set(cn)))

    changed_vs: Dict[str, int] = {}
    for cell in sorted(set(co) & set(cn)):
        a, b = co[cell], cn[cell]
        for tree in FROZEN_TREES:
            bad += _cmp(a[tree], b[tree], "%s/%s" % (cell, tree))
        bad += _cmp(a["bootstrap"], b["bootstrap"], "%s/bootstrap" % cell,
                    allow_new=BOOTSTRAP_NEW_KEYS)

        ra = {(r["post"], float(r["kappa"])): r for r in a["variant_sweep"]}
        rb = {(r["post"], float(r["kappa"])): r for r in b["variant_sweep"]}
        if set(ra) != set(rb):
            bad.append("%s: luoi (post,kappa) doi" % cell)
            continue
        for key in sorted(ra):
            post, kappa = key
            if post in MUTABLE_VARIANTS:
                if _cmp(ra[key], rb[key], "", allow_new=SWEEP_NEW_KEYS):
                    changed_vs[cell] = changed_vs.get(cell, 0) + 1
                continue
            bad += _cmp(ra[key], rb[key],
                        "%s/sweep[%s,k=%.2f]" % (cell, post, kappa),
                        allow_new=SWEEP_NEW_KEYS)

    return {
        "schema": "dt4n.g23_242.v1",
        "old_provenance": old_prov,
        "new": os.path.relpath(new_path, REPO),
        "n_cells": len(set(co) & set(cn)),
        "frozen_violations": bad,
        "n_frozen_violations": len(bad),
        "selective_rows_changed_by_cell": changed_vs,
        "G23_242_hit": bool(not bad),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old", default=None, help="duong dan file cu")
    ap.add_argument("--old-git-ref", default=None,
                    help="vd `eefd34a:results/LIVE/phase-23/taxonomy_audit.json`. UU TIEN hon --old: git blob TU CHUNG MINH noi dung, va khong doi ghi vao tang da khoa custody.")
    ap.add_argument("--new", required=True)
    ap.add_argument("--out",
                    default="results/LIVE/phase-23/g23_242_rerun_diff.json",
                    help="KHONG duoc mac dinh vao results/RAW/ -- tang do da `chmod a-w` theo amendment 23-61 va ghi vao do se phai pha custody.")
    a = ap.parse_args()

    rep = diff(a.old, a.new, a.old_git_ref)
    os.makedirs(os.path.dirname(os.path.join(REPO, a.out)), exist_ok=True)
    with open(os.path.join(REPO, a.out), "w", encoding="utf-8") as fh:
        json.dump(rep, fh, indent=2, sort_keys=True)
        fh.write("\n")

    print("G23-242  cell doi chieu        : %d" % rep["n_cells"])
    print("G23-242  vi pham vung DONG BANG: %d" % rep["n_frozen_violations"])
    for line in rep["frozen_violations"][:15]:
        print("    %s" % line)
    print("G23-242  hang V-S doi          : %s" % rep["selective_rows_changed_by_cell"])
    print("G23-242  %s" % ("PASS" if rep["G23_242_hit"] else "FAIL"))
    print("G23-242  ban cu               : %s" % rep["old_provenance"])
    print("-> %s" % a.out)
    return 0 if rep["G23_242_hit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

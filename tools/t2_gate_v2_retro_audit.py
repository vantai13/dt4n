#!/usr/bin/env python3
"""Audit HOI TO: gate v2 phan quyet the nao ve luoi DA CHAY cua T2.6 vong 3.

CAI SCRIPT NAY LAM:
    doc artifact vong 3, XAC MINH sha256, dung lai loi goi gate tu chinh
    ban ghi cua chung, chay gate v2, so verdict moi voi verdict da ghi.

CAI SCRIPT NAY KHONG LAM -- va khong duoc lam:
    khong sinh lai chuoi AR(1), khong goi rng, khong ghi vao sweep_r3/,
    khong lat mot verdict nao cua adjudication_r3.json.

Vi sao tach thanh mot artifact RIENG thay vi cap nhat artifact cu:
    sweep_r3/run_log.jsonl ghi sha256 tung tep va adjudication_r3.json da
    phan quyet tren chinh chung. Ghi de = ghi de bang chung SAU khi da doc
    ket qua. Mot audit dung phai CONG THEM mot lop, khong duoc SUA lop duoi.

    python3 tools/t2_gate_v2_retro_audit.py
"""
from __future__ import annotations

import datetime
import glob
import hashlib
import json
import os
import subprocess

from cert.realizability_gate import GATE_VERSION, realizability_gate
from cert.simultaneous_score import ALPHA
from twin.cost_v2 import sigma_max_regime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "results", "PENDING", "phase-T2", "sweep_r3")
OUT = os.path.join(ROOT, "results", "PENDING", "phase-T2",
                   "gate_v2_retro_audit.json")

# Tep tong hop, khong phai ket qua mot lenh chay -> khong co `rows` de audit.
NOT_A_RUN = {
    "adjudication_r3.json",
    "hygiene_r3.json",
    "hygiene_r3_FAIL_before_table_erratum.json",
    "level_probe_posthoc.json",
    "gate_v2_retro_audit.json",
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_hash() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                              capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return "UNKNOWN"


def audit_one(path: str) -> dict | None:
    """Dung lai loi goi gate tu ban ghi cua MOT artifact, roi chay gate v2."""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    if "rows" not in doc or "cell" not in doc:
        return None

    mode, rho_txt = str(doc["cell"]).split("@")
    rho_bar = float(rho_txt)
    alpha = float(doc.get("alpha", ALPHA))
    smax = sigma_max_regime(mode, rho_bar)

    per_tau = []
    for row in doc["rows"]:
        diag = row.get("ar1_diagnostics") or []
        if not diag:
            continue
        # DUNG chinh cong thuc ma cert/tau_sweep.py da dung khi chay, de audit
        # so THUOC MOI voi THUOC CU tren CUNG mot dau vao.
        sigma_in = sum(d["sigma_rho"] for d in diag) / len(diag)
        clip_in = max(d["ar1_clip_ratio"] for d in diag)

        new = realizability_gate(
            mode=mode, rho_bar=rho_bar, tau=float(row["tau"]),
            dt=float(row["dt"]), n=int(row["n"]), alpha=alpha, omega=0.0,
            sigma=float(sigma_in), clip_fraction=float(clip_in),
            min_cell_blocks=int(row["min_calib_blocks"]),
        )
        old_verdict = (row.get("realizability") or {}).get("verdict")
        per_tau.append({
            "tau": float(row["tau"]),
            "sigma_used": float(sigma_in),
            "sigma_max_regime": smax,
            "headroom_ratio": (float(sigma_in) / smax) if smax > 0 else None,
            "verdict_recorded_v1": old_verdict,
            "verdict_gate_v2": new["verdict"],
            "failed_gate_v2": new["failed"],
            "changed": old_verdict != new["verdict"],
        })

    return {
        "artifact": os.path.relpath(path, ROOT),
        "sha256": sha256_file(path),
        "cell": doc["cell"],
        "branch": doc.get("branch"),
        "sigma_axis": doc.get("sigma_axis"),
        "estimand_id": doc.get("estimand_id"),
        "n_tau": len(per_tau),
        "n_changed": sum(1 for p in per_tau if p["changed"]),
        "per_tau": per_tau,
    }


def main() -> int:
    files = sorted(p for p in glob.glob(os.path.join(SRC, "*.json"))
                   if os.path.basename(p) not in NOT_A_RUN)
    audits = [a for a in (audit_one(p) for p in files) if a is not None]

    changed = [
        {"artifact": a["artifact"], "cell": a["cell"],
         "sigma_axis": a["sigma_axis"], "tau": p["tau"],
         "sigma_used": p["sigma_used"],
         "sigma_max_regime": p["sigma_max_regime"],
         "from": p["verdict_recorded_v1"], "to": p["verdict_gate_v2"],
         "failed": p["failed_gate_v2"]}
        for a in audits for p in a["per_tau"] if p["changed"]
    ]

    tightest = min(
        (p for a in audits for p in a["per_tau"]
         if p["headroom_ratio"] is not None),
        key=lambda p: -p["headroom_ratio"], default=None)

    payload = {
        "schema": "dt4n.phase_t2.gate_retro_audit.v1",
        "question": (
            "Neu gate v2 (tieu chi sigma_within_headroom) da ton tai luc "
            "T2.6 vong 3 chay, co o nao bi loai ma thuc te da duoc dua vao "
            "phan quyet khong?"),
        "method": (
            "CHI DOC. Dung lai loi goi gate tu ban ghi cua tung artifact "
            "(sigma = mean(ar1_diagnostics.sigma_rho), clip = max(...), "
            "min_cell_blocks = min_calib_blocks -- dung cong thuc cua "
            "cert/tau_sweep.py), roi chay gate v2 tren CUNG dau vao. Khong "
            "sinh lai chuoi, khong goi RNG, khong ghi vao sweep_r3/."),
        "gate_version_audited": GATE_VERSION,
        "n_artifacts": len(audits),
        "n_cells_checked": sum(a["n_tau"] for a in audits),
        "n_verdict_changed": len(changed),
        "verdict_changes": changed,
        "tightest_headroom": tightest,
        "adjudication_effect": (
            "KHONG DOI -- khong o nao doi verdict" if not changed else
            "CO O DOI VERDICT: xem verdict_changes. KHONG duoc lat mot du "
            "doan da ky dua tren audit hoi to; khai thanh no cho 21R2."),
        "audits": audits,
        "provenance": {
            "script": "tools/t2_gate_v2_retro_audit.py",
            "git_hash": git_hash(),
            "timestamp_utc": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
            "source_dir": os.path.relpath(SRC, ROOT),
            "reads_only": True,
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True, ensure_ascii=True)

    print("artifact doc  : %d" % payload["n_artifacts"])
    print("o kiem tra    : %d" % payload["n_cells_checked"])
    print("verdict DOI   : %d" % payload["n_verdict_changed"])
    if tightest:
        print("sat tran nhat : sigma/sigma_max = %.4f  (tau=%g)"
              % (tightest["headroom_ratio"], tightest["tau"]))
    print("-> %s" % os.path.relpath(OUT, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

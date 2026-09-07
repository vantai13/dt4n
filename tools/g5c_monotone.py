#!/usr/bin/env python3
"""G'.5c -- P-3b: gate don dieu ky lai voi DAU DUNG.

`docs/phase-G/73-g5b-results.md` section 2 (`G-L111`) ghi rang `P-3` cua
doc 72 tu mau thuan: van xuoi doi day KHONG TANG, cong thuc phat moi buoc
GIAM qua 0.005. Ti le chap nhan tren mot truc cong suat PHAI giam, nen cong
thuc phat dung hieu ung dang tim. Gate ghi VOID -- khong PASS khong FAIL.

    P-3   (void)   min(diff(acceptance)) >= -0.005      phat su GIAM
    P-3b  (day)    max(diff(acceptance)) <= +0.005      phat su TANG

`tools/g5b_power_axis.py` KHONG bi sua: artifact cua no duoc tham chieu bang
SHA256 trong doc 73. Hang so `SEED` cua no duoc rebind luc import -- dung
khuon mau `tools/g2_kill_test.py:66` dung cho `g3_dryrun.DT_S` -- va ca hash
file lan gia tri rebind deu duoc ghi vao artifact.

⚠️ TAC DUNG PHU CO Y: import module nay DOI `g5b.SEED` cua ca tien trinh.
   Test nao can seed goc cua g5b phai tu dat lai. Rebind o cap module (thay
   vi trong main) la co chu dich: no khong the bi QUEN.

    python -m tools.g5c_monotone
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g5_estimand_transfer import verify_protected
from tools import g5b_power_axis as g5b

OUT = Path("results/SMOKE/phase-G2/g5c_monotone.json")
G5B_ARTIFACT = Path("results/SMOKE/phase-G2/g5b_power_axis.json")
PREREG = "docs/phase-G/74-prereg-g5c-monotone.md"

SEED_C = 20260909            # seed thu ba: G5 dung ...07, G5b dung ...08
STEP_UP_TOLERANCE = 0.005    # ngan sach sai so: doc 74 section 3

# Rebind TRUOC moi loi goi vao g5b.make_inputs. Lam viec nay sau khi sweep()
# da bat dau se cho mot lan chay nua seed nay nua seed kia.
g5b.SEED = SEED_C


def monotone_stats(acceptance) -> dict:
    """Tach ro HAI chieu cua mot day, de khong bao gio lan nua nham dau."""
    values = np.asarray(acceptance, dtype=float)
    if values.ndim != 1 or values.size < 2 or not np.isfinite(values).all():
        raise ValueError("acceptance must be a finite vector with at least two points")
    steps = np.diff(values)
    return {
        "steps": steps.tolist(),
        "worst_increase": float(steps.max()),   # P-3b doc CAI NAY
        "worst_decrease": float(steps.min()),   # P-3 (void) doc cai kia
        "n_steps": int(steps.size),
        "gate_read": "max(diff) <= +%.3f" % STEP_UP_TOLERANCE,
    }


def seed_independence(primary) -> dict:
    """NC-0: tu choi mot lan chay am tham tai lap lai G'.5b.

    Che do hong duy nhat cua khuon mau rebind la QUEN rebind. Khi do vector
    acceptance trung bit-doi-bit voi cai da cong bo, va "seed thu ba" chi la
    mot cau chuyen. Kiem bang may, khong bang tri nho.
    """
    if not G5B_ARTIFACT.exists():
        return {"checked": False, "distinct": None,
                "reason": "artifact G'.5b khong ton tai"}
    previous = json.loads(G5B_ARTIFACT.read_text())
    old = np.asarray(
        previous["results"]["primary"]["maxscore"]["acceptance_by_omega"], float)
    new = np.asarray(primary["maxscore"]["acceptance_by_omega"], float)
    return {"checked": True,
            "distinct": bool(not np.array_equal(old, new)),
            "max_abs_difference": float(np.abs(new - old).max()),
            "g5b_acceptance": old.tolist(),
            "g5b_sha256": sha256_of(G5B_ARTIFACT)}


def adjudicate(primary, null, monotone, independence) -> dict:
    """Cay phan quyet doc 72 section 4, `P-3` thay bang `P-3b`, them `NC-0`."""
    p = primary["maxscore"]
    gates = {
        "NC-0": bool(independence.get("distinct")),
        "P-1": bool(p["amplitude"] >= 0.050),
        "P-2": bool(p["snr"] >= 5.0),
        "P-3b": bool(monotone["worst_increase"] <= STEP_UP_TOLERANCE),
        "NC-1": bool(p["coverage_amplitude"] <= 0.005),
        "NC-2": bool(null["maxscore"]["amplitude"] <= 0.010),
    }
    if not gates["NC-0"]:
        verdict = "INVALID_SEED_NOT_INDEPENDENT"
    elif not (gates["NC-1"] and gates["NC-2"]):
        verdict = "STOP_GENERATOR"
    elif not gates["P-1"]:
        verdict = "POWER_TOO_WEAK"
    elif not (gates["P-2"] and gates["P-3b"]):
        verdict = "ADOPT_WEAK"
    else:
        verdict = "POWER_AXIS_HOLDS"

    remainder = p["irreducible_remainder"]
    classification = None
    if verdict == "POWER_AXIS_HOLDS":
        classification = ("REDUCIBLE_TO_EFFECTIVE_SIGMA" if abs(remainder) < 0.03
                          else "IRREDUCIBLE")
    return {"gates": gates, "verdict": verdict,
            "classification": classification,
            "irreducible_remainder": remainder}


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    if g5b.SEED != SEED_C:
        raise RuntimeError("rebind seed khong co hieu luc; dung lai")

    prereg_commit = subprocess.check_output(
        ["git", "rev-parse", "phase-G2-g5c-prereg"], text=True).strip()
    if provenance()["git_head_at_execution"] != prereg_commit:
        raise RuntimeError("run must start at the preregistration commit")
    if provenance()["worktree_dirty_at_execution"]:
        raise RuntimeError("tracked worktree must be clean before execution")

    sources = verify_protected()
    started = time.monotonic()

    print(f"Starting primary: seed={SEED_C}, replicates={g5b.REPLICATES}", flush=True)
    primary_rows = g5b.sweep(null_pair=False)
    primary = g5b.summarize(primary_rows)
    acceptance = np.array([[s["maxscore"]["acceptance"] for s in r["samples"]]
                           for r in primary_rows])
    paired_steps = np.diff(acceptance, axis=0)
    paired_diagnostics = {
        "step_mc_se": (paired_steps.std(axis=1, ddof=1) /
                       np.sqrt(g5b.REPLICATES)).tolist(),
        "adjacent_replicate_covariance": [float(np.cov(a, b, ddof=1)[0, 1])
                                           for a, b in zip(acceptance, acceptance[1:])],
        "role": "report only; no gate or threshold change",
    }
    print("Primary complete; starting null sweep", flush=True)
    null = g5b.summarize(g5b.sweep(null_pair=True))

    monotone = monotone_stats(primary["maxscore"]["acceptance_by_omega"])
    independence = seed_independence(primary)
    decision = adjudicate(primary, null, monotone, independence)

    if sources != verify_protected():
        raise RuntimeError("nguon duoc bao ve doi trong luc chay")

    payload = {
        "schema": "dt4n.phase_g2.g5c_monotone.v1",
        "status": "SYNTHETIC_NO_NETWORK",
        "results": {"primary": primary, "null_uA_uB": null},
        "monotonicity": monotone,
        "seed_independence": independence,
        "paired_step_diagnostics": paired_diagnostics,
        **decision,
        "design": {
            "seed": SEED_C,
            "seed_source": "rebound tools.g5b_power_axis.SEED at import",
            "omega_grid": list(g5b.OMEGAS),
            "replicates": g5b.REPLICATES,
            "dt_s": g5b.DT, "tau_s": g5b.TAU,
            "kappa_time_simulated": 1,
            "kappa_accept": g5b.KAPPA_ACCEPT,
            "alpha": g5b.ALPHA,
            "step_up_tolerance": STEP_UP_TOLERANCE,
            "gate_change": {
                "retired": "P-3: min(diff) >= -0.005  (VOID, G-L111)",
                "signed": "P-3b: max(diff) <= +0.005",
                "reason": "sign correction, not threshold relaxation",
            },
            "surrogate": ("score matrix scaled by measured c; "
                          "twin margins held at omega=0"),
        },
        "provenance": provenance(),
        "prereg_commit": prereg_commit,
        "python_executable": sys.executable,
        "numpy_version": np.__version__,
        "elapsed_s": time.monotonic() - started,
        "source_sha256": {
            **sources,
            "tools/g5c_monotone.py": sha256_of(__file__),
            "tools/g5b_power_axis.py": sha256_of("tools/g5b_power_axis.py"),
            PREREG: sha256_of(PREREG),
            str(G5B_ARTIFACT): sha256_of(G5B_ARTIFACT),
        },
    }
    write_contract_artifact(OUT, payload)
    print(json.dumps({k: payload[k] for k in
                      ("verdict", "classification", "gates",
                       "monotonicity", "irreducible_remainder", "elapsed_s")},
                     indent=2))


if __name__ == "__main__":
    main()

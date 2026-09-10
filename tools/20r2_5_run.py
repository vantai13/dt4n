#!/usr/bin/env python3
"""20R2.5 -- THUC THI ke hoach da ky. THUAN CO CHE: khong doc mot cot ket qua nao.

SO CAI LA NGUON SU THAT
=======================
docs/phase-20R2/04-campaign-log.jsonl la so cai; file tren dia la HE QUA. Day
la write-ahead log (ARIES): mot thay doi chi "co that" khi ban ghi cua no da
nam trong log, va log phai CHAM DIA (fsync) truoc buoc sau.

    parquet CO dong so, sha KHOP    -> hop le, bo qua khi resume
    parquet CO dong so, sha LECH    -> ai do da sua bang chung -> DUNG
    parquet KHONG co dong so        -> MO COI (chet giua chung) -> xoa, chay lai

Runner T2 bo qua moi file "da ton tai va > 0 byte". Mot parquet bi CAT CUT do
mat dien cung > 0 byte, va se bi bo qua IM LANG. Day la loi thiet ke nho ma
that -- so cai sua no.

SO CAI NAM TRONG docs/, khong phai results/
===========================================
No la SO SACH, khong phai ket qua do dac. Nho vay: khong phai luon qua
.gitignore, va khong bi test_no_stale_axes quet nhu mot artifact do dac.

    python -m tools.20r2_5_run --dry-run     # xem 167 lenh, khong chay gi
    python -m tools.20r2_5_run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/phase-20R2/03-run-plan.json"
LOG = ROOT / "docs/phase-20R2/04-campaign-log.jsonl"
TAG = "phase-20R2-prereg-signed"

# Ky KE HOACH ma khong ky DUNG CU thi chua ky gi ca: cung mot ke hoach chay
# tren mot harness khac cho mot chien dich khac.
INSTRUMENT = ("measurements", "twin", "cert", "tools/20r2_5_plan.py",
              "tools/20r2_5_run.py", "tools/20r2_5_perfect_twin.py")
# Duoc phep "ban" khi RESUME: chinh dau ra cua chien dich va so cai cua no.
# Neu khong loai, phien resume thu hai luon DUNG vi chinh no da ghi file.
CAMPAIGN_OWNED = (":(exclude)results", ":(exclude)docs/phase-20R2/04-campaign-log.jsonl")


def _git(*a: str) -> str:
    try:
        return subprocess.check_output(["git", *a], text=True, cwd=ROOT,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _sha(p: pathlib.Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _clean(text: str) -> str:
    return text.replace(str(ROOT), "<REPO>")      # 20R2-L7: khong ro ri duong dan may


def sidecar_of(p: pathlib.Path) -> pathlib.Path:
    return p.with_name(p.name[: -len(".parquet")] + "_report.json")


def guard() -> None:
    """Chan TRUOC khi tieu mot giay CPU nao."""
    if not _git("tag", "-l", TAG):
        raise SystemExit("DUNG: chua co tag %s -- prereg §11 chua ky." % TAG)
    if not _git("ls-remote", "--tags", "origin", TAG):
        # Ky tren may minh ma chua push thi voi moi nguoi khac VAN la chua ky.
        raise SystemExit("DUNG: tag chua co tren REMOTE -- chua phai dau vet.")
    dirty = _git("status", "--porcelain", "--", ".", *CAMPAIGN_OWNED)
    if dirty:
        raise SystemExit("DUNG: worktree ban ngoai phan chien dich so huu:\n" + dirty)
    changed = _git("diff", "--name-only", TAG, "HEAD", "--",
                   "docs/phase-20R2/03-run-plan.json", *INSTRUMENT)
    if changed:
        raise SystemExit("DUNG: ke hoach/dung cu doi SAU khi ky -> can AMENDMENT:\n"
                         + changed)


def env_fingerprint() -> dict:
    import numpy, pandas, pyarrow
    keys = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "PYTHONHASHSEED")
    return {"python": platform.python_version(), "numpy": numpy.__version__,
            "pandas": pandas.__version__, "pyarrow": pyarrow.__version__,
            "system": platform.system(), "machine": platform.machine(),
            "env": {k: os.environ.get(k) for k in keys},
            "git_commit": _git("rev-parse", "HEAD"),
            # [20R2.5-C3] Mot annotated tag CO THE bi xoa roi tao lai
            # (`git push -f --tags`). `ls-remote` chi chung minh tag TON TAI
            # luc kiem, KHONG chung minh no BAT BIEN. Ghi DICH cua tag vao so
            # cai: hygiene H2 doi signed_tag_commit == git_commit, nen so cai
            # TU chung minh chien dich chay dung commit da ky -- khong can ai
            # tin rang tag chua bi doi.
            "signed_tag_commit": _git("rev-parse", TAG + "^{commit}")}


def read_log() -> list:
    if not LOG.exists():
        return []
    return [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]


def append_log(entry: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())          # dong so phai CHAM DIA truoc buoc sau


def run_control(phase: str, plan: dict) -> None:
    out = "results/SMOKE/phase-20R2/perfect_twin_%s.json" % phase
    cmd = ["-m", "tools.20r2_5_perfect_twin",
           "--calibration", plan["branches"]["main"]["calibration"], "--out", out]
    t0 = time.time()
    r = subprocess.run([sys.executable, *cmd], cwd=ROOT, capture_output=True, text=True)
    append_log({"kind": "control_" + phase, "cmd": cmd, "returncode": r.returncode,
                "seconds": time.time() - t0, "out": out, "sha256": _sha(ROOT / out),
                "git_commit": _git("rev-parse", "HEAD"), "timestamp_utc": _now()})
    print("twin-hoan-hao (%s): %s" % (phase, "PASS" if r.returncode == 0 else "FAIL"))
    if r.returncode != 0:
        raise SystemExit("DUNG: dung cu hong (%s).\n%s" % (phase, _clean(r.stderr[-1500:])))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-guard", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    runs = plan["runs"]

    if a.dry_run:
        for r in runs:
            print("%3d %s %s" % (r["run_index"], "C" if r["is_canary"] else " ",
                                 " ".join(r["cmd"][2:])))
        print("\n%d lenh + %d diem canh. KHONG chay gi." % (plan["n_runs"], plan["n_canaries"]))
        return 0
    if not a.skip_guard:
        guard()

    log = read_log()
    # guard_skipped di VAO dau van tay, nen mot chien dich chay lach guard se
    # bi hygiene H2 danh FAIL -- khong the lach im lang.
    fp = {**env_fingerprint(), "guard_skipped": bool(a.skip_guard)}
    envs = [e for e in log if e["kind"] == "env"]
    if envs:
        prev = {k: v for k, v in envs[0].items() if k not in ("kind", "timestamp_utc")}
        if prev != fp:
            raise SystemExit("DUNG: moi truong/commit KHAC phien truoc.\n  cu : %s\n  moi: %s"
                             % (prev, fp))
    else:
        append_log({"kind": "env", **fp, "timestamp_utc": _now()})

    if not any(e["kind"] == "control_pre" and e["returncode"] == 0 for e in log):
        run_control("pre", plan)

    done = {e["run_index"]: e for e in read_log()
            if e["kind"] == "run" and e["returncode"] == 0}
    t_session = 0.0
    for r in runs:
        target = ROOT / r["out"]
        side = sidecar_of(target)
        head = "[%3d/%3d] %-14s tau=%-4g a=%-3g seed=%-4d" % (
            r["run_index"] + 1, len(runs), "CANARY" if r["is_canary"] else r["branch"],
            r["tau"], r["a"], r["seed"])
        if r["run_index"] in done:
            e = done[r["run_index"]]
            if _sha(target) != e["sha256"] or _sha(side) != e["sidecar_sha256"]:
                raise SystemExit("DUNG: %s -- file tren dia KHAC so cai (bang chung bi sua)."
                                 % r["out"])
            continue
        try:
            for p in (target, side):      # MO COI: co file ma khong co dong so
                if p.exists():
                    p.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            # [20R2.6-0.1] Phan CHUAN BI nay chay TRUOC append_log, nen truoc
            # ban va mot ngoai le o day (vd PermissionError khi tang SUPERSEDED
            # bi khoa 555) van ra khoi runner ma KHONG de lai mot dong so nao.
            # So cai khi do dung ve TRANG THAI nhung thieu ve LICH SU -- da xay
            # ra that 2026-09-10, xem docs/phase-20R2/04b-attempt1-permerror.md.
            # Gio moi lan chet deu co dong so.
            append_log({"kind": "run",
                        **{k: r[k] for k in ("run_index", "is_canary", "tau", "branch",
                                             "a", "seed", "n", "out", "cmd")},
                        "returncode": -1, "seconds": 0.0,
                        "sha256": None, "sidecar_sha256": None,
                        "sidecar": sidecar_of(pathlib.Path(r["out"])).as_posix(),
                        "git_commit": fp["git_commit"], "timestamp_utc": _now(),
                        "stage": "prepare_output_path",
                        "error": _clean("%s: %s" % (type(exc).__name__, exc))})
            print(head + "  LOI CHUAN BI: %s" % _clean(str(exc)))
            raise
        t0 = time.time()
        proc = subprocess.run([sys.executable, *r["cmd"]], cwd=ROOT,
                              capture_output=True, text=True)
        dt = time.time() - t0
        t_session += dt
        ok = proc.returncode == 0 and target.exists() and side.exists()
        append_log({"kind": "run",
                    **{k: r[k] for k in ("run_index", "is_canary", "tau", "branch",
                                         "a", "seed", "n", "out", "cmd")},
                    "returncode": proc.returncode, "seconds": dt,
                    "sha256": _sha(target),
                    "sidecar": sidecar_of(pathlib.Path(r["out"])).as_posix(),
                    "sidecar_sha256": _sha(side), "git_commit": fp["git_commit"],
                    "timestamp_utc": _now(),
                    "stderr_tail": "" if ok else _clean(proc.stderr[-800:])})
        print(head + "  %6.1f s  %s" % (dt, "ok" if ok else "LOI"))
        if not ok:
            # Chay tiep qua mot loi chua ro la tron mot cai KHONG BIET vao ket
            # qua sach. Dung ngay, chan doan, roi resume.
            raise SystemExit("DUNG o run_index=%d. Khong chay tiep qua loi chua ro."
                             % r["run_index"])

    if not any(e["kind"] == "control_post" and e["returncode"] == 0 for e in read_log()):
        run_control("post", plan)
    print("\nphien nay: %.1f phut. Tiep theo: python -m tools.20r2_5_hygiene"
          "  -- CHUA duoc mo ket qua." % (t_session / 60))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

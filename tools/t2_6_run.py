#!/usr/bin/env python3
"""T2.6 -- thuc thi ke hoach. THUAN CO CHE.

File nay KHONG doc mot nguong nao va KHONG sinh mot cot phan quyet nao.
No chay dung ke hoach da ky o docs/phase-T2/03-run-plan.json, theo dung
thu tu da ghi, va ghi mot so nhat ky.

CO THE DUNG VA CHAY TIEP: mot lenh da co parquet hop le thi bo qua, nen
mot lan Ctrl-C khong lam mat cong da chay.

    python3 tools/t2_6_run.py --out-dir results/PENDING/phase-T2/sweep --dry-run
    python3 tools/t2_6_run.py --out-dir results/PENDING/phase-T2/sweep
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/phase-T2/03-run-plan.json"
TAG = "phase-T2-prereg-signed"


def _rel(p: pathlib.Path) -> str:
    """Duong dan tuong doi so voi repo khi duoc, tuyet doi khi khong.

    `Path.relative_to` NEM khi dich nam ngoai repo (vi du --out-dir tro vao
    /tmp luc smoke test). Loi do xay ra SAU khi lenh da chay xong, nen no
    vut di ca ket qua lan dong nhat ky -- dung cai dat tien nhat de mat cong.
    """
    try:
        return str(p.resolve().relative_to(ROOT))
    except ValueError:
        return str(p.resolve())


def _git(*a: str) -> str:
    try:
        return subprocess.check_output(["git", *a], text=True, cwd=ROOT).strip()
    except Exception:
        return ""


def guard() -> None:
    """Bon dieu kien TRUOC khi chay mot o nao. Prereg tu dat ra chung."""
    if not _git("tag", "-l", TAG):
        raise SystemExit(
            "DUNG: tag %s chua ton tai.\n"
            "Prereg tu ghi: 'KHONG chay bat ky o nao cua T2.6 truoc khi file "
            "nay duoc ky, commit, tag VA PUSH.'" % TAG)

    # Tren REMOTE, khong chi local: chinh prereg viet 'Hieu luc den tu dau
    # vet'. Mot tag chua push la mot ghi chu ca nhan, khong phai dau vet.
    if not _git("ls-remote", "--tags", "origin", TAG):
        raise SystemExit(
            "DUNG: tag %s chua co tren REMOTE. Mot tag chua push la mot ghi "
            "chu ca nhan, khong phai mot dau vet." % TAG)

    if _git("status", "--porcelain"):
        raise SystemExit(
            "DUNG: worktree ban. Mot chien dich chay tren code chua commit "
            "thi khong quy trach nhiem duoc cho phien ban nao.")

    # Ke hoach phai la ke hoach DA KY, khong phai mot ban sinh lai sau do.
    # Sinh lai cho THU TU y het (cung ORDER_SEED) nhung hash DOI vi provenance
    # mang git_commit/git_dirty. Khong co kiem nay, ban co the chay mot ke
    # hoach KHAC voi ke hoach da ky ma khong he biet.
    plan_at_tag = _git("show", "%s:docs/phase-T2/03-run-plan.json" % TAG)
    if plan_at_tag:
        h_tag = hashlib.sha256((plan_at_tag + "\n").encode()).hexdigest()
        h_raw = hashlib.sha256(plan_at_tag.encode()).hexdigest()
        h_now = hashlib.sha256(PLAN.read_bytes()).hexdigest()
        if h_now not in (h_tag, h_raw):
            raise SystemExit(
                "DUNG: 03-run-plan.json da doi so voi luc ky.\n"
                "  luc ky  : %s\n  hien tai: %s\n"
                "Doi ke hoach sau khi ky la mot AMENDMENT, khong phai mot lan chay."
                % (h_raw, h_now))


def command_for(run: dict, out_dir: str) -> list[str]:
    """Giong het tools/t2_6_plan.command_for, nhung dung sys.executable."""
    cmd = [sys.executable, "-m", "measurements.decision_error_v2", "--run-fixed",
           "--tau", "%g" % run["tau"],
           "--z-mode", run["branch"],
           "--seeds", str(run["seed"]),
           "--out", "%s/t2_6_r%04d.parquet" % (out_dir, run["run_index"])]
    if run["a"] != 0.9:
        cmd += ["--a-override", "%g" % run["a"]]
    return cmd


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="in lenh, khong chay -- doc lai truoc khi tieu 30 phut")
    ap.add_argument("--skip-guard", action="store_true", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)

    if not a.skip_guard and not a.dry_run:
        guard()

    plan = json.loads(PLAN.read_text())
    runs = plan["runs"]
    out_dir = ROOT / a.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "run_log.jsonl"

    print("ke hoach : %d lenh (%d diem canh)" % (plan["n_runs"], plan["n_canaries"]))
    print("thu tu   : da xao voi order_seed = %s" % plan["provenance"]["order_seed"])
    print("dau ra   : %s" % out_dir)

    t_all = time.time()
    for i, run in enumerate(runs):
        cmd = command_for(run, str(out_dir))
        target = pathlib.Path(cmd[cmd.index("--out") + 1])
        tag = "CANARY" if run["is_canary"] else "      "
        head = "[%3d/%3d] %s tau=%-5g %-6s a=%-4g seed=%-4d" % (
            i + 1, len(runs), tag, run["tau"], run["branch"], run["a"], run["seed"])

        if a.dry_run:
            print(head + "  " + " ".join(cmd[2:]))
            continue
        if target.exists() and target.stat().st_size > 0:
            print(head + "  BO QUA (da co)")
            continue

        t0 = time.time()
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        dt = time.time() - t0
        ok = (r.returncode == 0 and target.exists())
        print(head + "  %5.1f s  %s" % (dt, "ok" if ok else "LOI rc=%d" % r.returncode))
        if not ok:
            print(r.stderr[-2000:])

        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "run_index": run["run_index"], "is_canary": run["is_canary"],
                "tau": run["tau"], "branch": run["branch"],
                "a": run["a"], "seed": run["seed"],
                "cmd": cmd[1:], "returncode": r.returncode,
                "seconds": dt, "out": _rel(target),
                "sha256": (hashlib.sha256(target.read_bytes()).hexdigest()
                           if ok else None),
                "git_commit": _git("rev-parse", "HEAD"),
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, sort_keys=True) + "\n")

        if not ok:
            # DUNG NGAY. Chay tiep se tron mot loi vao 150 ket qua sach va
            # ban se khong nho o nao. Mot chien dich dung som thi phan tich
            # duoc; mot chien dich chay tiep qua loi thi khong.
            raise SystemExit(
                "DUNG o run_index=%d. Khong chay tiep tren mot loi khong ro "
                "nguyen nhan." % run["run_index"])

    if not a.dry_run:
        print("\nTONG: %.1f phut" % ((time.time() - t_all) / 60.0))
        print("nhat ky: %s" % _rel(log_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

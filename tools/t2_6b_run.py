#!/usr/bin/env python3
"""T2.6 vong 3 -- chay dung ke hoach da dong bang, ghi run_log day du.

File nay KHONG quyet dinh gi. No doc 06-run-plan-v3.json va thuc thi. Neu
ban thay minh muon them mot nhanh `if` o day, do la chinh sach ro vao co che.

    python3 tools/t2_6b_run.py --out-dir results/PENDING/phase-T2/sweep_r3
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
sys.path.insert(0, str(ROOT))
from tools.t2_6b_plan import command_for            # noqa: E402

PLAN = ROOT / "docs/phase-T2/06-run-plan-v3.json"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="results/PENDING/phase-T2/sweep_r3")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    plan = json.loads(PLAN.read_text())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True, cwd=ROOT).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"],
                                         text=True, cwd=ROOT).strip())
    if dirty and not args.dry_run:
        print("!! cay lam viec BAN. Commit truoc khi chay -- neu khong, "
              "run_log ghi mot commit KHONG mo ta duoc code da chay.")
        return 2

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    log = out_dir / "run_log.jsonl"
    t_all = time.time()

    with log.open("a", encoding="utf-8") as f:
        for r in plan["runs"]:
            cmd = command_for(r, str(out_dir))
            if args.dry_run:
                print(" ".join(cmd)); continue
            t0 = time.time()
            p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
            art = ROOT / cmd[-1]
            rec = {
                "run_index": r["run_index"], "scope": r["scope"],
                "mode": r["mode"], "rho_bar": r["rho_bar"], "a": r["a"],
                "cmd": cmd, "rc": p.returncode,
                "seconds": round(time.time() - t0, 2),
                "commit": commit,
                "sha256": (hashlib.sha256(art.read_bytes()).hexdigest()
                           if art.is_file() else None),
            }
            f.write(json.dumps(rec) + "\n"); f.flush()
            print("%2d rc=%d %6.1fs %-8s %.3f a=%.1f %s"
                  % (r["run_index"], p.returncode, rec["seconds"],
                     r["mode"], r["rho_bar"], r["a"], r["scope"]))
            if p.returncode:
                print(p.stderr[-2000:])
                print("!! DUNG: mot lenh that bai. Sua roi chay lai TU DAU "
                      "de thu tu ngau nhien van la thu tu da ky.")
                return 1

    if not args.dry_run:
        print("TONG %.1f phut" % ((time.time() - t_all) / 60))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Phan tang results/ thanh RAW / LIVE / SUPERSEDED / SMOKE.  (Lesson 23.17)

Bon tang, khong phai ba: 78% file trong results/ la du lieu DO THO. Ep chung
vao LIVE hay SUPERSEDED la sai khai niem -- chung khong phai ket luan, chung
la bang chung goc, va chung thuoc Hang 1 (khong tai tao duoc).

Tieu chi:
    RAW         file sinh boi mot lan chay Mininet/probe/campaign -> PHEP DO
    LIVE        file dan xuat ma MOI truc cua no DA DUOC DUYET
    PENDING     hien hanh, nhung CHO mot truc duoc duyet (amendment 23-49d
                muc 4). Khac SUPERSEDED: no CHO, khong bi THAY THE.
    SUPERSEDED  file dan xuat co ban thay the moi hon / tren truc z sai
    SMOKE       pilot, attempt, preflight, FAILED, smoke -- moi lan chay
                KHONG nham tao ket qua cuoi

Hai diem khac ban trong giao trinh, do thuc te repo nay:

  1. `git mv` chi ap dung cho file DUOC TRACK. Repo co 2.201 file bi
     .gitignore (raw local, 427 MiB AoI campaign...). Voi chung dung hard-link
     + unlink NO-REPLACE: van phan tang, khong co lich su git, khong ghi de dich.
  2. RAW_TREES la TIEN TO CAY, khong phai thu muc phang. `aoi_v7_campaign`
     co 30 thu muc con `flows_*`; neu chi khop thu muc cha thi 960 file do
     roi nham vao SUPERSEDED.

Chay:
    python tools/tier_results.py            # DRY RUN, chi in ra
    python tools/tier_results.py --apply    # thuc su di chuyen
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import Counter
from typing import Sequence

ROOT = "results"
TIERS = ("RAW", "LIVE", "PENDING", "SUPERSEDED", "SMOKE")

# --- Luat phan loai, theo thu tu uu tien (khop dau tien thang) -------------

SMOKE_PAT = re.compile(
    r"(FAILED|attempt[0-9]|_smoke|smoke_|preflight|pilot[0-9]|\.pre[A-Z]|_bg\.)"
)

# Cay du lieu do tho -> RAW. Danh sach TUONG MINH, khong doan bang pattern.
# Moi muc la mot TIEN TO: moi file nam duoi cay deu la RAW.
RAW_TREES = (
    "results/phase-L/raw",
    "results/phase-L/golden",
    "results/phase-T/raw",
    "results/phase-T/sealed",
    "results/phase-23/aoi_v7_campaign",
    "results/phase-23/raw_differential",
    "results/phase-23/raw_differential_v2",
    "results/phase-23/differential_live",
    "results/phase-23/differential_live_v2",
    "results/phase-20R/raw",
    "results/phase-20R/raw_additivity",          # + moi bien the raw_additivity_*
    "results/phase-20/flow_logs",
)

# Artifact z-INDEPENDENT -> vao LIVE ngay. Danh sach TUONG MINH.
# Moi file o day phai co ly do ghi trong results/MANIFEST.md.
LIVE_ALLOW = {
    "results/phase-20R/truth_table.parquet",
    "results/phase-20R/decision_error_by_age_by_regime.parquet",
    "results/phase-20R/sla_calibration.json",
    "results/phase-L/link_model_v2_fit.json",
    "results/phase-23/aoi_v7_estimates.json",
    "results/phase-23/dsync_sensitivity.json",
    "results/phase-23/a0_instrument_calibration.json",
}


def classify(path: str) -> str:
    """Tra ve mot trong: RAW / SMOKE / LIVE / SUPERSEDED."""
    parent = os.path.dirname(path)
    name = os.path.basename(path)

    if parent.startswith(RAW_TREES):
        return "RAW"
    if SMOKE_PAT.search(name) or SMOKE_PAT.search(parent):
        return "SMOKE"
    if path in LIVE_ALLOW:
        return "LIVE"
    # Mac dinh: moi thu con lai la DAN XUAT TREN TRUC z SAI.
    # Bi quan la dung: buoc ban phai TUONG MINH dua tung file len LIVE.
    # Loi bo sot khi do gay ON AO (hinh thieu du lieu), khong gay IM LANG
    # (artifact truc sai lang le vao paper).
    return "SUPERSEDED"


def target(path: str, tier: str) -> str:
    rel = os.path.relpath(path, ROOT)      # vd: phase-20R/truth_table.parquet
    return os.path.join(ROOT, tier, rel)


def _tracked() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z", ROOT], capture_output=True, text=True, check=True
    ).stdout
    return {p for p in out.split("\0") if p}


def destination_collisions(moves) -> list[tuple[str, str, str]]:
    """Tra cac dich se bi ghi de, TRUOC khi bat ky file nao duoc dich.

    `os.replace` va `git mv -f` deu cho phep mat byte cu im lang. Dung
    `lexists` thay vi `exists` de mot symlink gay cung khong thanh loi thoat.
    Mot dich lap lai trong chinh ke hoach cung la va cham, ke ca no chua ton
    tai tren dia.
    """
    normalized = [
        (src, dst, os.path.normcase(os.path.abspath(dst)))
        for src, dst, _tier, _tracked_file in moves
        if os.path.normcase(os.path.abspath(src))
        != os.path.normcase(os.path.abspath(dst))
    ]
    duplicate_dsts = {
        dst_key for dst_key, count in Counter(row[2] for row in normalized).items()
        if count > 1
    }
    collisions = []
    for src, dst, dst_key in normalized:
        if os.path.lexists(dst):
            collisions.append((src, dst, "destination already exists"))
        elif dst_key in duplicate_dsts:
            collisions.append((src, dst, "duplicate destination in move plan"))
    return collisions


def _move_untracked_no_replace(src: str, dst: str) -> None:
    """Publish a complete file atomically, but never replace `dst`.

    Hard-link creation is atomic and fails with FileExistsError if another
    process creates `dst` after the preflight.  Unlinking the old name then
    completes the move.  A crash between the two calls leaves two names for
    the same bytes (recoverable), never a truncated or overwritten artifact.
    Source and destination are below the same results/ tree, so they share a
    filesystem; EXDEV is deliberately fatal rather than falling back to an
    unsafe copy.
    """
    os.link(src, dst, follow_symlinks=False)
    try:
        os.unlink(src)
    except BaseException:
        # Roll back the new name if removing the source fails.  At this point
        # `dst` is the hard link created by this function, not a prior file.
        os.unlink(dst)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="thuc su di chuyen")
    ap.add_argument("--map-out", default=None,
                    help="ghi bang anh xa cu->moi ra file TSV")
    args = ap.parse_args(argv)

    tracked = _tracked()
    moves = []
    counts = {t: [0, 0] for t in TIERS}       # [tracked, untracked]

    for dirpath, dirs, files in os.walk(ROOT):
        # bo qua cac tang da tao
        dirs[:] = [d for d in dirs
                   if not (dirpath == ROOT and d in TIERS)]
        for f in sorted(files):
            if f in ("MANIFEST.md", "PATH_MAP.tsv"):
                continue
            src = os.path.join(dirpath, f)
            tier = classify(src)
            is_tracked = src in tracked
            counts[tier][0 if is_tracked else 1] += 1
            moves.append((src, target(src, tier), tier, is_tracked))

    collisions = destination_collisions(moves)
    if collisions:
        print(
            "DUNG: phat hien %d va cham dich; CHUA di chuyen file nao."
            % len(collisions),
            file=sys.stderr,
        )
        for src, dst, reason in collisions:
            print("  %s\n    -> %s (%s)" % (src, dst, reason), file=sys.stderr)
        return 2

    print("=== TOM TAT ===")
    print(f"  {'tang':12} {'tracked':>8} {'ignored':>8} {'tong':>8}")
    for t in TIERS:
        tr, un = counts[t]
        print(f"  {t:12} {tr:8} {un:8} {tr + un:8}")
    tot_tr = sum(c[0] for c in counts.values())
    tot_un = sum(c[1] for c in counts.values())
    print(f"  {'TONG':12} {tot_tr:8} {tot_un:8} {tot_tr + tot_un:8}")

    if args.map_out:
        with open(args.map_out, "w", encoding="utf-8") as fh:
            fh.write("old\tnew\ttier\ttracked\n")
            for src, dst, tier, tr in moves:
                fh.write(f"{src}\t{dst}\t{tier}\t{int(tr)}\n")
        print(f"\nBang anh xa -> {args.map_out}")

    if not args.apply:
        print("\n=== 30 VI DU DAU (DRY RUN, chua di chuyen gi) ===")
        for src, dst, tier, tr in moves[:30]:
            flag = "git" if tr else "fs "
            print(f"  [{tier:11}][{flag}] {src}\n                    -> {dst}")
        print("\nChay lai voi --apply de thuc hien.")
        return 0

    n_git = n_fs = 0
    for src, dst, _tier, is_tracked in moves:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if is_tracked:
            # Khong `-f`: neu dich xuat hien sau preflight, git phai DUNG.
            subprocess.run(["git", "mv", src, dst], check=True)
            n_git += 1
        else:
            _move_untracked_no_replace(src, dst)
            n_fs += 1

    # don thu muc rong con lai (khong dung file nao)
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
        if os.path.basename(dirpath) in TIERS and os.path.dirname(dirpath) == ROOT:
            continue
        if not dirnames and not filenames:
            os.rmdir(dirpath)

    print(f"\nDa di chuyen {n_git} file bang `git mv` "
          f"va {n_fs} file (bi .gitignore) bang hard-link + unlink no-replace.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

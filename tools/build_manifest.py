#!/usr/bin/env python3
"""Sinh results/MANIFEST.md tu provenance + validity cua tung artifact.

Phan chia trach nhiem:
  MAY dien : duong dan, script sinh ra, nhan truc, git hash, thoi diem
  NGUOI dien: cot "Dung cho" -- day la Y DINH, may khong suy duoc tu du lieu

Tu dong hoa phan deterministic, de lai phan can phan doan.

Chay: python tools/build_manifest.py > results/MANIFEST.md
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIERS = ("LIVE", "SUPERSEDED", "SMOKE")
INTENT_PATH = os.path.join(REPO, "results", "_intent.json")


def read_meta(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return {}
    if not isinstance(d, dict):
        return {}
    prov = d.get("provenance", {}) or {}
    val = d.get("validity", {}) or {}

    # Repo co nhieu the he schema. Uu tien khoi `provenance` chuan, roi moi
    # rot xuong cac khoa cu -- de manifest khong day "?" cho artifact tien-NT33.
    def first(*cands):
        for c in cands:
            if isinstance(c, str) and c:
                return c
            if isinstance(c, list) and c:
                return str(c[0])
        return "?"

    return {
        "script": first(prov.get("script"), d.get("script"), d.get("source"),
                        d.get("generated_by")),
        "git": first(prov.get("git_hash"), d.get("git_hash"),
                     d.get("git_hash_values"), d.get("git"))[:7],
        "ts": first(prov.get("timestamp_utc"), d.get("timestamp_utc"),
                    d.get("generated_date"), d.get("created"))[:10],
        "aoi": (val.get("aoi_axis", {}) or {}).get("label", "-"),
        "sla": (val.get("sla_axis", {}) or {}).get("label", "-"),
    }


def load_intent() -> dict:
    """Cot 'Dung cho' do NGUOI viet, giu trong mot file rieng de khong bi
    ghi de moi lan sinh lai manifest."""
    if os.path.exists(INTENT_PATH):
        with open(INTENT_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def tier_files(tier: str) -> list[str]:
    root = os.path.join(REPO, "results", tier)
    files = sorted(glob.glob(os.path.join(root, "**", "*.json"), recursive=True))
    files += sorted(glob.glob(os.path.join(root, "**", "*.parquet"), recursive=True))
    return files


def count(path: str) -> int:
    return sum(len(f) for _, _, f in os.walk(path))


def main() -> None:
    intent = load_intent()
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()

    print("# MANIFEST -- kho artifact DT4N\n")
    print("Sinh tu dong boi `tools/build_manifest.py` tai commit "
          f"`{head}`. Cot **Dung cho** do NGUOI dien, luu trong "
          "`results/_intent.json` de khong bi ghi de.\n")
    print("Bon tang (Lesson 23.17, amendment 23-44):\n")
    print("```text")
    for t in ("RAW", "LIVE", "SUPERSEDED", "SMOKE"):
        root = os.path.join(REPO, "results", t)
        print(f"  {t:12} {count(root):5} file")
    print("```\n")
    print("`RAW/` khong liet ke tung file o day: do la du lieu do tho, Hang 1 "
          "(khong tai tao duoc), chi doc, khong bao gio ghi de. "
          "Xem `results/RAW/README.md`.\n")

    for tier in TIERS:
        files = tier_files(tier)
        root = os.path.join(REPO, "results", tier)
        print(f"\n## {tier}  ({len(files)} artifact json/parquet)\n")
        if not files:
            print("_(trong)_\n")
            continue
        print("| Artifact | Sinh boi | git | Ngay | Truc AoI | Truc SLA | Dung cho |")
        print("|---|---|---|---|---|---|---|")
        for f in files:
            rel = os.path.relpath(f, root).replace(os.sep, "/")
            m = read_meta(f) if f.endswith(".json") else {}
            use = intent.get(f"{tier}/{rel}", "_(dien tay)_")
            print(f"| `{rel}` | `{m.get('script','?')}` | `{m.get('git','?')}` "
                  f"| {m.get('ts','?')} | {m.get('aoi','-')} "
                  f"| {m.get('sla','-')} | {use} |")


if __name__ == "__main__":
    main()

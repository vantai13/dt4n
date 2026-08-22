#!/usr/bin/env python3
"""Tra cuu duong dan artifact CU -> MOI sau khi phan tang.   (Lesson 23.17)

Vi sao can module nay thay vi sua thang provenance trong artifact:

    Provenance ghi lai SU THAT LICH SU. Mot artifact ky ngay 2026-08-19 ghim
    `results/phase-23/lesson23_7_range_calibration.json` la ghi dung duong dan
    tai thoi diem do. Sua no thanh duong dan hom nay se lam ban ghi noi doi ve
    qua khu -- dung loi ma chinh Lesson 23.17 canh bao.

    SHA256 trong pin van xac minh NOI DUNG. Cai duy nhat mat di la VI TRI.
    Vay thi bo sung mot phep tra vi tri, dung sua ban ghi.

Nguon su that: results/PATH_MAP.tsv (sinh khi phan tang).
"""
from __future__ import annotations

import functools
import os

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_PATH = os.path.join(_REPO, "results", "PATH_MAP.tsv")


@functools.lru_cache(maxsize=1)
def _table() -> dict[str, str]:
    out: dict[str, str] = {}
    if not os.path.exists(MAP_PATH):
        return out
    with open(MAP_PATH, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or line.startswith("old\t"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2:
                out[parts[0]] = parts[1]
    return out


def resolve(path: str) -> str:
    """Tra ve duong dan hien tai cua `path`.

    - Neu file ton tai o `path`: tra nguyen (khong doan).
    - Neu khong, va `path` co trong PATH_MAP: tra duong dan sau phan tang.
    - Neu khong tra duoc: tra nguyen `path` de loi hien ra o cho goi,
      khong bi nuot o day.
    """
    if os.path.exists(os.path.join(_REPO, path)) or os.path.exists(path):
        return path
    return _table().get(path.replace(os.sep, "/"), path)


def exists(path: str) -> bool:
    """os.path.exists nhung co tra bang anh xa tang."""
    p = resolve(path)
    return os.path.exists(p) or os.path.exists(os.path.join(_REPO, p))

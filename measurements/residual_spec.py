#!/usr/bin/env python3
"""Phase 20R.6-v2 -- common schema for systematic residuals."""

from __future__ import annotations

import json
import math
import os
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np


Z90 = 1.644854
VALID_CHANNELS = ("loss", "delay_ms")
VALID_LEVELS = ("per_link", "per_path")


def git_commit() -> Dict[str, Any]:
    """Record the source tree that produced a residual artifact."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        )
    except Exception:
        commit, dirty = "unknown", True
    return {"git_commit": commit, "git_dirty": dirty}


@dataclass
class ResidualRecord:
    """One measured residual, with enough metadata to propagate it safely."""

    estimand: str
    source: str
    channel: str
    level: str
    mode: str
    point: float
    se: float
    per_unit: Dict[str, float] = field(default_factory=dict)
    se_unit: Dict[str, float] = field(default_factory=dict)
    cochran_q: Optional[float] = None
    cochran_df: Optional[int] = None
    i_squared: Optional[float] = None
    provenance: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.estimand or len(self.estimand.strip()) < 20:
            raise ValueError(
                "estimand phai la mot cau day du (>= 20 ky tu). "
                "Viet bang loi dai luong can do truoc khi tinh."
            )
        if self.channel not in VALID_CHANNELS:
            raise ValueError("channel phai thuoc %s" % (VALID_CHANNELS,))
        if self.level not in VALID_LEVELS:
            raise ValueError("level phai thuoc %s" % (VALID_LEVELS,))
        if self.se < 0:
            raise ValueError("se am -> loi tinh toan")
        if not self.provenance:
            self.provenance = git_commit()

    @property
    def ci90(self) -> List[float]:
        return [float(self.point) - Z90 * float(self.se), float(self.point) + Z90 * float(self.se)]

    @property
    def homogeneous(self) -> Optional[bool]:
        return None if self.i_squared is None else bool(self.i_squared < 0.5)

    @property
    def ci_contains_zero(self) -> bool:
        lo, hi = self.ci90
        return bool(lo <= 0.0 <= hi)

    def power_ok(self, delta: float) -> bool:
        return bool(Z90 * float(self.se) <= float(delta))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["ci90"] = self.ci90
        data["homogeneous"] = self.homogeneous
        data["ci_contains_zero"] = self.ci_contains_zero
        return data


def pool_inverse_variance(values: Sequence[float], ses: Sequence[float]) -> Dict[str, float]:
    """Pool compatible estimates with inverse-variance weights."""
    vals = np.asarray(values, dtype=float)
    se = np.asarray(ses, dtype=float)
    if vals.size == 0:
        raise ValueError("khong co gia tri de gop -- join rong (RC8)")
    if vals.size != se.size:
        raise ValueError("values va ses khong cung kich thuoc")
    if np.any(se <= 0):
        raise ValueError("se <= 0 -> khong the gop bang inverse-variance")

    w = 1.0 / se**2
    point = float(np.sum(w * vals) / np.sum(w))
    pooled_se = float(math.sqrt(1.0 / np.sum(w)))
    q = float(np.sum(w * (vals - point) ** 2))
    df = max(int(vals.size) - 1, 1)
    i2 = max(0.0, (q - df) / q) if q > 0 else 0.0
    return {
        "point": point,
        "se": pooled_se,
        "cochran_q": q,
        "cochran_df": int(df),
        "i_squared": i2,
    }


def save(records: Sequence[ResidualRecord], path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    payload = {"schema": "residual_spec/v1", "records": [record.to_dict() for record in records]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def load(path: str) -> List[ResidualRecord]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if payload.get("schema") != "residual_spec/v1":
        raise ValueError("schema khong khop: %r" % payload.get("schema"))
    records = []
    for raw in payload.get("records", []):
        data = dict(raw)
        for key in ("ci90", "homogeneous", "ci_contains_zero"):
            data.pop(key, None)
        records.append(ResidualRecord(**data))
    if not records:
        raise ValueError("file phan du RONG -- khong duoc chay tiep (RC8)")
    return records


def records_by_mode_channel(records: Sequence[ResidualRecord]) -> Dict[tuple[str, str], ResidualRecord]:
    out: Dict[tuple[str, str], ResidualRecord] = {}
    for record in records:
        key = (str(record.mode), str(record.channel))
        if key in out:
            raise ValueError("trung residual cho mode/channel %s" % (key,))
        out[key] = record
    return out


def as_jsonable(records: Sequence[ResidualRecord]) -> Dict[str, Any]:
    return {"schema": "residual_spec/v1", "records": [record.to_dict() for record in records]}

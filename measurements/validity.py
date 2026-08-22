#!/usr/bin/env python3
"""Khoi `validity`: artifact tu mo ta PHAM VI HIEU LUC cua chinh no.

Khac `provenance` (ai / luc nao / bang gi tao ra file) -- `validity` tra loi
"file nay con dung duoc khong, trong dieu kien nao".

    PROVENANCE   git_hash, timestamp, script, argv, constants
                 -> cau hoi VE QUA KHU: "file nay tu dau ra?"
    VALIDITY     aoi_source, d_sync, z_edges, sla_source, w_loss, omega
                 -> cau hoi VE TUONG LAI: "toi con duoc dung no khong?"

Repo nay co provenance rat day du (39 script) va van de loi d_sync = 51 ms
troi qua 5 phase, vi provenance ghi lai SU THAT LICH SU chu khong ghi
PHAM VI HIEU LUC.

NGUYEN TAC: nhan duoc SUY RA, khong duoc KHAI BAO.
Ban truyen vao DUNG doi tuong da dung de sinh z; ham nay bam ma nguon cua no
va tra registry ra nhan. Ban khong the ghi sai nhan ma khong dong thoi doi
ma nguon.

    # SAI -- mot loi khai, khong phai bang chung
    payload["validity"] = {"aoi_source": "measured_v7_renewal", "aoi_d_ms": 118.4}

    # DUNG -- suy ra tu thu da thuc su chay
    payload["validity"] = validity_block(aoi_generator=sawtooth_age_steps, ...)

Xem: docs/phase-23/00zx-amendment-44.md, docs/phase-23/axis_registry.json
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
from typing import Any, Callable, Sequence

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REGISTRY_PATH = os.path.join(_REPO, "docs", "phase-23", "axis_registry.json")

UNREGISTERED = "UNREGISTERED"
SCHEMA = "dt4n.validity.v1"


def _load_registry() -> dict:
    with open(_REGISTRY_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def aoi_axis(generator: Callable | object) -> dict[str, Any]:
    """Mo ta truc tuoi, SUY RA tu bo sinh THUC SU duoc dung.

    generator: ham hoac object da sinh ra z (vd ``sawtooth_age_steps``, hoac
               instance ``EmpiricalAoI`` sau Lesson 23.19).
    """
    module = inspect.getmodule(generator)
    if module is None:                       # bo sinh khong truy duoc ma nguon
        raise TypeError(
            "khong lay duoc module cua bo sinh z: %r. Truyen vao HAM hoac "
            "INSTANCE that su duoc dung, khong phai mot chuoi ten." % (generator,)
        )
    src_path = inspect.getsourcefile(module)
    sha = _sha256_file(src_path)

    entry = _load_registry().get("aoi_axis", {}).get(sha)
    label = entry["label"] if entry else UNREGISTERED

    try:
        gen_sha = hashlib.sha256(
            inspect.getsource(generator).encode("utf-8")
        ).hexdigest()
    except (OSError, TypeError):
        gen_sha = None

    return {
        "label": label,
        "generator_module": module.__name__,
        "generator_name": getattr(generator, "__name__", type(generator).__name__),
        "source_path": os.path.relpath(src_path, _REPO),
        "source_sha256": sha,
        # dau van tay hep hon: chi ma nguon cua chinh bo sinh. Thong tin them,
        # KHONG phai khoa tra registry -- de mot sua doi o bat ky dau trong
        # module van lam nhan thanh UNREGISTERED (fail loud, khong fail quiet).
        "generator_source_sha256": gen_sha,
        # tham so thuc te, doc tu module chu khong go tay
        "d_sync_s": getattr(module, "DEFAULT_D_SYNC_S", None),
        "sync_period_s": getattr(module, "DEFAULT_SYNC_PERIOD_S", None),
    }


def sla_axis(sla_path: str) -> dict[str, Any]:
    """Mo ta nguong SLA, suy ra tu file SLA thuc su duoc doc."""
    rel = os.path.relpath(os.path.abspath(sla_path), _REPO).replace(os.sep, "/")
    entry = _load_registry().get("sla_axis", {}).get(rel)
    return {
        "label": entry["label"] if entry else UNREGISTERED,
        "source_path": rel,
        "source_sha256": _sha256_file(sla_path),
    }


def validity_block(
    *,
    aoi_generator: Callable | object,
    z_edges: Sequence[float],
    sla_path: str,
    w_loss: float,
    omega: float | None = None,
) -> dict[str, Any]:
    """Khoi validity hoan chinh. Moi script ghi artifact goi ham NAY.

    omega=None nghia la "truc chua ton tai" (truoc Lesson 23.26), khac han voi
    omega=0.0 nghia la "da do va bang khong". Gop hai trang thai nay lam mot
    la cach mat dau mot truc thi nghiem.
    """
    return {
        "schema": SCHEMA,
        "aoi_axis": aoi_axis(aoi_generator),
        "sla_axis": sla_axis(sla_path),
        "z_edges": [float(x) for x in z_edges],
        "w_loss": float(w_loss),
        "omega": None if omega is None else float(omega),
    }

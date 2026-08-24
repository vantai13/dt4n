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

# Vai tro cua artifact doi voi TRUC tuoi. Hai vai tro nay khac nhau ve
# nguyen tac, khong phai ve muc do:
#   CONSUMES  artifact DUNG truc z de tinh ra ket qua. Truc sai -> ket qua
#             chi dung co dieu kien. Phai cho truc duoc DUYET moi vao LIVE.
#   MEASURES  artifact DO CHINH truc z (hoac chinh nhac cu do no). No khong
#             the bi lam sai boi cai ma no dang do. Vao LIVE duoc ngay.
# Day la ly do NGAM cua LEGACY_EXEMPT trong test_no_stale_axes.py; Lesson
# 23.18 lam no TUONG MINH (amendment 23-45a).
#   AXIS_FREE artifact KHONG dung truc AoI (luoi z CO DINH, tien nghiem) nhung
#             CO dung truc SLA. No khong phai cho `approved_for_live.aoi_axis`,
#             NHUNG PHAI cho `approved_for_live.sla_axis`.
#             Vi sao can vai tro rieng thay vi mot muc LEGACY_EXEMPT:
#             LEGACY_EXEMPT la MIEN TRU TOAN PHAN, trong khi ly do mien tru chi
#             dung cho MOT truc. Dung loi nay da cho
#             `decision_error_by_age_by_regime.parquet` song o LIVE/ voi truc
#             SLA DEPRECATED suot tu Lesson 23.17 den 23.21 (amendment 23-60).
ROLE_CONSUMES = "consumes_axis"
ROLE_MEASURES = "measures_axis"
ROLE_AXIS_FREE = "aoi_axis_free"


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
    axis_role: str = ROLE_CONSUMES,
) -> dict[str, Any]:
    """Khoi validity hoan chinh. Moi script ghi artifact goi ham NAY.

    axis_role=ROLE_MEASURES danh cho artifact DO chinh truc z (vd ket qua
    giai phau AoI cua Lesson 23.18). Chung khong bi truc lam sai nen khong
    phai cho `approved_for_live`.

    omega=None nghia la "truc chua ton tai" (truoc Lesson 23.26), khac han voi
    omega=0.0 nghia la "da do va bang khong". Gop hai trang thai nay lam mot
    la cach mat dau mot truc thi nghiem.
    """
    if axis_role not in (ROLE_CONSUMES, ROLE_MEASURES):
        raise ValueError("axis_role khong hop le: %r" % (axis_role,))
    return {
        "schema": SCHEMA,
        "axis_role": axis_role,
        "aoi_axis": aoi_axis(aoi_generator),
        "sla_axis": sla_axis(sla_path),
        "z_edges": [float(x) for x in z_edges],
        "w_loss": float(w_loss),
        "omega": None if omega is None else float(omega),
    }


def sla_axis_from_spec(
    *,
    t_delay_ms: float,
    t_loss: float,
    w_loss: float,
    manifest_path: str,
) -> dict[str, Any]:
    """Nhan truc SLA cho artifact TU DINH NGHIA spec (khong doc file manifest).

    KHONG dung duoc `sla_axis(path)` o day: cac quet `measurements/sla_exogenous.py`
    dinh nghia SLA NOI BO trong `SLA_SPECS` va khong bao gio doc manifest. Bam
    sha256 mot file ma script khong he mo ra la mot LOI KHAI, khong phai bang
    chung -- dung sai lech tinh than cua ca khoi `validity` (Luat 2).

    Thay vao do: DOI CHIEU NOI DUNG. Neu bo ba `(t_delay_ms, t_loss, w_loss)`
    TRUNG KHIT voi MOI cell cua manifest da dang ky, artifact dung tren CUNG
    MOT TRUC va duoc muon nhan cua manifest. Lech du mot phan nghin -> nhan
    UNREGISTERED -> khong vao duoc LIVE.

    Nho vay `S-A` (150 ms) va `S-C` (20 ms / 0.1%) TU DONG khong khop va o lai
    PENDING -- dung nhu ban chat cua chung: canh tay do nhay, khong phai truc
    chinh. (amendment 23-60)
    """
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    cells = manifest.get("cells", [])
    triples = {
        (
            round(float(c["t_delay_ms"]), 9),
            round(float(c["t_loss"]), 12),
            round(float(c["w_loss"]), 9),
        )
        for c in cells
    }
    want = (round(float(t_delay_ms), 9), round(float(t_loss), 12), round(float(w_loss), 9))
    matches = bool(cells) and triples == {want}

    rel = os.path.relpath(os.path.abspath(manifest_path), _REPO).replace(os.sep, "/")
    entry = _load_registry().get("sla_axis", {}).get(rel)
    return {
        "label": (entry["label"] if entry else UNREGISTERED) if matches else UNREGISTERED,
        "match_method": "content_triple",
        "spec_triple": {
            "t_delay_ms": float(t_delay_ms),
            "t_loss": float(t_loss),
            "w_loss": float(w_loss),
        },
        "manifest_path": rel,
        "manifest_sha256": _sha256_file(manifest_path),
        "manifest_triples": sorted(list(t) for t in triples),
        "matches_manifest": matches,
    }


def sla_only_validity_block(
    *,
    sla_path: str,
    w_loss: float,
    z_grid: Sequence[float],
    note: str,
) -> dict[str, Any]:
    """Khoi validity cho artifact KHONG dung truc AoI nhung CO dung truc SLA.

    Khac `validity_block`: khong co bo sinh z, vi artifact nay chay tren mot
    LUOI z CO DINH da tien dang ky. Luoi do duoc GHIM vao artifact, nen neu ai
    doi luoi thi nhan khong con khop.

    Khac `measurement_validity_block`: artifact nay KHONG do truc z, nen no
    KHONG duoc mien duyet truc SLA -- `sla_axis` van phai nam trong
    `approved_for_live`.

    z_grid rong ([]) nghia la artifact khong cham truc z o BAT KY dang nao
    (vd cac quet `sla_exogenous`, chay tren `ar1_matrix` chu khong sinh z).
    """
    return {
        "schema": SCHEMA,
        "axis_role": ROLE_AXIS_FREE,
        "aoi_axis": {
            "label": ROLE_AXIS_FREE,
            "note": "luoi z CO DINH, tien dang ky; khong goi bo sinh AoI nao",
            "z_grid_s": [float(z) for z in z_grid],
        },
        # SUY RA: bam sha256 file SLA that su duoc doc, khong go tay nhan.
        "sla_axis": sla_axis(sla_path),
        "w_loss": float(w_loss),
        "omega": None,
        "note": note,
    }


def measurement_validity_block(
    *,
    instrument_module: object,
    inputs: Sequence[str],
    note: str,
) -> dict[str, Any]:
    """Khoi validity cho artifact DO chinh truc z (vai tro MEASURES).

    Khac `validity_block`: khong co bo sinh z, vi artifact nay khong DUNG
    truc -- no DO ra truc. Van bam ma nguon cua NHAC CU do va sha256 cua moi
    file dau vao, nen van la nhan SUY chu khong phai nhan KHAI.
    """
    src_path = inspect.getsourcefile(instrument_module)
    return {
        "schema": SCHEMA,
        "axis_role": ROLE_MEASURES,
        "instrument": {
            "module": instrument_module.__name__,
            "source_path": os.path.relpath(src_path, _REPO),
            "source_sha256": _sha256_file(src_path),
        },
        "inputs_sha256": {
            os.path.relpath(p, _REPO): _sha256_file(p) for p in sorted(inputs)
        },
        "note": note,
    }

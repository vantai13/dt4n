"""Test cau truc code cho Lesson 23.7 -- buoc [3a].

Hai thu duoc thi hanh o day:

  1. DO THI IMPORT. Ba script hieu chuan la cac buoc CUNG CAP BAC, moi buoc mot
     artifact da commit. Neu chung import lan nhau, sua mot ham o script nay se
     am tham doi ket qua cua script kia -- trong khi artifact kia DA COMMIT.
     Chung chi duoc import XUONG `cert/cell_matrices.py`.

  2. APPROVAL SAU REFACTOR. Chay lai tung script va doi chieu TUNG CON SO voi
     artifact da commit. Test co xanh chua du: mot refactor co the giu test
     xanh ma van doi so, vi test kiem BAT BIEN chu khong kiem GIA TRI.
"""

from __future__ import annotations

import ast
import json
import os
import pathlib
from typing import Any, Dict, List

import pytest

CALIBRATION_SCRIPTS = (
    "lesson23_7_range_calibration",
    "lesson23_7_feasibility",
    "lesson23_7_calibration_2b",
)
BASE_MODULE = "cell_matrices"


def _imported_cert_modules(path: pathlib.Path) -> List[str]:
    """Ten cac module `cert.*` ma file nay import."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("cert"):
            parts = (node.module or "").split(".")
            if len(parts) >= 2:
                found.append(parts[1])
            else:  # `from cert import X`
                found.extend(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("cert."):
                    found.append(alias.name.split(".")[1])
    return found


@pytest.mark.parametrize("name", CALIBRATION_SCRIPTS)
def test_ba_script_hieu_chuan_khong_import_lan_nhau(name):
    """Chuoi import giua cac buoc cung cap bac la mot nguon lech am tham."""
    others = set(CALIBRATION_SCRIPTS) - {name}
    imported = set(_imported_cert_modules(pathlib.Path("cert/%s.py" % name)))
    assert not (imported & others), "%s import %s" % (name, sorted(imported & others))


@pytest.mark.parametrize("name", CALIBRATION_SCRIPTS)
def test_moi_script_hieu_chuan_import_module_nen(name):
    imported = _imported_cert_modules(pathlib.Path("cert/%s.py" % name))
    assert BASE_MODULE in imported


def test_module_nen_khong_import_nguoc_len():
    """`cell_matrices` la TANG DAY: khong duoc biet gi ve cac tang tren."""
    imported = set(_imported_cert_modules(pathlib.Path("cert/%s.py" % BASE_MODULE)))
    forbidden = set(CALIBRATION_SCRIPTS) | {"conditioning_audit"}
    assert not (imported & forbidden), sorted(imported & forbidden)


def test_module_nen_khong_import_vong():
    """Import `cell_matrices` mot minh phai chay duoc, khong keo theo tang tren."""
    import importlib
    import sys

    for name in CALIBRATION_SCRIPTS:
        sys.modules.pop("cert.%s" % name, None)
    sys.modules.pop("cert.cell_matrices", None)
    importlib.import_module("cert.cell_matrices")
    assert not any("cert.%s" % n in sys.modules for n in CALIBRATION_SCRIPTS)


def test_hai_buoc_sau_ghim_sha256_buoc_truoc():
    """Neu buoc truoc bi chay lai, buoc sau phai do ngay, khong lech am tham."""
    for name in ("lesson23_7_feasibility", "lesson23_7_calibration_2b"):
        path = "results/phase-23/%s.json" % name
        if not os.path.exists(path):
            pytest.skip("chua chay %s" % name)
        with open(path, "r", encoding="utf-8") as fh:
            prov = json.load(fh)["provenance"]
        pinned = prov.get("pins_previous_step")
        assert pinned is not None, name
        assert pinned["sha256"], name
        assert os.path.exists(pinned["path"]), pinned["path"]


# ---------------------------------------------------------------------------
# Approval sau refactor
# ---------------------------------------------------------------------------

def _strip_provenance(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _strip_provenance(v) for k, v in obj.items() if k != "provenance"}
    if isinstance(obj, list):
        return [_strip_provenance(v) for v in obj]
    return obj


def _diff(a: Any, b: Any, path: str = "") -> List[str]:
    out: List[str] = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append("%s/%s THEM" % (path, k))
            elif k not in b:
                out.append("%s/%s MAT" % (path, k))
            else:
                out += _diff(a[k], b[k], "%s/%s" % (path, k))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append("%s len %d -> %d" % (path, len(a), len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += _diff(x, y, "%s[%d]" % (path, i))
    elif a != b:
        out.append("%s: %r -> %r" % (path, a, b))
    return out


@pytest.mark.slow
@pytest.mark.parametrize("name", CALIBRATION_SCRIPTS)
def test_refactor_khong_doi_mot_con_so_nao(name, tmp_path):
    """Chay lai script va doi chieu tung con so voi artifact da commit."""
    import importlib

    artifact = "results/phase-23/%s.json" % name
    if not os.path.exists(artifact):
        pytest.skip("chua co artifact %s" % artifact)
    with open(artifact, "r", encoding="utf-8") as fh:
        committed = _strip_provenance(json.load(fh))

    mod = importlib.import_module("cert.%s" % name)
    fresh = json.loads(json.dumps(mod.json_clean(mod.build(str(tmp_path / "o.json")))
                                  if hasattr(mod, "json_clean")
                                  else mod._json_clean(mod.build(str(tmp_path / "o.json")))))
    delta = _diff(committed, _strip_provenance(fresh))
    assert not delta, "\n".join(delta[:20])

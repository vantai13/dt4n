"""Moi co CLI phai duoc doc o dau do trong cung module.  (L72)

Mot co duoc khai bao nhung khong bao gio duoc doc la mot co chet: lenh van
chay xanh, nhung nguoi dung co the tin nham rang thi nghiem da thay doi.
"""
from __future__ import annotations

import ast
import glob
import os
import re

import pytest


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES = sorted(
    glob.glob(os.path.join(REPO, "cert", "*.py"))
    + glob.glob(os.path.join(REPO, "measurements", "*.py"))
    + glob.glob(os.path.join(REPO, "tools", "*.py"))
)

# Known debt.  Entries may only be removed, never added without an amendment.
KNOWN_DEAD = {
    ("cert/abstain_cost.py", "calib_template"): "L72 -- sua o lesson so huu",
    ("measurements/decision_error_v2.py", "boot_metrics"): "L72 -- compatibility flag khong co semantics",
    ("measurements/l6_campaign.py", "resume"): "L72 -- resume la mac dinh, co khong duoc doc",
    ("measurements/l6_campaign_fine.py", "resume"): "L72 -- resume la mac dinh, co khong duoc doc",
    ("measurements/t5_campaign.py", "resume"): "L72 -- co khong duoc doc",
}

# Hai co nay duoc chuyen ca Namespace sang ham o module khac.  Chung khong
# phai dead; mapping nay buoc ca loi goi va noi doc ha nguon phai con ton tai.
FORWARDED = {
    ("measurements/calib_aoi_routing_auto.py", "controller_timeout"): (
        "start_controller",
        "measurements/calib_composition.py",
    ),
    ("measurements/calib_aoi_routing_auto.py", "ryu_manager"): (
        "start_controller",
        "measurements/calib_composition.py",
    ),
}


def _declared_flags(source: str) -> set[str]:
    """Return argparse destinations, including aliases with explicit dest=."""
    destinations: set[str] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument":
            continue
        options = [
            arg.value
            for arg in node.args
            if isinstance(arg, ast.Constant)
            and isinstance(arg.value, str)
            and arg.value.startswith("--")
        ]
        if not options:
            continue
        explicit_dest = next(
            (
                kw.value.value
                for kw in node.keywords
                if kw.arg == "dest"
                and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, str)
            ),
            None,
        )
        destinations.add(explicit_dest or options[0][2:].replace("-", "_"))
    return destinations


def _is_read(source: str, flag: str) -> bool:
    direct = r"\b(?:args|a|opts|ns)\.%s\b" % re.escape(flag)
    via_getattr = r"\bgetattr\(\s*(?:args|a|opts|ns)\s*,\s*['\"]%s['\"]" % re.escape(flag)
    return bool(re.search(direct, source) or re.search(via_getattr, source))


@pytest.mark.parametrize("path", MODULES)
def test_every_declared_flag_is_read_somewhere(path):
    rel = os.path.relpath(path, REPO).replace(os.sep, "/")
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    if "add_argument" not in source:
        pytest.skip("khong co CLI")

    dead = []
    for flag in sorted(_declared_flags(source)):
        if (rel, flag) in KNOWN_DEAD:
            continue
        if (rel, flag) in FORWARDED:
            continue
        if not _is_read(source, flag):
            dead.append(flag)
    assert not dead, (
        "%s: co CLI duoc khai bao nhung KHONG BAO GIO doc: %s\n"
        "  -> co chet; nguoi dung tuong da doi thi nghiem nhung thuc te khong doi."
        % (rel, dead)
    )


def test_known_dead_list_only_shrinks():
    """Moi muc debt phai tro toi mot co dang con ton tai."""
    for (rel, flag), reason in KNOWN_DEAD.items():
        path = os.path.join(REPO, rel)
        assert os.path.exists(path), "KNOWN_DEAD tro toi file khong con: %s" % rel
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        assert flag in _declared_flags(source), (
            "%s khong con khai bao --%s -> xoa debt da duoc sua" % (rel, flag)
        )
        assert reason.strip(), "moi muc KNOWN_DEAD phai co ly do"


def test_forwarded_flags_reach_the_named_downstream_function():
    for (rel, flag), (function_name, downstream_rel) in FORWARDED.items():
        with open(os.path.join(REPO, rel), encoding="utf-8") as handle:
            caller = handle.read()
        with open(os.path.join(REPO, downstream_rel), encoding="utf-8") as handle:
            downstream = handle.read()
        assert re.search(r"\b%s\(\s*(?:args|a|opts|ns)\s*\)" % function_name, caller)
        assert _is_read(downstream, flag), (
            "%s khong con doc %s duoc forward tu %s" % (downstream_rel, flag, rel)
        )


def test_detector_has_a_positive_control():
    """DC33: detector phai bat dung mot co da khai bao nhung khong doc."""
    source = 'parser.add_argument("--calib-template")\nargs.run\n'
    declared = _declared_flags(source)
    read = {flag for flag in declared if _is_read(source, flag)}
    assert declared - read == {"calib_template"}

#!/usr/bin/env python3
"""Phase T guardrail: new dynamic-load modules must not use link_model v1."""

import ast
import pathlib


BANNED_NAMES = {"OVERHEAD_FACTOR", "NETEM_OCCUPANCY_COEF", "OFFERED_CLIFF"}
PHASE_T_FILES = (
    "mininet/rho_spec.py",
    "measurements/rho_gen.py",
    "measurements/t5_qs_error.py",
)


def test_phase_t_khong_dung_link_model_v1():
    for rel in PHASE_T_FILES:
        path = pathlib.Path(rel)
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module != "twin.link_model", (
                    "%s: import twin.link_model v1; Phase T phai dung "
                    "twin.link_model_v2" % rel
                )
                for alias in node.names:
                    assert alias.name not in BANNED_NAMES, (
                        "%s: import %s tu model v1" % (rel, alias.name)
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "twin.link_model", (
                        "%s: import twin.link_model v1" % rel
                    )

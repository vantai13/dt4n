"""20R2.9-C/lop 6: test affinity phai canh do dai tap CPU cua may.

Lop 4 do khi phep kiem gan runner co 4 CPU vao gia dinh 8 CPU. Ban va do chi
doi hang so van vo tren may 1 CPU. Canh gac nay buoc moi test doc affinity
truc tiep phai noi ro cach xu ly khi tap CPU nho hon chi so am no su dung.
"""
from __future__ import annotations

import ast
import pathlib


REPO = pathlib.Path(__file__).resolve().parents[1]


def _negative_index(node: ast.Subscript) -> int | None:
    value = node.slice
    if (isinstance(value, ast.UnaryOp)
            and isinstance(value.op, ast.USub)
            and isinstance(value.operand, ast.Constant)
            and isinstance(value.operand.value, int)):
        return value.operand.value
    return None


def test_no_test_indexes_sched_getaffinity_without_a_length_guard() -> None:
    bad: list[str] = []
    for path in sorted((REPO / "test").glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "sched_getaffinity" not in source:
            continue
        tree = ast.parse(source, filename=str(path))
        for function in (n for n in ast.walk(tree)
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))):
            affinity_names = {
                target.id
                for assign in ast.walk(function)
                if isinstance(assign, ast.Assign)
                and any(
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "sched_getaffinity"
                    for call in ast.walk(assign.value)
                )
                for target in assign.targets
                if isinstance(target, ast.Name)
            }
            if not affinity_names:
                continue
            indexes = [
                (node.value.id, _negative_index(node), node.lineno)
                for node in ast.walk(function)
                if isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id in affinity_names
                and _negative_index(node) is not None
                and _negative_index(node) >= 2
            ]
            for name, needed, lineno in indexes:
                guarded = any(
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "len"
                    and len(node.args) == 1
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id == name
                    and node.lineno < lineno
                    for node in ast.walk(function)
                )
                if not guarded:
                    bad.append(f"{path.name}:{lineno} ({name}[-{needed}])")
    assert not bad, (
        "doc affinity ma danh chi so am khong co canh do dai: %r; "
        "so CPU la thuoc tinh cua may, khong phai hang so cua phep kiem" % bad
    )

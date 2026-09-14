# test/test_no_import_time_global_mutation.py
"""20R2.9-A5 -- import mot module KHONG duoc doi trang thai cua module khac."""
import ast, pathlib
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

def _module_level_attr_writes(path: pathlib.Path):
    """Tim `some_module.ATTR = ...` o MUC TOP-LEVEL (chay luc import)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:                        # CHI top-level
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name):
                yield node.lineno, "%s.%s" % (t.value.id, t.attr)

@pytest.mark.parametrize("path", sorted((REPO / "tools").glob("*.py")),
                         ids=lambda p: p.name)
def test_no_tool_mutates_another_module_at_import_time(path):
    bad = ["  line %d: %s" % (ln, tgt) for ln, tgt in _module_level_attr_writes(path)]
    assert not bad, (
        "%s: doi thuoc tinh cua module KHAC ngay luc IMPORT.\n%s\n"
        "  -> thu tu thu thap cua pytest se quyet dinh ket qua. Dung context "
        "manager hoac truyen tham so." % (path.name, "\n".join(bad)))

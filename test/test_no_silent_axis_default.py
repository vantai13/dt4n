# test/test_no_silent_axis_default.py
"""20R2.9-A4 -- mot TRUC khong duoc phep la mot MAC DINH.

Lich su: cung mot co che da bi bat NAM lan (`DEFAULT_TAU`, `axis=AXIS_LEGACY`,
`sigma=V3.SIGMA`, `--z-grid`, `--calibration`). Lan thu nam gay hau qua that:
`tools/20r2_2_se_pilot.py::_measure` goi `run_fixed_grid(...)` khong truyen
`calibration_path`, nen bang chap nhan duoc do tren truc SLA SAI (prereg §16.3).

20R2.5-P2 chi sua HAI cho (`main()` va `run_fixed_grid`) va KHAI DUNG pham vi do.
Test nay dem NHUNG CHO CON LAI, bang AST -- khong bang grep, vi grep bo sot
tham so chi-tu-khoa va tham so doi ten.
"""
from __future__ import annotations
import ast, pathlib
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

# Hang so CHON MOT TRUC. Lam mac dinh = chon ho nguoi dung, im lang.
BANNED_AS_DEFAULT = {"CALIBRATION", "AXIS_LEGACY", "DEFAULT_TAU", "SIGMA"}

# Hang so KHONG chon truc, duoc phep lam mac dinh -- nhung phai co LY DO o day.
ALLOWED_WITH_REASON = {
    "TRUTH_TABLE": ("bang tra su that la DUY NHAT trong repo; khong co lua chon "
                    "thu hai nen no khong phai mot truc."),
    "RHO_SOURCE": ("mac dinh 'calibration_ar1' la bo sinh DA KY; lua chon con lai "
                   "('scalar_ou') la CHAN DOAN. Mac dinh tro toi ban DA KY."),
}
SCAN = ["measurements", "cert", "twin"]

def _defaults(path: pathlib.Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        a = node.args
        positional = a.posonlyargs + a.args
        pairs = list(zip(positional[len(positional) - len(a.defaults):], a.defaults))
        pairs += [(x, d) for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None]
        for arg, dflt in pairs:
            if isinstance(dflt, ast.Name):
                yield node.lineno, node.name, arg.arg, dflt.id

def _all_py():
    out = []
    for d in SCAN:
        out += sorted((REPO / d).rglob("*.py"))
    return [p for p in out if "__pycache__" not in str(p)]

@pytest.mark.parametrize("path", _all_py(), ids=lambda p: str(p.relative_to(REPO)))
def test_no_function_defaults_to_an_axis_constant(path: pathlib.Path):
    bad = ["  line %4d  %s(%s = %s)" % (ln, fn, arg, const)
           for ln, fn, arg, const in _defaults(path)
           if const in BANNED_AS_DEFAULT]
    assert not bad, (
        "%s: MAC DINH IM LANG chon truc thay nguoi dung.\n%s\n"
        "  -> doi thanh sentinel MUST_CHOOSE va RAISE khi khong duoc truyen."
        % (path.relative_to(REPO), "\n".join(bad)))

def test_no_function_defaults_to_an_artifact_PATH():
    """Rong hon BANNED_AS_DEFAULT: BAT KY hang so tro toi mot tep trong
    `results/` deu la mot lua chon THI NGHIEM, khong phai mot tien nghi.
    Bat theo GIA TRI (chuoi chua 'results/'), khong theo TEN -- vi ten co the
    doi ma rui ro thi khong."""
    bad = []
    for path in _all_py():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        consts = {n.targets[0].id: n.value.value
                  for n in tree.body
                  if isinstance(n, ast.Assign) and len(n.targets) == 1
                  and isinstance(n.targets[0], ast.Name)
                  and isinstance(n.value, ast.Constant)
                  and isinstance(n.value.value, str)}
        for ln, fn, arg, const in _defaults(path):
            val = consts.get(const)
            if val and "results/" in val and const not in ALLOWED_WITH_REASON:
                bad.append("  %s:%d  %s(%s = %s -> %s)"
                           % (path.relative_to(REPO), ln, fn, arg, const, val))
    assert not bad, (
        "MAC DINH tro thang toi mot ARTIFACT trong results/:\n%s\n"
        "  -> nguoi goi tuong minh dang chon, thuc te ham chon ho." % "\n".join(bad))

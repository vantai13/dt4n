"""Cong cu 20R2 phai CHAY DUOC va TAI LAP DUOC, khong chi artifact phai dung.

VI SAO CAN BO TEST NAY -- lo hong no bit:

Bo test hien co kiem SAN PHAM (artifact) chu khong kiem DAY CHUYEN (tool).
Mot tool co the hong hoan toan ma moi test van xanh, mien la artifact cu con
nam tren dia. Do duoc 2026-09-10:

    $ python -m tools.20r2_0_axis_audit --out results/PENDING/phase-20R2/axis_audit.json
    TypeError: %d format: a real number is required, not NoneType
    $ echo $?
    1                       <- MA LOI, tren dung lenh trong docstring cua tool

Ba he qua, khong phai mot:

 1. ARTIFACT DUNG, TOOL DO. JSON duoc ghi TRUOC khi crash (24219 byte, so
    dung, n_grid_cells = 800). Trang thai la: tep ton tai VA lenh that bai.
    Day la to hop te nhat -- `set -e` chan buoc sau, ma tren dia lai co mot
    artifact trong nhu hoan chinh.
 2. SO QUAN TRONG NHAT KHONG BAO GIO IN RA. Dong crash chinh la dong in ngan
    sach A7 -- con so 800 o / 29.4 phut ma ca phase dua vao.
 3. KHONG TEST NAO DO, suot 3 commit. Do chinh la loai loi mot bo test
    kiem-san-pham KHONG THE thay.

Bo test nay la CHAN cho 20R2.3: golden chi co nghia neu tool sinh ra no con
chay duoc. Trong san xuat, phan biet nay goi la process validation (kiem day
chuyen) vs product inspection (kiem san pham). Kiem san pham bat duoc lo hang
hong; kiem day chuyen bat duoc LY DO lo sau se hong.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "results/PENDING/phase-20R2"

# module -> ten artifact da commit ma no phai tai lap
TOOLS = {
    "tools.20r2_0_axis_audit": "axis_audit",
    "tools.20r2_4_realizability_audit": "realizability_audit",
    "tools.20r2_1_canary_span": "canary_span",
    "tools.20r2_1_parquet_recovery": "parquet_recovery",
}

# Truong doi theo THOI DIEM chay, khong theo NOI DUNG. Loai truoc khi so.
VOLATILE = ("generated_utc", "generated_at")


def _run(module: str, out: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", module, "--out", str(out)],
        cwd=str(ROOT), capture_output=True, text=True,
    )


@pytest.mark.parametrize("module,artifact", sorted(TOOLS.items()))
def test_tool_exits_zero_on_its_own_documented_command(module, artifact, tmp_path):
    """DAY CHUYEN: lenh trong docstring cua tool phai thoat ma 0.

    Khong kiem noi dung o day -- chi kiem tool CHAY XONG. Tach rieng khoi
    phep kiem tai lap ben duoi de khi do, thong bao noi dung cai gi hong.
    """
    r = _run(module, tmp_path / (artifact + ".json"))
    assert r.returncode == 0, (
        module + " thoat ma " + str(r.returncode)
        + " tren lenh docstring cua chinh no:\n" + r.stderr[-1500:]
    )


@pytest.mark.parametrize("module,artifact", sorted(TOOLS.items()))
def test_tool_reproduces_the_committed_artifact(module, artifact, tmp_path):
    """TAI LAP: chay lai phai ra DUNG thu da commit.

    Neu test nay do ma test thoat-ma-0 o tren xanh, thi tool con chay nhung
    da DOI DAU RA -- artifact da commit khong con la san pham cua tool nua.
    """
    committed = COMMITTED / (artifact + ".json")
    if not committed.is_file():
        pytest.skip("chua co artifact da commit: " + artifact)
    out = tmp_path / (artifact + ".json")
    r = _run(module, out)
    if r.returncode != 0:
        pytest.skip("tool khong chay duoc -- xem test thoat-ma-0")
    a = json.loads(committed.read_text(encoding="utf-8"))
    b = json.loads(out.read_text(encoding="utf-8"))
    for k in VOLATILE:
        a.pop(k, None)
        b.pop(k, None)
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    assert not diff, (
        module + ": khong tai lap duoc artifact da commit.\n"
        "  khoa lech: " + str(diff) + "\n"
        "  -> hoac tool doi hanh vi, hoac artifact da commit bi sua tay.\n"
        "  -> golden cua 20R2.3 chi co nghia neu phep nay xanh."
    )


def test_the_a7_budget_line_is_actually_printed():
    """Canary cho DUNG lop loi da xay ra: so in ra phai la so DA GIAI.

    Loi goc in `args.n_cells` (dau vao, co the None) thay vi gia tri da giai
    tu bang kha thi. Test nay khong kiem "khong crash" -- no kiem con so
    800 THAT SU den duoc man hinh. Mot bai in im lang cung la mot bai in sai.
    """
    r = _run("tools.20r2_0_axis_audit",
             pathlib.Path(__import__("tempfile").mkdtemp()) / "a.json")
    assert r.returncode == 0, r.stderr[-800:]
    assert "A7: ngan sach CPU (800 o)" in r.stdout, (
        "dong ngan sach A7 khong in ra so o da giai.\n" + r.stdout[-800:]
    )

"""Host-capability gating for the dt4n test suite.

Vi sao ton tai: mot so doi chung chi CHAY DUOC tren mot may co du kha nang vat
ly -- vi du thang emitter cua G3 can **>= 8 CPU duoc phep** de tach emitter /
sampler / sink ra cac loi rieng (`tools/g3_emitter_dryrun.py`). Runner cua
GitHub Actions co 4 CPU, nen nhung test do do THEO CAU TAO o CI, va CI do
thuong truc thi khong ai doc nua.

Cach xu ly o day KHONG phai bo chon chung di mot cach vo dieu kien. Marker
`hostcap` khai **kha nang can co**; hook duoi day chi bo qua khi may THUC SU
khong dap ung, kem mot ly do co so. Tren may tac gia (8 CPU) chung van chay
binh thuong -- do phu khong mat o noi co the do duoc.

Moi test mang `hostcap` phai co mot dong trong
`docs/phase-20R2/C-validation/ci-coverage-debt.json`; test canh o
`test/test_20r2_9_c_chain.py` doi hai tap bang nhau theo ca hai chieu.
"""
from __future__ import annotations

import os

import pytest


def _allowed_cpus() -> int:
    try:
        return len(os.sched_getaffinity(0))
    except AttributeError:  # khong phai Linux
        return os.cpu_count() or 1


def pytest_runtest_setup(item: pytest.Item) -> None:
    mark = item.get_closest_marker("hostcap")
    if mark is None:
        return
    needed = mark.kwargs.get("cpus")
    if needed is None:
        raise pytest.UsageError(
            "mark `hostcap` phai khai kha nang can co, vi du hostcap(cpus=8)")
    available = _allowed_cpus()
    if available < needed:
        pytest.skip(
            "hostcap: can >= %d CPU duoc phep, may nay cho %d "
            "(xem docs/phase-20R2/C-validation/ci-coverage-debt.json)"
            % (needed, available))

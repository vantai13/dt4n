"""20R2.9-C: portable CI, tracked ledgers, and explained nullable fields."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
B3 = ROOT / "docs/phase-20R2/B3-axis-marginal.json"


def test_ci_checkout_fetches_history_and_tags() -> None:
    text = (ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
    assert "fetch-depth: 0" in text
    assert "fetch-tags: true" in text


def test_t2_run_ledger_is_part_of_a_clean_clone() -> None:
    path = "results/PENDING/phase-T2/sweep/run_log.jsonl"
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", path], cwd=ROOT,
        check=True, capture_output=True, text=True,
    )


def _unexplained_nulls(value, pointer=""):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = pointer + "/" + key
            if child is None:
                reason = value.get(key + "_undefined_reason")
                if not isinstance(reason, str) or not reason.strip():
                    found.append(child_pointer)
            found.extend(_unexplained_nulls(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_unexplained_nulls(child, pointer + "/" + str(index)))
    return found


def test_every_b3_null_has_a_local_reason() -> None:
    assert not _unexplained_nulls(json.loads(B3.read_text(encoding="utf-8")))


def test_t2_round1_parquet_goldens_are_in_git() -> None:
    """C-3: sweep/run_log.jsonl mot minh khong du -- hygiene() doc CA 166 parquet.

    `sweep_r2` (luot 2) da duoc bao ton tu 60a88784; luot 1 bi bo sot, nen phep
    tai sinh hygiene dung o FileNotFoundError tren MOI clone sach.
    """
    listed = subprocess.run(
        ["git", "ls-files", "results/PENDING/phase-T2/sweep/"], cwd=ROOT,
        check=True, capture_output=True, text=True,
    ).stdout.split()
    parquets = [p for p in listed if p.endswith(".parquet")]
    assert len(parquets) == 166, len(parquets)

    log = (ROOT / "results/PENDING/phase-T2/sweep/run_log.jsonl").read_text(
        encoding="utf-8").splitlines()
    wanted = {json.loads(line)["out"] for line in log}
    assert wanted <= set(parquets)


CUSTODY_DEBT = ROOT / "docs/phase-20R2/C-validation/custody-debt.json"


def test_every_custody_mark_has_a_named_missing_input() -> None:
    """G23-222 theo chieu nguoc lai: mark `custody` la DO PHU BI MAT o CI.

    Gate 8-5 chi chap nhan "CI xanh HOAC moi that bai con lai co ten va ly do".
    Mot mark custody bien mot that bai thanh mot skip; neu khong co so no thi
    do dung la mot den xanh rong. Test nay doi moi test custody phai co mot
    dong trong so, kem TEP THIEU va PHAN DO PHU BI MAT.
    """
    collected = subprocess.run(
        [sys.executable, "-m", "pytest", "test/", "-m", "custody",
         "-q", "--collect-only", "--no-header", "-p", "no:cacheprovider"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout
    marked = {line.strip() for line in collected.splitlines() if "::" in line}
    debt = json.loads(CUSTODY_DEBT.read_text(encoding="utf-8"))
    ledgered = {e["test"] for e in debt["entries"]}

    assert marked, "khong thu gom duoc test custody nao -- phep kiem se rong"
    assert marked <= ledgered, sorted(marked - ledgered)
    assert ledgered <= marked, sorted(ledgered - marked)
    for entry in debt["entries"]:
        assert entry["missing_input"].strip()
        assert entry["reason"].strip()
        assert entry["coverage_lost"].strip()


GATE_SOURCES = ROOT / "docs/phase-20R2/99c-gate-definition-sources.json"
GATE_LEDGER = ROOT / "docs/phase-20R2/99b-gate-ledger.md"


def _gate_sources() -> dict:
    return json.loads(GATE_SOURCES.read_text(encoding="utf-8"))


def test_every_scored_gate_declares_where_its_definition_lives() -> None:
    """C-1 (phan lam duoc): so cham 8 dong, so nguon phai co dung 8 muc."""
    rows = [line for line in GATE_LEDGER.read_text(encoding="utf-8").splitlines()
            if line.startswith("| 20R2-")]
    scored = {line.split("|")[1].strip() for line in rows}
    declared = {g["gate"] for g in _gate_sources()["gates"]}
    assert scored == declared, (sorted(scored - declared), sorted(declared - scored))


def test_in_repo_gate_definitions_quote_a_line_that_really_says_it() -> None:
    """Mot khai IN_REPO chi co nghia khi TRICH DUOC dung tai file:dong do."""
    checked = 0
    for gate in _gate_sources()["gates"]:
        if gate["status"] == "EXTERNAL_MISSING":
            continue
        lines = (ROOT / gate["path"]).read_text(encoding="utf-8").splitlines()
        assert gate["quote"] in lines[gate["line"] - 1], (gate["gate"], gate["line"])
        checked += 1
    assert checked == 6, checked


def test_a_missing_specification_cannot_arrive_unnoticed() -> None:
    """Khi byte goc xuat hien, so nguon PHAI duoc nang cap -- test nay bat buoc dieu do.

    Day la co che chong "dac ta roi im lang": ngay nao PHASE_20R2.md hoac
    MASTER_PLAN_v10.md duoc them vao kho hoac vao lich su, test do va buoc
    nguoi sua chuyen muc tuong ung tu EXTERNAL_MISSING sang IN_REPO kem sha256.
    """
    for doc in _gate_sources()["missing_documents"]:
        name = doc["name"]
        tracked = subprocess.run(
            ["git", "ls-files", "*" + name], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.split()
        assert not tracked, (name, tracked, "nang cap 99c-gate-definition-sources.json")
        in_history = subprocess.run(
            ["git", "log", "--all", "--format=%H", "--diff-filter=A", "--", "**/" + name],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout.split()
        assert not in_history, (name, in_history)

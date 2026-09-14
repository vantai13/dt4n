# test/test_20r2_9_h8_can_go_red.py
"""20R2.9-A2 -- MUTATION TEST cho H8. Mot phep kiem chua tung DO thi chua duoc
chung minh la co the do.

Lich su: gate 20R2-4 muc 4-2 doi `not_evaluated == []` cho MOI o. H8 -- noi duy
nhat chay realizability tren so DO DUOC cua chien dich -- chi doc `verdict`, va
`verdict` KHONG nhin `not_evaluated`. Nen 4-2 chua bao gio duoc assert. Do duoc
tren 320 o: not_evaluated rong tren CA 320 -- tuc gate dung, nhung dung DO MAY.
"""
from __future__ import annotations
import math
import pytest
from cert.realizability_gate import realizability_gate

CELL = dict(mode="poisson", rho_bar=0.925, tau=3.0, dt=0.005, n=200_000)
FULL = dict(sigma=0.0218, clip_fraction=0.001, min_cell_blocks=100)

def _h8_old(r) -> bool:  return r["verdict"] == "REALIZABLE"          # ban CU
def _h8_new(r) -> bool:  return r["verdict_strict"] == "REALIZABLE"   # ban MOI

def test_gate_keeps_the_signed_narrow_meaning_of_verdict():
    """Hop dong CU khong doi: `verdict` van la 'khong tieu chi nao TRUOT'."""
    thin = realizability_gate(**CELL)
    assert thin["verdict"] == "REALIZABLE"
    assert thin["not_evaluated"], "o mong phai co tieu chi khong chay"

def test_new_fields_answer_the_question_verdict_never_asked():
    thin, full = realizability_gate(**CELL), realizability_gate(**CELL, **FULL)
    assert thin["complete"] is False and thin["verdict_strict"] == "INCOMPLETE"
    assert full["complete"] is True  and full["verdict_strict"] == "REALIZABLE"

def test_MUTATION_dropping_sigma_turns_h8_red_on_the_new_reader():
    """★ DOT BIEN: bo `sigma=` -- H8 CU van xanh, H8 MOI PHAI do."""
    thin, full = realizability_gate(**CELL), realizability_gate(**CELL, **FULL)
    assert _h8_old(thin) is True,  "doi chung: ban CU khong bat duoc -- do la loi cu"
    assert _h8_new(thin) is False, "★ ban MOI PHAI bat duoc; neu khong, 4-2 van rong"
    assert _h8_new(full) is True,  "ban MOI khong duoc bat nham o day du tham so"

def test_MUTATION_dropping_only_clip_fraction_is_also_caught():
    """Bo MOT tham so thoi cung phai bat duoc, khong chi khi bo ca ba."""
    partial = dict(FULL); partial.pop("clip_fraction")
    r = realizability_gate(**CELL, **partial)
    assert r["not_evaluated"] == ["censoring_ok"]
    assert _h8_old(r) is True and _h8_new(r) is False

@pytest.mark.parametrize("bad", [
    dict(sigma=99.0,   clip_fraction=0.001, min_cell_blocks=100),  # vuot tran
    dict(sigma=0.0218, clip_fraction=0.99,  min_cell_blocks=100),  # kep qua nhieu
    dict(sigma=0.0218, clip_fraction=0.001, min_cell_blocks=1),    # thieu block
])
def test_a_real_failure_is_still_REJECTED_not_INCOMPLETE(bad):
    """Ba gia tri phai PHAN BIET duoc 'truot' voi 'khong biet'."""
    r = realizability_gate(**CELL, **bad)
    assert r["verdict_strict"] == "REJECTED", r["failed"]
    assert r["complete"] is True, "du tham so thi phai complete, du co truot"

def test_campaign_pass2_is_actually_complete_not_merely_unfailed():
    """Do lai tren THAM SO THAT cua chien dich: 4-2 co that su thoa khong."""
    import json, pathlib, pandas as pd
    from measurements import decision_error_v2 as DE
    root = pathlib.Path(__file__).resolve().parents[1]
    log = root / "docs/phase-20R2/04-campaign-log.jsonl"
    if not log.is_file():
        pytest.skip("chua co so cai chien dich")
    runs = [json.loads(x) for x in log.read_text().splitlines() if x.strip()]
    runs = [e for e in runs if e.get("kind") == "run"
            and not e.get("is_canary") and e.get("returncode") == 0]
    if not runs:
        pytest.skip("so cai rong")
    frames = []
    for e in runs:
        p = root / e["out"]
        if not p.is_file():
            pytest.skip("thieu parquet chien dich: %s" % e["out"])
        frames.append(pd.read_parquet(p))
    d = pd.concat(frames, ignore_index=True)
    import importlib
    h8 = importlib.import_module("tools.20r2_5_hygiene")
    # Preserve branch: the signed H8 checks 320 groups, not 160 pooled groups.
    for frame, entry in zip(frames, runs):
        frame["branch"] = entry["branch"]
    result = h8.realizability_pass2(pd.concat(frames, ignore_index=True))
    assert result["n_cells"] == 320
    assert result["rejected"] == []


@pytest.mark.parametrize("omitted", ["sigma", "clip_fraction", "min_cell_blocks"])
def test_production_h8_rejects_an_incomplete_gate_call(omitted):
    import importlib
    import pandas as pd
    h8 = importlib.import_module("tools.20r2_5_hygiene")
    frame = pd.DataFrame([dict(branch="main", mode="poisson", rho_bar=.925,
        tau_rho=3., sigma_rho=.0218, n=200000, ar1_clip_ratio=.001)])
    assert not h8.realizability_pass2(frame)["rejected"]
    def mutation(**kw):
        kw.pop(omitted)
        return realizability_gate(**kw)
    rejected = h8.realizability_pass2(frame, gate=mutation)["rejected"]
    assert len(rejected) == 1
    assert rejected[0]["verdict"] == "REALIZABLE"
    assert rejected[0]["verdict_strict"] == "INCOMPLETE"
    assert rejected[0]["not_evaluated"]

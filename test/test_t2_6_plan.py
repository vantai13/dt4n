"""T2.6 luot 1 -- ke hoach chay phai THUAN CO CHE.

Bo test nay chan CHINH SACH RO VAO CO CHE. Mot nguong lot vao luot 1
nghia la ban khong the doi nguong ma khong chay lai thi nghiem -- va do
la ly do khien mot amendment ve nguong tro nen dat den muc khong ai lam.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from tools.t2_6_plan import (
    A_VALS,
    BRANCHES,
    CANARY,
    CANARY_EVERY,
    ORDER_SEED,
    SEEDS,
    TAUS,
    baseline_table,
    build,
    command_for,
    is_live,
    plan,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "docs/phase-T2/03-run-plan.json"
FORBIDDEN = ("verdict", "pass", "fail", "readable", "lift_min",
             "k_sigma", "band", "eps_err", "eps_a")


@pytest.fixture(scope="module")
def doc():
    return json.loads(ARTIFACT.read_text())


# --- CO CHE khong duoc mang CHINH SACH ---------------------------------

def test_plan_contains_no_verdict_or_threshold_anywhere(doc):
    """Khong mot khoa nao trong ke hoach duoc mang ten mot phan quyet."""
    blob = json.dumps(doc).lower()
    for word in ("\"verdict\"", "\"pass\"", "\"fail\"", "\"lift_min\"",
                 "\"k_sigma\"", "\"recommended_band\""):
        assert word not in blob, word


def test_no_run_entry_carries_a_threshold(doc):
    for r in doc["runs"]:
        assert set(r) == {"tau", "branch", "a", "seed", "run_index", "is_canary"}


def test_generated_command_carries_no_threshold(doc):
    for r in doc["runs"][:20]:
        cmd = " ".join(command_for(r, "/tmp/x"))
        for w in FORBIDDEN:
            assert w not in cmd, (w, cmd)
        assert "--tau" in cmd and "--z-mode" in cmd


# --- vi tu loai o chay tren SO, khong tren TEN -------------------------

def test_is_live_has_no_default_epsilons():
    """QD-7 chua ky: khong duoc co mac dinh im lang cho eps."""
    with pytest.raises(TypeError):
        is_live({"err_baseline": 0.5, "A": 10.0})


def test_exclusion_runs_on_numbers_not_on_names():
    """Hai o CUNG rho_bar phai cho hai phan quyet KHAC nhau.

    Day la phep thu chan dung loi "loai rho_bar=0.96 moi mode": no vut bo
    poisson@0.960 (err = 0.231, khoe) chi vi h2@0.960 suy bien.
    """
    base = baseline_table()
    eps = dict(eps_err=0.01, eps_a=0.01)
    assert not is_live(base["h2@0.960"], **eps)
    assert is_live(base["poisson@0.960"], **eps)
    assert base["h2@0.960"]["rho_bar"] == base["poisson@0.960"]["rho_bar"]


def test_exclusion_catches_the_dead_family_too():
    base = baseline_table()
    eps = dict(eps_err=0.01, eps_a=0.01)
    assert not is_live(base["cbr@0.700"], **eps)
    assert all(is_live(base[c], **eps)
               for c in ("h2@0.700", "h2@0.850", "poisson@0.850", "poisson@0.925"))


def test_changing_epsilon_changes_the_verdict():
    """Vi tu phai thuc su doc eps, khong phai hard-code tra hinh."""
    base = baseline_table()
    assert is_live(base["h2@0.960"], eps_err=0.001, eps_a=0.01)
    assert not is_live(base["h2@0.960"], eps_err=0.01, eps_a=0.01)


# --- o suy bien VAN phai duoc chay (doi chung am V2) -------------------

def test_degenerate_cells_are_not_filtered_out_of_the_run(doc):
    """V2 doi DO o suy bien roi xac nhan suy bien.

    Loc chung khoi ke hoach se lam V2 khong the thuc hien. Va vi mot lenh
    dang nao cung tinh moi o (do duoc: 90 hang = 10 o x 9 z), loc chung
    KHONG tiet kiem gi.
    """
    assert "h2@0.960" in doc["baseline_table"]
    assert "cbr@0.700" in doc["baseline_table"]
    # ke hoach khong co truc "cell": moi lenh tinh tat ca cac o
    assert all("cell" not in r and "mode" not in r for r in doc["runs"])


# --- thu tu, diem canh, dem lenh ---------------------------------------

def test_plan_is_deterministic_given_the_order_seed():
    assert plan() == plan()
    assert ORDER_SEED == 7200


def test_run_count_matches_the_measured_execution_unit(doc):
    """Don vi chay la (tau,branch,a,seed): 8x2x2x5 = 160 lenh.

    Do duoc: mot lenh sinh 90 hang = 10 o x 9 muc z. Lap ke hoach theo
    tung O se dem sai (1120) va uoc sai ngan sach.

    So 160 duoc VIET RA thay vi chi tin vao tich cac len(): mot hang so
    doc lap bat duoc truong hop ai do lang le them mot muc vao mot truc.
    """
    assert doc["n_runs"] == len(TAUS) * len(BRANCHES) * len(A_VALS) * len(SEEDS)
    assert doc["n_runs"] == 160


def test_order_is_actually_randomised(doc):
    real = [r for r in doc["runs"] if not r["is_canary"]]
    taus = [r["tau"] for r in real]
    assert taus != sorted(taus), "thu tu chua duoc xao -- drift se trung truc tau"


def test_canary_seed_lies_outside_the_design(doc):
    """Canary phai la mot diem NGOAI thiet ke, khong phai mot o cua no."""
    assert CANARY["seed"] not in SEEDS
    canaries = [r for r in doc["runs"] if r["is_canary"]]
    assert canaries and all(r["seed"] == CANARY["seed"] for r in canaries)
    assert all(r["tau"] == CANARY["tau"] and r["branch"] == CANARY["branch"]
               for r in canaries), "diem canh phai KHONG DOI"


def test_canary_cadence(doc):
    idx = [i for i, r in enumerate(doc["runs"]) if r["is_canary"]]
    assert idx[0] == 0
    assert all(b - a == CANARY_EVERY + 1 for a, b in zip(idx, idx[1:]))


def test_inputs_still_match_recorded_hashes(doc):
    for rel, want in doc["provenance"]["inputs"].items():
        f = ROOT / rel
        assert f.is_file(), rel
        assert hashlib.sha256(f.read_bytes()).hexdigest() == want, rel


def test_artifact_is_valid_json_without_nan():
    raw = ARTIFACT.read_text()
    assert "NaN" not in raw and "Infinity" not in raw
    json.loads(raw, parse_constant=lambda s: pytest.fail("ngoai JSON: %s" % s))

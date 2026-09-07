"""T2.6-pre -- cua so bang kha thi: [k*se, |effect|).

Bo test nay chan hai loi doi xung nhau, ca hai deu lam gate mat nghia:
  - bang HEP hon nhieu   => gate la tung xu
  - bang RONG hon hieu ung => du doan khong the sai
Khi cua so rong, o do la INSUFFICIENT_POWER va KHONG duoc doc theo ca hai
chieu (NT 56).
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib

import pytest

from tools.t2_band_window import (
    BAND_FLOOR,
    DEGENERATE_ERR,
    EFFECT_BRANCH_B,
    K_SIGMA,
    SRC,
    build,
    windows,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "docs/phase-T2/02-band-window.json"


@pytest.fixture(scope="module")
def doc():
    return json.loads(ARTIFACT.read_text())


def test_inputs_still_match_recorded_hashes(doc):
    for rel, want in doc["provenance"]["inputs"].items():
        f = ROOT / rel
        assert f.is_file(), rel
        assert hashlib.sha256(f.read_bytes()).hexdigest() == want, rel


def test_rebuild_is_deterministic(doc):
    again = build()
    assert again["windows"] == doc["windows"]


def test_every_readable_band_clears_the_noise_floor(doc):
    """San: b >= k*se. Duoi do gate la tung xu."""
    for cell, w in doc["windows"].items():
        if w["verdict"] != "READABLE":
            continue
        assert w["recommended_band"] >= w["band_floor_from_noise"] - 1e-12, cell
        assert w["recommended_band"] >= BAND_FLOOR - 1e-12, cell


def test_every_readable_band_stays_under_the_effect_size(doc):
    """Tran: b < |effect|. Rong hon thi du doan khong the sai."""
    for cell, w in doc["windows"].items():
        if w["verdict"] != "READABLE":
            continue
        assert w["recommended_band"] < EFFECT_BRANCH_B, cell


def test_empty_window_is_flagged_insufficient_power_not_given_a_band(doc):
    """h2@0.960: k*se = 1.12 > |effect| = 0.80 => cua so RONG."""
    w = doc["windows"]["h2@0.960"]
    assert w["window_empty"] is True
    assert w["verdict"] == "INSUFFICIENT_POWER"
    assert w["recommended_band"] is None, "o rong khong duoc cap bang"


def test_artifact_is_valid_json_without_nan():
    """JSON chuan KHONG co NaN. Mot artifact ma parser chat che khong doc
    duoc la mot artifact hong, du Python tu doc lai duoc."""
    raw = ARTIFACT.read_text()
    assert "NaN" not in raw and "Infinity" not in raw
    json.loads(raw, parse_constant=lambda s: pytest.fail("hang so ngoai JSON: %s" % s))


def test_degenerate_and_healthy_cells_at_the_same_rho_bar():
    """Quy tac loai phai la mot TIEU CHI DO DUOC, khong phai mot danh sach o.

    rho_bar = 0.96 KHONG dong nhat: h2@0.960 suy bien (err = 0.0017) nhung
    poisson@0.960 khoe (err = 0.231). Loai ca hai theo rho_bar se vut bo mot
    o song. Do la ly do quy tac phai chay tren SO, khong tren ten o.
    """
    doc = build()
    h2 = doc["windows"]["h2@0.960"]
    po = doc["windows"]["poisson@0.960"]
    assert h2["err_baseline"] < DEGENERATE_ERR
    assert po["err_baseline"] > 10 * DEGENERATE_ERR
    assert h2["verdict"] != "READABLE"
    assert po["verdict"] == "READABLE"


def test_the_originally_proposed_flat_band_would_have_been_too_narrow(doc):
    """Doi chung: mot bang +/-0.03 dung chung cho moi o hep hon nhieu.

    Day la ly do bang phai TINH THEO O, va la cung loai loi voi gate
    |tau_hat - tau|/tau < 15%: nguong dat ma khong nhin do tan.
    """
    flat = 0.03
    too_narrow = [c for c, w in doc["windows"].items()
                  if w["verdict"] == "READABLE" and flat < w["band_floor_from_noise"]]
    assert len(too_narrow) >= 4, too_narrow


def test_k_sigma_scales_the_floor(doc):
    """Doi k phai doi san. Mot san khong phu thuoc k la san gia."""
    w3 = build(k=3.0)["windows"]
    w2 = build(k=2.0)["windows"]
    for c in w3:
        a, b = w3[c]["band_floor_from_noise"], w2[c]["band_floor_from_noise"]
        if a is not None and b is not None:
            assert a == pytest.approx(1.5 * b, rel=1e-9), c


def test_dispersion_uses_between_seed_variation_with_stated_dof(doc):
    """se phai tu bien thien GIUA SEED, va dof phai duoc ghi ra.

    sd uoc tu n=3 => dof=2: bat dinh cua chinh sd rat lon. Ghi ra de nguoi
    doc biet bang nay con phai do lai.
    """
    for cell, v in doc["dispersion"].items():
        assert v["n_seed_observed"] >= 2, cell
        assert v["dof"] == v["n_seed_observed"] - 1
        assert v["se_observed"] == pytest.approx(
            v["sd_between_seed"] / math.sqrt(v["n_seed_observed"]), rel=1e-9)
    assert "dof=2" in doc["provenance"]["caveat"]

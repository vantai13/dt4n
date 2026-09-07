"""Gate P-3b phai doc CHIEU TANG, khong phai chieu giam."""
import numpy as np
import pytest

from tools import g5c_monotone as M
from tools import g5b_power_axis as g5b

# Day thuc do cua G'.5b, doc 73 section 2
G5B_ACCEPTANCE = [0.53977, 0.50899, 0.48303, 0.45946, 0.43800]


def test_seed_rebinding_took_effect():
    assert M.SEED_C == 20260909
    assert g5b.SEED == M.SEED_C, "import g5c phai rebind seed cua g5b"


def test_p3b_passes_the_vector_that_void_p3_failed():
    """Cung mot day: gate cu FAIL, gate moi PASS. Do la toan bo van de."""
    s = M.monotone_stats(G5B_ACCEPTANCE)
    assert s["worst_decrease"] == pytest.approx(-0.03078, abs=1e-5)
    assert s["worst_increase"] == pytest.approx(-0.02146, abs=1e-5)
    assert not (s["worst_decrease"] >= -0.005)              # P-3 cu: FAIL
    assert s["worst_increase"] <= M.STEP_UP_TOLERANCE       # P-3b moi: PASS


def test_p3b_fires_on_a_genuine_increase():
    """Neu day THAT SU di len, gate phai bat duoc. Khong duoc la gate cho."""
    s = M.monotone_stats([0.50, 0.49, 0.51, 0.50, 0.49])
    assert s["worst_increase"] == pytest.approx(0.02, abs=1e-12)
    assert s["worst_increase"] > M.STEP_UP_TOLERANCE        # FAIL, dung nhu the


def test_p3b_tolerates_noise_inside_the_error_budget():
    """Mot buoc len +0.004 (< 3.5 SE) khong duoc lam hong gate."""
    s = M.monotone_stats([0.50, 0.48, 0.484, 0.46, 0.44])
    assert s["worst_increase"] == pytest.approx(0.004, abs=1e-12)
    assert s["worst_increase"] <= M.STEP_UP_TOLERANCE


def _blocks(*, amp=0.10, snr=7.4, cov=0.001, null_amp=0.0, remainder=0.0053):
    primary = {"maxscore": {"amplitude": amp, "snr": snr,
                            "coverage_amplitude": cov,
                            "irreducible_remainder": remainder,
                            "acceptance_by_omega": G5B_ACCEPTANCE}}
    return primary, {"maxscore": {"amplitude": null_amp}}


def test_verdict_holds_and_classifies_reducible():
    primary, null = _blocks()
    mono = M.monotone_stats(primary["maxscore"]["acceptance_by_omega"])
    d = M.adjudicate(primary, null, mono, {"distinct": True})
    assert d["verdict"] == "POWER_AXIS_HOLDS"
    assert d["classification"] == "REDUCIBLE_TO_EFFECTIVE_SIGMA"


def test_large_remainder_classifies_irreducible():
    primary, null = _blocks(remainder=0.09)
    mono = M.monotone_stats(primary["maxscore"]["acceptance_by_omega"])
    d = M.adjudicate(primary, null, mono, {"distinct": True})
    assert d["classification"] == "IRREDUCIBLE"


def test_nc0_invalidates_a_repeat_of_g5b():
    primary, null = _blocks()
    mono = M.monotone_stats(primary["maxscore"]["acceptance_by_omega"])
    d = M.adjudicate(primary, null, mono, {"distinct": False})
    assert d["verdict"] == "INVALID_SEED_NOT_INDEPENDENT"


def test_nc_failure_outranks_p_gates():
    """NC hong thi khong duoc phep ket luan gi ve P."""
    primary, null = _blocks(cov=0.02)          # NC-1 FAIL
    mono = M.monotone_stats(primary["maxscore"]["acceptance_by_omega"])
    d = M.adjudicate(primary, null, mono, {"distinct": True})
    assert d["verdict"] == "STOP_GENERATOR"
    assert d["classification"] is None


@pytest.mark.parametrize('values', [[], [0.5], [0.5, float('nan')], [[0.5, 0.4]]])
def test_invalid_monotonicity_input_is_rejected(values):
    with pytest.raises(ValueError):
        M.monotone_stats(values)


def test_nc0_reads_actual_baseline_and_detects_duplicate(tmp_path, monkeypatch):
    import json
    primary, _ = _blocks()
    path = tmp_path / 'baseline.json'
    path.write_text(json.dumps({'results': {'primary': primary}}))
    monkeypatch.setattr(M, 'G5B_ARTIFACT', path)
    assert M.seed_independence(primary)['distinct'] is False
    changed, _ = _blocks()
    changed['maxscore']['acceptance_by_omega'] = [0.54, 0.51, 0.48, 0.46, 0.44]
    assert M.seed_independence(changed)['distinct'] is True
    path.unlink()
    assert M.seed_independence(primary)['checked'] is False


@pytest.mark.parametrize('kwargs, verdict', [
    ({'amp': 0.01}, 'POWER_TOO_WEAK'),
    ({'snr': 4.0}, 'ADOPT_WEAK'),
    ({'null_amp': 0.02}, 'STOP_GENERATOR'),
])
def test_remaining_decision_branches(kwargs, verdict):
    primary, null = _blocks(**kwargs)
    mono = M.monotone_stats(G5B_ACCEPTANCE)
    result = M.adjudicate(primary, null, mono, {'distinct': True})
    assert result['verdict'] == verdict
    assert result['classification'] is None


def test_upward_step_causes_weak_verdict():
    primary, null = _blocks()
    mono = M.monotone_stats([0.5, 0.49, 0.51, 0.50, 0.49])
    assert M.adjudicate(primary, null, mono, {'distinct': True})['verdict'] == 'ADOPT_WEAK'

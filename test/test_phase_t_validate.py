"""Phase T / T.4 -- tests for validation gates and synthetic oracles."""

import bisect
import math

import pytest

from measurements.t4_validate import (
    V_T5_MODES,
    classify_err_qs,
    decompose,
    gate_rho_bias_aggregate,
    gate_row,
    oracle_frozen,
    oracle_quasistatic,
    rho_bias_sd,
)
from mininet.load_spec import FRAME_BG, FRAME_PROBE, PROBE_PPS, capacity_bytes_per_s
from mininet.rho_schedule import build_varying_schedule
from mininet.rho_spec import RhoTrajectory, ou_trajectory, sigma_from_a
from twin.link_model_v2 import LinkModelV2


MODEL = LinkModelV2.load("results/phase-L/link_model_v2_fit.json")
BW, Q, DUR, DT = 6.0, 13, 90.0, 0.005
NSTEP = int(round(DUR / DT))
T5_DUR, T5_WARM, T5_WINDOW = 105.0, 15.0, 0.100


def _traj(rho_bar=0.85, a=0.90, tau=1.0, seed=11):
    return ou_trajectory(rho_bar, sigma_from_a(rho_bar, a), tau, NSTEP, seed, dt=DT)


@pytest.mark.parametrize("mode", ("h2", "poisson"))
@pytest.mark.parametrize("a", (0.20, 0.90))
def test_oracle1_quasistatic_err_qs_bang_khong_trong_san_lay_mau(mode, a):
    tr = _traj(a=a)
    sched = build_varying_schedule(mode, tr, BW, 11)
    q = oracle_quasistatic(MODEL, mode, BW, Q, tr, sched.send_times)
    d = decompose(MODEL, mode, BW, Q, tr, q)

    assert abs(d["err_qs_ms"]) < 3.0 * d["se_err_qs_ms"]


@pytest.mark.parametrize("mode", ("h2", "poisson"))
@pytest.mark.parametrize("a", (0.20, 0.90))
def test_oracle2_he_tri_tre_cho_tong_ba_thanh_phan_bang_khong(mode, a):
    tr = _traj(a=a)
    sched = build_varying_schedule(mode, tr, BW, 11)
    q = oracle_frozen(MODEL, mode, BW, Q, tr, sched.send_times)
    d = decompose(MODEL, mode, BW, Q, tr, q)
    total = d["err_qs_ms"] + d["err_jensen_ms"] + d["d_sampling_ms"]

    assert total == pytest.approx(0.0, abs=1e-12)
    assert d["err_total_ms"] == pytest.approx(total, abs=1e-12)


def test_decompose_dung_quy_dao_thiet_ke_duoc_truyen_vao():
    tr_a = _traj(rho_bar=0.85, a=0.90)
    tr_b = _traj(rho_bar=0.90, a=0.90)
    a = decompose(MODEL, "h2", BW, Q, tr_a, 11.0)
    b = decompose(MODEL, "h2", BW, Q, tr_b, 11.0)

    assert abs(a["q_psa_load_ms"] - b["q_psa_load_ms"]) > 0.5


def test_classify_err_qs_co_hang_khong_phan_biet_duoc():
    assert (
        classify_err_qs(0.05, 0.01, 0.03)
        == "khong_phan_biet_duoc_o_phan_giai_nay"
    )
    assert classify_err_qs(0.005, 0.10, 0.001) == "bo_qua_duoc"
    assert classify_err_qs(0.050, 0.10, 0.001) == "cong_vao_band_21R"
    assert classify_err_qs(0.200, 0.10, 0.001) == "quasi_static_khong_dung"


def test_gate_row_bat_loi_van_hanh_va_giu_cac_cong_dung():
    tr = _traj()
    sched = build_varying_schedule("h2", tr, BW, 11)
    row = {
        "mode": "h2",
        "bw": BW,
        "rho_bar": 0.85,
        "duration_s": 105.0,
        "warmup_s": 15.0,
        "meas_s": 90.0,
        "trajectory_digest": tr.digest(),
        "rho_bias": 0.0,
        "socket_drops": 0,
        "n_foreign": 0,
        "n_late_ratio": 0.0,
    }
    good = gate_row(row, tr, sched, MODEL, MODEL.sigma("h2", BW, Q, 0.85))
    assert all(good.values())
    assert row["rho_bias_sd_pred"] > 0.003
    assert row["rho_bias_z"] == pytest.approx(0.0)

    bad = {
        **row,
        "trajectory_digest": "wrong",
        "rho_bias": 0.020,
        "socket_drops": 1,
        "n_foreign": 2,
        "n_late_ratio": 0.01,
    }
    out = gate_row(bad, tr, sched, MODEL, MODEL.sigma("h2", BW, Q, 0.85))
    assert out["V-T0_digest_khop"] is False
    assert out["V-T6b_rho_bias"] is False
    assert out["A5-7_socket_drops"] is False
    assert out["A5-7_n_foreign"] is False
    assert out["A5-7_n_late"] is False


def test_v_t5_phai_chay_tren_h2_hoac_poisson_khong_duoc_chi_cbr():
    assert "h2" in V_T5_MODES or "poisson" in V_T5_MODES
    assert V_T5_MODES != ("cbr",)


def _constant_rescale_rho_bias(mode: str, rho_bar: float, seed: int) -> float:
    traj = RhoTrajectory(
        [float(rho_bar)] * int(round(T5_DUR / DT)),
        DT,
        0,
        "ou",
        {"rho_bar": float(rho_bar)},
    )
    sched = build_varying_schedule(mode, traj, BW, seed)
    n_bins = int((T5_DUR - T5_WARM) // T5_WINDOW)
    meas_s = n_bins * T5_WINDOW
    lo, hi = T5_WARM, T5_WARM + meas_s
    n_bg = bisect.bisect_left(sched.send_times, hi) - bisect.bisect_left(
        sched.send_times, lo
    )
    rho_hat = (
        (n_bg / meas_s) * FRAME_BG + PROBE_PPS * FRAME_PROBE
    ) / capacity_bytes_per_s(BW)
    return rho_hat - float(rho_bar)


def _pop_sd(xs):
    mean = sum(xs) / len(xs)
    return math.sqrt(sum((x - mean) ** 2 for x in xs) / len(xs))


def test_rho_bias_sd_khop_mo_phong_200_seed_va_giam_fail_gia():
    cases = (("h2", 0.85), ("poisson", 0.85), ("cbr", 0.98))
    for mode, rho_bar in cases:
        vals = [
            _constant_rescale_rho_bias(mode, rho_bar, seed)
            for seed in range(1000, 1200)
        ]
        sd_pred = rho_bias_sd(mode, rho_bar, BW, T5_WARM, T5_DUR - T5_WARM)
        false_fail_new = sum(abs(v) > 3.0 * sd_pred for v in vals) / len(vals)
        assert false_fail_new < 0.01

        if mode != "cbr":
            assert _pop_sd(vals) == pytest.approx(sd_pred, rel=0.15)
            assert sum(abs(v) > 0.002 for v in vals) / len(vals) > 0.15

    cbr_gate = 3.0 * rho_bias_sd("cbr", 0.98, BW, T5_WARM, T5_DUR - T5_WARM)
    h2_gate = 3.0 * rho_bias_sd("h2", 0.85, BW, T5_WARM, T5_DUR - T5_WARM)
    assert cbr_gate < 0.002
    assert cbr_gate < h2_gate / 50.0


def test_gate_rho_bias_aggregate_bat_drift_nho():
    centered = [{"rho_bias_z": z} for z in (-1.0, -0.5, 0.0, 0.5, 1.0)]
    good = gate_rho_bias_aggregate(centered)
    assert good["pass_mean"] is True
    assert good["pass_sd"] is True

    drifted = [{"rho_bias_z": 0.5} for _ in range(240)]
    bad = gate_rho_bias_aggregate(drifted)
    assert bad["pass_mean"] is False
    assert bad["pass_sd"] is False

"""Phase T / T.4 -- tests for validation gates and synthetic oracles."""

import bisect
import math

import pytest

from measurements.t4_validate import (
    V_T5_MODES,
    ca_operational_se,
    ca_operational_threshold,
    classify_err_qs,
    decompose,
    gate_aggregate_z,
    gate_rho_bias_aggregate,
    gate_row,
    gate_vt5a_delegation,
    gate_vt5b_q_matches_phase_l,
    gate_vt5b_same_seed_aggregate,
    phase_l_seed_refs,
    oracle_frozen,
    oracle_quasistatic,
    phase_l_q_refs,
    rho_bias_sd,
)
from mininet.load_spec import (
    FRAME_BG,
    FRAME_PROBE,
    PROBE_PPS,
    background_pps,
    build_schedule,
    capacity_bytes_per_s,
    schedule_digest,
)
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
        "max_late_ms": 0.0,
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
        "max_late_ms": 100.0,
    }
    out = gate_row(bad, tr, sched, MODEL, MODEL.sigma("h2", BW, Q, 0.85))
    assert out["V-T0_digest_khop"] is False
    assert out["V-T6b_rho_bias"] is False
    assert out["A5-7_socket_drops"] is False
    assert out["A5-7_n_foreign"] is False
    assert out["A5-7_n_late"] is False
    assert out["A5-7_max_late"] is False


def test_v_t5_phai_chay_tren_h2_hoac_poisson_khong_duoc_chi_cbr():
    assert "h2" in V_T5_MODES or "poisson" in V_T5_MODES
    assert V_T5_MODES != ("cbr",)


def test_vt5a_delegation_khop_phase_l_const_schedule():
    rho_bar = 0.85
    tr = ou_trajectory(rho_bar, 0.0, 1.0, int(round(T5_DUR / DT)), 11, dt=DT)
    pps = background_pps(rho_bar, BW, PROBE_PPS)
    n_bg = max(1, int(pps * T5_DUR))
    row = {
        "mode": "h2",
        "rho_bar": rho_bar,
        "bw": BW,
        "duration_s": T5_DUR,
        "seed": 11,
        "schedule_digest": schedule_digest(build_schedule("h2", n_bg, 1.0 / pps, 11)),
    }

    assert gate_vt5a_delegation(row, tr) is True
    assert gate_vt5a_delegation({**row, "schedule_digest": "wrong"}, tr) is False
    assert gate_vt5a_delegation({**row, "mode": "cbr"}, tr) is None


def test_vt5b_105s_chi_tra_z_cho_cong_tap_hop():
    refs = {("h2", 0.85): {"mean_ms": 10.0, "sd_ms": 0.5, "n": 5.0}}
    good = gate_vt5b_q_matches_phase_l(
        {"mode": "h2", "rho_bar": 0.85, "q_mean_ms": 10.1},
        refs,
    )

    assert good == {"z": pytest.approx(0.2), "ref_n": 5.0}
    assert set(good) == {"z", "ref_n"}


def test_phase_l_q_refs_loc_dung_bw_q_probe_va_tinh_sd_mau():
    rows = [
        {"mode": "h2", "rho": 0.85, "bw": BW, "q": Q, "probe_pps": 20.0, "q_mean_ms": 10.0},
        {"mode": "h2", "rho": 0.85, "bw": BW, "q": Q, "probe_pps": 20.0, "q_mean_ms": 11.0},
        {"mode": "h2", "rho": 0.85, "bw": 8.0, "q": Q, "probe_pps": 20.0, "q_mean_ms": 99.0},
        {"mode": "h2", "rho": 0.85, "bw": BW, "q": Q, "probe_pps": 0.0, "q_mean_ms": 99.0},
    ]
    refs = phase_l_q_refs(rows, BW, Q, PROBE_PPS)

    assert refs[("h2", 0.85)]["mean_ms"] == pytest.approx(10.5)
    assert refs[("h2", 0.85)]["sd_ms"] == pytest.approx(2 ** 0.5 / 2)
    assert refs[("h2", 0.85)]["n"] == 2.0


def test_phase_l_seed_refs_giu_q_va_digest_theo_cung_seed():
    rows = [
        {
            "mode": "h2",
            "rho": 0.85,
            "bw": BW,
            "q": Q,
            "probe_pps": 20.0,
            "seed": 11,
            "q_mean_ms": 10.0,
            "schedule_digest": "abc",
        }
    ]
    refs = phase_l_seed_refs(rows, BW, Q, PROBE_PPS)

    assert refs[("h2", 0.85, 11)] == {"q_mean_ms": 10.0, "schedule_digest": "abc"}


def test_vt5b_same_seed_aggregate_loai_cbr_toi_han_khoi_cong():
    rows = [
        {"vt5b_same_seed_rel": 0.001, "vt5b_same_seed_gate_exempt": False},
        {"vt5b_same_seed_rel": -0.002, "vt5b_same_seed_gate_exempt": False},
        {"vt5b_same_seed_rel": 0.40, "vt5b_same_seed_gate_exempt": True},
    ]
    out = gate_vt5b_same_seed_aggregate(rows)

    assert out["n"] == 2
    assert out["mean_rel"] == pytest.approx(-0.0005)
    assert out["pass"] is True


def test_ca_operational_threshold_theo_noise_model_va_siet_cbr():
    n_gaps = 44123
    h2_se = ca_operational_se("h2", n_gaps)
    poisson_se = ca_operational_se("poisson", n_gaps)

    assert h2_se == pytest.approx(0.0214, rel=0.10)
    assert poisson_se == pytest.approx(0.00475, rel=0.15)
    assert ca_operational_threshold("h2", n_gaps) > 0.08
    assert ca_operational_threshold("poisson", n_gaps) < 0.021
    assert ca_operational_threshold("cbr", n_gaps) == pytest.approx(0.005)


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


def test_gate_aggregate_z_dung_n_eff_theo_nhom_seed():
    rows = []
    for seed, base in enumerate((0.70, 0.80, 0.85, 0.90, 0.85), 11):
        for j in range(4):
            rows.append({"seed": seed, "ca_operational_z": base + 0.01 * j})

    out = gate_aggregate_z(rows, "ca_operational_z", group_by="seed")

    assert out["n"] == 20
    assert out["n_eff"] == 5
    assert out["pass_mean"] is True

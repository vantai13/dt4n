"""Phase T / T.3 -- contract tests for two-scale schedule coupling."""

import pytest

from mininet.load_spec import (
    DESIGN_CA,
    background_pps,
    build_schedule,
    schedule_digest,
)
from mininet.rho_schedule import (
    build_varying_schedule,
    ca_pooled_predicted,
    ca_thinning_predicted,
    cumulative_intensity,
    intensity,
    invert_cumulative,
)
from mininet.rho_spec import ou_trajectory, sigma_from_a


BW, DUR, DT = 6.0, 90.0, 0.005
NSTEP = int(round(DUR / DT))
MODES = ("cbr", "poisson", "h2")
A_LEVELS = (0.20, 0.90)
TAUS = (0.2, 1.0, 5.0)


def _traj(rho_bar=0.85, a=0.90, tau=1.0, seed=11):
    return ou_trajectory(rho_bar, sigma_from_a(rho_bar, a), tau, NSTEP, seed, dt=DT)


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("rho", (0.70, 0.85, 0.90))
def test_vt5_duong_hang_so_trung_khit_phase_l_bit_exact(mode, rho):
    tr = ou_trajectory(rho, 0.0, 1.0, NSTEP, 11, dt=DT)
    s = build_varying_schedule(mode, tr, BW, 11)
    pps = background_pps(rho, BW)
    n_bg = max(1, int(pps * DUR))

    assert s.path == "phase_l_const"
    assert s.digest() == schedule_digest(build_schedule(mode, n_bg, 1.0 / pps, 11))


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("a", A_LEVELS)
@pytest.mark.parametrize("tau", TAUS)
def test_vt4a_ca_van_hanh_bang_thiet_ke(mode, a, tau):
    s = build_varying_schedule(mode, _traj(a=a, tau=tau), BW, 11)
    assert abs(s.ca_operational() - DESIGN_CA[mode]) < 0.02


def test_vt4a_ca_van_hanh_khong_nhuc_nhich_khi_quet_hai_truc():
    for mode in MODES:
        vals = [
            build_varying_schedule(mode, _traj(a=a, tau=tau), BW, 11).ca_operational()
            for a in A_LEVELS
            for tau in TAUS
        ]
        assert max(vals) - min(vals) < 0.01


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("a", A_LEVELS)
def test_vt4b_ca_gop_khop_cong_thuc_lam_phat(mode, a):
    tr = _traj(a=a)
    s = build_varying_schedule(mode, tr, BW, 11)
    pred = ca_pooled_predicted(intensity(tr, BW), DESIGN_CA[mode])
    if pred > 0.005:
        assert s.ca_pooled() == pytest.approx(pred, rel=0.05)


def test_ca_gop_tang_khi_sigma_tang_va_do_la_dung():
    lo = build_varying_schedule("cbr", _traj(a=0.20), BW, 11).ca_pooled()
    hi = build_varying_schedule("cbr", _traj(a=0.90), BW, 11).ca_pooled()
    assert hi > 3.0 * lo


def test_thinning_pha_ca_con_rescaling_thi_khong():
    p = 0.81
    assert ca_thinning_predicted(0.0, p) > 0.4
    assert ca_thinning_predicted(1.0, p) == pytest.approx(1.0, abs=1e-12)
    assert 0.05 < 1.0 - ca_thinning_predicted(2.0, p) / 2.0 < 0.10


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("a", A_LEVELS)
def test_vt6a_rate_ratio_dat_cong_a5_7(mode, a):
    s = build_varying_schedule(mode, _traj(a=a), BW, 11)
    assert abs(s.rate_ratio() - 1.0) < 0.001


@pytest.mark.parametrize("mode", MODES)
def test_vt6a_mean_gap_van_hanh_bang_mot(mode):
    s = build_varying_schedule(mode, _traj(), BW, 11)
    u = s.operational_times()
    gaps_u = [b - a for a, b in zip(u, u[1:])]
    assert sum(gaps_u) / len(gaps_u) == pytest.approx(1.0, rel=0.005)


def test_nghich_dao_lambda_la_nghich_dao_that():
    tr = _traj()
    cum = cumulative_intensity(intensity(tr, BW), tr.dt)
    for frac in (0.001, 0.13, 0.5, 0.77, 0.999):
        u = frac * cum[-1]
        t = invert_cumulative(cum, tr.dt, u)
        k = min(int(t / tr.dt), len(cum) - 2)
        back = cum[k] + (t / tr.dt - k) * (cum[k + 1] - cum[k])
        assert back == pytest.approx(u, rel=1e-9)


def test_khong_co_goi_nao_trung_thoi_diem():
    for mode in MODES:
        s = build_varying_schedule(mode, _traj(), BW, 11)
        assert min(s.bg_gaps[1:]) > 0.0


@pytest.mark.parametrize("mode", MODES)
def test_thoi_diem_gui_tang_nghiem_ngat_va_trong_cua_so(mode):
    s = build_varying_schedule(mode, _traj(), BW, 11)
    assert all(b > a for a, b in zip(s.send_times, s.send_times[1:]))
    assert 0.0 < s.send_times[0]
    assert s.send_times[-1] <= DUR + 1e-9


def test_cung_seed_cung_schedule_digest():
    a = build_varying_schedule("h2", _traj(seed=11), BW, 11)
    b = build_varying_schedule("h2", _traj(seed=11), BW, 11)
    assert a.digest() == b.digest()


def test_quy_dao_khac_thi_schedule_khac():
    a = build_varying_schedule("h2", _traj(seed=11), BW, 11)
    b = build_varying_schedule("h2", _traj(seed=12), BW, 11)
    assert a.digest() != b.digest()


def test_rho_qua_thap_so_voi_probe_thi_bao_loi():
    tr = ou_trajectory(0.50, 0.0, 1.0, 100, 1, dt=DT)
    with pytest.raises(ValueError):
        intensity(tr, 0.02)

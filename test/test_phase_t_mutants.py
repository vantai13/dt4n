"""Phase T / T.4 -- mutation tests for gates and analysis oracles.

Mutants live only in this test file. They intentionally implement bad variants
so the gate suite proves it can turn red for meaningful mistakes.
"""

import bisect
import random

import pytest

from measurements.t4_validate import decompose, oracle_frozen, oracle_quasistatic
from mininet.load_spec import DESIGN_CA, background_pps, build_schedule, schedule_digest
from mininet.rho_schedule import (
    VaryingSchedule,
    build_varying_schedule,
    ca_pooled_predicted,
    cumulative_intensity,
    intensity,
)
from mininet.rho_spec import ou_trajectory, sigma_from_a
from twin.link_model_v2 import LinkModelV2


MODEL = LinkModelV2.load("results/LIVE/phase-L/link_model_v2_fit.json")
BW, Q, DUR, DT = 6.0, 13, 90.0, 0.005
NSTEP = int(round(DUR / DT))


def _traj(rho_bar=0.85, a=0.90, tau=1.0, seed=11):
    return ou_trajectory(rho_bar, sigma_from_a(rho_bar, a), tau, NSTEP, seed, dt=DT)


def _gaps_from_times(times):
    return [b - a for a, b in zip([0.0] + list(times), times)]


def _round_inverse_schedule(mode):
    tr = _traj()
    lam = intensity(tr, BW)
    cum = cumulative_intensity(lam, tr.dt)
    total = cum[-1]
    g_op = build_schedule(mode, int(total), 1.0, 11)
    times = []
    u = 0.0
    for gap in g_op:
        u += gap
        if u > total:
            break
        k = bisect.bisect_right(cum, u) - 1
        times.append(max(0, min(k, tr.n_steps - 1)) * tr.dt)
    return tr, VaryingSchedule(
        times,
        _gaps_from_times(times),
        cum,
        tr.dt,
        mode,
        "mutant_round_inverse",
        {"total_operational": total},
    )


def _thinning_schedule(mode):
    tr = _traj()
    lam = intensity(tr, BW)
    cum = cumulative_intensity(lam, tr.dt)
    lam_max = max(lam)
    rng = random.Random(11)
    gaps = build_schedule(mode, int(lam_max * tr.duration_s), 1.0 / lam_max, 11)
    times = []
    t = 0.0
    for gap in gaps:
        t += gap
        if t > tr.duration_s:
            break
        k = min(int(t / tr.dt), tr.n_steps - 1)
        if rng.random() < lam[k] / lam_max:
            times.append(t)
    return tr, VaryingSchedule(
        times,
        _gaps_from_times(times),
        cum,
        tr.dt,
        mode,
        "mutant_thinning",
        {"total_operational": cum[-1]},
    )


def _normalize_after_schedule(mode):
    tr = _traj()
    good = build_varying_schedule(mode, tr, BW, 11)
    k = tr.duration_s / sum(good.bg_gaps)
    gaps = [g * k for g in good.bg_gaps]
    t = 0.0
    times = []
    for gap in gaps:
        t += gap
        times.append(t)
    return k, tr, VaryingSchedule(
        times,
        gaps,
        good.cum,
        good.dt,
        mode,
        "mutant_normalize_after",
        dict(good.design),
    )


def _reimpl_const_digest(mode, rho):
    tr = ou_trajectory(rho, 0.0, 1.0, NSTEP, 11, dt=DT)
    pps = background_pps(rho, BW)
    n_bg = max(1, int(pps * tr.duration_s))
    unit_gaps = build_schedule(mode, n_bg, 1.0, 11)
    return schedule_digest([g / pps for g in unit_gaps])


def _decompose_without_lambda_weight(model, mode, bw, q, traj, q_pkt_mean_ms):
    fs = [model.predict_delay(mode, bw, q, rho) for rho in traj.rho]
    q_psa_load = sum(fs) / len(fs)
    q_ssa = model.predict_delay(mode, bw, q, sum(traj.rho) / len(traj.rho))
    return {
        "q_psa_load_ms": q_psa_load,
        "err_qs_ms": q_pkt_mean_ms - q_psa_load,
        "err_jensen_ms": q_psa_load - q_ssa,
        "d_sampling_ms": 0.0,
        "err_total_ms": q_pkt_mean_ms - q_ssa,
    }


def test_mutant_round_inverse_bi_vt4a_va_gap_positive_bat():
    tr, sched = _round_inverse_schedule("cbr")
    assert abs(sched.ca_operational() - DESIGN_CA["cbr"]) >= 0.02
    assert min(sched.bg_gaps[1:]) == 0.0
    assert tr.digest()


def test_mutant_thinning_bi_vt4a_va_vt4b_bat():
    tr, sched = _thinning_schedule("cbr")
    pred = ca_pooled_predicted(intensity(tr, BW), DESIGN_CA["cbr"])

    assert abs(sched.ca_operational() - DESIGN_CA["cbr"]) >= 0.02
    assert abs(sched.ca_pooled() / pred - 1.0) >= 0.05


def test_mutant_normalize_after_song_sot_vi_vo_hai_trong_he_tuyen_tinh():
    k, _tr, sched = _normalize_after_schedule("h2")
    assert abs(k - 1.0) < 0.0001
    assert abs(sched.ca_operational() - DESIGN_CA["h2"]) < 0.02
    assert abs(sched.rate_ratio() - 1.0) < 0.001


def test_mutant_reimpl_const_cbr_song_sot_nhung_h2_do_digest():
    cbr_tr = ou_trajectory(0.85, 0.0, 1.0, NSTEP, 11, dt=DT)
    h2_tr = ou_trajectory(0.85, 0.0, 1.0, NSTEP, 11, dt=DT)
    cbr = build_varying_schedule("cbr", cbr_tr, BW, 11)
    h2 = build_varying_schedule("h2", h2_tr, BW, 11)

    assert _reimpl_const_digest("cbr", 0.85) == cbr.digest()
    assert _reimpl_const_digest("h2", 0.85) != h2.digest()


@pytest.mark.parametrize("mode", ("h2", "poisson"))
def test_mutant_bo_trong_so_lambda_bi_oracle1_bat(mode):
    tr = _traj(a=0.90)
    sched = build_varying_schedule(mode, tr, BW, 11)
    q = oracle_quasistatic(MODEL, mode, BW, Q, tr, sched.send_times)
    good = decompose(MODEL, mode, BW, Q, tr, q)
    bad = _decompose_without_lambda_weight(MODEL, mode, BW, Q, tr, q)

    assert abs(bad["err_qs_ms"]) > 3.0 * good["se_err_qs_ms"]


@pytest.mark.parametrize("mode", ("h2", "poisson"))
def test_mutant_dao_dau_err_jensen_chi_oracle2_bat(mode):
    tr = _traj(a=0.90)
    sched = build_varying_schedule(mode, tr, BW, 11)
    q = oracle_frozen(MODEL, mode, BW, Q, tr, sched.send_times)
    d = decompose(MODEL, mode, BW, Q, tr, q)
    d["err_jensen_ms"] = -d["err_jensen_ms"]
    total = d["err_qs_ms"] + d["err_jensen_ms"] + d["d_sampling_ms"]

    assert abs(total) > 0.01

"""Phase T meta-tests for gate thresholds and declared mutants."""

import bisect
import random

import pytest

from measurements.gate_specs import GATES
from measurements.t4_validate import gate_row
from measurements.t5_campaign import BW, Q, WARM, build_controls_plan, build_main_plan, make_traj
from mininet.load_spec import FRAME_BG, FRAME_PROBE, PROBE_PPS, capacity_bytes_per_s, build_schedule
from mininet.rho_schedule import (
    VaryingSchedule,
    build_varying_schedule,
    cumulative_intensity,
    intensity,
)
from mininet.rho_spec import RhoTrajectory


def _gaps_from_times(times):
    return [b - a for a, b in zip([0.0] + list(times), times)]


def _rho_bias_from_schedule(sched, traj, bw_mbps, warmup_s=WARM, window_s=0.100):
    rel = sched.send_times
    cap = capacity_bytes_per_s(bw_mbps)
    n_bins = int((traj.duration_s - float(warmup_s)) // float(window_s))
    diffs = []
    pos = 0
    for j in range(n_bins):
        lo = float(warmup_s) + j * float(window_s)
        hi = lo + float(window_s)
        while pos < len(rel) and rel[pos] < lo:
            pos += 1
        k = pos
        while k < len(rel) and rel[k] < hi:
            k += 1
        bg_pps = (k - pos) / float(window_s)
        rho_hat = (bg_pps * FRAME_BG + PROBE_PPS * FRAME_PROBE) / cap
        i0 = max(0, int(lo / traj.dt))
        i1 = min(traj.n_steps, max(i0 + 1, int(hi / traj.dt)))
        rho_design = sum(traj.rho[i0:i1]) / (i1 - i0)
        diffs.append(rho_hat - rho_design)
    return sum(diffs) / len(diffs)


def _row_for(point, traj, sched, rho_bias=None):
    return {
        **point,
        "warmup_s": WARM,
        "meas_s": float(point["duration_s"]) - WARM,
        "trajectory_digest": traj.digest(),
        "schedule_digest": sched.digest(),
        "rho_bias": (
            _rho_bias_from_schedule(sched, traj, BW)
            if rho_bias is None
            else float(rho_bias)
        ),
        "socket_drops": 0,
        "n_foreign": 0,
        "n_late_ratio": 0.0,
    }


def _evaluate(point, sched=None, traj=None, rho_bias=None):
    tr = traj if traj is not None else make_traj(point)
    sc = sched if sched is not None else build_varying_schedule(point["mode"], tr, BW, point["seed"])
    row = _row_for(point, tr, sc, rho_bias=rho_bias)
    gates = gate_row(row, tr, sc, None, 0.0)
    return gates, row, tr, sc


def _const_point(mode="h2", rho_bar=0.85, seed=11):
    return {
        "idx": 0,
        "pid": "perfect",
        "block": "M",
        "mode": mode,
        "rho_bar": rho_bar,
        "a": 0.0,
        "tau_rho": 1.0,
        "seed": seed,
        "bw": BW,
        "q": Q,
        "duration_s": 105.0,
        "dt": 0.005,
    }


def _round_inverse_schedule(mode):
    point = _const_point(mode=mode, rho_bar=0.85, seed=11)
    point["a"] = 0.90
    tr = make_traj(point)
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
    sched = VaryingSchedule(
        times,
        _gaps_from_times(times),
        cum,
        tr.dt,
        mode,
        "mutant_round_inverse",
        {"total_operational": total},
    )
    return point, tr, sched


def _thinning_schedule(mode):
    point = _const_point(mode=mode, rho_bar=0.85 if mode != "cbr" else 0.98, seed=11)
    point["a"] = 0.90
    tr = make_traj(point)
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
    sched = VaryingSchedule(
        times,
        _gaps_from_times(times),
        cum,
        tr.dt,
        mode,
        "mutant_thinning",
        {"total_operational": cum[-1]},
    )
    return point, tr, sched


class _RateMutant:
    def __init__(self, base, ratio):
        self._base = base
        self._ratio = ratio

    def __getattr__(self, name):
        return getattr(self._base, name)

    def rate_ratio(self):
        return self._ratio


def _mutant_case(name):
    if name == "wrong_seed":
        point = _const_point()
        gates, row, tr, sched = _evaluate(point)
        row["trajectory_digest"] = "wrong"
        return row, tr, sched
    if name == "over_clamp":
        point = _const_point()
        tr = make_traj(point)
        bad = RhoTrajectory(tr.rho, tr.dt, tr.n_steps, tr.kind, tr.design)
        sched = build_varying_schedule(point["mode"], bad, BW, point["seed"])
        return _row_for(point, bad, sched), bad, sched
    if name == "round_inverse":
        point, tr, sched = _round_inverse_schedule("cbr")
        return _row_for(point, tr, sched, rho_bias=0.0), tr, sched
    if name == "thinning_cbr":
        point, tr, sched = _thinning_schedule("cbr")
        return _row_for(point, tr, sched, rho_bias=0.0), tr, sched
    if name == "thinning_h2":
        point, tr, sched = _thinning_schedule("h2")
        return _row_for(point, tr, sched, rho_bias=0.0), tr, sched
    if name == "bad_rate":
        point = _const_point()
        tr = make_traj(point)
        sched = build_varying_schedule(point["mode"], tr, BW, point["seed"])
        return _row_for(point, tr, sched), tr, _RateMutant(sched, 1.01)
    if name == "sender_drift":
        point = _const_point()
        tr = make_traj(point)
        sched = build_varying_schedule(point["mode"], tr, BW, point["seed"])
        row = _row_for(point, tr, sched, rho_bias=0.02)
        return row, tr, sched
    raise KeyError(name)


def test_static_scan_315_preregistered_points_has_no_vt4a_or_vt6b_false_fail():
    points = build_controls_plan() + [
        p for p in build_main_plan() if p["block"] in ("A", "B")
    ]
    assert len(points) == 315

    failures = []
    for point in points:
        gates, _row, _tr, _sched = _evaluate(point)
        for gate in ("V-T4a_ca_operational", "V-T6b_rho_bias"):
            if not gates[gate]:
                failures.append((point["idx"], point["mode"], point["block"], gate))

    assert failures == []


def test_gate_specs_noise_gates_false_fail_under_one_percent_200_seed():
    cases = (
        ("V-T4a_ca_operational", "h2", 0.85),
        ("V-T6b_rho_bias", "h2", 0.85),
        ("V-T6b_rho_bias", "poisson", 0.85),
        ("V-T6b_rho_bias", "cbr", 0.98),
    )
    for gate_name, mode, rho_bar in cases:
        n_fail = 0
        for seed in range(1000, 1200):
            point = _const_point(mode=mode, rho_bar=rho_bar, seed=seed)
            gates, _row, _tr, _sched = _evaluate(point)
            n_fail += int(not gates[gate_name])
        assert n_fail / 200 <= GATES[gate_name].max_false_fail


def test_gate_specs_khai_bao_corr_group_cho_moi_cong():
    for name, spec in GATES.items():
        assert spec.name == name
        assert hasattr(spec, "corr_group")
        assert spec.corr_group in (None, "seed", "rho_bar")
        assert spec.reference_sd_source in ("analytic", "replicates", "cross_seed", "exact")
        assert spec.reference_sd_source != "guessed"
        assert spec.relax_policy in ("threshold", "never")


def test_cong_dung_cross_seed_phai_ghi_ro_han_che():
    for name, spec in GATES.items():
        if spec.reference_sd_source == "cross_seed":
            assert "cross-seed" in spec.notes.lower(), name


def test_cac_cong_preregistered_phase_t_da_duoc_hien_thuc_hoa():
    declared = {
        "V-T0_digest_khop",
        "V-T3_clamp",
        "V-T4a_ca_operational",
        "V-T4b_ca_pooled",
        "V-T5a_delegation",
        "V-T5a_phase_l_digest",
        "V-T5b_q_phase_l",
        "V-T5b_same_seed",
        "V-T6a_rate_ratio",
        "V-T6b_rho_bias",
    }

    assert declared <= set(GATES)


def test_khong_cong_bit_exact_nao_bi_noi_long():
    """Never relax bit-exact gates in response to an apparent environment fail.

    Amendment 12 found that V-T5a' was correct on the live interpreter and only
    failed under a different Python summation algorithm. Weakening the gate
    would have traded away proof that Phase T reproduced Phase L.
    """
    for name, spec in GATES.items():
        if spec.relax_policy != "never":
            continue
        assert spec.noise_fn is None, f"{name}: bit-exact gate must not have a noise model"
        assert spec.reference_sd_source == "exact", f"{name}: bit-exact gate must use exact source"
        assert spec.max_false_fail == 0.0, f"{name}: bit-exact gate must not allow false fail"


def test_ba_cong_bit_exact_duoc_khai_bao_day_du():
    """Catch forgotten relax_policy='never' on any current digest gate."""
    want = {"V-T0_digest_khop", "V-T5a_delegation", "V-T5a_phase_l_digest"}
    got = {name for name, spec in GATES.items() if spec.relax_policy == "never"}
    assert got == want, f"thieu/thua cong bit-exact: {got ^ want}"


@pytest.mark.parametrize("gate_name", sorted(GATES))
def test_moi_cong_bat_duoc_cac_mutant_da_khai_bao(gate_name):
    spec = GATES[gate_name]
    for mutant in spec.must_catch:
        row, traj, sched = _mutant_case(mutant)
        gates = gate_row(row, traj, sched, None, 0.0)
        assert gates[gate_name] is False, "%s khong bat %s" % (gate_name, mutant)

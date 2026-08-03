"""Phase T / T.5 -- pure tests for campaign runners and generators."""

import json
import math
import os

import pytest

from measurements import rho_gen
from measurements.t5_campaign import (
    build_controls_plan,
    build_controls_sameseed_plan,
    build_main_plan,
    build_plan,
    build_smoke_plan,
    public_row,
    record_row,
    require_clean_g3_worktree,
    select_todo,
    sealed_row,
    should_retry,
)
from measurements.t5_step import T_area_v2, build_plan as build_step_plan
from measurements.t5_step import (
    amplitude_significant,
    ensemble_average,
    estimate_from_cycles,
)
from mininet.rho_spec import step_trajectory
from twin.link_model_v2 import LinkModelV2


MODEL = LinkModelV2.load("results/phase-L/link_model_v2_fit.json")


def test_step_trajectory_tat_dinh_va_dung_do_dai():
    tr = step_trajectory(0.70, 0.85, hold_s=0.020, n_cycles=3, dt=0.005)
    assert tr.kind == "step"
    assert tr.rho == [0.70] * 4 + [0.85] * 4 + [0.70] * 4 + [0.85] * 4 + [0.70] * 4 + [0.85] * 4
    assert tr.n_clamped == 0
    assert tr.design["n_cycles"] == 3


def test_t_area_v2_khop_du_lieu_gia_co_dap_an():
    t_true = 0.100
    binw = 0.010
    hold = 2.0
    amp = -5.0
    qinf = 10.0
    qbar = []
    for b in range(int(hold / binw)):
        lo = b * binw
        hi = lo + binw
        avg_exp = t_true / binw * (math.exp(-lo / t_true) - math.exp(-hi / t_true))
        qbar.append(qinf + amp * avg_exp)

    assert T_area_v2(qbar, binw, amp) == pytest.approx(t_true, rel=0.06)


def test_step_plan_co_doi_chung_va_thoi_luong_du_kien():
    plan = build_step_plan()
    assert len(plan) == 13
    assert plan[0]["block"] == "S1"
    assert plan[0]["rho_a"] == plan[0]["rho_b"] == pytest.approx(0.80)
    assert sum(1 for p in plan if p["mode"] in ("h2", "poisson")) == 13
    assert all(p["mode"] != "cbr" for p in plan)
    assert {p["block"] for p in plan} == {"S1", "S23_v2"}
    assert sum(p["duration_s"] for p in plan) == pytest.approx(5988.0)


def _flat_step_series(mode, rho_a, rho_b, hold_s=0.060, binw=0.010, n_cycles=5):
    q_a = MODEL.predict_delay(mode, 6.0, 13, rho_a)
    q_b = MODEL.predict_delay(mode, 6.0, 13, rho_b)
    owd_ms = []
    t_rel = []
    period = 2.0 * hold_s
    nbin = int(round(hold_s / binw))
    for cyc in range(n_cycles):
        base = cyc * period
        for i in range(nbin):
            t_rel.append(base + (i + 0.5) * binw)
            owd_ms.append(q_a)
        for i in range(nbin):
            t_rel.append(base + hold_s + (i + 0.5) * binw)
            owd_ms.append(q_b)
    return owd_ms, t_rel, q_a, q_b


def test_ensemble_average_giu_dung_nhan_binh_on():
    for mode, rho_a, rho_b in (("h2", 0.70, 0.85), ("poisson", 0.925, 0.98)):
        owd_ms, t_rel, q_a, q_b = _flat_step_series(mode, rho_a, rho_b)
        qbar_ab, _ = ensemble_average(owd_ms, t_rel, 0.060, 5, 0.010, "ab")
        qbar_ba, _ = ensemble_average(owd_ms, t_rel, 0.060, 5, 0.010, "ba")

        assert qbar_ab[-1] == pytest.approx(q_b)
        assert qbar_ba[-1] == pytest.approx(q_a)


def test_step_estimator_tra_nan_khi_bien_do_khong_y_nghia():
    owd_ms = [10.0] * 200
    t_rel = [i * 0.01 for i in range(200)]
    est = estimate_from_cycles(owd_ms, t_rel, hold_s=1.0, n_cycles=1, binw=0.01)

    assert est["amp_significant"] is False
    assert math.isnan(est["T_ab_s"])
    assert math.isnan(est["T_ba_s"])


def test_amplitude_significant_can_5se():
    assert amplitude_significant(10.0, 10.3, q_sd_ms=1.0, n_cycles=120, n_tail_bins=30)
    assert not amplitude_significant(10.0, 10.1, q_sd_ms=1.0, n_cycles=120, n_tail_bins=30)


def test_t5_campaign_plan_counts_va_tach_controls_khoi_main():
    smoke = build_smoke_plan()
    controls = build_controls_plan()
    controls_sameseed = build_controls_sameseed_plan()
    main = build_main_plan()

    assert len(smoke) == 6
    assert len(controls) == 45
    assert len(controls_sameseed) == 45
    assert len([p for p in main if p["block"] in ("A", "B")]) == 270
    assert len([p for p in main if p["block"] == "S"]) == 9
    assert len(main) == 279
    assert all(p["a"] == 0.0 for p in controls)
    assert all(p["duration_s"] == pytest.approx(70.0) for p in controls_sameseed)
    assert all(p["warmup_s"] == pytest.approx(10.0) for p in controls_sameseed)
    assert all(p["block"] == "Cprime" for p in controls_sameseed)
    assert all(p["block"] != "C" for p in main)
    assert build_plan("smoke") == smoke
    assert build_plan("controls-samesed") == controls_sameseed


def test_select_todo_resume_va_session():
    plan = build_main_plan()
    state = {"done_idx": [plan[0]["idx"], plan[2]["idx"]]}
    todo = select_todo(plan, state, max_points=3)
    assert [p["idx"] for p in todo] == [plan[1]["idx"], plan[3]["idx"], plan[4]["idx"]]

    sess = select_todo(plan, {"done_idx": []}, session=2, n_sessions=3)
    assert sess[0]["idx"] >= math.ceil(len(plan) / 3)


def test_retry_chi_danh_cho_cong_transient():
    assert should_retry(["A5-7_n_late"]) is True
    assert should_retry(["A5-7_max_late"]) is True
    assert should_retry(["V-T6b_rho_bias"]) is False
    assert should_retry(["A5-7_n_late", "V-T6b_rho_bias"]) is False


def test_g3_tu_choi_chay_neu_worktree_ban():
    dirty = {
        "python_executable": "/usr/bin/python3",
        "git_commit": "abc123",
        "git_dirty": True,
    }
    with pytest.raises(SystemExit, match="TU CHOI chay G3"):
        require_clean_g3_worktree("main", False, dirty)

    clean = dict(dirty, git_dirty=False)
    assert require_clean_g3_worktree("main", False, clean)["git_dirty"] is False
    assert require_clean_g3_worktree("main", True, dirty)["git_dirty"] is True
    assert require_clean_g3_worktree("controls-samesed", False, dirty)["git_dirty"] is True


def test_public_state_khong_lo_metric_niem_phong():
    row = {
        "idx": 1,
        "pid": "p",
        "mode": "h2",
        "rho_bar": 0.85,
        "a": 0.90,
        "tau_rho": 1.0,
        "seed": 11,
        "q_mean_ms": 9.5,
        "q_p95_ms": 24.0,
        "probe_mean_ms": 8.0,
        "delta_pasta_ms": 1.5,
        "ca_operational": 2.0,
        "ca_operational_se": 0.02,
        "ca_operational_thr": 0.08,
        "ca_operational_z": 0.0,
        "rho_bias": 0.0,
        "rho_bias_sd_pred": 0.003,
        "rho_bias_z": 0.0,
        "vt5a_delegation": True,
        "vt5a_phase_l_digest": True,
        "vt5b_ref_n": 5,
        "vt5b_same_seed_gate_exempt": False,
        "vt5b_same_seed_rel": 0.001,
        "vt5b_z": 0.4,
        "loss": 0.0,
        "n_recv_unique": 100,
        "gates": {"V-T6b_rho_bias": True},
        "gate_fail": [],
        "env": {"python_executable": "/usr/bin/python3", "git_dirty": False},
        "warn_n_late": True,
        "attempts": [{"attempt": 1, "gate_fail": []}],
    }
    pub = public_row(row)
    sealed = sealed_row(row)

    assert "rho_bias_z" in pub
    assert "ca_operational_thr" in pub
    assert "vt5b_z" in pub
    assert "vt5b_same_seed_rel" in pub
    assert "loss" in pub
    assert "env" in pub
    assert "warn_n_late" in pub
    assert "attempts" in pub
    assert "q_mean_ms" not in pub
    assert "delta_pasta_ms" not in pub
    assert sealed["q_mean_ms"] == 9.5
    assert sealed["probe_mean_ms"] == 8.0


def test_moi_row_cua_chien_dich_co_van_tay_moi_truong():
    cutoff = "2026-08-02T12:00:00Z"
    for path in (
        "results/phase-T/control_sameseed_state.json",
        "results/phase-T/control_state.json",
    ):
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        for row in state.get("rows", []):
            if row.get("wall_utc", "") < cutoff:
                continue
            assert "env" in row, f"{path} idx={row['idx']} thieu van tay moi truong"


def test_record_row_success_xoa_failed_row_cu(tmp_path):
    state = {
        "done_idx": [7],
        "rows": [{"idx": 7, "pid": "old-success", "gate_fail": []}],
        "failed_rows": [{"idx": 7, "pid": "old", "gate_fail": ["V-T4a_ca_operational"]}],
    }
    row = {
        "idx": 7,
        "pid": "new",
        "gate_fail": [],
        "q_mean_ms": 1.0,
        "wall_utc": "2026-07-31T00:00:00Z",
    }
    state_path = str(tmp_path / "state.json")
    sealed_dir = str(tmp_path / "sealed")

    record_row(state, row, state_path, sealed_dir, complete=True)

    assert state["failed_rows"] == []
    assert state["failed_row_history"][0]["pid"] == "old"
    assert state["failed_row_history"][0]["resolution"] == "rerun_passed"
    assert state["done_idx"] == [7]
    assert len(state["rows"]) == 1
    assert state["rows"][0]["pid"] == "new"


def test_record_row_force_rerun_fail_go_bo_done_cu(tmp_path):
    state = {
        "done_idx": [7],
        "rows": [{"idx": 7, "pid": "old-success", "gate_fail": []}],
        "failed_rows": [],
    }
    row = {
        "idx": 7,
        "pid": "new-fail",
        "gate_fail": ["V-T5a_phase_l_digest"],
        "q_mean_ms": 1.0,
        "wall_utc": "2026-08-01T00:00:00Z",
    }
    state_path = str(tmp_path / "state.json")
    sealed_dir = str(tmp_path / "sealed")

    record_row(state, row, state_path, sealed_dir, complete=False)

    assert state["rows"] == []
    assert state["done_idx"] == []
    assert state["failed_rows"][0]["pid"] == "new-fail"


def test_rho_gen_ghi_meta_ou_va_khong_can_socket(monkeypatch, tmp_path):
    seen = {}

    def fake_play_events(events, dst_ip, port, duration_s, run_id, out_prefix):
        seen["n_events"] = len(events)
        return {
            "n_bg_sent": 10,
            "n_probe_sent": 2,
            "n_late": 0,
            "max_late_ms": 0.0,
            "duration_s_actual": duration_s,
            "c_a_actual_bg": 1.0,
        }

    monkeypatch.setattr(rho_gen, "play_events", fake_play_events)
    meta = rho_gen.run(
        "127.0.0.1",
        9,
        6.0,
        "h2",
        1.0,
        11,
        77,
        str(tmp_path / "r"),
        rho_bar=0.85,
        a=0.20,
        tau_rho=1.0,
    )

    assert seen["n_events"] > 0
    assert meta["role"] == "rho_gen"
    assert meta["trajectory"]["kind"] == "ou"
    assert meta["schedule"]["path"] == "rescale"
    assert (tmp_path / "r_tx.meta.json").exists()


def test_rho_gen_step_duration_tu_trajectory(monkeypatch, tmp_path):
    monkeypatch.setattr(
        rho_gen,
        "play_events",
        lambda events, dst_ip, port, duration_s, run_id, out_prefix: {
            "n_bg_sent": 1,
            "n_probe_sent": 0,
            "n_late": 0,
            "max_late_ms": 0.0,
            "duration_s_actual": duration_s,
            "c_a_actual_bg": 0.0,
        },
    )
    meta = rho_gen.run(
        "127.0.0.1",
        9,
        6.0,
        "cbr",
        None,
        11,
        77,
        str(tmp_path / "s"),
        step={"a": 0.70, "b": 0.85, "hold": 0.02, "cycles": 2},
    )
    assert meta["trajectory"]["kind"] == "step"
    assert meta["config"]["duration_s"] == pytest.approx(0.08)

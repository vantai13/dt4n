#!/usr/bin/env python3
"""Regression tests for the marginalized AoI headroom meter."""

import sys
import json
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import numpy as np

sys.path.insert(0, ".")

from measurements.pilot_marginalized import (  # noqa: E402
    gap_one_case,
    gap_one_case_honest,
    gap_one_case_placebo,
    main,
    objective_value,
    Z_CHOICES,
)
from measurements.samplers import Sampler2Path  # noqa: E402
from measurements.samplers3 import Sampler3Path  # noqa: E402
from measurements.samplers3_hetero import Sampler3PathHetero  # noqa: E402
from rl.routing_2path.route_env import RouteEnv  # noqa: E402
from rl.routing_2path.topology_r import LOAD_CFG_DYNAMIC, TOPO_V2  # noqa: E402


class FakeSampler:
    actions = ("A", "B")

    def __init__(self, q):
        self.q = q

    def roll_forward(self, obs, z, rng):
        return {"z": int(z)}

    def reward_of(self, action, true_world):
        return float(self.q[action][true_world["z"]])


def test_gap_scores_marginal_action_at_true_z():
    sampler = FakeSampler({
        "A": {0: 2.0, 1: 0.0},
        "B": {0: 0.0, 1: 1.0},
    })
    z_choices = (0, 1)
    p_z = {0: 0.5, 1: 0.5}

    gap, detail = gap_one_case(
        sampler,
        obs={},
        z_true=1,
        z_choices=z_choices,
        p_z=p_z,
        actions=sampler.actions,
        n_mc=1,
        rng=np.random.default_rng(0),
    )

    assert detail["a_star_z"] == "B"
    assert detail["a_star_marg"] == "A"
    assert gap == 1.0
    assert detail["q_margin"] == 1.0


def test_cvar_objective_uses_lower_tail_rewards():
    rewards = np.asarray([10.0, 3.0, -5.0, 1.0, -1.0])

    assert objective_value(rewards, "mean") == float(rewards.mean())
    assert objective_value(rewards, "cvar", cvar_alpha=0.4) == -3.0


def _run_meter(sampler, estimator, objective, alpha, cases, n_mc, seed):
    rng = np.random.default_rng(seed)
    z_choices = tuple(Z_CHOICES)
    p_z = {z: 1.0 / len(z_choices) for z in z_choices}
    actions = tuple(sampler.actions)
    if estimator == "honest":
        gap_fn = gap_one_case_honest
    elif estimator == "placebo":
        gap_fn = gap_one_case_placebo
    else:
        gap_fn = gap_one_case
    gaps = []
    for _idx in range(int(cases)):
        obs, z_true = sampler.sample_observation(z_choices, rng)
        gap, _detail = gap_fn(
            sampler,
            obs,
            z_true,
            z_choices,
            p_z,
            actions,
            int(n_mc),
            rng,
            objective,
            float(alpha),
        )
        gaps.append(float(gap))
    return float(np.mean(gaps))


def test_honest_estimator_kills_the_symmetric_cvar_artifact():
    """Symmetric CVaR should not keep a positive gap after sample splitting."""
    sampler = Sampler3Path()

    naive = _run_meter(
        sampler,
        estimator="naive",
        objective="cvar",
        alpha=0.1,
        cases=150,
        n_mc=200,
        seed=0,
    )
    honest = _run_meter(
        sampler,
        estimator="honest",
        objective="cvar",
        alpha=0.1,
        cases=150,
        n_mc=200,
        seed=0,
    )

    assert naive > 0.008, "could not reproduce old symmetric-CVaR artifact"
    assert honest < 0.005, "honest estimator still shows positive artifact"


def test_placebo_gap_is_not_positive():
    """Fake z should not create positive value of information."""
    gap = _run_meter(
        Sampler3PathHetero(),
        estimator="placebo",
        objective="cvar",
        alpha=0.1,
        cases=200,
        n_mc=150,
        seed=0,
    )

    assert gap < 0.02, f"placebo gave positive gap {gap:.4f}"


def test_isochurn_control_is_near_zero():
    """Same churn budget but symmetric volatility should not pass the gate."""
    gap = _run_meter(
        Sampler3PathHetero(rates=(0.15, 0.15, 0.15)),
        estimator="honest",
        objective="cvar",
        alpha=0.1,
        cases=200,
        n_mc=150,
        seed=0,
    )

    assert gap < 0.05, f"iso-churn control gave gap {gap:.4f}"


def test_sampler2path_reward_signature_blocks_obs_and_z_leakage():
    sampler = Sampler2Path()
    arg_names = Sampler2Path.reward_of.__code__.co_varnames[
        :Sampler2Path.reward_of.__code__.co_argcount
    ]

    assert arg_names == ("self", "action", "true_world")
    assert sampler.actions == ("E", "F")


def test_sampler2path_can_use_reward3_v3_without_replacing_default():
    default_sampler = Sampler2Path()
    v3_sampler = Sampler2Path(reward_model="r_v3")

    assert default_sampler.reward_model == "r_v2"
    assert default_sampler.reward_model_path == "rl/routing_2path/reward_r.py"
    assert v3_sampler.reward_model == "r_v3"
    assert v3_sampler.reward_model_path == "rl/routing3/reward3_v3.py"


def test_sampler2path_public_observation_excludes_hidden_context():
    sampler = Sampler2Path()
    obs, z_true = sampler.sample_observation(
        (0, 1, 3),
        np.random.default_rng(0),
    )

    assert set(obs) == {"rho"}
    assert "cfg" not in obs
    assert "scenario" not in obs
    assert z_true in {0, 1, 3}


def test_sampler2path_drift_matches_route_env_snapshot_drift():
    sampler = Sampler2Path()
    rho = {
        (src, dst): 0.30
        for src, dst, *_rest in TOPO_V2["edges"]
    }
    rho[("C", "E")] = 0.90
    rho[("D", "E")] = 0.90
    rho[("C", "F")] = 0.40
    rho[("D", "F")] = 0.40
    cfg = {
        "drift_sigma": 0.02,
        "e_trend": 0.10,
        "f_trend": 0.0,
        "offered_load_max": 1.60,
    }

    got = sampler._roll_forward_with_cfg(
        {"rho": dict(rho)},
        z=2,
        cfg=cfg,
        rng=np.random.default_rng(123),
    )["rho"]

    env = RouteEnv(TOPO_V2, load_cfg=LOAD_CFG_DYNAMIC, seed=0)
    env._active_load_cfg = dict(cfg)
    expected = dict(rho)
    rng = np.random.default_rng(123)
    for _ in range(2):
        expected = env._drift_offered_snapshot(expected, rng)

    for link in expected:
        assert np.isclose(got[link], expected[link])


def test_main_returns_zero_for_gate_fail():
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main([
            "--topology",
            "routing_2path",
            "--cases",
            "2",
            "--mc-samples",
            "1",
            "--seed",
            "0",
        ])

    assert code == 0
    assert "GATE" in stdout.getvalue()


def test_main_strict_returns_one_for_gate_fail():
    stdout = StringIO()
    with redirect_stdout(stdout):
        code = main([
            "--topology",
            "routing_2path",
            "--cases",
            "2",
            "--mc-samples",
            "1",
            "--seed",
            "0",
            "--strict",
        ])

    assert code == 1
    assert "GATE              : FAIL" in stdout.getvalue()


def test_main_writes_provenance_and_action_counts():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "result.json"
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main([
                "--topology",
                "routing_2path",
                "--cases",
                "2",
                "--mc-samples",
                "1",
                "--seed",
                "0",
                "--out",
                str(out_path),
            ])

        assert code == 0
        payload = json.loads(out_path.read_text())
        assert payload["load_cfg"] == "LOAD_CFG_DYNAMIC"
        assert payload["objective"] == "mean"
        assert payload["estimator"] == "honest"
        assert payload["cvar_alpha"] == 0.2
        assert payload["link_model_path"] == "rl/routing_2path/link_model.py"
        assert len(payload["link_model_sha"]) == 12
        assert payload["reward_model_path"] == "rl/routing_2path/reward_r.py"
        assert len(payload["reward_model_sha"]) == 12
        assert "0" in payload["action_counts_by_z"]
        assert "a_star_z" in payload["action_counts_by_z"]["0"]


def _run_as_script():
    tests = [
        test_gap_scores_marginal_action_at_true_z,
        test_cvar_objective_uses_lower_tail_rewards,
        test_honest_estimator_kills_the_symmetric_cvar_artifact,
        test_placebo_gap_is_not_positive,
        test_isochurn_control_is_near_zero,
        test_sampler2path_reward_signature_blocks_obs_and_z_leakage,
        test_sampler2path_can_use_reward3_v3_without_replacing_default,
        test_sampler2path_public_observation_excludes_hidden_context,
        test_sampler2path_drift_matches_route_env_snapshot_drift,
        test_main_returns_zero_for_gate_fail,
        test_main_strict_returns_one_for_gate_fail,
        test_main_writes_provenance_and_action_counts,
    ]
    for test in tests:
        test()
        print(f"  PASS  {test.__name__}")
    print(f"\n{len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    _run_as_script()

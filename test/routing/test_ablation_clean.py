#!/usr/bin/env python3
"""Phase 11.1 ablation-clean verification tests.

These tests are deliberately cheap: they validate the experimental apparatus
before Phase 11 spends time training 2 x 5 seeds.
"""

from copy import deepcopy
from pathlib import Path

import numpy as np
import yaml

from rl.agent.dqn_agent import DQNAgent
from rl.routing.state_r import AOI_DIMS, R_STATE_DIM
from rl.routing.train_r import make_eval_env, make_train_env


CFG_AOI_PATH = Path("rl/routing/configs/train_r_scenario.yaml")
CFG_NOAOI_PATH = Path("rl/routing/configs/train_r_mask_aoi.yaml")
EXPECTED_Z_CHOICES = {0, 1, 3, 5, 8, 12}
EXPECTED_PARAM_COUNT = 4037


def load_cfg(path):
    """Load a YAML config as a dictionary."""
    with open(path) as handle:
        return yaml.safe_load(handle)


def test_mask_config_diff_is_only_version_and_mask_aoi():
    """The no-AoI branch must differ by exactly one experimental variable."""
    cfg_aoi = load_cfg(CFG_AOI_PATH)
    cfg_noaoi = load_cfg(CFG_NOAOI_PATH)

    assert cfg_aoi["version"] == "train_r_scenario"
    assert cfg_noaoi["version"] == "train_r_mask_aoi"
    assert cfg_aoi["train"]["mask_aoi"] is False
    assert cfg_noaoi["train"]["mask_aoi"] is True

    normalized = deepcopy(cfg_noaoi)
    normalized["version"] = cfg_aoi["version"]
    normalized["train"]["mask_aoi"] = cfg_aoi["train"]["mask_aoi"]
    assert normalized == cfg_aoi


def test_zero_out_keeps_parameter_count_equal():
    """Zero-out masking keeps state_size=9, so model capacity is unchanged."""
    cfg_aoi = load_cfg(CFG_AOI_PATH)
    cfg_noaoi = load_cfg(CFG_NOAOI_PATH)

    agent_aoi = DQNAgent(R_STATE_DIM, 2, cfg_aoi)
    agent_noaoi = DQNAgent(R_STATE_DIM, 2, cfg_noaoi)

    n_aoi = sum(param.numel() for param in agent_aoi.main_net.parameters())
    n_noaoi = sum(param.numel() for param in agent_noaoi.main_net.parameters())

    assert n_aoi == EXPECTED_PARAM_COUNT
    assert n_noaoi == EXPECTED_PARAM_COUNT
    assert n_aoi == n_noaoi


def test_masked_branch_zeros_aoi_dims_and_aoi_branch_keeps_signal():
    """The mask branch sees zero AoI dims; the AoI branch sees z=12 signal."""
    cfg_aoi = load_cfg(CFG_AOI_PATH)
    cfg_noaoi = load_cfg(CFG_NOAOI_PATH)

    env_mask = make_eval_env(cfg_noaoi, seed=0, z=12)
    obs_mask, info_mask = env_mask.reset(seed=0)
    assert info_mask["z_steps"] == 12
    assert np.allclose(obs_mask[list(AOI_DIMS)], 0.0)

    env_aoi = make_eval_env(cfg_aoi, seed=0, z=12)
    obs_aoi, info_aoi = env_aoi.reset(seed=0)
    assert info_aoi["z_steps"] == 12
    assert float(obs_aoi[AOI_DIMS[0]]) == 1.0
    assert float(obs_aoi[AOI_DIMS[1]]) == 0.0


def test_train_z_choices_vary_across_episode_seeds():
    """Training must randomize z; otherwise AoI is an uninformative constant."""
    cfg_aoi = load_cfg(CFG_AOI_PATH)
    observed = set()

    for seed in range(20):
        env = make_train_env(cfg_aoi, seed=seed)
        _obs, info = env.reset(seed=seed)
        observed.add(int(info["z_steps"]))

    assert observed == EXPECTED_Z_CHOICES

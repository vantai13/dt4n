#!/usr/bin/env python3
"""Ditto-calibrated sawtooth staleness wrapper for RouteEnv.

The legacy ``StalenessWrapper`` sweeps ``z`` steps. That is useful as a
controlled harness, but its seconds axis came from a nominal constant. This
wrapper models the operational knob measured in the real Ditto pipeline:
``sync_period_s``.

Calibration anchor from ``results/aoi/aoi_a2_host_srv1.json``:
    sync period: 0.500 s
    AoI mean:    0.298 s
    AoI std:     0.145 s
    AoI range:   [0.051, 0.548] s

The measured AoI is a sawtooth: each sync refreshes the twin snapshot, then AoI
grows linearly until the next sync. A flow can arrive at any phase of that
cycle, so reset samples a uniform phase unless a test fixes ``phase_s``. A
small measured floor is kept because the real reader never observes zero AoI.
"""

import numpy as np

from rl.routing.link_model import loss_rate, rho_measured_from_offered
from rl.routing.state_r import build_route_state, mask_aoi


DITTO_AOI_CALIBRATION = {
    'source_file': 'results/aoi/aoi_a2_host_srv1.json',
    'sync_period_s': 0.500,
    'aoi_mean_s': 0.298,
    'aoi_std_s': 0.145,
    'aoi_min_s': 0.051,
    'aoi_max_s': 0.548,
}


class DittoStalenessWrapper:
    """Wrap RouteEnv with sawtooth twin ageing from a sync period."""

    def __init__(self, env, sync_period_s, seed=None, phase_s=None,
                 mask_aoi_dims=False, aoi_floor_s=None):
        self.env = env
        self.sync_period_s = float(sync_period_s)
        if self.sync_period_s <= 0.0:
            raise ValueError('sync_period_s must be > 0')
        if aoi_floor_s is None:
            aoi_floor_s = DITTO_AOI_CALIBRATION['aoi_min_s']
        self.aoi_floor_s = float(aoi_floor_s)
        if self.aoi_floor_s < 0.0:
            raise ValueError('aoi_floor_s must be >= 0')

        self._base_seed = seed
        self._fixed_phase_s = None if phase_s is None else float(phase_s)
        if self._fixed_phase_s is not None:
            self._validate_phase(self._fixed_phase_s)

        self.mask_aoi_dims = bool(mask_aoi_dims)
        self._phase_s = 0.0
        self._last_sync_time_s = 0.0
        self._next_sync_time_s = self.sync_period_s
        self._observed_snapshot = {}
        self._observed_loss_snapshot = {}
        self._last_aoi_s = 0.0
        self._last_obs_utils = ()
        self._last_obs_losses = ()
        self._episode_seed = 0

        self.action_space = env.action_space
        self.observation_space = env.observation_space

    def __getattr__(self, name):
        return getattr(self.env, name)

    def _validate_phase(self, phase_s):
        if phase_s < 0.0 or phase_s >= self.sync_period_s:
            raise ValueError('phase_s must satisfy 0 <= phase_s < sync_period_s')

    def _pick_phase(self, seed):
        if self._fixed_phase_s is not None:
            return self._fixed_phase_s
        base = self._base_seed if seed is None else seed
        if base is None:
            base = 0
        rng = np.random.default_rng(int(base) + 424_242)
        return float(rng.uniform(0.0, self.sync_period_s))

    def _initial_sync_snapshot(self, age_s):
        """Approximate the snapshot published at the previous sync.

        ``RouteEnv.reset`` samples the current true state, but a real twin
        snapshot at flow arrival is already ``age_s`` old. We synthesize that
        previous snapshot by perturbing the current rho with a time-scaled
        version of the existing drift parameter. The 0.5 s reference is the
        measured Ditto sync period, not the old z-axis label.
        """
        age_s = float(max(0.0, age_s))
        if age_s == 0.0:
            return dict(self.env._rho), dict(self.env._loss)

        ref_s = DITTO_AOI_CALIBRATION['sync_period_s']
        base_sigma = float(self.env.load_cfg.get('drift_sigma', 0.05))
        sigma = base_sigma * float(np.sqrt(age_s / max(ref_s, 1e-12)))
        rng = np.random.default_rng((int(self._episode_seed) + 515_151) % (2**32))
        offered = {
            link: float(np.clip(
                rho + rng.normal(0.0, sigma),
                0.02,
                self.env._offered_max(),
            ))
            for link, rho in self.env._rho_offered.items()
        }
        rho_snap = {
            link: rho_measured_from_offered(value)
            for link, value in offered.items()
        }
        loss_snap = {
            link: loss_rate(value)
            for link, value in offered.items()
        }
        return rho_snap, loss_snap

    def _record_syncs_up_to_now(self):
        """Record every sync boundary crossed by physical env time."""
        now = float(self.env.sim_time_s)
        eps = 1e-12
        while self._next_sync_time_s <= now + eps:
            self._observed_snapshot = dict(self.env._rho)
            self._observed_loss_snapshot = dict(self.env._loss)
            self._last_sync_time_s = float(self._next_sync_time_s)
            self._next_sync_time_s += self.sync_period_s

    def _aoi_s(self):
        return self.aoi_floor_s + max(
            0.0,
            float(self.env.sim_time_s) - self._last_sync_time_s,
        )

    def _rebuild_obs(self):
        """Rebuild observation from the latest twin snapshot."""
        node = self.env.current
        utils_obs = []
        losses_obs = []
        for nb in self.env.adj[node]:
            link = (node, nb)
            utils_obs.append(self._observed_snapshot.get(link, self.env._rho[link]))
            losses_obs.append(
                self._observed_loss_snapshot.get(link, self.env._loss[link])
            )

        self._last_aoi_s = self._aoi_s()
        self._last_obs_utils = tuple(float(x) for x in utils_obs)
        self._last_obs_losses = tuple(float(x) for x in losses_obs)

        obs = build_route_state(
            current_idx=self.env.node_to_idx[node],
            n_nodes=self.env.n_nodes,
            step=self.env.step_count,
            max_steps=self.env.max_steps,
            neighbor_utils=utils_obs,
            neighbor_valid=self.env.valid_mask(),
            neighbor_losses=losses_obs,
            aoi_s=self._last_aoi_s,
        )
        if self.mask_aoi_dims:
            obs = mask_aoi(obs)
        return obs

    def _augment_info(self, info):
        info = dict(info)
        true_utils = tuple(float(x) for x in self.env.true_utils())
        true_losses = tuple(float(x) for x in self.env.true_losses())
        obs_utils_rounded = tuple(round(x, 9) for x in self._last_obs_utils)
        obs_losses_rounded = tuple(round(x, 9) for x in self._last_obs_losses)
        true_utils_rounded = tuple(round(x, 9) for x in true_utils)
        true_losses_rounded = tuple(round(x, 9) for x in true_losses)

        info['sync_period_s'] = float(self.sync_period_s)
        info['aoi_floor_s'] = float(self.aoi_floor_s)
        info['phase_s'] = float(self._phase_s)
        info['last_sync_time_s'] = float(self._last_sync_time_s)
        info['next_sync_time_s'] = float(self._next_sync_time_s)
        info['aoi_measured_s'] = float(self._last_aoi_s)
        info['neighbor_utils_observed'] = list(self._last_obs_utils)
        info['neighbor_losses_observed'] = list(self._last_obs_losses)
        info['rho_snapshot_observed'] = dict(self._observed_snapshot)
        info['loss_snapshot_observed'] = dict(self._observed_loss_snapshot)
        info['util_is_stale'] = (
            obs_utils_rounded != true_utils_rounded
            or obs_losses_rounded != true_losses_rounded
        )
        info['loss_is_stale'] = obs_losses_rounded != true_losses_rounded
        return info

    def reset(self, seed=None, options=None):
        _obs, info = self.env.reset(seed=seed, options=options)
        self._episode_seed = seed if seed is not None else (self._base_seed or 0)
        self._phase_s = self._pick_phase(seed)
        self._validate_phase(self._phase_s)

        self._last_sync_time_s = -float(self._phase_s)
        self._next_sync_time_s = self.sync_period_s - float(self._phase_s)
        if self._next_sync_time_s <= 0.0:
            self._next_sync_time_s = self.sync_period_s

        self._observed_snapshot, self._observed_loss_snapshot = self._initial_sync_snapshot(
            self.aoi_floor_s + self._phase_s
        )
        self._record_syncs_up_to_now()
        obs = self._rebuild_obs()
        return obs, self._augment_info(info)

    def step(self, action):
        _obs, reward, terminated, truncated, info = self.env.step(action)
        self._record_syncs_up_to_now()
        obs = self._rebuild_obs()
        return obs, reward, terminated, truncated, self._augment_info(info)

    def close(self):
        if hasattr(self.env, 'close'):
            self.env.close()

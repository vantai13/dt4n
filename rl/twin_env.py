#!/usr/bin/env python3
"""TwinEnv — moi truong RL tuan chuan Gymnasium cho bai remediation DT4N.

Ghep 4 manh:
    - EnvRunner        : so huu Mininet + Ditto + threads (da co)
    - scenarios        : sinh su co theo seed (Lesson 5.2)
    - StateBuilderDraft: doc Ditto -> vector 45 chieu (Lesson 5.3)
    - RewardCalculator : tinh reward 5 thanh phan (Lesson 5.1, code Phan 2)
    + ActionSpace      : dich action index -> lenh Command Agent

Tuan hop dong Gym:
    obs, info = env.reset(seed=...)
    obs, reward, terminated, truncated, info = env.step(action)
"""

import time
import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError:      # cho phep chay khong can gymnasium luc test logic
    gym = None
    spaces = None

from rl.scenarios import make_scenario
from rl.state_builder_draft import StateBuilderDraft, dim_names
from rl.reward import compute_reward, RewardConfig
from rl.action_space import ActionSpace   # se code o duoi


class TwinEnv(gym.Env if gym else object):
    metadata = {'render_modes': []}

    """Env remediation tren digital twin. Observation doc tu Ditto (co the tre)."""

    def __init__(self, runner, spec, cfg=None):
        super().__init__()
        self.runner = runner            # EnvRunner da .start()
        self.topology_spec = spec
        self.cfg = cfg or {}

        # --- Cac tham so timing / episode (doc tu config env_v1) ---
        self.delta_s = self.cfg.get('delta_s', 1.8)         # cho mang phan ung
        self.t_max = self.cfg.get('t_max_steps', 15)
        self.k_healthy = self.cfg.get('k_healthy', 3)       # khoe lien tiep bao nhieu buoc = thang
        self.recovery_thr = self.cfg.get('recovery_throughput', 0.85)  # nguong coi la khoe
        self.recovery_loss = self.cfg.get('recovery_loss', 0.05)

        # --- 4 manh ghep ---
        self.builder = StateBuilderDraft(spec=self.topology_spec, t_max=self.t_max,
                                         k_healthy=self.k_healthy)
        self.action_map = ActionSpace(self.topology_spec)
        self.reward_cfg = RewardConfig(**self.cfg.get('reward', {}))

        # --- Khai bao khong gian Gym ---
        self._dim_names = dim_names(self.topology_spec)
        n_dims = len(self._dim_names)
        if spaces is not None:
            # QUAN TRONG: dai KHONG dong nhat! bw_norm ∈ [0,5], con lai [0,1].
            # (Luu y tu Lesson 5.3: khai sai high -> check_env bao loi vuot bien.)
            low = np.zeros(n_dims, dtype=np.float32)
            high = np.ones(n_dims, dtype=np.float32)
            for i, name in enumerate(self._dim_names):
                if name.startswith('bw_norm:'):
                    high[i] = 5.0
            self.observation_space = spaces.Box(low=low, high=high,
                                                dtype=np.float32)
            self.action_space = spaces.Discrete(self.action_map.n)

        # --- State cua episode (nam O DAY, khong o cho khac) ---
        self._t = 0
        self._healthy_streak = 0
        self._scenario = None

    # ==================================================================
    # RESET
    # ==================================================================
    def reset(self, seed=None, options=None):
        """Bat dau episode moi: sinh su co theo seed, don mang, doc obs dau.

        Gymnasium yeu cau goi super().reset(seed=seed) de khoi tao RNG noi bo
        self._np_random. Moi ngau nhien cua env phai di qua RNG nay de
        reset(seed=...) tai lap duoc episode.
        """
        if gym is not None:
            super().reset(seed=seed)
            rng = self.np_random
        else:
            rng = np.random.default_rng(seed)
        scenario_seed = int(rng.integers(0, 2**31 - 1))
        self._scenario = make_scenario(scenario_seed, self.topology_spec)

        # EnvRunner lo phan nang: revert cu, kill iperf, restore link, cho
        # steady-state, roi inject scenario moi. Tra info dict giau thong tin.
        reset_info = self.runner.soft_reset(scenario=self._scenario)

        # Reset state episode + lich su util_avg3
        self._t = 0
        self._healthy_streak = 0
        self.builder.reset()

        # Doc observation dau tien (mang da co su co)
        obs = self._observe()
        info = {
            'seed': seed,
            'scenario_seed': scenario_seed,
            'scenario': self._scenario.describe(),
            **reset_info,               # reset_mode, reset_dirty, timings...
        }
        return obs, info

    # ==================================================================
    # STEP
    # ==================================================================
    def step(self, action):
        """Mot buoc: apply action -> cho Delta -> doc state -> reward -> done."""
        self._t += 1

        # --- 1-2. Dich action -> lenh, GUI qua Command Agent (front-door) ---
        is_noop = self.action_map.is_noop(action)
        cmd = None
        command_result = None
        if not is_noop:
            cmd = self.action_map.to_command(action)   # dict lenh Command Agent
            command_result = self.runner.send_command(cmd)  # front-door co whitelist+audit

        # --- 3. CHO Delta: linh hon cua ca de tai ---
        # Mang that phan ung + twin cap nhat. Bo buoc nay -> pha nhan-qua.
        time.sleep(self.delta_s)

        # --- 4. Doc state moi ---
        obs = self._observe()

        # --- 5. Trich throughput/loss tu obs de tinh reward ---
        thr = self._throughput_from_obs(obs)
        loss = self._loss_from_obs(obs)

        # --- 6. Cap nhat healthy_streak ---
        healthy_now = (thr >= self.recovery_thr) and (loss <= self.recovery_loss)
        if healthy_now:
            self._healthy_streak += 1
        else:
            self._healthy_streak = 0
        just_recovered = (self._healthy_streak == self.k_healthy)  # dat moc DUNG buoc nay

        # --- 7. Tinh reward ---
        breakdown = compute_reward(
            throughput_norm=thr, loss_norm=loss,
            action_is_noop=is_noop, just_recovered=just_recovered,
            t_step=self._t, t_max=self.t_max, cfg=self.reward_cfg)

        # --- 8. terminated vs truncated (Phan 0 — TACH RO, khong gop!) ---
        terminated = self._healthy_streak >= self.k_healthy   # thang tu nhien
        truncated = (self._t >= self.t_max) and not terminated  # het gio

        # --- 9. Tra ve + info giau de debug (KHONG cho agent hoc) ---
        info = {
            'reward_breakdown': breakdown.__dict__,
            'throughput': thr, 'loss': loss,
            'healthy_streak': self._healthy_streak,
            'action_is_noop': is_noop,
            'action_requested': cmd,
            'command_result': command_result,
            't': self._t,
        }
        return obs, breakdown.total, terminated, truncated, info

    # ==================================================================
    # Helpers noi bo
    # ==================================================================
    def _observe(self):
        things, obs_info = self.runner.observe_raw()
        vec = self.builder.build(
            things, info=obs_info,
            episode={'t': self._t, 'healthy_streak': self._healthy_streak})
        return np.asarray(vec, dtype=np.float32)

    def _throughput_from_obs(self, obs):
        # server_rx_norm:srv1 va srv2 la proxy cho throughput toi dich.
        i1 = self._dim_names.index('server_rx_norm:srv1')
        i2 = self._dim_names.index('server_rx_norm:srv2')
        return float((obs[i1] + obs[i2]) / 2.0)

    def _loss_from_obs(self, obs):
        i = self._dim_names.index('path_loss_norm:h1-srv1')
        return float(obs[i])

import numpy as np

from rl.a2.staleness import StalenessWrapper
from rl.a2.state_a2 import AOI_DIMS


class FakeAlloc:
    c_total = 20.0
    n_levels = 5
    n_actions = 3
    _level = 2
    levels = [(16.0, 4.0), (13.0, 7.0), (10.0, 10.0),
              (7.0, 13.0), (4.0, 16.0)]

    def level_norm(self):
        return self._level / (self.n_levels - 1)


class FakeEnv:
    def __init__(self):
        self.alloc = FakeAlloc()
        self.c_total = 20.0
        self.t_max = 8
        self._t = 0
        self._last_action = 0
        self._cur_demand = (16.0, 4.0)
        self.action_space = None
        self.observation_space = None

    def true_demand(self):
        return self._cur_demand

    def _info(self):
        return {
            'goodput_A': 8.0,
            'goodput_B': 6.0,
            'demand_A': self._cur_demand[0],
            'demand_B': self._cur_demand[1],
            'alloc_level_norm': self.alloc.level_norm(),
            't': self._t,
        }

    def reset(self, seed=None, options=None):
        self._t = 0
        self._cur_demand = (16.0, 4.0)
        return np.zeros(11, dtype=np.float32), self._info()

    def step(self, action):
        self._t += 1
        if self._t >= 3:
            self._cur_demand = (4.0, 16.0)
        return (
            np.zeros(11, dtype=np.float32),
            1.0,
            False,
            self._t >= self.t_max,
            self._info(),
        )


def test_z0_no_staleness():
    wrapped = StalenessWrapper(FakeEnv(), z_steps_choices=(0,))
    wrapped.reset(seed=1)
    for _ in range(5):
        _obs, _reward, _term, _trunc, info = wrapped.step(0)
        assert info['demand_A_observed'] == info['demand_A']
        assert info['aoi_measured_s'] < 0.5


def test_z2_lags_flip_by_2_steps():
    wrapped = StalenessWrapper(FakeEnv(), z_steps_choices=(2,))
    wrapped.reset(seed=1)
    seen = []
    for _ in range(6):
        _obs, _reward, _term, _trunc, info = wrapped.step(0)
        seen.append((info['t'], info['demand_A'], info['demand_A_observed']))

    row_t3 = [row for row in seen if row[0] == 3][0]
    assert row_t3[1] == 4.0
    assert row_t3[2] == 16.0

    row_t5 = [row for row in seen if row[0] == 5][0]
    assert row_t5[2] == 4.0


def test_aoi_dim_reflects_z():
    w0 = StalenessWrapper(FakeEnv(), z_steps_choices=(0,))
    w3 = StalenessWrapper(FakeEnv(), z_steps_choices=(3,))
    w0.reset(seed=1)
    w3.reset(seed=1)
    for _ in range(4):
        obs0, *_ = w0.step(0)
        obs3, *_ = w3.step(0)
    assert obs0[AOI_DIMS[0]] < obs3[AOI_DIMS[0]]
    assert obs0[AOI_DIMS[1]] == 1.0


def test_mask_zeroes_aoi_dims():
    wrapped = StalenessWrapper(
        FakeEnv(), z_steps_choices=(3,), mask_aoi_dims=True)
    obs, _info = wrapped.reset(seed=1)
    for _ in range(4):
        obs, *_ = wrapped.step(0)
    for dim in AOI_DIMS:
        assert obs[dim] == 0.0


def test_z_deterministic_by_seed():
    zs = []
    for _ in range(3):
        wrapped = StalenessWrapper(FakeEnv(), z_steps_choices=(0, 1, 2, 3, 5))
        wrapped.reset(seed=42)
        zs.append(wrapped._z_steps)
    assert len(set(zs)) == 1


def test_z_varies_across_seeds():
    wrapped = StalenessWrapper(FakeEnv(), z_steps_choices=(0, 1, 2, 3, 5))
    zs = set()
    for seed in range(40):
        wrapped.reset(seed=seed)
        zs.add(wrapped._z_steps)
    assert len(zs) >= 3


def test_reward_untouched():
    wrapped = StalenessWrapper(FakeEnv(), z_steps_choices=(5,))
    wrapped.reset(seed=1)
    _obs, reward, _term, _trunc, _info = wrapped.step(0)
    assert reward == 1.0

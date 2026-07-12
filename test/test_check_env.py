#!/usr/bin/env python3
"""Lop 1: kiem TwinEnv tuan hop dong Gym — ban rut gon cho env STOCHASTIC.

Vi sao khong dung gymnasium check_env day du?
    check_env goi check_step_determinism: reset cung seed + step cung action
    -> doi observation GIONG HET. Nhung TwinEnv doc trang thai THAT tu Mininet
    qua Ditto, co nhieu vat ly (robust_sigma ~ 0.069 Mbps). Hai lan chay cung
    seed cho obs KHAC nhau -> khong phai bug, do la ban chat emulator/twin.
    (Chinh su ngau nhien nay la doi tuong nghien cuu — tr.uc staleness D5.)

    Nen ta kiem cac tinh chat HINH THUC ma env stochastic VAN phai thoa,
    bo phan kiem tat dinh.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np


def check_contract(env, n_steps=8):
    """Kiem hop dong Gym cho env stochastic. Raise AssertionError neu sai."""
    from gymnasium import spaces

    # --- 1. Khong gian khai bao dung kieu ---
    assert isinstance(env.observation_space, spaces.Box), \
        'observation_space phai la Box'
    assert isinstance(env.action_space, spaces.Discrete), \
        'action_space phai la Discrete (DQN can roi rac)'

    # --- 2. reset() tra (obs, info) dung dang ---
    out = env.reset(seed=123)
    assert isinstance(out, tuple) and len(out) == 2, \
        'reset() phai tra (obs, info)'
    obs, info = out
    assert isinstance(info, dict), 'info phai la dict'
    _check_obs(obs, env, 'reset')

    # --- 3. Sau reset(seed), RNG cua env da duoc khoi tao ---
    assert env.unwrapped._np_random is not None, \
        'reset(seed) chua goi super().reset(seed) -> _np_random None'

    # --- 4. step() tra dung 5 gia tri, dung kieu, obs trong dai ---
    for i in range(n_steps):
        action = int(env.action_space.sample())
        out = env.step(action)
        assert len(out) == 5, 'step() phai tra 5 gia tri'
        obs, reward, terminated, truncated, sinfo = out
        _check_obs(obs, env, 'step%d' % i)
        assert isinstance(reward, (int, float)) and np.isfinite(reward), \
            'reward phai la so huu han, gap: %r' % reward
        assert isinstance(terminated, bool), 'terminated phai bool'
        assert isinstance(truncated, bool), 'truncated phai bool'
        assert isinstance(sinfo, dict), 'info phai dict'
        # khong duoc terminated VA truncated cung True
        assert not (terminated and truncated), \
            'terminated va truncated khong duoc cung True'
        if terminated or truncated:
            env.reset(seed=123 + i)   # reset de tiep tuc kiem

    # --- 5. Tinh chat rieng cua bai toan: obs khong duoc trung nhau y het
    #        giua 2 step (chung to env THUC SU doc trang thai, khong bi dong bang)
    env.reset(seed=7)
    o1, *_ = env.step(0)
    o2, *_ = env.step(0)
    assert not np.array_equal(o1, o2), \
        ('Hai step lien tiep cho obs Y HET nhau -> nghi env bi dong bang '
         '(khong doc trang thai that, hoac Delta=0). Voi env that phai co '
         'chut khac biet do nhieu.')

    print('PASS: TwinEnv tuan hop dong Gym (ban stochastic).')
    print('  - observation_space Box, action_space Discrete(%d)' % env.action_space.n)
    print('  - reset/step tra dung dang, obs trong dai, reward huu han')
    print('  - terminated/truncated tach dung, obs bien thien (env song)')


def _check_obs(obs, env, where):
    assert isinstance(obs, np.ndarray), '%s: obs phai numpy array' % where
    assert obs.shape == env.observation_space.shape, \
        '%s: obs shape sai %s != %s' % (where, obs.shape,
                                        env.observation_space.shape)
    assert np.all(np.isfinite(obs)), '%s: obs co NaN/inf' % where
    low, high = env.observation_space.low, env.observation_space.high
    assert np.all(obs >= low - 1e-6) and np.all(obs <= high + 1e-6), \
        '%s: obs vuot dai [low, high]' % where


def main():
    from mininet.env_runner import EnvRunner
    from mininet.topology_meta import load_spec
    from rl.twin_env import TwinEnv

    spec = load_spec('ditto/topology_spec.json')
    runner = EnvRunner()
    runner.start()
    try:
        env = TwinEnv(runner, spec)
        check_contract(env)
    finally:
        runner.close()


if __name__ == '__main__':
    main()
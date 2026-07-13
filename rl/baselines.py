# rl/baselines.py
"""Ba baseline doi chung cho RQ1 (Lesson 6.2).

CUNG INTERFACE voi agent: select_action(state) -> int (action index).
Nho vay eval.py cham ca 4 policy qua DUNG mot duong code -> so sanh cong bang.

    NoOpPolicy      : luon action 0. "Su co co tu het khong?"
    RandomPolicy    : uniform tren 20 action. "San cua viec lam bua."
    RuleBasedPolicy : if-else nguong, DOI THU THAT cua RQ1. Nhin state suy ra
                      action — KHONG biet scenario (khac oracle_policy).
"""

import numpy as np

from mininet.topology_meta import load_spec, baseline_bw, find_bridges
from rl.state_builder_draft import dim_names


class NoOpPolicy:
    """Luon khong lam gi (action 0)."""
    def __init__(self, action_size=20):
        self.action_size = action_size

    def select_action(self, state, epsilon=None):
        return 0


class RandomPolicy:
    """Chon ngau nhien deu tren toan bo action (mọi action hop le nho whitelist)."""
    def __init__(self, action_size=20, seed=None):
        self.action_size = action_size
        self.rng = np.random.default_rng(seed)

    def select_action(self, state, epsilon=None):
        return int(self.rng.integers(self.action_size))


class RuleBasedPolicy:
    """Luat cung cua ky su van hanh gioi nghe — DOI THU THAT cua RQ1.

    Logic (chi nhin state, khong biet scenario):
      1. Neu link nao util_avg3 > u_hi  -> bw_up dung link do (action 1+i).
      2. Neu chua, va loss cao + throughput thap -> bw_up link backbone tac
         nhat (proxy cho TrafficFlood ma oracle biet la 's2-s3').
      3. Con lai (mang khoe hoac khong ro) -> no-op.

    Cac nguong (u_hi, loss_hi, thr_lo) la "hyperparameter" cua rule-based,
    TINH CHINH tren TRAIN_SEEDS cho cong bang voi agent. Gia tri duoi la
    diem khoi dau hop ly; chot sau khi chay tren TRAIN_SEEDS.
    """

    def __init__(self, spec_path='ditto/topology_spec.json',
                 u_hi=0.85, loss_hi=0.15, thr_lo=0.80):
        spec = load_spec(spec_path)
        self.links = sorted(baseline_bw(spec, 20.0, 5.0).keys())   # thu tu canonical
        self.names = dim_names(spec)
        self.u_hi = u_hi
        self.loss_hi = loss_hi
        self.thr_lo = thr_lo
        # chi so cac chieu can doc (tinh 1 lan, tranh .index() moi buoc)
        self._util_avg3_idx = [self.names.index('util_avg3:%s' % l) for l in self.links]
        self._i_thr1 = self.names.index('server_rx_norm:srv1')
        self._i_thr2 = self.names.index('server_rx_norm:srv2')
        self._i_loss = self.names.index('path_loss_norm:h1-srv1')
        # action index: 1+i = bw_up link thu i (khop ActionSpace layout)
        self._bw_up_base = 1
        # link backbone tac nhat de noi khi flood (oracle goi y 's2-s3')
        self._i_s2s3 = self.links.index('s2-s3') if 's2-s3' in self.links else 5

    def select_action(self, state, epsilon=None):
        util = np.array([state[i] for i in self._util_avg3_idx])
        thr = (state[self._i_thr1] + state[self._i_thr2]) / 2.0
        loss = state[self._i_loss]

        # Luat 1: link nghen nhat vuot nguong -> noi chinh no
        i_max = int(np.argmax(util))
        if util[i_max] > self.u_hi:
            return self._bw_up_base + i_max            # bw_up(link i_max)

        # Luat 2: loss cao + throughput thap -> noi backbone s2-s3
        if loss > self.loss_hi and thr < self.thr_lo:
            return self._bw_up_base + self._i_s2s3     # bw_up(s2-s3)

        # Luat 3: khoe / khong ro -> khong lam gi
        return 0
# rl/diagnostics.py
"""Bo cong cu tham tu — phat hien reward hacking & benh policy (Lesson 6.4).

4 lop phat hien (Buoi 1):
  1. component_share   : ty trong 5 thanh phan reward — mat can doi?
  2. return_vs_metric  : return cao nhung throughput thap? (metric doc lap)
  3. action_distribution : 1 action >80% bat ke state? (collapse/hack)
  4. replay_scan       : chuoi action co lap vo nghia? (xem su that)

Moi ham tra ve (red_flag: bool, detail: dict). diagnose_run() gop tat ca.
"""

import numpy as np
from collections import Counter


# ---- Lop 1: ty trong thanh phan reward ----
COMPONENT_KEYS = ['throughput_term', 'loss_term', 'action_term',
                  'step_term', 'recovery_term']


def component_share(component_sums, dominate_thr=0.6):
    """Ty trong |thanh phan| tren tong |thanh phan|. Canh bao neu recovery_term
    ap dao (nghi farm bonus) hoac throughput_term qua nho.

    Args:
        component_sums : dict cong don 5 thanh phan qua ca run (tu train_log/info).
        dominate_thr   : nguong ty trong bi coi la 'ap dao'.
    """
    abs_sum = {k: abs(component_sums.get(k, 0.0)) for k in COMPONENT_KEYS}
    total = sum(abs_sum.values()) + 1e-9
    share = {k: abs_sum[k] / total for k in COMPONENT_KEYS}
    red = False
    reasons = []
    # co do 1: recovery ap dao -> nghi farm bonus
    if share['recovery_term'] > dominate_thr:
        red = True
        reasons.append('recovery_term ap dao (%.0f%%) -> nghi farm bonus'
                       % (100 * share['recovery_term']))
    # co do 2: throughput qua nho du la muc tieu chinh
    if share['throughput_term'] < 0.1:
        red = True
        reasons.append('throughput_term qua nho (%.0f%%) -> muc tieu chinh bi bo qua'
                       % (100 * share['throughput_term']))
    return red, {'share': share, 'reasons': reasons}


# ---- Lop 2: return vs metric doc lap ----
def return_vs_metric(return_mean, throughput_mean,
                     high_return_pct=70, low_thr=0.6):
    """Canh bao neu return thuoc nhom CAO nhung throughput lai THAP.
    'return & throughput phai cung ke mot cau chuyen'.

    Args (chuan hoa truoc khi goi, hoac dung nguong tho):
        return_mean     : return trung binh (da chuan hoa 0..1 hoac tho).
        throughput_mean : throughput trung binh [0,1].
    """
    red = False
    reasons = []
    # dung nguong don gian: return cao ma throughput thap = mau thuan
    if return_mean > 0 and throughput_mean < low_thr:
        # return duong (co ve tot) nhung mang khong khoe
        red = True
        reasons.append('return duong (%.2f) nhung throughput thap (%.2f) '
                       '-> return co the noi doi' % (return_mean, throughput_mean))
    return red, {'return_mean': return_mean,
                 'throughput_mean': throughput_mean, 'reasons': reasons}


# ---- Lop 3: phan bo action ----
def action_distribution(actions, noop_action=0, dominate_thr=0.8):
    """Canh bao neu 1 action KHONG-noop chiem >dominate_thr. (no-op ap dao khi
    mang khoe la BINH THUONG, nen loai no-op khoi kiem tra collapse)."""
    counter = Counter(actions)
    n = len(actions) + 1e-9
    dist = {a: c / n for a, c in counter.items()}
    red = False
    reasons = []
    for a, frac in dist.items():
        if a != noop_action and frac > dominate_thr:
            red = True
            reasons.append('action %d chiem %.0f%% (>%.0f%%) -> nghi collapse/hack'
                           % (a, 100 * frac, 100 * dominate_thr))
    return red, {'dist': dist, 'reasons': reasons}


# ---- Lop 4: quet chuoi replay tim action lap vo nghia ----
def replay_scan(action_seq, noop_action=0, oscillate_thr=0.3):
    """Tim dau hieu 'lam roi hoan tac': A roi B roi A roi B... (dao qua lai).
    Dem ti le cap (a_t != a_{t+1} nhung a_t == a_{t+2}) — dao dong 2-chu-ky."""
    if len(action_seq) < 3:
        return False, {'oscillation_rate': 0.0, 'reasons': []}
    osc = 0
    for i in range(len(action_seq) - 2):
        a0, a1, a2 = action_seq[i], action_seq[i+1], action_seq[i+2]
        if a0 != a1 and a0 == a2 and a0 != noop_action:
            osc += 1
    rate = osc / (len(action_seq) - 2)
    red = rate > oscillate_thr
    reasons = (['dao dong 2-chu-ky %.0f%% -> nghi lam-roi-hoan-tac' % (100 * rate)]
               if red else [])
    return red, {'oscillation_rate': rate, 'reasons': reasons}


# ---- Gop tat ca ----
def diagnose_run(component_sums, return_mean, throughput_mean,
                 all_actions, sample_action_seq):
    """Chay ca 4 lop, in bao cao suc khoe. Tra ve True neu CO co do nao."""
    print("=" * 56)
    print("BAO CAO CHAN DOAN PILOT (Lesson 6.4)")
    print("=" * 56)
    any_red = False
    for name, (red, detail) in [
        ('1. Ty trong reward', component_share(component_sums)),
        ('2. Return vs throughput', return_vs_metric(return_mean, throughput_mean)),
        ('3. Phan bo action', action_distribution(all_actions)),
        ('4. Quet replay', replay_scan(sample_action_seq)),
    ]:
        status = 'CO DO' if red else 'OK'
        print('[%s] %s' % (status, name))
        for r in detail.get('reasons', []):
            print('       -> ' + r)
        any_red = any_red or red
    print("-" * 56)
    print('KET LUAN: %s' % ('CO VAN DE — dieu tra truoc khi sang 6.5!'
                            if any_red else 'LANH MANH — co the sang 6.5'))
    print("=" * 56)
    return any_red
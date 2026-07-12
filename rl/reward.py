#!/usr/bin/env python3
"""RewardCalculator v2 cho TwinEnv — ham THUAN, test duoc khong can Mininet.

Reward = throughput cong don (nen) + phat cham + thuong phuc hoi som.

    r_t = w_thr * throughput_norm
        - w_loss * loss_norm
        - c_act  * (action != no-op)
        - c_step
        + R_rec(t) * (vua_phuc_hoi)

    R_rec(t) = r_rec_base * (1 - rec_lambda * t/t_max)   # som -> thuong lon hon

Trong do moi thanh phan chong mot benh:
    throughput   -> chong reward hacking "tat het link cho loss=0"
    -loss        -> phat suy hao
    -c_act       -> chong spam action thua
    -c_step      -> ap luc "dung le me"
    +R_rec(t)    -> moc dich + thuong toc do (phuc hoi som duoc nhieu hon)

Muc tieu thiet ke: nghieng ve TONG THROUGHPUT (mang khoe lau, phuc vu nhieu
lưu luong), speed_factor pha the "ngoi im tu hoi cham" gia tri ngang "sua nhanh".
"""

from dataclasses import dataclass


@dataclass
class RewardConfig:
    w_thr: float = 1.0
    w_loss: float = 1.0
    c_act: float = 0.05
    c_step: float = 0.05
    r_rec_base: float = 5.0
    rec_lambda: float = 0.5   # muc do thuong toc do; tang neu agent "luoi"


@dataclass
class RewardBreakdown:
    throughput_term: float
    loss_term: float
    action_term: float
    step_term: float
    recovery_term: float
    total: float


def compute_reward(throughput_norm, loss_norm, action_is_noop,
                   just_recovered, t_step, t_max, cfg):
    """Tinh reward MOT buoc. Ham thuan: cung input -> cung output.

    Args:
        throughput_norm : [0,1] thong luong toi dich da chuan hoa.
        loss_norm       : [0,1] ti le mat goi da chuan hoa.
        action_is_noop  : bool, action vua roi co phai no-op.
        just_recovered  : bool, buoc nay co dat moc phuc hoi.
        t_step          : so thu tu buoc hien tai (1..t_max).
        t_max           : so buoc toi da moi episode.
        cfg             : RewardConfig.
    """
    thr = cfg.w_thr * float(throughput_norm)
    loss = -cfg.w_loss * float(loss_norm)
    act = 0.0 if action_is_noop else -cfg.c_act
    step = -cfg.c_step
    if just_recovered:
        speed_factor = 1.0 - cfg.rec_lambda * (float(t_step) / float(t_max))
        rec = cfg.r_rec_base * max(speed_factor, 0.0)   # khong am du muon
    else:
        rec = 0.0
    total = thr + loss + act + step + rec
    return RewardBreakdown(thr, loss, act, step, rec, total)
#!/usr/bin/env python3
r"""Bo sinh truc tuoi cho topology_v7 -- thay sawtooth_age_steps(d=0.051).

    z(t, link) = d + alpha(link) + phase(t),   phase ~ Uniform[0, T]

Vi sao `phase ~ Uniform[0, T]` la DINH LY chu khong phai gia dinh:
    giua hai lan refresh, dz/dt = 1 (tuoi troi deu theo dong ho). Nguoi doc
    (controller, dt = 5 ms) khong dong bo voi vong sync. Vay pha theo THOI
    GIAN la deu -- khong co gi de do. Chi `T` va `d` moi can do.
    => KHONG uoc luong lai cai ma dinh luat da quy dinh; lam vay chi them nhieu.

    Kiem: pipeline dt = 5 ms, T = 500.2922 ms -> T/dt = 100.0584 (khong nguyen)
    -> pha quet gan deu. Probe 100.108 ms -> T/probe = 4.9975 -> LUOC 5 rang.

★ HAI CHE DO PHAI TACH BACH (amendment 23-47 muc 7):

    process_mode()      qua trinh THAT       -> PIPELINE dung cai nay
    instrument_mode()   qua trinh + probe khoa -> SELFCHECK dung cai nay

    Gop lam mot = nap cai luoc vao pipeline. Do la loi te nhat co the xay ra
    o Lesson 23.19, va tinh vi hon `d = 51 ms` rat nhieu: no khong lam sai
    MUC cua z ma lam sai PHAN BO cua z theo tung bin tuoi.

Tham so (Lessons 23.8 / 23.18 / 23.19):
    T     = 500.2922 ms   do BRIDGE-SIDE tu t_source ke tiep. Khong bi luoc.
    d     = 115.9 ms +/- 6.5 (95%)   qua probe -> MANG CI (L32)
    alpha = do theo link, bien do 25.95 ms, mean = 0 theo dinh nghia

Han che da biet: `d` thuc ra la bien ngau nhien LECH PHAI (skew +4.045);
mo hinh nay coi no la hang so, nen dung o momen 1 va 2, sai o momen 3
(trung vi lech 7.93 ms = 2.2% cua T). Xem L33 va amendment 23-47 muc 2-3.
"""
from __future__ import annotations

import numpy as np

# --- Tham so DO DUOC. Moi thay doi PHAI qua mot amendment. -----------------
D_SYNC_S = 0.1159             # 115.9 ms; CI95 +/- 6.5 ms (L32)
D_SYNC_CI95_S = 0.0065
SYNC_PERIOD_S = 0.5002922     # bridge-side, 8 link trai 0.0495 ms
ALPHA_S = {                   # Lesson 23.8 [A3] offset_regression
    "ac": -0.008690344772, "ad": -0.008541153302,
    "bc": -0.008559493550, "bd": -0.006720544039,
    "uA": +0.012110617257, "uB": +0.017263197251,
    "vC": -0.002681537040, "vD": +0.005819258196,
}
LINK_READ_ORDER = ("ac", "ad", "bc", "bd", "uA", "uB", "vC", "vD")

# Nhac cu do (Lesson 23.19 Task A) -- CHI dung trong instrument_mode
PROBE_INTERVAL_S = 0.1001080
PROBE_JITTER_S = 0.0000791
PROBE_READ_STEP_S = 0.004713   # 32.99 ms / 7 vi tri
CYCLES_PER_RUN = 224
RUNS_PER_CAMPAIGN = 15

# Muc tieu: CLEAN da cat 20 chu ky warm-up, n = 133.814
TARGET_MS = {"mean": 366.070, "p05": 143.612, "p50": 358.141, "p95": 582.604}

# Tham so CU, chi de lam NEGATIVE CONTROL
LEGACY_D_S = 0.051
LEGACY_T_S = 0.5


class AoIModelV7:
    def __init__(self, d_s: float = D_SYNC_S, T_s: float = SYNC_PERIOD_S,
                 alpha_s: dict | None = None, profile: str = "U3",
                 d_samples_s: np.ndarray | None = None):
        """profile: U0 = tuoi dong nhat (alpha = 0) | U3 = alpha DO DUOC.

        d_samples_s: MUC 2 (tuy chon). Neu truyen vao, `d` duoc lay mau tu
        phan bo thuc nghiem thay vi la hang so -- vi `d_transport` that ra
        LECH PHAI (skew +4.045, amendment 23-47 muc 2). CHI dung de kiem do
        nhay: hinh dang duoi khong dang tin (L33), chi SU TON TAI la chac.
        """
        self.d = float(d_s)
        self.d_samples = (None if d_samples_s is None
                          else np.asarray(d_samples_s, float))
        self.T = float(T_s)
        self.alpha = ({k: 0.0 for k in ALPHA_S} if profile == "U0"
                      else dict(alpha_s or ALPHA_S))
        self.profile = profile

    # ---------------------------------------------------------------- (1)
    def process_mode(self, n: int, dt: float, link: str,
                     phase0: float = 0.0) -> np.ndarray:
        """Tuoi THAT theo thoi gian. PIPELINE dung ham nay.

        `phase0` CHUNG cho ca 8 link, khong phai 8 vong sync doc lap: trong
        he that MOT vong sync phuc vu ca 8 link. Sinh 8 pha doc lap tao ra
        mot he KHONG TON TAI va lam sai tuong quan giua cac link trong
        margin m = cost(a2) - cost(a1). Day la anh em cua loi S13.
        """
        t = np.arange(n, dtype=float) * dt
        return self._d_of(len(t)) + self.alpha[link] + np.mod(t + phase0, self.T)

    def age_steps(self, n: int, dt: float, link: str,
                  phase0: float = 0.0) -> np.ndarray:
        """Tuoi theo BUOC nguyen -- cung chu ky voi sawtooth_age_steps()."""
        return np.round(self.process_mode(n, dt, link, phase0) / dt).astype(int)

    # ---------------------------------------------------------------- (2)
    def instrument_mode(self, rng: np.random.Generator,
                        n_runs: int = RUNS_PER_CAMPAIGN) -> np.ndarray:
        """Qua trinh QUAN SAT QUA PROBE khoa. SELFCHECK dung ham nay.

        Tai lap dung nhac cu cua chien dich 23.8:
          - probe moi PROBE_INTERVAL_S, jitter sd PROBE_JITTER_S
          - 8 link doc TUAN TU trong mot luot, cach nhau PROBE_READ_STEP_S
          - luan phien fwd/rev theo chi so luot
          - pha ban dau moi run NGAU NHIEN (an so that cua chien dich)
        """
        n_probe = int(CYCLES_PER_RUN * self.T / PROBE_INTERVAL_S)
        out = []
        for _ in range(n_runs):
            phi0 = rng.random() * self.T
            t_probe = np.cumsum(
                PROBE_INTERVAL_S + rng.normal(0.0, PROBE_JITTER_S, n_probe))
            even = (np.arange(n_probe) % 2 == 0)
            for j, link in enumerate(LINK_READ_ORDER):
                off = np.where(even, j, 7 - j) * PROBE_READ_STEP_S
                t = t_probe + off
                out.append(self._d_of(t.size, rng) + self.alpha[link]
                           + np.mod(phi0 + t, self.T))
        return np.concatenate(out)

    def _d_of(self, n: int, rng: np.random.Generator | None = None):
        """`d` hang so (muc 1) hoac lay mau tu phan bo thuc nghiem (muc 2)."""
        if self.d_samples is None:
            return self.d
        r = rng if rng is not None else np.random.default_rng(0)
        return r.choice(self.d_samples, size=n, replace=True)

    # ---------------------------------------------------------------- (3)
    @staticmethod
    def _stats_ms(z_s: np.ndarray) -> dict:
        z = z_s * 1000.0
        return {"mean": float(z.mean()),
                "p05": float(np.percentile(z, 5)),
                "p50": float(np.percentile(z, 50)),
                "p95": float(np.percentile(z, 95))}

    def selfcheck(self, n_campaigns: int = 400, seed: int = 2319,
                  mode: str = "instrument") -> dict:
        """★ POSITIVE CONTROL -- so theo DAI TIEN DOAN, khong theo diem.

        Pha ban dau cua 15 run la AN SO. Mot chien dich mo phong se khong
        trung rang voi chien dich quan sat, nen doi khop DIEM la doi khop
        mot thu ngau nhien. Cach dung: mo phong N chien dich, lay dai
        5-95% cua tung thong ke, va hoi thong ke QUAN SAT co roi vao khong.

        mode="instrument" -> qua probe khoa (DUNG)
        mode="process"    -> qua trinh tho (SAI; dung cho doi chung duong)
        """
        rng = np.random.default_rng(seed)
        rows = []
        for _ in range(n_campaigns):
            if mode == "instrument":
                z = self.instrument_mode(rng)
            else:
                # cung co mau, nhung lay mau LY TUONG (khong qua probe)
                n = int(CYCLES_PER_RUN * self.T / PROBE_INTERVAL_S) * 8 * RUNS_PER_CAMPAIGN
                z = np.concatenate([
                    self._d_of(n // 8, rng) + self.alpha[l]
                    + rng.random(n // 8) * self.T
                    for l in LINK_READ_ORDER])
            rows.append(self._stats_ms(z))
        band, inside = {}, {}
        for k in TARGET_MS:
            v = np.array([r[k] for r in rows])
            lo, hi = np.percentile(v, [5, 95])
            band[k] = {"lo": float(lo), "hi": float(hi),
                       "sd": float(v.std(ddof=1)), "median": float(np.median(v))}
            inside[k] = bool(lo <= TARGET_MS[k] <= hi)
        return {"mode": mode, "profile": self.profile,
                "n_campaigns": n_campaigns,
                "d_ms": self.d * 1000, "T_ms": self.T * 1000,
                "band_ms": band, "observed_ms": TARGET_MS,
                "inside": inside,
                "n_inside": int(sum(inside.values())),
                "pass": all(inside.values())}

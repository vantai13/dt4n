#!/usr/bin/env python3
"""Lesson 1: kiem chung luat f(1-f) bang mo phong thuan tuy, khong can mang.

Bon thi nghiem:
  E1  In ra day dN that su -> thay no chi co HAI gia tri.
  E2  Quet f tu 0 den 1 -> so Var(dN) mo phong voi f(1-f) va voi 1/6.
  E3  Cho jitter vao thoi diem lay mau -> xem luat GAY o dau, va vi sao
      1/6 tro lai dung khi jitter >> khoang cach goi.
  E4  Ap luat len 8 link that cua topology_v7.
"""
from __future__ import annotations

import numpy as np

from tools.g_quant_null import (
    WIRE_BYTES_DEFAULT,
    frac,
    rate_for_integer_window,
    rate_pps,
    var_dn_deterministic,
    var_rho_pack,
)

CAP = {
    "uA": 8.0,
    "uB": 6.0,
    "ac": 6.0,
    "ad": 4.0,
    "bc": 6.0,
    "bd": 6.0,
    "vC": 8.0,
    "vD": 6.0,
}  # Mbps, twin/topology_v7.py


def count_per_window(
    rate: float,
    dt: float,
    n_win: int,
    phase0: float = 0.0,
    jitter_s: float = 0.0,
    seed: int = 0,
) -> np.ndarray:
    """Mo phong CHINH XAC bo phat + sampler cua ban.

    N(t) = floor((t - t0)*r)   <- static_emitter.py
    T_k  = T_0 + k*dt + e_k    <- RhoLogger, e_k la jitter cua thoi diem doc
    """
    rng = np.random.default_rng(seed)
    k = np.arange(n_win + 1, dtype=float)
    t = phase0 / rate + k * dt
    if jitter_s > 0.0:
        t = t + rng.normal(0.0, jitter_s, size=t.shape)
        t = np.maximum.accumulate(t)
    n_cum = np.floor(t * rate)
    return np.diff(n_cum)


def simulate_window(
    rate: float,
    dt: float,
    cap_bps: float,
    n_win: int,
    phase0: float = 0.137,
    jitter_s: float = 0.0,
    seed: int = 7,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Mo phong DAY DU chuoi xu ly cua RhoLogger.

    Khac ban E3 cu: tra ve rho tinh bang dt THUC DO, dung nhu
    run_sync_v7.py::RhoLogger:

        dt  = sample_t - prev_t
        rho = tx_bytes_delta * 8 / dt / C

    Bo qua buoc chia nay se do Var(dN) thay vi Var(rho). Var(dN) nhay
    theo do dai cua so, trong khi phep chuan hoa cua rho triet tieu anh
    huong do o bac nhat.
    """
    rng = np.random.default_rng(seed)
    k = np.arange(n_win + 1, dtype=float)
    t = phase0 / rate + k * dt
    if jitter_s > 0.0:
        t = t + rng.normal(0.0, jitter_s, size=t.shape)
        t = np.maximum.accumulate(t)
    d_n = np.diff(np.floor(t * rate))
    d_t = np.diff(t)
    good = d_t > 0.0
    d_n, d_t = d_n[good], d_t[good]
    rho = d_n * wire_bytes * 8.0 / (d_t * cap_bps)
    return d_n, d_t, rho


def e1_show_sequence() -> None:
    print("=" * 74)
    print("E1 | Day dN that su trong (chi co HAI gia tri)")
    print("=" * 74)
    for label, rate, dt in [
        ("uA that (r=563.93, dt=0.2)", 563.9285714285714, 0.20),
        ("f=0.5 chinh xac", 562.5, 0.20),
        ("f=0.0 chinh xac (locked)", 560.0, 0.20),
    ]:
        dn = count_per_window(rate, dt, 24)
        n = rate * dt
        print("\n%-30s n=%9.4f  f=%.4f" % (label, n, frac(n)))
        print("   dN =", " ".join("%d" % v for v in dn))
        print("   gia tri xuat hien : %s" % sorted(set(int(v) for v in dn)))
        print(
            "   Var(dN) mo phong  : %.6f      f(1-f) = %.6f"
            % (np.var(dn), var_dn_deterministic(rate, dt))
        )


def e2_sweep_f() -> None:
    print("\n" + "=" * 74)
    print("E2 | Quet f: mo phong vs f(1-f) vs 1/6      (n_win = 200000)")
    print("=" * 74)
    print(
        "%8s %12s %12s %12s %10s %10s"
        % ("f", "Var mo phong", "f(1-f)", "1/6", "err det", "err 1/6")
    )
    dt, base = 0.20, 560.0
    for f in [0.0, 0.02, 0.1, 0.25, 0.446, 0.5, 0.732, 0.786, 0.911, 0.982, 0.999]:
        rate = base + f / dt
        dn = count_per_window(rate, dt, 200_000, phase0=0.137)
        v_sim, v_det, v_uni = float(np.var(dn)), f * (1 - f), 1.0 / 6.0
        e_det = abs(v_sim - v_det) / v_det if v_det > 0 else abs(v_sim)
        print(
            "%8.3f %12.6f %12.6f %12.6f %9.2f%% %9.1f%%"
            % (
                f,
                v_sim,
                v_det,
                v_uni,
                100 * e_det,
                100 * abs(v_sim - v_uni) / v_uni,
            )
        )


def e3_jitter() -> None:
    """Do chuyen che do jitter tren Var(rho), khong phai Var(dN)."""
    print("\n" + "=" * 78)
    print("E3 | Jitter pha huy luat tat dinh khi nao?  (do tren Var(rho))")
    print("=" * 78)
    for label, rate, cap_mbps in [
        ("bd-like  f=0.982  ->  f(1-f) NHO hon 1/6", 489.9107142857143, 6.0),
        ("f=0.500           ->  f(1-f) LON hon 1/6", 562.5, 8.0),
    ]:
        cap = cap_mbps * 1e6
        n = rate * 0.20
        f = frac(n)
        rho_bar = rate * WIRE_BYTES_DEFAULT * 8.0 / cap
        scale = n**2 / rho_bar**2
        gap_ms = 1000.0 / rate
        print("\n### %s" % label)
        print(
            "    n=%.4f  f=%.4f  f(1-f)=%.5f   1/6=%.5f   gap=%.3f ms"
            % (n, f, f * (1 - f), 1 / 6, gap_ms)
        )
        print(
            "    %9s %8s | %12s %9s %9s"
            % ("jitter", "j/gap", "Var(rho)eq", "/f(1-f)", "/(1/6)")
        )
        for j_ms in [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2, 2.0, 5.0]:
            _, _, rho = simulate_window(
                rate, 0.20, cap, 300_000, jitter_s=j_ms / 1000.0
            )
            v = float(np.var(rho)) * scale
            print(
                "    %7.2f ms %8.3f | %12.5f %9.2f %9.2f"
                % (j_ms, j_ms / gap_ms, v, v / (f * (1 - f)), v / (1 / 6))
            )


def e4_real_links() -> None:
    print("\n" + "=" * 74)
    print("E4 | Ap luat len 8 link that (rho_bar = 0.857 tren DAY)")
    print("=" * 74)
    print(
        "%5s %7s %10s %10s %7s %11s %11s %8s"
        % (
            "link",
            "C Mbps",
            "r pps",
            "n=r*dt",
            "f",
            "v_pack det",
            "v_pack 1/6",
            "ti so",
        )
    )
    for link, cap_mbps in CAP.items():
        cap = cap_mbps * 1e6
        r = rate_pps(cap, 0.857)
        n = r * 0.20
        vd = var_rho_pack(r, 0.20, cap, model="deterministic")
        vu = var_rho_pack(r, 0.20, cap, model="random_phase")
        print(
            "%5s %7.1f %10.2f %10.4f %7.4f %11.4e %11.4e %8.2f"
            % (link, cap_mbps, r, n, frac(n), vd, vu, vu / vd)
        )

    print("\n--- O NULL: khoa toc do sao cho f = 0 (thiet ke v4) ---")
    print(
        "%5s %10s %10s %10s %9s %14s"
        % ("link", "r goc", "r khoa", "n nguyen", "rho thuc", "v_pack sau khoa")
    )
    for link, cap_mbps in CAP.items():
        cap = cap_mbps * 1e6
        r0 = rate_pps(cap, 0.857)
        r1, rho1, n_int = rate_for_integer_window(cap, 0.857, 0.20)
        v1 = var_rho_pack(r1, 0.20, cap)
        print(
            "%5s %10.2f %10.2f %10d %9.4f %14.3e"
            % (link, r0, r1, n_int, rho1, v1)
        )


if __name__ == "__main__":
    e1_show_sequence()
    e2_sweep_f()
    e3_jitter()
    e4_real_links()

#!/usr/bin/env python3
"""Null luong tu hoa goi cho bo phat CBR tat dinh (Phase G, Lesson 1).

Bo phat trong mininet/static_emitter.py gui goi thu k tai deadline tuyet doi
t0 + k/r, nen so goi tich luy la mot ham bac thang tat dinh:

    N(t) = floor((t - t0) * r)

Voi luoi lay mau deu buoc dt, so goi moi cua so chi nhan hai gia tri:

    dN_k = m + Bernoulli(f),   n = r*dt = m + f

=> Var(dN) = f*(1-f)                        [KHONG phai 1/6]
=> Var(rho) = rho_bar^2 * f*(1-f) / n^2

Hang so 1/6 la trung binh cua f(1-f) tren pha ngau nhien:
    integral_0^1 f(1-f) df = 1/6
No chi dung khi pha lay mau ngau nhien (jitter >> 1/r), khong dung cho
pacer tat dinh voi sampler on dinh.
"""
from __future__ import annotations

import math

# Ethernet 14 + IPv4 20 + UDP 8 + payload 1400. Kiem toan tich luy trong
# NC-G1-static v3 do duoc 1441.92-1442.12 byte/goi tren ca 8 link.
WIRE_BYTES_DEFAULT = 1442.0


def frac(x: float) -> float:
    """Phan thap phan, luon nam trong [0, 1)."""
    return float(x) - math.floor(float(x))


def rate_pps(
    cap_bps: float,
    rho_bar: float,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
) -> float:
    """Toc do goi de dat rho_bar TREN DAY (khong phai tren payload).

    Luu y G-A008/N6: static_emitter.py hien chia cho payload_bytes (1400),
    nen rho tren day bi vuot 1442/1400 = 1.0300. Ham nay la dinh nghia dung.
    """
    return float(cap_bps) * float(rho_bar) / (float(wire_bytes) * 8.0)


def n_per_window(rate: float, dt_s: float) -> float:
    """So goi trung binh moi cua so do."""
    return float(rate) * float(dt_s)


def var_dn_deterministic(rate: float, dt_s: float) -> float:
    """Var(dN) cho pacer tat dinh: f*(1-f)."""
    f = frac(n_per_window(rate, dt_s))
    return f * (1.0 - f)


def var_dn_random_phase() -> float:
    """Var(dN) khi pha lay mau ngau nhien: 1/6. Chi de doi chung."""
    return 1.0 / 6.0


def var_rho_pack(
    rate: float,
    dt_s: float,
    cap_bps: float,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
    model: str = "deterministic",
) -> float:
    """San luong tu hoa cua Var(rho_measured), don vi rho^2.

    model = 'deterministic' -> f(1-f)   (dung cho NC-G1-static)
    model = 'random_phase'  -> 1/6      (doi chung, mo hinh cu)
    """
    n = n_per_window(rate, dt_s)
    if n <= 0.0:
        return float("inf")
    rho_bar = float(rate) * float(wire_bytes) * 8.0 / float(cap_bps)
    if model == "deterministic":
        var_dn = var_dn_deterministic(rate, dt_s)
    elif model == "random_phase":
        var_dn = var_dn_random_phase()
    else:
        raise ValueError("model must be 'deterministic' or 'random_phase'")
    return rho_bar**2 * var_dn / n**2


def signal_fraction(
    sigma: float,
    rate: float,
    dt_s: float,
    cap_bps: float,
    v_path: float = 0.0,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
) -> float:
    """sf = sigma^2 / (sigma^2 + v_pack + v_path).

    Day la dai luong quyet dinh cua G.1: sf < 0.85 nghia la khong the
    tin tau/omega uoc luong tu chuoi rho_measured tai cell do.
    """
    v_pack = var_rho_pack(rate, dt_s, cap_bps, wire_bytes)
    total = float(sigma) ** 2 + v_pack + float(v_path)
    return float(sigma) ** 2 / total if total > 0 else float("nan")


def rate_for_integer_window(
    cap_bps: float,
    rho_target: float,
    dt_s: float,
    wire_bytes: float = WIRE_BYTES_DEFAULT,
) -> tuple[float, float, int]:
    """Chon toc do 'commensurate': r*dt la SO NGUYEN => f = 0 => v_pack = 0.

    Tra ve (rate_locked, rho_thuc_te, n_nguyen). Day la nen mong cua o NULL
    trong thiet ke v4: khi f = 0, moi cua so chua dung n goi, nen bat ky
    bien thien nao con lai deu la v_path do truc tiep.
    """
    r_raw = rate_pps(cap_bps, rho_target, wire_bytes)
    n_int = max(1, int(round(r_raw * float(dt_s))))
    r_locked = n_int / float(dt_s)
    rho_actual = r_locked * float(wire_bytes) * 8.0 / float(cap_bps)
    return r_locked, rho_actual, n_int

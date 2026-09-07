"""V-T2-2 MOI: so tau_hat voi KY VONG HUU HAN MAU, khong voi thiet ke.

Nguyen tac T-G2 cua Phase T: so sanh dung la voi KY VONG DUOI CUA SO HUU
HAN, khong voi gia tri thiet ke tho.

DO DUOC o T2.2 (MC tren AR(1) thuan, trung binh 8 link, reps=60):

    cycles = T_sim/tau     E[tau_hat]/tau     sd cua MOT lan rut (1 link)
        1000                   0.9971                 4.6%
         200                   0.9878                 9.9%
          50                   0.9400                18.5%

Hai dieu phai doc cho dung:

  1. Do chech THAT nho hon nhieu so voi mot lan rut don le goi y. Mot chuoi
     1 link o tau=28 cho tau_hat/tau = 0.81, nhung KY VONG la 0.94 -- phan
     con lai la NHIEU LAY MAU, khong phai chech. Nham hai thu nay se dan
     den "sua" mot bo sinh von dang dung.

  2. Do chech theo T_sim/tau (so chu ky doc lap), KHONG theo tau. Giu cycles
     co dinh thi tau doi 5 lan cung cho cung mot ti so (test ben duoi).

He qua thiet ke: muon do chech hang so thi phai cho n ~ tau khong san, tuc
28x compute o tau=28. Dung tra gia do. Sua GATE, dung sua ngan sach.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy.signal import lfilter

from measurements import sla_calib_v2 as S

DT = 0.005
SIGMA_925 = 0.0218
N_LINKS = 8


def tau_hat_lag1(x: np.ndarray, dt: float) -> float:
    x = np.asarray(x, dtype=float)
    x = x - x.mean()
    r1 = float((x[1:] * x[:-1]).sum() / (x * x).sum())
    return -dt / math.log(r1) if 0.0 < r1 < 1.0 else float("nan")


def _pure_ar1(rng, phi: float, n: int) -> np.ndarray:
    """AR(1) THUAN, phuong sai dung 1: khong offset, khong kep, khong twin."""
    e = rng.standard_normal(int(n)) * math.sqrt(1.0 - phi * phi)
    e[0] = rng.standard_normal()          # khoi tao dung phan phoi dung
    return lfilter([1.0], [1.0, -phi], e)


def expected_tau_hat(tau: float, n: int, dt: float, reps: int = 24,
                     links: int = N_LINKS, seed: int = 9_000) -> tuple[float, float]:
    """Ky vong va do tan cua tau_hat DUOI CUNG mot cua so huu han.

    Uoc luong tren AR(1) thuan de tach do chech CUA UOC LUONG khoi do chech
    CUA BO SINH: neu tron hai thu, mot gate FAIL khong quy trach nhiem duoc.

    ``n`` va ``links`` phai TRUNG voi luc do, vi do chech phu thuoc T_sim/tau
    va do tan phu thuoc so link duoc trung binh.
    """
    rng = np.random.default_rng(seed)
    phi = math.exp(-dt / float(tau))
    out = [float(np.mean([tau_hat_lag1(_pure_ar1(rng, phi, n), dt)
                          for _ in range(int(links))]))
           for _ in range(int(reps))]
    arr = np.asarray(out, dtype=float)
    return float(arr.mean()), float(arr.std())


def generator_tau_hat(tau: float, n: int) -> float:
    """tau_hat cua bo sinh that, trung binh tren ca 8 link."""
    rho = S.ar1_matrix("poisson", 0.925, SIGMA_925,
                       tau=tau, dt=DT, n=n, seed=101)
    return float(np.mean([tau_hat_lag1(rho[:, i], DT)
                          for i in range(rho.shape[1])]))


@pytest.mark.parametrize("tau", [1.0, 5.0, 28.0])
def test_generator_matches_finite_window_expectation(tau):
    """V-T2-2: bo sinh phai nam trong 3 sigma cua ky vong huu han mau."""
    n = S.n_for_tau(tau, DT)
    exp_mu, exp_sd = expected_tau_hat(tau, n, DT)
    got = generator_tau_hat(tau, n)
    z = abs(got - exp_mu) / exp_sd
    assert z < 3.0, (tau, got, exp_mu, exp_sd, z)


def test_comparing_to_the_design_value_would_misjudge_the_generator():
    """Doi chung: gate CU so voi tau THIET KE danh gia sai bo sinh.

    O tau=28 (50 chu ky), ky vong da la 0.94*tau -- lech 6% ngay ca khi bo
    sinh hoan hao. Mot chuoi don le con lech toi ~19%. Gate cu do lan hai
    nguon do lech nay vao nhau.
    """
    tau, n = 28.0, S.n_for_tau(28.0, DT)
    exp_mu, exp_sd = expected_tau_hat(tau, n, DT)
    # ky vong TU NO da lech khoi thiet ke: khong the la tieu chi dung/sai
    assert (tau - exp_mu) / tau > 0.03
    # mot chuoi DON LE tan hon trung binh 8 link dung he so sqrt(8) ~ 2.83
    # (8 link la 8 lan rut doc lap). Chinh do tan nay -- khong phai do chech
    # -- moi la thu day mot chuoi don le ra 0.81*tau.
    _mu1, sd1 = expected_tau_hat(tau, n, DT, reps=24, links=1, seed=4242)
    assert 2.0 < sd1 / exp_sd < 4.0, (sd1, exp_sd, sd1 / exp_sd)


@pytest.mark.parametrize("cycles", [200, 50])
def test_bias_tracks_cycles_not_tau(cycles):
    """Do chech theo T_sim/tau. Giu cycles co dinh, tau doi 5 lan -> khong doi."""
    ratios = {}
    for tau in (1.0, 5.0):
        n = int(round(float(cycles) * tau / DT))
        mu, _sd = expected_tau_hat(tau, n, DT, reps=24)
        ratios[tau] = mu / tau
    assert abs(ratios[1.0] - ratios[5.0]) < 0.02, (cycles, ratios)


def test_n_for_tau_keeps_cycles_at_the_budget_floor():
    """n_for_tau giu T_sim/tau >= 50 -- chinh la cot 'cycles' o tren."""
    for tau in (1.0, 5.0, 20.0, 28.0):
        n = S.n_for_tau(tau, DT)
        assert (n * DT) / tau >= 50.0

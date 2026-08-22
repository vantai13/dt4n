#!/usr/bin/env python3
"""Freeze bit-exact provenance for the Phase L / Phase T schedule generator.

The digests below were extracted from the Phase L campaign
(`results/RAW/phase-L/raw/*_tx.meta.json`) using the interpreter that ran the live
campaign. They are the contract between Phase L and Phase T.

IF THIS TEST FAILS, check in this order; do not edit the reference digests:
  1. ENVIRONMENT: python3 -VV, which python3
  2. INPUTS: bw, probe_pps, n_bg, seed
  3. CODE: git log --oneline -- mininet/load_spec.py
  4. Only then ask whether the reference digest is wrong.

See docs/phase-T/00m-amendment-12.md.
"""

import random

import pytest

from mininet.load_spec import background_pps, build_schedule, normalize_rate, schedule_digest


BW = 6.0
PROBE_PPS = 20.0


# (mode, rho, seed, n_bg, digest_bg)
#
# The trailing comments record the observed ULP delta in the normalization
# factor between explicit sequential summation (CPython <= 3.11 behavior) and
# Neumaier-compensated float sum() (CPython >= 3.12). Samples with |ULP| > 0
# have teeth: they distinguish the two interpreters. ULP=0 samples still lock
# code branches, but do not lock the summation behavior.
FROZEN_PHASE_L = [
    (
        "poisson",
        1.050,
        15,
        36360,
        "58648632e63d2531c9027c4a22291fb4438c02bd0b9418e85cf643f844c61301",
    ),  # +55 ULP: has teeth
    (
        "poisson",
        0.600,
        12,
        20735,
        "09d8dee872d0a672bc3128f3d2330df305c5dfc5d698e5b2da4427d0af52e6f9",
    ),  # 0 ULP: locks poisson branch only
    (
        "h2",
        0.600,
        14,
        20735,
        "26cd7dcd0a51b5da8bcd89568c282c586c9264b1a8589de977077c893d76d306",
    ),  # -9 ULP: has teeth
    (
        "h2",
        0.500,
        15,
        17262,
        "c80d539a16dab8966f972b09433f83223f0ff47a0c5fef574c1024a1ac8eac89",
    ),  # +29 ULP: has teeth
    (
        "onoff",
        0.600,
        15,
        20735,
        "ad6713b08f641f3e92dcc401abf0702ed390623457f0d2d7f5d89760620296b7",
    ),  # 0 ULP: locks onoff branch only
    (
        "cbr",
        0.950,
        11,
        32887,
        "6c0dffbfbe403203e6eabe1ca6adb1de34e929273802aa4fa809afc1e6930063",
    ),  # n/a: cbr returns before normalize_rate
]


@pytest.mark.parametrize("mode,rho,seed,n_bg,want", FROZEN_PHASE_L)
def test_phase_l_schedule_digest_bit_exact(mode, rho, seed, n_bg, want):
    pps = background_pps(rho, BW, PROBE_PPS)
    got = schedule_digest(build_schedule(mode, n_bg, 1.0 / pps, seed))
    assert got == want, (
        "Digest lech -> KHONG duoc sua digest tham chieu. "
        "Chay checklist trong docstring dau file."
    )


def test_normalize_rate_khong_phu_thuoc_sum_dung_san():
    """Catch the root cause directly, with an easy-to-read failure.

    Python >= 3.12 changed float ``sum()`` to compensated summation.
    ``normalize_rate`` must use explicit summation in this repo, not builtin
    ``sum()``, because tiny ULP-scale changes alter the schedule digest.
    """
    rng = random.Random(7)
    gaps = [rng.expovariate(500.0) for _ in range(30000)]

    naive = 0.0
    for gap in gaps:
        naive = naive + gap
    k_naive = (1.0 / 500.0) / (naive / len(gaps))

    assert normalize_rate(gaps, 1.0 / 500.0)[0] == gaps[0] * k_naive

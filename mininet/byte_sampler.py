"""Read byte counters for ALL links in ONE pass over /proc/net/dev.

Three design points:

  1. One read covers every interface, so all links share a single timestamp
     and the sampler introduces no phase offset between links of its own.
     `G-L37` and `G-L41` record what happens when that is not true.
  2. Normalisation uses the REAL elapsed time between reads, not the nominal
     `dt`. If the sampler is late by `delta`, both the byte delta and the time
     delta grow together and the ratio stays correct to first order.
  3. The sampler records its own `delta_w`, exactly as the controller does.

⚠️ Counting bytes does NOT lower the quantisation floor: the counter advances
   by WHOLE FRAMES, so the step is the same whether frames or bytes are
   counted. `sigma_qfloor = (8L/(C*dt))/sqrt(12)`; see `G-L43`. Bytes are used
   because rho is a ratio of BYTE rates, so bytes measure the right quantity.
"""
from __future__ import annotations

import time

import numpy as np

TX_BYTES_FIELD = 8   # /proc/net/dev columns after the colon: rx has 8, then tx


def read_counters(ifaces) -> dict:
    """Return {ifname: tx_bytes} from a single pass over /proc/net/dev."""
    wanted = set(ifaces)
    out = {}
    with open("/proc/net/dev", "r") as handle:
        for line in handle:
            if ":" not in line:
                continue
            name, rest = line.split(":", 1)
            name = name.strip()
            if name in wanted:
                out[name] = int(rest.split()[TX_BYTES_FIELD])
    return out


def sample(ifaces, n_windows: int, dt: float, cap_bps):
    """Sample `n_windows` windows; return (rho[n_windows, n_links], lateness)."""
    n_link = len(ifaces)
    rho = np.empty((n_windows, n_link))
    lateness = np.empty(n_windows)
    read_span = np.empty(n_windows)

    t0 = time.perf_counter()
    prev_counts = read_counters(ifaces)
    prev_t = time.perf_counter()

    for k in range(n_windows):
        target = t0 + (k + 1) * dt
        now = time.perf_counter()
        if now < target:
            time.sleep(target - now)
        before = time.perf_counter()
        counts = read_counters(ifaces)
        after = time.perf_counter()

        mid = 0.5 * (before + after)
        elapsed = mid - prev_t
        lateness[k] = before - target
        read_span[k] = after - before
        for i, name in enumerate(ifaces):
            rho[k, i] = ((counts[name] - prev_counts[name]) * 8.0
                         / (elapsed * cap_bps[i]))
        prev_counts, prev_t = counts, mid

    return rho, lateness, read_span

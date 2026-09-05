#!/usr/bin/env python3
"""Set the HTB rate of every link once per window, from ONE long-lived process.

Cost of setting 8 rates per 100 ms window:

    subprocess `tc` x8            ~3 ms x8 = 24 ms   24 percent of the window
    one `tc -batch` per window    ~4 ms              4 percent
    ONE long-lived `tc -batch`    ~0.3 ms            0.3 percent   <- this

fork+exec is not merely slow, it has a heavy tail (page faults, cold cache),
and the tail is what `E[delta^2]` is made of.

★ `delta_w` is recorded for every window. It is not a debug log: it is the
  measured INPUT to the model test of `docs/phase-G/58` section 5, where
  `v_predicted = 2*E[delta^2]/(dt*tau) * sigma^2` is compared against the
  nugget actually observed.
"""
from __future__ import annotations

import subprocess
import time

import numpy as np


class TcBatchWriter:
    """One `tc -force -batch -` process, fed through stdin for its lifetime.

    ⚠️ `flush()` after every write is mandatory. Without it the commands sit in
    Python's buffer, `delta` looks excellent, and the rates land late or not at
    all. That failure is SILENT, which is why `KILL-4` measures the achieved
    rate at the sink through an independent counter.
    """

    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            ["stdbuf", "-o0", "-e0", "tc", "-force", "-batch", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def set_rates(self, specs) -> None:
        """specs: iterable of (ifname, classid, rate_kbit, burst_bytes)."""
        self.proc.stdin.write("".join(
            f"class change dev {ifn} parent 1: classid {cid} htb "
            f"rate {rate}kbit ceil {rate}kbit burst {burst}b cburst {burst}b\n"
            for ifn, cid, rate, burst in specs
        ))
        self.proc.stdin.flush()

    def close(self) -> str:
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
        return (self.proc.stderr.read() or "") if self.proc.stderr else ""


def drive(rho_series: np.ndarray, ifaces, cap_bps, burst_bytes: int,
          dt: float, classid: str = "1:10") -> dict:
    """Drive the shaper for `rho_series.shape[0]` windows and return delta stats.

    `rho_series` has shape (n_windows, n_links).
    """
    writer = TcBatchWriter()
    n_win, n_link = rho_series.shape
    lateness = np.empty(n_win)
    t0 = time.perf_counter()
    for k in range(n_win):
        target = t0 + k * dt
        now = time.perf_counter()
        if now < target:
            time.sleep(target - now)
        lateness[k] = time.perf_counter() - target
        writer.set_rates([
            (ifaces[i], classid,
             max(8, int(round(rho_series[k, i] * cap_bps[i] / 1000.0))),
             burst_bytes)
            for i in range(n_link)
        ])
    stderr = writer.close()
    return {
        "delta_mean_s": float(lateness.mean()),
        "delta_p50_s": float(np.percentile(lateness, 50)),
        "delta_p95_s": float(np.percentile(lateness, 95)),
        "delta_p99_s": float(np.percentile(lateness, 99)),
        "delta_max_s": float(lateness.max()),
        "delta_rms_s": float(np.sqrt((lateness ** 2).mean())),
        "n_windows": int(n_win),
        "dt_s": float(dt),
        "tc_stderr_head": stderr[:400],
        "tc_stderr_empty": not stderr.strip(),
    }

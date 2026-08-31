#!/usr/bin/env python3
"""Lesson 1 phu luc - phap y 5 buoc tren RAW DA CO, khong chay mang.

Muc dich: xac dinh nguon cua phan du (v_measured - v_pack) sau khi mo hinh
jitter chung MOT tham so bi bac bo boi cap uA/vC.

Chay:
  python -m tools.g_lesson1_forensics \
      --run results/RAW/phase-G/g1-static-v3-smoke/D/rep1
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

LINKS = ("uA", "uB", "ac", "ad", "bc", "bd", "vC", "vD")
WIRE = 1442.0
BURN_S = 20.0


def frac(x: float) -> float:
    return float(x) - math.floor(float(x))


def load(run: Path):
    meta = json.loads((run / "rho_trace_meta.json").read_text(encoding="utf-8"))
    measured = pd.read_csv(run / "rho_measured.csv")
    return meta, measured


def post_burn(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    result = frame.sort_values("monotonic_s").reset_index(drop=True)
    start = float(result["monotonic_s"].iloc[0]) + BURN_S
    return result[result["monotonic_s"] >= start].reset_index(drop=True)


def t1_byte_purity(meta, measured: pd.DataFrame, run: Path) -> None:
    """T1 | Kiem tra tx_bytes_delta co la boi so chinh xac cua 1442."""
    print("\n" + "=" * 76)
    print("T1 | Do tinh khiet byte:  tx_bytes_delta mod 1442")
    print("=" * 76)
    print(
        "%5s %8s %10s %12s %12s %10s"
        % ("link", "n_win", "frac du!=0", "du trung vi", "du max", "byte la/win")
    )
    for link in LINKS:
        frame = post_burn(measured[measured["link"] == link])
        if frame.empty:
            continue
        tx = frame["tx_bytes_delta"].to_numpy(dtype=float)
        rem = np.mod(tx, WIRE)
        rem = np.minimum(rem, WIRE - rem)
        bad = float(np.mean(rem > 1.0))
        print(
            "%5s %8d %10.4f %12.1f %12.1f %10.2f"
            % (
                link,
                len(tx),
                bad,
                float(np.median(rem)),
                float(np.max(rem)),
                float(np.mean(rem)),
            )
        )
    print("  Doc: 'frac du!=0' phai bang 0.0000. Bat ky gia tri duong nao")
    print("  => co goi khong-CBR tren interface (H1).")


def t2_tx_vs_rx(meta, measured: pd.DataFrame, run: Path) -> None:
    """T2 | So sanh TX va RX cua cung mot link."""
    print("\n" + "=" * 76)
    print("T2 | TX so voi RX cung link (hai instrument tren cung tap goi)")
    print("=" * 76)
    print(
        "%5s %10s %10s %8s %12s %12s"
        % ("link", "Var(TX)pk", "Var(RX)pk", "corr", "sd(TX-RX)pk", "mean|d|pk")
    )
    for link in LINKS:
        frame = post_burn(measured[measured["link"] == link])
        if frame.empty or "rx_bytes_delta" not in frame:
            continue
        tx = frame["tx_bytes_delta"].to_numpy(dtype=float) / WIRE
        rx = frame["rx_bytes_delta"].to_numpy(dtype=float) / WIRE
        corr = (
            float(np.corrcoef(tx, rx)[0, 1])
            if np.std(tx) > 0 and np.std(rx) > 0
            else float("nan")
        )
        delta = tx - rx
        print(
            "%5s %10.4f %10.4f %8.3f %12.4f %12.4f"
            % (
                link,
                float(np.var(tx)),
                float(np.var(rx)),
                corr,
                float(np.std(delta)),
                float(np.mean(np.abs(delta))),
            )
        )
    print("  Doc: corr ~ 1 => hai counter thay cung tien trinh.")
    print("  corr thap hoac sd(TX-RX) > 1 goi => hang doi giua hai diem (H2).")


def t3_emitter_schedule(meta, measured: pd.DataFrame, run: Path) -> None:
    """T3 | Do lech lich cua bo phat tu cumulative ledger 2 ms."""
    print("\n" + "=" * 76)
    print("T3 | Bo phat lech lich tuyet doi bao nhieu?  (ledger 2 ms)")
    print("=" * 76)
    print(
        "%5s %9s %9s %9s %9s %9s %9s"
        % ("link", "dev p01", "dev p50", "dev p99", "sd(dev)", "backlog", "catchup")
    )
    for link in LINKS:
        path = run / "flow_logs" / ("rho_offered_%s.csv" % link)
        if not path.exists():
            continue
        ledger = pd.read_csv(path)
        tcol = "t_mono" if "t_mono" in ledger.columns else "monotonic_s"
        rate = float(meta["profile"][link]["rate_pps"])
        engine = meta.get("flow_engine", {}).get(link, {})
        t0 = engine.get("t0_monotonic")
        if t0 is None:
            t0 = float(ledger[tcol].iloc[0]) - float(ledger["cum_packets"].iloc[0]) / rate
        t = ledger[tcol].to_numpy(dtype=float)
        keep = t >= t[0] + BURN_S
        dev = (
            ledger["cum_packets"].to_numpy(dtype=float)
            - np.floor((t - float(t0)) * rate)
        )[keep]
        print(
            "%5s %9.2f %9.2f %9.2f %9.4f %9s %9s"
            % (
                link,
                float(np.percentile(dev, 1)),
                float(np.percentile(dev, 50)),
                float(np.percentile(dev, 99)),
                float(np.std(dev)),
                engine.get("max_backlog"),
                engine.get("n_catchup"),
            )
        )
    print("  Doc: sd(dev) <= 0.5 goi la binh thuong (bien lam tron).")
    print("  sd(dev) > 1 goi => emitter phat theo cum (H3).")
    print("  Canh bao: ledger duoc ghi SAU due-batch, nen sd(dev) nho khong loai")
    print("  duoc jitter noi batch. max_backlog>1/n_catchup>0 la bang chung batch.")


def t4_stationarity(meta, measured: pd.DataFrame, run: Path) -> None:
    """T4 | Chia hau-burn thanh bon doan va so sanh phuong sai."""
    print("\n" + "=" * 76)
    print("T4 | Tinh dung cua phuong sai: 4 doan bang nhau (don vi goi^2)")
    print("=" * 76)
    print(
        "%5s %9s | %8s %8s %8s %8s | %8s"
        % ("link", "f(1-f)", "Q1", "Q2", "Q3", "Q4", "max/min")
    )
    dt_nom = float(meta["measured_window_s"])
    for link in LINKS:
        frame = post_burn(measured[measured["link"] == link])
        if frame.empty:
            continue
        profile = meta["profile"][link]
        rate = float(profile["rate_pps"])
        cap = float(profile["cap_mbps"]) * 1e6
        n = rate * dt_nom
        f = frac(n)
        rho_bar = rate * WIRE * 8.0 / cap
        scale = n**2 / rho_bar**2
        vals = [
            float(np.var(chunk, ddof=1)) * scale
            for chunk in np.array_split(frame["rho"].to_numpy(dtype=float), 4)
        ]
        print(
            "%5s %9.5f | %8.4f %8.4f %8.4f %8.4f | %8.2f"
            % (link, f * (1 - f), *vals, max(vals) / max(min(vals), 1e-12))
        )
    print("  Doc: max/min > ~1.5 => phuong sai KHONG dung (H4).")
    print("  So sanh moi Qi voi f(1-f): Qi nao vuot manh la doan chua su kien.")
    print("  Canh bao: nguong 1.5 chi mo ta; phai hieu chinh bang null huu han")
    print("  theo f. Khi f gan 0/1, mot block co the co Var=0 ngay ca duoi null.")


def t5_read_cost(meta, measured: pd.DataFrame, run: Path) -> None:
    """T5 | Kiem tra chi phi doc counter co di vao rho khong."""
    print("\n" + "=" * 76)
    print("T5 | read_duration_us va do lech dt")
    print("=" * 76)
    frame = post_burn(measured[measured["link"] == LINKS[0]])
    if frame.empty:
        return
    read = frame["read_duration_us"].to_numpy(dtype=float)
    dts = frame["dt_s"].to_numpy(dtype=float)
    dt_nom = float(meta["measured_window_s"])
    print(
        "  read_us   p50=%.1f p95=%.1f p99=%.1f max=%.1f"
        % (
            np.percentile(read, 50),
            np.percentile(read, 95),
            np.percentile(read, 99),
            np.max(read),
        )
    )
    print(
        "  dt_s      sd=%.6f ms  p95-p05=%.6f ms  max lech=%.6f ms"
        % (
            np.std(dts) * 1e3,
            (np.percentile(dts, 95) - np.percentile(dts, 5)) * 1e3,
            np.max(np.abs(dts - dt_nom)) * 1e3,
        )
    )
    for link in LINKS:
        link_frame = post_burn(measured[measured["link"] == link])
        if link_frame.empty:
            continue
        rho = link_frame["rho"].to_numpy(dtype=float)
        rd = link_frame["read_duration_us"].to_numpy(dtype=float)
        corr = (
            float(np.corrcoef(rho, rd)[0, 1])
            if np.std(rd) > 0 and np.std(rho) > 0
            else float("nan")
        )
        print("    corr(rho_%s, read_us) = %+.3f" % (link, corr))
    print("  Doc: |corr| > 0.2 => chi phi doc counter tham gia vao rho (H5).")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, help="thu muc mot run, vd .../D/rep1")
    args = parser.parse_args()
    run = Path(args.run)
    meta, measured = load(run)
    print(
        "RUN: %s   engine=%s   dt=%s   ledger_tick=%s"
        % (run, meta.get("engine"), meta.get("measured_window_s"), meta.get("offered_dt_s"))
    )
    t1_byte_purity(meta, measured, run)
    t2_tx_vs_rx(meta, measured, run)
    t3_emitter_schedule(meta, measured, run)
    t4_stationarity(meta, measured, run)
    t5_read_cost(meta, measured, run)


if __name__ == "__main__":
    main()

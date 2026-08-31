#!/usr/bin/env python3
"""Lesson 1 - ap luat f(1-f) len artifact NC-G1-static v3 DA CO.

R1--R4 doc compact detail va tinh lai null luong tu hoa; R5 doc dt_s va
timestamp_s trong RAW cell D de doi chieu jitter doc lap. Khong chay mang.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

import numpy as np

from tools.g_lesson1_verify import simulate_window

DETAIL = Path("results/SMOKE/phase-G/g1_static_v3_smoke_detail.json")
CAP_MBPS = {
    "uA": 8.0,
    "uB": 6.0,
    "ac": 6.0,
    "ad": 4.0,
    "bc": 6.0,
    "bd": 6.0,
    "vC": 8.0,
    "vD": 6.0,
}
WIRE = 1442.0
BAND_02_05 = (3.125, 12.5)
BAND_05_10 = (2.0, 8.0)


def link_geometry(link: str, entry: dict, dt: float) -> dict:
    """Suy nguoc r, n, f, rho tu artifact."""
    tick = entry["ledger"]["tick_s"]
    rate = entry["ledger"]["align_error_pkts_design"] / tick
    n = rate * dt
    f = n - math.floor(n)
    rho = rate * WIRE * 8.0 / (CAP_MBPS[link] * 1e6)
    return {
        "rate": rate,
        "n": n,
        "f": f,
        "rho": rho,
        "v_det": rho**2 * f * (1 - f) / n**2,
        "v_uni": rho**2 / (6.0 * n**2),
    }


def fit_sampler_jitter(cell: dict) -> tuple[float, float]:
    """Khop sigma jitter tu chu ky Var(rho) theo f tren mot cell dt=0.2.

    SSE la tong sai so tuong doi binh phuong so voi Var_eq quan sat. Cach
    chuan hoa nay ngan cac link co Var lon ap dao phep khop, va tai tao bang
    phan tich trong Lesson 1 correction.
    """
    print()
    print("=" * 78)
    print("R4 | Khop jitter gian tiep tu chu ky theo f (cell D)")
    print("=" * 78)
    links = list(CAP_MBPS)
    geometry = {
        link: link_geometry(link, cell["per_link"][link], 0.2) for link in links
    }
    observed = {
        link: cell["per_link"][link]["v_measured"]
        * geometry[link]["n"] ** 2
        / geometry[link]["rho"] ** 2
        for link in links
    }

    print("%5s %9s %11s %15s" % ("link", "f", "f(1-f)", "Var_eq quan sat"))
    for link in links:
        f = geometry[link]["f"]
        print("%5s %9.4f %11.5f %15.5f" % (link, f, f * (1 - f), observed[link]))

    candidates_ms = [
        0.00,
        0.02,
        0.04,
        0.05,
        0.06,
        0.07,
        0.08,
        0.09,
        0.10,
        0.12,
        0.15,
        0.20,
        0.30,
        0.50,
    ]
    rows = []
    print("\n%8s | %s | %7s" % ("jitter", " ".join("%7s" % x for x in links), "SSE"))
    for jitter_ms in candidates_ms:
        predicted = {}
        for link in links:
            g = geometry[link]
            _, _, rho = simulate_window(
                g["rate"],
                0.2,
                CAP_MBPS[link] * 1e6,
                300_000,
                jitter_s=jitter_ms / 1000.0,
            )
            predicted[link] = float(np.var(rho)) * g["n"] ** 2 / g["rho"] ** 2
        sse = sum(((predicted[x] - observed[x]) / observed[x]) ** 2 for x in links)
        rows.append((sse, jitter_ms, predicted))
        print(
            "%6.2f ms | %s | %7.3f"
            % (
                jitter_ms,
                " ".join("%7.4f" % predicted[x] for x in links),
                sse,
            )
        )
    best_sse, best_ms, _ = min(rows)
    print("\n  jitter khop tot nhat: %.2f ms  (relative SSE = %.3f)" % (best_ms, best_sse))
    return best_ms, best_sse


def measure_direct_dt_jitter(cell: dict, indirect_ms: float) -> None:
    """Do doc lap jitter thoi diem va do dai cua so tu RAW cell D."""
    print()
    print("=" * 78)
    print("R5 | Do jitter truc tiep tu RAW cell D")
    print("=" * 78)
    run_dir = Path(cell["run_dir"])
    paths = (run_dir / "rho_measured.csv", run_dir / "rho_measured_s1.csv")
    print(
        "%19s %7s %11s %13s %14s %14s"
        % ("file", "windows", "sd(dt) ms", "p95-p05 ms", "sd(dt) steady", "sd(time) ms")
    )
    direct_time_sd = []
    for sampler_index, path in enumerate(paths):
        with path.open(newline="", encoding="utf-8") as handle:
            # dt_s is repeated for eight links. Keep one link per sample.
            rows = [row for row in csv.DictReader(handle) if row["link"] == "uA"]
        dt_s = np.asarray([float(row["dt_s"]) for row in rows])
        sample_index = np.asarray([int(row["sample_index"]) for row in rows])
        timestamp_s = np.asarray([float(row["timestamp_s"]) for row in rows])
        dt_error_ms = (dt_s - 0.2) * 1000.0
        phase_s = 0.2 + sampler_index * 0.1
        time_error_ms = (
            timestamp_s - (phase_s + sample_index.astype(float) * 0.2)
        ) * 1000.0
        sd_dt = float(np.std(dt_s, ddof=1) * 1000.0)
        sd_dt_steady = float(np.std(dt_s[1:], ddof=1) * 1000.0)
        span = float(np.percentile(dt_error_ms, 95) - np.percentile(dt_error_ms, 5))
        sd_time = float(np.std(time_error_ms, ddof=1))
        direct_time_sd.append(sd_time)
        print(
            "%19s %7d %11.5f %13.5f %14.5f %14.5f"
            % (path.name, len(dt_s), sd_dt, span, sd_dt_steady, sd_time)
        )
    print(
        "\n  timestamp-jitter truc tiep: %.5f-%.5f ms"
        % (min(direct_time_sd), max(direct_time_sd))
    )
    print(
        "  khop gian tiep / do truc tiep: %.2f-%.2fx -> KHONG KHOP"
        % (indirect_ms / max(direct_time_sd), indirect_ms / min(direct_time_sd))
    )
    print("  Luu y: mau dt dau tien cua sampler 0 la outlier khoi tao; cot")
    print("  'sd(dt) steady' bo mau do. sd(time) do sai lech khoi lich deadline.")
    print("  STOP: con co che khac hoac mo hinh jitter chua dung; chua sang Lesson 2.")


def main() -> None:
    data = json.loads(DETAIL.read_text(encoding="utf-8"))
    cells = {c["cell"]: c for c in data["cells"]}

    print("=" * 78)
    print("R1 | v_measured / null   tren 72 link-run")
    print("=" * 78)
    r_det, r_uni = [], []
    for cell in data["cells"]:
        dt = cell["measured_window_s"]
        for link, entry in cell["per_link"].items():
            g = link_geometry(link, entry, dt)
            vm = entry["v_measured"]
            r_det.append(vm / g["v_det"])
            r_uni.append(vm / g["v_uni"])
    for name, arr in (("f(1-f)", r_det), ("1/6", r_uni)):
        print(
            "  null=%-8s median=%.3f  p10=%.3f  p90=%.3f  min=%.3f  max=%.3f"
            % (
                name,
                statistics.median(arr),
                sorted(arr)[len(arr) // 10],
                sorted(arr)[9 * len(arr) // 10],
                min(arr),
                max(arr),
            )
        )

    print()
    print("=" * 78)
    print("R2 | Truc dt-control: luat nao du doan dung PASS/FAIL?")
    print("=" * 78)
    print(
        "%5s %9s %9s %9s %9s %7s %7s %7s"
        % ("link", "r1 do", "r1 f(1-f)", "r2 do", "r2 f(1-f)", "THAT", "PRED_f", "PRED_u")
    )
    hit_f = hit_u = 0
    for link in CAP_MBPS:
        v, ff = {}, {}
        for name, dt in (("D_dt_0p2", 0.2), ("D_dt_0p5", 0.5), ("D_dt_1p0", 1.0)):
            e = cells[name]["per_link"][link]
            g = link_geometry(link, e, dt)
            v[dt], ff[dt] = e["v_measured"], g["f"] * (1 - g["f"])
        r1o, r2o = v[0.2] / v[0.5], v[0.5] / v[1.0]
        r1p = (ff[0.2] / ff[0.5]) * (0.5 / 0.2) ** 2
        r2p = (ff[0.5] / ff[1.0]) * (1.0 / 0.5) ** 2

        def verdict(a: float, b: float) -> str:
            return (
                "PASS"
                if BAND_02_05[0] <= a <= BAND_02_05[1]
                and BAND_05_10[0] <= b <= BAND_05_10[1]
                else "FAIL"
            )

        real, pf, pu = verdict(r1o, r2o), verdict(r1p, r2p), verdict(6.25, 4.0)
        hit_f += real == pf
        hit_u += real == pu
        print(
            "%5s %9.2f %9.2f %9.2f %9.2f %7s %7s %7s"
            % (link, r1o, r1p, r2o, r2p, real, pf, pu)
        )
    print("\n  luat f(1-f) du doan dung : %d/8" % hit_f)
    print("  luat 1/dt^2 thuan        : %d/8" % hit_u)

    print()
    print("=" * 78)
    print("R3 | residual = v_measured - v_det (exploratory, chua dinh danh)")
    print("=" * 78)
    print(
        "%-10s %6s %6s %6s %8s %13s %10s"
        % ("cell", "ditto", "aoi", "recon", "cpu p95", "median excess", "sigma_resid")
    )
    for cell in data["cells"]:
        if cell["measured_window_s"] != 0.2:
            continue
        ex = []
        for link, entry in cell["per_link"].items():
            ex.append(entry["v_measured"] - link_geometry(link, entry, 0.2)["v_det"])
        med = statistics.median(ex)
        t = cell["telemetry_config"]
        print(
            "%-10s %6s %6s %6s %7.1f%% %13.3e %10.5f"
            % (
                cell["cell"],
                t["ditto"],
                t["aoi_probe"],
                t["reconcile_every"],
                cell["infra"]["cpu_p95"],
                med,
                math.sqrt(max(med, 0.0)),
            )
        )

    cell_d = cells["D"]
    indirect_ms, _ = fit_sampler_jitter(cell_d)
    measure_direct_dt_jitter(cell_d, indirect_ms)


if __name__ == "__main__":
    main()

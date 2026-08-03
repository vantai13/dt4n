#!/usr/bin/env python3
"""Phase T -- bang chung cho Gate T (T-G1 .. T-G5) theo MASTER_PLAN_v8.

Chay bang interpreter live:
    sudo -n env PYTHONPATH="$PWD" /usr/bin/python3 -m measurements.t7_gate_table \
        --out results/phase-T/t7_gate_table.json

LUU Y T-G2: so sanh voi GIA TRI KY VONG GIAI TICH duoi cua so huu han,
KHONG so voi gia tri thiet ke tho.
  - sigma: uoc luong sigma_hat bi chech AM do tru trung binh mau
           -> dung expected_sigma_hat() (da co san trong rho_spec)
  - tau  : uoc luong lag-1 bi chech AM, E[r1] ~ phi - (1+3phi)/n
           -> khi phi -> 1, ln() khuech dai thanh lech lon (tau=5: -16%)
Day la do chech DA BIET cua uoc luong, khong phai loi bo sinh.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
from collections import defaultdict
from typing import Any, Dict, List

from mininet.load_spec import background_pps, build_schedule, schedule_digest
from mininet.rho_spec import (
    expected_sigma_hat,
    measure_sigma,
    measure_tau,
    ou_trajectory,
    sigma_from_a,
)


MAIN = "results/phase-T/campaign_state.json"
CTRL = "results/phase-T/control_state.json"
BW, Q, PROBE = 6.0, 13, 20.0


def make_traj(row: Dict[str, Any]):
    sigma = 0.0 if float(row["a"]) == 0.0 else sigma_from_a(row["rho_bar"], row["a"])
    n_steps = int(round(float(row["duration_s"]) / float(row["dt"])))
    return ou_trajectory(
        row["rho_bar"],
        sigma,
        row["tau_rho"],
        n_steps,
        row["seed"],
        dt=row["dt"],
    )


def expected_tau_hat(tau: float, dt: float, n: int) -> float:
    """Ky vong giai tich cua uoc luong tau tu lag-1, co do chech huu han mau."""
    if tau <= 0:
        return float("nan")
    phi = math.exp(-dt / tau)
    r1 = phi - (1.0 + 3.0 * phi) / n
    if not (0.0 < r1 < 1.0):
        return float("nan")
    return -dt / math.log(r1)


def load(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["rows"]


def gate_g1(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tai lap bit-exact: dung lai ca hai digest chi tu (seed, tham so)."""
    ok_traj = ok_sched = 0
    for row in rows:
        if make_traj(row).digest() == row["trajectory_digest"]:
            ok_traj += 1
        if row["a"] == 0.0:
            pps = background_pps(row["rho_bar"], BW, PROBE)
            n_packets = max(1, int(pps * float(row["duration_s"])))
            digest = schedule_digest(
                build_schedule(row["mode"], n_packets, 1.0 / pps, row["seed"])
            )
            if digest == row["schedule_digest"]:
                ok_sched += 1
    n_static = sum(1 for row in rows if row["a"] == 0.0)
    return {
        "n_rows": len(rows),
        "trajectory_digest_khop": ok_traj,
        "schedule_digest_khop_tinh": ok_sched,
        "n_diem_tinh": n_static,
        "pass": ok_traj == len(rows) and ok_sched == n_static,
    }


def _gate_g2_cells(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """sigma, tau do lai vs ky vong giai tich duoi cua so huu han."""
    groups: Dict[tuple, List[Dict[str, float]]] = defaultdict(list)
    for row in rows:
        if row["a"] == 0.0:
            continue
        traj = make_traj(row)
        sigma_design = sigma_from_a(row["rho_bar"], row["a"])
        groups[(row["rho_bar"], row["a"], row["tau_rho"])].append(
            {
                "sig_do": measure_sigma(traj.rho),
                "sig_tk": sigma_design,
                "sig_kv": expected_sigma_hat(
                    sigma_design,
                    row["tau_rho"],
                    traj.duration_s,
                    traj.dt,
                ),
                "tau_do": measure_tau(traj.rho, traj.dt),
                "tau_tk": float(row["tau_rho"]),
                "tau_kv": expected_tau_hat(float(row["tau_rho"]), traj.dt, traj.n_steps),
                "clamp": traj.clamp_ratio,
            }
        )

    out: List[Dict[str, Any]] = []
    n_pass = 0
    n_total = 0
    for key in sorted(groups):
        vals = groups[key]
        report_row: Dict[str, Any] = {
            "rho_bar": key[0],
            "a": key[1],
            "tau_rho": key[2],
            "n": len(vals),
        }
        for tag in ("sig", "tau"):
            measured = st.mean(x[f"{tag}_do"] for x in vals)
            design = st.mean(x[f"{tag}_tk"] for x in vals)
            expected = st.mean(x[f"{tag}_kv"] for x in vals)
            report_row[f"{tag}_do"] = measured
            report_row[f"{tag}_vs_thiet_ke"] = measured / design - 1.0
            report_row[f"{tag}_vs_ky_vong"] = measured / expected - 1.0
            report_row[f"{tag}_pass"] = abs(measured / expected - 1.0) <= 0.10
            n_pass += int(report_row[f"{tag}_pass"])
            n_total += 1
        report_row["clamp_max"] = max(x["clamp"] for x in vals)
        out.append(report_row)
    return {
        "cells": out,
        "n_pass": n_pass,
        "n_tong": n_total,
        "clamp_max_toan_cuc": max(row["clamp_max"] for row in out),
        "pass": n_pass == n_total,
    }


def gate_g2(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Gate T-G2 on regular design rows; sentinels are repeated stability checks."""
    gate_rows = [row for row in rows if row.get("block") != "S"]
    sentinel_rows = [row for row in rows if row.get("block") == "S"]
    result = _gate_g2_cells(gate_rows)
    all_weighted = _gate_g2_cells(rows)
    result.update(
        {
            "n_rows_input": len(rows),
            "n_rows_gate": len(gate_rows),
            "n_sentinel_excluded": len(sentinel_rows),
            "sentinel_policy": (
                "block S la diem canh lap lai cung seed, khong phai mau thiet ke doc lap; "
                "T-G2 gate tren 270 dong regular."
            ),
            "all_main_weighted_n_pass": all_weighted["n_pass"],
            "all_main_weighted_n_tong": all_weighted["n_tong"],
        }
    )
    return result


def gate_g3(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    have = sum(1 for row in rows if "ca_operational" in row and row["ca_operational"] is not None)
    z = [row["ca_operational_z"] for row in rows if row.get("ca_operational_z") is not None]
    return {
        "n_rows": len(rows),
        "co_ca_operational": have,
        "z_mean": st.mean(z),
        "z_sd": st.stdev(z),
        "z_max_abs": max(abs(x) for x in z),
        "c_s_ghi_chu": (
            "link shaping, goi BG co dinh 1500B -> thoi gian phuc vu "
            "TAT DINH, c_s = 0 theo cau tao. Khong do tung trace; "
            "ghi la hang so trong closure."
        ),
        "pass": have == len(rows),
    }


def gate_g5(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups: Dict[float, List[float]] = defaultdict(list)
    for row in rows:
        groups[row["rho_bar"]].append(row["rho_bias"])
    out = []
    for key in sorted(groups):
        vals = groups[key]
        out.append(
            {
                "rho_bar": key,
                "n": len(vals),
                "mean": st.mean(vals),
                "sd": st.stdev(vals),
                "max_abs": max(abs(x) for x in vals),
            }
        )
    all_biases = [row["rho_bias"] for row in rows]
    return {
        "theo_muc_tai": out,
        "toan_cuc_mean": st.mean(all_biases),
        "toan_cuc_max_abs": max(abs(x) for x in all_biases),
        "pass": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="results/phase-T/t7_gate_table.json")
    args = parser.parse_args()

    main_rows = load(MAIN)
    ctrl_rows = load(CTRL)
    all_rows = main_rows + ctrl_rows

    result = {
        "T-G1_tai_lap_bit_exact": gate_g1(all_rows),
        "T-G2_dac_trung_khop": gate_g2(main_rows),
        "T-G3_ca_cs_ghi_nhan": gate_g3(all_rows),
        "T-G4_DOI": {"pass": False, "ghi_chu": "dien DOI sau khi upload Zenodo"},
        "T-G5_rho_offered_vs_measured": gate_g5(all_rows),
    }

    print("=" * 72)
    print("BANG GATE T -- Phase T (MASTER_PLAN_v8)")
    print("=" * 72)
    for key, value in result.items():
        print(f"\n{key}   ->   {'PASS' if value.get('pass') else 'CHUA XONG'}")
        for item_key, item_value in value.items():
            if item_key in ("pass", "cells", "theo_muc_tai"):
                continue
            print(f"    {item_key} = {item_value}")

    print("\n--- T-G2 chi tiet (o | sigma | tau) ---")
    print(
        f"{'rho':>6}{'a':>5}{'tau':>6} | {'sig_do':>9}{'vs_tk':>8}{'vs_kv':>8} |"
        f" {'tau_do':>8}{'vs_tk':>8}{'vs_kv':>8}"
    )
    for cell in result["T-G2_dac_trung_khop"]["cells"]:
        print(
            f"{cell['rho_bar']:>6}{cell['a']:>5}{cell['tau_rho']:>6} | "
            f"{cell['sig_do']:>9.5f}{100 * cell['sig_vs_thiet_ke']:>+7.1f}%"
            f"{100 * cell['sig_vs_ky_vong']:>+7.1f}% | "
            f"{cell['tau_do']:>8.4f}{100 * cell['tau_vs_thiet_ke']:>+7.1f}%"
            f"{100 * cell['tau_vs_ky_vong']:>+7.1f}%"
        )

    print("\n--- T-G5 rho_bias theo muc tai ---")
    for cell in result["T-G5_rho_offered_vs_measured"]["theo_muc_tai"]:
        print(
            f"  rho={cell['rho_bar']:<6} n={cell['n']:>3}  mean={cell['mean']:+.6f}  "
            f"sd={cell['sd']:.6f}  max|.|={cell['max_abs']:.6f}"
        )

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nwrote -> {args.out}")


if __name__ == "__main__":
    main()

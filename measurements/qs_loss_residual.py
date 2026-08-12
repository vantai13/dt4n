#!/usr/bin/env python3
"""Phase 20R.8 -- reanalyze Phase T for quasi-static residual on loss.

The estimand is a paired difference-of-differences:

    (observed_loss_dynamic - packet_weighted_QS_loss_dynamic)
      - (observed_loss_control - packet_weighted_QS_loss_control)

Pairing is by ``(mode, rho_bar, seed)``.  The packet-weighted QS term uses the
designed Phase T trajectory and arrival intensity, matching the delay-side
``decompose`` logic but evaluating the loss curve instead of the delay curve.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from mininet.load_spec import PROBE_PPS
from mininet.rho_schedule import intensity
from mininet.rho_spec import DT_DEFAULT, ou_trajectory, sigma_from_a
from twin.link_model_v2 import LinkModelV2


BW = 6.0
Q = 13
MODEL_PATH = "results/phase-L/link_model_v2_fit.json"
MAIN_STATE = "results/phase-T/campaign_state.json"
CONTROL_STATE = "results/phase-T/control_state.json"
OUT = "results/phase-20R/qs_loss_residual.json"
LOSS_SUP_NEG = -0.001
LOSS_SUP_POS = 0.00005


Row = Dict[str, Any]
CellSeed = Tuple[str, float, int]


def _load_rows(path: str) -> List[Row]:
    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)
    return [dict(row) for row in state.get("rows", [])]


def _clean(row: Mapping[str, Any]) -> bool:
    return not row.get("gate_fail")


def _sent_from_loss(row: Mapping[str, Any]) -> float:
    loss = float(row["loss"])
    recv = float(row["n_recv_unique"])
    if not (0.0 <= loss < 1.0):
        raise ValueError("loss outside [0,1): %r" % loss)
    return recv / max(1.0 - loss, 1e-12)


def _cell_seed(row: Mapping[str, Any]) -> CellSeed:
    return (
        str(row["mode"]),
        round(float(row["rho_bar"]), 3),
        int(row["seed"]),
    )


class LossResidualCalculator:
    def __init__(self, model_path: str = MODEL_PATH):
        self.model = LinkModelV2.load(model_path)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def row_terms(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        pid = str(row["pid"])
        if pid in self._cache:
            return dict(self._cache[pid])

        mode = str(row["mode"])
        bw = float(row.get("bw", BW))
        q = int(row.get("q", Q))
        rho_bar = float(row["rho_bar"])
        a = float(row["a"])
        tau = float(row["tau_rho"])
        seed = int(row["seed"])
        dt = float(row.get("dt", DT_DEFAULT))
        n_steps = int(round(float(row["duration_s"]) / dt))
        sigma = 0.0 if a == 0.0 else sigma_from_a(rho_bar, a)

        traj = ou_trajectory(rho_bar, sigma, tau, n_steps, seed, dt=dt)
        lam = intensity(traj, bw, PROBE_PPS)
        losses = [
            self.model.predict_loss(mode, bw, q, float(rho))
            for rho in traj.rho
        ]
        packet_weighted_qs = sum(l * p for l, p in zip(lam, losses)) / sum(lam)
        time_weighted_qs = sum(losses) / len(losses)
        ssa_qs = self.model.predict_loss(mode, bw, q, sum(traj.rho) / len(traj.rho))
        observed = float(row["loss"])
        sent = _sent_from_loss(row)

        out = {
            "pid": pid,
            "mode": mode,
            "rho_bar": rho_bar,
            "a": a,
            "tau_rho": tau,
            "seed": seed,
            "observed_loss": observed,
            "packet_weighted_qs_loss": packet_weighted_qs,
            "time_weighted_qs_loss": time_weighted_qs,
            "ssa_qs_loss": ssa_qs,
            "residual_loss": observed - packet_weighted_qs,
            "n_recv_unique": int(row["n_recv_unique"]),
            "n_sent_est": sent,
            "trajectory_digest_ok": str(row.get("trajectory_digest", "")) == traj.digest(),
        }
        self._cache[pid] = dict(out)
        return out


def _mean(values: Sequence[float]) -> float:
    return sum(float(v) for v in values) / len(values)


def _normal_summary(values: Sequence[float]) -> Dict[str, Any]:
    vals = [float(v) for v in values]
    mean = _mean(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    se = sd / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
    return {
        "n": len(vals),
        "mean": mean,
        "sd": sd,
        "se": se,
        "ci95_normal": [mean - 1.96 * se, mean + 1.96 * se],
    }


def _verdict(ci95: Sequence[float]) -> str:
    lo, hi = float(ci95[0]), float(ci95[1])
    if lo >= LOSS_SUP_NEG and hi <= LOSS_SUP_POS:
        return "PASS"
    return "KHONG_KET_LUAN_DUOC"


def _paired_row_diffs(
    main_rows: Sequence[Mapping[str, Any]],
    control_rows: Sequence[Mapping[str, Any]],
    calc: LossResidualCalculator,
    modes: Sequence[str],
    a_levels: Sequence[float],
) -> List[Row]:
    controls: Dict[CellSeed, Dict[str, Any]] = {}
    for row in control_rows:
        if not _clean(row) or abs(float(row.get("a", 0.0))) > 1e-12:
            continue
        controls[_cell_seed(row)] = calc.row_terms(row)

    out: List[Row] = []
    wanted_modes = {str(mode) for mode in modes}
    wanted_a = {round(float(a), 12) for a in a_levels}
    for row in main_rows:
        if not _clean(row):
            continue
        if str(row.get("block")) == "S":
            continue
        if str(row["mode"]) not in wanted_modes:
            continue
        if round(float(row["a"]), 12) not in wanted_a:
            continue
        key = _cell_seed(row)
        if key not in controls:
            raise ValueError("missing Phase T control for %s@%.3f seed %d" % key)
        dyn = calc.row_terms(row)
        ctrl = controls[key]
        diff = float(dyn["residual_loss"]) - float(ctrl["residual_loss"])
        out.append(
            {
                "mode": str(row["mode"]),
                "rho_bar": round(float(row["rho_bar"]), 3),
                "a": float(row["a"]),
                "tau_rho": float(row["tau_rho"]),
                "seed": int(row["seed"]),
                "diff_of_differences_loss": diff,
                "weight_packets": float(dyn["n_sent_est"]),
                "dynamic": dyn,
                "control": ctrl,
            }
        )
    return out


def _summarize_group(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    diffs = [float(row["diff_of_differences_loss"]) for row in rows]
    weights = [float(row["weight_packets"]) for row in rows]
    row_summary = _normal_summary(diffs)
    weighted_row_point = sum(v * w for v, w in zip(diffs, weights)) / sum(weights)

    by_seed: Dict[int, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_seed[int(row["seed"])].append(row)
    seed_rows = []
    seed_values = []
    for seed, seed_group in sorted(by_seed.items()):
        vals = [float(row["diff_of_differences_loss"]) for row in seed_group]
        wts = [float(row["weight_packets"]) for row in seed_group]
        value = sum(v * w for v, w in zip(vals, wts)) / sum(wts)
        seed_values.append(value)
        seed_rows.append(
            {
                "seed": int(seed),
                "n_rows": len(seed_group),
                "packet_weighted_diff_loss": value,
            }
        )
    seed_summary = _normal_summary(seed_values)
    verdict = _verdict(seed_summary["ci95_normal"])
    return {
        "n_rows": len(rows),
        "row_level_normal": row_summary,
        "row_packet_weighted_point": weighted_row_point,
        "seed_cluster_packet_weighted_normal": seed_summary,
        "seed_rows": seed_rows,
        "verdict": verdict,
        "threshold": [LOSS_SUP_NEG, LOSS_SUP_POS],
    }


def _group_rows(rows: Iterable[Mapping[str, Any]], keys: Sequence[str]) -> Dict[str, List[Mapping[str, Any]]]:
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        label = ",".join("%s=%g" % (key, float(row[key])) if key != "mode" else "mode=%s" % row[key] for key in keys)
        grouped[label].append(row)
    return dict(sorted(grouped.items()))


def run(
    main_state: str = MAIN_STATE,
    control_state: str = CONTROL_STATE,
    model_path: str = MODEL_PATH,
    modes: Sequence[str] = ("h2", "poisson"),
    a_levels: Sequence[float] = (0.2, 0.9),
) -> Dict[str, Any]:
    calc = LossResidualCalculator(model_path)
    rows = _paired_row_diffs(
        _load_rows(main_state),
        _load_rows(control_state),
        calc,
        modes=modes,
        a_levels=a_levels,
    )
    if not rows:
        raise ValueError("no paired QS-LOSS rows")

    digest_fail = [
        row
        for row in rows
        if not row["dynamic"]["trajectory_digest_ok"] or not row["control"]["trajectory_digest_ok"]
    ]
    mode_a = {
        label: _summarize_group(group)
        for label, group in _group_rows(rows, ("mode", "a")).items()
    }
    mode_a_tau = {
        label: _summarize_group(group)
        for label, group in _group_rows(rows, ("mode", "a", "tau_rho")).items()
    }
    return {
        "phase": "20R.8",
        "schema": "phase20r8/qs_loss_residual/v1",
        "estimand": (
            "(observed_loss_dynamic - packet_weighted_QS_loss_dynamic) - "
            "(observed_loss_control - packet_weighted_QS_loss_control), "
            "paired by mode/rho_bar/seed"
        ),
        "source": {
            "main_state": main_state,
            "control_state": control_state,
            "model_path": model_path,
        },
        "decision_ci": "seed_cluster_packet_weighted_normal",
        "threshold": {
            "loss_negative": LOSS_SUP_NEG,
            "loss_positive": LOSS_SUP_POS,
        },
        "summary": {
            "n_rows": len(rows),
            "n_digest_fail": len(digest_fail),
            "mode_a": mode_a,
            "mode_a_tau": mode_a_tau,
            "headline": {
                "poisson_a0p9": mode_a["mode=poisson,a=0.9"],
                "h2_a0p9": mode_a["mode=h2,a=0.9"],
            },
        },
        "rows": rows,
    }


def _parse_csv_floats(text: str) -> List[float]:
    return [float(x) for x in str(text).split(",") if x.strip()]


def _parse_csv_text(text: str) -> List[str]:
    return [x.strip() for x in str(text).split(",") if x.strip()]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--main-state", default=MAIN_STATE)
    ap.add_argument("--control-state", default=CONTROL_STATE)
    ap.add_argument("--model-path", default=MODEL_PATH)
    ap.add_argument("--modes", default="h2,poisson")
    ap.add_argument("--a-levels", default="0.2,0.9")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args(argv)

    report = run(
        main_state=args.main_state,
        control_state=args.control_state,
        model_path=args.model_path,
        modes=_parse_csv_text(args.modes),
        a_levels=_parse_csv_floats(args.a_levels),
    )
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")

    print("mode     a   point(seed-pw)  CI95 normal                  verdict")
    for label, block in report["summary"]["mode_a"].items():
        point = block["seed_cluster_packet_weighted_normal"]["mean"]
        ci = block["seed_cluster_packet_weighted_normal"]["ci95_normal"]
        mode = label.split(",")[0].split("=")[1]
        a = float(label.split(",")[1].split("=")[1])
        print(
            "%-8s %.1f %+14.6f  [%+.6f, %+.6f]  %s"
            % (mode, a, point, ci[0], ci[1], block["verdict"])
        )
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

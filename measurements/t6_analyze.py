#!/usr/bin/env python3
"""Phase T / T.6 -- blinded err_qs analysis.

This file is written before opening the real sealed Phase T response metrics.
All confirmatory choices are fixed here and exercised on fake sealed data first.

A13.1: report err_qs both raw and corrected.
A13.2: Delta_hat = 0.0158 ms, estimated only from C' controls.
A13.3: SE(Delta_hat) = 0.0023 ms, added as a system component.
A14.6: also report the homogeneous subset n_late_ratio < 1e-3.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from measurements.t4_validate import classify_err_qs, decompose
from measurements.t5_campaign import (
    BW,
    MODEL_PATH,
    Q,
    SEALED,
    STATE,
    make_traj,
)
from twin.link_model_v2 import LinkModelV2


DELTA_HAT_MS = 0.0158
DELTA_SE_MS = 0.0023
HOMOGENEOUS_N_LATE_MAX = 1e-3
SCRIPT_VERSION = "t6_analyze_v1_pre_unblind"


Row = Dict[str, Any]


def _mean(xs: Sequence[float]) -> float:
    return sum(float(x) for x in xs) / len(xs)


def _sd(xs: Sequence[float]) -> float | None:
    if len(xs) <= 1:
        return None
    m = _mean(xs)
    return math.sqrt(sum((float(x) - m) ** 2 for x in xs) / (len(xs) - 1))


def _se_mean(xs: Sequence[float]) -> float | None:
    sd = _sd(xs)
    return sd / math.sqrt(len(xs)) if sd is not None else None


def _pctl(xs: Sequence[float], q: float) -> float | None:
    if not xs:
        return None
    vals = sorted(float(x) for x in xs)
    k = int(math.ceil(float(q) * len(vals))) - 1
    return vals[min(max(k, 0), len(vals) - 1)]


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _number_summary(values: Iterable[Any]) -> Dict[str, Any]:
    xs = [float(x) for x in values if _finite(x)]
    if not xs:
        return {
            "n": 0,
            "mean": None,
            "sd": None,
            "se_mean": None,
            "min": None,
            "p05": None,
            "p50": None,
            "p95": None,
            "max": None,
        }
    return {
        "n": len(xs),
        "mean": _mean(xs),
        "sd": _sd(xs),
        "se_mean": _se_mean(xs),
        "min": min(xs),
        "p05": _pctl(xs, 0.05),
        "p50": _pctl(xs, 0.50),
        "p95": _pctl(xs, 0.95),
        "max": max(xs),
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _load_state_rows(path: str) -> List[Row]:
    with open(path, "r", encoding="utf-8") as f:
        state = json.load(f)
    rows = list(state.get("rows", []))
    rows.sort(key=lambda row: int(row["idx"]))
    return rows


def _load_sealed(pid: str, sealed_dir: str) -> Row:
    path = os.path.join(sealed_dir, pid + ".json")
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if str(payload.get("pid")) != str(pid):
        raise ValueError("%s: pid mismatch" % path)
    sealed = payload.get("sealed")
    if not isinstance(sealed, dict):
        raise ValueError("%s: missing sealed object" % path)
    if "q_mean_ms" not in sealed:
        raise ValueError("%s: sealed object missing q_mean_ms" % path)
    return dict(sealed)


def combine_rows(public_rows: Sequence[Row], sealed_dir: str) -> List[Row]:
    rows: List[Row] = []
    missing: List[str] = []
    for row in public_rows:
        pid = str(row["pid"])
        try:
            sealed = _load_sealed(pid, sealed_dir)
        except FileNotFoundError:
            missing.append(pid)
            continue
        combined = dict(row)
        combined.update(sealed)
        rows.append(combined)
    if missing:
        raise FileNotFoundError(
            "missing sealed rows: %d, first=%s" % (len(missing), missing[0])
        )
    return rows


def _core_terms(row: Mapping[str, Any], model: LinkModelV2) -> Row:
    traj = make_traj(dict(row))
    mode = str(row["mode"])
    bw = float(row.get("bw", BW))
    q = int(row.get("q", Q))
    rho_bar = float(row["rho_bar"])
    sigma_ref = model.sigma(mode, bw, q, rho_bar)
    dec = decompose(model, mode, bw, q, traj, float(row["q_mean_ms"]))

    err_raw = float(dec["err_qs_ms"])
    se_raw = float(dec["se_err_qs_ms"])
    err_corrected = err_raw - DELTA_HAT_MS
    se_corrected = math.sqrt(se_raw * se_raw + DELTA_SE_MS * DELTA_SE_MS)

    return {
        "q_psa_load_ms": dec["q_psa_load_ms"],
        "q_psa_time_ms": dec["q_psa_time_ms"],
        "q_ssa_ms": dec["q_ssa_ms"],
        "err_qs_raw_ms": err_raw,
        "err_qs_corrected_ms": err_corrected,
        "err_jensen_ms": dec["err_jensen_ms"],
        "d_sampling_ms": dec["d_sampling_ms"],
        "err_total_ms": dec["err_total_ms"],
        "se_err_qs_raw_ms": se_raw,
        "se_err_qs_corrected_ms": se_corrected,
        "n_pkt_model": dec["n_pkt"],
        "sigma_ref_ms": sigma_ref,
        "err_qs_raw_class": classify_err_qs(err_raw, sigma_ref, se_raw),
        "err_qs_corrected_class": classify_err_qs(
            err_corrected, sigma_ref, se_corrected
        ),
        "err_qs_corrected_z": err_corrected / max(se_corrected, 1e-12),
        "homogeneous_a14": float(row.get("n_late_ratio", 0.0))
        < HOMOGENEOUS_N_LATE_MAX,
        "trajectory_rho_mean": _mean(traj.rho),
        "trajectory_rho_min": min(traj.rho),
        "trajectory_rho_max": max(traj.rho),
        "trajectory_clamp_ratio": traj.clamp_ratio,
    }


def analyze_rows(rows: Sequence[Row], model: LinkModelV2) -> List[Row]:
    out: List[Row] = []
    for row in rows:
        enriched = dict(row)
        enriched.update(_core_terms(row, model))
        out.append(enriched)
    return out


def _group_key(row: Mapping[str, Any], keys: Sequence[str]) -> str:
    parts = []
    for key in keys:
        value = row.get(key)
        if isinstance(value, float):
            value = "%g" % value
        parts.append("%s=%s" % (key, value))
    return ",".join(parts)


def summarize_rows(rows: Sequence[Row]) -> Dict[str, Any]:
    class_raw = Counter(str(row["err_qs_raw_class"]) for row in rows)
    class_corrected = Counter(str(row["err_qs_corrected_class"]) for row in rows)
    commits = Counter(
        str(row.get("env", {}).get("git_commit", "unknown"))[:8] for row in rows
    )
    return {
        "n": len(rows),
        "err_qs_raw_ms": _number_summary(row["err_qs_raw_ms"] for row in rows),
        "err_qs_corrected_ms": _number_summary(
            row["err_qs_corrected_ms"] for row in rows
        ),
        "err_qs_corrected_z": _number_summary(
            row["err_qs_corrected_z"] for row in rows
        ),
        "err_jensen_ms": _number_summary(row["err_jensen_ms"] for row in rows),
        "d_sampling_ms": _number_summary(row["d_sampling_ms"] for row in rows),
        "q_mean_ms": _number_summary(row["q_mean_ms"] for row in rows),
        "loss": _number_summary(row.get("loss") for row in rows),
        "n_late_ratio": _number_summary(row.get("n_late_ratio") for row in rows),
        "class_raw": dict(sorted(class_raw.items())),
        "class_corrected": dict(sorted(class_corrected.items())),
        "commits": dict(sorted(commits.items())),
    }


def grouped_summary(rows: Sequence[Row], keys: Sequence[str]) -> Dict[str, Any]:
    grouped: Dict[str, List[Row]] = defaultdict(list)
    for row in rows:
        grouped[_group_key(row, keys)].append(row)
    return {
        key: summarize_rows(grouped[key])
        for key in sorted(grouped)
    }


def sentinel_summary(rows: Sequence[Row]) -> Dict[str, Any]:
    sentinels = [row for row in rows if str(row.get("block")) == "S"]
    if not sentinels:
        return {"n": 0}
    return {
        "n": len(sentinels),
        "idx": [int(row["idx"]) for row in sentinels],
        "schedule_digests": sorted(
            {str(row.get("schedule_digest", "")) for row in sentinels}
        ),
        "loss": _number_summary(row.get("loss") for row in sentinels),
        "n_recv_unique": _number_summary(row.get("n_recv_unique") for row in sentinels),
        "n_late_ratio": _number_summary(row.get("n_late_ratio") for row in sentinels),
        "q_mean_ms": _number_summary(row.get("q_mean_ms") for row in sentinels),
        "err_qs_corrected_ms": _number_summary(
            row.get("err_qs_corrected_ms") for row in sentinels
        ),
    }


def build_report(rows: Sequence[Row], state_path: str, sealed_dir: str) -> Dict[str, Any]:
    regular = [row for row in rows if str(row.get("block")) != "S"]
    homogeneous = [
        row for row in regular if bool(row.get("homogeneous_a14", False))
    ]
    return {
        "metadata": {
            "script_version": SCRIPT_VERSION,
            "state_path": state_path,
            "sealed_dir": sealed_dir,
            "delta_hat_ms": DELTA_HAT_MS,
            "delta_se_ms": DELTA_SE_MS,
            "homogeneous_n_late_max": HOMOGENEOUS_N_LATE_MAX,
            "model_path": MODEL_PATH,
            "confirmatory_note": (
                "Script locked and fake-tested before reading real sealed data."
            ),
        },
        "counts": {
            "n_all": len(rows),
            "n_regular": len(regular),
            "n_sentinel": len(rows) - len(regular),
            "n_homogeneous_regular": len(homogeneous),
            "n_warn_n_late_regular": sum(
                1 for row in regular if bool(row.get("warn_n_late", False))
            ),
        },
        "summary_all_regular": summarize_rows(regular),
        "summary_homogeneous_regular": summarize_rows(homogeneous),
        "summary_by_mode": grouped_summary(regular, ("mode",)),
        "summary_by_mode_a_tau": grouped_summary(
            regular, ("mode", "a", "tau_rho")
        ),
        "summary_by_cell": grouped_summary(
            regular, ("mode", "rho_bar", "a", "tau_rho")
        ),
        "sentinel": sentinel_summary(rows),
        "rows": list(rows),
    }


def write_fake_sealed(public_rows: Sequence[Row], sealed_dir: str, model: LinkModelV2) -> None:
    os.makedirs(sealed_dir, exist_ok=True)
    for row in public_rows:
        base = _core_terms({**row, "q_mean_ms": 0.0}, model)["q_psa_load_ms"]
        idx = int(row["idx"])
        jitter = 0.004 * math.sin((idx + 1) * 1.61803398875)
        q_mean = max(0.0, base + DELTA_HAT_MS + jitter)
        spread = max(0.01, abs(q_mean) * 0.05)
        sealed = {
            "q_mean_ms": q_mean,
            "q_sd_ms": spread,
            "q_p50_ms": q_mean,
            "q_p90_ms": q_mean + 0.80 * spread,
            "q_p95_ms": q_mean + 1.10 * spread,
            "q_p99_ms": q_mean + 1.70 * spread,
            "se_batch_ms": max(DELTA_SE_MS, spread / 12.0),
            "se_naive_ms": max(DELTA_SE_MS / 2.0, spread / 40.0),
            "probe_mean_ms": q_mean - 0.002,
            "delta_pasta_ms": 0.002,
        }
        payload = {"pid": row["pid"], "sealed": sealed}
        path = os.path.join(sealed_dir, str(row["pid"]) + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_jsonable(payload), f, indent=1, sort_keys=True)


def _print_report_summary(report: Mapping[str, Any]) -> None:
    counts = report["counts"]
    all_reg = report["summary_all_regular"]["err_qs_corrected_ms"]
    homog = report["summary_homogeneous_regular"]["err_qs_corrected_ms"]
    sentinel = report["sentinel"]
    print(
        "T6 rows all=%d regular=%d sentinel=%d homogeneous_regular=%d"
        % (
            counts["n_all"],
            counts["n_regular"],
            counts["n_sentinel"],
            counts["n_homogeneous_regular"],
        )
    )
    print(
        "err_qs_corrected regular: n=%d mean=%+.6f ms sd=%s p50=%+.6f ms"
        % (
            all_reg["n"],
            float(all_reg["mean"]),
            "None" if all_reg["sd"] is None else "%.6f ms" % float(all_reg["sd"]),
            float(all_reg["p50"]),
        )
    )
    print(
        "err_qs_corrected homogeneous: n=%d mean=%+.6f ms sd=%s p50=%+.6f ms"
        % (
            homog["n"],
            float(homog["mean"]),
            "None" if homog["sd"] is None else "%.6f ms" % float(homog["sd"]),
            float(homog["p50"]),
        )
    )
    if sentinel.get("n"):
        loss = sentinel["loss"]
        q_mean = sentinel["q_mean_ms"]
        print(
            "sentinel: n=%d loss_mean=%.8f q_mean_mean=%.6f ms"
            % (
                sentinel["n"],
                float(loss["mean"]),
                float(q_mean["mean"]),
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", default=STATE)
    parser.add_argument("--sealed-dir", default=SEALED)
    parser.add_argument("--out", default="-")
    parser.add_argument(
        "--make-fake-sealed",
        default=None,
        help="write fake sealed files to this directory and exit",
    )
    args = parser.parse_args()

    public_rows = _load_state_rows(args.state)
    model = LinkModelV2.load(MODEL_PATH)

    if args.make_fake_sealed:
        write_fake_sealed(public_rows, args.make_fake_sealed, model)
        print(
            "wrote fake sealed rows: n=%d dir=%s"
            % (len(public_rows), args.make_fake_sealed)
        )
        return

    rows = analyze_rows(combine_rows(public_rows, args.sealed_dir), model)
    report = build_report(rows, args.state, args.sealed_dir)
    text = json.dumps(_jsonable(report), indent=1, sort_keys=True)
    _print_report_summary(report)
    if args.out == "-":
        print(text)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print("wrote report -> %s" % args.out)


if __name__ == "__main__":
    main()

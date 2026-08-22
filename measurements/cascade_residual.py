#!/usr/bin/env python3
"""Phase 20R.6-v2 -- measure the cascade residual r = C - sum(B_i).

Estimand: difference between the mean cost measured directly on a 3-link path
(branch C) and the composed cost of the same three links measured separately
(branch B), in the same TandemTopo design and paired by seed/trajectory.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from measurements import residual_spec as RS


TANDEM_LINKS = ("L1", "L2", "L3")
N_BOOT = 2000
DELTA_LOSS_LEGACY = 0.005
DELTA_DELAY_MS_LEGACY = 0.44


def load_rows(paths: Sequence[str], branch: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
        for row in state.get("rows", []):
            if str(row.get("branch")) == branch:
                copied = dict(row)
                copied["_state_file"] = path
                copied["_probe_size"] = state.get("probe_size_bytes")
                copied["_probe_rate"] = row.get("probe_rate_pps_configured", state.get("probe_rate_pps"))
                copied["_carve_out_fraction"] = row.get("carve_out_fraction", state.get("carve_out_fraction"))
                rows.append(copied)
    if not rows:
        raise ValueError(
            "KHONG co row nao cho nhanh %r trong %s. Join rong -> DUNG (RC8)."
            % (branch, list(paths))
        )
    return rows


def bg_loss(row: Mapping[str, Any], link: str) -> float:
    for load_row in row.get("load_rows", []):
        if str(load_row.get("link")) == str(link):
            sent = float(load_row["n_bg_sent"])
            recv = float(load_row["n_bg_recv"])
            if sent <= 0:
                raise ValueError("n_bg_sent = 0 tren %s -- load khong chay?" % link)
            return 1.0 - recv / sent
    raise KeyError("khong tim thay load_rows cho link %s" % link)


def bg_n(row: Mapping[str, Any], link: str) -> int:
    for load_row in row.get("load_rows", []):
        if str(load_row.get("link")) == str(link):
            return int(load_row["n_bg_sent"])
    raise KeyError(link)


def path_loss(row: Mapping[str, Any]) -> float:
    sent = float(row["n_sent"])
    recv = float(row["n_recv_unique"])
    if sent <= 0:
        raise ValueError("n_sent = 0 -- dong do khong chay?")
    return 1.0 - recv / sent


def measured_probe_loss(row: Mapping[str, Any]) -> float:
    if row.get("probe_loss") is not None:
        return float(row["probe_loss"])
    return path_loss(row)


def assert_structural_invariant(rows_b: Sequence[Mapping[str, Any]], rows_c: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Branch B and C must match except for how many links the measured flow crosses."""

    def signature(rows: Sequence[Mapping[str, Any]]) -> Dict[str, set]:
        return {
            "probe_size": {row.get("_probe_size") for row in rows},
            "probe_rate": {row.get("_probe_rate") for row in rows},
            "carve_out_fraction": {row.get("_carve_out_fraction") for row in rows},
            "modes": {str(row["mode"]) for row in rows},
            "rho_bars": {round(float(row["rho_bar"]), 6) for row in rows},
            "seeds": {int(row["seed"]) for row in rows},
        }

    sig_b, sig_c = signature(rows_b), signature(rows_c)
    problems = []
    for key in ("probe_size", "probe_rate", "carve_out_fraction", "modes", "rho_bars", "seeds"):
        if sig_b[key] != sig_c[key]:
            problems.append("%s: B=%s C=%s" % (key, sorted(sig_b[key]), sorted(sig_c[key])))
    if problems:
        raise AssertionError(
            "VI PHAM BAT BIEN CAU TRUC (Amd 14):\n  "
            + "\n  ".join(problems)
            + "\nKet qua KHONG duoc bao cao."
        )
    return {"branch_b": {key: sorted(val) for key, val in sig_b.items()}, "branch_c": {key: sorted(val) for key, val in sig_c.items()}}


def traversed_link_digest(row: Mapping[str, Any], link: str) -> str:
    """Return the background schedule digest for the link crossed by the probe."""
    digests = row.get("load_schedule_digests")
    key = str(link)
    if not isinstance(digests, Mapping) or key not in digests:
        raise KeyError("thieu load_schedule_digests[%r] -- state cu?" % key)
    return str(digests[key])


def paired_residuals(
    rows_b: Sequence[Mapping[str, Any]],
    rows_c: Sequence[Mapping[str, Any]],
    mode: str,
    rho_bar: float,
    channel: str,
) -> Tuple[np.ndarray, List[int]]:
    residuals, _baselines, seeds = paired_residuals_with_baseline(
        rows_b, rows_c, mode, rho_bar, channel
    )
    return residuals, seeds


def paired_residuals_with_baseline(
    rows_b: Sequence[Mapping[str, Any]],
    rows_c: Sequence[Mapping[str, Any]],
    mode: str,
    rho_bar: float,
    channel: str,
) -> Tuple[np.ndarray, np.ndarray, List[int]]:
    idx_b: Dict[Tuple[int, str], Mapping[str, Any]] = {}
    for row in rows_b:
        if str(row["mode"]) == str(mode) and abs(float(row["rho_bar"]) - float(rho_bar)) <= 1e-9:
            idx_b[(int(row["seed"]), str(row["link"]))] = row

    idx_c: Dict[int, Mapping[str, Any]] = {}
    for row in rows_c:
        if str(row["mode"]) == str(mode) and abs(float(row["rho_bar"]) - float(rho_bar)) <= 1e-9:
            idx_c[int(row["seed"])] = row

    seeds = sorted(set(idx_c) & {seed for seed, _link in idx_b})
    if not seeds:
        raise ValueError("khong ghep duoc cap nao cho (%s, %.3f) -- o RONG (RC8)" % (mode, rho_bar))

    vals: List[float] = []
    baselines: List[float] = []
    kept: List[int] = []
    for seed in seeds:
        try:
            b_rows = [idx_b[(seed, link)] for link in TANDEM_LINKS]
        except KeyError:
            continue
        c_row = idx_c[seed]

        for link, row in zip(TANDEM_LINKS, b_rows):
            db = traversed_link_digest(row, link)
            dc = traversed_link_digest(c_row, link)
            if db != dc:
                raise AssertionError(
                    "lich link %s lech giua B va C o seed %d (B=%s C=%s) "
                    "-> KHONG phai paired that" % (link, seed, db[:12], dc[:12])
                )

        if channel == "loss":
            keep = 1.0
            for link, row in zip(TANDEM_LINKS, b_rows):
                keep *= 1.0 - measured_probe_loss(row)
            b_val = 1.0 - keep
            c_val = measured_probe_loss(c_row)
        elif channel == "delay_ms":
            b_val = float(sum(float(row["q_mean_ms"]) for row in b_rows))
            c_val = float(c_row["q_mean_ms"])
        else:
            raise ValueError("channel khong hop le: %s" % channel)

        vals.append(c_val - b_val)
        baselines.append(b_val)
        kept.append(seed)

    if len(vals) < 3:
        raise ValueError("chi ghep duoc %d cap -- qua it de bootstrap" % len(vals))
    return np.asarray(vals, dtype=float), np.asarray(baselines, dtype=float), kept


def bootstrap_seed_mean(diffs: np.ndarray, n_boot: int = N_BOOT, seed: int = 20206) -> Dict[str, float]:
    rng = np.random.default_rng(seed)
    n = int(diffs.size)
    means = np.asarray([rng.choice(diffs, size=n, replace=True).mean() for _ in range(int(n_boot))], dtype=float)
    return {
        "point": float(diffs.mean()),
        "se": float(means.std(ddof=1)),
        "ci90_lo": float(np.percentile(means, 5.0)),
        "ci90_hi": float(np.percentile(means, 95.0)),
        "n_pairs": int(n),
    }


def check_estimator_control(rows_b: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """DC-C3: compare background and probe loss only when arrivals match."""
    abs_z_applicable = []
    abs_z_all = []
    details = []
    for row in rows_b:
        link = str(row["link"])
        try:
            p_bg = bg_loss(row, link)
            p_probe = float(row["probe_loss"])
            n_bg = bg_n(row, link)
            n_probe = int(row["n_sent"])
        except (KeyError, ValueError):
            continue
        se = math.sqrt(
            max(p_bg * (1.0 - p_bg), 1e-12) / max(n_bg, 1)
            + max(p_probe * (1.0 - p_probe), 1e-12) / max(n_probe, 1)
        )
        z = (p_probe - p_bg) / se if se > 0 else 0.0
        applicable = str(row["mode"]) == "poisson"
        abs_z_all.append(abs(z))
        if applicable:
            abs_z_applicable.append(abs(z))
        details.append(
            {
                "link": link,
                "mode": str(row["mode"]),
                "seed": int(row["seed"]),
                "applicable": bool(applicable),
                "p_bg": p_bg,
                "p_carveout": p_probe,
                "z": z,
                "n_bg": n_bg,
                "n_carveout": n_probe,
            }
        )
    max_z_applicable = max(abs_z_applicable) if abs_z_applicable else float("nan")
    max_z_all = max(abs_z_all) if abs_z_all else float("nan")
    return {
        "control": "DC-C3 estimator",
        "max_abs_z": max_z_applicable,
        "max_abs_z_all_modes": max_z_all,
        "threshold_z": 3.0,
        "pass": bool(max_z_applicable <= 3.0),
        "applicable_modes": ["poisson"],
        "not_applicable_modes": ["h2"],
        "note": (
            "DC-C3 gates only rows where probe/background arrival process matches. "
            "For h2, Poisson probe and h2 background are expected to have different loss; "
            "see Amd 14 section 38 and DC-C3b."
        ),
        "details": details,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--branch-b", required=True, help="comma-separated branch B state files")
    ap.add_argument("--branch-c", required=True, help="comma-separated branch C state files")
    ap.add_argument("--modes", default="poisson,h2")
    ap.add_argument("--rho-bar", type=float, default=0.925)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    ap.add_argument("--out", default="results/SUPERSEDED/phase-20R/residual_cascade.json")
    args = ap.parse_args(argv)

    rows_b = load_rows([part.strip() for part in args.branch_b.split(",") if part.strip()], "B")
    rows_c = load_rows([part.strip() for part in args.branch_c.split(",") if part.strip()], "C")

    invariant = assert_structural_invariant(rows_b, rows_c)
    print("=== BAT BIEN CAU TRUC: DAT ===")
    print("  B: %s" % json.dumps(invariant["branch_b"], sort_keys=True))
    print("  C: %s" % json.dumps(invariant["branch_c"], sort_keys=True))

    dc3 = check_estimator_control(rows_b)
    print()
    print("=== DC-C3 (background vs carve-out) ===")
    print(
        "  max |z| applicable = %.3f (nguong 3.0) -> %s"
        % (dc3["max_abs_z"], "DAT" if dc3["pass"] else "*** KHONG DAT ***")
    )
    print("  max |z| all modes = %.3f (h2 khong gate)" % dc3["max_abs_z_all_modes"])
    if not dc3["pass"]:
        return 2

    records: List[RS.ResidualRecord] = []
    print()
    print("=== PHAN DU GHEP r = C - sum(B) ===")
    hdr = "%-8s %-9s %10s %10s %22s %8s %6s"
    print(hdr % ("mode", "kenh", "r", "se", "CI90", "n_cap", "CI~0"))
    for mode in [part.strip() for part in args.modes.split(",") if part.strip()]:
        for channel in ("loss", "delay_ms"):
            diffs, baselines, seeds = paired_residuals_with_baseline(
                rows_b, rows_c, mode, args.rho_bar, channel
            )
            bs = bootstrap_seed_mean(diffs, args.n_boot)
            baseline_magnitude = float(np.mean(baselines))
            relative_point = float(bs["point"]) / baseline_magnitude
            rec = RS.ResidualRecord(
                estimand=(
                    ("Chenh lech ton that trung binh" if channel == "loss" else "Chenh lech delay trung binh")
                    + " do end-to-end tren duong 3-link (nhanh C) tru dai luong "
                    "ghep tu tung link do rieng (nhanh B), cung topology/session/"
                    "seed/background/kich-thuoc-goi/carve-out. Bang tra A khong "
                    "tham gia. Kenh: %s." % channel
                ),
                source="cascade",
                channel=channel,
                level="per_path",
                mode=mode,
                point=bs["point"],
                se=bs["se"],
                rho_bar_measured=float(args.rho_bar),
                baseline_magnitude=baseline_magnitude,
                relative_point=relative_point,
                valid_range=None,
                per_unit={"seed_%d" % seed: float(val) for seed, val in zip(seeds, diffs)},
                provenance={
                    **RS.git_commit(),
                    "branch_b_files": [part.strip() for part in args.branch_b.split(",") if part.strip()],
                    "branch_c_files": [part.strip() for part in args.branch_c.split(",") if part.strip()],
                    "rho_bar": float(args.rho_bar),
                    "baseline_per_seed": {
                        "seed_%d" % seed: float(value)
                        for seed, value in zip(seeds, baselines)
                    },
                    "n_boot": int(args.n_boot),
                    "ci90_percentile": [bs["ci90_lo"], bs["ci90_hi"]],
                    "dc3": dc3,
                },
            )
            records.append(rec)
            lo, hi = rec.ci90
            print(
                hdr
                % (
                    mode,
                    channel,
                    "%+.6f" % rec.point,
                    "%.6f" % rec.se,
                    "[%+.6f, %+.6f]" % (lo, hi),
                    "%d" % bs["n_pairs"],
                    "co" if rec.ci_contains_zero else "khong",
                )
            )

    print()
    print("--- Doi chieu voi nguong CU (tham khao, khong phai gate) ---")
    for rec in records:
        delta = DELTA_LOSS_LEGACY if rec.channel == "loss" else DELTA_DELAY_MS_LEGACY
        print(
            "  %-8s %-9s power_ok(delta=%.4f) = %s [1.645*se = %.6f]"
            % (rec.mode, rec.channel, delta, rec.power_ok(delta), RS.Z90 * rec.se)
        )

    RS.save(records, args.out)
    print()
    print("-> %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

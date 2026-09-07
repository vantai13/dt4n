#!/usr/bin/env python3
"""L2.1 -- recompute the additivity decomposition from Phase 20R.6 artifacts.

AUDIT_NO_MEASUREMENT. No root, no netns, no tc, no Mininet, no traffic.
Every number is read back from artifacts that already exist in the repo.

    e_add   = sum_i B_i            - C            additivity error (measured only)
    e_model = sum_i predict(rho_i) - sum_i B_i    model error (twin vs measured link)
    e_total = sum_i predict(rho_i) - C            what the twin actually gets wrong

C   = branch C, one probe over the whole 3-link path
B_i = branch B, one probe over link i, ALL THREE links loaded
Paired by (mode, seed): same topology, same session, same background.

    python -m tools.l2_1_additivity_recheck
    python -m tools.l2_1_additivity_recheck --json OUT.json
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from typing import Dict, List, Sequence, Tuple

from twin.link_model_v2 import LinkModelV2

# mininet/topology_tandem.py:16-20 -- the three measured tandem classes
TANDEM_CLASS: Dict[str, Tuple[float, int]] = {
    "L1": (8.0, 18),
    "L2": (6.0, 13),
    "L3": (4.0, 10),
}
LINKS = ("L1", "L2", "L3")

BRANCH_B = (
    "results/SMOKE/phase-20R/branch_b_fixed_pilot3.json",
    "results/SUPERSEDED/phase-20R/branch_b_fixed_s104_108.json",
)
BRANCH_C = (
    "results/SMOKE/phase-20R/branch_c_fixed_pilot3.json",
    "results/SUPERSEDED/phase-20R/branch_c_fixed_s104_108.json",
)
FIT = "results/LIVE/phase-L/link_model_v2_fit.json"

# Amendment 14 section 42 -- the signed values this tool must reproduce.
SIGNED_R_PATH = {"poisson": -0.746400, "h2": -0.449241}

T90 = {8: 1.894579, 7: 1.894579, 6: 1.943180, 5: 2.015048}


def load_rows(paths: Sequence[str]) -> List[dict]:
    rows: List[dict] = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            rows.extend(json.load(handle)["rows"])
    return rows


def cbr_floor_ms(fit: dict, bw: float, q: int) -> float:
    """Software floor of the Phase L pipeline = the cbr level at the lowest rho.

    NOT `LinkModelV2.irreducible_floor_ms`, which returns `sigma_schedule`, a
    noise STANDARD DEVIATION. Subtracting an SD as if it were an offset is a
    category error; it is the mistake this tool exists to not repeat.
    """
    return float(fit["links"]["cbr|%g|%d" % (bw, q)]["delay_observed"][0])


def decompose(subtract_floor: bool = True) -> dict:
    model = LinkModelV2.load(FIT)
    with open(FIT, "r", encoding="utf-8") as handle:
        fit = json.load(handle)

    b_rows = load_rows(BRANCH_B)
    c_rows = load_rows(BRANCH_C)
    b_idx = {(r["mode"], r["seed"], r["link"]): r for r in b_rows}
    c_idx = {(r["mode"], r["seed"]): r for r in c_rows}

    out: Dict[str, dict] = {}
    for mode in sorted({r["mode"] for r in c_rows}):
        per_seed = []
        for seed in sorted({r["seed"] for r in c_rows if r["mode"] == mode}):
            try:
                b = [b_idx[(mode, seed, link)] for link in LINKS]
                c = c_idx[(mode, seed)]
            except KeyError:
                continue
            sum_b = sum(float(r["queue_mean_ms"]) for r in b)
            c_path = float(c["queue_mean_ms"])
            pred = 0.0
            rhos = {}
            for link, row in zip(LINKS, b):
                bw, q = TANDEM_CLASS[link]
                rho = float(row["rho_total_actual_by_link"][link])
                rhos[link] = rho
                floor = cbr_floor_ms(fit, bw, q) if subtract_floor else 0.0
                pred += model.predict_delay(mode, bw, q, rho) - floor
            per_seed.append({
                "seed": seed,
                "rho": rhos,
                "sum_b_ms": sum_b,
                "c_path_ms": c_path,
                "sum_pred_ms": pred,
                "e_add_ms": sum_b - c_path,
                "e_model_ms": pred - sum_b,
                "e_total_ms": pred - c_path,
            })
        out[mode] = {"per_seed": per_seed, "summary": summarise(per_seed)}
    return out


def summarise(per_seed: List[dict]) -> dict:
    n = len(per_seed)
    tcrit = T90.get(n, 1.894579)
    summary = {"n_pairs": n}
    for field in (
        "sum_b_ms",
        "c_path_ms",
        "sum_pred_ms",
        "e_add_ms",
        "e_model_ms",
        "e_total_ms",
    ):
        values = [row[field] for row in per_seed]
        mean = st.mean(values)
        se = st.stdev(values) / n**0.5 if n > 1 else 0.0
        summary[field] = {
            "mean": mean,
            "se": se,
            "ci90": [mean - tcrit * se, mean + tcrit * se],
        }
    c_mean = summary["c_path_ms"]["mean"]
    for field in ("e_add_ms", "e_model_ms", "e_total_ms"):
        summary[field + "_pct_of_path"] = (
            abs(summary[field]["mean"]) / c_mean * 100.0
        )
    # e_total = e_add + e_model holds by ALGEBRA on paired data, not by physics.
    summary["interaction_ms"] = max(
        abs(row["e_total_ms"] - row["e_add_ms"] - row["e_model_ms"])
        for row in per_seed
    )
    summary["interaction_is_algebraic_identity"] = True
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default=None)
    parser.add_argument(
        "--no-floor",
        action="store_true",
        help="do not subtract the cbr floor (sensitivity check)",
    )
    args = parser.parse_args()

    result = decompose(subtract_floor=not args.no_floor)

    print("L2.1 -- additivity decomposition, Phase 20R.6 tandem, rho_bar = 0.925")
    print("AUDIT_NO_MEASUREMENT: read-back only.\n")
    for mode, block in result.items():
        s = block["summary"]
        print(f"=== mode = {mode}   n_pairs = {s['n_pairs']}")
        for field in (
            "sum_b_ms",
            "c_path_ms",
            "sum_pred_ms",
            "e_add_ms",
            "e_model_ms",
            "e_total_ms",
        ):
            v = s[field]
            print(
                f"   {field:<12} {v['mean']:9.4f} +/- {v['se']:6.4f}"
                f"   CI90 = [{v['ci90'][0]:8.4f}, {v['ci90'][1]:8.4f}]"
            )
        print(f"   |e_add|/path   = {s['e_add_ms_pct_of_path']:6.2f} %")
        print(f"   |e_model|/path = {s['e_model_ms_pct_of_path']:6.2f} %")
        print(
            f"   |e_total|/path = {s['e_total_ms_pct_of_path']:6.2f} %"
            f"   (gate L2.4-5 threshold 15 %)"
        )
        signed = SIGNED_R_PATH.get(mode)
        if signed is not None:
            got = -s["e_add_ms"]["mean"]
            print(
                f"   r_path check: recomputed {got:+.6f} vs Amd14 sec42"
                f" {signed:+.6f}  delta {abs(got - signed):.2e}"
            )
        print()

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema": "dt4n.phase_l2.additivity_recheck.v1",
                    "kind": "AUDIT_NO_MEASUREMENT",
                    "sources": {
                        "branch_b": list(BRANCH_B),
                        "branch_c": list(BRANCH_C),
                        "fit": FIT,
                    },
                    "results": result,
                },
                handle,
                indent=1,
            )
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()

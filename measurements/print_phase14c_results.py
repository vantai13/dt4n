"""Print Phase 14C pilot results as a terminal table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev


def _fmt(value: float, width: int, digits: int) -> str:
    return f"{value:>{width}.{digits}f}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print Phase 14C pilot JSON results as a terminal table."
    )
    parser.add_argument(
        "--glob",
        default="results/phase-14c/pilot3_v3_*.json",
        help="Result-file glob to summarize.",
    )
    parser.add_argument("--json-out", default=None,
                        help="optional JSON summary output path")
    parser.add_argument("--txt-out", default=None,
                        help="optional text-table output path")
    parser.add_argument("--no-print", action="store_true",
                        help="write outputs without printing the table")
    args = parser.parse_args()

    candidates = sorted(Path().glob(args.glob))
    files = []
    for file_path in candidates:
        try:
            data = json.loads(file_path.read_text())
        except json.JSONDecodeError:
            continue
        if {"objective", "gap_mean", "gap_lower", "seed"}.issubset(data):
            files.append((file_path, data))

    if not files:
        print(f"Khong thay file nao: {args.glob}")
        return 1

    groups: dict[str, list[float]] = {}
    rows: list[dict] = []
    lines: list[str] = []

    lines.append(
        f"{'file':<36} {'obj':<6} {'gap':>9} {'lower':>9} "
        f"{'disag':>7} {'regret':>8} {'qmarg':>8} {'verdict':>7}"
    )
    lines.append("-" * 97)

    for file_path, data in files:
        objective = data["objective"]
        group = objective
        if objective == "cvar":
            group += "_a" + str(data["cvar_alpha"])
        groups.setdefault(group, []).append(data["gap_mean"])

        row = {
            "file": file_path.name,
            "objective": objective,
            "cvar_alpha": data["cvar_alpha"] if objective == "cvar" else None,
            "seed": data["seed"],
            "gap": data["gap_mean"],
            "lower": data["gap_lower"],
            "disagree": data["disagree_rate"],
            "regret": data["decision_regret"],
            "q_margin": data["q_margin"],
            "verdict": data["verdict"],
        }
        rows.append(row)

        lines.append(
            f"{file_path.name:<36} {objective:<6} "
            f"{_fmt(data['gap_mean'], 9, 5)} "
            f"{_fmt(data['gap_lower'], 9, 5)} "
            f"{_fmt(data['disagree_rate'], 7, 4)} "
            f"{_fmt(data['decision_regret'], 8, 5)} "
            f"{_fmt(data['q_margin'], 8, 4)} "
            f"{data['verdict']:>7}"
        )

    lines.append("")
    lines.append("TRUNG BINH QUA SEED:")
    summary = {}
    for group, values in groups.items():
        summary[group] = {
            "gap_mean": mean(values),
            "gap_std": pstdev(values),
            "n": len(values),
        }
        lines.append(
            f"  {group:<12}: {summary[group]['gap_mean']:.5f}  "
            f"(std {summary[group]['gap_std']:.5f})"
        )

    table = "\n".join(lines) + "\n"
    if not args.no_print:
        print(table, end="")

    if args.txt_out:
        txt_path = Path(args.txt_out)
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(table)
        if not args.no_print:
            print(f"-> wrote {txt_path}")

    if args.json_out:
        json_path = Path(args.json_out)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source_glob": args.glob,
            "rows": rows,
            "summary": summary,
        }
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        if not args.no_print:
            print(f"-> wrote {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

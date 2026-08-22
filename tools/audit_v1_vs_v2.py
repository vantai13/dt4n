#!/usr/bin/env python3
"""Phase 20R inherited audit: quantify v1-vs-v2 model drift.

This script is intentionally small and read-only with respect to experiment
artifacts. It regenerates the four tables embedded in
``docs/phase-20R/01-inherited-audit.md`` from the frozen Phase 20 calibration,
``topology_v7``, and the Phase L ``link_model_v2`` fit.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from twin import topology_v7 as T7  # noqa: E402
from twin.link_model import loss_rate, total_delay_ms  # noqa: E402
from twin.link_model_v2 import LinkModelV2  # noqa: E402


FRAME_BYTES = 1512
MODEL_PATH = REPO_ROOT / "results/LIVE/phase-L/link_model_v2_fit.json"
PHASE20_CALIBRATION_PATH = REPO_ROOT / "results/SUPERSEDED/phase-20/decision_error_offered.json"
TABLE_DIR = REPO_ROOT / "docs/phase-20R/tables"
AUDIT_PATH = REPO_ROOT / "docs/phase-20R/01-inherited-audit.md"
AUDIT_DATE = "2026-08-04"
RHO_GRID_WITH_REJECTED = (0.70, 0.85, 0.925, 0.98, 0.96)
RHO_GRID_FINAL = (0.70, 0.85, 0.925, 0.96)
SIGMA_RHO = 0.010
RHO_MIN = 0.50
RHO_MAX = 1.05


def serialization_ms(bw_mbps: float) -> float:
    return FRAME_BYTES * 8.0 / (float(bw_mbps) * 1e6) * 1000.0


def load_mean() -> float:
    return sum(float(T7.LOAD_MEAN[link]) for link in T7.LINK_NAMES) / len(T7.LINK_NAMES)


def offsets() -> Dict[str, float]:
    mean = load_mean()
    return {link: float(T7.LOAD_MEAN[link]) - mean for link in T7.LINK_NAMES}


def rho_from_bar(rho_bar: float) -> Dict[str, float]:
    off = offsets()
    return {
        link: min(max(float(rho_bar) + off[link], RHO_MIN), RHO_MAX)
        for link in T7.LINK_NAMES
    }


def phase20_calibration() -> Dict[str, float]:
    with PHASE20_CALIBRATION_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    c = data["config"]["calibration"]
    return {
        "t_delay_ms": float(c["t_delay_ms"]),
        "t_loss": float(c["t_loss"]),
        "w_loss": float(c["w_loss"]),
        "optimal_violation": float(c["optimal_violation"]),
    }


def link_v1(link: str, rho: float | None = None) -> Tuple[float, float]:
    bw, base, q = T7.LINKS[link]
    r = float(T7.LOAD_MEAN[link] if rho is None else rho)
    return total_delay_ms(base, r, bw_mbps=bw, queue_pkts=q), loss_rate(r)


def link_v2(
    model: LinkModelV2,
    link: str,
    rho: float | None = None,
    mode: str = "poisson",
) -> Tuple[float, float]:
    bw, base, q = T7.LINKS[link]
    r = float(T7.LOAD_MEAN[link] if rho is None else rho)
    delay = base + serialization_ms(bw) + model.predict_delay(mode, bw, q, r)
    loss = model.predict_loss(mode, bw, q, r)
    return delay, loss


def path_metrics(
    link_metric: Callable[[str], Tuple[float, float]],
    path: str,
    w_loss: float,
) -> Tuple[float, float, float]:
    delay = 0.0
    keep = 1.0
    for link in T7.PATHS[path]:
        d, loss = link_metric(link)
        delay += d
        keep *= 1.0 - loss
    loss = 1.0 - keep
    return delay, loss, delay + float(w_loss) * loss


def format_block(title: str, header: str, rows: Iterable[str]) -> str:
    return "\n".join([title, header, *rows])


def table1_link_drift(model: LinkModelV2) -> str:
    rows = []
    for link in T7.LINK_NAMES:
        bw, _base, q = T7.LINKS[link]
        rho = float(T7.LOAD_MEAN[link])
        d1, l1 = link_v1(link)
        d2, l2 = link_v2(model, link)
        rows.append(
            "%-4s %4.0f %3d %.4f | %9.3f %8.5f | %9.3f %8.5f | %5.2fx"
            % (link, bw, q, rho, d1, l1, d2, l2, d2 / d1)
        )
    return format_block(
        "BANG 1 -- lech theo link tai LOAD_MEAN (mode=poisson)",
        "link   bw   q   rho   |  v1_delay  v1_loss |  v2_delay  v2_loss | v2/v1",
        rows,
    )


def table2_path_ranking(model: LinkModelV2) -> str:
    c = phase20_calibration()
    rows = []
    for label, metric in (
        ("v1", lambda link: link_v1(link)),
        ("v2", lambda link: link_v2(model, link)),
    ):
        vals = [
            (path, *path_metrics(metric, path, c["w_loss"]))
            for path in T7.PATH_NAMES
        ]
        for rank, (path, delay, loss, cost) in enumerate(sorted(vals, key=lambda x: x[3]), 1):
            rows.append(
                "%-2s %4d %-4s | %9.3f %8.5f %9.3f"
                % (label, rank, path, delay, loss, cost)
            )
    return format_block(
        "BANG 2 -- xep hang path tai LOAD_MEAN (mode=poisson, w_loss Phase 20)",
        "model rank path |  delay_ms     loss   cost_ms",
        rows,
    )


def uniform_v2_path_metrics(
    model: LinkModelV2,
    rho_bar: float,
    path: str,
    w_loss: float,
    mode: str = "poisson",
) -> Tuple[float, float, float]:
    return path_metrics(lambda link: link_v2(model, link, float(rho_bar), mode), path, w_loss)


def table3_old_sla_under_v2(model: LinkModelV2) -> str:
    c = phase20_calibration()
    rows = []
    for rho_bar in (0.70, 0.85, 0.925, 0.98):
        vals = [
            (path, *uniform_v2_path_metrics(model, rho_bar, path, c["w_loss"]))
            for path in T7.PATH_NAMES
        ]
        by_cost = sorted(vals, key=lambda x: x[3])
        best_path, best_delay, best_loss, _best_cost = by_cost[0]
        delay_viol = sum(1 for _p, delay, _loss, _cost in vals if delay > c["t_delay_ms"])
        loss_viol = sum(1 for _p, _delay, loss, _cost in vals if loss > c["t_loss"])
        opt_viol = (best_delay > c["t_delay_ms"]) or (best_loss > c["t_loss"])
        rows.append(
            "%.3f   %-4s | %9.3f %8.5f | %+8.3f | %d/%d %d/%d | %s"
            % (
                rho_bar,
                best_path,
                best_delay,
                best_loss,
                best_delay - c["t_delay_ms"],
                delay_viol,
                T7.K,
                loss_viol,
                T7.K,
                "YES" if opt_viol else "NO",
            )
        )
    title = (
        "BANG 3 -- nguong SLA Phase 20 duoi v2 "
        "(mode=poisson, rho dong nhat de lay can duoi)"
    )
    header = (
        "rho_bar best |  opt_delay opt_loss | delay-T20 | "
        "delay_viol loss_viol | opt_viol"
    )
    return format_block(title, header, rows)


def normal_lower_tail(x: float, mean: float, sigma: float) -> float:
    z = (float(x) - float(mean)) / float(sigma)
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def normal_upper_tail(x: float, mean: float, sigma: float) -> float:
    z = (float(x) - float(mean)) / float(sigma)
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def clip_stats_for_link(rho_bar: float, link: str) -> Tuple[float, float, float, float]:
    mu = float(rho_bar) + offsets()[link]
    p_low = normal_lower_tail(RHO_MIN, mu, SIGMA_RHO)
    p_high = normal_upper_tail(RHO_MAX, mu, SIGMA_RHO)
    return mu, p_low, p_high, p_low + p_high


def table4_clip_diagnostic() -> str:
    rows = []
    for rho_bar in RHO_GRID_WITH_REJECTED:
        stats = [
            (link, *clip_stats_for_link(rho_bar, link))
            for link in T7.LINK_NAMES
        ]
        link, mu, p_low, p_high, p_total = max(stats, key=lambda x: x[4])
        verdict = "REJECT" if abs(rho_bar - 0.98) < 1e-12 else "OK"
        rows.append(
            "%.3f   %-4s %.4f | %9.4f %9.4f %10.4f | %s"
            % (rho_bar, link, mu, 100.0 * p_low, 100.0 * p_high, 100.0 * p_total, verdict)
        )
    return format_block(
        "BANG 4 -- chan doan clipping Q7 (sigma_rho=0.010, domain=[0.50,1.05])",
        "rho_bar link mean | clip_low% clip_high% clip_total% | verdict",
        rows,
    )


def all_tables() -> List[Tuple[str, str]]:
    model = LinkModelV2.load(str(MODEL_PATH))
    return [
        ("bang1.txt", table1_link_drift(model)),
        ("bang2.txt", table2_path_ranking(model)),
        ("bang3.txt", table3_old_sla_under_v2(model)),
        ("bang4.txt", table4_clip_diagnostic()),
    ]


def static_path_delays() -> str:
    rows = []
    for path in T7.PATH_NAMES:
        delay = 0.0
        for link in T7.PATHS[path]:
            bw, base, _q = T7.LINKS[link]
            delay += base + serialization_ms(bw)
        rows.append("%s = %.3f ms" % (path, delay))
    return " ; ".join(rows)


def write_tables(table_dir: Path) -> None:
    table_dir.mkdir(parents=True, exist_ok=True)
    for name, text in all_tables():
        (table_dir / name).write_text(text + "\n", encoding="utf-8")


def audit_markdown() -> str:
    c = phase20_calibration()
    table_map = dict(all_tables())
    body = [
        "# INHERITED AUDIT -- Phase 20R",
        "",
        "Ngay lap: %s" % AUDIT_DATE,
        "Trang thai: viet truoc khi sinh `results/SUPERSEDED/phase-20R/`. Khong sua nguoc Phase 20.",
        "",
        "## Muc dich",
        "",
        "Phase 20 da dong bang tai tag `phase-20-complete`. Audit nay ghi ro vi sao",
        "`err = 0.187` va `d_sla = 0.081` chi con la phu luc v7, khong duoc",
        "trich dan nhu ket qua khoa hoc cua Phase 20R.",
        "",
        "Moi bang ben duoi duoc sinh lai bang:",
        "",
        "```bash",
        "python3 tools/audit_v1_vs_v2.py --write",
        "```",
        "",
        "Nguon so lieu: `twin/topology_v7.py`, `twin/link_model.py`,",
        "`twin/link_model_v2.py`, `results/LIVE/phase-L/link_model_v2_fit.json`, va",
        "`results/SUPERSEDED/phase-20/decision_error_offered.json`.",
        "",
        "## Bang 1 -- link_model v1 -> v2 la sai so vi sai",
        "",
        "```text",
        table_map["bang1.txt"],
        "```",
        "",
        "Ket luan: v2/v1 khong dong pha. Tai LOAD_MEAN, `ad` giam xuong 0.61x",
        "trong khi `bd` tang len 2.00x. Do la differential error, khong phai",
        "common-mode error.",
        "",
        "## Bang 2 -- xep hang path bi doi",
        "",
        "```text",
        table_map["bang2.txt"],
        "```",
        "",
        "Ket luan: thu tu `P3`/`P4` hoan vi khi thay v1 bang v2. Vi ranking la",
        "doi tuong duoc do trong `P(argmin_twin != argmin_true)`, Phase 20 khong",
        "the duoc ke thua nhu dap an that.",
        "",
        "## Bang 3 -- nguong SLA cu nam duoi phan phoi v2",
        "",
        "Nguong Phase 20 doc tu artifact:",
        "",
        "```text",
        "T_delay = %.4f ms" % c["t_delay_ms"],
        "T_loss  = %.5f" % c["t_loss"],
        "w_loss  = %.4f" % c["w_loss"],
        "opt_viol_rate = %.4f" % c["optimal_violation"],
        "```",
        "",
        "```text",
        table_map["bang3.txt"],
        "```",
        "",
        "Ket luan: ngay ca o `rho_bar = 0.70`, delay toi uu duoi v2 da la",
        "`15.35 ms`, cao hon `T_delay` cu `14.5138 ms`. Neu giu nguong cu,",
        "`d_sla` bi mat do phan giai mot cach co hoc.",
        "",
        "## Bang 4 -- Q7 phai sua rho_bar max",
        "",
        "Offset dung: mean(LOAD_MEAN) = %.4f; offset = LOAD_MEAN[link] - mean."
        % load_mean(),
        "",
        "```text",
        table_map["bang4.txt"],
        "```",
        "",
        "Ket luan: `rho_bar = 0.98` lam link `ad` bi clip khoang 22.66%, qua lon",
        "de coi la threat nho. Phase 20R chot `rho_bar max = 0.96`; khi do clip",
        "xau nhat con khoang 0.30%.",
        "",
        "## Hanh dong",
        "",
        "1. Khong chay lai Phase 20.",
        "2. Khong sua `results/SUPERSEDED/phase-20/`.",
        "3. Them erratum moi tai `docs/phase-20/99c-erratum-2.md`.",
        "4. Phase 20R dung `link_model_v2` va pre-registration Q1-Q7.",
        "",
        "## Ghi chu tinh",
        "",
        "Shortest-hop tinh theo `base + serialization`: %s." % static_path_delays(),
    ]
    return "\n".join(body) + "\n"


def write_audit(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(audit_markdown(), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="write tables and audit markdown")
    ap.add_argument("--tables-dir", default=str(TABLE_DIR), help="table output directory")
    ap.add_argument("--audit", default=str(AUDIT_PATH), help="audit markdown output path")
    args = ap.parse_args(argv)

    if args.write:
        write_tables(Path(args.tables_dir))
        write_audit(Path(args.audit))

    for _name, text in all_tables():
        print(text)
        print()
    if args.write:
        print("WROTE %s" % args.tables_dir)
        print("WROTE %s" % args.audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

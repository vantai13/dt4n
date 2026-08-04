#!/usr/bin/env python3
"""Phase 20R.2 -- calibrate SLA thresholds per operating regime.

The calibration target is not "use p85". It is:

    P((delay > T_delay) OR (loss > T_loss) | optimal path) = 0.15

For each feasible ``(mode, rho_bar)`` cell we solve the percentile ``p`` by
bisection, then iterate the fixed point ``w_loss = T_delay / LOSS_EXCHANGE``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

from twin import cost_v2 as C
from twin import topology_v7 as T7


LOSS_EXCHANGE = 0.01
TARGET_VIOL = 0.15
VIOL_BAND = (0.10, 0.25)
P_LO, P_HI = 50.0, 99.9
N_BISECT = 40
N_FIXPOINT = 12
TOL_W = 1e-6

RHO_BAR_GRID = (0.70, 0.85, 0.925, 0.96)
MODE_GRID = ("cbr", "poisson", "h2")
DEFAULT_N = 200_000
DEFAULT_DT = 0.005
DEFAULT_TAU = 1.0
DEFAULT_A = 0.9
DEFAULT_SEED = 100

RESULT_PATH = "results/phase-20R/sla_calibration.json"
DOC_PATH = "docs/phase-20R/03-sla-calibration.md"
FIGURE_PATH = "docs/phase-20R/figures/opt_path_share.svg"
AMENDMENT_PATH = "docs/phase-20R/00c-amendment-2.md"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ar1_matrix(
    mode: str,
    rho_bar: float,
    sigma: float,
    tau: float,
    dt: float,
    n: int,
    seed: int,
) -> np.ndarray:
    """Return rho matrix ``(n, 8)``: independent AR(1) per link.

    Values are clipped to the measured/reliable range of the selected traffic
    family. For ``cbr`` this upper bound is 0.95, so the CostV2 reliability
    guard can remain strict during calibration.
    """
    rng = np.random.default_rng(int(seed))
    phi = float(np.exp(-float(dt) / float(tau)))
    sd_eps = float(sigma) * math.sqrt(max(1.0 - phi * phi, 0.0))
    hi = float(C.RELIABLE_CEILING[mode])
    out = np.empty((int(n), len(T7.LINK_NAMES)), dtype=float)
    for i, link in enumerate(T7.LINK_NAMES):
        mu = float(rho_bar) + C.LINK_OFFSET[link]
        shocks = rng.standard_normal(int(n)) * sd_eps
        x = np.empty(int(n), dtype=float)
        x[0] = mu + float(sigma) * rng.standard_normal()
        for t in range(1, int(n)):
            x[t] = mu + phi * (x[t - 1] - mu) + shocks[t]
        out[:, i] = np.clip(x, C.RHO_MIN, hi)
    return out


def _optimal_series(delay: np.ndarray, loss: np.ndarray, opt: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    rows = np.arange(delay.shape[0])
    return delay[rows, opt], loss[rows, opt]


def viol_rate_at_p(
    delay: np.ndarray,
    loss: np.ndarray,
    opt: np.ndarray,
    p: float,
) -> Tuple[float, float, float]:
    """Return optimal-policy violation rate when both thresholds use percentile p."""
    d_opt, l_opt = _optimal_series(delay, loss, opt)
    t_delay = float(np.percentile(d_opt, float(p)))
    t_loss = float(np.percentile(l_opt, float(p)))
    viol = (d_opt > t_delay) | (l_opt > t_loss)
    return float(viol.mean()), t_delay, t_loss


def solve_percentile(
    delay: np.ndarray,
    loss: np.ndarray,
    opt: np.ndarray,
    target: float = TARGET_VIOL,
) -> Tuple[float, float, float, float]:
    """Solve p so the OR-coupled optimal violation rate matches target."""
    lo, hi = P_LO, P_HI
    best = None
    for _ in range(N_BISECT):
        mid = 0.5 * (lo + hi)
        viol, t_delay, t_loss = viol_rate_at_p(delay, loss, opt, mid)
        best = (mid, t_delay, t_loss, viol)
        if viol > float(target):
            lo = mid
        else:
            hi = mid
    assert best is not None
    return best


def _opt_path_share(opt: np.ndarray) -> Dict[str, float]:
    return {T7.PATH_NAMES[k]: float(np.mean(opt == k)) for k in range(T7.K)}


def _clip_fraction(rho_mat: np.ndarray, mode: str) -> float:
    hi = float(C.RELIABLE_CEILING[mode])
    clipped = (rho_mat <= C.RHO_MIN + 1e-12) | (rho_mat >= hi - 1e-12)
    return float(clipped.mean())


def calibrate_cell(
    cv2: C.CostV2,
    mode: str,
    rho_bar: float,
    seed: int,
    n: int = DEFAULT_N,
    dt: float = DEFAULT_DT,
    tau: float = DEFAULT_TAU,
    a: float = DEFAULT_A,
) -> Dict[str, object]:
    sigma = C.sigma_from_a_regime(mode, rho_bar, a)
    sigma_max = C.sigma_max_regime(mode, rho_bar)
    base = {
        "mode": mode,
        "rho_bar": float(rho_bar),
        "a": float(a),
        "sigma_max": float(sigma_max),
        "sigma_rho": float(sigma),
        "tau_rho": float(tau),
        "dt": float(dt),
        "n": int(n),
        "seed": int(seed),
        "loss_exchange": LOSS_EXCHANGE,
        "target_viol": TARGET_VIOL,
        "reliable_ceiling": float(C.RELIABLE_CEILING[mode]),
    }
    if sigma <= 0.0:
        return {
            **base,
            "feasible": False,
            "in_band": False,
            "role": "pc1_excluded_by_q8" if mode == "cbr" else "excluded",
            "reason": "sigma_max_regime = 0 (het headroom den tran do tin cay)",
        }

    rho_mat = ar1_matrix(mode, rho_bar, sigma, tau, dt, n, seed)
    clip = _clip_fraction(rho_mat, mode)
    w_loss = 2500.0
    history = []
    converged = False
    p = t_delay = t_loss = opt_viol = float("nan")
    for round_idx in range(N_FIXPOINT):
        delay, loss, cost = cv2.tables_batch(rho_mat, mode, w_loss)
        opt = np.argmin(cost, axis=1)
        p, t_delay, t_loss, opt_viol = solve_percentile(delay, loss, opt)
        w_new = t_delay / LOSS_EXCHANGE
        history.append(
            {
                "round": int(round_idx),
                "w_loss_input": float(w_loss),
                "percentile": float(p),
                "t_delay_ms": float(t_delay),
                "t_loss": float(t_loss),
                "opt_viol_at_percentile": float(opt_viol),
                "w_loss_next": float(w_new),
            }
        )
        if abs(w_new - w_loss) < TOL_W:
            w_loss = float(w_new)
            converged = True
            break
        w_loss = float(w_new)
    if not converged:
        raise RuntimeError("fixed point did not converge for %s rho_bar=%.3f" % (mode, rho_bar))

    delay, loss, cost = cv2.tables_batch(rho_mat, mode, w_loss)
    opt = np.argmin(cost, axis=1)
    p, t_delay, t_loss, _ = solve_percentile(delay, loss, opt)
    rows = np.arange(int(n))
    viol = (delay > t_delay) | (loss > t_loss)
    opt_viol = float(viol[rows, opt].mean())
    margin = np.sort(cost, axis=1)[:, 1] - np.sort(cost, axis=1)[:, 0]
    in_band = bool(VIOL_BAND[0] <= opt_viol <= VIOL_BAND[1])
    role = "gate" if in_band and mode != "cbr" else ("pc1" if mode == "cbr" else "excluded")
    return {
        **base,
        "feasible": True,
        "role": role,
        "percentile": float(p),
        "t_delay_ms": float(t_delay),
        "t_loss": float(t_loss),
        "w_loss": float(w_loss),
        "opt_viol_rate": opt_viol,
        "in_band": in_band,
        "clip_fraction": clip,
        "cost_margin_mean_ms": float(margin.mean()),
        "cost_margin_p10_ms": float(np.percentile(margin, 10)),
        "opt_path_share": _opt_path_share(opt),
        "fixpoint_rounds": int(len(history)),
        "fixpoint_converged": True,
        "fixpoint_history": history,
    }


def run_calibration(
    n: int = DEFAULT_N,
    dt: float = DEFAULT_DT,
    tau: float = DEFAULT_TAU,
    a: float = DEFAULT_A,
    seed: int = DEFAULT_SEED,
) -> Dict[str, object]:
    cv2 = C.CostV2(strict_reliable=True)
    cells: List[Dict[str, object]] = []
    for mode in MODE_GRID:
        for rho_bar in RHO_BAR_GRID:
            cells.append(calibrate_cell(cv2, mode, rho_bar, seed=seed, n=n, dt=dt, tau=tau, a=a))
    summary = {
        "n_design_cells": len(cells),
        "n_feasible": sum(1 for c in cells if c["feasible"]),
        "n_gate_cells": sum(1 for c in cells if c.get("role") == "gate"),
        "n_pc1_cells": sum(1 for c in cells if str(c.get("role", "")).startswith("pc1")),
        "n_in_band": sum(1 for c in cells if c.get("in_band")),
        "max_fixpoint_rounds": max(int(c.get("fixpoint_rounds", 0)) for c in cells),
        "max_clip_fraction_feasible": max(
            float(c.get("clip_fraction", 0.0)) for c in cells if c["feasible"]
        ),
    }
    return {
        "phase": "20R.2",
        "generated_date": "2026-08-04",
        "script": "measurements.sla_calib_v2",
        "config": {
            "loss_exchange": LOSS_EXCHANGE,
            "target_viol": TARGET_VIOL,
            "viol_band": list(VIOL_BAND),
            "p_lo": P_LO,
            "p_hi": P_HI,
            "n_bisect": N_BISECT,
            "n_fixpoint": N_FIXPOINT,
            "tol_w": TOL_W,
            "rho_bar_grid": list(RHO_BAR_GRID),
            "mode_grid": list(MODE_GRID),
            "n": int(n),
            "dt": float(dt),
            "tau": float(tau),
            "a": float(a),
            "seed": int(seed),
            "z_gate_s": 0.55,
            "z_extrapolation_s": [1.0, 2.0, 4.0],
        },
        "inputs": {
            "twin/cost_v2.py": sha256_file("twin/cost_v2.py"),
            "twin/link_model_v2.py": sha256_file("twin/link_model_v2.py"),
            "results/phase-L/link_model_v2_fit.json": sha256_file("results/phase-L/link_model_v2_fit.json"),
            "twin/topology_v7.py": sha256_file("twin/topology_v7.py"),
            "docs/phase-20R/00-preregistration.md": sha256_file("docs/phase-20R/00-preregistration.md"),
            "docs/phase-20R/00b-amendment-1.md": sha256_file("docs/phase-20R/00b-amendment-1.md"),
        },
        "summary": summary,
        "cells": cells,
    }


def table_lines(cells: Sequence[Mapping[str, object]]) -> List[str]:
    lines = [
        "mode     rho_bar sigma   p      T_delay  T_loss    w_loss  optviol clip   margin_ms  best-path",
        "-" * 94,
    ]
    for cell in cells:
        mode = str(cell["mode"])
        rho_bar = float(cell["rho_bar"])
        if not cell["feasible"]:
            lines.append(
                "%-8s %.3f   --      --     --       --        --      --     --      --      LOAI: %s"
                % (mode, rho_bar, cell["reason"])
            )
            continue
        share = cell["opt_path_share"]
        best = max(share, key=share.get)
        suffix = ""
        if not cell["in_band"]:
            suffix = " <-- NGOAI BAND"
        lines.append(
            "%-8s %.3f  %.4f  %5.2f  %7.2f  %.5f  %7.0f  %.3f  %.3f  %8.3f  %s(%.2f)%s"
            % (
                mode,
                rho_bar,
                float(cell["sigma_rho"]),
                float(cell["percentile"]),
                float(cell["t_delay_ms"]),
                float(cell["t_loss"]),
                float(cell["w_loss"]),
                float(cell["opt_viol_rate"]),
                float(cell["clip_fraction"]),
                float(cell["cost_margin_mean_ms"]),
                best,
                float(share[best]),
                suffix,
            )
        )
    return lines


def opt_share_lines(cells: Sequence[Mapping[str, object]]) -> List[str]:
    lines = [
        "mode     rho_bar  margin_mean  margin_p10   ti le duong nao la toi uu",
    ]
    for cell in cells:
        if not cell["feasible"]:
            continue
        share = cell["opt_path_share"]
        parts = [
            "%s=%.2f" % (path, float(share[path]))
            for path in T7.PATH_NAMES
            if float(share[path]) >= 0.005
        ]
        lines.append(
            "%-8s %.3f  %11.3f  %10.3f   %s"
            % (
                str(cell["mode"]),
                float(cell["rho_bar"]),
                float(cell["cost_margin_mean_ms"]),
                float(cell["cost_margin_p10_ms"]),
                ", ".join(parts),
            )
        )
    return lines


def write_json(report: Mapping[str, object], path: str) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, indent=2, sort_keys=True, separators=(",", ": ")) + "\n",
        encoding="utf-8",
    )


def write_doc(report: Mapping[str, object], path: str, figure_path: str) -> None:
    cells = report["cells"]
    summary = report["summary"]
    text = [
        "# SLA CALIBRATION -- Phase 20R.2",
        "",
        "Ngay lap: 2026-08-04",
        "Trang thai: sinh tu `python3 -m measurements.sla_calib_v2 --write`.",
        "",
        "## Ket Qua Chinh",
        "",
        "```text",
        *table_lines(cells),
        "",
        "%d/%d o vao gate; %d o PC1; max fixpoint rounds = %d; max clip = %.4f."
        % (
            int(summary["n_gate_cells"]),
            int(summary["n_design_cells"]),
            int(summary["n_pc1_cells"]),
            int(summary["max_fixpoint_rounds"]),
            float(summary["max_clip_fraction_feasible"]),
        ),
        "```",
        "",
        "## Opt Path Share",
        "",
        "Day la kiem tra som xem bai toan co rong khong. Neu mot path thang 1.00",
        "thi o do khong co bai toan quyet dinh cho gate chinh.",
        "",
        "```text",
        *opt_share_lines(cells),
        "```",
        "",
        "Hinh: `%s`." % figure_path,
        "",
        "## Dieu Chinh So Voi Pre-registration",
        "",
        "Amendment 2 tach `LOSS_EXCHANGE = 0.01` khoi `T_loss`: `0.01` la ti",
        "gia quy doi loss sang ms, con `T_loss` la nguong SLA duoc hieu chuan",
        "tung o. Percentile `p` duoc giai nguoc bang bisection de dat",
        "`TARGET_VIOL = 0.15`, thay vi co dinh p85.",
        "",
        "Gate doc tai `z_max = 0.55 s`; cac diem `z in {1, 2, 4}` van bao cao",
        "nhung danh dau ngoai suy.",
        "",
        "## Provenance",
        "",
        "```text",
        "n=%d  dt=%.3f  tau=%.3f  a=%.1f  seed=%d"
        % (
            int(report["config"]["n"]),
            float(report["config"]["dt"]),
            float(report["config"]["tau"]),
            float(report["config"]["a"]),
            int(report["config"]["seed"]),
        ),
        "LOSS_EXCHANGE=%.4f  TARGET_VIOL=%.2f  VIOL_BAND=%s"
        % (
            float(report["config"]["loss_exchange"]),
            float(report["config"]["target_viol"]),
            report["config"]["viol_band"],
        ),
        "```",
    ]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(text) + "\n", encoding="utf-8")


def write_opt_share_svg(report: Mapping[str, object], path: str) -> None:
    cells = [c for c in report["cells"] if c["feasible"]]
    row_h = 30
    left = 140
    width = 440
    height = 70 + row_h * len(cells)
    colors = {"P1": "#2563eb", "P2": "#dc2626", "P3": "#16a34a", "P4": "#9333ea"}
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
        % (left + width + 180, height, left + width + 180, height),
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="20" y="28" font-family="Arial, sans-serif" font-size="18" font-weight="700">Phase 20R.2 opt_path_share</text>',
    ]
    y = 55
    for cell in cells:
        label = "%s %.3f" % (cell["mode"], float(cell["rho_bar"]))
        lines.append(
            '<text x="20" y="%d" font-family="Arial, sans-serif" font-size="12">%s</text>'
            % (y + 15, label)
        )
        x = left
        for path_name in T7.PATH_NAMES:
            frac = float(cell["opt_path_share"][path_name])
            w = width * frac
            if w > 0:
                lines.append(
                    '<rect x="%.2f" y="%d" width="%.2f" height="18" fill="%s"/>'
                    % (x, y, w, colors[path_name])
                )
            x += w
        lines.append(
            '<rect x="%d" y="%d" width="%d" height="18" fill="none" stroke="#111827" stroke-width="0.5"/>'
            % (left, y, width)
        )
        y += row_h
    lx = left + width + 25
    ly = 58
    for path_name in T7.PATH_NAMES:
        lines.append('<rect x="%d" y="%d" width="12" height="12" fill="%s"/>' % (lx, ly, colors[path_name]))
        lines.append(
            '<text x="%d" y="%d" font-family="Arial, sans-serif" font-size="12">%s</text>'
            % (lx + 18, ly + 11, path_name)
        )
        ly += 20
    lines.append("</svg>")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_amendment(path: str, previous_commit: str) -> None:
    text = """# AMENDMENT 2 -- Phase 20R: sua Q2 (hieu chuan SLA) va z_max cua gate

Ngay: 2026-08-04
Commit truoc thay doi: %s

## Toi Da Thay Gi

1. Hang so `0.01` cua Phase 20 dong hai vai khac nhau: nguong SLA cua loss
   va ti gia quy doi loss sang ms trong `w_loss`. Gop lam mot lam `h2` de roi
   vao trang thai vi pham 100%% va `d_sla = 0` co hoc.
2. Lay ca `T_delay` va `T_loss` o p85 khong dam bao opt-viol 15%%, vi vi pham
   la hop `(delay > T_delay) OR (loss > T_loss)`. Giai nguoc cho `p` nam
   quanh 88..92 va khac nhau tung o.
3. `cbr` khong hieu chuan duoc trong vung tin cay: delay gan hang so, loss
   bang 0, nen opt-viol bang 0%%.
4. `z_max = 4.0 s` khong ton tai trong he thong. AoI that Phase 9 sawtooth
   nam trong `[0.051, 0.548] s`, nen gate doc tai 4 s la ngoai suy.

## Toi Doi Gi

```text
Q2' HIEU CHUAN SLA
    LOSS_EXCHANGE = 0.01  CO DINH moi che do
    TARGET_VIOL   = 0.15  CHOT
    w_loss        = T_delay / LOSS_EXCHANGE
    T_delay,T_loss = phan vi p cua delay/loss duong TOI UU,
                     voi p giai nguoc bang bisection sao cho
                     P((delay>T_delay) OR (loss>T_loss) | toi uu) = 0.15
    RANG BUOC: opt_viol_rate in [0.10,0.25], ngoai band -> LOAI o

Q5' z_max cua gate = 0.55 s (p95 AoI that, Phase 9)
    z in {1,2,4} van do va bao cao, nhung danh dau NGOAI SUY.
```

## Hau Qua Len Luoi Che Do

12 o thiet ke -> 10 o kha thi (Amendment 1, Q8) -> 8 o vao gate.
4 o `cbr` chuyen vai tro thanh doi chung duong PC1; khi can PC1 se dung
nguong muon tu o `poisson` cung `rho_bar`, ky vong `err = 0` tuyet doi.

## Toi Khong Doi Gi

Q1, Q3, Q4, Q6, Q7, Q8 giu nguyen. Nguong gate G1 `[0.05,0.40]`,
G2 `>= 0.03`, G3 Spearman `> 0` giu nguyen. Ngan sach lap giu nguyen.
""" % previous_commit
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=DEFAULT_N)
    ap.add_argument("--dt", type=float, default=DEFAULT_DT)
    ap.add_argument("--tau", type=float, default=DEFAULT_TAU)
    ap.add_argument("--a", type=float, default=DEFAULT_A)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--out", default=RESULT_PATH)
    ap.add_argument("--doc", default=DOC_PATH)
    ap.add_argument("--figure", default=FIGURE_PATH)
    ap.add_argument("--amendment", default=AMENDMENT_PATH)
    ap.add_argument("--previous-commit", default="5506e3e975dbad33e5ca240779a5a31bf4d072dd")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    report = run_calibration(n=args.n, dt=args.dt, tau=args.tau, a=args.a, seed=args.seed)
    print("\n".join(table_lines(report["cells"])))
    print()
    print(
        "%d/%d o vao gate, %d o PC1, max fixpoint rounds = %d, max clip = %.4f"
        % (
            report["summary"]["n_gate_cells"],
            report["summary"]["n_design_cells"],
            report["summary"]["n_pc1_cells"],
            report["summary"]["max_fixpoint_rounds"],
            report["summary"]["max_clip_fraction_feasible"],
        )
    )
    print()
    print("\n".join(opt_share_lines(report["cells"])))

    if args.write:
        write_json(report, args.out)
        write_doc(report, args.doc, args.figure)
        write_opt_share_svg(report, args.figure)
        write_amendment(args.amendment, args.previous_commit)
        print()
        print("WROTE %s" % args.out)
        print("WROTE %s" % args.doc)
        print("WROTE %s" % args.figure)
        print("WROTE %s" % args.amendment)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

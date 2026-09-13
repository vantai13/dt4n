#!/usr/bin/env python3
"""20R2-E1 c/d/e -- BA bang chung MAY MOC cho erratum. Khong doc cot ket qua nao.

  C  co che cbr:      argmin co the lat khong? -> so, khong phai loi ke   [NT 50]
  D  tua-tinh:        T_relax(rho) so voi tau -> tau nao vi pham          [NT 49]
  E  chi phi:         ty trong so hang w_loss*loss trong cost
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, pathlib, subprocess
from datetime import datetime, timezone
import numpy as np
from measurements.decision_error_v2 import TruthTable
from measurements import sla_calib_v2 as SLA
from twin import cost_v2 as C
from twin import topology_v7 as T7
from twin.link_model import MTU_BYTES

ROOT  = pathlib.Path(__file__).resolve().parents[1]
EXO   = ROOT / "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json"
TRUTH = ROOT / "results/LIVE/phase-20R/truth_table.parquet"
W_LOSS   = 5000.0
TAU_GRID = (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0)
RHO_BARS = (0.700, 0.850, 0.925, 0.960)
QS_MARGIN = 5.0          # nguong tua-tinh: T_relax <= tau / QS_MARGIN
L_BITS = MTU_BYTES * 8.0

def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _git(*a):
    try: return subprocess.check_output(["git",*a],text=True,cwd=ROOT,stderr=subprocess.DEVNULL).strip()
    except Exception: return ""

# ---------------------------------------------------------------- C: cbr
def block_c(tt):
    """argmin cua cbr co the lat khong? So sanh BIEN DO voi KHE HO."""
    per_link, per_mode = {}, {}
    for mode in ("cbr", "poisson", "h2"):
        sp = {}
        for link in T7.LINK_NAMES:
            bw, base, q = T7.LINKS[link]
            grid, delay, loss, _ = tt.curves[(mode, float(bw), int(q))]
            sp[link] = {"queue_span_ms": float(delay.max()-delay.min()),
                        "delay_min_ms": float(delay.min()), "delay_max_ms": float(delay.max()),
                        "loss_max": float(loss.max()),
                        "rho_domain": [float(grid.min()), float(grid.max())]}
        per_link[mode] = sp
        per_mode[mode] = {"queue_span_ms_max_over_links": max(v["queue_span_ms"] for v in sp.values()),
                          "loss_max_over_links": max(v["loss_max"] for v in sp.values())}
    out = {}
    for mode in ("cbr", "poisson", "h2"):
        sp = {k: v["queue_span_ms"] for k, v in per_link[mode].items()}
        path_span = {p: sum(sp[l] for l in T7.PATHS[p]) for p in T7.PATH_NAMES}
        margin_span = max(path_span[x]+path_span[y]
                          for x, y in itertools.combinations(T7.PATH_NAMES, 2))
        rho = np.array([[0.5 + C.LINK_OFFSET[l] for l in T7.LINK_NAMES]])
        _, _, cost = tt.path_tables(mode, rho, W_LOSS)
        s = np.sort(cost[0]); gap = float(s[1]-s[0])
        # A failed sufficient bound is not evidence that a flip exists.
        # Supply actual path-cost witnesses over all 2^8 domain corners.
        domains = [tt.domain(mode, T7.LINKS[l][0], T7.LINKS[l][2])
                   for l in T7.LINK_NAMES]
        probes = np.array([rho[0].tolist(), *itertools.product(*domains)])
        _, _, probe_cost = tt.path_tables(mode, probes, W_LOSS)
        winners = probe_cost.argmin(axis=1)
        witness = []
        for winner in np.unique(winners):
            i = int(np.flatnonzero(winners == winner)[0])
            witness.append({"winner": T7.PATH_NAMES[int(winner)],
                            "rho_by_link": dict(zip(T7.LINK_NAMES, probes[i].tolist())),
                            "path_cost_ms": probe_cost[i].tolist()})
        loss_is_zero = per_mode[mode]["loss_max_over_links"] == 0.0
        certified = loss_is_zero and margin_span < gap
        out[mode] = {"path_span_ms": {k: float(v) for k, v in path_span.items()},
                     "max_margin_span_ms": float(margin_span),
                     "min_path_cost_gap_ms": gap,
                     "gap_over_span": float(gap/margin_span) if margin_span > 0 else None,
                     "reference_rho_by_link": dict(zip(T7.LINK_NAMES, rho[0].tolist())),
                     "delay_only_bound_applies_to_full_cost": loss_is_zero,
                     "argmin_invariance_certified": bool(certified),
                     "argmin_can_flip": bool(len(witness) > 1),
                     "flip_witnesses": witness,
                     "interpretation": "No flip witness alone does not certify invariance; use the bound."}
    return {"WHAT_IT_ANSWERS": "Truth-table argmin stability over its clipped lookup domain.",
            "per_link": per_link, "per_mode_summary": per_mode, "flip_analysis": out,
            "reading": ("For cbr, loss is zero and the full-domain delay variation bound is "
                        "smaller than the reference best/second-best gap: truth argmin is invariant. "
                        "The curves are nearly flat, not exactly constant. This does not alone "
                        "prove err_total=0: the fitted twin must choose the same action. "
                        "For h2/poisson the delay-only bound is not a full-cost bound; "
                        "flip_witnesses demonstrate any reported argmin change.")}

# ------------------------------------------------------------- D: tua-tinh
def block_d():
    rows, worst = [], {}
    for link in T7.LINK_NAMES:
        bw, base, q = T7.LINKS[link]
        s_ms = L_BITS/(bw*1e6)*1000.0
        off  = float(C.LINK_OFFSET[link])
        per = {}
        for rb in RHO_BARS:
            rho   = rb + off
            t_inf = (s_ms/(1.0-rho)**2) if rho < 1.0 else float("inf")
            t_fin = (q*s_ms/abs(1.0-rho)) if abs(1.0-rho) > 1e-12 else float("inf")
            t = min(t_inf, t_fin)/1000.0
            per["%.3f" % rb] = {"rho_link": rho, "T_relax_s": t,
                                "bound_used": "finite_buffer" if t_fin <= t_inf else "mm1"}
            worst.setdefault("%.3f" % rb, []).append((t, link))
        rows.append({"link": link, "bw_mbps": bw, "q_pkts": q, "service_time_ms": s_ms,
                     "link_offset": off, "by_rho_bar": per})
    verdict = {}
    for rb in RHO_BARS:
        k = "%.3f" % rb
        t, link = max(worst[k])
        bad = [x for x in TAU_GRID if x < QS_MARGIN*t]
        verdict[k] = {"T_relax_worst_s": t, "worst_link": link,
                      "tau_min_safe_s": QS_MARGIN*t,
                      "tau_violating_quasi_static": bad, "n_tau_violating": len(bad)}
    return {"WHAT_IT_ANSWERS": ("Bang tra SU THAT la duong cong TRANG THAI DUNG delay=f(rho). "
                                "Gia dinh ngam: hang doi KIP can bang truoc khi rho doi dang ke. "
                                "O dau gia dinh do VO?"),
            "model": {"mm1_infinite_buffer": "T = (L/C)/(1-rho)^2",
                      "finite_buffer_q": "T = q*(L/C)/|1-rho|  (thoi gian day/xa het buffer)",
                      "rule": "MIN of two characteristic-time estimates; not a proven stochastic relaxation bound",
                      "L_bits": L_BITS, "MTU_BYTES": MTU_BYTES,
                      "quasi_static_criterion": "T_relax <= tau / %g" % QS_MARGIN},
            "per_link": rows, "verdict_by_rho_bar": verdict,
            "caveat": ("Heuristic screening, not measured queue dynamics or a rigorous mixing-time bound. "
                       "The M/M/1 characteristic-time approximation and finite-buffer drift time "
                       "need not describe cbr/h2 transients. Taking MIN is an explicit modeling "
                       "assumption. QS_MARGIN=5 is a convention, not derived from a law. "
                       "Flagged tau values identify conditions needing a dynamic experiment; "
                       "they do not establish failure or a cause of the campaign MISS outcomes.")}

# ------------------------------------------------------------- E: loss share
def block_e(tt, tau=3.0, n=50_000, seed=101):
    cells = [c for c in json.loads(EXO.read_text())["cells"] if c.get("role") == "gate"]
    rows = []
    for c in cells:
        for a in (0.5, 0.9):
            sig = a*float(c["sigma_max"])
            rho = SLA.ar1_matrix(str(c["mode"]), float(c["rho_bar"]), sig,
                                 tau=tau, dt=0.005, n=n, seed=seed)
            d, l, _ = tt.path_tables(str(c["mode"]), rho, W_LOSS)
            dm, lm = float(d.mean()), float((W_LOSS*l).mean())
            rows.append({"cell": "%s@%.3f" % (c["mode"], c["rho_bar"]), "a": a, "sigma": sig,
                         "delay_ms_mean": dm, "w_loss_term_ms_mean": lm,
                         "loss_share_of_cost": lm/(dm+lm)})
    sh = [r["loss_share_of_cost"] for r in rows]
    return {"WHAT_IT_ANSWERS": ("cost = delay_ms + w_loss*loss.  argmin ma 20R2 do dang xep hang "
                                "theo DAI LUONG VAT LY NAO?"),
            "constants": {"w_loss": W_LOSS, "w_loss_rule": "T_delay/T_loss = 50/0.01",
                          "tau": tau, "n": n, "seed": seed, "dt": 0.005},
            "rows": rows,
            "summary": {"min": min(sh), "max": max(sh), "median": float(np.median(sh)),
                        "n_combos": len(rows),
                        "n_loss_dominated_ge_50pct": int(sum(x >= 0.5 for x in sh))},
            "reading": ("Loss share is the ratio of means over all times and all four paths. "
                        "It describes cost composition, not which term determines argmin. "
                        "Ranking depends on pairwise path differences; causal attribution to "
                        "w_loss requires a separate sensitivity experiment.")}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="docs/phase-20R2/E1-mechanics.json")
    ap.add_argument("--deterministic", action="store_true",
                    help="Omit time and commit metadata for byte-exact reproduction")
    a = ap.parse_args()
    tt = TruthTable(str(ROOT / "results/LIVE/phase-20R/truth_table.parquet"))
    manifest = json.loads(EXO.read_text())
    assert all((c["t_delay_ms"], c["t_loss"], c["w_loss"]) == (50.0, 0.01, 5000.0)
               for c in manifest["cells"]), "SLA constants differ from the E1 contract"
    out = {"WHAT_THIS_IS": ("BA tinh chat MOI TRUONG lam bang chung may moc cho 20R2-E1. "
                            "Khong doc mot cot ket qua nao cua chien dich. Cung the loai voi "
                            "07a-dsla-structure.json."),
           "schema": "dt4n.e1_mechanics_20r2.v1",
           "generated_by": "tools/20r2_9_e1_mechanics.py",
           "generated_utc": datetime.now(timezone.utc).isoformat(),
           "git_commit": _git("rev-parse", "HEAD"),
           "inputs_sha256": {"results/LIVE/phase-20R/truth_table.parquet": _sha(TRUTH),
                             "results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json": _sha(EXO)},
           "C_cbr_mechanism": block_c(tt),
           "D_quasi_static": block_d(),
           "E_cost_composition": block_e(tt),
           "validity": {"schema": "dt4n.validity.v1", "axis_role": "measures_axis",
                        "note": ("C va D KHONG dung truc SLA lan truc AoI. E CO dung truc SLA qua "
                                 "w_loss = 5000 (exogenous S-B), khai o constants.")}}
    if a.deterministic:
        out.pop("generated_utc")
        out.pop("git_commit")
    out["source_sha256"] = {rel: _sha(ROOT / rel) for rel in (
        "tools/20r2_9_e1_mechanics.py", "measurements/decision_error_v2.py",
        "measurements/sla_calib_v2.py", "twin/cost_v2.py",
        "twin/topology_v7.py", "twin/link_model.py")}
    p = ROOT / a.out; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=True), encoding="utf-8")
    c = out["C_cbr_mechanism"]["flip_analysis"]["cbr"]
    print("C cbr    : gap %.5f ms / span %.5f ms = %.1fx  -> argmin_can_flip = %s"
          % (c["min_path_cost_gap_ms"], c["max_margin_span_ms"],
             c["gap_over_span"], c["argmin_can_flip"]))
    for k, v in out["D_quasi_static"]["verdict_by_rho_bar"].items():
        print("D rho=%s: T_relax worst %7.3f s (%s) -> tau vi pham %s" %
              (k, v["T_relax_worst_s"], v["worst_link"], v["tau_violating_quasi_static"]))
    s = out["E_cost_composition"]["summary"]
    print("E cost   : loss_share %.1f%% .. %.1f%% ; %d/%d to hop >= 50%%"
          % (100*s["min"], 100*s["max"], s["n_loss_dominated_ge_50pct"], s["n_combos"]))
    print("->", a.out)
    h2 = out["C_cbr_mechanism"]["flip_analysis"]["h2"]
    return int(not (c["argmin_invariance_certified"] and h2["argmin_can_flip"]
                    and s["n_combos"] == 16
                    and all(np.isfinite(r["loss_share_of_cost"])
                            and 0 <= r["loss_share_of_cost"] <= 1
                            for r in out["E_cost_composition"]["rows"])))

if __name__ == "__main__":
    raise SystemExit(main())

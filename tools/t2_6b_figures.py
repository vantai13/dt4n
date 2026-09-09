#!/usr/bin/env python3
"""T2.7 -- ba hinh cua Phase T2. CHI DOC artifact, khong tinh lai ket qua.

HINH T2-1  R(tau) do vs ky, mot panel moi o song
HINH T2-2  du doan vs do, voi bang da ky
HINH T2-3  mien kha thi Omega tren mat phang (tau, sigma)

!! HINH T2-3 PHAI goi cert.realizability_gate.realizability_gate() tren mot
   luoi min va to theo `verdict`. KHONG duoc go lai bat dang thuc vao day:
   go lai la tao co hoi thu hai de sai, va do dung la co che da gay loi bang
   level tau=3 (ERRATUM A-T2-3.1).

    python3 tools/t2_6b_figures.py
"""
from __future__ import annotations

import glob
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cert.realizability_gate import realizability_gate      # noqa: E402
from twin.cost_v2 import sigma_max_regime                   # noqa: E402
from measurements.sla_calib_v2 import n_for_tau             # noqa: E402

SWEEP = ROOT / "results/PENDING/phase-T2/sweep_r3"
FIGS = ROOT / "docs/phase-T2/figures"
ADJ = SWEEP / "adjudication_r3.json"
SIGNED = ROOT / "docs/phase-T2/01-prediction-signed.json"

LIVE = ("h2@0.700", "poisson@0.850", "poisson@0.925")
A_COLOR = {0.5: "#1f77b4", 0.9: "#d62728"}
BOX_LO, BOX_HI = 1.0, 3.0          # khoang boc argmax (A-T2-3.3 muc c)


def _runs(pattern="t2_6b_r*.json"):
    out = []
    for p in sorted(glob.glob(str(SWEEP / pattern))):
        out.append(json.loads(pathlib.Path(p).read_text()))
    return out


# ------------------------------------------------------------------ T2-1
def fig1(runs, signed):
    peaks = signed["signed_predictions"]["D-T2.6-3"]["per_cell"]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=False)
    for ax, cell in zip(axes, LIVE):
        ax.axvspan(BOX_LO, BOX_HI, color="0.88", zorder=0)
        for r in runs:
            if r["cell"] != cell:
                continue
            a = r["sigma_axis"]["a"]
            rows = sorted(r["rows"], key=lambda x: x["tau"])
            tau = [x["tau"] for x in rows]
            m = [(x.get("level_matched") or {}).get("ratio_measured") for x in rows]
            f = [x["ratio_measured"] for x in rows]
            sat = [x["ratio_pred_saturated"] for x in rows]
            ax.plot(tau, m, "-o", color=A_COLOR[a], ms=6, lw=1.1,
                    label="chinh (khop muc), a=%.1f" % a, zorder=3)
            ax.plot(tau, f, "--o", color=A_COLOR[a], ms=6, lw=0.9, mfc="white",
                    label="do nhay (day du), a=%.1f" % a, zorder=2)
            if a == 0.9:
                ax.plot(tau, sat, ":", color="0.4", lw=1.0,
                        label="can tren giai tich", zorder=1)
        ax.plot([peaks[cell]], [ax.get_ylim()[0]], "*", ms=14, color="k",
                clip_on=False, label="dinh DA KY (%.2f s)" % peaks[cell], zorder=4)
        ax.set_xscale("log")
        ax.set_xticks([0.5, 1, 2, 3, 5, 10, 20, 28])
        ax.set_xticklabels(["0.5", "1", "2", "3", "5", "10", "20", "28"])
        ax.set_xlabel(r"$\tau$ (s, log)")
        ax.set_title(cell)
        ax.grid(alpha=0.25, lw=0.5)
    axes[0].set_ylabel(r"$R(\tau) = \hat{q}[bin\,3]\,/\,\hat{q}[bin\,0]$")
    axes[0].legend(fontsize=6.5, loc="best")
    fig.suptitle("HINH T2-1  R(tau): nhanh chinh (khop muc) va nhanh do nhay",
                 fontsize=11)
    fig.text(0.5, -0.10,
             "Nhanh chinh la nhanh khop muc (25 block hieu chuan moi bin o moi tau), theo bien phap da ky sau khi D-T2.6-10 FAIL.\n"
             "Nhanh day du ve song song; thien lech do muc conformal tren nhanh do <= 2.67%, con cv nhieu rut mau cua nhanh chinh len toi 12.4%.\n"
             "Dai to la khoang boc argmax do do phan giai luoi; luoi khong co diem nao giua 1 va 2 s nen vi tri dinh KHONG duoc phan giai min hon (1,3) s.",
             ha="center", fontsize=7.5)
    fig.tight_layout()
    out = FIGS / "T2-1-R-tau.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out


# ------------------------------------------------------------------ T2-2
def fig2(adj):
    d2 = adj["verdicts"]["D-T2.6-2"]["per_cell"]
    marker = {"h2@0.700": "o", "poisson@0.850": "s", "poisson@0.925": "^"}
    fig, ax = plt.subplots(figsize=(6.2, 6.0))
    band = None
    for cell, arms in sorted(d2.items()):
        for arm, zs in sorted(arms.items()):
            a = float(arm.split("=")[1])
            for z, r in sorted(zs.items()):
                band = r["band"]
                ax.plot([r["signed"]], [r["measured"]], marker[cell], ms=8,
                        color=A_COLOR[a],
                        mfc=A_COLOR[a] if r["inside"] else "white", zorder=3)
    # arm chan doan sigma (hau nghiem), neu co
    probe = sorted(glob.glob(str(SWEEP / "sigmaprobe_*.json")))
    if probe:
        import tools.t2_6b_adjudicate as J
        signed = json.loads(SIGNED.read_text())
        bands = json.loads((ROOT / "docs/phase-T2/05-band-window-v2.json").read_text())
        pr = J.adj_2([json.loads(pathlib.Path(p).read_text()) for p in probe],
                     signed, bands)
        for cell, arms in sorted(pr["per_cell"].items()):
            for arm, zs in sorted(arms.items()):
                for z, r in sorted(zs.items()):
                    ax.plot([r["signed"]], [r["measured"]], "x", ms=9, mew=1.8,
                            color="#2ca02c", zorder=4)
    lo, hi = 0.10, 0.50
    ax.plot([lo, hi], [lo, hi], "-", color="0.3", lw=1.0, zorder=1)
    if band:
        ax.fill_between([lo, hi], [lo - band, hi - band], [lo + band, hi + band],
                        color="0.85", zorder=0)
    ax.set_xlabel("gia tri KY  (suy tu 22.6, sigma = 0.0096)")
    ax.set_ylabel("gia tri DO  (vong 3)")
    ax.set_title("HINH T2-2  D-T2.6-2: du doan vs do, bang da ky", fontsize=11)
    ax.grid(alpha=0.25, lw=0.5)
    from matplotlib.lines import Line2D
    leg = [Line2D([], [], ls="", marker=marker[c], color="0.3", label=c) for c in marker]
    leg += [Line2D([], [], ls="", marker="o", color=A_COLOR[a], label="a=%.1f" % a)
            for a in (0.5, 0.9)]
    leg += [Line2D([], [], ls="", marker="o", color="0.3", mfc="white", label="ngoai bang"),
            Line2D([], [], ls="", marker="x", color="#2ca02c",
                   label="arm chan doan sigma (HAU NGHIEM)")]
    ax.legend(handles=leg, fontsize=7, loc="upper left")
    fig.text(0.5, -0.06,
             "Diem ky suy tu artifact 22.6 tai sigma = 0.0096. Vong 3 do tai sigma = a*sigma_max, a in {0.5, 0.9}, tuc lon hon 1.3-4.8 lan tuy o.\n"
             "Chenh lech sigma la mot sai khac thiet ke da biet giua diem ky va diem do, va duoc luong hoa o Threats T-3. D-T2.6-2 = FAIL (6 trong / 10 ngoai).\n"
             "Diem x la arm chan doan HAU NGHIEM o dung sigma da ky; no KHONG tham gia phan quyet D-T2.6-2, von da dong o FAIL.",
             ha="center", fontsize=7.5)
    fig.tight_layout()
    out = FIGS / "T2-2-pred-vs-measured.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out


# ------------------------------------------------------------------ T2-3
def _tau_window(dt: float, n_rule, sigma=0.02, taus=None):
    """Bien DO TU gate, khong go lai bat dang thuc.

    Quet realizability_gate tren luoi tau va lay [tau_min, tau_max] ma
    verdict == REALIZABLE. Doc bien tu chinh ham phan quyet la cach duy nhat
    bao dam hinh khong lech khoi cai da chay.
    """
    if taus is None:
        taus = np.logspace(np.log10(0.01), np.log10(200.0), 400)
    ok = []
    for tau in taus:
        g = realizability_gate(mode="poisson", rho_bar=0.925, tau=float(tau),
                               dt=dt, n=int(n_rule(float(tau))), sigma=sigma,
                               clip_fraction=0.0, min_cell_blocks=25)
        ok.append(g["verdict"] == "REALIZABLE")
    ok = np.array(ok)
    if not ok.any():
        return None
    return float(taus[ok][0]), float(taus[ok][-1])


def fig3(runs):
    """Bien VE TU realizability_gate(), khong go lai bat dang thuc.

    !! Gate KHONG chan tren theo sigma: tieu chi sigma_feasible chi kiem
       sigma > 0 (do duoc: sigma = 99.0 van REALIZABLE). Nen tran sigma o
       hinh nay ve RIENG tu twin/cost_v2.sigma_max_regime va PHAI duoc chu
       thich la khong den tu gate. Ve no nhu mot bien cua gate la noi doi
       bang hinh.
    """
    import cert.build_calib_set_v3 as V3

    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    y0, y1 = 1e-4, 0.2

    # (1) mien gate voi NGAN SACH CO DINH n = V3.N -- ngan sach that cua 22.6
    w_fixed = _tau_window(0.005, lambda tau: V3.N)
    ax.axvspan(w_fixed[0], w_fixed[1], color="#cfe3f7", zorder=0,
               label=r"gate REALIZABLE, twin dt=0.005, n = 200 000")
    for x in w_fixed:
        ax.axvline(x, color="0.25", lw=1.3, zorder=2)

    # (2) mien gate khi n = n_for_tau(tau) -- bien PHAI bien mat
    w_pertau = _tau_window(0.005, lambda tau: n_for_tau(tau, 0.005))
    ax.axvline(w_pertau[1], color="0.25", lw=1.0, ls="-.", zorder=2)
    ax.text(w_pertau[1] * 0.75, y1 * 0.45,
            "n = n_for_tau  ->  khong con\nbien phai trong pham vi quet\n(%.0f s), tra gia CPU tuyen tinh" % w_pertau[1],
            fontsize=6.5, ha="right", color="0.3")

    # (3) testbed dt = 0.1: bien TRAI dich sang phai
    w_tb = _tau_window(0.1, lambda tau: n_for_tau(tau, 0.1))
    ax.axvline(w_tb[0], color="0.25", lw=1.3, ls="--", zorder=2,
               label=r"gate, testbed dt=0.1 (bien trai $\tau \geq$ %.1f s)" % w_tb[0])

    # (4) tran sigma -- KHONG tu gate
    for cell, mode, rb, dy in (("h2@0.700", "h2", 0.700, 1.06),
                               ("poisson@0.850", "poisson", 0.850, 0.86),
                               ("poisson@0.925", "poisson", 0.925, 1.0)):
        s = sigma_max_regime(mode, rb)
        ax.axhline(s, color="#8c564b", lw=0.9, ls=":", zorder=1)
        ax.text(0.0115, s * dy, r"$\sigma_{max}$ %s = %.4f  (KHONG tu gate)" % (cell, s),
                fontsize=6.2, va="bottom", color="#8c564b")

    grid = sorted({x["tau"] for r in runs for x in r["rows"]})
    for a, c in A_COLOR.items():
        ax.plot(grid, [a * sigma_max_regime("poisson", 0.925)] * len(grid), "o",
                ms=5, color=c, label="luoi vong 3, a=%.1f" % a, zorder=4)
    ax.plot(grid, [0.0096] * len(grid), "x", ms=7, mew=1.6, color="#2ca02c",
            label="arm legacy / chan doan, sigma = 0.0096", zorder=4)
    ax.plot([1.0], [0.010], "X", ms=11, color="k", zorder=5,
            label="prior work operating point (v8/v9)")
    ax.plot([2, 5, 30], [0.045, 0.045, 0.036], "^", ms=9, color="#8c564b",
            zorder=5, label="Phase G, kernel datapath (dt = 0.1)")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(0.01, 200); ax.set_ylim(y0, y1)
    ax.set_xlabel(r"$\tau$ (s, log)")
    ax.set_ylabel(r"$\sigma_\rho$ (log)")
    ax.set_title(r"HINH T2-3  Mien kha thi $\Omega$ tren mat phang $(\tau, \sigma)$",
                 fontsize=11)
    ax.grid(alpha=0.2, lw=0.5, which="both")
    ax.legend(fontsize=6.5, loc="lower left")
    fig.text(0.5, -0.13,
             "Bien tau ve tu cert/realizability_gate.py -- quet gate tren luoi tau roi lay khoang REALIZABLE, CUNG ham ma chien dich dung de chap nhan tung o.\n"
             "Vung to dung ngan sach CO DINH n = 200 000: bien trai la phan giai luoi (tau >= 20*dt), bien phai la ngan sach block (T_sim >= 50*tau).\n"
             "Duong gach-cham: khi n = n_for_tau(tau) bien phai chay xa hon, doi lai CPU tuyen tinh theo tau -- do la cach vong 3 chay tau = 28 s.\n"
             "TRAN sigma KHONG den tu gate (tieu chi sigma_feasible chi kiem sigma > 0; do duoc: sigma = 99 van REALIZABLE); no ve tu twin/cost_v2.sigma_max_regime.\n"
             "Diem tam giac la bang chung kha thi DO DUOC tren kernel datapath o Phase G (tau in {2,5,30}; |sai so| round-trip lon nhat 4.94% cho tau va 3.82%\n"
             "cho sigma, moi o la trung vi qua link/luot; T_run = 205*tau; docs/phase-G/66-g3b-results.md). Vung tau < 2 s CHI khao sat trong twin.",
             ha="center", fontsize=7.2)
    fig.tight_layout()
    out = FIGS / "T2-3-feasible-region.png"
    fig.savefig(out, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> int:
    runs = _runs()
    signed = json.loads(SIGNED.read_text())
    adj = json.loads(ADJ.read_text())
    for f in (fig1(runs, signed), fig2(adj), fig3(runs)):
        print("-> %s" % f.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

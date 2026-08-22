"""Figure 4 -- c*(gamma) kem dai dong thoi, ba cell.

Vi sao hinh NAY la headline chu khong phai R_system(gamma)
------------------------------------------------------------
Sau khi tai khung (06-reframe.md), `c` la THAM SO NGOAI SINH. Mot hinh ve
R_system(gamma) phai chon vai gia tri `c` de ve, tuc phai chon vai fallback --
dung dieu ma tai khung vua bo di. Hinh headline phai ve dai luong KHONG phu
thuoc fallback: do la `c*(gamma)`.

R_system(gamma) van duoc ve, nhu Figure 4b o phu luc, de nguoi doc quen voi
duong risk-coverage nhan ra hinh dang quen thuoc. No khong phai dong gop.

Bay rang buoc, moi cai co ly do (xem 11-abstain-cost.md muc 4):
  1. Ve CA dai tung diem VA dai dong thoi -- gia cua tinh dong thoi phai NHIN
     THAY duoc; chi ve mot cai la giau mot nua thong tin.
  2. Khong ve gamma > 0.98 -- K-D4 cam ngoai suy, va ve la mo loi ngoai suy.
  3. Danh dau gamma = 0 la R_neo -- do la NC23v2-4, va no neo ca duong.
  4. Danh dau diem cat c_F2 = c* canh `band_low` cua Lesson 23.3 -- de doi
     chung cheo C23v2-1 NHIN THAY duoc.
  5. F1 va F3 la MOT duong, mot nhan. Ve hai duong chong nhau la noi doi bang
     hinh anh (F-23.6-6).
  6. Phan biet duong bang CA mau LAN kieu net -- in den trang phai doc duoc.
  7. Chu thich ghi c_supt va K_eff cua tung duong -- do la so moi cua lesson.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")            # khong can display; tai lap duoc trong CI
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np               # noqa: E402

RESULTS = Path("results/SUPERSEDED/phase-23")
CELLS = ("poisson@0.925", "poisson@0.850", "h2@0.700")
GAMMA_MAX = 0.98                 # (2) K-D4 cam ngoai suy

# (6) mau VA kieu net -- in den trang phai doc duoc
STYLE = {
    "c_star": dict(color="#1a1a1a", ls="-", lw=2.0, zorder=5),
    "c_f2": dict(color="#c1440e", ls="--", lw=1.7, zorder=4),
    "c_f1": dict(color="#1f6f8b", ls="-.", lw=1.7, zorder=4),
}


def _tag(cell: str) -> str:
    return cell.replace("@", "_")


def require(d: Mapping[str, Any], key: str) -> Any:
    if key not in d:
        raise KeyError("thieu khoa %r; co: %s" % (key, sorted(d)))
    return d[key]


def load(cell: str) -> dict:
    return json.loads((RESULTS / ("abstain_cost_%s.json" % _tag(cell))).read_text())


def load_band_v1(cell: str) -> dict:
    art = json.loads(
        (RESULTS / ("baseline_rankings_%s_C3_static.json" % _tag(cell))).read_text())
    return require(require(art, "beneficial_band_err"), "C3_conformal")


def _series(art: dict, key: str) -> tuple[np.ndarray, np.ndarray]:
    """(gamma DO DUOC, gia tri) tu sweep_locked; cat o GAMMA_MAX, bo None."""
    g, y = [], []
    for r in require(art, "sweep_locked"):
        gv = float(r["coverage_measured"])
        v = r.get(key)
        if v is None or gv > GAMMA_MAX + 1e-9:
            continue
        g.append(gv)
        y.append(float(v))
    return np.asarray(g), np.asarray(y)


def panel(ax, art: dict, cell: str, band_v1: Mapping[str, Any],
          show_ylabel: bool, ylim: tuple[float, float]) -> dict:
    g_cs, cs = _series(art, "c_star_err")
    g_f2, f2 = _series(art, "c_f2_err")
    g_f1, f1 = _series(art, "c_f1_err")

    bands = require(art, "supt_bands")
    b = require(bands, "c_star_err")
    gb = np.asarray(b["gamma"], float)
    keep = gb <= GAMMA_MAX + 1e-9
    gb = gb[keep]

    # Truc y DUNG CHUNG cho ba panel (tham so `ylim`). Neu moi panel tu chon
    # thang do, hai cell co R_neo khac nhau se trong giong nhau va nguoi doc
    # mat kha nang so sanh DO LON cua c* giua cac che do -- chinh la thu bang
    # G23-36 dung de so.
    ax.set_ylim(*ylim)

    # (7) vung F2 CO LAI: c_F2 < c*  <=>  Delta = (1-g)(c_F2 - c*) < 0
    if g_cs.size and g_f2.size:
        f2_on_cs = np.interp(g_cs, g_f2, f2)
        ax.fill_between(g_cs, f2_on_cs, cs, where=f2_on_cs < cs,
                        color="#2e7d32", alpha=0.15, lw=0, zorder=0,
                        label=r"vung F2 CO LAI  ($c_{F2} < c^*$)")

    # (1) hai dai, hai sac do
    ax.fill_between(gb, np.asarray(b["lo"], float)[keep],
                    np.asarray(b["hi"], float)[keep],
                    color="#1a1a1a", alpha=0.12, lw=0, zorder=1,
                    label=r"dai DONG THOI 95%%  ($c_{supt}$=%.3f, $K_{eff}$=%.1f)"
                          % (b["c_supt"], b["k_eff"]))
    ax.fill_between(gb, np.asarray(b["pointwise_lo"], float)[keep],
                    np.asarray(b["pointwise_hi"], float)[keep],
                    color="#1a1a1a", alpha=0.30, lw=0, zorder=2,
                    label="dai tung diem 95%  (bao cao KEM, khong thay the)")

    ax.plot(g_cs, cs, label=r"$c^*(\gamma)$ -- nguong hoa von", **STYLE["c_star"])
    ax.plot(g_f2, f2, label="F2 STATIC", **STYLE["c_f2"])
    # (5) MOT duong, MOT nhan
    ax.plot(g_f1, f1, label="F1 STICKY = F3 WAIT", **STYLE["c_f1"])

    # (3) neo: c*(0) = R_neo chinh xac theo dinh nghia (NC23v2-4)
    r_neo = float(require(art["sweep_locked"][0], "r_neo_err"))
    ax.axhline(r_neo, color="#666", ls=":", lw=1.0, zorder=1)
    ax.annotate(r"$R_{neo}$=%.4f" % r_neo, xy=(GAMMA_MAX, r_neo),
                xytext=(GAMMA_MAX - 0.005, r_neo + 0.014), fontsize=7.5,
                color="#444", ha="right")

    # (4) diem cat + doi chung cheo C23v2-1
    seen = []
    for c in require(art, "crossings_locked"):
        gx = float(c["gamma_cross"])
        if gx > GAMMA_MAX:
            continue
        seen.append(gx)
        ax.axvline(gx, color="#2e7d32", ls=":", lw=1.1, zorder=3)
        ax.annotate(r"$\gamma^\dagger$=%.4f" % gx, xy=(gx, 0.0),
                    xytext=(gx + 0.012, 0.030), fontsize=7.5, color="#2e7d32")
    bl = band_v1.get("band_low")
    if bl is not None and bl <= GAMMA_MAX:
        ax.plot([bl], [0.010], marker="^", ms=7, color="#2e7d32", zorder=6,
                clip_on=False)
        ax.annotate("band_low (L23.3)\n%.4f" % bl, xy=(bl, 0.010),
                    xytext=(max(0.02, bl - 0.34), 0.012), fontsize=7,
                    color="#2e7d32")

    ax.set_title(cell, fontsize=10)
    ax.set_xlabel(r"coverage $\gamma$")
    if show_ylabel:
        ax.set_ylabel("rui ro tren tap TU CHOI (thang err)")
    ax.set_xlim(0.0, GAMMA_MAX)
    ax.grid(alpha=0.22, lw=0.6)
    ax.legend(fontsize=6.4, loc="upper left", framealpha=0.92)
    return {"crossings": seen, "band_low": bl, "r_neo": r_neo,
            "c_star_max": float(np.nanmax(cs)), "c_star_min": float(np.nanmin(cs))}


def make_figure4(out: str = "results/SUPERSEDED/phase-23/fig4_cstar_by_coverage.png") -> dict:
    arts = {c: load(c) for c in CELLS}
    hi = max(float(np.nanmax(np.asarray(a["supt_bands"]["c_star_err"]["hi"], float)))
             for a in arts.values())
    ylim = (0.0, hi * 1.08)
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.8), sharey=True)
    checks = {}
    for ax, cell in zip(axes, CELLS):
        checks[cell] = panel(ax, arts[cell], cell, load_band_v1(cell),
                             show_ylabel=(ax is axes[0]), ylim=ylim)
    fig.suptitle(
        r"Figure 4 -- nguong hoa von $c^*(\gamma)$ va vi tri cua HAI fallback"
        "\n"
        r"BAT certification khi va chi khi chi phi fallback $c < c^*(\gamma)$; "
        r"$c^*$ do duoc tu twin + certificate va KHONG phu thuoc fallback nao duoc chon",
        fontsize=10.5)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200)
    plt.close(fig)
    checks["_out"] = out
    return checks


def make_figure4b(cell: str = "poisson@0.925",
                  out: str = "results/SUPERSEDED/phase-23/fig4b_risk_vs_coverage_by_c.png") -> str:
    """Phu luc: R_system(gamma, c) cho vai gia tri c. KHONG phai dong gop.

    Duong `c = c*(0.78)` phai CHAM neo dung tai gamma = 0.78. Do la G23-32
    duoc ve ra, khong phai mot ket qua.
    """
    art = load(cell)
    g, ra = _series(art, "r_accept_err")
    r_neo = float(art["sweep_locked"][0]["r_neo_err"])
    op = next(r for r in art["sweep_locked"]
              if abs(r["coverage_target"] - art["operating_gamma"]) < 1e-12)
    c_star_op, c_f2_op = float(op["c_star_err"]), float(op["c_f2_err"])

    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    ax.axhline(r_neo, color="#666", ls=":", lw=1.3,
               label=r"$R_{neo}$ = %.4f (luon tin twin)" % r_neo)
    for c, lab in ((0.30, ""), (c_f2_op, "  = $c_{F2}(0.78)$"),
                   (c_star_op, "  = $c^*(0.78)$"), (0.55, "")):
        ax.plot(g, g * ra + (1.0 - g) * c, lw=1.5, label=r"$c$=%.4f%s" % (c, lab))
    ax.axvline(float(art["operating_gamma"]), color="#999", ls="--", lw=0.9)
    ax.set_xlabel(r"coverage $\gamma$")
    ax.set_ylabel(r"$R_{system}(\gamma, c)$")
    ax.set_title("Figure 4b (phu luc) -- rui ro he thong theo coverage, %s" % cell,
                 fontsize=10)
    ax.set_xlim(0.0, GAMMA_MAX)
    ax.grid(alpha=0.22, lw=0.6)
    ax.legend(fontsize=7.5)
    fig.tight_layout()
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


if __name__ == "__main__":
    c = make_figure4()
    print("wrote %s" % c.pop("_out"))
    for cell, v in c.items():
        print("  %-15s crossings=%s  band_low=%s" % (cell, [round(x, 4) for x in v["crossings"]],
                                                     round(v["band_low"], 4) if v["band_low"] else None))
    print("wrote %s" % make_figure4b())

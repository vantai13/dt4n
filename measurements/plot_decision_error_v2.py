#!/usr/bin/env python3
"""Plot Phase 20R.5 decision-error artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


SUMMARY = "results/phase-20R/decision_error_by_age_summary.parquet"
PREDICTION = "results/phase-20R/prediction_pre_campaign.json"
CONSTANT_SIGMA = "results/phase-20R/decision_error_constant_sigma.parquet"
TAU_PATHS = (
    "results/phase-20R/decision_error_tau0.2.parquet",
    "results/phase-20R/decision_error_tau1.0.parquet",
    "results/phase-20R/decision_error_tau5.0.parquet",
)
UNIMODAL = "results/phase-20R/decision_error_unimodal.parquet"
W2500 = "results/phase-20R/decision_error_w2500.parquet"
DELAY_ONLY = "results/phase-20R/decision_error_delay_only.parquet"
MARGIN_CV_UNIMODAL = "results/phase-20R/margin_cv_unimodal.parquet"
MARGIN_CV_OPERATIONAL = "results/phase-20R/margin_cv_operational.parquet"
OPERATIONAL_RAW = "results/phase-20R/decision_error_by_age_by_regime.parquet"
OUT_DIR = "docs/phase-20R/figures"


def _plt():
    cache_dir = "/tmp/matplotlib-%s" % os.getuid()
    os.makedirs(cache_dir, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", cache_dir)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _label(row: pd.Series) -> str:
    return "%s %.3f" % (row["mode"], row["rho_bar"])


def _prediction_rows(path: str) -> pd.DataFrame:
    data = json.load(open(path, "r", encoding="utf-8"))
    source: Dict[str, dict] = data.get("with_model_error") or data.get("main", {})
    rows: List[dict] = []
    for item in source.values():
        per_z = item.get("per_z", {})
        if "0.550" not in per_z:
            continue
        rows.append(
            {
                "mode": str(item["mode"]),
                "rho_bar": float(item["rho_bar"]),
                "pred_err_total": float(per_z["0.550"]["err"]),
                "pred_d_sla": float(per_z["0.550"].get("d_sla", 0.0)),
            }
        )
    return pd.DataFrame(rows)


def _z055(summary_path: str, prediction_path: str) -> pd.DataFrame:
    measured = pd.read_parquet(summary_path)
    measured = measured[measured["z_key"] == "0.550"].copy()
    pred = _prediction_rows(prediction_path)
    merged = measured.merge(pred, on=["mode", "rho_bar"], how="left")
    return merged.sort_values(["mode", "rho_bar"]).reset_index(drop=True)


def plot_prediction_vs_measured(z055: pd.DataFrame, out_dir: Path) -> Path:
    plt = _plt()
    df = z055[z055["pred_err_total"].notna()].copy()
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    colors = {"cbr": "#555555", "h2": "#2f6f73", "poisson": "#b4452c"}
    for mode, group in df.groupby("mode"):
        ax.scatter(
            group["pred_err_total"],
            group["err_total"],
            s=58,
            color=colors.get(mode, "#333333"),
            label=mode,
            zorder=3,
        )
        for _, row in group.iterrows():
            ax.annotate(
                "%.3f" % row["rho_bar"],
                (row["pred_err_total"], row["err_total"]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=8,
            )
    lim = max(float(df["pred_err_total"].max()), float(df["err_total"].max())) * 1.08 + 0.005
    ax.plot([0, lim], [0, lim], color="#222222", linewidth=1.0, linestyle="--", label="1:1")
    ax.set_xlim(-0.005, lim)
    ax.set_ylim(-0.005, lim)
    ax.set_xlabel("Predicted err_total at z=0.55")
    ax.set_ylabel("Measured err_total at z=0.55")
    ax.set_title("Phase 20R.5 prediction check")
    ax.grid(True, color="#dddddd", linewidth=0.7)
    ax.legend(frameon=False)
    fig.tight_layout()
    path = out_dir / "decision_error_pred_vs_measured_z055.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_decomposition(summary_path: str, out_dir: Path) -> Path:
    plt = _plt()
    df = pd.read_parquet(summary_path)
    df = df[(~df["extrapolated"]) & (df["mode"].isin(["poisson", "h2"]))].copy()
    selected: List[Tuple[str, float]] = [("poisson", 0.850), ("h2", 0.700)]
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.4), sharey=True)
    metrics = [
        ("err_total", "#111111", "total"),
        ("err_stale", "#b4452c", "stale"),
        ("err_model", "#2f6f73", "model"),
    ]
    for ax, (mode, rho_bar) in zip(axes, selected):
        sub = df[(df["mode"] == mode) & (df["rho_bar"].round(3) == rho_bar)].sort_values("z_s")
        for metric, color, label in metrics:
            ax.plot(sub["z_s"], sub[metric], marker="o", linewidth=2, color=color, label=label)
        ax.set_title("%s rho=%.3f" % (mode, rho_bar))
        ax.set_xlabel("z seconds")
        ax.grid(True, color="#dddddd", linewidth=0.7)
    axes[0].set_ylabel("error rate")
    axes[1].legend(frameon=False)
    fig.suptitle("Decision-error decomposition")
    fig.tight_layout()
    path = out_dir / "decision_error_decomposition_vs_z.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_d_sla_ci(z055: pd.DataFrame, out_dir: Path) -> Path:
    plt = _plt()
    df = z055[z055["mode"] != "cbr"].copy().sort_values(["mode", "rho_bar"])
    labels = [_label(row) for _, row in df.iterrows()]
    yerr = [
        df["d_sla"] - df["d_sla_ci95_lo"],
        df["d_sla_ci95_hi"] - df["d_sla"],
    ]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.errorbar(
        range(len(df)),
        df["d_sla"],
        yerr=yerr,
        fmt="o",
        color="#2f6f73",
        ecolor="#6ca6a9",
        capsize=4,
    )
    ax.axhline(0.03, color="#b4452c", linestyle="--", linewidth=1.2, label="G2 lower threshold")
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylabel("Delta SLA violation")
    ax.set_title("G2 d_sla CI95 at z=0.55")
    ax.grid(True, axis="y", color="#dddddd", linewidth=0.7)
    ax.legend(frameon=False)
    fig.tight_layout()
    path = out_dir / "decision_error_d_sla_ci_z055.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_constant_sigma(summary_path: str, constant_path: str, out_dir: Path) -> Path:
    plt = _plt()
    op = pd.read_parquet(summary_path)
    op = op[(op["z_key"] == "0.550") & (op["mode"].isin(["poisson", "h2"]))].copy()
    cs = pd.read_parquet(constant_path)
    cs = (
        cs[(cs["z_key"] == "0.550") & (cs["mode"].isin(["poisson", "h2"]))]
        .groupby(["mode", "rho_bar"])["err_total"]
        .mean()
        .reset_index()
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.4), sharey=True)
    for ax, mode in zip(axes, ["poisson", "h2"]):
        op_sub = op[op["mode"] == mode].sort_values("rho_bar")
        cs_sub = cs[cs["mode"] == mode].sort_values("rho_bar")
        ax.plot(op_sub["rho_bar"], op_sub["err_total"], marker="o", linewidth=2, color="#b4452c", label="calibrated sigma")
        ax.plot(cs_sub["rho_bar"], cs_sub["err_total"], marker="o", linewidth=2, color="#2f6f73", label="sigma=0.0096")
        ax.set_title(mode)
        ax.set_xlabel("rho_bar")
        ax.grid(True, color="#dddddd", linewidth=0.7)
    axes[0].set_ylabel("err_total at z=0.55")
    axes[1].legend(frameon=False)
    fig.suptitle("Constant-sigma deconfounding")
    fig.tight_layout()
    path = out_dir / "decision_error_constant_sigma_z055.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_tau_scaling(tau_paths: Tuple[str, ...], out_dir: Path) -> Path:
    plt = _plt()
    frames = []
    for path in tau_paths:
        frame = pd.read_parquet(path).copy()
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    selected: List[Tuple[str, float]] = [("poisson", 0.925), ("h2", 0.700)]
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.4), sharey=True)
    colors = {0.2: "#b4452c", 1.0: "#2f6f73", 5.0: "#3b5ca8"}
    for ax, (mode, rho_bar) in zip(axes, selected):
        sub = df[(df["mode"] == mode) & (df["rho_bar"].round(3) == rho_bar)]
        mean = sub.groupby(["tau_rho", "z_over_tau"])["err_total"].mean().reset_index()
        for tau, group in mean.groupby("tau_rho"):
            group = group.sort_values("z_over_tau")
            ax.plot(
                group["z_over_tau"],
                group["err_total"],
                marker="o",
                linewidth=2,
                color=colors.get(float(tau), "#333333"),
                label="tau=%g" % float(tau),
            )
        ax.set_title("%s rho=%.3f" % (mode, rho_bar))
        ax.set_xlabel("z / tau")
        ax.grid(True, color="#dddddd", linewidth=0.7)
    axes[0].set_ylabel("err_total")
    axes[1].legend(frameon=False)
    fig.suptitle("H6 scaling by z/tau")
    fig.tight_layout()
    path = out_dir / "decision_error_tau_scaling.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def plot_loss_mechanism(unimodal_path: str, w2500_path: str, delay_only_path: str, out_dir: Path) -> Path:
    plt = _plt()
    paths = {
        "calibrated w": unimodal_path,
        "w=2500": w2500_path,
        "w=0": delay_only_path,
    }
    frames = []
    for label, path in paths.items():
        frame = pd.read_parquet(path)
        frame = frame[(frame["z_key"] == "0.550") & (frame["mode"].isin(["poisson", "h2"]))].copy()
        frame["slice"] = label
        frames.append(frame)
    df = pd.concat(frames, ignore_index=True)
    mean = df.groupby(["slice", "mode", "rho_bar"])["err_total"].mean().reset_index()
    styles = {
        "calibrated w": ("#111111", "o"),
        "w=2500": ("#b4452c", "s"),
        "w=0": ("#2f6f73", "^"),
    }
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.6), sharey=True)
    for ax, mode in zip(axes, ["poisson", "h2"]):
        sub = mean[mean["mode"] == mode]
        for label in ["calibrated w", "w=2500", "w=0"]:
            group = sub[sub["slice"] == label].sort_values("rho_bar")
            color, marker = styles[label]
            ax.plot(group["rho_bar"], group["err_total"], marker=marker, linewidth=2, color=color, label=label)
        ax.set_title(mode)
        ax.set_xlabel("rho_bar")
        ax.grid(True, color="#dddddd", linewidth=0.7)
    axes[0].set_ylabel("err_total at z=0.55")
    axes[1].legend(frameon=False)
    fig.suptitle("Loss term drives decision flips")
    fig.tight_layout()
    path = out_dir / "decision_error_loss_mechanism_z055.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def _err_at_z055(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = df[(df["z_key"] == "0.550") & (df["mode"].isin(["poisson", "h2"]))].copy()
    return df.groupby(["mode", "rho_bar"])["err_total"].mean().reset_index()


def _margin_cv_mean(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    df = df[df["mode"].isin(["poisson", "h2"])].copy()
    return df.groupby(["mode", "rho_bar"])["margin_cv"].mean().reset_index()


def plot_margin_cv_vs_error(
    margin_cv_unimodal: str,
    margin_cv_operational: str,
    unimodal_path: str,
    operational_raw_path: str,
    out_dir: Path,
) -> Path:
    plt = _plt()
    parts = []
    for label, cv_path, err_path in [
        ("sigma=0.0096", margin_cv_unimodal, unimodal_path),
        ("operational sigma", margin_cv_operational, operational_raw_path),
    ]:
        cv = _margin_cv_mean(cv_path)
        err = _err_at_z055(err_path)
        merged = cv.merge(err, on=["mode", "rho_bar"], how="inner")
        merged["set"] = label
        parts.append(merged)
    df = pd.concat(parts, ignore_index=True)
    fig, ax = plt.subplots(figsize=(7.4, 5.2))
    colors = {"poisson": "#b4452c", "h2": "#2f6f73"}
    markers = {"sigma=0.0096": "o", "operational sigma": "s"}
    for (mode, label), group in df.groupby(["mode", "set"]):
        ax.scatter(
            group["margin_cv"],
            group["err_total"],
            s=62,
            marker=markers[label],
            color=colors[mode],
            label="%s, %s" % (mode, label),
            alpha=0.92,
            zorder=3,
        )
        for _, row in group.iterrows():
            ax.annotate(
                "%.3f" % row["rho_bar"],
                (row["margin_cv"], row["err_total"]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=8,
            )
    ax.axvline(0.35, color="#777777", linestyle="--", linewidth=1.0, label="R=0.35")
    ax.set_xlabel("R = sd(cost margin) / mean(cost margin)")
    ax.set_ylabel("err_total at z=0.55")
    ax.set_title("Decision error collapses by cost-margin CV")
    ax.grid(True, color="#dddddd", linewidth=0.7)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    path = out_dir / "decision_error_margin_cv_vs_err.png"
    fig.savefig(path, dpi=180)
    plt.close(fig)
    return path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summary", default=SUMMARY)
    ap.add_argument("--prediction", default=PREDICTION)
    ap.add_argument("--constant-sigma", default=CONSTANT_SIGMA)
    ap.add_argument("--tau-paths", default=",".join(TAU_PATHS))
    ap.add_argument("--unimodal", default=UNIMODAL)
    ap.add_argument("--w2500", default=W2500)
    ap.add_argument("--delay-only", default=DELAY_ONLY)
    ap.add_argument("--margin-cv-unimodal", default=MARGIN_CV_UNIMODAL)
    ap.add_argument("--margin-cv-operational", default=MARGIN_CV_OPERATIONAL)
    ap.add_argument("--operational-raw", default=OPERATIONAL_RAW)
    ap.add_argument("--out-dir", default=OUT_DIR)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    z055 = _z055(args.summary, args.prediction)
    tau_paths = tuple(part.strip() for part in args.tau_paths.split(",") if part.strip())
    paths = [
        plot_prediction_vs_measured(z055, out_dir),
        plot_decomposition(args.summary, out_dir),
        plot_d_sla_ci(z055, out_dir),
        plot_constant_sigma(args.summary, args.constant_sigma, out_dir),
        plot_tau_scaling(tau_paths, out_dir),
    ]
    if Path(args.unimodal).exists() and Path(args.w2500).exists() and Path(args.delay_only).exists():
        paths.append(plot_loss_mechanism(args.unimodal, args.w2500, args.delay_only, out_dir))
    if Path(args.margin_cv_unimodal).exists() and Path(args.margin_cv_operational).exists():
        paths.append(
            plot_margin_cv_vs_error(
                args.margin_cv_unimodal,
                args.margin_cv_operational,
                args.unimodal,
                args.operational_raw,
                out_dir,
            )
        )
    for path in paths:
        print("plot -> %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

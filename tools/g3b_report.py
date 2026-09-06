#!/usr/bin/env python3
"""Audit saved G3b observations and export a Vietnamese result report.

Run after acquisition/teardown. No network traffic and no gate amendments.
"""
from __future__ import annotations

import csv
import json
import platform
import sys
from pathlib import Path

import numpy as np

from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g3b_sigma_tau_grid import adjudicate, orthogonality
from tools.measurement_path_calib import estimate_nugget


BASE = Path("results/SMOKE/phase-G2")
REPORT = Path("docs/phase-G/66-g3b-results.md")


def write_csv(path, rows):
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    source = BASE / "g3b_sigma_tau.json"
    raw_path = BASE / "g3b_sigma_tau_series.npz"
    payload = json.loads(source.read_text())
    cells = payload["cells"]
    raw = np.load(raw_path, allow_pickle=False)
    per_link, diagnostics, target_cells = [], [], []
    for cell in cells:
        tau, sigma = cell["tau_s"], cell["sigma_ref"]
        rho = raw[f"rho_t{tau:g}_s{sigma:g}"]
        target = raw[f"tgt_t{tau:g}_s{sigma:g}"]
        expected_shape = (cell["n_replicates"], cell["n_windows"], len(raw["ifaces"]))
        assert rho.shape == target.shape == expected_shape
        assert np.isfinite(rho).all() and np.isfinite(target).all()
        sigma_target = np.array(cell["replicates"][0]["sigma_target_per_link"])
        tau_measured, ratio_measured, tau_target, ratio_target = [], [], [], []
        variances, acf1s, sf_measured = [], [], []
        for rep in range(len(rho)):
            checkpoint = BASE / "g3b_sigma_tau_checkpoints" / f"t{tau:g}_s{sigma:g}_rep{rep}.npz"
            with np.load(checkpoint, allow_pickle=False) as saved:
                np.testing.assert_array_equal(saved["rho"], rho[rep])
                np.testing.assert_array_equal(saved["target"], target[rep])
            for link, iface in enumerate(raw["ifaces"]):
                fit = estimate_nugget(rho[rep, :, link], .1, cell["n_lags"], lag_lo=2)
                tgt_fit = estimate_nugget(target[rep, :, link], .1, cell["n_lags"], lag_lo=2)
                stored = cell["replicates"][rep]
                np.testing.assert_allclose(fit["tau_from_fit_s"], stored["tau_hat_per_link"][link],
                                           rtol=1e-12, atol=1e-12)
                np.testing.assert_allclose(fit["sigma_true"], stored["sigma_hat_per_link"][link],
                                           rtol=1e-12, atol=1e-12)
                np.testing.assert_allclose(fit["sf"], stored["sf_per_link"][link],
                                           rtol=1e-12, atol=1e-12)
                sf_measured.append(fit["sf"])
                tau_measured.append(fit["tau_from_fit_s"])
                ratio_measured.append(fit["sigma_true"] / sigma_target[link])
                tau_target.append(tgt_fit["tau_from_fit_s"])
                ratio_target.append(tgt_fit["sigma_true"] / sigma_target[link])
                eps = rho[rep, :, link] - target[rep, :, link]
                centered = eps - eps.mean()
                variances.append(float(eps.var(ddof=1)))
                acf1s.append(float(centered[:-1] @ centered[1:] / (centered @ centered)))
                per_link.append({
                    "tau_s": tau, "sigma_ref": sigma, "replicate": rep,
                    "iface": str(iface), "sigma_target": float(sigma_target[link]),
                    "tau_hat_s": fit["tau_from_fit_s"],
                    "tau_rel_error": float(fit["tau_from_fit_s"] / tau - 1),
                    "sigma_hat": fit["sigma_true"],
                    "sigma_ratio": float(fit["sigma_true"] / sigma_target[link]),
                    "sf": fit["sf"], "fit_ok": fit["ok"],
                    "n_lags_used": fit["n_lags_used"],
                    "target_tau_hat_s": tgt_fit["tau_from_fit_s"],
                    "target_sigma_ratio": float(tgt_fit["sigma_true"] / sigma_target[link]),
                    "residual_variance": variances[-1], "residual_acf1": acf1s[-1],
                })
        np.testing.assert_allclose(np.median(tau_measured), cell["tau_hat_median"], rtol=1e-12)
        np.testing.assert_allclose(np.median(ratio_measured), cell["sigma_ratio_median"], rtol=1e-12)
        sf_per_link = np.median(np.array(sf_measured).reshape(len(rho), -1), axis=0)
        np.testing.assert_allclose(sf_per_link, cell["sf_per_link_median"], rtol=1e-12)
        np.testing.assert_allclose(min(sf_per_link), cell["sf_min_over_links"], rtol=1e-12)
        target_cells.append({"tau_s": tau, "sigma_ref": sigma,
                             "tau_hat_median": float(np.median(tau_target)),
                             "sigma_ratio_median": float(np.median(ratio_target))})
        diagnostics.append({
            **target_cells[-1],
            "target_tau_rel_error": float(np.median(tau_target) / tau - 1),
            "residual_variance_median": float(np.median(variances)),
            "residual_acf1_median": float(np.median(acf1s)),
            "measured_minus_target_tau_s": float(cell["tau_hat_median"] - np.median(tau_target)),
            "measured_minus_target_sigma_ratio": float(cell["sigma_ratio_median"] - np.median(ratio_target)),
        })
    raw.close()
    recomputed = adjudicate(cells, orthogonality(cells))
    assert recomputed == payload["gates"], (recomputed, payload["gates"])

    infra = [json.loads(line) for line in (BASE / "g3b_infra.jsonl").read_text().splitlines()]
    samples = [row for row in infra if not row.get("_header")]
    infra_summary = {"n_samples": len(samples), "span_s": samples[-1]["t_mono_s"],
                     "cpu_percent_median": float(np.median([r["cpu_percent"] for r in samples])),
                     "cpu_percent_p95": float(np.percentile([r["cpu_percent"] for r in samples], 95)),
                     "load_1m_max": max(r["load_1m"] for r in samples),
                     "clock_skew_abs_max_ms": max(abs(r["clock_skew_ms"]) for r in samples),
                     "steal_recorded": False}
    for key in ("drop_in", "drop_out", "err_in", "err_out"):
        infra_summary[key + "_increase"] = samples[-1][key] - samples[0][key]

    result_rows = [{k: c[k] for k in ("tau_s", "sigma_ref", "n_replicates", "n_windows", "n_lags",
                                    "tau_hat_median", "tau_rel_error", "sigma_ratio_median",
                                    "sigma_rel_error", "sf_min_over_links", "max_target_clip",
                                    "max_abs_sink_error", "max_underrun", "max_delta_rms_s")}
                   for c in cells]
    write_csv(BASE / "g3b_roundtrip.csv", result_rows)
    write_csv(BASE / "g3b_per_link.csv", per_link)
    audit = {"schema": "dt4n.phase_g2.g3b_saved_series_audit.v1",
             "status": "REANALYSIS_NO_NEW_NETWORK_DATA", "raw_reproduction_pass": True,
             "checkpoint_identity_pass": True, "gates_identical": True,
             "source_sha256": sha256_of(source), "series_sha256": sha256_of(raw_path),
             "target_only_diagnostics": diagnostics,
             "target_only_orthogonality": orthogonality(target_cells),
             "infrastructure": infra_summary,
             "analysis_environment": {"python": sys.version, "numpy": np.__version__,
                                      "kernel": platform.release(), "machine": platform.machine(),
                                      "captured_after_acquisition": True},
             "note": "Diagnostic only; nominal targets and signed gates are unchanged."}
    write_contract_artifact(BASE / "g3b_saved_series_audit.json", audit)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    labels = [f"tau={c['tau_s']:g}s\nsigma={c['sigma_ref']:.3f}" for c in cells]
    for ax, field, gate, title in zip(axes, ("tau_rel_error", "sigma_rel_error"),
                                    (20, 10), ("Tau recovery", "Sigma recovery")):
        ax.axhspan(-gate, gate, color="#e2f2e9", label=f"Signed limit +/-{gate}%")
        ax.axhline(0, color="#666", linewidth=.8)
        ax.scatter(range(len(cells)), [100*c[field] for c in cells], color="#185b8e", s=55, zorder=3)
        ax.set_xticks(range(len(cells)), labels, fontsize=8)
        ax.set_ylabel("Relative error (%)")
        ax.set_title(title)
        ax.legend(fontsize=8)
    fig.suptitle(f"G3b measured kernel path — {payload['gates']['verdict']}")
    figure = BASE / "g3b_roundtrip.png"
    if figure.exists():
        raise FileExistsError(figure)
    fig.savefig(figure, dpi=170)
    plt.close(fig)

    maxval = lambda key: max(c[key] for c in cells)
    minval = lambda key: min(c[key] for c in cells)
    ortho = payload["orthogonality"]
    gate_rows = [
        ("RT-C1", max(abs(c["sigma_rel_error"]) for c in cells), "<= 0.10"),
        ("RT-B1_small_tau", max(abs(c["tau_rel_error"]) for c in cells if c["tau_s"] <= 5), "<= 0.20"),
        ("RT-B1_tau30", next((abs(c["tau_rel_error"]) for c in cells if c["tau_s"] == 30), None), "<= 0.20"),
        ("RT-O1", abs(ortho["d_log_tau_hat_d_log_sigma"]) if ortho.get("available") else None, "<= 0.10"),
        ("RT-O2", abs(ortho["d_log_sigma_ratio_d_log_tau"]) if ortho.get("available") else None, "<= 0.05"),
        ("T-5", minval("lag_span_over_tau"), ">= 0.30"),
        ("Q-1", minval("quantisation_headroom_min"), ">= 4.36"),
        ("C-1", maxval("max_target_clip"), "<= 0.01"),
        ("B-1a", minval("sf_min_over_links"), ">= 0.8264"),
        ("S-1", maxval("max_abs_sink_error"), "<= 0.02"),
        ("K-2", maxval("max_underrun"), "<= 0.001"),
    ]
    lines = ["# G′.3b — Kết quả đo σ/τ và kiểm tra trực giao", "",
             f"**Phán quyết: `{payload['gates']['verdict']}`.** Dữ liệu đo trên 8 link veth/HTB của kernel, trên host hiện tại.",
             f"Bắt đầu: {payload['started_utc']}; hoàn tất: {payload['finished_utc']}.",
             f"Đã thực hiện {sum(c['n_replicates'] for c in cells)} lượt, {len(cells)}/5 ô; "
             f"tổng thời lượng đo danh định {sum(c['T_run_s'] * c['n_replicates'] for c in cells):g} s.",
             f"Prereg: [doc 65](65-prereg-g3b-sigma-tau-roundtrip.md), tag `phase-G2-g3b-prereg`, commit `{payload['prereg_commit']}`.",
             "Ngưỡng và cách tổng hợp được giữ nguyên sau khi ký. Host không quiesce.", "",
             "## 1. Bảng đánh giá gate", "", "| Gate | Số đo | Ngưỡng đã ký | Kết quả |", "|---|---:|---|---|"]
    for name, value, threshold in gate_rows:
        observed = "CHƯA ĐO" if value is None else f"{value:.8g}"
        verdict = "CHƯA ĐO" if value is None else ("PASS" if payload["gates"][name] else "FAIL")
        lines.append(f"| {name} | {observed} | {threshold} | {verdict} |")
    lines += ["", f"Lưới đầy đủ: {payload['gates']['complete_grid']}; tất cả ước lượng hữu hạn: {payload['gates']['finite_estimates']}.",
              "", "## 2. Bảng round-trip", "",
              "σ̂/σ được chia theo σ thiết kế của từng link trước khi lấy trung vị gộp qua link/lượt.", "",
              "| τ đặt (s) | σ_ref | Lượt | Lags fit | τ̂ (s) | Sai số τ | σ̂/σ | Sai số σ |",
              "|---:|---:|---:|---|---:|---:|---:|---:|"]
    for c in cells:
        lines.append(f"| {c['tau_s']:g} | {c['sigma_ref']:.3f} | {c['n_replicates']} | 2–{c['n_lags']} | "
                     f"{c['tau_hat_median']:.6f} | {c['tau_rel_error']:+.3%} | {c['sigma_ratio_median']:.6f} | {c['sigma_rel_error']:+.3%} |")
    lines += ["", "![Round-trip errors](../../results/SMOKE/phase-G2/g3b_roundtrip.png)", "",
              "## 3. Trực giao", "", "```json", json.dumps(ortho, indent=2), "```", "",
              "Thống kê đã ký lấy trung bình có dấu của hai độ dốc rồi mới lấy trị tuyệt đối.",
              "Không diễn giải PASS của trung bình thành giới hạn cho từng độ dốc riêng hoặc từng link.", "",
              "## 4. Dụng cụ hỗ trợ và đối chiếu chuỗi thô", "",
              f"Controller delta_rms lớn nhất: {maxval('max_delta_rms_s')*1000:.6f} ms.",
              "Clipping, signal fraction, sink và underrun nằm trong bảng gate ở trên.",
              "Đã tính lại estimator từ NPZ và đối chiếu mọi ước lượng từng link/lượt với JSON (rtol=1e-12).",
              "Đã đối chiếu từng mảng checkpoint với NPZ tổng hợp bằng so sánh bằng nhau chính xác.",
              "Kết quả gate tính lại trùng khớp. Không chạy lại mạng cho bước đối chiếu này.", "",
              "| τ | σ_ref | τ̂ từ target | σ̂/σ từ target | Var(measured−target) trung vị | ACF residual lag 1 trung vị |",
              "|---:|---:|---:|---:|---:|---:|"]
    for d in diagnostics:
        lines.append(f"| {d['tau_s']:g} | {d['sigma_ref']:.3f} | {d['tau_hat_median']:.6f} | "
                     f"{d['sigma_ratio_median']:.6f} | {d['residual_variance_median']:.6g} | {d['residual_acf1_median']:.6f} |")
    lines += ["", "Các số từ target chỉ dùng chẩn đoán biến động mẫu hữu hạn và đường đo; không thay thế σ/τ danh định trong gate.",
              "", "Hạ tầng:", "", "```json", json.dumps(infra_summary, indent=2), "```", "",
              "## 5. Điều đã thiết lập", "",
              "Code estimator hỗ trợ lag_lo=2 và giữ kết quả số cũ với mặc định lag_lo=1 (200 chuỗi hồi quy).",
              "Bảy kiểm thử chuẩn bị PASS; mô phỏng khả thi và dry-run PASS trước khi đo mạng.",
              "Các số và kết quả gate ở mục 1–3 là bằng chứng đo được cho đúng host, cấu hình và các ô đã thực hiện.",
              "Chuỗi đo, chuỗi target, từng replicate và log hạ tầng được giữ lại để kiểm toán.", "",
              "## 6. Điều chưa thiết lập và giới hạn", "",
              "- Đây là đường kernel veth/HTB; không phải phép thử NIC vật lý, Internet hoặc nhiều host.",
              "- Trung vị gộp 16 hoặc 8 ước lượng link/lượt của G3b khác protocol trung vị 3 lượt sau hiệu chỉnh b(tau) ở doc 55.",
              "- Không chứng nhận các điểm τ/σ chưa đo, toàn miền khả thi, hoặc trực giao ở τ=30 chỉ có một mức σ.",
              "- Tám quá trình target độc lập không tự chứng minh tám quan sát độc lập qua kernel dùng chung.",
              "- Log hạ tầng hiện có không ghi CPU steal riêng; không suy ra số steal từ CPU/load.",
              "- Mô phỏng và dry-run là SYNTHETIC_NO_NETWORK; các gate sink/clip/underrun ở dry-run là giá trị giả lập.",
              "- Các sửa lỗi code mẫu trước khi đo (phương sai nhiễu, guard dt, Q-1, lưu checkpoint) được ghi ở prereg mục 7.",
              "", "## 7. Artifact và SHA256", "",
              "Số liệu ô: `g3b_roundtrip.csv`; từng link/lượt: `g3b_per_link.csv`; toàn bộ kết quả: `g3b_sigma_tau.json`.",
              "Chuỗi thô: `g3b_sigma_tau_series.npz`; dữ liệu mỗi lượt: `g3b_sigma_tau_checkpoints/`.",
              "Các đường dẫn dưới đây tính từ thư mục gốc repository.", "",
              "| Artifact | SHA256 |", "|---|---|"]
    artifacts = [source, raw_path, BASE / "g3b_bias_sim.json", BASE / "g3b_dry_run.json",
                 BASE / "g3b_signed_dry/g3b_dry_run.json", BASE / "g3b_infra.jsonl",
                 BASE / "g3b_roundtrip.csv", BASE / "g3b_per_link.csv",
                 BASE / "g3b_saved_series_audit.json", figure]
    artifacts += sorted((BASE / "g3b_logs").glob("*"))
    artifacts += sorted((BASE / "g3b_sigma_tau_checkpoints").glob("*"))
    artifacts += [Path(p) for p in (
        "tools/g3b_report.py", "tools/g3b_sigma_tau_grid.py", "tools/g3b_bias_sim.py",
        "tools/measurement_path_calib.py", "test/test_estimator_lag_lo.py",
        "test/test_g3b_sigma_tau_grid.py", "docs/phase-G/65-prereg-g3b-sigma-tau-roundtrip.md")]
    manifest = {str(p): sha256_of(p) for p in artifacts if p.is_file()}
    for path, digest in manifest.items():
        lines.append(f"| [{path}](../../{path}) | `{digest}` |")
    with REPORT.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    manifest[str(REPORT)] = sha256_of(REPORT)
    write_contract_artifact(BASE / "g3b_artifact_manifest.json", {
        "schema": "dt4n.phase_g2.g3b_artifact_manifest.v1", "sha256": manifest})
    print("\n".join(lines[:lines.index("## 3. Trực giao")]))
    print(f"\nReport: {REPORT}\nAudit: {BASE / 'g3b_saved_series_audit.json'}")


if __name__ == "__main__":
    main()

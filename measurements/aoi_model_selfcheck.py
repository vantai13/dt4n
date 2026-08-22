#!/usr/bin/env python3
r"""Lesson 23.19 Task B + C -- selfcheck va doi chung cho aoi_model_v7.

Selfcheck so theo DAI TIEN DOAN, khong theo diem: pha ban dau cua 15 run la
AN SO, nen doi mot chien dich mo phong trung rang voi chien dich quan sat la
doi khop mot thu ngau nhien.

Preregistration: docs/phase-23/00zzd-amendment-47.md muc 5
Chay:
    python measurements/aoi_model_selfcheck.py \
        --campaign results/RAW/phase-23/aoi_v7_campaign \
        --out results/LIVE/phase-23/aoi_model_selfcheck.json
"""
from __future__ import annotations

import argparse, glob, json, os
from collections import defaultdict

import numpy as np

from measurements.aoi_model_v7 import ALPHA_S, AoIModelV7
from measurements.aoi_stall_anatomy import WARMUP_CYCLES, load_jsonl

LINKS = ["ac", "ad", "bc", "bd", "uA", "uB", "vC", "vD"]


def _pairs(campaign):
    out = []
    for f in sorted(glob.glob(os.path.join(campaign, "**", "aoi_clean_*.jsonl"),
                              recursive=True)):
        c = os.path.join(os.path.dirname(f),
                         os.path.basename(f).replace("aoi_", "cycles_", 1))
        if os.path.exists(c):
            out.append((f, c))
    return out


def recompute_alpha(campaign) -> dict:
    """M-109b -- tinh lai alpha DOC LAP tren du lieu DA CAT warm-up.

    M-109 nhu ban ke hoach de xuat (so alpha_fwd voi alpha_rev) KHONG
    ESTIMABLE: trong mot chieu doc, `link` va `read_pos` cong tuyen HOAN
    TOAN, nen thiet ke bi khuyet hang (rank 8/9) va he so tach tuy y giua
    hai cot. Chinh su luan phien fwd/rev lam alpha DINH DANH duoc -- do la
    ly do NC-R cua 23.8 bao `design_rank 9/9`.

    Thay bang: tinh lai alpha bang CUNG thiet ke (dummy link + read_pos)
    tren du lieu DA CAT warm-up, roi so voi gia tri cong bo.
    """
    A, L, P = [], [], []
    for f, c in _pairs(campaign):
        tcut = {r["cycle"]: r["t_cycle_start"]
                for r in load_jsonl(c)}.get(WARMUP_CYCLES)
        for row in load_jsonl(f):
            if row.get("record") != "probe":
                continue
            for l, v in row["links"].items():
                if v.get("aoi_s") is None or (tcut and v["t_obs"] < tcut):
                    continue
                A.append(v["aoi_s"] * 1000)
                L.append(LINKS.index(l))
                P.append(v["read_pos"])
    A, L, P = np.array(A), np.array(L), np.array(P)
    X = np.zeros((A.size, 9))
    for j in range(8):
        X[L == j, j] = 1.0
    X[:, 8] = P
    beta, *_ = np.linalg.lstsq(X, A, rcond=None)
    rank = int(np.linalg.matrix_rank(X))
    a = beta[:8] - beta[:8].mean()
    mine = {LINKS[j]: float(a[j]) for j in range(8)}
    pub = {k: v * 1000 for k, v in ALPHA_S.items()}
    diff = {k: mine[k] - pub[k] for k in pub}
    mx = max(abs(v) for v in diff.values())
    return {
        "_note": ("M-109 nhu ky KHONG estimable (link x read_pos cong tuyen "
                  "trong mot chieu doc). Thay bang M-109b."),
        "design_rank": rank, "design_columns": 9,
        "beta_ms_per_pos": float(beta[8]),
        "alpha_recomputed_ms": mine, "alpha_published_ms": pub,
        "diff_ms": diff, "M_109b_max_abs_diff_ms": mx, "M_109b_hit": mx < 2.0,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-campaigns", type=int, default=200)
    a = ap.parse_args()
    N = a.n_campaigns

    alpha_chk = recompute_alpha(a.campaign)

    m = AoIModelV7()
    sc = m.selfcheck(n_campaigns=N)                       # M-110
    pc_proc = AoIModelV7().selfcheck(n_campaigns=N // 2, mode="process")  # M-111
    pc_d = AoIModelV7(d_s=0.1436).selfcheck(n_campaigns=N // 2)           # M-112

    # M-113 (NC bit-exact) KHONG chay o day: no phai import bo sinh z CU,
    # ma mot artifact vai tro MEASURES thi khong duoc dung bo sinh z nao
    # (amendment 23-45a muc 3, kiem bang AST trong test_no_stale_axes.py).
    # NC do song trong bo test, la cho dung cua no:
    #     test/test_phase23_aoi_model.py::test_negative_control_is_bit_exact
    # NC23v3-2: alpha = 0 -> sd mo phong = T/sqrt(12)
    u0 = AoIModelV7(profile="U0")
    z0 = u0.process_mode(2_000_000, 0.005, "ac") * 1000
    sd_expect = u0.T * 1000 / np.sqrt(12)

    from measurements import validity as V
    import measurements.aoi_model_selfcheck as _self
    rep = {
        "schema": "dt4n.aoi.model_selfcheck.v1",
        "lesson": "23.19", "task": "B+C",
        "prereg": "docs/phase-23/00zzd-amendment-47.md",
        "status": "MEASUREMENT_ESTIMATE",
        "model_params": {"d_ms": m.d * 1000, "d_ci95_ms": 6.5,
                         "T_ms": m.T * 1000, "profile": m.profile},
        "M_109b_alpha_stability": alpha_chk,
        "M_110_selfcheck": sc,
        "M_110_hit": sc["pass"],
        "M_111_process_mode_misuse": {
            "n_inside": pc_proc["n_inside"], "pass": pc_proc["pass"],
            "hit": not pc_proc["pass"],
            "_note": "PC: dung nham process_mode cho selfcheck PHAI fail"},
        "M_112_wrong_d": {
            "d_ms": 143.6, "mean_band_ms": pc_d["band_ms"]["mean"],
            "mean_inside": pc_d["inside"]["mean"],
            "hit": not pc_d["inside"]["mean"],
            "_note": "PC: d = p05 PHAI fail o mean"},
        "M_113_negative_control": {
            "enforced_by": ("test/test_phase23_aoi_model.py::"
                            "test_negative_control_is_bit_exact"),
            "_note": ("d=0.051, T=0.5, alpha=0, phase0=-d phai trung KHIT bo "
                      "sinh cu. Khong bit-exact = da doi HAI thu. Chay trong "
                      "bo test chu khong o day: artifact vai tro MEASURES "
                      "khong duoc import bo sinh z (amendment 23-45a muc 3).")},
        "NC23v3_2_u0_sd": {
            "sd_simulated_ms": float(z0.std(ddof=1)),
            "sd_expected_ms": float(sd_expect),
            "rel_error": float(abs(z0.std(ddof=1) - sd_expect) / sd_expect),
            "hit": bool(abs(z0.std(ddof=1) - sd_expect) / sd_expect < 0.001)},
        "validity": V.measurement_validity_block(
            instrument_module=_self,
            inputs=["results/LIVE/phase-23/aoi_sampling_diagnostic.json"],
            note="Artifact DO/KIEM chinh truc tuoi z va mo hinh cua no."),
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w", encoding="utf-8"), indent=1, sort_keys=True)

    print("=" * 70)
    print("TASK B + C -- SELFCHECK va DOI CHUNG cho aoi_model_v7")
    print("-" * 70)
    print(f"  M-109b alpha tinh lai vs cong bo, lech lon nhat : "
          f"{alpha_chk['M_109b_max_abs_diff_ms']:.3f} ms  HIT={alpha_chk['M_109b_hit']}")
    print(f"         (M-109 nhu ky KHONG estimable -- rank "
          f"{alpha_chk['design_rank']}/9 chi dat khi GOP fwd+rev)")
    print(f"  M-110  selfcheck instrument_mode : {sc['n_inside']}/4 trong dai"
          f"   HIT={sc['pass']}")
    for k in ("mean", "p05", "p50", "p95"):
        b = sc["band_ms"][k]
        print(f"         {k:5} dai [{b['lo']:8.2f}, {b['hi']:8.2f}]  quan sat "
              f"{sc['observed_ms'][k]:8.2f}  {'TRONG' if sc['inside'][k] else 'NGOAI'}")
    print(f"  M-111  PC dung nham process_mode -> fail? "
          f"{not pc_proc['pass']}   HIT={not pc_proc['pass']}")
    print(f"  M-112  PC d=143.6 -> fail o mean? "
          f"{not pc_d['inside']['mean']}   HIT={not pc_d['inside']['mean']}")
    print(f"  M-113  NC bit-exact: xem test_phase23_aoi_model.py"
          f"::test_negative_control_is_bit_exact")
    print(f"  NC23v3-2 U0 sd {rep['NC23v3_2_u0_sd']['sd_simulated_ms']:.4f} vs "
          f"{rep['NC23v3_2_u0_sd']['sd_expected_ms']:.4f} ms  "
          f"HIT={rep['NC23v3_2_u0_sd']['hit']}")
    print("=" * 70)


if __name__ == "__main__":
    main()

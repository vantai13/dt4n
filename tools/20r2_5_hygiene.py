#!/usr/bin/env python3
"""20R2.5 F4 -- VE SINH, chay TRUOC khi mo mot duong cong ket qua nao. [NT 56, F5]

CHI kiem VALIDITY. KHONG in, KHONG tong hop mot cot ket qua nao. Cac cot ket
qua chi duoc dung o H6 de so BANG NHAU TUNG BIT giua hai nhanh -- so sanh
bang nhau, khong doc gia tri, nen khong he lo ket qua.

VI SAO PHAI COMMIT VE SINH TRUOC KHI XEM KET QUA
================================================
Neu ve sinh va ket qua duoc xem CUNG LUC: khi ket qua xau, ta bi cam do di
"tim mot loi ve sinh" de bien minh; khi ket qua dep, ta bo qua loi ve sinh.
Commit truoc bien ve sinh thanh NHAN CHUNG CO DAU THOI GIAN. Do la blind
analysis cua vat ly hat (Klein & Roodman 2005), va la NT 56: tach gate
validity khoi gate outcome.

H9 (CPU) la hang BUDGET, KHONG vao phan quyet validity: lech ngan sach khong
lam ket qua sai, no chi lam du bao sai.

    python -m tools.20r2_5_hygiene --out docs/phase-20R2/05-hygiene.json
Ma thoat 0 = moi kiem VALIDITY PASS; 1 = co FAIL -> SUA nguyen nhan, khong dien giai.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/phase-20R2/03-run-plan.json"
LOG = ROOT / "docs/phase-20R2/04-campaign-log.jsonl"
# Cac cot SO -- dung o H6 CHI de so bang nhau tung bit.
NUM = ("err_total", "err_model", "err_stale", "d_sla",
       "rms_e_model", "rms_e_stale", "cov_e")
EXO_LABEL = "exogenous_g114_S-B"


def _sha(p: pathlib.Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _side(p: pathlib.Path) -> pathlib.Path:
    return p.with_name(p.name[: -len(".parquet")] + "_report.json")


def main(argv=None) -> int:
    import measurements.decision_error_v2 as DE
    from measurements.sla_calib_v2 import DEFAULT_DT
    from cert.realizability_gate import realizability_gate

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    log = [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]
    checks: dict = {}

    def put(name, ok, category="VALIDITY", **info):
        checks[name] = {"verdict": "PASS" if ok else "FAIL", "category": category, **info}

    ok_runs = {e["run_index"]: e for e in log if e["kind"] == "run" and e["returncode"] == 0}

    # H1 -- du va KHOP KE HOACH. Khong chi dem: doi chieu tung truong, vi mot
    # chien dich du 167 file nhung chay sai tham so van la 167 file.
    fields = ("tau", "branch", "a", "seed", "n", "is_canary", "out")
    missing = [r["run_index"] for r in plan["runs"] if r["run_index"] not in ok_runs]
    mism = [r["run_index"] for r in plan["runs"] if r["run_index"] in ok_runs
            and any(ok_runs[r["run_index"]][k] != r[k] for k in fields)]
    put("H1_complete_and_matches_plan", not missing and not mism,
        missing=missing, mismatched=mism, n_planned=len(plan["runs"]),
        n_logged_ok=len(ok_runs))

    # H2 -- MOT chien dich = MOT commit = MOT moi truong.
    envs = [e for e in log if e["kind"] == "env"]
    commits = sorted({e["git_commit"] for e in log if e["kind"] != "env"})
    # [20R2.5-C3] tag co the bi dời; so cai phai TU chung minh no chay dung
    # commit DA KY, thay vi tin rang tag hom nay van tro cho cu.
    tag_ok = bool(envs) and envs[0].get("signed_tag_commit") == envs[0].get("git_commit")
    put("H2_single_commit_single_env",
        len(envs) == 1 and len(commits) == 1
        and not envs[0].get("guard_skipped") and tag_ok,
        n_env=len(envs), commits=commits,
        guard_skipped=bool(envs and envs[0].get("guard_skipped")),
        signed_tag_commit=(envs[0].get("signed_tag_commit") if envs else None),
        tag_points_at_campaign_commit=tag_ok)

    # H3 -- so cai la nguon su that: file tren dia phai KHOP sha da ghi.
    bad3 = [e["run_index"] for e in ok_runs.values()
            if _sha(ROOT / e["out"]) != e["sha256"]
            or _sha(_side(ROOT / e["out"])) != e["sidecar_sha256"]]
    put("H3_sha_on_disk_matches_log", not bad3, bad=bad3, n_checked=len(ok_runs))

    # H4 -- doi chung dung cu OM TRON chien dich: PASS truoc lenh dau, PASS sau
    # lenh cuoi. Mot dung cu chi dung o dau khong noi gi ve luc no gay giua chung.
    kinds = [e["kind"] for e in log]
    last = lambda k: len(kinds) - 1 - kinds[::-1].index(k)
    ok4 = ("control_pre" in kinds and "control_post" in kinds and "run" in kinds
           and kinds.index("control_pre") < kinds.index("run")
           and last("control_post") > last("run")
           and all(e["returncode"] == 0 for e in log if e["kind"].startswith("control")))
    put("H4_perfect_twin_brackets_campaign", ok4,
        note="thay NC1b (menh de luon dung) bang doi chung qua run_cell [20R2.5-P4]")

    # H5 -- diem canh: span = 0. VA doi chung AM cua chinh no: cac lenh KHONG
    # phai diem canh phai ra sha KHAC nhau. Neu moi lenh cung sha thi span = 0
    # vi mot ly do TAM THUONG (vd tham so seed bi bo qua), khong phai vi may on.
    can = [e for e in ok_runs.values() if e["is_canary"]]
    non = [e for e in ok_runs.values() if not e["is_canary"]]
    put("H5_canary_span_zero_with_negative_control",
        len({e["sha256"] for e in can}) == 1
        and len({e["sha256"] for e in non}) == len(non),
        n_canary=len(can), n_distinct_canary_sha=len({e["sha256"] for e in can}),
        n_non_canary=len(non), n_distinct_non_canary=len({e["sha256"] for e in non}),
        note="so sha PARQUET; sidecar mang duong dan nen khac nhau theo cau tao")

    # H6 -- CRN: hai nhanh dung CUNG (tau, a, seed, n) nen dong rho(t) giong
    # het tung bit; chi luoi z khac. Vay tai cac diem z CHUNG, hai nhanh PHAI
    # trung tung bit. NEO B chi kiem dieu nay o tau=3 (no D8); o day kiem
    # tren MOI (tau, a, seed) -- 80 cap, khong ton them mot giay CPU nao.
    shared = sorted(set(DE.Z_ALL) & set(DE.Z_ALL_20R2))
    pairs: dict = {}
    for e in non:
        pairs.setdefault((e["tau"], e["a"], e["seed"]), {})[e["branch"]] = e
    sel = lambda d: (d[d["z_s"].isin(shared)]
                     .sort_values(["mode", "rho_bar", "z_s"]).reset_index(drop=True))
    diff6 = []
    for key, pr in sorted(pairs.items()):
        if set(pr) != {"main", "control_legacy"}:
            diff6.append({"key": list(key), "why": "thieu mot nhanh"})
            continue
        x = sel(pd.read_parquet(ROOT / pr["main"]["out"]))
        y = sel(pd.read_parquet(ROOT / pr["control_legacy"]["out"]))
        if len(x) != len(y) or not all(
                np.array_equal(x[c].to_numpy(), y[c].to_numpy(), equal_nan=True)
                for c in NUM):
            diff6.append({"key": list(key), "why": "lech tai diem z chung"})
    put("H6_crn_shared_z_bit_identical", not diff6 and len(pairs) == 80,
        n_pairs=len(pairs), shared_z=shared, differing=diff6,
        closes="20R2-D8 o quy mo chien dich (80 cap x 10 o), mien phi nho CRN")

    # H7 -- VALIDITY TAI NGUON: doc sidecar cua chinh artifact, khong doc loi
    # khai o cho khac. z_grid_id phai SUY RA tu diem z that va phai khop nhanh.
    viol7 = []
    for e in non:
        v = json.loads(_side(ROOT / e["out"]).read_text(encoding="utf-8"))["validity"]
        derived = DE.z_grid_id_of(v["aoi_axis"]["z_grid_s"])
        probs = [p for p, bad in (
            ("sla_axis", v["sla_axis"]["label"] != EXO_LABEL),
            ("z_grid", derived != plan["branches"][e["branch"]]["z_grid"]
                       or v.get("z_grid_id") != derived),
            ("estimand_by_field", v.get("estimand_by_field") != DE.ESTIMAND_BY_FIELD),
            ("axis_role", v.get("axis_role") != "aoi_axis_free"),
        ) if bad]
        if probs:
            viol7.append({"run_index": e["run_index"], "problems": probs})
    put("H7_validity_at_source", not viol7 and len(non) == 160,
        violations=viol7, n_checked=len(non),
        note="z_grid_id SUY RA tu diem z, khong nhan loi khai [20R2.5-P5]")

    # H8 -- realizability LUOT 2, tren so DO DUOC cua chinh chien dich (luot 1
    # chay o n NEN va tren so DU BAO). Anh xa "so do nao cam vao tieu chi nao"
    # da KY o ke hoach, khong duoc chon o day.
    frames = []
    for e in non:
        d = pd.read_parquet(ROOT / e["out"])
        d["branch"] = e["branch"]
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    rows8 = []
    for (br, mode, rb, tau, sig), g in d.groupby(
            ["branch", "mode", "rho_bar", "tau_rho", "sigma_rho"]):
        n = int(g["n"].iloc[0])
        blocks = int(math.floor(n * DEFAULT_DT / (DE.BLOCKS_PER_TAU * float(tau))))
        r = realizability_gate(
            mode=str(mode), rho_bar=float(rb), tau=float(tau), dt=DEFAULT_DT, n=n,
            sigma=float(sig),
            clip_fraction=float(g["ar1_clip_ratio"].max()),
            min_cell_blocks=blocks)
        if r["verdict"] != "REALIZABLE":
            rows8.append({"branch": br, "cell": "%s@%.3f" % (mode, rb), "tau": float(tau),
                          "verdict": r["verdict"],
                          "failed": [k for k, c in r["checks"].items()
                                     if isinstance(c, dict) and c.get("ok") is False]})
    put("H8_realizability_pass2_on_measured", not rows8,
        n_cells=int(d.groupby(["branch", "mode", "rho_bar", "tau_rho", "sigma_rho"]).ngroups),
        rejected=rows8, mapping=plan["realizability_pass2_mapping"])

    # H9 -- NGAN SACH, khong phai validity. Lech ngan sach khong lam ket qua sai.
    secs = sum(e["seconds"] for e in non)
    signed = float(plan["budget"]["signed_minutes_two_branches"])
    tol = float(plan["budget"]["tolerance"])
    got = secs / 60.0
    put("H9_cpu_within_budget", abs(got - signed) <= tol * signed, category="BUDGET",
        measured_minutes=got, signed_minutes=signed, tolerance=tol,
        ratio=(got / signed if signed else float("nan")),
        note="chi lenh khong-canary; doi chung twin-hoan-hao khong tinh vao")

    validity = {k: v for k, v in checks.items() if v["category"] == "VALIDITY"}
    n_fail = sum(1 for v in validity.values() if v["verdict"] == "FAIL")
    doc = {
        "schema": "dt4n.hygiene_20r2_5.v1",
        "generated_by": "tools/20r2_5_hygiene.py",
        "WHAT_THIS_IS": ("Gate VALIDITY -- 'dung cu va so sach co sach khong'. "
                         "KHONG chua mot cot ket qua nao. Phai COMMIT truoc khi "
                         "mo 20R2.6 [F5, NT 56]."),
        "plan_sha256": _sha(PLAN),
        "log_sha256": _sha(LOG),
        "n_validity_checks": len(validity),
        "n_validity_failed": n_fail,
        "verdict": "PASS" if n_fail == 0 else "FAIL",
        "checks": checks,
    }
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n",
                   encoding="utf-8")
    for k in sorted(checks):
        print("  %-8s %-42s %s" % (checks[k]["category"], k, checks[k]["verdict"]))
    print("\nVE SINH: %s (%d/%d kiem validity FAIL)" % (doc["verdict"], n_fail, len(validity)))
    if n_fail:
        print("SUA nguyen nhan. Neu la ma: amendment + tag moi + chay lai TOAN BO.")
        print("KHONG BAO GIO 'sua du lieu'.")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

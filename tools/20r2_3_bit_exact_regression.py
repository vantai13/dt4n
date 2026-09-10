"""20R2.3 -- DOI CHUNG HOI QUY bit-exact tren 166 parquet cua sweep_r2.

DAY LA DOI CHUNG HOI QUY, KHONG PHAI KET QUA KHOA HOC  [gate 3-3, S26]
=====================================================================
No tra loi DUNG MOT cau: "ma hom nay co con lam DUNG NHUNG GI no lam hom qua
khong?". No KHONG tra loi "hom qua lam co dung khong".

    Mot golden CHEP LAI CA LOI. Neu hom qua sai, hom nay sai y het => PASS.

Mot dong "bit-exact PASS" trong luan van ma khong kem nhan nay se duoc doc
thanh "ket qua da duoc xac nhan". Hai chuyen khac han nhau.

DO PHU -- va day moi la phan quan trong  [gate 3-4]
===================================================
Doi chung hoi quy neo CHINH XAC nhung doan ma ban KHONG doi.

    Duong ma neo nay di qua : Z_ALL (9 diem legacy) - nhanh SLA cu -
                              lag k = round(z/dt) tren luoi cu
    Duong ma CHIEN DICH di   : Z_ALL_20R2 (13 diem) - SLA exogenous -
                              dispatch --z-grid MOI VIET

    => Giao cua hai = phan KHONG doi.
    => Ma MOI cua G4 (Z_GRIDS, dispatch --z-grid) KHONG duoc neo nay phu.

"bit-exact PASS" ma khong khai do phu la mot phat bieu DUNG dan toi mot ket
luan SAI. Cho ma moi, xem NEO B trong test/test_20r2_3_anchors.py: cac bat
bien TAT DINH, khong dua vao qua khu.

CO --z-grid TRONG LENH LICH SU
==============================
`cmd` trong run_log sinh TRUOC G4 nen KHONG co `--z-grid`, ma co do gio la
required=True. Phat lai nguyen van se that bai. Tool nay THEM `--z-grid legacy`
-- dung gia tri ma T2 da chay ngam. Gia tri khong doi; chi loi khai doi.

Chay:
    python -m tools.20r2_3_bit_exact_regression --out results/PENDING/phase-20R2/bit_exact_regression.json
    python -m tools.20r2_3_bit_exact_regression --out ... --limit 3    # kiem nhanh
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
RUN_LOG_REL = "results/PENDING/phase-T2/sweep_r2/run_log.jsonl"

# T2 chay tren luoi legacy. Truoc G4 do la mac dinh IM LANG.
REPLAY_Z_GRID = "legacy"


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _entries() -> list:
    out = []
    with open(REPO / RUN_LOG_REL, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def _replay_cmd(entry: dict, out_path: str) -> list:
    """Lenh phat lai. THEM --z-grid legacy vi lenh lich su khong co no."""
    cmd = list(entry["cmd"])
    if "--z-grid" not in cmd:
        # cmd = ["-m", "<module>", ...] -- chen SAU ten module, khong phai sau "-m"
        assert cmd[0] == "-m", "dang cmd la khac: %r" % cmd[:2]
        cmd = cmd[:2] + ["--z-grid", REPLAY_Z_GRID] + cmd[2:]
    # thay --out bang duong dan tam
    i = cmd.index("--out")
    cmd[i + 1] = out_path
    return [sys.executable] + cmd


def run(limit: int | None, reuse_rows: str | None = None) -> dict:
    """Phat lai va so sha. `reuse_rows` chi LAM MOI SIEU DU LIEU.

    `reuse_rows` doc lai `rows` cua mot artifact da co thay vi chay lai 166
    lenh (~35 phut). CHI dung khi thay doi la sieu du lieu tinh (khai do phu,
    ghi chu) -- KHONG dung khi ma do da doi, vi luc do `rows` cu khong con noi
    len dieu gi ve ma hom nay. Artifact ghi ro no da tai dung hang.
    """
    if reuse_rows:
        prev = json.loads(pathlib.Path(reuse_rows).read_text(encoding="utf-8"))
        rows = prev["rows"]
        t0 = time.time() - prev["summary"]["elapsed_s"]
        return _assemble(rows, t0, reused_from=reuse_rows)

    entries = _entries()
    if limit:
        entries = entries[:limit]
    tmp = tempfile.mkdtemp()
    rows = []
    t0 = time.time()
    for e in entries:
        out = os.path.join(tmp, "replay_r%04d.parquet" % e["run_index"])
        cmd = _replay_cmd(e, out)
        r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
        actual = _sha256(pathlib.Path(out)) if os.path.exists(out) else None
        rows.append({
            "run_index": e["run_index"],
            "tau": e["tau"], "seed": e["seed"], "a": e.get("a"),
            "branch": e.get("branch"),
            "is_canary": bool(e.get("is_canary")),
            "git_commit_original": e.get("git_commit"),
            "sha_expected": e["sha256"],
            "sha_actual": actual,
            "match": actual == e["sha256"],
            "returncode": r.returncode,
            "stderr_tail": r.stderr[-300:] if r.returncode else "",
        })
        if os.path.exists(out):
            os.remove(out)

    return _assemble(rows, t0)


def _assemble(rows: list, t0: float, reused_from: str | None = None) -> dict:
    n_match = sum(1 for x in rows if x["match"])
    mism = [x for x in rows if not x["match"]]
    return {
        "schema": "dt4n.bit_exact_regression.v1",
        "generated_by": "tools/20r2_3_bit_exact_regression.py",
        "WHAT_THIS_IS": (
            "DOI CHUNG HOI QUY: ma hom nay co con lam DUNG NHUNG GI no lam hom "
            "qua khong. KHONG phai mot ket qua khoa hoc, va KHONG noi rang ket "
            "qua hom qua la dung -- mot golden chep lai ca loi.  [gate 3-3, S26]"),
        "anchors": {
            "NOTE": (
                "HAI neo, KHAC CAP. Khai ca hai kem DO PHU cua tung cai -- chon "
                "mot roi im la de nguoi doc tu suy ra mot do phu khong co that."),
            "A1_generator_digest": {
                "path": "results/RAW/phase-T2/golden/ar1_tau1.0_poisson_0.925_s101.json",
                "what_it_anchors": (
                    "BO SINH DAU VAO: measurements.sla_calib_v2.ar1_matrix. "
                    "Digest sha256 cua mang 200000x8 float64."),
                "axis_independent": True,
                "why_digest_not_array": (
                    "mang 200k x 8 float64 = 12.8 MB, va .gitignore:64 chi cho "
                    "qua *.json trong results/. Digest 64 ky tu cho doi chung "
                    "BIT-EXACT y het (sha khac <=> bytes khac) VA chay duoc "
                    "tren clone sach. Mot golden khong nam trong git la mot "
                    "doi chung khong ton tai voi nguoi khac."),
                "coverage": "bo sinh AR(1); KHONG cham truc AoI hay SLA",
            },
            "A2_pipeline_parquet": {
                "path": "results/PENDING/phase-T2/sweep_r2/*.parquet (166 tep)",
                "manifest": "results/PENDING/phase-T2/sweep_r2/run_log.jsonl",
                "what_it_anchors": (
                    "TOAN DUONG ONG tren nhanh LEGACY: truth table -> cost -> "
                    "argmin -> err/d_sla, tren luoi z 9 diem."),
                "axis_independent": False,
                "coverage": "nhanh legacy DAY DU; nhanh 20r2_measured KHONG",
            },
        },
        "coverage": {
            "code_path_anchored": (
                "Z_ALL (9 diem legacy), nhanh SLA cu, lag k = round(z/dt)"),
            "code_path_of_campaign": (
                "Z_ALL_20R2 (13 diem), SLA exogenous, dispatch --z-grid"),
            "NOT_anchored": [
                "measurements/decision_error_v2.py Z_GRIDS / Z_ALL_20R2",
                "dispatch --z-grid trong main()",
                "nhanh SLA exogenous_g114_S-B",
            ],
            "why_it_matters": (
                "Doi chung hoi quy neo CHINH XAC nhung doan ma KHONG doi. Ma "
                "moi cua G4 vua duoc viet, tuc la cho rui ro cao nhat, va no "
                "KHONG co artifact lich su nao de so. Xem NEO B: "
                "test/test_20r2_3_anchors.py -- bat bien TAT DINH."),
            "gate_3_4": (
                "'bit-exact PASS' ma khong khai do phu la mot phat bieu DUNG "
                "dan toi mot ket luan SAI."),
        },
        "replay": {
            "z_grid_added": REPLAY_Z_GRID,
            "why": ("lenh trong run_log sinh TRUOC G4 nen khong co --z-grid, ma "
                    "co do gio la required=True. Gia tri khong doi -- T2 von "
                    "chay luoi legacy; chi loi khai doi."),
        },
        "summary": {
            "n_runs": len(rows),
            "n_match": n_match,
            "n_mismatch": len(mism),
            "all_match": not mism,
            "elapsed_s": time.time() - t0,
            "mismatched_run_index": [x["run_index"] for x in mism],
            "rows_reused_from": reused_from,
            "rows_are_fresh": reused_from is None,
        },
        "rows": rows,
    }


def _validity() -> dict:
    return {
        "schema": "dt4n.validity.v1",
        "axis_role": "bit_exact_regression",
        "pending_on": ["aoi_axis", "sla_axis"],
        "aoi_axis": {
            "label": "UNREGISTERED", "z_grid_s": [],
            "note": ("doi chung hoi quy tren nhanh LEGACY; no khong dieu kien "
                     "theo truc AoI da ky cua 20R2"),
        },
        "sla_axis": {
            "label": "UNREGISTERED", "match_method": "none",
            "note": "chay tren nhanh SLA cu cua T2, khong phai exogenous cua 20R2",
        },
        "omega": None, "w_loss": None,
        "note": ("DOI CHUNG HOI QUY, khong phai ket qua khoa hoc. Khong duoc "
                 "promote len LIVE/ nhu mot ket qua."),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None,
                    help="chi phat lai N lenh dau (kiem nhanh)")
    ap.add_argument("--reuse-rows", default=None,
                    help="lam moi SIEU DU LIEU tu artifact da co, khong chay lai. "
                         "CHI dung khi ma do KHONG doi.")
    args = ap.parse_args()

    doc = run(args.limit, args.reuse_rows)
    doc["validity"] = _validity()
    doc["generated_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=True)
        fh.write("\n")

    s = doc["summary"]
    print("=== 20R2.3: DOI CHUNG HOI QUY bit-exact ===")
    print("(KHONG phai ket qua khoa hoc -- golden chep lai ca loi)")
    print("\nphat lai %d lenh (them --z-grid %s)" % (s["n_runs"], REPLAY_Z_GRID))
    print("KHOP     : %d" % s["n_match"])
    print("LECH     : %d %s" % (s["n_mismatch"], s["mismatched_run_index"] or ""))
    print("thoi gian: %.1f s%s" % (
        s["elapsed_s"], "" if s["rows_are_fresh"] else "  (TAI DUNG hang cu)"))
    print("\nDO PHU: neo nay KHONG phu %s"
          % ", ".join(doc["coverage"]["NOT_anchored"]))
    print("-> %s" % os.path.relpath(args.out, REPO))
    if not s["all_match"]:
        raise SystemExit("co %d lenh KHONG tai lap bit-exact" % s["n_mismatch"])


if __name__ == "__main__":
    main()

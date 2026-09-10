"""Cong cu 20R2 phai CHAY DUOC va TAI LAP DUOC, khong chi artifact phai dung.

VI SAO CAN BO TEST NAY -- lo hong no bit:

Bo test hien co kiem SAN PHAM (artifact) chu khong kiem DAY CHUYEN (tool).
Mot tool co the hong hoan toan ma moi test van xanh, mien la artifact cu con
nam tren dia. Do duoc 2026-09-10:

    $ python -m tools.20r2_0_axis_audit --out results/PENDING/phase-20R2/axis_audit.json
    TypeError: %d format: a real number is required, not NoneType
    $ echo $?
    1                       <- MA LOI, tren dung lenh trong docstring cua tool

Ba he qua, khong phai mot:

 1. ARTIFACT DUNG, TOOL DO. JSON duoc ghi TRUOC khi crash (24219 byte, so
    dung, n_grid_cells = 800). Trang thai la: tep ton tai VA lenh that bai.
    Day la to hop te nhat -- `set -e` chan buoc sau, ma tren dia lai co mot
    artifact trong nhu hoan chinh.
 2. SO QUAN TRONG NHAT KHONG BAO GIO IN RA. Dong crash chinh la dong in ngan
    sach A7 -- con so 800 o / 29.4 phut ma ca phase dua vao.
 3. KHONG TEST NAO DO, suot 3 commit. Do chinh la loai loi mot bo test
    kiem-san-pham KHONG THE thay.

Bo test nay la CHAN cho 20R2.3: golden chi co nghia neu tool sinh ra no con
chay duoc. Trong san xuat, phan biet nay goi la process validation (kiem day
chuyen) vs product inspection (kiem san pham). Kiem san pham bat duoc lo hang
hong; kiem day chuyen bat duoc LY DO lo sau se hong.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMITTED = ROOT / "results/PENDING/phase-20R2"

# module -> (thu muc, ten artifact da commit ma no phai tai lap)
#
# MOI tool TAT DINH cua 20R2 phai co mat o day. Mot tool khong nam trong bang
# nay la mot tool KHONG AI CANH -- dung lo hong ma chinh bo test nay sinh ra de
# bit. Do duoc 2026-09-10: 4 tool moi cua 20R2.2/20R2.4 deu tai lap bit-identical
# nhung KHONG co gi kiem dieu do.
PENDING_DIR = "results/PENDING/phase-20R2"
DOCS_DIR = "docs/phase-20R2"

TOOLS = {
    "tools.20r2_0_axis_audit": (PENDING_DIR, "axis_audit"),
    "tools.20r2_4_realizability_audit": (PENDING_DIR, "realizability_audit"),
    "tools.20r2_1_canary_span": (PENDING_DIR, "canary_span"),
    "tools.20r2_1_parquet_recovery": (PENDING_DIR, "parquet_recovery"),
    # 20R2.2 / 20R2.4
    "tools.20r2_2_predictions": (DOCS_DIR, "01-prediction-signed"),
    "tools.20r2_2_se_pilot": (DOCS_DIR, "02-se-pilot"),
    "tools.20r2_4_grid_and_gate": (PENDING_DIR, "grid_prescreen"),
    "tools.20r2_4_em_over_a": (PENDING_DIR, "em_over_a"),
    "tools.20r2_4_n3_n4_recheck": (PENDING_DIR, "n3_n4_baseline"),
    # 20R2.5 -- ke hoach chien dich. TAT DINH CO CHU DICH: khong mang
    # git_commit/git_dirty, nen sinh lai bao gio cung ra cung sha256. Chinh vi
    # the no vao duoc bang nay, khac t2_6_plan (mang provenance thoi diem nen
    # sinh lai ra hash khac, va guard phai do hai bien the hash).
    "tools.20r2_5_plan": (DOCS_DIR, "03-run-plan"),
}

# tools.20r2_4_cpu_pilot CO Y DE NGOAI: no DO THOI GIAN, nen KHONG tat dinh --
# hai lan chay lech ~1% (do duoc: +21.4% roi +20.0%). Dua no vao bang tren se
# tao mot phep so bit-exact DO THUONG TRUC, va "do thuong truc thi da chet"
# (Phu luc B). No duoc kiem RIENG o duoi bang exit code + luoc do, KHONG bang
# bit-exact. Ghi ly do o day de nguoi sau khong "sua" bang cach them no vao.
NON_DETERMINISTIC = {"tools.20r2_4_cpu_pilot": (PENDING_DIR, "cpu_pilot")}

# Bang nay HIEN RONG, va do la trang thai TOT -- giu lai vi cau truc.
#
# `tools.20r2_2_se_pilot` TUNG o day: parquet pilot bi .gitignore:64 loai, nen
# tren clone sach tool khong chay lai duoc. Da sua bang cach `git add -f` 10
# parquet (444 KB) vao results/RAW/phase-20R2/se_pilot/ -- dung tien le ma
# commit 60a88784 dat ra khi bao ton 166 parquet cua T2.
# Ly do bao ton: 10 parquet nay la BANG CHUNG cua luat se_rel = C/sqrt(N), va
# luat do la tham so cua BANG CHAP NHAN DA KY. Mot bang ma nguoi khac khong
# kiem lai duoc thi khong phai mot bang da ky.
REQUIRES_LOCAL_RAW: dict = {}

# tools.20r2_3_bit_exact_regression TAT DINH nhung CHAY 31 PHUT (phat lai 166
# lenh). Dua vao TOOLS se lam bo test cham hon 15 lan va khong ai chay no nua
# -- mot test khong ai chay la mot test da chet, cung ket cuc voi test do
# thuong truc. No duoc kiem RIENG bang mot phep chay --limit nho.
TOO_SLOW_FOR_SUITE = {
    "tools.20r2_3_bit_exact_regression": (PENDING_DIR, "bit_exact_regression"),
}

# 20R2.5 -- ba tool KHONG chay duoc trong bo test, moi cai mot ly do KHAC nhau.
# Chung van phai duoc CANH, nen moi cai ghi ro no duoc kiem O DAU.
NEEDS_SIGNED_CAMPAIGN = {
    # Tat dinh, nhung ~3-4 phut (2 luoi x 8 tau x 10 o). Duoc kiem bang HANH VI
    # o test_20r2_3_anchors.py: mot test chay that qua run_cell, mot test cay
    # loi lech-mot va DOI doi chung phai do (mutation testing).
    "tools.20r2_5_perfect_twin": "cham (~3-4 phut); kiem hanh vi o test_20r2_3_anchors.py",
    # Guard doi tag DA KY co tren remote, roi chay 75-97 phut va ghi 167 file.
    # Kiem o duoi: guard phai TU CHOI khi chua ky.
    "tools.20r2_5_run": "doi tag da ky + 75-97 phut; kiem guard tu choi o duoi",
    # Doc so cai cua mot chien dich DA CHAY. Truoc do khong co gi de kiem.
    "tools.20r2_5_hygiene": "can chien dich da chay xong (04-campaign-log.jsonl)",
    # 20R2.6 -- doi tag phase-20R2-adjudicator-frozen CO tren remote + du lieu
    # chien dich. Duoc kiem RIENG tren du lieu GIA o
    # test/test_20r2_6_adjudicator.py (12 test, 8 mutation deu bi bat).
    "tools.20r2_6_adjudicate": "doi tag adjudicator-frozen + du lieu chien dich; "
                               "kiem tren du lieu GIA o test_20r2_6_adjudicator.py",
}

# Truong doi theo THOI DIEM chay, khong theo NOI DUNG. Loai truoc khi so.
VOLATILE = ("generated_utc", "generated_at")


def _run(module: str, out: pathlib.Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", module, "--out", str(out), *extra],
        cwd=str(ROOT), capture_output=True, text=True,
    )


@pytest.mark.parametrize("module,spec", sorted(TOOLS.items()))
def test_tool_exits_zero_on_its_own_documented_command(module, spec, tmp_path):
    """DAY CHUYEN: lenh trong docstring cua tool phai thoat ma 0.

    Khong kiem noi dung o day -- chi kiem tool CHAY XONG. Tach rieng khoi
    phep kiem tai lap ben duoi de khi do, thong bao noi dung cai gi hong.
    """
    r = _run(module, tmp_path / (spec[1] + ".json"))
    assert r.returncode == 0, (
        module + " thoat ma " + str(r.returncode)
        + " tren lenh docstring cua chinh no:\n" + r.stderr[-1500:]
    )


@pytest.mark.parametrize("module,spec", sorted(TOOLS.items()))
def test_tool_reproduces_the_committed_artifact(module, spec, tmp_path):
    """TAI LAP: chay lai phai ra DUNG thu da commit.

    Neu test nay do ma test thoat-ma-0 o tren xanh, thi tool con chay nhung
    da DOI DAU RA -- artifact da commit khong con la san pham cua tool nua.
    """
    subdir, artifact = spec
    committed = ROOT / subdir / (artifact + ".json")
    if not committed.is_file():
        pytest.skip("chua co artifact da commit: " + artifact)
    out = tmp_path / (artifact + ".json")
    r = _run(module, out)
    if r.returncode != 0:
        pytest.skip("tool khong chay duoc -- xem test thoat-ma-0")
    a = json.loads(committed.read_text(encoding="utf-8"))
    b = json.loads(out.read_text(encoding="utf-8"))
    for k in VOLATILE:
        a.pop(k, None)
        b.pop(k, None)
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    assert not diff, (
        module + ": khong tai lap duoc artifact da commit.\n"
        "  khoa lech: " + str(diff) + "\n"
        "  -> hoac tool doi hanh vi, hoac artifact da commit bi sua tay.\n"
        "  -> golden cua 20R2.3 chi co nghia neu phep nay xanh."
    )


def test_the_a7_budget_line_is_actually_printed():
    """Canary cho DUNG lop loi da xay ra: so in ra phai la so DA GIAI.

    Loi goc in `args.n_cells` (dau vao, co the None) thay vi gia tri da giai
    tu bang kha thi. Test nay khong kiem "khong crash" -- no kiem con so
    800 THAT SU den duoc man hinh. Mot bai in im lang cung la mot bai in sai.
    """
    r = _run("tools.20r2_0_axis_audit",
             pathlib.Path(__import__("tempfile").mkdtemp()) / "a.json")
    assert r.returncode == 0, r.stderr[-800:]
    assert "A7: ngan sach CPU (800 o)" in r.stdout, (
        "dong ngan sach A7 khong in ra so o da giai.\n" + r.stdout[-800:]
    )


@pytest.mark.parametrize("module,spec", sorted(NON_DETERMINISTIC.items()))
def test_non_deterministic_tool_runs_and_keeps_its_schema(module, spec, tmp_path):
    """Tool DO THOI GIAN: kiem CHAY DUOC + LUOC DO, KHONG kiem bit-exact.

    Doi bit-exact o day se do thuong truc, va mot test do thuong truc thi da
    chet -- khong ai doc no nua. Nhung "khong tat dinh" KHONG co nghia "khong
    kiem duoc": cau truc va cac bat bien van phai dung.
    """
    subdir, artifact = spec
    out = tmp_path / (artifact + ".json")
    # --quick: 3 tau thay vi 8. Test nay kiem DAY CHUYEN va LUOC DO, khong
    # kiem con so, nen khong can tra ~4 phut cho ban day du.
    r = _run(module, out, "--quick")
    assert r.returncode == 0, (
        module + " thoat ma " + str(r.returncode) + ":\n" + r.stderr[-1200:])
    fresh = json.loads(out.read_text(encoding="utf-8"))
    committed = ROOT / subdir / (artifact + ".json")
    if not committed.is_file():
        pytest.skip("chua co artifact da commit")
    old = json.loads(committed.read_text(encoding="utf-8"))
    assert set(fresh) == set(old), (
        module + ": luoc do da doi. khoa lech: "
        + str(sorted(set(fresh) ^ set(old))))
    # Ban --quick do 3 tau roi nhan 8/3, ma QUICK_TAUS chua tau DAT NHAT, nen
    # no thien lech LEN. Vi vay no TU KHAI khong co tham quyen thay vi im lang
    # tra mot verdict sai -- va test doi dung dieu do.
    assert fresh["gate_4_3"]["verdict"] == "NOT_AUTHORITATIVE"
    assert fresh["gate_4_3"]["authoritative"] is False
    assert old["gate_4_3"]["authoritative"] is True, (
        "artifact da commit phai la ban DAY DU (8 tau), khong phai --quick")
    assert old["gate_4_3"]["verdict"] == "PASS"
    # ket luan E4 la bat bien THAT: no khong doi theo nhieu do
    assert fresh["e4_fractional_design"]["needed"] == \
        old["e4_fractional_design"]["needed"]


def test_every_20r2_tool_is_covered_by_one_of_the_two_tables():
    """Mot tool 20R2 khong nam trong bang nao la mot tool KHONG AI CANH.

    Test nay DO khi ai do them tool moi ma quen dang ky -- do la y muon: no
    bat nguoi them phai QUYET tool do tat dinh hay khong, thay vi de no roi
    vao khoang toi.
    """
    import re
    covered = ({m.split(".")[-1] for m in TOOLS}
               | {m.split(".")[-1] for m in NON_DETERMINISTIC}
               | {m.split(".")[-1] for m in REQUIRES_LOCAL_RAW}
               | {m.split(".")[-1] for m in TOO_SLOW_FOR_SUITE}
               | {m.split(".")[-1] for m in NEEDS_SIGNED_CAMPAIGN})
    on_disk = {p.stem for p in (ROOT / "tools").glob("20r2_*.py")}
    # cong cu chi chay mot lan (sinh baseline / smoke) khong sinh artifact ky
    ONE_SHOT = {"20r2_baseline_failures", "20r2_remediation_smoke"}
    missing = sorted(on_disk - covered - ONE_SHOT)
    assert not missing, (
        "tool 20R2 chua duoc dang ky trong test tai lap: " + str(missing)
        + "\n-> them vao TOOLS (neu tat dinh) hoac NON_DETERMINISTIC (neu do "
        "thoi gian / co nguon ngau nhien) hoac NEEDS_SIGNED_CAMPAIGN, KEM LY DO.")


def test_campaign_runner_refuses_until_the_prereg_is_signed():
    """[20R2.5] Guard cua chien dich phai chan TRUOC khi tieu mot giay CPU nao.

    Day la phep kiem THAT cho tools.20r2_5_run trong bo test: khong chay 75
    phut, nhung ep cai chan phai lam viec. Neu tag DA duoc ky (chien dich that
    su duoc phep chay) thi test tu bo qua -- luc do guard dung la PHAI cho qua.
    """
    import subprocess
    tag = "phase-20R2-prereg-signed"
    signed = subprocess.run(["git", "tag", "-l", tag], cwd=str(ROOT),
                            capture_output=True, text=True).stdout.strip()
    if signed:
        pytest.skip("prereg da ky -- guard dung ra phai cho qua")
    r = subprocess.run([sys.executable, "-m", "tools.20r2_5_run"], cwd=str(ROOT),
                       capture_output=True, text=True)
    assert r.returncode != 0, "guard CHO QUA du prereg chua ky -- den xanh rong"
    assert "chua ky" in (r.stdout + r.stderr), (
        "guard dung nhung khong noi VI SAO:\n" + (r.stdout + r.stderr)[-800:])


def test_pin_chain_has_no_cycle():
    """[20R2.5-C1] Chuoi ghim sha256 phai KHONG CO VONG.

    prereg ghim 01-prediction-signed.json va 03-run-plan.json. Neu ai do them
    prereg vao `inputs_sha256` cua ke hoach, vong khep lai va KHONG FILE NAO
    KY DUOC NUA: sha cua prereg phu thuoc ke hoach, ma ke hoach lai ghim sha
    cua prereg. Cung ban chat voi o "Commit sha cua ban duoc ky" o §11 -- mot
    file khong the chua sha256 cua chinh no.

    TRICH DAN duong dan (vd "authority": ".../00-preregistration.md") thi KHONG
    tao vong -- no khong phu thuoc NOI DUNG. Chi GHIM SHA moi tao vong.
    """
    import json as _json
    plan_p = ROOT / "docs/phase-20R2/03-run-plan.json"
    if not plan_p.is_file():
        pytest.skip("chua sinh ke hoach")
    pinned = _json.loads(plan_p.read_text(encoding="utf-8"))["inputs_sha256"]
    for path in pinned:
        assert "preregistration" not in path, (
            "ke hoach GHIM SHA cua prereg (%s) -> vong tu quy chieu: prereg "
            "ghim ke hoach, ke hoach ghim prereg. Khong ai ky duoc nua." % path)


def test_campaign_plan_is_a_pure_function_of_its_inputs():
    """[20R2.5] Ke hoach KHONG duoc mang git_commit/git_dirty.

    t2_6_plan ghi provenance thoi diem VAO ke hoach, nen sinh lai cho cung thu
    tu nhung KHAC hash, va guard phai do hai bien the hash. Thoi diem thuoc ve
    SO CAI va TAG. Test nay giu cho bai hoc do khong bi hoan tac.
    """
    import json as _json
    p = ROOT / "docs/phase-20R2/03-run-plan.json"
    if not p.is_file():
        pytest.skip("chua sinh ke hoach")
    blob = _json.loads(p.read_text(encoding="utf-8"))
    for banned in ("git_commit", "git_dirty", "generated_utc", "generated_at"):
        assert banned not in blob, (
            "ke hoach mang truong theo THOI DIEM (%s) -> khong con tat dinh"
            % banned)


@pytest.mark.parametrize("module,spec", sorted(REQUIRES_LOCAL_RAW.items()))
def test_local_raw_tool_fails_loudly_when_the_raw_data_is_absent(module, spec, tmp_path):
    """Thieu du lieu tho phai bao TO, khong duoc sinh am tham mot ket qua khac.

    Tren clone sach thu muc RAW rong. Neu tool cu chay va sinh mot artifact tu
    tap con it hon thi ta co hai artifact cung ten, khac noi dung, khong ai
    biet -- dung hinh dang cua den xanh rong.
    """
    out = tmp_path / (spec[1] + ".json")
    empty = tmp_path / "empty"
    empty.mkdir()
    r = _run(module, out, "--raw-dir", str(empty))
    assert r.returncode != 0, "tool VAN chay khi khong co du lieu tho"
    msg = r.stdout + r.stderr
    assert "gitignore" in msg.lower(), "thong bao khong noi VI SAO thu muc rong"
    assert "--measure" in msg, "thong bao khong chi cach khac phuc"
    assert not out.exists(), "tool da ghi artifact du that bai"


@pytest.mark.parametrize("module,spec", sorted(TOO_SLOW_FOR_SUITE.items()))
def test_slow_tool_runs_on_a_small_slice(module, spec, tmp_path):
    """Tool qua cham cho ca bo test van phai duoc kiem -- bang mot lat mong.

    Phat lai 3 lenh dau thay vi 166. Kiem DAY CHUYEN (chay duoc, so sha dung)
    ma khong tra 31 phut. Ban day du duoc chay tay va artifact cua no da commit.
    """
    import json as _json
    out = tmp_path / (spec[1] + ".json")
    r = _run(module, out, "--limit", "3")
    assert r.returncode == 0, (
        module + " thoat ma " + str(r.returncode) + ":\n" + r.stderr[-1200:])
    d = _json.loads(out.read_text(encoding="utf-8"))
    assert d["summary"]["n_runs"] == 3
    assert d["summary"]["all_match"], (
        "lat mong 3 lenh KHONG tai lap bit-exact: %s"
        % d["summary"]["mismatched_run_index"])
    assert d["summary"]["rows_are_fresh"] is True


def test_the_committed_regression_artifact_is_a_full_fresh_run():
    """Artifact da commit phai la ban DAY DU va TUOI, khong phai lat mong hay
    ban tai dung hang cu -- neu khong no khong con la mot doi chung."""
    import json as _json
    p = ROOT / "results/PENDING/phase-20R2/bit_exact_regression.json"
    if not p.is_file():
        pytest.skip("chua chay doi chung hoi quy")
    d = _json.loads(p.read_text(encoding="utf-8"))
    s = d["summary"]
    assert s["n_runs"] == 166, "ban da commit chi co %d lenh" % s["n_runs"]
    assert s["rows_are_fresh"] is True, "hang bi TAI DUNG tu artifact khac"
    assert s["all_match"]

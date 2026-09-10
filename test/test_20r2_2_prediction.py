"""20R2.2 -- du doan da KY khong duoc troi, va bang phai KHOP CONG THUC tai z DA KY.

BAY MA RT20-3 NEU DICH DANH:
ban Sheppard cua MASTER_PLAN (0.257 / 0.153 / ...) duoc CHEP chu khong duoc
TINH, va no chi dung o z = 0.369. So sanh mot DU DOAN tai z_A voi mot SO DO
tai z_B la so sanh hai dai luong khac nhau -- va no se KHONG BAO GIO BAO LOI.
Bo test nay bien loi im lang do thanh mot loi ON AO.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIGNED = ROOT / "docs/phase-20R2/01-prediction-signed.json"

# Ghim sha256 cua artifact DA KY. Doi artifact = pha custody => phai amendment.
SIGNED_SHA256 = "8eff683ff4fe115a322b8639bd17d2dd71c58829fefcbf4b2df3670d83bf1d9c"


@pytest.fixture(scope="module")
def pred():
    assert SIGNED.is_file(), "thieu docs/phase-20R2/01-prediction-signed.json"
    return json.loads(SIGNED.read_text(encoding="utf-8"))


def test_signed_prediction_hash_is_pinned():
    """Neu test nay do, artifact da ky DA DOI. Do la mot su kien custody."""
    got = hashlib.sha256(SIGNED.read_bytes()).hexdigest()
    assert got == SIGNED_SHA256, (
        "01-prediction-signed.json DA DOI.\n  ky: " + SIGNED_SHA256
        + "\n  nay: " + got
        + "\n-> artifact da ky KHONG duoc sua. Can amendment moi + hash moi."
    )


def test_signed_prediction_uses_the_same_z_as_the_artifact(pred):
    """Bang du doan va so do phai dung CUNG mot z tham chieu.

    RT20-3: chep bang Sheppard ma khong kiem z. Bang do chi dung o z = 0.369.
    """
    assert pred["z_reference_s"] == pytest.approx(0.3650, abs=1e-9)
    for row in pred["sheppard"]:
        expect = math.acos(math.exp(-pred["z_reference_s"] / row["tau"])) / math.pi
        assert row["err"] == pytest.approx(expect, abs=1e-12), (
            "du doan tai tau=%s KHONG khop cong thuc tai z da ky" % row["tau"])


def test_the_table_is_NOT_the_master_plan_table(pred):
    """Canary: neu ai do chep lai bang z=0.369, test nay do.

    Kiem bang CACH PHAN BIET, khong bang cach tin: tinh bang tai 0.369 va doi
    hoi bang da ky KHAC no.
    """
    for row in pred["sheppard"]:
        wrong = math.acos(math.exp(-0.369 / row["tau"])) / math.pi
        assert row["err"] != pytest.approx(wrong, abs=1e-12), (
            "bang dang o z = 0.369 (bang MASTER_PLAN), khong phai z da ky")


def test_sheppard_is_correct_at_the_three_extreme_points():
    """Kiem mot cong thuc la o ba diem cuc TRUOC khi tin no."""
    f = lambda rho: math.acos(rho) / math.pi
    assert f(1.0) == pytest.approx(0.0)      # giong het -> khong bao gio doi dau
    assert f(0.0) == pytest.approx(0.5)      # doc lap   -> tung dong xu
    assert f(-1.0) == pytest.approx(1.0)     # nguoc han -> luon doi dau


# ------------------------------------------------------------------ estimand

REQUIRED_FIELDS = ("LEVEL", "POPULATION", "SCALE", "UNIT",
                   "BRANCH", "CODE", "ARTIFACT_FIELD")


@pytest.mark.parametrize("eid", ["DECISION_ERR_BY_AGE", "SLA_VIOL_BY_AGE"])
def test_each_estimand_declares_all_seven_fields(pred, eid):
    """Mot muc thieu mot truong la mot muc CHUA DINH NGHIA XONG (luat A-T2-3)."""
    e = pred["estimands"][eid]
    missing = [f for f in REQUIRED_FIELDS if not e.get(f)]
    assert not missing, eid + " thieu truong bat buoc: " + str(missing)


def test_the_two_estimands_differ_in_scale_and_field(pred):
    """Neu hai ID cho cung SCALE va cung ARTIFACT_FIELD thi mot cai la thua."""
    a = pred["estimands"]["DECISION_ERR_BY_AGE"]
    b = pred["estimands"]["SLA_VIOL_BY_AGE"]
    assert a["ARTIFACT_FIELD"] != b["ARTIFACT_FIELD"]
    assert a["UNIT"] != b["UNIT"], "ti le va chi phi khong the cung don vi"


def test_rms_allaction_delay_is_not_reused(pred):
    """RMS_ALLACTION_DELAY dung LEVEL nhung SAI SCALE va SAI ARTIFACT_FIELD.

    Tai dung no la lap lai DUNG loi A-T2-3 (hai dai luong mot ten).
    """
    assert "RMS_ALLACTION_DELAY" not in pred["estimands"]
    for eid, e in pred["estimands"].items():
        assert "rms_e_model" not in e["ARTIFACT_FIELD"], eid


def test_artifact_fields_actually_exist_in_the_harness(pred):
    """Estimand tro vao mot truong KHONG ton tai la mot estimand chet.

    Kiem bang DAU VET trong ma nguon, khong bang tri nho.
    """
    src = (ROOT / "measurements/decision_error_v2.py").read_text(encoding="utf-8")
    lines = src.splitlines()
    for eid, e in pred["estimands"].items():
        field = e["ARTIFACT_FIELD"].split(".")[-1]
        assert ('"%s"' % field) in src, eid + ": khong thay truong " + field
        ln = e.get("ARTIFACT_FIELD_LINE")
        if ln:
            assert ('"%s"' % field) in lines[ln - 1], (
                "%s: dong %d khong con chua '%s' -- so dong DA TROI, "
                "neo lai theo ten ham." % (eid, ln, field))


# ------------------------------------------------------------ bang chap nhan

def test_band_floor_uses_the_residual_not_the_negative_control(pred):
    """San cua bang phai la DO BAT DINH CON LAI, khong phai DOI CHUNG AM.

    Do nhay 'measured vs legacy' (~9%) KHONG phai do bat dinh cua ket qua
    chinh: legacy la doi chung am co chu dich. Lay no lam san se cho mot bang
    rong gap ~6 lan muc can, va bang qua rong lam gate MAT LUC PHAN GIAI.
    """
    ax = pred["axis_sensitivity"]
    band = pred["acceptance_band"]
    floors = [r["axis_floor_rel"] for r in band["per_tau"]]
    assert max(floors) == pytest.approx(
        ax["worst_measured_family_residual_rel"], abs=1e-12)
    assert max(floors) < ax["worst_legacy_contrast_rel"]
    assert band["DO_NOT_USE"]["value_rel"] == pytest.approx(
        ax["worst_legacy_contrast_rel"], abs=1e-12)


def test_band_is_per_tau_because_power_is_not_uniform(pred):
    """Mot bang DUY NHAT gia dinh luc thong ke deu nhau tren luoi. Khong dung.

    `n_for_tau` giu CHI PHI phang nhung khong giu LUC: chu ky doc lap = T_sim/tau
    di tu 2000 (tau=0.5) xuong 50 (tau=20,28) -- 40 lan. Mot so duy nhat se hoac
    qua chat o tau lon hoac qua long o tau nho.
    """
    band = pred["acceptance_band"]
    assert len(band["per_tau"]) == len(pred["taus"])
    bands = [r["band_rel"] for r in band["per_tau"]]
    assert len(set(round(b, 9) for b in bands)) > 1, (
        "bang giong nhau o moi tau -- vay thi no khong theo tau")
    assert "superseded_scalar_band" in band, "mat dau vet ban vo huong cu"


def test_cycle_floor_makes_power_uniform_in_the_tail(pred):
    """SAN CHU KY: co mau hieu dung la T_sim/tau, KHONG phai n.

    Khong co san, cap 20->28 chi dat 2.20 sigma (do duoc) -- duoi nguong 3.
    """
    band = pred["acceptance_band"]
    assert band["cycle_floor"] == 200.0
    for r in band["per_tau"]:
        assert r["independent_cycles"] >= band["cycle_floor"] - 1e-9, (
            "tau=%g chi co %.1f chu ky, duoi san" % (r["tau"], r["independent_cycles"]))
    muls = {r["tau"]: r["n_multiplier"] for r in band["per_tau"]}
    assert muls[0.5] == 1 and muls[5.0] == 1, "khong duoc nang tau nho"
    assert muls[10.0] == 2 and muls[20.0] == 4 and muls[28.0] == 4


def test_band_uses_the_pooled_law_not_noisy_per_tau_estimates(pred):
    """se tu 5 seed KHONG dung lam san bang duoc -- co bang chung doi chung.

    Nang n gap 4 o tau=28 le ra lam se GIAM 2 lan; do duoc no TANG 1.7 lan.
    Mot dai luong ma phep do khong theo kip huong DA BIET thi khong dung duoc
    lam tham so. Vi vay dung LUAT GOP se_rel = C/sqrt(chu ky), uoc MOT tham so
    tu 10 phep do.
    """
    law = pred["acceptance_band"]["se_law"]
    assert law["form"].startswith("se_rel = C / sqrt")
    assert law["which_C_is_used"].startswith("C_upper")
    assert law["C_upper"] > law["C_mean"], "phai bao thu hon trung binh"
    assert abs(law["fitted_exponent"] - law["theoretical_exponent"]) < 0.10, (
        "so mu do duoc %.3f lech xa -0.5 -- luat 1/sqrt(N) khong con dung"
        % law["fitted_exponent"])
    assert law["n_points"] >= 10


def test_band_formula_is_signed_with_no_free_parameters_left(pred):
    """K_MC va CYCLE_FLOOR phai co gia tri TRUOC chien dich.

    Neu chung con mo thi so do co the tu chon he so cho minh -- 'garden of
    forking paths' o dang tinh vi nhat.
    """
    b = pred["acceptance_band"]
    assert b["K_MC"] == 3.0
    assert b["cycle_floor"] == 200.0
    for r in b["per_tau"]:
        assert r["band_rel"] is not None and r["band_rel"] > 0
        assert r["band_rel"] >= r["axis_floor_rel"], (
            "tau=%g: bang hep hon san truc" % r["tau"])


def test_the_widest_band_still_has_resolving_power(pred):
    """Bang rong nhat phai VAN hep hon tuong phan legacy (~9%).

    Neu no rong bang tuong phan doi chung thi gate khong con phan biet duoc
    nhanh measured voi nhanh legacy -- den xanh rong dang 4.
    """
    b = pred["acceptance_band"]
    widest = max(r["band_rel"] for r in b["per_tau"])
    assert widest < pred["axis_sensitivity"]["worst_legacy_contrast_rel"], (
        "bang rong nhat %.3f%% >= tuong phan legacy %.3f%%"
        % (widest * 100,
           pred["axis_sensitivity"]["worst_legacy_contrast_rel"] * 100))


def test_monotonicity_is_counted_in_pairs_not_points(pred):
    """8 tau cho 7 CAP. Don dieu la tinh chat cua mot CAP, khong phai mot DIEM.

    Ban ky dau viet '>= 7/8 diem' -- vua sai don vi vua sai mau so.
    """
    sp = pred["reading_policy"]["SECONDARY_shape"]
    assert sp["n_pairs"] == len(pred["taus"]) - 1 == 7
    assert "6/7" in sp["pass_rule"] and "CAP" in sp["pass_rule"]
    assert "sigma" in sp["statistic"]


# ------------------------------------------------------- POPULATION / doi chung

def test_population_is_the_eight_gate_cells_and_matches_the_artifact(pred):
    """POPULATION la QUYET DINH KHOA HOC, nhung no phai NEO vao artifact.

    Nguon phan hoach la sla_calibration.json, khong phai tri nho.
    """
    calib = json.loads(
        (ROOT / "results/LIVE/phase-20R/sla_calibration.json").read_text())
    s = calib["summary"]
    assert s["n_gate_cells"] == 8 and s["n_pc1_cells"] == 4
    assert s["n_design_cells"] == 12 and s["n_feasible"] == 10
    for eid, e in pred["estimands"].items():
        assert "8 o `gate`" in e["POPULATION"], eid
        assert "DOI CHUNG DUONG" in e["POPULATION"], eid


def test_cbr_is_not_claimed_as_a_positive_control(pred):
    """20R2.4 (E2) rut mot du kien lam DO cach doc cu.

    Mot doi chung DUONG chi co gia tri khi ta BIET TRUOC ket qua phai ra sao.
    cbr suy bien tren truc bien (A_bar ~ 2e-4..4e-4, nho hon o khong-cbr nho
    nhat ~3213 lan; span/pure ~ 0.005 => duong cong theo tuoi PHANG), va o do
    HAI co che keo err ve HAI HUONG NGUOC NHAU:
        (1) cbr deu theo thoi gian  -> twin cu con dung -> err THAP
        (2) bien giua 4 duong ~ 0   -> argmin tuy y     -> err CAO
    Khong co co so tien nghiem chon giua hai. Ky mot bat dang thuc mot chieu
    o day la DOAN, khong phai doi chung.
    """
    pc = pred["reading_policy"]["POSITIVE_CONTROL"]
    assert pc["status"] == "DOWNGRADED_TO_DIAGNOSTIC"
    assert pc["claim"] is None, "khong duoc ky lai mot bat dang thuc mot chieu"
    assert pc["claim_withdrawn"]
    assert "RIENG" in pc["reported"]
    assert pc["signed_before_run"]["both_recorded_before_measurement"] is True


def test_both_cbr_mechanisms_are_recorded_before_measurement(pred):
    """Ghi CA HAI co che TRUOC roi bao cao cai nao thang -- do la quan sat.
    Ghi mot co che roi thay no dung -- do la xac nhan thien lech."""
    m = pred["reading_policy"]["POSITIVE_CONTROL"]["signed_before_run"]
    assert m["mechanism_1_low_err"] and m["mechanism_2_high_err"]


def test_the_real_instrument_check_is_the_perfect_twin_control(pred):
    """Doi chung twin-hoan-hao la rang buoc TAT DINH, khong bi suy bien lam hong.

    Kiem bang DAU VET trong ma, khong bang tri nho.
    """
    pc = pred["reading_policy"]["POSITIVE_CONTROL"]
    assert "twin-hoan-hao" in pc["instrument_check_instead"]
    src = (ROOT / "measurements/decision_error_v2.py").read_text(encoding="utf-8")
    assert "perfect-twin control is required to be exactly zero" in src, (
        "docstring khong con bao dam doi chung twin-hoan-hao = 0 -- "
        "phep kiem dung cu cua 20R2 mat cho dua")


def test_denominator_is_declared_before_the_run(pred):
    d = pred["reading_policy"]["DENOMINATOR"]
    assert d["declared_before_run"] is True
    assert d["n_predictions_scored"] == len(pred["taus"]) == 8


def test_primary_prediction_is_directional_not_a_point(pred):
    """Du doan diem truot la 'khong khop'; du doan co dinh huong SAI CO NGHIA.

    Va no phai liet ke DU hai cach no co the sai.
    """
    p = pred["reading_policy"]["PRIMARY_directional"]
    assert p["claim"] == "err_do >= err_sheppard tai MOI tau"
    assert len(p["if_violated"]) == 2


def test_three_of_four_sheppard_violations_push_err_up(pred):
    """Day la co so cua du doan co dinh huong. Neu no khong con dung, du doan
    khong con dung -- nen no phai duoc ghim, khong phai ghi nho."""
    v = pred["sheppard_is_a_reference_line_not_truth"]["violations"]
    assert len(v) == 4
    up = [x for x in v if x["pushes_err"].startswith("TANG")]
    assert len(up) == 3, "so vi pham day err LEN da doi: %d" % len(up)


# ------------------------------------ nhan estimand phai o MUC TRUONG, khong
#                                      phai chi o muc artifact

def test_harness_declares_estimands_per_field_not_only_per_artifact(pred):
    """Nhan muc-artifact KHONG DU DO PHAN GIAI cho 20R2.

    `run_cell` ghi mot artifact mang MOT `estimand_id`, nhung per_z[] cua no
    chua BA dai luong khac THANG va khac DON VI:
        rms_e_* / cov_e -> RMS_ALLACTION_DELAY (delay_ms)
        err_*           -> DECISION_ERR_BY_AGE (ti le)
        d_sla           -> SLA_VIOL_BY_AGE     (cost_ms)
    Phan quyet mot du doan 20R2 bang nhan muc-artifact la lap lai A-T2-3 o do
    phan giai thap hon. Test nay doi hoi ban do theo TRUONG.
    """
    import measurements.decision_error_v2 as DE
    m = getattr(DE, "ESTIMAND_BY_FIELD", None)
    assert m, "decision_error_v2 chua khai ESTIMAND_BY_FIELD"
    assert m["err_total"] == "DECISION_ERR_BY_AGE"
    assert m["d_sla"] == "SLA_VIOL_BY_AGE"
    assert m["rms_e_model"] == "RMS_ALLACTION_DELAY"
    assert len(set(m.values())) == 3, (
        "ban do phai phan biet DUNG ba estimand; gop lai la mat do phan giai")


def test_every_20r2_estimand_field_is_in_the_harness_map(pred):
    """Estimand da ky ma harness khong biet la mot estimand khong do duoc."""
    import measurements.decision_error_v2 as DE
    for eid, e in pred["estimands"].items():
        field = e["ARTIFACT_FIELD"].split(".")[-1]
        assert DE.ESTIMAND_BY_FIELD.get(field) == eid, (
            "%s: harness anh xa truong '%s' -> %r, khong phai %r"
            % (eid, field, DE.ESTIMAND_BY_FIELD.get(field), eid))


def test_prereg_pins_the_same_hash_as_the_signed_artifact():
    """Hash ghim trong prereg phai con dung. Neu khong, custody da dut.

    Cung tinh than voi test_prereg_hash_still_matches_the_signed_artifact cua
    T2: mot hash ghim trong van ban ma khong ai kiem la mot hash trang tri.
    """
    prereg = (ROOT / "docs/phase-20R2/00-preregistration.md").read_text(
        encoding="utf-8")
    got = hashlib.sha256(SIGNED.read_bytes()).hexdigest()
    assert got in prereg, (
        "prereg khong ghim hash hien tai cua 01-prediction-signed.json.\n"
        "  hash tep: " + got + "\n"
        "  -> cap nhat §12.1, hoac artifact da bi sua ngoai quy trinh.")


def test_prereg_records_the_population_decision_and_the_band_correction():
    """POPULATION va san bang la hai QUYET DINH, phai nam trong van ban ky.

    Mot quyet dinh chi song trong artifact JSON la mot quyet dinh khong ai
    doc. Prereg la noi nguoi ky nhin vao.
    """
    prereg = (ROOT / "docs/phase-20R2/00-preregistration.md").read_text(
        encoding="utf-8")
    assert "LỐI B" in prereg, "prereg chua ghi quyet dinh POPULATION"
    assert "ĐỐI CHỨNG DƯƠNG" in prereg
    assert "AXIS_FLOOR" in prereg, "prereg chua ghi san bang"
    assert "1,47%" in prereg, (
        "prereg chua ghi con so do bat dinh CON LAI (1,47%) -- neu no bien "
        "mat, san bang lai co the bi lay tu tuong phan legacy (~9%)")


def test_the_prediction_tool_still_runs_and_reproduces_the_signed_content():
    """DAY CHUYEN, khong chi SAN PHAM.

    Hash ghim o tren bao ve artifact khoi bi SUA. No KHONG bao ve cong cu
    khoi bi HONG: neu tools/20r2_2_predictions.py ngung chay, hash van khop
    va moi test van xanh -- artifact chi la mot tep tren dia. Do la dung lo
    hong da de tools/20r2_0_axis_audit.py thoat ma 1 suot 3 commit.

    So sanh NOI DUNG (tru truong bien thien), khong so sanh byte: generated_utc
    doi moi lan chay theo THIET KE.
    """
    import subprocess
    import sys
    import tempfile

    out = pathlib.Path(tempfile.mkdtemp()) / "regen.json"
    r = subprocess.run(
        [sys.executable, "-m", "tools.20r2_2_predictions", "--out", str(out)],
        cwd=str(ROOT), capture_output=True, text=True)
    assert r.returncode == 0, (
        "tools/20r2_2_predictions.py thoat ma %d:\n%s"
        % (r.returncode, r.stderr[-1500:]))

    a = json.loads(SIGNED.read_text(encoding="utf-8"))
    b = json.loads(out.read_text(encoding="utf-8"))
    a.pop("generated_utc", None)
    b.pop("generated_utc", None)
    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    assert not diff, (
        "cong cu khong con sinh ra artifact da ky. Khoa lech: " + str(diff)
        + "\n-> hoac cong cu doi hanh vi, hoac artifact bi sua tay.")


# ------------------------------------------------- C_coverage (khai TRUOC)

def test_c_upper_coverage_is_declared_not_assumed():
    """C_upper = trung binh + 1sd KHONG phu het quan sat. Khai ra, dung im.

    Bam theo max quan sat duoc la KHOP THEO NHIEU -- chinh cai ma luat gop sinh
    ra de tranh (C tu no bat dinh ~35% o 5 seed). Nhung "chap nhan khong phu
    het" la mot QUYET DINH, va mot quyet dinh khong duoc khai thi sau nay se
    duoc GIAI THICH -- do la HARKing.
    """
    import json
    p = ROOT / "docs/phase-20R2/02-se-pilot.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    cov = d["C_coverage"]
    assert cov["n_covered_by_C_upper"] < cov["n_observations"], (
        "gio C_upper phu het -- cap nhat lai lap luan, dung de assert nay do im")
    assert cov["why_accepted"], "khong khai VI SAO chap nhan"
    assert cov["if_an_uncovered_cell_fails_the_band"], (
        "khong ky truoc cach doc khi mot o khong duoc phu bi truot")


def test_the_campaign_config_cell_that_is_uncovered_is_flagged():
    """Trong cac diem khong duoc phu, diem nao la CAU HINH CHIEN DICH?

    Mot diem pilot khong duoc phu thi vo hai -- cau hinh do khong con dung.
    Mot diem CHIEN DICH khong duoc phu thi bang o do HEP HON nhieu rieng cua
    no, va o do co the truot vi bang chu khong vi hien tuong.
    """
    import json
    d = json.loads((ROOT / "docs/phase-20R2/02-se-pilot.json").read_text())
    unc = d["C_coverage"]["uncovered"]
    campaign = [u for u in unc if u["is_campaign_config"]]
    assert campaign, (
        "khong con diem chien dich nao ngoai vung phu -- neu that thi tot, "
        "nhung phai cap nhat §14 va bo canh bao di")
    for u in campaign:
        assert u["three_sigma"] > 0
        assert "CHIEN DICH" in u["note"]


def test_band_at_the_uncovered_campaign_cell_is_narrower_than_its_own_noise(pred):
    """Hau qua SO HOC cua viec khong phu, tinh ra chu khong noi chung chung.

    Neu bang o tau do HEP HON 3x se do duoc cua chinh no, thi o do de truot hon
    cac tau khac -- va do la mot ung vien giai thich DA KY TRUOC.
    """
    import json
    d = json.loads((ROOT / "docs/phase-20R2/02-se-pilot.json").read_text())
    bands = {r["tau"]: r["band_rel"] for r in pred["acceptance_band"]["per_tau"]}
    for u in d["C_coverage"]["uncovered"]:
        if not u["is_campaign_config"]:
            continue
        band = bands[u["tau"]]
        assert u["three_sigma"] > band, (
            "tau=%g: 3sigma %.4f%% KHONG con vuot bang %.4f%% -- canh bao het "
            "hieu luc, cap nhat lap luan" % (u["tau"], u["three_sigma"] * 100,
                                             band * 100))

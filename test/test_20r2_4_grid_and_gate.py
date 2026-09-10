"""20R2.4 -- luoi, realizability, ngan sach. Chan DEN XANH RONG.

DEN XANH RONG MA BO TEST NAY CANH
=================================
`cert/realizability_gate.py` tinh verdict bang MOT dong:

    "verdict": "REALIZABLE" if not failed else "REJECTED"     (dong 195)

No CHI nhin `failed`. Mot tieu chi KHONG CHAY co `pass = None`, nen khong bao
gio vao `failed`, nen khong bao gio doi duoc verdict. Gioi han: goi gate ma
khong truyen tieu chi nao -> 0 truot -> REALIZABLE, mot den xanh cho mot o
CHUA BAO GIO DUOC KIEM.

Do duoc 2026-09-10, CUNG o / CUNG ma / CUNG may:
    cbr@0.925, tau=3, dt=0.005, n=200000
      thieu sigma -> REALIZABLE  (3/9 tieu chi not_evaluated)
      du sigma    -> REJECTED    (sigma_max_regime(cbr, 0.925) = 0.0)

LUAT BA GIA TRI: PASS / FAIL / CHUA KIEM. Thieu thong tin KHONG duoc cu xu
nhu thong tin tot. Gate da lam dung phan kho (dung None) va hong o phan de
(dong tong hop lam phang ba gia tri thanh hai).
"""
from __future__ import annotations

import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRESCREEN = ROOT / "results/PENDING/phase-20R2/grid_prescreen.json"
EM_OVER_A = ROOT / "results/PENDING/phase-20R2/em_over_a.json"
CPU_PILOT = ROOT / "results/PENDING/phase-20R2/cpu_pilot.json"
N3N4 = ROOT / "results/PENDING/phase-20R2/n3_n4_baseline.json"

POST_RUN_ONLY = {"censoring_ok", "mondrian_cells_populated"}


def _load(p):
    if not p.is_file():
        pytest.skip("chua sinh %s" % p.name)
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def prescreen():
    return _load(PRESCREEN)


# ------------------------------------------------------- den xanh rong

def test_the_gate_verdict_ignores_not_evaluated():
    """GHIM HANH VI THAT cua gate, de no khong bi hieu nham la an toan.

    Test nay KHONG doi gate phai sua. No ghi lai rang `verdict` la mot cau
    tra loi HEP ("khong tieu chi nao truot"), khong phai cau tra loi rong
    ("o nay do duoc"). Moi nguoi doc artifact phai biet dieu do.
    """
    from cert.realizability_gate import realizability_gate
    r = realizability_gate(mode="cbr", rho_bar=0.925, tau=3.0, dt=0.005,
                           n=200000)                      # THIEU sigma
    assert r["verdict"] == "REALIZABLE", (
        "gate da doi hanh vi -- neu no da nhin not_evaluated thi cap nhat "
        "tai lieu va bo qua canh bao nay")
    assert "sigma_within_headroom" in r["not_evaluated"]
    assert r["failed"] == []


def test_the_same_cell_flips_verdict_when_called_with_full_arguments():
    """CUNG o, CUNG ma: thieu tham so -> xanh; du tham so -> do.

    Day la bang chung so cho '20R2-L4 / den xanh rong'.
    """
    from cert.realizability_gate import realizability_gate
    from twin import cost_v2 as C
    kw = dict(mode="cbr", rho_bar=0.925, tau=3.0, dt=0.005, n=200000)
    smax = C.sigma_max_regime("cbr", 0.925)
    assert smax == 0.0, "cbr@0.925 phai het headroom (sigma_max = 0)"
    thin = realizability_gate(**kw)
    full = realizability_gate(**kw, sigma=0.9 * smax,
                              clip_fraction=0.0, min_cell_blocks=50)
    assert thin["verdict"] == "REALIZABLE"
    assert full["verdict"] == "REJECTED"
    assert full["failed"] == ["sigma_within_headroom"]
    assert full["not_evaluated"] == []


def test_prescreen_tool_rejects_an_empty_green_light():
    """Guard cua E1 phai BAT duoc mot hang xanh-rong bi tiem vao."""
    import importlib
    m = importlib.import_module("tools.20r2_4_grid_and_gate")
    from cert.realizability_gate import realizability_gate
    doc = {"gate_version": 2, "rows": [{
        "mode": "cbr", "rho_bar": 0.925, "tau": 3.0, "a": 0.9,
        **{k: realizability_gate(mode="cbr", rho_bar=0.925, tau=3.0,
                                 dt=0.005, n=200000)[k]
           for k in ("verdict", "failed", "not_evaluated")},
        "gate_version": 2}]}
    with pytest.raises(SystemExit, match="DEN XANH RONG"):
        m._check(doc)


# ------------------------------------------------------- luoi 800

def test_grid_is_800_cells_from_10_feasible_cells(prescreen):
    g = prescreen["grid"]
    assert g["n_cells_mode_rho"] == 10
    assert len(g["taus"]) == 8 and len(g["a_values"]) == 2 and len(g["seeds"]) == 5
    assert g["n_combos_without_seed"] == 160
    assert g["n_grid_cells"] == 800


def test_every_prescreened_cell_is_realizable(prescreen):
    """gate 4-1: o khong realizable KHONG duoc lot im lang vao chien dich."""
    s = prescreen["summary"]
    assert s["n_rejected"] == 0, (
        "%d o truot tien sang: %s" % (s["n_rejected"], s["rejected_by_reason"]))
    assert s["n_realizable"] == 160


def test_prescreen_not_evaluated_is_exactly_the_two_post_run_criteria(prescreen):
    """PHAM VI cua den xanh, khang dinh RIENG khoi verdict.

    Bay tieu chi quyet duoc tu tham so thiet ke; hai tieu chi con lai can gia
    tri SINH RA tu lan chay. `not_evaluated` = dung hai cai do la DUNG o buoc
    tien sang -- nhieu hon la mot tieu chi bi bo quen im lang.
    """
    for r in prescreen["rows"]:
        assert set(r["not_evaluated"]) == POST_RUN_ONLY, (
            "%s@%.3f tau=%g a=%g: not_evaluated = %s"
            % (r["mode"], r["rho_bar"], r["tau"], r["a"], r["not_evaluated"]))


def test_prescreen_is_pass_one_and_says_so(prescreen):
    """`assert not_evaluated == []` la cua LAN 2, khong phai lan nay.

    Neu khong ghi ro, nguoi doc se ap gate 4-2 cho lan 1, thay no khong thoa,
    roi noi assert -- tuc mo lai dung cai lo vua bit.
    """
    assert prescreen["pass_number"] == 1
    assert "LAN 2" in prescreen["pass_meaning"]


# ------------------------------------------------------- GATE_VERSION (20R2-L8)

def test_prescreen_uses_gate_version_2(prescreen):
    assert prescreen["gate_version"] == 2
    for r in prescreen["rows"]:
        assert r["gate_version"] == 2


def test_inherited_grid_is_v1_and_must_not_be_reused():
    """20R2-L8: luoi thua ke sinh boi gate v1 -- vo hieu vi BA ly do doc lap.

    1. sai PHIEN BAN     v1, khong phai v2
    2. 3/9 tieu chi khong chay
    3. tieu chi da chay la TIEU CHI MA (`sigma > 0`, khong bao gio fail duoc)
    """
    p = ROOT / "results/PENDING/phase-T2/realizability_grid.json"
    if not p.is_file():
        pytest.skip("khong co luoi thua ke")
    d = json.loads(p.read_text(encoding="utf-8"))
    row = d["rows"][0]
    assert row["derived"].get("gate_version") is None, (
        "luoi thua ke gio da co gate_version -- cap nhat 20R2-L8")
    assert "sigma_feasible" in row["checks"], "ten tieu chi v1 da doi"
    assert "sigma_within_headroom" not in row["checks"]
    assert "sigma_max_regime" not in row["derived"]
    assert d["n_realizable"] == 96 and d["n_cells"] == 96


def test_current_gate_actually_calls_the_headroom_function():
    """Tieu chi ma cua v1: `cost_v2` duoc import ma KHONG BAO GIO goi.

    v1: `grep -c "C\\."` = 0 (do tren commit 54a05ddc).
    v2 phai THUC SU goi no, neu khong ten moi cung chi la ten moi.
    """
    src = (ROOT / "cert/realizability_gate.py").read_text(encoding="utf-8")
    assert "from twin import cost_v2 as C" in src
    assert src.count("C.sigma_max_regime") >= 1, (
        "cost_v2 lai thanh dead import -- tieu chi headroom tro lai la tieu chi ma")


# ------------------------------------------------------- em/A (E2)

def test_em_over_a_table_has_twenty_rows_not_ten():
    """Phan quyet phu thuoc sigma, KHONG chi mode [RT2-4 thieu mot truc].

    h2@0.700: a=0.9 -> span/pure 0.9375 DOC DUOC
              a=0.5 -> span/pure 1.5691 BI CHI PHOI
    Lap bang theo `mode` roi ket luan cho ca o la lap lai loi T2.
    """
    d = _load(EM_OVER_A)
    assert d["summary"]["n_rows"] == 20
    keys = {(r["cell"], r["a"]) for r in d["rows"]}
    assert len(keys) == 20, "co dong trung (cell, a)"


def test_em_over_a_marks_but_does_not_exclude():
    """Loai o co em/A cao = chon du lieu theo tinh chat lien quan ket qua
    => selection bias. Bang phai GIU du 20 dong va chi DANH DAU."""
    d = _load(EM_OVER_A)
    flags = {r["flag"] for r in d["rows"]}
    assert "BI_CHI_PHOI" in flags, "phai co o bi danh dau, neu khong bang vo dung"
    assert d["summary"]["n_rows"] == d["summary"]["n_expected"], (
        "co dong bi LOAI khoi bang -- chi duoc DANH DAU")


def test_cbr_rows_are_degenerate_or_unmeasured():
    """DU KIEN QUYET DINH POPULATION cua 20R2.2.

    cbr@0.700: A_bar ~ 2e-4 .. 4e-4, nho hon o khong-cbr nho nhat ~3200 lan;
    span/pure ~ 0.005 (duong cong theo tuoi gan nhu PHANG).
    cbr@0.850: T2 KHONG do.
    => ca 4 dong cbr deu KHONG phai bang chung dung duoc cho mot doi chung
       duong theo nghia "biet truoc ket qua phai ra sao".
    """
    d = _load(EM_OVER_A)
    cbr = [r for r in d["rows"] if r["mode"] == "cbr"]
    assert len(cbr) == 4
    for r in cbr:
        assert r["flag"] in ("SUY_BIEN", "CHUA_BIET"), (
            "%s a=%s co flag %s -- neu cbr het suy bien thi phai xet lai "
            "quyet dinh POPULATION cua 20R2.2" % (r["cell"], r["a"], r["flag"]))


# ------------------------------------------------------- ngan sach (E3/E4)

def test_cpu_pilot_meets_gate_4_3():
    """Uoc tinh ke thua phai khop phep do trong +-30%."""
    d = _load(CPU_PILOT)
    g = d["gate_4_3"]
    assert g["verdict"] == "PASS", (
        "s/o do duoc %.4f vs ke thua %.4f = %+.1f%%, ngoai +-%d%%"
        % (g["measured_seconds_per_cell"], g["inherited_seconds_per_cell"],
           g["relative_drift"] * 100, g["tolerance"] * 100))


def test_fractional_design_is_not_needed_and_the_reason_is_recorded():
    """E4: khong can thi phai GHI LY DO, khong de trong."""
    d = _load(CPU_PILOT)
    e4 = d["e4_fractional_design"]
    assert e4["needed"] is False
    assert e4["measured_minutes_two_branches"] < e4["threshold_hours"] * 60
    assert e4["why"]


def test_pilot_measured_both_z_grids():
    """Chi phi cua LUOI phai tach khoi chi phi cua MAY.

    Neu chi do mot luoi thi khong biet +21% den tu 13 diem hay tu may khac.
    """
    d = _load(CPU_PILOT)
    assert d["z_grids"]["n_z_20r2"] == 13
    for r in d["per_tau"]:
        assert r["seconds_z20r2"] > 0 and r["seconds_zlegacy"] > 0
        assert 1.0 < r["z20r2_over_legacy"] < 1.5, (
            "ti so 13/9 diem = %.3f, ngoai khoang hop ly" % r["z20r2_over_legacy"])


# ------------------------------------------------------- N3/N4 (E5)

def test_n3_n4_baseline_matches_the_pinned_values():
    """Moc so sanh phai on dinh: mot moc troi lam moi so sanh sau vo nghia."""
    d = _load(N3N4)
    assert not d["baseline_drift"], d["baseline_drift"]
    assert d["N3"]["n_pass"] == 14 and d["N3"]["n_fail"] == 4
    assert d["N4"]["n_pass"] == 7 and d["N4"]["n_fail"] == 11


def test_n3_failure_spans_more_cells_than_the_handoff_says():
    """Handoff viet 'chu yeu o poisson@0.850'. Do lai: 3 o khac nhau."""
    d = _load(N3N4)
    assert len(d["N3"]["fail_by_cell"]) == 3
    assert "poisson@0.850" in d["N3"]["fail_by_cell"]


def test_n3_n4_for_20r2_is_declared_not_measured():
    """KHONG duoc chep ket qua T2 sang 20R2 [E5].

    Mot gia dinh vo 11/18 o dieu kien A co the vo 3/18 hoac 17/18 o dieu kien B.
    """
    d = _load(N3N4)
    assert d["status_20r2"]["measured"] is False
    assert d["label"] == "T2_baseline"


# ------------------------------------------- LO HONG DA BIET: luoi z chua sua

def test_the_20r2_z_grid_is_wired_into_the_harness():
    """20R2-D3 DA GO -- va test nay giu cho no khong quay lai.

    Truoc 2026-09-10: decision_error_v2.py chi co Z_GRID legacy (9 diem), con
    Z_GRID_20R2_MEASURED chi ton tai trong van ban prereg. Chay chien dich se
    LANG LE ra ket qua truc legacy va KHONG bao loi -- ca hai luoi deu chay
    duoc, chi tra loi hai cau hoi khac nhau.

    Gio: hai luoi cung ton tai, va nguoi goi PHAI CHON (--z-grid required).
    """
    import measurements.decision_error_v2 as DE
    assert set(DE.Z_GRIDS) == {"legacy", "20r2_measured"}
    assert len(DE.Z_ALL) == 9, "luoi legacy phai giu nguyen 9 diem"
    assert len(DE.Z_ALL_20R2) == 13, "luoi 20R2 phai la 13 diem"
    assert DE.Z_GRID_20R2_MEASURED[0] == 0.115, "san that cua truc measured"
    assert DE.Z_GRID_20R2_MEASURED[-1] == 0.615, "max cua truc mo hinh measured"
    assert 0.0 in DE.Z_ALL_20R2, "thieu diem doi chung z = 0"


def test_the_legacy_grid_values_are_unchanged():
    """166 artifact cua T2 dieu kien theo luoi legacy, va 20R2.3 dung chung lam
    neo hoi quy. Doi MOT gia tri o day la pha neo -- nen ghim tung so."""
    import measurements.decision_error_v2 as DE
    assert DE.Z_GRID == (0.0, 0.05, 0.10, 0.20, 0.30, 0.55)
    assert DE.Z_EXTRAP == (1.0, 2.0, 4.0)


def test_both_grids_share_the_same_max_so_the_scoring_window_matches():
    """max(luoi) quyet dinh scoring_window_start.

    Neu hai luoi khac max thi chung cham diem tren HAI DAI HANG KHAC NHAU, va
    ket qua khong so duoc voi nhau -- dung loi ma docstring cua
    scoring_window_start canh bao ("do lech DOI DAU theo tau").
    """
    import measurements.decision_error_v2 as DE
    assert max(DE.Z_ALL) == max(DE.Z_ALL_20R2) == 4.0
    assert DE.scoring_window_start(3.0, DE.DT) == \
        DE.scoring_window_start(3.0, DE.DT)
    a = max(int(round(z / DE.DT)) for z in DE.Z_ALL)
    b = max(int(round(z / DE.DT)) for z in DE.Z_ALL_20R2)
    assert a == b, "hai luoi cho hai cua so cham diem khac nhau"


def test_the_cli_refuses_to_guess_the_z_grid():
    """Mot mac dinh im lang o luoi z nguy hiem y het o truc AoI: CA HAI luoi
    deu chay duoc va KHONG bao loi. Cung thuoc da dung cho `axis` o gate 0-5.
    """
    import subprocess
    import sys
    r = subprocess.run(
        [sys.executable, "-m", "measurements.decision_error_v2", "--run-fixed",
         "--tau", "3", "--z-mode", "fixed", "--seeds", "101",
         "--out", "/dev/null"],
        cwd=str(ROOT), capture_output=True, text=True)
    assert r.returncode != 0, "CLI van chay duoc khi THIEU --z-grid"
    assert "--z-grid" in r.stderr, r.stderr[-400:]


def test_t2_tools_declare_the_legacy_grid_explicitly():
    """T2 chay luoi legacy. Truoc D3 do la mac dinh IM LANG; gio phai khai ra.

    Gia tri khong doi -- chi loi khai doi, va do la diem: lua chon luoi z gio
    nam trong chinh dong lenh, doc duoc ma khong phai tra ma nguon.
    """
    import importlib
    run = {"tau": 3, "branch": "fixed", "seed": 101, "run_index": 0, "a": 0.9}
    for mod_name in ("tools.t2_6_plan", "tools.t2_6_run"):
        cmd = [str(x) for x in importlib.import_module(mod_name).command_for(run, "/tmp")]
        assert "--z-grid" in cmd, mod_name + " khong khai --z-grid"
        assert cmd[cmd.index("--z-grid") + 1] == "legacy", (
            mod_name + " khai luoi khac legacy -- T2 phai o legacy")


def test_the_pilot_records_both_grids_and_the_d3_resolution():
    """Lo hong -- va viec no da duoc go -- phai nam trong ARTIFACT.

    Nguoi doc ngan sach phai thay ngay no do tren luoi nao, va rang truoc
    2026-09-10 harness khong co luoi 20R2 nen mot lan chay se lang le ra ket
    qua truc legacy.
    """
    d = _load(CPU_PILOT)
    zg = d["z_grids"]
    assert zg["n_z_legacy"] == 9 and zg["n_z_20r2"] == 13
    assert "d3_status" in zg, "artifact khong ghi trang thai 20R2-D3"
    assert "DA GO" in zg["d3_status"]
    assert max(zg["z_20r2_prereg"]) == max(zg["z_legacy_in_code"]) == 4.0


def test_the_pilot_reads_the_grid_from_code_not_a_local_copy():
    """Mot hang so song o hai noi la mot hang so se lech.

    Truoc D3, tool giu BAN CHEP cua luoi 20R2 vi ma chua co ten do. Gio ma da
    co, ban chep phai bien mat -- neu khong ta co hai nguon su that.
    """
    import importlib
    import measurements.decision_error_v2 as DE
    m = importlib.import_module("tools.20r2_4_cpu_pilot")
    assert tuple(m._z_20r2()) == tuple(float(z) for z in DE.Z_ALL_20R2)
    src = (ROOT / "tools/20r2_4_cpu_pilot.py").read_text(encoding="utf-8")
    assert "0.115, 0.170, 0.241" not in src, (
        "tool van giu ban chep cua luoi 20R2 -- doc tu DE.Z_ALL_20R2")


def test_prereg_budget_number_comes_from_the_artifact(): 
    """Con so ngan sach trong prereg phai TRICH tu artifact, khong go tay.

    Do duoc 2026-09-10: artifact ghi 35.08 phut (ngan sach NEN, chua nang n)
    trong khi prereg §14.7 ghi mot con so GO TAY cho ban da nang. Hai nguon,
    hai so, khong ai canh.

    Hau qua CU THE, khong phai ly thuyet: gate 4-3 doi chieu ARTIFACT (gate
    0-1: sinh boi cong cu), nen no doc con so NEN roi so voi thoi gian chay
    THAT (~74.5 phut), thay lech ~110% va TRUOT OAN. Mot FAIL do so sach,
    khong do khoa hoc.  [NT 50]
    """
    d = _load(CPU_PILOT)
    b = d["budget"]
    scaled = b["minutes_two_branches_scaled"]
    assert scaled, "artifact khong ghi ngan sach DA NANG"
    prereg = (ROOT / "docs/phase-20R2/00-preregistration.md").read_text(
        encoding="utf-8")
    assert "%.2f" % scaled in prereg, (
        "prereg khong chua %.2f phut (ngan sach da nang tu artifact). "
        "Sinh lai muc 14.7 tu cpu_pilot.json." % scaled)


def test_the_gate_number_is_the_scaled_one_not_the_base():
    """Chien dich chay VOI he so nang n. So nen chi de truy nguon."""
    d = _load(CPU_PILOT)
    b = d["budget"]
    assert b["which_number_the_campaign_will_take"] == "minutes_two_branches_scaled"
    assert b["minutes_two_branches_scaled"] > b["minutes_two_branches"], (
        "ban da nang phai TON HON ban nen")


def test_scaling_is_measured_because_cost_is_not_linear_in_n():
    """Ngoai suy tuyen tinh UOC THAP, va uoc thap lam gate 4-3 truot khi chay that.

    Do duoc: he so 2 ton 2.06x; he so 4 ton 4.35x va 4.67x. Deu TREN tuyen tinh.
    """
    d = _load(CPU_PILOT)
    b = d["budget"]
    assert b["scaling_is_measured_not_extrapolated"] is True
    lifted = [r for r in b["scaled_per_tau_measured"] if r["n_multiplier"] > 1]
    assert lifted, "khong co tau nao duoc nang -- san chu ky da bien mat?"
    for r in lifted:
        assert r["ratio_vs_x1"] >= r["n_multiplier"] * 0.95, (
            "tau=%g: ti so %.2f THAP hon he so %d -- kiem lai phep do"
            % (r["tau"], r["ratio_vs_x1"], r["n_multiplier"]))
        assert r["how"].startswith("measured_x"), "khong phai phep do that"


def test_prereg_quotes_the_pilot_artifact_not_a_stale_number():
    """Van ban chi TRICH artifact; artifact la nguon dung.

    Chi phi do lai lech ~1% moi lan chay. Neu prereg ghim mot chu so cu thi
    no se lech im lang khoi artifact -- va nguoi doc khong biet tin cai nao.
    Test nay doi hai ben khop trong 2%, du rong cho nhieu do va du chat de
    bat mot con so bi bo quen.
    """
    d = _load(CPU_PILOT)
    two = d["budget"]["minutes_two_branches"]
    prereg = (ROOT / "docs/phase-20R2/00-preregistration.md").read_text(
        encoding="utf-8")
    import re
    quoted = [float(x.replace(",", ".")) for x in
              re.findall(r"29,4 phút → ([\d.,]+) phút", prereg)]
    assert quoted, "prereg khong con trich con so hai nhanh"
    for q in quoted:
        assert abs(q - two) / two < 0.02, (
            "prereg ghi %.2f phut, artifact do %.2f phut -- lech %.1f%%. "
            "Sinh lai prereg tu artifact." % (q, two, abs(q - two) / two * 100))

#!/usr/bin/env python3
"""Doi chung cho SLA ngoai sinh (Lesson 23.21, amendment 23-52).

Moi test o day PHAI thay DO it nhat mot lan truoc khi duoc tin -- danh sach
doi chung duong da chay o cuoi file.
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from measurements import sla_exogenous as X
from twin import cost_v2 as C

N_FAST = 20_000          # du de bat sai co hoc, khong du de la mot ket qua


@pytest.fixture(scope="module")
def cv2():
    return C.CostV2(strict_reliable=True)


# -- tinh chat dai so, khong can chay mo phong --------------------------------
def test_equal_budget_rule():
    assert X.w_loss_equal_budget(50.0, 0.01) == 5000.0
    assert X.w_loss_equal_budget(150.0, 0.01) == 15000.0
    assert X.w_loss_equal_budget(20.0, 0.001) == 20000.0
    with pytest.raises(ValueError):
        X.w_loss_equal_budget(50.0, 0.0)


def test_spec_table_is_locked():
    """Doi mot con so trong SLA_SPECS phai lam test DO -- no da duoc KY."""
    assert X.SLA_SPECS["S-B"]["t_delay_ms"] == 50.0
    assert X.SLA_SPECS["S-B"]["t_loss"] == 0.010
    assert X.PIVOTAL_MIN == 0.10
    assert X.VIOL_OPT_BAND == (0.01, 0.50)
    assert X.W_LOSS_SWEEP == (1250.0, 5000.0, 20000.0)
    # Sweep phai bao dai noi sinh cu cua TAM cell GATE = [1656.4, 4722.7].
    #
    # DINH CHINH (xem `L48`): amendment 23-52 muc 3 ghi can duoi 1250 "bao tron
    # dai noi sinh cu [1245.6, 4722.7]". Sai: 1250 > 1245.6. Con so 1245.6 la
    # cua HAI cell `cbr` role=`pc1`, khong phai cua tam cell `gate` ma ket luan
    # dua tren. Sweep VAN du cho pham vi ket luan; chi cau chu la thieu chinh
    # xac. Amendment DA KY nen khong sua -- ghi dinh chinh o `LIMITS.md` va o day.
    assert X.W_LOSS_SWEEP[0] <= 1656.4      # min w_loss cua 8 cell gate
    assert X.W_LOSS_SWEEP[-1] >= 4722.7     # max w_loss cua 8 cell gate


def test_w_loss_of_primary_spec_matches_constants_ledger_k06():
    """`w_loss` = 5000 duoc khoa o CONSTANTS.md K06. Doi mot noi -> test do."""
    spec = X.SLA_SPECS[X.PRIMARY_SPEC]
    assert X.w_loss_equal_budget(spec["t_delay_ms"], spec["t_loss"]) == 5000.0


def test_shares_partition_exactly():
    d = np.array([[10.0, 60.0], [10.0, 20.0], [80.0, 90.0]])
    l = np.zeros((3, 2))
    sh = X.regime_shares(d, l, t_delay_ms=50.0, t_loss=0.01)
    assert sh["S_pivotal"] == pytest.approx(1 / 3)      # hang 1: mot vi pham
    assert sh["S_trivial"] == pytest.approx(1 / 3)      # hang 2: khong ai vi pham
    assert sh["S_collapsed"] == pytest.approx(1 / 3)    # hang 3: ca hai vi pham
    assert (sh["S_trivial"] + sh["S_pivotal"]
            + sh["S_collapsed"]) == pytest.approx(1.0)


def test_regime_shares_signature_has_no_w_loss():
    """G23-160 o muc KIEU: them `w_loss`/`opt` vao day la vo hieu tinh bat bien.

    Cach manh nhat de dam bao mot bat bien khong phai la KIEM no, ma la lam
    cho no khong the bi vi pham. Cung ky thuat `G23-115`.
    """
    import inspect
    params = set(inspect.signature(X.regime_shares).parameters)
    assert "w_loss" not in params
    assert "opt" not in params
    assert "cost" not in params


def test_classify_boundaries():
    assert X.classify({"S_pivotal": 0.10, "S_trivial": 0.9,
                       "S_collapsed": 0.0}) == "LIVE"
    assert X.classify({"S_pivotal": 0.09, "S_trivial": 0.9,
                       "S_collapsed": 0.01}) == "TRIVIAL"
    assert X.classify({"S_pivotal": 0.09, "S_trivial": 0.01,
                       "S_collapsed": 0.9}) == "COLLAPSED"


def test_no_endogenous_solver_is_reachable():
    """Kiem KIEN TRUC, khong kiem ket qua.

    Sau nay ai muon "muon tam solve_percentile cho tien" se thay test do va
    phai giai thich. Day la cach khoa mot quyet dinh THIET KE.
    """
    import inspect
    src = inspect.getsource(X)
    body = src.split('"""', 2)[-1]        # bo docstring module
    for banned in ("solve_percentile", "viol_rate_at_p", "TARGET_VIOL"):
        assert banned not in body, (
            "sla_exogenous goi lai co che noi sinh: %s" % banned)


# -- doi chung chay mo phong --------------------------------------------------
@pytest.mark.parametrize("mode,rb", [("poisson", 0.925), ("h2", 0.700)])
def test_NC3_pivotal_is_invariant_to_w_loss(cv2, mode, rb):
    """G23-160. Neu test nay do, lap luan 'phan hoach doc lap ham muc tieu' SAI."""
    vals = [X.evaluate_cell(cv2, mode, rb, t_delay_ms=50.0, t_loss=0.01,
                            w_loss=w, n=N_FAST)["S_pivotal"]
            for w in X.W_LOSS_SWEEP]
    assert max(abs(v - vals[0]) for v in vals) == 0.0


@pytest.mark.parametrize("mode,rb", [("poisson", 0.925), ("h2", 0.700)])
def test_PC1_impossible_sla_collapses(cv2, mode, rb):
    c = X.evaluate_cell(cv2, mode, rb, t_delay_ms=0.0, t_loss=0.0,
                        w_loss=5000.0, n=N_FAST)
    assert c["S_collapsed"] == 1.0
    assert c["regime"] == "COLLAPSED"


@pytest.mark.parametrize("mode,rb", [("poisson", 0.925), ("h2", 0.700)])
def test_PC2_trivial_sla_is_trivial(cv2, mode, rb):
    c = X.evaluate_cell(cv2, mode, rb, t_delay_ms=float("inf"), t_loss=1.0,
                        w_loss=5000.0, n=N_FAST)
    assert c["S_trivial"] == 1.0
    assert c["regime"] == "TRIVIAL"


def test_NC1_reproduces_legacy_artifact(cv2):
    """G23-159. Nap LAI nguong + `w_loss` noi sinh cu -> phai ra dung so cu.

    Chung minh duong ong MOI khong doi bat cu thu gi NGOAI SLA. Neu no do,
    moi so sanh CU vs MOI cua Lesson 23.21 deu vo nghia.

    `opt_viol_rate` va `opt_path_share` khop CHINH XAC (chung la trung binh
    cua bool/dem). `cost_margin_mean_ms` khop den ~3e-14: no la trung binh
    cua 200k so thuc, nen thu tu cong anh huong bit cuoi. Dung `abs=1e-9`,
    van chat hon sai so do 5 bac.
    """
    with open(X.LEGACY_SLA, "r", encoding="utf-8") as fh:
        legacy = [c for c in json.load(fh)["cells"] if c.get("feasible")]
    assert len(legacy) == 10, "artifact cu phai co dung 10 cell kha thi"
    for old in legacy:
        new = X.evaluate_cell(
            cv2, str(old["mode"]), float(old["rho_bar"]),
            t_delay_ms=old["t_delay_ms"], t_loss=old["t_loss"],
            w_loss=old["w_loss"], n=int(old["n"]), seed=int(old["seed"]))
        assert new["opt_viol_rate"] == pytest.approx(
            old["opt_viol_rate"], abs=1e-12)
        assert new["cost_margin_mean_ms"] == pytest.approx(
            old["cost_margin_mean_ms"], abs=1e-9)
        for p, v in old["opt_path_share"].items():
            assert new["opt_path_share"][p] == pytest.approx(v, abs=1e-12)


def test_G23_161_role_semantics_unchanged(cv2):
    """`role` la truong DUONG ONG. Phan loai moi phai o `regime`.

    Neu ai do gan `role = regime`, `feasible_cells()` se loc mat cell va
    `eight_cell_sweep` nem ValueError o mot noi RAT XA cho sua.
    """
    c = X.evaluate_cell(cv2, "h2", 0.960, t_delay_ms=50.0, t_loss=0.01,
                        w_loss=5000.0, n=N_FAST)
    assert c["role"] == "gate"                      # y het artifact cu
    assert c["regime"] in {"LIVE", "TRIVIAL", "COLLAPSED"}
    assert c["role"] != c["regime"]


def test_infeasible_cells_keep_legacy_role(cv2):
    """Cell bi loai boi Q8 phai giu NGUYEN `role` cu de ha nguon khong doi."""
    c = X.evaluate_cell(cv2, "cbr", 0.960, t_delay_ms=50.0, t_loss=0.01,
                        w_loss=5000.0, n=N_FAST)
    assert c["feasible"] is False
    assert c["role"] == "pc1_excluded_by_q8"
    assert c["regime"] == "INFEASIBLE"


def test_loss_exchange_keeps_the_w_loss_identity(cv2):
    """`w_loss = t_delay_ms / loss_exchange` GIU nguyen (amendment 23-52 muc 2b).

    Truong `loss_exchange` khong bi nap nghia moi: no van la "so chia sinh ra
    `w_loss` tu `t_delay`". Voi equal-budget no tinh co bang `T_loss`.
    """
    for spec_id, spec in X.SLA_SPECS.items():
        w = X.w_loss_equal_budget(spec["t_delay_ms"], spec["t_loss"])
        c = X.evaluate_cell(cv2, "poisson", 0.850,
                            t_delay_ms=spec["t_delay_ms"],
                            t_loss=spec["t_loss"], w_loss=w, n=N_FAST)
        assert c["w_loss"] == pytest.approx(
            c["t_delay_ms"] / c["loss_exchange"]), spec_id


def test_sla_calib_v2_is_untouched():
    """Amendment 23-52 muc 12: the gioi NOI SINH khong bi sua.

    Neu `LOSS_EXCHANGE` hay `TARGET_VIOL` bi doi, doi chung am G23-159 mat
    y nghia va test ghim cua Phase 20R cung do.
    """
    from measurements import sla_calib_v2 as S14
    assert S14.LOSS_EXCHANGE == 0.01
    assert S14.TARGET_VIOL == 0.15


# DOI CHUNG DUONG da chay (moi cai phai DO it nhat mot lan):
#   DC15  PIVOTAL_MIN 0.10 -> 0.15             -> test_spec_table_is_locked DO
#   DC16  them tham so w_loss vao regime_shares -> test_..._signature DO
#   DC17  gan role = regime                     -> test_G23_161 DO
#   DC18  doi mot hang so trong ar1_matrix      -> test_NC1 DO
#   DC19  import solve_percentile               -> test_no_endogenous DO
#   DC20  doi LOSS_EXCHANGE trong sla_calib_v2  -> test_sla_calib_v2_is_untouched DO


# -- amendment 23-53: CI, AMBIGUOUS, quet T_loss, Dot 4 ----------------------
def test_ambiguous_only_when_ci_straddles_threshold():
    """`AMBIGUOUS` = CI CHUA nguong. `PIVOTAL_MIN` khong duoc doi."""
    sh = {"S_pivotal": 0.1112, "S_trivial": 0.0, "S_collapsed": 0.8888}
    assert X.classify(sh, (0.0956, 0.1269)) == "AMBIGUOUS"   # chua 0.10
    assert X.classify(sh, (0.1050, 0.1269)) == "LIVE"        # khong chua
    assert X.classify(sh, None) == "LIVE"                    # hanh vi cu
    assert X.PIVOTAL_MIN == 0.10


def test_block_bootstrap_is_wider_than_iid(cv2):
    """G23-168. Neu block va iid cho CI BANG NHAU thi lap luan tu tuong quan SAI."""
    c = X.evaluate_cell(cv2, "h2", 0.700, t_delay_ms=50.0, t_loss=0.01,
                        w_loss=5000.0, n=X.S14.DEFAULT_N, with_ci=True)
    ci = c["S_pivotal_ci"]
    assert ci["ci_width_block"] > 3.0 * ci["ci_width_iid"], (
        "CI block phai RONG hon iid dang ke; do duoc ratio = %r"
        % ci["width_ratio_block_over_iid"])


def test_with_ci_defaults_off_so_23_21_artifacts_reproduce():
    """Mac dinh TAT: artifact 23.21 duoc sinh truoc amendment 53 phai tai tao duoc."""
    import inspect
    assert inspect.signature(X.evaluate_cell).parameters["with_ci"].default is False


def test_wave4_does_not_claim_to_discharge_debt_gates():
    """Chay 4 cell moi KHONG tra G23-141/G23-142 -- chung can calib parquet."""
    import inspect
    src = inspect.getsource(X.run_wave4)
    assert "_does_not_discharge" in src
    assert X.WAVE4_CELLS == (("poisson", 0.875), ("poisson", 0.900),
                             ("h2", 0.650), ("h2", 0.675))


def test_t_loss_grid_brackets_all_three_signed_specs():
    """Quet phai BAO ca ba spec da ky, neu khong no khong thay duoc chung."""
    for spec in X.SLA_SPECS.values():
        assert min(X.T_LOSS_GRID) <= spec["t_loss"] <= max(X.T_LOSS_GRID)
    assert X.BLOCK_STEPS == 1000        # 5 s >> tau = 1 s


# -- amendment 23-54: luoi min, luoi rho, doi chung sigma --------------------
def test_fine_grid_brackets_the_endogenous_range():
    """Luoi min PHAI bao dai `t_loss` noi sinh, neu khong no khong thay dinh."""
    assert X.T_LOSS_FINE[0] <= 0.00042           # t_loss_endo nho nhat
    assert len(X.T_LOSS_FINE) == 32
    ratio = X.T_LOSS_FINE[1] / X.T_LOSS_FINE[0]
    assert abs(ratio - 1.25) < 1e-6


def test_sigma_override_reports_infeasible_instead_of_clipping(cv2):
    """`sigma` vuot tran phai tra `feasible = False`, KHONG cat lang le.

    Neu no cat xuong `sigma_max` thi doi chung `G23-172` se so hai cell o
    hai `sigma` KHAC nhau ma khong ai biet -- dung cai confound no sinh ra
    de chan.
    """
    c = X.evaluate_cell(cv2, "h2", 0.960, t_delay_ms=50.0, t_loss=0.01,
                        w_loss=5000.0, n=N_FAST, sigma_override=X.SIGMA_FIXED)
    assert c["feasible"] is False          # sigma_max(h2, 0.960) = 0.0107 < 0.020
    ok = X.evaluate_cell(cv2, "h2", 0.700, t_delay_ms=50.0, t_loss=0.01,
                         w_loss=5000.0, n=N_FAST, sigma_override=X.SIGMA_FIXED)
    assert ok["feasible"] is True
    assert ok["sigma_rho"] == pytest.approx(X.SIGMA_FIXED)


def test_sigma_fixed_grid_stays_inside_feasible_range():
    """Moi `rho` cua luoi doi chung phai chiu duoc `sigma` = 0.020."""
    for rb in X.RHO_GRID_SIGMA_FIXED:
        for mode in ("poisson", "h2"):
            assert C.sigma_max_regime(mode, rb) >= X.SIGMA_FIXED, (
                "%s@%.3f khong chiu duoc sigma = %g" % (mode, rb, X.SIGMA_FIXED))


def test_pivotal_identity_holds(cv2):
    """`S_pivotal` = `pct_t_loss/100 - S_trivial` khi truc tre TRO.

    Dong nhat thuc cua amendment 23-54 muc 1b. Neu no vo hieu, moi lap luan
    "mot dinh duy nhat" va "bat bien w_loss" mat co so giai tich.
    """
    c = X.evaluate_cell(cv2, "poisson", 0.850, t_delay_ms=50.0, t_loss=0.01,
                        w_loss=5000.0, n=X.S14.DEFAULT_N)
    assert c["percentile_of_t_delay"] == 100.0          # truc tre TRO
    pred = c["percentile_of_t_loss"] / 100.0 - c["S_trivial"]
    assert abs(pred - c["S_pivotal"]) < 5e-3


# -- amendment 23-55: V, luoi 2D, ten truong ---------------------------------
def test_decision_value_is_zero_at_all_three_degenerate_ends():
    """`V` = 0 o CA BA dau suy bien: tam thuong, sup, va oracle-cung-thua."""
    triv = {"feasible": True, "mean_paths_violating": 0.0, "opt_viol_rate": 0.0}
    coll = {"feasible": True, "mean_paths_violating": 4.0, "opt_viol_rate": 1.0}
    lose = {"feasible": True, "mean_paths_violating": 2.0, "opt_viol_rate": 0.5}
    for c in (triv, coll, lose):
        assert X.decision_value(c) == pytest.approx(0.0)
    good = {"feasible": True, "mean_paths_violating": 1.0, "opt_viol_rate": 0.0}
    assert X.decision_value(good) == pytest.approx(0.25)


def test_low_opt_viol_alone_does_not_mean_easy(cv2):
    """`L61`: `opt_viol` thap = ORACLE THANH CONG, khong phai "bai toan de".

    `h2@0.600` co oracle 0% vi pham NHUNG `S_pivotal` ~ 0.94 va `V` ~ 0.24:
    SLA dat duoc, va CHI KHI chon dung duong. Neu ai do quay lai dung
    `in_band` lam tieu chi duy nhat, test nay nhac vi sao khong duoc.
    """
    c = X.evaluate_cell(cv2, "h2", 0.600, t_delay_ms=50.0, t_loss=0.01,
                        w_loss=5000.0, n=X.S14.DEFAULT_N)
    assert c["opt_viol_rate"] == pytest.approx(0.0, abs=1e-9)
    assert c["in_band"] is False                 # tieu chi CU loai no
    assert c["S_pivotal"] > 0.9                  # nhung chon duong QUYET DINH
    assert c["decision_value_V"] > 0.2           # va co gia tri that


def test_plane_grid_marks_infeasible_instead_of_clipping():
    """O `sigma > sigma_max` phai duoc danh dau, KHONG bi cat xuong tran.

    Cat lang le se tao ra mot bien GIA tren mat phang (rho, sigma).
    """
    import json
    import os
    p = os.path.join("results", "PENDING", "phase-23", "sigma_rho_plane.json")
    if not os.path.exists(p):
        pytest.skip("chua chay --plane")
    d = json.load(open(p, encoding="utf-8"))
    for mode, plane in d["planes"].items():
        for rk, row in plane.items():
            smax = row["sigma_max"]
            for sk, cell in row["by_sigma"].items():
                sg = float(sk.split("=")[1])
                assert cell["feasible"] == (sg <= smax), (
                    "%s %s %s: feasible=%r nhung sigma_max=%.4f"
                    % (mode, rk, sk, cell["feasible"], smax))


def test_spearman_ridge_alignment_matches_ledger():
    """`G23-181`: `K07` phai tai tinh duoc tu artifact, khong phai so troi."""
    import json
    import os
    import re
    p = os.path.join("results", "PENDING", "phase-23", "t_loss_fine.json")
    if not os.path.exists(p):
        pytest.skip("chua chay --t-loss-fine")
    from scipy.stats import spearmanr
    d = json.load(open(p, encoding="utf-8"))
    lf_path = os.path.join("results", "PENDING", "phase-23",
                           "t_loss_local_fine.json")
    lf = (json.load(open(lf_path, encoding="utf-8"))["cells"]
          if os.path.exists(lf_path) else {})
    # Chi cell co `T*` XAC DINH. Cell co CAO NGUYEN cham mut bi LOAI (`L63`):
    # dua `T*` cua chung vao se lam `K07` tinh tren mot gia tri BIA.
    pairs = []
    for k, v in d["cells"].items():
        ts = v["T_star"] or lf.get(k, {}).get("T_star")
        if ts:
            pairs.append((v["t_loss_endogenous"], ts))
    assert len(pairs) >= 6, "qua it cell co T* xac dinh: %d" % len(pairs)
    rho = spearmanr([a for a, _ in pairs], [b for _, b in pairs]).statistic
    txt = open(os.path.join("docs", "phase-23", "CONSTANTS.md"),
               encoding="utf-8").read()
    row = [l for l in txt.splitlines() if l.startswith("| K07 |")]
    assert row, "CONSTANTS.md thieu dong K07"
    val = float(row[0].split("|")[3].strip())
    assert abs(val - rho) < 5e-4, (
        "K07 ghi %r nhung tai tinh tu artifact cho %.4f" % (val, rho))


# -- amendment 23-56: cao nguyen va bien kha thi ------------------------------
def test_peak_at_edge_checks_value_not_argmax_index():
    """`G23-183`. Phep kiem cu dung `argmax` nen MU voi CAO NGUYEN.

    `argmax` tra chi so DAU TIEN trong nhom bang nhau. Neu cuc dai dat o
    nhieu diem va cao nguyen CHAM mut, `argmax` van tra mot chi so o GIUA
    -> co bao "khong o mut" trong khi gia tri cuc dai CO o mut. Do la loi
    that da xay ra voi `h2@0.960` (9/16 diem cung dat 1.0000). Xem `L63`.
    """
    import numpy as np
    curve = [0.0, 0.5, 1.0, 1.0, 1.0]          # cao nguyen cham mut PHAI
    grid = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert int(np.argmax(curve)) == 2          # phep kiem CU se bao "khong o mut"
    pk = X.peak_diagnostics(curve, grid)
    assert pk["peak_at_grid_edge"] is True     # phep kiem MOI bat duoc
    assert pk["plateau"] is True
    assert pk["n_at_max"] == 3
    assert pk["T_star"] is None                # cao nguyen -> khong xac dinh
    assert pk["T_star_range"] == [3.0, 5.0]
    assert pk["bracketed"] is False


def test_peak_diagnostics_accepts_a_genuine_interior_peak():
    """Doi chung am: dinh THAT o trong phai duoc nhan la kep duoc."""
    pk = X.peak_diagnostics([0.1, 0.9, 0.3], [1.0, 2.0, 3.0])
    assert pk["peak_at_grid_edge"] is False
    assert pk["plateau"] is False
    assert pk["T_star"] == 2.0
    assert pk["bracketed"] is True


def test_m147_excludes_cells_without_a_determined_peak():
    """`G23-188`: chi cell co `T*` XAC DINH moi gop vao `M-147`."""
    import json
    import os
    p = os.path.join("results", "PENDING", "phase-23", "t_loss_fine.json")
    if not os.path.exists(p):
        pytest.skip("chua chay --t-loss-fine")
    d = json.load(open(p, encoding="utf-8"))
    assert d["M147_n_cells_used"] + d["M147_n_cells_undetermined"] == 8
    for k in d["M147_undetermined_cells"]:
        assert d["cells"][k]["log2_ratio"] is None or not d["cells"][k]["bracketed"]

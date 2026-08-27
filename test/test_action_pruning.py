#!/usr/bin/env python3
"""Gate cau truc cua Lesson 23.24 (`A074` muc 9, sua boi `A074b`).

Khong test nao o day CHAM DIEM. Chung ep ma nguon khop voi tien dang ky.
"""
from __future__ import annotations

import ast
import json
import os

import numpy as np
import pytest

from cert import action_pruning as AP
from cert import cell_matrices as CMX
from cert import config_matrix as CM
from cert import simultaneous_score as SS
from cert.build_calib_set_v2 import Z_EDGES_PRIMARY, assign_bin
from cert.build_calib_set_v3 import AXIS_MEASURED, Z_EDGES_V7, _load_cell
from cert.cell_matrices import DEAD_ACTION_THRESHOLD, LADDER
from cert.taxonomy_audit import SLA_MANIFEST, W_LOSS
from cert.transfer_matrix import KAPPA_OP

SRC = os.path.join(os.path.dirname(os.path.abspath(AP.__file__)), "action_pruning.py")


def _source() -> str:
    with open(SRC, "r", encoding="utf-8") as fh:
        return fh.read()


def _func(name: str) -> ast.FunctionDef:
    tree = ast.parse(_source())
    return next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == name)


def _body_src(name: str) -> str:
    """Ma THUC THI cua mot ham, DA BO docstring.

    Quet chuoi tren `ast.unparse` nguyen ban se bat trung chinh docstring --
    tuc test tu doc lai loi canh bao cua no va tuong do la ma. Bo docstring
    di thi cai chan moi noi ve HANH VI.
    """
    fn = _func(name)
    body = fn.body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    return "\n".join(ast.unparse(n) for n in body)


def _flat(text: str) -> str:
    """Gop moi khoang trang lien tiep thanh mot dau cach.

    `BACKLOG.md` xuong dong giua cau, nen so chuoi tho se truot.
    """
    return " ".join(text.split())


# ---------------------------------------------------------------------------
# `A074` muc 9
# ---------------------------------------------------------------------------

def test_path_indices_are_zero_based():
    """Bay lech-mot: P1 = 0, P2 = 1, P3 = 2, P4 = 3.

    `RUNGS` phai khop `LADDER` da dong o ba bac dau. Lech mot chi so o day
    lam hong ca lesson ma khong co gi bao.
    """
    ladder = dict(LADDER)
    assert AP.RUNGS["S0_K4"] == ladder["S0"] == ()
    assert AP.RUNGS["S1_K3"] == ladder["S1"] == (1,)
    assert AP.RUNGS["S2_K2"] == ladder["S2"] == (1, 3)
    assert AP.RUNGS["NC_K3"] == (2,)          # P3, duong SONG
    assert AP.path_name(0) == "P1" and AP.path_name(3) == "P4"


def test_alpha_each_ladder():
    """`alpha/3, alpha/2, alpha/1` cho K = 4, 3, 2; `min_blocks` 29, 19, 9."""
    a = AP.ladder_analytics()
    assert (a["S0_K4"]["m"], a["S0_K4"]["min_blocks"]) == (3, 29)
    assert (a["S1_K3"]["m"], a["S1_K3"]["min_blocks"]) == (2, 19)
    assert (a["S2_K2"]["m"], a["S2_K2"]["min_blocks"]) == (1, 9)
    assert a["S0_K4"]["alpha_each"] == pytest.approx(0.10 / 3)
    assert a["S1_K3"]["alpha_each"] == pytest.approx(0.05)
    assert a["S2_K2"]["alpha_each"] == pytest.approx(0.10)
    # doi chung am phai co CUNG ngan sach voi nhanh chinh -- neu khac thi no
    # do ca chenh lech ngan sach chu khong chi "song hay chet".
    assert a["NC_K3"]["alpha_each"] == a["S1_K3"]["alpha_each"]
    assert a["NC_K3"]["min_blocks"] == a["S1_K3"]["min_blocks"]
    for v in a.values():
        assert CM.conformal_min_blocks(v["alpha_each"]) == v["min_blocks"]


def test_dead_action_threshold_unchanged():
    """`DEAD_ACTION_THRESHOLD == 0.05`, khop `cell_matrices`."""
    assert DEAD_ACTION_THRESHOLD == 0.05
    assert AP.DEAD_ACTION_THRESHOLD is DEAD_ACTION_THRESHOLD


def test_dead_action_uses_calib_only():
    """Quet AST: `dead_action_calib` khong duoc cham mot hang TEST nao.

    Chan cu the: khong duoc co phep NGHICH DAO bit (`~mask`) trong than ham,
    vi do la cach duy nhat de lat mat na calib thanh mat na test.
    """
    fn = _func("dead_action_calib")
    inverts = [n for n in ast.walk(fn)
               if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Invert)]
    assert not inverts, "dead_action_calib dao mat na calib -> cham hang TEST"
    body = _body_src("dead_action_calib")
    assert "is_calib" in body
    for forbidden in ("~cal", "tst", "test"):
        assert forbidden not in body, forbidden


def test_two_tier_criterion_is_signed():
    """Tieu chi hai tang trong code khop tung chu voi `A074` muc 3.2."""
    fn = _body_src("dead_action_calib")
    assert "p_star[p] < DEAD_ACTION_THRESHOLD" in fn      # tang 1, NGHIEM NGAT
    assert "p_twin[p] == 0.0" in fn                       # tang 2(a)
    assert "3.0 / n" in fn                                # `A074` N2, quy tac ba
    doc = os.path.join(os.path.dirname(os.path.dirname(SRC)),
                       "docs", "phase-23", "A074-amendment-74.md")
    with open(doc, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert "P_calib(a* = a) < DEAD_ACTION_THRESHOLD = 0.05" in text
    assert "P_calib(a_twin = a) = 0" in text


def test_nc_cuts_a_live_action_and_leg_i_is_dropped():
    """`NC-23.24-1` cat duong co `P_calib(a*) > 0.05`, khong cat duong chet.

    Va ve (i) phai DA BI BO theo `A074b` muc 4 -- neu no quay lai duoi dang
    mot khoa duoc cham diem thi test nay do.
    """
    assert AP.RUNGS["NC_K3"] == (2,)                       # P3
    assert AP.RUNGS["NC_K3"] != AP.RUNGS["S1_K3"]
    doc = AP.negative_control.__doc__ or ""
    assert "DA BO" in doc and "mo neo" in doc
    src = _source()
    assert "leg_i_status" in src
    assert "leg_i_hit" not in src        # khong con ve (i) duoc cham diem
    assert "leg_ii_hit" in src and "leg_iii_guard_pass" in src


def test_backlog_counter_definition_pinned():
    """Dinh nghia bo dem o `A074` muc 2 khop dong quy tac trong `BACKLOG.md`."""
    root = os.path.dirname(os.path.dirname(SRC))
    with open(os.path.join(root, "docs", "phase-23", "BACKLOG.md"),
              "r", encoding="utf-8") as fh:
        backlog = _flat(fh.read())
    with open(os.path.join(root, "docs", "phase-23", "A074-amendment-74.md"),
              "r", encoding="utf-8") as fh:
        amd = _flat(fh.read())
    for clause in ("trang thai la HOAN", "TRUOC khi lesson hien tai bat dau",
                   "khong nhan no lam noi dung"):
        assert clause in amd, clause
    for clause in ("trang thai HOAN", "TRUOC khi lesson hien tai bat dau",
                   "khong nhan no lam noi dung"):
        assert clause in backlog, clause
    assert "A074` muc 2" in backlog


# ---------------------------------------------------------------------------
# `A074b` -- ba su that ky thuat, moi cai mot test
# ---------------------------------------------------------------------------

def test_cutting_a_non_anchor_path_preserves_surviving_scores():
    """Tinh chat NEN cua ca lesson (`A074b` muc 1).

    Neu duong bi cat KHONG BAO GIO la `a_1`, thi `e(a)` cua moi duong song
    sot GIU NGUYEN, nen tap `s` con lai la tap cu BOT DI mot phan tu -- khong
    phai mot tap moi. Day la ly do cat P2 duoc goi la "sach".

    Nua thu hai la nua PHAN BIET: cat mot duong CO KHI la mo neo thi tinh
    chat tap con VO HIEU. Khong co nua nay, test tren luon xanh.
    """
    rng = np.random.default_rng(23241)
    n, k, victim = 4000, 4, 1

    y_hat = rng.normal(100.0, 10.0, (n, k))
    y_hat[:, victim] += 500.0                    # P2 khong bao gio la a_1
    y_true = y_hat + rng.normal(0.0, 3.0, (n, k))
    assert (y_hat.argmin(axis=1) == victim).sum() == 0

    keep = [p for p in range(k) if p != victim]
    s_full = SS.pair_scores(y_true, y_hat)
    s_cut = SS.pair_scores(y_true[:, keep], y_hat[:, keep])
    assert s_cut.shape[1] == s_full.shape[1] - 1
    for i in range(n):
        assert np.isin(np.sort(s_cut[i]), np.sort(s_full[i])).all()

    # --- nua PHAN BIET: cat mot duong CO KHI la mo neo ---------------------
    anchor = int(np.bincount(y_hat.argmin(axis=1), minlength=k).argmax())
    keep2 = [p for p in range(k) if p != anchor]
    s_cut2 = SS.pair_scores(y_true[:, keep2], y_hat[:, keep2])
    subset_rows = sum(int(np.isin(np.sort(s_cut2[i]), np.sort(s_full[i])).all())
                      for i in range(n))
    assert subset_rows < n, "cat mo neo ma van la tap con -> test khong phan biet"


def test_parquet_cannot_rerank_so_module_uses_cell_matrices():
    """`A074b` muc 2: parquet khong luu `y_hat`/`y_true` theo TUNG DUONG.

    Neu mot ngay nao do parquet CO luu, test nay do va ta duoc nhac doc lai
    quyet dinh kien truc thay vi de no muc ngam.
    """
    from cert.build_calib_set_v3 import build_one_v3
    src = ast.unparse(ast.parse(open(
        os.path.join(os.path.dirname(SRC), "build_calib_set_v3.py"),
        encoding="utf-8").read()))
    assert "'y_hat_full'" not in src and '"y_hat_full"' not in src
    assert build_one_v3 is not None
    # va module nay phai IMPORT tang day, khong phai duong parquet. Kiem tren
    # cay import chu khong tren chuoi: nhac ten `baselines_lit.json` trong mot
    # ghi chu la hop le, IMPORT no thi khong.
    imported = {
        n.module for n in ast.walk(ast.parse(_source()))
        if isinstance(n, ast.ImportFrom) and n.module
    }
    assert "cert.cell_matrices" in imported
    assert not any("baselines_lit" in m for m in imported)


def test_module_uses_measured_axis_not_legacy():
    """`A074b` muc 3 / `L130`: truc DO, khong phai truc legacy.

    `cell_matrices.prepare()` ghim cung `Z_EDGES_PRIMARY` va NEM tren truc
    do. Module nay phai TU bin bang `Z_EDGES_V7` va KHONG duoc goi `prepare`.
    """
    assert AP.AXIS == AXIS_MEASURED
    src = _source()
    assert "prepare_v7" in src
    assert "CMX.prepare(" not in src
    body = _body_src("prepare_v7")
    assert "Z_EDGES_V7" in body and "Z_EDGES_PRIMARY" not in body

    # mien cua hai truc that su khong long nhau -- day la ly do `prepare` nem
    z = np.array([0.115, 0.615])
    assert assign_bin(z, Z_EDGES_V7).tolist() == [0, 3]
    with pytest.raises(ValueError):
        assign_bin(z, Z_EDGES_PRIMARY)


def test_selective_m_bin_collapses_the_mhat_axis():
    """Thu truc `m_hat` ve MOT o, khong sua `cell_matrices` (`CL-01`)."""
    mb = AP._selective_m_bin(1000)
    assert mb.shape == (1000,) and np.unique(mb).tolist() == [0]


def test_kappa_and_family_match_live_config():
    assert AP.KAPPA_OP == KAPPA_OP == 0.50
    assert AP.ALPHA_FAMILY == 0.10
    assert AP.MULTIPLICITY == "bonferroni"


# ---------------------------------------------------------------------------
# Cai chan quan trong nhat: `q_hat` cua module khop DUONG DA DONG
# ---------------------------------------------------------------------------

def test_action_pruning_uses_live_sla_axis():
    """Chan `L132`. `cell_matrices` mac dinh ve truc SLA DEPRECATED.

    `cell_matrices()` co `calibration_path = SLA_CALIB` (self_calibrated,
    `S14`) va `w_loss_override = None`. Khong truyen tuong minh thi Lesson
    23.24 chay voi `w_loss = 3222.244682` thay vi `5000.0`, va vi chi phi la
    `delay + w_loss * loss` thi ca thang `q_hat` co lai 0.6445 lan.
    """
    body = _body_src("build_base")
    assert "calibration_path=SLA_MANIFEST" in body
    assert "w_loss_override=resolve_w_loss()" in body

    # hai nguon PHAI lech nhau -- neu khong, test nay tam thuong
    dep = float(_load_cell(AP.MODE, AP.RHO_BAR,
                           calibration_path=CMX.SLA_CALIB)["w_loss"])
    live = float(_load_cell(AP.MODE, AP.RHO_BAR,
                            calibration_path=SLA_MANIFEST)["w_loss"])
    assert dep != live, "hai truc SLA trung nhau -> cai chan nay khong phan biet"
    assert live == 5000.0 == float(W_LOSS)
    assert AP.resolve_w_loss() == live

    # va ban build LIVE ma chuoi chung nhan dung cung khai dung so do
    with open("results/LIVE/phase-21R/"
              "calib_set_poisson_0.925_U3_measured_v7_report.json",
              "r", encoding="utf-8") as fh:
        assert float(json.load(fh)["w_loss"]) == 5000.0


def test_validity_reads_wloss_from_data_not_from_argument():
    """Chan `L134` / `A075` R6. `validity` phai DOC, khong duoc NHAN.

    `config.w_loss_used` di qua `resolve_w_loss()` (doc tu manifest bang
    `_load_cell`), con `validity.w_loss` di qua tham so `W_LOSS`. Hai duong
    DOC LAP phai chi ve cung mot so; do la thu duy nhat bat duoc lech truc.
    """
    if not os.path.exists(AP.OUTPUT):
        pytest.skip("chua chay `python -m cert.action_pruning --run`")
    with open(AP.OUTPUT, "r", encoding="utf-8") as fh:
        art = json.load(fh)
    assert art["config"]["w_loss_used"] == art["validity"]["w_loss"] == 5000.0
    assert art["config"]["w_loss_source"] == "override"
    assert art["config"]["sla_calibration_path"] == SLA_MANIFEST
    assert art["validity"]["sla_axis"]["source_path"] == SLA_MANIFEST


def test_void_artifact_is_demoted_and_labelled():
    """`A075` muc 2: ban chay dau tien phai nam o SUPERSEDED va mang nhan VOID.

    Khong dua vao ten file: doc khoi `VOID` ben trong.
    """
    void = ("results/SUPERSEDED/phase-23/"
            "action_pruning_VOID_wloss_defect.json")
    assert os.path.exists(void), "ban VOID phai duoc giu lai de truy vet"
    assert not os.path.exists("results/PENDING/phase-23/action_pruning.json")
    with open(void, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    assert d["VOID"]["status"].startswith("VOID")
    assert d["config"]["w_loss_used"] if "w_loss_used" in d["config"] else True
    # ban VOID that su chay tren truc sai -- neu khong thi no khong phai VOID
    assert d["validity"]["w_loss"] == 5000.0          # LOI KHAI
    assert "3222.244681647411" in d["VOID"]["reason"]  # so THAT


def test_doc52_ladder_table_matches_artifact():
    """Bang thang cat trong doc 52 phai khop artifact TUNG CHU SO.

    Bang do duoc CHEP TAY. Lan dau chep, ba o bi sai (S0 `err|acc` va
    `err_anchor`, S2 `err|acc` va `err_anchor`) -- khong test nao bat duoc,
    va doc la thu nguoi doc tin. Day la cai chan do: hai duong doc lap (doc
    va artifact) phai chi ve cung mot so, cung tinh than `A075` R6.
    """
    if not os.path.exists(AP.OUTPUT):
        pytest.skip("chua chay `python -m cert.action_pruning --run`")
    with open(AP.OUTPUT, "r", encoding="utf-8") as fh:
        rungs = json.load(fh)["G23_298_rungs"]
    doc = os.path.join(os.path.dirname(os.path.dirname(SRC)),
                       "docs", "phase-23", "52-action-pruning.md")
    with open(doc, "r", encoding="utf-8") as fh:
        lines = [l for l in fh.read().splitlines() if l.startswith("| S0 K=4")
                 or l.startswith("| **S1 K=3") or l.startswith("| S2 K=2")
                 or l.startswith("| NC K=3")]
    assert len(lines) == 4, "khong tim du 4 hang cua bang thang cat"

    for line, key in zip(lines, ("S0_K4", "S1_K3", "S2_K2", "NC_K3")):
        cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
        acc, viol, err, anchor = (float(cells[5]), float(cells[6]),
                                  float(cells[7]), float(cells[8]))
        r = rungs[key]
        assert acc == round(r["acceptance"], 6), key
        assert viol == round(r["viol_given_accept"], 6), key
        assert err == round(r["err_given_accept"], 6), key
        assert anchor == round(r["err_anchor"], 6), key
        assert int(cells[2]) == r["m"], key
        assert int(cells[4]) == r["min_blocks"], key
        assert float(cells[3]) == round(r["alpha_each"], 6), key


def test_accept_matches_closed_path():
    """`qhat_by_zbin` + nguong `kappa` phai khop BIT voi `fit_and_accept`.

    Module nay tinh `q` mot lan roi dung cho CA `accept` lan `viol`, thay vi
    goi `fit_and_accept` (no tinh `q` ben trong va khong tra ra). Test nay la
    thu chung minh hai duong khong lech: neu ai do sua mot ben, test do.
    """
    rng = np.random.default_rng(74)
    n, k = 6000, 4
    y_hat = rng.normal(100.0, 10.0, (n, k))
    y_true = y_hat + rng.normal(0.0, 3.0, (n, k))
    z_bin = rng.integers(0, 4, n).astype(np.int64)
    block_id = (np.arange(n) // 20).astype(np.int32)
    is_calib = (block_id % 2 == 0)

    m_hat = SS.pair_margins_hat(y_hat)
    s_pair = SS.pair_scores(y_true, y_hat)
    prep = {"z_bin": z_bin, "is_calib": is_calib, "block_id": block_id}
    alpha_each, kappa = 0.05, 0.50

    q = AP.qhat_by_zbin(prep, s_pair, alpha_each)
    mine = (m_hat >= kappa * AP._q_rows(prep, q, s_pair.shape[1])).all(axis=1)
    closed = CMX.fit_and_accept(
        z_bin, AP._selective_m_bin(n), block_id, is_calib,
        m_hat, s_pair, alpha_each, kappa,
    )
    assert np.array_equal(mine, closed)
    assert 0.0 < mine.mean() < 1.0, "cai chan tam thuong: accept toan 0 hoac 1"

"""20R2.2 -- sinh BANG DU DOAN KY TRUOC cho phase 20R2.

VI SAO LA MOT CONG CU, KHONG PHAI MOT BANG GO TAY (gate 0-1):
mot bang go tay khong tai lap duoc, va RT20-3 da chung minh dieu do ton kem:
ban Sheppard cua MASTER_PLAN duoc CHEP chu khong duoc TINH, nen no mang mot
z tham chieu KHAC (0.369) voi z ma pipeline that su dung. Mot bang chep sai
z KHONG BAO GIO BAO LOI -- no chi lam moi so sanh sau do so hai dai luong
khac nhau.

Cong cu nay sinh:
  1. Bang Sheppard err(z, tau) = arccos(exp(-z/tau))/pi tai z DA KY
  2. Hai khai bao estimand (7 truong) cho 20R2
  3. Bang chap nhan + chinh sach doc, KY TRUOC khi chay
  4. Do nhay truc AoI -- so hoc, khong phai tinh tu

Chay:
    python -m tools.20r2_2_predictions --out docs/phase-20R2/01-prediction-signed.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import os
import pathlib

SCHEMA = "dt4n.prediction_signed.v1"

# ---------------------------------------------------------------- truc AoI ky
# z THAM CHIEU: trung vi cua MO HINH measured (base_age_steps, U0).
# KHONG 0.369: 0.369 thuoc ho measured nhung la hang so Z_MEDIAN_S cua
# link_corr_matrix.py, khong phai trung vi cua bo sinh ma pipeline THUC SU goi.
# Prereg 00-preregistration.md muc A3/A3b da lap luan va chot dieu nay.
Z_REFERENCE_S = 0.3650

# Cac gia tri z KHAC trong CUNG ho measured -- dung de do DO NHAY CON LAI sau
# khi truc da duoc ky. Day KHONG phai cac lua chon dang mo.
Z_MEASURED_FAMILY = {
    "model_median_U0": 0.3650,
    "empirical_clean_p50": 0.35827,
    "model_mean": 0.36594,
    "empirical_p50_alt": 0.36728,
    "link_corr_matrix_Z_MEDIAN_S": 0.369,
}

# Truc legacy -- DOI CHUNG AM co chu dich, KHONG phai mot lua chon canh tranh.
Z_LEGACY_CONTRAST = 0.30237

TAUS = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 28.0]

K_MC = 3.0

REPO = pathlib.Path(__file__).resolve().parents[1]
HARNESS_REL = "measurements/decision_error_v2.py"


def _field_line(field: str) -> int:
    """Tra SO DONG cua mot truong artifact bang cach QUET NGUON, khong go tay.

    VI SAO KHONG GO TAY: GLOSSARY da ghi rang so dong ":402" cua T2 DA TROI mot
    lan. Mot so dong go tay la mot su that co han su dung, va no het han IM
    LANG. Quet nguon thi no khong bao gio het han.

    Lay lan xuat hien TRONG run_cell (khoi dung dict per_z), tuc lan dau tien
    sau dong `out["per_z"][z_key(z_s)] = {`.
    """
    src = (REPO / HARNESS_REL).read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(src) if 'out["per_z"][z_key(z_s)] = {' in l)
    needle = '"%s":' % field
    for i in range(start, len(src)):
        if needle in src[i]:
            return i + 1
        if src[i].strip() == "}":
            break
    raise LookupError("khong tim thay truong %r trong run_cell" % field)


def sheppard(z: float, tau: float) -> float:
    """err(z, tau) = arccos(exp(-z/tau)) / pi.

    Dan xuat, khong phai cong thuc roi tu tren troi:
      1. Dinh ly Sheppard (1898): voi (X, Y) chuan hai chieu, ky vong 0,
         tuong quan rho thi P(sign X != sign Y) = arccos(rho)/pi.
      2. Twin quyet dinh bang DAU cua bien (margin). Chon sai <=> bien doi dau
         giua luc twin nhin (tuoi z) va luc thuc te xay ra.
      3. Bien tien hoa AR(1) voi thoi gian tuong quan tau => rho(z) = exp(-z/tau).
    Ghep lai duoc cong thuc tren.

    Kiem ba diem cuc (lam TRUOC khi tin bat ky cong thuc la nao):
      rho =  1 -> arccos(1)/pi  = 0    khong bao gio doi dau
      rho =  0 -> arccos(0)/pi  = 0.5  tung dong xu
      rho = -1 -> arccos(-1)/pi = 1    luon doi dau
    """
    return float(math.acos(math.exp(-float(z) / float(tau))) / math.pi)


def sheppard_table(z: float) -> list:
    return [{"tau": t, "rho": math.exp(-z / t), "err": sheppard(z, t)}
            for t in TAUS]


def axis_sensitivity() -> dict:
    """Do nhay cua err theo LUA CHON TRUC -- tach hai thu thuong bi gop.

    (a) DO NHAY CON LAI trong ho measured, SAU KHI truc da duoc ky.
        Day la do bat dinh THAT SU con lai. Do duoc: <= 1.47% moi tau.
    (b) TUONG PHAN measured vs legacy (~ -9%). Day KHONG phai do bat dinh:
        legacy la DOI CHUNG AM co chu dich. Dung con so nay lam co so chon
        bang chap nhan la NHAM LAN hai thu khac nhau -- no se cho mot bang
        rong gap 6 lan muc can thiet, va mot bang qua rong lam gate MAT LUC
        PHAN GIAI (cai gi cung PASS).
    """
    out = {"per_tau": [], "note": (
        "residual_rel = bien do trong HO measured / err tai z da ky. "
        "legacy_contrast_rel = tuong phan voi truc DOI CHUNG AM, KHONG phai "
        "do bat dinh cua ket qua chinh.")}
    worst = 0.0
    for t in TAUS:
        e0 = sheppard(Z_REFERENCE_S, t)
        es = [sheppard(z, t) for z in Z_MEASURED_FAMILY.values()]
        res = (max(es) - min(es)) / e0
        worst = max(worst, res)
        out["per_tau"].append({
            "tau": t,
            "err_at_signed_z": e0,
            "measured_family_residual_rel": res,
            "legacy_contrast_rel": (sheppard(Z_LEGACY_CONTRAST, t) - e0) / e0,
        })
    out["worst_measured_family_residual_rel"] = worst
    out["worst_legacy_contrast_rel"] = max(
        abs(r["legacy_contrast_rel"]) for r in out["per_tau"])
    return out


def estimands() -> dict:
    """Hai estimand cua 20R2, DU BAY TRUONG (luat A-T2-3 cua GLOSSARY).

    KHONG tai dung RMS_ALLACTION_DELAY: no dung LEVEL (all_action) nhung SAI
    SCALE (delay_ms vs ti le khong thu nguyen) va SAI ARTIFACT_FIELD
    (rms_e_model vs err_total). Dung lai no la lap lai DUNG loi A-T2-3.
    """
    pop_gate = (
        "8 o `gate` cua luoi 20R2: mode c_a thuoc {poisson, h2} x rho_bar "
        "thuoc {0.700, 0.850, 0.925, 0.960}. Nguon phan hoach: "
        "results/LIVE/phase-20R/sla_calibration.json summary.n_gate_cells = 8. "
        "Luoi KET QUA = 8 o x 8 tau x 2 sigma x 5 seed = 640 o. "
        "2 o `cbr` kha thi (rho_bar 0.700, 0.850) la DOI CHUNG DUONG, bao cao "
        "RIENG, KHONG gop vao bat ky trung binh nao. 2 o cbr con lai bi loai "
        "boi q8 (sigma_max_regime = 0).")
    return {
        "DECISION_ERR_BY_AGE": {
            "LEVEL": "all_action",
            "POPULATION": pop_gate,
            "SCALE": ("ti le (khong thu nguyen), trong [0, 1]. KHONG phai "
                      "delay_ms: `err` la TI LE hang sai, khong phai mot do "
                      "tre. KHONG duoc dat cung nguong voi d_sla."),
            "UNIT": "dimensionless",
            "BRANCH": (
                "z_fixed -- lag TAT DINH k = round(z/dt), "
                "measurements/decision_error_v2.py (lag TAT DINH). KHONG goi bo sinh AoI "
                "nao trong run_cell (T2-L8 dinh chinh co che). Truc AoI vao qua "
                "VIEC CHON z, khong qua bo sinh."),
            "CODE": "measurements/decision_error_v2.py : run_cell",
            "ARTIFACT_FIELD": "per_z[<z_key>].err_total",
            "ARTIFACT_FIELD_LINE": _field_line("err_total"),
            "DECOMPOSITION": {
                "per_z[<z_key>].err_model": _field_line("err_model"),
                "per_z[<z_key>].err_stale": _field_line("err_stale"),
                "per_z[<z_key>].extrapolated": _field_line("extrapolated"),
            },
            "EXTRAPOLATED_MEANS": (
                "z nam NGOAI mien tuoi that cua truc measured [0.115, 0.615]. "
                "CO NGHIA 'so nay dung nhung no noi ve mot trang thai he chua "
                "bao gio o', KHONG co nghia 'so nay sai'."),
            "DUNG CHO": ["RQ-20R2a", "RQ-20R2c", "RQ-20R2d"],
            "GIA TRI MOC": None,
            "GIA TRI MOC NOTE": "dien SAU pilot 3 o cua 20R2.4, TRUOC chien dich",
        },
        "SLA_VIOL_BY_AGE": {
            "LEVEL": "all_action",
            "POPULATION": pop_gate + " (GIONG DECISION_ERR_BY_AGE co chu dich: "
                          "hai estimand phai noi ve cung mot quan the thi moi "
                          "doc chung duoc trong mot ket luan.)",
            "SCALE": ("cost_ms -- DI QUA ham chi phi (delay + w_loss * loss), "
                      "nen NHAY voi w_loss va voi truc SLA. Day la khac biet "
                      "CHINH voi DECISION_ERR_BY_AGE: err la TI LE, d_sla la "
                      "CHI PHI. Khac ca THANG va DON VI."),
            "UNIT": "ms",
            "BRANCH": "z_fixed",
            "CODE": "measurements/decision_error_v2.py : run_cell",
            "ARTIFACT_FIELD": "per_z[<z_key>].d_sla",
            "ARTIFACT_FIELD_LINE": _field_line("d_sla"),
            "DUNG CHO": ["RQ-20R2b"],
            "GIA TRI MOC": None,
            "GIA TRI MOC NOTE": "dien sau pilot",
        },
    }


SE_PILOT_REL = "docs/phase-20R2/02-se-pilot.json"

# SAN CHU KY DOC LAP moi o. Co mau hieu dung la T_sim/tau, KHONG phai n.
# `n_for_tau` giu CHI PHI gan nhu phang nhung KHONG giu LUC: chu ky di tu 2000
# (tau=0.5) xuong 50 (tau=20, 28) -- bien thien 40 lan. San nay lam LUC deu
# nhau thay vi de no roi 40 lan theo tau.
# 200 duoc chon vi do la muc tau=5 DA co san; no lam san ma khong nang bat ky
# tau nao <= 5. KY TRUOC chien dich.
CYCLE_FLOOR = 200.0


def n_multiplier(tau: float) -> int:
    """Nhan n (luy thua 2) de o dat CYCLE_FLOOR chu ky doc lap.

    Suy tu QUY TAC, khong go tay tung tau -- de khi ai doi CYCLE_FLOOR thi ca
    bang tu cap nhat thay vi lech am tham.
    """
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    cycles = n_for_tau(tau, DEFAULT_DT) * DEFAULT_DT / float(tau)
    mul = 1
    while cycles * mul < CYCLE_FLOOR:
        mul *= 2
    return mul


def _se_law() -> dict:
    """se_rel(tau) tu LUAT GOP, khong tu tung uoc luong 5-seed roi rac.

    VI SAO KHONG DUNG TUNG UOC LUONG: se uoc tu 5 seed co ~35% do bat dinh, va
    do duoc thi te hon the. Chung minh bang phep do doi chung: nang n gap 4 lan
    o tau=28 le ra phai lam se GIAM 2 lan, nhung se do duoc lai TANG 1.7 lan
    (0.000908 -> 0.001569). Mot dai luong ma phep do khong theo kip huong da
    biet thi khong dung lam san bang duoc.

    LUAT: se_rel = C / sqrt(so chu ky).  Do duoc tren 10 diem (8 tau x1 + 2
    tau x4): so mu khop -0.532 so voi -0.5 cua ly thuyet. Gop 10 phep do de
    uoc MOT tham so C thi on dinh hon nhieu so voi 10 uoc luong doc lap.
    Dung C + 1sd (bao thu vua phai), khong dung C trung binh.
    """
    path = REPO / SE_PILOT_REL
    if not path.is_file():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc["law"]


def acceptance_band(axis: dict) -> dict:
    """Bang chap nhan THEO TUNG TAU -- cong thuc ky truoc, gia tri cam sau.

    VI SAO KHONG PHAI MOT SO DUY NHAT (sua 2026-09-10):
    `n_for_tau` giu CHI PHI gan nhu phang (~1.32 s/o) nhung KHONG giu LUC
    THONG KE. Co mau hieu dung la SO CHU KY DOC LAP = T_sim/tau, va no bien
    thien 40 lan tren luoi:

        tau=0.5 -> 2000 chu ky        tau=20 -> 50 chu ky
        tau=28  ->   50 chu ky  (n da co gian x1.4 de giu dung san 50)

    Do duoc tren pilot 5 seed: se_rel di tu 0.64% (tau=0.5) den 5.84%
    (tau=20) -- bien thien ~9 lan. Mot bang DUY NHAT se:
        lay theo tau nho -> qua chat o tau lon -> TRUOT GIA
        lay theo tau lon -> qua long o tau nho -> MAT LUC PHAN GIAI
        lay trung binh   -> ca hai benh cung luc
    Benh thu hai chinh la thu DO_NOT_USE ben duoi canh bao.

    BANG NAY GATE CAI GI: muc do KHOP giua err do duoc va duong tham chieu
    Sheppard TAI TUNG tau. No KHONG phai phep kiem don dieu -- phep do dung
    thong ke KHAC (sigma tung cap, xem reading_policy), vi hai cau hoi khac
    nhau thi khong dung chung mot con so.
    """
    from measurements.sla_calib_v2 import DEFAULT_DT, n_for_tau
    law = _se_law()
    C = law.get("C_upper") if law else None
    per_tau = []
    for row in axis["per_tau"]:
        t = float(row["tau"])
        floor = float(row["measured_family_residual_rel"])
        mul = n_multiplier(t)
        cycles = n_for_tau(t, DEFAULT_DT) * mul * DEFAULT_DT / t
        s = (C / math.sqrt(cycles)) if C else None
        band = max(floor, K_MC * s) if s is not None else None
        per_tau.append({
            "tau": t,
            "axis_floor_rel": floor,
            "n_multiplier": mul,
            "independent_cycles": cycles,
            "se_rel_from_law": s,
            "band_rel": band,
            "binding_term": (None if band is None
                             else ("axis_floor" if floor >= K_MC * s else "mc_noise")),
        })
    return {
        "formula": "band_rel(tau) = max(AXIS_FLOOR(tau), K_MC * se_pilot_rel(tau))",
        "K_MC": K_MC,
        "K_MC_why": (
            "3 sai so chuan. Ky TRUOC pilot de so pilot khong the tu chon he so "
            "cho minh."),
        "AXIS_FLOOR_why": (
            "do nhay CON LAI trong ho measured sau khi truc da ky, THEO TUNG tau "
            "(1.109% o tau=0.5 den 1.466% o tau=28). Bang khong the hep hon "
            "chinh do bat dinh cua truc."),
        "per_tau": per_tau,
        "se_source": SE_PILOT_REL,
        "se_law": law,
        "cycle_floor": CYCLE_FLOOR,
        "cycle_floor_why": (
            "co mau hieu dung la T_sim/tau, KHONG phai n. Khong co san nay thi "
            "luc thong ke roi 40 lan tren luoi trong khi chi phi gan nhu phang, "
            "va cap 20->28 chi dat 2.20 sigma (do duoc) -- duoi nguong 3 sigma."),
        "n_multiplier": {str(t): n_multiplier(t) for t in TAUS},
        "superseded_scalar_band": {
            "was": "band_rel = max(AXIS_FLOOR_worst, K_MC * se_pilot_rel)",
            "AXIS_FLOOR_worst": axis["worst_measured_family_residual_rel"],
            "why_replaced": (
                "mot so duy nhat gia dinh luc thong ke deu nhau tren luoi. Do "
                "duoc: se_rel bien thien ~9 lan, va co mau hieu dung 40 lan. "
                "Giu ban cu o day de dau vet khong mat."),
        },
        "DO_NOT_USE": {
            "value_rel": axis["worst_legacy_contrast_rel"],
            "what_it_really_is": (
                "tuong phan measured vs LEGACY (~9%). Legacy la DOI CHUNG AM co "
                "chu dich, khong phai mot lua chon truc dang mo. Lay no lam san "
                "cho bang la nham lan DOI CHUNG voi DO BAT DINH: no cho mot bang "
                "rong gap ~6 lan muc can, va mot bang qua rong lam gate MAT LUC "
                "PHAN GIAI -- cai gi cung PASS, nen gate khong con noi len dieu gi."),
        },
    }


def reading_policy() -> dict:
    """Chinh sach doc -- viet cac cau 'neu...thi...' TRUOC khi co so.

    Chong 'garden of forking paths' (Gelman & Loken 2013): ngay ca khi khong
    thu nhieu phan tich, chi can BAN SE CHON KHAC DI neu du lieu khac thi muc
    y nghia da bi pha. Voi 800 o, so loi re la 8 tau x 2 (gop seed?) x 2 (gop
    cbr?) x 3 (z nao?) x 2 (bang nao?) = 768 to hop phan tich. Gan nhu chac
    chan co it nhat mot to hop cho ket qua dep.
    """
    return {
        "PRIMARY_directional": {
            "claim": "err_do >= err_sheppard tai MOI tau",
            "why": (
                "3 trong 4 gia dinh Sheppard bi vi pham theo cung MOT huong "
                "(ky vong khac 0 => co san; 4 hanh dong thay vi 2 => nhieu co "
                "hoi sai hon; nugget MA(1) + clip => them nhieu). Nen du doan "
                "CO DINH HUONG manh hon du doan diem: no co the sai theo mot "
                "cach CHO BIET cai gi sai."),
            "if_violated": [
                "(a) mot vi pham chua nghi toi day err XUONG -- phai neu ten no",
                "(b) estimator co bug -- chay doi chung TRUOC khi dien giai",
            ],
            "note": ("Vi pham thu 4 (bien chuan hai chieu) KHONG doan duoc dau, "
                     "nen day la du doan mot phia co dieu kien, khong phai dinh ly."),
        },
        "SECONDARY_shape": {
            "claim": "err don dieu GIAM theo tau tai z da ky",
            "unit_of_comparison": (
                "CAP LIEN KE, khong phai DIEM. 8 tau cho 7 cap. Ban ky dau viet "
                ">= 7/8 diem, ma don dieu khong phai tinh chat cua mot diem -- "
                "no la tinh chat cua mot CAP. Sua 2026-09-10."),
            "n_pairs": len(TAUS) - 1,
            "pass_rule": "don dieu o >= 6/7 CAP => 20R2-2 PASS",
            "one_break": "vo don dieu o DUNG MOT cap => bao cao la DU LIEU, KHONG sua luoi",
            "two_breaks": "vo o >= 2 cap => nghi estimator, chay doi chung TRUOC khi dien giai",
            "statistic": (
                "sigma = |err_i - err_j| / sqrt(se_i^2 + se_j^2). Mot cap chi "
                "DOC DUOC neu sigma >= 3. Day la thong ke KHAC voi band_rel: "
                "band_rel hoi 'co khop Sheppard khong', cap sigma hoi 'hai tau "
                "co phan biet duoc khong'. Hai cau hoi khac nhau."),
            "power_note": (
                "Do duoc tren pilot (5 seed, truoc khi nang n): moi cap >= 4.82 "
                "sigma TRU cap 20->28 chi dat 2.20 sigma -- khoang cach nho nhat "
                "(13.3%) gap it chu ky nhat (50). Vi vay n tai tau=20 va 28 duoc "
                "NANG x4, ky TRUOC chien dich. Xem acceptance_band.n_multiplier."),
        },
        "POSITIVE_CONTROL": {
            "status": "DOWNGRADED_TO_DIAGNOSTIC",
            "claim": None,
            "claim_withdrawn": "err(cbr) < err(poisson) < err(h2) tai cung (z, tau)",
            "cells": "2 o cbr kha thi (rho_bar 0.700, 0.850)",
            "reported": "RIENG, KHONG gop vao trung binh cua 8 o gate",
            "why_withdrawn": (
                "Mot doi chung DUONG chi co gia tri khi ta BIET TRUOC ket qua "
                "phai ra sao. Du kien do duoc o 20R2.4 (E2) cho thay ta KHONG "
                "biet truoc, vi cbr suy bien tren truc bien:\n"
                "  cbr@0.700  A_bar = 3.50e-04 (a=0.9), 2.24e-04 (a=0.5)\n"
                "             nho hon o khong-cbr nho nhat ~3213 lan\n"
                "             span/pure = 0.0067 / 0.0047 -> duong cong theo "
                "tuoi gan nhu PHANG\n"
                "  cbr@0.850  T2 KHONG do -> CHUA BIET\n"
                "Voi bien ~ 0, HAI co che keo err ve HAI HUONG NGUOC NHAU:\n"
                "  (1) cbr deu theo thoi gian -> twin cu VAN dung -> err THAP\n"
                "  (2) bien giua 4 duong ~ 0 -> argmin gan nhu tuy y, lat vi mot "
                "nhieu rat nho -> err CAO\n"
                "Khong co co so tien nghiem de noi co che nao thang. Ky mot bat "
                "dang thuc mot chieu trong tinh huong do la doan, khong phai "
                "doi chung."),
            "what_it_becomes": (
                "CHAN DOAN co dieu kien, bao cao RIENG, KHONG dung de phan "
                "quyet bat ky RQ nao. Ghi ca hai co che TRUOC, roi bao cao co "
                "che nao thang -- do la mot quan sat, khong phai mot phep kiem "
                "dung cu."),
            "signed_before_run": {
                "mechanism_1_low_err": "cbr deu theo thoi gian -> twin cu con dung",
                "mechanism_2_high_err": "bien ~ 0 -> argmin tuy y",
                "both_recorded_before_measurement": True,
            },
            "instrument_check_instead": (
                "Phep kiem DUNG CU that su cua 20R2 la doi chung twin-hoan-hao "
                "(--control), von PHAI cho dung 0 theo docstring cua "
                "decision_error_v2. Do la mot rang buoc TAT DINH, khong phu "
                "thuoc che do luu luong, nen no khong bi suy bien lam hong."),
            "evidence": "results/PENDING/phase-20R2/em_over_a.json",
        },
        "DENOMINATOR": {
            "declared_before_run": True,
            "n_predictions_scored": len(TAUS),
            "rule": (
                "MOI tau trong TAUS deu duoc cham, ke ca khi truot. Giu nguyen "
                "moi miss trong bao cao -- T2 cham 21/32 = 65.6% va GIU ca 10 "
                "miss; lam y het."),
        },
        "AGGREGATION_FALLACY_GUARD": (
            "Gop cbr vao trung binh se KEO err trung binh XUONG (cbr la che do "
            "de nhat), nen bao cao 'twin sai 12%' trong khi o che do kho that "
            "(h2@0.960) co the la 20%. Hop phap ve so hoc, sai lech ve khoa hoc. "
            "Vi vay POPULATION = 8 o gate, cbr bao cao RIENG."),
    }


def build() -> dict:
    axis = axis_sensitivity()
    return {
        "schema": SCHEMA,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "generated_by": "tools/20r2_2_predictions.py",
        "authority": "docs/phase-20R2/00-preregistration.md",
        "z_reference_s": Z_REFERENCE_S,
        "z_reference_why": (
            "trung vi cua MO HINH measured (base_age_steps, U0). KHONG 0.369: "
            "0.369 thuoc ho measured nhung la hang so Z_MEDIAN_S cua "
            "measurements/link_corr_matrix.py, khong phai trung vi cua bo sinh "
            "ma pipeline THUC SU goi."),
        "z_measured_family": Z_MEASURED_FAMILY,
        "z_legacy_contrast": Z_LEGACY_CONTRAST,
        "taus": TAUS,
        "sheppard": sheppard_table(Z_REFERENCE_S),
        "sheppard_is_a_reference_line_not_truth": {
            "violations": [
                {"assumption": "bien chuan hai chieu",
                 "reality": "bien = hieu chi phi PHI TUYEN theo rho",
                 "pushes_err": "khong doan duoc dau"},
                {"assumption": "ky vong 0",
                 "reality": "err_model != 0 => co thien lech",
                 "pushes_err": "TANG (co san, err(z->0) > 0)"},
                {"assumption": "chi 2 hanh dong",
                 "reality": "4 duong, argmin trong 4",
                 "pushes_err": "TANG (nhieu co hoi sai hon)"},
                {"assumption": "AR(1) thuan",
                 "reality": "co nugget MA(1) + clip o RELIABLE_CEILING",
                 "pushes_err": "TANG (nhieu them)"},
            ],
            "net": "3/4 day cung mot huong => du doan CO DINH HUONG",
            "what_the_800_cells_buy": (
                "Sheppard cho GIOI HAN DUOI ly tuong duoi 4 gia dinh, khong cai "
                "nao dung trong he that. 800 o do KHOANG CACH giua ly tuong va "
                "thuc te -- chinh khoang cach do la dong gop, khong phai con so err."),
        },
        "axis_sensitivity": axis,
        "estimands": estimands(),
        "acceptance_band": acceptance_band(axis),
        "reading_policy": reading_policy(),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    doc = build()
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=True)
        fh.write("\n")

    print("=== 20R2.2 du doan ky truoc ===")
    print("z tham chieu = %.4f s  (KHONG 0.369)" % doc["z_reference_s"])
    print("\ntau      rho        err")
    for r in doc["sheppard"]:
        print("%5.1f   %.6f   %.6f" % (r["tau"], r["rho"], r["err"]))
    ax = doc["axis_sensitivity"]
    print("\ndo nhay truc CON LAI (ho measured, sau khi ky): %.2f%%"
          % (ax["worst_measured_family_residual_rel"] * 100))
    print("tuong phan legacy (DOI CHUNG AM, KHONG dung lam san bang): %.2f%%"
          % (ax["worst_legacy_contrast_rel"] * 100))
    b = doc["acceptance_band"]
    print("\nbang: %s" % b["formula"])
    print("  K_MC = %.1f   san chu ky = %g   C = %.4f (trung binh + 1sd)"
          % (b["K_MC"], b["cycle_floor"], b["se_law"]["C_upper"]))
    print("\n  tau   nhan  chu ky   san truc   se(luat)    BANG")
    for r in b["per_tau"]:
        print("  %5.1f  x%-3d %7.1f   %6.3f%%    %6.3f%%    %6.3f%%"
              % (r["tau"], r["n_multiplier"], r["independent_cycles"],
                 r["axis_floor_rel"] * 100, r["se_rel_from_law"] * 100,
                 r["band_rel"] * 100))
    pc = doc["reading_policy"]["POSITIVE_CONTROL"]
    print("\nPOPULATION = 8 o gate; cbr = %s, bao cao RIENG" % pc["status"])
    sp = doc["reading_policy"]["SECONDARY_shape"]
    print("don dieu   : %s  (%d cap)" % (sp["pass_rule"], sp["n_pairs"]))
    print("\n-> %s" % args.out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""T2 luot 2 -- bo phan quyet tat dinh. NAM trang thai, khong phai hai.

    PASS · FAIL · VACUOUS · INSUFFICIENT_POWER · NOT_EVALUATED

Hai trang thai giua khong duoc doc theo BAT KY chieu nao, ke ca chieu
"khong sao dau" (NT 56). Chung khong phai PASS nhe, cung khong phai FAIL
nhe -- chung la IM LANG.

CUA SO KHA THI cua mot bang +/-b:

    b >= k*se        SAN   -- hep hon nhieu thi gate la tung xu
    b <  |effect|    TRAN  -- rong hon hieu ung thi du doan khong the sai

Ba nhanh, theo DUNG thu tu do, vi mot chan doan co ban hon phai thang:

    floor >= effect   -> INSUFFICIENT_POWER   nhieu >= hieu ung: KHONG bang
                                              nao cuu duoc (cua so rong)
    b     >= effect   -> VACUOUS              bang CHON qua rong: sua duoc
    nguoc lai         -> PASS / FAIL

!! BAC TU DO. `se` uoc tu n seed co df = n-1, va duoi t thi duoi beo hon
   chuan rat nhieu. k=3 voi n=5 cho FAIL gia 3.99% moi phep chu KHONG phai
   0.27% -- lech 15 lan. Nen `band()` BAT BUOC nhan `n_seed` va quy doi k
   qua phan vi t. Bo qua no la mot loi im lang.

`k` KHONG co mac dinh: no la chinh sach (QD-7) va chua duoc ky.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable, Mapping, Sequence

from scipy import stats

READABLE_STATES = ("PASS", "FAIL")
ALL_STATES = ("PASS", "FAIL", "VACUOUS", "INSUFFICIENT_POWER", "NOT_EVALUATED")


def band(*, se: float, k: float, n_seed: int) -> float:
    """Nua do rong cua bang, DA hieu chinh bac tu do.

    `k` phat bieu muc kiem soat sai so MONG MUON theo don vi sigma chuan.
    Voi df huu han, boi so THUC SU dat duoc muc do la phan vi t tuong ung:

        multiplier = t.isf( norm.sf(k), df )

    Nen cung mot `k` cho bang RONG HON khi it seed hon -- dung nhu no phai
    the. Dung `k*se` tho la tu nhan minh dang o df = vo cung.
    """
    n_seed = int(n_seed)
    if n_seed < 2:
        raise ValueError("can >= 2 seed de uoc se (df = n-1)")
    if not math.isfinite(se) or se < 0:
        raise ValueError("se phai huu han va khong am")
    df = n_seed - 1
    mult = float(stats.t.isf(stats.norm.sf(float(k)), df))
    return mult * float(se)


def effective_k(*, k: float, n_seed: int) -> float:
    """Boi so t thuc su dung -- de bao cao, khong de quyet dinh."""
    return band(se=1.0, k=k, n_seed=n_seed)


def required_k(*, n_seed: int, n_tests: int, fwer: float = 0.05) -> float:
    """k (don vi sigma chuan) can de giu FWER Bonferroni tren n_tests phep.

    Bonferroni gia dinh doc lap. Cac phep o day dung chung du lieu nen
    KHONG doc lap; khi do Bonferroni la BAO THU -- an toan nhung co the
    qua chat. Ghi ra de nguoi doc biet chieu cua sai lech.
    """
    alpha = float(fwer) / int(n_tests)
    return float(stats.norm.isf(alpha / 2.0))


def required_multiplier(*, n_seed: int, n_tests: int,
                        fwer: float = 0.05) -> float:
    """Boi so THO (b = m*se) can cho cung muc kiem soat.

    HAI QUY UOC cho chu "k", quy ve nhau nhung tro vao hai dai luong:

        (A) tho    b = m*se           => m phai LON khi n nho
        (B) o day  k = muc kiem soat  => band() tu quy doi qua t

    Doi chieu (kiem bang so): required_multiplier == boi so ma `band()`
    thuc su ap khi dua vao `required_k`. Vi du n=5, K=35: k=3.19 (B) va
    m=7.84 (A) la CUNG mot bang.
    """
    return effective_k(k=required_k(n_seed=n_seed, n_tests=n_tests, fwer=fwer),
                       n_seed=n_seed)


def adjudicate(*, obs: Sequence[float], predicted: float, null: float,
               k: float, signed_band: float | None = None) -> Dict[str, Any]:
    """Phan quyet MOT du doan. Thuan tat dinh.

    ``obs``          quan sat theo SEED (moi phan tu la mot seed).
    ``predicted``    diem du doan, tu artifact 01.
    ``null``         gia tri duoi gia thuyet khong -- xac dinh |effect|.
    ``signed_band``  bang tuyet doi da ky, neu co. Khong co thi dung san.
    """
    vals = [float(v) for v in obs]
    n = len(vals)
    if n < 2:
        return {"state": "NOT_EVALUATED", "why": "can >= 2 seed", "n_seed": n}

    mean = sum(vals) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1))
    se = sd / math.sqrt(n)
    floor = band(se=se, k=k, n_seed=n)
    effect = abs(float(predicted) - float(null))
    b = floor if signed_band is None else float(signed_band)

    out: Dict[str, Any] = {
        "n_seed": n, "df": n - 1, "observed_mean": mean, "sd_between_seed": sd,
        "se": se, "noise_floor": floor, "band_used": b, "effect": effect,
        "predicted": float(predicted), "null": float(null),
        "k_requested": float(k), "k_effective": effective_k(k=k, n_seed=n),
        "deviation": abs(mean - float(predicted)),
    }
    if floor >= effect:
        out["state"] = "INSUFFICIENT_POWER"
        out["why"] = ("san nhieu >= hieu ung: cua so rong, KHONG bang nao "
                      "cuu duoc. Khong doc theo ca hai chieu.")
        return out
    if b >= effect:
        out["state"] = "VACUOUS"
        out["why"] = ("bang DA CHON rong hon hieu ung: du doan khong the sai. "
                      "Sua duoc bang cach siet bang xuong trong cua so.")
        return out
    out["state"] = "PASS" if out["deviation"] <= b else "FAIL"
    return out


def summarize(verdicts: Mapping[str, Any]) -> Dict[str, Any]:
    """Gop ket qua. MAU SO chi dem READABLE.

    Bao cao 'n/N PASS' voi N gom ca VACUOUS la lam loang: mot muc khong the
    sai van chiem mot cho trong mau so va keo ti le len. Nen o day KHONG co
    truong `pass_rate`, va KHONG co `overall_verdict` -- mot dong tong quan
    moi nguoi ta bo qua mau so.
    """
    states = [v["state"] if isinstance(v, Mapping) else str(v)
              for v in verdicts.values()]
    for s in states:
        if s not in ALL_STATES:
            raise ValueError("trang thai la: %s" % s)
    readable = [s for s in states if s in READABLE_STATES]
    return {
        "n_readable": len(readable),
        "n_pass": readable.count("PASS"),
        "n_fail": readable.count("FAIL"),
        "n_vacuous": states.count("VACUOUS"),
        "n_insufficient_power": states.count("INSUFFICIENT_POWER"),
        "n_not_evaluated": states.count("NOT_EVALUATED"),
        "n_total": len(states),
    }


def tau_star_curve(*, taus: Sequence[float], lifts: Sequence[float],
                   lift_min_grid: Sequence[float]) -> Dict[str, Any]:
    """tau*(lift_min) nhu MOT DUONG. `None` = khong dat tren luoi.

    `None` KHAC voi max(taus): "khong dat tren luoi" khong phai "dat o 28".
    Va cam mo rong luoi de di tim tau* (prereg T2-6c).
    """
    pairs = sorted(zip((float(t) for t in taus), (float(v) for v in lifts)))
    out: Dict[str, Any] = {}
    for lm in lift_min_grid:
        hit = next((t for t, v in pairs if v < float(lm)), None)
        out["%g" % lm] = hit
    return {"lift_min_grid": [float(x) for x in lift_min_grid],
            "tau_star_s": out,
            "tau_grid_max": max(float(t) for t in taus) if taus else None,
            "note": ("null = khong dat nguong tren luoi tau. KHONG duoc mo "
                     "rong luoi de di tim tau* (T2-6c).")}

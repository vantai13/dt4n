"""cert/abstain_cost.py -- Lesson 23.6: tham so hoa chi phi abstain.

Cau hoi ma module nay tra loi
------------------------------
Khong phai "fallback nao tot nhat" (do la mot lua chon KE TOAN, NT-v2-1) ma:

    "Voi chi phi fallback bang bao nhieu thi bat certificate la CO LAI?"

Tra loi la mot dai luong duy nhat, do duoc tu twin + certificate, KHONG phu
thuoc fallback nao duoc chon:

    R_neo               = gamma * R|accept + (1 - gamma) * R|reject(twin)   (*)
    R_system(gamma, c)  = gamma * R|accept + (1 - gamma) * c
    Delta               = (1 - gamma) * (c - c*)
    c*(gamma)          := R|reject(twin, gamma)          NGUONG HOA VON
    CO LOI  <=>  c < c*(gamma)

Trung thuc ve muc dong gop (K-D7, Amendment 23-25 muc 6.1)
-----------------------------------------------------------
(*) la DINH LY xac suat toan phan. Do do R_system(gamma, c*) = R_neo la mot
DONG NHAT THUC, dung theo dinh nghia. `G23-32` la kiem tra DUNG CODE, khong
phai mot ket qua khoa hoc. Dong gop nam o ba cho:
   (1) TAI KHUNG cau hoi khong tra loi duoc thanh cau hoi tra loi duoc
   (2) GIA TRI c*(gamma) kem DAI TIN CAY DONG THOI -- so moi, v1 chua co
   (3) DINH VI F1/F2/F3 nhu ba diem tren mot truc lien tuc

Quyet dinh thiet ke -- doc truoc khi sua file nay
--------------------------------------------------
D1  c* duoc tinh TRUC TIEP: sum_b rej_wrong[b] / sum_b n_rej[b].
    CAM dung cong thuc DAO  (R_neo - g*R_acc)/(1-g)  trong duong tinh chinh:
    no chia cho (1-g) nen khuech dai sai so 50x tai g = 0.98, va cho nan tai
    g = 0 (vi R_acc khong xac dinh khi n_accept = 0). Duong dao CHI xuat hien
    trong `inverse_formula_crosscheck()`, va chi tren g <= 0.90 noi
    1/(1-g) <= 10. Day la K-D8 ban siet.

D2  Bootstrap CO DINH NGUONG tau(gamma), khong co dinh coverage. Coverage dao
    dong giua cac draw va PHAI duoc bao cao (khoa `coverage_sd_boot`).
    Gioi han L26 -- ghi ro trong 11-abstain-cost.md.

D3  Moi phep tinh dung `coverage_measured`, KHONG dung `coverage_target`.
    Tai gamma = 0.78, n = 499967: k = floor(0.78*n + 0.5) = 389974, nen
    coverage do duoc la 0.7799994799656778. Sai lech 5.2e-7 nhan voi
    |R_acc - c*| ~ 0.3 cho ~1.5e-7 -- lon hon nguong G23-32 (1e-12) mot tram
    nghin lan. Dung target se lam G23-32 FAIL oan.

D4  Diem so va thu tu hang lay tu `threshold_families.fit_c3_inputs`, dung
    HAM ma `baselines.run_report` goi, chu khong phai chep lai chuoi bon dong.
    Neu chep lai thi mot ngay nao do hai ben lech nhau va doi chung cheo
    C23v2-1 mat het y nghia ma khong ai biet.

D5  Bootstrap bang TRONG SO BOI + nhan ma tran, khong bang gather chi so.
    Day la mot REFORMULATION chinh xac, khong phai xap xi (xem test A9).

D6  `block_curve_stats` dung TONG TIEN TO tren thu tu da sap, khong quet lai
    toan bo hang o moi diem luoi. Tap accept LONG NHAU theo gamma, nen tong
    chi phi la O(n) cho CA luoi thay vi O(n*K). Voi K = 100 va n = 500k day la
    khac biet giua 1 giay va 1 phut moi cell.

Khoa boi
--------
docs/phase-23/00z-amendment-25.md   muc 6 (K-D1..K-D7), muc 7 (K-1..K-8)
docs/phase-23/00za-amendment-26.md  muc 1.5 (K-D8), muc 3 (C23v2-1), muc 5 (K-9..K-11)

KHONG co main()/CLI trong file nay -- viec sinh artifact va Figure 4 thuoc
pham vi luot sau, xem Amendment 23-25 muc 8.
"""

from __future__ import annotations

import subprocess
from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd

from cert import baselines as BL
from cert import fallback as FB
from cert import threshold_families as TF
from cert.go2_simultaneous import critical_values, supt_band
from cert.simultaneous_score import ALPHA

# ---------------------------------------------------------------------------
# 1. Hang so -- MOI bac tu do khoa bang so (NT-v2-3)
# ---------------------------------------------------------------------------

STATUS = "CONFIRMATORY"          # khac 23.5[A]; 23.6 khong phai exploratory

# K-D4: luoi gamma. `np.arange` voi buoc thap phan sinh bui dau phay dong
# (0.06 -> 0.060000000000000005), lam khoa JSON khong on dinh giua cac lan
# chay. Lam tron 10 chu so du de dong bang khoa va khong doi gia tri.
GRID_STEP_LOCKED = 0.02
GRID_STEP_FINE = 0.01            # NT-v2-11: luoi min gap doi, BAO CAO bat buoc
GRID_HI = 1.0                    # gamma = 1.0 BI LOAI (tap reject rong)

N_BOOT = 2000                    # cung cau truc voi 23.5[B]/[C]
SEED_BOOT = 23610
FWER = 0.05
LEVEL = 1.0 - FWER

CONFIG = "C3"
MULTIPLICITY = "bonferroni"
KAPPA_FIT = 1.0                  # gia tri `fit_c3_inputs` dung; xem test A2

SCALES = ("err", "regret")       # K-D1 headline `err`; K-D2 `regret` song song
IDENTITY_TOL = 1e-12             # G23-32
CROSSCHECK_GAMMA_MAX = 0.90      # D1: duong dao chi dung o vung 1/(1-g) <= 10
INVERSE_TOL = 1e-9               # duong dao mat chinh xac; nguong long hon
BAND_TOL = 0.02                  # C23v2-1: mot buoc luoi da khoa


def gamma_grid(step: float = GRID_STEP_LOCKED) -> np.ndarray:
    """Luoi coverage. gamma = 1.0 bi loai khoi luoi (K-D4); ngoai suy CAM."""
    return np.round(np.arange(0.0, GRID_HI, float(step)), 10)


def _git(*cmd: str) -> str:
    try:
        return subprocess.check_output(["git", *cmd], text=True).strip()
    except Exception:
        return "unknown"


def require(d: Mapping[str, Any], key: str) -> Any:
    """Thay cho `d.get(key, <mac dinh>)`.

    Mot default so hoc tren du lieu thieu bien mot loi ON AO thanh mot ket
    luan SAI LANG LE. Neu khoa thieu thi do la bug, khong phai gia tri 0.
    """
    if key not in d:
        raise KeyError("thieu khoa bat buoc %r; co: %s" % (key, sorted(d)))
    return d[key]


# ---------------------------------------------------------------------------
# 2. Dong nhat thuc -- ba ham tam thuong, va do CHINH LA diem
# ---------------------------------------------------------------------------

def risk_system(gamma: float, r_accept: float, c: float) -> float:
    """R_system(gamma, c) = gamma*R|accept + (1-gamma)*c.

    Ham nay TAM THUONG. No ton tai de dong nhat thuc duoc VIET MOT LAN va
    duoc TEST, thay vi duoc go lai o nam cho khac nhau. Xem K-D7: day khong
    phai mot ket qua.
    """
    g = float(gamma)
    return g * float(r_accept) + (1.0 - g) * float(c)


def breakeven_c(r_reject_twin: float) -> float:
    """c*(gamma) = R|reject(twin, gamma).

    Cung tam thuong -- va do la MENH DE TRUNG TAM cua Lesson 23.6: nguong hoa
    von KHONG phu thuoc fallback nao duoc chon. Ham nay khong nhan tham so nao
    lien quan den fallback, va chu ky cua no CHINH LA bang chung cua menh de.
    """
    return float(r_reject_twin)


def delta_vs_anchor(gamma: float, c: float, c_star: float) -> float:
    """Delta = (1 - gamma) * (c - c*). Am <=> co loi."""
    return (1.0 - float(gamma)) * (float(c) - float(c_star))


# ---------------------------------------------------------------------------
# 3. Diem so -- goi DUNG ham ma baselines.run_report goi (D4)
# ---------------------------------------------------------------------------

def fit_score(
    df: pd.DataFrame,
    config: str = CONFIG,
    multiplicity: str = MULTIPLICITY,
) -> tuple[pd.DataFrame, np.ndarray, Dict[str, Any]]:
    """Tra (test_rows, score_C3, fit_cong_khai).

    `TF.fit_c3_inputs` la DUNG ham ma `baselines.run_report` goi o dong dau
    tien. Goi lai no -- thay vi chep chuoi calib/sort/fit/_q_rows -- bao dam ba
    thu giong het: THU TU HANG (`sort_for_stateful`), DIEM SO (`score_C3`), va
    do do QUY TAC PHA HOA khi `_accept_at_coverage` sap xep on dinh. Lech mot
    trong ba thi doi chung cheo C23v2-1 mat y nghia.
    """
    _calib, test, qhat_rows, fit, _q_by_age, _qbar = TF.fit_c3_inputs(
        df, config=config, multiplicity=multiplicity
    )
    score = np.asarray(BL.score_C3(test, qhat_rows), dtype=np.float64)
    public = {k: v for k, v in fit.items() if not k.startswith("_")}
    return test, score, public


def row_losses(test: pd.DataFrame,
               scales: Sequence[str] = SCALES) -> Dict[str, np.ndarray]:
    """Ton that MOI HANG cho hai tac nhan, tren cac thang yeu cau.

      twin : hanh dong cua Advanced Controller (`a_twin`)
      p1   : hanh dong cua F2 STATIC -- duong tinh ngan nhat (`path_static_shortest`)

    `c*` chi dung nhanh `twin_*`. Nhanh `p1_*` chi de DINH VI F2 tren truc c,
    va de doi chung cheo C23v2-1. Menh de "c* khong phu thuoc fallback" van
    dung: khong mot khoa `c_star_*` nao doc `p1_*`.
    """
    n = len(test)
    a_p1 = np.full(n, FB.path_static_shortest(), dtype=np.int64)
    a_tw = test["a_twin"].to_numpy(np.int64)
    out: Dict[str, np.ndarray] = {}
    for scale in scales:
        out["twin_" + scale] = FB.loss_of(test, a_tw, scale).astype(np.float64)
        out["p1_" + scale] = FB.loss_of(test, a_p1, scale).astype(np.float64)
    return out


# ---------------------------------------------------------------------------
# 4. Thong ke du theo block -- xuong song cua bootstrap (D2, D5, D6)
# ---------------------------------------------------------------------------

def accept_counts(grid: np.ndarray, n: int) -> np.ndarray:
    """So hang duoc chap nhan o moi diem luoi.

    Sao chep DUNG quy tac lam tron cua `baselines._accept_at_coverage`:
    `k = floor(coverage * n + 0.5)`, kep vao [0, n]. Neu quy tac nay lech thi
    `coverage_measured` lech, va G23-32 se FAIL vi mot ly do khong lien quan
    gi den khoa hoc.
    """
    k = np.floor(np.asarray(grid, np.float64) * int(n) + 0.5).astype(np.int64)
    return np.clip(k, 0, int(n))


def block_curve_stats(
    block_id: np.ndarray,
    score: np.ndarray,
    grid: np.ndarray,
    losses: Mapping[str, np.ndarray],
) -> Dict[str, Any]:
    """Ma tran (K, n_block) du de tinh MOI diem tren duong o MOI draw.

    Vi sao du: `coverage`, `R|accept`, `c*` deu la TI SO CUA TONG. Mot
    bootstrap draw chi la mot phep cong co trong so tren truc block. Chinh xac
    tuyet doi, khong xap xi.

    D6 -- tong tien to: tap accept LONG NHAU theo gamma (top-k theo cung mot
    diem so), nen `acc[i+1] = acc[i] + doan moi`. Tong chi phi la O(n) cho CA
    luoi. Cach ngay tho (quet lai n hang o moi diem luoi) la O(n*K), cham gap
    ~K lan va cho DUNG CUNG mot ket qua -- xem test A10.
    """
    codes, uniq = pd.factorize(np.asarray(block_id), sort=True)
    codes = codes.astype(np.int64)
    nb = int(len(uniq))
    n = int(len(codes))
    K = int(len(grid))

    order = np.argsort(-np.asarray(score, np.float64), kind="mergesort")
    codes_s = codes[order]
    ks = accept_counts(grid, n)
    if np.any(np.diff(ks) < 0):
        raise ValueError("luoi gamma phai khong giam de dung tong tien to")

    out: Dict[str, Any] = {
        "block_ids": np.asarray(uniq),
        "n_block": nb,
        "n_row": n,
        "grid": np.asarray(grid, np.float64),
        "k_accept": ks,
        "n_rows_b": np.bincount(codes, minlength=nb).astype(np.float64),
        "n_acc": np.zeros((K, nb), np.float64),
        "n_rej": np.zeros((K, nb), np.float64),
    }
    loss_s = {}
    for name, v in losses.items():
        w = np.asarray(v, np.float64)
        out["tot_" + name] = np.bincount(codes, weights=w, minlength=nb)
        out["acc_" + name] = np.zeros((K, nb), np.float64)
        out["rej_" + name] = np.zeros((K, nb), np.float64)
        loss_s[name] = w[order]

    run_cnt = np.zeros(nb, np.float64)
    run_loss = {name: np.zeros(nb, np.float64) for name in losses}
    prev = 0
    for i in range(K):
        k = int(ks[i])
        if k > prev:
            seg = slice(prev, k)
            cs = codes_s[seg]
            run_cnt += np.bincount(cs, minlength=nb)
            for name in losses:
                run_loss[name] += np.bincount(
                    cs, weights=loss_s[name][seg], minlength=nb)
            prev = k
        out["n_acc"][i] = run_cnt
        out["n_rej"][i] = out["n_rows_b"] - run_cnt
        for name in losses:
            out["acc_" + name][i] = run_loss[name]
            out["rej_" + name][i] = out["tot_" + name] - run_loss[name]
    return out


def _ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
    """num/den voi broadcasting, tra nan o cho den == 0.

    Tra 0 se bien 'khong xac dinh' thanh 'bang khong' -- dung loai loi ma
    `require()` chong. nan lan truyen va bi bat o cho no gay hai, thay vi im
    lang tro thanh mot con so trong bang.

    `num` co the la (K, n_boot) con `den` la (n_boot,); np.divide voi `where`
    lo phan broadcasting. Mot phien ban dung `out[ok] = ...` se index SAI truc
    trong dung truong hop nay.
    """
    num = np.asarray(num, np.float64)
    den = np.broadcast_to(np.asarray(den, np.float64), np.broadcast_shapes(
        np.shape(num), np.shape(den)))
    num = np.broadcast_to(num, den.shape)
    out = np.full(den.shape, np.nan, dtype=np.float64)
    np.divide(num, den, out=out, where=den > 0.0)
    return out


def curve(stats: Mapping[str, Any], w: np.ndarray | None = None,
          scales: Sequence[str] = SCALES) -> Dict[str, np.ndarray]:
    """Duong cong cho tap test goc (w = None) hoac cho cac draw (w = trong so).

    D1 -- c* tinh TRUC TIEP:
        c*(gamma) = sum_b rej_twin_x[b] / sum_b n_rej[b]

    Tai gamma = 0 tap reject la TOAN BO tap test, nen c* = R_neo TU DONG,
    khong can nhanh dac biet. Day chinh la ly do D1 tot hon cong thuc dao:
    cong thuc dao cho `0 * nan = nan` o dung diem nay (K-D8).

    Tai gamma = 1 tap reject rong; gamma = 1 khong nam tren luoi (K-D4), va
    neu ai do them vao thi `_ratio` tra nan chu khong nem im lang.
    """
    if w is None:
        red = lambda m: np.asarray(m, np.float64).sum(axis=-1)
    else:
        wv = np.asarray(w, np.float64)
        red = lambda m: np.asarray(m, np.float64) @ wv

    n_tot = red(stats["n_rows_b"])
    n_acc = red(stats["n_acc"])
    n_rej = red(stats["n_rej"])
    out: Dict[str, np.ndarray] = {
        "coverage": _ratio(n_acc, n_tot),                    # D3: DO DUOC
        "n_accept": n_acc,
        "n_reject": n_rej,
    }
    for scale in scales:
        out["r_neo_" + scale] = _ratio(red(stats["tot_twin_" + scale]), n_tot)
        out["r_accept_" + scale] = _ratio(red(stats["acc_twin_" + scale]), n_acc)
        out["c_star_" + scale] = _ratio(red(stats["rej_twin_" + scale]), n_rej)
        out["c_f2_" + scale] = _ratio(red(stats["rej_p1_" + scale]), n_rej)
    return out


# ---------------------------------------------------------------------------
# 5. Bootstrap ghep cap theo block -- trong so boi + nhan ma tran (D5)
# ---------------------------------------------------------------------------

def bootstrap_weights(n_block: int, n_boot: int = N_BOOT,
                      seed: int = SEED_BOOT) -> np.ndarray:
    """Tra W (n_block, n_boot): W[j, b] = so lan block j duoc rut o draw b.

    Bootstrap theo block rut `n_block` block CO HOAN LAI. Tong cac block duoc
    rut BANG tong CO TRONG SO voi trong so la so lan xuat hien. Day la mot
    REFORMULATION chinh xac, khong phai xap xi -- test A9 chung minh bang cach
    so voi phep gather ngay tho.

    Ghep cap: MOI draw dung CUNG mot cot cua W cho MOI gamma va MOI dai luong,
    nen moi so sanh (c_f2 - c*, hoac so gia giua hai gamma) la GHEP CAP hoan
    hao va nhieu chung triet tieu. Ghep cap phai TAT DINH, khong duoc phu
    thuoc so luot rut rng cua tung thu tuc.
    """
    rng = np.random.default_rng(int(seed))
    picks = rng.integers(0, int(n_block), size=(int(n_boot), int(n_block)))
    W = np.zeros((int(n_block), int(n_boot)), dtype=np.float64)
    for b in range(int(n_boot)):
        W[:, b] = np.bincount(picks[b], minlength=int(n_block))
    return W


def bootstrap_curves(stats: Mapping[str, Any], W: np.ndarray,
                     scales: Sequence[str] = SCALES) -> Dict[str, np.ndarray]:
    """Tra dict ten -> (n_boot, K). Mot nhan ma tran cho ca n_boot draw.

    Cac dai luong khong phu thuoc gamma (`r_neo_*`) co dang (n_boot,) va duoc
    giu nguyen chieu do; cac dai luong tren duong co dang (n_boot, K).
    """
    d = curve(stats, W, scales)
    return {k: np.asarray(v).T for k, v in d.items()}


# ---------------------------------------------------------------------------
# 6. Doi chung tu than (Amendment 23-25 muc 6.5) va G23-32
# ---------------------------------------------------------------------------

def partition_identity(pt: Mapping[str, np.ndarray],
                       scale: str = "err") -> Dict[str, Any]:
    """G23-32: R_system(gamma_do, c*) == R_neo tren MOI diem luoi.

    Phep kiem nay bat duoc gi, va KHONG bat duoc gi -- noi ro de khong ai doc
    qua tay:

      BAT DUOC : accept/reject khong phan hoach dung tap test; lech mot hang
                 (`k` sai); dung sai cot ton that; `coverage` khong khop tap
                 accept that su; tron hai thang voi nhau.
      KHONG BAT: sai so lam tron. Ve mat DAI SO day la dang thuc CHINH XAC cua
                 cac tong -- A/n + R/n = (A+R)/n -- nen no chi kiem CAU TRUC,
                 khong kiem SO HOC. Duong doc lap ve so hoc la
                 `inverse_formula_crosscheck`.

    D3: dung `coverage` DO DUOC. Thay bang target cho sai so ~1.5e-7, lon hon
    nguong 1e-12 mot tram nghin lan -- xem test A6.
    """
    g = np.asarray(pt["coverage"], np.float64)
    lhs = g * np.asarray(pt["r_accept_" + scale], np.float64) \
        + (1.0 - g) * np.asarray(pt["c_star_" + scale], np.float64)
    rhs = np.asarray(pt["r_neo_" + scale], np.float64)
    resid = np.abs(lhs - rhs)
    live = np.isfinite(resid)
    worst = float(resid[live].max()) if live.any() else 0.0
    return {
        "scale": str(scale),
        "max_abs_residual": worst,
        "n_points_checked": int(live.sum()),
        "n_points_skipped_undefined": int((~live).sum()),
        "tolerance": IDENTITY_TOL,
        "pass": bool(live.any() and worst <= IDENTITY_TOL),
    }


def inverse_formula_crosscheck(pt: Mapping[str, np.ndarray],
                               scale: str = "err",
                               gamma_max: float = CROSSCHECK_GAMMA_MAX
                               ) -> Dict[str, Any]:
    """Duong DAO doi chieu duong TRUC TIEP -- hai loi tinh doc lap ve so hoc.

        c*_dao(gamma) = (R_neo - gamma * R|accept) / (1 - gamma)

    D1 cam duong nay o duong tinh chinh va cho phep no DUY NHAT o day, tren
    `gamma <= gamma_max` (mac dinh 0.90) noi `1/(1-gamma) <= 10`. Ngoai vung
    do, triet tieu tru khuech dai sai so lam tron toi muc so sanh vo nghia --
    do la ly do ky thuat de cam no, va cung la ly do phai gioi han vung o day.

    Tai gamma = 0 cong thuc dao cho `0 * nan = nan`; diem do bi BO va duoc DEM
    (`n_skipped_undefined`), khong duoc coi la dat.
    """
    g = np.asarray(pt["coverage"], np.float64)
    ra = np.asarray(pt["r_accept_" + scale], np.float64)
    rn = np.asarray(pt["r_neo_" + scale], np.float64)
    direct = np.asarray(pt["c_star_" + scale], np.float64)

    inside = g <= float(gamma_max)
    with np.errstate(invalid="ignore", divide="ignore"):
        inv = (rn - g * ra) / (1.0 - g)
    resid = np.abs(inv - direct)
    live = inside & np.isfinite(resid)
    worst = float(resid[live].max()) if live.any() else float("nan")
    return {
        "scale": str(scale),
        "gamma_max": float(gamma_max),
        "max_abs_diff": worst,
        "n_points_checked": int(live.sum()),
        "n_skipped_undefined": int((inside & ~np.isfinite(resid)).sum()),
        "n_skipped_out_of_range": int((~inside).sum()),
        "tolerance": INVERSE_TOL,
        "pass": bool(live.any() and worst <= INVERSE_TOL),
    }


def self_controls(pt: Mapping[str, np.ndarray]) -> Dict[str, Any]:
    """Bon dang thuc cho khong -- NC23v2-4/5/6 va PC23v2-1."""
    g = np.asarray(pt["coverage"], np.float64)
    r_neo = float(np.asarray(pt["r_neo_err"]).reshape(-1)[0])
    i0 = int(np.argmin(g))                     # diem gamma = 0

    # NC23v2-4: gamma = 0 => tu choi tat ca => c* = R_neo CHINH XAC.
    # Voi D1 dieu nay dung TU DONG. Doi chung nay chinh la thu bat duoc viec
    # ai do doi sang cong thuc dao: khi do c*(0) = nan va nc4 = nan -> FAIL.
    nc4 = float(abs(np.asarray(pt["c_star_err"])[i0] - r_neo))

    # NC23v2-5: gamma = 1 => R_system = R_neo voi MOI c, vi (1-gamma)*c = 0.
    # gamma = 1 KHONG nam tren luoi (K-D4) nen kiem bang dai so truc tiep.
    nc5 = max(abs(risk_system(1.0, r_neo, c) - r_neo) for c in (0.0, 0.5, 1.0))

    # NC23v2-6: c = 0 => R_system = gamma * R|accept (can duoi tam thuong)
    ra = np.asarray(pt["r_accept_err"], np.float64)
    fin = np.isfinite(ra)
    nc6 = float(np.max(np.abs(
        np.array([risk_system(gg, r, 0.0) for gg, r in zip(g[fin], ra[fin])])
        - g[fin] * ra[fin]))) if fin.any() else 0.0

    # PC23v2-1: c = 1 => R_system > R_neo voi MOI gamma < 1.
    # Doi chung DUONG: no phai KICH HOAT. Neu no khong kich hoat lan nao thi
    # phep so sanh dang bi mu, va "khong thay vi pham" khong co y nghia.
    worse = [risk_system(gg, r, 1.0) > r_neo + IDENTITY_TOL
             for gg, r in zip(g[fin], ra[fin])]

    return {
        "NC23v2_4_cstar0_minus_rneo": nc4,
        "NC23v2_4_pass": bool(np.isfinite(nc4) and nc4 <= IDENTITY_TOL),
        "NC23v2_5_gamma1_invariant_to_c": float(nc5),
        "NC23v2_5_pass": bool(nc5 <= IDENTITY_TOL),
        "NC23v2_6_c_zero_lower_bound": nc6,
        "NC23v2_6_pass": bool(nc6 <= IDENTITY_TOL),
        "PC23v2_1_n_worse": int(sum(worse)),
        "PC23v2_1_n_checked": int(len(worse)),
        "PC23v2_1_pass": bool(len(worse) > 0 and all(worse)),
    }


# ---------------------------------------------------------------------------
# 7. K-6 / K-9 / K-10 -- don dieu va so gia
# ---------------------------------------------------------------------------

def monotonicity(grid: np.ndarray, c_star: np.ndarray) -> Dict[str, Any]:
    """K-6: c*(gamma) khong giam.

    Doc dung: day la mot GATE VE CHAT LUONG BO CHON, khong phai mot du doan
    (K-D6). c* tang la CAU TRUC: gamma tang => tap reject thu hep, chi con ca
    KHO NHAT => err|reject tang. Neu do duoc KHONG tang thi certificate xep
    hang ca SAI o vung gamma do.

    Chi so `i_lo`/`i_hi` la chi so TRONG `grid`, de `increment_ci` lay dung
    hai cot cua cung mot ma tran draw.
    """
    c = np.asarray(c_star, np.float64)
    idx = np.flatnonzero(np.isfinite(c))
    viol = [
        {"i_lo": int(a), "i_hi": int(b),
         "gamma_lo": float(grid[a]), "gamma_hi": float(grid[b]),
         "drop": float(c[b] - c[a])}
        for a, b in zip(idx, idx[1:]) if c[b] < c[a]
    ]
    return {
        "n_points_finite": int(len(idx)),
        "n_increments": int(max(0, len(idx) - 1)),
        "n_violations": len(viol),
        "violations": viol,
        "monotone": len(viol) == 0,
    }


def increment_ci(draws: np.ndarray, viol: Sequence[Mapping[str, Any]],
                 level: float = 0.95) -> list[Dict[str, Any]]:
    """K-10: CI ghep cap cua so gia Delta(gamma) = c*(g+h) - c*(g).

    Ghep cap tu dong va HOAN HAO: hai cot cua cung mot HANG `draws` den tu
    CUNG mot tap block duoc rut, nen nhieu chung triet tieu truoc khi lay
    phan vi. Neu tinh CI cua tung diem roi tru thi dai se rong hon nhieu va
    ket luan se sai lech ve phia "khong ket luan duoc".

    Bien mot LAP LUAN ("0.009 duoi mot SD") thanh mot PHEP DO -- nguyen tac da
    lap o 10-go2-simultaneous.md muc 1.2: nguong phai dan tu do phan giai cua
    chinh phep do, khong tu mot hang so tuy y.
    """
    lo_q, hi_q = (1.0 - level) / 2.0, 1.0 - (1.0 - level) / 2.0
    out = []
    for v in viol:
        d = draws[:, int(v["i_hi"])] - draws[:, int(v["i_lo"])]
        d = d[np.isfinite(d)]
        lo, hi = ((float(np.quantile(d, lo_q)), float(np.quantile(d, hi_q)))
                  if d.size else (float("nan"), float("nan")))
        out.append({
            "gamma_lo": float(v["gamma_lo"]), "gamma_hi": float(v["gamma_hi"]),
            "drop": float(v["drop"]),
            "ci_lo": lo, "ci_hi": hi,
            "contains_zero": bool(lo <= 0.0 <= hi),
            "n_draws_finite": int(d.size),
            "sd_boot": float(d.std(ddof=1)) if d.size > 1 else float("nan"),
        })
    return out


# ---------------------------------------------------------------------------
# 8. C23v2-1 -- doi chung cheo voi beneficial_band cua Lesson 23.3
# ---------------------------------------------------------------------------

def crossings(grid: np.ndarray, c_f2: np.ndarray, c_star: np.ndarray
              ) -> list[Dict[str, Any]]:
    """Diem ma (c_F2 - c*) doi dau, noi suy tuyen tinh de lay gamma.

    `baselines.beneficial_band` cung noi suy tuyen tinh (`np.interp` tren luoi
    20001 diem cua sweep), nen hai ben dung CUNG mot phep noi suy. Neu ben nay
    dung noi suy khac thi sai lech se la mot tao tac cua phep noi suy chu
    khong phai mot bug -- va doi chung se do vi ly do sai.
    """
    d = np.asarray(c_f2, np.float64) - np.asarray(c_star, np.float64)
    out = []
    for i in range(1, len(d)):
        a, b = d[i - 1], d[i]
        if not (np.isfinite(a) and np.isfinite(b)) or a == 0.0:
            continue
        if np.sign(a) != np.sign(b):
            t = a / (a - b) if a != b else 0.5
            out.append({
                "gamma_lo": float(grid[i - 1]), "gamma_hi": float(grid[i]),
                "gamma_cross": float(grid[i - 1] + t * (grid[i] - grid[i - 1])),
                "direction": ("F2_becomes_profitable" if a > 0
                              else "F2_becomes_lossy"),
            })
    return out


def band_crosscheck(cross: Sequence[Mapping[str, Any]],
                    band: Mapping[str, Any], grid_hi: float,
                    tol: float = BAND_TOL) -> Dict[str, Any]:
    """C23v2-1: tap diem doi dau phai khop {band_low, band_high} cua v1.

    Hai lesson tinh HAI duong khac nhau tu CUNG du lieu; chung PHAI gap nhau.
    Lesson 23.3 tinh `err_system < R_neo`; Lesson 23.6 tinh `c_F2 < c*`. Hai
    dieu kien nay tuong duong vi Delta = (1-gamma)(c_F2 - c*). Neu hai ben
    khong gap nhau thi mot trong hai co bug -- va day la cach duy nhat de biet.

    Dau mut nam NGOAI luoi (vi du `band_high = 0.99995 > 0.98`) duoc MIEN, va
    viec mien duoc GHI vao `endpoint_out_of_grid`, khong duoc im lang.

    Ban thao dau tien cua Amendment 23-26 chi kiem `band_low` va da BO SOT
    diem doi dau thu hai cua `poisson@0.850` (`band_high = 0.9892`, nam TRONG
    luoi). Doi chung phai phu TOAN BO bien cua doi tuong, khong phai phan dang
    duoc chu y. Do la ly do khoa nay ton tai va vi sao test A13 chot no lai.
    """
    ends = {"band_low": float(require(band, "band_low")),
            "band_high": float(require(band, "band_high"))}
    got = [float(c["gamma_cross"]) for c in cross]
    rows, missed, out_of_grid = [], [], []
    for name, gam in ends.items():
        if gam > float(grid_hi):
            out_of_grid.append({"endpoint": name, "gamma": gam})
            continue
        if not got:
            missed.append({"endpoint": name, "gamma": gam, "nearest": None})
            continue
        j = int(np.argmin([abs(x - gam) for x in got]))
        err = abs(got[j] - gam)
        rows.append({"endpoint": name, "band_gamma": gam,
                     "cross_gamma": got[j], "abs_error": err,
                     "within_tol": bool(err <= tol)})
        if err > tol:
            missed.append({"endpoint": name, "gamma": gam, "nearest": got[j]})
    return {
        "matched": rows,
        "endpoint_out_of_grid": out_of_grid,
        "n_crossings_found": len(got),
        "n_endpoints_in_grid": len(rows),
        "unmatched": missed,
        "tolerance": float(tol),
        "pass": bool(not missed and len(rows) == 2 - len(out_of_grid)),
    }


# ---------------------------------------------------------------------------
# 9. Ket xuat -- mot ban ghi moi diem luoi
# ---------------------------------------------------------------------------

def sweep_records(grid: np.ndarray, pt: Mapping[str, np.ndarray]
                  ) -> list[Dict[str, Any]]:
    """Bien `curve()` thanh danh sach ban ghi ghi duoc ra JSON.

    Ba viec nho nhung deu bat buoc:
      * CA `coverage_target` LAN `coverage_measured` deu duoc ghi (D3). Ghi mot
        cai la mat kha nang truy nguoc khi ai do nghi ngo G23-32.
      * `nan` -> `None`. `json.dumps(float('nan'))` sinh `NaN`, khong hop le
        theo RFC 8259, va nhieu bo doc JSON se tu choi hoac doc sai file.
      * `r_neo_*` la vo huong (khong phu thuoc gamma) nen duoc PHAT tren moi
        dong, de moi dong tu no du de kiem dong nhat thuc.
    """
    def cell(v: Any, i: int) -> Any:
        x = np.ravel(np.asarray(v))
        x = float(x[i] if x.size > 1 else x[0])
        return None if not np.isfinite(x) else x

    fixed = ("coverage", "n_accept", "n_reject")
    return [
        {
            "coverage_target": float(grid[i]),
            "coverage_measured": float(pt["coverage"][i]),
            "n_accept": int(pt["n_accept"][i]),
            "n_reject": int(pt["n_reject"][i]),
            **{k: cell(pt[k], i) for k in pt if k not in fixed},
        }
        for i in range(len(grid))
    ]


# ---------------------------------------------------------------------------
# 10. Chay mot cell
# ---------------------------------------------------------------------------

def run_cell(df: pd.DataFrame, cell: str,
             band: Mapping[str, Any] | None = None,
             n_boot: int = N_BOOT, seed: int = SEED_BOOT,
             scales: Sequence[str] = SCALES) -> Dict[str, Any]:
    """Toan bo Lesson 23.6 cho mot cell. Khong ghi file -- xem ghi chu dau file."""
    test, score, fit = fit_score(df)
    eval_scales, skipped = FB.available_scales(test, scales)
    losses = row_losses(test, eval_scales)
    block_id = test["block_id"].to_numpy()

    grid_l = gamma_grid(GRID_STEP_LOCKED)
    grid_f = gamma_grid(GRID_STEP_FINE)
    st_l = block_curve_stats(block_id, score, grid_l, losses)
    st_f = block_curve_stats(block_id, score, grid_f, losses)
    pt_l = curve(st_l, None, eval_scales)
    pt_f = curve(st_f, None, eval_scales)

    W = bootstrap_weights(st_l["n_block"], n_boot, seed)     # D5, dung chung
    bt_l = bootstrap_curves(st_l, W, eval_scales)
    bt_f = bootstrap_curves(st_f, W, eval_scales)

    # K-D5: dai DONG THOI tren luoi da khoa. Dai tung-diem bao cao KEM, khong
    # thay the: 50 khoang tung-diem 95% cho ky vong 2.5 diem sai ngau nhien.
    bands: Dict[str, Any] = {}
    for scale in eval_scales:
        key = "c_star_" + scale
        d = bt_l[key]
        cols = np.flatnonzero(np.isfinite(d).all(axis=0)
                              & np.isfinite(pt_l[key]))
        sub = d[:, cols]
        sb = supt_band(sub, np.asarray(pt_l[key])[cols], level=LEVEL)
        cv = critical_values(int(len(cols)), FWER)
        bands[key] = {
            **sb,
            "gamma": [float(x) for x in grid_l[cols]],
            "n_points_in_band": int(len(cols)),
            "pointwise_lo": [float(x) for x in np.quantile(sub, 0.025, axis=0)],
            "pointwise_hi": [float(x) for x in np.quantile(sub, 0.975, axis=0)],
            "c_bonferroni": float(cv["c_bonferroni"]),
            "c_sidak": float(cv["c_sidak"]),
            "c_supt_over_bonferroni": float(sb["c_supt"] / cv["c_bonferroni"]),
        }

    mono_l = monotonicity(grid_l, pt_l["c_star_err"])
    mono_f = monotonicity(grid_f, pt_f["c_star_err"])

    return {
        "cell": str(cell),
        "status": STATUS,
        "scale": "err (headline, K-D1); regret reported in parallel (K-D2)",
        "level_tag": "system",
        "rowset": "test rows of %s, n=%d, n_block=%d" % (
            cell, st_l["n_row"], st_l["n_block"]),
        "scales_evaluated": list(eval_scales),
        "scales_skipped": skipped,
        "config": CONFIG, "kappa_fit": KAPPA_FIT, "alpha": float(ALPHA),
        "multiplicity": MULTIPLICITY, "fit": fit,
        "grid_locked_step": GRID_STEP_LOCKED,
        "grid_fine_step": GRID_STEP_FINE,
        "n_boot": int(n_boot), "seed_boot": int(seed),
        "sweep_locked": sweep_records(grid_l, pt_l),
        "identity_G23_32": {s: partition_identity(pt_l, s) for s in eval_scales},
        "inverse_crosscheck": {s: inverse_formula_crosscheck(pt_l, s)
                               for s in eval_scales},
        "self_controls": self_controls(pt_l),
        "supt_bands": bands,
        "monotonicity_locked_K6": mono_l,
        "monotonicity_fine_K9": mono_f,
        "increment_ci_K10": increment_ci(bt_f["c_star_err"],
                                         mono_f["violations"]),
        "crossings_locked": crossings(grid_l, pt_l["c_f2_err"],
                                      pt_l["c_star_err"]),
        "crossings_fine": crossings(grid_f, pt_f["c_f2_err"],
                                    pt_f["c_star_err"]),
        "band_crosscheck_C23v2_1": (
            band_crosscheck(crossings(grid_f, pt_f["c_f2_err"],
                                      pt_f["c_star_err"]),
                            band, float(grid_f[-1]))
            if band is not None
            else {"pass": None, "note": "beneficial_band khong duoc cung cap"}
        ),
        # Gioi han L26 (D2): dai la CO DIEU KIEN theo nguong tau(gamma) uoc
        # luong tren tap test day du. Coverage dao dong giua cac draw; do lech
        # do phai duoc BAO CAO, khong duoc giau.
        "coverage_sd_boot": [float(np.nanstd(bt_l["coverage"][:, i], ddof=1))
                             for i in range(len(grid_l))],
        "provenance": {
            "script": "cert/abstain_cost.py",
            "git_hash": _git("rev-parse", "HEAD"),
            "git_dirty": bool(_git("status", "--porcelain")),
        },
    }

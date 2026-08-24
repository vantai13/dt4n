# 36 -- `decision_error_by_age_by_regime` duoi truc SLA ngoai sinh

Ngay     : 2026-08-24
Lesson   : 23.21i (Viec 1)
Amendment: `A060-amendment-60.md`
Artifact : `results/LIVE/phase-20R/decision_error_by_age_by_regime_slaB.parquet`
           `results/LIVE/phase-20R/decision_error_by_age_by_regime_slaB_report.json`

## 0. Moi truong do -- doc truoc khi so sanh bat ky so nao

```text
python3            -> KHONG co numpy. Khong chay duoc bat ky script nao.
.venv/bin/python   -> numpy 2.2.6, pandas 2.3.3, pyarrow 25.0.1   <- DUNG CAI NAY
```

Moi lenh trong tai lieu nay chay bang `.venv/bin/python`. Ghi ra vi mot lan
chay bang `python3` se that bai voi `ModuleNotFoundError` chu khong phai voi
mot ket qua sai -- nhung ai doc runbook can biet truoc.

## 1. Khong sua mot dong logic nao

`decision_error_v2.py` DA co san co `--calibration`. Manifest ngoai sinh
tuong thich drop-in vi `feasible_cells()` chi can `feasible`, `role`, `mode`,
`rho_bar`, `sigma_rho`, `sigma_max`, `w_loss`, `t_delay_ms`, `t_loss` -- co du.

```bash
.venv/bin/python -m measurements.decision_error_v2 \
  --calibration results/LIVE/phase-20R/sla_manifest_exogenous_S-B.json \
  --run-fixed \
  --out results/LIVE/phase-20R/decision_error_by_age_by_regime_slaB.parquet
```

**Do duoc: 47.8 s, 450 hang.** (Ban `/tmp` doi chung: 54.2 s.)

HANG SO `CALIBRATION` GIU NGUYEN. Doi no = mat doi chung am vinh vien.

## 2. `G23-202` -- NC am. **KHONG PASS nhu da ky. Bao cao nguyen.**

Nguong da ky: `equals == True` tren cot chung.

```text
CU  (results/LIVE/.../decision_error_by_age_by_regime.parquet) : 450 x 22
MOI (chay khong co, /tmp/nc_old.parquet)                       : 450 x 24

chi co o ban MOI : ['w_loss', 'w_loss_source']
chi co o ban CU  : []
cot chung        : 22/22
equals           : False        <-- KHONG dat nguong
```

Du doan hai cot thua da DUNG. Nhung `equals` van `False`. Dao sau:

```text
cot            max|diff|
--------------------------------
err_total      0            <- BIT-EXACT
err_model      0            <- BIT-EXACT
err_stale      0            <- BIT-EXACT
d_sla          0            <- BIT-EXACT
z_*, sigma_*, clip_*, ...   0
rms_e_model    7.77e-16
rms_e_stale    3.11e-15
cov_e          3.19e-16
```

**Moi cot MUC QUYET DINH tai lap BIT-EXACT.** Ba cot lech deu o muc bit cuoi
cua float64 (~1e-15).

Va ban LIVE cu la ban DA TIEN DANG KY:

```text
sha256 tren dia : 5e4d4797a5b5471a93a0eb8898555fd4e682ea33a5356e4b11253deff962596f
prereg 21R      : 5e4d4797a5b5471a93a0eb8898555fd4e682ea33a5356e4b11253deff962596f
KHOP            : True
```

Nen day KHONG phai "nham file". Day dung la hien tuong `L71` da ghi:
*"Nguong NC `1e-9` KHONG dat duoc voi ban luu tru sinh o moi truong khac."*
Ghi lam `L74`, KHONG sua de cho khop.

> **`G23-202`: FAIL theo van ban da ky (`equals == True`).**
> **Ket qua thuc: bit-exact tren 19/22 cot, `<= 3.2e-15` tren 3 cot con lai.**
> Khong dien giai lai nguong. Neu lesson so huu muon mot nguong dung duoc,
> no phai duoc KY LAI thanh `max|diff| <= 1e-12 tren cot chung`, va viec ky
> lai do la mot amendment rieng.

## 3. `G23-203` -- **PASS. Dung bang 0, khong phai "gan 0".**

Ghep cap 450/450 hang, doi truc SLA (`w_loss` noi sinh 9 gia tri -> 5000):

```text
cot            max|diff|      mean CU    mean MOI
────────────────────────────────────────────────────
err_total       0.17136044     0.17396    0.18442
err_model       0.02495984     0.01406    0.01641
err_stale       0.16262550     0.16984    0.17937
d_sla           0.29365462     0.06675    0.01615     <- sup 4 lan
rms_e_model     0.00000000     0.15455    0.15455     <- BAT BIEN TUYET DOI
rms_e_stale     0.00000000     0.89716    0.89716     <- BAT BIEN TUYET DOI
cov_e           0.00000000    -0.00101   -0.00101     <- BAT BIEN TUYET DOI

w_loss CU : [1245.6, 1656.4, 2424.4, 2861.4, 3222.2, 3655.9, 4021.4, 4515.9, 4722.7]
w_loss MOI: [5000.0]
```

Vi sao dung bang 0? Doc ma nguon:

```python
# measurements/decision_error_v2.py, trong run_cell
e_model = d_true[current] - d_fresh[current]      # d = DELAY thuan
e_stale = d_fresh[current] - d_fresh[lag_rows]
```

`e_model` va `e_stale` tinh tren **delay thuan**, khong di qua ham chi phi
`cost = delay + w_loss * loss`. Nen `w_loss` khong co duong nao cham toi
chung. Do la mot bat bien CAU TRUC, khong phai mot trung hop so hoc.

> **He qua cho paper:** hinh phan ra sai so, va con so thu tu trong abstract
> (`MASTER_PLAN` PART VI: ti le `e_model / e_staleness` tai `z` trung vi),
> **MIEN NHIEM voi S14**. Viet duoc ngay, khong phai cho gi.
>
> Day cung la cau tra loi cho cau hoi tu kiem 1: `err_model` la ti le
> QUYET DINH SAI (`a_now != a_truth`) -- di qua `argmin` cua ham chi phi, nen
> `w_loss` doi thi no doi. `rms_e_model` la sai so DELAY -- khong qua ham chi
> phi. Cung ten "model", hai dai luong khac han.

## 4. `G23-204` -- gia thuyet da ky BI BAC BO; dang MANH hon PASS 10/10

### 4.1. Dang da ky: FAIL 4/5

Nguong da ky: tap cell co `d_sla ~ 0` duoi S-B **trung** tap `COLLAPSED`.

```text
d_sla == 0 (S-B, z=0.55): cbr@0.700, cbr@0.850, h2@0.850, h2@0.925,
                          h2@0.960, poisson@0.700, poisson@0.960
COLLAPSED (23.21 S-B)   : h2@0.850, h2@0.925, h2@0.960,
                          poisson@0.925, poisson@0.960

COLLAPSED subset cua d_sla==0 : False  (4/5)
hai tap TRUNG KHIT            : False
chenh (d_sla0 \ COLLAPSED)    : cbr@0.700, cbr@0.850, poisson@0.700
```

Hai cho lech, va **ca hai deu la loi cua gia thuyet, khong phai cua so lieu**:

1. **Ba cell `TRIVIAL` cung cho `d_sla = 0`.** Gia thuyet da ky quen mat
   chung. `TRIVIAL` = khong duong nao vi pham:
   `P(vp|twin) = 0`, `P(vp|dung) = 0`, hieu = 0. Cung mot ly do CAU TRUC voi
   `COLLAPSED` (1 - 1 = 0), chi khac dau mut.
2. **`poisson@0.925` co `d_sla = 0.0003`, khong dung bang 0.** No la
   `COLLAPSED` nhung `S_collapsed = 0.9913`, khong phai 1.0 -- tuc 0.87% thoi
   gian KHONG phai moi duong deu vi pham.

### 4.2. Dang sua lai, do duoc

```text
cell             regime       max|d_sla|  mean_viol  S_collapsed  S_pivotal
cbr@0.700        TRIVIAL        0.000000     0.0000       0.0000     0.0000
cbr@0.850        TRIVIAL        0.000000     0.0000       0.0000     0.0000
h2@0.700         LIVE           0.077299     3.8855       0.8888     0.111235
h2@0.850         COLLAPSED      0.000000     4.0000       1.0000     0.0000
h2@0.925         COLLAPSED      0.000000     4.0000       1.0000     0.0000
h2@0.960         COLLAPSED      0.000000     4.0000       1.0000     0.0000
poisson@0.700    TRIVIAL        0.000060     0.0033       0.0000     0.003300
poisson@0.850    LIVE           0.342826     1.7878       0.0314     0.893210
poisson@0.925    COLLAPSED      0.003007     3.9913       0.9913     0.008690
poisson@0.960    COLLAPSED      0.000000     4.0000       1.0000     0.0000
```

Moi cell co `S_collapsed == 1.0000` chinh xac -> `d_sla == 0.0` chinh xac.
Moi cell co `S_collapsed < 1` -> `d_sla > 0`, va lon dan theo phan du.

**Menh de dung la mot BAT DANG THUC, khong phai mot phep so tap:**

```text
max|d_sla|  <=  S_pivotal          -> 10/10 cell, tren MOI z
```

Chi buoc chan PIVOTAL moi co the doi ket qua SLA. Buoc TRIVIAL cho 0-0, buoc
COLLAPSED cho 1-1; ca hai triet tieu bat ke twin chon duong nao. Nen do lech
SLA bi chan tren boi ti le buoc pivotal. Do la mot chan tren CHAT CHE suy tu
dinh nghia, va no dung ca o cell `poisson@0.925` von pha vo dang nhi phan.

Phan tach hoan toan giua hai lop:

```text
min max|d_sla| tren LIVE       = 0.077299
max max|d_sla| tren KHONG-LIVE = 0.003007
khoang cach                    = 25.7 lan
```

> **`G23-204`: dang da ky FAIL (4/5). Dang sua lai PASS 10/10.**
> Gia tri doi chung cheo VAN CON, va manh hon: hai script khac nhau, hai
> duong code khac nhau -- `decision_error_v2` (Phase 20R) va `sla_exogenous`
> (Lesson 23.21) -- dong y voi nhau tren mot BAT DANG THUC DINH LUONG, chu
> khong chi tren mot phep phan loai nhi phan.

Day la cau tra loi cho cau hoi tu kiem 4: khi `G23-204` fail, hai giai thich
thay the la (a) mot trong hai script tinh sai, (b) gia thuyet sai. Doi chung
giet (a): neu mot script sai thi bat dang thuc `d_sla <= S_pivotal` se bi vi
pham o dau do -- no khong bi vi pham o 10/10 cell tren 9 muc `z`. Con lai (b),
va (b) da duoc xac nhan bang co che (`TRIVIAL` cung cho hieu 0).

## 5. Lo hong goc -- lon hon ban than file parquet

```python
# test/test_no_stale_axes.py  (truoc amendment 23-60)
def _live_json_files() -> list[str]:
    return sorted(glob.glob(os.path.join(LIVE, "**", "*.json"), recursive=True))
    #                                                 ^^^^^^  CHI JSON
```

MOI file `.parquet` trong `LIVE/` deu khong bi kiem. Do la ly do goc khien
loi song sot -- khong phai vi `LEGACY_EXEMPT` viet sai, ma vi cai chan
**khong nhin thay** parquet.

### Mot dinh chinh voi ho so ky thuat

Huong dan noi "parquet khong mang duoc metadata tuy y". **Do duoc, dieu do
chi dung mot nua:**

```text
truth_table.parquet                  -> ['pandas', 'phase', 'truth_field', 'truth_field_note']
decision_error_by_age_by_regime.parquet -> ['pandas']
```

`build_truth_table.py` DA ghi metadata tuy y qua `pyarrow`
(`replace_schema_metadata`). Nen nhung parquet di qua `pandas.to_parquet`
moi khong mang duoc. Chon sidecar VAN la lua chon dung -- vi no khop mau da
co cua Phase 21R va khong bat moi builder doi sang pyarrow -- nhung ly do la
NHAT QUAN, khong phai BAT KHA THI. Ghi ra de lan sau khong ai loai bo phuong
an nhung o mot tien de sai.

## 6. `G23-205` -- PASS, va da DO dung mot lan

`test_every_live_parquet_has_a_validity_sidecar`: moi `.parquet` trong `LIVE/`
phai co `<ten>_report.json` mang `validity`.

Doi chung duong da chay:

```text
giau tam truth_table_report.json  -> DO:
    "parquet trong LIVE/ khong co sidecar _report.json mang validity:
       phase-20R/truth_table.parquet"
tra lai                           -> XANH
```

`truth_table` nhan vai tro `ROLE_MEASURES`, khong phai `AXIS_FREE`: no la
DAU VAO cua ca hai truc, khong phai dau ra, nen no khong cho `approved_for_live`
nao ca. Da kiem bang quet AST: `build_truth_table.py` khong cham
`sawtooth_age_steps` / `D_SYNC` / `cert.freshness_requirement`, nen vai tro
`MEASURES` la hop le chu khong phai mot loi khai.

## 7. Vai tro truc thu ba

```python
ROLE_CONSUMES  = "consumes_axis"
ROLE_MEASURES  = "measures_axis"
ROLE_AXIS_FREE = "aoi_axis_free"     # MOI (amendment 23-60)
```

`decision_error_by_age_by_regime` khong CONSUMES truc AoI (luoi z co dinh),
khong MEASURES truc AoI, nhung CO CONSUMES truc SLA. `LEGACY_EXEMPT` la mien
tru TOAN PHAN trong khi ly do mien tru chi dung cho MOT truc -- dung lo do
da cho file nay song o `LIVE/` voi truc S14 suot 5 lesson.

Mot dinh chinh nho voi ban patch trong huong dan: no viet
`assert v["aoi_axis"].get("z_grid_s")` -- se DO voi luoi z RONG. Ma luoi rong
chinh la truong hop cua 14 artifact `sla_exogenous` (chung chay tren
`ar1_matrix`, khong sinh z bao gio). Da doi thanh `assert "z_grid_s" in ...`.

## 8. Trang thai file

```text
HA   results/SUPERSEDED/phase-20R/decision_error_by_age_by_regime.parquet
TAO  results/LIVE/phase-20R/decision_error_by_age_by_regime_slaB.parquet
     results/LIVE/phase-20R/decision_error_by_age_by_regime_slaB_report.json
     results/LIVE/phase-20R/truth_table_report.json
```

Hai script tieu thu (`h9_separability.py`, `plot_decision_error_v2.py`) da
duoc tro sang `SUPERSEDED/` de chung chay NGUYEN, bit-identical. Chung VAN
dung tren truc SLA da DEPRECATED -- ghi lam `L76`, thuoc lesson so huu hinh
do, khong sua lut o day.

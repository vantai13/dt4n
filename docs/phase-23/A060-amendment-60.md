# AMENDMENT 23-60 -- Cai chan khong NHIN THAY artifact: parquet vo chu va PASS RONG

Ngay ky : 2026-08-24
Lesson  : 23.21i (Viec 1 + Viec 2)
Loai    : SUA CAI CHAN + VAI TRO TRUC MOI
Prereq  : amendment-59 (`dcd6e53`), amendment-57 (truc SLA ngoai sinh S-B)

## 0. Doi he ten file amendment: `00z*` -> `A0NN-`

`docs/phase-23/00zzv-amendment-59.md` la muc thu 22 cua day `00z*` cap phat
theo CHU CAI. Con dung BON cho: `00zzw`, `00zzx`, `00zzy`, `00zzz`. Amendment
thu 64 KHONG CO TEN.

Tu amendment 60 tro di dung `A0NN-amendment-NN.md` (ba chu so -> toi 999).
Sap xep lexicographic van dung vi `00z*` < `A0*`. Tai lieu DA KY khong doi
ten -- sua duong CODE tuong lai, khong sua BANG CHUNG qua khu.

Ghi lam `L73`. Cung lop loi voi `L21` (va cham ID), `L29`/`L31`, `L67`
(deadlock so sach): mot he danh so khong duoc thiet ke de lon.

## 1. Ky truoc khi chay -- hai cai chan, MOT ho loi

Viec 1 va Viec 2 khong phai hai viec. Chung la mot cau: **cai chan khong
nhin thay artifact no phai chan.**

```text
Viec 1  test_no_stale_axes._live_json_files() glob "**/*.json"
        -> MOI .parquet trong LIVE/ khong bao gio bi kiem.
        -> decision_error_by_age_by_regime.parquet song o LIVE/ voi truc SLA
           DEPRECATED (S14) tu Lesson 23.17 den 23.21 ma khong test nao keu.

Viec 2  test_pending_artifacts_declare_what_they_wait_for:
            if "validity" not in payload: pytest.skip(...)
        -> muon THOAT test chi can KHONG viet `validity`.
        -> do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung
           duong do. PASS RONG (vacuous pass), cung lop loi voi `R1`.
```

Ca hai deu la cai chan chua bao gio DO. Luat cua repo nay (bang `DC15..DC20`
trong `31-exogenous-sla.md`): moi test phai do it nhat MOT lan.

## 2. Vai tro truc thu ba: `ROLE_AXIS_FREE = "aoi_axis_free"`

`measurements/validity.py` hom nay co dung hai vai tro:

```text
ROLE_CONSUMES  artifact DUNG truc z   -> phai cho approved_for_live.aoi_axis
ROLE_MEASURES  artifact DO chinh truc z -> mien duyet (khong the bi lam sai
               boi cai no dang do)
```

`decision_error_by_age_by_regime.parquet` KHONG thuoc cai nao:

- khong CONSUMES truc AoI: no chay tren LUOI z CO DINH tien dang ky
  `(0, .05, .1, .2, .3, .55, 1, 2, 4)` s, khong goi bo sinh AoI nao;
- khong MEASURES truc AoI: no khong do AoI;
- NHUNG no CONSUMES truc SLA (`d_sla`, `err_total` deu qua `w_loss`).

Ep no vao `ROLE_MEASURES` se FAIL DUNG: quet AST thay
`decision_error_v2.py:22` co `from measurements.decision_error import
check_z_grid, sawtooth_age_steps`, va `sawtooth_age_steps` nam trong
`forbidden`. Cai chan hoat dong dung; thieu la TU VUNG.

```text
ROLE_AXIS_FREE  artifact KHONG dung truc AoI (luoi z co dinh, tien nghiem)
                nhung CO dung truc SLA. Khong cho approved_for_live.aoi_axis,
                NHUNG PHAI cho approved_for_live.sla_axis.
```

Vi sao can vai tro rieng thay vi mot muc `LEGACY_EXEMPT`: `LEGACY_EXEMPT` la
MIEN TRU TOAN PHAN, trong khi ly do mien tru chi dung cho MOT truc. Dung loi
nay da cho `decision_error_by_age_by_regime.parquet` song o LIVE/ voi truc
SLA DEPRECATED suot 5 lesson.

Day la nua con lai cua amendment 23-45a: bien ly do NGAM cua `LEGACY_EXEMPT`
thanh vai tro TUONG MINH.

## 3. Sidecar: parquet khong mang duoc `validity`

Da kiem: parquet cua repo nay chi co key metadata `b'pandas'`; `pandas`
khong ghi metadata tuy y mot cach on dinh. Nen KHONG mo rong glob sang
parquet.

Thay vao do: moi `.parquet` trong `LIVE/` phai co sidecar
`<ten>_report.json` mang `validity`. Day la mau DA CO cua Phase 21R (moi
`calib_set_*.parquet` co `calib_set_*_report.json`, va chinh report json do
la thu `test_no_stale_axes` kiem). Chi la chua ap cho 20R.

Test moi: `test_every_live_parquet_has_a_validity_sidecar`.

## 4. Sua DU LIEU, khong sua DUONG CODE

`decision_error_v2.py` DA co san co `--calibration`. Khong sua mot dong logic
nao; chi nap file khac.

HANG SO `CALIBRATION` GIU NGUYEN tro toi duong CU. Chay KHONG co co phai tai
tao ban cu -- do la doi chung am muc duong ong, cung logic da dung cho `--sla`
trong `cert/eight_cell_sweep.py:450`. Doi hang so = mat doi chung do VINH VIEN.

File moi, khong ghi de (`MAP.md` muc 4):

```text
GIU  results/SUPERSEDED/phase-20R/decision_error_by_age_by_regime.parquet
TAO  results/LIVE/phase-20R/decision_error_by_age_by_regime_slaB.parquet
```

## 5. Thu tu bat buoc cho Viec 2: SUA TEST TRUOC

```text
[1] SUA test  -> test phai DO 16 lan  -> GHI SO
[2] Roi moi sinh validity -> test xanh dan
```

Lam nguoc (sinh truoc, sua test sau) thi KHONG BAO GIO thay test do, va
khong biet no co suc phan biet hay khong. Day la ky luat doi chung duong
(`PC`) ap cho chinh bo test: *"Mot cong cu khong bao gio tra COLLAPSED thi
viec no tra LIVE khong co nghia."*

`PENDING_NO_VALIDITY_GRANDFATHERED` khoi tao RONG va CHI duoc ngan di.

## 6. Gate mo trong amendment nay

```text
G23-202  NC am: chay khong co -> tai tao ban cu tren COT CHUNG. equals == True
G23-203  rms_e_model / rms_e_stale / cov_e bat bien qua doi truc SLA.
         Nguong da ky: max|diff| == 0.0 (KHONG phai "gan 0")
G23-204  Doi chung cheo: tap cell co d_sla ~ 0 duoi S-B TRUNG tap COLLAPSED
         cua sla_exogenous_S-B.json. Nguong: >= 5/5
G23-205  test_every_live_parquet_has_a_validity_sidecar xanh
G23-206  DOI CHUNG DUONG: sau khi patch test, chay TRUOC khi sinh validity
         -> phai DO. Nguong: >= 16 fail. GHI LAI SO.
G23-207  15 file (14 nhom A + 1 nhom B) promote len LIVE/, test xanh
G23-208  1 file nhom C ha xuong SUPERSEDED/, co ly do bang van ban
G23-209  PENDING/ RONG sau lesson nay. Nguong: 0 file
```

`G23-203` la gate quan trong nhat ve NOI DUNG: neu no PASS, hinh phan ra sai
so va con so thu tu trong abstract (`MASTER_PLAN` PART VI, ti le
`e_model / e_staleness` tai `z` trung vi) MIEN NHIEM voi S14.

`G23-206` la gate quan trong nhat ve PHUONG PHAP.

## 7. Du doan phai bao cao NGUYEN neu sai

Du doan: ban LIVE cu thieu hai cot `w_loss`, `w_loss_source` ma ban chay lai
CO -> bang chung thu hai rang ban LIVE cu duoc sinh boi mot PHIEN BAN CODE
CU. Neu dung: ghi `L73`/`L74`, KHONG sua de cho khop.

Neu `G23-204` FAIL: KHONG duoc dien giai lai nguong. Hai giai thich thay the
phai duoc giet rieng (xem muc 8 cua `36-decision-error-sla-axis.md`).

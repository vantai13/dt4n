# AMENDMENT 23-75 -- SUA KHIEM KHUYET NGUON DU LIEU CUA LESSON 23.24

Ngay ky : 2026-08-27

Moc     : sau `744412c` (promote artifact 23.24), TRUOC khi bat ky ai trich
          dan so cua Lesson 23.24

Loai    : SUA KHIEM KHUYET THI HANH. KHONG doi mot dai nao. KHONG doi mot
          phan quyet nao. CHAY LAI cung 4 gate tren du lieu dung.

Ngan sach: KHONG doi. Van 4 gate `G23-297..300`.

## 1. Khiem khuyet  (`L132`)

`cell_matrices.cell_matrices()` co hai mac dinh nguy hiem:

```python
SLA_CALIB = "results/LIVE/phase-20R/sla_calibration.json"     # dong 62
def cell_matrices(tt, ..., w_loss_override: float | None = None,
                  calibration_path: str = SLA_CALIB, ...):    # dong 182-183
```

`cert/action_pruning.py` ban dau KHONG truyen ca hai. Nen Lesson 23.24 chay
tren truc SLA `self_calibrated` da DEPRECATED (`S14`), khong phai truc ngoai
sinh da duyet.

Do duoc tren chinh hai file:

```text
sla_calibration.json           poisson@0.925  w_loss = 3222.244681647411
sla_manifest_exogenous_S-B     poisson@0.925  w_loss = 5000.0
                               ti so = 1.551719   nghich dao = 0.644446
```

Chi phi la `c = delay + w_loss * loss` (`measurements/decision_error_v2.py:204`),
va `w_loss` duoc chon o dong 262 cua cung file:

```python
w_loss = float(w_loss_override) if w_loss_override is not None else float(cal_cell["w_loss"])
```

Nen ca thang chi phi -- va do do `s`, `q_hat`, `m_hat` -- bi co lai 0.6445 lan.

Bang chung doi chieu: `S0_K4` (khong cat, `alpha/3`, `selective`, `kappa=0.5`,
cung cell, cung 4 bin) DUNG RA la chinh `C3` cua Lesson 23.23. Ban VOID cho
`q_hat` bang 0.60--0.66 lan `C3`. Va
`results/LIVE/phase-21R/calib_set_poisson_0.925_U3_measured_v7_report.json`
khai ro `w_loss = 5000.0`.

## 2. Xu ly artifact

```text
results/LIVE/phase-23/action_pruning.json
  -> results/SUPERSEDED/phase-23/action_pruning_VOID_wloss_defect.json
     voi khoi `VOID` gan trong file.

Nhan la VOID, KHONG phai MISS va KHONG phai HIT: no chay tren du lieu sai
truc, nen no khong phat bieu duoc dieu gi ve the gioi.

`G23-297..300` GIU NGUYEN ID va GIU NGUYEN DAI. Day la lan thi hanh THU HAI
cua CUNG BON gate, khong phai bon gate moi. `A071` R1 khong bi vi pham:
ngan sach van la 4. Chay lai mot gate tren du lieu dung khong tieu them ngan
sach -- neu no tieu, thi luat se thuong cho viec khong sua loi.
```

Tien le: `results/LIVE/phase-23/g23_242_rerun_diff.json`.

## 3. Sua ma

`action_pruning.build_base()` phai truyen TUONG MINH ca hai:

```python
CMX.cell_matrices(tt, mode=MODE, rho_bar=RHO_BAR, axis=AXIS,
                  aoi_profile=AOI_PROFILE,
                  calibration_path=SLA_MANIFEST,
                  w_loss_override=resolve_w_loss())
```

## 4. Quy tac moi R6 -- `validity` phai DOC, khong duoc NHAN  (`L134`)

Artifact VOID khai `sla_axis = exogenous_g114_S-B` va `w_loss = 5000.0`
trong khi du lieu dung `sla_calibration.json` va `3222.24`. **Artifact khai
mot truc no KHONG dung.**

Nguyen nhan la kien truc, khong phai so suat:

```python
validity_block(aoi_generator=AOI_V7, z_edges=Z_EDGES_V7,
               sla_path=SLA_MANIFEST, w_loss=W_LOSS)
#                       ^^^^^^^^^^^^          ^^^^^^^
#             nhan LOI KHAI lam THAM SO, khong doc tu du lieu
```

Mot khoi `validity` nhan loi khai lam tham so thi VE NGUYEN TAC khong the
phat hien lech -- no chi chep lai dieu nguoi goi noi. Cung lop benh voi
`L101` / `L119` / `A073` muc 2: **mot co che khong the kich hoat**. Nghiem
trong vi `validity_block` chinh la hang phong thu ma `S12`/`S14` sinh ra de
dung, va no vua de lot dung loai loi no ton tai de bat.

```text
R6  Moi gia tri trong `validity` ma du lieu CO THE tu khai thi PHAI doc tu
    du lieu, khong nhan lam tham so:
      w_loss      <- nguon SLA THUC SU duoc truyen (`_load_cell(...)["w_loss"]`)
      sla_axis    <- `calibration_path` THUC SU duoc truyen
      aoi_profile <- tham so thuc su dung de dung `y_hat`
    Tham so chi dung cho thu du lieu khong tu biet (vi du `axis_role`).

    Thi hanh toi thieu, cho moi artifact moi: in CA HAI duong doc lap
    (`config.w_loss_used` doc tu nguon, va `validity.w_loss` nhan tu tham so)
    va co mot test doi chung khop. Hai duong cung chi mot so thi moi bat
    duoc lech.
```

`action_pruning.py` thi hanh R6 bang `resolve_w_loss()`: doc tu manifest bang
`_load_cell`, doi chieu voi hang so `W_LOSS`, NEM neu lech.

R6 chua duoc ap nguoc cho artifact cu -- do se la `A071` N1 (hoi to). No ap
tu artifact moi tro di.

## 5. Pham vi da tuyen -- ho so AoI  (`L133`)

Sau khi sua `w_loss`, `q_hat` hai lesson da gan nhau nhung `acceptance` van
lech ~3 diem (0.4264 vs 0.3955). Nguon la ho so AoI:

```text
Chuoi chung nhan song (23.21--23.23):
    calib_set_..._U3_measured_v7.parquet, khai `aoi_profile = U3`
    `y_hat` dung bang `y_hat_rho_shift` (`build_calib_set_v3.py:360`)

Lesson 23.24:
    `aoi_profile = "U0"`; `cell_matrices.py:218` GHIM CUNG
    `yh.append(y_hat_row_shift(arr["c_fresh"], old))`
```

`cell_matrices` KHONG co nhanh `rho_shift`, nen no VE MAT CAU TRUC khong the
sinh ra `U3`. Day khong phai loi tham so ma la gioi han cua module tang day.

```text
TUYEN PHAM VI (khong phai loi, khong phai no):
  Moi ket luan cua Lesson 23.24 ve pruning do tren ho so AoI DONG NHAT (U0).
  Chuoi chung nhan chinh chay tren U3. CHUA kiem tren U3.

KHONG sua `cell_matrices` -- module tang day, nhieu artifact da dong phu
thuoc. `A071` R2: tuyen pham vi thay vi mo nhanh. Ghi `L133`.
```

## 6. Anh huong -- da chay thu, ca hai phia

```text
                       VOID (3222.24)   SONG (5000.0)   dai            phan quyet
M-233 tap CAT          {P2}             {P2}            == {P2}        DAT, khong doi
M-234a ti so q_hat     0.923259         0.923007        [0.88, 0.94]   DAT, khong doi
M-234b Delta tong      +0.039508        +0.042714       [+0.01,+0.05]  DAT, khong doi
M-235 budget_share     1.003850         0.994144        >= 0.90        DAT, khong doi
NC ve (ii) Delta err   -0.091538        -0.093702       >= +0.02       MISS, khong doi
NC ve (iii) chan       DAT              DAT             --             DAT, khong doi
-----------------------------------------------------------------------------------
nhanh (i) rang buoc    -0.000300        +0.000152       (khong ky)     ★ DOI DAU
constraint_share       -0.007598        +0.003561       (khong ky)     ★ DOI DAU
```

**BON PHAN QUYET GATE KHONG DOI.** Ket luan khoa hoc cua Lesson 23.24 dung vung.

**PHAI RUT** cau sau trong `52-action-pruning.md`:

> "constraint_share AM. Don khong gian hanh dong, tu no, khong mua duoc
> acceptance -- no mua mot luong AM rat nho."

Do la HIEN VAT cua `w_loss` sai. Cau dung lai sach hon: kenh rang buoc dong
gop `+0.36%`, khong phan biet duoc voi 0; kenh ngan sach dong gop `99.41%`.

## 7. `viol|accept` -- mot truc KHONG AI KY DAI  (`L135`)

`A074` ky dai cho `acceptance`, ti so `q_hat`, `budget_share`, `Delta err`.
KHONG ai ky dai cho `viol|accept`. Nhung no nam san trong artifact:

```text
S0_K4  (K=4, alpha_each 0.033333)   viol|accept = 0.100037
S1_K3  (K=3, alpha_each 0.050000)   viol|accept = 0.107425
S2_K2  (K=2, alpha_each 0.100000)   viol|accept = 0.119936
```

Tang DON DIEU theo bac thang cat. Co che ro: `alpha_each` noi -> `q_hat` hep
-> nhan them nhung hang sat bien -> ti le vi pham trong tap nhan tang.

### Mot dieu chinh ve cach doc

Ban thao de nghi doc so nay la "vuot `alpha` -> MAT BAO DAM". Cach doc do
PHAI can than, vi hai ly do do duoc:

```text
(1) `alpha` la ngan sach mat-bao-phu CUA BANG CONFORMAL, cham TREN CALIB va
    theo tung slot. `viol|accept` la mot dai luong CO DIEU KIEN tren viec
    NHAN, cham tren TEST. Hai doi tuong khac nhau. "viol|accept > alpha"
    KHONG tu dong la mot bao dam bi pha.
(2) `S0_K4` -- cau hinh KHONG cat gi -- da o 0.100037, tuc da o dung bien
    alpha truoc khi cat bat ky thu gi. Nen khong doc duoc thanh "viec cat
    lam vo mot bao dam von dang giu".
```

Cau doc duoc, va van la cau dang gia:

> Cat hanh dong chet mua `+4.27%` acceptance va tra bang `viol|accept` tang
> tu `0.1000` len `0.1074` (`+7.4%` tuong doi). Day khong phai mot mon mien
> phi ma la mot GIAO DICH CO GIA DO DUOC. Va toan bo giao dich nam o kenh
> ngan sach `alpha` (`99.41%`), khong o viec don khong gian hanh dong
> (`0.36%`).

```text
KY LUAT: day la quan sat POST-HOC. Khong dai nao duoc ky cho `viol`. No vao
doc 52 voi nhan [MO TA] va KHONG duoc dem la mot `CL-*` moi. Muon phat bieu
trong paper thi phai tien dang ky o mot lesson sau. Ghi `L135`.
```

`A074` muc 6 K1 du kien cau "... **ma khong mat bao dam nao**". Ve in dam do
KHONG duoc phat bieu: chua ai do bao dam theo mot dai da ky. Va `G23-300`
van FAIL, nen K1 van khong duoc phat bieu -- muc nay khong doi dieu do.

## 8. Pham vi va gioi han cua chinh amendment nay

```text
N1  Amendment nay KHONG noi rong mot dai nao, KHONG them gate, KHONG doi
    hang so. No sua NGUON DU LIEU va chay lai.

N2  Viec bon phan quyet khong doi la mot KET QUA, khong phai mot ly do de
    coi nhe khiem khuyet. Neu ti so `w_loss` la 3 thay vi 1.55, mot trong
    cac dai da co the lat. Khong duoc dung "may la khong doi" lam tien le.

N3  R6 chi ap tu artifact moi tro di (`A071` N1 cam hoi to). Ra soat artifact
    cu xem cai nao khai truc sai la mot nhanh RIENG, khong mo o day
    (`A071` R2). Ghi vao `BACKLOG.md`.

N4  `L133` (U0 vs U3) la PHAM VI DA TUYEN, khong phai no ky thuat da tra.
    Moi phat bieu ve pruning gioi han o ho so AoI dong nhat.
```

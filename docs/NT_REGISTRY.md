# SO DANG KY DINH DANH

Ly do ton tai: mot chi dan dau vao da de xuat `G-L27--G-L30` va `NT56` trong
khi cac dinh danh do DA CO NGHIA DA KY; `docs/phase-G/17-amendment-G-A005-
reclassification.md:41` phai cap lai `G-L31--G-L34` va `NT59`. Cung loai su
co lap lai o Phase T2 voi quy mo lon hon. So nay chan no bang co che thay vi
bang tri nho.

## Quy tac

```text
1. Moi ID chi duoc DINH NGHIA o DUNG MOT cho.
2. ID da cap KHONG BAO GIO duoc tai su dung cho nghia khac, ke ca khi bi rut.
3. ID moi cap tu so ke tiep trong so nay, KHONG tu tri nho.
4. Nguon ngoai workspace -> trang thai EXTERNAL. KHONG duoc tai dung noi dung
   tu tri nho (docs/phase-D/02-limits-addendum.md:88).
5. Moi ID xuat hien trong repo phai co mot dong o day. `tools/lint_identifiers.py`
   chan o CI.
```

Bang nay duoc dung tu `grep` tren repo, khong tu mot bang cho san. Cot "Nguon"
la file:dong DA KIEM. ID co trong repo nhung khong tim duoc dong dinh nghia
duoc ghi `USED_NO_DEF` -- do la NO KY THUAT, khong phai loi cua nguoi doc.

## ACTIVE -- co dinh nghia trong workspace

| ID | Nguon dinh nghia | Noi dung |
|---|---|---|
| NT 49 | docs/phase-23/A077-amendment-77.md:30 | cam RUT ket qua; chi duoc doi nhan |
| NT 50 | docs/phase-23/00zzu-amendment-58.md:172 | doi mot gia tri NGUON phai xu ly moi truong phai sinh; xoa theo NGHIA khong theo TEN |
| NT 51 | docs/phase-23/A063-amendment-63.md:47 | chan doan phai bat bien qua doi truc |
| NT 53 | docs/phase-D/02-limits-addendum.md:38 | positive control cho chinh ESTIMATOR, tach khoi positive control cho he thong |
| NT 55 | docs/phase-G/63-prereg-g3a-omega-positive-control.md:142 | mot doi chung chi hop le trong dung cau hinh no duoc do |
| NT 56 | docs/phase-D/02-limits-addendum.md:57 | power cua doi chung phai chung minh truoc khi doc phep so; nhieu hon nguong = INSUFFICIENT_POWER |
| NT 57 | docs/phase-D/02-limits-addendum.md:63 | gate phai dat tren chinh thong ke ma phan quyet doc, khong dung proxy |
| NT 58 | docs/phase-D/02-limits-addendum.md:71 | audit luong thong tin truoc khi chia mau |
| NT 59 | docs/phase-D/02-limits-addendum.md:80 | power phai chay toan bo pipeline duoc trien khai |
| NT 63 | docs/phase-L2/99-gate-decision.md:41 | ky luat pham vi (nhom voi 64/65) |
| NT 64 | docs/phase-L2/01-additivity-already-measured.md:29 | truoc khi xay mot phep do, grep repo bang it nhat ba cach goi: ten khai niem, ten gate, cong thuc |
| NT 65 | docs/phase-L2/99-gate-decision.md:41 | dat ten estimand (nhom voi 63/64) |
| NT-L22 | docs/phase-T/00t-amendment-19.md:70 | hieu ung goi la "dong luc" phai scale theo truc dong luc |

## USED_NO_DEF -- co dung trong repo, chua dinh vi duoc dong dinh nghia

Khong duoc suy noi dung tu ten. Muon dung phai tim nguon truoc, hoac viet
noi dung tran khong kem ID.

| ID | Vi du su dung |
|---|---|
| NT 21 | docs/phase-23/00v-amendment-21.md:259 |
| NT33 | measurements/aoi_decompose.py:438 |
| NT 36 | docs/phase-L/00-preregistration.md:106 |
| NT 39 | docs/phase-L/00-preregistration.md:77 |
| NT 41 | test/test_estimator_lag_lo.py:5 |
| NT 44 | docs/phase-23/00zzh-amendment-49b.md:84 |
| NT48 | docs/phase-23/16-eight-cell-confirmation.md:85 |
| NT 52 | docs/phase-23/MASTER_PLAN_v8-closeout-addendum.md:17 |
| NT-L10 | docs/phase-T/00o-amendment-14.md:53 |
| NT-L14 | docs/phase-T/00o-amendment-14.md:102 |
| NT-L15 | docs/phase-T/00o-amendment-14.md:105 |
| NT-L16 | docs/phase-T/00o-amendment-14.md:108 |
| NT-L17 | docs/phase-T/00r-amendment-17.md:77 |
| NT-L18 | docs/phase-T/00r-amendment-17.md:81 |
| NT-L19 | docs/phase-T/00r-amendment-17.md:84 |
| NT-L20 | docs/phase-T/00s-amendment-18.md:86 |
| NT-L21 | docs/phase-T/00s-amendment-18.md:89 |
| NT-L23 | docs/phase-T/00u-amendment-20.md:103 |
| NT-L24 | docs/phase-T/00u-amendment-20.md:106 |
| NT-L25 | docs/phase-T/00v-amendment-21.md:105 |
| NT-L26 | docs/phase-T/00v-amendment-21.md:108 |

## UNVERIFIABLE_HERE -- nguon duy nhat nam ngoai workspace

KHONG phai "bia", cung KHONG phai "da xac minh". Mot chi dan dau vao khai
rang nguon cua chung la `/mnt/user-data/uploads/MASTER_PLAN_v10.md`. Duong
dan do KHONG TON TAI trong moi truong nay, va `git log --all -- "MASTER_PLAN*"`
rong. Nen khong kiem duoc THEO CA HAI CHIEU.

Trang thai nay ton tai vi mot ban kiem toan truoc do xep chung nham vao ca
hai nhom: dau tien la "dung" (dua tren mot file ngoai custody), sau do la
"bia" (dua tren mot phep grep truot). Ca hai deu la ket luan vuot qua bang
chung co duoc.

Luat dung: KHONG trich chung trong tai lieu moi. Muon dung -> commit mot
trich luc vao `docs/` truoc, roi chuyen sang ACTIVE kem nguon that.

| ID | Noi dung duoc khai | Trang thai |
|---|---|---|
| NT 27 | dong gop la duong bien/metric/dinh ly | 0 lan trong workspace; nguon khai la file upload khong ton tai o day |
| NT 37 | tinh truoc ly thuyet roi moi fit | nhu tren |
| NT 38 | hang so then chot do o >= 3 diem | nhu tren |
| NT 21 | ket qua am co kiem soat la du lieu | duoc DUNG 1 lan (docs/phase-23/00v-amendment-21.md:259) nhung khong dinh nghia o day |
| NT 52 | bench truoc, wire sau | chi duoc nhac nhu moc danh so (docs/phase-D/02-limits-addendum.md:40) |

## EXTERNAL -- thuoc master plan ngoai workspace

`docs/phase-D/02-limits-addendum.md:88` ghi ro: khong duoc tai dung tu tri nho.
`MASTER_PLAN_v10.md` KHONG co trong checkout nay (chi co
`docs/phase-23/MASTER_PLAN_v8-closeout-addendum.md`).

| ID | Ghi chu |
|---|---|
| NT 54 | docs/phase-D/02-limits-addendum.md:88 -- ngoai workspace |
| NT 55 | cung nhom, nhung DA co su dung co noi dung trong repo (xem ACTIVE) |

## DA TU CHOI -- de xuat tu chi dan ngoai, KHONG cap

Phan quan trong nhat cua so nay. Khong co bang nay, mot nguoi doc lai chat log
sau nay se tuong cac ID duoi day la that va cap lai chung.

Moi dong o day la MOT ID, viet tran o cot dau, de linter doc duoc. Mot ID
o bang nay bi CHAN CHU DONG: dung no o bat ky dau la loi.

| ID | Ngay | Noi dung duoc de xuat | Ly do tu choi |
|---|---|---|---|
| NT 66 | 2026-09-07 | luat truy vet den ket qua | de xuat, chua co amendment ky. So nay VAN CON TRONG -- xem muc SO TIEP THEO |
| NT 67 | 2026-09-07 | moi so phai kem n va bat dinh | de xuat, chua co amendment ky. Noi dung DUNG va huu ich; viet tran cho den khi co amendment |
| NT-L1 | 2026-09-07 | so hoan hao la dau hieu dang nghi | 0 lan xuat hien |
| NT-L2 | 2026-09-07 | viet so du doan ra giay | 0 lan xuat hien |
| NT-L6 | 2026-09-07 | CI tu bien thien giua seed | 0 lan xuat hien duoi ID nay. NOI DUNG CO THAT o docs/phase-L/00f-amendment-5.md:29 -- trich file do, dung trich ID nay |
| NT-L8 | 2026-09-07 | lich sinh truoc + digest | 0 lan xuat hien |

### Va cham noi dung -- KHAC voi tu choi

`NT 49`, `NT 53`, `NT 56` la ID **hop le va dang hoat dong** (xem bang ACTIVE).
Cai bi tu choi khong phai ID, ma la viec gan cho chung NOI DUNG KHAC:

```text
NT 49  duoc trich  "suy rang buoc tu dinh luat"     -> SAI
       noi dung that: cam RUT ket qua, chi doi nhan
NT 53  duoc trich  "ngan sach suy tu tham so"       -> SAI
       noi dung that: positive control cho chinh ESTIMATOR
NT 56  duoc trich  "gate hop le tach gate ket qua"  -> SAI
       noi dung that: power cua doi chung phai chung minh truoc
       (noi dung duoc trich thuc ra gan `NT 57`)
```

Ba noi dung bi gan sai o tren KHONG co ID. Viet chung tran, hoac cap so moi
qua amendment. Tien le xu ly: `docs/phase-G/17-amendment-G-A005-
reclassification.md:41` -- cap so moi thay vi tai dung so da co nghia.

## DINH CHINH mot ban kiem toan dau vao

Mot ban kiem toan dau vao (2026-09-07) xep `NT 50`, `NT 63`, `NT 64` vao nhom
"bia". Grep bac bo dieu do:

```text
NT 50  CO THAT  docs/phase-23/00zzu-amendment-58.md:172  (12 lan dung)
       -> khong phai bia, ma la VA CHAM: noi dung that khac noi dung duoc trich
NT 63  CO THAT  docs/phase-L2/99-gate-decision.md:41
NT 64  CO THAT  docs/phase-L2/01-additivity-already-measured.md:29
       -> noi dung trich ("grep ba chieu") KHOP voi nguon. Trich dan DUNG.
NT 65  CO THAT  docs/phase-L2/99-gate-decision.md:41
```

Nguoc lai, ban kiem toan do xep `NT 27`, `NT 37`, `NT 38` vao nhom "dung" --
ca ba xuat hien 0 lan trong workspace.

Bai hoc: mot ban kiem toan trich dan cung phai duoc kiem bang grep. Chinh
no cung co the sai theo CA HAI chieu.

## SO TIEP THEO DUOC CAP

```text
NT 66        (cao nhat dang ton tai: NT 65, docs/phase-L2/99-gate-decision.md:41)
NT-L27       (cao nhat dang ton tai: NT-L26, docs/phase-T/00v-amendment-21.md:108)
```

Cap mot so moi = viet mot amendment danh so dinh nghia no, roi them dong vao
bang ACTIVE o tren. Khong cap bang cach viet no vao mot tai lieu khac truoc.

# AMENDMENT 23-70 -- Lesson 23.22d: cua so chong lan, va ba cell song moi

Ngay ky : 2026-08-26

Moc      : sau `3c0b2fb`, truoc mot dong ma/chay moi cua A070

Loai     : TIEN DANG KY

## 0. Disclosure

### 0.1. DA XEM

`err_neo` va `kappa_A` cua 6 cell A069 va 12 cell cu. Spearman
(`kappa_A`, `err_neo`) tren 11 cell song = **-0.9909** da duoc tinh
POST-HOC, KHONG duoc ky lai. `P-3`/`M-213` CHET vinh vien vi ca hai dai
luong da in; nguyen nhan la `kappa_A` vao allowlist A069 ma khong stop-rule
nao doc (`L108`).

Cung da xem lan `INVALID_SELF_CALIBRATED_SLA` (`48` muc 0--4). Ca hai lan
cho cung cau truc dinh tinh: poisson cat 0.05 va h2 cat 0.05 giua .740/.780.
Lan INVALID khong duoc dung de cham gate.

### 0.2. CHUA XEM

Moi dai luong cham diem cua ba cell song moi `h2@0.740`, `poisson@0.780`,
`poisson@0.820`: `viol|accept`, `acceptance`, `err|accept`, `qhat_source`.
Moi dai luong cua 12 cell W chua sinh.

## 1. Hai nhanh DOC LAP

A069 ky stop-rule muc LESSON, nhung chi `M-209`/`M-210` phu thuoc cua so;
`M-211`/`M-212`/`M-214` khong phu thuoc (`L109`). A070 tach:

```text
NHANH W (cua so)   phu thuoc dieu kien chong lan.  Stop-rule rieng.
NHANH E (mo rong)  KHONG phu thuoc.                Stop-rule rieng.
W that bai KHONG chan E; E that bai KHONG chan W.
```

## 2. NHANH W -- cua so chong lan

### 2.1. Cau truc va luoi ky truoc

```text
S-W1  Noi suy tuyen tinh / log-tuyen-tinh:
      poisson dat .05 tai .7422 / .7449; h2 tut .05 tai .7701 / .7670.
      Cua so [0.742,.770] hoac [0.745,.767], rong 0.022--0.028.
      G23-270 FAIL la ket qua ve DO PHAN GIAI, khong phai ve su ton tai.
S-W2  Hai mo hinh lech ~.003 tai moi bien; diem du doan khong sac hon +-.005.
S-W3  rho=.760, diem ung vien goc bi A069 bo khi lam tho luoi, nam giua.

rho in {0.744,0.750,0.756,0.760,0.764,0.770} x {poisson,h2} = 12 cell.
Hai bien .744/.770 la doi chung am theo du doan. Sinh CA 12 cell trong mot
batch TRUOC khi doc bat ky truong nao.
```

### 2.2. Allowlist va niem phong

Chi ba outcome duoc giai niem: `err_neo`, `n_calib_blocks`, `build_seconds`.
`kappa_A`, hash parquet tung cell, `mode`, `rho_bar` va moi outcome khac
KHONG thuoc allowlist. `cell` la khoa thiet ke, khong phai outcome. Builder
bi chan stdout/stderr outcome; 12 output duoc commit bang MOT digest gop.

Code phai tach hai pha: `build_all_sealed` tao du 12 cell va receipt; chi
khi receipt du 12/12 va digest khop, `reveal_allowlist` moi duoc doc ba
outcome. Khong co lenh CLI nao in full builder report.

Quy tac: mot outcome chi vao allowlist neu co MOT stop-rule doc no (`L108`).

### 2.3. Du doan

```text
M-215  MU. >=2 rho trong luoi co CA HAI ho `err_neo >= .05`.

M-216  MU. Cua so nam dung cho noi suy:
       (a) rho nho nhat ca hai song thuoc [.744,.756]
       (b) rho lon nhat ca hai song thuoc [.760,.770]
       (c) rho=.760 co ca hai ho song
       HIT khi CA BA dat.
       Neu (c) MISS nhung M-215 HIT: hai mo hinh noi suy duoc bac bo o muc
       dinh vi diem; paper chi bao cao interval do truc tiep, khong dung
       .760 hay noi suy luoi tho lam dai dien.

M-217  MU. Doi chung am: poisson@.744 chet; h2@.770 chet.
       Neu ca hai bien cung song, cua so rong hon du kien va S-W1 sai.
```

STOP-RULE W: M-215 MISS -> dung W, ghi gioi han cuoi cung cho truc rho o do
phan giai 0.006, khong mo luoi lan ba. E van chay.

## 3. NHANH E -- ba cell song moi

```text
M-218  MU. P-1 tai n=250 tren ba cell song moi:
       max/min cua `err|accept / anchor` C3-R <=1.60;
       max/min cua B2-R >=1.80. Neo 8 cell cu: 1.22x va 2.39x.

M-219  MU. P-2 tai bon acceptance {.70,.50,.30,.15}:
       |err_C3R-err_B2R| KHONG GIAM khi acceptance giam o >=3/4 buoc,
       va C3-R <= B2-R o CA BON muc.

M-220  MU. M-202 tren 11 cell song, n=500:
       slope thuoc [.40,.62] VA Spearman >=+.90.
       Bien |log(kappa_A/kappa_B)| mo tu .526 len xap xi .86.

M-221  MU. Do nhay a*/san:
       a* in {.30,.42679,.55} x san in {.20,.30};
       n*(C3-R) in {60,120,250} VA n*(C3-R)/n*(B2-R)>=2 o >=4/6 to hop.

NC-E-0  WIRING. Dung 8 cell cu phai tai tao bit-for-bit TOAN BO payload
        khoa hoc cua `recalibrate_transfer.json`. Envelope provenance co
        timestamp/HEAD duoc bam va so rieng, khong danh dong voi payload.
        Payload lech bat ky bit nao -> DUNG E.

NC-E-1  AM. Cell chet dung tieu chi tuong doi:
        err|accept(C3-R)/anchor >=.80 o >=3/4 cell. Du bao FAIL; no do mot
        dai luong khac voi NC-B3-3.
```

STOP-RULE E: NC-E-0 khong trung bit -> dung E. W van chay.

## 4. No ghi truoc

```text
N1  M-213/P-3 CHET vinh vien. Spearman -0.9909 chi POST-HOC, khong vao bang.
N2  Ke ca M-215 HIT, phat bieu chi ap dung trong cua so do duoc.
N3  Co che hai ho di nguoc chieu la GIA THUYET; can do P(delay>t_delay).
N4  Sau A070, ba cell song moi cung se CAN. N4 cua A069 van dung.
```

## 5. Kiem toan nguoc A068 va thi hanh "so lan nhin" bang code

Ap quy tac allowlist moi vao A068 muc 4: stop-rule chi doc `kappa_A`/
`bracketed` va `qhat_source`. Cac outcome `acc@k=.50`, `acc@kappa_A`,
`abs_error`, `min_blocks`, `qhat_has_infinite`, `qhat_at_sample_max`, trace
bisection va bang do doc S-6 le ra khong duoc in. Viec in chung da tieu kha
nang dung tap pilot do de cham mu cac menh de ve acceptance/do doc va de
chinh dai M-201(b)/M-202 ma khong can mot tap moi; no khong lam M-201(a)/(c)
mat mu vi `viol` khong bi in.

Hai thay doi code bat buoc tu A070:

1. API/CLI sinh du lieu chi co pha sealed: chan stdout builder, sinh tron
   batch, ghi receipt co danh sach file+digest; khong tra DataFrame/outcome.
   Pha reveal la lenh khac, tu choi chay neu batch thieu hoac digest lech.
2. Allowlist khai bao gan stop-rule va duoc test bang nhau chinh xac. Serializer
   tu choi key ngoai allowlist; stdout chi in view da loc. Full artifact nam o
   duong dan sealed, khong co ham/flag CLI de dump no ra terminal.

## 6. Gate

| Gate | Noi dung |
|---|---|
| G23-277 | M-215, cua so ton tai |
| G23-278 | M-216, vi tri cua so |
| G23-279 | M-217, doi chung bien |
| G23-280 | M-218, P-1 tren 3 cell moi |
| G23-281 | M-219, P-2 tren 3 cell moi |
| G23-282 | M-220, M-202 tren truc kappa mo rong |
| G23-283 | M-221, do nhay a*/san |
| G23-284 | NC-E-0/NC-E-1 |

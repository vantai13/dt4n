# AMENDMENT 23-28 -- F1 == F3 tren truc c, F1 rut gon duoc theo block, va khoa G23-32..36

Ngay: 2026-08-20
Commit: sau `5c07458` (PC23v2-2, K-15), TRUOC khi viet `main()` va sinh artifact.

Amendment nay:

```text
(1) ghi F-23.6-6: F1 STICKY va F3 WAIT TRUNG NHAU tung hang tren truc c
    => G23-35 dinh vi HAI diem, khong phai ba
(2) ghi F-23.6-7: F1 RUT GON DUOC thanh thong ke du theo block
    => bac bo tien de cua ca hai phuong an A va B; chon phuong an C
(3) khoa dinh nghia G23-32, G23-33, G23-35, G23-36 va ghi ro provenance
(4) khoa luoc do artifact abstain_cost_<cell>.json
(5) ghi F-23.6-8: thu tu c_F2 < c_F1 tai gamma = 0.78, cell chinh
(6) KHONG them dong du doan tinh diem nao -- va noi ro vi sao
(7) ghi nhan mot mon no moi: 14 dong du doan cua lesson DA DONG chua duoc dien
```

---

## 1. F-23.6-6 -- F1 va F3 la CUNG MOT DIEM tren truc c

Trang thai: **[TAT DINH]**, doc tu ma nguon, khong phai mot phep do.

`cert/fallback.py::fallback_wait` voi `secondary = "sticky"` (mac dinh da dang
ky, P17) tra ve:

```python
if secondary == "sticky":
    a_chosen = fallback_sticky(df, acc)
```

Docstring cua chinh no noi ro:

```text
"With the preregistered sticky secondary, this is exactly F1 at row level;
 the wait horizon is only a diagnostic."
```

Do duoc de xac nhan (cell chinh, `gamma = 0.78`):

```text
F1 == F3 tung hang : True   (so hang khac: 0 / 499,967)
F1 == F2 tung hang : False  (so hang khac: 50,870)

c_F1 err = 0.455929014    c_F1 regret = 4.261205876
c_F3 err = 0.455929014    c_F3 regret = 4.261205876     <- TRUNG TUYET DOI
c_F2 err = 0.394852400    c_F2 regret = 3.283852627
```

### 1.1. He qua cho G23-35

```text
G23-35 phat bieu "dinh vi F1/F2/F3 nhu BA DIEM tren truc c".
Tren truc c chi co HAI diem: c_F2 va c_F1 = c_F3.
```

Day KHONG phai mot loi cua `G23-35`; no la mot dac tinh cua `P17` ma khong ai
ghi lai. `F3 WAIT` khac `F1 STICKY` o **do tre quyet dinh** (`wait_s`), khong o
**rui ro tren tap reject**. Trong khi controller cho, mat phang du lieu van
chuyen tiep tren duong DA CAI DAT -- ma duong da cai dat chinh la sticky.

```text
K-D9  Artifact PHAI ghi c_F1 va c_F3 thanh HAI khoa rieng, ke ca khi chung
      bang nhau, VA phai ghi mot khoa `f1_f3_identical` (bool) noi ro chung
      trung nhau va TAI SAO.
      Gop hai khoa lam mot se giau mat mot su that ve thiet ke; ghi hai khoa
      ma khong ghi ly do se lam nguoi doc tuong do la trung hop so hoc.

      F3 duoc dinh vi tren truc c BANG c_F1, va duoc phan biet voi F1 BANG
      thong ke do tre `wait_s`. Bang cua G23-35 phai co CA HAI cot.
```

Cau duoc phep viet:

```text
DUOC:  "Tren truc chi phi abstain, F1 STICKY va F3 WAIT la cung mot diem: voi
        secondary sticky da dang ky, hang doi cua F3 duoc phuc vu boi chinh
        duong ma F1 giu. Chung khac nhau o do tre quyet dinh, khong o rui ro
        tren tap reject. Truc c dinh vi HAI fallback, khong phai ba."
KHONG: "Ba fallback nam o ba diem khac nhau tren truc c."
```

---

## 2. F-23.6-7 -- F1 RUT GON DUOC theo block; bac bo tien de cua A va B

Trang thai: **[TAT DINH]**, doc tu ma nguon + do thoi gian.

De xuat ban dau dat ra hai phuong an, ca hai dua tren tien de:

```text
"F1 STICKY va F3 WAIT la CO TRANG THAI, nen KHONG rut gon duoc thanh thong ke
 du theo block."
```

Tien de nay **SAI**. `fallback_sticky` cai dat trang thai bang:

```python
filled = seeded.groupby(df["block_id"].to_numpy()).ffill()
```

`groupby(block_id).ffill()` KHONG BAO GIO dien qua ranh gioi block, va
`fillna(p_static)` xu ly cac hang dau moi block. Nghia la trang thai cua sticky
**reset tuyet doi o dau moi block** -- dung nhu `P17` yeu cau ("Reset ve P1 o
dau moi block de khong ro ri calib/test"). `_next_refresh_index` cua F3 cung
dat `carry = -1` o ranh gioi block.

```text
Trang thai khong vuot block
   => ton that cua moi hang chi phu thuoc cac hang CUNG BLOCK
   => tong ton that theo block la mot THONG KE DU
   => bootstrap theo block = nhan ma tran trong so, y het F2 va c*.
```

Khac biet duy nhat so voi F2: ton that MOI HANG cua F2 khong phu thuoc `gamma`
(luon la P1), nen mot vector duy nhat dung cho ca luoi; con F1 phai tinh lai
`a_chosen` o MOI diem luoi. Do la mot he so `K` tren mot phep tinh RE, khong
phai mot rao can cau truc.

Do thoi gian (cell chinh, `n = 499,967`, `n_block = 500`, `K = 50`):

```text
fallback_static  tai mot diem luoi : 0.001 s
fallback_sticky  tai mot diem luoi : 0.014 s
fallback_wait    tai mot diem luoi : 0.131 s   (chi phi nam o _next_refresh_index)

dung ca ma tran (K, n_block) cho F1 tren CA luoi : 1.14 s
   -> sau do bootstrap 2000 draw la MIEN PHI (cung phep nhan W)
```

### 2.1. Quyet dinh -- phuong an C

```text
K-D10  c_F1 (va do do c_F3) duoc tinh tren CA luoi da khoa, kem DAI DONG THOI,
       bang cung co che thong ke du theo block nhu c* va c_F2.

       Bac bo phuong an A ("chi ba diem gamma"): no duoc de xuat de tranh mot
       chi phi khong ton tai. Chon no se lam mat dai tin cay cua c_F1 ma khong
       tiet kiem duoc gi dang ke.
       Bac bo phuong an B ("ca luoi, chap nhan O(n*K), khong bootstrap duoc"):
       nua sau cua no sai.

       Chi phi thuc te: ~1.2 s/cell them vao, tong ~2.5 s/cell.
```

`fallback_wait` KHONG duoc goi o moi diem luoi (0.131 s x K x 3 cell la lang
phi cho mot ket qua da biet la trung `fallback_sticky`). No duoc goi DUNG MOT
LAN tai diem van hanh, de lay thong ke do tre `wait_s`. Ly do phai ghi vao
artifact bang khoa `f3_wait_evaluated_at`.

---

## 3. Khoa dinh nghia G23-32 .. G23-36

### 3.1. Canh bao provenance (NT-v2-12)

`PLAN_v2.md` VAN khong co trong repo (Amendment 23-26 muc 7.2 -- mon no MO).
Cac dinh nghia duoi day duoc chep tu ban ke hoach song NGOAI repo va **chua doi
chieu duoc**. Chung duoc ghi o day de tro thanh ID CO THAT trong repo, dung
theo `NT-v2-12`; khi `PLAN_v2.md` vao repo phai ra soat lai NGAY.

```text
G23-32  Dong nhat thuc R_system(gamma, c*) == R_neo tren moi diem luoi,
        sai so <= 1e-12.                                  [da co, Amd 23-25 muc 6.1]
G23-33  c*(gamma) duoc tinh tren luoi buoc <= 0.02, tren ca 3 cell khong suy bien.
G23-34  DINH NGHIA KHONG BIET. Khong duoc bia. Giu NOT_RUN cho toi khi
        PLAN_v2.md vao repo.                              <- mon no HIEN
G23-35  Dinh vi F1/F2/F3 tren truc c (xem F-23.6-6: HAI diem, khong phai ba).
G23-36  Bang "khi nao bat certification": c*(0.78) tren hai thang, 3 cell.
```

```text
NT-v2-15  Khi mot tam ID duoc dua vao so ma mot phan tu trong tam khong co
          dinh nghia, phan tu do PHAI duoc ghi la khong biet dinh nghia va giu
          NOT_RUN. Bia mot dinh nghia hop ly de "cho du bang" la tao ra mot ID
          gia -- te hon la de trong, vi no doc duoc bang may va trong nhu that.
```

`G23-34` la truong hop dau tien ap `NT-v2-15`.

---

## 4. Luoc do artifact `results/phase-23/abstain_cost_<cell>.json`

```text
K-D11  Artifact PHAI co, ngoai cac khoa da co trong run_cell():

  cell, status, scale, level_tag, rowset             (metadata, P14/K-D3)
  coverage_target VA coverage_measured tren moi dong  (D3)
  c_star_err / c_star_regret                          (K-D1, K-D2)
  c_f1_err / c_f1_regret / c_f2_err / c_f2_regret     (K-D9: F1 va F2 rieng)
  c_f3_err / c_f3_regret                              (K-D9: ghi ke ca khi = F1)
  f1_f3_identical  (bool)  + f1_f3_reason (chuoi)     (K-D9)
  f3_wait_diagnostics       (do tre, danh gia 1 lan)  (muc 2.1)
  f3_wait_evaluated_at      (gamma cua lan danh gia do)
  supt_bands.c_star_err / c_star_regret / c_f1_err / c_f2_err
  certification_table_G23_36
  fallback_locations_G23_35
  gates: G23-32, G23-33, G23-35, G23-36 voi trang thai va bang chung

  MOI khoa mang thang do phai co hau to `_err` hoac `_regret` (K-D3).
  Khong duoc co khoa `c_star` tran; test quet JSON se lam do.
```

---

## 5. F-23.6-8 -- thu tu cua F1 va F2 tren tap reject

Trang thai: **[MO TA]**, DA NHIN SO tren cell chinh, khong tinh diem.

```text
Tai gamma = 0.78, poisson@0.925:
   c_F2 = 0.394852  <  c*  = 0.453347   ->  F2 CO LAI
   c_F1 = 0.455929  >  c*  = 0.453347   ->  F1 LO (sat nguong, du 0.0026)
   c_F3 = c_F1                          ->  F3 LO
```

Nghia la o diem van hanh cua cell chinh, **STATIC tot hon STICKY** tren tap
reject. Doc dung, va mot cai bay phai tranh:

```text
(1) Dieu nay KHONG cham lai F4 (Lesson 23.1: "Thu tu risk: F2 > F1 > F3").
    F4 duoc ky cho kappa = 0.5 cua ho NHAN o Lesson 23.1, tren thang
    err_system TOAN HANG. O day la gamma = 0.78 cua bo chon C3, tren thang
    err|reject. KHAC diem van hanh, KHAC tap hang, KHAC dai luong.
    Cham F4 bang so cua 23.6 la mot loi so sanh cheo lesson.
(2) NHUNG cang thang giua hai ket qua PHAI duoc ghi ra, va F4 phai duoc cham
    bang so cua CHINH 23.1 (xem muc 7 -- no chua bao gio duoc dien).
(3) Co che kha di, CHUA duoc kiem: sticky giu mot hanh dong da CU, va do tuoi
    cua no tang theo do dai chuoi reject. O gamma cao, chuoi reject dai ra,
    nen sticky xau di nhanh hon static (static khong co tuoi). Day la mot GIA
    THUYET, khong phai ket luan; muon khang dinh phai do c_F1(gamma) tren ca
    luoi va doi chieu voi do dai chuoi reject trung binh.
```

Diem (3) tro nen kiem duoc nho `K-D10` (c_F1 tren ca luoi). No duoc de MO o
day, khong khoa thanh du doan, vi toi da nhin `c_F1(0.78)` cua cell chinh.

---

## 6. KHONG co dong du doan tinh diem moi -- va vi sao

Amendment nay khong them dong `[CO CHE]` nao tinh diem. Do la mot lua chon co
y thuc, phai ghi lai:

```text
Toi da nhin c_F1(0.78) cua cell chinh khi do thoi gian cho quyet dinh
A/B/C (muc 2). Mot du doan ve c_F1 tren hai cell con lai se bi thong tin do
lam nhiem mot phan, va khong co co che nao du chac de dan mot dai tu dau --
dung tinh huong da lam C-1 MISS (Amd 23-25 muc 3).

NT-v2-16  Khong tao du doan de co du doan. Mot dai khong dan duoc tu co che
          hoac tu mo phong la mot dai doan, va mot dai doan TRUNG cung khong
          chung minh gi. Ky luat pre-registration la SAN LUONG THAP mot cach
          trung thuc, khong phai san luong cao.
```

Cac dong Lesson 23.6 giu nguyen: ba dong LOP 3 (`K-7`, `K-8`, `K-15`), tat ca
da HIT; phan con lai la `[TAT DINH]` / `[MO TA]` / gate.

---

## 7. Mon no MOI phat hien -- 14 dong du doan cua lesson DA DONG chua duoc dien

Quet `00-preregistration.md` bang may:

```text
Dong du doan co cot "Do duoc" = "___" :  14
   F1 F2 F3 F4 F5 F6      (Lesson 23.1 -- DA DONG)
   T2 T3 T4               (Lesson 23.2 -- DA DONG)
   B2p B3p B4p B5p B6p    (Lesson 23.3 -- DA DONG)
```

Day la CUNG MOT LOAI mon no voi ba gate `DEBT` (`G23-10`, `G23-12a`, `G23-12b`)
tim thay o Amendment 23-26 muc 7.3: mot nghia vu duoc dang ky, lesson da dong,
va khong ai cham.

```text
Hau qua truc tiep: moi phat bieu ve "ti le prediction-hit cua Phase 23" hien
GIO deu KHONG TINH DUOC. Mau so chua xac dinh.
```

```text
K-D12  Mon no nay duoc ghi nhan o day va KHONG duoc dong trong Lesson 23.6.
       Dien 14 dong do can artifact cua 23.1/23.2/23.3 va can quyet dinh tung
       dong xem no la [TAT DINH] hay du doan that (NT-v2-9). Do la mot lesson
       ke toan rieng, khong phai mot muc phu cua 23.6.
       Cam bao cao BAT KY ti le prediction-hit tong nao cho toi khi no dong.
```

---

## 8. Pham vi duoc phep chay sau amendment nay

```text
* sua cert/abstain_cost.py: them c_F1/c_F3 theo thong ke du block (K-D10),
  fallback_locations (G23-35), certification_table (G23-36), main()/CLI
* sinh results/phase-23/abstain_cost_<cell>.json cho 3 cell khong suy bien
* sua docs/phase-23/GATES.md: G23-32/33/35/36 tu NOT_RUN sang trang thai that;
  G23-34 GIU NOT_RUN (NT-v2-15)
* sua test/test_phase23_abstain_cost.py
* sua pytest.ini: them marker `slow` va `addopts = -m "not slow"`

KHONG sua: cert/fallback.py, cert/config_matrix.py, cert/baselines.py,
           cert/conformal_simultaneous.py, cert/aurc_go1.py,
           cert/go2_simultaneous.py, cert/studentized_score.py
KHONG dong: 14 dong du doan o muc 7 (K-D12)
```

---

## 9. Chu ky

```text
Nguoi ky : vantai (Claude-assisted)
Ngay     : 2026-08-20
```

Toi xac nhan: khong mot dai khoa nao bi noi rong; khong mot dong du doan moi
nao duoc them; hai phat hien o muc 1 va muc 2 deu doc duoc tu MA NGUON chu
khong tu ket qua cham diem, nen viec khoa `K-D9`/`K-D10` theo chung la hop le
voi `NT-v2-3`.

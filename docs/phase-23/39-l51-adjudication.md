# 39 -- Phan quyet `L51`: tach `L51` khoi `M-136`

Ngay    : 2026-08-24
Lesson  : 23.21i (Viec 4)
Amendment: `A060-amendment-60.md`
Loai    : PHAN QUYET + CHAN TAI DIEN

## 1. Hai thu bi gop nham

`M-136` bi ghi la "bi chan boi `L51`". Do la mot gop nham, va no da giu
`M-136` dong bang khong can thiet.

```text
L51    = "digest LICH SU da mat"                 -> ve TAI LAP QUA KHU
M-136  = "dau (lift - swing) bat bien qua sweep w_loss"  -> ve MOT TINH CHAT
```

`M-136` hoi: *khi doi `w_loss` thuoc {1250, 5000, 20000}, dau cua
`lift - swing` co doi khong?* Do la cau hoi ve BAT BIEN. Mot bat bien duoc
kiem bang cach chay BA LAN tren CUNG MOT tap du lieu -- bat ke tap do la ban
dung nao. Ba lan chay dung chung moi hang so, nen moi hang so chung TRIET
TIEU trong phep so sanh.

```text
KHONG can parquet lich su:  M-136 (phep kiem GHEP CAP / bat bien)
CAN parquet lich su:        bat ky NC am nao doi "tai tao SO CU"
```

Day dung la lap luan da dung o Lesson 23.20 (`30-close-23-20.md`): *"Dot 1 va
Dot 3 la GHEP CAP nen SLA triet tieu va VAN DUNG"*. No chua duoc ap cho
`M-136`.

> **Bai hoc tong quat, dang viet vao paper:** mot phep kiem GHEP CAP khong can
> du lieu GOC, no chi can du lieu NHAT QUAN. Chi phep kiem doi chieu voi mot
> GIA TRI da cong bo moi can du lieu goc.

Phan biet nay tra loi luon cau hoi 3 o cuoi huong dan: `G23-212` (NC am cua
Viec 3) CAN du lieu goc vi no khang dinh *"con so moi TRUNG con so cu"* --
mot menh de ve mot GIA TRI cu the. `M-136` khang dinh *"dau khong doi qua ba
lan chay"* -- mot menh de ve QUAN HE giua ba lan chay do.

## 2. Hien trang do duoc (2026-08-24)

```text
find results -name "*.parquet" | wc -l          ->  47
```

> Huong dan ngoai repo du doan 24. So THAT la 47. Bao cao nguyen, khong ep ve
> du doan -- cung ky luat da dung o amendment 23-59 muc 2.

Tam parquet Phase 22 ma `eight_cell_sweep` + `live_region_sweep` tro toi:

```text
CO (4/8 luoi goc):  calib_set_v3.parquet            (= poisson@0.925)
                    calib_set_v3_poisson_0.850.parquet
                    calib_set_v3_poisson_0.700.parquet
                    calib_set_v3_h2_0.700.parquet
                    (+ calib_set_v3_cbr_0.700, _poisson_0.925, _poisson_0.925_V3)

MAT (4/8 luoi goc): calib_set_v3_poisson_0.960.parquet
                    calib_set_v3_h2_0.850.parquet
                    calib_set_v3_h2_0.925.parquet
                    calib_set_v3_h2_0.960.parquet

MAT (4/4 Dot 4):    calib_set_v3_poisson_0.875.parquet
                    calib_set_v3_poisson_0.900.parquet
                    calib_set_v3_h2_0.650.parquet
                    calib_set_v3_h2_0.675.parquet
```

Tam file mat -> `eight_cell_sweep` KHONG sinh lai duoc -> day la ly do
`eight_cell_sweep_U3_measured_v7_slaB.json` phai bi grandfather trong Viec 2
(xem `L75`). Do la mot he qua CU THE cua `L51` ma truoc day chua ai chi ra.

## 3. Phan quyet

### `M-136` -> GIAI PHONG

`M-136` khong con bi `L51` chan. No duoc do tren ban dung MOI, va ket qua do
la mot ket qua hop le vi no la phep kiem bat bien.

Hai duong viet phai chuan bi TRUOC khi chay (de khong dien giai lai nguong
sau khi thay so):

```text
NEU dau (lift - swing) KHONG doi qua ba w_loss:
    -> "ket luan trust gate co loi KHONG phu thuoc ty gia w_loss trong dai
        1250..20000 (he so 16)."

NEU dau CO doi:
    -> "ket luan trust gate co loi PHU THUOC w_loss." Day KHONG phai loi. Do
       la mot ket qua, va la ket qua MANH hon: mot tham so AN da duoc bien
       thanh mot truc CO KIEM SOAT. Bao cao nguyen kem diem doi dau.
```

### ⚠️ PHAN QUYET NAY DA BI SUA -- xem muc 6

Muc 3 duoi day giu NGUYEN dang da ky ngay 2026-08-24 sang. Tien de cua no
("digest da mat") DA BI BAC BO chieu cung ngay. Khong xoa, vi mot phan quyet
bi lat la lich su chu khong phai vet ban.

### `L51` -> DONG, tuyen VINH VIEN khong tai dung duoc

Day la lua chon dung, khong phai lua chon de.

```text
Can de tai dung bit-exact:  seed + config + PHIEN BAN CODE cua builder Phase 22
Dang co:                     seed + config
Da mat:                      digest cua 8 parquet (bao cao cung thoi khong luu)
```

Khong co digest thi du dung lai duoc mot file, cung KHONG chung minh duoc no
la file cu. Va `L51` da tu viet luat cho tinh huong nay:

> *"Dung lai ma tham so khong khop goc -> doi chung am muc duong ong vo nghia
> IM LANG. Bao cao 'khong tai dung duoc', KHONG dung so thay the."*

Cau viet vao Threats to Validity:

> *"Tam bang hieu chuan Phase 22 (~1.9 GB) khong duoc commit vi gioi han kich
> thuoc cua kho, va tong kiem (digest) cua chung khong duoc luu trong bao cao
> cung thoi. Do do viec tai lap bit-exact cac con so Phase 22 la khong the.
> Chung toi dung lai duong ong tu seed va doi chieu tren cac dai luong GHEP
> CAP, von triet tieu moi hang so dung chung. Day la ly do chung toi tu nay
> ghim digest cua moi artifact trung gian ngay trong bao cao sinh ra no
> (`G23-198/199`)."*

## 4. Chan tai dien -- `test/test_no_dangling_parquet_refs.py`

Lint tinh (AST) tren `cert/`, `measurements/`, `tools/`: khong hang so chuoi
`*.parquet` nao duoc tro toi file khong ton tai ma im lang.

**`G23-218` -- so dong DO lan quet DAU TIEN: `29`.**

Sau khi loc ba dang duong-ong-hop-le (mau `{}` / `%s`, glob `*`, duoi don
thuan `.parquet` khong co `/`): con **16**. Trong 16:

```text
12  KNOWN_DANGLING  8 parquet Phase 22 that su mat, tro toi tu 3 script
                    (eight_cell_sweep 4, live_region_sweep 4,
                     g23_174_reuse_verdict 4 -- trung ten, 8 file rieng biet)
 4  OUTPUT_PATHS    duong GHI RA, khong can ton tai truoc khi chay
```

Ca hai danh sach CHI DUOC NGAN DI, va co `test_known_dangling_only_shrinks`
ep dieu do: parquet nao song lai ma con nam trong danh sach thi test do.

Doi chung duong da chay: bo mot muc khoi `KNOWN_DANGLING` -> test do dung hai
dong tro toi file do. Bo lai -> xanh.

### Mot ghi chu ve `decision_error_v2.FIXED_OUT`

`FIXED_OUT` CO Y duoc giu tro toi `results/LIVE/...decision_error_by_age_by_regime.parquet`
du file da bi ha xuong `SUPERSEDED/`. Doi no sang `SUPERSEDED/` se khien mot
lan chay khong co co LANG LE GHI DE bang chung da dong -- vi pham `MAP.md`
muc 4. Giu nguyen thi lan chay do ghi ra `LIVE/` va bi
`test_every_live_parquet_has_a_validity_sidecar` bat ngay. *Fail loud, khong
fail quiet.*

## 5. `M-136` DA CHAY -- va ket qua bac bo mot tien de cua chinh muc 1

Phan quyet muc 1 ("`M-136` khong can parquet LICH SU") VAN DUNG. Nhung tien de
ngam di kem no -- *"nen chi can chay lai eight_cell_sweep ba lan tren cung mot
tap du lieu"* -- **DA BI BAC BO bang do**.

### 5.1. Do duoc

```bash
# 3 manifest, queo DUNG MOT THU (w_loss), giu nguyen t_delay/t_loss
.venv/bin/python -m measurements.sla_manifest_exogenous --w-loss $W \
    --out results/PENDING/phase-20R/sla_manifest_w${W}.json

# 3 lan quet, dung calib set DA CO o LIVE/phase-21R
.venv/bin/python -m cert.eight_cell_sweep \
    --sla results/PENDING/phase-20R/sla_manifest_w${W}.json \
    --calib-template "results/LIVE/phase-21R/calib_set_{mode}_{rho:.3f}_U0_measured_v7.parquet" \
    --axis measured_v7 --aoi-profile U0 \
    --out results/PENDING/phase-23/eight_cell_w${W}.json
```

```text
w_loss =  1250   ->  AssertionError: objective ratio=1 parity fail
                     for poisson@0.925: 2.815e-02
w_loss =  5000   ->  CHAY DUOC
w_loss = 20000   ->  AssertionError: objective ratio=1 parity fail
                     for poisson@0.925: 8.347e-03
```

### 5.2. Vi sao -- `w_loss` DA BI NUONG VAO calib parquet

```python
# cert/eight_cell_sweep.py:_objective_curve
y_base = base["y_true"]                       # tinh voi w_loss CUA MANIFEST
...
at_one = <curve tai ratio = 1>                # => argmin(y_base)
parity = |at_one.delta - selected_at_one.delta|   # selected_* den tu PARQUET
if parity > 1e-12: raise AssertionError(...)
```

`selected_at_one` den tu calib parquet, va parquet do DA duoc dung voi mot
`w_loss` co dinh:

```text
results/LIVE/phase-21R/calib_set_poisson_0.925_U0_measured_v7_report.json
    report/w_loss           = 5000.0
    report/validity/w_loss  = 5000.0

cot cua parquet: a_twin, a_star, regret, gap_true, viol_star, ...
                 -- TAT CA deu suy tu ham chi phi, tuc tu w_loss
```

Nen doi `w_loss` o manifest ma giu nguyen parquet la dat HAI dinh nghia
`w_loss` canh nhau trong cung mot phep tinh. Parity `1e-12` la cai chan bat
dung dieu do. **Tai `w = 5000` parity = 0 vi hai dinh nghia trung nhau** --
do cung la ly do lan chay do di qua.

### 5.3. Ket luan sua lai

```text
DUNG   : M-136 khong can parquet LICH SU cua Phase 22.
SAI    : M-136 chi can chay lai tren CUNG tap du lieu.
DUNG   : M-136 can calib set DUNG LAI o TUNG w_loss (3 bo, khong phai 1 bo).
```

Cau tra loi cho cau hoi tu kiem 3 phai duoc noi chinh xac hon: mot phep kiem
GHEP CAP khong can du lieu GOC, nhung no van can du lieu duoc sinh DUNG CACH
duoi tung dieu kien duoc so sanh. `w_loss` khong phai mot tham so CHAM DIEM
(ap sau khi co du lieu); no la tham so SINH (quyet dinh `a_twin`, `a_star`).
Queo mot tham so sinh thi phai sinh lai.

### 5.4. Trang thai `M-136`: 1/3 diem, BI CHAN vi ly do MOI

Diem `w = 5000` (do duoc, `results/PENDING/phase-23/eight_cell_w5000.json`):

```text
cell             lift - swing    dau
h2@0.700           +0.015118      +1
h2@0.850           +0.006540      +1
h2@0.925           +0.000000       0      <- dung bang 0, khong co dau
h2@0.960           +0.000910      +1
poisson@0.700      +0.000582      +1
poisson@0.850      -0.013999      -1      <- dau AM
poisson@0.925      +0.045400      +1
poisson@0.960      +0.011771      +1
```

Ngay tai MOT diem `w_loss`, dau da KHONG dong nhat: 6 duong, 1 am, 1 bang 0.
Nen menh de `M-136` phai duoc phat bieu theo TUNG CELL (dau cua cell `c` co
bat bien qua `w_loss` khong?), khong phai theo toan bo luoi.

`G23-217` KHONG do duoc trong lan nay. Ghi `L77`. Viec con lai thuoc lesson
so huu `M-136`: them duong queo `w_loss` vao `build_calib_set_v3` roi dung
lai 8 cell x 3 `w_loss` (uoc tu so ledger: 8 job x 26.3 s x 3 ~ 11 phut may),
KHONG phai chay lai eight_cell_sweep tren bo cu.

> Cai chan `parity > 1e-12` da lam dung viec cua no: no TU CHOI sinh ra mot
> con so sai mot cach im lang. Neu no khong co, `M-136` da co ba con so trong
> tay va ca ba deu vo nghia. *Fail loud, khong fail quiet.*

---

# 6. ★ SUA PHAN QUYET (cung ngay, sau review doc lap)

## 6.1. Tien de "digest da mat" LA SAI

Review doc lap yeu cau ghim digest 5 parquet Phase 22 con song. Khi lam viec
do, toi doi chieu chung voi `provenance.inputs` cua artifact CU -- va phat
hien digest lich su **KHONG mat**:

```text
nguon: results/SUPERSEDED/phase-23/eight_cell_sweep_U3_measured_v7.json
       provenance.git_hash = 05b597f5a9b27ee390f03ba3be2355aedca17dc0
```

Artifact do ghi `sha256` cua CA 8 calib parquet + `truth_table` +
`sla_calibration` + amendment. Muc 3 tren viet *"digest cua 8 parquet (bao cao
cung thoi khong luu)"* -- **sai**. Bao cao cung thoi CO luu; khong ai di doc.

## 6.2. Doi chieu -- va mot file BI PHAT HIEN KHONG PHAI BAN GOC

```text
file                                  tren dia   doi chieu digest lich su
truth_table.parquet                   CO         KHOP
sla_calibration.json                  CO         KHOP
00zp-amendment-39.md                  CO         KHOP
calib_set_v3.parquet      (p@0.925)   CO         ★ KHOP  -> BAN GOC
calib_set_v3_h2_0.700     (h2@0.700)  CO         ★ KHOP  -> BAN GOC
calib_set_v3_poisson_0.850            CO         ★ KHOP  -> BAN GOC
calib_set_v3_poisson_0.700            CO         ✗ KHAC  -> KHONG PHAI BAN GOC
      lich su : ec49deb8725498f9cf03d7c302983ab5...
      tren dia: 2267423d8d33f3da3ad07ab12a2c5d28...
calib_set_v3_cbr_0.700                CO         LO 13/08 -- SUPERSEDED_GENERATION
calib_set_v3_poisson_0.925            CO         LO 13/08 -- SUPERSEDED_GENERATION
calib_set_v3_poisson_0.925_V3         CO         LO 13/08 -- SUPERSEDED_GENERATION
calib_set_v3_poisson_0.960            MAT        -
calib_set_v3_h2_0.850 / _0.925 / _0.960  MAT     -
```

**Bay da suyt roi vao:** review de xuat `ALIVE = (poisson@0.925, poisson@0.850,
poisson@0.700, h2@0.700)` -- BON cell. Mot trong bon (`poisson@0.700`) KHONG
phai ban goc. Dung no lam moc doi chung se rot dung cai bay chinh `L51` da
canh bao: *"dung lai ma tham so khong khop goc -> doi chung am muc duong ong
vo nghia IM LANG."*

Chi phat hien duoc vi co digest LICH SU DOC LAP de doi chieu. Do la lap luan
tu bao ve cua `G23-174`, hoat dong lan dau tren du lieu that. Phan quyet ban
dau dung o `UNKNOWN` vi ba file cuoi khong co digest lich su rieng. Hau kiem
61b tim duoc bang chung THE HE: ca ba cung `git_hash=f95c6bee`, builder
`0f534288...`, `git_dirty=true` va cua so 13/08 04:33--04:35 voi
`poisson_0.700` cu. Report 21/08 cua chinh cell sau dung builder
`f02b1d1c...`; digest ma eight-cell da ghim thuoc the he sau va nay da mat.

Vi vay ba file khong duoc nang thanh ORIGINAL, ma duoc doi tu `UNKNOWN` sang
`VERIFIED_SUPERSEDED_GENERATION`: xac minh duoc la thanh vien lo 13/08 da bi
thay cho muc dich canonical eight-cell/Phase 23. Phan quyet nay KHONG noi moi
artifact Phase 22 lich su tung doc lo 13/08 la sai; no cam TAI DUNG lo do nhu
dau vao canonical hien hanh.

## 6.3. `L51` sua thanh ba menh de rieng

```text
L51a  DIGEST lich su:      KHONG mat. Nam trong provenance cua artifact cu.
L51b  DU LIEU GOC:         5/9 parquet input lich su khong dung duoc:
                           4 vang mat + 1 da bi thay noi dung.
L51c  XAC MINH FILE LOCAL: 3 VERIFIED_ORIGINAL / 1 NOT_ORIGINAL /
                           3 VERIFIED_SUPERSEDED_GENERATION / 0 UNKNOWN.
                           Hai nhom khong-original deu CAM tai dung.
```

Ket luan "khong tai dung duoc bit-exact cac con so Phase 22" VAN DUNG (thieu
5/9 input). Nhung **ly do** khac han: khong phai *"mat digest nen khong xac
minh duoc"* ma *"mat DU LIEU, tuy digest van con nen phan con lai xac minh
duoc"*. Van ban Threats to Validity o muc 3 phai sua theo -- cau
*"tong kiem cua chung khong duoc luu trong bao cao cung thoi"* la SAI su that.

Ban sua:

> *"Nam trong chin dau vao cua bang hieu chuan Phase 22 khong con tren dia va
> khong duoc commit (gioi han kich thuoc kho), nen viec tai lap bit-exact cac
> con so Phase 22 la khong the. Tong kiem cua chung VAN CON -- chung duoc ghim
> trong `provenance` cua artifact cung thoi -- nen bon file con song deu doi
> chieu duoc; ba trong so do xac minh la ban goc va mot bi phat hien KHONG
> phai, va do dó bi cam tai dung. Chung toi dung lai duong ong tu seed va doi
> chieu tren cac dai luong GHEP CAP."*

## 6.4. `G23-212a` -- va vi sao no KHONG dung parquet Phase 22

Y dinh ban dau: chay doi chung am tren 3 cell goc con song. **Da thu, da bo**,
vi phat hien thu hai:

```text
poisson@0.925 + calib_set_v3.parquet (BAN GOC) + manifest S-B
    -> AssertionError: objective ratio=1 parity fail: 6.312e-03
```

Parquet Phase 22 duoc dung duoi SLA NOI SINH (`w_loss` 1245..4722 tuy cell).
Ghep chung voi manifest NGOAI SINH (`w_loss = 5000`) dung co che `L77`. Ban
goc hay khong KHONG cuu duoc dieu do -- chung o SAI TRUC.

Duong dung: bo `results/LIVE/phase-21R/calib_set_*_U0_measured_v7.parquet`,
duoc dung O `w_loss = 5000` nen TU NHAT QUAN voi S-B, va 8/8 co
`parquet_sha256` ghim san trong sidecar (`G23-198`/`G23-199`).

```text
G23-212a  8/8 cell   2340 truong so sanh
          NHOM A (bit-exact) lech: 0
          NHOM B (qua thu gon, dung sai 3.18e-12*|v|) lech: 0
          -> PASS

doi chung duong: nhieu 1e-9 vao mot truong NHOM A  -> bat (1 lech)
                 nhieu 1e-15 vao mot truong NHOM A -> bat (1 lech)
```

Nen `G23-212a` phu **8/8 cell**, khong phai 3 hay 4. Ten `212a` giu vi no van
khac `G23-212`: `212` doi tai tao artifact LICH SU (bat kha thi -- `L75`+`L51b`),
`212a` chi khang dinh TUONG DUONG DUONG CODE tren mot tap du lieu ghim digest.

Gioi han: `G23-212a` co the PASS neu duong cu va duong moi CUNG sai theo mot
cach. No khang dinh thay `prepare_sla()` bang nap manifest khong doi 2340
truong ha nguon; no KHONG tu than chung minh manifest ngoai sinh la dung.
Tinh dung do thuoc cac gate noi dung/validity rieng, khong thuoc parity nay.

**Viec 3 khong con bi chan boi `L51`.** Ve A da chup:
`results/RAW/phase-23/g23_212a_before.json`.

## 6.5. Thu tu dung (sua muc 5 cua ke hoach cu)

Chuoi `mo L51 -> sinh lai _slaB -> G23-212 -> Viec 3` la mot DEADLOCK THU HAI
cung dang `L67`: mat dau (`mo L51`) khong bao gio giai duoc.

```text
[0] Ghim digest 7 parquet con song                    XONG (468 MB, git=0/7)
[1] test_no_dangling cham theo `git ls-files`         XONG (L79)
[2] pin() fail loud                                   XONG (L78)
[3] G23-219 phan nhom A/B cho tieu chi bit-exact      XONG
[4] G23-212a doi chung am 8/8 cell                    XONG -- ve A da chup
[5] Viec 3 = Lesson 23.21h                            SAN SANG (chua lam)
```

`L51` khong nam trong chuoi. No da dong bang phan quyet; no chi dang bi dung
de CHAN thu no khong thuc su chan.

> ⚠️ **CON LAI, GAP, chi ban lam duoc:** 7 parquet Phase 22 (468 MB) va 16
> parquet phase-21R deu KHONG trong git. Digest da ghim, nhung digest khong
> thay the duoc DU LIEU. **Sao luu ra ngoai o dia.** Neu o dia hong truoc do:
> `L51b` tu 5/9 thanh 9/9, `G23-212a` mat luon ve A, va Viec 3 khong bao gio
> lam dung duoc.

## 6.6. Custody sau phan quyet (`L82`--`L84`, `G23-221`--`G23-223`)

Da backup 23/23 parquet (7 Phase 22 + 16 Phase-21R) sang filesystem Windows
ngoai `/dev/sdd`; SHA-256 nguon/đich lech 0. Sau do khoa write bit cua
`results/RAW` va `results/SUPERSEDED` o muc OS.

Mtime cua bay file deu nam 13--15/08. Tuy nhien `poisson_0.700`, da chung minh
bang digest la KHAC ban goc, cung mang mtime 13/08. Mtime khong du nang ba
file thanh ORIGINAL. Ket hop timestamp trong report + `git_hash` + builder
hash, no lai xac nhan ca bon thuoc cung lo 13/08; xem `A061b-amendment-61b.md`.

Test custody da tach: VANG MAT chi do tren may giu du lieu; DOI NOI DUNG van
la bat bien portable va do o moi noi file co mat. CI/clone sach loai marker
`custody`, con may tac gia chay rieng marker nay.

## 6.7. Hau kiem 61b -- nguyen nhan ghi de va anh xa cell

`tools/tier_results.py` tai commit phan tang `5e1837f` dung `git mv -f` cho
file tracked va `os.replace` cho file ignored. Ca hai cho phep dich co san bi
ghi de; `os.replace` lai de mtime cua file NGUON di theo. Co che nay giai
thich dong thoi digest 21/08 bien mat va mtime tren dia lui ve 13/08. Quet
blast radius thay mot va cham Phase 22. Muoi sau cap report Phase-21R cung
stem la phan tang dung: ban `self_calibrated` o SUPERSEDED, ban
`exogenous_g114_S-B` o LIVE.

`G23-224` bo ca hai primitive overwrite: preflight dung truoc moi mutation,
`git mv` khong `-f`, file ignored dung hard-link atomic + unlink va van fail
neu dich xuat hien sau preflight.

`L85` cung duoc sua tai nguon: `phase23_cell_margins.DEFAULT_CELLS` nay dung
`calib_set_v3.parquet` cho `poisson@0.925`, giong `eight_cell_sweep`. Chay doi
chieu cu/moi tren G23-17a/b/c cho **0 khac biet so hoc**; chi path/digest
provenance doi. Artifact cu giu nguyen trong SUPERSEDED nhu bang chung lich
su, khong ghi de de "lam dep" qua khu.

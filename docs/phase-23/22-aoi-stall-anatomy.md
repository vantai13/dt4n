# Lesson 23.18 -- Giai phau stall + phan ra `d`

Ngay      : 2026-08-22
Prereg    : `docs/phase-23/00zy-amendment-45.md` (tag `amendment-45`)
Bo sung   : `docs/phase-23/00zz-amendment-45a.md` (tag `amendment-45a`)
Du lieu   : `results/RAW/phase-23/aoi_v7_campaign` -- 30 run, KHONG do moi
Artifact  : `results/LIVE/phase-23/aoi_stall_anatomy.json`
            `results/LIVE/phase-23/aoi_decomposition.json`

## 1. Ba cau hoi

```text
Q1  Stall ~1.4 s xay ra O DAU trong 120 s?    -> H1, dut khoat (muc 3)
Q2  "d_sync" that ra la may dai luong?         -> hai, va mot cai bi dac ta sai (muc 5)
Q3  Vi sao 8 link lech tuoi 25.95 ms?          -> vong PATCH tuan tu (muc 4)
```

## 2. SUA CO CHE truoc khi chay: `t_source` la dau RIENG tung Thing

Ban ke hoach 23.18 muc 3.1 doc `collector.py:573-577` roi ket luan `t_source`
la dau CHUNG cho ca 8 thing, va xay H4 tren do. Doc tiep thi thay nguoc lai:

```text
collector.py:576   't_source': t_cycle_start     <- CHI la fallback, co nhan
collector.py:585   data['t_source'] = t_i        <- hosts,    dau RIENG
collector.py:592   data['t_source'] = t_i        <- switches, dau RIENG
collector.py:608   data['t_source'] = t_i        <- links,    dau RIENG
```

Docstring cua chinh ham do noi thang dieu nguoc lai voi suy dien cua ban ke
hoach: *"Dau chung cho ca vong se xoa mat do lech tuoi giua cac link va lam
estimand E3 khong do duoc"* (Amendment 23-42b).

Kiem tren du lieu: trong MOT probe, 8 link co 8 gia tri `t_source` khac nhau.

Day la tin TOT: `t_source - t_cycle_start` la **do lech scan do duoc TRUC
TIEP**, khong phai suy ra. Nho no, H4 tach duoc lam hai thanh phan dau nguoc
nhau va do rieng duoc tung cai.

## 3. Q1 -- Stall o dau: H1, khong nhap nhang

```text
M-78   ty le run co chu ky overrun DAU TIEN o cycle < 20 :  100.0%   (30/30)
M-78b  so chu ky overrun moi run                         :  1 - 2
       PHAN XU (tinh bang cong thuc, nguong 0.80 khoa o amendment 23-45)
       -> H1_STARTUP_TRANSIENT
```

Khong can den quy tac phan xu cho truong hop nhap nhang: ket qua la 100%,
khong phai 65%.

**H3 (chu ky reconcile) bi BAC BO bang mot phep kiem co suc phan biet.**
`M-78c` nhu da ky ra MISS (0.545 so voi nguong <0.5) nhung phep kiem do
KHONG PHAN BIET DUOC: o CLEAN `reconcile_every = 1` nen MOI chu ky deu la
reconcile, cau hoi "chu ky overrun co phai reconcile khong" luon dung bat ke
H3 dung hay sai. Chi PROD (`reconcile_every = 30`) moi phan biet duoc:

```text
PROD:  0 / 15 chu ky overrun la chu ky reconcile
       ty le nen cua chu ky reconcile = 3.69%
-> chu ky overrun KHONG chi la khong uu tien reconcile, chung TRANH han.
-> H3 bi bac bo.
```

**H5 (ping dinh ky) da bi loai TRUOC khi chay, bang doc ma nguon:**
`collector.py:410  self.ping_every = ping_every  # legacy option; collect_all
no longer pings`. Loai mot gia thuyet bang bang chung ma nguon cung la mot
ket qua.

### Cat warm-up: gate hinh dang rang cua gan nhu dong lai

```text
CV CLEAN truoc cat  0.4195
CV CLEAN sau  cat   0.3952        <- M-79 HIT (dai khoa 0.375-0.400)
null rang cua       0.3667
khoang cach con lai 0.0285   (truoc khi cat la 0.0528)
```

Lesson 23.8 ghi `M-72b` MISS voi gap 0.0522 > 0.05. **Hon mot nua khoang
cach do la artifact khoi dong.** Day la dau vao truc tiep cho hinh dang
`aoi_model_v7` o Lesson 23.19.

Xac nhan DOC LAP cho H1, do tren mot truc khac: sau khi cat warm-up, ty le
khoang refresh dai (`T_eff > 0.55 s`) tut tu 0.4167% xuong **dung 0.0000%**.
Moi khoang dai deu nam trong 19 chu ky dau.

## 4. Q3 -- H4 duoc xac nhan bang mot DONG NHAT THUC, khong phai mot he so

O trang thai on dinh, gia tri cua link `l` nhin thay duoc tu
`t_visible(l) = t_source(l) + d_transport(l)` va giu den lan refresh sau.
Probe roi deu tren cua so do, nen `E[AoI(l)] = d_transport(l) + T/2`, tuc

```text
alpha(l)  ==  d_transport(l) - mean(d_transport)
```

Do duoc:

```text
link   alpha_ms   scan_off_ms   d_transport_ms
ac       -8.690        50.717          154.682
ad       -8.541        53.685          154.289
bc       -8.559        56.681          151.561
bd       -6.721        59.621          150.946
vC       -2.682        62.773          156.039
vD        5.819        65.959          163.065
uA       12.111        69.061          168.093
uB       17.263        72.206          175.579

RMS du cua dong nhat thuc : 2.473 ms  tren bien do alpha 25.95 ms  (9.5%)
=> dong nhat thuc giai thich 90% bien do.
```

Ket luan, va no la mot ket qua cho paper:

> **Su khong dong nhat AoI giua cac link bi chi phoi boi vong cap nhat tuan
> tu cua twin, khong phai boi bat doi xung cua mang.**

Va no co he qua thiet ke that: song song hoa vong PATCH se xoa phan lon
trai nay.

**scan_offset la bien DI KEM, khong phai nguyen nhan.** No tuong quan 0.939
voi alpha va thu hang cua no on dinh tuyet doi giua 15 run (`M-78e` = 1.0000)
-- nhung no KHONG vao dong nhat thuc. Ca hai cung tang theo vi tri trong vong
lap nen cong tuyen. Bien dieu khien la `d_transport` (vi tri PATCH), tuong
quan 0.9751.

Hai thanh phan dau nguoc nhau, dung nhu du doan o amendment 23-45 muc 2:
scan lam link muon HON tro nen TUOI hon (bien do 21.49 ms), patch lam no
GIA hon (bien do 24.63 ms). Trai quan sat duoc la phan con lai.

### `M-78g` MISS la van de CONG SUAT, khong phai co che

```text
khoang cach d_transport giua hai link ke nhau  : 3.52 ms
sd cua d_transport GIUA cac run, nho nhat      : 5.56 ms  (uB: 23.28 ms)
-> sd / khoang cach >= 1.58
```

Thu hang **khong the** on dinh giua cac run khi nhieu lon hon khoang cach can
phan giai -- du co che dung hoan toan. Trung binh 15 run thi on dinh (do la
ly do tuong quan muc trung vi dat 0.9751). Day la gioi han do phan giai cua
nhac cu, khong phai bang chung chong H4.

## 5. Q2 -- Chot `d`: mot estimator bi DAC TA SAI

Amendment 23-45 muc 5 buoc: ba cach lech > 15 ms thi phai DIEU TRA, khong
duoc chon bua. Ba cach cho:

```text
quantile_fit             119.22 ms
decomposition_debiased   108.99 ms
cycle_trace              208.30 ms     <- lech han
M-85 chenh lech lon nhat  99.32 ms     MISS
```

Dieu tra cho ket qua dut khoat: **`cycle_trace` khong do cung mot dai luong.**

```text
cycle_elapsed_ms  = thoi gian tron MOT CHU KY cho CA 20 Thing
                    (6 host + 6 switch + 8 link)
d_transport       = duong di cua MOT link: tu t_source cua rieng no
                    den luc nhin thay duoc
```

Hai cai chi trung nhau neu he chi co mot Thing. Day la loi DAC TA cua
estimator, khong phai bang chung rang he chua duoc hieu. `M-81b` MISS cung
tu dung mot goc nay.

Hai estimator KHOP dai luong thi dong y:

```text
quantile_fit             119.22 ms
decomposition_debiased   108.99 ms
chenh lech                10.24 ms     <= 15 ms
d chot (cap khop)        114.11 ms
```

`M-84` MISS (145.50 ms) vi no lay trung binh ca ba, ke ca cai bi dac ta sai.
Con so dung de mang sang Lesson 23.19 la **114.11 ms**, va no nam trong dai
115-132 ms cua `M-84` chi lech 0.9 ms o can duoi -- tuc **du doan CO CHE ve
do lon cua `d` la dung; chi cong thuc tong hop la sai.**

Doi chieu: gia tri dang dung trong pipeline la `d_sync = 51 ms`. Gia tri do
duoc la 114 ms. Ty so 2.24x.

### Gioi han nhac cu -- ghi CANH so, khong phai o "future work"

```text
d_transport uoc luong bang "t_obs SOM NHAT nhin thay mot t_source".
Probe chay moi 100 ms -> gia tri that co the da xuat hien bat ky luc nao
trong 100 ms truoc do.
=> d_transport do duoc la CAN TREN.
=> bias HE THONG +50 ms (nua khoang probe).
=> TANG SO RUN KHONG LAM NO NHO DI. Chi doi nhac cu moi lam duoc.
```

`M-83` MISS (89.92%) chinh la bias nay hien ra: tru mot `d` bi thoi len 50 ms
khoi AoI thi phase bi day am. Dung `d` da khu bias, ty le lot khoang len
96.61%. Van duoi 99.5% vi `d` con bien thien theo tung epoch, khong phai
mot hang so.

## 6. Thong ke: CI theo thiet ke long nhau -- va cau tra loi la "khong can"

15 run CLEAN la **5 muc rho x 3 lan lap**, khong phai 15 lan lap doc lap.

```text
d          = 158.99 ms   (d_transport tho, chua khu bias)
CI95 long nhau (df=4)   [155.17, 162.80]
CI95 gop iid   (df=14)  [154.87, 163.10]
ty so rong  0.927x      <- M-90 MISS (du doan 1.3-2.5x)
ICC         0.0000
```

`ICC = 0` la mot cau tra loi THAT, khong phai mot that bai: phuong sai giua
cac muc rho khong vuot phuong sai trong muc, tuc **`d` khong phu thuoc tai**.
Vi vay CI gop iid cua amendment 23-44 KHONG hep gia tao, va khong can sua.
Du doan 1.3-2.5x sai vi no gia dinh co cau truc rho dang ke -- khong co.

Ghi chu ve muc 0 cua ban ke hoach 23.18: viec dung `t` thay vi `z` cho n=15
la dung va da ap dung. Viec them mot tang long nhau cung dung ve nguyen tac
-- va khi do duoc, no cho biet tang do rong bang 0.

## 7. corr(AoI, rho): gia thuyet artifact co hoc KHONG duoc ung ho

Ban ke hoach de xuat kiem gia thuyet (b) bang tuong quan rieng phan TRONG
tung chu ky refresh. **Phep do do thoai hoa**: `rho` doc ra tu CUNG snapshot
voi `t_source`, nen trong moi epoch `rho` la HANG SO (kiem: 0/1928 epoch co
hon mot gia tri). Phan du cua mot hang so bang 0, nen tuong quan ra dung
`0.0000` -- khong phai vi khong co hieu ung ma vi phep kiem khong con bien.

Phep kiem dung phai o MUC EPOCH:

```text
corr(mean AoI, rho) tho                :  -0.2066
                    khu LINK           :  -0.3139
                    khu LINK + T_eff   :  -0.1994
```

Hieu ung **song sot** ca hai phep khu. Gia thuyet (b) khong duoc ung ho:
tuong quan am khong phai chi do do dai epoch. Co che van CHUA RO.

Vi mo hinh rang cua cua Lesson 23.19 gia dinh `corr = 0` chinh xac, dieu nay
phai vao **threats to validity**, khong duoc bo qua.

(`M-86` HIT o muc mau: -0.0573. Muc mau loang hon muc epoch vi bien thien
cua ram trong epoch lan at.)

## 8. `M-87/M-89` MISS: mot su that ve NHAC CU

```text
M-87 ty le MAU trong khoang dai   0.3013%
M-88 ty le KHOANG dai             0.4167%   HIT
M-89 he so length-bias            0.723     <- duoi 1
```

He so duoi 1 la **khong the** voi length-biased sampling that: khoang dai
hon phai chua NHIEU mau hon. Nguyen nhan do duoc: moi link chi co DUNG MOT
khoang dai va do la khoang DAU TIEN, bat dau **1.25 s TRUOC** mau probe dau
tien. Probe khoi dong sau sync agent, nen khoang dai gan nhu khong duoc lay
mau. Day la mot su that ve nhac cu, khong phai ve he thong -- va no cung cung
co H1 mot lan nua.

## 9. T6 -- PROD khong tai lap duoc (L29 dong)

```text
p05 CLEAN   143.69 ms   sd  2.855
p05 PROD    122.52 ms   sd 16.532
sd gap 5.79x
```

Co che (doc tu `sync_agent.py:65`): PROD dung delta-sync
(`reconcile_every = 30`), chi Thing THAY DOI moi duoc day, nen `d` phu thuoc
bao nhieu Thing doi trong chu ky do -- ma cai do phu thuoc tai VA may rui.

```text
PHAN QUYET: mo hinh AoI CHINH lay tu CLEAN.
            PROD bao cao nhu threat to validity, kem CI da do.
            KHONG dung PROD lam mo hinh.
```

Va do la **mot ket qua**, khong phai mot han che:

> delta-sync giam bang thong dieu khien nhung lam san AoI bien thien gap
> 5.79 lan. He chung nhan phu thuoc AoI on dinh nen chay full-push.

## 10. Bang doi chieu du doan

```text
HIT 9 / MISS 10 / ghi lai 1   (tong 20)
```

| ID | dai khoa | do duoc | KQ |
|---|---|---|---|
| M-78 | >= 80% | 100.0% | HIT |
| M-78b | 1-2 | [1, 2] | HIT |
| M-78c | < 0.5 | 0.545 | MISS -- phep kiem khong phan biet duoc (muc 3) |
| M-78d | ~8 | 9 | HIT |
| M-78e | > 0.8 | 1.0000 | HIT |
| M-78f | \|r\| > 0.8 | 0.9387 | HIT |
| M-78g | > 0.8 | 0.4302 | MISS -- gioi han cong suat (muc 4) |
| M-79 | 0.375-0.400 | 0.3952 | HIT |
| M-80 | 360-372 ms | 366.07 | HIT |
| M-81 | ghi lai | 158.99 ms | - |
| M-81b | <= 40 ms | 99.32 | MISS -- estimator dac ta sai (muc 5) |
| M-82 | 2.5-3.5x | 6.08x | MISS |
| M-83 | >= 99.5% | 89.92% (96.61% khu bias) | MISS -- bias nhac cu (muc 5) |
| M-84 | 115-132 ms | 145.50 | MISS -- gop ca estimator sai (muc 5) |
| M-85 | <= 15 ms | 99.32 | MISS -- estimator dac ta sai (muc 5) |
| M-86 | -0.10..-0.02 | -0.0573 | HIT |
| M-87 | 0.8-1.4% | 0.3013% | MISS -- probe khoi dong muon (muc 8) |
| M-88 | 0.40-0.85% | 0.4167% | HIT |
| M-89 | 2.0-3.5 | 0.723 | MISS -- probe khoi dong muon (muc 8) |
| M-90 | 1.3-2.5x | 0.927x | MISS -- ICC = 0, khong co cau truc rho (muc 6) |

Muoi MISS khong phai muoi loi doc lap. Chung gom thanh **nam nguyen nhan**,
va bon trong nam la loi cua BAN KE HOACH chu khong phai cua he thong:

```text
(a) estimator thu ba dac ta sai        -> M-81b, M-84, M-85   [ke hoach sai]
(b) probe khoi dong sau sync agent     -> M-87, M-89          [nhac cu]
(c) phep kiem M-78c khong phan biet    -> M-78c               [ke hoach sai]
(d) gioi han cong suat / do phan giai  -> M-78g, M-83         [nhac cu]
(e) khong co cau truc rho (ICC = 0)    -> M-90                [ket qua THAT]
```

## 11. Mang gi sang Lesson 23.19

```text
1. d = 114.11 ms  (khong phai 51 ms; ty so 2.24x)
   tu hai estimator khop dai luong, lech 10.24 ms
   CAN TREN; bias he thong +50 ms da duoc khu

2. CAT 20 chu ky dau. CV 0.4195 -> 0.3952, null rang cua 0.3667.
   Hon mot nua gap cua M-72b la artifact khoi dong.

3. Lech tuoi giua link KHONG phai ngau nhien: alpha(l) = d_transport(l)
   - mean(d_transport), RMS du 2.47 ms. Neu aoi_model_v7 can tuoi
   theo tung link, dung dong nhat thuc nay chu dung fit lai.

4. corr(AoI,rho) = -0.20 o muc epoch, SONG SOT khu link va khu T_eff.
   Mo hinh rang cua gia dinh 0 -> phai vao threats to validity.

5. Mo hinh lay tu CLEAN. PROD chi bao cao.
```

## 12. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-79 | amendment 23-45 commit RIENG, co tag, truoc moi code | PASS |
| G23-80 | histogram vi tri chu ky overrun, ca 30 run | PASS |
| G23-81 | phan xu H1/H2/AMBIGUOUS tinh bang CONG THUC | PASS -- H1, 100% |
| G23-82 | d_transport / phase tach duoc, moi cai co CI | PASS |
| G23-83 | PC: phase thuoc [0, T_eff] >= 99.5% | FAIL -- 89.92%, nguyen nhan muc 5 |
| G23-84 | ba cach uoc luong d chenh <= 15 ms | FAIL nhu ky; cap KHOP dai luong 10.24 ms |
| G23-85 | L29 (PROD khong tai lap) dong thanh pham vi CO SO | PASS |

`G23-83` va `G23-84` duoc bao cao FAIL, khong duoc lam tron len. Ca hai deu
co nguyen nhan da xac dinh va da ghi; ca hai deu KHONG chan Lesson 23.19,
vi con so mang sang (muc 11) khong phu thuoc vao chung.

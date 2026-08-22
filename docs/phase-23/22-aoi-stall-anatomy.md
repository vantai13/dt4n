# Lesson 23.18 -- Giai phau stall + phan ra `d`

Ngay      : 2026-08-22
Prereg    : `docs/phase-23/00zy-amendment-45.md` (tag `amendment-45`)
Bo sung   : `docs/phase-23/00zz-amendment-45a.md` (tag `amendment-45a`)
SUA       : `docs/phase-23/00zza-amendment-45b.md` -- bug cong thuc null
            `docs/phase-23/00zzb-amendment-45c.md` -- sua ket luan T5
!! Bao cao nay DA DUOC SUA sau ra soat. Muc 3, 4, 5, 7 va bang muc 10
   mang ket qua MOI; ket qua cu duoc giu canh ben de doi chieu.
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
CV CLEAN truoc cat   0.419529
CV CLEAN sau  cat    0.395182     <- M-79 HIT (dai khoa 0.375-0.400)
null rang cua DUNG   0.394289     (amendment 23-45b)
khoang cach          0.000893
                     ^^^^^^^^ ban dau bao cao 0.0285 -- do la BUG cong thuc
                     null (dung p05 lam d), khong phai khoang cach that.
```

**Sau khi cat warm-up, AoI tren `topology_v7` LA MOT RANG CUA SACH.** Ba doi
chung doc lap tren `n = 133.814` mau:

```text
sd Uniform[d, d+500] = 144.3376 ms   vs   sd quan sat = 144.6644 ms
   ty so 1.002265                          LECH 0.23%
CV null dung 0.394289                vs   CV quan sat 0.395182   -> +0.000893
max AoI  1568.9 ms  ->  657.1 ms          DUOI BIEN MAT
ty le khoang refresh dai sau cat = 0.0000%
```

Lesson 23.8 ghi `M-72b` MISS voi gap 0.0522. Gap do la **mot bug cong thuc
cong voi mot transient khoi dong**, khong phai mot tinh chat cua he. Gate do
khong phai ngo cut.

Nhung khop MOMENT khong chung minh la uniform. Kiem HINH DANG:

```text
M-91  KS vs Uniform[115.504, 616.636]  :  D = 0.03093   MISS (nguong 0.03)
      voi n = 133.814, KS rat manh -> D = 0.031 nghia la "rat gan nhung
      phan biet duoc", khong phai "khac xa".
      p05  +3.05 ms | p50  -7.93 ms | p95  -8.98 ms
      -> hoi nen o duoi va o duoi trung vi. Bien do ~2%.
      Gia thuyet: alpha(link) trai 25.95 ms tron 8 rang cua LECH PHA.
      => mo hinh 23.19 CO alpha phai tai tao dung ba so nay. Do la
         positive control THAT cua 23.19, khong phai mot chu thich.
M-92  T tu sd = 501.13 ms  vs  T tu phan vi = 487.77 ms  lech 13.36 ms  HIT
M-97  cat DOI XUNG (bo them 5 chu ky cuoi, transient TAT MAY):
      CV 0.395182 -> 0.395484, delta +0.000302   HIT
      -> chu ky 244 khong lam lech ket luan.
```

Xac nhan DOC LAP cho H1, do tren mot truc khac: sau khi cat warm-up, ty le
khoang refresh dai (`T_eff > 0.55 s`) tut tu 0.4167% xuong **dung 0.0000%**.
Moi khoang dai deu nam trong 19 chu ky dau.

## 4. Q3 -- co che vong PATCH: dong nhat thuc, tich luy phuong sai, vi tri that

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

### Phat bieu lai (amendment 23-45b muc 8)

Dong nhat thuc tren dung **THEO CAU TRUC**: no suy truc tiep tu dinh nghia
`AoI = phase + d_transport`. Phan du cua no do dung MOT thu:

```text
residual(l) = E[phase(l)] - mean_l E[phase]
```

tuc "phase co phan bo giong nhau giua 8 link khong". `RMS 2.473 ms` tren chu
ky `500 ms` = **0.5%** la mot ket qua THAT va TOT, nhung no la kiem tra tinh
NHAT QUAN cua phep phan ra, **khong phai bang chung co che**.

### Bang chung CO CHE thuc su: tich luy phuong sai (M-98, hau nghiem)

Neu `d_transport(l) = sum_{i<=p(l)} tau_i` voi `tau_i` doc lap thi
`E[d] ~ p(l)` VA `Var(d) ~ p(l)`, tuc **`Var` tuyen tinh theo `E`**, va giao
truc `Var = 0` roi vao **vi tri DAU vong lap**:

```text
hoi quy Var(d_transport) theo E[d_transport], 8 link, 15 run moi diem
    R2 = 0.8410
    giao truc Var = 0 tai  151.89 ms
    d_transport nho nhat quan sat duoc  153.78 ms      lech -1.90 ms
    nhieu tuong doi cua moi sd: 1/sqrt(2x14) = 19%
```

Khong mo hinh nao khac -- bat doi xung mang, hang doi, jitter -- cho
`Var ~ E` kem giao truc dung o vi tri dau vong lap.

### Vi tri THAT trong vong PATCH, do chu khong suy (M-99)

Thu tu chen vao `snapshot['things']` la TAT DINH: hosts -> switches -> links
(`collector.py`), va `sync_agent.py:123` duyet `things_now.items()` giu
nguyen thu tu chen. `n_things = 20` voi 8 link, nen link o hang scan `r` co
vi tri toan cuc `p = 12 + r`. Hang scan duoc **DO** tu `scan_offset`:

```text
thu tu scan do duoc : ac, ad, bc, bd, vC, vD, uA, uB

slope d_transport   / vi tri :  3.035 ms   R2 = 0.7120   M-99 HIT
slope visible_offset/ vi tri :  6.109 ms   <- thoi gian mot PATCH
slope scan_offset   / vi tri :  3.075 ms   <- DAU NGUOC lai
kiem nhat quan: 6.109 - 3.075 - 3.035 = -0.001 ms
```

`slope(visible) = 6.109 ms` doi chieu voi `other_ms / 20 = 117.5/20 = 5.87 ms`
do doc lap tu `cycles_*.jsonl`. Hai duong khop trong 4%.

Hai thanh phan DAU NGUOC NHAU dung nhu amendment 23-45 muc 2 du doan, va
bay gio ca hai deu duoc DO rieng.

Ket luan, va no la mot ket qua cho paper:

> **Su khong dong nhat AoI giua cac link bi chi phoi boi vong cap nhat tuan
> tu cua twin, khong phai boi bat doi xung cua mang.**

Va no co he qua thiet ke that: song song hoa vong PATCH se xoa phan lon
trai nay.

**scan_offset la bien DI KEM, khong phai nguyen nhan.** No tuong quan 0.939
voi alpha va thu hang cua no on dinh tuyet doi giua 15 run (`M-78e` = 1.0000)
-- nhung no KHONG vao dong nhat thuc. Ca hai cung tang theo vi tri trong vong
lap nen cong tuyen. Bien dieu khien la `d_transport` (vi tri PATCH).

### `M-78g` MISS la van de CONG SUAT, khong phai co che

```text
khoang cach d_transport giua hai link ke nhau  : 3.52 ms
sd cua d_transport GIUA cac run, nho nhat      : 5.56 ms  (uB: 23.28 ms)
-> sd / khoang cach >= 1.58
```

Thu hang **khong the** on dinh giua cac run khi nhieu lon hon khoang cach can
phan giai -- du co che dung hoan toan. Trung binh 15 run thi on dinh (do la
ly do tuong quan muc trung vi dat 0.9751).

Va con manh hon the: `sd` **khong dong deu** -- no TANG doc vong lap
(5.56 ms o dau -> 23.28 ms o cuoi), dung nhu `Var ~ E` du doan. Nen link o
CUOI vong lap co thu hang bat on dinh HON mot cach he thong.

```text
=> M-78g khong MISS vi "nhac cu yeu".
   No MISS vi H4b DU DOAN no phai MISS.
=> nang cap tu MOT LOI BAO CHUA thanh MOT BANG CHUNG.
```

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

### Bias probe: DO DUOC thay vi gia dinh (M-93)

Hang so `50 ms` la mot GIA DINH (nua khoang probe). Dung sai so 10.24 ms
giua hai duong NHO HON sai so 20% cua chinh hang so do -- tuc "hai duong
doc lap dong y" la CO DIEU KIEN vao con so 50. Nhung bias **do duoc**:

```text
bias = E[t_obs(probe thay lan dau) - t_obs(probe truoc do, cung link)] / 2
     tren 358.590 lan chuyen refresh
M-93 = 53.01 ms   CI95 [52.90, 53.12]     HIT (dai khoa 30-70)
       gia dinh cu 50 ms -> lech +3.01 ms
```

Va phai kiem KHOA PHA: `T = 500 ms`, probe `= 100 ms`, ty so DUNG BANG 5.
Neu pha giua hai vong lap bi khoa trong mot run thi `sd` cua `d_transport`
giua run phai `~ 100/sqrt(12) = 28.87 ms`. Quan sat: 5.56 - 23.28 ms, deu
NHO HON. Pha co randomize mot phan -- **do la ly do duoc phep dung ~50 ms.**

### Bon duong, ba trong do KHONG phu thuoc bias (amendment 23-45b muc 5)

```text
duong                              d (ms)   phu thuoc bias?
quantile_fit (p05, p95)            119.22   khong
moment (mean, sd)                  115.50   khong
decomposition, bias DO DUOC        105.98   co (nhung bias da do)
cycle_trace                        208.30   -- DAC TA SAI, loai
trai cua ba duong dau               13.25 ms   <= 15 ms
```

**CHOT `d` = 115.50 ms** (estimator MOMENT): no dung TOAN BO du lieu chu
khong chi hai phan vi, va khong phu thuoc hang so bias. Lech voi con so
114.11 cua ban bao cao dau la 1.39 ms -- khong doi ket luan nao.

Doi chieu: gia tri dang dung trong pipeline la `d_sync = 51 ms`. Gia tri do
duoc la **115.5 ms**. Ty so **2.26x**.

### No ky thuat: mat phep kiem cheo hai dong ho

Sau khi loai `cycle_trace`, ca ba duong con lai deu den tu CUNG luong probe.
Khong con phep kiem nao qua dong ho phia bridge (monotonic). Neu probe co
bias he thong chung, khong gi phat hien duoc.

```text
Sua bang MOT dong log trong sync_agent: ghi t_patch_done cho TUNG Thing.
=> d_transport(l) = t_patch_done(l) - t_source(l), do phia bridge
=> khoi phuc kiem cheo hai dong ho VA do truc tiep vi tri vong PATCH
Ghi vao backlog Phase 24 (amendment 23-45b muc 10).
```

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

## 7. corr(AoI, rho): KHONG co hieu ung -- va mot khiem khuyet do

> **Muc nay da duoc SUA (amendment 23-45c).** Ket luan cong bo lan dau
> -- *"hieu ung song sot ca hai phep khu, co che chua ro"* -- la SAI.

### Hai loi cong lai

**Loi 1.** `partial_corr_within_epoch` KHONG cat warm-up, khac han `T2` va
`decompose_run` (ca hai deu cat). 2.040 / 28.680 epoch truoc moc cat van
duoc tinh. Chi 7% epoch do da lat DAU cua tuong quan da khu link.

**Loi 2.** `uA` va `uB` co `rho` HONG tren toan bo chien dich:

```text
link         n   n_rho=0    ty le    rho max
ac       35970        46    0.13%    1.0000
uA       35970     35263   98.03%    0.0005   <-- HONG
uB       35970     35232   97.95%    0.0036   <-- HONG
```

`canonical_link_key` xep ten switch truoc nen hai canh bien phia nguon
thanh `link-sA-sSRC` / `link-sB-sSRC`; `util_direction = tx` do chieu
`sA -> SRC`, chieu KHONG co luu luong. Luu luong that co ton tai
(`flows_*/rho_offered_uA.csv` ghi `rho_offered = 0.832`).

Va `uA`, `uB` cung la hai Thing CUOI vong PATCH nen co `d_transport` lon
nhat va AoI cao nhat. Trung hop do mot minh tao ra:

```text
corr GIUA LINK (n = 8):   rho vs AoI = -0.9134
```

### Ket qua DUNG

```text
corr muc epoch, gop 8 link          : -0.3667    <- so nay VO NGHIA
GIUA cac link (n = 8)               : -0.9134    <- confounding
TRONG link (khu bien link)          : +0.0263
TRONG link, bo uA/uB                : +0.0308
K1  corr(rho, T_eff khoang TRUOC)   : +0.0004
K2  khu T_eff khoang truoc          : +0.0263
K3  khu theo 1/dt (quan he ti so)   : +0.0263
```

Quy tac phan xu cua amendment 23-45b muc 7 gia dinh CO mot hieu ung can
giai thich. Tien de do khong duoc thoa, nen quy tac **khong ap dung** --
ghi ro thay vi be quy tac de lay mot phan xu.

```text
PHAN XU: NO_EFFECT_TO_EXPLAIN
=> corr(AoI, rho) RA KHOI threats to validity.
=> Gia dinh corr = 0 cua mo hinh rang cua 23.19 duoc BIEN MINH bang so do,
   khong con phai "bo qua".
=> Gia thuyet (b') (artifact estimator co cua so) KHONG CAN den: K1 = +0.0004.
```

Thay vao do, so threats to validity nhan MOT MUC MOI:

```text
L30  rho cua uA va uB do SAI CHIEU trong toan bo chien dich 23.8.
     KHONG anh huong AoI (AoI la hieu hai dau thoi gian, khong dung rho).
     Anh huong moi phan tich dung rho THEO TUNG LINK tu twin.
     Sua canonical_link_key hoac chon chieu truoc Phase 24.
```

### Vi sao loi nay khong bi bat som hon

`M-86` (muc mau, da cat warm-up, GOP link) do duoc `-0.0573` va **HIT** dai
khoa `-0.10..-0.02`. Dai khoa do lay tu Lesson 23.8 -- ma 23.8 cung do tren
du lieu co cung khiem khuyet.

> **Mot du doan duoc xac nhan boi chinh cai loi da sinh ra no.**
> Day la ly do vi sao HIT khong bao gio la bang chung du.

Phep kiem da bat duoc no: **tach BEN TRONG don vi va GIUA cac don vi**. Neu
hai cai khac dau hoac khac do lon nhieu, gan nhu chac chan co confounding.

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

## 9. T6 -- PROD khong tai lap duoc (L31; xem canh bao va cham ma o duoi)

> **Va cham ma ID.** Ban ke hoach 23.18 goi han che nay la `L29`. Nhung
> trong repo, `L29` DA duoc dung cho mot han che khac:
> `docs/phase-23/11-abstain-cost.md:372` -- *"c_F1 duoc tinh tren ca luoi
> nhung `wait_s` cua F3 chi duoc danh gia o DIEM"*. `L29` cua ban ke hoach
> thuoc he danh so cua `PHASE_23_v3.md`, mot tai lieu NGOAI repo.
> De tranh hai han che khac nhau mang cung mot ma, han che ve PROD duoc cap
> ma **`L31`** trong repo. `G23-85` giu nguyen noi dung.
>
> `GATES.md` muc "Ghi chu ve pham vi ID" da du lieu truoc kha nang nay va de
> xuat tao `LIMITS.md` rieng. Va cham nay la bang chung rang no can duoc tao;
> viec do NAM NGOAI Lesson 23.18.

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

### Vong hai (amendment 23-45b va 23-45c)

```text
HIT 7 / MISS 2   (tong 9)
```

| ID | dai khoa | do duoc | KQ |
|---|---|---|---|
| M-91 | KS D < 0.03 | 0.03093 | MISS -- gan sat, xem muc 3 |
| M-92 | T lech < 20 ms | 13.36 ms | HIT |
| M-93 | bias DO DUOC 30-70 ms | 53.01 ms | HIT |
| M-94 | K1 < -0.3 | +0.0004 | MISS -- khong co ghep noi de tim |
| M-95 | K2 \|r\| < 0.10 | +0.0263 | HIT |
| M-96 | K3 \|r\| < 0.10 | +0.0263 | HIT |
| M-97 | delta CV < 0.005 | +0.000302 | HIT |
| M-98 | R2 > 0.7 (hau nghiem) | 0.8410 | HIT |
| M-99 | slope 3-9 ms/vi tri | 3.035 ms | HIT |

Hai MISS cua vong hai deu la MISS "tot":

```text
M-91  D = 0.031 voi n = 133.814. KS o co mau nay phan biet duoc lech 2%.
      Lech do la THAT va DA DINH DANH (alpha tron 8 rang cua lech pha)
      -> thanh positive control cho 23.19 chu khong phai mot bi an.
M-94  du doan corr(rho, T_eff truoc) < -0.3 gia dinh CO ghep noi.
      Do duoc +0.0004: khong co gi de tim. Tien de sai, khong phai co che sai.
```

### Vong mot

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
1. d = 115.50 ms   (estimator MOMENT; khong phu thuoc hang so bias)
   T = 501.13 ms
   Ba duong doc lap voi bias trai 13.25 ms.
   Gia tri cu trong pipeline 51 ms -> ty so 2.26x.

2. CAT 20 chu ky dau (va nen cat doi xung 5 chu ky cuoi -- delta CV
   +0.000302, khong doi ket luan).
   Sau khi cat: AoI LA RANG CUA SACH.
       sd lech 0.23% so voi Uniform[d, d+500]
       CV lech 0.000893 so voi null DUNG
   => KHONG can thanh phan duoi, KHONG can renewal ngau nhien.
   => Bo lua chon C (empirical renewal replay) cua PHASE_23_v3.

3. MO HINH:  z(t) = d + alpha(link) + phase(t),  phase ~ Uniform[0, T]
   alpha da do, bien do 25.95 ms, dong nhat thuc RMS du 2.47 ms.
   Dung dong nhat thuc, DUNG fit lai.

4. SELFCHECK cua aoi_model_v7 phai tai tao:
       mean 366.070 ms   sd 144.664 ms   CV 0.395182   p05 143.612 ms
   VA hinh dang: p05 +3.05 / p50 -7.93 / p95 -8.98 ms so voi Uniform thuan.
   Ba so lech nay la POSITIVE CONTROL: mo hinh CO alpha phai sinh ra chung,
   mo hinh KHONG co alpha thi khong.

5. corr(AoI, rho) trong tung link = +0.0263 ~ 0.
   Gia dinh corr = 0 duoc BIEN MINH. KHONG con o threats to validity.

6. Mo hinh lay tu CLEAN. PROD chi bao cao (sd gap 5.79x).

7. NO MANG THEO:
   L30  rho cua uA/uB do sai chieu -> moi phan tich dung rho theo link
   Phase 24: log t_patch_done tung Thing -> khoi phuc kiem cheo hai dong ho
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
| G23-85 | L31 (PROD khong tai lap; ke hoach goi la L29) dong thanh pham vi CO SO | PASS |

`G23-83` va `G23-84` duoc bao cao FAIL, khong duoc lam tron len. Ca hai deu
co nguyen nhan da xac dinh va da ghi; ca hai deu KHONG chan Lesson 23.19,
vi con so mang sang (muc 11) khong phu thuoc vao chung.

### Gate cua vong ra soat (23.18b)

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-86 | null rang cua tinh DUNG; khoang cach CV <= 0.005 | PASS -- 0.000893 |
| G23-87 | d chot qua >= 3 duong doc lap voi bias, trai <= 15 ms | PASS -- 13.25 ms |
| G23-88 | co che vong PATCH duoc DO (Var~E va vi tri that) | PASS -- R2 0.841 / 0.712 |
| G23-89 | corr(AoI,rho) TRONG link, sau cat warm-up | PASS -- +0.0263 |
| G23-90 | KS hinh dang vs Uniform[d, d+T], D < 0.03 | FAIL -- 0.03093 |

`G23-90` FAIL la mot FAIL CO GIA TRI: no do duoc mot lech 2% da dinh danh
duoc (alpha tron 8 rang cua lech pha), va lech do tro thanh positive control
cho Lesson 23.19.

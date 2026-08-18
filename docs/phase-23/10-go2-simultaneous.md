# Lesson 23.5[C] -- Dai tin cay DONG THOI va dong no GO-2

Ngay chay: 2026-08-18
Thu tuc khoa tai: `docs/phase-23/00y-amendment-24.md` (C-D1..C-D6).

Input: `results/phase-22/calib_set_v3_{poisson_0.925,poisson_0.850,h2_0.700}.parquet`
Output: `results/phase-23/go2_simultaneous_<cell>.json`
Code: `cert/go2_simultaneous.py`. `cert/conformal_simultaneous.py` KHONG bi sua.

---

## 0. Ket luan mot dong

**GO-2 SONG SOT sau hieu chinh dong thoi** (`C-5` dat). Nhung **loi ich cua
tuong quan nho hon du bao 4 lan**: `c_supt` chi thap hon Bonferroni `3.8-7.2%`,
khong phai `22%`. `C-1` va `C-3` deu MISS, va ly do la mot phat hien that.

---

## 1. Bon cong -- doc truoc, ket luan sau

### 1.1. NC-C-1 -- ghep cap, ca ba variant

Bootstrap `maxscore` vs CHINH no, cung draw. Ghep cap nguyen ven <=> `delta = 0`
chinh xac o moi draw.

```text
cell             variant A      variant B      variant C
poisson@0.925    w=0.0e+00 OK   w=0.0e+00 OK   w=0.0e+00 OK
poisson@0.850    w=0.0e+00 OK   w=0.0e+00 OK   w=0.0e+00 OK
h2@0.700         w=0.0e+00 OK   w=0.0e+00 OK   w=0.0e+00 OK
```

Doi chieu duong ong Phase 22 tren cung phep do (do truoc khi viet `[C]`):

```text
variant   max|delta_mean|    max CI width
B           0.000000e+00     0.000000e+00     PASS
C           0.000000e+00     0.000000e+00     PASS
A           7.992773e-02     4.235592e+00     FAIL -- CI rong 4.24 ms cho hieu
                                              cua mot thu tuc VOI CHINH NO
```

Nguyen nhan da xac nhan tren code: `_reduce_block_arrays` tieu thu `rng` o
variant A, va `maxscore` goi no MOT lan (`sim_blocks`) trong khi
`bonferroni`/`sidak` goi BA lan (moi slot mot lan) -- nen khac ca SO LUOT rut.

Sua o `C-D6`: chon MOT chi so hang moi (bin, block-instance) o cap `bootstrap_deltas`,
roi TRUYEN VAO moi thu tuc. Ghep cap thanh tat dinh.

**Loi thu hai, nang hon, phat hien khi sua:** duong ong cu rut DOC LAP cho tung
cot, nen `s_sim` den tu hang 17 con `s_pair_2` den tu hang 4 cua cung block.
Rang buoc `s_sim = max_j s_pair_j` -- da kiem chung dung tren 100% hang that --
bi PHA VO. Do khong phai loi ghep cap giua hai thu tuc, do la pha vo rang buoc
TRONG MOT HANG. Duong ong moi doc ca hang tu mot ma tran `(n_rows, m+1)`, chot
bang `test_C10`.

Artifact Phase 22 dung `variant = "B"` nen KHONG bi anh huong.

### 1.2. PC-C-1 -- doi chung duong, DA THIET KE LAI

Thiet ke dau tien ("cong 1 ms vao moi delta, doi moi o loai tru 0") **DO** tren
du lieu that: `22/24` va `16/24`. Chan doan cho thay HAI khiem khuyet doc lap,
ca hai deu la loi cua thiet ke chu khong phai cua cai dat:

```text
(1) LOI DEM.  No dem `lo > 0`, tuc "khoang nam hoan toan ben DUONG", chu khong
    phai "khoang KHONG chua 0".  Tam o slot 1 co point ~ -2.4..-2.8 ms DA loai
    tru 0 tu phia AM va bi dem nham la truot:

      bin0 bonferroni slot1  point=-2.6324  sigma=0.1145
      bin1 sidak      slot1  point=-2.7671  sigma=0.1325
      ... (8 o, tat ca deu la slot 1)

(2) LOI THIET KE.  Mot phep cong HANG SO khong phai doi chung duong hop le khi
    uoc luong diem trai tu -2.8 den +1.6 ms: no day mot so o RA XA 0 va mot so
    o LAI GAN 0.  Voi o co point = -1.0 ms, cong dung 1 ms lam no THANH 0 --
    thiet ke tu tao ra that bai.  MOT CAI DAT DUNG VAN TRUOT.
```

Cung ho loi voi tieu chi MC `"do rong ~ 1/sqrt(B)"` o Lesson 23.5[B]: **nguong
khong duoc dan tu mot hang so tuy y, no phai dan tu do phan giai cua chinh phep
do.**

Thiet ke lai -- bom tin hieu theo DON VI `sigma_hat`, va kiem CA HAI PHIA:

```text
draws = (delta - dbar) + s * sigma_hat        # dat lai tam ve null
point = s * sigma_hat
=> lo_k = (s - c) * sigma_k   =>  loai tru 0  <=>  s > c

s = c + 0.5  ->  PHAI loai tru 0 o CA 24 o
s = c - 0.5  ->  PHAI KHONG loai tru 0 o o nao
```

Doi chung moi MANH HON cai cu (hai phia thay vi mot phia) va hieu chinh theo
thang nhieu cua chinh du lieu. Ket qua:

```text
cell             s=c+0.5   s=c-0.5   pass    MDE ms (min / median / max)
poisson@0.925    24/24        0      True    -2.790 /  0.014 /  0.791
poisson@0.850    24/24        0      True    -1.466 / -0.406 /  0.241
h2@0.700         24/24        0      True    -2.925 / -1.901 /  0.405
```

`MDE` (minimum detectable effect) am nghia la o do **da** loai tru 0 truoc khi
bom tin hieu. `MDE` duong lon nhat la `0.79 ms`: do la thang phan giai that su
cua dai dong thoi tren cell chinh.

### 1.3. Hoi tu Monte Carlo -- tieu chi DA SUA (chi cell chinh)

```text
B       c_mean    c_sd      width_mean
200     2.8464    0.08027   1.24701
2000    2.9028    0.03129   1.26569

width_relative_change = 0.0150   <= 0.10   PASS   (do rong ON DINH)
mc_error_shrink       = 2.565    >= 1.8    PASS   (ky vong 3.162)
```

Dung nhu Lesson 23.5[B] da xac lap: **do rong dai KHONG co theo `1/sqrt(B)`**
(`1.247 -> 1.266`, gan nhu hang so, dinh boi `n_block = 500`), con **sai so MC
cua dau mut thi CO** (`0.0803 -> 0.0313`, co `2.57x`).

### 1.4. C-D5 -- bang chung `B = 200` khong du

```text
cell             n_contains_zero tren 10 seed              range   sd
poisson@0.925    [6, 9, 7, 7, 8, 8, 5, 7, 8, 8]              4     1.16
poisson@0.850    [5, 5, 5, 5, 5, 4, 5, 5, 4, 4]              1     0.48
h2@0.700         [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]              0     0.00
```

Tren cell chinh, dai luong headline dao dong `5..9` tren `24` o chi vi doi seed.
Con so `5/24` trong artifact `go2_fwer_restatement.json` da commit (`B = 200`)
duoc **RUT LAI** theo NT-v2-7.

---

## 2. Ket qua -- `c_supt` va hai MISS

```text
cell             c_supt   c_bonferroni   c_sidak   supt/bonf   supt/1.96
poisson@0.925    2.9051      3.0781      3.0708     0.9438      1.4822
poisson@0.850    2.8572      3.0781      3.0708     0.9282      1.4578
h2@0.700         2.9623      3.0781      3.0708     0.9624      1.5114
```

```text
C-1  c_supt in [2.2, 2.7]        -> do 2.8572 .. 2.9623      MISS (cao hon dai)
C-2  c_bonferroni = 3.078088     -> khop chinh xac            dat (hang so)
C-3  supt/bonf in [0.71, 0.88]   -> do 0.9282 .. 0.9624      MISS (cao hon dai)
```

### 2.1. Vi sao MISS -- cau truc tuong quan, do duoc

`C-1` gia dinh 24 dai luong tuong quan MANH (chung block, chung slot), nen
max-t se re hon Bonferroni nhieu. Do lai ma tran tuong quan tren 1000 draw:

```text
cap                                  n    corr trung binh
cung bin & cung slot (bonf vs sidak) 12       +0.9889
cung slot, khac bin                  72       +0.3554
khac slot                           192       -0.2043      <- AM
--------------------------------------------------------------
trung binh toan bo ngoai duong cheo           -0.0064

so chieu hieu dung (Kaiser, eig > 1) = 6 / 24
eigenvalue top-5 = [6.295, 5.502, 2.594, 2.285, 1.725]
```

Doc bang nay:

```text
* Chi co MOT cap thuc su du thua: (bonferroni, sidak) trong cung o, corr 0.989.
  Hai thu tuc nay gan nhu la MOT dai luong -- dung nhu Amendment 23-24 da ghi:
  alpha/3 = 0.03333 va 1-(0.9)^(1/3) = 0.03451 chi cach nhau 3.5%.

* Giua cac SLOT, tuong quan AM (-0.204).  Tuong quan am lam thong ke MAX LON
  HON, khong nho di -- no CHONG LAI loi ich cua sup-t.

* Hai hieu ung gan nhu triet tieu nhau: du thua theo cap keo c_supt xuong,
  tuong quan am day no len.  Ket qua rong: c_supt chi thap hon Sidak 5.4%.
```

Co che cua tuong quan am giua cac slot: moi `delta_j = qhat_j - qhat_maxscore`
tru CUNG mot so hang `qhat_maxscore`, ma so hang do duoc quyet dinh boi
`s_sim = max_j s_pair_j`, tuc bi chi phoi boi slot LON NHAT. Khi mot draw lam
slot 3 nang len, `qhat_maxscore` tang theo, keo `delta_1` xuong trong khi
`delta_3` len. Do la nguon tuong quan am co he thong giua slot thap va slot cao.

### 2.2. Cau chuyen da du dinh viet -- KHONG viet duoc

Amendment 23-24 muc 5.1 du dinh:

> *"mot dai tin cay dong thoi can he so `2.4` thay vi `3.08` cua Bonferroni --
> hep hon `22%` -- vi 24 dai luong suy luan tuong quan manh. Day la cung mot co
> che, o tang meta, voi ly do max-score vuot Bonferroni."*

**Cau do sai ve dinh luong.** Do duoc `5.4%`, khong phai `22%`. Cau dung:

> *"O tang suy luan, 24 uoc luong delta chi tuong quan YEU: he so toi han sup-t
> la `2.86-2.96` so voi `3.071` cua Sidak, tuc chi hep hon `3.5-7.0%`. Tuong
> quan manh lam max-score vuot Bonferroni o tang SCORE KHONG chuyen sang tang
> uoc luong bootstrap. Phep tuong tu giua hai tang la ve CAU TRUC
> (`max_k |d_k|/sigma_k` giong `max_j s_j/sigma_j`), khong phai ve DO LON."*

Ghi vao so MISS: `"cau chuyen max-t re hon Bonferroni 22% o tang meta"` -- SAI,
do nguoi huong dan de xuat va nguoi thuc hien khong kiem truoc khi khoa dai.

---

## 3. C-4 -- containment, bat bien cau truc

```text
cell             percentile   normal   supt   C4_monotone
poisson@0.925         7          7      12       True
poisson@0.850         5          5       6       True
h2@0.700              6          6       8       True
```

`C-4` dat o ca ba cell. Nho ba khoang duoc bao cao (Amendment 23-24 muc 1.1),
`C-4` duoc phat bieu tren cap CUNG CAU TRUC (`normal` vs `supt`) chu khong tren
`percentile` vs `supt`. Neu so nham cap, `C-4` co the truot vi bat doi xung cua
khoang percentile chu khong phai vi code sai.

Ghi nhan: `percentile` va `normal` trung nhau o ca ba cell (`7/7`, `5/5`,
`6/6`), tuc phan phoi bootstrap cua cac delta gan doi xung -- `max_abs_skew_shift`
nho. Vay o lan nay hai cap cho cung ket luan; nhung viec tach ba khoang van la
dieu kien de PHAT BIEU duoc `C-4`, khong phai mot buoc thua.

---

## 4. C-5 -- KET LUAN GO-2

Dau cua 24 delta duoi dai DONG THOI 95%:

```text
poisson@0.925   slot1: 8 zero              slot2: 4 pos, 4 zero    slot3: 8 pos
poisson@0.850   slot1: 8 neg               slot2: 1 pos, 1 neg, 6 zero  slot3: 8 pos
h2@0.700        slot1: 8 neg               slot2: 8 zero           slot3: 8 pos
```

**`C-5` DAT: phat bieu "thu tu FWER phu thuoc slot" SONG SOT sau hieu chinh
dong thoi.** Bang chung manh nhat la slot 3: `8/8 pos` o CA BA cell, nghia la
`qhat_bonferroni` va `qhat_sidak` RONG HON `qhat_maxscore` o rank slot cao nhat
mot cach co y nghia dong thoi. Va slot 1 di theo huong NGUOC LAI (`neg` o hai
cell, `zero` o cell chinh). Khong ton tai mot thu tu toan phan.

Pham vi phat bieu duoc phep (ghi vao artifact):

```text
"Dai sup-t bao dam DONG THOI cho ca 24 dai luong o muc 0.95. Thu tu FWER duoc
 phat bieu THEO SLOT; khong duoc neu mot thu tu toan phan."
```

### 4.1. Cau KHONG duoc viet

```text
KHONG: "bonferroni rong hon maxscore".  Chi dung o slot 3 (8/8), va NGUOC LAI
       o slot 1 tren hai cell (8/8 neg).  Do chinh la noi dung cua GO-2.

KHONG: "slot 2 khong khac 0".  Tren poisson@0.925 co 4/8 o la pos.  Dung la
       "slot 2 khong tach duoc nhat quan giua cac cell".

KHONG: dung con so 5/24 cu.  Da RUT LAI (muc 1.4).
```

---

## 5. So MISS cua Lesson 23.5[C]

```text
C-1  c_supt in [2.2, 2.7]              MISS -- do 2.857..2.962
C-3  supt/bonf in [0.71, 0.88]         MISS -- do 0.928..0.962
"max-t re hon Bonferroni 22%"          SAI  -- do 5.4%; cau chuyen dinh luong
                                              khong ton tai
PC-C-1 "cong 1 ms, doi lo > 0"         SAI  -- hai khiem khuyet doc lap (muc 1.2)
n_contains_zero = 5/24 (B=200)         RUT LAI -- khong on dinh
```

`C-1` la dong confirmatory chinh cua `[C]` va no MISS. Nhung MISS nay mang
thong tin: no do duoc rang cau truc tuong quan o tang suy luan KHAC han o tang
score, va no dan ra ma tran tuong quan o muc 2.1 lam bang chung.

---

## 6. Trang thai ba mon no

```text
GO-1  Lesson 23.5[B]  DAT   ratio AURC[0.6,1] C3/C0, CI95_high max = 1.003173
                            (Bonferroni 3 cell: 1.004125), 3/3 cell danh gia duoc
GO-2  Lesson 23.5[C]  DAT   "thu tu phu thuoc slot" song sot dai dong thoi 95%
                            tren 24 dai luong, 3/3 cell
GO-3  Lesson 23.5[A]  DONG  studentized max-score, nhan EXPLORATORY
```

Lesson 23.5 dong hoan toan.

## 7. Chuyen giao cho Lesson 23.6

Ha tang thong ke da xay xong va dung lai duoc:

```text
supt_band()               dai dong thoi cho BAT KY vector dai luong nao
bootstrap_deltas()        paired block bootstrap, draw TOAN CUC
three_interval_table()    ba khoang, de moi so sanh deu CUNG cau truc (NT-v2-6)
negative_control_self_delta()  NC tu than, bat loi ghep cap
positive_control_shift()  PC hai phia, hieu chinh theo sigma
mc_convergence()          tieu chi DA SUA, hai menh de tach roi
```

`R-23.6-1` (Amendment 23-21 muc 5.3) du bao `kappa = 1` bao thu qua muc `~30`
lan va argmin cua `risk_system` nam o `kappa < 1`. Khi quet `kappa`, moi diem
tren duong bien deu can CI, va do la mot ho dai luong doc DONG THOI -- tuc dung
`supt_band()` chu khong phai 20 khoang tung-diem.

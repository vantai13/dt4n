# Phase 20R.7 -- Mechanism Map

Trang thai: DONG.
Amendment lien quan: 00p-15, 00q-16, 00r-17, 00s-18.

## 0. Tom tat mot doan

Lesson 20R.7 xac dinh KENH va DANG TOAN cua co che sinh loi quyet dinh, va
BAC BO hai cach dinh vi `err` theo canh quan chi phi.

```text
Xac dinh duoc  : co che K4 cascade = ro ri phi tuyen + CLIPPING vat ly loss>=0
                 kenh loss chi phoi do cong chi phi (P3, 17/17 o)
                 nguong chuyen kenh phu thuoc bang thong (phat hien moi)
Bac bo         : P1 ban kinh le tho     (p = 0.085491)
                 P2 vi tri dinh do cong (lech 4.5 buoc luoi)
Khong kiem duoc: argmax do cong cua h2  (khong phan giai duoc)
                 argmax err cua h2      (nam o mep trai)
```

## 1. Estimand

```text
cost = delay + w_loss * loss
```

Khong dung `d2(delay)/d(rho)^2` lam hinh chinh (Amd 15 sec.1). Ly do da duoc
xac nhan bang so o sec.5: kenh loss lon hon kenh delay tu 3.74x den 3955.60x
tren moi o co y nghia.

## 2. K4 Gap Mechanism

Tai `rho_bar=0.925`, path cost baseline:

```text
poisson:  P1 = 112.9658  P2 = 174.1808  P3 = 120.5115  P4 = 146.5933
          khe nho nhat = |P1-P3| = 7.5457
h2     :  P1 = 745.4047  P2 = 1005.9540  P3 = 848.0640  P4 = 986.3044
          khe nho nhat = |P2-P4| = 19.6496
```

Scan cascade lam `poisson@0.925` doi ranking:

```text
P1,P3,P4,P2 -> P3,P1,P4,P2
```

K4 gay dung o cap co khe quyet dinh nho nhat cua o binding.

## 3. Cong thuc bac nhat khong-clip KHONG phai co che

```text
S_P = sum_i prod_{j != i}(1 - p_j)
d(gap_ab)/d(delta) = w_loss * (S_a - S_b)
delta*_ab = |gap_ab| / (w_loss * |S_a - S_b|)

poisson first-order best = P2/P4, r*_path = 1.533354
h2      first-order best = P3/P4, r*_path = 1.398990
scan    r* = 0.008868, cap gay = P1/P3
```

Lech ~173x. Cong thuc khong-clip duoc giu nhu chan doan, KHONG duoc bao cao
nhu closed-form cua `r*`. Guard: `test_unclipped_first_order_is_not_the_k4_mechanism`.

## 4. Clipped Piecewise Mechanism -- ket qua co che chinh

```text
sign = -1, r_path = 0.008868, per_link_shift = -0.002956, clip_events = 4/12
link bi clip: uA loss = 0.000536, vC loss = 0.000536

p'_i      = max(p_i - x, 0)
loss_P(x) = 1 - prod_i (1 - p'_i)
cost_P(x) = delay_P + w_loss * loss_P(x)

giai cost_P1(x) = cost_P3(x):
  x_link*      = 0.002936189839
  r_path*      = 3 * x_link* = 0.008808569518
  scan bracket = [0.008804852308, 0.008868196569]   -> NAM TRONG
```

K4 cascade khong chi do leak tuyen tinh cua common-mode qua composition phi
tuyen; no do leak phi tuyen CONG VOI clipping vat ly o mien loss >= 0.

Hinh 1 cho thay ca ba dac diem: duong `P1-P3` gay khuc (moi cho gay = mot link
cham day 0), cat truc 0 dung tai bracket scan, roi PHANG khi ca ba link da bi
clip (landscape bao hoa, bom them nhieu khong con tac dung).

Kiem du doan Amd 15 sec.8, ky truoc khi chay B.3:

```text
[PASS] cap mong manh nhat poisson@0.925 = P1/P3
[PASS] cap mong manh nhat h2@0.925      = P2/P4
[PASS] ti so r*_quet / r*_giai_tich = 1.006769, trong [0.8, 1.3]
       (lech tuong doi 0.68%)
```

## 5. Ban do co che (Amendment 16)

Estimator: danh gia TAI NUT LUOI, `h = buoc luoi = 0.02`. Ly do sua: bang tra
tuyen tinh tung khuc nen `h = 0.01` bien `d2` thanh ban do vi tri nut. Chi tiet
va bang chung so: `00q-amendment-16.md` sec.1.

```text
grid step = 0.0200   h_primary = 0.0200   h_robust = 0.0400
truth-table crosscheck: 150 nut, max abs diff = 0
modes excluded: cbr (Amd 15 sec.6)
```

### 5.1 Nguong chuyen kenh -- PHAT HIEN MOI

```text
R(rho) = |w_loss * d(loss)/d(rho)| / |d(delay)/d(rho)|,  rho_cross tai R = 1

poisson  bw=4 q=10   rho_cross = 0.6653   max R =  32.68
poisson  bw=6 q=13   rho_cross = 0.7375   max R =  30.54
poisson  bw=8 q=18   rho_cross = 0.8216   max R =   8.44
h2       bw=4 q=10   rho_cross = none     max R = 143.56
h2       bw=6 q=13   rho_cross = none     max R = 134.45
h2       bw=8 q=18   rho_cross = 0.5887   max R =  66.02
```

Link cang hep (q cang nho) thi chuyen sang che do loss-chi-phoi cang som. Voi
`h2`, hai cau hinh hep khong co diem chuyen: loss chi phoi tren TOAN dai do.

Day la dai luong mo ta, KHONG phai gia thuyet tien dang ky.

### 5.2 Do phan giai cua do cong

```text
poisson  bw=4 q=10   21 nut,  0 vuot nguong 2*SE  -> khong cong bo argmax
poisson  bw=6 q=13   26 nut,  5 vuot nguong,  argmax 0.980
poisson  bw=8 q=18   22 nut,  3 vuot nguong,  argmax 0.940
h2       bw=4 q=10   21 nut,  4 vuot nguong,  argmax 0.800
h2       bw=6 q=13   26 nut,  1 vuot nguong,  argmax 1.020
h2       bw=8 q=18   22 nut,  4 vuot nguong,  argmax 0.900

kiem ben vung stride 1 vs stride 2:
  poisson  2/2 on dinh  -> argmax CONG BO DUOC
  h2       2/3 on dinh  -> argmax KHONG cong bo duoc
```

Do cong loss chi do duoc o `rho` cao. O `rho` thap, `loss * n_pkt < 10` nen so
do la nhieu dem goi, khong phai phep do. Muon nghien cuu co che o tai thap phai
TANG `n_pkt`, khong phai tang so diem `rho`.

`h2` khong phan giai duoc dinh do cong. Dieu nay khop H7
(`h2 peak below left edge PARTIAL`) -- hai phuong phap doc lap, cung chan doan.

## 6. Ban kinh le quyet dinh r(s) (Amendment 17)

```text
r(s) = (cost_second - cost_best) / (2 * ||grad_rho cost||)
nguon chi phi : MEASURED truth table (khong phai twin)
gradient      : doc doan chinh xac cua noi suy tuyen tinh, khong sai phan
w_loss        : theo TUNG cell, khong dung hang so cua rho_bar=0.925
diem van hanh : z = 0.55, n = 200000, seeds 101-105, tau = 1.0
```

Ghi chu sua so voi ban nhap: sec.7 ban nhap ghi `err(z=0.3)`. `z=0.3` chua bao
gio duoc ky. Amd 17 sec.5 chot `z = 0.55` vi do la diem van hanh dung cho G1,
G2, G7 va nhanh 20R.8.

```text
mode     rho_bar  w_loss   median r(s)  median margin  P[r<sigma]
poisson  0.700    1656.4   0.030707     1.5210         0.6892
poisson  0.850    2424.4   0.013001     8.7647         0.9997
poisson  0.925    3222.2   0.008037    20.7039         0.9453
poisson  0.960    3655.9   0.005040    21.4336         0.8142
h2       0.700    2861.4   0.014931    21.3674         0.9742
h2       0.850    4021.4   0.018451    77.7465         0.9175
h2       0.925    4515.9   0.018213   100.1677         0.6106
h2       0.960    4722.7   0.018802   116.4029         0.0826
```

Pham vi: `ar1_matrix` chi gieo theo `seed`, nen `poisson` va `h2` tai cung
`rho_bar` dung chung quy dao rho. Tam o KHONG phai tam quan sat doc lap;
p-value hoan vi la lac quan.

## 7. Phan xu ba du doan Amd 15 sec.7

### P1 -- KHONG DUOC UNG HO

```text
Spearman(median r(s), err) = -0.547619   n = 8   p_one_sided = 0.085491
poisson rieng: -0.200000    h2 rieng: -0.800000
```

Dau dung, do manh khong du. Ap dung dieu khoan Amd 15 sec.7: ban do co che
khong ung ho giai thich `err` bang ban kinh cost-margin. `r(s)` KHONG duoc dinh
nghia lai, kenh KHONG doi, khong them bien the.

### P2 -- KHONG DUOC UNG HO

P2 nhu da viet la ill-posed: `err` chi so theo `rho_bar`, ban do chi so theo
`rho_link = rho_bar + LINK_OFFSET`, va mot duong cong `(bw,q)` phuc vu toi 5
link co offset khac nhau nen argmax khong co anh nguoc duy nhat. Amd 18 dua do
cong len MUC DUONG, truc `rho_bar`.

```text
mien hop le rho_bar = [0.5875, 0.9575], siet boi link `ad`
o do rho_bar = 0.960 nam NGOAI mien -> khong tinh duoc do cong

poisson: argmax err       = 0.850 (interior, nhan dang duoc)
         argmax do cong   = 0.940 cho CA BON duong P1..P4
         lech = 0.090 = 4.5 buoc luoi  >> 1  -> KHONG thang hang
h2     : argmax err       = 0.700 (mep trai) -> KHONG NHAN DANG DUOC
         P2 khong kiem duoc cho h2

so o thang hang = 0, yeu cau >= 3
```

Ket qua rat on dinh (4/4 duong cung cho 0.940), nen day la PHU DINH RO RANG,
khong phai thieu du lieu: noi do cong loss lon nhat KHONG phai noi `err` lon
nhat. `err` dat dinh SOM hon dinh do cong 4.5 buoc luoi.

### P3 -- DUOC UNG HO

```text
17/17 o co y nghia thoa |w_loss * d2 loss| > |d2 delay|
ti so: min = 3.74, median = 55.68, max = 3955.60
```

Xac nhan quyet dinh doi estimand cua Amd 15 la dung: neu giu ke hoach cu, hinh
co che chinh se ve dai luong nho hon dai luong that tu 4 den 4000 lan.

## 8. Ket luan Lesson 20R.7

Lesson 20R.7 xac nhan KENH cua co che (loss, khong phai delay) va DANG TOAN cua
no (piecewise + clipping). No BAC BO hai cach dinh vi `err` theo canh quan chi
phi: vi tri dinh do cong, va trung vi ban kinh le.

Dieu nay khong mau thuan voi H8 da PASS. H8 dung `R = sd(margin)/mean(margin)`,
mot TI SO KHONG THU NGUYEN, va cho `Spearman(R, err) = 1.000000`. Lesson 20R.7
dung cac dai luong THO, CO THU NGUYEN, mang tinh VI TRI.

```text
Ket luan gop: `err` duoc du bao boi thong ke le DA CHUAN HOA,
khong phai boi hinh dang cuc bo cua duong cong chi phi.
```

Day la ket luan manh hon ke hoach ban dau vi no LOAI TRU hai gia thuyet canh
tranh chu khong chi khang dinh mot cai.

## 9. Muc tham do -- KHONG phai ket qua Phase 20R

Sau khi P1 that bai, mot dai luong khac to ra lien he rat manh voi `err`:

```text
P[ r(s) < sigma_rho ]  vs  err
Spearman = +1.000000 chinh xac tren ca 8 o, p = 2.48e-05
poisson rieng: +1.0   h2 rieng: +1.0
```

Day la QUAN SAT POST-HOC, sinh ra SAU khi thay P1 that bai. No KHONG duoc tinh
la bang chung cua Phase 20R. Ly do co the: `err` la dai luong DUOI (xac suat
vuot nguong) con `median` la dai luong TRUNG TAM; va `r(s)` tho co thu nguyen
trong khi `sigma_rho` chenh 5 lan giua cac o (0.0096 den 0.0480).

De tro thanh ket qua, no phai duoc TIEN DANG KY o mot Lesson sau va kiem tren
cell/seed CHUA DUNG. Hinh cua no duoc luu rieng
`figures/exploratory_margin_exceedance.png`, khong dung tien to `mechanism_`.

## 10. Artifacts

```text
results/phase-20R/mechanism_k4_closed_form.json
results/phase-20R/mechanism_maps.json
results/phase-20R/margin_radius.json
results/phase-20R/mechanism_predictions.json

measurements/mechanism_map.py            (K4 closed form)
measurements/mechanism_maps.py           (Amd 16 maps)
measurements/margin_radius.py            (Amd 17 r(s))
measurements/mechanism_predictions.py    (Amd 18 adjudication)
measurements/plot_mechanism_maps.py
measurements/plot_mechanism_final.py

test/test_phase20r7_mechanism.py    ( 4 test)
test/test_phase20r7_maps.py         (12 test)
test/test_phase20r7_radius.py       (11 test)
test/test_phase20r7_predictions.py  (10 test)
                                    -- tong 37 test
```

## 11. Figures

```text
figures/mechanism_gap_clipped.png         fig 1  co che clipped, sec.4
figures/mechanism_channel_split_d2.png    fig 2  P3, sec.7
figures/mechanism_d2_cost.png             fig 3  do cong cost, sec.5
figures/mechanism_radius_vs_err.png       fig 4  P1 NOT SUPPORTED, sec.7
figures/exploratory_margin_exceedance.png       THAM DO, sec.9

phu luc:
figures/mechanism_d1_loss.png
figures/mechanism_d2_loss.png
figures/mechanism_cost_split.png
figures/mechanism_channel_ratio.png
```

## 12. Gioi han da ghi

```text
- do cong loss khong do duoc o rho thap (nhieu dem goi, loss*n_pkt < 10)
- argmax do cong cua h2 khong phan giai duoc o buoc luoi 0.02
- argmax err cua h2 nam o mep trai cua cua so do -> khong nhan dang duoc
- o rho_bar = 0.960 nam ngoai mien tinh do cong muc duong
- 8 o khong doc lap: poisson va h2 chung quy dao rho theo seed
- SE lan truyen gia dinh ba node rho doc lap -> can tren neu chung seed
```

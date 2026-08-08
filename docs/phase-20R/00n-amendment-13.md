# AMENDMENT 13 -- Nguon goc cua thieu hut loss trong `A' - A`

Ngay: 2026-08-07
Trang thai: chan doan offline hoan tat; ky truoc khi chay bat ky testbed nao.

Amendment nay sua HAI ket luan sai trong Amendment 12 (muc 10.1 va 10.2), bo
sung hai root cause moi (RC7, RC8), va thay doi thu tu uu tien: **branch A0 KHONG
con la buoc tiep theo**.

Moi so trong tai lieu nay tai lap duoc bang lenh o muc 8.

---

## 1. SUA -- Luoi truth table DEU 0.02; "khoang trong 0.08" khong ton tai

Amendment 12 muc 10.2 khang dinh luoi `rho` co khoang trong 0.08 quanh
`0.9775`/`0.9875`. **Sai.** Luoi do duoc doc tu `campaign_state.json`, tuc CHI
chien dich 20R.4. `truth_table.parquet` tron ca Phase L va 20R.4, va luoi that
la:

```text
mode      bw   q    n   rho range      gap_min  gap_max  deu?
poisson  4.0  10   23   0.60..1.04     0.0200   0.0200   yes
poisson  6.0  13   28   0.50..1.04     0.0200   0.0200   yes
poisson  8.0  18   24   0.50..0.96     0.0200   0.0200   yes
h2       4.0  10   23   0.60..1.04     0.0200   0.0200   yes
h2       6.0  13   28   0.50..1.04     0.0200   0.0200   yes
h2       8.0  18   24   0.50..0.96     0.0200   0.0200   yes
```

`gap_min = gap_max = 0.0200` o ca sau duong cong. Cac diem 0.98/1.00/1.02 den tu
Phase L, lap day dung khoang ma 20R.4 bo trong.

### 1.1 Bias noi suy THAT cua estimator dang dung

`TruthTable.delay_loss` dung `np.interp` (tuyen tinh tung doan) tren luoi tren.
Bias cua no = (duong cong) - (duong gap khuc). Uoc luong duong cong bang
monotone cubic Fritsch-Carlson (khong overshoot, thuan numpy):

```text
mode     link     rho      linear    curvature    bias_curv | bracket    source
poisson  L1    0.8575    0.000536     0.000528    -0.000009 | 0.84-0.86  20R + 20R
poisson  L2    0.9775    0.024962     0.024855    -0.000107 | 0.96-0.98  20R + L
poisson  L3    0.9875    0.038345     0.038176    -0.000169 | 0.98-1.00  L   + L
h2       L1    0.8575    0.030810     0.030805    -0.000005 | 0.84-0.86  20R + 20R
h2       L2    0.9775    0.100824     0.100735    -0.000088 | 0.96-0.98  20R + L
h2       L3    0.9875    0.132736     0.132872    +0.000136 | 0.98-1.00  L   + L
```

O muc path (dai luong di vao gate), truyen qua `d/dl_i = prod_{j!=i}(1-l_j)`:

```text
mode      path_linear   path_curv    bias_path   deficit quan sat   bias/deficit
poisson      0.062853    0.062578    -0.000275         -0.001378          20.0%
h2           0.244202    0.244243    +0.000041         -0.011497          -0.4%
```

**Ket luan: noi suy KHONG phai co che chinh.** Voi poisson no giai thich 20%
(khong phai ~100% nhu Amendment 12 muc 10.2 da viet); voi h2 no giai thich ~0%
va NGUOC DAU.

### 1.2 Phan biet hai dai luong -- khong duoc tron

```text
bias_curv   bias cua estimator TREN LUOI THAT (0.02).       -> dung de hieu chinh
loo_h       do nhay neu luoi THUA HON k lan (o day h~0.10). -> chi la sensitivity
```

Con so `-0.0018` trong Amendment 12 muc 10.2 la `loo_h`, khong phai bias. Ty le
`(0.10/0.02)^2 = 25` giai thich vi sao no lon hon `bias_curv` khoang 20 lan. Giu
lai cot `loo_*` trong `diag_interp_bias.json` nhung phai ghi nhan dung ten.

---

## 2. SUA -- Khong duoc dung "phan bo delay khop" de loai arrival smoothing

Amendment 12 muc 10.1 ket luan: phan bo hang doi khop trong 0.53 ms o `p99` nen
gia thuyet "burst bi lam muot" bi loai. **Lap luan nay khong vung.**

Chinh doan do da tu ghi: `p99` cua h2 **gan sat tran buffer o CA HAI phia**. Do
la dieu kien khien phep so sanh mat kha nang phan biet.

### 2.1 Toan hoc cua censoring

Goi `X` = backlog ma mot goi "muon gap" tai thoi diem den, neu buffer vo han.
Buffer huu han `q_max` bien no thanh:

```text
delay quan sat duoc = min(X, q_max)     <- BI CAT CUT (censored)
loss  quan sat duoc = P(X > q_max)      <- CHINH LA PHAN BI CAT BO
```

Hai phan bo `X` khac nhau CHI o phan duoi vuot `q_max` se cho:

```text
- phan bo delay quan sat duoc gan nhu Y HET  (vi phan khac nhau da bi cat)
- loss khac nhau ro ret                       (vi do chinh la phan bi cat)
```

Voi L3: `q_max = 10 x 1512 x 8 / 4e6 = 30.24 ms`, va `p99` do duoc 30.225 (A')
vs 30.190 (Phase L) -- ca hai deu dung tran.

**Vi vay "Delta p99 = 0.035 ms" khong noi len rang hai qua trinh den giong nhau;
no chi noi rang ca hai deu lam day buffer.**

### 2.2 Khi nao phan bo delay LAI co kha nang phan biet

Khi `p99 << q_max`, tuc che do KHONG bao hoa. Do la mot ly do ky thuat de uu
tien diem van hanh xa vung bao hoa cho Phase 21R.

### 2.3 He qua

Gia thuyet source-side smoothing QUAY LAI danh sach, va muc 3 duoi day cho thay
no co bang chung truc tiep.

---

## 3. RC8 (MOI) -- Nguon phat KHONG giong nhau: `c_a` cua A' thap hon

`load_gen` tu ghi thong ke qua trinh den vao `*_tx.meta.json`. So sanh hai phia
tai cung `(mode, bw)` va `rho` lan can, lay branch A qua `pid`/`raw_dir` trong
campaign state (chi cac run da dung nen truth table):

```text
mode     link  n_A/A'    ca_A     ca_A'      d_ca   t_welch |  late_A    late_A'
poisson  L1     15/5    1.0015   1.0045   +0.0030    +1.65  | 0.000131  0.000475
poisson  L2     15/5    1.0037   0.9990   -0.0047    -1.94  | 0.000143  0.000266
poisson  L3     10/5    1.0044   0.9986   -0.0058    -1.65  | 0.000052  0.000228
h2       L1     15/5    2.0059   1.9868   -0.0191    -1.35  | 0.000172  0.000172
h2       L2     15/5    2.0044   1.9988   -0.0056    -0.37  | 0.000093  0.000236
h2       L3     10/5    2.0253   1.9693   -0.0560    -4.53  | 0.000074  0.000255
```

**`h2 L3` -- dung o co thieu hut lon nhat -- co `d_ca = -0.0560` (`-2.77%`) voi
`t = -4.53`.** Do la o duy nhat vuot nguong canh bao.

`late_ratio` cua A' cao hon A o 5/6 o (thuong 2-4 lan), va `max_late_ms` cua A'
len toi 25-28 ms so voi 15-24 ms cua A. Phu hop voi ap luc lap lich cao hon
trong topology 4-switch/14-host.

### 3.1 `c_a` giai thich duoc bao nhieu phan thieu hut?

Truth table tu cung cap neo: tai cung `(bw, q, rho)` no giu ca duong poisson
(`c_a ~ 1`) lan duong h2 (`c_a ~ 2`), nen hieu hai duong la phan ung cua loss
theo burstiness tai tai co dinh. Coi la tuyen tinh cuc bo:

```text
mode     link     d_ca    d_ca_%   dloss/dca     du doan     quan sat  giai thich   phan du
poisson  L1    +0.0030    +0.30%     0.03027   +0.000091   +0.000018        519%  -0.000074
poisson  L2    -0.0047    -0.47%     0.07586   -0.000359   +0.000358       -100%  +0.000716
poisson  L3    -0.0058    -0.58%     0.09439   -0.000549   -0.001785         31%  -0.001236
h2       L1    -0.0191    -0.95%     0.03027   -0.000578   -0.002567         23%  -0.001989
h2       L2    -0.0056    -0.28%     0.07586   -0.000427   -0.002712         16%  -0.002286
h2       L3    -0.0560    -2.77%     0.09439   -0.005288   -0.008231         64%  -0.002943
```

`h2 L3`: burstiness giai thich **64%**. Vi `loss(c_a)` loi, uoc luong tuyen tinh
nhieu kha nang THAP HON thuc te, nen 64% la can duoi.

Cac o poisson co `d_ca` nho va `deficit` nho, ty le nhieu -- khong doc duoc.

---

## 4. RC7 (MOI) -- Diem bom probe khac nhau

Xac nhan cau truc tu chinh metadata, khong phai suy dien:

```text
branch A  : probe_pps_nominal = 20.0  -> probe IN-BAND, cung loadgen, cung veth
branch A' : probe_pps_nominal =  0.0  -> probe OUT-OF-BAND, host rieng,
                                         hop luu tai OVS switch
```

Ngan sach byte da khop (RC4 sua dung: `rho_nominal(A') = 0.98326 = 0.9875 - 20
pps x 106 B x 8 / 4e6`). Nhung QUA TRINH DEN tai cua `bfifo` thi khong khop: mot
ben la mot lich phat duy nhat, mot ben la hai dong hop luu qua OVS.

Voi `bfifo` gioi han theo byte, cau truc vi-burst tai cua vao quyet dinh truc
tiep xac suat tran. RC7 va RC8 co the la cung mot co che nhin tu hai phia.

---

## 5. Phan tang theo NGUON GOC diem luoi -- mot bien gay nhieu chua tach duoc

```text
link  rho      hai diem luoi neo        deficit poisson   deficit h2
L1    0.8575   ca hai tu 20R.4          +0.000018         -0.002567
L2    0.9775   mot 20R.4, mot Phase L   +0.000358         -0.002712
L3    0.9875   ca hai tu Phase L        -0.001785         -0.008231
```

Thieu hut lon nhat, o CA HAI mode, roi vao link ma ca hai diem neo deu tu Phase
L. Day CHUA phai bang chung (`n = 3` link, va `rho`/`bw` doi cung luc -- bi
confound), nhung no la gia thuyet canh tranh ma thiet ke A0 hien tai KHONG tach
duoc, vi A0 chi chay dung ba `rho` do.

---

## 6. Sentinel CO power tren loss

Nghi van "loss khong drift" chi la false reassurance da duoc kiem:

```text
o sentinel: h2 | bw=6 | q=13 | rho=0.90  ->  muc nen loss = 0.063904 (KHONG ~ 0)
MDE (3 sigma, two-sample) = 0.000338
deficit dang truy = 0.00179 .. 0.00823  ->  gap 5 den 24 lan MDE
```

Vay phat bieu "loss khong drift (`z_welch = +1.78`)" la co can cu. `q_mean_ms`
drift `+0.036 ms` (`z_welch = +4.61`, MDE = 0.0235) -- that ve thong ke nhung
bang 0.33% muc nen va NGUOC DAU voi `Delta delay` cua `A' - A`.

---

## 7. Do nhay `rho`: loai gia thuyet "sai ngan sach byte thuan tuy"

```text
mode     link     rho    dloss/drho    drho can    % cua rho
h2       L1    0.8575        0.3153    -0.00814       -0.95%
h2       L2    0.9775        0.3692    -0.00735       -0.75%
h2       L3    0.9875        0.4489    -0.01834       -1.86%
poisson  L1    0.8575        0.0131    +0.00134       +0.16%
poisson  L2    0.9775        0.3140    +0.00114       +0.12%
poisson  L3    0.9875        0.4524    -0.00395       -0.40%
```

`load_gen` la cung mot doan code cho ca hai mode, nen mot loi ngan sach byte
phai can CUNG MOT `drho` o cung link. L3 can `-1.86%` cho h2 nhung `-0.40%` cho
poisson -- lech 4.6 lan. Loai.

Nguoc lai, h2 can `drho` lon hon poisson dung theo huong ma smoothing du bao:
giam burstiness tuong duong giam `rho` hieu dung nhieu hon nhieu o dong bursty.

---

## 8. Tai lap moi so trong tai lieu nay

```bash
cd ~/dt4n

# Muc 1  -- luoi + bias noi suy + provenance
python3 -m measurements.diag_interp_bias

# Muc 3, 4 -- c_a, late, diem bom probe, do nhay burstiness
python3 -m measurements.diag_ca_late

# Muc 6  -- power cua sentinel (khong do lai, chi tinh lai tu report cu)
python3 -m measurements.sentinel_loss_recheck \
  --from-report results/phase-20R/sentinel_loss_recheck.json \
  --out results/phase-20R/sentinel_loss_recheck.json

# Muc 9  -- gate hien tai
python3 -m measurements.additivity_check \
  --from-state results/phase-20R/additivity_branch_a_state_budgetfix_bg.json \
  --out results/phase-20R/additivity_check_budgetfix_bg.json
```

Khong lenh nao trong so nay can testbed hay sudo.

---

## 9. Trang thai da cap nhat, va thu tu uu tien MOI

```text
poisson : bias khong xac lap (RC5), noi suy giai thich 20%, khong drift.
          Ket luan: INCONCLUSIVE do POWER, kem CI. (Amendment 12 muc 10.4 viet
          "HET bat thuong" -- sua thanh "khong du power de ket luan", vi noi suy
          chi giai thich 20% chu khong phai ~100%.)

h2      : khong phai noi suy (muc 1, ~0%)
          khong phai drift   (muc 6, va nguoc dau)
          KHONG con loai duoc arrival smoothing (muc 2 -- censoring)
          CO bang chung truc tiep nguon phat khac (muc 3, t = -4.53, giai thich >=64%)
          -> phan du chua giai thich: -0.0029 tren -0.0082
```

Thu tu uu tien doi lai:

```text
[1] RC7/RC8 truoc, A0 sau.
    Ly do: neu nguon phat da khac, A0 se cho `A0 - A ~ 0` (vi A0 dung
    SplitQdiscTopo, nguon phat nhe nhu A), va ta se ket luan "truth table lanh
    manh, vay h2 la cascade that" -- KET LUAN SAI, vi thu pham nam o loadgen
    duoi TandemTopo.

[2] Neu sau khi sua RC7/RC8 ma `A' - A` van lech, moi chay A0.

[3] A0 phai la A0+ : them D4 (rho=0.96, neo 20R.4) va D5 (rho=0.90, neo Phase L)
    de tach "tuoi diem do" khoi "vung rho" -- xem muc 5.
```

### 9.1 Du doan ky TRUOC khi chay (chong HARKing)

```text
H13-1  RC7 in-band probe:
       Chay lai A' voi `--probe-inband` (loadgen phat ca bg lan probe).
       Neu RC7/RC8 la co che chinh:
           |d_ca(h2, L3)| < 0.02  VA  deficit h2 path giam ve trong [-0.006, 0]
       Neu deficit khong doi qua -20%:
           RC7 khong phai thu pham; chuyen sang [2].

H13-2  Neu sau RC7 con phan du:
       phan du du bao ~ -0.003 (muc 3.1), tuc con FAIL o delta_loss = 0.005
       hay khong la 50/50. Khong du doan huong.

H13-3  A0+ (chi chay neu can):
       Neu bang tra lanh manh va may khong drift:
           |A0 - A| < 3e-4 o MOI diem
       Neu temporal drift: |D5 - A| > 1e-3 va |D4 - A| < 3e-4
       Neu loi vung rho:   |D4 - A| > 1e-3 va |D5 - A| < 3e-4
```

### 9.2 Khong thay doi

- Khong doi `delta_path`, `delta_loss`, hay bat ky nguong nao.
- Khong doi gia thuyet G6.
- Khong xoa ket qua cu; hai muc sai cua Amendment 12 duoc danh dau va giu
  nguyen van.
- Branch B/C van DUNG.

---

## 10. RC8 -- Silent join failure (loi cua chinh chan doan nay)

Lan chay dau cua `diag_ca_late` tra ve `SOURCE_MATCHES` va **thieu hoan toan L3**.
Nguyen nhan: `results/phase-L/campaign_state.json` khong co cot `raw_dir` (chi co
`pid`), nen 728 run Phase L bi bo qua. L3 neo THUAN Phase L, nen o do rong.

Code chay xong, khong bao loi, va tra ve ket luan NGUOC.

Mot join im lang tra ve tap rong la dang loi nguy hiem nhat trong phan tich du
lieu, vi no khong giong loi -- no giong mot ket qua. Da chuyen thanh assert cung
trong `assert_join_is_populated()`: moi join tu khai bao ky vong ve so luong va
ve tap o phai co mat. Kiem chung:

```bash
# bo phase-L khoi input -> phai CHET, khong duoc tra ve ket qua
python3 -m measurements.diag_ca_late \
  --campaign-states results/phase-20R/campaign_state.json
# => join hong: cac o sau RONG [('h2', 'L3'), ('poisson', 'L3')]
```

Nguyen tac ap cho moi phan tich ve sau: **khong join nao duoc phep tra ve tap
rong ma khong nem loi.**

---

## 11. Do doc BAC HAI thay secant, va chu ky cua phan du

### 11.1 Neo cbr hop le

```text
cbr loss max = 0.00000000 o CA BA duong cong (bw 4/6/8)  ->  loss(c_a = 0) = 0
```

Ba diem `(c_a, loss)` tai cung `(bw, q, rho)`: `(0, 0)`, `(1, l_p)`, `(2, l_h)`.
Parabol qua goc cho do doc CUC BO tai `c_a = 2`:

```text
loss(c) = a c^2 + b c ,  loss(0) = 0
=>  loss'(2) = 4a + b = 1.5 l_h - 2 l_p      (cuc bo)
    secant   =          l_h - l_p            (trung binh tren [1,2])
```

### 11.2 Ket qua

```text
link        l_p        l_h    secant    quad@2  ratio    pred_quad          obs   expl%       resid
L1     0.000536   0.030810   0.03027   0.04514  1.491    -0.000862    -0.002567   33.6%   -0.001705
L2     0.024962   0.100824   0.07586   0.10131  1.335    -0.000570    -0.002712   21.0%   -0.002143
L3     0.038345   0.132736   0.09439   0.12241  1.297    -0.006858    -0.008231   83.3%   -0.001373
```

**O FAIL (h2 L3): burstiness giai thich 83.3%, khong phai 64%.** Con so 64% o
Amendment 13 muc 3.1 dung secant; giu lai de doi chieu, nhung so dung la 83.3%.

### 11.3 Chu ky cua phan du: HANG SO CONG

```text
phan du:  -0.001705   -0.002143   -0.001373
          mean = -0.001740   sd = 0.000386   CV = 22%
ghep len path (qua dao ham rieng) = -0.004327
```

Ba link co `loss` nen lech nhau 4.3 lan (0.031 / 0.101 / 0.133), `rho`/`bw`/`q`
deu khac, ma phan du gan nhu mot hang so cong.

```text
Neu phan du la HANG SO NHAN (ti le voi loss)  ->  co che HANG DOI
     phai la  -6.5% / -2.1% / -1.0%  ->  KHONG phai (lech > 6 lan)
Neu phan du la HANG SO CONG                   ->  co che theo SO GOI/giay,
     khong theo ti le tai
```

**Nhung "hang so cong" KHONG duy nhat chi ve co che dem goi.** Xem muc 12.

### 11.4 Bao toan goi tren du lieu da co

```text
mode     link    n_sent    loss_total   loss_warm   dup   sockdrop   foreign
h2       L1      39600      0.028616    0.028243     0          0         0
h2       L2      33842      0.099173    0.098111     0          0         0
h2       L3      22760      0.125571    0.124504     0          0         0
poisson  L1      39600      0.000540    0.000554     0          0         0
poisson  L2      33842      0.024880    0.025320     0          0         0
poisson  L3      22760      0.036722    0.036560     0          0         0
```

Phia NHAN sach tuyet doi: `socket_drops = 0`, `foreign = 0`, `duplicate = 0`, va
ca 14 host-interface deu `noqueue` (khong co pfifo_fast an).

Phia GUI: `packet_player.play_events` goi `sock.sendto()` khong bat exception va
khong kiem gia tri tra ve -- NHUNG `seq_bg` chi tang SAU khi `sendto` tra ve, nen
`n_bg_sent` chi dem cac lan gui THANH CONG. Mot loi `ENOBUFS` se lam CHET run
chu khong tao loss gia. **Ung vien "sendto nuot loi" bi loai.**

Con lai chua kiem duoc: drop tai veth phia SWITCH va tai softirq backlog. State
hien tai KHONG chua bat ky counter `dropped`/`overlimits`/`backlog` nao, nen phai
gop vao phien do (muc 13).

---

## 12. Phan bien chinh gia thuyet "dem goi": probe in-band CHIEM CHO trong buffer

Mot co che HANG DOI that su cung sinh ra phan du hang so cong:

```text
branch A : probe 20 pps di IN-BAND, cung socket, cung lich phat voi bg
           -> goi probe nam BEN TRONG cac cum bg
           -> trong cua so tran buffer, probe canh tranh truc tiep voi bg
branch A': probe 20 pps di OUT-OF-BAND tu host rieng
           -> den doc lap, it roi vao dung cua so tran
```

`20 pps` la mot toc do CO DINH, khong ti le voi tai. Vi vay phan bg bi day ra
khoi buffer boi probe cung gan nhu CO DINH theo so goi -- tuc **hang so cong**,
dung chu ky quan sat duoc, va chi ro ret voi h2 (poisson khong co cum de probe
roi vao).

He qua quan trong cho thiet ke:

```text
Phep do bao toan goi (R = n_sent - n_recv - tc_dropped) KHONG phan biet duoc
hai gia thuyet nay:
  - "dem goi"        -> R > 0
  - "probe chiem cho" -> R = 0, vi goi that su bi bfifo drop
=> Can THEM mot phep phan biet: chinh la lan chay A' voi probe IN-BAND (RC7).
   RC7 fix du doan phan du BIEN MAT; gia thuyet dem goi du doan phan du GIU NGUYEN.
```

Do do RC7 khong con la "sua cho chac"; no la **phep do phan biet gia thuyet**.

---

## 13. §9.2 CHINH SACH NGUONG -- ky truoc phien S1

### 13.1 Van de: `DELTA_LOSS` la hang so oi

```python
DELTA_MS   = 0.44     # da bi RC3 vo hieu, thay bang runtime
DELTA_LOSS = 0.005    # HANG SO CO DINH, chua bao gio duoc RC3 hoa
```

Hai nguong trong CUNG mot gate duoc sinh boi HAI nguyen tac khac nhau: nguong
delay la tuong doi (20% khe cost, tinh lai moi lan do), nguong loss la tuyet doi
va bat bien. Hau qua:

```text
poisson  path loss = 0.0629  ->  delta = 0.005 = 8.0% tuong doi   (RAT LONG)
h2       path loss = 0.2442  ->  delta = 0.005 = 2.0% tuong doi   (RAT CHAT)
```

RC3-hoa theo dung nguyen tac da ky (`w_loss * delta_loss <= 0.20 * khe cost`),
voi `w_loss` THUC TE tu calibration (`h2 = 4515.9`, `poisson = 3222.2`):

```text
mode      khe cost    delta_loss(0.20)   delta_loss(0.10)   delta_loss cu
h2         102.659           0.004547           0.002273           0.005
poisson      7.546           0.000468           0.000234           0.005
```

Nguong moi lam h2 CHAT hon mot chut (0.00455 vs 0.005) va poisson CHAT HON 10
LAN (0.00047 vs 0.005). **Khong chieu nao co loi cho ket qua hien tai** -- day la
bang chung day khong phai HARKing.

### 13.2 Chinh sach ky

```text
Gate chinh (PASS/FAIL/INCONCLUSIVE):  chi tren `cost`.
    delta_cost = 0.20 x khe cost do tai runtime.  KHONG DOI.

Chan doan (bao cao mean + CI90, KHONG phan quyet):
    delay_ms, loss_fraction

Bang sensitivity (bao cao, khong phan quyet):
    delta_loss = 0.005                  (nguong cu, giu de doi chieu)
    delta_loss = 0.20 x khe / w_loss    (RC3-hoa, ngan sach day)
    delta_loss = 0.10 x khe / w_loss    (RC3-hoa, ngan sach chia doi)

Ly do doi: hai nguong trong cung mot gate duoc sinh boi hai nguyen tac khac
nhau -> khong nhat quan noi bo. Gate ba dai luong cung luc con la DEM TRUNG:
cost da chua delay va loss.
```

### 13.3 !! Chinh sach nay KHONG cuu h2 -- phai noi ro truoc khi chay

Chieu du doan hau-RC7 (gia su `d_ca -> 0`, con lai dung phan du muc 11.3):

```text
cost residual du doan = delay_res + w_loss x loss_res
                      = -0.51 + 4515.9 x (-0.004327)
                      = -20.05 ms      vs  delta_path = 20.53 ms
                      -> bien con lai 2.3%
```

De CI90 lot vao `+-20.53` can `se(cost) < 0.25 ms`; hien tai `se = 11.18 ms`
-> can giam 44 lan -> `n ~ 9700 seed`. Ghep cap giam 2-4 lan. **Khong kha thi.**

Tuong tu voi gate loss: de PASS voi hieu ung that `-0.004327` va `delta = 0.005`
can `se < 0.000355`, hien tai `0.002260` -> `n ~ 203 seed`.

```text
KET LUAN PHAI GHI TRUOC: khong mot lua chon nguong nao cuu duoc h2 neu phan du
-0.00433 la THAT. Thu duy nhat co the doi phan quyet la phan du bien mat, tuc
gia thuyet RC7 o muc 12 dung.

=> Doi ngan sach testbed: uu tien tuyet doi cho RC7 in-band. Tranh luan ve
   nguong khong tao ra du lieu.
```

### 13.4 §9.3 Du doan ky truoc cho phien S1

```text
H-S1-1  V-CA (gate theo CAP, cung seed -> cung schedule_digest):
        |c_a(A'+) - c_a(A0)| <= 0.020  va  |late_ratio| <= 2e-4  o >= 90% cap.
        Vi pham -> cap do INVALID, chay lai, KHONG phan tich roi moi loai.

H-S1-2  Neu RC7 (muc 12) dung:
        phan du loss path cua h2 -> trong [-0.002, +0.002]
        => cost residual -> trong [-9, +9] ms  -> CI90 co the lot +-20.53  -> PASS

H-S1-3  Neu gia thuyet "dem goi" dung:
        phan du loss path GIU NGUYEN ~ -0.0043
        => cost residual ~ -20 ms  -> INCONCLUSIVE hoac FAIL bat ke nguong nao
        => ghi la bias co he thong (Amendment 11 phuong an (a)), thu hep pham vi.

H-S1-4  A0 - A, loss, moi link: |lech| < 3e-4.
        Neu > 1e-3 -> kich hoat D4 (rho 0.96, neo 20R) va D5 (rho 0.90, neo L).

H-S1-5  Bao toan goi: R = n_sent - n_recv - tc_dropped.
        R ~ 0 o ca hai mode -> loai gia thuyet dem goi -> ung ho muc 12.
        R ~ 1.7e-3 x n_sent o h2 -> ung ho gia thuyet dem goi.
        LUU Y: R mot minh KHONG du (muc 12); phai doc cung ket qua RC7.

H-S1-6  poisson: khong du doan huong; bao cao CI. Voi delta_loss RC3-hoa
        (0.000468) poisson se CHAT hon truoc rat nhieu -> nhieu kha nang
        INCONCLUSIVE. Do la ket qua hop le.
```

---

## 14. §14 -- Dinh nghia lai estimand cua G6: G6-ABS va G6-DIFF

### 14.1 Ly do (nguyen tac da ky tu Lesson 20R.0)

`docs/phase-20R/01-inherited-audit.md` da bac Phase 20 vi loi cua no la
**differential**, khong phai common-mode. Nguyen tac do duoc ky TRUOC moi phep do
cua 20R.6. G6 hien tai lai do `|A' - A|`, mot dai luong TUYET DOI, trong khi RQ-A
dinh nghia tren `argmin cost`.

Vi vay bo sung mot gate thu hai. **Khong bo gate cu.**

```text
G6-ABS   |A' - A| <= 0.20 x khe cost.  Da FAIL. Bao cao nguyen ven.
G6-DIFF  |d err| <= 0.10 x err  VA  |d d_sla| <= 0.10 x d_sla,
         khi ap phan du len CA BON hanh dong.
```

### 14.2 Ba ly do chong-HARKing

```text
1. Nguyen tac common-mode/differential ky tu 20R.0, truoc moi so cua 20R.6.
2. RQ-A dinh nghia tren argmin -> gate bao ve RQ-A phai dung estimand ma
   argmin nhin thay. Gate cu dung sai estimand: do la loi THIET KE GATE.
3. Estimand moi KHONG cho khong -- no dat ra rang buoc MOI (chan tren bien
   thien per-link) ma du lieu hien tai khong dap ung cho poisson. Va G6-ABS
   van FAIL, van duoc bao cao.
```

### 14.3 !! Ket qua: G6-DIFF KHONG cuu duoc phase

Chay `measurements/g6_differential.py` (n = 100k, seed 11/12/13, worst-case
hoan vi cua vector phan du giua ba lop link):

```text
===== poisson =====
  Dcost COMMON-MODE  =  +3.296 ms      Dcost DIFFERENTIAL =  +9.286 ms
  khe quyet dinh     =  24.082 ms   -> differential/khe = 38.56%
  k=0  max|d err| = 0.000091  (tol 0.031810) PASS
  k=1  max|d err| = 0.068599  (tol 0.031810) FAIL
  do tan giua link 0.000955 > se mot link 0.000427 -> differential PHAN BIET DUOC
  -> G6-DIFF = FAIL

===== h2 =====
  Dcost COMMON-MODE  = -23.144 ms      Dcost DIFFERENTIAL =  +4.392 ms
  khe quyet dinh     = 103.793 ms   -> differential/khe = 4.23%
  k=0  max|d err| = 0.000020  (tol 0.008562) PASS | d_sla 0.004627 (tol 0.002548) FAIL
  k=1  max|d err| = 0.006028  (tol 0.008562) PASS | d_sla 0.005726 (tol 0.002548) FAIL
  do tan giua link 0.000386 < se mot link 0.001360 -> differential KHONG phan biet duoc
  -> G6-DIFF = INCONCLUSIVE
```

### 14.4 Vi sao bias theo LOP LINK khong tu dong la common-mode

Bon duong KHONG co cung thanh phan lop link:

```text
P1 = L1 + L2 + L1      P2 = L1 + L3 + L2
P3 = L2 + L2 + L1      P4 = L2 + L2 + L2
```

Nen mot bias khac nhau giua cac LOP se roi khac nhau len bon cot, va con duoc
khuech dai boi BOI SO (P4 dung lop L2 ba lan). Voi h2:

```text
    P1 dloss=-0.005552 ddelay=-0.432 -> dcost = -25.504 ms
    P2 dloss=-0.005221 ddelay=-0.510 -> dcost = -24.086 ms
    P3 dloss=-0.005990 ddelay=-0.232 -> dcost = -27.282 ms
    P4 dloss=-0.006428 ddelay=-0.032 -> dcost = -29.060 ms
    common-mode = -26.483 ms | differential = 4.974 ms   (ti le ~5:1, khong phai 20:1)
```

Lap luan "cong cung mot so vao ca bon cot" chi dung neu bias GIONG NHAU o moi
link. No khong giong nhau.

### 14.5 `d_sla` KHONG bat bien voi common-mode

`_viol` dung nguong TUYET DOI (`t_delay_ms`, `t_loss`). Mot dich chuyen chung van
lam tung hanh dong vuot nguong khac nhau, nen `d_sla` doi ngay ca tai `k = 0`:
h2 co `max|d d_sla| = 0.004627` tai `k = 0` so voi `tol = 0.002548`.

Do do khong duoc phat bieu "common-mode triet tieu trong d_sla".

### 14.6 Trang thai va viec con lai

```text
poisson : differential PHAN BIET DUOC va vuot nguong -> FAIL.
          Day la o can do them, khong phai h2.
h2      : differential khong phan biet duoc voi 0 -> INCONCLUSIVE,
          va d_sla FAIL ngay ca o common-mode thuan tuy.

=> Phase KHONG dong duoc tai day. Phien do RC7 in-band la buoc tiep theo,
   va no phai bao gom CA HAI mode voi 8 seed (poisson quan trong hon).
```

### 14.7 Quy tac dung -- ky ngay

```text
Dieu tra tiep CHI khi sai so con lai co the lam |d err| > 0.10 x err_goc.
Hien tai: poisson |d err| = 0.0686 > tol 0.0318  -> CON MO.
          h2      |d err| = 0.0060 < tol 0.0086  -> DONG ve err;
                  con mo ve d_sla.
Sau phien RC7: neu ca hai mode dat |d err| <= tol va |d d_sla| <= tol -> DUNG.
Khong RC9, khong branch moi, khong buoi testbed nao nua.
```

---

## 15. §15 -- Pham vi hieu luc sau khi do lai in-band

### 15.1 Ket qua phien RC7 (48 diem, 8 seed, 2026-08-07)

Validity: `n_fail = 0`, `max_abs_rho_error = 2.85e-05`, `max_probe_intrusion =
0.00424`, `direct_packets_delta = 0`, `socket_drops = 0`, `n_foreign = 0`.

```text
                        OUT-band     IN-band        doi     verdict
h2  path loss          -0.011497   -0.010130   +0.001367    FAIL -> FAIL
poisson path loss      -0.001378   -0.001334   +0.000044    PASS -> PASS
h2  path cost         -61.524589  -54.167839   +7.356750    FAIL -> FAIL
h2  path delay         -0.510404   -0.441477   +0.068928    PASS -> PASS
```

**H13-1 bi bac.** Dieu kien ky truoc la deficit h2 ve `[-0.006, 0]`; thuc te
`-0.010130`, va muc giam chi `11.9%` (nguong da ky: `20%`).
`probe_injection_differs = False` -- RC7 dong ve cau truc -- nhung
`d_ca(h2, L3)` chi tu `-0.0560` xuong `-0.0453` (t = -3.43), van bi gan co.

**RC7 va RC8 la hai nguyen nhan doc lap. Sua diem bom probe khong sua duoc
chenh lech burstiness.**

### 15.2 Phan du sau 8 seed

```text
mode      phan du/link                          gop        se_gop    CI90                   Cochran Q  I2
h2        -0.001749 / -0.001735 / -0.002169   -0.001884   0.000679  [-0.003000, -0.000768]   0.06     0%
poisson   +0.000022 / -0.000016 / -0.000793   -0.000262   0.000311  [-0.000774, +0.000249]   0.62     0%
```

Ca hai mode `I2 = 0%` -> ba uoc luong link tuong thich voi MOT gia tri chung,
nen viec gop thanh mot so hang common-mode la hop le. Voi 5 seed truoc do
poisson co `I2 = 67%`; phan lon "di dieu" khi ay la nhieu do, da duoc boc ra
bang 8 seed. **CI90 cua poisson CHUA 0** -> voi poisson khong co bang chung ve
bias, va moi con so duoi day cho poisson la CAN TREN cua tac hai.

### 15.3 G6-PRE sau khi do lai

**Ten goi da duoc sua (2026-08-07).** Cac con so duoi day den tu contrast
`Aprime_minus_A_*`, tuc CHUYEN TOPOLOGY, khong phai cascade. Cascade la
`C - sum(B)` va CHUA duoc do (`has_branch_b = false`, `has_branch_c = false`,
`g6_evaluated = false`). Cach goi cu ("G6") noi qua pham vi phep do.

```text
G6-PRE-ABS   h2       loss FAIL (-0.010130 vs delta_loss 0.005)
             poisson  loss PASS | delay PASS | cost INCONCLUSIVE
                      mean -4.655 ms, CI90 [-14.990, +5.681], delta 1.509,
                      1.645*se = 9.27 ms > delta -> power_ok = false
G6-PRE-DIFF  h2 INCONCLUSIVE | poisson PASS (truoc: FAIL)
G6-CASCADE   NOT MEASURED (dung som, Amendment 11)
```

`cost` cua poisson INCONCLUSIVE do THIEU POWER CAU TRUC, khong phai do bias: de
dat `power_ok` can `se <= 0.917 ms`, tuc giam 6.1 lan so voi `5.638 ms` hien
tai, tuc khoang 300 seed. Khong kha thi.

poisson chuyen FAIL -> PASS dung bang co che da du bao: 8 seed siet phan du
per-link (L1/L2 ve gan 0), `differential` tu `9.286 ms` xuong `2.763 ms`.

h2 tac o `d_sla`, va tac ngay tai `k = 0` -- tuc o COMMON-MODE thuan tuy, khong
phai differential. Them seed khong cuu duoc. Ly do o muc 15.5.

### 15.4 Bang sai so he thong tren headline

Xem `docs/phase-20R/08-gates.md`. Tom tat: `err` dich toi da `+0.0217`
(h2 @ 0.700); `d_sla` dich toi da `-0.0429` (poisson @ 0.700). Trong sau o cua
tap G2, nam o giu `d_sla_lower >= 0.03` o dau xau nhat; mot o lat.

### 15.5 Vi sao `d_sla` nhay ma `err` thi khong -- co che

`err` so sanh HIEU cost giua bon hanh dong: mot dich chuyen CHUNG khong doi thu
tu, nen `argmin` mien nhiem.

`d_sla` dem so lan vuot MOT NGUONG TUYET DOI (`t_delay_ms`, `t_loss`). Va
`sla_calib_v2` hieu chuan nguong do de no nam GIUA phan bo path loss -- neu
khong thi hoac khong duong nao vi pham, hoac tat ca cung vi pham, va `d_sla` se
luon bang 0, vo dung lam thuoc do.

```text
o                t_loss     khoang cach tu bon duong toi nguong        n_up
poisson 0.700   4.24e-04    co duong tren va duong duoi                 1/4
h2      0.700   2.65e-02    co duong tren va duong duoi                 2/4
h2      0.850   1.10e-01    co duong tren va duong duoi                 2/4
poisson 0.850   ...         co duong tren va duong duoi                 2/4
```

Khong o nao co `n_up = 0` hay `n_up = 4`. Do la ket qua cua hieu chuan, khong
phai ngau nhien.

> **`d_sla` nhay voi dich chuyen chung LA HE QUA CUA THIET KE, khong phai khiem
> khuyet cua phep do.** Ket luan nay dung cho moi thuoc do dua tren nguong
> tuyet doi duoc hieu chuan vao giua phan bo.

Chi so mong manh, du doan o nao nhay ma khong can chay mo phong:

```text
F = |dich chuyen path loss| / min_a |path_loss(a) - t_loss|
```

Dung `min` chu khong phai trung binh: mot lan vuot nguong la du de doi so dem,
va duong gan nguong nhat vuot truoc.

### 15.6 O `poisson @ rho_bar = 0.700` -- co mong manh

`F = 3.9`, `t_loss = 4.24e-04`, `min_gap = 2.01e-04`. Ca bon duong nam trong
mot dai hep quanh nguong. O dau xau nhat cua CI90, `d_sla` sup ve `0.0000` va
`G2` truot.

Quyet dinh: **GIU o nay trong headline, kem co mong manh nay**, va **khong dung
no lam o van hanh cho Phase 21R**. Ly do giu:

```text
- CI90 phan du cua poisson CHUA 0, nen kich ban nay la CAN TREN cua tac hai,
  khong phai uoc luong diem.
- Bo o sau khi thay no truot la chon ket qua sau khi thay so.
- Chinh o nay minh hoa co che o 15.5 ro nhat: t_loss = 4.2e-4 sat gioi han
  phan giai cua bang tra.
```

### 15.7 Huong lech -- ghi ca phan bat loi

```text
d_sla: 2/8 o co bien nam hoan toan duoi 0 -> con so cong bo la CAN TREN.
       Cac o con lai bien HAI CHIEU -> KHONG duoc phat bieu "bao thu".
err  : 5/8 o co dau tren duong -> con so cong bo la CAN DUOI.
       h2 @ 0.700: d err toi +0.0217 (+7.2%). Day la phan BAT LOI, ghi ro.
```

### 15.8 Pham vi hieu luc

```text
1. Phat bieu ve XEP HANG duong (err, don dinh, NC1b, NC2, phan ra
   e_model/e_staleness): hieu luc DAY DU. |d err| <= 0.026 tren moi o, va
   khong o nao ra khoi khoang G1.
2. Phat bieu ve d_sla: kem bien mot phia o 15.4/08-gates.md.
3. Phat bieu TUYET DOI ve cost path cua h2: gioi han o SplitQdiscTopo.
   Tren TandemTopo, cost path h2 lech -54.2 ms (G6-ABS FAIL).
4. poisson @ 0.700: co mong manh, khong dung lam o van hanh 21R.
5. Branch B, C KHONG mo (quy tac dung som Amendment 11) -> future work.
```

### 15.9 Quy tac dung -- da thoa

`§14.7` yeu cau dieu tra tiep chi khi sai so con lai co the lam
`|d err| > 0.10 x err_goc`. Sau phien in-band:

```text
poisson : |d err| = 0.027 <= tol 0.032   VA  |d d_sla| = 0.006 <= tol 0.013  -> DAT
h2      : |d err| = 0.004 <= tol 0.009   -> DAT
          |d d_sla| = 0.005 > tol 0.003  -> TRUOT, NHUNG truot ngay tai k = 0,
          tuc o common-mode thuan tuy. Day la ket luan CAU TRUC (muc 15.5),
          khong phai thieu power -> them seed khong doi duoc.
```

**Khong con buoi testbed nao can chay.** Lesson 20R.6 dong voi G6 co dieu kien.

---

## 16. Dai sai so cua gia dinh TUA TINH (khong Mininet)

Provenance: code va docs duoc commit tai `cf520ab` truoc khi sinh so cuoi.
So o §16.2/§16.3 hien tai la SMOKE (`--seeds 101,102 --n 60000`), sinh
TRUOC commit nay; phai chay lai `--seeds 101,102,103,104,105 --n 120000`
sau `cf520ab` truoc khi trich vao ban cuoi.

Gia dinh tua tinh -- `f(rho_now)` tra bang tra tai `rho` tuc thoi -- chua duoc do
o MUC DUONG. `results/phase-20R/quasistatic_check.json` van la placeholder rong
(`evaluated: false`, `n_input_rows: 0`).

Thay vi de trong, sai so nay duoc CHAN TREN bang cung ky thuat da dung cho
additivity: bom phan du vao bang tra roi tinh lai headline
(`measurements/quasistatic_band.py`).

### 16.1 Sai so tua tinh do duoc o Phase T (muc link)

Nguon: `results/phase-T/t6e_paired.json`, khoa `summary_dyn_by_mode`.

```text
mode      mean_ms      sd    se_mean    n    CI95 cua TRUNG BINH    p05/p95 mot cua so
cbr       -0.6166   1.1548   0.2108    30   [-1.0298, -0.2034]     [-3.058, +0.526]
h2        -0.0342   0.1887   0.0172   120   [-0.0679, -0.0004]     [-0.281, +0.401]
poisson   -0.0313   0.2019   0.0184   120   [-0.0674, +0.0048]     [-0.448, +0.245]
```

`cbr` khong dung trong 20R. Dau te nhat dung cho bien: `-0.0679 ms` (CI95 cua
trung binh) hoac `-0.448 ms` neu muon chan mot CUA SO don le.

### 16.2 Quet kenh delay -- mien nhiem

```text
resid_ms   max|d err|   min d_sla (tap G2)   gate
  +0.000     0.00000          0.0494          SONG
  -0.050     0.00000          0.0542          SONG
  -0.100     0.00000          0.0567          SONG
  -0.500     0.00000          0.0552          SONG
  -1.000     0.00000          0.0548          SONG
  -2.000     0.00000          0.0548          SONG
```

`d err = 0.00000` o MOI muc, dung nhu co che §15.5 du bao: phan du delay dong
deu len ca bon duong -> common-mode -> `argmin` mien nhiem. Day la xac nhan bang
so cho mot lap luan truoc do chi bang loi.

`-2.0 ms/link` la **29 lan** dau te nhat cua CI95 Phase T (`-0.0679 ms`) va
**4.5 lan** dau te nhat cua mot cua so don le (`-0.448 ms`). Gate van song.

### 16.3 Quet kenh loss -- cho mong manh, va BAT DOI XUNG

```text
resid       max|d err|   min d_sla (tap G2)   gate
 -0.0005      0.01965          0.0537          SONG
 -0.0010      0.02445          0.0492          SONG
 -0.0020      0.02403          0.0330          SONG   <- sat mep
 -0.0050      0.07016         -0.0728          LAT: h2@0.700, poisson@0.925, poisson@0.960
 +0.0005      0.00003          0.0000          LAT: poisson@0.700
 +0.0020      0.00011          0.0000          LAT: poisson@0.700, poisson@0.850
```

```text
nguong sup do chieu am    : -0.002  / link
nguong sup do chieu duong : +0.0005 / link      <- chat hon 4 lan
phan du cong tinh do duoc : h2 -0.001884 (94% nguong am) | poisson -0.000262 (13%)
```

Bat doi xung sinh ra tu `poisson @ 0.700`: `t_loss = 4.24e-04`, bon duong nam
trong dai `2.0e-04` quanh nguong (§15.6). Day loss LEN thi ca bon cung vi pham
-> `n_up = 4` -> `d_sla` triet tieu ve 0 -> thuoc chet. Day loss XUONG thi thu tu
con giu duoc.

Nhat quan voi H7 (co che la loss-driven, khong phai delay-driven): hai ket qua
doc lap cung chi ve mot huong.

Tham so lan chay: `--seeds 101,102 --n 60000`. Can chay lai voi 5 seed / n=120k
truoc khi trich vao ban cuoi.

### 16.4 Ket luan ve lo hong tua tinh -- CO PHAM VI THEO KENH

**!! SUA (2026-08-08).** Ban truoc cua muc nay suy tu "kenh delay an toan" ra
"lo hong tua tinh khong lat duoc ket luan nao". Suy luan do KHONG hop le: no
ngam gia dinh rang gia dinh tua tinh, khi sai, chi bieu hien o delay. Chua ai
chung minh dieu do, va co che censoring (§2) noi nguoc lai.

```text
KENH DELAY -- DA CHAN TREN:
  Phase T do err_dyn o don vi ms. Dau te nhat:
    CI95 cua trung binh  -0.0679 ms/link  |  mot cua so p05  -0.4480 ms/link
  Quet cho thay gate song toi -2.0 ms/link = 29x CI95, 4.5x mot cua so.
  => Kenh delay: lo hong DA DUOC CHAN. Phep do live chi con vai tro xac nhan.

KENH LOSS -- CHUA CHAN DUOC:
  Nguong sup do: +5e-4 (chieu duong) va -2e-3 (chieu am) tren moi link.
  Chieu duong CHAT HON kenh delay khoang 4 lan.
  Phase T KHONG do sai so tua tinh o kenh loss. Khong artifact nao chan duoc.

  Va censoring (§2) noi day KHONG phai ngau nhien:
      delay quan sat = min(X, q_max)   -> bi cat cut o tran -> MU voi dong hoc
      loss  quan sat = P(X > q_max)    -> chinh la phan bi cat -> giu dong hoc
  Khi rho tang, occupancy bo len cham hon trang thai dung, nen bang tra tinh
  NOI QUA ve loss; khi rho giam thi noi thieu. Tuc sai so tua tinh CO mat o
  kenh loss, va co dau xac dinh.

  => `err_dyn` nho o kenh delay KHONG duoc dung lam bang chung cho kenh loss.

TRANG THAI: gia dinh tua tinh CHUA duoc chan o kenh quyet dinh chinh (loss).
            Day la muc phai DO, khong phai muc co the suy luan.
```

### 16.5 Loi thiet ke phai sua TRUOC khi chay live

`measurements/quasistatic_check.py:280,306` dung `TandemTopo`. Nhung chinh Lesson
20R.6 vua chung minh `TandemTopo` KHONG chuyen doi duoc tu bang tra
(`Aprime_minus_A_path`, h2, `-54.168 ms`, FAIL). Chay tua tinh tren do se tron
hai nguyen nhan:

```text
lech quan sat = (gia dinh tua tinh sai) + (chuyen topology sai, da biet -54 ms)
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                          khong tach duoc -> phep do vo gia tri
```

De xuat sua: dung `SplitQdiscTopo` -- chinh topology da sinh ra bang tra -- va do
o MUC LINK, roi lan truyen len muc quyet dinh bang `quasistatic_band.py` (thay CI
Phase T bang CI vua do). Hai ve cua phep so sanh khi do cung mot topology nen
chenh lech chi con la tua tinh.

**Chua thuc hien.** Day la thay doi thiet ke do, can duyet truoc khi sua code.


### 16.6 Nguong sup do kenh loss -- hai con so, khong mot

O `poisson @ 0.700` da duoc khai bao MONG MANH tu §15.6 (`F = 3.9`,
`t_loss = 4.24e-04`, bon duong nam trong dai `2.01e-04` quanh nguong), kem
quyet dinh ky truoc: giu trong headline, KHONG dung lam o van hanh 21R. Ap
dung nhat quan quyet dinh do:

```text
Ke ca o mong manh (8/8 o) :  [-2e-3, +5e-4]
Loai o mong manh  (7/8 o) :  [-2e-3, +2e-3]      <- doi xung
Chi so `err` rieng        :  |d err| <= 3e-5 den +5e-3  => BAT BIEN
```

Chi so `err` khong nhuc nhich o chieu duong (`max|d err| = 3e-5`); chi `d_sla`
chet. Dung co che §15.5: `err` so HIEU giua cac duong nen mien nhiem dich
chuyen chung, `d_sla` dem vuot NGUONG TUYET DOI nen khong.

**Phat bieu chinh dung con so CHAT HON (`+5e-4`).** Con so noi long chi de giai
thich NGUON GOC cua nguong, khong duoc trich rieng.

### 16.7 Trang thai cua QS-LOSS

```text
| QS-DELAY | tua tinh, kenh delay | CHAN DUOC, bien 29x   | DAT           |
| QS-LOSS  | tua tinh, kenh loss  | CHUA DO, nguong +5e-4 | CHUA DANH GIA |
```

Bo sung vao pham vi hieu luc §15.8:

```text
6. Phat bieu ve `d_sla`: chua chan duoc sai so tua tinh o KENH LOSS.
   Nguong sup do +5e-4/link. Day la gioi han DA BIET, chua duoc do.
```

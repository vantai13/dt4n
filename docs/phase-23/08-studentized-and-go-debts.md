# Lesson 23.5[A] -- Studentized max-score and GO-3 debt

Ngay chay lan 1: 2026-08-16
Ngay chay lai (sua PC-S-1): 2026-08-17
Trang thai: EXPLORATORY, theo `docs/phase-23/00u-amendment-20.md` va
`docs/phase-23/00v-amendment-21.md`.

Input:

```text
results/phase-22/calib_set_v3_poisson_0.925.parquet
results/phase-22/calib_set_v3_poisson_0.850.parquet
results/phase-22/calib_set_v3_h2_0.700.parquet
```

Output:

```text
results/phase-23/studentized_poisson_0.925.json
results/phase-23/studentized_poisson_0.850.json
results/phase-23/studentized_h2_0.700.json
```

## 1. Doc ket qua theo dung thu tu khoa

| Cell | `sigma_max/min` theo bin | `c` theo bin | G3 ratios slot1/2/3 | coverage | acceptance max -> stud |
|---|---|---|---|---:|---:|
| poisson@0.925 | 1.1117, 1.1110, 1.1167, 1.1421 | 2.1018, 2.1252, 2.1030, 2.0928 | 0.9525 / 0.9966 / 1.0671 | 0.9095 | 0.1666 -> 0.1857 |
| poisson@0.850 | 1.2787, 1.2914, 1.3051, 1.3325 | 2.1946, 2.1842, 2.1596, 2.1418 | 0.8740 / 0.9865 / 1.1378 | 0.9113 | 0.0952 -> 0.1356 |
| h2@0.700 | 1.6557, 1.4976, 1.4268, 1.3897 | 1.9661, 2.0340, 2.0609, 2.0672 | 0.7678 / 0.9931 / 1.1411 | 0.9048 | 0.2611 -> 0.3867 |

S-5 phai doc truoc: main cell co slot heterogeneity nho (`~1.11-1.14`), nen
studentization chi mua duoc +0.0191 acceptance tuyet doi. Hai cell phu co
heterogeneity lon hon va lift lon hon, dung co che tai phan bo.

## 2. GO-3

G3a v1 tren main cell PASS:

```text
qhat_stud/qhat_max slot 1 = 0.9525, nam trong dai v1 0.92-0.98.
```

G3b v1 la PARTIAL/MISS:

```text
slot 2 = 0.9966, nam trong dai v1 0.98-1.02.
slot 3 = 1.0671, nam ngoai dai v1 0.98-1.02.
```

Theo Amendment 23-20, slot 3 rong hon maxscore khong phai loi: studentization
tai phan bo budget, khong lam moi qhat nho di. Dai v2 PASS cho ca ba slot tren
main cell:

```text
slot 1: 0.90-1.00  -> 0.9525 PASS
slot 2: 0.94-1.05  -> 0.9966 PASS
slot 3: 1.00-1.12  -> 1.0671 PASS
```

### 2.1. Kiem chung can dai so -- 9/9 trong can

Can `qhat_stud/qhat_max ~ rms(v) * sigma_j / rms(s_sim)` voi
`rms(v) in [rms(s_sim)/sigma_3, rms(s_sim)/sigma_1]` duoc dan TRUOC khi do:

```text
cell             slot   can duoi   DO DUOC   can tren   trong can?
poisson@0.925     1      0.897     0.9525     1.000        yes
                  2      0.942     0.9966     1.051        yes
                  3      1.000     1.0671     1.116        yes
poisson@0.850     1      0.769     0.8740     1.000        yes
                  2      0.846     0.9865     1.100        yes
                  3      1.000     1.1378     1.300        yes
h2@0.700          1      0.711     0.7678     1.000        yes
                  2      0.867     0.9931     1.219        yes
                  3      1.000     1.1411     1.407        yes
```

Can duoi cua slot 3 bang `1.000` o ca ba cell va do duoc deu `> 1.0`. Day la
xac nhan thuc nghiem cho canh bao muc 3.8 cua ghi chep: **studentization TAI
PHAN BO, khong thu nho**. Mot gate dang `qhat_stud <= qhat_max` voi moi `j` se
FAIL ca ba cell va vut bo mot thu tuc dang chay dung.

### 2.2. S-5 dai v2 -- MISS, khong sua hoi to

```text
S-5 dai v2 [1.05, 1.50] -> MISS o h2@0.700 bin 0 (1.6557).
Nguyen nhan: dai duoc dan tu rms GOP, ap cho dai luong PER-BIN.
Day la loi MUC DO TONG HOP (level-of-aggregation), khong phai loi ve co che.
Co che (sigma tang theo rank slot) van dung 12/12 o.
```

Xem `docs/phase-23/00v-amendment-21.md` muc 3. Dai da tach thanh
`S-5-pooled` / `S-5-perbin` CHI cho cac phase sau.

## 3. Coverage, acceptance, controls

| Cell | coverage stud | coverage maxscore | delta acceptance | NC-S-1 max diff |
|---|---:|---:|---:|---:|
| poisson@0.925 | 0.909492 | 0.906662 | +0.019147 | 0.0 |
| poisson@0.850 | 0.911294 | 0.905742 | +0.040419 | 0.0 |
| h2@0.700 | 0.904788 | 0.902250 | +0.125620 | 0.0 |

G23-25 PASS: simultaneous coverage giu quanh 0.90 tren ca ba cell.

G23-26 PASS: NC-S-1 cho `max_abs_diff = 0.0` chinh xac o 12/12 o, nghia la
sigma dong nhat dung bang maxscore tren fold2 nhu D7.

### G23-27 -- PC-S-1, ro ri sigma

KET LUAN: KHONG PHAT HIEN DUOC o che do du lieu day. KHONG PHAI PASS.

Co so phan tich: thien lech do uoc luong trong mau bac `O(p/n_eff)`. O day
`p = 3` (mot sigma moi rank slot), `n_eff ~ 250` block hieu chuan, nen can
thien lech `~ 1.2e-2 ... 1.2e-5` tuy cach dem mau huu dung.

Do duoc, full data:

```text
cell            coverage_clean  coverage_leaked  coverage_drop
poisson@0.925      0.9094920        0.9085980       0.0008941
poisson@0.850      0.9112941        0.9109481       0.0003460
h2@0.700           0.9047877        0.9040477       0.0007400
```

Nhat quan voi can, va duoi nguong `0.02` cua gate.

Do o che do it du lieu, `n_blocks_fold2_target = 30`, 5 seed, mean +/- SD:

```text
cell            coverage_clean       coverage_leaked      coverage_drop
poisson@0.925   0.93592 +/- 0.01634  0.93436 +/- 0.01609  0.00156 +/- 0.00028
poisson@0.850   0.93228 +/- 0.01781  0.93016 +/- 0.01885  0.00213 +/- 0.00187
h2@0.700        0.93048 +/- 0.01386  0.92880 +/- 0.01472  0.00167 +/- 0.00176
```

Doc dung: che do it du lieu MOT MINH khong cuu duoc doi chung. `drop ~ 1.6e-3`
nam sau duoi SD cua chinh no. Cai da thay doi la BAY GIO cau "khong phat hien
duoc" moi co nghia, vi `coverage_clean` da roi khoi tran (0.936, khong phai
0.9997).

### HUY BO

```text
Ket qua PC_S_1_small_n voi subsample_blocks=20 trong artifact ngay 2026-08-16
bi TRAN CHAN: fold2 chi con 9 block moi bin, conformal_level = 1.0, nen
qhat = max cua fold2 va coverage ~ 0.9997 bat ke ro ri.
  coverage_drop 0.0025909 / 0.0019545 / 0.0010000 -- VO NGHIA, khong trich dan.
Nguong dung la n >= 19 o alpha = 0.10, KHONG phai n >= 11
(conformal_level(11, 0.10) = 1.0).
Xem docs/phase-23/00v-amendment-21.md muc 1.
```

### G23-27b -- PC-S-1d, doi chung duong chieu cao

Vi mot doi chung duong khong kich hoat thi KHONG chung minh duoc gi, bo sung
PC-S-1d: `sigma` uoc rieng cho tung o `(phan vi m_hat_1) x (rank slot)`.
`m_hat_1` quan sat duoc luc chay that, nen sigma nay ap duoc len test.
Bien o lay tu fold1 o ca hai nhanh; chi GIA TRI sigma di chuyen.

Bao cao mot THANG `p`, khong phai mot diem. **Moi so `p` mang nhan level**:
`p_per_bin` la so tham so sigma TRONG MOT bin Mondrian, `p_total` la tong tren
4 bin. Dai luong co nghia cho lap luan ro ri la `p_per_bin`, vi `sigma` va `c`
deu hieu chuan TRONG bin.

```text
poisson@0.925
  p_per_bin [p_total]  CLEAN     LEAKED    drop     min cov/z_bin  spread cov/o mhat  block/o
     30      [  120]   0.90727   0.90376  +0.00351     0.90350          0.06553        160.5
    300      [ 1200]   0.90722   0.88086  +0.02636     0.90178          0.35631         24.0
   3000      [12000]   0.90161   0.68645  +0.21516     0.89859          1.00000          2.0

poisson@0.850
     30      [  120]   0.91188   0.90833  +0.00355     0.90791          0.05270        158.0
    300      [ 1200]   0.91165   0.88471  +0.02693     0.90744          0.23124         24.0
   3000      [12000]   0.90756   0.68680  +0.22076     0.90378          1.00000          2.0

h2@0.700
     30      [  120]   0.90459   0.90124  +0.00335     0.90239          0.07463        156.5
    300      [ 1200]   0.90585   0.87515  +0.03070     0.90356          0.28514         24.0
   3000      [12000]   0.90014   0.68527  +0.21487     0.89866          1.00000          2.0
```

Ba doc rieng biet, ca ba deu quan trong:

1. **LEAKED VO, don dieu theo `p`, giong het nhau o ca ba cell**
   (`0.904 -> 0.881 -> 0.686`). Phep do coverage CO do nhay. Truong hop `p = 3`
   don gian la co muc ro ri duoi do phan giai. G23-27 duoc doc la
   "khong phat hien duoc" mot cach CO CO SO, khong phai vi phep do mu.

2. **CLEAN giu bao phu BIEN TRONG TUNG BIN MONDRIAN o moi `p`** -- cot
   `min cov/z_bin` khong bao gio xuong duoi `0.8986`, ke ca khi
   `p_per_bin = 3000` va `sigma` chi duoc uoc tren ~2 block moi o, tuc gan nhu
   vo nghia. Day la dung pham vi dinh ly muc 3.3: bao dam split-conformal
   KHONG phu thuoc `sigma` dung hay sai, chi phu thuoc `sigma` doc lap voi
   fold2/test. Do la hinh dang gia nhat cho phan conformal.

3. **Bao phu CO DIEU KIEN theo o `m_hat` KHONG duoc bao dam, va o `p` cao no
   vo hoan toan** -- cot `spread cov/o mhat` di `0.066 -> 0.356 -> 1.000`. O
   `p_per_bin = 3000` co o dat bao phu `0.0` va o khac dat `1.0` trong khi bien
   van la `0.90`. Dieu nay khong mau thuan: bao phu co dieu kien chinh xac la
   BAT KHA THI (Vovk 2012; Lei & Wasserman 2014), da co trong nen ly thuyet
   Phase 21R. Ghi lai de cau phat bieu bien khong bi doc thanh nhieu hon no la.

Phat hien phu: do manh cua ro ri bam theo SO BLOCK moi o, khong phai so HANG
moi o. O `p_per_bin = 300` van con 24 block/o va drop chi `~0.027`; o
`p_per_bin = 3000` chi con 2 block/o va drop nhay len `~0.215`. `m_hat_1` co
cau truc theo block, nen `n` hieu dung cua `sigma` la block chu khong phai hang
-- cung don vi ma `conformal_level` dung.

**Nguyen tac rut ra, dung lai o 23.9 va 23.11:**

```text
Don vi mau hieu dung cua MOI dai luong uoc luong trong duong ong nay la BLOCK,
ke ca nhung dai luong khong di qua conformal_level (nhu sigma). Ly do chung:
rho(t) la AR(1) voi tau ~ 1.4 s, nen hang trong cung block gan nhu la ban sao.
He qua: khi phan hoach du lieu theo BAT KY bien nao (bin tuoi, o m_hat,
profile), dai luong can theo doi la block/o, khong phai hang/o.
```

## 4. Bang rui ro cua cac hang DUOC THEM -- do, khong suy

`accept_set_contingency` do truc tiep bang 2x2 giua hai tap accept:

| cell | both | only_max | only_stud | long nhau? | `err` tren hang THEM |
|---|---:|---:|---:|:--:|---:|
| poisson@0.925 | 83,279 | 0 | 9,573 | co | 3.395% |
| poisson@0.850 | 47,597 | 0 | 20,208 | co | 1.648% |
| h2@0.700 | 130,549 | 0 | 62,806 | co | 1.802% |

Ket qua do duoc: `only_max = 0` o ca ba cell, tuc tap accept cua studentized
CHUA TRON tap accept cua maxscore. Nghi ngo truoc do rang hai tap khong long
nhau (vi `slot_reject_rates[2]` tang `0.01348 -> 0.01842`) da bi bac bo bang
phep do. Giai thich: `qhat_3` rong ra lam slot 3 TU CHOI nhieu hon
(`reject = m_hat < kappa*qhat`), nhung cac hang do da bi slot 1 tu choi san,
nen tap accept khong mat hang nao. `slot1_decides_share` cua studentized la
`0.9996 / 0.9977 / 0.9988`, khong con bang `1.0` nhu maxscore, nhung phan con
lai khong doi dau tap accept.

### 4.1. Nesting KHONG phai tinh chat cau truc -- va bien do dang rat mong

Tren ba cell nay `only_max = 0` la mot QUAN SAT, khong phai dinh ly. Voi
`qhat_max` phang o `q_max` va `m_hat_1 <= m_hat_2 <= m_hat_3`, mot hang duoc
maxscore chap nhan (`m_hat_1 >= q_max`) tu dong vuot slot `j` cua studentized
khi `qhat_stud_j <= q_max`. Nhung `qhat_stud_3 > q_max`, nen nesting DOI HOI
do trai chi phi giua cac duong -- **dung truc ma Lesson 23.11 se thay doi**.

Dai luong EXACT, `nesting_slack_min = min` tren cac hang maxscore chap nhan cua
`min_j m_hat_j / (kappa * qhat_stud_j)`; nesting giu khi va chi khi `>= 1`:

```text
cell            nesting_slack_min   slot bi rang buoc   only_max
poisson@0.925        1.0271                2               0
poisson@0.850        1.0071                2               0
h2@0.700             1.0446                2               0
```

**Doc ky: bien do chi con 0.7% - 4.5%.** Nesting dang giu, nhung sat mep. Bat ky
profile nao lam chi phi cac duong sat nhau hon deu day so nay xuong duoi 1, va
khi do `only_max > 0`: se co hang bi MAT, va phai bao cao `err` tren hang bi
mat chu khong chi hang duoc them.

Hai dieu chinh so voi suy dien ban dau, ca hai deu do phep do sua lai:

1. **Slot bi rang buoc la slot 2, khong phai slot 3.** Suy dien "slot 3 chat
   nhat vi `qhat_3/q_max` lon nhat" sai, vi slack la `m_hat_j / qhat_j` va
   `m_hat_3` cung la margin lon nhat. Code do slot rang buoc thay vi gia dinh.
2. Can DU re tien (`min(m_hat_3/m_hat_1) >= max_j qhat_stud_j/q_max`) cho margin
   `-0.0308 / +0.3470 / +0.5334`. Am o main cell nhung nesting VAN giu -- can du
   khong phai can can. Artifact ghi no la `sufficient_condition_margin` va
   khong duoc doc nhu bang chung nesting vo.

Dien giai: nhung hang ma studentization THEM vao tap accept co ti le sai
`1.65 - 3.40%`, thap hon `alpha = 0.10` tu 3 den 6 lan. Acceptance tang len la
acceptance CO CHAT LUONG, khong phai noi long bua.

### Ngan sach rui ro dang dung rat it

```text
P(sai VA accept) = acceptance x p_wrong|accept, do o kappa = 1:

  poisson@0.925  stud  0.18572 x 0.01576 = 0.00293   ->  2.9% cua alpha=0.10
  poisson@0.850  stud  0.13562 x 0.01043 = 0.00141   ->  1.4%
  h2@0.700       stud  0.38674 x 0.00880 = 0.00340   ->  3.4%
```

`kappa = 1` dang bao thu qua muc `~30` lan. Day khong phai loi -- `kappa` la
tham so quet trong ho nguong NHAN va toan bo duong bien risk-coverage song o
`kappa < 1`. Con so nay duoc ghi vao du doan cua Lesson 23.6
(`R-23.6-1`, Amendment 23-21 muc 5.3).

## 5. Do lon cua loi ich duoc du bao boi mot dai luong do TRUOC khi chay

```text
cell            sigma3/sigma1  acc_max   acc_stud   delta tuyet doi  delta TUONG DOI
poisson@0.925       1.1204     0.16657    0.18572      +0.01915        +11.50%
poisson@0.850       1.3019     0.09520    0.13562      +0.04042        +42.46%
h2@0.700            1.4924     0.26112    0.38674      +0.12562        +48.11%

ratio slot 1: 0.9525 -> 0.8740 -> 0.7678   (don dieu giam theo sigma3/sigma1)
Spearman(sigma3/sigma1, delta_acc_rel) = 1.0000  voi n = 3
```

Voi `n = 3` day la GIA THUYET, khong phai dinh luat. No se duoc kiem tren 5
profile cua Lesson 23.11 (`H-23.11-1..3`, Amendment 23-21 muc 5.1).

MISS phai ghi: ghi chep truoc khi chay du bao studentization "chi mua them
1-2 diem phan tram acceptance". Du bao dung tren main cell va SAI tren hai cell
phu (+42%, +48% tuong doi). Loi la ngoai suy tu MOT cell sang ca ba -- dung loi
`S6`: ba cell khong phai mot truc thi nghiem.

## 6. Phat hien ngoai du kien -- F-23.5A-1

```text
F-23.5A-1  `c` gan nhu BAT BIEN theo bin tuoi khi sigma uoc PER-BIN.
Trang thai: [MO TA], phat hien ngoai du kien, KHONG confirmatory.
Chuyen giao: Lesson 23.9 (P23-E) -- day la co che cho transfer.
```

Do duoc, `c` theo bin:

```text
sigma PER-BIN:
                  bin0     bin1     bin2     bin3  | (max-min)/mean | /min
poisson@0.925   2.1018   2.1252   2.1030   2.0928  |     1.54%      | 1.55%
poisson@0.850   2.1946   2.1842   2.1596   2.1418  |     2.43%      | 2.47%
h2@0.700        1.9661   2.0340   2.0609   2.0672  |     4.98%      | 5.14%

sigma TOAN CUC:
poisson@0.925   1.1535   1.5715   1.9557   2.4336  |    71.97%      | 110.97%
poisson@0.850   1.2227   1.6252   2.0149   2.4879  |    68.85%      | 103.47%
h2@0.700        1.2861   1.6079   1.9458   2.3527  |    59.32%      |  82.94%
```

(Hai cot bien do khac nhau o mau so; ca hai duoc in de tranh nham lan.)

Doc bang:

```text
qhat(z, j)  =  c(z) x sigma(z, j)

sigma per-bin  -> c gan HANG SO   (bien thien 1.5 - 5.0% theo mean)
sigma toan cuc -> c phai ganh toan bo su phu thuoc z (59 - 72% theo mean)

=> TOAN BO su phu thuoc cua qhat vao tuoi z nam trong THANG sigma(z).
=> HINH DANG chuan hoa cua phan phoi score KHONG doi theo tuoi.
```

Vi sao quan trong: Lesson 23.9 (P23-E) hoi "hieu chuan o MOT bin tuoi roi ngoai
suy sang bin khac duoc khong?". Day la dieu kien du cho viec do:

```text
qhat(g, j) = c(g0) * sigma(g, j)

(1) c bat bien theo bin        -- DA DO: dung trong 1.5 - 5.0%
(2) sigma(g, j) uoc duoc o bin dich
    sigma la mot RMS, hoi tu nhu 1/sqrt(n); phan vi 90% can n lon hon nhieu lan
=> bin dich chi can IT DU LIEU HON HAN
```

Do la duong tra loi cho `G23-51` ("N* ma transfer thang hieu chuan truc tiep"),
va may moc da co san: `estimate_sigma()` va `qhat_studentized()`.

Ghi chu phuong phap: phat hien nay chi lo ra vi `c` duoc in THEO TUNG BIN thay
vi gop. Neu chi in `mean(c)` no bien mat khong dau vet.

## 6b. Kiem tra tai lap qua bien moi truong

Lan chay 2026-08-17 dung mot moi truong KHAC lan chay Phase 22
(`python 3.12`, `pandas 3.0.2`, `numpy 2.4.3`, `pyarrow 25.0.1`; ghi trong
`provenance.env` cua ca ba artifact). Vi Phase 23 tinh lai maxscore tu cung
parquet qua cung duong ong, moi sai khac se la sai khac MOI TRUONG chu khong
phai sai khac phuong phap. Do duoc, so voi
`results/phase-22/conformal_sim_<cell>.json` da commit:

```text
cell            acceptance diff   coverage diff   qhat max diff   bit_exact
poisson@0.925        0.0              0.0             0.0           true
poisson@0.850        0.0              0.0             0.0           true
h2@0.700             0.0              0.0             0.0           true
```

Vi du main cell:

```text
acceptance maxscore:  0.16656899355357455  (nay)  ==  0.16656899355357455  (P22)
coverage  maxscore:   0.906661839681419    (nay)  ==  0.906661839681419    (P22)
qhat bin0:            15.271990776062012   (nay)  ==  15.271990776062012   (P22)
```

Duong ong tai lap bit-exact qua mot bien moi truong. Duoc chot bang test
`test_T22_maxscore_reproduces_phase22_artifact_exactly` de lan sau doi env la
biet ngay.

## 7. Ket luan GO-3

Thu tuc studentized max-score da ky o Amendment 1 Phase 22 duoc chay nhu
EXPLORATORY tren ba cell khong suy bien. Bao phu dong thoi giu tren ca ba
(0.9048 / 0.9095 / 0.9113; nominal 0.90, dung sai +/-0.02). Doi chung am
NC-S-1 khop CHINH XAC (sai khac 0.0 o 12/12 o), xac nhan thu tuc quy ve
max-score khi sigma dong nhat.

Studentization tai phan bo ngan sach dung nhu ly thuyet du doan: `qhat` o rank
slot 1 hep lai (ti so 0.7678-0.9525) va o slot 3 rong ra (1.0671-1.1411). Ca 9
ti so nam trong can dai so dan truoc khi do. Vi acceptance chi phu thuoc slot 1
(`slot1_decides_share = 1.0` voi max-score, chung minh duoc tu
`m_hat_1 <= m_hat_2 <= m_hat_3`), viec thu hep co muc tieu nay lam acceptance
tang `+11.5% / +42.4% / +48.1%` tuong doi, o coverage khong doi. Tap accept moi
CHUA TRON tap cu (`only_max = 0`, do truc tiep), va cac hang duoc them co ti le
sai `1.65 - 3.40%`, thap hon `alpha` tu 3 den 6 lan. Nesting nay la tinh chat
CUA DU LIEU chu khong phai dinh ly, va bien do dang rat mong
(`nesting_slack_min = 1.0271 / 1.0071 / 1.0446`); no se duoc theo doi o 23.11
noi chi phi cac duong duoc lam sat nhau (muc 4.1, `H-23.11-4`).

Doi chung duong PC-S-1d con cho mot ket qua manh hon muc tieu ban dau: nhanh
CLEAN giu bao phu trong TUNG bin Mondrian o moi `p_per_bin` len toi `3000`, tuc
khi `sigma` chi duoc uoc tren ~2 block moi o va gan nhu vo nghia. Bao phu co
dieu kien theo o `m_hat` thi VO hoan toan o muc do (`spread -> 1.0`), dung nhu
ly thuyet bat kha thi du bao. Hai dieu nay cung nhau khoanh chinh xac pham vi
ma dinh ly muc 3.3 hua.

Do lon cua loi ich duoc du bao boi muc bat dong nhat giua rank slot,
`sigma3/sigma1 in [1.12, 1.49]`: ba cell xep hang don dieu theo dai luong nay
(Spearman = 1.0, `n = 3`). Voi `n = 3` day la mot GIA THUYET, khong phai dinh
luat; no se duoc kiem tren 5 profile cua Lesson 23.11.

Doi chung duong: PC-S-1 o `p = 3` KHONG phat hien duoc ro ri, va do la mot
phat bieu co co so chu khong phai mot phep do mu -- PC-S-1d cho thay cung phep
do coverage nay phat hien ro ri rat ro khi `p` tang (`drop -> 0.215` o
`p/bin = 3000`), trong khi nhanh CLEAN van giu `~0.90` o moi `p`.

Chi phi: mat mot nua du lieu hieu chuan cho viec chia fold, them mot bac tu do
(uoc luong tu `sigma`), va khong co bao dam nao rang `qhat` nho di o moi slot.

Trang thai GO-3: DONG. Giu nhan EXPLORATORY. Khong dua vao duong ong
confirmatory cua Phase 23. Chuyen sang Phase 24 nhu mot tuy chon cau hinh da
duoc dinh luong, va sang Lesson 23.9 nhu co che cho transfer giua bin tuoi
(xem phat hien F-23.5A-1).

## 8. Cac dong da ghi MISS trong lesson nay

```text
S-5 dai v1 [1.5, 3.0]       MISS -- da ghi tu Amendment 23-20
S-1 dai v1 [1.15, 1.30]     MISS -- da ghi tu Amendment 23-20
G3b slot 3 dai v1           MISS -- da ghi tu Amendment 23-20
S-5 dai v2 [1.05, 1.50]     MISS -- MOI, h2@0.700 bin 0 = 1.6557 (muc 2.2)
"hieu ung nho 1-2 pp"       MISS -- MOI, sai tren 2/3 cell (muc 5)
PC-S-1 small-n cu           HUY BO -- tran chan, khong phai MISS (muc 3)
```

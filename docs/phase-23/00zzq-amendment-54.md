# AMENDMENT 23-54 -- song nui T_loss, dong nhat thuc S_pivotal, tach confound sigma

Ngay ky : 2026-08-23
Tag     : amendment-54
Lesson  : 23.21c
Loai    : TIEN DANG KY
Prereq  : amendment-53 (`d2620fd`), Lesson 23.21b (`65a34fc`)

## 0. Hai hieu chinh so voi ban thao ngoai repo

```text
(a) Spearman(t_loss_endo, T*) = 0.9856, KHONG phai 0.9429. Tinh lai tren
    6 cell trong luoi (`scipy.stats.spearmanr`). Ket luan manh HON ban thao.

(b) Ban thao cap `L55` cho HAI viec khac nhau (dong nhat thuc, va "khong tai
    dung duoc parquet"). Mot ma - mot han che: `L55` cho dong nhat thuc,
    va viec parquet lay `L59` neu no xay ra.
```

## 1. Phat hien HAU NGHIEM tu 23.21b -- KHONG duoc dung de dien giai 23.21b

### (a) SONG NUI TRUNG NGUONG NOI SINH

Doi chieu dinh cua `S_pivotal` voi nguong `t_loss` ma thu tuc TU HIEU CHUAN cu
da sinh ra:

```text
cell             t_loss_endo        T*      t_endo/T*
poisson@0.700         0.0004     0.001         0.42
poisson@0.850         0.0072     0.010         0.72
poisson@0.925         0.0292     0.020         1.46
poisson@0.960         0.0479     0.050         0.96
h2@0.700              0.0265     0.020         1.32
h2@0.850              0.1103     0.100         1.10
h2@0.925              0.1668     ngoai luoi      --   (t_endo > 0.100, cung chieu)
h2@0.960              0.1946     ngoai luoi      --   (t_endo > 0.100, cung chieu)

Spearman tren 6 cell trong luoi = 0.9856
Moi ty so nam trong [0.42, 1.46]; buoc luoi hien tai la he so 2.0-2.5
=> KHONG lech nao qua MOT buoc luoi, tren mot dai t_loss trai 500 lan
   (0.0004 -> 0.1946).
```

Y nghia: thu tuc tu hieu chuan khong chi lam nguong PHU THUOC du lieu. No dat
nguong cua MOI cell vao (trong mot buoc luoi) dung diem ma bai toan chon duong
o cell do trong HUU ICH NHAT.

CO CHE la CO HOC, khong phai y do -- va phai viet dung nhu vay:

```text
(1) t_loss_endo = phan vi ~p88-92 cua mat goi tren duong toi uu
                  -> no bam theo THANG DO cua phan phoi mat goi trong cell
(2) dinh S_pivotal nam o noi nguong CAT QUA than cua phan phoi
                  -> cung bam theo THANG DO do
=> hai dai luong cung theo MOT bien tiem an. Trung nhau la TAT YEU.
   Khong ai gian lan, va ket qua VAN bi thien lech.
```

### (b) DONG NHAT THUC cua `S_pivotal`

```text
S_pivotal(T) = F_min(T) - F_max(T)
    F_min = CDF cua  min_j loss_j(t)     (duong TOT nhat)
    F_max = CDF cua  max_j loss_j(t)     (duong TE nhat)
```

Dieu kien de no CHINH XAC: truc tre phai TRO, tuc
`percentile_of_t_delay = 100.0` o moi cell -- da do duoc o 23.21.

Kiem tren 12 cell (8 goc + 4 Dot 4), dung `percentile_of_t_loss/100 - S_trivial`
lam dai dien cho `F_min - F_max`:

```text
lech lon nhat = 1.44e-03   (o h2@0.650)
lech = 0 chinh xac o 5/12 cell
```

Phan du la cho `argmin cost != argmin loss`: tre van gop vao `argmin` du khong
gop vao vi pham.

**Ca (a) va (b) la HAU NGHIEM.** Chung phai duoc KIEM tren du lieu MOI (luoi
`T_loss` min + luoi `rho` moi), KHONG duoc dung de dien giai 23.21b.

## 2. `M-135` -- ly do THU BA, khong sua duoc bang thong ke

```text
phan hoach err_neo : moi cell do duoi SLA + w_loss NOI SINH CUA CHINH NO
                     (w_loss troi 1245.6 -> 4722.7; t_loss troi 0.0004 -> 0.1946)
phan hoach regime  : moi cell do duoi MOT SLA CHUNG (50 ms, 1%, w = 5000)

=> hai ve do duoi HAI HAM MUC TIEU KHAC NHAU
=> phep so sanh KHONG DAT DUNG (ill-posed), DOC LAP voi kich thuoc mau
```

Va muc 1a lam no te hon: `err_neo` do duoi SLA nam o DINH song nui cua tung cell.

```text
Ba ly do doc lap khien M-135 khong mang bang chung:
  (i)   tran bi bien chan: 6/8 la max, P(ngau nhien) = 0.214, kappa = 0.50
  (ii)  h2@0.700 doi sang AMBIGUOUS sau khi co CI
  (iii) hai ve do duoi hai ham muc tieu khac nhau -- ILL-POSED

(i) va (ii) la van de THONG KE. (iii) KHONG sua duoc bang thong ke;
chi sua duoc bang DO LAI err_neo duoi SLA chung.
```

```text
QUYET DINH: M-135 GIU HIT da bao cao (khong sua ket qua da ky).
            CAM dung no de bien minh bat ky phat bieu nao.
            Cot `err_neo` trong bang hai chieu `G23-167` hien dang la so
            NOI SINH -- bang do dang TRON hai truc SLA. Phai ghi ro dieu do
            cho den khi do lai duoc.
```

Han che moi: `L57`.

## 3. Confound `sigma_rho` theo `rho`

```text
sigma = 0.9 * sigma_max_regime(rho),  va sigma_max KHONG don dieu:

rho     0.575  0.625  0.650  0.675  0.700  0.775  0.850  0.925  0.960
sigma   0.0026 0.0201 0.0288 0.0375 0.0462 0.0724 0.0480 0.0218 0.0096
                                            ^^^^^^ dinh o rho ~ 0.775

h2@0.650  sigma = 0.0288  }  chenh 1.60 lan giua hai cell dang duoc so sanh
h2@0.700  sigma = 0.0462  }
```

Quet `rho` doi DONG THOI MUC tai (`rho_bar`) va DO BIEN DONG cua tai
(`sigma_rho`). Duong cong `S_pivotal(rho)` la mot duong cong TRON hai hieu ung.

Day la CUNG LOP LOI voi `L37` (`U1`/`U2` khong bao toan trung binh nen so
`U0/U1/U2` do dong thoi hinh dang VA muc tuoi), tai xuat o mot truc khac.

```text
QUYET DINH: moi phat bieu dang "vung song nam o rho thuoc [x, y]" PHAI kem
            doi chung `sigma` CO DINH. Khong co doi chung do thi khong duoc
            viet cau do.

            sigma = 0.020 kha thi o rho thuoc [0.625, 0.925] (do duoc:
            sigma_max >= 0.0201 tren toan dai do). rho = 0.960 va rho <= 0.600
            KHONG kha thi o sigma nay va bi loai khoi luoi doi chung.
```

Han che moi: `L58`.

## 4. Du doan -- DIEN TRUOC KHI CHAY

| id | dai luong | loai | dai da ky | do duoc | KQ |
|---|---|---|---|---|---|
| M-147 | median \|log2(t_loss_endo / T*)\| tren luoi min 1.25x, 8 cell | CO CHE | <= 0.50 | | |
| M-148 | so cell co \|log2(t_endo/T*)\| <= 1.0 (mot he so 2) | CO CHE | >= 7/8 | | |
| M-149 | lech lon nhat cua dong nhat thuc `F_min - F_max` tren luoi rho MOI | CO CHE | <= 5e-3 | | |
| M-150 | dinh `S_pivotal` cua ho `h2` theo `rho` | NGOAI SUY | `rho` <= 0.625 hoac KHONG KEP DUOC | | |
| M-151 | dinh `S_pivotal` cua ho `poisson` theo `rho` | NGOAI SUY | `rho` thuoc [0.775, 0.875] | | |
| M-152 | o `sigma` CO DINH, `S_pivotal(rho)` con don dieu giam tren ho `h2` | CO CHE | KHONG con don dieu giam | | |
| M-153 | so cell LIVE theo CA HAI tieu chi tren luoi day du | NGOAI SUY | >= 3 (dai 3..8) | | |

Ghi chu:

```text
M-150/M-151  neu dinh nam o MUT cua luoi thi ket qua la "KHONG KEP DUOC",
             KHONG duoc ghi la dinh. Bai hoc `M-142` (HIT*) va `L53`.

M-152  la du doan CO CHE quan trong nhat cua ban nay. Neu o `sigma` co dinh
       ho `h2` VAN don dieu giam theo `rho`, thi dinh la do MUC TAI va
       confound `L58` khong quan trong. Neu no HET don dieu, thi duong cong
       o luoi chinh phan lon la hieu ung cua `sigma`, va MOI phat bieu ve
       "vung song theo rho" o 23.21b phai viet lai.
       Da ky "KHONG con don dieu giam" -- tuc du doan rang confound CO that.

M-147/M-148  dung `log2` de ty so 0.42 va 2.38 doi xung quanh 0.
             Luoi min he so 1.25 -> mot buoc = log2(1.25) = 0.32.
```

## 5. Gate

| id | noi dung | nguong |
|---|---|---|
| G23-169 | luoi `T_loss` log 1.25x, 32 diem, moi cell; `T*` bao cao kem buoc luoi | bat buoc |
| G23-170 | doi chieu `t_loss_endo` vs `T*`, ca 8 cell, ke ca cell ngoai luoi | bat buoc |
| G23-171 | dong nhat thuc `F_min - F_max` kiem tren luoi `rho` MOI, lech bao cao | bat buoc |
| G23-172 | doi chung `sigma` CO DINH = 0.020: `S_pivotal(rho)` tren `rho` [0.625, 0.925] | bat buoc |
| G23-173 | dinh nam o mut luoi -> ghi "KHONG KEP DUOC", KHONG ghi la dinh | bat buoc |
| G23-174 | test digest parquet chay TRUOC khi dung lai calib set | bat buoc |

## 6. Han che moi

```text
  L55  `S_pivotal = F_min - F_max` do CAC DUONG KHAC NHAU BAO NHIEU, KHONG do
       duoc lieu twin CU co chon dung duong hay khong. `S_pivotal` cao KHONG
       keo theo "chung nhan co gia tri". BAT BUOC dung kem truc `err_neo`:
       bang hai chieu khong phai mot cach trinh bay dep, ma la dieu kien CAN
       ve mat logic.
  L56  (neu xay ra) dinh `S_pivotal` cua ho `h2` nam duoi `rho` = 0.575, tuc
       NGOAI mien kha thi cua mo hinh (`sigma_max` -> 0 duoi do).
  L57  `M-135` so sanh hai phan hoach do duoi HAI ham muc tieu khac nhau
       (err_neo: SLA noi sinh tung cell; regime: SLA chung). Ill-posed, doc
       lap voi n. Cot `err_neo` cua bang `G23-167` dang TRON hai truc SLA.
  L58  Quet `rho` doi DONG THOI `rho_bar` va `sigma_rho` (`sigma` = 0.9 *
       `sigma_max(rho)`, va `sigma_max` co dinh o `rho` ~ 0.775). Cung lop
       loi voi `L37`.
```

## 7. Dieu KHONG lam

```text
- KHONG dung phat hien 1a/1b de dien giai 23.21b (chung la HAU NGHIEM)
- KHONG tinh lai M-135
- KHONG dung lai calib parquet truoc khi `G23-174` chay
- KHONG viet cau "vung song nam o rho thuoc [x,y]" truoc khi co `G23-172`
```

So ke tiep: `L59`, gate so 175, `M-154`, `K07`.

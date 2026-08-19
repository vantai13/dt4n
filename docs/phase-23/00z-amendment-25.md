# AMENDMENT 23-25 -- Doi dinh danh C -> K, ghi F-23.5-2, va khoa thu tuc Lesson 23.6

Ngay: 2026-08-18
Commit: sau khi dong Lesson 23.5 (`c03cbf5`), TRUOC khi viet code Lesson 23.6.

---

## 1. Xung dot dinh danh -- sua TRUOC moi thu

### 1.1. Van de

```text
00-preregistration.md hien tai:  C-1 .. C-5  =  GO-2 / Lesson 23.5[C]   DA DIEN
Ban ke hoach 23.6 de xuat     :  C-1 .. C-6  =  Lesson 23.6 (c*)        SAP DUNG
```

Dien `C-1 = c*(0.78)` vao bang dang co `C-1 = c_supt` se lam hong khoa chinh
cua bang pre-registration. Day dung la loai toan ven tham chieu `NT-v2-7` bao ve.

### 1.2. Quyet dinh

```text
K-D0  Cac dong du doan cua Lesson 23.6 mang tien to K ("cost of abstain"),
      danh so K-1 .. K-8.
      C-1 .. C-5 GIU NGUYEN cho GO-2, khong dong toi.
      Day la doi DINH DANH, khong doi noi dung du doan nao.
```

### 1.3. Kiem tra va cham -- lam duoc den dau, va khong lam duoc gi

`PHASE_23_v2` KHONG co trong repo (giong `MASTER_PLAN.md` va `PHASE_23.md` goc;
xem `docs/phase-23/PLAN.md` dong dau). Vi vay **khong the ra soat §8.3-8.7 cua
tai lieu do de tim va cham khac** -- toi khong doc duoc no.

Thay vao do, liet ke TOAN BO dinh danh dang dung, de moi tien to tuong lai
duoc doi chieu voi mot danh sach THAT:

```text
tien to A  -> A-1' A-2' A-3' A-4' A-5' A-6' A-6'b A-7' A-8'    (GO-1, 23.5[B])
tien to B  -> B1p B2p B3p B4p B5p B6p                          (23.3)
tien to C  -> C-1 C-2 C-3 C-4 C-5                              (GO-2, 23.5[C])
tien to F  -> F0 F1 F2 F3 F4 F5 F6                             (23.1)
tien to G  -> G3a G3b                                          (GO-3)
tien to S  -> S-5 S-8                                          (23.5[A])
tien to T  -> T2 T3 T4                                         (23.2)
tong 34 dong, KHONG co trung lap hien tai.

Tien to CON TRONG: K L M N Q R U V W X Y Z
(P da dung cho P1..P20 quyet dinh khoa; R da dung cho R-23.6-1; H cho H-23.11-*)
```

```text
K-D0b  Truoc khi mo BAT KY lesson nao, phai chay lai phep liet ke nay va doi
       chieu tien to du dinh dung. Neu `PHASE_23_v2` duoc dua vao repo, phai
       ra soat toan bo §8 cua no NGAY luc do -- day la mot muc CON NO.
```

---

## 2. RA SOAT DU DOAN (NT-v2-7 ap cho chinh amendment nay)

Amendment nay doi dinh danh va them dai luong moi. Cac dong da khoa lien quan:

| Dong da khoa | Xu ly | Ly do |
|---|---|---|
| C-1 .. C-5 (GO-2) | GIU NGUYEN | chi doi tien to cua lesson KHAC, khong dong toi |
| R-23.6-1 (Amd 23-21 §5.3) | GIU NGUYEN | van la du doan ve `kappa < 1`, khong bi K-D nao doi |
| A-1'..A-8', S-5, S-8 | GIU NGUYEN | khong lien quan |
| H-23.11-1..4 (Amd 23-21, 23-24) | GIU NGUYEN | bo sung H-23.11-5/6, khong sua cai cu |
| G23-8/14/15/17/23 | **TAI BAN** thanh DIAGNOSTIC | Lesson 23.6 tuyen bo fallback la tham so NGOAI SINH (NT-v2-1); cac gate nay do dai luong phu thuoc fallback nen khong con la gate. KHONG rut so lieu nao. |

---

## 3. Sua nhan nguon cua C-1 -- loi ghi nhan, khong sua hoi to ket qua

```text
C-1 (`c_supt in [2.2, 2.7]`) duoc ky nhan [CO CHE].
Nhan do SAI. Dai duoc dan tu mot truc giac vo huong ("24 dai luong tuong quan
manh"), khong tu mot co che tinh duoc. Nhan dung la [KINH NGHIEM].

KHONG sua ket qua: C-1 van la MISS, va van duoc cham nhu da cham.
Chi sua NHAN NGUON, va ghi day la loi ghi nhan.
```

### 3.1. Nguyen tac rut ra

```text
NT-v2-8  `c_supt` (va moi hang so toi han cua mot thong ke MAX) KHONG suy duoc
         tu mot tom tat VO HUONG cua ma tran tuong quan -- khong tu `corr`
         trung binh, khong tu so chieu hieu dung, khong tu eigenvalue.
         No phai duoc MO PHONG.
         Du doan ve `c_supt` dua tren heuristic phai mang nhan [KINH NGHIEM].
         Chi duoc mang nhan [CO CHE] neu co mot mo phong da chay TRUOC khi ky.
```

Bang chung cho `NT-v2-8`, do duoc o Lesson 23.5[C]:

```text
Kaiser cho K_eff = 6 (6 eigenvalue > 1) tren 24 dai luong.
   c_sidak(K=6)  = 2.6310
   c_sidak(K=24) = 3.0708
   DO DUOC c_supt = 2.857 .. 2.962      <- gan K=24 hon HAN K=6
Heuristic "so chieu hieu dung" hut 0.23-0.33. Ly do: eigenvalue dem CHIEU chu
khong phan biet DAU. Tuong quan am lam giam eigenvalue (trong nhu it chieu hon)
nhung lai LAM TANG E[max].
```

---

## 4. F-23.5-2 -- `sigma3/sigma1` sap hang CA [A] LAN [C]

Trang thai: **[MO TA]**, phat hien ngoai du kien, KHONG confirmatory.

### 4.1. Do duoc (tinh lai doc lap tu artifact Phase 22 va 23)

```text
cell             s3/s1   rms(s_sim)/s1 | delta_1 theo bin (bonf - max)  | C-5 slot1
poisson@0.925   1.1111      1.4652     | -0.088 -0.116 -0.169 -0.110    | 8 zero
poisson@0.850   1.2906      1.6213     | -0.471 -0.584 -0.604 -0.814    | 8 neg
h2@0.700        1.4005      1.6866     | -2.632 -2.638 -2.391 -2.384    | 8 neg

                 sigma3/sigma1   |delta_1|/sigma_1   [A] d_acceptance tuong doi
poisson@0.925       1.1111            0.0095                 +11.50%
poisson@0.850       1.2906            0.1766                 +42.46%
h2@0.700            1.4005            0.3535                 +48.11%

Spearman(sigma3/sigma1, |delta_1|/sigma_1)  = 1.0000   (n = 3)
Spearman(sigma3/sigma1, d_acceptance)       = 1.0000   (n = 3)
```

**Mot dai luong duy nhat, do duoc tu Phase 22, sap hang CA HAI ket qua doc lap.**
Va nguong cua no quyet dinh `slot 1` la `zero` hay `neg` trong `C-5`.

### 4.2. Dan giai dai so -- dung DAU va THU HANG, khong dung gia tri

Voi score dang nua-chuan, phan vi mot phia `Q_p(s_j) = k_p * sigma_j`:

```text
k_{0.90}   = 1.6449        k_{1-alpha/3} = k_{0.9667} = 2.1284
qhat_max   = Q_{0.90}(max_j s_j) = k_max * rms(s_sim)

=> delta_1 / sigma_1  ~  2.1284 - k_max * [rms(s_sim)/sigma_1]
                                          ^^^^^^^^^^^^^^^^^^^^ TANG theo s3/s1
```

Kiem tren ba cell (suy nguoc `k_max` thay vi gia dinh):

```text
cell             do d1/s1   2.128-1.495*r   k_max suy nguoc   sai lech
poisson@0.925     -0.0095      -0.0625           1.4589        -0.0530
poisson@0.850     -0.1766      -0.2959           1.4214        -0.1193
h2@0.700          -0.3535      -0.3935           1.4713        -0.0399
```

Doc dung:

```text
* DAU: dung 3/3 cell (deu am).
* THU HANG: dung 3/3 cell.
* GIA TRI: KHONG dung. Voi k_max = 1.495 co dinh, du bao vuot 0.04-0.12.
* NHUNG k_max suy nguoc rat ON DINH: 1.4214 .. 1.4713, bien do 3.5%.
  Mot HANG SO duy nhat lam duoc viec tren ca ba cell -> co che duoc ung ho,
  chi la hang so 1.495 (lay tu bridge_to_rms cua mot cell) hoi cao.
```

### 4.3. Vi sao `delta_1` la o mong manh nhat

```text
delta_1 la HIEU cua hai so ~15 ms de ra mot so ~0.1 ms (tren cell chinh).
Sai so 1% cua xap xi nua-chuan tren 15 ms = 0.15 ms -- LON HON chinh delta_1.
=> "8 zero" o C-5 KHONG phai "khong co hieu ung"; no la
   "hieu ung nho hon do phan giai". Phai viet dung nhu vay.
```

### 4.4. Cau duoc phep viet, va cau khong

```text
DUOC:  "Mau hinh dau phu thuoc slot khong phai quan sat ngau nhien. No suy duoc
        tu viec max-score hieu chuan tren max_j s_j -- dai luong bi slot cao
        nhat chi phoi -- trong khi Bonferroni hieu chuan tren tung s_j rieng.
        Chung toi dan delta_1/sigma_1 ~ k_{1-alpha/m} - k_max*rms(s_sim)/sigma_1,
        du bao dung DAU va THU HANG tren ca ba che do. Dong gop thuc nghiem la
        DINH LUONG hieu ung va chung minh no song sot hieu chinh dong thoi 95%
        tren 24 dai luong, chu khong phai phat hien su ton tai cua no."

KHONG:  "Chung toi phat hien rang thu tu FWER phu thuoc slot."
        Dau bi ep boi cau truc; noi "phat hien" la noi qua.
```

---

## 5. Khoa TRUOC Lesson 23.11

```text
H-23.11-5  Tren 5 profile, dau cua delta_1 chuyen tu `zero` sang `neg` khi
           sigma3/sigma1 vuot mot nguong. Du doan nguong: 1.15 - 1.30.
           Nhan [CO CHE], dan tu  2.1284 - k_max * rms(s_sim)/sigma_1 = 0
           voi k_max in [1.42, 1.47] (muc 4.2).

H-23.11-6  Dan giai dai so du bao dung THU HANG cua |delta_1| tren ca 5 profile.
           Nhan [CO CHE]. Spearman >= 0.9.
           Neu SAI: co che bi bac bo, va F-23.5-2 tro thanh trung hop n=3.
```

---

## 6. Quyet dinh khoa cho Lesson 23.6

### 6.1. Tai khung -- va noi thang no la tai tham so hoa

```text
R_system(gamma, c) = gamma * R|accept(gamma) + (1 - gamma) * c
CO LOI  <=>  c < R|reject(twin, gamma)  =:  c*(gamma)

c* KHONG phu thuoc fallback nao; no DO DUOC tu twin + certificate.
```

```text
K-D7  Doc 23.6 PHAI viet ro, TRUOC khi trinh bay so:
      "R_neo = gamma*R|accept + (1-gamma)*R|reject la DINH LY xac suat toan
       phan. Do do R_system(gamma, c*) = R_neo la mot DONG NHAT THUC, dung
       theo dinh nghia, va G23-32 (kiem <= 1e-12) la kiem tra DUNG CODE, khong
       phai mot ket qua. Dong gop nam o: (1) TAI KHUNG cau hoi khong tra loi
       duoc thanh cau hoi tra loi duoc; (2) GIA TRI c*(gamma) kem CI; (3) DINH
       VI F1/F2/F3 nhu ba diem tren mot truc lien tuc."
```

### 6.2. Thang do -- `c` phai cung thang voi `R`

```text
K-D1  c* headline dung thang `err`. Khoa.
K-D2  BAT BUOC bao cao c*_regret song song (don vi ms). Khong lam headline
      (Amendment 23-18). Ly do: nguoi van hanh quan tam do tre, khong chi ti le sai.
K-D3  MOI khoa trong artifact mang hau to thang: c_star_err, c_star_regret.
      Thuc thi bang test quet JSON (mau: test_T24 cua Lesson 23.5[A]).
```

### 6.3. Luoi gamma -- va mot loi da bat duoc bang mo phong

```text
K-D4  Luoi gamma = np.arange(0.0, 1.0, 0.02) -> 50 diem, tu 0.00 den 0.98.
      gamma = 1.0 BI LOAI KHOI LUOI.
      Ngoai suy CAM.
```

Ly do loai `gamma = 1.0` -- phat hien khi chay mo phong tong hop:

```text
gamma = 1  =>  chap nhan TAT CA  =>  tap reject RONG  =>  c*(1) = 0/0 KHONG XAC DINH.
Mo phong: luoi den 1.00 cho K=51 nhung chi 50 cot huu han; cot cuoi la nan.
Neu de nguyen, supt_band se hoac no hoac am tham bo cot -- ca hai deu xau.
gamma = 1 duoc xu ly RIENG nhu doi chung am NC23v2-5 (muc 6.5), khong nam tren luoi.
```

### 6.4. Dai DONG THOI la bat buoc

```text
K-D5  Figure 4 ve CA DUONG c*(gamma) va nguoi doc doc no DONG THOI.
      50 khoang tung-diem 95% => ky vong 2.5 diem sai ngau nhien tren duong.
      => dung supt_band() tren 50 dai luong. Dai tung-diem bao cao KEM, khong thay the.
```

### 6.5. Doi chung tu than -- ba dang thuc cho khong

```text
NC23v2-4  c*(0) = R_neo CHINH XAC. (gamma=0 => reject tat ca => R|reject = R_neo)
          poisson@0.925: c*(0) phai = 0.222399
NC23v2-5  gamma = 1 => R_system = R_neo VOI MOI c   (vi (1-gamma)*c = 0)
NC23v2-6  c = 0 => R_system = gamma * R|accept      (can duoi tam thuong)
PC23v2-1  c = 1 => R_system > R_neo voi MOI gamma < 1
```

### 6.6. K-6 la GATE ve bo chon, khong phai du doan ve c*

```text
K-D6  c*(gamma) don dieu TANG la CAU TRUC: gamma tang => tap reject thu hep,
      chi con ca KHO NHAT => err|reject tang.
      Neu do duoc KHONG don dieu tang => certificate xep hang ca SAI o dau do.
      => K-6 duoc doc la mot GATE ve CHAT LUONG BO CHON, khong phai mot du doan
         ve c*. Ghi dung nhu vay trong bang.
```

### 6.7. Tai su dung ha tang -- va vi sao lan nay nen duoc

```text
c*(gamma) = (so hang SAI va BI TU CHOI) / (so hang BI TU CHOI)
          = sum_b n_wrong_reject[b] / sum_b n_reject[b]      <- TI SO CUA TONG

=> block_sufficient_stats() cua [B] dung lai duoc (doi n_acc -> n_reject).
=> paired block bootstrap cua [B] dung lai nguyen.
=> supt_band() cua [C] dung lai cho dai dong thoi tren luoi gamma.
=> chi phi moi draw O(n_block), khong phai O(n_row).

Doi lap voi 23.5[C]: qhat la PHAN VI, khong phai ti so cua tong, nen KHONG nen
duoc -- do la ly do [C] ton 46 s/cell con 23.6 se ton vai giay.
```

---

## 7. Bang du doan Lesson 23.6

| ID | Dai luong | Nhan | Dai khoa |
|---|---|---|---:|
| K-1 | `c*_err(0.78)` tren cell chinh | [NGOAI SUY] | 0.42 - 0.47 |
| K-2 | `c*_err(0)` = `R_neo` | [TAT DINH] | 0.222399 |
| K-3 | `c*_err(0.50)` tren cell chinh | [NGOAI SUY] | 0.30 - 0.40 |
| K-4 | `F2 STATIC` co vuot `c*` o `gamma = 0.78` khong? | [CO CHE] | xem so do |
| K-5 | So cell (trong 3) co `c*(0.78) > err_neo` | [CO CHE] | 3 |
| K-6 | `c*(gamma)` don dieu khong giam tren luoi | [GATE bo chon] | CO |
| K-7 | `c_supt` tren 50 diem `gamma` | [CO CHE] | 2.2 - 3.0 |
| K-8 | `c_supt / c_bonferroni(50)` | [CO CHE] | 0.67 - 0.92 |

### 7.1. Co so cua K-7/K-8 -- mo phong da chay TRUOC khi ky (NT-v2-8)

Theo `NT-v2-8`, `[CO CHE]` cho `c_supt` chi hop le neu co mot mo phong da chay
truoc. Da chay, **CHI tren du lieu TONG HOP** de khong cham cau tra loi that:

```text
Thiet ke mo phong: 500 block x 400 hang, do kho tiem an co tuong quan trong
block, P(sai) tang theo do kho, tap reject LONG NHAU theo gamma. B = 400 draw.

luoi 0.00..0.98 buoc 0.02 (K = 50):
    c_supt = 2.6749   c_bonferroni(50) = 3.2905   supt/bonf = 0.8129
    corr trung binh giua cac diem gamma = +0.7546
```

```text
Doc mo phong:
* Tuong quan giua cac diem gamma la DUONG MANH (+0.75), NGUOC HAN voi [C]
  (giua cac slot la -0.204). Ly do cau truc: tap reject o gamma va gamma+0.02
  chia se gan nhu toan bo hang. Day la co che, khong phai phong doan.
* c_supt mo phong = 2.67 nam o MEP TREN cua dai [2.0, 2.7] de xuat ban dau.
  Dai da duoc NOI RONG thanh [2.2, 3.0] va [0.67, 0.92] truoc khi ky.
* Canh bao: mo phong chi khop CAU TRUC (long nhau), khong khop DO MANH tuong
  quan cua du lieu that. Neu du lieu that tuong quan manh hon, c_supt se THAP
  hon 2.67; neu yeu hon, cao hon. Dai duoc dat de bao ca hai chieu.
```

Danh sach dai luong ĐƯỢC PHÉP nhin trong buoc mo phong (khoa truoc khi chay,
theo bai hoc Amendment 23-23 muc 3.3):

```text
DUOC do : c_supt tren du lieu TONG HOP, corr trung binh tren du lieu TONG HOP,
          so cot huu han theo luoi
CAM do  : c*(gamma) tren BAT KY cell that nao, c_supt tren cell that
```

Ranh gioi nay da duoc ton trong: khong cell that nao duoc cham trong muc 7.1.

---

## 8. Pham vi duoc phep chay sau amendment nay

```text
* them docs/phase-23/06-reframe.md  (tuyen bo fallback ngoai sinh; ha 5 gate
  xuong DIAGNOSTIC; viet ro "c* la tai tham so hoa, khong phai kham pha")
* them cert/abstain_cost.py va test/test_phase23_abstain_cost.py
* sinh results/phase-23/abstain_cost_<cell>.json cho 3 cell khong suy bien
* them docs/phase-23/11-abstain-cost.md
* Figure 4 (duong c* kem dai dong thoi) va Figure Phat hien 8 (no tu 23.5[B])

KHONG sua cert/config_matrix.py, cert/conformal_simultaneous.py,
cert/aurc_go1.py, cert/go2_simultaneous.py.
```

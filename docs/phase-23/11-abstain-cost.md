# 11 -- Lesson 23.6: chi phi abstain va nguong hoa von `c*`

Ngay chay: 2026-08-20
Khoa boi: `00z-amendment-25` (K-D1..K-D7, K-1..K-8), `00za-amendment-26`
(K-D8, C23v2-1, K-9..K-11), `00zb-amendment-27` (K-12..K-15, PC23v2-2),
`00zc-amendment-28` (K-D9..K-D12, F-23.6-6/7/8)
Khung: doc `06-reframe.md` TRUOC tai lieu nay.
Code: `cert/abstain_cost.py`, `cert/plot_abstain_cost.py`
Test: `test/test_phase23_abstain_cost.py` (46 test)
Artifact: `results/phase-23/abstain_cost_{poisson_0.925,poisson_0.850,h2_0.700}.json`
Hinh: `fig4_cstar_by_coverage.png`, `fig4b_risk_vs_coverage_by_c.png`

---

## 0. Ket luan mot dong

`c*(0.78)` = 0.4533 / 0.4566 / 0.3643 tren ba cell. F2 STATIC nam DUOI nguong o
cell chinh (co lai) va TREN nguong o hai cell con lai (lo). Ba dong du doan
NGOAI MAU cua lesson (`K-7`, `K-8`, `K-15`) deu HIT 3/3.

---

## 1. Cong: doi chung phai dat TRUOC khi doc bat ky con so nao

| Doi chung | Y nghia | Ket qua |
|---|---|---|
| NC23v2-4 | `c*(0) = R_neo` chinh xac | PASS 3/3, resid = 0 |
| NC23v2-5 | `gamma = 1` => `R_system` bat bien theo `c` | PASS |
| NC23v2-6 | `c = 0` => `R_system = gamma * R\|accept` | PASS |
| NC23v2-7 | `gamma = 0` => `c_F1 = c_F2` chinh xac (sticky khong co gi de dinh) | PASS 3/3 |
| PC23v2-1 | `c = 1` => `R_system > R_neo` voi moi `gamma < 1` | PASS, KICH HOAT tren moi diem |
| PC23v2-2 | bom sut giam 2.5 sigma -> CI loai tru 0; 1.5 sigma -> khong | PASS 7/7 hai phia |
| G23-32 | dong nhat thuc phan hoach | 2.8e-17 / 5.6e-17 / 2.8e-17 <= 1e-12 |
| inverse crosscheck | duong DAO vs duong TRUC TIEP, `gamma <= 0.90` | 2.8e-16 / 2.2e-16 / 2.2e-16 |
| C23v2-1 | diem cat khop `beneficial_band` cua L23.3 | PASS, 4/4 dau mut trong luoi |
| bit-parity | coverage / n_acc / err_acc / err_rej vs L23.3 | 0.0e+00 tren 100 diem x 3 cell |

```text
Doi chung DUONG phai KICH HOAT thi ket luan "khong thay vi pham" moi co nghia.
Bai hoc G23-27: mot doi chung duong khong kich hoat khong chung minh duoc gi.
Ca PC23v2-1 lan PC23v2-2 deu kich hoat.
```

`bit-parity` chung minh gi va KHONG chung minh gi:

```text
CHUNG MINH   : D4 dung do cau tao. Hai module tinh tu hai duong code khac nhau
               (23.3 lay `mean` tren hang; 23.6 lay ti so cua tong theo block)
               va gap nhau o muc BIT.
KHONG CHUNG  : rang con so do dung ve VAT LY. Ca hai duong cung dua tren
               `a_star` tu bang tra (gioi han L1). Trung khop la TINH NHAT QUAN
               NOI BO, khong phai TINH DUNG DAN NGOAI TAI. Do la ly do Lesson
               23.10 (ground truth muc goi) ton tai.

`regret` lech 8.9e-16 chu KHONG phai 0 -- do la thu tu cong dau phay dong.
Khong duoc "lam tron len" thanh 0.
```

---

## 2. Bang chinh -- G23-36 "khi nao bat certification"

```text
Tai diem van hanh gamma = 0.78 (coverage DO DUOC 0.7799994799656778):

cell             c*_err    c*_regret   c_F2_err   c_F1 = c_F3   ket luan
─────────────────────────────────────────────────────────────────────────────
poisson@0.925    0.4533    4.130 ms     0.3949      0.4559       F2 CO LAI
poisson@0.850    0.4566    1.158 ms     0.4707      0.4755       ca hai LO
h2@0.700         0.3643    1.590 ms     0.3818      0.3842       ca hai LO
```

Ba dieu phai di KEM bang nay, neu khong no bi doc sai. Ba cau nay duoc nhung
vao chinh artifact (`certification_table_G23_36.reading_notes`) chu khong chi
nam trong tai lieu, de chung di theo du lieu khi ai do trich bang ra cho khac.

```text
(1) c* la NGUONG, khong phai KHUYEN NGHI. No khong noi "hay bat"; no noi "bat
    khi va chi khi controller du phong CUA BAN tot hon con so nay". Nguoi van
    hanh mang so cua HO den, khong mang F2 cua chung ta.

(2) F2 thua o 2/3 cell KHONG phai that bai cua certificate. Do la phat bieu ve
    P1, khong ve C3: `P(a* = P1) = 0.656` do thiet ke topology, nen P1 la mot
    baseline manh bat thuong. Lesson 23.11 bien `swing` thanh mot truc de do
    chinh dieu nay.

(3) Hai thang cho ket luan cung DAU nhung khac BIEN DO. Tren cell chinh, F2
    thap hon c* la 12.9% tren thang `err` nhung 20.5% tren thang `regret`.
    Chung khong phai bien doi don dieu cua nhau, va nguoi van hanh quan tam do
    tre -- do la ly do K-D2 bat bao cao song song.
```

---

## 3. Ba dong du doan NGOAI MAU -- ket qua cua lesson

| ID | Dai luong | Dai da ky | Do duoc (3 cell) | KQ |
|---|---|---|---|---|
| K-7 | `c_supt` tren 50 diem `gamma` | 2.2 - 3.0 | 2.7389 / 2.7010 / 2.6714 | **HIT 3/3** |
| K-8 | `c_supt / c_bonferroni(50)` | 0.67 - 0.92 | 0.8324 / 0.8208 / 0.8119 | **HIT 3/3** |
| K-15 | `c_supt(100) / c_supt(50)` | 0.98 - 1.04 | 1.0273 / 1.0194 / 1.0303 | **HIT 3/3** |

```text
Mo phong TONG HOP chay TRUOC khi ky (Amd 23-25 muc 7.1) cho c_supt = 2.6749 va
ratio = 0.8129. Du lieu that cho 2.6714-2.7389 va 0.8119-0.8324 -- lech <= 2.4%.

Mot mo phong chi khop CAU TRUC (tap reject long nhau theo gamma) chu khong khop
du lieu that, va no du bao dung trong 2.4% tren ba che do. Day la XAC NHAN THUC
NGHIEM cho NT-v2-8, va phai duoc doc CANH C-1:

    C-1 (23.5[C])  dai dan tu mot TRUC GIAC VO HUONG ve tuong quan  -> MISS
    K-7 (23.6)     dai dan tu mot MO PHONG da chay truoc khi ky     -> HIT 3/3

Cap C-1 MISS / K-7 HIT la mot cau chuyen hoan chinh ve ky luat do, va no thuoc
chuong phuong phap chu khong phai chuong ket qua.
```

### 3.1. Nhieu Monte-Carlo -- K-7/K-8 VUNG theo seed

```text
c_supt tren 10 seed lien tiep (23610..23619), B = 2000, luoi da khoa:

cell             mean      sd       range               sd/mean
poisson@0.925   2.6996   0.0261   [2.6622, 2.7389]      0.97%
poisson@0.850   2.6918   0.0238   [2.6653, 2.7329]      0.88%
h2@0.700        2.6573   0.0244   [2.6113, 2.6814]      0.92%

Gia tri bao cao (seed khoa 23610) la 2.7389 -- tinh co la MAX cua 10 seed tren
cell chinh. Uoc luong ON DINH la 2.6996 +/- 0.0261. Phai noi ra.
K-7 va K-8 HIT tren CA 30 phep do (10 seed x 3 cell). Ket luan VUNG theo seed.
```

### 3.2. K-15 la phep kiem MOT PHIA -- can duoi vo dung

```text
50 diem luoi khoa la TAP CON dung cua 100 diem luoi min, va `sd_k` dung chung
ma tran draw W. Do do T_fine^(b) = max tren tap LON HON >= T_locked^(b) voi MOI
draw, nen ti so >= 1.0 TAT DINH. Can duoi 0.98 khong bao gio co the vi pham.

Toan bo noi dung kiem dinh nam o CAN TREN 1.04, va no LOAI TRU kich ban
"K_eff gap doi" (1.081) o ~4.3 sd. Phai viet dung nhu vay.
```

---

## 4. K-6 / K-9 / K-10 -- don dieu, va gioi han cua phep do

```text
K-6  (luoi da khoa 0.02) : 0 vi pham, 3/3 cell.               PASS
K-9  (luoi min 0.01)     : 4 / 3 / 0 vi pham; trong gamma <= 0.98 la 3 / 2 / 0
                           [MO TA], khong tinh diem (da nhin so o Amd 23-26)
K-11 (vi tri vi pham)    : moi vi pham o gamma >= 0.87        [MO TA]
K-10 (CI ghep cap)       : 7/7 CI chua 0.   TRANG THAI: UNDETECTED, KHONG PASS
```

### 4.1. Vi sao `UNDETECTED` chu khong `PASS`

```text
cell            gamma        drop        MDE        |drop| / MDE   PC23v2-2
────────────────────────────────────────────────────────────────────────────
poisson@0.925   0.88->0.89  -0.000032   0.006323      0.005        dat
                0.93->0.94  -0.004843   0.011581      0.418        dat
                0.97->0.98  -0.008983   0.032507      0.276        dat
                0.98->0.99  -0.041453   0.060360      0.687        dat
poisson@0.850   0.87->0.88  -0.001640   0.005193      0.316        dat
                0.97->0.98  -0.004081   0.031961      0.128        dat
                0.98->0.99  -0.004557   0.062888      0.072        dat
```

`MDE` = nua-be-rong CI95 = sut giam nho nhat ma phep do phan biet duoc khoi 0.

```text
Cot |drop|/MDE < 1 o MOI dong. Nghia la: NEU sut giam la THAT va bang DUNG do
lon quan sat duoc, phep do VAN se khong phat hien ra no.

"Khong bac bo duoc 0" KHONG phai bang chung cho "hieu ung bang 0". No chi tro
thanh bang chung khi phep do da duoc CHUNG MINH la khong mu -- va do la viec
cua PC23v2-2, khong phai cua CI.

Day la G23-27 tai sinh. O 23.5[A] chung toi da tu choi ghi PASS va thiet ke
PC-S-1d de chung minh phep do khong mu. K-10 duoc xu ly GIONG HET.
```

### 4.2. Cau duoc phep viet

```text
DUOC:  "Bay vi pham don dieu tren luoi min deu co CI ghep cap chua 0. Chung toi
        chung minh phep do khong mu bang cach bom mot sut giam nhan tao 2.5
        sigma: CI loai tru 0 o ca bay, con o 1.5 sigma thi khong. MDE nam trong
        khoang 0.0052 den 0.0629; vi pham lon nhat bang 0.69 MDE. Ket luan: cac
        vi pham KHONG PHAN BIET DUOC voi nhieu lay mau o do phan giai hien co."
KHONG: "Chung toi chung minh cac vi pham la nhieu."
KHONG: "K-10 PASS."
```

Su khac biet giua hai cach viet la su khac biet giua *"toi khong thay"* va
*"no khong co o do"* -- va do la ranh gioi ma ca chuong phuong phap duoc xay tren.

---

## 5. F-23.6-6/7/8/9 -- F1, F3, va so chieu hieu dung

```text
F-23.6-6  [TAT DINH] F1 == F3 TUNG HANG (0 / 499,967 hang khac) khi
          secondary = "sticky" -- mac dinh da dang ky o P17. `fallback_wait`
          tra ve chinh `fallback_sticky`.
          => G23-35 dinh vi HAI diem tren truc c, khong phai ba.
          => F3 khac F1 o DO TRE QUYET DINH (204.3 ms tren tap reject), khong o
             RUI RO tren tap reject. Hai truc khac nhau, mot diem tren truc c.
          => du doan F4 cua Lesson 23.1 la BAT KHA THI CAU TRUC. Xem muc 7.

F-23.6-7  [TAT DINH] Ton that sticky theo block LA thong ke du: `ffill` khong
          dien qua bien block va `fillna(p_static)` xu ly hang dau moi block,
          nen trang thai reset tuyet doi o bien block (dung nhu P17 yeu cau).
          Bootstrap block chay y het F2. Chi phi that: 1.14 s cho ca luoi.
          => bac bo tien de "stateful => khong rut gon duoc".

F-23.6-8  [MO TA] Thu tu c_F2 < c_F1 = c_F3 dung 3/3 cell. STATIC tot hon
          STICKY tren tap reject, nhat quan tren ca ba che do.

F-23.6-9  [MO TA] So chieu hieu dung:
              c_star_err   c_supt 2.7389   K_eff  8.11
              c_f2_err     c_supt 2.6902   K_eff  7.00
              c_f1_err     c_supt 3.0064   K_eff 18.92
```

### 5.1. `K_eff` -- va mot su thong nhat giua thuat toan va thong ke

```text
K_eff = alpha / (2 (1 - Phi(c_supt))),  dao nguoc hang so Bonferroni.
Kiem nguoc bat buoc: c_bonferroni(K) -> K_eff = K chinh xac o K = 8/24/50/100.

Duong c_F1 co GAP DOI so chieu hieu dung so voi c*. CUNG mot nguyen nhan voi
viec `sticky_curve_stats` khong dung duoc tong tien to:

   NGUYEN NHAN CHUNG: hanh dong sticky KHONG long nhau theo gamma.
      he qua THUAT TOAN : tong tien to khong ap dung -> O(n*K) thay vi O(n)
      he qua THONG KE   : hai diem gamma ke nhau chia se it thong tin hon
                          -> tuong quan thap hon -> max giai rong hon
                          -> c_supt cao hon -> K_eff gap doi

Mot tinh chat CAU TRUC cua bo uoc luong hien ra o CA HAI mat. Neu chi thay mot
mat, ta se goi mat kia la "ngau nhien".
```

```text
CANH BAO BAT BUOC: K_eff duoc suy bang cach DAO NGUOC mot cong thuc CHUAN TAC
(Gaussian) tren mot phan phoi bootstrap KHONG chuan tac. No la MOT CACH PHAT
BIEU LAI c_supt cho de doc, KHONG phai mot dai luong co y nghia xac suat rieng.
Nhan [MO TA], khong tinh diem. Quen dieu nay la tai sinh dung loi cua C-1
(Amd 23-25 muc 3): dan mot hang so toi han tu mot tom tat vo huong.
```

### 5.2. So sanh voi Lesson 23.5[C]

```text
                        K danh nghia  c_bonf   c_supt do duoc   K_eff      K_eff/K
──────────────────────────────────────────────────────────────────────────────────
23.5[C] slot rank            24       3.0781   2.857 - 2.962   11.7 - 16.4  0.49-0.68
23.6    luoi coverage        50       3.2905   2.671 - 2.739    6.6 -  8.1  0.13-0.16

NHIEU diem hon nhung IT chieu hieu dung hon. Khong mau thuan: so DIEM la lua
chon cua nguoi do; so CHIEU la tinh chat cua he.

Co che duoc tien doan TRUOC, khong giai thich SAU:
   luoi gamma : tap reject tai gamma va gamma+0.02 chia se gan het hang
                -> corr +0.75 (mo phong, Amd 23-25 muc 7.1)
   slot rank  : s_sim = max_j s_j rang buoc ba slot
                -> corr -0.204 (do duoc, Lesson 23.5[C])
Tuong quan DUONG lam max co lai; tuong quan AM lam max gian ra.
```

---

## 6. Hinh

```text
Figure 4  (headline)  fig4_cstar_by_coverage.png
   c*(gamma) kem dai DONG THOI va dai TUNG DIEM, mot panel moi cell, kem c_F2
   va c_F1 = c_F3, vung F2 co lai to bong.

Figure 4b (phu luc)   fig4b_risk_vs_coverage_by_c.png
   R_system(gamma, c) cho vai gia tri c. KHONG phai dong gop -- chi de nguoi
   doc quen voi duong risk-coverage nhan ra hinh dang quen thuoc.
```

### 6.1. Vi sao Figure 4 ve `c*` chu khong ve `R_system`

```text
Ban ke hoach v1 phac R_system(gamma) voi mot duong cho moi `c`. Sau khi tai
khung, hinh do khong con la headline: no ve mot dai luong PHU THUOC `c`, tuc
phu thuoc mot lua chon ke toan -- dung dieu ma tai khung vua bo di.
Headline phai la dai luong KHONG phu thuoc fallback.
```

### 6.2. Bay rang buoc cua Figure 4, moi cai co ly do

```text
1  Ve CA dai tung diem VA dai dong thoi, hai sac do.
   Ly do: nguoi doc phai THAY duoc gia cua tinh dong thoi. Chi ve mot la giau
   mot nua thong tin.
2  Khong ve gamma > 0.98. K-D4 cam ngoai suy; ve la mo loi ngoai suy.
3  Danh dau gamma = 0 la R_neo. Do la NC23v2-4, va no neo ca duong.
4  Danh dau diem cat c_F2 = c* canh `band_low` cua Lesson 23.3.
   Ly do: C23v2-1 la doi chung cheo; phai NHIN THAY duoc.
5  F1 va F3 la MOT duong, MOT nhan. Ve hai duong chong nhau la noi doi bang
   hinh anh.
6  Phan biet duong bang CA mau LAN kieu net. In den trang phai doc duoc.
7  Truc y DUNG CHUNG ba panel. Neu moi panel tu chon thang do, hai cell co
   R_neo khac nhau se trong giong nhau va nguoi doc mat kha nang so sanh DO
   LON cua c* -- chinh la thu bang G23-36 dung de so.
```

### 6.3. Ba kiem tra sau khi ve -- nhin hinh cung la mot phep do

```text
[1] c*(gamma) TANG tu trai sang phai va bat dau DUNG tai R_neo.       DAT
[2] Diem cat gamma_dagger trung tam giac `band_low (L23.3)`:          DAT
        0.6073 vs 0.6076   |   0.8081 vs 0.8091   |   0.8434 vs 0.8428
[3] Ba panel KHAC nhau (neu giong nhau: dang ve cung mot cell ba lan). DAT
```

Kiem tra [2] va [3] duoc chuyen thanh khang dinh bang may
(`test_R12`, `test_R13`) de khong ai phai nheo mat vao file PNG.

---

## 7. Mot MISS cua Lesson 23.1 duoc GIAI THICH boi Lesson 23.6

```text
F4 du doan thu tu NGHIEM NGAT F2 > F1 > F3, cham tai kappa = 0.5.
Do duoc tren artifact CUA CHINH Lesson 23.1:
        0.238685753  >  0.236889635  =  0.236889635
Bat dang thuc thu nhat DUNG. Bat dang thuc thu hai la DANG THUC.

Theo F-23.6-6, dieu nay KHONG THE khac di voi bat ky du lieu nao. F4 la mot du
doan BAT KHA THI, khong phai mot du doan SAI.

Cham diem KHONG doi: F4 van la MISS, cham bang artifact 23.1 tai dieu kien da
khoa. F-23.6-6 dong vai tro GIAI THICH, khong dong vai tro BANG CHUNG.
```

```text
NT-v2-19  Mot phat hien o lesson SAU khong duoc dung de CHAM LAI mot dong o
          lesson TRUOC. No chi duoc dung de HIEU ket qua cham.
```

Tuong tu, `F3` va `F6` MISS vi `kappa = 0.5` nam NGOAI beneficial band
`[0.6076, 0.99995]` do Lesson 23.3 do duoc -- tuc vi DIEM VAN HANH duoc chon
truoc khi biet band nam o dau, khong vi CO CHE sai. Chi tiet o Amendment 23-29
muc 6.1.

---

## 8. Gioi han

```text
L26  Dai tin cay cua c*(gamma) la dai CO DIEU KIEN theo nguong tau(gamma) uoc
     luong tren tap test day du (D2). No KHONG bao gom bat dinh cua viec uoc
     luong tau. Coverage dao dong giua cac draw: sd = 5.9e-3 / 6.0e-3 / 7.7e-3
     tai gamma = 0.78. Phuong an co dinh coverage loai bo gioi han nay nhung
     doi hoi mot phep sort moi draw moi gamma -- khong kha thi.

L27  c* la dai luong PHAN THUC (counterfactual): no do twin sai bao nhieu tren
     nhung hang ma he KHONG dung twin. Do duoc o day vi day la moi truong co
     ground truth. Trong he that, c* phai duoc UOC LUONG, khong do truc tiep.
     Ke thua L1 (ground truth la bang tra) -- dong o Lesson 23.10.

L28  G23-34 NOT_RUN: khong co dinh nghia duoc khoa o bat ky dau trong repo, va
     PLAN_v2.md van chua vao repo. Xem NT-v2-15.

L29  c_F1 duoc tinh tren ca luoi nhung `wait_s` cua F3 chi duoc danh gia o DIEM
     VAN HANH (`f3_wait_evaluated_at = 0.78`). Do tre quyet dinh cua F3 o cac
     gamma khac KHONG duoc do.
```

---

## 9. Tai tao

```text
python -m cert.abstain_cost                       # 19.7 s, B=2000, seed 23610
python -m cert.plot_abstain_cost                  # hai hinh
pytest test/test_phase23_abstain_cost.py -q       # 46 passed
```

Artifact mang `provenance.git_dirty_tracked = false` va `git_hash` cua commit
sinh ra chung. Khoa `git_dirty_including_untracked` duoc ghi rieng: mot phep
`git status --porcelain` tran luon bao dirty khi ghi mot file chua duoc theo
doi, nen cau hoi co nghia la "MA NGUON co sach khong".

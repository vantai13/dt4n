# AMENDMENT 23-27 -- Ha K-10 xuong UNDETECTED, khoa PC23v2-2 va K-12..K-15

Ngay: 2026-08-19
Commit: sau `f41f564` (`cert/abstain_cost.py`), TRUOC khi tinh `c_supt` tren
luoi 0.01 va truoc khi viet doi chung duong cho `K-10`.

Amendment nay:

```text
(1) HA KET LUAN cua K-10 tu "HIT" xuong UNDETECTED -- thieu doi chung duong
(2) khoa PC23v2-2 (doi chung duong cho K-10) va bat buoc bao cao MDE
(3) khoa K-12 [TAT DINH], K-13 [MO TA], K-14 [GATE thu tuc], K-15 [CO CHE]
(4) ghi F-23.6-3 (K_eff) va F-23.6-4 (nhieu MC cua c_supt), ca hai [MO TA]
(5) GHI NHAN K-7 va K-8 HIT 3/3 -- hai dong du doan THAT duy nhat cua 23.6
```

Ba con so trong ban de xuat goc bi SUA o day: khoang `K_eff` cua 23.6, nhan
cua `K-12`, va dai khoa cua `K-15`. Ly do o muc 4, 5.2 va 6.2.

---

## 1. Phan loai ket qua Lesson 23.6 -- ba lop, khong duoc tron

```text
LOP 1 -- TAT DINH (kiem dung code, KHONG phai ket qua)
   c*(0.78), c_F2(0.78), n_accept, G23-32 resid, bit-for-bit voi 23.3,
   K-1..K-6, K-9, K-11
LOP 2 -- XAC NHAN CO CHE (co gia tri, khong phai "phat hien")
   inverse crosscheck, NC/PC tu than 4/4, C23v2-1 khop 4/4 dau mut
LOP 3 -- DU DOAN THAT, NGOAI MAU  <- CHI CO HAI DONG
   K-7  c_supt        dai [2.2, 3.0]    HIT 3/3
   K-8  c_supt/c_bonf dai [0.67, 0.92]  HIT 3/3
```

```text
NT-v2-13  Khi bao cao ti le prediction-hit, CHI duoc dem cac dong LOP 3.
          Gop lop 1 vao lam phong dai thanh tich pre-registration -- day la
          he qua truc tiep cua NT-v2-9, va phai duoc ap khi VIET, khong chi
          khi KY.
```

Cau duoc phep viet:

```text
DUOC:  "Lesson 23.6 co HAI dong du doan ngoai mau (c_supt va ti so cua no voi
        Bonferroni). Ca hai nam trong dai da ky, tren ca ba che do. Sau dong
        con lai la kiem tra tinh nhat quan cua duong ong, mang nhan [TAT DINH],
        va khong tinh diem du doan."
KHONG: "Chung toi du doan truoc tam dai luong va trung ca tam."
```

---

## 2. K-7 / K-8 -- ghi nhan HIT, va ghi nhan nhieu Monte-Carlo

### 2.1. Do duoc

```text
                    mo phong    poisson@0.925   poisson@0.850   h2@0.700
                    (Amd 23-25 muc 7.1)
c_supt                2.6749       2.7389          2.7010         2.6714
c_supt / c_bonf(50)   0.8129       0.8324          0.8208         0.8119
sai lech tuong doi      --         +2.4%           +1.0%          -0.1%
```

`c_bonferroni(50) = 3.290527` (`go2_simultaneous.critical_values`).

### 2.2. F-23.6-4 -- nhieu MC cua `c_supt`, va tinh vung theo seed

Trang thai: **[MO TA]**, khong tinh diem.

Con so o muc 2.1 lay tai seed da khoa `SEED_BOOT = 23610`. Seed do la mot bac
tu do, va no duoc chon TRONG CUNG PHIEN chay chu khong tu mot amendment truoc.
Vi vay phai cong khai do nhay theo seed, neu khong con so bi doc chac hon thuc te.

Do tren 10 seed lien tiep (`23610..23619`), `B = 2000`, luoi da khoa:

```text
cell             mean      sd       range               sd/mean
────────────────────────────────────────────────────────────────
poisson@0.925   2.6996   0.0261   [2.6622, 2.7389]      0.97%
poisson@0.850   2.6918   0.0238   [2.6653, 2.7329]      0.88%
h2@0.700        2.6573   0.0244   [2.6113, 2.6814]      0.92%
```

Doc dung:

```text
(1) Gia tri tai seed khoa (2.7389) la MAX cua 10 seed tren cell chinh. Do la
    trung hop, khong phai lua chon -- seed duoc khoa truoc khi chay. Nhung
    phai NOI RA, neu khong nguoi doc tuong 2.7389 la mot uoc luong on dinh.
    Uoc luong on dinh la 2.6996 +/- 0.0261.
(2) K-7 va K-8 HIT tren CA 30 phep do (10 seed x 3 cell): moi c_supt nam trong
    [2.61, 2.74] (dai khoa [2.2, 3.0]) va moi ti so nam trong [0.794, 0.832]
    (dai khoa [0.67, 0.92]). Ket luan VUNG theo seed, khong phu thuoc mot lan rut.
(3) sd/mean ~ 0.9% la DO PHAN GIAI cua phep do c_supt tai B = 2000. Moi dai
    du doan ve c_supt hep hon ~2% se bi nhieu MC chi phoi. Con so nay duoc
    dung de hieu chinh K-15 o muc 6.
```

---

## 3. K-10 -- HA XUONG UNDETECTED

### 3.1. Vi sao "7/7 CI chua 0" chua du

Ket qua do duoc (`B = 2000`, bootstrap ghep cap theo block, luoi 0.01):

```text
cell            gamma        drop        nua-be-rong CI   |drop| / nua-be-rong
──────────────────────────────────────────────────────────────────────────────
poisson@0.925   0.88->0.89  -0.000032       0.006323            0.005
                0.93->0.94  -0.004843       0.011581            0.42
                0.97->0.98  -0.008983       0.032507            0.28
                0.98->0.99  -0.041453       0.060361            0.69   <- gan nhat
poisson@0.850   0.87->0.88  -0.001640       0.005193            0.32
                0.97->0.98  -0.004081       0.031961            0.13
                0.98->0.99  -0.004557       0.062888            0.072
```

Cot cuoi la van de. Tai `0.98->0.99`, phep do chi phan biet duoc khoi 0 mot sut
giam LON HON `0.0604`. Sut giam quan sat duoc la `0.0415`. Tuc la:

```text
NEU day la mot sut giam THAT bang dung do lon quan sat duoc,
phep do VAN se khong phat hien ra no.
```

```text
NT-v2-14  Mot khoang tin cay CHUA 0 khong phai bang chung cho "hieu ung bang 0".
          No chi tro thanh bang chung khi phep do da duoc CHUNG MINH la khong mu,
          bang mot doi chung DUONG co kich hoat, va khi MDE (nua-be-rong CI)
          duoc bao cao ben canh.
          Ket luan dung khi thieu doi chung duong la UNDETECTED, khong phai PASS.
```

### 3.2. Day la `G23-27` tai sinh

```text
23.5[A]  G23-27   drop 8.9e-4 duoi nguong 0.02
                  -> KHONG ghi PASS, ghi UNDETECTED
                  -> thiet ke PC-S-1d chung minh phep do khong mu
                     (p=300 -> 0.027; p=3000 -> 0.215), va do la G23-27b PASS
23.6     K-10     7/7 CI chua 0, nhung MDE >= |drop| o moi vi pham
                  -> phai ghi UNDETECTED, va phai co PC23v2-2
```

Ghi `K-10 HIT` la lam dung dieu da tu choi lam o `G23-27`. Lan thu ba cung mot
loai loi trong Phase 23 neu khong bat.

### 3.3. Ghi o dau -- sua so voi ban de xuat

Ban de xuat noi "ha `K-10` xuong UNDETECTED trong `GATES.md`". **Khong lam vay.**
`GATES.md` khoa pham vi la "chi chua ID dang `G23-*`" (muc "Ghi chu ve pham vi
ID"), va `K-10` la mot dong DU DOAN chu khong phai mot gate. Nhet no vao se pha
chinh nguyen tac "mot so, mot loai ID" da khoa o Amendment 23-26 muc 7.

```text
K-10 duoc ghi UNDETECTED trong BANG PRE-REGISTRATION (00-preregistration.md),
noi cac dong du doan song. GATES.md khong doi.
```

---

## 4. F-23.6-3 -- so kiem dinh hieu dung `K_eff`

Trang thai: **[MO TA]**, DA NHIN CA HAI SO, khong tinh diem.

Dao nguoc hang so Bonferroni de hoi "bao nhieu kiem dinh DOC LAP cho ra hang so
toi han nay":

```text
c = z(1 - alpha / (2 K_eff))   =>   K_eff = alpha / (2 (1 - Phi(c)))

Kiem nguoc (bat buoc, de chac cong thuc dung):
   c_bonferroni(24) = 3.078088  ->  K_eff = 24.0000
   c_bonferroni(50) = 3.290527  ->  K_eff = 50.0000
```

```text
                        K danh nghia  c_bonf   c_supt do duoc   K_eff      K_eff/K
──────────────────────────────────────────────────────────────────────────────────
23.5[C] slot rank            24       3.0781   2.857 - 2.962   11.7 - 16.4  0.49-0.68
23.6    luoi coverage        50       3.2905   2.671 - 2.739    6.6 -  8.1  0.13-0.16
```

**Sua so voi ban de xuat:** ban de xuat ghi `K_eff = 8 - 9` va `K_eff/K =
0.16-0.18` cho 23.6. Tinh lai cho `6.6 - 8.1` va `0.13 - 0.16`. Ban de xuat cho
23.5[C] (`12-16`, `0.50-0.68`) chi lech lam tron.

Doc:

```text
(1) Duong coverage 50 diem hanh xu nhu ~7 kiem dinh doc lap. 24 slot rank hanh
    xu nhu ~12-16. NHIEU diem hon nhung IT chieu hieu dung hon. Khong mau
    thuan: so DIEM la lua chon cua nguoi do; so CHIEU la tinh chat cua he.
(2) Co che da duoc tien doan TRUOC, khong phai giai thich SAU:
       luoi gamma : tap reject tai gamma va gamma+0.02 chia se gan het hang
                    -> corr +0.75 (mo phong, Amd 23-25 muc 7.1)
       slot rank  : s_sim = max_j s_j rang buoc ba slot
                    -> corr -0.204 (do duoc, Lesson 23.5[C])
    Tuong quan DUONG lam max co lai; tuong quan AM lam max gian ra.
```

```text
CANH BAO BAT BUOC -- phai chep vao 11-abstain-cost.md:
K_eff duoc suy bang cach DAO NGUOC mot cong thuc CHUAN TAC (Gaussian), trong
khi phan phoi bootstrap KHONG chuan tac. Vi vay K_eff la MOT CACH PHAT BIEU
LAI c_supt cho de hieu, KHONG phai mot dai luong co y nghia xac suat rieng.
Quen dieu nay la tai sinh dung loi cua C-1 (Amd 23-25 muc 3): dan mot hang so
toi han tu mot tom tat vo huong.
```

---

## 5. PC23v2-2 va K-12 -- doi chung duong cho K-10

### 5.1. Thiet ke doi chung

```text
PC23v2-2  (doi chung DUONG, BAT BUOC cho moi ket luan cua K-10)
          Voi MOI vi pham don dieu, bom mot sut giam nhan tao theo don vi
          sigma_hat CUA CHINH phan phoi bootstrap so gia, va kiem CA HAI phia:
              s = 2.5  ->  CI95 phai LOAI TRU 0
              s = 1.5  ->  CI95 phai KHONG loai tru 0
          Bom theo don vi sigma_hat, KHONG theo mot hang so tuyet doi: mot
          hang so se day o nay ra xa 0 va o kia van gan 0, va khi do doi chung
          tu tao ra that bai cua chinh no. Khuon nay sao chep PC-C-1
          (10-go2-simultaneous.md muc 1.2).

          BAT BUOC bao cao kem: MDE = nua-be-rong CI, va ti so |drop| / MDE.
```

### 5.2. K-12 -- HA NHAN xuong [TAT DINH], KHONG tinh diem

Ban de xuat dat `K-12` la `[CO CHE]` va **TINH DIEM**. Ap `NT-v2-9` (thu tuc
tu hoi "toi co tinh duoc so nay ngay bay gio khong?") cho thay nhan do SAI:

```text
Voi phan phoi bootstrap duoc dat lai tam, CI95 cua (d - mean(d) - s*sd) la
    [q_025 - s*sd,  q_975 - s*sd]
nen no LOAI TRU 0 khi va chi khi  q_975 / sd  <  s.

Ti so q_975/sd DA DUOC BAO CAO o muc 3.1 (nua-be-rong chia sd_boot):
    0.006323/0.003271 = 1.933      0.005193/0.002634 = 1.972
    0.011581/0.005871 = 1.972      0.031961/0.016257 = 1.966
    0.032507/0.016215 = 2.005      0.062888/0.031452 = 1.999
    0.060361/0.031569 = 1.912
Tat ca nam trong (1.5, 2.5). Ket qua cua PC23v2-2 do do DA DUOC XAC DINH bang
so hoc tu cac so da bao cao: s=2.5 loai tru 0 (7/7), s=1.5 khong (7/7).
```

```text
K-12  PC23v2-2 kich hoat dung hai phia tren MOI vi pham:
          s = 2.5 -> loai tru 0 (7/7);  s = 1.5 -> khong loai tru (7/7)
      Nhan **[TAT DINH]** (sua tu [CO CHE] de xuat). KHONG tinh diem.
      Ghi: CO, 7/7 ca hai phia.

      VAN PHAI CHAY va PHAI BAO CAO. Gia tri cua no khong nam o cho "du doan
      dung" ma o cho CHUNG MINH PHEP DO KHONG MU -- dung vai tro cua PC-S-1d
      voi G23-27. Mot doi chung duong tat dinh van la mot doi chung duong.
```

Ghi chu ve mot thiet ke MANH HON da bi loai: bom sut giam vao DU LIEU muc hang
(lat `twin_err` tren cac hang bi tu choi tai `gamma_hi`) roi chay lai ca duong
ong se KHONG tat dinh, vi no dong cham block structure va bootstrap. Nhung
uoc luong diem cua no van la `m / n_reject`, tinh duoc dong; phan khong tat
dinh chi la thay doi bac hai cua `sd`. Loi it hon chi phi, nen chon ban dat
lai tam va ghi nhan dung nhan cua no.

### 5.3. K-13, K-14

```text
K-13  MDE (nua-be-rong CI95) duoc bao cao cho MOI vi pham, cung voi ti so
      |drop| / MDE.
      Nhan [MO TA] -- DA NHIN SO, khong tinh diem.
      Ghi: max(|drop| / MDE) = 0.69 (poisson@0.925, 0.98->0.99). Ca 7 deu < 1.

K-14  Ket luan cua K-10 duoc ghi la UNDETECTED, KHONG phai HIT/PASS.
      Nhan [GATE thu tuc]. Khong phai du doan, khong tinh diem.
      Thuc thi: bang pre-registration ghi "UNDETECTED"; test doc bang do.
```

### 5.4. Cau duoc phep viet

```text
DUOC:  "Bay vi pham don dieu tren luoi min deu co CI ghep cap chua 0. Chung toi
        chung minh phep do khong mu bang cach bom mot sut giam nhan tao 2.5
        sigma: CI loai tru 0 o ca bay, con o 1.5 sigma thi khong. MDE nam trong
        khoang 0.0052 den 0.0629; vi pham lon nhat bang 0.69 MDE. Ket luan: cac
        vi pham KHONG PHAN BIET DUOC voi nhieu lay mau o do phan giai hien co."
KHONG: "Chung toi chung minh cac vi pham la nhieu."
KHONG: "K-10 PASS."
```

---

## 6. K-15 -- `c_supt` tren luoi min, VA MOT DAI DA DUOC HIEU CHINH

### 6.1. Dai de xuat ban dau KHONG PHAN BIET DUOC hai kich ban

Ban de xuat: `1.00 <= c_supt(100)/c_supt(50) <= 1.08`, bac bo neu `> 1.15`.

Tinh hai kich ban canh tranh TRUOC khi nhin so (chua ai goi `supt_band` tren
luoi 0.01 -- `cert/abstain_cost.py` chi goi no tren `bt_l`):

```text
[i]  gap doi so DIEM khong them CHIEU  (co che duoc ung ho)
     K_eff giu nguyen  ->  ti so = 1.0000

[ii] gap doi so DIEM gap doi CHIEU     (co che BI BAC BO)
     K_eff 6.6 -> 13.2 : 2.8953/2.6704 = 1.0842
     K_eff 7.2 -> 14.4 : 2.9225/2.6995 = 1.0826
     K_eff 8.1 -> 16.2 : 2.9590/2.7385 = 1.0805

[iii] moc doc lap hoan toan: c_bonf(100)/c_bonf(50) = 3.4808/3.2905 = 1.0578
```

```text
Dai [1.00, 1.08] CHUA CA [i] LAN [ii]. No trung du ket qua nao xay ra, nen no
khong kiem dinh dieu gi. Va nguong bac bo 1.15 nam TREN kich ban [ii] (1.083),
nen no se khong bao gio kich hoat ke ca khi so chieu that su gap doi.
Mot dai chua ca gia thuyet lan phu dinh cua no la mot dai vo dung.
```

### 6.2. Dai duoc hieu chinh -- dan tu DO PHAN GIAI DA DO

`F-23.6-4` cho `sd(c_supt) = 0.024 - 0.026` tai `B = 2000`, tuc ~0.9% tuong doi.
Hai lan chay dung CHUNG mot ma tran `W` (mot seed) nen ti so duoc ghep cap va
nhieu triet tieu mot phan; can tren khong ghep cap la `sqrt(2) * 0.9% = 1.3%`.

```text
[i]  1.000  +/- 0.013
[ii] 1.081  +/- 0.013            cach nhau ~6 sd -- phan biet duoc thoai mai
diem giua hai kich ban: (1.000 + 1.081)/2 = 1.0405
```

```text
K-15  Ti so c_supt(luoi 0.01, 100 diem) / c_supt(luoi 0.02, 50 diem),
      CUNG seed, CUNG B = 2000, tren ca ba cell.
      Nhan [CO CHE], dan tu K_eff ~ 7: gap doi so DIEM khong gap doi so CHIEU.
      Du doan: 0.98 <= ti so <= 1.04 tren ca ba cell.       TINH DIEM.

      Can duoi 0.98 va can tren 1.04 la +/- 3 sd quanh kich ban [i], va
      can tren 1.04 dong thoi la DIEM GIUA giua [i] (1.000) va [ii] (1.081).
      Neu ti so > 1.04: cach doc "so chieu hieu dung on dinh theo do min luoi"
      BI BAC BO, va F-23.6-3 phai duoc rut lai.
```

Dai nay hep hon de xuat goc (`0.06` thay vi `0.08` be rong) nhung QUAN TRONG
hon la no LOAI TRU kich ban [ii]. Mot dai hep va sai van tot hon mot dai rong
va khong phan biet duoc -- vi cai thu nhat co the MISS, con cai thu hai thi
khong the.

### 6.3. Rui ro da khai bao

```text
Ti so nay ghep cap qua seed nhung KHONG ghep cap qua tap diem: c_supt(100) lay
max tren 100 cot con c_supt(50) tren 50 cot, va 50 cot do la TAP CON. Vi max
tren tap lon hon khong the nho hon, ti so KY VONG >= 1 gan nhu chac chan.
Do do can duoi 0.98 chu yeu bat loi hien thuc (lay nham tap cot), khong phai
bat mot kich ban khoa hoc. Noi ro de khong ai doc "0.98 <= ti so" nhu mot du
doan hai phia can bang.
```

---

## 7. RA SOAT DU DOAN (NT-v2-7 ap cho chinh amendment nay)

| Dong da khoa | Xu ly | Ly do |
|---|---|---|
| K-1..K-6, K-9, K-11 | GIU NGUYEN | da cham, khong lien quan |
| K-7, K-8 | GHI KET QUA: HIT 3/3 | dai khoa tu Amd 23-25 muc 7, khong doi |
| K-10 | **KET LUAN -> UNDETECTED** | thieu doi chung duong; dai va phat bieu KHONG doi |
| K-12 (moi) | ky voi nhan [TAT DINH] | NT-v2-9; ban de xuat dat [CO CHE] la sai nhan |
| K-13, K-14 (moi) | ky voi nhan [MO TA] / [GATE thu tuc] | da nhin so / thu tuc |
| K-15 (moi) | ky [CO CHE], dai HIEU CHINH | dai goc chua ca hai kich ban |
| C-1..C-5, A-*', S-5, S-8 | GIU NGUYEN | khong lien quan |
| G23-27 | GIU NGUYEN UNDETECTED | K-10 duoc xu ly GIONG no, khong nguoc lai |
| GATES.md | KHONG DOI | K-10 khong phai `G23-*`; xem muc 3.3 |

Ra soat `NT-v2-9` cho ba dong moi:

```text
K-12  tinh duoc dong tu q_975/sd da bao cao  -> [TAT DINH], khong diem.  DUNG.
K-13  da nhin so (0.69)                      -> [MO TA],    khong diem.  DUNG.
K-15  can goi supt_band tren 100 cot, chua ai goi, va ket qua phu thuoc cau
      truc tuong quan that cua du lieu       -> [CO CHE],   TINH DIEM.    DUNG.
```

---

## 8. Pham vi duoc phep chay sau amendment nay

```text
* them cert/abstain_cost.py: pc_k10_planted_drop(), supt_band tren luoi 0.01,
  khoa artifact `mde` / `observed_over_mde` / `c_supt_fine_over_locked`
* them test cho PC23v2-2 va K-15 vao test/test_phase23_abstain_cost.py
* sua docs/phase-23/00-preregistration.md: ghi K-7/K-8 HIT, K-10 UNDETECTED,
  them K-12..K-15

KHONG sua: GATES.md, cert/config_matrix.py, cert/conformal_simultaneous.py,
           cert/aurc_go1.py, cert/go2_simultaneous.py, cert/studentized_score.py
```

---

## 9. Chu ky

```text
Nguoi ky : vantai (Claude-assisted)
Ngay     : 2026-08-19
```

Toi xac nhan: `c_supt` tren luoi 0.01 CHUA duoc tinh o bat ky dau tai thoi diem
ky amendment nay (`cert/abstain_cost.py` chi goi `supt_band` tren `bt_l`, dong
714). Dai cua `K-15` duoc dan tu hai kich ban co che va tu do phan giai MC da
do o `F-23.6-4`, khong tu ket qua.

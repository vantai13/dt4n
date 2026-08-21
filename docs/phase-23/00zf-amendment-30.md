# AMENDMENT 23-30 -- Khoa Lesson 23.7

Ngay: 2026-08-20
Commit: sau `[3a]`, TRUOC khi `cert/conditioning_audit.py` doc hai cell giu kin.

Nam buoc da chay va da commit TRUOC amendment nay:

```text
[0]/[1]  lesson23_7_range_calibration.json    17 test
[2a]     lesson23_7_feasibility.json          25 test (1 slow)
[2b]     lesson23_7_calibration_2b.json       20 test
         lesson23_7_tables.md                 (SINH, khong chep)
[3a]     cert/cell_matrices.py                12 test (3 slow)
         approval sau refactor: 0 khac biet / 3 artifact + markdown giong het
```

`pytest -k phase23`: 240 passed, 1 skipped.

Amendment nay KHONG mo rong mot dai nao sau khi nhin so tren cell duoc cham.

---

## 1. [0] L10 -- ket luan (ii), va phat bieu dinh luong dau tien

```text
5 cho nhac L10 trong repo, 0 cho dinh luong.

Phat bieu dinh luong (nam trong breakdown_scan_cascade.json, chua ai viet ra):
    r_star     = 0.008868197    residual DU DE LAT K4
    |point|    = 0.009521786    UOC LUONG DIEM cua residual DO DUOC
    |CI90 xau| = 0.010135082    bien xau

    r_star / |CI90 xau| = 0.868750   == safety_published
    r_star / |point|    = 0.931282   <- CUNG < 1

⟹ KHONG CO KICH BAN AN TOAN trong pham vi residual da do.
  Khong phai "bien xau thi lat"; GIA TRI TRUNG TAM da lat.

L10: "Open, dinh tinh" -> "Open, DINH LUONG".
P23-D cho ket qua AM: gia dinh KHONG go duoc.
```

```text
NT-v2-21  Mot gioi han phat bieu dinh tinh KHONG dong duoc bang mot phep do.
          Viec dau tien la VIET phat bieu dinh luong -- mot quyet dinh khoa hoc,
          khong phai buoc chuan bi.
NT-v2-22  Ti so giua hai MUC khac nhau khong xac nhan lan nhau, ke ca khi cung
          dau. `1.1511` (muc BANG TRA, loss fraction) va `1.6022` (muc HANG,
          khe margin) NHAT QUAN VE DAU, KHONG khop VE SO.
```

---

## 2. [2a] Ba mat xich tai lap duoc -- M-12/M-15 KY DUOC

```text
A1  sha256 ba input 20R                   KHOP 3/3
A2  ranking goc P1,P3,P4,P2               KHOP
    P1,P3,P4,P2 -> P3,P1,P4,P2            TAI LAP dung, CHI o dau -1
    bracket giu o r_star_lo, vo o r_star  NHAT QUAN
A3  a_star tai lap TUYET DOI              1.000000000 / 999,945 hang
    a_twin tai lap TUYET DOI              1.000000000
```

`a_star` la cot THUA KE tu artifact Phase 21R, nen A3 la mot **approval test**,
khong phai tu kiem.

Bat bien kien truc duoc kiem va DUNG: trong `_cell_arrays`, `c_true` di tu `tt`
(thuc te) con `c_fresh` di tu `cv2` (mo hinh twin). Bom vao `tt` chi cham phia
chan ly; `y_hat` khong doi.

---

## 3. [2b] Hai hieu chuan -- va MOT DAI SO BI BAC BO

### 3.1. M-D11: M-6 co confound, da phan ra

```text
S1  cat P2    : ngan sach 99.30%  rang buoc  0.99%  tuong tac 0.30% cua tong
S2  cat P2,P4 : ngan sach 84.96%  rang buoc 12.78%  tuong tac 2.27% cua tong
```

Hai co che CONG DUOC. Ket qua chinh: `Delta acceptance` gan nhu THUAN la hieu
ung NGAN SACH `alpha`. O `S1` dieu nay TUYET DOI, vi `P(a_twin = P2) = 0` nen
bo rang buoc do khong doi mot quyet dinh nao.

### 3.2. M-D13: cong thuc nguong bi BAC BO

```text
DE XUAT (SAI):  r_crit = 1 + 1/P_fix, ap len ti so BIEN
                r = P(a_twin=p)/P(a*=p)

Hai loi:
  loi ich: [P(a_twin=p) - P(a*=p)] la hieu hai BIEN, khong phai giao
           {twin chon p} ∩ {a* != p}
  chi phi: P(a*=p) tinh ca hang twin KHONG chon p -- nhung hang do DA SAI SAN
           gia dinh 6,883  vs  THAT 2,227  ->  thoi 3.09 lan

DUNG:  a = |{twin chon p} ∩ {a* != p}| = 9,273   (co the sua)
       b = |{twin chon p} ∩ {a* = p}|  = 2,227   (dang dung, cam lam hong)
       co lai <=> a·P_fix > b <=> a/b > 1/P_fix
       a/b = 4.164 > 1/0.7608 = 1.3144  ->  CO LAI

Nguyen nhan goc: lap luan tren PHAN PHOI BIEN trong khi ke toan can PHAN PHOI
DONG THOI. Hai bien khong xac dinh dong thoi tru khi doc lap; o day
kappa = 0.525.
```

Cong thuc SAI duoc GIU LAI trong artifact kem ly do, va duoc khoa boi
`test_MD13_phac_thao_ban_dau_KHONG_khop`, de nguoi sau khong dan lai dung no.

---

## 4. Bac tu do da khoa

```text
M-D9   [B] bao cao THANG CAT long nhau S0/S1/S2 kem SAN LOI, khong mot diem cat.
M-D10  M-11 dung MOT PHIA (bien co: min_j m_true_j < 0, khop 1.0000).
       HAI PHIA gop nhanh "twin bao thu" -- vo hai -- va lech 13 diem.
       Muc headline = all test rows; accept-only bao cao KEM (M-14).
M-D11  M-6 phan ra ba nhanh (rang buoc / ngan sach / ca hai) + kiem cong duoc.
M-D12  M-12 danh gia o BA diem: r_star, |point|, |CI90 xau|.
M-D13  Nguong M-13 dan tu ti so CO DIEU KIEN a/b, crit = 1/P_fix voi P_fix
       cua CELL CHINH ap cho cell khac.
M-D14  [C] tinh lai TOAN BO duong ong o moi diem bom; `q̂` GIU tu the gioi goc.
```

---

## 5. Nguyen tac moi

```text
NT-v2-23  Bang trong tai lieu phai duoc SINH tu artifact. Mot cot bi dan de
          khong lam do test nao -- no chi lam sai mot ket luan.
NT-v2-24  Truoc khi ky mot du doan dang bat dang thuc, viet ca hai ve ra cong
          thuc va rut gon. Neu hai ve dinh nghia tu CUNG mot phep do, do la
          HANG DANG THUC va dong do khong kiem dinh gi.
NT-v2-25  Moi NGUONG DAN XUAT phai kem mot phep kiem DOC LAP tren du lieu that.
          Khong khop -> NGUONG sai. Ghi ca cong thuc sai va ly do.
NT-v2-26  Khong lam phang hai LOAI khac nhau vao mot tap roi so sanh.
```

---

## 6. Co che M-12a -- co so cua nhan [CO CHE]

```text
Δ = (1 − γ)·(c_F2 − c*)

c_F2: F2 chon P1 tren MOI hang reject             -> chien luoc MOT DUONG
c*  : twin chon P1 49.9% / P3 46.9% tren reject   -> chien luoc HAI DUONG
      (baseline_c3_b2_audit, C3 reject a_twin_dist = [0.4989, 0, 0.4689, 0.0322])

Cu lat chu dao P1 -> P3 chiem 178,440 / 226,132 = 78.9% so hang doi.
Goi f = ti le hang reject co a* lat P1 -> P3.

  Δc_F2 ≈ +f                              (thuan hai, khong bu tru)
  Δc*   ≈ +f·(0.499 − 0.469) = +0.03·f    (gan nhu TRIET TIEU)
  ⟹ Δ(c_F2 − c*) ≈ +0.97·f

Hien tai c_F2 − c* = −0.058495.  Doi dau can f > 0.060.
Ti le lat P1->P3 toan bo = 178,440/999,945 = 0.178.  Khoang cach ~3 lan.
```

> **Menh de:** `F2 STATIC` la chien luoc MOT DUONG nen KHONG CO PHONG HO truoc
> viec `a*` roi khoi duong do. Twin la chien luoc HAI DUONG nen cu lat vua hai
> vua loi va gan nhu triet tieu. Mot dich chuyen cua chan ly ve phia `P3` PHA
> `F2` ma gan nhu khong pha twin.

---

## 7. Bang du doan Lesson 23.7 -- BAN KHOA

| ID | Dai luong (ba nhan) | Nhan | Cham o | Diem |
|---|---|---|---|:--:|
| M-1 | `spread_m` = 1.1188 | [TAT DINH] | — | KHONG |
| M-2 | `spread_z` = 2.1232 | [TAT DINH] | — | KHONG |
| M-3 | `spread_total` = 2.6134 | [TAT DINH] | — | KHONG |
| M-7', M-8' | neo `err\|acc` / `c*` @0.78 | [TAT DINH] | — | KHONG |
| M-7, M-8 | **RUT** (NT-v2-21) | — | — | — |
| M-4 | Jaccard(C3, C3-q̂-hang), accept-set, γ=0.78; **0.94–0.99** | [CO CHE] | 3 cell | CO |
| M-5 | q̂(K'=3,α/2)/q̂(K=4,α/3), slot-1, calib; **0.905–0.935** | [CO CHE] | 3 cell | CO |
| M-6 | Δacceptance nhanh (iii) tai S2; **0.08–0.18** | [NGOAI SUY] | 2 giu kin | CO |
| M-6b | phan NGAN SACH tai S2; **0.75–1.00** | [NGOAI SUY] | 2 giu kin | CO |
| M-6c | phan ngan sach S1 > phan ngan sach S2 | [CO CHE] | 2 giu kin | CO |
| M-9 | \|tach duoc\| cua q̂; **<= 0.05** | [CO CHE] | 2 giu kin | CO |
| M-10 | Spearman(z_s, m̂_1), row, test; **−0.7 … −0.3** | [NGOAI SUY] | 3 cell | CO |
| M-11 | q95(mot phia)/mean(m̂_1), all-test; **1.45–1.76** | [NGOAI SUY] | 2 giu kin | CO |
| M-12a | dau cua Δ(c_F2 − c*) duoi bom; **DUONG** | [CO CHE] | 3 cell | CO |
| M-12b | ket luan 23.6 doi dau o CA BA diem; **CO** | [NGOAI SUY] | cell chinh | CO |
| M-13 | cat P4 co lai ⟺ a/b > 1.3144 | [CO CHE] | 2 giu kin | CO |
| M-13b | ti so over-selection P4; **1.0–2.5** | [NGOAI SUY] | 2 giu kin | CO |
| M-13c | `P_fix`; **0.60–0.90** | [NGOAI SUY] | 2 giu kin | CO |
| M-14 | ratio(accept)/ratio(all) < 1.0 | [CO CHE] | 2 giu kin | CO |
| M-15 | n_flip/n_test; **0.10–0.40**; can duoi do clip 40% | [NGOAI SUY] | 2 giu kin | CO |
| M-16 | coverage C3 duoi bom, q̂ giu goc; **< 0.90** | [CO CHE] | cell chinh | CO |

**16 dong lop 3.** (Lesson 23.6 co 3.)

### 7.1. Lam ro M-D2 truoc khi cham M-4

Chon cach doc (c): do CA HAI doi chung. M-4 duoc CHAM theo cach (a), tuc
`post_variant="none"` van giu `z_bin` va chi bo truc `m_hat_bin`; day la phep
do dong gop cua truc `m_hat`, dung voi cau hoi S4 va dai da khoa 0.94--0.99.
Doi chung qhat hang so toan cuc (b) duoc bao cao RIENG de cho thay anh huong cua
viec bo ca hai truc; ket qua nay KHONG dung de cham M-4 va KHONG noi dai.

```text
Ky luat pham vi: CELL CHINH = PHONG HIEU CHUAN. Moi dong da nhin so tren cell
chinh chi cham tren HAI CELL GIU KIN. Ba ngoai le co ly do:
  M-4, M-5, M-10  : chua nhin so tren cell nao      -> cham ca ba
  M-12b, M-16     : ban chat la cau hoi VE CELL CHINH (ket luan 23.6 nam o do)
                    -> cham tren cell chinh; dai dan tu CO CHE, khong tu so
```

---

## 8. Hai rang buoc BAT BUOC cho [C] (M-D14)

```text
① Tai MOI diem bom, tinh lai TOAN BO duong ong:
      a* moi -> wrong moi -> c*(γ) moi, c_F2(γ) moi, Δ(γ) moi
   KHONG duoc chi dieu chinh err_neo. Ly do: Δ = (1−γ)(c_F2 − c*) va CA HAI
   ve deu doi.

② Certificate KHONG duoc hieu chuan lai. `q̂` giu tu bang tra GOC.
   Ly do: trong the gioi that ta khong biet residual, nen khong the hieu chuan
   de bu no. Hieu chuan lai la cho certificate mot thong tin no khong the co
   -- mot dang ro ri oracle (S1).

   He qua chinh xac (day la M-16): `s_pair_j` phu thuoc `y_true`, nen khi bom,
   diem so tren TEST doi trong khi `q̂` tu CALIB goc khong doi. Gia dinh TRAO
   DOI DUOC giua calib va test bi pha mot cach HE THONG.
```

### 8.1. Cap doi chung cho M-16 -- bat buoc

```text
NC23v2-8  Bom CA calib LAN test  ->  trao doi duoc duoc GIU  ->  coverage
          phai giu quanh 1 − α = 0.90.
          Neu coverage TUT o day thi loi nam o CODE, khong o gia thuyet.

PC23v2-3  Bom CHI test, `q̂` tu calib goc  ->  trao doi duoc bi PHA  ->
          coverage phai TUT.  Day chinh la M-16.

Hai nhanh dung CUNG mot bang tra bi bom, CHI khac o cho `q̂` lay tu dau.
Neu ca hai cung tut hoac cung giu, phep do khong phan biet duoc hai gia
thuyet va M-16 vo nghia.
```

Dien giai duoc phep, neu M-16 dat:

```text
DUOC:  "Bao dam conformal la PHAN PHOI-TU-DO doi voi PHAN PHOI, nhung KHONG
        mien nhiem voi SAI LECH HE THONG cua thuoc do. Khi bang tra hieu chuan
        lech khoi thuc te o muc da do o Phase 20R, bao phu thuc te tut xuong
        duoi muc danh nghia."
KHONG: "Conformal prediction khong hoat dong."
KHONG: bao cao M-16 ma khong bao cao NC23v2-8.
```

---

## 9. Cau truc code (buoc [3a] da xong)

```text
cert/cell_matrices.py         TANG DAY. Khong import bat ky lesson23_7_* nao,
                              cung khong import conditioning_audit.
cert/lesson23_7_*.py          ba buoc hieu chuan, CUNG CAP BAC, chi import
                              XUONG cell_matrices, KHONG import lan nhau.
cert/conditioning_audit.py    [3b] cham diem, import cell_matrices.

Hai buoc sau GHIM sha256 artifact buoc truoc vao provenance.
Approval sau refactor: 0 khac biet tren ca ba artifact + markdown.
Thuc thi: test_phase23_lesson237_structure.py (9 nhanh + 3 slow).
```

---

## 10. Ra soat NT-v2-9 / NT-v2-24 nguoc len bang M

```text
NT-v2-9 (tinh duoc bang dai so dong tu artifact da co):
   M-1, M-2, M-3, M-7', M-8'  -> [TAT DINH], DA ha nhan.
   Cac dong con lai: kiem va XAC NHAN can chay moi.

NT-v2-24 (bat dang thuc co phai hang dang thuc):
   M-13  -> DA SUA: nguong dung P_fix CUA CELL CHINH ap cho cell khac.
            Neu dung P_fix cua chinh cell do, no la hang dang thuc.
   M-6c  -> hai ve do tren HAI MUC (S1 vs S2) cua CUNG cell. Khong co rang buoc
            dai so nao buoc S1 > S2. HOP LE.
   M-14  -> tu so va mau so do tren HAI TAP HANG khac nhau. HOP LE.
   M-9   -> spread_total va tich ba spread bien la HAI phep tinh khac nhau tren
            cung tensor; bang nhau CHI KHI tach duoc. HOP LE.
   M-16  -> coverage do duoc vs 0.90 danh nghia; 0.90 la hang so tu ALPHA,
            khong dan tu du lieu. HOP LE.
```

---

## 11. Chu ky

```text
Nguoi ky : vantai (Claude-assisted)
Ngay     : 2026-08-20
```

Toi xac nhan: khong mot dai nao duoc noi sau khi nhin so tren cell duoc cham.
Cell chinh la phong hieu chuan; 13/16 dong lop 3 cham tren hai cell giu kin.
Cong thuc nguong bi bac bo duoc ghi lai kem ly do, khong bi xoa.

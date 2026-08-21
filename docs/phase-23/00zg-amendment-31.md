# AMENDMENT 23-31 -- Hau kiem Lesson 23.7 va sua so cai du doan

Ngay: 2026-08-21
Thoi diem: SAU khi chay Lesson 23.7 tai commit `d2869b8`.

Amendment nay KHONG cham lai va KHONG noi bat ky dai da khoa nao. No sua mot
du doan trai voi artifact da commit, ghi ro hai cell moi khong dung duoc lam
phong thi cho ti so `rho`, va khoa truoc hai dong mo rong M-21/M-22 neu phep
do mo rong duoc chay.

---

## 1. RUT M-10 -- du doan nguoc voi artifact da commit

Amendment 23-30 ghi:

```text
M-4, M-5, M-10: chua nhin so tren cell nao -> cham ca ba.
```

Menh de nay SAI doi voi M-10. Moi build report `calib_set_v3_*.json` cua Phase
22 da ghi san `corr_z_s_m_hat_calib`:

```text
poisson@0.925  -0.0000566644
poisson@0.850  -0.0000500681
h2@0.700       +0.0005854247
poisson@0.700  +0.0006962695
cbr@0.700      -0.0005839418
```

`mhat_bin_by_z_bin_calib_pct` cung cho thay trong moi `z_bin`, bon
`m_hat_bin` deu xap xi 25.0%. Day la bang chung da commit rang tuoi va margin
gan doc lap theo thiet ke profile U0. Dung Pearson tren calib thay cho
Spearman tren test khong lam chung thanh cung mot thong ke, nhung no du de
bac bo tu cach "chua tung nhin so" cua M-10 va dat dải `-0.7 ... -0.3`.

```text
M-10: MISS -> RUT.
Nhan moi: [TAT DINH].
Khong tinh diem, khong vao mau so prediction-hit.
```

Gia thuyet "z va m_hat tuong quan am roi triet tieu" van bi bac bo, nhung do la
ket qua [MO TA], KHONG phai mot prediction confirmatory cua Lesson 23.7.

```text
NT-v2-34  Truoc khi ky mot dong du doan ve MOT DAI LUONG THONG KE CUA DU LIEU
          (tuong quan, phuong sai, phan vi, phan phoi bien), grep TOAN BO
          build report cua phase truoc. Build report thuong da tinh san cac
          chan doan ma nguoi ky chua doc.
```

---

## 2. Phong thi cho rho KHONG ton tai

Hai cell `poisson@0.700` va `cbr@0.700` chua duoc dung cho dong M-* nao, nhung
khong vi the ma chung la phong thi hop le cho mot ti so co mau
`Var(log m_hat_eff)`.

```text
cell             err_neo   trang thai    Var(log m_hat) uoc tu canh phan vi
poisson@0.925    0.222399  EVALUABLE     0.8833  (do truc tiep: 1.2045)
poisson@0.850    0.220727  EVALUABLE     0.8378  (do truc tiep: 1.2607)
h2@0.700         0.126536  EVALUABLE     0.6935  (do truc tiep: 1.0409)
poisson@0.700    0.000000  DEGENERATE    0.0291  (~0.04 sau hieu chinh)
cbr@0.700        0.000000  DEGENERATE    2.32e-09
```

`cbr@0.700` co IQR tuong doi cua `m_hat` chi khoang `6.5e-05`; margin gan nhu
la mot hang so. `poisson@0.700` co thang bien thien nho hon khoang 30 lan so
voi ba cell da do. Vi vay ti so `rho` khong so sanh duoc giua phong hieu chuan
va hai cell nay.

```text
M-17..M-20 voi dai |rho| <= 0.15: KHONG DUOC KY, rut khoi ke hoach.
```

```text
NT-v2-33  Truoc khi chon mot "phong thi" moi, kiem rang MAU SO hoac thang
          chuan hoa cua dai luong duoc cham CO SO SANH DUOC voi cac don vi da
          hieu chuan. Mot cell chua ai doc van vo dung neu no khac cau truc o
          dung chieu ma dai luong chuan hoa theo.
```

---

## 3. Omega bi thay; dai 0.02--0.05 BI BAC BO

Phep do hau kiem tren slot nut co chai cho:

```text
cell             Var(log score)  Var(log qhat_eff)  omega
poisson@0.925       1.161490          0.064374       0.055424
poisson@0.850       1.282073          0.059736       0.046593
h2@0.700            0.949125          0.065571       0.069086
```

Chi `1/3` cell nam trong dai hau kiem `0.02--0.05`; dai do BI BAC BO va khong
duoc ky cho cell moi. Loi uoc luong ban dau la suy `sd(log m_hat)` tu bien do
mau thay vi do phuong sai that.

Cong thuc dung phai giu covariance:

```text
Var(log score) = Var(log m_hat_eff) + Var(log qhat_eff)
                 - 2 Cov(log m_hat_eff, log qhat_eff)

Cov do duoc = 0.053675 / 0.019148 / 0.078706.
```

M-10 (`z` gan doc lap voi `m_hat_1`) KHONG suy ra `qhat_eff` doc lap voi
`m_hat_eff`: qhat duoc lap chi muc theo ca `m_hat_bin`, va phep `argmin` chon
slot cung phu thuoc margin. Do do omega chi do phan phuong sai bien cua qhat;
no khong tu dong la mot phep quy thuoc thay doi thu hang.

```text
NT-v2-31  Khong uoc phuong sai log tu BIEN DO mau. Bien do phu thuoc co mau
          va ngoai lai; neu dai luong can phuong sai, do phuong sai tren dung
          rowset va dung bien bien doi se duoc cham.

NT-v2-32  Mot phan ra phuong sai phai ghi du so hang covariance. Khong duoc
          dien giai ti so hai phuong sai bien nhu "dong gop vao thu hang" neu
          chua chung minh doc lap tren CHINH cac bien hieu dung sau moi phep
          lap chi muc va chon argmin.
```

---

## 4. Hai dong ky moi cho phep do mo rong

Ba cell da doc co `Var(log qhat_eff) = 0.059736--0.065571`, bien thien duoi
10% trong khi thang `Var(log m_hat_eff)` thay doi lon. Neu mo phep do mo rong,
hai dong sau duoc khoa TRUOC khi tinh qhat/Jaccard tren hai cell moi:

```text
M-21  Var(log qhat_eff) tren poisson@0.700 va cbr@0.700.
      Nhan: [NGOAI SUY]. TINH DIEM.
      Dai khoa: 0.03--0.12 tren moi cell.

M-22  Ti le hang lech MOI BEN khi bo TOAN BO Mondrian conditioning.
      Nhan: [CO CHE]. TINH DIEM neu phep do khong suy bien vi hoa diem.
      Du doan: ca hai cell moi cao hon 2.2281% (max cua ba cell da doc),
      va cbr@0.700 cao hon poisson@0.700.

NC23v2-9  Ep qhat thanh mot hang so toan cuc thi
          Var(log qhat_eff) - 2 Cov(log m_hat_eff, log qhat_eff) = 0
          chinh xac den 1e-12.
```

Canh bao khoa cho M-22: `cbr@0.700` co margin gan hang so, nen score co the
hoa hang loat va `_accept_at_coverage` pha hoa bang `mergesort` theo thu tu
hang. Phai bao cao ty le hang thuoc nhom score hoa tai bien accept. Neu ty le
nay vuot 10%, `cbr@0.700` ha thanh [MO TA], M-22 chi cham confirmatory tren
`poisson@0.700` va KHONG duoc thay dải.

M-21/M-22 la mot phep do MO RONG chua chay, khong nam trong ke toan 16 dong
goc cua Lesson 23.7.

---

## 5. NC23v2-8 la tieu chi MOT PHIA

Amendment 23-30 viet coverage "giu quanh 1-alpha = 0.90". Tu "quanh" mo ho
va da duoc cai thanh cua so doi xung `+/-0.02`. Do la sai: bao dam conformal
la mot phia.

```text
NC23v2-8 dat <=> coverage >= 1-alpha = 0.90, khong co can tren.
```

Sua nay duoc thuc hien SAU khi thay `0.923055`, nhung hop le vi:

```text
(a) tieu chi dan tu dinh ly, doc lap voi so quan sat;
(b) neu NC cho 0.88, cua so +/-0.02 cho DAT con tieu chi moi cho TRUOT;
(c) sua theo huong bat loi o phia duoi, khong phai noi dai de vua so.
```

Baseline `0.922749 > 0.90` la tinh bao thu huu han mau do ba nguon cung chieu:

```text
1. empirical_qhat dung method="higher";
2. conformal_level dung ceil((n+1)(1-alpha))/n;
3. Bonferroni alpha/3 tren ba slot.
```

```text
NT-v2-29  Moi tieu chi PASS/FAIL phai viet bang mot bat dang thuc tuong minh,
          khong bang tu dinh tinh nhu "quanh", "gan", "xap xi".
```

---

## 6. M-5 chot cach cham sau khi chay

Cach cham nhat quan voi hieu chuan la:

```text
M-5 dat tren mot cell <=> min VA max cua 16 o Mondrian deu nam trong dai.
```

Day la lam ro SAU khi chay, KHONG noi dai. Ke toan trung thuc:

```text
cell             min--max              [0.90,0.96] ke hoach  [0.905,0.935] khoa
poisson@0.925    0.9072--0.9322          HIT                  HIT
poisson@0.850    0.8952--0.9194          MISS                 MISS
h2@0.700         0.9011--0.9362          HIT                  MISS
```

Viec siet dải tu cell chinh da bien h2 tu HIT thanh MISS vi bo quen bien
thien GIUA cell. Ket qua van duoc cham theo dải khoa `0.905--0.935`.

```text
NT-v2-30  Khi cach cham la "moi don vi con deu trong dai", dai phai bao ca
          bien thien TRONG don vi hieu chuan va bien thien GIUA cac don vi
          duoc cham. Min--max cua mot don vi khong bao nguon thu hai.
```

---

## 7. Hai loai MISS, RUT va NEUTRAL

```text
MISS ve NGUOI KY:
  M-4   tran dải qua thap; Jaccard 0.9946--0.9990 > 0.99, co che manh hon.
  M-5   dai siet quen bien thien giua cell.

MISS ve THE GIOI:
  M-6   h2 thap hon dai vi P4 chet doi voi twin.
  M-9   h2 vuot can 0.05 mot luong 0.003079.
  M-11  h2 co residual/margin thap hon hai cell poisson.
  M-13b hai cell giu kin co over-selection thap hon dai; h2 bang 0.

RUT:
  M-10  artifact Phase 22 da ghi dai luong lien quan xap xi 0.

NEUTRAL, KHONG DANH GIA DUOC:
  M-13 va M-13c tren h2: a=b=0, twin khong bao gio chon P4.
```

```text
NT-v2-27  Mot tuong duong X <=> Y thoa man tam thuong khi ca hai ve sai khong
          tao mot HIT neu tien de cua phep do khong ton tai. Trang thai dung
          la NEUTRAL/khong danh gia duoc va dong do khong vao mau so hit.

NT-v2-28  Tai lieu sinh ra phai byte-identical qua vong ghi JSON -> doc JSON
          -> sinh lai. Thu tu dong phai den tu mot hang so thu tu duy nhat,
          khong tu thu tu dict, JSON hay he thong tap tin.
```

---

## 8. Ke toan cuoi cua 16 dong goc

```text
13 dong danh gia duoc: 7 HIT / 6 MISS = 53.8%
1 dong RUT          : M-10
2 ket qua NEUTRAL   : M-13, M-13c tren h2 (khong vao mau so)
```

HIT hoan toan: M-6b, M-6c, M-12a, M-12b, M-14, M-15, M-16.

---

## 9. Gioi han cua viec dong so gate

Repo hien tai KHONG co `PLAN_v2.md` hoac `PHASE_23.md` dinh nghia noi dung cua
`G23-37..G23-42`. `GATES.md` chi co sau ID provisional voi trang thai NOT_RUN.
Vi vay amendment nay KHONG gan nghia hau nghiem va KHONG tu cham sau gate do.
Xu ly dung giong `G23-34`: giu NOT_RUN cho den khi dinh nghia goc vao repo.

Co the dua 16 dong M-* vao registry va kiem bang test ngay; KHONG the khai bao
Lesson 23.7 da dong trong `CLOSED_LESSONS` ma van giu mot so gate khong co
dinh nghia. Viec dong lesson o tang gate bi CHAN boi thieu nguon dinh nghia,
khong bi chan boi phep do Lesson 23.7.

---

## 10. Chu ky

```text
Nguoi ky : vantai (Codex-assisted)
Ngay     : 2026-08-21
Trang thai: amendment hau kiem; khong cham lai mot dong nao
```


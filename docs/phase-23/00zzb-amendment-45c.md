# AMENDMENT 23-45c -- Sua ket luan T5 cua Lesson 23.18, va mot khiem khuyet do

Ngay ky : 2026-08-22
Tag     : amendment-45c
Lesson  : 23.18 (sua ket luan da cong bo)
Loai    : CORRECTION -- day KHONG phai du doan. So da duoc nhin truoc khi viet.

## 1. Ket luan bi sua

Lesson 23.18 muc 7 (`docs/phase-23/22-aoi-stall-anatomy.md`) cong bo:

```text
corr(AoI, rho) muc epoch:  -0.2066 tho  ->  -0.3139 khu link
                           ->  -0.1994 khu them T_eff
"Hieu ung SONG SOT ca hai phep khu. Gia thuyet (b) khong duoc ung ho:
 tuong quan am khong phai chi do do dai epoch. Co che van CHUA RO."
-> dua vao threats to validity cua Lesson 23.19
```

**Ket luan do sai.** No dua tren hai loi cong lai.

## 2. Loi 1 -- ham T5 KHONG cat warm-up

`measurements/aoi_decompose.py::partial_corr_within_epoch` doc thang
`aoi_*.jsonl` va KHONG ap dung moc cat warm-up, khac han `T2_warmup_trim`
va `decompose_run` (ca hai deu cat). 2.040 / 28.680 epoch nam truoc moc cat
van duoc tinh vao.

```text
                        n        tho      khu LINK   corr(rho, T_eff truoc)
TAT CA epoch         28.680   -0.3020     +0.1638         -0.0897
CHI epoch SAU cat    26.640   -0.3667     +0.0263         +0.0004
```

Chi 7% epoch warm-up da lat DAU cua tuong quan da khu link, tu `+0.026`
thanh `+0.164`, va con so `-0.3139` cong bo o 23.18 la ket qua cua cung
loi do tren mot tap epoch khac.

## 3. Loi 2 -- `uA` va `uB` co `rho` HONG, va no gay nhieu gia

Kiem tren TOAN BO 30 run, 35.970 mau moi link:

```text
link         n   n_rho=0    ty le    rho max
ac       35970        46    0.13%    1.0000
ad       35970        47    0.13%    1.0000
bc       35970        53    0.15%    1.0000
bd       35970        31    0.09%    1.0000
uA       35970     35263   98.03%    0.0005      <-- HONG
uB       35970     35232   97.95%    0.0036      <-- HONG
vC       35970        59    0.16%    0.9532
vD       35970        52    0.14%    1.0000
```

Nguyen nhan: `canonical_link_key` xep ten switch truoc, nen hai canh bien
phia nguon thanh `link-sA-sSRC` va `link-sB-sSRC`. Truong `util_direction`
la `tx`, tuc do chieu **sA -> SRC** va **sB -> SRC** -- chieu KHONG co luu
luong. Sau canh con lai duoc khoa theo chieu thuan nen khong bi.

Luu luong that co ton tai: `flows_*/rho_offered_uA.csv` ghi
`rho_offered = 0.832` o cung dieu kien.

**He qua cho T5:** `uA` va `uB` la hai Thing CUOI trong vong PATCH nen co
`d_transport` lon nhat (168.09 va 175.58 ms) va do do AoI cao nhat -- dong
thoi co `rho == 0`. Chi rieng su trung hop do tao ra

```text
corr GIUA LINK (n = 8):   rho vs AoI          = -0.9123
                          rho vs d_transport  = -0.8978
```

Tuong quan am "quan sat duoc" gan nhu hoan toan la **nhieu gia giua cac
link** (confounding), khong phai quan he giua tai va tuoi. Gop mau cua 8
link roi tinh mot he so la vi pham dieu kien dong nhat.

## 4. Ket luan DUNG

```text
Sau khi cat warm-up VA khu bien link:
    corr(AoI, rho) = +0.0263        (n = 26.640 epoch)
    corr(rho, T_eff khoang truoc) = +0.0004
```

Nghia la:

```text
- Gia thuyet (b') "artifact cua estimator toc do co cua so" KHONG CAN den.
  K1 do duoc +0.0004: khong co ghep noi nao qua bien tre.
- Khong con hieu ung nao de giai thich. corr(AoI, rho) trong tung link,
  sau khi cat warm-up, la KHONG.
- Mo hinh rang cua cua Lesson 23.19 gia dinh corr = 0. Gia dinh do duoc
  BIEN MINH bang so do, khong con phai "bo qua".
- corr(AoI, rho) RA KHOI threats to validity.
```

Thay vao do, threats to validity nhan MOT MUC MOI:

```text
L30  rho cua uA va uB do sai chieu trong toan bo chien dich 23.8.
     Khong anh huong AoI (AoI la hieu hai dau thoi gian, khong dung rho).
     Anh huong moi phan tich dung rho THEO TUNG LINK tu twin.
     Phai sua canonical_link_key hoac chon chieu truoc Phase 24.
```

## 5. Vi sao loi nay khong bi bat som hon

`M-86` (muc mau, da cat warm-up, gop link) do duoc `-0.0573` va HIT dai
khoa `-0.10 .. -0.02`. Dai khoa do lay tu Lesson 23.8, ma 23.8 cung do
tren du lieu co cung khiem khuyet. **Mot du doan duoc xac nhan boi chinh
cai loi da sinh ra no.** Day la ly do vi sao HIT khong bao gio la bang
chung du: phai co mot phep kiem doc lap ve co che.

Phep kiem da bat duoc no: tach BEN TRONG link va GIUA cac link. Neu hai
cai khac dau hoac khac do lon nhieu, gan nhu chac chan co confounding.

## 6. Hanh dong

```text
- sua partial_corr_within_epoch: ap dung moc cat warm-up
- bao cao TACH BACH: giua-link vs trong-link, khong gop mot he so
- danh dau tuong minh link co rho hong trong artifact
- KHONG rut lai so cu cua 23.18; cong bo ban moi canh ban cu
- them L30 vao so threats to validity
```

## 7. Bai hoc

```text
Ba ham trong cung mot phan tich, hai ham cat warm-up, mot ham quen.
=> moc cat phai la MOT tham so duoc truyen, khong phai mot buoc moi ham
   tu lam lay. Da sua theo huong do.
```

Chu ky: ____________

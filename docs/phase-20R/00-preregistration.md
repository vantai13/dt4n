# PRE-REGISTRATION -- Phase 20R: Decision error tren dai che do van hanh

Ngay ky   : 2026-08-04
Git tag   : phase-20R-start
Nguoi ky  : vantai13
Trang thai: DA KY. Moi thay doi phai qua AMENDMENT, khong sua file nay.

## 0. Input Da Khoa

```text
twin/link_model_v2.py                  sha256 = 17011990fa50c7d0c7155831cce475513684022c20b551440acead00ed1ef2a1
results/phase-L/link_model_v2_fit.json sha256 = ab17908c40359572e35effdee561f8217477168ba77298831a734ab47cc9563b
mininet/rho_spec.py    @ fa6dbda       sha256 = 6a2e8775a08460ab4810ee822ceba81ea1da578a4bc15740f1a192398f20c1e7
mininet/load_spec.py   @ fa6dbda       sha256 = a522c0d2079f43151f39912f6ba289b560478f69edd12e163b0c591399ad3dec
twin/topology_v7.py    KHONG SUA       sha256 = c8263ce17feffdd17031dbcb3694880a4f649c6870068ce7a1f6631ec859076a
docs/phase-T/APPENDIX-quasistatic.md   sha256 = 57bccc1fc29a66a28440969b8b2724efa8d36322660affb0fc76d766911985bf
```

## 1. Quan He Voi Phase 20

Phase 20 dong bang tai tag `phase-20-complete`. KHONG sua nguoc.

Ly do khong dung lai: `docs/phase-20R/01-inherited-audit.md` va
`docs/phase-20/99c-erratum-2.md`. Tom tat: thay `link_model` la sai so vi
sai, khong phai dong pha; tai LOAD_MEAN, `ad = 0.61x` con `bd = 2.00x`;
xep hang `P3/P4` hoan vi; `T_delay` cu nam duoi phan phoi delay do v2.

## 2. Bay Quyet Dinh -- Chot

### Q1. Dai Luong Du Doan

```text
y_hat(a,t)  = sum_link [base + frame*8/bw*1000 + link_model_v2.predict_delay(mode,bw,q,rho(t-z))]
y_true(a,t) = sum_link [base + frame*8/bw*1000 + MEAN OWD DO DUOC tai rho(t)]
loss(a)     = 1 - product_link(1 - loss_link)
cost(a)     = delay(a) + w_loss * loss(a)
frame_bytes = 1512
```

Loss duong dung phep nhan survival, khong cong loss theo link.

### Q2. Nguong SLA -- Quy Tac, Khong Chot So Dep

```text
T_delay(o) = percentile p85 cua delay duong TOI UU, tinh rieng tung o
T_loss(o)  = percentile p85 cua loss duong TOI UU, tinh rieng tung o
w_loss(o)  = T_delay / T_loss
vi_pham    = (delay > T_delay) OR (loss > T_loss)
hoi_tu     = lap den |w_moi - w| < 1e-6, toi da 8 vong
rang_buoc  = opt_viol_rate trong [0.10, 0.25]
```

Neu mot o khong dat rang buoc, loai o do khoi gate voi ly do ghi ro; khong
chinh tay nguong sau khi thay `err` hay `d_sla`. Ly do doi voi Phase 20:
`T_loss = 0.01` co dinh lam `h2` vi pham co hoc khi loss toi uu da quanh 6.8%.

### Q3. Fallback Khi ABSTAIN

Fallback 20R la F2 shortest-hop tinh: `P1`, tinh theo `base + serialization`
la 12.04 ms. F3 minimax de danh cho Phase 23. Gia cua fallback phai duoc do
trong 20R.

### Q4. So Hanh Dong

`K = 4`. Khong sua `twin/topology_v7.py`.

### Q5. Luoi Tuoi z

```text
z in {0, 0.05, 0.10, 0.20, 0.30, 0.50, 1.0, 2.0, 4.0} s
dt trace = 0.005 s
```

Bat buoc goi `check_z_grid()` truoc moi lan do; raise neu aliasing.

### Q6. Che Do Van Hanh

```text
rho_bar in {0.70, 0.85, 0.925, 0.96}
family  in {cbr, poisson, h2}
```

Khong dung `c_a` lam truc. Phase L bac bo `f(rho, c_a)`: tai `bw=6`,
`q=13`, `rho=0.90`, `onoff` co `c_a=2.312` nhung delay 6.63 ms, trong khi
`h2` co `c_a=2.032` nhung delay 11.04 ms.

Bo `onoff` khoi 20R vi `link_model_v2` chi phu `onoff|6|13`, con
`topology_v7` can them `(8,18)` va `(4,10)`. Giu `onoff` chi lam phan vi du
bac bo `f(rho, c_a)`.

Loai truoc cell `(cbr, rho_link >= 0.95)` vi `is_reliable = False` va
`T_relax = 28.5 s` pha xap xi tua-tinh.

### Q7. Anh Xa rho_bar -> rho Tung Link

```text
mean(LOAD_MEAN) = 0.8675
offset = LOAD_MEAN[link] - mean

uA -0.0675   uB -0.0475   ac +0.0525   ad +0.0625
bc +0.0475   bd +0.0575   vC -0.0675   vD -0.0375

rho_link = clip(rho_bar + offset_link, 0.50, 1.05)
```

Khong tune offset; lay tu thiet ke da co truoc. Neu moi link cung `rho`, thu
tu tinh bi khoa boi `P1 = 12.04 < P3 = 13.54 < P4 = 13.55 < P2 = 14.05 ms`,
lam `err ~= 0` mot cach nhan tao.

Ly do chon `rho_bar max = 0.96` thay vi `0.98`:

```text
rho_bar 0.70 / 0.85 / 0.925  -> max clip 0.00%
rho_bar 0.98                 -> link ad clip 22.66%   KHONG CHAP NHAN
rho_bar 0.96                 -> link ad clip  0.30%   CHAP NHAN
```

Ti le clip phai ghi vao provenance moi o.

## 3. Thiet Ke Thi Nghiem

Phep do chinh la tua-tinh, do theo link, dai luong cong tinh la mean OWD,
cua so `W = 60 s`, dung ha tang Phase L. Giay phep:
`docs/phase-T/APPENDIX-quasistatic.md`.

Doi chung bat buoc:

```text
DC1 end-to-end tren P1 va P4, 2 che do, 5 seed -> kiem tinh cong tinh
DC2 CRN tren 1 che do -> kiem sigma_repeat
```

## 4. Gia Thuyet Viet Truoc Khi Do

```text
H1 ton tai >=1 o (rho_bar, family) co err(z_max) in [0.05, 0.40]
H2 trong o do, err tang don dieu theo z (Spearman, khong nhin mat)
H3 trong cung family, err tang don dieu theo rho_bar
H4 err(cbr) < err(poisson) o moi rho_bar
H5 err(h2)  < err(poisson) o rho_bar >= 0.85
```

## 5. Du Doan Bang So

```text
poisson @ LOAD_MEAN, tau=1.0s, sigma=0.010:
    T_delay ~ 24.9 ms, w_loss ~ 2490, opt_viol ~ 0.178
    z=0.05  err=0.100  d_sla=0.011
    z=0.20  err=0.194  d_sla=0.042
    z=1.00  err=0.398  d_sla=0.143
cbr : err ~ 0 o moi z
h2  : err < 0.01
```

Neu do that lech > 2x so voi du doan, dung va dieu tra thuoc do truoc khi tin
con so.

## 6. Gate 20R

```text
20R-G1 ton tai >=1 o co err(z_max) in [0.05, 0.40]
20R-G2 o do co d_sla_lower >= 0.03
20R-G3 trong o do, Spearman(err, z) > 0, p < 0.05
20R-G4 trong >=1 family, Spearman(err, rho_bar) > 0
20R-G5 NC1b twin hoan hao -> err = 0.000000 tuyet doi
       NC2 twin ngau nhien -> err in [0.72, 0.78]
       PC1 cbr -> err ~ 0
20R-G6 |cost_end_to_end - sum(link)| <= 0.20 * khe cost = 0.44 ms
20R-G7 moi CI dung se_batch. Khong bao cao nao dua tren se_naive.
```

Ngoai le da ghi truoc: neu G3 FAIL nhung `err` lon, khong coi la fail. Do la
nhanh (d): `e_model` chi phoi. Bao cao tach `e_model/e_staleness`, di tiep
21R.

## 7. Ngan Sach Lap

Toi da 2 vong. Neu moi o FAIL, sua theo thu tu, moi vong dung mot thu:

```text
1. siet T_delay xuong p70
2. nhan offset Q7 voi he so 1.5 cho moi o
3. tang K
```

Khong duoc doi family, `link_model_v2`, topology, hoac luoi `rho_bar`.

## 8. Doi Chung Bat Buoc

```text
NC1  z = 0 -> err > 0 va bang xap xi ti le e_model
NC1b twin hoan hao -> err = 0.000000 TUYET DOI
NC2  twin ngau nhien -> err ~ 1 - 1/K = 0.75
PC1  cbr -> err ~ 0 vi do doc hang doi = 0
PC2  tinh cong tinh end-to-end -> lech <= 0.44 ms
```

## 9. Rui Ro Da Biet

```text
R-20R-1 tua-tinh khong hop le o cbr gan bao hoa -> da loai
R-20R-2 path p95/p99 khong cong tinh -> duoi phai do end-to-end
R-20R-3 probe 20 pps lam lech delay toi 1.46% -> ghi provenance
R-20R-4 onoff bi loai vi thieu cau hinh do -> ghi ro truoc
R-20R-5 luoi rho Phase L chi 12 muc -> Lesson 20R.4 do bu buoc 0.01
R-20R-6 clip tai tran 1.05 -> da xu ly bang rho_bar max = 0.96
```

# AMENDMENT 23-78 -- LESSON 23.25b: VA NEN CUA `omega_hat`

Ngay ky : 2026-08-27

Moc     : sau `a595fb4` (Lesson 23.25 dong), TRUOC khi mo Lesson 23.26

Loai    : SUA PHAM VI mot ket luan + TIEN DANG KY hai phep phan xu

Commit  : `a595fb4` (tag `lesson-23-25-complete`)

## 1. Vi sao amendment nay ton tai

Lesson 23.25 dong voi 8/8 HIT va quyet dinh `D3`. Kiem toan sau do tim ba van
de, deu o NEN cua uoc luong, khong o phan tinh toan.

### V1 -- 16 cap NULL KHONG dong nhat

`b_hat = +0.1097` la trung binh cua mot phan phoi LUONG CUC. Do lai:

```text
ho theo thang do    n    r trung binh      sd       khoang
fast-fast           6      +0.0163      0.0166   [-0.011, +0.036]
slow-fast           8      +0.0527      0.0973   [-0.014, +0.265]
slow-slow           2      +0.6181      0.0276   [+0.599, +0.638]

spread giua ho = 0.6018   vs   sd gop toan bo = 0.2104
ngoai lai (>3 MAD): vC-vD (+0.6376), uA-uB (+0.5986), bd-vC (+0.2654)
```

`goodness_of_fit` CHI soi 12 cap CO CAU TRUC, nen no VE NGUYEN TAC khong the
thay cau truc nay. `M-248` = "khong co cau truc" la mot AM TINH GIA: no dung
trong pham vi no nhin, va pham vi do bo sot cho cau truc lon nhat.

### V2 -- `Var(m)` bi hai phan tu chi phoi

```text
cap        day du   bo uA-uB va vC-vD   % do HAI cap giai thich
m(P1,P2)   0.6940        1.0128                  96%
m(P1,P3)   0.7068        1.0061                  98%
m(P1,P4)   0.6506        1.0626                  85%
m(P2,P3)   0.5417        0.9538                 111%
m(P2,P4)   0.7013        1.0006                 100%
m(P3,P4)   0.6666        0.9853                 105%
```

Bo DUNG hai phan tu ma tran thi ti so ve **0.95 .. 1.06**, tuc DON VI. Va co
che cua hai cap do (chung diem cuoi) NGUOC DAU voi co che cua `omega` (chung
duong). Goi ket qua do la "dinh luong `L46`" la GAN SAI NGUYEN NHAN -- lop bai
hoc `K4` ("khong bao gio bao cao so gop khi mot phan tu chi phoi").

### V3 ★ -- `n_eff = 393` la mot so GOP, va no sai theo CAU TRUC

Do lai theo tung cap:

```text
tau theo link:  ac 2.75  ad 4.17  bc 2.74  bd 2.76      <- NHANH
                uA 20.03 uB 27.35 vC 20.03 vD 27.67     <- CHAM

12 cap CO CAU TRUC, n_eff = n_run * n_samples * dt / (2 * tau_max):
    ac-vC 44.9   ad-vD 32.5   bc-vC 44.9   bd-vD 32.5
    uA-ac 44.9   uA-ad 44.9   uA-vC 44.9   uA-vD 32.5
    uB-bc 32.9   uB-bd 32.9   uB-vC 32.9   uB-vD 32.5

SO CAP CHI GOM HAI LINK NHANH:  0 / 12
```

Day la he qua TAT DINH cua topology: `k_lm > 0` doi hai link chung duong;
moi link LOI (`ac`, `ad`, `bc`, `bd`) thuoc DUNG MOT duong, nen hai link loi
khac nhau KHONG BAO GIO chung duong. Vay moi cap co cau truc phai chua it
nhat mot link BIEN.

```text
=> CAU TRUC mua do chinh xac sqrt(5), nhung TOPOLOGY bat tra bang `tau` cua
   link cham nhat. Hai dieu do khong bu duoc cho nhau.

sum(w * k^2) = 175.70  ->  sd(omega_hat) = 0.0754  ->  CI95 = +-0.1479
                           so voi +-0.0389 da bao cao: RONG GAP 3.8 LAN
```

### V4 -- mot dau hieu da bi bo qua o 23.25

`omega_hat = +0.085248` nam **NGOAI** CI95 bootstrap cua chinh no
`[-0.031371, +0.047471]`, lech **3.70 sd** so voi tam CI. Mot uoc luong diem
nam ngoai CI cua chinh no la dau hieu bootstrap bi LECH VI TRI, khong chi hep.
Dau hieu do co san trong artifact 23.25 va da khong duoc doc. Ghi `L143`.

## 2. ★ SUA PHAM VI ket luan cua Lesson 23.25 (`NT 49`: doi nhan, khong rut)

```text
RUT LAI  : moi phat bieu ve DAU cua `omega_hat`, va moi phat bieu dung
           `sd = 0.0209` tu block bootstrap.

THAY BANG: "|omega| <= 0.15 voi do tin cay 95%. DAU cua omega_hat KHONG xac
            dinh duoc: tho +0.0852, hieu chinh -0.0828, co trong so +0.0820
            -- ca ba trong +-1.2 sd cua 0."

GIU NGUYEN: ket luan DINH TINH "testbed la omega ~ 0 dung nhu du bao co che
            tu `traffic_v7.LOAD_CHANNELS`". Ket luan nay KHONG doi; chi do
            CHAT CHE cua no doi.
```

Ba uoc luong voi `sd` dung:

| uoc luong | gia tri | so sd | phan biet voi 0? |
|---|---:|---:|:--:|
| tho | +0.0852 | +1.13 | KHONG |
| tru `b_hat` | -0.0828 | -1.10 | KHONG |
| co trong so (WLS) | +0.0820 | +1.09 | KHONG |

`M-245` GIU nhan HIT (do tren bien the THO, dai `[0.00, 0.15]`, `+0.0852` nam
trong). Nhung phai ghi chu: voi `sd` dung, dai `[0, 0.15]` gan bang do rong
CI (`+-0.1479`), nen `M-245` gan nhu KHONG THE MISS -- mot du doan CONG SUAT
THAP. Ghi `L144`.

## 3. ★ KHAI BAO: mot phan ket qua DA duoc tinh TRUOC khi ky

Truoc khi ky, cac dai luong sau DA duoc tinh tren `link_corr_matrix.json`
(artifact da co, khong can CSV): phan tang tap NULL theo thang do, `n_eff`
theo cap, `sd(omega_hat)` dung, `omega_hat` co trong so, va do nhay `Var(m)`
khi bo hai cap ngoai lai.

```text
=> Chung mang nhan [MO TA -- DA TINH TRUOC KHI KY].
=> KHONG cap ma `M-*` co cham diem.
=> Bao cao con so, KHONG dem vao so diem du doan.
```

Dieu THAT SU chua biet tai thoi diem ky la **Test A** va **Test B** (muc 4):
chua mot file `rho_measured_*.csv` nao duoc doc theo TUNG RUN, va chua mot
file `rho_offered_*.csv` nao duoc mo. Do la cho ky du doan.

Cung khuon voi `A076` muc 2.

## 4. Du doan CO CHAM DIEM -- dieu that su chua biet

`r(uA,uB) = +0.599` va `r(vC,vD) = +0.638` co HAI gia thuyet canh tranh:

```text
H1  CONFOUND CHUNG DIEM CUOI (that)
    `traffic_v7.LOAD_CHANNELS`: uA = hsrc->hA, uB = hsrc->hB (chung HOST
    NGUON); vC = hC->hdst, vD = hD->hdst (chung HOST DICH). Nghen CPU/NIC
    tai endpoint lam hai luong cham cung luc.
    LO HONG cua H1: `ac`/`ad` cung chung `hA`, `bc`/`bd` cung chung `hB`, ma
    `r(ac,ad)` va `r(bc,bd)` deu ~ +0.03. H1 chua giai thich duoc vi sao
    `hsrc`/`hdst` khac `hA`/`hB`.

H2  HIEN VAT CHUOI QUA NGAN
    Dung bon link cham nhat (`tau` 20-28 s) trong run chi dai 119.8 s
    = 4.3 `tau`. `n_eff` cua cap slow-slow ~ 32 -> `sd(r) ~ 0.18`.
```

| ID | Dai luong | Nguon | Dai khoa | Do | KQ |
|---|---|---|---|---|---|
| M-252 ★ | `sd` cua `r(uA,uB)` qua 15 run rieng le | [CO CHE] | H1: < 0.30 ; H2: > 0.45 | ___ | ___ |
| M-253 ★ | so run trong 15 co `r(uA,uB) < 0` | [CO CHE] | H1: 0-1 ; H2: >= 3 | ___ | ___ |
| M-254 ★ | `r(uA,uB)` tren `rho_offered_clean_*.csv` | [CO CHE] | H1: \|r\| < 0.15 ; H2: ~ +0.6 | ___ | ___ |
| M-255 | `sd` cua `r(ac,ad)` qua 15 run (doi chieu NHANH) | [NGOAI SUY] | 0.05 - 0.25 | ___ | ___ |
| M-256 ★ | `SNR_dec` trung vi khi BO 2 cap ngoai lai | [NGOAI SUY] | 0.28 - 0.42 | ___ | ___ |
| M-257 ★ | quyet dinh `D` co DOI khi bo 2 cap ngoai lai? | [CO CHE] | KHONG doi (van `D3`) | ___ | ___ |

`M-252`/`M-253` la phep phan xu CHINH: neu `r(uA,uB)` on dinh qua 15 run DOC
LAP thi do la mot HIEU UNG THAT; neu no vang loan va co ca gia tri am thi do
la NHIEU cua chuoi ngan. So lieu DA NAM trong duong `pooled_corr`, chi chua
bao gio duoc in ra.

`M-255` la doi chieu: `ac`/`ad` la hai link NHANH cung chung host `hA`. Neu
`sd(r(ac,ad))` cung lon thi phep do per-run co van de RIENG, va `M-252` khong
dien giai duoc.

DIEU KIEN KHA THI (`A073` R5): moi du doan deu fire duoc theo hai chieu.

## 5. Kich ban thi hanh -- ky TRUOC

```text
K1  H1 thang (`M-252` < 0.30 VA `M-254` |r| < 0.15)
    -> confound CHUNG DIEM CUOI la THAT.
    -> Ghi `L142` va dua vao Threats to Validity.
    -> `Var(m)_do/don_vi = 0.54-0.71` la THAT nhung KHONG phai hieu ung cua
       `omega`. Doi nhan trong `56-link-corr-matrix.md` va `CLAIMS.md`.
    -> Lesson 23.26 PHAI thiet ke lai `LOAD_CHANNELS` de moi link co endpoint
       RIENG, hoac chap nhan va DO LUONG confound nay.

K2  H2 thang (`M-252` > 0.45 HOAC `M-253` >= 3)
    -> `+0.62` la nhieu cua chuoi ngan.
    -> `Var(m)_do/don_vi` KHONG dung duoc; phai bao cao ban BO 2 cap.
    -> Lesson 23.26 PHAI keo dai run: `duration >= 15*tau_max` = 415 s (thay
       vi 120 s), neu khong thi moi thong ke lien quan link BIEN deu vo nghia.
       => day la mot RANG BUOC THIET KE cho 23.26, phai biet TRUOC khi tieu
          ba tuan may.

K3  Khong ro (`M-252` trong [0.30, 0.45])
    -> bao cao CA HAI kich ban song song trong paper; khong chon.
    -> Lesson 23.26 keo dai run (re hon viec sua topology) de phan xu.
```

Khong kich ban nao duoc dien giai lai sau khi nhin so.

## 6. Doi chung

```text
NC-25b-1   chay hai lan cung dau vao -> ket qua giong bit-for-bit
NC-25b-2 ★ ham moi KHONG lam doi bat ky truong nao cua `link_corr_matrix.json`
           da co: `T0`..`T6` va `PC_25_1` giu nguyen BIT-FOR-BIT; moi ket qua
           moi vao KHOI MOI `T7_null_audit`.  Ly do: `NT 49`.
PC-25b-1 ★ `null_homogeneity` cho mot ma tran DONG NHAT nhan tao (moi cap NULL
           = +0.05 + nhieu nho) -> PHAI ket luan `heterogeneous = False`
PC-25b-2 ★ cho ma tran co DUNG hai cap NULL bi bom len +0.6 -> PHAI ket luan
           `heterogeneous = True` va liet ke DUNG hai cap do
```

## 7. Gate

| ma | noi dung | nguong |
|---|---|---|
| G23-312 ★ | `M-252/253/254/255`: phan xu H1 vs H2 | nhi phan |
| G23-313 | `T7_null_audit` day du + `n_eff` theo cap + `sd` dung | bat buoc |
| G23-314 ★ | `M-256/257`: quyet dinh `D` ben vung khi bo 2 cap ngoai lai | nhi phan |

Ngan sach RIENG 3 gate, KHONG lay tu ngan sach cua 23.26.

## 8. Sua ma nguon duoc phep

```text
(a) `measurements/link_corr_matrix.py`     -- CHI THEM ham, KHONG sua ham cu
(b) `measurements/link_pair_stability.py`  -- MOI (Test A + Test B)
(c) `test/test_link_corr_audit.py`         -- MOI
KHONG sua: cac ham `T0`..`T6` hien co (`NC-25b-2`).
```

## 9. Pham vi va gioi han

```text
N1  `TIMESCALE_SLOW_S = 10.0` phan loai link NHANH/CHAM. Do duoc: loi
    2.74-4.17 s, bien 20.03-27.67 s. Khe ho rong ~5 lan nen nguong 10.0 nam
    giua va KHONG nhay cam. HANG SO KHOA, khong phai co dong lenh.

N2  `n_eff = n_run * n_samples * dt / (2*tau_max)` la cong thuc AR(1) chuan
    cho trung binh; no la mot XAP XI cho `r`. No co the LAC QUAN vi `r` hoi
    tu cham hon trung binh. Nen `sd = 0.0754` van co the la CAN DUOI.

N3  `rho_offered_*.csv` lay mau o `dt = 0.01 s` (12000 mau) con
    `rho_measured_*.csv` o `dt = 0.2 s` (599 mau). Test B so SU TON TAI va
    DO LON cua `r`, KHONG so `n_eff` giua hai nguon.

N4  Lesson nay KHONG do moi tren Mininet. Moi ket luan gioi han o chien dich
    23.8.
```

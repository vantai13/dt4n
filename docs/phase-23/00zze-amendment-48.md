# AMENDMENT 23-48 -- Rut co che "d lech phai", sua dac ta selfcheck, khoa Z_EDGES

Ngay ky : 2026-08-22
Tag     : amendment-48
Lesson  : 23.19 Task B (sua) + Task D (khoa canh bin)

## 1. RUT co che "d_transport lech phai" (amendment 23-47 muc 2)

Amendment 23-47 quy lech trung vi `7.929 ms` cho viec `d_transport` la bien
ngau nhien lech phai (`skew +4.045`), dan bang chung `corr = +0.9637` giua
lech phai cua AoI theo link va cua `d_transport` theo link.

**Co che do SAI, va bi loai bang chinh so do cua no.**

### Ngan sach phuong sai khong con cho

```text
Var(z) quan sat        = 20927.80 ms^2   (sd 144.664)
Var(phase) = T^2/12    = 20857.69
Var(alpha)             =    94.08
                         ─────────
tong hai thanh phan    = 20951.77
CHO CON LAI cho Var(d) =   -23.97        <- AM
```

### Va skew truyen theo LUY THUA BA

```text
gamma_X = gamma_D * sigma_D^3 / sigma_X^3

de dat mean - median = 7.929 ms voi gamma_D = 4.045:
    gamma_z can  = 3 * 7.929 / 144.664 = 0.1644
    sigma_d can  = 49.74 ms
    => sd(z) phai = sqrt(20857.7 + 94.1 + 2474) = 153.06 ms
       QUAN SAT                                 = 144.66 ms    MAU THUAN +8.39 ms

nguoc lai, voi sigma_d trong ngan sach:
    sigma_d =  3 ms -> mean-median ~ 0.0017 ms   (thieu ~4700 lan)
    sigma_d =  5 ms -> mean-median ~ 0.0081 ms   (thieu ~1000 lan)
    sigma_d = 10 ms -> mean-median ~ 0.0644 ms   (thieu  ~120 lan)
```

**Cong mot Uniform rong `144 ms` nghien nat moi skew cua mot thanh phan hep,
du `gamma_D` bang 4 hay bang 40.**

`corr = 0.9637` tren 8 diem cho biet CUNG CHIEU, khong cho biet CUNG DO LON.
Do la cai bay: mot tuong quan cao van tuong thich voi mot co che sai ba bac
do lon. Bai hoc ghi lai: **tuong quan khong bao gio thay duoc ngan sach.**

## 2. SUA DAC TA SELFCHECK -- va TU CHOI cach sua bang `sigma_d`

Ban ra soat de xuat cong `sigma_d = 3.32 ms` vao dai tien doan, va khi do
`M-110` PASS 4/4. **Khong nhan cach sua do.**

```text
d duoc uoc luong bang  d = mean_quan_sat - T/2  tren CHINH du lieu do.
=> mo hinh khop mean THEO CAU TAO.
=> dich `d` mot luong x lam dich CA mean cua mo hinh, ma mean da bi ghim
   vao mean quan sat. Bat dinh cua `d` TUONG QUAN HOAN TOAN voi mean quan sat.
=> cong no vao dai la DEM HAI LAN, va no lam MOI thong ke PASS mot cach gia tao.
```

Doi chieu ba cach dac ta, cung 200 chien dich mo phong:

```text
                                p05        p50        p95
A  dai tho                     TRONG   TRONG(1.61)  NGOAI(2.26)
B  cong sigma_d (de xuat)      TRONG   TRONG(1.32)  TRONG(1.64)   <- moi thu PASS
C  chuan hoa theo mean         TRONG   NGOAI(4.10)  NGOAI(4.03)   <- DUNG
```

Dac ta DUNG la **C**: so `(phan vi - mean)`. Trong dai luong do `d` TRIET
TIEU chinh xac, nen bat dinh cua no khong con lien quan -- khong can cong,
khong duoc cong.

Va nhu ban ra soat neu dung o muc 3: `mean` **khong phai mot phep kiem**.
Chuan hoa theo mean loai bo tautology do mot cach TU DONG.

```text
=> M-110 bao cao 1/3 tren {p05, p50, p95}, KHONG phai 2/4 hay 4/4.
```

## 3. L35 -- phan du hinh dang, co che CHUA BIET

```text
L35  Phan bo z quan sat lech phai so voi mo hinh
     (d + alpha + Uniform[0,T], quan sat qua probe khoa):
         p50 - mean : quan sat -7.93 ms vs dai [-3.35, +3.13]   4.10 sigma
         p95 - mean : quan sat 216.53 ms vs dai [221.58, 228.51] 4.03 sigma
     Da LOAI bon co che:
         alpha                 -> chung minh dai so (amendment 23-46 muc 2)
         nghich ly kiem tra    -> T_eff CV = 0.0046, chi 0.29 ms
         luoc lay mau          -> dai tien doan lam dung, +/-2 ms
         d lech phai           -> ngan sach phuong sai, muc 1 tren
     CO CHE CHUA BIET. Do lon: ~8 ms tren trung vi = 1.6% cua T.
     Doi chieu: sua d tu 51 -> 116 ms la mot hieu ung 65 ms, lon hon 8 lan.
     KHONG duoc dieu chinh mo hinh de che phan du nay. Ghi va di tiep.
```

## 4. Khoa `Z_EDGES` (Task D)

### Nguyen tac chon -- khoa TRUOC khi nhin `s(z)` hay `q_hat`

```text
- theo TU PHAN VI cua phan bo z MO HINH (khong phai cua score)
- giu 4 bin de so duoc voi v2
- lam tron 1 ms
- canh NGOAI mo rong de phu ca CI cua d (+/-6.5 ms), vi canh chi phu diem
  uoc luong se lam mat hang neu d duoc chinh lai sau nay
- KHONG duoc dieu chinh sau khi thay s(z) hay q_hat
```

### Bo canh

```text
Z_EDGES_V7 = (0.100, 0.241, 0.366, 0.491, 0.641)   [giay]

  B0 [100, 241) : 25.0071%   z_tb 178.1 ms
  B1 [241, 366) : 24.9875%   z_tb 303.5 ms
  B2 [366, 491) : 24.9852%   z_tb 428.5 ms
  B3 [491, 641) : 25.0203%   z_tb 553.9 ms
  ngoai dai     :  0.000000%
```

Canh trong (241, 366, 491) la tu phan vi. Canh ngoai noi rong tu
`(0.107, 0.634)` -- bien thuc cua z voi d diem uoc luong -- ra
`(0.100, 0.641)` de phu ca `d` o hai dau CI. Noi rong nay **khong doi ty
trong bin** (kiem: giong het den chu so thu tu) vi khong co khoi luong nao
o ngoai.

### Bo canh CU vo hoan toan tren truc moi

```text
Z_EDGES_PRIMARY = (0.055, 0.10, 0.20, 0.30, 0.5501) ap len z moi:
  B0 [ 55, 100) :  0.0000%   <- RONG => q_hat = +inf, n_g < 9, pipeline gay
  B1 [100, 200) : 16.8110%
  B2 [200, 300) : 19.9900%
  B3 [300, 550) : 49.9897%
  ngoai dai     : 13.2093%   <- MAT TRANG
```

## 5. Du doan -- dien TRUOC khi chay Task E

```text
ID       Dai luong                                        Nguon      Dai khoa       KQ
--------------------------------------------------------------------------------------
M-114    ty trong bin thuc te lech thiet ke 25%           [MO TA]    < 2 diem %     __
M-115 *  ty le hang ngoai dai                             [CO CHE]   = 0            __
M-116 *  q_hat(B3)/q_hat(B0) khop do gian z^0.431         [CO CHE]   1.62 +/- 25%   __
M-117 *  NC-E1: d=0.051, T=0.5, U0, phase0=-d -> calib_set
         BIT-EXACT ban cu                                 [CO CHE]   diff = 0       __
M-118 *  NC-E2: corr(z_uA - alpha_uA, z_ac - alpha_ac)    [CO CHE]   = 1 (dai so)   __
M-119 *  PC-E1: dung instrument_mode trong pipeline ->
         ty trong bin lech manh                           [CO CHE]   >= 1 bin lech
                                                                     > 5 diem %     __
M-120 *  PC-E2: giu canh CU tren z moi -> B0 RONG         [CO CHE]   0.0%           __
```

## 6. KHONG duoc lam

```text
- KHONG doi Z_EDGES_V7 sau khi nhin s(z) hoac q_hat.
- KHONG cong bat dinh tham so vao dai selfcheck khi tham so do duoc fit tu
  chinh thong ke dang kiem (muc 2).
- KHONG dieu chinh mo hinh de che L35.
```

Chu ky: ____________

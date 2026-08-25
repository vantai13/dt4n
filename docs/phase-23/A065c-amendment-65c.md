# AMENDMENT 23-65c -- Dai van hanh hop le cua V-S theo `kappa`

Ngay ky : 2026-08-25
Lesson  : 23.22 vong hai
Loai    : TIEN DANG KY MOT DU DOAN MU (khong them mot dong code nao)
Moc     : sau `abfeb16`, TRONG khi `taxonomy_audit` vong hai dang chay,
          va TRUOC khi tac gia nhin bat ky output nao cua lan chay do

## 0. Disclosure -- vi sao van la du doan MU

Lan chay vong hai bat dau luc commit `abfeb16` va dang chay. Amendment nay
duoc ky khi log moi in DUNG MOT dong (`[MAIN] poisson@0.925`) va **chua mot
gia tri nao cua lan chay do duoc doc**.

Du lieu de cham `M-192` DA NAM SAN trong lan chay do -- `min_blocks_at_final_qhat`
duoc noi vao TUNG hang cua `variant_sweep` o commit `abfeb16`, tuc cho ca luoi
`kappa = (0, 0.25, 0.50, 1.00, 2.00)` tren 12 cell. Khong can chay them gi.

Cai DA XEM (tu smoke `n_boot=60`, artifact vut o `/tmp`, khong vao `results/`):

```text
poisson@0.925  kappa=1  min_blocks_at_final_qhat = 51
poisson@0.850  kappa=1  min_blocks_at_final_qhat = 80
h2@0.700       kappa=1  min_blocks_at_final_qhat = 182
kappa=2        ca ba suy bien ngay vong 0 -> min_blocks = None
```

CHUA XEM: gia tri o `kappa = 0.25` va `0.50` o BAT KY cell nao; gia tri o
9 cell ROBUSTNESS; bat ky gia tri nao cua lan chay `n_boot=2000`.

## 1. Vi sao dai nay quan trong -- ngan sach mau cua V-S

Do duoc tren `poisson@0.925` (cell CHINH), tai diem van hanh `kappa = 1`:

```text
V-M  qhat hieu chuan tren TOAN BO hang calib
     16 o, n_eff ~ 457 block moi o     ->  level(457) = 0.969365   BINH THUONG

V-S  qhat hieu chuan tren TAP DUOC CHON
     4 o,  n_eff = 51 block o thua nhat ->  level(51)  = 1.000000   MAX MAU

==> tai diem van hanh, V-M co 9.0x nhieu block hieu dung hon V-S cho moi
    phan vi -- DU V-M co gap BON so o.
```

### 1.1. Va day la cho `H-B` KHONG ap dung duoc

```text
H-B  chia theo TAXONOMY gan nhu mien phi o tang block, vi mot block trai qua
     moi gia tri z va m_hat nen no cham gan nhu MOI o
     (block_touch_ratio 0.873..0.915).   -> DUNG cho V-M.

     NHUNG V-S khong chia theo taxonomy. No chia theo TAP DUOC CHON, va tap
     duoc chon KHONG cham moi block -- no CO LAI theo kappa.
     -> H-B KHONG ap dung cho V-S.
```

Cung mot lap luan cho hai ket luan nguoc nhau, tuy CHIEU chia. Ca hai thu tuc
deu tra mot khoan "phi dieu kien hoa"; chung chi tra bang HAI DONG TIEN khac
nhau:

```text
V-M  tra bang SO O      16 o, nhung moi o giu ~457 block
V-S  tra bang TAP MAU    4 o, nhung chi ~51 block o o thua nhat
```

Tai `kappa = 1` tren cell chinh, **hoa don cua V-S CAO HON**.

## 2. M-192   [KY THAT -- du doan MU]

```text
M-192  Voi bien the V-S, `min_blocks_at_final_qhat` GIAM DON DIEU theo `kappa`,
       va `kappa` LON NHAT ma no con >= 59 (san on dinh, `L93`) la:

           tren `poisson@0.925`      ->  du doan thuoc {0.25, 0.50}
           trung vi tren 8 cell A=True -> du doan thuoc {0.25, 0.50}
```

```text
[CO CHE]  kappa tang => nguong chap nhan chat hon => tap chon CO LAI
          => so block trong o thua nhat GIAM. Tinh DON DIEU la tat dinh.
          Cai duoc DOAN la NGUONG CAT, khong phai chieu bien thien.
```

Cham o 8 cell co `A = True` (tieu chi A, amendment 23-62). Cell `A = False`
bao cao lam doi chung am, khong dem vao mau so.

### 2.1. Quy tac doc -- ky truoc

```text
nguong cat >= 1.00   V-S dung duoc TAI diem van hanh da tien dang ky.
                     Khuyen nghi "chuyen sang selective" DUNG VO DIEU KIEN.

nguong cat thuoc     kappa = 1 NAM NGOAI vung V-S dung duoc. Khuyen nghi phai
{0.25, 0.50}         KEM DIEU KIEN ve kappa, va Task B phai chon lai diem van
                     hanh hoac chon lai thu tuc.

nguong cat = 0       V-S KHONG BAO GIO o tren san on dinh voi bat ky kappa > 0.
                     Khi do "V-S giu bao phu 12/12" hoan toan la mot phat bieu
                     ve su TU CHOI HANH DONG, khong phai ve hieu chuan.
```

Ba nhanh deu cho ket qua dung duoc.

### 2.2. Truong hop `min_blocks = None`

Khi vong lap suy bien NGAY vong 0, `q` giu nguyen ban dau -- tinh tren TOAN BO
calib (500 block), tuc **on dinh**. Ma hoa: `None` duoc doc la "tren san",
KHONG phai "duoi san". Da xu ly dung trong `qhat_at_sample_max` (`_nb is not
None and ...`), va cach doc nay duoc ghi o day de khong ai dien giai nguoc.

## 3. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-246 | M-192: `min_blocks_at_final_qhat` cua V-S giam don dieu theo `kappa` o >= 6/8 cell `A=True`; VA nguong cat tren `poisson@0.925` thuoc {0.25, 0.50} | tat/bat |

## 4. Mot tuy chon da kiem va BO -- giu Bonferroni

Vi V-S dang cham san, da kiem xem doi hieu chinh da boi co cuu duoc khong:

```text
                alpha_each      san hop le   san on dinh
bonferroni      0.03333333          29           59
sidak           0.03451062          28           57
```

Sidak noi san on dinh tu 59 xuong 57. **Khong dang**: `min_blocks = 51` van
duoi CA HAI. Va doi hieu chinh giua chung se lam moi so cua Phase 22 / 21R
khong so duoc nua.

**Giu Bonferroni.** Ghi lai o day de sau nay khong ai phai thu lai.

## 5. Pham vi anh huong

KHONG them mot dong code nao. `M-192` duoc cham tu du lieu DA CO trong lan
chay `abfeb16`. `G23-242` khong bi anh huong.

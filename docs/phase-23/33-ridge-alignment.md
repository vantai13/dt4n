# Lesson 23.21c -- Song nui trung nguong noi sinh: S14 tro thanh do duoc

Ngay    : 2026-08-23
Khoa boi: `00zzq-amendment-54.md` (tag `amendment-54`, commit `f22f711`)
Artifact: `results/PENDING/phase-23/t_loss_fine.json`,
          `results/PENDING/phase-23/rho_grid_main.json`,
          `results/PENDING/phase-23/rho_grid_sigma_fixed.json`

## 1. Ket qua mot dong

```text
Tren luoi log 1.25x, nguong t_loss ma thu tuc TU HIEU CHUAN cu sinh ra nam
cach dinh song nui S_pivotal MEDIAN 0.22 octave (~17%), tren mot dai t_loss
trai 500 lan va tam cell doc lap. S14 khong con la mot cao buoc; no la mot
hien tuong DO DUOC.
```

## 2. Doi chieu du doan da ky

| id | dai da ky | do duoc | KQ |
|---|---|---|---|
| M-147 | median \|log2(t_endo/T*)\| <= 0.50 | **0.2216** | **HIT** |
| M-148 | >= 7/8 cell co \|log2\| <= 1.0 | **8/8** (max 0.440) | **HIT** |
| M-149 | lech dong nhat thuc tren luoi `rho` MOI <= 5e-3 | **2.07e-03** | **HIT** |
| M-150 | dinh `h2` o `rho` <= 0.625 hoac KHONG KEP DUOC | **0.625, KEP DUOC** | **HIT** |
| M-151 | dinh `poisson` o `rho` thuoc [0.775, 0.875] | **0.850, KEP DUOC** | **HIT** |
| M-152 | o `sigma` co dinh, `h2` KHONG con don dieu giam | **VAN don dieu giam** | **MISS** |
| M-153 | >= 3 cell LIVE theo CA HAI tieu chi | **4** | **HIT** |

## 3. `G23-169` / `G23-170` -- song nui trung nguong noi sinh

Luoi log he so 1.25 (32 diem, `0.0002` -> `0.2019`), mot buoc = `log2(1.25)` = 0.322.

```text
cell               t_loss_endo         T*   S_piv(T*)   log2(t_endo/T*)   kep?
poisson@0.700          0.00042    0.00031      0.9328            +0.440   CO
poisson@0.850          0.00722    0.00888      0.9014            -0.299   CO
poisson@0.925          0.02921    0.03388      0.9294            -0.214   CO
poisson@0.960          0.04791    0.05294      0.9934            -0.144   CO
h2@0.700               0.02645    0.02711      0.8966            -0.035   CO
h2@0.850               0.11026    0.12925      0.8641            -0.229   CO
h2@0.925               0.16684    0.20195      0.8910            -0.275   MUT LUOI
h2@0.960               0.19461    0.20195      0.9920            -0.053   MUT LUOI

median |log2| = 0.2216      MOT BUOC LUOI = 0.322
=> lech dien hinh nho hon MOT buoc luoi
```

Doc cho dung ba dieu:

```text
(1) `S_pivotal` tai T* nam trong [0.864, 0.993] o CA TAM cell. Nghia la o
    nguong noi sinh cua chinh no, moi cell trong "gan nhu toi da huu ich".

(2) `h2@0.925` va `h2@0.960` co T* o MUT PHAI cua luoi -> ghi "KHONG KEP DUOC"
    theo `G23-173`. `T*` cua chung la CAN DUOI, nen `|log2|` do duoc la can
    tren cua do lech that. Ket luan khong yeu di, nhung phai ghi dung.

(3) `poisson@0.700` la cell duy nhat lech DUONG (+0.440): nguong noi sinh
    CAO hon dinh. Bay cell con lai deu lech AM, tuc nguong noi sinh THAP hon
    dinh mot chut. Khong doi dau nao.
```

### Co che -- CO HOC, khong phai y do

```text
(1) t_loss_endo = phan vi ~p88-92 cua mat goi tren duong toi uu
    -> bam theo THANG DO cua phan phoi mat goi trong cell
(2) dinh S_pivotal nam o noi nguong CAT QUA than cua phan phoi
    -> cung bam theo thang do do
=> hai dai luong cung theo MOT bien tiem an. Trung nhau la TAT YEU.
```

Day la diem phai viet ro trong paper: **khong co ai gian lan, va ket qua van
bi thien lech.** Do la dang thien lech nguy hiem nhat, vi no song sot qua moi
lan ra soat trung thuc.

## 4. `G23-171` -- dong nhat thuc dung tren du lieu MOI

```text
S_pivotal(T) = F_min(T) - F_max(T)      (dung khi truc tre TRO)

lech lon nhat tren 26 cell cua hai luoi rho MOI = 2.07e-03   (h2@0.650, sigma co dinh)
```

Da kiem NGOAI MAU: dong nhat thuc duoc phat hien tren 12 cell cua 23.21b, gio
dung tren 26 cell moi khong tham gia vao viec phat hien no.

## 5. `G23-172` -- doi chung `sigma` co dinh: confound CO that nhung KHONG lai duoc ket luan

```text
                     LUOI CHINH (a = 0.9)          DOI CHUNG (sigma = 0.020)
rho        sigma     S_pivotal                     S_pivotal
h2  0.575  0.0026      0.00093                     (khong kha thi)
h2  0.600  0.0113      0.94007                     (khong kha thi)
h2  0.625  0.0201      0.98355                       0.98374     <- trung khop
h2  0.650  0.0288      0.67240                       0.61485
h2  0.675  0.0375      0.28678                       0.07305
h2  0.700  0.0462      0.11123                       0.00155
h2  0.850  0.0480      0.00000                       0.00000
```

`M-152` **MISS**: da ky "o `sigma` co dinh, `h2` KHONG con don dieu giam". Do
duoc: no VAN don dieu giam (0.984, 0.615, 0.073, 0.0016, 0, 0, 0).

Doc cho dung -- day la MISS co gia tri:

```text
Confound `L58` CO THAT (sigma chenh 1.60 lan giua h2@0.650 va h2@0.700, va
no doi DO LON rat manh: S_pivotal(h2@0.700) tut tu 0.111 xuong 0.0016, tuc
70 lan, khi giu sigma co dinh).

NHUNG no KHONG lai duoc HINH DANG: ca hai luoi deu don dieu giam tren ho h2,
va VI TRI dinh khong doi.

=> Ket luan "vung song cua ho h2 nam o rho thap" DUNG VUNG, va gio da co
   doi chung. Truoc `G23-172` ta KHONG duoc phep viet cau do (`L58`).
```

Voi ho `poisson`, doi chung con manh hon: dinh o `sigma` co dinh cung nam
dung `rho` = 0.850 (0.9306) nhu o luoi chinh (0.8932). Vi tri dinh BAT BIEN
voi cach dat `sigma`.

## 6. `G23-173` -- hai dinh gio da KEP DUOC

```text
ho h2 (luoi chinh, gop 23.21b):
   0.575    0.600    0.625    0.650    0.675    0.700    0.850
  0.00093  0.94007  0.98355  0.67240  0.28678  0.11123  0.00000
                    ^^^^^^^ DINH, kep boi 0.600 va 0.650

ho poisson (gop 23.21 + 23.21b):
   0.700    0.750    0.775    0.800    0.825    0.850    0.875    0.900    0.925
  0.00330  0.17661  0.43917  0.59724  0.76494  0.89321  0.81274  0.32400  0.00869
                                               ^^^^^^^ DINH, kep boi 0.825 va 0.875
```

`M-142` cua 23.21b mang dau `HIT*` vi dinh nam o MUT TRAI cua luoi. Gio no da
duoc kep that su: `poisson` dinh o 0.850, co diem thap hon o CA HAI phia.

Va `L54` duoc xac nhan dinh luong: ho `h2` co dinh o `rho` = 0.625, trong khi
luoi 8 cell goc bat dau tu 0.700 -- tuc luoi goc bo lo dinh cua ho `h2` mot
khoang **12 diem phan tram** cua `rho`.

`h2@0.575` (`sigma` = 0.0026, gan mut kha thi) co `S_pivotal` = 0.00093 ->
dinh KHONG nam duoi 0.575. `L56` KHONG xay ra.

## 7. `M-153` -- bon cell song theo CA HAI tieu chi

```text
cell             regime   S_pivotal   opt_viol   in_band
h2@0.625         LIVE       0.98355     0.0112     TRUE   ***
poisson@0.850    LIVE       0.89321     0.0316     TRUE   ***
poisson@0.875    LIVE       0.81274     0.1819     TRUE   ***
h2@0.650         LIVE       0.67240     0.3290     TRUE   ***
```

Tieu chi kep cat bo HAI phia, va ca hai phia deu co nghia van hanh:

```text
BI LOAI VI opt_viol QUA THAP (< 0.01) -- "bai toan qua de":
   h2@0.600 (0.0000), poisson@0.825 (0.0056), poisson@0.800 (0.0010),
   poisson@0.775 (0.0002), poisson@0.750 (0.0000)
   Chon duong QUYET DINH, nhung bo toi uu gan nhu luon tim duoc duong dat.

BI LOAI VI opt_viol QUA CAO (> 0.50) -- "mang gan sup":
   poisson@0.900 (0.6762), h2@0.675 (0.7135)
```

Bon cell song phu CA HAI ho luu luong, va `opt_viol` cua chung trai tu 1.1%
den 32.9%. Tuyen bo xuyen-ho duoc khoi phuc, va lan nay tu tieu chi TIEN
NGHIEM co trich dan chu khong tu `err_neo > 0.05` hau nghiem.

## 8. Dieu KHONG duoc ket luan

```text
- `M-135` VAN khong dung duoc: ly do (iii) o `L57` (hai ve do duoi hai ham
  muc tieu khac nhau) chua duoc sua. Cot `err_neo` cua bang `G23-167` van la
  so NOI SINH.
- Muc 3 chung minh nguong noi sinh nam TREN song nui. No KHONG chung minh
  ket qua Phase 22/23 SAI -- no chung minh chung duoc do o diem thuan loi
  nhat cua moi cell. Do la mot phat bieu ve THIEN LECH, khong phai ve tinh
  dung sai cua tung con so.
- `S_pivotal` cao KHONG keo theo "chung nhan co gia tri" (`L55`).
```

## 9. Chua lam

```text
- Mo rong luoi T_loss qua 0.2019 de kep dinh cua h2@0.925 / h2@0.960.
- `G23-174` (test digest parquet) chua chay -> chua biet co tai dung duoc
  calib set khong -> `M-135`/`M-136` van treo.
- Duyet truc: `approved_for_live` van rong. Artifact o `PENDING/`.
```

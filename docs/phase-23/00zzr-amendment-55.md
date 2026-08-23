# AMENDMENT 23-55 -- sua dai luong vong tron, dao nghia tieu chi thu cap,
#                    va chuyen tu TRUC `rho` sang MAT PHANG `(rho, sigma)`

Ngay ky : 2026-08-23
Tag     : amendment-55
Lesson  : 23.21d
Loai    : DINH CHINH DAI LUONG + TIEN DANG KY
Prereq  : amendment-54 (`f22f711`), Lesson 23.21c (`7651f3a`)

## 0. Hai hieu chinh so voi ban thao

```text
(a) "h2@0.600 bi loai OAN" -- qua manh. Theo `V` no xep thu SAU (0.2356),
    duoi ca `poisson@0.825` (0.2897). No bi loai duoi CA HAI tieu chi.
    Cai SAI la LY DO da ghi ("bai toan qua de"), khong phai ket qua loai.

(b) Ban thao danh so `L60..L63`. So ke tiep trong repo la `L59`.
    Dung `L59..L62`.
```

## 1. Dinh chinh dai luong muc [5] cua `33-ridge-alignment.md`

`33-ridge-alignment.md` muc 3 viet:

> *"`S_pivotal` tai `T*` nam trong [0.864, 0.993] o CA TAM cell. Nghia la o
> nguong noi sinh cua chinh no, moi cell trong gan nhu toi da huu ich."*

```text
S_pivotal_at_T_star = S_pivotal(T*) = max_T S_pivotal(T)   <- CUC DAI theo DINH NGHIA
"tai nguong noi sinh" = S_pivotal(t_loss_endo)             <- MOT DIEM KHAC
```

Cau do dung gia tri TAI cuc dai de chung minh rang nguong noi sinh NAM O cuc
dai. Do la gia dinh dieu can chung minh -- lap luan VONG TRON.

**Pham vi cua loi:** chi cau tren. `M-147`
(`median |log2(t_endo/T*)| = 0.2216`) do KHOANG CACH giua hai diem, khong dinh
den gia tri tai cuc dai, nen no KHONG vong tron. Ket qua chinh cua 23.21c dung
tren `M-147` va GIU nguyen.

### Dai luong dung

```text
efficiency = S_pivotal(t_loss_endo) / max_T S_pivotal(T)
```

Do duoc (noi suy tuyen tinh tren luoi 1.25x):

```text
cell               S(T*)   S(t_endo)   efficiency   canh noi suy
poisson@0.700     0.9328      0.9178       0.9839   [0.930, 0.894]
h2@0.700          0.8966      0.8789       0.9802   [0.749, 0.897]
poisson@0.850     0.9014      0.8758       0.9716   [0.874, 0.901]
h2@0.850          0.8641      0.8178       0.9464   [0.801, 0.864]
poisson@0.925     0.9294      0.8595       0.9247   [0.828, 0.929]
h2@0.925          0.8910      0.7893       0.8859   [0.774, 0.891]
---- KHONG TIN CAY: noi suy qua BAC NHAY ----
poisson@0.960     0.9934      0.7592       0.7642   [0.500, 0.993]  <- nhay 0.49
h2@0.960          0.9920      0.8117       0.8182   [0.000, 0.992]  <- nhay 0.99
```

Tren 6 cell tin cay: `efficiency` thuoc **[0.886, 0.984]**, trung vi ~0.96.

```text
=> MENH DE DUNG VUNG, va gio duoc CHUNG MINH thay vi duoc GIA DINH:
   "Tai nguong ma thu tuc tu hieu chuan sinh ra, moi cell dat 89-98% muc huu
    ich TOI DA co the dat duoc o cell do."
```

Hai cell `@0.960` noi suy BAC NGANG qua mot buoc nhay -- do la lop loi da cho
ra `L34`, `L35`, `M-133`, lan thu TU. Quy tac o amendment 23-53 muc 8 da co
nhung chua duoc ap vao cho nay.

Han che moi: `L60`.

## 2. Tieu chi thu cap `opt_viol in [0.01, 0.50]` bi DAO NGHIA

```text
Thoi NOI SINH  : opt_viol bi EP = 0.15 bang chia doi
                 -> dai [0.01, 0.50] chi la phep kiem VE SINH ("bo giai hoi tu?")
Thoi NGOAI SINH: opt_viol la PHEP DO TU DO = P(ORACLE vi pham)
```

Nguong duoc chuyen qua nguyen xi qua mot lan DOI DINH NGHIA. Cung lop loi voi
`S12` (truc tuoi suy chu khong do), nhung lan nay xay ra tren mot TIEU CHI
thay vi tren mot BIEN.

Hau qua doc duoc tu du lieu:

```text
h2@0.600   S_pivotal = 0.9401   opt_viol(ORACLE) = 0.0000
           P(vi pham | chon NGAU NHIEN) = mean_paths_violating/4 = 0.2356

=> "opt_viol ~ 0" KHONG co nghia "bai toan de". No co nghia ORACLE THANH CONG.
   opt_viol ~ 0 va S_pivotal ~ 0   -> TAM THUONG (khong ai vi pham)
   opt_viol ~ 0 va S_pivotal ~ 0.94 -> SLA DAT DUOC, nhung CHI KHI chon dung
```

```text
QUYET DINH: `M-153` GIU nguyen 4 cell da bao cao.
            RUT cau giai thich "opt_viol < 1% la bai toan qua de" khoi
            `33-ridge-alignment.md` muc 7 -- cau do SAI.
            Ket qua loai `h2@0.600` VAN dung (theo `V` no xep thu 6), nhung
            LY DO da ghi la sai.
```

Han che moi: `L61`.

### Truc thu hai MOI -- gia tri cua quyet dinh `V`

```text
V = P(vi pham | chon NGAU NHIEN) - P(vi pham | ORACLE)
  = mean_paths_violating / K  -  opt_viol_rate
```

`V` bang 0 o CA BA dau suy bien: tam thuong, sup, va "oracle cung thua".

Do duoc tren 19 cell hien co, TOP-4 theo `V`:

```text
poisson@0.875  0.4868      h2@0.625       0.4366
h2@0.650       0.4475      poisson@0.850  0.4154
```

**Trung DUNG bon cell ma `M-153` da chon.** Tieu chi da ky cho KET QUA DUNG
bang LY DO SAI. Tren `topology_v7` chung trung nhau; tren topology khac khong
co gi bao dam.

## 3. Doi chung `sigma` -- hai dieu chua noi duoc

```text
(a) Dinh `h2` o luoi doi chung nam tai `rho` = 0.625 = MUT TRAI cua luoi.
    Theo `G23-173` -> phai ghi "KHONG KEP DUOC", chua duoc goi la dinh.
    `sigma` = 0.020 khong kha thi duoi 0.625 (`sigma_max(0.600)` = 0.0126).
    => can doi chung THU HAI o `sigma` = 0.010.

(b) "khong lai duoc HINH DANG" dung cho VI TRI dinh `poisson`, SAI cho DO RONG:
        so cell LIVE     11 -> 4
        poisson@0.750    0.17662 -> 0.00016    tut 1104 lan
        h2@0.700         0.11123 -> 0.00155    tut   72 lan
        poisson@0.800    0.59724 -> 0.08872    tut  6.7 lan
        poisson@0.850    0.89321 -> 0.93055    TANG 1.04 lan
    => phan lon cai lam cac cell "song" o luoi chinh la DO BIEN DONG `sigma`,
       khong phai MUC tai `rho`.
    => CAM viet "vung song la `rho` thuoc [x, y]" o dang MOT CHIEU.

(c) NC duoc mien phi: `h2@0.625` co `sigma(a=0.9)` = 0.02006 ~ 0.020, va hai
    luoi cho 0.98355 vs 0.98374. Hai luoi CAT NHAU tai do va cho cung so --
    cong cu tu kiem chinh no. Phai ghi thanh mot `NC` rieng, khong de lan
    trong bang.
```

Han che moi: `L62`.

## 4. Vach dung cua `h2` tai `rho` thuoc [0.575, 0.600] la ARTIFACT

```text
S_pivotal  0.00093 -> 0.94007    nhay ~1000 lan trong MOT buoc luoi
sigma      0.00262 -> 0.01134    tang 4.3 lan
sigma_max(rho) = 0 voi moi rho <~ 0.565
```

Can duoi cua "vung song ho `h2`" TRUNG voi cho `sigma_max(rho)` roi khoi 0.
Do la bien cua THAM SO HOA mo hinh, khong phai bien cua MANG.

`33-ridge-alignment.md` ket luan "`L56` khong xay ra" -- dung ve hinh thuc.
Ket luan DAY DU phai la: dinh `h2` khong nam duoi 0.575, nhung LY DO la o do
`sigma ~ 0` nen MOI duong gan nhu giong het nhau. Neu tham so hoa `sigma`
khac di, can duoi se dich.

Han che moi: `L59`.

## 5. Doi tuong nghien cuu doi: TRUC `rho` -> MAT PHANG `(rho, sigma)`

```text
Luoi chinh (a = 0.9)        la MOT DUONG cong tren mat phang
Doi chung (sigma = 0.020)   la MOT DUONG NGANG
Hai duong CAT NHAU tai h2@0.625 -- va o do chung cho cung so (muc 3c)

Ca hai deu khong mo ta duoc MIEN.
```

## 6. Du doan -- DIEN TRUOC KHI CHAY

| id | dai luong | loai | dai da ky | do duoc | KQ |
|---|---|---|---|---|---|
| M-154 | trung vi `efficiency` tren 8/8 cell sau luoi cuc bo | CO CHE | >= 0.90 | | |
| M-155 | so cell co `efficiency` >= 0.85 | CO CHE | >= 7/8 | | |
| M-156 | dinh `h2` o doi chung `sigma` = 0.010, `rho` = | NGOAI SUY | thuoc [0.60, 0.65] | | |
| M-157 | ty le o SONG tren luoi 2D `(rho, sigma)` | NGOAI SUY | thuoc [0.15, 0.50] | | |
| M-158 | mien song tren luoi 2D co LIEN THONG khong | CO CHE | CO | | |
| M-159 | dinh cua `V` tren luoi 2D trung dinh cua `S_pivotal` | CO CHE | KHONG trung | | |
| M-160 | Spearman(`t_endo`, `T*`) tren 8 cap, luoi min | CO CHE | >= 0.95 | | |

Ghi chu:

```text
M-159  da ky "KHONG trung" co chu dich. `S_pivotal` do CAC DUONG KHAC NHAU
       BAO NHIEU; `V` do CHON DUNG LOI BAO NHIEU. Chung khac nhau (`L55`),
       nen dinh cua chung KHONG co ly do gi phai trung. Neu chung TRUNG thi
       `L55` yeu di va phai ghi lai.

M-156  neu dinh lai nam o MUT luoi -> "KHONG KEP DUOC" (`G23-173`), khong
       duoc ghi la dinh.
```

## 7. Gate

| id | noi dung | nguong |
|---|---|---|
| G23-175 | `efficiency` thay `S_pivotal_at_T_star` trong MOI phat bieu ve song nui | bat buoc |
| G23-176 | luoi cuc bo 1.05x cho `poisson@0.960` va `h2@0.960` truoc khi bao cao `efficiency` cua chung | bat buoc |
| G23-177 | doi chung `sigma` = 0.010 kep dinh `h2` HAI phia | bat buoc |
| G23-178 | NC `h2@0.625` (hai luoi cat nhau) bao cao RIENG | bat buoc |
| G23-179 | luoi 2D `(rho, sigma)`, toi thieu 8x8, ca hai ho | bat buoc |
| G23-180 | `V` tinh va bao cao cho MOI cell da do | bat buoc |
| G23-181 | Spearman(`t_endo`, `T*`) vao `CONSTANTS.md` (`K07`) + test ghim | bat buoc |
| G23-182 | truong `M148_*` doi ten cho khop dinh nghia; them `n_within_one_grid_step` | bat buoc |

## 8. Han che moi

```text
  L59  Can duoi vung song ho `h2` TRUNG cho `sigma_max(rho)` roi khoi 0
       (`rho` ~ 0.565). Do la bien cua THAM SO HOA mo hinh, khong phai bien
       cua MANG. Neu tham so hoa `sigma` khac di, can duoi se dich.
  L60  `efficiency` cua `poisson@0.960` va `h2@0.960` duoc noi suy BAC NGANG
       qua mot buoc nhay ([0.500, 0.993] va [0.000, 0.992]) -> VO NGHIA cho
       toi khi co luoi cuc bo. Lop loi `L34`/`L35`/`M-133`, lan thu TU.
  L61  Tieu chi `opt_viol in [0.01, 0.50]` ke thua tu thoi NOI SINH, khi
       `opt_viol` bi ep = 0.15 va dai do chi la phep kiem VE SINH. Duoi SLA
       ngoai sinh y nghia da DAO: `opt_viol` thap = ORACLE THANH CONG, khong
       phai "bai toan de". `M-153` dung KET QUA nhung sai LY DO.
  L62  Do rong vung song theo `rho` CO LAI ~3 lan khi giu `sigma` co dinh
       (11 cell LIVE -> 4). Phat bieu MOT CHIEU ve vung song la KHONG DAY DU;
       doi tuong that la mot MIEN trong mat phang `(rho, sigma)`.
```

## 9. Dieu KHONG lam

```text
- KHONG rut ket luan chinh cua 23.21c: `M-147` khong vong tron (muc 1).
- KHONG doi `M-153` (van 4 cell); chi RUT cau giai thich sai.
- KHONG bao cao `efficiency` cua hai cell @0.960 truoc khi co luoi cuc bo.
- KHONG viet "vung song la `rho` thuoc [x,y]" duoi dang mot chieu.
```

So ke tiep: `L63`, gate so 183, `M-161`, `K08`.

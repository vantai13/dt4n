# 43 -- Task A0: do lai co so truc `m_hat`, va ba du doan bi bac bo

Ngay      : 2026-08-24
Lesson    : 23.22 (Task A0 + A)
Amendment : `A064-amendment-64.md`  (ky TRUOC, tag `lesson-23-22-prereg` = `7c23151`)
Artifact  : `results/LIVE/phase-23/taxonomy_audit.json`
Chay      : 12 cell, `n_boot = 2000`, 3 gio 03 phut, `git_dirty = false`

## 1. Bang cham -- theo dai DA KY, khong noi mot dai nao

```text
ID      dai da ky        do duoc (3 cell CHINH)                  hit
------------------------------------------------------------------------
M-181   [440, 500]       436.4 / 457.6 / 457.5                   2/3
M-182   [1.00, 1.15]     1.1458 / 1.0926 / 1.0929                3/3   ***
M-183   [1.45, 1.70]     1.4919 / 1.5979 / 1.5978                3/3   (khong cham)
M-184   [1.05, 1.30]     1.2007 / 1.0286 / 1.1149                2/3
M-185   [1.10, 1.30]     1.1460 / 1.0157 / 1.1029                2/3
M-186   [0.50, 1.00]     1.0015 / 1.0124 / 1.0639                0/3   ***
M-187   V-N vo & V-S giu HIT / MISS / HIT                        2/3
        (thu tu cell: h2@0.700 / poisson@0.850 / poisson@0.925)
```

Sau dong duoc cham diem. **Khong dong nao dat 3/3 ngoai M-182.**

```text
G23-230  PASS   12/12 cell, git_dirty=false, validity hop le
G23-231  FAIL   doi CA M-181 va M-182 dat 3/3; M-181 chi 2/3
G23-232  PASS   M-184 2/3, M-185 2/3, nguong >=2/3
G23-233  FAIL   M-186 0/3
G23-234  FAIL   M-187 2/3, nguong 3/3
G23-235  PASS   3/3  [SUA SAU KHI XEM -- khong dem diem]
G23-236  PASS   2/3, nguong >=2/3
G23-237  PASS   da bao cao
G23-238  PASS   9/9 cell robustness
```

## 2. Ket qua CHINH -- `H-B` duoc xac nhan sach (`M-182`, 3/3)

```text
cell             hang/o (4o)/(16o)    block/o (4o)/(16o)   block_touch
poisson@0.925          4.00x                1.0929            0.915
poisson@0.850          4.00x                1.0926            0.915
h2@0.700               4.00x                1.1458            0.873
```

Bo truc `m_hat` cho **dung 4.00x so HANG** moi o -- va **chi 1.09..1.15x so
BLOCK**. Vi `cert/config_matrix.py::_qhat` lay
`n_eff = sub["block_id"].nunique()`, muc conformal chi nhin so BLOCK.

> **"4x du lieu" ma ban ke hoach neu la mot ao tuong o tang conformal.**
> No co that o tang uoc luong phan vi (4x hang), nhung tang quyet dinh muc
> bao dam thi khong thay gi. Do la vi `T = 500 ms` << block `5 s`, nen gan
> nhu MOI block cham MOI o (touch 0.87..0.92).

Day la con so duy nhat dat 3/3, va no la con so quan trong nhat cua Task A0.

## 3. `M-186` = 0/3 -- du doan cua toi bi bac bo, va phep do cua toi co tat

Da ky: ti so do rong CI95 (4 o)/(16 o) thuoc **[0.50, 1.00]** -- tuc "4x hang
mua duoc it nhat MOT CHUT do on dinh".

```text
poisson@0.925   16o: w=1.67513   4o: w=1.78215   ti so = 1.0639
poisson@0.850   16o: w=0.62491   4o: w=0.63268   ti so = 1.0124
h2@0.700        16o: w=1.04723   4o: w=1.04880   ti so = 1.0015
```

Ca ba **> 1.00**: taxonomy 4 o cho CI RONG HON, khong hep hon.

Doi chieu voi hai mo hinh:

```text
neu SO HANG quyet dinh do on dinh  ->  ti so ~ sqrt(1/4)    = 0.500
neu SO BLOCK quyet dinh            ->  ti so ~ sqrt(1/1.09) = 0.958
DO DUOC                            ->  1.0015 .. 1.0639
```

Khong khop ca hai, va lech ve phia **> 1**.

### 3.1. Han che cua chinh phep do -- ghi `L90`, KHONG dien giai qua

`M-186` do CI cua **trung binh qhat TREN CAC O**. Taxonomy 16 o trung binh 16
so; taxonomy 4 o trung binh 4 so. Trung binh it so hon thi nhieu hon, **doc
lap voi so hang moi o**. Nen mot phan cua ti so `> 1` co the la HIEN VAT cua
phep trung binh, khong phai phat bieu ve do on dinh cua TUNG `qhat`.

Phep do tach bach (CI cua qhat MOT o, khong qua trung binh nhieu o) **chua
chay**. Cho den khi no chay:

```text
KET LUAN DUOC PHEP RUT:  du doan [0.50,1.00] BI BAC BO -- 4x hang KHONG mua
                         duoc do on dinh nhu da ky. M-186 = 0/3.
KET LUAN KHONG DUOC RUT: "vi tuong quan noi block gan hoan toan". Phep do
                         hien tai khong tach duoc gia thuyet do khoi hien vat
                         trung binh.
```

`M-186` giu nguyen **MISS 0/3**. Khong noi dai, khong dien giai lai.

## 4. `M-187` = 2/3 -- `H-A` bi bac bo o dang manh

Tai `kappa = 1`, tren **12 cell**:

```text
V-N vo bao phu (viol|acc > 0.10):   4/12 cell
    poisson@0.925 (0.1276)   h2@0.700 (0.1198)
    h2@0.650      (0.1217)   h2@0.675 (0.1176)

V-N KHONG vo:                        8/12 cell
    poisson@{0.700, 0.850, 0.875, 0.900, 0.960}
    h2@{0.850, 0.925, 0.960}

V-S giu bao phu:                    12/12 cell   <- khong mot ngoai le
```

Amendment muc 4.2 da dinh truoc cach doc:

> *"Neu V-N khong vo thi H-A bi bac bo tren truc moi, va phai ghi ro rang
> tuong quan `m_hat`--`s` da bien mat khi doi truc AoI -- mot phat hien can
> dieu tra rieng, khong duoc lam ngo."*

**Do la dieu da xay ra o 8/12 cell.** Nen phat bieu dung la:

```text
SAI   "bo truc m_hat lam vo bao phu"                  -- chi dung o 4/12 cell
DUNG  "bo truc m_hat lam vo bao phu o MOT SO cell, va
       khong co cach biet truoc cell nao"
```

Muc "[A]" cua ban ke hoach **khong sai o moi noi** nhu toi da khang dinh khi
soan amendment. No sai o mot phan tu so cell -- va do la du de khong dung
duoc, vi khong ai biet truoc cell nao roi vao phan tu do.

### 4.1. `V-S` la loi ra an toan, va gia cua no da do

```text
V-S giu bao phu 12/12 cell
acceptance(V-S)/acceptance(V-M) = 0.7354 / 0.7793 / 0.8022
```

V-S nhan **it hon 20-27%** so voi V-M. Do la cai gia thuc, bao cao khong lam
tron (`G23-237`).

## 5. `poisson@0.850` -- mot cell lech HE THONG

Bon phep do doc lap deu chi vao cung mot cell:

```text
M-184  spread_m = 1.0286   (thap nhat trong ba, duoi dai [1.05,1.30])
M-185  1.0157              (thap nhat, duoi dai [1.10,1.30])
M-187  V-N = 0.0822        (KHONG vo -- cell duy nhat trong ba)
G236   V-M@kappa=2 = 0.0829 (KHONG vo -- cell duy nhat trong ba)
qhat   thang do ~15.3      (so voi 43.9 va 28.0 cua hai cell kia)
```

Bon dau hieu nhat quan: o cell nay truc `m_hat` gan nhu KHONG mang thong tin,
va bai toan de hon han. Day khong phai nhieu -- do la mot cell o CHE DO KHAC.

`M-183` cua no van binh thuong (1.5979, bang cell `poisson@0.925`), nen khac
biet **khong** den tu truc `z`.

Chua giai thich duoc. Ghi lai de Task B (ma tran chuyen giao) khong lay
`poisson@0.850` lam cell chuan.

## 6. `M-183` -- co so DA DUOC DO LAI (muc dich chinh cua Task A0)

```text
                     truc CU (Z_EDGES_LEGACY)   truc MOI (Z_EDGES_V7)
spread_z                   2.1232                1.4919 .. 1.5979
spread_m                   1.1188                1.0286 .. 1.2007
```

`spread_z` tut **~26%** khi doi sang truc da duyet. Con so `2.1232` trong
`PHASE_23_v3.md` KHONG dung nua. Ghi `L89`; anh xa song trong
`taxonomy_audit.json::superseded_basis`.

`M-183` khai [DA XEM] tu truoc (dai [1.45,1.70] rut tu
`axis_remeasure_impact_wave1.json`) nen **khong duoc dem diem** du no 3/3.

## 7. Hai sua TRUOC khi chay -- va mot doi chung duong ngoai y muon

### 7.1. `H-A` phat bieu sai, bi chinh test cua no bac bo

Ban nhap dau (theo ban review) viet *"profile BIEN lam nhoe hieu ung don"*.
Test viet de ma hoa lap luan do da FAIL:

```text
hieu ung 1.20x don o m=3, DEU tren moi z:   spread_m = 1.2000 = M-185
```

`spread_profiles` trung binh theo `(z, slot)` va GIU NGUYEN truc `m`, nen
hieu ung don hien ra day du. Co che that la **ti so cua trung binh vs trung
binh cua ti so**, va no chi lo ra khi CO tuong tac `z x m`:

```text
base qhat [100,10,10,10], hieu ung 1.5x chi o ba z_bin nho:
    spread_m = 1.1154    M-185 = 1.3750    -> lech 1.23 lan
```

Do duoc tren du lieu that: `M-185` **thap hon** `spread_m` o ca ba cell
(1.1029 vs 1.1149; 1.0157 vs 1.0286; 1.1460 vs 1.2007). Tuc **khong co tuong
tac `z x m` dang ke**, va `M-185` khong them thong tin. Do la ket qua hop le,
va da duoc dinh truoc cach doc trong amendment.

### 7.2. `G23-235` bat mot dieu SAI

Tieu chi ban dau doi ca ba bien the cho `viol|acc` bang nhau tai `kappa=0`.
Chay nhap cho FAIL 3/3. Truy nguyen: `viol|acc = P(score > qhat | accept)` ma
`qhat` PHU THUOC taxonomy, nen V-M (16 o) va V-N/V-S (4 o) **khong the** bang
nhau. Da thay bang hai khang dinh dung va sac hon:

```text
(a) acceptance == 1.0 o ca ba          -> DUNG, 3/3
(b) V-N === V-S TRUNG BIT tai kappa=0  -> DUNG, |dviol| = |dqhat| = 0.0e+00
```

Sua nay lam SAU khi nhin so, nen `G23-235` mang nhan **[SUA SAU KHI XEM]** va
**khong dem diem**. Bay dong `M-181..M-187` khong bi dong vao.

### 7.3. So gate bat loi cua chinh lesson nay -- lan thu ba

Cau *"vung `G23-216` khong duoc dung"* trong ban nhap amendment lam
`test_every_gate_id_mentioned_in_repo_is_in_the_ledger` DO ngay. Khong viet
duoc cau "dung dung ma X" ma khong dang ky X.

Truy ra: `G23-216` la khe do CHINH Lesson 23.21i tao ra -- ke hoach cap no cho
"dung lai Dot 1, 16/16 job", nhung phep do do bi `L77` chan va dai
`G23-215/217/218` duoc cap bo qua no. Da dang ky NOT_RUN.

## 8. Mot loi cua ban de xuat da sua truoc khi chay

Bootstrap cua ban review lay 500 block CO HOAN LAI tu 500 block roi de `_qhat`
dem `block_id.nunique()`:

```text
500 block lay lai co hoan lai  ->  311 nhan duy nhat  (ky vong n(1-1/e) = 316)
=> n_eff = 311 thay vi 500  =>  muc conformal bao thu gia tao o MOI vong
```

`_resample_blocks()` gan nhan block MOI cho tung ban sao, giu dung
`n_eff = 500`. Ghim bang `test_bootstrap_relabels_blocks_so_n_eff_is_preserved`.

## 9. Trang thai va viec ke tiep

```text
Task A0  XONG. Co so da do lai tren truc da duyet. L89 ghi.
Task A   XONG ve DO. Ba bien the da quet tren 12 cell x 5 kappa.
```

Ba dong phai giai truoc khi vao Task B:

1. **`M-186` can phep do tach bach** (CI cua qhat MOT o) de tach gia thuyet
   tuong quan block khoi hien vat trung binh. Chua chay.
2. **`poisson@0.850` o che do khac** -- bon dau hieu nhat quan, chua giai
   thich. Khong duoc lay lam cell chuan cho Task B.
3. **`V-N` vo o 4/12 cell, khong doan truoc duoc cell nao.** Neu Task B can
   mot quy tac chon taxonomy theo cell, day la dau vao cua no.

Khuyen nghi dung `V-S` lam thu tuc mac dinh: no giu bao phu 12/12 cell, doi
lai 20-27% acceptance. Nhung khuyen nghi do dua tren `G23-234` FAIL, nen no
la mot LUA CHON KY THUAT co danh doi, khong phai mot ket luan duoc gate xac
nhan.

# 43 -- Lesson 23.22 Task A0/A: do lai co so truc `m_hat`

Vong mot  : 2026-08-24, `eefd34a`  -- muc 1..9
Vong hai  : 2026-08-25, `b9d2774`  -- muc 10..17 (sua `L91`; them `M-188`, `M-191`, `M-192`)

Lesson    : 23.22 (Task A0 + A)
Amendment : `A064-amendment-64.md` (ky TRUOC, tag `lesson-23-22-prereg` = `7c23151`);
            vong hai: `A065`, `A065b`, `A065c`, `A065d`
Artifact  : `results/LIVE/phase-23/taxonomy_audit.json` (`git_hash = cced37a`, `git_dirty = false`)
Chay      : 12 cell, `n_boot = 2000`, 3 gio 03 phut

> Muc 1..9 giu NGUYEN van ban vong mot. BA ket luan trong do da bi DINH CHINH o
> vong hai; moi muc lien quan co mot dong tro. KHONG sua tai cho: doc ket qua
> phai giu duoc dau vet ta da nghi gi vao luc nao.

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

> **DINH CHINH (vong hai, muc 11):** `M-186` khong chi "co tat" -- no tron BA
> hien vat (`L90` bo sung), khong phai hai. `M-188` tach bach chung va cho
> **3/3**, nhanh HANG. `M-186` giu nguyen MISS 0/3.

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

> **DINH CHINH (vong hai, muc 12):** `H-A` **KHONG** bi bac bo. Bon cell "V-N
> khong vo" deu co `err_neo < 0.05` -- chung la DOI CHUNG AM, khong phai phan
> vi du. Tren 8 cell `A=True`: `V-N - V-S > 0` o **8/8**. `M-187` (phep thu
> NHI PHAN) giu MISS 2/3 va `G23-234` van FAIL; cai duoc sua la CACH DOC.

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

> **DINH CHINH (vong hai, muc 15 D3):** KHONG lech he thong. No la diem MUT
> cua mot xu huong TRON theo `rho_bar`, va bon phep do "truot" deu la ham tang
> cua CUNG mot dai luong (`spread_m`) -- tuc MOT bang chung doc bon lan
> (`NT 51`). "Bon phep do doc lap" ngay duoi la phat bieu SAI.

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

> **DINH CHINH (vong hai):** ca ba dong da giai. (1) -> `M-188`, muc 11.
> (2) -> muc 15 D3: khong phai che do khac, la diem MUT cua mot duong cong
> tron; cam dung lam cell chuan duoc GO. (3) -> muc 12: doan truoc duoc MOT
> CHIEU -- ca 4 cell V-N vo deu nam trong 8 cell song, 0/4 cell chet vo, va
> trong vung song do lon `V-N - V-S` tang theo `spread_m` (Spearman +0.881).
> Cai KHONG doan duoc la cell song nao vuot han moc 0.10.

Khuyen nghi dung `V-S` lam thu tuc mac dinh: no giu bao phu 12/12 cell, doi
lai 20-27% acceptance. Nhung khuyen nghi do dua tren `G23-234` FAIL, nen no
la mot LUA CHON KY THUAT co danh doi, khong phai mot ket luan duoc gate xac
nhan.

> **DINH CHINH (vong hai, muc 14.2):** khuyen nghi tren phai KEM DIEU KIEN ve
> `kappa`. Tai `kappa = 1` -- chinh diem van hanh da tien dang ky -- 4/8 cell
> song co `min_blocks` duoi san on dinh 59, va tai `kappa = 2` thi V-S KHONG
> CHAY: no tra ve `qhat` cua V-N (`L95`).

---

# VONG HAI -- sau khi sua `L91`

Amendment : `A065` (`L91`, `L92`, `M-188`), `A065b` (`L93`, `M-191`),
            `A065c` (`M-192`), `A065d` (`L95`, `L96`)
Artifact  : `results/LIVE/phase-23/taxonomy_audit.json`, `git_hash = cced37a`,
            `git_dirty = false`
Differ    : `results/LIVE/phase-23/g23_242_rerun_diff.json`

## 10. `G23-242` -- pham vi anh huong khai TRUOC, va no dung

```text
0 vi pham vung dong bang tren 12/12 cell
hang V-S doi o dung 5 cell -- CA NAM la ROBUSTNESS:
    h2@0.650, h2@0.925, h2@0.960, poisson@0.875, poisson@0.960
khong cell MAIN nao doi; M-181..M-187 khong doi mot chu so
ban cu nap tu git blob `1e715ff3...` (`eefd34a:results/LIVE/.../taxonomy_audit.json`),
khong tu mot ban sao tren dia
```

`A065` muc 1.2 khai TRUOC: "KHONG DOI: census, spread, mhat_concentration,
bootstrap, moi hang V-M va V-N, M-181..M-187 tren 3 cell MAIN". Dung het.

`provenance` cua artifact ghi `git_hash = cced37a`, `git_dirty = false`: repo
KHONG dich chuyen giua chung, nen artifact khai dung ma da chay.

Day la ly do lam viec theo thu tu "khai pham vi TRUOC, do SAU": khi differ
xanh, ta biet moi thay doi den TU dau, thay vi phai suy luan nguoc tu 244 KB
JSON.

## 11. `M-188` = 3/3 -- KET QUA CHINH cua ca Lesson 23.22

```text
cell            M-188      du doan HANG = 0.500      du doan BLOCK = 0.957
poisson@0.925   0.5375     quy tac ky: <=0.70 -> HANG | >=0.88 -> BLOCK
poisson@0.850   0.5315
h2@0.700        0.5406
```

Ba cell MAIN duoc cham. Ngoai ra, ca 12/12 cell deu roi vao nhanh HANG
(0.4914 .. 0.5406) -- ke ca bon cell suy bien, noi khong co chon loc. Khong
tinh diem, nhung no noi rang co che nay khong phu thuoc vao vung song.

**`H-B` dung o tang MUC conformal nhung SAI o tang UOC LUONG.**

```text
Tang MUC        bo truc `m_hat` -> so BLOCK moi o tang 1.0929 / 1.0926 /
                1.1458 tren ba cell MAIN  (M-182 3/3, dai ky [1.00, 1.15])
                muc conformal gan nhu khong doi
                => "4x du lieu" o tang nay la AO TUONG

Tang UOC LUONG  bo truc `m_hat` -> so HANG moi o tang dung 4.00x
                phan vi mau uoc luong tu 4x hang -> SD giam ~1.9x  (M-188 3/3)
                => "4x du lieu" o tang nay la THAT
```

Hai tang, hai ket luan nguoc, va ca hai deu dung. Ban ke hoach goc noi dung
KET LUAN ("4x du lieu, `qhat` on dinh hon") nhung SAI TANG ("muc conformal").

### 11.1. Vi sao `M-186` khong the thay dieu nay

`M-186` do be rong CI cua **trung binh `qhat` TREN CAC O**. No tron BA thu:

```text
(a) quy luat co gian phuong sai cua qhat   <- thu ta MUON do
(b) so o duoc lay trung binh (16 vs 4)     <- hien vat
(c) tuong quan cheo o qua block dung chung <- hien vat
    (block_touch_ratio = 0.861 .. 0.920 tren 12 cell)
```

Neu sai so cac o doc lap:

```text
phuong sai ~ 1/so HANG   ->  Var(T_M) = 4v4/16 = v4/4 = Var(T_F)  ->  ti so 1.00
phuong sai ~ 1/so BLOCK  ->  Var(T_M) = 1.094v4/16, Var(T_F)=v4/4 ->  ti so 1.91
```

(a) va (b) TRIET TIEU nhau gan het duoi mo hinh HANG; (c) keo ti so xuong nen
mot the gioi BLOCK cung cho ~1.0. Ba an, mot phuong trinh.

`M-188` bo han viec lay trung binh: no do be rong CI cua CHINH con so ma mot
hang o o `(z, m)` nhan duoc -- `qhat_flat(z)` duoi V-N/V-S so voi
`qhat_mondrian(z, m)` duoi V-M, ghep CAP theo o. (b) bien mat vi khong trung
binh; (c) khong ap dung vi khong gop o.

### 11.2. Bai hoc ve THIET KE PHEP DO (khong phai ve ket qua)

```text
M-186  gia tri that 0.9426 .. 1.0639 tren 12 cell, moc quyet dinh 1.00
       -> SAT bien: 5/12 cell nam duoi 1.00, 7/12 nam tren
M-188  gia tri 0.4914 .. 0.5406 tren 12 cell, moc gan nhat 0.70
       -> cach 0.16, va CA 12/12 cung phia
```

Do rong cua phep do cung phai bao cao: `M-188` tinh trung binh tren 16 o
Mondrian, va tung o rai tu 0.41 den 0.73. Mot o duy nhat trong 48 o cua ba
cell MAIN vuot moc 0.70 (`h2@0.700`, o `(1,2)`: 0.7344). Dai luong DUOC CHAM
la trung binh theo o, nen dieu do khong doi phan quyet -- nhung no la ly do
khong duoc doc `M-188` nhu mot hang so vat ly.

Do KHONG phai vi `M-188` may man. Mot phep do bi TRIET TIEU se luon nam quanh
diem trung tinh cua no, va diem do thuong CHINH LA moc quyet dinh. Neu mot dai
luong ban thiet ke cu lat qua lat lai quanh nguong, hay nghi den TRIET TIEU
truoc khi nghi den nhieu.

## 12. `H-A` -- KHONG bi bac bo. Bon "phan vi du" la DOI CHUNG AM

Vong mot ket luan `H-A` bi bac bo vi `V-N` chi vo o 4/12 cell. Sai lam la
KHONG PHAN TANG.

```text
Tieu chi A cua Lesson 23.21 (`A_err_neo_ge_0_05`, DA KY o amendment 23-62):
    err_neo < 0.05  ->  h2@0.850, h2@0.925, h2@0.960, poisson@0.700
    (anchor_err 0.0002 .. 0.0042)
```

Bon cell do co `err_neo ~ 0`: twin gan nhu khong bao gio sai, bai toan quyet
dinh TAM THUONG, tap ACCEPT ~ toan bo dan so, KHONG CO chon loc, nen KHONG THE
co thien lech hau chon loc. Chung la DOI CHUNG AM cua `H-A`, va chung cho ket
qua DUNG nhu `H-A` du doan.

Tren 8 cell `A = True`, tai `kappa = 1`:

```text
V-N >= V-M : 8/8      V-M >= V-S : 8/8      V-N - V-S > 0 : 8/8
min +0.0128 (poisson@0.850)   trung vi +0.0280   max +0.0462 (poisson@0.925)

Spearman(spread_m, V-N - V-S):   8 cell = +0.881   |   12 cell = +0.007
```

Cell suy bien XOA SACH tin hieu (+0.881 -> +0.007). Do vua la bang chung `H-A`
dung, vua la bang chung viec phan tang la BAT BUOC.

`M-187` (phep thu NHI PHAN `viol > 0.10`) giu MISS 2/3 -- KHONG lat. Cai duoc
sua la CACH DOC: huong cua `H-A` dung pho quat tren vung song; cai khong dung
la "do lon LUON vuot alpha".

> ⚠️ Muc nay mang nhan **POST-HOC** (`M-189`, `A065` muc 3). No KHONG dem diem
> va KHONG lat `G23-234` (van FAIL). No ton tai de lam regression control:
> `A065c` xac nhan 8/8 sau khi sua `L91`.

## 13. DANH DOI NGAN SACH MAU -- 9.0x, va mot menh de khai niem

Tai diem van hanh `kappa = 1` tren `poisson@0.925`:

```text
V-M  qhat hieu chuan tren TOAN BO hang calib
     16 o, n_eff trung binh 457.5 block/o     level(457) = 0.9694   binh thuong

V-S  qhat hieu chuan tren TAP DUOC CHON
     4 o,  n_eff = 51 block o o thua nhat     level(51)  = 1.0000   MAX MAU

=> V-M co 9.0x nhieu block hieu dung hon V-S cho MOI phan vi,
   DU V-M co gap BON so o.
```

**Ca hai thu tuc deu PHAI tra mot khoan "phi dieu kien hoa". Chung chi tra
bang HAI DONG TIEN KHAC NHAU:**

```text
V-M  tra bang SO O      -> 16 o, nhung moi o giu ~457 block
     (block chong len moi o, chia o gan nhu khong ton block -- dung `H-B`)

V-S  tra bang TAP MAU   -> 4 o, nhung chi ~51 block o o thua nhat
     (tap chon co lai theo kappa; tap chon KHONG chong len moi block)
```

Va day la menh de khai niem sac nhat cua ca lesson:

> `H-B` noi chia theo taxonomy gan nhu mien phi o tang block, vi block chong
> len moi o. Dung cho `V-M`. Nhung `V-S` khong chia theo taxonomy -- no chia
> theo **TAP DUOC CHON**, va tap do khong chong len moi block. **Cung mot lap
> luan, hai ket luan nguoc, tuy CHIEU chia.**

## 14. `M-191` = 4 va `M-192` -- khuyen nghi V-S phai KEM DIEU KIEN

### 14.1. `M-191` -- che do `qhat = max mau` (`L93`)

```text
qhat_at_sample_max @ kappa=1, V-S:
    poisson@0.925 (nb=51)   poisson@0.900 (42)
    poisson@0.960 (42)      h2@0.650      (58)     -> 4, trong dai ky [1, 8]

G23-240  0/12 con qhat vo han   (truoc khi sua L91: 3/12)
G23-241  suy bien 6/12 TRUOC va 6/12 SAU
```

`G23-241` noi mot dieu tinh: sua `L91` KHONG doi SO LUONG cell suy bien, no
doi CHAT LUONG cua `qhat` o nhung cell do -- het `+inf`. San cu (`9`) va san
moi (`29`) roi vao cung mot cho tren duong cong `min_blocks`, nhung o nao lot
qua san cu thi nhan `qhat = +inf`.

### 14.2. `M-192` -- dai van hanh hop le cua V-S

```text
cell            k=0    k=0.25   k=0.50   k=1.00     [san on dinh = 59]
poisson@0.925   500     500      461       51  X
poisson@0.850   500     499      421       80
h2@0.700        500     500      490      182
poisson@0.875   500     500      429       93
poisson@0.900   500     500      443       42  X
poisson@0.960   500     500      471       42  X
h2@0.650        500     500      485       58  X
h2@0.675        500     500      489      128

don dieu 8/8; nguong cat tren poisson@0.925 = 0.50   -> M-192 HIT
```

**Tai `kappa = 0.50`: CA 8/8 cell song co `min_blocks` thuoc [421, 490] >> 59.
Tai `kappa = 1.00`: 4/8 roi duoi san on dinh.**

> `kappa = 1` la diem van hanh DA TIEN DANG KY tu `A064`, va no nam NGOAI dai
> V-S dung duoc tren cell chinh. Khuyen nghi "chuyen tu Mondrian sang
> selective" **phai kem dieu kien ve `kappa`**, khong con vo dieu kien.

Cach doc `M-192` da phai phan xu: xem `L94` (van ban ky mo ho) va muc 15 D4.

## 15. Bon dinh chinh doi voi vong mot

```text
D1  `M-186` tron BA hien vat (khong phai hai): con thieu (c) tuong quan cheo o
    qua block dung chung. Ghi o `L90` (bo sung) va muc 11.1.

D2  `H-A` KHONG bi bac bo (muc 12). Bon cell "phan vi du" la doi chung am,
    va chung la doi chung am CO DINH NGHIA TRUOC (tieu chi A, amendment 23-62),
    khong phai mot tap duoc chon sau khi nhin ket qua.

D3  `poisson@0.850` KHONG lech he thong. Thang `qhat` (V-M, kappa=0) cua ho
    poisson di 1.0467 -> 15.5590 -> 23.7692 -> 34.4153 -> 44.1072 -> 62.3353
    theo `rho_bar`: don dieu, tron. `15.56` nam DUNG tren duong cong -- diem
    MUT, khong phai ngoai lai. No trong lech vi vong mot chi so voi hai cell
    MAIN kia, ma ca hai o dau CAO.
    Bon phep do "truot" (`spread_m`, `M-185`, `V-N` vo, `V-M@k=2` vo) deu la
    ham tang cua CUNG mot dai luong -- MOT bang chung doc bon lan (`NT 51`,
    `A063` muc 2). Cau "bon phep do doc lap" o muc 5 la SAI.

D4  `L95`: `selective` tut ve `none` khi suy bien o vong 0 (`A065d`).
    Do duoc 8/8 cell song tai `kappa=2`, `n_iter=0`, trung bit. Nen tai
    `kappa=2` khong ton tai mot "V-S" nao de doc `M-192` tren do -- day la ly
    do THUC CHAT (khong chi ngu nghia) de cham theo DOAN LIEN TUC.
```

## 16. So gate vong hai

```text
G23-239  PASS   M-188 3/3, nhanh HANG, ap dung dung quy tac ky
G23-240  PASS   0/12 con qhat vo han
G23-241  PASS   suy bien 6/12 truoc va sau, da bao cao khong lam tron
G23-242  PASS   0 vi pham vung dong bang, 12/12 cell
G23-243  PASS   max|anchor_err - err_neo| = 0.000e+00, 12/12
G23-244  PASS   M-189 8/8  [POST-HOC -- khong dem diem]
G23-245  PASS   M-191 = 4, trong dai [1, 8]; chot chan van la floor_blocks
G23-246  PASS   M-192 don dieu 8/8, nguong cat 0.5 (doc theo DOAN LIEN TUC)
G23-247  PASS   L95 do thang tren artifact, 8/8 trung bit; khong chay lai

G23-233  FAIL   M-186 0/3   -- giu nguyen, KHONG dien giai lai
G23-234  FAIL   M-187 2/3   -- giu nguyen; muc 12 la POST-HOC, khong lat
```

## 17. Ket luan cua Lesson 23.22 -- ba cau

```text
1. Bo truc `m_hat` khoi taxonomy KHONG mua duoc gi o tang MUC conformal
   (block chong len moi o: +9.3% / +9.3% / +14.6% block moi o tren ba cell
   MAIN, `M-182`), nhung mua duoc ~1.9x do on
   dinh o tang UOC LUONG phan vi (4.00x hang). `H-B` dung mot nua, va nua kia
   quan trong.

2. Bo truc `m_hat` ma KHONG thay bang mot sua chua chon loc thi VO bao dam
   hau chon loc -- nhung chi o cac cell co chon loc that (`err_neo >= 0.05`),
   va do lon ti le voi `spread_m` (Spearman +0.881 tren 8 cell song, +0.007
   tren ca 12). `selective` sua duoc o 8/8 cell, VOI DIEU KIEN `kappa <= 0.5`.

3. Cai gia cua `selective` KHONG phai co mau taxonomy ma la co mau CHON LOC:
   9.0x it block hieu dung hon `mondrian` tai `kappa = 1`. Chon giua hai thu
   tuc la mot quyet dinh ve NGAN SACH MAU, khong phai ve tinh dung dan.
```

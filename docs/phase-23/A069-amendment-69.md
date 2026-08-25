# AMENDMENT 23-69 -- Lesson 23.22c: go `L92`, va mot tap MU moi

Ngay ky : 2026-08-26

Lesson  : 23.22c (mo SAU tag `lesson-23-22-complete` tai commit `18f82cd`)

Loai    : TIEN DANG KY

## 0. Disclosure

### 0.1. DA XEM

Toan bo Task A/B/B-2/B-3; `err_neo` va `kappa_A` tren 12 cell; Spearman
(`kappa_A`, `err_neo`) = -0.9762 [POST-HOC]; va day du 656 dong
`recalibrate_transfer.json::rows_dead` (`L105`).

### 0.2. Vi sao can lesson nay

```text
`L92`  ho tai GHEP HOAN TOAN voi rho trong tap song; chua duoc noi "qua HO".
L105   tap 4 cell chet da can lam tap mu.
N2/N5  do nhay theo a* va san acceptance chua do; M-203 cho thay san bind.
```

Ba menh de post-hoc duoc ky lai tren cell moi:

```text
P-1  C3-R giu err|accept/anchor hep (1.22x), B2-R de no chay 2.39x va
     Spearman(anchor, he so B2-R)=+0.9286.
P-2  Khoang cach err C3-R/B2-R tang khi acceptance giam.
P-3  kappa_A la chi so don dieu cua do kho; Spearman=-0.9762.
```

## 1. Cau truc suy duoc truoc

```text
S-1  err_neo hai ho bien thien NGUOC CHIEU theo rho; ranh song/chet cua ca
     hai nam trong (0.700,0.850). Rho {0.760,0.800} chi la phong doan.
     -> pilot do kho tren {0.740,0.780,0.820} x {poisson,h2} la bat buoc.

S-2  Chi phi troi la sinh calib_set parquet. SLA_MANIFEST chi la provenance
     pointer trong validity block, khong tra cell. KHONG sua manifest cu.
     Builder van can mot calibration cell de sinh rho/sigma/w_loss; runner
     phai dung `extra_calibrated_cells()` cua repo va ghi mot SIDECAR MOI,
     khong ghi de `sla_calibration.json`.

S-3  Neu kappa_A giai thich het transfer thi "ho tai" khong them suc giai
     thich. Day la null -> ky NGUONG TUONG DUONG, khong ky p > 0.05.

S-4  Cell moi la tap mu cho P-1/P-2/P-3. Pilot chi duoc xuat/bao cao:
     err_neo, n_calib_blocks, n_test_blocks, kappa_A, thoi gian va digest.
     Moi truong ket qua khac trong parquet van MU den khi muc 4 da commit/tag.
```

## 2. Thiet ke

```text
BUOC 1  PILOT DO KHO
    Sinh 6 cell: rho in {0.740,0.780,0.820} x {poisson,h2}, U3,
    measured_v7, 5 seed 101..105, n=200000/seed, block split.
    Muc tieu: >=1 rho co CA HAI ho err_neo >= 0.05.

    CHAN DUNG:
      (a) khong rho nao co ca hai ho song -> DUNG, L92 khong go bang truc nay;
      (b) cell nao co n_calib_blocks < 500 -> DUNG, ky lai luoi n.

BUOC 2  MO RONG MA TRAN -- chi sau tag `lesson-23-22c-prereg`
    Them K cell moi duoc pilot xac nhan vao tap song. Chay lai Task B-3 voi
    cung a*, N_GRID, seed, san 0.20 va alpha.

BUOC 3  DO NHAY -- chi sau tag prereg
    a* in {0.30,0.42679,0.55}; san in {0.20,0.30}; 6 to hop.
```

## 3. Pilot duoc phep doc gi

Duoc doc va ghi vao report: `err_neo`, `n_calib_blocks`, `n_test_blocks`,
`kappa_A`, thoi gian build va SHA-256 cua parquet/report. TAT CA truong khac
cua cell moi la MU cho den khi muc 4 duoc commit tai tag prereg.

Runner: `tools/a069_pilot_new_cells.py`. Artifact du kien:

```text
results/LIVE/phase-20R/sla_calibration_A069_pilot.json
results/LIVE/phase-21R/calib_set_{mode}_{rho}_U3_measured_v7_A069.parquet
results/LIVE/phase-21R/calib_set_{mode}_{rho}_U3_measured_v7_A069_report.json
results/LIVE/phase-23/a069_pilot.json
```

Pilot cung do thoi gian cua TUNG cell; gioi han chi phi duoc ky truoc:

```text
mot cell > 30 phut -> DUNG va ky lai luoi rho/seed.
```

## 4. Du doan -- BAN KHOA truoc BUOC 2/3

### `M-209` -- MU. `L92` co go duoc khong?

Tren cac rho co ca hai ho song, co >=2 cap A->B GIUA HO tai cung rho; moi cap
co `viol|accept <= 0.10` tai n=250 va acceptance >=0.20.

### `M-210` -- MU. Ho tai co them suc giai thich khong?

Hoi quy `|acceptance_B-a*|` tren `|log(kappa_A/kappa_B)|`, moi o ngoai cheo,
n=500:

```text
(a) slope trong [0.40,0.62]
(b) them bien cung_ho/khac_ho:
    |he so| <= 0.02 VA delta R^2 <= 0.02
(c) Spearman >= +0.90
```

HIT khi ca ba dat. Neu (b) MISS, ho tai la truc doc lap va M-202 cua Task B-3
la hieu ung ghep; day la ket qua quan trong hon null HIT.

### `M-211` -- MU. P-1 tren cell moi

Tai n=250: range ratio C3-R `err|accept/anchor <=1.60`; B2-R >=1.80; va
Spearman(anchor, he so B2-R) >=+0.70.

### `M-212` -- MU. P-2 tren cell moi

Tai n=250 va acceptance {0.70,0.50,0.30,0.15}: `|err_C3R-err_B2R|` don dieu
khong giam o >=3/4 buoc, va C3-R <= B2-R o ca bon muc.

### `M-213` -- MU. P-3 tren cell moi

Tren toan bo 8+K cell song: Spearman(`kappa_A`,`err_neo`) <= -0.85.

### `M-214` -- do nhay a*/san

Voi moi trong 6 to hop: n*(C3-R) in {60,120,250} va
n*(C3-R)/n*(B2-R) >=2.0.

## 5. Doi chung

```text
NC-C-0  WIRING: chay lai 8 cell cu phai tai tao artifact tung bit; max delta=0.

NC-C-1  AM: cell chet dung tieu chi TUONG DOI
         err|accept(C3-R)/anchor_err >=0.80 o >=3/4 cell.
         No duoc du kien FAIL tren 4 cell chet cu; do la chu dich vi no do
         mot dai luong khac voi doi chung tuyet doi cu.

NC-C-2  DUONG: B1-R trung a* khong kem B2-R nhung err|accept >=0.90*anchor.
         PHAI FIRE.

NC-C-3  B2-R/B1-R trung bit theo truc A.
```

## 6. Gate

| Gate | Noi dung |
|---|---|
| G23-270 | `M-209`, go `L92` |
| G23-271 | `M-210`, equivalence cua bien ho tai |
| G23-272 | `M-211`, P-1 cham mu |
| G23-273 | `M-212`, P-2 cham mu |
| G23-274 | `M-213`, P-3 cham mu |
| G23-275 | `M-214`, do nhay a*/san |
| G23-276 | `NC-C-0..3` |

## 7. Chan dung

```text
1. Pilot khong rho nao co ca hai ho song -> DUNG; L92 khong go bang truc nay.
2. Pilot co cell n_calib_blocks <500 -> DUNG; ky lai luoi n.
3. NC-C-0 khong trung bit -> DUNG.
4. Chi phi sinh mot cell >30 phut -> DUNG va ky lai luoi rho/seed.
```

## 8. No ghi truoc

```text
N1  Ket qua chi ap dung tai rho co ca hai ho song.
N2  Cell moi dung cung pipeline va seed; pipeline change phai khai va NC-C-0.
N3  L100 van chua sua; dung qhat_source.
N4  Tap cell moi cung se can sau lesson nay. Khong in day du bien ket qua vao
    artifact pilot; tap mu la tai nguyen can kiet.
```

# Lesson 23.20 Dot 1 -- Tac dong cua viec sua truc tuoi

Ngay     : 2026-08-22
Prereg   : `docs/phase-23/00zzh-amendment-49b.md` (tag `amendment-49b`)
Cau hoi  : **U0 @ legacy vs U0 @ measured** -- chi `d` va `T` doi, ho so giu
           nguyen `U0`. Neu dung `U3` thi doi BA thu va khong quy trach nhiem duoc.
Artifact : `results/LIVE/phase-23/axis_remeasure_impact_wave1.json`
So ledger: `results/LIVE/phase-23/run_ledger_wave1.json`

## 0. Quy mo va thoi gian THUC

```text
16 build, moi build 26 s  ->  ~7 phut, KHONG phai 3 ngay
parquet 65.5 MB moi file  ->  ~2 GB (HANG 3, KHONG commit)
bon cong nhanh PASS tren 16/16 job
```

Ban ke hoach uoc "2-3 ngay may". **Do truoc, dung doan** -- chenh lech la
ba bac do lon, va no doi hoan toan cach to chuc cong viec.

## 1. Bon cong nhanh

```text
mean(z_s) : 302.488 ms (legacy)  ->  366.023 ms (measured), giong het 16/16 job
ty trong  : [0.2531, 0.2499, 0.2499, 0.2472]   lech lon nhat 0.31 diem %
ngoai dai : 0
block/bin : >= 9 tren moi cell
```

`mean(z_s)` va ty trong bin **giong het nhau o ca 8 cell** -- dung nhu ky
vong: truc `z` doc lap voi cell (cung `d`, `T`, `phase0`, ho so `U0`); cell
chi doi `rho`/`cost`.

## 2. Bang 1 -- `M-125a`: q_hat BIEN

| cell | q_hat CU | q_hat MOI | delta | tien doan z^0.431 | lech | err_neo | dem? |
|---|---:|---:|---:|---:|---:|---:|:-:|
| h2@0.700 | 11.4915 | 12.6195 | +9.82% | +8.56% | +1.15% | 0.1265 | CO |
| h2@0.850 | 29.8783 | 32.7028 | +9.45% | +8.56% | +0.82% | 0.0029 | suy bien |
| h2@0.925 | 39.3999 | 42.5189 | +7.92% | +8.56% | -0.60% | 0.0002 | suy bien |
| h2@0.960 | 43.2056 | 47.0270 | +8.84% | +8.56% | +0.26% | 0.0005 | suy bien |
| poisson@0.700 | 0.3863 | 0.4218 | +9.19% | +8.56% | +0.58% | 0.0000 | suy bien |
| poisson@0.850 | 5.6398 | 6.2157 | +10.21% | +8.56% | +1.52% | 0.2207 | CO |
| poisson@0.925 | 20.5032 | 22.6037 | +10.24% | +8.56% | +1.55% | 0.2224 | CO |
| poisson@0.960 | 32.2674 | 35.5819 | +10.27% | +8.56% | +1.57% | 0.1995 | CO |

**M-125a: 8/8 cell trong dai khoa +5%..+13%** (do duoc +7.92% .. +10.27%, tien doan +8.56%).

## 3. Bang 2 -- `M-125b`: dinh luat z^0.431 tren 8 cell x 4 bin

| cell | bin | z_tb CU | z_tb MOI | ty so z | q ty so | tien doan | lech | dem? | KQ |
|---|---|---:|---:|---:|---:|---:|---:|:-:|:-:|
| h2@0.700 | B0 | 75.0 | 179.2 | 2.389 | 1.429 | 1.456 | -1.8% | CO | HIT |
| h2@0.700 | B1 | 147.5 | 305.0 | 2.068 | 1.352 | 1.368 | -1.1% | CO | HIT |
| h2@0.700 | B2 | 247.5 | 430.0 | 1.737 | 1.255 | 1.269 | -1.1% | CO | HIT |
| h2@0.700 | B3 | 425.0 | 554.4 | 1.304 | 1.109 | 1.121 | -1.1% | CO | HIT |
| h2@0.850 | B0 | 75.0 | 179.2 | 2.389 | 1.484 | 1.456 | +1.9% | -- | HIT |
| h2@0.850 | B1 | 147.5 | 305.0 | 2.068 | 1.371 | 1.368 | +0.3% | -- | HIT |
| h2@0.850 | B2 | 247.5 | 430.0 | 1.737 | 1.259 | 1.269 | -0.8% | -- | HIT |
| h2@0.850 | B3 | 425.0 | 554.4 | 1.304 | 1.100 | 1.121 | -1.9% | -- | HIT |
| h2@0.925 | B0 | 75.0 | 179.2 | 2.389 | 1.368 | 1.456 | -6.0% | -- | HIT |
| h2@0.925 | B1 | 147.5 | 305.0 | 2.068 | 1.312 | 1.368 | -4.1% | -- | HIT |
| h2@0.925 | B2 | 247.5 | 430.0 | 1.737 | 1.226 | 1.269 | -3.4% | -- | HIT |
| h2@0.925 | B3 | 425.0 | 554.4 | 1.304 | 1.096 | 1.121 | -2.3% | -- | HIT |
| h2@0.960 | B0 | 75.0 | 179.2 | 2.389 | 1.462 | 1.456 | +0.4% | -- | HIT |
| h2@0.960 | B1 | 147.5 | 305.0 | 2.068 | 1.363 | 1.368 | -0.3% | -- | HIT |
| h2@0.960 | B2 | 247.5 | 430.0 | 1.737 | 1.246 | 1.269 | -1.8% | -- | HIT |
| h2@0.960 | B3 | 425.0 | 554.4 | 1.304 | 1.101 | 1.121 | -1.8% | -- | HIT |
| poisson@0.700 | B0 | 75.0 | 179.2 | 2.389 | 1.390 | 1.456 | -4.5% | -- | HIT |
| poisson@0.700 | B1 | 147.5 | 305.0 | 2.068 | 1.336 | 1.368 | -2.3% | -- | HIT |
| poisson@0.700 | B2 | 247.5 | 430.0 | 1.737 | 1.240 | 1.269 | -2.2% | -- | HIT |
| poisson@0.700 | B3 | 425.0 | 554.4 | 1.304 | 1.102 | 1.121 | -1.7% | -- | HIT |
| poisson@0.850 | B0 | 75.0 | 179.2 | 2.389 | 1.468 | 1.456 | +0.8% | CO | HIT |
| poisson@0.850 | B1 | 147.5 | 305.0 | 2.068 | 1.379 | 1.368 | +0.8% | CO | HIT |
| poisson@0.850 | B2 | 247.5 | 430.0 | 1.737 | 1.272 | 1.269 | +0.3% | CO | HIT |
| poisson@0.850 | B3 | 425.0 | 554.4 | 1.304 | 1.116 | 1.121 | -0.5% | CO | HIT |
| poisson@0.925 | B0 | 75.0 | 179.2 | 2.389 | 1.479 | 1.456 | +1.6% | CO | HIT |
| poisson@0.925 | B1 | 147.5 | 305.0 | 2.068 | 1.371 | 1.368 | +0.2% | CO | HIT |
| poisson@0.925 | B2 | 247.5 | 430.0 | 1.737 | 1.262 | 1.269 | -0.5% | CO | HIT |
| poisson@0.925 | B3 | 425.0 | 554.4 | 1.304 | 1.117 | 1.121 | -0.4% | CO | HIT |
| poisson@0.960 | B0 | 75.0 | 179.2 | 2.389 | 1.494 | 1.456 | +2.6% | CO | HIT |
| poisson@0.960 | B1 | 147.5 | 305.0 | 2.068 | 1.380 | 1.368 | +0.9% | CO | HIT |
| poisson@0.960 | B2 | 247.5 | 430.0 | 1.737 | 1.278 | 1.269 | +0.7% | CO | HIT |
| poisson@0.960 | B3 | 425.0 | 554.4 | 1.304 | 1.114 | 1.121 | -0.7% | CO | HIT |

**M-125b: 16/16 o DEM DUOC trong +/-25% (100%), lech lon nhat 2.6%.**

Ke ca 16 o suy bien (khong dem theo amendment 23-49b): **32/32**, lech lon nhat 6.0%.

## 4. Doc ket qua cho dung

### `z^0.431` la mot dinh luat DUNG DUOC, khong chi MO TA

Dinh luat duoc kiem o **32 o**, voi ty so `z` tu `1.30` den `2.39` -- tuc
bon tien doan KHAC NHAU tren moi cell (`1.121` den `1.456`). Ca 32 o deu
trong `+/-25%`; tren 16 o dem duoc, lech lon nhat chi `2.6%`.

```text
=> Day la dau vao truc tiep cho Lesson 23.28 (transfer giua bin tuoi):
   cau tra loi la DUNG DUOC.
```

### Ba canh bao ve pham vi -- phai ghi kem khi trich dan

**(a) Day la so sanh GHEP CAP.** Hai ve dung CUNG 5 seed, CUNG trace `rho`,
CUNG truth table; chi truc `z` doi. Sai so lay mau cua hai ve tuong quan va
triet tieu phan lon trong ty so.

```text
KHONG duoc doc "q_hat do duoc voi sai so 2.6%".
Trong paper phai viet "paired comparison on identical load realisations".
Con thieu: CI KHONG ghep cap cua tung q_hat (block bootstrap 2000 draw).
```

**(b) Ba trong bon bin la NOI SUY.** `z_tb` moi `179 / 305 / 430` nam TRONG
dai cu `75..425`. Chi `B3` (`554.4`) la **ngoai suy**, vuot `30%` ngoai dai
da hieu chuan.

```text
Phat bieu dung : "dinh luat giu duoc khi ngoai suy 30%, kiem o MOT diem
                  tren moi cell (8 diem)"
Phat bieu SAI  : "dinh luat ngoai suy duoc"
```

Dang chu y: `B3` -- o ngoai suy duy nhat -- lai la bin **on dinh nhat**
(lech `-0.4%` den `-2.3%` tren ca 8 cell, va deu AM). Do la mot dau hieu co
he thong, khong phai nhieu; xem muc 5.

**(c) Bon cell suy bien khong DEM nhung van BAO CAO.** Nguong
`err_neo >= 0.05` ky TRUOC o amendment 23-49b muc 1, khi chua tinh `M-125b`
tren cac cell do. Chung van HIT (32/32) nen viec loai khong doi ket luan --
nhung neu de sau khi thay bang moi loai thi do la chon mau hau nghiem.

## 5. Mot cau truc trong phan du, chua giai thich

Lech cua `B3` AM tren ca 8 cell (`-0.4%` .. `-2.3%`), trong khi `B0` phan
lon DUONG. Tuc dinh luat `z^0.431` hoi **qua manh** o duoi cao va hoi
**qua yeu** o duoi thap -- goi y so mu thuc te nho hon `0.431` mot chut o
dai `z` moi.

```text
Do lon: <= 2.6% tren o dem duoc. Nho hon nhieu so voi dai khoa +/-25%.
Nghi pham: L35 (du hinh dang ~8 ms chua ro co che).
KHONG dieu chinh so mu de che phan du nay -- 0.431 duoc khoa o Phase 22.
Ghi lai de Lesson 23.28 kiem.
```

## 6. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-123 | `OUT_*` tro dung TANG (LIVE khi measured) | PASS |
| G23-124 | ten file mang CA ho so VA truc | PASS |
| G23-126 | Dot 1 (16 job): bon cong nhanh PASS tren MOI job | PASS -- 16/16 |
| G23-129 | `M-125a`: `+5%..+13%` tren MOI cell | PASS -- 8/8, `+7.92%..+10.27%` |
| G23-130 | `M-125b` >= 90% trong `+/-25%` tren o dem duoc | PASS -- 16/16 = 100% |

`G23-125` (ha nguon co `--axis`) van MO: bay script ha nguon chua co co do.
`conformal_v2` khong can vi no nhan `--calib`/`--out` truc tiep.

## 6b. Test chan cua 23.17 tu choi 9 artifact -- va no DUNG

Sau Dot 1, `test_no_stale_axes.py` FAIL tren 8 `calib_set report.json` cong
mot `run_ledger`. Hai nguyen nhan TACH BIET:

```text
(a) aoi_axis.label = UNREGISTERED
    sha cua measurements/aoi_model_v7.py chua co trong axis_registry.json.
    Co che "nhan duoc SUY, khong duoc KHAI" hoat dong dung: ma nguon moi
    thi phai dang ky QUA AMENDMENT. Da dang ky (amendment 23-49c):
    label `measured_v7_uniform`, status ACTIVE.

(b) sla_axis.label = self_calibrated  -- VAN chua duoc duyet
    calib_set DUNG nguong SLA mang loi cau truc S14 (nguong suy tu chinh du
    lieu duoc danh gia). Loi do sua o Lesson 23.21, CHUA lam.
```

`(b)` la mot loi CO THAT, va no lat mot quyet dinh cua amendment 23-49b muc 3:

> Mot artifact vao `LIVE/` khi **MOI** truc cua no duoc duyet, khong phai khi
> **mot** truc duoc sua. Sua truc tuoi roi coi `calib_set` la "sach" chinh la
> cach bo qua truc SLA chua sua -- kieu loi ma Lesson 23.17 duoc viet ra de chan.

```text
=> Dot 1/2/3 vao SUPERSEDED/ cho den khi Lesson 23.21 sua S14 va mot
   amendment duyet CA HAI truc. `approved_for_live` VAN RONG.
=> Dat o SUPERSEDED khong lam mat canh gac: chinh cai TANG la loi phat bieu
   "dan xuat, chua phai ban paper dung".
```

Artifact TONG HOP `axis_remeasure_impact_wave1.json` van o `LIVE/` vi no la
ket qua DO (vai tro MEASURES), khong DUNG truc SLA de ket luan.

## 7. Con lai

```text
Dot 2  U3 @ measured, 8 cell   -- con so HEADLINE
Dot 3  U1/U2 @ measured, 3 cell -- ablation ho so (M-131)
       (gio moi tach duoc HINH DANG khoi MUC, nho amendment 23-49a muc 2)
ha nguon: them --axis cho 7 script, roi Bang 3 (ket luan CU vs MOI)
```

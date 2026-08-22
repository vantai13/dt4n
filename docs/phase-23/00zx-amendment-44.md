# AMENDMENT 23-44 -- Doi nhan CONDITIONAL_ON_DSYNC_51MS

Ngay ky      : 2026-08-22
Tag dong bang: `pre-aoi-fix` -> 06f8a26
Lesson       : 23.17
DOI raw data : (CHUA CO -- xem muc 7, gate G23-74 con MO)

Trang thai: **TRUOC bat ky dong code phan tich nao cua Lesson 23.18.**
Commit nay chi chua mot file la chinh no.

## 1. Su co

Lesson 23.8 (A1--A5) do AoI truc tiep tren `topology_v7`, 30 run x 120 s,
287.760 quan sat. Ket qua CLEAN (15 run, gop):

```text
p05    143.072 ms     (trung binh 15 run 143.100; CI95 t14 [141.82, 144.38])
mean   368.924 ms     (trung binh 15 run 368.924; CI95 t14 [365.92, 371.93])
CV     0.419529       (sd giua run 0.005305)
```

Nguon: `results/phase-23/aoi_v7_estimates.json`, khoi `modes.clean.aoi` va
`runs[]`. CI95 o tren tinh bang t-Student df=14 tren trung binh 15 run CLEAN;
day la phuong phap duoc ghi ro de nguoi khac tinh lai ra dung so.

Tham so dang dung trong pipeline la `d_sync = 51 ms`
(`measurements/decision_error.py:38  DEFAULT_D_SYNC_S = 0.051`, va ban sao
`cert/freshness_requirement.py:53  D_SYNC = 0.051`). Gia tri do duoc do tren
`twin/topology3.py` (topology 3 duong, 9 canh, tien Phase 20). No chua bao gio
duoc do lai khi he chuyen sang butterfly 8 link (`twin/topology_v7.py`).

Day la loi cau truc S12: mot hang so do tren he A duoc ke thua sang he B ma
khong ai do lai. Bien thien cua p05 tren nam muc rho chi 2.126 ms, nen sai lech
51 ms vs 143 ms khong phai nhieu do -- no la mot truc sai.

## 2. Pham vi anh huong

Moi artifact sinh boi duong di qua `sawtooth_age_steps()` hoac hang so
`D_SYNC` / `DEFAULT_D_SYNC_S`:

```text
cert/build_calib_set.py
cert/build_calib_set_v2.py
cert/build_calib_set_v3.py          (D_SYNC = DEFAULT_D_SYNC_S, dong 80)
cert/freshness_requirement.py       (D_SYNC = 0.051, dong 53)
cert/dsync_sensitivity.py           (0.051 la diem dau cua thang quet)
measurements/decision_error.py      (dong 37--38, nguon goc)
measurements/decision_error_v2.py
measurements/phase20_block_crossing_diagnostic.py
```

Chi tiet theo tung artifact: `results/MANIFEST.md`, cot "Truc AoI".

## 3. Hanh dong

```text
KHONG rut lai bat ky con so nao.
KHONG xoa bat ky artifact nao.
CHI doi NHAN pham vi hieu luc.
```

Ly do: cac con so **khong sai**. Chung la mot ham duoc danh gia tai mot diem
dau vao. Diem dau vao do khong mo ta he hien tai -- nhung phep tinh van dung.
Khi ca hai ban duoc cong bo canh nhau o Lesson 23.20, cap so do tro thanh mot
phep do do nhay tu nhien theo truc tuoi.

Cac ket luan sau day tu nay mang nhan `CONDITIONAL_ON_DSYNC_51MS`:

```text
Lesson 23.3   bang xep hang baseline tai coverage 0.78
Lesson 23.4   ket luan cross-cell va dinh luat lift > swing (phan SO)
Lesson 23.14  fallback bottleneck va objective robustness
Lesson 23.15  phan tang song/chet tam cell
Lesson 23.16  vung song va bracket doi dau (0.900, 0.925)
```

## 4. KHONG bi anh huong -- giu nguyen hieu luc day du

Cac dong nhat thuc dai so khong phu thuoc z:

```text
K23-1        dong nhat thuc hoa von cua fallback
K23-5        delta = reject_share * (swing - lift), sai so 2.17e-17
Co che #8    regret_ratio = err_ratio * normpen_ratio * scale_ratio
Co che #9    co loi <=> lift > swing
```

Cac phase do luong:

```text
Phase L      toan bo
Phase T      toan bo
Phase 20R    95/96 artifact; chi decision_error_sawtooth.json bi anh huong.
             decision_error_by_age_by_regime.parquet dung LUOI z CO DINH
             [0, 0.05, 0.1, 0.2, 0.3, 0.55, 1.0, 2.0, 4.0] s -> z-independent.
Phase 23     aoi_v7_estimates.json la SO DO cua chinh truc z -> khong the
             bi chinh truc do lam sai.
```

## 5. Du doan (ghi TRUOC, doi chieu o Lesson 23.20)

Tinh bang cach lay trung binh duong cong 20R theo hai phan phoi z:

```text
err_neo tang        +10.5% .. +10.8%  tren ca ba cell
q_hat rong them     ~ +10%
so cell co loi      2/5 -> 3/5
h2@0.700            chuyen tu CO HAI sang CO LOI
poisson@0.925       giu dau, manh them ~19%
```

Doi chieu chinh thuc: Lesson 23.20, gate G23-98, G23-99.

## 6. Co che thuc thi kem theo amendment nay

Amendment nay khong dua tren ky luat ca nhan. No duoc gan vao ba co che:

```text
docs/phase-23/axis_registry.json   nguon su that duy nhat cho nhan truc;
                                   `approved_for_live` hien RONG.
measurements/validity.py           sinh khoi `validity` bang cach BAM ma nguon
                                   bo sinh z -- nhan duoc SUY, khong duoc KHAI.
test/test_no_stale_axes.py         chan artifact truc chua duyet vao
                                   results/LIVE/. Chay trong CI.
```

## 7. Dieu kien go nhan

Nhan `CONDITIONAL_ON_DSYNC_51MS` duoc go khi va chi khi:

```text
- Lesson 23.20 hoan tat
- gate G23-97 (negative control bit-exact) PASS
- bang CU vs MOI duoc cong bo day du trong docs/phase-23/23-*.md
- nhan truc moi duoc them vao axis_registry.json `approved_for_live`
  QUA MOT AMENDMENT RIENG
```

## 8. Sao luu du lieu Hang 1 (khong tai tao duoc)

```text
File     : ~/archive/dt4n-raw-measurements-20260822.tar.gz   (105 MB, 5.888 muc)
SHA256   : a97fa0a5ebecb21ed90f85b35be14175c18f68e5181d41e8b2885c631167eceb
Noi dung : phase-23/aoi_v7_campaign (427 MiB giai nen), raw_differential,
           raw_differential_v2, phase-L/raw, phase-L/golden, phase-T/raw,
           phase-T/sealed, phase-20R/raw_additivity_* (ca 8 bien the)
```

Ban sao NGOAI may (Zenodo -> DOI) **chua thuc hien** -- can tai khoan cua
nguoi dung. Gate G23-74 giu trang thai MO cho den khi DOI duoc dan vao muc
"DOI raw data" o dau file nay. Cho den luc do, du lieu Hang 1 van nam tren
mot o cung duy nhat va do la rui ro R-v3-1 chua dong.

Chu ky: ____________

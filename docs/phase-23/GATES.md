# GATES -- so gate Phase 23 (nguon chan ly duy nhat)

Moi gate cua Phase 23 co DUNG MOT dong o day.
Duoc kiem bang `test/test_phase23_gate_ledger.py`.
Sua bang tay; KHONG sinh tu dong (sinh tu dong se copy ca loi cua nguon).

Khoa boi Amendment 23-26 muc 7 (`docs/phase-23/00za-amendment-26.md`).

## Tu vung trang thai -- KHOA

Khong duoc them muc moi neu khong co amendment.

```text
PASS         gate dat nguong da ky
FAIL         gate khong dat, va do la mot ket qua duoc bao cao
UNDETECTED   doi chung duong khong kich hoat; KHONG duoc doc la PASS
DIAGNOSTIC   ha cap theo NT-v2-1: do mot lua chon ke toan, khong phan quyet
ADJUDICATED  co tranh chap hoac doi ten, da phan xu, xem evidence
DEBT         DA DUOC DINH NGHIA nhung CHUA duoc cham o bat ky bang nao, trong
             mot lesson DA DONG. Mon no HIEN. Tap DEBT duoc GHIM trong test.
NOT_RUN      chua chay
```

## Pham vi va do tin cay cua cot `lesson`

```text
G23-1 .. G23-31   anh xa lesson DO DUOC tu file trong repo (cot evidence).
G23-32            anh xa DO DUOC (Amendment 23-25 muc 6.1).
G23-33 .. G23-73  anh xa TAM DINH (provisional). Chep tu ban ke hoach Phase 23
                  v2 song NGOAI repo; CHUA doi chieu duoc. Can tren 73 cung
                  TAM DINH. Xem Amendment 23-26 muc 7.2 -- day la mon no MO,
                  phai ra soat lai ngay khi PLAN_v2.md vao repo (K-D0b).
```

Tam `G23-1 .. G23-23` KHONG lien tuc: chi cac ma xuat hien duoi day duoc dinh
nghia o dau do trong repo. Cac so con thieu (2, 3, 6, 13, 16, 18, 19, 22)
khong ton tai va khong duoc bia ra sau nay -- neu can ma moi, dung tu 74.

| id | lesson | status | evidence |
|---|---|---|---|
| G23-1 | 23.1 | PASS | docs/phase-23/02-fallback.md:461 |
| G23-4 | 23.1 | PASS | docs/phase-23/02-fallback.md:462 |
| G23-4b | 23.1 | PASS | test/test_phase23_fallback.py |
| G23-5 | 23.1 | PASS | docs/phase-23/02-fallback.md:464 (sua boi Amd 23-4) |
| G23-14 | 23.1 | DIAGNOSTIC | PASS o v1 (02-fallback.md:466); ha cap boi Amd 23-25 muc 2 |
| G23-14b | 23.1 | PASS | docs/phase-23/02-fallback.md:467 |
| G23-14c | 23.1 | PASS | docs/phase-23/02-fallback.md:468 |
| G23-6b | 23.2 | PASS | test/test_phase23_thresholds.py |
| G23-7 | 23.2 | PASS | docs/phase-23/03-threshold-families.md:60 |
| G23-7b | 23.2 | PASS | test/test_phase23_thresholds.py |
| G23-8 | 23.2 | DIAGNOSTIC | PASS o v1 (03-threshold-families.md:62); ha cap boi Amd 23-25 muc 2 |
| G23-9 | 23.2 | PASS | test/test_phase23_thresholds.py |
| G23-9b | 23.2 | PASS | docs/phase-23/03-threshold-families.md:64 |
| G23-10 | 23.3 | DEBT | dinh nghia o 00-preregistration.md:310; chua cham o bang gate nao |
| G23-10b | 23.3 | PASS | test/test_phase23_baselines.py |
| G23-11 | 23.3 | ADJUDICATED | alias cua PC23-1; ten chuan trong repo la PC23-1 (99-gate-decision.md:50) |
| G23-12a | 23.3 | DEBT | dinh nghia o 00o-amendment-14.md:46; chua cham o bang gate nao |
| G23-12b | 23.3 | DEBT | dinh nghia o 00o-amendment-14.md:47; chua cham o bang gate nao |
| G23-12c | 23.3 | PASS | test/test_phase23_baselines.py |
| G23-20 | 23.3 | PASS | test/test_phase23_baselines.py |
| G23-21 | 23.3 | PASS | test/test_phase23_baselines.py |
| G23-21b | 23.3 | ADJUDICATED | 99-gate-decision.md; noi suy gamma B2-to-B3 bi bac bo |
| G23-21c | 23.3 | PASS | 99-gate-decision.md; min effective blocks 433 |
| G23-15 | 23.4 | DIAGNOSTIC | FAIL o v1 (99-gate-decision.md); ha cap boi Amd 23-25 muc 2 |
| G23-17 | 23.4 | DIAGNOSTIC | FAIL o v1 (99-gate-decision.md); ha cap boi Amd 23-25 muc 2 |
| G23-17a | 23.4 | ADJUDICATED | results/phase-23/g23_17a_cell_margins.json |
| G23-17b | 23.4 | ADJUDICATED | results/phase-23/g23_17b_code_sanity.json |
| G23-17c | 23.4 | ADJUDICATED | results/phase-23/g23_17c_scale_and_sla.json |
| G23-23 | 23.4 | DIAGNOSTIC | PASS o v1 (2.17e-17); ha cap boi Amd 23-25 muc 2 |
| G23-24 | 23.5A | PASS | docs/phase-23/00-preregistration.md:203-204 |
| G23-25 | 23.5A | PASS | docs/phase-23/08-studentized-and-go-debts.md:104 |
| G23-26 | 23.5A | PASS | docs/phase-23/08-studentized-and-go-debts.md:106 |
| G23-27 | 23.5A | UNDETECTED | docs/phase-23/08-studentized-and-go-debts.md:111 |
| G23-27b | 23.5A | PASS | docs/phase-23/08-studentized-and-go-debts.md:154 |
| G23-28 | 23.5A | PASS | test/test_phase23_studentized.py::test_T8_status_label_is_enforced |
| G23-29 | 23.5B | PASS | results/phase-23/aurc_go1_*.json -- 5/5 cell |
| G23-30 | 23.5B | PASS | docs/phase-23/09-aurc-and-go1.md:22-24 |
| G23-31 | 23.5C | PASS | docs/phase-23/10-go2-simultaneous.md:117-118 |
| G23-32 | 23.6 | PASS | results/phase-23/abstain_cost_*.json gates.G23-32 -- resid <= 5.6e-17, 3/3 cell |
| G23-33 | 23.6 | PASS | results/phase-23/abstain_cost_*.json gates.G23-33 -- buoc 0.02, 50 diem, 3/3 cell |
| G23-34 | 23.6 | NOT_RUN | - |
| G23-35 | 23.6 | PASS | results/phase-23/abstain_cost_*.json fallback_locations_G23_35 -- HAI diem, xem Amd 23-28 muc 1 |
| G23-36 | 23.6 | PASS | results/phase-23/abstain_cost_*.json certification_table_G23_36 |
| G23-37 | 23.7 | NOT_RUN | - |
| G23-38 | 23.7 | NOT_RUN | - |
| G23-39 | 23.7 | NOT_RUN | - |
| G23-40 | 23.7 | NOT_RUN | - |
| G23-41 | 23.7 | NOT_RUN | - |
| G23-42 | 23.7 | NOT_RUN | - |
| G23-43 | 23.8 | NOT_RUN | - |
| G23-44 | 23.8 | NOT_RUN | - |
| G23-45 | 23.8 | NOT_RUN | - |
| G23-46 | 23.8 | NOT_RUN | - |
| G23-47 | 23.8 | NOT_RUN | - |
| G23-48 | 23.8 | NOT_RUN | - |
| G23-49 | 23.9 | NOT_RUN | - |
| G23-50 | 23.9 | NOT_RUN | - |
| G23-51 | 23.9 | NOT_RUN | - |
| G23-52 | 23.9 | NOT_RUN | - |
| G23-53 | 23.9 | NOT_RUN | - |
| G23-54 | 23.10 | NOT_RUN | - |
| G23-55 | 23.10 | NOT_RUN | - |
| G23-56 | 23.10 | NOT_RUN | - |
| G23-57 | 23.10 | NOT_RUN | - |
| G23-58 | 23.10 | NOT_RUN | - |
| G23-59 | 23.11 | NOT_RUN | - |
| G23-60 | 23.11 | NOT_RUN | - |
| G23-61 | 23.11 | NOT_RUN | - |
| G23-62 | 23.11 | NOT_RUN | - |
| G23-63 | 23.11 | NOT_RUN | - |
| G23-64 | 23.11 | NOT_RUN | - |
| G23-65 | 23.12 | NOT_RUN | - |
| G23-66 | 23.12 | NOT_RUN | - |
| G23-67 | 23.12 | NOT_RUN | - |
| G23-68 | 23.12 | NOT_RUN | - |
| G23-69 | 23.12 | NOT_RUN | - |
| G23-70 | 23.12 | NOT_RUN | - |
| G23-71 | 23.13 | NOT_RUN | - |
| G23-72 | 23.13 | NOT_RUN | - |
| G23-73 | 23.13 | NOT_RUN | - |
| G23-74 | 23.17 | NOT_RUN | - |
| G23-75 | 23.17 | NOT_RUN | - |
| G23-76 | 23.17 | PASS | `results/MANIFEST.md` -- 7/7 dong LIVE co cot "Dung cho"; nguon nguoi dien: `results/_intent.json` |
| G23-77 | 23.17 | PASS | `measurements/validity.py`; goi boi `cert/build_calib_set_v2.py`, `cert/build_calib_set_v3.py` |
| G23-78 | 23.17 | PASS | `test/test_no_stale_axes.py` (3 passed, 5 skipped) + buoc "axis guard" trong `.github/workflows/tests.yml` |
| G23-79 | 23.18 | PASS | `docs/phase-23/00zy-amendment-45.md`, commit rieng 1161da2, tag `amendment-45` |
| G23-80 | 23.18 | PASS | `results/LIVE/phase-23/aoi_stall_anatomy.json` -> `T1_stall_positions.position_histogram_fraction_of_run`, 30/30 run |
| G23-81 | 23.18 | PASS | phan xu tinh bang cong thuc (nguong 0.80/0.50 khoa o amendment 23-45 muc 4): M-78 = 100% -> H1_STARTUP_TRANSIENT |
| G23-82 | 23.18 | PASS | `aoi_decomposition.json` -> `T4_d_estimate.nested_ci` (CI long nhau df=4 + CI iid + ICC) |
| G23-83 | 23.18 | FAIL | phase trong [0, T_eff] = 89.92% (96.61% sau khu bias) < 99.5%. Nguyen nhan: bias he thong +50 ms cua probe. `22-aoi-stall-anatomy.md` muc 5 |
| G23-84 | 23.18 | FAIL | ba cach lech 99.32 ms > 15 ms. Dieu tra: estimator `cycle_trace` do 20 Thing chu khong do 1 link -> dac ta sai. Cap KHOP dai luong lech 10.24 ms. `22-aoi-stall-anatomy.md` muc 5 |
| G23-85 | 23.18 | PASS | `T6_prod_verdict`: sd(p05) PROD/CLEAN = 5.79x; mo hinh lay tu CLEAN, PROD la threat to validity (han che L31 -- ban ke hoach goi la L29, va cham voi L29 cua `11-abstain-cost.md`) |
| G23-86 | 23.18b | PASS | null rang cua tinh dung (amendment 23-45b): CV quan sat 0.395182 vs null 0.394289, khoang cach 0.000893 |
| G23-87 | 23.18b | PASS | d = 115.50 ms qua 3 duong doc lap voi hang so bias, trai 13.25 ms; bias DO DUOC 53.01 ms (M-93) |
| G23-88 | 23.18b | PASS | co che vong PATCH duoc DO: Var(d)~E[d] R2=0.8410 giao truc 151.89 ms (M-98); slope theo vi tri that 3.035 ms R2=0.7120 (M-99) |
| G23-89 | 23.18b | PASS | corr(AoI,rho) TRONG link sau cat warm-up = +0.0263; giua-link -0.9134 la confounding (amendment 23-45c) |
| G23-90 | 23.18b | FAIL | KS vs Uniform[d,d+T]: D = 0.03093 > 0.03. Nguyen nhan XAC DINH o Lesson 23.19 Task A: probe lay mau khoa tuong uoc (luoc 5 rang), KHONG phai alpha -- xem amendment 23-46 muc 2 |
| G23-91 | 23.19A | PASS | `docs/phase-23/00zzc-amendment-46.md`, commit rieng, tag `amendment-46` |
| G23-92 | 23.19A | PASS | phan xu bang cong thuc (nguong khoa o amendment 23-46 muc 6): M-100 0.18063 / M-101 0.12812 / M-103 152.0 -> H7_BIASED_MUST_CORRECT |
| G23-93 | 23.19A | PASS | muc tieu selfcheck duoc hieu chinh: mo hinh hoa CA NHAC CU roi so qua probe mo phong (`23-sampling-diagnostic.md` muc 6) |
| G23-94 | 23.19A | PASS | sai so lay mau len `d`: +/-6.5 ms (95%), mo phong lai dung dieu kien do duoc |
| G23-95 | 23.19B | PASS | `aoi_model_selfcheck.json` -> `M_113_negative_control`: d=0.051, T=0.5, alpha=0, phase0=-d trung KHIT `sawtooth_age_steps` tren 3 cau hinh |
| G23-96 | 23.19B | PASS | selfcheck co suc phan biet: M-111 (dung nham `process_mode`) FAIL va M-112 (d=143.6 ms) FAIL, dung nhu du kien |
| G23-100 | 23.19B | FAIL | selfcheck M-110 chi 2/4 thong ke trong dai (mean, p05 TRONG; p50, p95 NGOAI). Nguyen nhan xac dinh: `d` lech phai, mo hinh coi la hang so -> sai o momen 3. `24-aoi-model-v7.md` muc 3 |
| G23-101 | 23.19B | PASS | M-109b: alpha tinh lai tren du lieu da cat warm-up lech ban cong bo toi da 0.970 ms (< 2 ms) |
| G23-102 | 23.19B | PASS | `measurements/aoi_model_v7.py` tach `process_mode()` (pipeline) va `instrument_mode()` (selfcheck); M-111 chung minh phan biet duoc |
| G23-103 | 23.19DE | PASS | `Z_EDGES_V7 = (0.100, 0.241, 0.366, 0.491, 0.641)` khoa o amendment 23-48 TRUOC khi nhin s(z); 4 bin 24.99-25.02%, 0.000000% ngoai dai |
| G23-104 | 23.19DE | PASS | NC-E1: `process_mode_steps(d=0.051,T=0.5,U0,phase0=-d)` bit-exact voi `sawtooth_age_steps` tren 3 cau hinh, VA `_valid_rows` trung khit |
| G23-105 | 23.19DE | PASS | NC-E2: pha CHUNG cho 8 link -- kiem dai so `allclose` sau khi tru alpha (em ruot cua S13) |
| G23-106 | 23.19DE | PASS | PC-E2: canh CU tren truc moi -> B0 [55,100) RONG 0.0%, mat 13.21% hang |
| G23-107 | 23.19DE | FAIL | PC-E1: ty trong bin chi lech ~2 diem % khi dung nham `instrument_mode` (du doan > 5). O do phan giai 4 bin cai luoc bi lam phang -> tach bach phai la RANG BUOC THIET KE, khong phai phep kiem ha nguon. `25-zedges-and-task-e-controls.md` muc 3 |
| G23-108 | 23.19DE | PASS | selfcheck chuan hoa theo mean; `mean` bi loai khoi phep kiem vi `d` fit tu no (amendment 23-48 muc 2) |
| G23-109 | 23.19E | PASS | `docs/phase-23/00zzf-amendment-49.md`, commit rieng, tag `amendment-49` |
| G23-110 | 23.19E | PASS | NC-E1 bit-exact: poisson@0.925 axis=legacy U0 5 seed -> z_s/z_bin/z_bin2/gap_true max|diff| = 0; `validate_v3` (V22-1, V22-5) PASS doc lap |
| G23-111 | 23.19E | PASS | M-121 mean(z_s) = 366.0140 ms (dai khoa 366.07 +/- 0.10) |
| G23-112 | 23.19E | PASS | M-122 ty trong bin [0.2494, 0.2499, 0.2499, 0.2509], lech lon nhat 0.089 diem % |
| G23-113 | 23.19E | PASS | M-123 hang ngoai dai = 0 |
| G23-114 | 23.19E | PASS | M-124 so block moi bin = 500 (>= 9); T=500ms << block 5s nen moi block gop hang cho ca 4 bin -- tinh chat DA CO tu v2 |
| G23-115 | 23.19E | PASS | L36 chan o KIEU du lieu: `instrument_mode` tra `InstrumentSamples`, `_valid_rows` raise TypeError; monkeypatch xac nhan chan nam TRONG pipeline |
| G23-116 | 23.19E | PASS | PC-E4: D_BASE danh dinh (8.690) -> mean(z_s) = 365.4608, M-121 FAIL dung du kien |
| G23-117 | 23.19F | PASS | `docs/phase-23/00zzg-amendment-49a.md`, commit rieng, tag `amendment-49a` |
| G23-118 | 23.19F | PASS | M-132: `d_base` la ham cua ho so -> moi ho so cung mean z, trai 0.0091 ms (< 0.01). Truoc sua: U0 357.889 vs U3 366.014 |
| G23-119 | 23.19F | PASS | `d_base_s(profile_ms, dt)` raise TypeError khi nhan scalar -- chan loi im lang do doi chu ky ham |
| G23-120 | 23.19F | PASS | PILOT M-125a 1 cell: q_hat bien 20.5032 -> 22.3289 = +8.90% (dai +5..13%), tien doan +8.56% |
| G23-121 | 23.19F | PASS | PILOT M-125b 1 cell: 4/4 bin trong +/-25%, thuc te <= 1.5%. Bon ty so z tu 1.30 den 2.38 -> bon tien doan 1.121-1.452, deu khop |
| G23-122 | 23.19F | PASS | PILOT M-126 1 cell: q_hat(B3)/q_hat(B0) = 1.604 vs tien doan 1.630, lech -1.6% |
| G23-123 | 23.20A | ADJUDICATED | `out_stem()` ban dau cho LIVE khi axis=measured; test chan 23.17 tu choi 9 artifact vi sla_axis (S14) CHUA duoc duyet. Phan xu (amendment 23-49c muc 3): LIVE chi khi MOI truc duoc duyet -> Dot 1/2/3 vao SUPERSEDED den sau Lesson 23.21 |
| G23-124 | 23.20A | PASS | ten file mang CA ho so VA truc (`calib_set_<mode>_<rho>_<profile>_<axis>`); chay U0 roi U3 khong ghi de |
| G23-125 | 23.20A | NOT_RUN | - |
| G23-126 | 23.20A | PASS | Dot 1, 16/16 job: bon cong nhanh PASS. mean_z 302.488 -> 366.023 ms, ty trong lech <= 0.31 diem %, 0 hang ngoai dai, block/bin >= 9 |
| G23-129 | 23.20A | PASS | M-125a: 8/8 cell trong +5%..+13% (do duoc +7.92%..+10.27%, tien doan +8.56%) |
| G23-130 | 23.20A | PASS | M-125b: 16/16 o dem duoc trong +/-25% (100%), lech lon nhat 2.6%. Ke ca 16 o suy bien: 32/32, lech lon nhat 6.0% |
| G23-127 | 23.20B | PASS | Dot 2 (8 job): bon cong nhanh PASS 8/8, mean_z 366.014 ms |
| G23-128 | 23.20B | PASS | Dot 3 (6 job) + M-132: U0 366.023 / U1 366.022 / U2 366.022 / U3 366.014 ms, trai 0.009 ms |
| G23-131 | 23.20B | PASS | M-131 q_hat(U3)/q_hat(U0) = 0.9878..0.9958 tren 4 cell dem duoc (dai 0.98-1.03). Ho so AoI gan nhu khong anh huong khi MUC tuoi bang nhau |
| G23-135 | 23.20B | PASS | Phep kiem hinh hoc bin: khop hinh hoc lam corr(r,lech) 0.9899 -> 0.5008 va mat don dieu; |lech|max 2.69% -> 1.56%. Phan xu PARTIAL -> L39 |
| G23-136 | 23.20B | PASS | Tang PENDING + truong `pending_on` + test tu don; doi chung duong: gia vo duyet sla_axis -> test DO doi PROMOTE |
| G23-97 | 23.20 | NOT_RUN | - |
| G23-98 | 23.20 | NOT_RUN | - |
| G23-99 | 23.20 | NOT_RUN | - |

## Lesson da dong

```text
23.1  23.2  23.3  23.4  23.5A  23.5B  23.5C
```

Gate thuoc mot lesson trong danh sach nay KHONG duoc mang trang thai `NOT_RUN`.
Neu no chua duoc cham thi trang thai dung la `DEBT`, va mon no do bi GHIM trong
test de khong the xuat hien them mot cach im lang.

## G23-34 -- dinh nghia khong biet

```text
G23-34 nam trong tam G23-32..G23-36 cua Lesson 23.6 nhung DINH NGHIA cua no
khong co o bat ky dau trong repo, va PLAN_v2.md van chua duoc dua vao.
No GIU NOT_RUN. Bia mot dinh nghia hop ly de "cho du bang" se tao ra mot ID
gia -- te hon la de trong, vi no doc duoc bang may va trong nhu that.
Xem NT-v2-15, Amendment 23-28 muc 3.1.
```

## Mon no DEBT hien tai

```text
G23-10   "Moi baseline quet coverage [0,1] voi buoc <= 0.02"
G23-12a  "B6 nam duoi cac duong khac tren err|accept"
G23-12b  "B6-sys nam duoi cac duong khac tren err_system"
```

Ba ma nay duoc dinh nghia nhung khong xuat hien trong bang gate cua
`02-fallback.md`, `03-threshold-families.md`, `04-baselines.md`,
`05-cross-cell.md` hay `99-gate-decision.md`. Chung KHONG duoc goi la PASS chi
vi "nhin thi thay dung"; muon dong thi phai cham va ghi evidence.

## Gate tu 74 tro len

`G23-103 .. G23-108` (lesson `23.19DE`) la Task D + E.
`G23-109 .. G23-116` (lesson `23.19E`) la phan tich hop con lai.
`G23-123 .. G23-130` (lesson `23.20A`) la Dot 1 cua Lesson 23.20.
`G23-127`, `G23-128`, `G23-131`, `G23-135`, `G23-136` (lesson `23.20B`) la
Dot 2 + Dot 3 va phep kiem hinh hoc bin.
`G23-125` (ha nguon co `--axis`) NOT_RUN: bay script ha nguon chua co co do;
`conformal_v2` khong can vi no nhan `--calib`/`--out` truc tiep.

`G23-117 .. G23-122` (lesson `23.19F`) la hai sua truoc 5b va PILOT M-125
tren MOT cell -- KHONG phai ket qua cua 23.20. Ban ke hoach
danh so `G23-101 .. G23-114` nhung vung do DA duoc cap -- va cham ma thu NAM;
xem `test_no_duplicate_gate_or_limit_ids`.

`G23-91 .. G23-94` (lesson `23.19A`) la Task A cua Lesson 23.19. Ban ke hoach
23.19 danh so tu 91 den 102 (theo cach danh so cua ban ke hoach), nhung `G23-97 .. G23-99` DA duoc cap cho
Lesson 23.20 boi amendment 23-44 muc 5. Gate cua Task B..E se lay tu so 100 tro len. Day la va cham ma thu hai (truoc do la `L29`); so `LIMITS.md` van chua
duoc tao.

`G23-86 .. G23-90` (lesson `23.18b`) la vong RA SOAT cua Lesson 23.18, mo boi
amendment 23-45b (bug cong thuc null) va 23-45c (sua ket luan T5).

`G23-74 .. G23-78` mo o Lesson 23.17; `G23-79 .. G23-85` o Lesson 23.18
(`22-aoi-stall-anatomy.md`, amendment 23-45). `G23-83` va `G23-84` la FAIL
duoc BAO CAO, khong phai NOT_RUN: ca hai da chay, ket qua duoi nguong, va
nguyen nhan da xac dinh trong bao cao lesson.
`G23-74 .. G23-78` mo o Lesson 23.17 (`21-freeze-label-tidy.md`,
amendment 23-44). `G23-97 .. G23-99` la gate DU KIEN cua Lesson 23.20, duoc
ghi truoc trong amendment 23-44 muc 5 de du doan khong the sua sau khi thay
so. Chung KHONG lien tuc voi dai 24..73 va khong nam trong rang buoc day du
cua dai do.

G23-74 va G23-75 con MO vi ca hai can thong tin xac thuc cua tac gia (tai
khoan Zenodo de lay DOI; credential git de push tag). Chung khong duoc cham
PASS thay mat tac gia.

## Ghi chu ve pham vi ID

So nay chi chua ID dang `G23-*`. Cac ho ID khac -- `PC23-*`, `NC23-*`, `V23-*`,
`L2*`, `S*`, `C23v2-*`, `NC23v2-*` -- thuoc tu vung khac (doi chung, gioi han)
va KHONG duoc tron vao day. Mot so, mot loai ID. Neu can, tao `CONTROLS.md` va
`LIMITS.md` rieng.

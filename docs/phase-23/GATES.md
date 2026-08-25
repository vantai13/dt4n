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
| G23-126 | 23.20A | PASS | Dot 1, 16/16 job: bon cong nhanh PASS. mean_z 302.488 -> 366.023 ms, ty trong lech <= 0.31 diem %, 0 hang ngoai dai, block/bin >= 9 |
| G23-129 | 23.20A | PASS | M-125a: 8/8 cell trong +5%..+13% (do duoc +7.92%..+10.27%, tien doan +8.56%) |
| G23-130 | 23.20A | PASS | M-125b: 16/16 o dem duoc trong +/-25% (100%), lech lon nhat 2.6%. Ke ca 16 o suy bien: 32/32, lech lon nhat 6.0% |
| G23-127 | 23.20B | PASS | Dot 2 (8 job): bon cong nhanh PASS 8/8, mean_z 366.014 ms |
| G23-128 | 23.20B | PASS | Dot 3 (6 job) + M-132: U0 366.023 / U1 366.022 / U2 366.022 / U3 366.014 ms, trai 0.009 ms |
| G23-131 | 23.20B | PASS | M-131 q_hat(U3)/q_hat(U0) = 0.9878..0.9958 tren 4 cell dem duoc (dai 0.98-1.03). Ho so AoI gan nhu khong anh huong khi MUC tuoi bang nhau |
| G23-135 | 23.20B | PASS | Phep kiem hinh hoc bin: khop hinh hoc lam corr(r,lech) 0.9899 -> 0.5008 va mat don dieu; |lech|max 2.69% -> 1.56%. Phan xu PARTIAL -> L39 |
| G23-136 | 23.20B | PASS | Tang PENDING + truong `pending_on` + test tu don; doi chung duong: gia vo duyet sla_axis -> test DO doi PROMOTE |
| G23-125 | 23.20C | PASS | 3/7 script ha nguon nhan `--calib-template` (mac dinh None = giu duong cu). Bon script kia da nhan duong dan tuong minh, khong can sua |
| G23-137 | 23.20C | PASS | Doi chung am ha nguon: `eight_cell_sweep` chay mac dinh tai tao ban cu, moi gia tri bit-exact (chi khac chuoi duong dan do phan tang 23.17) |
| G23-138 | 23.20C | PASS | Bang 3 + doi chieu M-127..M-130: 1/4 HIT, bao cao NGUYEN kem giai thich (L34: noi suy tuyen tinh qua 124 ms tren artifact SENSITIVITY_ONLY) |
| G23-139 | 23.20C | PASS | P23-A, L11, L13 DONG; L37..L41 ghi vao LIMITS.md |
| G23-140 | 23.20C | PASS | Nhan CONDITIONAL_ON_DSYNC_51MS GIU nguyen: `approved_for_live` con rong vi truc SLA (S14) chua sua. `30-close-23-20.md` muc 4 |
| G23-141 | 23.20C | PASS | Dot 4 da chay 12/12 build, moi build qua G1..G4; `results/RUN_LEDGER_wave4.json`, digest `results/RAW/phase-21R/WAVE4_DIGESTS.json` |
| G23-142 | 23.20C | PASS | M-125a mo rong 12/12 cell HIT (+7.916%..+10.886%); M-125b 48/48 o HIT, 32/32 o dem duoc HIT, max lech 3.464%; `axis_remeasure_impact_wave4.json` |
| G23-97 | 23.20 | ADJUDICATED | ma DU KIEN ky truoc o amendment 23-44 muc 5; noi dung DA chay duoi ma khac. Alias -> `G23-137` (doi chung am ha nguon, bit-exact). Phan xu: amendment 23-51 muc 4 |
| G23-98 | 23.20 | ADJUDICATED | ma DU KIEN; noi dung DA chay duoi `G23-129` + `G23-130` (M-125a 8/8, M-125b 16/16). Phan xu: amendment 23-51 muc 4 |
| G23-99 | 23.20 | ADJUDICATED | ma DU KIEN; noi dung DA chay duoi `G23-138` (Bang 3 + doi chieu M-127..M-130, bao cao ca MISS). Phan xu: amendment 23-51 muc 4 |
| G23-143 | 23.20D | PASS | `L21` phan xu: `00s-amendment-18.md:139` cap ma moi `L43`; `KNOWN_OPEN` rong; `test_no_duplicate_limit_ids` xanh ma khong con mien tru |
| G23-144 | 23.20D | PASS | Anh xa song o HAI noi (`ADJUDICATED_ALIAS` + bang `LIMITS.md`) va bi khoa vao nhau. DC1: go dong `\| L43 \|` khoi bang -> `test_adjudicated_aliases_are_documented` DO. Ban nhap dau chi kiem `"L43" in txt` va DC1 KHONG do (chuoi con trong van xuoi) -> da siet thanh kiem DONG BANG |
| G23-145 | 23.20D | PASS | DC2: lam hong manh 40 ky tu -> `test_adjudicated_alias_fragments_still_match_a_real_line` VA `test_no_duplicate_limit_ids` cung DO. DC3: go han anh xa -> `test_no_duplicate_limit_ids` DO (va cham quay lai). Khoi phuc -> 6 passed |
| G23-146 | 23.20D | PASS | `docs/phase-23/00zzm-amendment-50.md` la commit RIENG, co tag `amendment-50`, TRUOC moi code chay thi nghiem cua Lesson 23.21 |
| G23-147 | 23.20E | PASS | Va cham thu SAU (`G23-135`/`G23-136` trong `30-close-23-20.md`) phan xu -> `G23-141`/`G23-142`. Anh xa song o bang GATES.md VA `ADJUDICATED_GATE_TYPO`, khoa boi `test_adjudicated_gate_typos_are_documented` |
| G23-148 | 23.20E | PASS | `test_gate_status_is_consistent_across_documents` tim them BON do lech trang thai (`G23-123`; `G23-15`/`G23-17`/`G23-23`) ma kiem toan bang mat khong thay; ca bon da phan xu vao `ADJUDICATED_STALE_STATUS` |
| G23-149 | 23.20E | PASS | `G23-97 .. G23-99` (ma DU KIEN ky truoc o amendment 23-44) dong vong lap -> ADJUDICATED, evidence tro toi `G23-137` / `G23-129`+`G23-130` / `G23-138` |
| G23-150 | 23.20E | PASS | `CLOSED_LESSONS` + `PINNED_DEBT` lap dan: `23.20*` vao danh sach, `G23-141`/`G23-142` -> DEBT va duoc ghim. `test_no_closed_lesson_gate_is_still_not_run` xanh |
| G23-151 | 23.20E | PASS | `test_prose_in_ledger_does_not_restate_status`: van xuoi GATES.md khong con phat bieu trang thai. Da sua mau thuan `G23-125` (bang PASS vs van xuoi NOT_RUN) |
| G23-152 | 23.20E | PASS | `docs/phase-23/CONSTANTS.md` (so thu BA) + `test/test_constants_ledger.py` 7/7. `sd(beta) = 0.0059` tai tinh duoc tu CI bootstrap Phase 22; chat hon can hau kiem `L39` khoang 3 lan |
| G23-153 | 23.21 | PASS | SLA co dinh tu ITU-T G.114, ghi o `00zzo-amendment-52.md` muc 2, ky TRUOC khi chay (tag `amendment-52`, commit `2ac8ec5`) |
| G23-154 | 23.21 | PASS | `w_loss = 5000` = `T_delay/T_loss` (equal-budget), khoa o `CONSTANTS.md` K06; `test_w_loss_of_primary_spec_matches_constants_ledger_k06` ghim |
| G23-155 | 23.21 | PASS | sweep {1250, 5000, 20000} bao cao DU o `w_loss_sensitivity.json`; ba spec S-A/S-B/S-C deu co artifact rieng |
| G23-156 | 23.21 | PASS | `M-171`: dau cua `delta_system_vs_neo` GIU nguyen o 7/8 cell khi `w_loss` doi tu NOI SINH [1245.6, 4722.7] sang CO DINH 5000. Mot cell doi dau: `h2@0.700` (+0.000176 -> -0.002592). Bao cao NGUYEN |
| G23-157 | 23.21 | PASS | M-135: phan hoach S-B vs phan hoach `err_neo >= 0.05` trung 6/8 cell (dai da ky >= 6/8). Bang 8 cell day du o `31-exogenous-sla.md` muc 3 |
| G23-158 | 23.21 | PASS | `L40` DONG: Dot 2 da chay lai duoi SLA ngoai sinh (`eight_cell_sweep_U3_measured_v7_slaB.json`), nhan `CONDITIONAL_ON_SLA_AXIS` go. `L41` UNBLOCKED (khong con can `--prepare-sla`) nhung `live_region_sweep` CHUA chay -> `L41` giu MO |
| G23-159 | 23.21 | PASS | NC-1 muc MODULE: nap lai SLA+w_loss noi sinh cu -> 10/10 cell, `d_opt_viol` = 0.0 va `d_share` = 0.0 CHINH XAC, `d_margin` = 2.84e-14 (cong don dau phay dong, nguong 1e-9). Muc DUONG ONG con cho: 8 calib parquet khong co tren dia -- `31-exogenous-sla.md` muc 6 |
| G23-160 | 23.21 | PASS | `S_pivotal` max_dev = 0.0 qua ca ba `w_loss`. Bat bien duoc chan o CHU KY HAM (`regime_shares` khong nhan `w_loss`/`opt`), khong chi kiem o gia tri -- `test_regime_shares_signature_has_no_w_loss` |
| G23-161 | 23.21 | PASS | `role` giu semantics cu (`gate`/`pc1`/`pc1_excluded_by_q8`); ket luan moi o truong `regime`. Doi chung duong DC17: gan `role = regime` -> test DO |
| G23-162 | 23.21b | PASS | `kappa` = 0.5000 va `P(>=6/8 ngau nhien)` = 0.2143 ghi canh moi phat bieu ve `M-135` (`32-scale-ci-and-wave4.md` muc 7, `L49`) |
| G23-163 | 23.21b | PASS | CI block bootstrap (block 1000 buoc = 5 s, 200 block, 2000 draw) cho ca 10 cell kha thi -> `sla_exogenous_S-B_ci.json` |
| G23-164 | 23.21b | PASS | `AMBIGUOUS` them vao tu vung `regime`; `PIVOTAL_MIN` GIU 0.10. `h2@0.700` CI95 [0.0956, 0.1269] chua nguong -> doi nhan. 1 cell doi (M-144 HIT) |
| G23-165 | 23.21b | PASS | Quet `T_loss` 7 diem (0.001..0.100), `T_delay` giu 50 ms -> `t_loss_sweep.json`. Thay ba spec roi rac. Phat hien: moi cell co DINH RIENG, dinh TRUOT theo tai |
| G23-166 | 23.21b | PASS | Bon cell Dot 4 chay tren `sla_exogenous` -> `sla_exogenous_wave4.json`. CA BON LIVE. KHONG tra `G23-141`/`G23-142` (can calib parquet) |
| G23-167 | 23.21b | PASS | Bang hai chieu ca 8 cell, ke ca o TRONG (`32-scale-ci-and-wave4.md` muc 6). Goc tren-trai TRONG dung du kien -- khong cell nao vi pham tien doan |
| G23-168 | 23.21b | PASS | do rong CI block / iid = 7.45..11.36 lan -> bo qua tu tuong quan cho CI hep gia mot bac. Nhung `n_eff` do duoc 1551..3603 chu khong phai 500 (cong thuc AR(1) la can duoi) -> `L52` |
| G23-169 | 23.21c | PASS | Luoi `T_loss` log 1.25x, 32 diem (0.0002..0.2019), 8 cell -> `t_loss_fine.json`. Mot buoc = log2(1.25) = 0.322 |
| G23-170 | 23.21c | PASS | M-147: median \|log2(t_endo/T*)\| = **0.2216** < mot buoc luoi. M-148: 8/8 cell trong mot octave (max 0.440). `S_pivotal(T*)` thuoc [0.864, 0.993] o ca tam cell |
| G23-171 | 23.21c | PASS | Dong nhat thuc `F_min - F_max` kiem NGOAI MAU tren 26 cell cua hai luoi `rho` MOI: lech lon nhat 2.07e-03 (M-149 HIT) |
| G23-172 | 23.21c | PASS | Doi chung `sigma` = 0.020 co dinh: confound `L58` CO that (S_piv(h2@0.700) tut 70 lan) nhung KHONG lai duoc hinh dang -- ca hai luoi don dieu giam tren `h2`, vi tri dinh `poisson` bat bien o 0.850. M-152 MISS |
| G23-173 | 23.21c | PASS | Hai dinh gio KEP DUOC: `h2` o 0.625 (kep boi 0.600/0.650), `poisson` o 0.850 (kep boi 0.825/0.875). `h2@0.925`/`h2@0.960` co T* o MUT luoi -> ghi "KHONG KEP DUOC", T* la can duoi |
| G23-174 | 23.21c | PASS | Phan quyet: KHONG co tai dung khong xac minh. Bon parquet Dot 4 (`L51`) vang mat. Snapshot ngoai repo noi glob rong, nhung checkout thuc te co 6 parquet legacy (ban dau o `results/phase-22/`, da phan tang vao `results/SUPERSEDED/phase-22/`); bao cao nguyen va CAM tai dung neu chua ghep duoc digest. Khong file legacy nao la input/output cua 16 build LIVE. 16/16 output sinh lai tu seed con tren dia va khop `output.parquet_sha256`. Artifact: `results/LIVE/phase-23/g23_174_reuse_verdict.json`. KHONG dong `L51`, `G23-141`, `G23-142` |
| G23-175 | 23.21d | PASS | `efficiency = S_piv(t_endo)/max_T S_piv` thay `S_pivotal_at_T_star` o moi phat bieu. Trung vi 8/8 cell = **0.9356**, min 0.8215. Cau vong tron da bi RUT khoi `33-ridge-alignment.md` |
| G23-176 | 23.21d | PASS | Luoi cuc bo 1.05x: buoc nhay tai diem noi suy giam 0.49 -> 0.1087 (`poisson@0.960`) va 0.99 -> 0.2489 (`h2@0.960`). Dai dau QUA HEP -> da NOI LUOI theo `G23-173`, khong goi mut la dinh |
| G23-177 | 23.21d | PASS | Doi chung `sigma` = 0.010: dinh `h2` o `rho` = 0.625 KEP DUOC hai phia (0.96076 / 0.99994 / 0.46503). Vi tri dinh BAT BIEN qua ca ba cach dat `sigma` |
| G23-178 | 23.21d | PASS | NC tai giao diem hai luoi: `h2@0.625` co `sigma(a=0.9)` = 0.02006 ~ 0.020; hai duong code khac nhau cho 0.98355 vs 0.98374, lech 1.9e-04 |
| G23-179 | 23.21d | PASS | Luoi 2D `(rho, sigma)` 10x10, ca hai ho, 134 o kha thi. Ty le o SONG = 33/134 = 0.2463. Mien song la SONG NUI CHEO: `sigma` tang -> mien truot sang `rho` cao hon |
| G23-180 | 23.21d | PASS | `V` tinh cho MOI cell. Dinh `V` va dinh `S_pivotal` o HAI cho khac nhau o CA HAI ho (poisson: sigma 0.046 vs 0.004; h2: (0.650,0.028) vs (0.600,0.004)). `L55` xac nhan bang DO LUONG |
| G23-181 | 23.21d | PASS | Spearman(`t_endo`, `T*`) = 0.9940 vao `CONSTANTS.md` (`K07`) kem nguon va so cap; `test_spearman_ridge_alignment_matches_ledger` ghim |
| G23-182 | 23.21d | PASS | Truong `M148_*` doi ten: `n_bracketed_and_within_one_octave` = 6, them `n_within_one_grid_step` = 7 va `n_within_one_octave` = 8 |
| G23-183 | 23.21e | PASS | `peak_diagnostics()` kiem GIA TRI o mut (`curve[0]==max or curve[-1]==max`) thay vi CHI SO `argmax`. DC29: quay ve `argmax` -> test DO |
| G23-184 | 23.21e | PASS | Phat hien CAO NGUYEN: `h2@0.960` co 22 diem cung dat 1.0000, `T_star = None`, `T_star_range = [0.21107, 0.58802]` (he so 2.786) |
| G23-185 | 23.21e | PASS | Luoi cuc bo 1.05x cho `h2@0.925`: `T*` = 0.18233, KHONG cao nguyen, KHONG o mut -> KEP DUOC. `efficiency` = 0.8837. `M-161` MISS (da ky "khong kep duoc") |
| G23-186 | 23.21e | PASS | Quet `a` thuoc {0.90, 0.95, 0.99}: `V` VAN tang o 19/20 cell toi `a` = 0.99 -> dinh `V` nam tai `a` = 1.0, tuc TREN BIEN kha thi. Khong kep duoc bang cau tao (`L64`). 0 cell doi nhan `regime` |
| G23-187 | 23.21e | PASS | Yeu cau ve `sigma_max(rho)` chong len HINH 2 duoc ghi thanh dieu kien BAT BUOC o `35-close-23-21.md` muc 5 va `L65`; du lieu `sigma_max` co san trong `sigma_rho_plane.json` (truong `sigma_max` moi hang) |
| G23-188 | 23.21e | PASS | `M-147` bao cao kem `M147_n_cells_used` = 6 va `M147_n_cells_undetermined` = 2 (`h2@0.925`, `h2@0.960` tren luoi tho). Trung vi 0.2216 |
| G23-189 | 23.21e | PASS | DC29: quay ve phep kiem `argmax` -> `test_peak_at_edge_checks_value_not_argmax_index` DO. Doi chung am kem theo: dinh THAT o trong van duoc nhan la kep duoc |
| G23-190 | 23.21f | PASS | `sla_manifest_exogenous_S-B.json` cung schema ban cu, 12 cell, `w_loss` = 5000, mang truong `validity`. Builder KHONG doi mot dong nao |
| G23-191 | 23.21f | PASS | NC muc DUONG ONG tren `poisson@0.925` U0 legacy: 156 truong so, 150 khop CHINH XAC, 5 lech <= 3.7e-13. Rieng `gap_true_pct.p90` lech 5.72e-06 -- co che xac dinh: `gap_true` la `float32`, khac biet numpy/dtype chu khong phai logic. `M-167` MISS, ghi `L69` |
| G23-192 | 23.21f | PASS | 16/16 build (8 cell x U0/U3) hoan tat duoi SLA ngoai sinh; artifact mang `validity.aoi_axis = measured_v7_uniform` va `validity.sla_axis = exogenous_g114_S-B` |
| G23-193 | 23.21f | PASS | `approved_for_live` co CA HAI truc -> 16 artifact len `results/LIVE/phase-21R/`. `sha256` trong registry tinh TU FILE THAT; `test_registered_sha_matches_the_file_on_disk` ghim |
| G23-194 | 23.21f | PASS | `test_close_doc_lists_every_not_run_gate_of_that_lesson`: bat ngay `35-close-23-21.md` bo sot `G23-156`/`G23-158` (`L66`). Da sua muc 6 thanh "TAI MO" va liet ke DU |
| G23-195 | 23.21f | PASS | `test_debt_dependency_graph_has_no_cycle` (DFS tim back-edge). DC30: them canh `G23-141 -> G23-158` -> test DO, tai hien dung deadlock da xay ra (`L67`) |
| G23-196 | 23.21g | PASS | Manifest khong con NAM truong phai sinh (`opt_viol_rate`, `in_band`, `cost_margin_mean_ms`, `cost_margin_p10_ms`, `opt_path_share`). `M-174` = 0 truong sot. `NT 50`: xoa theo NGHIA |
| G23-197 | 23.21g | PASS | `config` khong con BAY khoa fixpoint (`target_viol`, `n_bisect`, `n_fixpoint`, `p_hi`, `p_lo`, `tol_w`, `viol_band`). Het tu mau thuan voi `endogenous: false` |
| G23-198 | 23.21g | PASS | `build_calib_set_v3` ghi khoi `output` voi `parquet_sha256` tinh tren BYTE THAT tren dia sau flush. Dong `G23-174` phan "luu duoc van tay" |
| G23-199 | 23.21g | PASS | Van tay chung to gia tri NGAY: hai lan chay (float32 vs float64) cho CUNG `parquet_sha256` `5d95343a...` -> du lieu BIT-IDENTICAL, lech `p90` nam o phep tinh trong report chu khong o du lieu |
| G23-200 | 23.21g | FAIL | `M-173` max\|diff\| = 5.72e-06, khong dat nguong da ky `< 1e-9`. Gia thiet float32 BI BAC BO (`L71`): ep float64 lam viec tai lap TE HON. Da hoan nguyen. Nguyen nhan `p90` CHUA xac dinh. Bao cao NGUYEN, KHONG noi nguong |
| G23-201 | 23.21g | PASS | `test_no_two_reports_claim_the_same_parquet`: khong hai report nao cung khai mot parquet -- chan loi `out_stem` tro nham tang da xay ra o amendment 23-49c |
| G23-202 | 23.21i | FAIL | NC am `decision_error_v2` chay KHONG co: nguong da ky `equals == True` tren cot chung KHONG dat. Thuc te: BIT-EXACT tren 19/22 cot (moi cot muc quyet dinh: `err_total`, `err_model`, `err_stale`, `d_sla`), lech <= 3.11e-15 tren `rms_e_model`/`rms_e_stale`/`cov_e`. Ban LIVE cu KHOP digest tien dang ky 21R (`5e4d4797...`) nen KHONG phai nham file -- dung hien tuong `L71`. Ghi `L74`, KHONG noi nguong |
| G23-203 | 23.21i | PASS | `rms_e_model`, `rms_e_stale`, `cov_e` BAT BIEN qua doi truc SLA (`w_loss` noi sinh 9 gia tri -> 5000 ngoai sinh): max\|diff\| = **0.0 dung bang khong**, 450/450 hang ghep cap. Co che CAU TRUC: chung tinh tren delay thuan, khong qua ham chi phi. Hinh phan ra sai so + con so thu 4 cua abstract MIEN NHIEM voi S14 |
| G23-204 | 23.21i | ADJUDICATED | Dang DA KY (tap `d_sla ~ 0` TRUNG tap `COLLAPSED`) FAIL 4/5: (a) ba cell `TRIVIAL` cung cho `d_sla = 0` (0-0, cung co che cau truc voi 1-1), (b) `poisson@0.925` co `S_collapsed = 0.9913 != 1` nen `d_sla = 3.0e-03`. Gia thuyet nhi phan BI BAC BO. Dang SUA LAI la bat dang thuc `max\|d_sla\| <= S_pivotal`: **PASS 10/10 cell tren moi z**; phan tach LIVE vs KHONG-LIVE hoan toan, khoang cach 25.7 lan |
| G23-205 | 23.21i | PASS | `test_every_live_parquet_has_a_validity_sidecar`: moi `.parquet` trong `LIVE/` phai co `<ten>_report.json` mang `validity`. Doi chung duong: giau `truth_table_report.json` -> DO dung file do; tra lai -> XANH. Bit lo hong goc: cai chan cu chi glob `*.json` |
| G23-206 | 23.21i | PASS | DOI CHUNG DUONG cho chinh bo test. Sau khi bit PASS RONG (`if "validity" not in payload: skip`), chay TRUOC khi sinh `validity`: **16 failed** -- dung bang so file `PENDING/` khong co `validity`. Nguong da ky `>= 16` |
| G23-207 | 23.21i | PASS | Promote len `LIVE/phase-23/` 7 artifact co nhan SUY RA = `exogenous_g114_S-B` (doi chieu NOI DUNG bo ba `t_delay/t_loss/w_loss` voi manifest). `S-A`/`S-C` va 5 quet SPAN truc nhan `UNREGISTERED` va O LAI -- dung, khong phai thieu sot |
| G23-208 | 23.21i | PASS | Ha `eight_cell_sweep_U3_measured_v7.json` xuong `SUPERSEDED/phase-23/` (w_loss noi sinh 8 gia tri, truc S14). Ly do bang van ban o `37-pending-tier-adjudication.md` muc 5 |
| G23-209 | 23.21i | FAIL | `PENDING/` KHONG rong: con 9 file. Khong phai viec chua xong -- la phat hien ve THIET KE TANG: `PENDING/` gop ca "dang CHO duyet" lan "CO Y ngoai truc chinh" (canh do nhay `S-A`/`S-C`, 5 quet SPAN truc). Loai sau khong bao gio "toi luot". De xuat tach `CONTROLS/`, can amendment rieng |
| G23-215 | 23.21i | PASS | Phan quyet bang van ban: `L51` (tai lap QUA KHU) != `M-136` (mot BAT BIEN). `M-136` khong bi chan boi parquet lich su -- nhung xem `G23-217`: no bi chan boi mot thu KHAC. DINH CHINH sau review: digest lich su VAN CON; trong 9 parquet input (8 calib + truth), 4 dung duoc, 4 vang mat, 1 da doi noi dung. Van ban Threats to Validity sua o `39-l51-adjudication.md` muc 6 |
| G23-216 | 23.21i | NOT_RUN | - |
| G23-217 | 23.21h | NOT_RUN | - |
| G23-212 | 23.21h | NOT_RUN | - |
| G23-212a | 23.21h | PASS | Doi chung am cho patch Viec 3, dang TUONG DUONG DUONG CODE (khong phai tai tao so LICH SU). `tools/g23_212a_partial_nc.py`, 8/8 cell, bo calib phase-21R (tu nhat quan voi manifest S-B, `parquet_sha256` ghim o ca hai ve). Ve A: `results/RAW/phase-23/g23_212a_before.json`, 2340 truong, NHOM A lech 0 / NHOM B lech 0. Doi chung duong: nhieu 1e-15 vao mot truong NHOM A -> bat duoc. GIOI HAN: hai ve co the cung sai; gate nay KHONG chung minh manifest dung, chi chung minh patch khong doi ha nguon |
| G23-219 | 23.21i | PASS | Tieu chi bit-exact phai PHAN NHOM. NHOM A (so nguyen/bool -> `.mean()` cua 0/1): bit-exact KHA CHUYEN, ky `== 0`. NHOM B (`rms_e_model`/`rms_e_stale`/`cov_e` -- float qua PHEP THU GON tren mang 2-D): KHONG kha chuyen. Bang chung LIEN MOI TRUONG: numpy 2.2.6 -> 3.11e-15, numpy 2.4.4 -> 0.0, cung commit cung artifact. Co che tai hien duoc: tren mang (200000,4), doi thu tu thu gon (axis=0 / axis=1 / toan mang / Fortran-order) sinh lech 4.44e-16..8.44e-15 -- dung dai da quan sat. Chan de xuat `32*eps*sqrt(n)*|v|` = 1.18e-11, du 3 bac |
| G23-220 | 23.21j | NOT_RUN | - |
| G23-218 | 23.21i | PASS | `test_no_hardcoded_missing_parquet` (lint AST). So dong DO lan quet DAU TIEN: **29**. Sau khi loc mau `{}`/`%s`, glob `*`, duoi khong co `/`: 16 = 12 `KNOWN_DANGLING` (8 parquet Phase 22 that su mat) + 4 `OUTPUT_PATHS`. Doi chung duong: bo 1 muc -> DO dung hai dong tro toi file do |
| G23-221 | 23.21j | PASS | Sau backup 23/23 parquet (SHA mismatch 0), `chmod -R a-w results/SUPERSEDED results/RAW`. `test_closed_evidence_tiers_are_read_only` quet de quy moi write bit user/group/other; doi chung truoc chmod DO |
| G23-222 | 23.21j | PASS | Them marker `custody`; tach presence khoi content drift. Suite portable/CI chay `not custody`; may tac gia chay rieng `-m custody`. Meta-test buoc moi presence check phai mang mark |
| G23-223 | 23.21j | PASS | Mtime rieng le khong nang duoc file thanh ORIGINAL. Bang chung manh hon giai thich di thuong: `os.replace` giu mtime NGUON; report timestamp + git/builder hash ghep bon file vao lo 13/08. L82 doi sang VERIFIED_SUPERSEDED_GENERATION, khong phai ORIGINAL |
| G23-224 | 23.21j | PASS | `tier_results.py` preflight TAT CA dich truoc moi mutation/map-out; dich co san hoac dich lap trong plan -> return 2 va in chi tiet. Bo `git mv -f`; file ignored dung hard-link + unlink no-replace, nen ca va cham xuat hien sau preflight cung fail. DC duong: dich gia giu nguyen ca source/destination va khong tao map; 3 test xanh |
| G23-225 | 23.21j | PASS | Lint AST tren `cert/`, `measurements/`, `tools/`: moi legacy `(mode,rho_bar)` chi co mot parquet literal. DC L85 voi `calib_set_v3.parquet` + `_poisson_0.925.parquet` -> DO. Da sua `phase23_cell_margins`; 3 regression test doi chieu artifact G23-17a/b/c cu voi canonical moi co 0 khac biet so hoc |
| G23-226 | 23.21h | PASS | Wave 4: 12/12 job qua G1..G4; 12 parquet + 12 report; digest ghim tai `results/RAW/phase-21R/WAVE4_DIGESTS.json`; backup logic 12/12 SHA khop tai `C:\\Users\\VAN TAI\\dt4n-evidence-backup-2026-08-24` |
| G23-210 | 23.21h | PASS | Manifest 14 cell = 10 feasible base + 4 Dot 4, 14 feasible/14 unique, w_loss=5000, 0 fixpoint/derived/ngoai whitelist; sha256 `6e97ac054cce76284db3a7d3f674440408ee6f9f073c1e627b67a2bdbd1eae2d` |
| G23-211 | 23.21h | PASS | `--prepare-sla` fail-loud kem huong dan thay the; `--calib-template` duoc forward that; xoa debt L72 cua `live_region_sweep`; test CLI/locked controls xanh |
| G23-212b | 23.21h | PASS | NC am bat buoc: 8 cell, 2340 truong chung, chi mot ve 0, NHOM A lech 0, NHOM B lech 0; `results/RAW/phase-23/g23_212b_after.json` |
| G23-227 | 23.21h | PASS | `NC_H truth_domain_check` chay 4/4 cell Dot 4 truoc build, 4/4 PASS; fallback duoc ghi `None` (khong ap dung), khong ep thanh `False` |
| G23-213 | 23.21h | PASS | Sweep S-B sinh du 12 cell va bang A/B; M-176=10/12, M-177=0.925, M-178=0.257012/0.252413, M-179=1.281290; artifact `live_region_sweep_slaB.json`. M_57 va M_47b MISS, bao cao nguyen |
| G23-214 | 23.21h | PASS | `regime` tinh lai tu shares/CI khop nhan authoritative `sla_exogenous_S-B` + `wave4` tai 12/12 cell |
| G23-228 | 23.21h-close | PASS | Clean replay tu HEAD `6aa08c8`: artifact v3 `git_dirty=false`, hash khop HEAD; so commit `08b6879` co `cells` 3564 leaf, `metrics` 31 leaf, `live_definition_table` 60 leaf deu bit-exact, 0 mismatch. `results/RAW/phase-23/g23_228_clean_replay.json` |
| G23-229 | 23.21h-close | PASS | p@.900 co 2/5 fold chon F6, selected-F2 = 0; ep F2b/P3 qua cung `_risk_summary` cho chenh `+0.012923831842096334`, nen selection wired va F6=F2 la suy bien tren mau. `results/RAW/phase-23/g23_229_family_selection_control.json` |
| G23-230 | 23.22 | PASS | 12/12 cell chay (3 MAIN + 9 ROBUSTNESS), `git_dirty=false`, `git_hash=7c231518`, `validity` hop le (aoi=`measured_v7_uniform`, sla=`exogenous_g114_S-B`), `n_boot=2000`. Artifact `results/LIVE/phase-23/taxonomy_audit.json` |
| G23-231 | 23.22 | FAIL | M-182 3/3 (ti so block 1.0926 / 1.0929 / 1.1458 -- **H-B XAC NHAN**: 4.00x HANG nhung chi 1.09-1.15x BLOCK). Nhung M-181 chi 2/3: `h2@0.700` cho 436.4 block/o, duoi dai da ky [440,500]. Nguong doi CA HAI 3/3 -> FAIL. KHONG noi dai |
| G23-232 | 23.22 | PASS | M-184 2/3 va M-185 2/3, dat nguong >=2/3. Ca hai cung MISS o DUNG mot cell `poisson@0.850` (spread_m=1.0286 < 1.05; M-185=1.0157 < 1.10) |
| G23-233 | 23.22 | FAIL | M-186 **0/3**. Do duoc 1.0639 / 1.0124 / 1.0015, dai da ky [0.50, 1.00]. Du doan '4x hang mua duoc do on dinh' BI BAC BO. Kem mot canh bao ve chinh phep do -- xem `L90` |
| G23-234 | 23.22 | FAIL | M-187 2/3 (`poisson@0.850` MISS: V-N=0.0822 KHONG vo). Tren 12 cell chi 4 cell co V-N vo. Nguong 3/3 -> FAIL. Theo amendment muc 4.2, day la BAC BO H-A o dang manh tren truc moi |
| G23-235 | 23.22 | PASS | 3/3: `acceptance == 1.0` o ca ba bien the, va V-N === V-S TRUNG BIT (`|dviol| = 0.0e+00`, `|dqhat| = 0.0e+00`). Nhan **[SUA SAU KHI XEM]** -- tieu chi ban dau bat mot dieu SAI, da sua truoc lan chay that; KHONG dem diem |
| G23-236 | 23.22 | PASS | 2/3, dat nguong >=2/3. V-M vo bao phu o kappa=2 tren `poisson@0.925` (0.1812) va `h2@0.700` (0.1345); KHONG vo tren `poisson@0.850` (0.0829). Ket qua Lesson 22.4 chuyen sang truc moi o 2/3 cell |
| G23-237 | 23.22 | PASS | Cai gia cua V-S da bao cao khong lam tron: `acceptance(V-S)/acceptance(V-M)` = 0.7354 / 0.7793 / 0.8022 -- V-S nhan it hon 20-27% |
| G23-238 | 23.22 | PASS | 9/9 cell robustness chay va bao cao. Khong cell nao duoc dung de chon ket luan chinh; chung chi dung de MO RONG mau cho M-187 (4/12 cell co V-N vo) |
| G23-239 | 23.22 | NOT_RUN | - |
| G23-240 | 23.22 | NOT_RUN | - |
| G23-241 | 23.22 | NOT_RUN | - |
| G23-242 | 23.22 | NOT_RUN | - |
| G23-243 | 23.22 | NOT_RUN | - |
| G23-244 | 23.22 | NOT_RUN | - |
| G23-245 | 23.22 | NOT_RUN | - |

## Va cham da phat hien

Song song voi muc cung ten trong `LIMITS.md`. Ho `G23-*` cung mac benh nhu ho
`L*`: mot ma duoc dung cho hai viec o hai tai lieu.

### G23-135 / G23-136 -- `30-close-23-20.md` dung NHAM ma

```text
GATES.md + 29-waves-2-3-and-bin-geometry.md:145-146
  G23-135  phep kiem HINH HOC BIN            <- nghia DUNG
  G23-136  tang PENDING + `pending_on`       <- nghia DUNG

30-close-23-20.md:152-153
  G23-135  "Dot 4: 12 build"                 <- ma SAI, dung phai la G23-141
  G23-136  "M-125a/b mo rong 12 cell / 48 o" <- ma SAI, dung phai la G23-142
```

NOI DUNG cua hai dong trong `30-close-23-20.md` la DUNG (ca hai viec do that su
chua chay, bi chan boi S14). Chi MA la sai. Hau qua: doc van ban DONG lesson,
nguoi ta ket luan phep kiem hinh hoc bin chua chay -- trong khi no da chay va
da sinh ra `L39`.

| ma bi dung nham | trong file | ma dung | phan xu tai |
|---|---|---|---|
| `G23-135` | `30-close-23-20.md` | `G23-141` | `00zzn-amendment-51.md` |
| `G23-136` | `30-close-23-20.md` | `G23-142` | `00zzn-amendment-51.md` |

Ma o cot dau duoc boc BACKTICK co chu dich: `_rows()` nhan mot dong bang la
dong gate khi o dau tien khop `^G23-\d+[a-z]?$`. Khong boc backtick thi bang
phan xu nay bi doc thanh hai dong gate that -- va `test_no_duplicate_gate_id`
do ngay. Do la chuyen da xay ra o ban nhap.

### Trang thai CU con sot lai trong tai lieu da ky

Khac loai voi tren: MA dung, nhung TRANG THAI la trang thai dung tai thoi diem
VIET, roi gate bi phan xu lai sau do. Tai lieu da ky nen khong sua.

| ma | trong file | o doc | dung | phan xu tai |
|---|---|---|---|---|
| `G23-123` | `28-axis-remeasure-impact.md` | `PASS` | `ADJUDICATED` | `00zzi-amendment-49c.md` |
| `G23-15` | `99-gate-decision.md` | `FAIL` | `DIAGNOSTIC` | `00z-amendment-25.md` |
| `G23-17` | `99-gate-decision.md` | `FAIL` | `DIAGNOSTIC` | `00z-amendment-25.md` |
| `G23-23` | `99-gate-decision.md` | `PASS` | `DIAGNOSTIC` | `00z-amendment-25.md` |

`G23-123`: bao cao Dot 1 viet TRUOC khi amendment 23-49c phan xu viec
`out_stem()` tro nham tang.

`G23-15`/`G23-17`/`G23-23`: Lesson 23.6 (`06-reframe.md` muc 5) HA CAP nam gate
xuong `DIAGNOSTIC` khi tai khung fallback thanh tham so ngoai sinh.
`99-gate-decision.md` giu trang thai truoc tai khung. Nhu `06-reframe.md` ghi
ro: KHONG mot con so nao bi rut lai, chi doi VAI TRO.

Bon dong nay KHONG nam trong ban kiem toan ban dau; ca bon do
`test_gate_status_is_consistent_across_documents` tim ra trong hai lan chay dau.

`30-close-23-20.md` DA KY nen KHONG duoc sua. Anh xa song o HAI noi -- bang
tren va `test/test_phase23_gate_ledger.py :: ADJUDICATED_GATE_TYPO` -- va
`test_adjudicated_gate_typos_are_documented` bat buoc hai noi phai khop.

## Lesson da dong

```text
23.1  23.2  23.3  23.4  23.5A  23.5B  23.5C
23.20  23.20A  23.20B  23.20C  23.20D
```

Gate thuoc mot lesson trong danh sach nay KHONG duoc mang trang thai `NOT_RUN`.
Neu no chua duoc cham thi trang thai dung la `DEBT`, va mon no do bi GHIM trong
test de khong the xuat hien them mot cach im lang.

Tieu chi vao danh sach nay la CO MOT TAI LIEU TUYEN BO DONG, khong phai "cac
gate tinh co deu xanh". Den 2026-08-23 chi `30-close-23-20.md` tuyen bo `DONG`,
nen chi ho `23.20*` duoc them. Cu the, `23.17` KHONG duoc them du gate cua no
gan het da cham: `G23-74`/`G23-75` con MO mot cach chinh dang (can thong tin
xac thuc cua tac gia), va them `23.17` vao day se ep chung sang `DEBT` --
tuc bien mot viec dang cho thanh mot mon no, sai ban chat. `23.18`, `23.18b`,
`23.19*` cung chua co tai lieu dong.

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
`G23-125`, `G23-137 .. G23-142` (lesson `23.20C`) la tich hop ha nguon va
dong Lesson 23.20. `G23-141`/`G23-142` phu Dot 4 va viec mo rong M-125 len
12 cell / 48 o; ca hai da duoc dong o Lesson 23.21h sau khi S14 bi thay.
`G23-125` phu viec cho ha nguon nhan duong dan calib tuong minh;
`conformal_v2` khong can vi no nhan `--calib`/`--out` truc tiep.

`G23-196 .. G23-201` (lesson `23.21g`) mo boi amendment 23-58: xoa truong
PHAI SINH khoi manifest, ghi van tay parquet DAU RA, va ep float64.
`G23-198`/`G23-199` dong `G23-174`. KE TIEP `G23-195`.

`G23-190 .. G23-195` (lesson `23.21f`) mo boi amendment 23-57: pha DEADLOCK
so sach giua `G23-158` va `G23-141`/`G23-142`, va dung hai cai chan de lan
sau khong xay ra duoc. KE TIEP `G23-189`.

`G23-183 .. G23-189` (lesson `23.21e`) mo boi amendment 23-56: sua phep kiem
dinh-o-mut cho truong hop CAO NGUYEN, va rut hai phat bieu chua chung minh
duoc (vi tri dinh `V`, chieu truot mien song). KE TIEP `G23-182`.

`G23-175 .. G23-182` (lesson `23.21d`) mo boi amendment 23-55: sua dai luong
vong tron, dao nghia tieu chi thu cap, va chuyen tu TRUC `rho` sang MAT PHANG
`(rho, sigma)`. KE TIEP `G23-174`.

`G23-169 .. G23-174` (lesson `23.21c`) mo boi amendment 23-54: song nui
`T_loss`, dong nhat thuc `S_pivotal`, va tach confound `sigma`. KE TIEP `G23-168`.

`G23-162 .. G23-168` (lesson `23.21b`) mo boi amendment 23-53: doc lai ket qua
23.21 (thang do bi bien chan, khoang tin cay, phan loai hai chieu). Chung KE
TIEP `G23-161`. Trang thai cua `G23-141`/`G23-142` trong bang KHONG doi:
chung can calib parquet ma `sla_exogenous` khong dung den, nen viec chay bon
cell moi khong tra duoc hai mon do.

`G23-153 .. G23-161` (lesson `23.21`) mo boi amendment 23-52: SLA ngoai sinh.
Chung KE TIEP `G23-152`. Ban thao ngoai repo danh so `G23-147 .. G23-155`,
nhung vung do DA cap cho `23.20E` o amendment 23-51 -- suyt la va cham ma thu
BAY; da doi truoc khi ky.

`G23-143 .. G23-146` (lesson `23.20D`) mo boi amendment 23-50: phan xu va cham
ma `L21` (cap `L43` cho muc `00s-amendment-18.md:139`) va khoa anh xa do vao
HAI noi. Chung KE TIEP `G23-142`, khong dung lai vung 117..122 da cap cho
`23.19F`. Amendment 23-50 KHONG dang ky truc nao va KHONG duyet truc nao --
viec dang ky truc AoI da xong o amendment 23-49c (`measured_v7_uniform`), va
truc SLA van bi TU CHOI duyet cho den Lesson 23.21 (xem `G23-140`, `L41`).

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
(`22-aoi-stall-anatomy.md`, amendment 23-45). Trang thai cua `G23-83` va
`G23-84` trong bang la mot KET QUA duoc bao cao, khong phai mot gate chua ai
cham: ca hai da chay, ket qua duoi nguong, va nguyen nhan da xac dinh trong
bao cao lesson.
`G23-74 .. G23-78` mo o Lesson 23.17 (`21-freeze-label-tidy.md`,
amendment 23-44). `G23-97 .. G23-99` la gate DU KIEN cua Lesson 23.20, duoc
ghi truoc trong amendment 23-44 muc 5 de du doan khong the sua sau khi thay
so. Chung KHONG lien tuc voi dai 24..73 va khong nam trong rang buoc day du
cua dai do.

G23-74 va G23-75 con MO vi ca hai can thong tin xac thuc cua tac gia (tai
khoan Zenodo de lay DOI; credential git de push tag). Chung khong duoc cham
PASS thay mat tac gia.


`G23-230 .. G23-238` (lesson `23.22`) mo boi amendment 23-64: do lai co so
truc `m_hat` tren truc AoI da duyet (`L89`), va thay `post="none"` bang
`post="selective"`. KE TIEP `G23-229`.

`G23-216` la mot KHE do chinh Lesson 23.21i tao ra: ke hoach cap no cho
"dung lai Dot 1, 16/16 job qua bon cong nhanh", nhung phep do do khong chay
duoc (`M-136` bi chan boi `L77`), va dai `G23-215/217/218` duoc cap bo qua no.
Nay da dang ky NOT_RUN de khong ai tai su dung ma. Phat hien boi review doc
lap 2026-08-24, va boi chinh `test_every_gate_id_mentioned_in_repo_is_in_the_ledger`
khi amendment 23-64 chi CAN NHAC ten no.

`G23-239 .. G23-244` (lesson `23.22` vong hai) mo boi amendment 23-65: sua `L91`
(nguong dung luong cua V-S), tien dang ky `M-188`, va bon doi chung cho lan chay
lai. KE TIEP `G23-238`. `G23-245` mo boi amendment 23-65b (`L93`).

## Ghi chu ve pham vi ID

So nay chi chua ID dang `G23-*`. Cac ho ID khac -- `PC23-*`, `NC23-*`, `V23-*`,
`L2*`, `S*`, `C23v2-*`, `NC23v2-*` -- thuoc tu vung khac (doi chung, gioi han)
va KHONG duoc tron vao day. Mot so, mot loai ID. Neu can, tao `CONTROLS.md` va
`LIMITS.md` rieng.

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
| G23-239 | 23.22 | PASS | M-188 **3/3** trong dai ky [0.45,1.00]: 0.5375 / 0.5315 / 0.5406 (16 o moi cell, 0 rut thuc vo han). Nhanh doc da ky: **<= 0.70 = HANG chi phoi**. Du doan HANG = 0.500, BLOCK = 0.957 -> do duoc nam sat HANG. `H-B` DUNG o tang MUC conformal nhung SAI o tang UOC LUONG: 4x hang MUA duoc ~1.9x do on dinh |
| G23-240 | 23.22 | PASS | 0/12 cell con `qhat_has_infinite` tai `kappa <= 1` sau khi sua `L91`. Truoc khi sua: 3/12 (`poisson@0.875`, `poisson@0.960`, `h2@0.650`) |
| G23-241 | 23.22 | PASS | So cell V-S suy bien tai `kappa=1` bao cao khong lam tron: **6/12 TRUOC va 6/12 SAU**. Sua `L91` KHONG doi so cell suy bien -- no doi CHAT LUONG cua `qhat` o nhung cell do (het `+inf`), khong doi so luong |
| G23-242 | 23.22 | PASS | 0 vi pham vung DONG BANG tren 12/12 cell. Chi hang V-S doi, o dung 5 cell -- va CA NAM la ROBUSTNESS (`h2@0.650`, `h2@0.925`, `h2@0.960`, `poisson@0.875`, `poisson@0.960`). Khong cell MAIN nao doi, nen `M-181..M-187` giu nguyen (da kiem: M-187 2/3 MAIN va 4/12 toan bo, truoc va sau). Ban cu nap tu git blob `1e715ff3...`, khong tu mot ban sao |
| G23-243 | 23.22 | PASS | `max |anchor_err - err_neo| = 0.000e+00` tren 12/12 cell. `taxonomy_audit` tinh `test['wrong'].mean()` tu parquet; `live_region_sweep` tinh qua duong ong fallback/objective KHAC HAN. Hai duong doc lap, trung den bit |
| G23-244 | 23.22 | PASS | M-189 **8/8** cell `A=True` co `V-N - V-S > 0`. Bon cell `A=False` (`poisson@0.700`, `h2@{0.850,0.925,0.960}`) lam doi chung am. Nhan POST-HOC, KHONG dem diem -- chi la regression control, va no cho thay phep sua `L91` khong pha gi |
| G23-245 | 23.22 | PASS | M-191 = **4** cell co `qhat_at_sample_max=true` tai `kappa=1`, trong dai ky [1,8]: `poisson@0.925` (nb=51), `poisson@0.900` (42), `poisson@0.960` (42), `h2@0.650` (58) -- deu duoi san on dinh 59. Chot chan van la `floor_blocks` (ghim boi test doc ma nguon) |
| G23-246 | 23.22 | PASS | M-192: `min_blocks_at_final_qhat` cua V-S GIAM DON DIEU theo `kappa` o **8/8** cell `A=True` (nguong >=6/8); va nguong cat tren `poisson@0.925` = **0.5**, thuoc {0.25,0.50} da ky -- doc theo DOAN LIEN TUC tu `kappa=0`. Xem `L94`: van ban da ky mo ho, doc theo `max` ca tap cho 2.0 va se MISS |
| G23-247 | 23.22 | PASS | `L95` do THANG tren artifact `b9d2774`, khong chay lai: **8/8** cell `A=True` tai `kappa=2` co `n_iter=0` va `qhat_slot1_mean` / `violation_given_accept` cua `selective` trung den chu so cuoi voi `none` (nguong >=8). VA `test_no_tool_writes_into_frozen_tiers` xanh voi tap ghim chin cong cu cua `L96` |
| G23-248 | 23.22 | FAIL | `M-193` kiem wiring. Nhanh C3 TRUNG BIT tren 8/8 o: `max abs delta` cua ca `violation_given_accept` lan `acceptance` = **0.000e+00** so voi hang V-S @`kappa=0.5` cua `taxonomy_audit.json`. Nhanh B2 truot: lech acceptance lon nhat = **0.02061** (`h2@0.650`) so voi dai da ky 0.02 -- truot 0.0006. Dai la phan vi mau tren mot tach test huu han; KHONG noi dai sau khi xem. Wiring da duoc xac minh; cai truot la dai, khong phai duong ong |
| G23-249 | 23.22 | FAIL | `M-194` T1 giua ho: trung vi drift B2 = **0.2174**, C3 = **0.2090**, ti so **1.04x** so voi nguong da ky >= 3x. Khong phai truot sat: ca hai phan phoi gan trung nhau (q1 0.1292/0.1293, q3 0.3398/0.3324, max 0.5291/0.5186). Du doan chinh cua Task B BI BAC BO -- khi mang nguyen `qhat_A` sang B, C3 troi ngang B2 |
| G23-250 | 23.22 | FAIL | `M-195` T3 giua ho: **6/30** o co `abs(viol - alpha) <= 0.05`, nguong da ky >= 20/30. Dai HAI PHIA phat ca chieu bao thu: 12/30 o co `viol < 0.05`. So mot phia (chieu bao dam): 16/30 o giu `viol <= alpha`. Con so mot phia KHONG phai tieu chi da ky va chi de mo ta |
| G23-251 | 23.22 | PASS | `M-196` T2 giua ho: trung vi `abs(err_C3 - err_B2)` tai acceptance khop = **0.00526** tren 120 diem (30 o x 4 muc), nguong <= 0.02. KET QUA AM da tien dang ky: o cung ti le chap nhan, hai phuong phap gan nhu khong khac nhau ve risk |
| G23-252 | 23.22 | PASS | `M-190` bat doi xung: trung vi `T1_drift_C3` cua (poisson->h2) = **0.2352** > (h2->poisson) = **0.1803**. `L92`: chieu nay CUNG LA (rho cao -> rho thap), nen KHONG duoc quy cho ho tai |
| G23-253 | 23.22 | PASS | `NC-1` doi chung am: tren 12 o ngoai duong cheo cua ma tran 4x4 cell chet, trung vi T1 = **0.0276** (C3) va **0.0277** (B2), nguong <= 0.05. Thiet hai do o cell song KHONG phai hien vat cua duong ong |
| G23-254 | 23.22 | FAIL | `NC-2` doi chung duong: trung vi `T1_drift_B1` = **1.19e-05**, cua B2 = **0.2174**. Score NGAU NHIEN troi it hon ca hai phuong phap that. Doi chung nay FIRE dung nhu thiet ke: thang T1 mot minh xep mot score vo dung len dau bang, nen no KHONG duoc lam thang chinh. Day la ket qua quan trong nhat cua Task B |
| G23-255 | 23.22 | PASS | `NC-3a` bat bien co uoc luong lai: nhan CA calib va test x2 roi hieu chuan lai -> `qhat_ratio = 2.0` chinh xac va acceptance C3 **0.46640864363804463 -> 0.46640864363804463**, lech dung bang **0.0**. B2 mang nguyen `c` -> lech **0.2553**. Kiem CO CHE truc tiep, tat dinh |
| G23-256 | 23.22 | PASS | `NC-3b` mang nguyen: giu `qhat_A` va `c` roi tha vao che do da gian x2 -> CA HAI troi, C3 **0.2510** va B2 **0.2553**, nguong > 0.05. Chan cach doc "C3 mien nhiem voi doi che do" |
| G23-257 | 23.22 | PASS | `M-197` cham MU tren ma tran 4x4 cell CHET. Spearman(log ti le thang, `viol` C3) = **+0.9500** (12 o ngoai duong cheo) va **+0.8915** (16 o ke ca duong cheo) -- dat nguong +0.70 duoi CA HAI cach doc, nen van ban ky mo ho khong doi phan quyet. Phan tach theo dau: `viol` trung vi nhom "`qhat` qua nho" = **0.5866**, nhom "qua lon" = **0.0200**. Ba o (`h2@*` -> `poisson@0.700`) co `n_accept = 0` nen `viol` khong xac dinh: chieu an toan bao hoa o TU CHOI TOAN BO |
| G23-258 | 23.22 | PASS | `M-198` chi bao KHONG CAN NHAN. (1) Spearman(log `median m_hat_1` tren tach TEST, log `scale qhat`) = **+0.9650** tren 12 cell, nguong >= +0.85 -- **MU**. (2) Dung ti le `m_hat` thay ti le `qhat` de du doan dau cua (`viol - alpha`): **53/56**, nguong >= 48. Menh de (2) KHONG mu (`A067` muc 6.2): bien ket qua da xem, no chi kiem phep thay the khong lam hong gi |
| G23-259 | 23.22 | PASS | `M-199` chi phi tai hieu chuan. Duoi san hop le 29 block (`n` = 10 va 20; **160** lan lay mau tren 8 cell): C3 gan co `qhat_has_infinite`/`qhat_at_sample_max` o **100%** (nguong >= 90%), B2 tra `c` HUU HAN o **100%** va gan co o **0%**. 8/8 cell HIT rieng le. C3 BIET truoc khi no khong du du lieu; B2 khong co dai luong nao de biet |
| G23-260 | 23.22 | DIAGNOSTIC | `L100`: tai `n = 30` block, ti le lan chay co `qhat_source = degenerate_fallback_to_none` (90-100%) LON HON ti le duoc hai co `L91`/`L93` bat (0-10%) tren **8/8** cell, nguong >= 6/8. POST-HOC, khong dem diem. Do la bang chung truong `qhat_source` (`A065d`) la co duy nhat con nhin thay o vung giao cua `L93` va `L95` |
| G23-261 | 23.22 | PASS | `M-200` KIEM WIRING: C3-R tai `kappa` ep bang 0.50 va `n` = 500 tai tao duong cheo `transfer_matrix.json` TUNG BIT tren **8/8** cell song -- `max abs delta acceptance` = **0.000e+00**, `max abs delta viol` = **0.000e+00**. Chay TRUOC toan bo (`A068` buoc 7). Dap an DA BIET; ma nay KHONG mang mot bit thong tin nao ve the gioi, va do la muc dich cua no (`46-recalibrate-transfer.md` muc 2) |
| G23-262 | 23.22 | PASS | `M-201` menh de bao toan song sot o `n` HUU HAN. Tai `n` = 250, tren **60/64** o co acceptance >= 0.20: `sd(viol)` = **0.00242** (<= 0.020), `sd(acceptance)` = **0.11007** (trong [0.090, 0.180]), `mean(viol)` = **0.07413** (trong [0.05, 0.12]). Ve `sd(viol)` HA CAP: dai rong gap 8 lan gia tri do duoc, xem `L103` |
| G23-263 | 23.22 | PASS | `M-202` gia cua `kappa` sai CO DAU va DU DOAN DUOC. Tai `n` = 500, 56 o ngoai duong cheo: Spearman(\|log(kappa_A/kappa_B)\|, \|acceptance_B - a\*\|) = **+0.9674** (>= +0.90) va do doc = **0.4776** (trong [0.40, 0.62]). Neo do doc -0.509 do tren CALIB cua A trong PILOT; lech **-6.2%** khi do tren TEST cua B sau tai hieu chuan. Nguong da duoc NANG tu +0.60 sau PILOT (`A068` muc 4.2) |
| G23-264 | 23.22 | PASS | `M-203` bao dam duoc KHOI PHUC HOAN TOAN. Tai `n` = 250: **60/64** o thoa tieu chi HOP (`viol` <= 0.10 VA acceptance >= 0.20), nguong >= 52. TACH VE: bao phu **64/64** (`viol` lon nhat = **0.0800** < alpha, ke ca bon o duoi san), acceptance **60/64**. Ve bao phu KHONG BIND o dau; toan bo con so hop do ACCEPTANCE quyet dinh -- xem `L104`. Bon o roi duoi san la dung bon o co \|log(kappa_A/kappa_B)\| lon nhat |
| G23-265 | 23.22 | PASS | `M-204` GIA tinh bang `n`. n\*(C3-R) = **120** (trong [60, 250]), n\*(B2-R) = **30** (<= 60), ti so = **4.00** (>= 2.0). 120 TRUNG DUNG con so cua Task B-2 TRONG CUNG CELL: mang `kappa_A` tu che do khac KHONG lam tang yeu cau co mau. n\*(B2-R) = 30 la SAN CUA LUOI nen ti so la mot CAN DUOI |
| G23-266 | 23.22 | PASS | `M-205` KET QUA AM ve `err`. Tai acceptance khop, `n` = 250, 2560 diem: trung vi \|err_C3R - err_B2R\| = **0.00549** (<= 0.02), so voi **0.00526** cua `M-196`. Dong gop cua C3 KHONG nam o risk. Trung vi GOP che mot xu the don dieu theo muc acceptance -- xem `L102` |
| G23-267 | 23.22 | PASS | `M-206` ve DOI XUNG cua menh de bao toan. Tai `n` = 250, 8 cell B: `sd(err|accept)` cua B2-R = **0.03531** (>= 0.020), cua C3-R = **0.01500** (<= 0.025). Ma duy nhat ma chinh `A068` muc 5.7 du bao se MISS (uoc luong tho 0.013). Ly do uoc luong sai da truy duoc: he so `err/anchor` cua B2-R KHONG la hang so ma chay 2.39x va CUNG CHIEU voi anchor (Spearman +0.9286) |
| G23-268 | 23.22 | PASS | `NC-B3-1` doi chung DUONG da FIRE, va manh hon du kien: B1-R (score NGAU NHIEN) trung `a*` o **8/8** cell voi \|delta\| = **0.0009** -- CHINH XAC HON B2-R (0.0123) -- va `err|accept` cua no bang **0.998 .. 1.006** lan anchor o **8/8**. 'Trung muc tieu acceptance' MOT MINH la mot thang do VO GIA TRI. `L99` lan thu TU, lan dau duoc ky TRUOC |
| G23-269 | 23.22 | PASS | `NC-B3-2` B2-R/B1-R trung BIT theo truc A tren **6/6** truong, `max abs delta` = **0.0e+00** (tinh LAI trong vong lap A, khong chep). `NC-B3-3` **4/4** cell chet sap ve anchor -- nhung nguong TUYET DOI 0.02 tren dai luong <= 0.0042 khong the fail, xem `L101`. `NC-B3-4` tai `n` = 30: `qhat_source` sup ve `none` **96.1%** vs hai co cu **3.9%** (`L100` tai lap tren luoi moi). Census `n_accept = 0`: **0/3264** |
| G23-270 | 23.22c | FAIL | `M-209`: tren PILOT S-B hop le, **0/3** rho cua luoi buoc 0.040 co ca hai ho cung `err_neo >= 0.05`, nen so cap A->B giua ho tai cung rho = **0 < 2**. Stop-rule A069 kich hoat. Pham vi: `L92` KHONG go duoc O DO PHAN GIAI 0.040; khong ket luan truc rho vo dung. Noi suy doc lap du doan cua so `[0.742,0.770]` hep hon buoc luoi; xem `L107`, `A070`. Capacity 500/500 block tren 6/6; custody 106 PASS/7 SKIP. `a069_pilot.json`; `48-a069-pilot.md` |
| G23-271 | 23.22c | NOT_RUN | - |
| G23-272 | 23.22c | NOT_RUN | - |
| G23-273 | 23.22c | NOT_RUN | - |
| G23-274 | 23.22c | NOT_RUN | - |
| G23-275 | 23.22c | NOT_RUN | - |
| G23-276 | 23.22c | NOT_RUN | - |
| G23-277 | 23.22d | PASS | `M-215` CUA SO CHONG LAN TON TAI. Tren luoi DAY buoc 0.006 niem phong (12 cell, batch digest `ddc11ba2..457e8`), **2/6** rho co CA HAI ho `err_neo >= 0.05`: `rho` = **0.744** (poisson **0.0636**, h2 **0.0692**) va **0.750** (poisson **0.1099**, h2 **0.0541**). Nguong ky >= 2. `L92` GO DUOC tren truc rho -- phat bieu "khong go duoc bang truc rho" cua `L107` ban dau da bi bac bo bang do luong, khong bang lap luan. Capacity 500/500 block tren 12/12; build 8.87--9.61 giay/cell. `a070_window_allowlist.json` |
| G23-278 | 23.22d | FAIL | `M-216` VI TRI cua so SAI so voi ca hai mo hinh noi suy. (a) bien duoi do duoc **0.744** thuoc [.744,.756] DAT; (b) bien tren do duoc **0.750**, NGOAI [.760,.770] MISS; (c) `rho` = **0.760** h2 `err_neo` = **0.0424** < 0.05 nen KHONG ca hai song, MISS. Doc theo dung cach da ghi TRUOC (`A070` muc 2.3): hai mo hinh noi suy bi bac bo o muc dinh vi diem; paper chi duoc bao cao interval DO TRUC TIEP. He qua nguoc voi tu-phe cua ban de xuat: luoi GOC `{0.760, 0.800}` cung se TRUOT, vi 0.760 nam NGOAI cua so -- xem `L111` |
| G23-279 | 23.22d | FAIL | `M-217` doi chung am: h2@0.770 CHET (`err_neo` = **0.0405**) DUNG du doan; nhung poisson@0.744 **SONG** (**0.0636**) thay vi chet, nen bien duoi cua luoi W nam TRONG cua so, khong phai ngoai. Cua so KHONG bi bao boi luoi W o phia duoi. Bracket duoc CUU bang `poisson@0.740` = **0.0413** (chet) cua A069, hop le vi manifest A070 32 cell la SIEU TAP cua manifest A069 20 cell va **0/20** cell chung lech mot truong nao (kiem `L106`). Bien duoi thuc: `rho` thuoc (0.740, 0.744] |
| G23-280 | 23.22d | PASS | `M-218` `P-1` TAI LAP MU tren ba cell song moi (`h2@0.740`, `poisson@0.780`, `poisson@0.820`), `n` = 250. He so `err\|accept / anchor` cua C3-R gan NHU HANG SO: **0.3290 / 0.2881 / 0.3162**, range = **1.142x** (<= 1.60). Cua B2-R trai **0.0872 .. 0.4129**, range = **4.732x** (>= 1.80). Manh HON ca neo 8 cell cu (1.22x / 2.39x). Bat doi xung cua `P-1` khong phai hien vat cua 8 cell goc |
| G23-281 | 23.22d | PASS | `M-219` `P-2` tren ba cell song moi, `n` = 250. Khoang cach trung vi `\|err_C3R - err_B2R\|` theo acceptance GIAM dan 0.70 -> 0.15: **0.00182 / 0.00336 / 0.00887 / 0.00447** -- khong giam o **3/4** buoc (nguong >= 3/4), va C3-R <= B2-R o **4/4** muc. TAI LAP dung HINH DANG da thay tren tap cu (`L102`: 0.00183 / 0.00570 / 0.01125 / 0.00981), KE CA cho gay o muc 0.15. Day chinh la lan ky lai tren tap CHUA XEM ma `L102` doi hoi: mon no do da duoc TRA |
| G23-282 | 23.22d | PASS | `M-220` `M-202` tren TRUC kappa MO RONG, 11 cell song, `n` = 500, **110** o ngoai cheo. Do doc = **0.4873** (dai da ky [0.40, 0.62]), Spearman = **+0.9798** (>= +0.90). Don bay `\|log(kappa_A/kappa_B)\|` mo tu **0.5260** len **0.8601** (**+63.5%**), dung con so `A070` du bao (~0.86). Do doc GIU NGUYEN (`M-202` = 0.4776, lech 0.0097) khi bien rong them 63%: quan he KHONG phai hien vat hoi quy tren mot doan ngan. **54/110** cap co it nhat mot cell moi, tuc mot NUA hoi quy la diem chua tung in -- day la phan mu that su, doi trong voi `L113` |
| G23-283 | 23.22d | PASS | `M-221` do nhay `a*`/san: **4/6** to hop dat (nguong >= 4, tuc DUNG BANG bien). Dat: (0.30, 0.20) ti so 8.33; (0.42679, 0.20) va (0.42679, 0.30) ti so 4.00; (0.55, 0.30) ti so 2.00. TRUOT: (0.30, 0.30) `n*(C3-R)` khong dat trong luoi {30,60,120,250}; (0.55, 0.20) ti so 1.00. `n*(B2-R)` = **30** o CA SAU to hop = SAN CUA LUOI, nen moi ti so la CAN DUOI (cung canh bao voi `G23-265`). Ket luan chi vung o quanh `a*` da ky; hai dau dai `a*` la cho yeu |
| G23-284 | 23.22d | PASS | `NC-E-0` WIRING: payload khoa hoc cua `recalibrate_transfer.json` tai tao BIT-FOR-BIT, sha256 = **20dba292..0786f1af**, tren **HAI** lan chay doc lap (10:07 va 09:13 UTC+7). Envelope provenance bam rieng va lech dung nhu da ky. `NC-E-1` AM: ti so `err\|accept(C3-R)/anchor` tren 4 cell chet = **0.0 / 0.0 / 0.0 / 0.00382**, **0/4** >= 0.80 -> FAIL **DUNG NHU DU BAO** (`A070` muc 3 ghi `Du bao FAIL` TRUOC khi chay). Doc: tieu chi TUONG DOI cho thay `err` cua C3-R tren cell chet sup ve DUNG KHONG, chu khong chi "trong khoang 0.02" -- xac nhan `L101` rang nguong TUYET DOI cua `NC-B3-3` la mot phep dem, khong phai bang chung |
| G23-285 | 23.22d | PASS | `M-222` NANG LUC cap GIUA HO tai CUNG `rho`, tren OVERLAP-4, `n` = 250. **3/4** cap co huong dung duoc (nguong >= 2). Bao phu giu o **4/4**: `viol|accept` = **0.0719 / 0.0762 / 0.0758 / 0.0736**, tat ca <= alpha = 0.10. Ve BIND lai la ACCEPTANCE: `h2@0.750 -> poisson@0.750` co acceptance **0.1837** < san 0.20 nen bi loai; ba cap kia 0.3667 / 0.4474 / 0.5963. Day la lan thu HAI trong 23.22 ma ve bao phu dat 100% con ve acceptance moi la ve rang buoc -- xem `L104` |
| G23-286 | 23.22d | PASS | `M-223` `M-210` nguyen van tren LIVE-15, `n` = 500, **210** o ngoai cheo (102 cap cung ho). Ca BA ve dat: (a) do doc = **0.4661** trong [0.40, 0.62]; (b) he so ho tai = **+0.00628** (<= 0.02) va `delta R^2` = **+0.00050** (<= 0.02); (c) Spearman = **+0.9804** (>= 0.90). Do doc tai lap qua ba tap cell: 0.4776 (8 cell, `M-202`) -> 0.4873 (11 cell, `M-220`) -> 0.4661 (15 cell). **VE (b) BI STRUCK boi `G23-288`**: `NC-W-1` cho thay mot nhan NGAU NHIEN cung roi trong dai, nen (b) HIT khong mang thong tin. Chi (a) va (c) duoc trich dan |
| G23-287 | 23.22d | FAIL | `M-224` doi chieu CUNG-RHO tren OVERLAP-4, `n` = 500, doc theo cach PHAN TANG (`L115`). Dat **1/2** `rho`, doi 2/2. Tai `rho` = 0.750: trung vi residual khac_ho **+0.04671** (n=4) vs cung_ho **+0.03681** (n=2), `|chenh|` = **0.00990** <= 0.02 DAT. Tai `rho` = 0.744: khac_ho **+0.00168** (n=4) vs cung_ho **+0.03552** (n=2), `|chenh|` = **0.03384** > 0.02 VUOT. Voi n=2 thi 'trung vi' dung bang TRUNG BINH cua hai so rat khac nhau (+0.06143 va +0.00962), va hai cap cung ho lai la hai cap co `|log(kappa_A/kappa_B)|` LON NHAT trong tang -- tuc bien ho tai VAN bi ghep voi bien don bay ngay trong OVERLAP-4. `A070b` N2 da ky truoc rang moi phat bieu cua `M-224` chi ve HAI diem tai. Xem `L120` |
| G23-288 | 23.22d | PASS | `NC-W-1` doi chung AM da chay dung nhu ky va cho ket qua da du bao: nhan NGAU NHIEN cung ti le (seed 232301) cho he so = **-0.00261** va `delta R^2` = **+0.00009**, CA HAI roi trong dai da ky cua `M-223`(b). CHAN DOAN ngoai dai ky (200 rut tham): **100.0%** roi trong dai; `|he so|` p95 = **0.00874**, tuc dai da ky (0.02) rong gap **2.3 lan** ca duoi phan bo nhan ngau nhien. He so THAT (+0.00628) nam TRONG phan bo nhan ngau nhien (p95 = 0.00874). HE QUA DA KY: `M-223`(b) **KHONG duoc trich dan** lam bang chung. Cung hinh dang `L99`/`L101`; xem `L119` |
| G23-289 | 23.23 | PASS | `M-225` wiring: qhat C3 tu duong chung trung BIT voi `config_matrix.fit_config`; `max_abs_diff=0`, acceptance 0.395462, `viol|accept=0.081721` |
| G23-290 | 23.23 | PASS | `NC-23.23-1`, 200 draw xao `z_bin`: `viol` mean 0.078239, p95 0.078444, max 0.078563; acceptance mean 0.364950. p95 duoc khoa vao A072 truoc nhanh chinh |
| G23-291 | 23.23 | ADJUDICATED | `M-226`: dai `>=3/5 bin` HONG-KHI-KY vi truc LIVE chi co 4 bin. B8b toan cell: acceptance 0.405077, `viol|accept=0.087444 < alpha=0.10`. MO TA, khong HIT/MISS; A073 muc 1 |
| G23-292 | 23.23 | FAIL | `M-227` khong fire: 0/12 cap `(z_bin,slot)` co `CI95_lo(CV) > K08=0.755510640`; can duoi lon nhat 0.750832. Bat doi xung: KHONG duoc suy ra Gaussian dung |
| G23-293 | 23.23 | DIAGNOSTIC | `M-228` [MO TA]: B8a `viol|accept=0.547114` (cong thuc thieu vi tri); B8c 0.088096. Khong co dai HIT/MISS theo A072 |
| G23-294 | 23.23 | ADJUDICATED | `M-229`: dai `>=4/5 bin` KHONG THE DAT khi chi co 4 bin. B8d toan cell: acceptance 0.388199, `viol|accept=0.076945`; lech C3 0.004776. MO TA; A073 muc 1 |
| G23-295 | 23.23 | ADJUDICATED | `M-230` BAT KHA THI, khong phai MISS: 4/4 o co 500 block, san tu choi 29, nen C3 tu choi 0/4. `CL-13` chua duoc kiem; A073 muc 2, L125 |
| G23-296 | 23.23 | PASS | `M-231` B7 da chay: Chow/Sun threshold `h*=0.618125 s`, acceptance 1.0, `err|accept=0.238841`; C3 acceptance 0.395462, `err|accept=0.083978` (ti so 2.844x). B7 khong co claim coverage; L127 |

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
lai. KE TIEP `G23-238`. `G23-245` mo boi amendment 23-65b (`L93`); `G23-246` boi amendment 23-65c (`M-192`); `G23-247` boi amendment 23-65d (`L95`, `L96`) -- no doc thang artifact da co, khong mo mot lan chay nao.

`G23-248 .. G23-255` (lesson `23.22` Task B) mo boi amendment 23-66: ma tran
chuyen giao C3 vs B2 tren 8 cell song, diem van hanh `kappa = 0.5` lay tu
`M-192`. Nam du doan (`M-193`, `M-194`, `M-195`, `M-196`, `M-190`) va ba doi
chung (`NC-1`, `NC-2`, `NC-3`). Ban thao noi bo cap den `G23-254` va gop
`NC-2` voi `NC-3`; da tach vi hai doi chung kiem hai thu khac han.
`G23-256` mo boi amendment 23-66b: `NC-3` duoc tach lam hai nhanh vi bat bien
thang chi dung khi `qhat` DUOC UOC LUONG LAI, con nhanh mang nguyen thi ca hai
phuong phap deu troi.

`G23-257 .. G23-259` mo boi amendment 23-67: `M-197` ky lai phat hien "that
bai cua C3 CO DAU" (POST-HOC o tap song -> cham tren 16 o cell CHET chua xem),
`M-198` chi bao khong can nhan, `M-199` chi phi tai hieu chuan (Task B-2). Ban
thao noi bo cap `G23-255..257` cho ba ma nay va va cham voi `NC-3a`/`NC-3b`;
da cap lai tu `G23-257`.

`G23-261 .. G23-269` (lesson `23.22` Task B-3) mo boi amendment 23-68: tai hieu
chuan qua che do, va menh de bao toan. KE TIEP `G23-260`. Bay ma do (`M-200 ..
`M-206`) va ba doi chung (`NC-B3-1..4`, gop `NC-B3-2/3/4` vao `G23-269` vi ca
ba deu la kiem CAU TRUC/AM tren cung mot lan chay). `M-200` la KIEM WIRING --
dap an da biet tu `taxonomy_audit.json`, ha cap theo tien le `M-193`.
Hai nguong DA DUOC DOI sau PILOT va TRUOC khi nhanh do luong ton tai
(`A068` muc 4.2): `G23-262` ve sd(acceptance) va `G23-263` ve Spearman -- ca
hai o dang cu deu la HIT gan nhu chac sau khi do rong cua truc A duoc do.

Noi dung tung ma (nguong day du o `A068` muc 7; o day chi de tra cuu):

```text
G23-261  M-200  kiem WIRING, nguong BIT           A068 muc 5.1
G23-262  M-201  bao toan o `n` huu han            A068 muc 5.2
G23-263  M-202  gia cua `kappa` sai, du doan duoc A068 muc 5.3
G23-264  M-203  bao dam duoc khoi phuc            A068 muc 5.4
G23-265  M-204  GIA tinh bang `n`                 A068 muc 5.5
G23-266  M-205  ket qua AM ve `err`               A068 muc 5.6
G23-267  M-206  ve DOI XUNG cua bao toan          A068 muc 5.7
G23-268  NC-B3-1  doi chung DUONG (PHAI FIRE)     A068 muc 6
G23-269  NC-B3-2 + NC-B3-3 + NC-B3-4              A068 muc 6
```

`G23-260` mo boi amendment 23-67b (`L100`): co cua `L93` mu dung trong truong
hop cua `L95`. Nhan DIAGNOSTIC vi no POST-HOC -- tim ra khi doc bang `n` cua
Task B-2, khong tu mot dai da ky.

## Ghi chu ve pham vi ID

So nay chi chua ID dang `G23-*`. Cac ho ID khac -- `PC23-*`, `NC23-*`, `V23-*`,
`L2*`, `S*`, `C23v2-*`, `NC23v2-*` -- thuoc tu vung khac (doi chung, gioi han)
va KHONG duoc tron vao day. Mot so, mot loai ID. Neu can, tao `CONTROLS.md` va
`LIMITS.md` rieng.

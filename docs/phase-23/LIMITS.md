# LIMITS -- so han che Phase 23 (nguon chan ly duy nhat cho ma `L*`)

Moi han che cua Phase 23 co DUNG MOT dong o day.
Sua bang tay; KHONG sinh tu dong.

Duoc mo o Lesson 23.19 Task A sau BA lan va cham ma trong hai lesson
(`L29`, `G23-97..99`, `amendment-47`). `GATES.md` muc "Ghi chu ve pham vi ID"
da de xuat tao file nay tu Amendment 23-26; den 2026-08-22 no moi duoc tao,
va kiem ke dau tien phat hien ngay hai va cham CHUA AI BIET.

## Quy tac cap ma

```text
1. Ma moi lay so KE TIEP so lon nhat trong bang duoi. KHONG tai su dung.
2. Ban ke hoach NGOAI repo (PHASE_23_v3.md, ...) co he danh so RIENG.
   Khi mot han che tu ban ke hoach vao repo, no duoc cap ma theo bang nay
   va ghi ma cu o cot "ghi chu".
3. Mot ma - mot han che. Neu hai cho mo ta cung mot han che thi mot cho la
   DINH NGHIA (o day), cho kia chi TRICH DAN.
```

## Bang

| ma | han che (rut gon) | dinh nghia tai | ghi chu |
|---|---|---|---|
| L10 | campaign Mininet Amendment 36 tam dung | `15-fallback-and-objective-robustness.md:176` | |
| L11 | AoI ke thua tu he khac: `d_sync = 51 ms` do tren `topology3` (3 duong, 9 canh) roi dung cho `topology_v7` (butterfly, 8 link) | `PHASE_23_v3.md` (NGOAI repo), trich o `00zx-amendment-44.md` | **DONG** o Lesson 23.20: `d = 115.9 +/- 6.5 ms` do tren chinh `topology_v7` |
| L13 | Ho so AoI theo tung link chua duoc do; Phase 22 dung ho so danh dinh U0/U1/U2 | `PHASE_23_v3.md` (NGOAI repo) | **DONG** o Lesson 23.20: ho so `U3` do duoc, `M-109b` lech ban cong bo <= 0.970 ms |
| L14 | ngu nghia fallback do ta chon, khong phai he thong bat buoc | `01-inherited-audit.md:134` | |
| L15 | F1 STICKY reset dau block la quy uoc phuong phap | `01-inherited-audit.md:137` | |
| L16 | ba thang risk do tren cung tap hang nen tuong quan | `01-inherited-audit.md:140` | |
| L20 | intervention-rate check | `04-baselines.md:218` | |
| L21 | khong gian hanh dong hieu dung la 3 | `04-baselines.md:365` | va cham **DA PHAN XU** (amendment 23-50) -- xem duoi. Dinh nghia goc `00p-amendment-15.md:144`; dong nay la TRICH DAN |
| L22 | gamma != 1 la diagnostic-only, khong guarantee-preserving | `00s-amendment-18.md:141` | |
| L26 | dai tin cay cua c*(gamma) la dai CO DIEU KIEN | `11-abstain-cost.md:358` | |
| L27 | c* la dai luong PHAN THUC (counterfactual) | `11-abstain-cost.md:364` | |
| L28 | G23-34 NOT_RUN, khong co dinh nghia khoa trong repo | `11-abstain-cost.md:369` | |
| L29 | c_F1 tinh tren ca luoi nhung wait_s cua F3 chi o DIEM | `11-abstain-cost.md:372` | |
| L30 | rho cua uA/uB do SAI CHIEU trong toan bo chien dich 23.8 | `00zzb-amendment-45c.md:99` | trich dan o `22-aoi-stall-anatomy.md:416` |
| L31 | PROD (delta-sync) khong tai lap duoc: sd(p05) gap 5.79x CLEAN | `22-aoi-stall-anatomy.md` muc 9 | ban ke hoach 23.18 goi la "L29" -- va cham, xem duoi |
| L32 | `d` do qua probe mang sai so lay mau +/-6.5 ms (95%) do khoa luoc | `23-sampling-diagnostic.md` muc 4 | |
| L33 | duoi phai cua `d_transport` chi do duoc qua nhac cu tho (MIN, luong tu 100 ms, khoa luoc): SU TON TAI chac, HINH DANG khong | `00zzd-amendment-47.md` muc 3 | |
| L34 | diem doi dau cua `lift_minus_swing` noi suy TUYEN TINH qua khoang 124 ms tren artifact `SENSITIVITY_ONLY` voi z_edges CU | `00zzd-amendment-47.md` muc 4 | |

| L35 | phan du hinh dang cua z: `p50-mean` lech 4.10 sigma, `p95-mean` 4.03 sigma so voi mo hinh. Da LOAI bon co che (alpha, nghich ly kiem tra, cai luoc, `d` lech phai). CO CHE CHUA BIET. Do lon ~8 ms = 1.6% cua T, nho hon hieu ung dang do (65 ms) 8 lan | `00zze-amendment-48.md` muc 3 | KHONG duoc dieu chinh mo hinh de che |
| L36 | ty trong bin (4 bin) KHONG phat hien duoc viec dung nham `instrument_mode` trong pipeline (lech chi ~2 diem %). Tach bach hai che do phai la RANG BUOC THIET KE, khong phai phep kiem ha nguon | `25-zedges-and-task-e-controls.md` muc 3 | G23-107 FAIL |

| L37 | `U1` va `U2` KHONG bao toan trung binh (mean +22.5 va +12.5 ms), nen so `U0/U1/U2` o Phase 22 la so DONG THOI hinh dang ho so VA muc tuoi. Cung cham `M-76` cua 23.8 | `00zzf-amendment-49.md` muc 3 | da them `U1c`/`U2c`; ket luan cu mang nhan `CONFOUNDED_SHAPE_AND_LEVEL` |
| L38 | `T = 500 ms` << block `5 s` nen MOI block dong gop hang cho CA BON bin -> so block "hieu dung" moi bin la 500 chu khong phai `600 x 25%`. Cac bin KHONG doc lap ve block | `26-axis-integration.md` muc 4 | tinh chat DA CO tu v2, khong do bo canh moi gay ra; so sanh CU vs MOI van hop le |

| L39 | Phan du cua `M-125b`: phan CO HE THONG do HINH HOC BIN (cu 45/100/100/250 ms vs moi ~125-150). Khop hinh hoc lam `corr(r,lech)` tut 0.9899 -> 0.5008 va mat don dieu; `\|lech\|max` 2.69% -> 1.56%. Con ~1% tan xa CHUA giai thich (nghi pham L35) | `00zzj-amendment-49d.md` muc 2 | Transfer giua bin CUNG hinh hoc se chinh xac hon 2.6%. Gioi han: khop hinh hoc lam dai r hep lai nen it don bay hon |
| L40 | `Dot 2` (con so TUYET DOI: LS, err_neo, acceptance, c*) phu thuoc `w_loss` va nguong SLA -> BI THAY THE boi Lesson 23.21. `Dot 1` va `Dot 3` la GHEP CAP nen SLA triet tieu va VAN DUNG | `29-waves-2-3-and-bin-geometry.md` muc 4 | Dot 2 mang nhan `CONDITIONAL_ON_SLA_AXIS`; headline viet sau 23.21 |

| L41 | CLOSED 23.21h: `live_region_sweep` khong con `prepare_sla`/`SLA.calibrate_cell`; no nap manifest ngoai sinh 14 cell. Dot 4 da chay 12/12; M-125a mo rong 12 cell, M-125b 48 o | `A062-amendment-62.md`; `41-live-region-exogenous.md` | Dong boi G23-141/142/211/213; output `results/LIVE/phase-23/live_region_sweep_slaB.json` |
| L42 | `cert/cell_matrices.py` co BAN SAO row-selection rieng (`_valid_rows` goi tu dong 177). Neu no va `calib_set` dung hai truc khac nhau thi so hang lech (999.945 vs 999.495) | `00zzl-amendment-49f.md` muc 1 | Da truyen `axis`/`aoi_profile` xuong. Loi la ON AO (AssertionError), khong im lang |

| L43 | `alpha/3` vs `alpha/4` da dong boi Amendment 23-16; pruning action chet con la limitation OPTIONAL, chua duoc dung de dien giai ket qua | `00s-amendment-18.md:139` | cap moi o amendment 23-50; truoc do mang nham ma `L21`. Tai lieu DA KY khong duoc sua nen dong do VAN mang chuoi `L21`; anh xa o `test/test_limits_ledger.py :: ADJUDICATED_ALIAS` |

| L44 | `ar1_matrix()` sinh TAM chuoi shock DOC LAP cho tam link (`measurements/sla_calib_v2.py:79`, docstring tu khai "independent AR(1) per link"). Trong `topology_v7` (butterfly) cac duong DUNG CHUNG link, nen tai that su tuong quan. Mo hinh doc lap danh gia THAP phuong sai cua margin giua cac duong -> conformal band hep gia tao. Day la `S13` | `00zzn-amendment-51.md` muc 6 | Lesson 23.21 hieu chuan `w_loss` TREN CHINH mo hinh nay: khong lam S13 te hon nhung cung KHONG sua. Sua o 23.25/23.26 |
| L45 | Xuat xu chinh xac cua `beta = 0.431` CHUA truy duoc. Hai ung vien tai dung tu Phase 22 cho 0.4340 va 0.4371; ca hai nam trong CI95 cua phep fit `[0.4195, 0.4425]` nhung khong cai nao ra dung 0.431 | `CONSTANTS.md` muc "K01" | KHONG lam hong `M-125b` (fit tren phep doi BIN, kiem tren phep doi TRUC -> ngoai mau). Anh huong: khong tai lap duoc chinh xac con so tu tai lieu Phase 22 |

| L46 | `S_pivotal` do tren mo hinh rho DOC LAP theo link (`S13`, xem `L44`; chua sua). Tuong quan tai that se lam cac duong vi pham DONG THOI nhieu hon -> `S_pivotal` THAT nho hon so do duoc | `00zzo-amendment-52.md` muc 11 | Uoc luong hien tai la CAN TREN cua vung song. Sua cung luc voi `L44` o 23.25/23.26 |
| L47 | Nguong ITU-T G.114 (150 ms one-way) la ngan sach cho THOAI. Nhiem vu cua `topology_v7` khong duoc dac ta la thoai | `00zzo-amendment-52.md` muc 11 | Viec muon nguong nay la mot ANH XA hop ly, KHONG phai mot dac ta hop dong. Phai viet ro trong paper |

| L48 | DINH CHINH amendment 23-52 muc 3: can duoi sweep `w_loss = 1250` KHONG "bao tron dai noi sinh cu [1245.6, 4722.7]" -- `1250 > 1245.6`. So `1245.6` la cua HAI cell `cbr` role=`pc1`; tam cell `gate` (co so cua moi ket luan) co dai `[1656.4, 4722.7]`, va `1250` bao tron dai do | `00zzo-amendment-52.md` muc 3 (cau chu sai); do duoc tren `sla_calibration.json` | Sweep VAN du cho pham vi ket luan. Amendment DA KY nen khong sua; dinh chinh ghi o day va o `test_spec_table_is_locked` |

| L49 | `M-135` dung thang do bi BIEN CHAN: voi bien 2-vs-6 (SLA) va 4-vs-4 (err_neo), so cell trung chi nhan {2,4,6} va 6/8 la TRAN co the dat. Nguong ">= 6/8" duoc ky TRUOC khi biet bien | `00zzp-amendment-53.md` muc 1 | Bang chung thuc: `kappa` = 0.50, `P(>=6/8 ngau nhien)` = 0.214, n = 8. KHONG duoc viet "SLA ngoai sinh xac nhan vung song cu" |
| L50 | `S_pivotal` bao cao o Lesson 23.21 KHONG kem khoang tin cay. Chuoi `rho` la AR(1) (`tau` = 1 s, `dt` = 5 ms) nen `n_eff` = 500 chu khong phai 200 000 | `00zzp-amendment-53.md` muc 2 | Sai so thuc lon gap ~20 lan so voi gia dinh iid. `h2@0.700` cach nguong 0.80 sigma -> nhan `AMBIGUOUS` |
| L51 | Tam calib parquet cua `M-136` va bon parquet Dot 4 khong con tren dia, va report cu KHONG luu digest cua chung | `00zzp-amendment-53.md` muc 9 | Dung lai ma tham so khong khop goc -> doi chung am muc duong ong vo nghia IM LANG. Bao cao "khong tai dung duoc", KHONG dung so thay the |

| L52 | Cong thuc `n_eff = n(1-phi)/(1+phi)` mo ta tu tuong quan cua CHUOI `rho`, khong phai cua CHI BAO `pivotal`. Do duoc bang block bootstrap: `n_eff` = 1551..3603 chu khong phai 500 | `32-scale-ci-and-wave4.md` muc 3 | Ham NGUONG pha tu tuong quan -> cong thuc AR(1) la CAN DUOI bao thu. Ket luan `AMBIGUOUS` cua `h2@0.700` KHONG doi |
| L53 | Dinh cua `S_pivotal(poisson, rho)` nam o MUT TRAI cua luoi (`rho` = 0.850); dinh cua ho `h2` nam DUOI 0.650, ngoai moi diem da do | `32-scale-ci-and-wave4.md` muc 2, 5 | Vi tri dinh CHUA duoc kep. Can luoi min hon; chi phi ~1 s/cell, KHONG can calib parquet |
| L54 | Ket luan "1/8 cell song" cua Lesson 23.21 la phat bieu ve LUOI LAY MAU (`rho` thuoc [0.700, 0.960]), KHONG phai ve MANG | `32-scale-ci-and-wave4.md` muc 5 | Dot 4: ho `h2` co vung song o `rho <= 0.675`, hoan toan ngoai luoi goc. Ca bon cell Dot 4 deu LIVE |

| L55 | `S_pivotal = F_min - F_max` do CAC DUONG KHAC NHAU BAO NHIEU, KHONG do duoc lieu twin CU co chon dung duong hay khong | `00zzq-amendment-54.md` muc 1b, 6 | `S_pivotal` cao KHONG keo theo "chung nhan co gia tri". Bang hai chieu la dieu kien CAN ve logic, khong phai cach trinh bay dep |
| L56 | Dinh `S_pivotal` cua ho `h2` co the nam duoi `rho` = 0.575, tuc NGOAI mien kha thi cua mo hinh (`sigma_max` -> 0 duoi do) | `00zzq-amendment-54.md` muc 6 | Neu xay ra: ghi "KHONG KEP DUOC", khong ghi la dinh (`G23-173`) |
| L57 | `M-135` so sanh hai phan hoach do duoi HAI ham muc tieu khac nhau: `err_neo` duoi SLA NOI SINH tung cell, `regime` duoi SLA CHUNG | `00zzq-amendment-54.md` muc 2 | Ill-posed, DOC LAP voi n -- khong sua duoc bang thong ke. Cot `err_neo` cua bang `G23-167` dang TRON hai truc SLA |
| L58 | Quet `rho` doi DONG THOI `rho_bar` va `sigma_rho`: `sigma` = 0.9 x `sigma_max(rho)`, va `sigma_max` co DINH o `rho` ~ 0.775 (0.0804). Giua `h2@0.650` va `h2@0.700` `sigma` chenh 1.60 lan | `00zzq-amendment-54.md` muc 3 | Cung lop loi voi `L37`. Moi phat bieu "vung song o `rho` thuoc [x,y]" PHAI kem doi chung `sigma` co dinh (`G23-172`) |

| L59 | Can duoi vung song ho `h2` TRUNG cho `sigma_max(rho)` roi khoi 0 (`rho` ~ 0.565). `S_pivotal` nhay ~1000 lan tu 0.575 sang 0.600 trong khi `sigma` chi tang 4.3 lan | `00zzr-amendment-55.md` muc 4 | Do la bien cua THAM SO HOA mo hinh, KHONG phai bien cua MANG. Tham so hoa `sigma` khac -> can duoi dich |
| L60 | `efficiency` cua `poisson@0.960` va `h2@0.960` duoc noi suy BAC NGANG qua mot buoc nhay ([0.500, 0.993] va [0.000, 0.992]) -> VO NGHIA | `00zzr-amendment-55.md` muc 1 | Lop loi `L34`/`L35`/`M-133`, lan thu TU. Sua bang luoi cuc bo he so 1.05 (`G23-176`) |
| L61 | Tieu chi `opt_viol in [0.01, 0.50]` ke thua tu thoi NOI SINH khi `opt_viol` bi EP = 0.15 va dai do chi la phep kiem VE SINH. Duoi SLA ngoai sinh y nghia DAO: `opt_viol` thap = ORACLE THANH CONG | `00zzr-amendment-55.md` muc 2 | Cung lop loi voi `S12` nhung tren mot TIEU CHI thay vi mot BIEN. `M-153` dung KET QUA (trung top-4 theo `V`) nhung sai LY DO |
| L62 | Do rong vung song theo `rho` CO LAI ~3 lan khi giu `sigma` co dinh (11 cell LIVE -> 4); `poisson@0.750` tut 1104 lan | `00zzr-amendment-55.md` muc 3b | Phat bieu MOT CHIEU ve vung song la KHONG DAY DU. Doi tuong that la mot MIEN trong mat phang `(rho, sigma)` |

| L63 | Co `peak_at_grid_edge` kiem CHI SO `argmax` nen MU voi CAO NGUYEN. `h2@0.960` co 9/16 diem cung dat `S_pivotal` = 1.0000, cao nguyen trai `T` thuoc [0.211, 0.312] va CHAM mut phai, nhung co bao `false` | `00zzs-amendment-56.md` muc 1 | Loi o cap PHEP KIEM, khong o cap du lieu. Cao nguyen pha VI TRI (`M-147`) nhung KHONG pha GIA TRI (`efficiency`) |
| L64 | Dinh `V` nam TREN BIEN kha thi `sigma = sigma_max(rho)` o 13/14 gia tri `rho` do duoc; chua kep duoc | `00zzs-amendment-56.md` muc 3 | Phat bieu "V cuc dai o sigma trung binh" DA BI RUT. Muon kep phai quet theo `a`, khong quet theo `sigma` |
| L65 | Chieu truot cua mien song theo `sigma` bi TRON voi hinh dang mien kha thi: tai `sigma` = 0.072 chi con MOT cot `rho` kha thi (0.800) | `00zzs-amendment-56.md` muc 4 | Phat bieu "mien song truot sang rho cao hon o ca hai ho" DA BI RUT (hai ho di NGUOC chieu). HINH 2 BAT BUOC ve `sigma_max(rho)` chong len |

| L66 | Van ban dong lesson (`NN-close-*.md`) va `GATES.md` duoc cap nhat bang tay o HAI cho. `35-close-23-21.md` BO SOT `G23-156` va `G23-158` khoi muc "No mang sang" (do duoc: grep = 0 lan) | `00zzt-amendment-57.md` muc 2a | Khong test nao buoc hai cho khop ve TAP gate mang sang. Chan bang `G23-194` |
| L67 | So no khong co co che chan CHU TRINH CHO: moi `DEBT` duoc phep ghi "mo lai sau X" ma khong ai kiem `X` co phu thuoc NGUOC vao no khong | `00zzt-amendment-57.md` muc 2b | Hau qua that: `G23-158` <-> `G23-141`/`G23-142` DEADLOCK tu 2026-08-23. Chan bang `G23-195` |
| L68 | Artifact cua `sla_exogenous` dung schema rieng (`sla_axis_label` + `sla_spec_id`) thay vi truong `validity` chuan | `00zzt-amendment-57.md` muc 8 | `test_no_stale_axes` KHONG kiem duoc chung neu chung len `LIVE/`. Manifest moi PHAI co `validity` |

| L69 | Doi chung am muc DUONG ONG dat max\|diff\| = 5.72e-06 chu khong phai 0: 150/156 truong khop CHINH XAC, 5 lech <= 3.7e-13, rieng `gap_true_pct.p90` lech 5.72e-06 | `00zzt-amendment-57.md` muc 6 | **CHAN DOAN BAN DAU SAI, da sua o amendment 23-58**: `L69` tung ghi "co che DA XAC DINH: float32". Bac bo o `L71`. Nguyen nhan VAN CHUA biet |

| L70 | Manifest ban dau (amendment 23-57) mang NAM truong PHAI SINH (`opt_viol_rate`, `in_band`, `cost_margin_mean_ms`, `cost_margin_p10_ms`, `opt_path_share`) va BAY khoa `config` cua vong fixpoint. `opt_viol_rate` ghi 0.15 trong khi su that duoi `S-B` la 0.99-1.00 | `00zzu-amendment-58.md` muc 1 | KHONG hong SO (`cert/` khong doc chung) nhung hong NHAN: `sla_calib_v2` doc 21 lan de sinh bang/hinh paper. Xoa THEO NGHIA chu khong theo TEN -- `NT 50` |

| L71 | BAC BO chan doan cua `L69`. Gia thiet "phan du `p90` do tich luy float32" da duoc THU bang cach ep float64: ket qua TE HON. `p5`/`p10` khop CHINH XAC (lech 0.0) o float32 nhung lech 4.8e-08 o float64; `p90` lech 5.7e-06 o float32 va 7.6e-07 o float64 | `00zzu-amendment-58.md` muc 3; do tren `poisson@0.925` U0 | Du lieu BIT-IDENTICAL (`output.parquet_sha256` giong het qua hai lan chay). Nguyen nhan cua RIENG `p90` CHUA XAC DINH. Da HOAN NGUYEN phep ep float64. Nguong NC `1e-9` KHONG dat duoc voi ban luu tru sinh o moi truong khac |

| L73 | Ten file amendment `23-1..23-59` dung tien to `00z*` cap phat theo CHU CAI; sau `00zzv` chi con BON cho (`00zzw`..`00zzz`). Amendment thu 64 KHONG CO TEN | `A060-amendment-60.md` muc 0 | Tu `23-60` doi sang `A0NN-amendment-NN.md` (ba chu so -> toi 999). Sap xep lexicographic van dung vi `00z*` < `A0*`. Tai lieu DA KY khong doi ten. Cung lop loi voi `L21` (va cham ID), `L29`/`L31`, `L67`: mot he danh so khong duoc thiet ke de lon |

| L74 | `decision_error_by_age_by_regime.parquet` ban LIVE cu (450x22) THIEU hai cot `w_loss`, `w_loss_source` ma ban chay lai (450x24) CO -> sinh boi mot PHIEN BAN CODE CU. Tren 22 cot chung: BIT-EXACT 19 cot, lech <= 3.11e-15 o `rms_e_model`/`rms_e_stale`/`cov_e` | `A060-amendment-60.md` muc 7; `36-decision-error-sla-axis.md` muc 2 | File cu KHOP digest tien dang ky 21R (`5e4d4797...`) nen KHONG phai nham file -- day dung la hien tuong `L71` ("nguong NC 1e-9 khong dat duoc voi ban luu tru sinh o moi truong khac"). `G23-202` bao cao NGUYEN, KHONG noi nguong. Moi cot muc QUYET DINH tai lap bit-exact nen ket luan khong bi anh huong |

| L75 | `cert/eight_cell_sweep.py` ghi `provenance.inputs` va `NC_F_w_loss_source` bang HANG SO `SLA_ARTIFACT` chu khong phai tham so `sla_artifact` that su duoc nap. Hau qua do duoc: `eight_cell_sweep_U3_measured_v7_slaB.json` co `w_loss == 5000` o MOI cell (bang chung da doc manifest ngoai sinh) nhung provenance KHAI doc `sla_calibration.json` (truc S14 DEPRECATED) | `A060-amendment-60.md`; `37-pending-tier-adjudication.md` muc 6 | Mot artifact KHAI SAI nguon cua chinh no -- dung thu khoi `validity` sinh ra de chong. Ma nguon DA SUA ca hai cho. Artifact phai SINH LAI; sinh lai bi chan boi `L51` (thieu 4/8 parquet phase-22). Tam thoi vao `PENDING_NO_VALIDITY_GRANDFATHERED` kem ly do; xoa muc do ngay khi `L51` mo khoa |

| L76 | `measurements/h9_separability.py` va `measurements/plot_decision_error_v2.py` van doc `decision_error_by_age_by_regime.parquet` (truc SLA `self_calibrated`, loi S14), nay o `SUPERSEDED/` | `A060-amendment-60.md`; `36-decision-error-sla-axis.md` muc 8 | Duong DA doi theo file de hai script chay NGUYEN, bit-identical. CHUA chuyen sang `..._slaB.parquet` vi doi truc se doi SO cua hinh H9 va hinh phan ra -- viec do thuoc lesson so huu hinh do. Ghi de khong bi quen |

| L78 | `cert/cell_matrices.py::pin()` NUOT `OSError` va tra `sha256: None` -- lam DUNG NGUOC docstring cua chinh no ("buoc sau do ngay thay vi am tham lech"). Hau qua do duoc: `eight_cell_sweep_U3_measured_v7_slaB.json` khai 8 input calib parquet voi `sha256 = null` o CA 8, artifact van ghi ra "thanh cong" | review doc lap 2026-08-24; `A060-amendment-60.md` | `provenance` co HINH THUC ma khong co NOI DUNG. DA SUA: mac dinh NEM `FileNotFoundError`; ai co y ghim duong chua ton tai phai goi `pin(p, allow_missing=True)` -- tuong minh tai diem goi chu khong am tham toan cuc |

| L79 | `test_no_dangling_parquet_refs` cham theo `os.path.exists`, tuc hoi "co tren MAY TOI" chu khong "co tren BAN CLONE SACH". Hai cau do NGHICH nhau: file rac local LAM IM cai chan | review doc lap 2026-08-24 (chay tren clone sach: 1 failed thay vi 201 passed) | Cung lop loi voi PASS RONG, lan nay nan nhan la nguoi VIET cai chan. DA SUA sang `git ls-files`. Do lai sau khi sua: 20 tham chieu tren 9 script se chet tren clone sach (nhieu hon con so 5 ma review uoc). Ba loi thoat tuong minh: `KNOWN_DANGLING`, `OUTPUT_PATHS`, `LOCAL_ONLY` |

| L80 | ★ Tien de cua `L51` SAI: digest lich su KHONG mat. Chung nam trong `provenance.inputs` cua `results/SUPERSEDED/phase-23/eight_cell_sweep_U3_measured_v7.json` (git_hash `05b597f5`). Trong 8 calib: 3 file con song KHOP digest goc (`calib_set_v3`, `_h2_0.700`, `_poisson_0.850`), 1 file KHAC (`_poisson_0.700`: lich su `ec49deb8...`, tren dia `2267423d...`), 4 mat | do 2026-08-24; `results/RAW/phase-22/SURVIVING_CALIB_DIGESTS.json` | 7 parquet Phase 22 (468 MB) nam tren dia: 3 verified, 1 changed, 3 thuoc VERIFIED_SUPERSEDED_GENERATION (`L82`); khong trong git, `git_tracked=0/7`. Bon file khong-original CAM tai dung. `truth_table.parquet` + `sla_calibration.json` doi chieu = KHOP |

| L81 | Artifact QUET NGANG truc (`w_loss_sensitivity` quet {1250, **5000**, 20000}; `t_loss_sweep` quet {0.001..0.1}) khong the thoa `triples == {want}` VE NGUYEN TAC -> nhan `UNREGISTERED` -> mac o `PENDING` VINH VIEN | review doc lap 2026-08-24 muc 5.4; do tren `by_w_loss`/`t_loss_grid` | `PENDING` dinh nghia la "CHO, khong bi THAY THE". Cho mot dieu KHONG THE xay ra thi khong phai dang cho -- la bi MAC. Cung benh `L67` o dang khac. Ca hai quet DEU chua truc chuan trong tap quet, nen mot vai tro `spans_axis` la hop le. CHAN mot hinh paper (sensitivity cua `w_loss`) -- khong phai chuyen ve sinh |

| L82 | Ba parquet Phase 22 (`cbr_0.700`, `poisson_0.925`, `poisson_0.925_V3`) khong co digest lich su rieng, nhung cung `git_hash=f95c6bee`, builder `0f534288...`, `git_dirty=true` va cua so 2 phut voi ban cu `poisson_0.700`; report sau cua cell do dung builder `f02b1d1c...` va digest eight-cell ghim | `A061b-amendment-61b.md` muc 2; `39-l51-adjudication.md` muc 6.2 | `UNKNOWN -> VERIFIED_SUPERSEDED_GENERATION` cho muc dich canonical eight-cell/Phase 23. Van CAM tai dung. Bon trang thai: VERIFIED_ORIGINAL / NOT_ORIGINAL / VERIFIED_SUPERSEDED_GENERATION / UNKNOWN (hien rong) |
| L83 | `calib_set_v3_poisson_0.700.parquet` doi digest giua artifact `05b597f5` va kiem ke `dcd6e53`; co che cu the tai `5e1837f`: `tier_results.py` dung `git mv -f`/`os.replace`, ca hai ghi de dich im lang; `os.replace` giu mtime nguon nen ban 13/08 co the de len ban 21/08 ma dau thoi gian lui ve qua khu | `A061b-amendment-61b.md` muc 3 | Hai lop chan: chmod/custody (`G23-221`) va chan tai nguon (`G23-224`): preflight truoc mutation, bo `-f`, hard-link + unlink no-replace cho file ignored |
| L84 | `test_pinned_digests_still_match_disk` gop VANG MAT (binh thuong tren clone sach) va DOI NOI DUNG (bao dong o moi noi) vao mot assert | `A061-amendment-61.md` muc 6 | Da tach presence thanh marker `custody`, content drift giu portable. CI/default suite loai custody; may tac gia chay rieng `pytest -m custody` |
| L85 | Cell `poisson@0.925` co hai parquet hai the he: `calib_set_v3.parquet` (14/08, khop digest eight-cell) va `calib_set_v3_poisson_0.925.parquet` (13/08, lo superseded). `eight_cell_sweep` doc ban dau, `phase23_cell_margins` tung doc ban sau | `A061b-amendment-61b.md` muc 5 | Da sua `phase23_cell_margins` sang ban canonical. Doi chieu G23-17a/b/c: 0 khac biet so hoc, chi provenance path/digest doi. `G23-225` ep moi legacy `(mode,rho_bar)` trong source song co dung mot path |
| L86 | `tools/tier_results.py` tung dung `os.replace` / `git mv -f`; tinh atomic cua replace bao ve dich khoi trang thai ghi do, nhung pha huy dich co san va che dau vet bang mtime nguon. Blast radius hau kiem: 1 parquet Phase 22; 16 cap Phase-21R la hai the he dung o hai tang khac nhau | `A061b-amendment-61b.md` muc 3 | `G23-224` PASS. Primitive thay the cho ignored file la hard-link atomic (fail neu dich ton tai) roi unlink; crash giua hai buoc de lai hai ten cho cung byte, khong lam mat byte |
| L87 | Backup 24/08 o `C:\Users\VAN TAI\...` va WSL `ext4.vhdx` gan nhu chac cung nam tren o C:. Ban sao chong loi logic/VHDX, khong chong hong dia vat ly, mat may, trom/chay | `A061b-amendment-61b.md` muc 6 | Chua tuyen bo backup hai thiet bi. Can Drive/Zenodo/doi tuong luu tru vat ly doc lap; chua thuc hien trong dot `[1]--[3]` nay |

| L88 | `delta_system_vs_neo` dung ve dai so nhung de bi doc nham thanh phep tru truc tiep voi truong `err_neo`; thuc te no la `reject_share * (err_F_given_reject - c_star_err_twin_given_reject)` | `A063-amendment-63.md` muc 5; review doc lap artifact 23.21h | Giu khoa cu de tuong thich; artifact headline them `field_semantics` va alias `delta_fallback_vs_twin_weighted`; tai lieu moi dung ten ro |

| L77 | `w_loss` KHONG phai tham so cham diem, no la tham so SINH: no bi nuong vao calib parquet (`a_twin`, `a_star`, `regret`, `gap_true`, `viol_star` deu suy tu ham chi phi; `calib_set_*_report.json` ghi `w_loss = 5000.0`). Doi `w_loss` o manifest ma giu nguyen parquet -> hai dinh nghia `w_loss` trong cung mot phep tinh | `39-l51-adjudication.md` muc 5; do 2026-08-24 | Bac bo tien de "M-136 chi can chay lai eight_cell_sweep 3 lan tren cung tap du lieu". Do duoc: `--w-loss 1250` -> parity fail 2.815e-02; `20000` -> 8.347e-03; `5000` -> chay duoc (parity = 0 vi hai dinh nghia trung). Cai chan `parity > 1e-12` o `_objective_curve` da TU CHOI sinh so sai im lang. `M-136` can dung lai calib set o TUNG `w_loss` (~11 phut may), thuoc lesson so huu no |

| L72 | PARTIAL: `live_region_sweep.py --calib-template` da dong o 23.21h va duoc xoa khoi `KNOWN_DEAD`. Con `abstain_cost --calib-template`, `decision_error_v2 --boot-metrics` va ba co `--resume` (`l6_campaign.py`, `l6_campaign_fine.py`, `t5_campaign.py`) | `00zzv-amendment-59.md`; `A062-amendment-62.md`; do bang `test_cli_flags_are_wired.py` | Co con lai sua theo lesson so huu. Danh sach `KNOWN_DEAD` da ngan di mot muc; detector van khoa `getattr`, `dest` alias va forwarding lien module |

So ke tiep duoc cap: **L100**.

| L99 | `T1` (drift cua ti le chap nhan) bi TOI DA HOA boi mot score DOC LAP DU LIEU. `score_B1_random` la `U(0,1)` o MOI cell nen phan phoi khong doi khi che do doi, nen mot nguong hoc tren A cho dung ti le tren B: trung vi drift **1.19e-05**, so voi B2 **0.2174** va C3 **0.2090** -- nho hon bon van lan | `A067-amendment-67.md` muc 3; `NC-2`, do 2026-08-25 | Moi thang dang "X thay doi it den dau" deu co khuyet tat nay: toi uu cua mot thang on dinh khong co so hang huu ich la mot HANG SO. `T1` KHONG duoc bao cao mot minh, phai kem SAN HUU ICH (`T2`/`T3`). Lan thu BA cung hinh dang: FCR giu bao phu 0.0160 bang cach chap nhan 9.9% (Phase 22); V-S giu 12/12 mot phan bang `qhat = max mau` (`L93`); B1 co drift nho nhat bang cach khong nhin du lieu |

| L98 | Ve thu ba cua `M-193` (`max(b2_off) <= 0.02`) so `acceptance` cua B2 do tren TEST voi `acceptance` cua C3 do tren CALIB -- tuc nhieu tach mau cong khac biet quy tac, KHONG phai wiring. Do duoc 0.0206 | `A067-amendment-67.md` muc 2; do 2026-08-25 | Hai ve dau (kiem wiring THAT) PASS tuyet doi: `max_abs_delta_violation_C3 = max_abs_delta_acceptance_C3 = 0.000e+00` tren 8/8 o -- duong cheo tai tao TUNG BIT hang `variant_sweep` @`kappa=0.5`. Doi chung: `T1_drift_C3` tren cung duong cheo chay den 0.0173, cung co. `G23-248` GIU FAIL (dai da ky, khong noi sau khi xem) nhung doc PHAI ghi ro duong ong khong hong |

| L97 | `A066` muc 1.2 lap luan C3 bat bien thang vi luat la TI SO `m_hat/qhat >= kappa`. Trong ma tran chuyen giao `qhat` bi DONG BANG tu cell A, nen luat thanh `m_hat_j >= kappa * qhat_j^A` -- mot NGUONG TUYET DOI theo `z_bin` va slot, CUNG LOAI voi B2 | `A067-amendment-67.md` muc 1; do 2026-08-25 | Tien de cua `M-194` sai ve CAU TRUC va suy ra duoc TRUOC khi chay, nen `M-194` MISS (1.04x; hai phan phoi chong khit q1 0.1292/0.1293, q3 0.3398/0.3324) KHONG phai mot ket qua thuc nghiem. `A066b` da bat nua lap luan nay cho `NC-3` nhung khong rut ra rang KHOI CHINH cung chay o che do do. Nguyen tac: mot tinh chat cua LUAT khong tu dong la tinh chat cua LUAT VOI THAM SO DONG BANG |

| L96 | CHIN cong cu co `--out*` mac dinh tro vao tang DA KHOA `chmod -R a-w` (amendment 23-61): `cert/{abstain_cost, decomposition, gate_report, lesson23_7_calibration_2b, lesson23_7_feasibility, lesson23_7_range_calibration, operational_sigma, threshold_families}.py` va `tools/g23_212a_partial_nc.py`. Chay khong doi `--out` thi hoac lenh hong, hoac ai do `chmod` nguoc lai "cho tien" va pha custody | `A065d-amendment-65d.md` muc 3.1; do 2026-08-25 khi viet cai chan cho muc 3 | Chung co TU TRUOC khi tang bi khoa nen KHONG sua: output da dong bang, doi duong dan mac dinh se lam mat dau vet giua tai lieu cu va file that. Ghim thanh tap DA KHAI BAO trong `test_no_tool_writes_into_frozen_tiers`, so sanh BANG NHAU -- them cong cu moi thi do, sua cong cu cu ma quen go khoi danh sach cung do. Danh sach chi duoc NGAN di. Co soi chi bat `--out*` (co GHI); mac dinh DOC vao tang khoa la hop le (`tools/check_phase20r6_structure.py`) |

| L95 | Nhanh `post="selective"` (`cert/config_matrix.py`) khoi tao `q` bang `_qhat` tren TOAN BO calib -- tuc `qhat` cua thu tuc `none`. Khi vong lap suy bien o VONG 0, `q` chua tung duoc cap nhat, nen ket qua tra ve TRUNG BIT voi `none`. Do duoc tren `b9d2774`: 8/8 cell `A=True` tai `kappa=2`, `n_iter=0`, `qhat_slot1_mean` va `violation_given_accept` trung den chu so cuoi | `A065d-amendment-65d.md` muc 1; do 2026-08-25 | `min_blocks_at_final_qhat = None` KHONG phai "thieu du lieu" ma la "V-S da thanh V-N". `none` la thu tuc DA DO LA VO (`M-187`), nen day la HOI QUY DUNG DAN im lang, khong phai lo hong chan doan. Khong doi ket luan da cong bo (`pass_coverage=false` o cac hang do), nhung nhan `post="selective"` sai su that. Sua: truong `qhat_source` voi mac dinh la GIA DINH XAU NHAT, `evaluate_config` ghi `procedure_actually_run`. Cung co phan quyet `L94`: cach doc "max ca tap" tro vao `kappa=2`, noi V-S khong chay |

| L94 | Van ban da ky cua `M-192` (`A065c` muc 2) viet *"`kappa` LON NHAT ma no con >= 59"* -- MO HO. Doc theo DOAN LIEN TUC tu `kappa=0` cho `poisson@0.925` = **0.5** (HIT dai ky {0.25,0.50}); doc theo `max` tren ca tap cho **2.0** (MISS). Hai cach doc, hai phan quyet nguoc | `A065c-amendment-65c.md` muc 2; do 2026-08-25 | Nguyen nhan: tai `kappa=2` vong lap suy bien NGAY vong 0 nen `min_blocks = None`, va `A065c` muc 2.2 ma hoa `None` = "tren san". Tap `{kappa : tren san}` do KHONG con la mot doan. Da cham theo DOAN LIEN TUC vi cung cau van do goi dai luong nay la "dai van hanh", ma mot "dai" phai lien tuc. Bai hoc: mot du doan ve MOT NGUONG phai noi ro nguong do lay tren tap nao |

| L93 | Voi `alpha_each = alpha/3` va `n_eff` trong `[29, 58]`, `conformal_level` tra ve dung `1.0`, va vi `empirical_qhat` dung `method="higher"` nen `_qhat` tra ve MAX cua mau. `qhat` do HUU HAN va bao dam VAN GIU, nhung no do MOT quan sat cuc dai quyet dinh: phuong sai lon, acceptance sup, "bao phu giu" mot cach TAM THUONG. Voi `alpha = 0.10` dai tuong ung la `[9, 18]` | `A065b-amendment-65b.md` muc 1 | Cung HINH DANG loi voi `qhat = +inf` cua `L91`: hop le ve toan, vo nghia ve van hanh, di qua IM LANG. Khai bao bang co `qhat_at_sample_max`. **KHONG nang chot chan tu 29 len 59** -- 29 la san HOP LE (toan), 59 la san ON DINH (van hanh, dat SAU khi xem du lieu = HARKing); gop hai san khac loai lam mot la mat kha nang phan biet. Ghim boi `test_stability_floor_does_not_gate_anything` (doc ma nguon) |

| L91 | `cert/config_matrix.py:253` nhanh `post="selective"` dung nguong dung luong hard-code `< 9`. `9` la san cua `alpha=0.10`; nhung nhanh nay chay `simultaneous=True` voi `alpha_each = alpha/3`, ma san cua muc do la **29** (do bang `conformal_level`, KHONG phai 30). O co 9..28 block lot qua chot chan -> `conformal_level` tra `None` -> `_qhat` tra `+inf` | `A065-amendment-65.md` muc 1 | Do duoc o `eefd34a`: V-S suy bien 6/12 cell tai `kappa=1`; `qhat_slot1_mean = null` o `poisson@0.875`, `poisson@0.960`, `h2@0.650` -- CA BA la ROBUSTNESS nen `M-181..M-187` KHONG doi. Sua bang `conformal_min_blocks(a_each)` TINH tai cho. `selective_conformal.py:277` giu `9` vi o do `alpha=0.10` va con so DUNG |

| L92 | Trong tap 8 cell co `err_neo >= 0.05`, ho tai va muc tai BI RANG BUOC: `h2` chi song o `rho_bar` thuoc {0.650, 0.675, 0.700}, `poisson` chi song o {0.850, 0.875, 0.900, 0.925, 0.960}. Khong `rho_bar` nao co ca hai ho cung song | `A065-amendment-65.md` muc 5 | Ma tran chuyen giao `poisson <-> h2` NHAT THIET cung la `rho cao <-> rho thap`. Phat bieu DUOC PHEP: "chuyen giao qua CHE DO VAN HANH". KHONG duoc noi "qua HO TAI". Go bo can 4 cell moi tai `rho_bar` thuoc {0.760, 0.800} -- co trong `truth_table` (luoi buoc 0.02) nhung thieu trong manifest SLA |

| L90 | `M-186` do CI cua TRUNG BINH `qhat` TREN CAC O: taxonomy 16 o trung binh 16 so, taxonomy 4 o trung binh 4 so. Trung binh it so hon thi nhieu hon, DOC LAP voi so hang moi o. Nen ti so do duoc (1.0015 / 1.0124 / 1.0639) tron lan HAI hieu ung: do on dinh cua tung `qhat`, va so o duoc trung binh | `43-taxonomy-audit.md` muc 3.1 | Du doan `[0.50,1.00]` VAN bi bac bo (M-186 = 0/3) -- do la ket luan duoc phep rut. KHONG duoc rut ket luan "vi tuong quan noi block gan hoan toan": phep do hien tai khong tach duoc gia thuyet do khoi hien vat trung binh. Can phep do CI cua `qhat` MOT o; chua chay |

| L89 | Co so thiet ke cua Lesson 23.22 trong `PHASE_23_v3.md` trich `spread_z=2.1232` / `spread_m=1.1188` tu `00zf-amendment-30.md` dong 176-177 (`M-1`/`M-2`, nhan [TAT DINH]), do tren `Z_EDGES_LEGACY = (0.055, 0.10, 0.20, 0.30, 0.5501)`. Truc do DA BI THAY THE o amendment 23-49c bang `measured_v7_uniform` / `Z_EDGES_V7 = (0.100, 0.241, 0.366, 0.491, 0.641)` | `A064-amendment-64.md` muc 1 va muc 7 | Ban ke hoach NGOAI repo khong sua duoc; anh xa sang so DO LAI song o `results/LIVE/phase-23/taxonomy_audit.json::superseded_basis` va o `cells[].spread`. Task A0 cua 23.22 ton tai chinh de do lai co so nay |

## Va cham da phat hien

### L21 -- dinh nghia BA lan, hai noi dung khac nhau

```text
00p-amendment-15.md:144   "Khong gian hanh dong hieu dung la 3..."
04-baselines.md:365       "Khong gian hanh dong hieu dung la 3..."   <- trung noi dung
00s-amendment-18.md:139   "alpha/3 vs alpha/4 da dong boi Amendment 23-16..."  <- KHAC
```

Hai dong dau la cung mot han che (mot dinh nghia + mot trich dan) -- khong
sao. Dong thu ba la mot han che KHAC mang cung ma.

```text
TRANG THAI: PHAN XU o amendment 23-50 (2026-08-23).

  00p-amendment-15.md:144   DINH NGHIA  }  cung mot han che
  04-baselines.md:365       TRICH DAN   }  -> giu ma L21
  00s-amendment-18.md:139   han che KHAC   -> cap ma moi L43

Vi sao L43 chu khong phai L39: khi va cham nay duoc phat hien (Lesson 23.19
Task A) so ke tiep la L39, nhung L39..L42 DA duoc cap o amendment 23-49d,
23-49f va lesson 29 truoc khi phan xu kip xay ra. Quy tac cap ma #1 cam tai
su dung so, nen ma phan xu lay so ke tiep tai thoi diem KY, khong phai tai
thoi diem PHAT HIEN.

Tai lieu DA KY KHONG duoc sua -- dong 139 cua 00s-amendment-18.md VAN mang
chuoi "L21". Anh xa duoc ghi o HAI noi:
  - bang tren (dong L43)
  - test/test_limits_ledger.py :: ADJUDICATED_ALIAS
va `test_adjudicated_aliases_are_documented` bat buoc hai noi phai khop.
`test_adjudicated_alias_fragments_still_match_a_real_line` bat buoc manh
40 ky tu con khop mot dong that, de anh xa khong chet im lang.
```

### L29 vs L31 -- ban ke hoach va repo dung cung so cho hai viec

`L29` trong repo (`11-abstain-cost.md:372`) noi ve `c_F1` / `wait_s`.
`L29` trong ban ke hoach 23.18 noi ve PROD khong tai lap duoc. Da cap `L31`
cho cai thu hai (Lesson 23.18 muc 9). Khong sua `11-abstain-cost.md`.

## Ma KHONG thuoc so nay

```text
G23-*  -> GATES.md
S*     -> loi cau truc, dinh nghia trong PHASE_23_v3.md (NGOAI repo)
PC*/NC*/V*/C23v2*/NC23v2*  -> doi chung; chua co so rieng
```

`test/test_limits_ledger.py` (them o Lesson 23.19E) chan ca hai ho:
`test_no_duplicate_limit_ids` va `test_no_duplicate_gate_or_limit_ids_in_new_docs`.
Doi chung duong da chay: chen mot dinh nghia `L30` khac noi dung -> test FAIL;
go ra -> PASS.

Ba ho ID tren van CHUA co so. Neu chung bat dau va cham nhu `L*` da va cham,
hay tao `CONTROLS.md` theo dung khuon nay.

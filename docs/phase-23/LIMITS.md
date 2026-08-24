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

| L41 | `live_region_sweep` phu thuoc `--prepare-sla`, von goi `SLA.calibrate_cell` -- CHINH co che tu-hieu-chuan mang loi S14. Khong the mo rong sang 4 cell `rho = 0.650/0.675/0.875/0.900` truoc Lesson 23.21 | `00zzl-amendment-49f.md` muc 3 | Dot 4 hoan; M-125a giu 8 cell, M-125b giu 32 o |
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

| L80 | ★ Tien de cua `L51` SAI: digest lich su KHONG mat. Chung nam trong `provenance.inputs` cua `results/SUPERSEDED/phase-23/eight_cell_sweep_U3_measured_v7.json` (git_hash `05b597f5`). Trong 8 calib: 3 file con song KHOP digest goc (`calib_set_v3`, `_h2_0.700`, `_poisson_0.850`), 1 file KHAC (`_poisson_0.700`: lich su `ec49deb8...`, tren dia `2267423d...`), 4 mat | do 2026-08-24; `results/RAW/phase-22/SURVIVING_CALIB_DIGESTS.json` | 7 parquet Phase 22 (468 MB) nam tren dia: 3 verified, 1 changed, 3 UNKNOWN (`L82`); khong trong git, `git_tracked=0/7`. `_poisson_0.700` va ba UNKNOWN CAM tai dung. `truth_table.parquet` + `sla_calibration.json` doi chieu = KHOP |

| L81 | Artifact QUET NGANG truc (`w_loss_sensitivity` quet {1250, **5000**, 20000}; `t_loss_sweep` quet {0.001..0.1}) khong the thoa `triples == {want}` VE NGUYEN TAC -> nhan `UNREGISTERED` -> mac o `PENDING` VINH VIEN | review doc lap 2026-08-24 muc 5.4; do tren `by_w_loss`/`t_loss_grid` | `PENDING` dinh nghia la "CHO, khong bi THAY THE". Cho mot dieu KHONG THE xay ra thi khong phai dang cho -- la bi MAC. Cung benh `L67` o dang khac. Ca hai quet DEU chua truc chuan trong tap quet, nen mot vai tro `spans_axis` la hop le. CHAN mot hinh paper (sensitivity cua `w_loss`) -- khong phai chuyen ve sinh |

| L82 | Ba parquet Phase 22 (`cbr_0.700`, `poisson_0.925`, `poisson_0.925_V3`) chi co digest bam 2026-08-24 tren chinh file hien tai, khong co moc lich su doc lap | `A061-amendment-61.md` muc 3; `39-l51-adjudication.md` muc 6.2 | Trang thai dung la UNKNOWN, khong phai "khop". CAM tai dung ngang `poisson_0.700` (NOT_ORIGINAL). Ba trang thai: VERIFIED_ORIGINAL / NOT_ORIGINAL / UNKNOWN |
| L83 | `results/` khong duoc bao ve ghi; `calib_set_v3_poisson_0.700.parquet` doi digest giua artifact `05b597f5` va kiem ke `dcd6e53` ma khong co ban ghi ghi de | `A061-amendment-61.md` muc 5 | MAP.md muc 4 la luat khong co co che. Sau backup 23/23 parquet, khoa `results/SUPERSEDED` va `results/RAW` bang `chmod -R a-w`; custody test ghim write bits |
| L84 | `test_pinned_digests_still_match_disk` gop VANG MAT (binh thuong tren clone sach) va DOI NOI DUNG (bao dong o moi noi) vao mot assert | `A061-amendment-61.md` muc 6 | Da tach presence thanh marker `custody`, content drift giu portable. CI/default suite loai custody; may tac gia chay rieng `pytest -m custody` |

| L77 | `w_loss` KHONG phai tham so cham diem, no la tham so SINH: no bi nuong vao calib parquet (`a_twin`, `a_star`, `regret`, `gap_true`, `viol_star` deu suy tu ham chi phi; `calib_set_*_report.json` ghi `w_loss = 5000.0`). Doi `w_loss` o manifest ma giu nguyen parquet -> hai dinh nghia `w_loss` trong cung mot phep tinh | `39-l51-adjudication.md` muc 5; do 2026-08-24 | Bac bo tien de "M-136 chi can chay lai eight_cell_sweep 3 lan tren cung tap du lieu". Do duoc: `--w-loss 1250` -> parity fail 2.815e-02; `20000` -> 8.347e-03; `5000` -> chay duoc (parity = 0 vi hai dinh nghia trung). Cai chan `parity > 1e-12` o `_objective_curve` da TU CHOI sinh so sai im lang. `M-136` can dung lai calib set o TUNG `w_loss` (~11 phut may), thuoc lesson so huu no |

| L72 | Co CLI chet/no-op: `cert/live_region_sweep.py --calib-template` va `cert/abstain_cost.py --calib-template` khong duoc doc; `decision_error_v2.py --boot-metrics` va ba co `--resume` (`l6_campaign.py`, `l6_campaign_fine.py`, `t5_campaign.py`) duoc chap nhan nhung khong doi semantics | `00zzv-amendment-59.md` muc 3; do bang `test_cli_flags_are_wired.py` | Co bi bo qua im lang, cung lop loi `R1`. Sua theo lesson so huu; `live_region_sweep` sang 23.22. Danh sach `KNOWN_DEAD` chi duoc ngan di. Test hieu `getattr`, `dest` alias va hai co controller duoc forward lien module de khong ghi debt gia |

So ke tiep duoc cap: **L85**.

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

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

So ke tiep duoc cap: **L52**.

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

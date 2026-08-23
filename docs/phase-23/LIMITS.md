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
| L14 | ngu nghia fallback do ta chon, khong phai he thong bat buoc | `01-inherited-audit.md:134` | |
| L15 | F1 STICKY reset dau block la quy uoc phuong phap | `01-inherited-audit.md:137` | |
| L16 | ba thang risk do tren cung tap hang nen tuong quan | `01-inherited-audit.md:140` | |
| L20 | intervention-rate check | `04-baselines.md:218` | |
| L21 | khong gian hanh dong hieu dung la 3 | `04-baselines.md:365` | **VA CHAM** -- xem duoi |
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

So ke tiep duoc cap: **L39**.

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
TRANG THAI: MO. Khong duoc sua lang le -- ca ba dong deu nam trong tai lieu
DA KY. Phai co mot amendment quyet dinh cap ma moi cho muc nao, roi ghi
ca hai ten trong bang nay.
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

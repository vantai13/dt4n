# AMENDMENT 23-49c -- Dang ky truc AoI moi, va SUA quyet dinh tang cua 23-49b

Ngay ky : 2026-08-22
Tag     : amendment-49c
Loai    : DANG KY NHAN TRUC + CORRECTION cua amendment 23-49b muc 3

## 1. Su co: test chan cua Lesson 23.17 tu choi 9 artifact cua Dot 1

```text
FAILED test_no_stale_axes.py -- 8 calib_set report + 1 run ledger
  aoi_axis.label = UNREGISTERED
  sla_axis.label = self_calibrated  (chua duoc duyet)
```

**Test lam dung viec cua no.** Va no bat duoc mot quyet dinh sai cua
amendment 23-49b muc 3.

## 2. Hai nguyen nhan TACH BIET

### (a) Truc AoI moi chua duoc dang ky

`AoIModelV7` sinh `z`, va `validity_block` bam `measurements/aoi_model_v7.py`:

```text
sha256 = b6e55a7faceac3b2c736b304ec310a5fc537f000ba2715ff7e473811f737f151
```

Sha nay chua co trong `docs/phase-23/axis_registry.json` -> nhan
`UNREGISTERED`. Day la co che "nhan duoc SUY, khong duoc KHAI" cua Lesson
23.17 hoat dong dung: ma nguon moi thi phai dang ky QUA AMENDMENT.

**Dang ky tai day**, nhan `measured_v7_uniform`, trang thai `ACTIVE`.

### (b) Truc SLA VAN chua duoc duyet -- va do la loi CO THAT

`calib_set` DUNG nguong SLA (`sla_calibration.json`, nhan `self_calibrated`,
trang thai `DEPRECATED` vi loi cau truc **S14**: nguong SLA suy tu chinh du
lieu duoc danh gia). Loi do duoc sua o **Lesson 23.21**, chua lam.

```text
=> Du truc AoI da dung, calib_set VAN dung mot truc SLA co loi cau truc.
=> KHONG duoc dua vao LIVE/.
```

## 3. CORRECTION: `out_stem` cua amendment 23-49b muc 3

Amendment 23-49b quyet dinh artifact truc do duoc vao `LIVE/` "de test chan
canh duoc". Quyet dinh do **som**: mot artifact chi vao `LIVE/` khi **MOI**
truc cua no da duoc duyet, khong phai khi mot truc da duoc sua.

```text
SUA: tier = LIVE  <=>  aoi_axis VA sla_axis DEU nam trong approved_for_live
     Hien tai sla_axis chua duoc duyet -> Dot 1/2/3 vao SUPERSEDED/.
     Sau Lesson 23.21 (sua S14) va mot amendment duyet ca hai truc,
     chung duoc CHUYEN LEN LIVE/.
```

Dat o `SUPERSEDED/` KHONG lam mat canh gac -- chinh cai TANG la loi phat
bieu: "dan xuat, chua phai ban paper dung". Do la thiet ke fail-safe cua
Lesson 23.17 hoat dong dung chieu.

## 4. `approved_for_live` VAN RONG

Amendment nay **khong duyet** truc nao. No chi:

```text
- DANG KY sha cua truc AoI moi (de nhan khong con UNREGISTERED)
- SUA quy tac chon tang
```

Viec duyet truc cho `LIVE/` van cho:

```text
Lesson 23.20 hoan tat  +  gate G23-110 (NC-E1 bit-exact) PASS   -> aoi_axis
Lesson 23.21 sua S14                                            -> sla_axis
va mot amendment RIENG duyet ca hai.
```

Day dung la dieu kien go nhan `CONDITIONAL_ON_DSYNC_51MS` da ky o
amendment 23-44 muc 7.

## 5. `run_ledger_wave*.json` la SO SACH, khong phai artifact

No ghi cong nhanh va thoi gian moi job, khong phai mot ket qua. Cung loai
voi `MANIFEST.md` / `PATH_MAP.tsv` / `_intent.json`.

```text
=> chuyen ve `results/RUN_LEDGER_wave<N>.json` (cap so sach o goc results/)
=> them vao tap BOOKKEEPING cua test_results_is_tiered
```

## 6. Bai hoc

> Mot artifact vao `LIVE/` khi **MOI** truc cua no duoc duyet, khong phai khi
> **mot** truc duoc sua. Sua mot truc va coi artifact la "sach" la dung cach
> bo qua nhung truc chua sua -- va do dung la kieu loi ma Lesson 23.17 duoc
> viet ra de chan.

Chu ky: ____________

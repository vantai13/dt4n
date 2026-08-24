# 37 -- Phan quyet tang `PENDING/`: PASS RONG va 16 artifact vo nhan

Ngay     : 2026-08-24
Lesson   : 23.21i (Viec 2)
Amendment: `A060-amendment-60.md`

## 1. Van de that TE HON `L68` mo ta

`L68` viet: *"Artifact cua `sla_exogenous` dung schema rieng (`sla_axis_label` +
`sla_spec_id`) thay vi truong `validity` chuan."*

Do duoc 2026-08-24 tren ca 16 file `results/PENDING/phase-23/*.json`:

```text
16/16  validity = KHONG CO
```

Khong phai "schema rieng". La **khong co gi ca**.

## 2. Duong thoat -- mot dong

```python
# test/test_no_stale_axes.py  (truoc amendment 23-60)
if not isinstance(payload, dict) or "validity" not in payload:
    pytest.skip("khong phai artifact co khoi validity")      # <- O DAY
```

Logic: *"khong co `validity` -> bo qua"*. Ma `validity` chinh la thu can kiem.

> **PASS RONG (vacuous pass)** -- test "xanh" vi no KHONG KIEM GI CA, chu
> khong phai vi dieu kien duoc thoa. Muon thoat test, chi can khong viet
> `validity`.

Cung lop loi voi `R1` ("sensitivity chua thuc su chay"): mot cai chan khong
bao gio kich hoat. Va repo da co luat cho no -- moi test phai DO it nhat mot
lan (`DC15..DC20` trong `31-exogenous-sla.md`). Test nay chua tung do.

## 3. `G23-206` -- doi chung duong. **PASS: 16 DO.**

Thu tu bat buoc: **SUA TEST TRUOC**, roi moi sinh `validity`.

```bash
# sau khi patch test, TRUOC khi sinh validity:
.venv/bin/python -m pytest test/test_no_stale_axes.py -q
```

```text
16 failed, 30 passed, 5 skipped in 0.22s
```

**16/16 file DO, dung bang so file khong co `validity`.** Do la bang chung cai
chan co suc phan biet.

Day la cau tra loi cho cau hoi tu kiem 2: neu sinh `validity` truoc roi sua
test sau, thu bi mat la **doi chung duong cua chinh bo test** -- khong con
cach nao biet cai chan moi co kich hoat duoc hay khong, vi khong con dau vao
nao lam no do. Test se xanh, va cai xanh do vo nghia y het cai xanh cu.

## 4. Nhan phai SUY RA -- va cho nay huong dan ban dau sai

Huong dan de xuat:

```python
payload["validity"] = sla_only_validity_block(sla_path=MANIFEST, ...)
```

**Khong lam duoc.** Doc ma nguon: `measurements/sla_exogenous.py` dinh nghia
SLA NOI BO trong `SLA_SPECS` va **khong bao gio mo file manifest**:

```python
SLA_SPECS = {"S-A": {"t_delay_ms": 150.0, "t_loss": 0.010, ...},
             "S-B": {"t_delay_ms":  50.0, "t_loss": 0.010, ...},   # CHINH
             "S-C": {"t_delay_ms":  20.0, "t_loss": 0.001, ...}}
```

Bam `sha256` mot file ma script khong he doc la mot **LOI KHAI**, dung cai ma
ca khoi `validity` sinh ra de chong (Luat 2). No se tao ra mot nhan trong sach
ve hinh thuc nhung sai ve noi dung.

### Cach lam thay the: DOI CHIEU NOI DUNG

`sla_manifest_exogenous.py` import `SLA_SPECS` tu `sla_exogenous` -- hai ben
dung CHUNG mot nguon su that. Nen co the CHUNG MINH artifact dung cung truc
voi manifest, thay vi khai:

```python
sla_axis_from_spec(t_delay_ms=..., t_loss=..., w_loss=..., manifest_path=...)
#  -> doc manifest, lay tap {(t_delay_ms, t_loss, w_loss)} cua MOI cell
#  -> neu tap do == {bo ba cua artifact}: muon nhan cua manifest
#  -> neu khong: UNREGISTERED
```

Bo ba lay tu `art["config"]` -- ban ghi cua chinh artifact ve thu no da dung.

## 5. Ket qua phan loai -- va no KHAC huong dan

Huong dan du doan: 14 promote (nhom A) + 1 promote (nhom B) + 1 ha (nhom C),
`PENDING/` ve 0.

Do duoc:

```text
file                            nhan SUY RA            khop manifest  phan quyet
------------------------------------------------------------------------------
rho_grid_main.json              exogenous_g114_S-B     True           PROMOTE
rho_grid_sigma_fixed.json       exogenous_g114_S-B     True           PROMOTE
rho_grid_sigma_low.json         exogenous_g114_S-B     True           PROMOTE
sigma_rho_plane.json            exogenous_g114_S-B     True           PROMOTE
sla_exogenous_S-B.json          exogenous_g114_S-B     True           PROMOTE
sla_exogenous_S-B_ci.json       exogenous_g114_S-B     True           PROMOTE
sla_exogenous_wave4.json        exogenous_g114_S-B     True           PROMOTE
------------------------------------------------------------------------------
sla_exogenous_S-A.json          UNREGISTERED           False          O LAI
sla_exogenous_S-C.json          UNREGISTERED           False          O LAI
a_sweep.json                    UNREGISTERED           (span)         O LAI
t_loss_fine.json                UNREGISTERED           (span)         O LAI
t_loss_local_fine.json          UNREGISTERED           (span)         O LAI
t_loss_sweep.json               UNREGISTERED           (span)         O LAI
w_loss_sensitivity.json         UNREGISTERED           (span)         O LAI
------------------------------------------------------------------------------
eight_cell_sweep_U3_..._v7.json      (truc S14)                       HA
eight_cell_sweep_U3_..._slaB.json    (xem muc 6)                      GRANDFATHER
```

**7 promote, khong phai 15.** Hai ly do, va ca hai deu la ly do DUNG:

1. **`S-A` (150 ms) va `S-C` (20 ms / 0.1%) khong o tren truc da duyet.**
   Chung la CANH TAY DO NHAY, khong phai truc chinh. Phep doi chieu noi dung
   phat hien dieu do tu dong -- khong ai phai nho.
2. **Nam quet (`a_sweep`, ba `t_loss_*`, `w_loss_sensitivity`) khong DUNG mot
   truc, chung SPAN nhieu truc.** Mot quet queo `w_loss` qua {1250, 5000,
   20000} khong dung tren gia tri nao trong ba gia tri do. Gan cho no nhan
   `exogenous_g114_S-B` se la noi doi.

### `G23-209` (`PENDING/` rong) -- KHONG DAT DUOC, va khong nen dat

Nguong da ky doi `PENDING/` ve 0 file. Con 9. Do khong phai viec chua lam
xong; do la mot phat hien ve THIET KE TANG:

> `PENDING/` dang gop hai thu khac han: (a) artifact DANG CHO mot truc duoc
> duyet, va (b) artifact CO Y nam ngoai truc chinh (canh tay do nhay, quet
> queo truc). Loai (b) khong cho gi ca -- no se khong bao gio "toi luot".
> Nhet chung vao mot tang co ten "PENDING" bao dam tang do khong bao gio rong,
> va do la cach mot cai chan mat dan y nghia.

De xuat cho lesson ke tiep: tach mot tang `CONTROLS/` (hoac dat vai tro
`axis_spanning`) cho loai (b). KHONG lam trong lan nay -- no la mot thay doi
tu vung tang, can amendment rieng.

## 6. `L75` -- mot artifact KHAI SAI nguon cua chinh no

Phat hien ngoai du kien, va no nghiem trong hon phan con lai cua Viec 2.

```text
eight_cell_sweep_U3_measured_v7_slaB.json
    w_loss trong MOI cell        : [5000.0]        <- da doc manifest ngoai sinh
    provenance.inputs KHAI doc   : results/LIVE/phase-20R/sla_calibration.json
                                                    <- truc S14 DA DEPRECATED
```

Nguyen nhan, `cert/eight_cell_sweep.py`:

```python
"NC_F_w_loss_source": SLA_ARTIFACT,                       # HANG SO
"inputs": [pin(AMENDMENT), pin(SLA_ARTIFACT), pin(TRUTH_TABLE)] + ...
#                          ^^^^^^^^^^^^ hang so, KHONG phai `args.sla`
```

Ham bao no (`run_eight_cells`) CO tham so `sla_artifact` va CO dung no de
tinh toan -- chi rieng khoi provenance la ghim hang so. Nen artifact tinh
DUNG nhung KHAI SAI.

Da sua ca hai cho sang `sla_artifact`. Nhung artifact hien co thi khong dan
nhan duoc: suy nhan tu mot ban ghi DA BIET LA SAI cung la vi pham Luat 2. No
phai duoc SINH LAI -- va sinh lai dang bi chan boi `L51` (thieu 4/8 parquet
`phase-22`, xem `39-l51-adjudication.md`).

Vi vay no vao `PENDING_NO_VALIDITY_GRANDFATHERED` KEM LY DO, va muc do bi xoa
ngay khi `L51` mo khoa. Danh sach khoi tao RONG va chi duoc ngan di.

## 7. Trang thai cuoi

```bash
.venv/bin/python -m pytest test/test_no_stale_axes.py -q
```

```text
44 passed, 6 skipped in 0.12s
```

```text
LIVE/phase-23/       7 file moi promote
SUPERSEDED/phase-23/ 1 file ha (eight_cell_sweep_U3_measured_v7.json, truc S14)
PENDING/phase-23/    9 file con lai (2 canh S-A/S-C, 5 quet span, 2 eight_cell)
```

`L68` DONG: nguyen nhan da xac dinh (PASS RONG, khong phai "schema rieng"),
cai chan da sua, doi chung duong da ghi (16 DO).

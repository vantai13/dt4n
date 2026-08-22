# Lesson 23.17 -- Dong bang, gan nhan, don kho

Ngay: 2026-08-22
Tag  : `pre-aoi-fix` (06f8a26), `amendment-44` (9e905eb)
Amendment: `docs/phase-23/00zx-amendment-44.md`

Lesson nay khong sinh mot con so ket qua nao. No thay TRI NHO bang MAY.

## 1. Van de do duoc

```text
results/  co 6.262 file, trong do 4.061 duoc track.
    8 thu muc raw_additivity_* khac nhau  ->  696 file
    chi 2 trong 8 duoc tham chieu o bat ky dau
    -> 452 file MO COI: khong ai biet chung thuoc lan chay nao

447 tham chieu duong dan `results/...` hard-code trong .py
    -> khong co lop chi muc nao; moi tham chieu la mot diem gay
```

Va sau Lesson 23.20 se co **ban thu hai cua moi artifact** tren truc `z`
dung. Neu khong phan tang truoc, hai ban chi phan biet duoc bang tri nho.

## 2. Provenance khong cuu duoc loi d_sync

```text
PROVENANCE   git_hash, timestamp, script, argv, constants
             -> "file nay tu dau ra?"      (QUA KHU)
VALIDITY     aoi_source, d_sync, z_edges, sla_source, w_loss, omega
             -> "toi con dung duoc no khong?"  (TUONG LAI)
```

Repo co provenance rat day du va van de `d_sync = 51 ms` troi qua 5 phase,
vi khong o dau ghi PHAM VI HIEU LUC. Do la khoang trong Lesson 23.17 lap.

## 3. Da lam gi

| # | Viec | Ket qua do duoc |
|---|---|---|
| 1 | Tag dong bang `pre-aoi-fix` (annotated) | tro toi 06f8a26 |
| 2 | Sao luu Hang 1 + SHA256 | 105 MB, 5.888 muc, sha `a97fa0a5...` |
| 3 | Amendment 23-44, commit RIENG | 9e905eb, 1 file, tag `amendment-44` |
| 4 | Phan tang `results/` thanh 4 tang | 6.262 file, **0 file bi xoa** |
| 5 | `measurements/validity.py` + registry | nhan SUY tu sha ma nguon |
| 6 | `test/test_no_stale_axes.py` + CI | 3 passed, 5 skipped |
| 7 | `results/MANIFEST.md` tu sinh | 100% dong LIVE co cot "Dung cho" |
| 8 | Canh bao DEPRECATED o `twin/topology3.py` | 0 module song import no |

## 4. Bon tang, khong phai ba

Ban ke hoach v3 viet ba tang. Kiem ke thuc te bac bo thiet ke do:

```text
RAW          5.848 file   93%   du lieu DO THO, Hang 1, chi doc
LIVE             7 file          dan xuat paper dang dung
SUPERSEDED     373 file          dan xuat tren truc z sai
SMOKE           34 file          pilot / preflight / FAILED
             ─────────
             6.262 file
```

93% so file la du lieu do tho, khong phai rac. Ep chung vao LIVE hay
SUPERSEDED la sai khai niem: chung khong phai ket luan, chung la bang chung
goc, va chung khong tai tao duoc.

Mac dinh cua `classify()` la **SUPERSEDED**, khong phai LIVE. Loi bo sot vi
the gay ON AO (hinh thieu du lieu, thay ngay) chu khong gay IM LANG (artifact
truc sai lang le vao paper).

## 5. Doi chung

```text
Test suite TRUOC phan tang    1060 passed,  5 skipped,  0 failed   (531 s)
Test suite SAU  phan tang     1060 passed,  5 skipped,  0 failed   (534 s)
git diff --name-status         4061 R,  0 D      <- KHONG file nao bi xoa
.gitignore viet lai            danh sach ignore truoc/sau IDENTICAL
                               tren layout cu (2201 = 2201)
```

Ba test that bai sau phan tang, ca ba deu la mot rao chan lam dung viec:

```text
test_phase23_conditioning_audit  doc 12-mechanisms.md sinh tu code, phai
                                 sinh lai   -> da sinh lai, lech dung 2 dong
test_phase23_gate_ledger         amendment nhac G23-74/97/98/99 chua co
                                 trong so   -> da ghi vao GATES.md
test_phase23_lesson237_structure pin provenance tro toi duong dan TRUOC
                                 phan tang  -> them measurements/path_map.py,
                                 KHONG sua ban ghi lich su
```

Diem thu ba dang chu y: cach sua **khong** phai viet lai provenance. Mot
artifact ky ngay 2026-08-19 ghim duong dan cua ngay do la ghi DUNG. SHA256
trong pin van xac minh noi dung; chi VI TRI la mat. Vay bo sung mot phep tra
vi tri (`results/PATH_MAP.tsv`, 6.262 dong), dung sua ban ghi.

## 6. Doi chung DUONG cho test chan

Dat mot artifact mang nhan truc CU vao `results/LIVE/`:

```text
E  AssertionError: phase-23/_positive_control.json:
   aoi_axis.label = 'assumed_sawtooth_51ms' chua duoc duyet cho LIVE.
       duyet hien tai: []
   1 failed, 3 passed, 5 skipped
```

Go ra -> `3 passed, 5 skipped`. Test chan hom nay PASS mot cach tam thuong
(7 file LIVE deu legacy-exempt). Do la dung: gia tri cua no o Lesson 23.20,
khi mot `calib_set` moi muon vao LIVE va bi bat phai cap nhat
`approved_for_live` -- viec do bat phai viet mot amendment.

## 7. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-74 | raw Hang 1 len Zenodo, co DOI | **MO** -- can tai khoan nguoi dung |
| G23-75 | tag `pre-aoi-fix` ton tai va da push | **MO** -- tag co o local, chua push |
| G23-76 | MANIFEST phu 100% LIVE, cot "Dung cho" da dien | PASS |
| G23-77 | `validity.py` ton tai, >=1 script goi `validity_block()` | PASS (2 script) |
| G23-78 | `test_no_stale_axes.py` chay duoc va nam trong CI | PASS |

Hai gate MO deu vi mot ly do: chung can thong tin xac thuc cua nguoi dung
(tai khoan Zenodo, credential git). Chung KHONG duoc cham PASS ho.

## 8. Con lai cho nguoi dung

```text
1. Upload ~/archive/dt4n-raw-measurements-20260822.tar.gz len Zenodo,
   dan DOI vao amendment-44 muc "DOI raw data" va muc 8.
2. git push origin main pre-aoi-fix amendment-44
3. Ky ten vao amendment 23-44 (dong cuoi).
4. Ra soat cot "Dung cho" cua MANIFEST: doan danh dau **can xac nhan
   hinh/bang** la suy tu tham chieu code, chua phai y dinh cua tac gia.
```

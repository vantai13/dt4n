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
| G23-32 | 23.6 | NOT_RUN | - |
| G23-33 | 23.6 | NOT_RUN | - |
| G23-34 | 23.6 | NOT_RUN | - |
| G23-35 | 23.6 | NOT_RUN | - |
| G23-36 | 23.6 | NOT_RUN | - |
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

## Lesson da dong

```text
23.1  23.2  23.3  23.4  23.5A  23.5B  23.5C
```

Gate thuoc mot lesson trong danh sach nay KHONG duoc mang trang thai `NOT_RUN`.
Neu no chua duoc cham thi trang thai dung la `DEBT`, va mon no do bi GHIM trong
test de khong the xuat hien them mot cach im lang.

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

## Ghi chu ve pham vi ID

So nay chi chua ID dang `G23-*`. Cac ho ID khac -- `PC23-*`, `NC23-*`, `V23-*`,
`L2*`, `S*`, `C23v2-*`, `NC23v2-*` -- thuoc tu vung khac (doi chung, gioi han)
va KHONG duoc tron vao day. Mot so, mot loai ID. Neu can, tao `CONTROLS.md` va
`LIMITS.md` rieng.

# PLAN -- Phase 23

Ngay khoa ban hien hanh: 2026-08-14

Repo khong co file `PHASE_23.md` goc tai thoi diem tag `phase-23-start`.
File nay dong vai tro PLAN tracked cho Phase 23 tu cac nguon da co:

```text
docs/phase-23/00-preregistration.md
docs/phase-23/01-inherited-audit.md
docs/phase-23/00b..00g-amendment-*.md
```

## Scope dang duoc phep chay

Lesson 23.1 duoc phep chay sau khi cac amendment duoi day duoc commit:

```text
23-1  cong bo day du P(a*=P1) la pilot/description
23-2  chuyen thang risk chinh cua cau chuyen he thong sang regret
23-3  chot F3-a va bao cao F3-idl/F3-exp (superseded boi 23-6)
23-4  sua G23-5 thanh ba menh de co y nghia
23-5  them sticky diagnostics: sticky_age, reject_run_len, initial_state_share
23-6  rut lai F3 look-ahead accounting; F3-a == F1 theo installed path
```

Lesson 23.2 va 23.3 chi duoc chay theo cac dong prediction da khoa trong
`00-preregistration.md`.

## Scope bi chan

Neu can cac dong du doan E/A/R/X cua `PHASE_23.md` goc cho Lesson 23.4--23.7,
phai them amendment TRUOC khi chay lesson tuong ung. Khong duoc them cac dong
do sau khi da nhin ket qua.

## Cac cau hoi khoa cua 23.1

```text
1. Khi nhieu hang bi reject, fallback nao lam risk_system tot hon neo?
2. F2 STATIC co vuot nguong hoa von err|fallback < 0.3592 hay khong?
3. F1 STICKY gan F2 hay gan F3, va dieu nay duoc giai thich bang sticky_age?
4. F3-a co suy bien thanh F1 sau khi cham theo installed path khong?
5. Ket luan he thong co giu tren regret, err, va sla_rate hay chi mot thang?
```

## Dinh nghia fallback khoa

```text
F2 STATIC : reject -> duong tinh ngan nhat P1.
F1 STICKY : reject -> quyet dinh accept gan nhat trong cung block, neu chua co
            thi P1.
F3 WAIT   : F3-a, cho mot lan den refresh ke tiep trong cung block, nhung
            row-level installed path trong luc cho giong F1 STICKY.
```

Sau Amendment 23-6, F3-idl/F3-exp cu bi rut lai:

```text
F3-a action risk : bang F1 STICKY.
F3 delay/horizon : chi la diagnostic, khong tao chinh sach row-level moi.
```

## Artifact dau vao

Artifact local nang:

```text
results/phase-22/calib_set_v3.parquet
```

Duoc tai tao bang lenh trong `docs/phase-23/01-inherited-audit.md` va khoa
bang `results/phase-23/INHERITED.sha256`.

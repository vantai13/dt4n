# PLAN -- Phase 23

Ngay khoa ban hien hanh: 2026-08-14

Repo khong co file `PHASE_23.md` goc tai thoi diem tag `phase-23-start`.
File nay dong vai tro PLAN tracked cho Phase 23 tu cac nguon da co:

```text
docs/phase-23/00-preregistration.md
docs/phase-23/01-inherited-audit.md
docs/phase-23/02-fallback.md
docs/phase-23/03-threshold-families.md
docs/phase-23/04-baselines.md
docs/phase-23/00b..00o-amendment-*.md
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
23-7  lam min luoi kappa MOT LAN vi argmin o bien khong-suy-bien dau tien
23-8  khoa du doan shrinkage C3-vs-B2 cho Lesson 23.3
23-9  khoa doi chung F1 low-kappa truoc paired-CI diagnostic rieng
23-10 khoa khung Lesson 23.2: ho nguong nhu ranking, B6-sys, T5..T9
23-11 khoa canh bao AURC mat do luoi giua hai ho nguong
23-12 khoa chi so headline Phase 23 cho risk_system hinh chu U
23-13 ha B4 variance proxy thanh gate vi B4 dong nhat B3
23-14 tach B6 du doan va B6-sys he thong; them gate dang dong
23-15 them G23-21/G23-21b va chance-agreement cho co che break-even
23-16 sua dinh ly C3 tu K khoang chi phi sang K-1 bien, khop alpha/3 trong code
23-17 chay G23-17a ba xac suat bien truoc moi sweep Lesson 23.4
23-18 khoa quy tac so sanh cross-cell: err headline, regret phan ra ba thua so,
      SLA khong lam headline, va E4-moi S1--S7
23-19 rebuild parity artifact cho hai cell moi; khoa Co che #9 lift>swing va
      gate G23-23; ghi G23-15/G23-17 FAIL
23-20 khoa 7 bac tu do D1--D7 cua studentized max-score; dieu chinh dai v1->v2
23-21 huy bo PC-S-1 small-n bi tran chan (level=1.0); ghi MISS cho S-5 dai v2
      (loi muc do tong hop); them PC-S-1d sigma nhieu chieu; khoa du doan
      H-23.11-*, E-1/E-2/E-3 (23.9), R-23.6-1
23-22 khoa thu tuc AURC cho GO-1: truc y err_given_accept (khong phai
      err_system), luoi chung 4001 diem tren [0.6,1.0], chuan hoa /0.40,
      cam ngoai suy, suy bien = err_neo < 0.02, paired block bootstrap
      B=2000, quyet dinh theo CI95_high; khoa du doan A-1'..A-6'; NT-v2-6
23-23 Phat hien 8: cua so [0.6,1.0] chi tua tren 3 nut kappa; khoa luoi mit
      KAPPA_REFINED (21 diem) va B-D12/13/14; ha A-7'/A-8' xuong [MO TA] vi
      do qua tay trong buoc kiem tra thiet ke
23-24 NT-v2-7 (muc ra soat du doan bat buoc trong moi amendment); siet GO-1
      bang can Bonferroni 3 cell; khoa C-D1..C-D6 cho GO-2 (draw toan cuc,
      max-t dong thoi, B=2000, NC-C-1 ba variant); du doan C-1..C-5
23-25 doi dinh danh Lesson 23.6 C-* -> K-* (va cham voi GO-2); ghi F-23.5-2
      (sigma3/sigma1 sap hang ca [A] lan [C]); NT-v2-8 (c_supt phai duoc MO
      PHONG, khong suy tu tom tat vo huong); khoa K-D0..K-D7 va K-1..K-8
```

## Trang thai Lesson 23.6

```text
23.6 duong bien risk-coverage va chi phi abstain c*   CHUA CHAY -- khoa Amd 23-25
```

## Trang thai Lesson 23.5

```text
23.5[A] studentized max-score / GO-3        DONG (2026-08-17), nhan EXPLORATORY
23.5[B] AURC rieng phan [0.6, 1.0] / GO-1   DONG (2026-08-17), GO-1 DAT 3/3 cell
23.5[C] dai dong thoi sup-t / GO-2          DONG (2026-08-18), GO-2 DAT 3/3 cell
```

Lesson 23.2 duoc phep chay theo Amendment 23-10. Lesson 23.3 chi duoc chay
theo cac dong prediction da khoa trong `00-preregistration.md` va bo sung
B6-sys/B4 gates cua Amendments 23-10, 23-13, va 23-14. Lesson 23.4 phai dung
headline metrics cua Amendment 23-12 thay vi AURC toan dai, va phai dung
dinh ly C3 da sua trong Amendment 23-16: certificate tren `K-1` bien, khong
tren `K` chi phi tuyet doi. Truoc bat ky sweep 23.4 nao, phai doc G23-17a/b/c
trong Amendments 23-17 va 23-18, phai dung artifact 45 cot da khoa trong
Amendment 23-19, va phai bao cao G23-23 lift law khi dien giai cross-cell.

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

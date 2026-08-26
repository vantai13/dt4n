# AMENDMENT 23-71 -- QUY TAC 23-STOP: kiem soat pham vi lesson

Ngay ky : 2026-08-26

Moc     : sau tag `lesson-23-22-complete`, TRUOC khi chay G23-285..288

Loai    : QUY TAC VAN HANH (khong phai tien dang ky mot phep do)

## 0. Vi sao amendment nay ton tai

Lesson 23.22 duoc `PHASE_23_v3.md` cap 4 NGAY va mot dai gate. Thuc te no
tieu:

```text
23.22        Task A0/A/B/B-2/B-3     G23-230..269   40 gate
23.22c       A069 pilot              G23-270..276    7 gate
23.22d-W     A070 cua so             G23-277..279    3 gate
23.22d-E     A070 nhanh E            G23-280..284    5 gate
A070b        overlap                 G23-285..288    4 gate
                                                   ---------
                                                    59 gate
```

Con lai: 7 lesson (23.23..23.29) + Phase 24 + Phase 25.

59 amendment truoc kiem soat NOI DUNG phep do. Khong cai nao kiem soat
PHAM VI. Day la thieu admission control: toc do sinh cau hoi moi lon hon
toc do dong cau hoi cu, nen hang doi khong bao gio rong.

`L105` da ghi "tap mu la tai nguyen can kiet" va `L108` da ghi "day la lan
tieu dau tien, ma khong mua duoc quyet dinh nao". Chan doan da dung; con
thieu mot LUAT.

## 1. Quy tac

### R1 -- NGAN SACH GATE KY TRUOC

Moi lesson tu 23.23 tro di phai ky mot ngan sach gate TRUOC khi viet dong
code cham diem dau tien. Vuot ngan sach -> DUNG lesson, khong xin them.

```text
23.23   8 gate      23.24   4 gate      23.25   5 gate
23.26  10 gate      23.27   6 gate      23.28   5 gate      23.29   8 gate
```

Con so nay co the doi bang mot amendment KY TRUOC khi lesson bat dau.
KHONG duoc doi khi lesson dang chay.

### R2 -- `L*` MOI KHONG DUOC MO NHANH TRONG CUNG LESSON

Mot gioi han `L*` phat sinh trong lesson N KHONG duoc mo mot nhanh trong
lesson N. No di vao `docs/phase-23/BACKLOG.md` voi ba cot bat buoc:

```text
(a) chi phi uoc luong (gio may + gio nguoi)
(b) no thay doi PHAT BIEU nao trong CLAIMS.md   <- cot quyet dinh
(c) neu KHONG lam, phai in cau canh bao gi
```

Chi khi cot (b) KHAC RONG thi `L*` do moi duoc xet mo mot lesson rieng, va
viec mo do can mot amendment.

### R3 -- IN NGAN SACH THOI GIAN O MOI DOC DONG LESSON

Moi `docs/phase-23/*-close-*.md` phai co mot muc:

```text
## Ngan sach
Da tieu   : X / 35 tuan (MASTER_PLAN_v8 PART II)
Con lai   : N lesson + Phase 24 + Phase 25
Gate lesson nay: G / <ngan sach R1>
```

Con so nay PHAI xuat hien. Khong duoc bo qua, khong duoc de trong.

### R4 -- CAU HOI CHAN

Truoc khi mo BAT KY nhanh nao, tra loi bang van ban trong amendment:

> "Neu KHONG lam nhanh nay, paper mat CAU NAO trong `CLAIMS.md`?"

Khong tra loi duoc bang mot ID `CL-*` cu the -> KHONG duoc mo.

## 2. Ap R4 nguoc lai cho A070b (ca thu dau tien cua luat)

Cau hoi: neu KHONG chay `G23-285..288`, paper mat cau nao?

Tra loi: mat `CL-08` -- "bao dam chuyen giao duoc QUA HO TAI". `L92` ghi
ho tai bi rang buoc hoan toan voi `rho` trong tap 8 cell song, nen moi
phat bieu ve ho tai hien bi CAM. `M-224` la phep do DUY NHAT giu `rho`
co dinh bang THIET KE (OVERLAP-4 tai `rho` thuoc {0.744, 0.750}), khong
bang hieu chinh hoi quy.

=> Mat mot phat bieu cu the => DUOC PHEP chay. Ngan sach: 4 gate, khong
   mo them.

## 3. Pham vi va gioi han cua chinh amendment nay

```text
N1  R1 khong ap nguoc cho 23.22. Lesson do da dong; ap luat hoi to len mot
    ket qua da co la mot dang HARKing ve quan tri.
N2  Ngan sach o R1 la UOC LUONG, khong phai ket qua do. Neu mot lesson
    vuot ngan sach vi mot ly do CHINH DANG (vd doi chung am FIRE va bat
    buoc phai truy), thi phai ky amendment mo rong TRUOC khi vuot, va ghi
    ly do. Ngan sach de bat buoc DUNG LAI VA SUY NGHI, khong phai de cam.
N3  R2 co the lam bo sot mot `L*` that su quan trong. Chan: `BACKLOG.md`
    phai duoc ra lai o dau MOI lesson, va moi dong bi bo qua >= 3 lan phai
    duoc ghi vao Threats to Validity cua paper.
```

## 4. Gate

Amendment nay KHONG sinh gate do luong. No sinh mot test cau truc:

| Test | Noi dung |
|---|---|
| `test_close_doc_has_budget_section` | moi doc dong lesson tu 23.23 co muc "Ngan sach" |
| `test_backlog_rows_have_three_columns` | moi dong `BACKLOG.md` co du (a)(b)(c) |

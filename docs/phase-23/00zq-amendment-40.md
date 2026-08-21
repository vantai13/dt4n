# AMENDMENT 23-40 -- Lesson 23.16: dinh vi bien va phan tang theo err_neo

Ngay: 2026-08-21
Trang thai: **SAU khi doc artifact Lesson 23.15; TRUOC khi chay SLA
calibration, truth-domain check, calib-set builder, hoac bat ky metric nao tai
rho_bar moi.**

## 0. Khai bao hau nghiem va khong sua hoi to

Phan hoach song/chet la phat hien hau nghiem cua Lesson 23.15. Bien phan
tang `err_neo=P(a_twin!=a_star)` khong dung C3, `q_hat`, `kappa`, fallback
hay `Delta`; no chi dung twin va truth table, nen co the tinh truoc thi
nghiem certificate. Nguong khoa cho Lesson 23.16:

```text
cell SONG <=> err_neo >= 0.05
```

Khoang trong da do la `0.002944 -> 0.126536 = 43.0x`; moi nguong trong
`[0.005,0.12]` tao cung phan hoach cua tam cell cu. Tinh vung nay la readout,
khong bien nguong hau nghiem thanh prereg cua Lesson 23.15.

M-47 giu **MISS**. Dai `<0` khong luong truoc `Delta==0` va tron khong hieu
ung voi hieu ung nguoc; day la loi thiet ke du doan cua nguoi ky. M-48 giu
**MISS** vi spread 8-cell co mau so 0. Khong sua verdict cu.

## 1. Cell moi va thu tu

Nhom A, dinh vi bien tren truc Poisson:

```text
poisson@0.875, poisson@0.900
```

Nhom B, severe test qua ho luu luong:

```text
h2@0.650
```

Neu va chi neu `h2@0.650` truot truth-domain control o Muc 3, loai cell do
truoc khi build va dung fallback da khoa `h2@0.675`. Fallback cung phai qua
cung control; neu truot thi khong them H2 cell nao. Khong duoc chon giua
`0.650/0.675` bang `err_neo`, lift, swing hay Delta.

Moi rho moi phai duoc chay fixed-point SLA calibration rieng; cam noi suy
`w_loss`. Artifact Phase 20R goc khong bi ghi de. Output SLA mo rong:

```text
results/phase-23/sla_calibration_lesson23_16.json
```

## 2. Du doan khoa M-53..M-57, M-47b, M-48b

| ID | Dai luong (thang / muc / tap hang) | Nhan | Dai khoa |
|---|---|---|---|
| M-53 | `rho_hit`: rho Poisson nho nhat trong luoi da do co `lift-swing>0` | [NGOAI SUY] | `0.860 .. 0.925` |
| M-54 | dau `lift-swing` khong dao nguoc tu duong ve am tren Poisson `rho in [0.850,0.925]` | [CO CHE] | CO |
| M-55 | `err_neo` tai poisson@0.875 va @0.900 | [CO CHE] | `0.15 .. 0.26` ca hai |
| M-56 | H2 candidate qua domain co `err_neo>=0.05` | [NGOAI SUY] | CO |
| M-57 | neu H2 candidate SONG, `lift-swing<0` | [NGOAI SUY] | CO |
| M-47b | `Delta<=0` tai ratio `0.8352557797157567` tren moi cell SONG giu kin | [NGOAI SUY] | CO |
| M-48b | twin_deg spread tren 4 cell SONG cua Lesson 23.15 | [TAI TINH] | `1.00 .. 1.30` |

`rho_hit` la endpoint luoi dau tien co dau duong, khong phai zero crossing
lien tuc. Bracket bien la cap diem ke nhau co dau am/duong. M-54 dung chuoi
dau, khong doi thanh tinh don dieu cua do lon. Cell SONG giu kin cua M-47b
gom `poisson@0.960` va moi cell Lesson 23.16 co `err_neo>=0.05`; ba cell cu
da dung truoc Lesson 23.15 khong tinh vao M-47b.

M-48b tai tinh artifact da cong bo (`1.059170x`) va khong tinh prediction-hit.
M-57 co chu dich khoa dau am de severe-test gia thuyet H2: neu duong, khong
tong quat hoa bien Poisson qua ho luu luong.

## 3. Truth-domain control bat buoc

Sau SLA calibration nhung truoc calib-set build, tai moi seed `101..105`,
dung dung rho generator va `TruthTable.path_tables`; yeu cau:

```text
max(TruthTable.clip_log.values()) < 1e-4
```

Control nay do clip mien **do duoc** cua truth table, khac clip mien vat ly
cua loss trong Lesson 23.7-bis. Cell truot bi loai; ghi link, seed va ty le,
khong bao cao `err_neo`, lift, swing hay Delta cua cell do.

## 4. He thong dong bang va controls

C3, alpha/Bonferroni, `GAMMA_OP`, fallback families, tie-break va
leave-one-seed-out cross-fitting giu nguyen Amendments 38--39. Objective
curve dung ratio `0.50..1.50` step `0.05`; `w_loss` va `loss_exchange` lay
tu SLA artifact mo rong, khong hardcode.

NC-G: ba cell cu tai lap F2 den `1e-12`.  
NC-H: domain control chay truoc builder va ghi du moi seed/link.  
NC-I: `Delta=reject_share*(swing-lift)` tren moi cell hop le.  
NC-J: selection row/seed-disjoint va F6 chi dung hai bin/action map.  
NC-K: artifact ghi ro cell requested, passed, excluded va fallback cascade.

## 5. Stop rule va output

Neu M-53/M-54 FAIL, khong lam day luoi them; Figure chi trinh bay cac diem
roi rac va bracket neu co. Moi MISS bao nguyen trang, khong retune nguong
song, gate, fallback hay ratio.

Output khoa:

```text
cert/live_region_sweep.py
test/test_phase23_live_region.py
results/phase-23/sla_calibration_lesson23_16.json
results/phase-23/live_region_sweep.json
results/phase-23/fig1_live_region.png
docs/phase-23/17-live-region-boundary.md
```

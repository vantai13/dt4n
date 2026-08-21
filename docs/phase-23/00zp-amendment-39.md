# AMENDMENT 23-39 -- Lesson 23.15: xac nhan objective tren nam cell chua dung

Ngay: 2026-08-21
Trang thai: **SAU khi doc ba artifact Lesson 23.14 va SLA cell manifest;
TRUOC khi dung calib set, chay fallback, hoac nhin bat ky so nao cua nam cell
moi.**

## 0. Khai bao phat hien hau nghiem

Sau khi nhin ba duong objective da cong bo, noi suy cho thay ca ba co
`Delta<0` khi `r=w_eff/w_loss` nam duoi khoang `0.867`. Nguong `0.867` la
readout hau nghiem, khong phai prediction cua ba cell cu. Amendment nay khoa
no thanh du doan truoc khi chay nam gate cell chua dung.

`LOSS_EXCHANGE=0.01` trong `measurements/sla_calib_v2.py` la tham so quy doi
van hanh va `w_loss=T_delay/LOSS_EXCHANGE`. Vi vay:

```text
r = w_eff / w_loss
LOSS_EXCHANGE_eff = 0.01 / r
```

## 1. Tap cell va pham vi

Tap seen da cong bo:

```text
poisson@0.925, poisson@0.850, h2@0.700
```

Tap confirmation chua dung, khoa tu cac gate cell kha thi trong
`results/phase-20R/sla_calibration.json`:

```text
poisson@0.700, poisson@0.960,
h2@0.850, h2@0.925, h2@0.960
```

Tat ca la offline va dung truth table/topology hien co. Cam sua `LINKS`, cam
retune gate/fallback sau khi nhin cell moi, khong chay Mininet, va khong doc
artifact AoI. Fallback families, tie-break, leave-one-seed-out cross-fitting,
C3 gate, `GAMMA_OP`, va Bonferroni giu nguyen Amendment 38.

## 2. Objective sweep khoa

Quet chung:

```text
r = 0.50, 0.55, ..., 1.50
```

Tai moi cell, lay `w_loss` truc tiep tu cell tuong ung trong
`sla_calibration.json`; cam hardcode cac gia tri w_loss da quan sat. Dong bang
`y_hat`, C3 accept set, family selection va action map tai objective goc.
Chi tinh lai truth cost/a_star tai `w_eff=r*w_loss`.

De tranh mo ho trong cum "smallest r", dinh nghia bien chung:

```text
r_cross = supremum r sao cho Delta(r)<0 tren TAT CA 5 cell moi,
          tinh bang noi suy tuyen tinh tai zero crossing som nhat theo r.
```

Neu mot cell khong cross trong dai, dung bien dai phu hop; khong mo rong grid.

## 3. Dai khoa M-46..M-52

| ID | Dai luong | Nhan | Dai khoa |
|---|---|---|---|
| M-46 | `r_cross` chung cua 5 cell moi | [XAC NHAN] | `0.80 .. 0.95` |
| M-47 | `Delta(r=0.8352557797157567)<0` tren ca 5 cell moi | [XAC NHAN] | CO |
| M-48 | spread `twin_deg` max/min cua C3+F2 tren 8 cell | [NGOAI SUY] | `1.00 .. 1.30` |
| M-49 | spread `prior_deg` max/min cua C3+F2 tren 8 cell | [NGOAI SUY] | `>3.0` |
| M-50 | `sign(lift-swing)=sign(-Delta)` cua C3+F2 | [DINH LY] | `8/8` |
| M-51 | trung binh so o reject F6 nonempty qua cell/fold | [CO CHE] | `4 .. 8` |
| M-52 | mean 8-cell `(Delta_selected-Delta_F2)` | [NGOAI SUY] | `<=0` |

M-48..M-50 dung decomposition F2 de noi truc tiep voi M-40/M-41. M-46,
M-47 dung fallback calibration-selected; M-52 la doi chung selection-vs-default.

## 4. Controls bat buoc

**NC-D -- parity ba cell cu.** Runner moi phai tai lap F2:

```text
poisson@0.925 : -0.012868849344056688
poisson@0.850 : +0.0031202059335916077
h2@0.700      : +0.0038662551728414207
tolerance     : 1e-12
```

**NC-E -- leakage va dong nhat.** NC-A row/seed-disjoint, NC-B gioi han
thong tin F6, NC-C F2 parity va dong nhat
`Delta=reject_share*(swing-lift)` phai dung tren du 8 cell.

**NC-F -- nguon objective.** `w_loss_for_cell` phai doc
`results/phase-20R/sla_calibration.json`; code runner cam hardcode bat ky
`w_loss` cu the.

## 5. Stop rule va output

Neu M-46 hoac M-47 MISS, bao MISS nguyen trang, khong doi nguong `0.867`,
khong retune va khong them cell. Khi do `0.867` van chi o Discussion. Cac
luan diem transfer, bottleneck va diagnostic khong phu thuoc dau Delta van
giu nguyen.

Output khoa:

```text
cert/eight_cell_sweep.py
test/test_phase23_eight_cell.py
results/phase-23/eight_cell_sweep.json
results/phase-23/fig1_lift_vs_swing_8cells.png
results/phase-23/fig2_objective_eight_cells.png
docs/phase-23/16-eight-cell-confirmation.md
```

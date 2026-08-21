# AMENDMENT 23-32 -- Lesson 23.7-bis: kiem toan tang ap phan du S7

Ngay: 2026-08-21
Trang thai: **KHOA TRUOC KHI VIET `cert/residual_level_audit.py` VA TRUOC KHI
CHAY PHEP DO.**

Amendment nay khong xoa, sua, hay cham lai ket qua Lesson 23.7. No mo mot phep
kiem toan moi de tach ba co che khi phan du loss duoc do o tang duong nhung
duoc chia va bom vao tung link:

```text
H_path  : bom o tang duong
H_link0 : chia deu per-link, KHONG cat loss tai 0
H_link1 : chia deu per-link, CO cat loss tai 0 (hien thuc Lesson 23.7)
```

Muc tieu la do rieng dong gop cua phi tuyen `1 - prod(1-p)` va cua phep cat
mien `loss >= 0`. Ket qua cu cua Lesson 23.7 tro thanh doi chung H_link1,
khong bi rut khoi artifact hay tai lieu.

---

## 1. Estimand va pham vi

Nguon phan du duoc ghim:

```text
results/phase-20R/residual_cascade.json
channel = loss
level   = per_path
mode    = poisson
point   = -0.009521786236599921
CI90    = [-0.010135081793680400, -0.008908490679519442]
```

Estimand cua audit:

```text
Ty le hang ma a* doi so voi bang tra goc, tren dung rowset cua moi cell
Phase 23, khi cung mot phan du duong duoc ap theo H_path, H_link0, H_link1.
```

Ba endpoint giu nguyen Lesson 23.7:

```text
r_star     = -0.008868196569470351
point      = -0.009521786236599921
ci90_worst = -0.010135081793680400
```

Pham vi confirmatory la `poisson@0.925` va `poisson@0.850`. Cell
`h2@0.700` la **NOT_APPLICABLE** cho audit loss nay: residual file khong co
record `(mode=h2, channel=loss)`. Khong duoc bom residual Poisson vao H2 chi
de tao du ba artifact; lam vay se tao them mot lech mode ngoai estimand.

---

## 2. Bang du doan khoa

| ID | Dai luong | Nhan | Dai khoa |
|---|---|---|---|
| M-23 | `flip_fraction(H_path)` tai ca 3 endpoint, tren moi cell Poisson | [TAT DINH] | `= 0.000000` chinh xac |
| M-24 | `flip_fraction(H_link0)` tai `point`, cell `poisson@0.925` | [CO CHE] | `0.000--0.020` |
| M-25 | `clip_share_of_total` tai `point`, cell `poisson@0.925` | [CO CHE] | `> 0.90` |
| M-26 | `flip_fraction(H_link1)` tai `point`, cell `poisson@0.925` | [DOI CHUNG] | `abs(value - 0.2130) < 0.005` |

M-23 khong tinh diem prediction-hit vi no duoc suy tu bat bien
`argmin_p(c_p + w*r) = argmin_p(c_p)`. Neu M-23 sai, phai doc no nhu mot loi
cai dat hoac mot tien de ngam bi vi pham, khong noi dai hay doi dinh ly sau khi
nhin so.

M-26 bat buoc dung lai lop H_link1 cua `measurements.band_v2`, rowset va
pipeline tao ma tran cua Phase 23. Khong duoc viet mot ban sao gan giong roi
goi sai lech la hien tuong.

---

## 3. Doi chung va chan doan bat buoc

```text
NC23v2-10: shift = 0
            => H_path = H_link0 = H_link1 = 0 hang lat CHINH XAC.

G23v2-S7-1: moi duong trong topology_v7 co cung 3 link.
G23v2-S7-2: source record co level=per_path, channel=loss, mode=poisson.
G23v2-S7-3: artifact ghi clip_events, eval_count va clip_ratio cho moi nhanh.
G23v2-S7-4: tong cac cap a*_old -> a*_new bang dung n_flip.
```

Nhanh H_link0 cho phep loss link am co chu dich va chi la doi chung tach co
che; no khong duoc dien giai nhu mot mo hinh vat ly. Nhanh H_path va H_link1
phai ghi moi lan cham rang co cat mien hay khong.

---

## 4. Quy tac ket luan khoa truoc

```text
KICH BAN A  clip_share_of_total > 0.90
  => S7 duoc xac nhan bang so.
  => Rut ket luan "khong co kich ban an toan" cua 23.7[C] doi voi phan du
     CHUNG; L10 van mo cho thanh phan VI SAI chua do.

KICH BAN B  0.50 <= clip_share_of_total <= 0.90
  => Ca phi tuyen ghép loss va clipping cung dong gop; bao cao ca hai.
  => L10 van mo.

KICH BAN C  clip_share_of_total < 0.50
  => Gia thuyet clipping chi phoi S7 bi bac bo; ket qua am 23.7[C] dung vung
     trong audit nay; L10 van mo.
```

Neu `H_path != 0`, ba kich ban tren **khong du dieu kien de cham** cho den khi
phan tich xong tien de bi vi pham. Khong duoc ep ket qua vao A/B/C.

---

## 5. Lenh khoa

```bash
python -m pytest test/test_phase23_residual_level.py -v
python -m cert.residual_level_audit --cell poisson@0.925
python -m cert.residual_level_audit --cell poisson@0.850
python -m cert.residual_level_audit --cell h2@0.700
```

Lenh thu ba phai sinh artifact `NOT_APPLICABLE` co ly do ro rang, khong duoc
im lang dung record sai mode.

Sau khi file nay duoc commit, tag `lesson-23.7bis-pre` tro vao commit khoa.


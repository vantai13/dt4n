# AMENDMENT 15 -- Lesson 20R.7: sua kenh cua ban do co che

Ngay ky: 2026-08-10
Trang thai: KY TRUOC KHI VIET `measurements/mechanism_map.py`.
Quan he: BO SUNG cho Lesson 20R.7; khong sua cac artifact 20R.6.

---

## 1. Estimand

Bang loi cua Lesson 20R.7:

```text
Do doc va do cong cua CHI PHI theo rho, trong do
cost = delay + w_loss * loss.
```

Lesson 20R.7 KHONG do chinh la `d2(delay)/d(rho)^2`. Delay curvature duoc giu
lam phu luc/doi chung, khong lam hinh giai thich chinh.

## 2. Ly do sua truoc code

Lesson 20R.5 da xac lap co che la loss-driven va don dinh, khong phai
delay-driven. Tai o `poisson@0.925`:

```text
w_loss = 3222.244681647411
loss_path ~= 0.0504
w_loss * loss ~= 162 ms
delay_path ~= 40.4 ms
ti le loss/delay ~= 4.0x
```

Tai `h2@0.925`:

```text
w_loss = 4515.904012589386
loss_path ~= 0.132
w_loss * loss ~= 596 ms
delay_path ~= 45.6 ms
ti le loss/delay ~= 13.1x
```

Do do ke hoach cu ve `d2(delay)/d(rho)^2` do thanh phan chiem khoang
8--20% cua cost. Sua estimand nay la hop le ngay ca neu ke hoach cu cho ket qua
dep; day la sua truoc khi viet code mechanism, khong phai sua sau khi xem hinh.

## 3. Ban do phai ve

Lesson 20R.7 phai ve toi thieu ba ban do chinh:

```text
1. d(loss)/d(rho)      theo family, bw, q, rho
2. d2(loss)/d(rho)^2   theo family, bw, q, rho
3. d(cost)/d(rho) = d(delay)/d(rho) + w_loss * d(loss)/d(rho)
```

Ban do `d2(delay)/d(rho)^2` chi la phu luc de chung minh bang hinh rang kenh
loss chi phoi cost.

## 4. Ky vong co che

Co che duoc ky truoc khong phai "rho cao hon thi err lon hon". G4 da fail va
H7 cho thay dang don dinh. Ky vong moi:

```text
err lon nhat o vung rho ma |d2(loss)/d(rho)^2| lon nhat,
khong nhat thiet o rho cao nhat.
```

Kiem tra cong bo:

```text
argmax_rho |d2(loss)/d(rho)^2|
  co trung, hoac cach khong qua mot buoc grid, voi argmax_rho err khong?
```

## 5. Ban kinh r(s)

Neu Lesson 20R.7 dung ban kinh:

```text
r(s) = (cost_nhi - cost_tot_nhat) / (2 * ||grad_rho cost||)
```

mau so BAT BUOC la gradient day du cua cost:

```text
grad_rho cost = grad_rho delay + w_loss * grad_rho loss
```

Neu code chi dung `grad_rho delay`, chi dung `grad_rho loss`, hoac bo qua
`w_loss`, thi sai estimand.

## 6. Pham vi `cbr`

`cbr` khong nam trong scope Lesson 20R.7. Phase 20R da loai `cbr` khoi bang
quyet dinh vi vach da cua `cbr` la artifact audit; `band_v2` cung loc
`mode != "cbr"`. Moi hinh, hinh, va validation Lesson 20R.7 chi dung
`poisson` va `h2`.

## 7. Du doan ky truoc

Du doan truoc khi viet code:

```text
[x] Spearman(median r(s), err) < 0, p < 0.05.
[x] Argmax_rho |d2(loss)/d(rho)^2| trung, hoac cach <= 1 buoc grid,
    voi argmax_rho err trong it nhat 3 o/cau hinh khong-cbr.
[x] Trong hinh tach dong gop, |w_loss*d2(loss)/d(rho)^2| lon hon
    |d2(delay)/d(rho)^2| tai cac o substantively relevant.
```

Neu `Spearman(median r(s), err) > 0` hoac `p >= 0.05`, ket luan se la:

```text
Ban do co che khong ung ho giai thich bang ban kinh cost-margin.
Cac gate thuc nghiem cua Phase 20R van giu, nhung Lesson 20R.7 khong duoc
claim da giai thich duoc err bang curvature/r(s). Khong sua lai dinh nghia
r(s), khong doi kenh, va khong them bien the sau khi thay ket qua.
```

## 8. Them -- Nguong gay dang khep kin

Voi nhieu dong common-mode `delta` tren kenh loss cua moi link:

```text
S_P = sum_{i in P} prod_{j in P, j != i} (1 - p_j)
d(gap_ab)/d(delta) = w_loss * (S_a - S_b)
delta*_ab = |gap_ab(0)| / (w_loss * |S_a - S_b|)
```

Thanh phan delay triet tieu trong `d(gap_ab)/d(delta)` vi common-mode delay
dich moi duong cung mot hang so khi moi duong co cung 3 chang. Thanh phan loss
khong triet tieu vi phep ghep `1 - prod(1-p_i)` phi tuyen.

`S_a - S_b` la he so ro ri: bang 0 khi common-mode link van la common-mode
path, khac 0 khi common-mode link bien thanh differential giua cac duong qua
composition phi tuyen. Day la dang dinh luong cua ket qua "common-mode khong
bao toan qua ghep phi tuyen".

Trong `band_v2`, residual cascade `per_path` duoc bom thanh per-link bang cach
chia cho `N_LINKS_IN_PATH = 3`, nen:

```text
r*_path = 3 * min_ab(delta*_ab)
```

Du doan ky truoc, truoc khi chay script kiem B.3:

```text
[x] Cap mong manh nhat cua poisson@0.925: P1/P3.
[x] Cap mong manh nhat cua h2@0.925     : P2/P4.
[x] Ti so r*_quet / r*_giai_tich cua poisson du kien nam trong [0.8, 1.3].
```

Neu ti so lech `> 1.5x` hoac `< 0.7x`, ket luan se la:

```text
Cong thuc bac nhat van dung nhu mot can/chan doan co che, nhung khong duoc
bao cao nhu du doan diem cua r*. Nguyen nhan can ghi truoc khi viet hinh:
bac hai cua loss composition va clipping nang tren poisson/loss
(`clip_ratio = 43.20%` trong band cascade).
```

## 9. Ket qua B.3 -- cong thuc khong-clip sai, cong thuc co clip khop

Lenh kiem B.3 khong chay Mininet; chi doc `truth_table.parquet`.

Ket qua khong-clip bac nhat:

```text
poisson: best r*_path = 1.533354, cap P2/P4
h2     : best r*_path = 1.398990, cap P3/P4
```

Ket qua nay KHONG khop scan cascade (`poisson` scan `r* = 0.008868`, cap
`P1/P3`). Do do khong duoc dung cong thuc khong-clip nhu cong thuc khép kin
cua r*.

Dieu tra tiep cho thay scan K4 gay o dau am cua residual:

```text
sign = -1
r_path = 0.008868
per_link_shift = -0.002956
ranking: P1,P3,P4,P2 -> P3,P1,P4,P2
clip_events = 4 / 12
```

Hai link `poisson` bi clip trong co che nay la:

```text
uA loss = 0.000536
vC loss = 0.000536
```

Giai piecewise voi `p'_i = max(p_i - x, 0)` cho cap `P1/P3` cho:

```text
x_link* = 0.002936189839
r_path* = 3*x_link* = 0.008808569518
scan bracket = [0.008804852308, 0.008868196569]
```

Vay co che dung cua K4 cascade la:

```text
common-mode leak qua ghep loss phi tuyen + physical clipping o dau am.
```

Ket luan Lesson 20R.7 phai viet theo dang piecewise/clipped, khong viet nhu
cong thuc tuyen tinh khong-clip. `h2` khong co root K4 trong vung quet clipped
`|r_path| <= 0.15`, khop scan cascade `h2/loss safety > 10`.

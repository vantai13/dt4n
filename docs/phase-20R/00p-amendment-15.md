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

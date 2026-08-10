# AMENDMENT 18 -- Lesson 20R.7: sua tinh dat dung cua du doan P2

Ngay ky: 2026-08-10
Trang thai: KY TRUOC KHI CHAY `measurements/mechanism_predictions.py`.
Quan he: BO SUNG cho Amd 15 sec.7 du doan #2. Khong sua P1, P3, Amd 16, Amd 17.

## 1. Van de -- P2 khong dat dung nhu da viet

Amd 15 sec.7 #2 so sanh:

```text
argmax_rho |d2(loss)/d(rho)2|   va   argmax_rho err
```

Hai `rho` nay KHONG cung mot bien:

```text
err        duoc danh chi so theo rho_bar
ban do Amd 16 duoc danh chi so theo rho_link = rho_bar + LINK_OFFSET[link]
```

Hon nua, mot duong cong `(bw, q)` phuc vu nhieu link co offset khac nhau. Vi du
`(6.0, 13)` phuc vu `uB, ac, bc, bd, vD` voi offset
`-0.0475, +0.0525, +0.0475, +0.0575, -0.0375`. Mot `argmax` tren duong cong do
co NAM anh nguoc tren truc `rho_bar`. Khong the chon mot cai.

Do do P2 nhu da viet la ill-posed, khong phai underpowered.

## 2. Sua -- dua do cong len MUC DUONG, truc rho_bar

```text
loss_P(rho_bar) = 1 - prod_{i in P} ( 1 - p_i(rho_bar + offset_i) )
```

Day la ham vo huong cua `rho_bar`, cung truc voi `err`. Dai luong van la
`d2(loss)/d(rho)2` dung Amd 15 sec.3; chi hop thanh len muc duong de so sanh
duoc. Bao cao cho ca 4 duong `P1..P4`; neu 4 duong cho `argmax` khac nhau thi
ghi ro va khong gop.

## 3. h van la buoc luoi, ke ca khi mau khong roi vao nut

`rho_bar + offset` khong roi vao nut. Voi f tuyen tinh tung khuc, nut cach deu
h, tai `x = knot_k + t*h`:

```text
f(x+h) - 2f(x) + f(x-h) = (1-t)*num_k + t*num_{k+1}
d2f(x)                  = (1-t)*D_k + t*D_{k+1}
```

Tuc sai phan bac hai ngoai nut la NOI SUY TUYEN TINH cua sai phan tai nut. No
khong bao gio nhin thay cau truc duoi luoi. Amd 16 duoc ton trong voi dieu kien
`h = buoc luoi = 0.02`. Guard test bat buoc.

## 4. Mien hop le

```text
rho_bar in [ max_i(grid_i.min - offset_i) + h , min_i(grid_i.max - offset_i) - h ]
         = [ 0.5875 , 0.9575 ]
link siet chat nhat: `ad` (bw=4.0, grid.max=1.04, offset=+0.0625)
```

O do `rho_bar = 0.960` nam NGOAI mien. Do cong khong tinh duoc o do. Ghi la
gioi han, khong bu bang ngoai suy.

## 5. Luat nhan dang argmax cua err

`err` chi do tai `rho_bar in {0.700, 0.850, 0.925, 0.960}`. Neu argmax roi vao
DAU MUT cua danh sach nay thi dinh that co the nam ngoai cua so do, va argmax
KHONG DUOC NHAN DANG. Khi do P2 ghi la KHONG KIEM DUOC cho family do, khong
ghi FAIL.

```text
poisson argmax tai 0.850  -> ben trong -> kiem duoc
h2      argmax tai 0.700  -> mep trai  -> khong kiem duoc
```

Luat nay khop voi H7 (`h2 peak below left edge PARTIAL`).

## 6. Ngu canh "3 o/cau hinh"

Amd 15 sec.7 doi it nhat 3 o non-cbr thang hang. Sau khi sua truc, mot "o" la
mot cap `(family, path)`. Chi dem cac family co argmax err duoc nhan dang.

## 7. Khong noi long ket luan

Neu so o thang hang < 3, P2 KHONG DUOC UNG HO. Khong doi `max_grid_steps` tu 1
len 2. Khong doi sang argmax cua `d1` thay `d2`. Khong doi sang mot family khac
sau khi xem so.

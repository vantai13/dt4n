# AMENDMENT 23-43a -- mien kha thi cua traffic tai rho_bar=0.960

Ngay: 2026-08-22  
Trang thai: **SAU 3/30 run A4; SAU khi run 4 dung truoc luc tao topology;
TRUOC bat ky outcome nao tai rho_bar=0.960.**

## Su co tien dinh

Run 4 `prod_rho0.960_rep3` dung trong `TrafficConfig.__post_init__`, truoc khi
tao Mininet, voi `ValueError: rho_target must be in (0, 1)`. Nguyen nhan la
`cost_v2.rho_vector(0.960)` co bon muc core 1.0075--1.0225. Mien mo hinh cho
phep den 1.05, nhung traffic M/G/inf dung yen chi dinh nghia voi rho < 1.

Khong co file AoI/cycle/push nao cua run 4 duoc sinh. Ba run da hoan thanh
khong bi anh huong vi cac vector cua rho_bar 0.700, 0.850 deu kha thi; run
CLEAN 0.850 cung xac nhan NC-U.

## Sua vat ly da khoa

Truoc khi resume, vector rho cho bo tao traffic duoc chieu vao mien
`0 < rho[l] <= 0.995`, giu chinh xac trung binh bang rho_bar. Phep chieu dung
mot common shift va clipping (nghiem Euclid cua rang buoc box + tong). Tai
rho_bar <= 0.925 no la identity; tai 0.960, bon core bi cap 0.995 va phan tai
thieu duoc phan deu sang cac link chua cham cap.

Quyet dinh nay:

* khong thay E1--E4, M-70--M-77, schema, mode, duration, seed hay thu tu;
* khong dua tren outcome AoI;
* giu y nghia cua `rho_bar` la trung binh cua tam target vat ly;
* them hai test: mien `(0,1)` + bao toan mean; identity tai 0.925.

Run 4 mang trang thai `failed` trong manifest va se duoc chay lai tai cung vi
tri logic bang `--resume`; ba run `complete` khong chay lai.

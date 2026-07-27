# AMENDMENT 1 - Phase 20 Pre-Registration

Ngay: 2026-07-26
Trang thai: TRUOC khi chay phep do chinh
Ly do: thiet ke san khau Q7=B va phat hien mau thuan Q9 voi G1.

Khong sua file `00-preregistration.md` da ky. Amendment nay ghi ro thay doi,
pilot da xem, va cach dong bang san khau truoc confirmatory run.

## A1.1 Q7 Chot = B

Topology B la 2x2 butterfly / mini leaf-spine, `K = 4`, 6 nut, 8 link.
File cau hinh: `twin/topology_v7.py`.

Ma tran chia se:

```text
uA -> {P1, P2}
uB -> {P3, P4}
vC -> {P1, P3}
vD -> {P2, P4}
ac -> {P1}
ad -> {P2}
bc -> {P3}
bd -> {P4}
```

Khong link nao nam tren ca 4 duong. Dinh ly san khau: link nam tren moi duong
khong doi `argmin`, ke ca khi delay ghep cong va loss ghep nhan. Link dung
chung chi co tac dung quyet dinh khi no nam tren mot tap con thuc su cua cac
duong.

Rang buoc hieu chuan: moi `bw_mbps` chi nam trong `{4, 6, 8}` Mbps, la dai da
duoc do trong `results/calib/density_bw{4,6,8}_*.csv`.

## A1.2 Sua Rang Buoc (i)

Cu:

```text
dai rho cua moi duong phai phu vung quanh J
```

Moi:

```text
moi duong phai chua it nhat mot link vat qua J = {0.9250, 0.9325}
```

Ly do: ep moi link vao vung cliff la phi thuc te va lam mat do tuong phan.
Mang that co link bien nhan roi; link loi/core moi thuong sat bao hoa.

## A1.3 Khai Bao Pilot

Da thu 2 thiet ke tren mo phong AR(1), 60k buoc, truoc khi dong bang san khau:

Thu 1 - moi link quanh `rho ~= 0.92`, `sigma = 0.035`:

```text
err(z=8) = 0.5546
P(r_jump < 0.01) = 0.924
```

Chan doan: san khau qua nhay, 92% thoi gian sat nguong; gan nhanh fail (d)
"twin vo dung". Day khong phai mang that ma la bieu dien moi link cung o vung
toi han.

Thu 2 - link bien nhan roi, link loi vat qua J, `sigma = 0.010`:

```text
seed0: err(z=4) = 0.3228, Delta_sla_lower = 0.1752
seed1: err(z=4) = 0.3239, Delta_sla_lower = 0.1729
seed2: err(z=4) = 0.3288, Delta_sla_lower = 0.1757
tie rate = 0.0000%
K_eff = 2.54/4
P(r_jump < 0.01 | decision error) = 0.998
```

Ly do sua la vat ly, doc lap voi `err`: mang that co link bien nhan roi va
link loi nong. Thu 1 bi loai vi no mat do tuong phan va phi thuc te.

San khau dong bang tu amendment nay. Confirmatory run phai dung seed moi:
`100, 101, 102`. Pilot seed `0, 1, 2` khong duoc dung lai de ket luan gate.

## A1.4 Mau Thuan Q9 Vs G1

Do duoc voi thiet ke Thu 2, `tau = 8` buoc:

```text
A/tau = 0.125 -> err = 0.192
A/tau = 0.250 -> err = 0.255
A/tau = 0.500 -> err = 0.327
A/tau = 1.000 -> err = 0.399
A/tau = 2.000 -> err = 0.457
```

Q9 cu `[0.5, 2.0]` va G1 `err <= 0.40` khong tuong thich o nua tren. Tai
`A/tau = 2.0`, G1 da fail.

Sua Q9:

```text
0.25 <= A/tau <= 1.0
```

Bien minh: quy tac `A ~ tau` suy ra tu sai so gia tri. Sai so quyet dinh bao
hoa som hon vi no chi can `rho` vuot mot nguong, khong can tin hieu mat tuong
quan hoan toan. Day la mot phat hien can viet vao paper: bao dam o muc gia tri
khong suy ra bao dam o muc quyet dinh.

## A1.5 Cap Nhat Q5

`z* = 4`, thay cho `z* = 8` trong ban goc.

Ly do: voi Q9 moi, `z* = 4` ung voi `A/tau = 0.5`, nam giua dai moi va co
CI pilot nam tron trong Gate G1.

Bin quet van la:

```text
z in {0, 1, 2, 4, 8, 16, 32}
```

Cac bin `z != 4` la exploratory.

## A1.6 Ban Do Can Gat

Pilot cho thay hai can gat tach cap:

```text
z/tau -> dieu khien do kho, tuc err
sigma -> dieu khien so hanh dong song, tuc K_eff
```

Quan sat:

```text
sigma tang 3x -> err(z=4) tang 0.327 -> 0.399, +22%
sigma tang 3x -> K_eff tang 2.58 -> 3.10, +20%
z/tau tang 4x -> err tang 0.19 -> 0.33, +72%
```

Neu fail nhanh (b), err qua nho: van `z/tau` len.
Neu `K_eff < 2.0` hoac mot path thang > 80%: van `sigma` len.
Trong he that, `sigma` va `tau` la he qua cua Q8 va phai do o 20.1b.

## A1.7 Kiem Chung Tinh Ghep

Truoc Lesson 20.2, dung:

```text
measurements/calib_topo_validate.py
measurements/analyze_topo_validate.py
```

cho ca 4 path. Tieu chi chot truoc:

```text
sai so tuong doi < 15% o ca hai phia cliff
giua delay_e2e do that va tong total_delay_ms tung link
```

Neu khong dat: dung cost e2e do that lam su that; twin van dung mo hinh ghep.
Do chenh lech la mot nguon sai so twin co that, khong phai that bai cua Phase
20.

## A1.8 Files Dong Bang

```text
twin/topology_v7.py
docs/phase-20/00b-amendment-1.md
test/routing/test_topology_v7.py
```

Tag dong bang: `phase-20-stage-frozen`.

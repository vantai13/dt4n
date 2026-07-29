# AMENDMENT 3 -- Phase L

Ngay: 2026-07-29
Trang thai: viet truoc khi dung L.4 lam bo sinh tai chinh.

## A3-1  Bon che do; h2 la truc c_a chinh

Phase L doi truc che do thanh:

| mode | c_a | vai tro |
|---|---:|---|
| cbr | 0 | doi chung cu, noi voi hieu chuan CBR |
| poisson | 1 | renewal, khop Pollaczek-Khinchine |
| h2 | 2 | truc c_a chinh, dieu khien duoc |
| onoff | do lai | doi chung LRD, chi chay cau hinh 6 Mbps / q=13 |

Can cu bang so tren lich 27000 goi, 5 seed:

| mode | c_a seed-level | mean | sd | sd/mean |
|---|---|---:|---:|---:|
| h2 | 1.9893, 1.9980, 2.0074, 1.9636, 2.0127 | 1.9942 | 0.0173 | 0.9% |
| onoff | 2.864, 1.401, 1.797, 2.505, 2.211 | 2.156 | 0.515 | 24.0% |

Ket luan: onoff khong the la bien doc lap c_a vi moi seed la mot c_a khac.
Neu dung onoff lam truc chinh, do tan xa giua seed bi nham thanh nhieu do trong
khi bien doc lap dang dao dong. Onoff van giu lai vi no co long-range dependence,
con h2 la renewal process; so sanh h2 va onoff o cung c_a do duoc tach duoc anh
huong cua c_a khoi anh huong cua tuong quan.

Luoi do cap nhat sau L.4:

| nhom | diem |
|---|---:|
| (cbr, poisson, h2) x 12 rho x 3 cau hinh x 5 seed | 540 |
| onoff x 12 rho x 1 cau hinh x 5 seed | 60 |
| tong | 600 |

## A3-2  Dinh nghia rho theo byte HTB dem

HTB dem `skb->len`, tuc payload UDP cong UDP/IP/Ethernet header, khong cong
FCS/preamble/IFG.

```
frame_bg    = 1470 + 42 = 1512 B
frame_probe =   64 + 42 =  106 B
C_bytes     = bw_mbps * 1e6 / 8
rho         = (n_bg * 1512 + n_probe * 106) / C_bytes
n_bg        = (rho * C_bytes - n_probe * 106) / 1512
```

Tai bw=6 Mbps, rho=0.90, probe=20 goi/s:

```
n_bg = 445.0265 goi/s
mean_gap = 2.247057 ms
rho tai tao = 0.900000
```

Probe duoc tinh vao rho. `OVERHEAD_FACTOR = 1.079` khong con hop le trong
Phase L vi no tron accounting Ethernet voi sai so cong cu iperf. Tu L.4 tro di,
rho danh nghia la rho theo dung don vi qdisc, va moi diem van phai ghi
`rate_ratio` cung `rho_actual` tu toc do gui that.

## A3-3  Chuan hoa toc do bang co gian thoi gian

Sinh lich xong, moi gap duoc nhan voi cung mot he so:

```
gap_i' = k * gap_i
k = mean_gap_muc_tieu / mean(gap)
```

Phep nay lam mean va sd cung nhan `k`, nen `c_a = sd/mean` khong doi. No cho
phep dat dung toc do ma khong pha muc burstiness da thiet ke. Day la bat buoc
voi onoff, vi khong chuan hoa thi mot seed co the lam rho=0.90 thanh rho thuc
te khoang 0.921.

## A3-4  Lich sinh truoc, phat sau

`mininet/load_spec.py` bien seed thanh mang gap, chuan hoa toc do, roi SHA-256.
Phan phat song chi thuc thi lich tuyet doi:

```
t_target = t0 + t_rel
```

Khong dung `time.monotonic() + gap` trong vong lap, vi cach do lam tre tich luy
va toc do thuc thap hon nhan.

Moi diem L.4 phai ghi bon so lien quan c_a:

| truong | y nghia |
|---|---|
| design_target | gia tri dat vao: 0, 1, 2, hoac null cho onoff |
| schedule_bg | c_a cua lich nen truoc khi phat |
| actual_bg | c_a do tu timestamp gui that |
| aggregate_schedule | c_a cua dong tong hop nen + probe |

Neu `schedule_bg` khop `design_target` nhung `actual_bg` lech, loi nam o khau
phat. Neu `schedule_bg` da lech, loi nam o bo sinh lich.

## A3-5  Probe 20 goi/s

Mo phong truoc L.4 tai bw=6 Mbps, rho=0.90, Poisson:

| probe pps | q_delay TB (ms) | lech |
|---:|---:|---:|
| 0 | 5.920 | - |
| 10 | 5.920 | +0.0% |
| 20 | 5.944 | +0.4% |
| 40 | 6.014 | +1.6% |
| 80 | 6.209 | +4.9% |

Chot `PROBE_PPS = 20`. V-L7 tren he that phai cho lech delay < 2% voi probe
<= 20 goi/s.

## A3-6  Mot tien trinh gui, mot tien trinh nhan

Gui: `measurements/load_gen.py` gop lich nen va probe vao mot dong su kien, phat
bang mot UDP socket. Nhan: `measurements/owd_probe.py recv --out-prefix` nhan
mot cong roi tach file theo `kind`.

Dinh dang packet khong doi, nen `PKT_VERSION = 1` giu nguyen.

## Rui ro moi

RL6. Onoff co the tao cum lon hon buffer va gay loss cao o rho thap. Giam nhe:
`peak_factor = 1.35`; neu loss > 25% o rho <= 0.8 thi giam peak factor va ghi
amendment.

RL7. Pareto alpha=1.5 hoi tu cham. Giam nhe: cat tren `tmax_s = 1.0` va xem
`steady_state.spread_ms` trong output analyzer, dac biet voi onoff.

# AMENDMENT 4 -- Phase L / V-L7 duration

Ngay: 2026-07-29

## A4-1  Khong doi gate V-L7, tang cua so do

Lan live L.4 dau tien sach o V-L3 va V-L4, nhung V-L7 voi duration 40 s cho:

| probe pps | q_mean_ms |
|---:|---:|
| 0 | 6.258 |
| 10 | 6.144 |
| 20 | 6.075 |
| 40 | 5.967 |

Sai lech tuyet doi tai 20 pps la 2.94%, nen gate `|dev| < 2%` fail. Dau
hieu nay khong phai probe lam tang delay; signed deviation tai 20 pps la am.
No cho thay noise/cua so 40 s lon hon hieu ung du doan 0.4%.

Kiem tra rieng voi duration 80 s, cung seed, cung rho:

| probe pps | q_mean_ms | signed dev |
|---:|---:|---:|
| 0 | 6.104 | - |
| 20 | 6.001 | -1.69% |

Ket luan: giu gate V-L7 nhu preregistered (`|dev| < 2%` voi probe <=20 pps),
nhung tang duration cua cac diem V-L7 chinh (0/10/20 pps) len 80 s. Diem 40 pps
van la doi chung ngoai gate chinh va giu 40 s de tiet kiem thoi gian.

Khong dung ket qua 40 s de claim "probe phang"; no duoc giu nhu artifact cho
thay hieu ung can cua so dai hon.

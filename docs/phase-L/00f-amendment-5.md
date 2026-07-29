# AMENDMENT 5 -- Phase L / after L.4 audit

Ngay: 2026-07-29
Artifacts chinh:

```
results/phase-L/l4_loadgen_0729_0955.json  # V-L7 40 s fail theo huong am
results/phase-L/l4_loadgen_0729_1007.json  # L.4 PASS sau khi tang V-L7 len 80 s
```

## A5-1  Bang du doan da ky duoc xac nhan

Dung `cbr` tai rho=0.90 lam san co tai: `floor = 0.1347 ms`.

| dai luong, bw=6/q=13/rho=0.90 | du doan | do duoc tru san | lech |
|---|---:|---:|---:|
| cbr mean | 0.00 | 0.000 | 0.0% |
| poisson mean | 5.77 | 5.942 | +3.0% |
| h2 mean | 10.67 | 10.664 | -0.05% |
| poisson p95 | 19.55 | 19.993 | +2.3% |
| h2 p95 | 24.70 | 24.583 | -0.5% |
| poisson loss | 0.0060 | 0.0059 | -1.4% |
| h2 loss | 0.0640 | 0.0693 | +8.2% |

Ket luan: D1', D3', D5', va D6 phan bursty deu dung. Bang nay xac nhan dong
thoi probe OWD, qdisc, bo sinh tai `c_a`, dinh nghia rho, va mo hinh token
bucket + bfifo.

## A5-2  CI phai tinh bang batch means / giua seed

Mau OWD tu tuong quan, nen so goi khong bang luong thong tin. Tu raw 10:07:

| mode | spread_ms | SE naive | SE batch | inflation |
|---|---:|---:|---:|---:|
| cbr | 0.030 | 0.0006 | 0.0045 | 6.95x |
| poisson | 2.360 | 0.0575 | 0.3564 | 6.19x |
| h2 | 2.661 | 0.0758 | 0.4222 | 5.57x |
| onoff | 4.223 | 0.0678 | 0.6725 | 9.92x |

Chot:

- `owd_analyze.py` ghi `se_batch_means_ms`, `se_naive_ms`, va
  `inflation_factor`.
- Moi khoang tin cay Phase L dung bien thien giua seed voi Student-t, hoac
  batch means khi chi noi ve mot run. Khong bao gio dung SE naive tu so goi.
- `steady_state_spread` chi can dieu tra khi `spread > 4 * se_batch_means`.

## A5-3  onoff: LRD lo ra trong chinh cong cu

Truoc fix: `ca_schedule` khoang 3.15, `ca_actual` khoang 1.52, `rate_ratio`
1.0178. Nguyen nhan: sinh du lich 1.15x, chuan hoa tren toan bo lich, nhung chi
dung doan dau. Renewal modes it bi vi moi doan co cung ky vong; onoff co LRD nen
doan dau co the khac toan bo.

Fix: sinh dung so event cho cua so do va chuan hoa tren dung cac event se dung.
Gioi han can ghi: cach nay co y kiem soat rho theo cau truc, tuc loai bo mot
phan drift toc do cham cua LRD; van giu burstiness thang ngan va tuong quan
trong cua so.

## A5-4  D7 sua gate rate_ratio

Cu: `[0.97, 1.00]`, voi ly do "Python chi gui thieu".

Sai: run truoc fix co `rate_ratio > 1`. Sau fix, rate chinh xac theo cau truc.
Gate moi cho moi diem do:

```
abs(rate_ratio - 1) < 0.001
abs(rho_actual - rho_nominal) < 0.002
socket_drops_delta = 0
n_foreign_packets = 0
n_late_ratio < 0.001
max_late_ms < 50
```

## A5-5  V-L7: probe lam delay giam nhe

Run 40 s cho signed deviation am:

| probe pps | q_mean_ms | lech so voi pps=0 |
|---:|---:|---:|
| 0 | 6.258 | - |
| 10 | 6.144 | -1.82% |
| 20 | 6.075 | -2.94% |
| 40 | 5.967 | -4.65% |

Run 80 s chinh thuc:

| probe pps | q_mean_ms | lech so voi pps=0 |
|---:|---:|---:|
| 0 | 6.083 | - |
| 10 | 6.028 | -0.90% |
| 20 | 5.994 | -1.46% |

Co che: probe duoc tru khoi tai nen de giu rho, nen thanh phan byte doi tu it
goi lon sang nhieu goi nho. Hat cong viec min hon lam hang doi muot hon. Chot:
giu probe 64 B / 20 pps; ghi sai so he thong huong am khoang 1.5% tai rho=0.9.

## A5-6  Cau hoi mo cho L.5: PASTA poisson

L.4 do:

| mode | packet mean | probe mean | delta packet-probe |
|---|---:|---:|---:|
| cbr | 0.135 | 0.110 | +0.024 |
| poisson | 6.077 | 6.243 | -0.167 |
| h2 | 10.799 | 9.553 | +1.246 |
| onoff | 5.825 | 5.635 | +0.190 |

Du doan tien dang ky cho L.5:

```
delta_pasta(poisson) trung binh 5 seed nam trong [-0.3, +0.3] ms
va CI95 phu 0.
```

Neu khong phu 0, dieu tra size-biased admission: bfifo gioi han byte cho phep
probe 106 B vao nhung loai goi nen 1512 B khi backlog gan tran.

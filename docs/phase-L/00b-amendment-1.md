# AMENDMENT 1 -- Phase L

Ngay: 2026-07-29   Tag truoc do: phase-L-start   Commit quan sat: d375156

## DA THAY SO NAO TRUOC KHI SUA

results/phase-L/l1_infra_0729_0716.json:

```text
ping RTT avg = 3.413 ms
burst_chosen = 1600 B
V-L4 ratio = 0.38461538461538464, expected = 0.38461538461538464
raw_after_burst: overlimits = 14965, tokens = -30992
```

results/phase-L/l1_infra_0729_0728.json (lan chay lai cua user, chua stage):

```text
ping RTT avg = 3.448 ms
burst_chosen = 1600 B
V-L4 ratio = 0.38461538461538464, expected = 0.38461538461538464
```

Ping min RTT trong output L.1 on dinh quanh 3.05 ms. Du doan L.0 cu cho
RTT toi thieu la khoang 3.13 ms (= 3.0 ms netem + serialization cua goi
ping/probe). Lech khoang 0.08 ms, co he thong, theo huong "khong co
serialization delay tren tung goi".

Doc lai co che HTB: dieu kien nha goi la `tokens >= 0`, KHONG phai
`tokens >= len`. HTB nha goi tuc thi khi con token; toc do duoc enforced
bang viec token am sau khi gui, lam goi sau phai cho. Do do trong Mininet
khong co serialization delay nhu delay tren tung goi; no chi la rang buoc
toc do theo thoi gian.

## SUA GI

A1-1. Mo hinh tham chieu doi tu "server noi tiep GI/D/1/K" sang
"token bucket (burst B) + bfifo (limit K byte)".

A1-2. V-L2 sua lai:

```text
CU : OWD(tai 0) ~ 106*8/bw, ti le nghich voi bw
MOI: OWD(tai 0) = SAN PHAN MEM (do bang V-L0), KHONG phu thuoc bw
```

Ly do: tokens day o tai 0 nen goi nha tuc thi.

A1-3. D1 sua lai:

```text
CU : CBR p50 = S_probe + E[S](0.5-(1-rho))/rho
MOI: CBR q_delay = 0.00 ms voi moi rho <= 0.98, chi con san phan mem
Nguong: q_delay(cbr) <= san + 0.2 ms
```

A1-4. THEM V-L2b -- GOLDEN TEST BAC THANG TOKEN BUCKET.

Gui 8 goi 1512 B lien tiep vao link rong. Delay tung goi phai la:

```text
d1 = d2 = 0
d_k = ((k-1)*1512 - 1600)/C   voi k >= 3
```

Bang du doan:

```text
bw=6: 0, 0, 1.899, 3.915, 5.931, 7.947, 9.963, 11.979 ms
bw=4: 0, 0, 2.848, 5.872, 8.896, 11.920, 14.944, 17.968 ms
bw=8: 0, 0, 1.424, 2.936, 4.448, 5.960, 7.472, 8.984 ms
```

Nguong: sai so tuyet doi < 0.3 ms tren median cua moi goi tu k=3, lay qua
5 burst doc lap. Day la golden test kiem dong thoi probe, rate C, va burst,
khong co tham so tu do.

A1-5. Dai luong chinh doi tu `owd_p50` sang `owd_mean`.

Ly do khong phai so thich ma la rang buoc toan hoc:

```text
topology_v7.path_delay_loss() cong don delay qua cac link.
E[X+Y] = E[X]+E[Y], nhung p95(X+Y) != p95(X)+p95(Y).
```

Do do dai luong duoc mo hinh hoa bat buoc phai cong duoc: MEAN. Van ghi
day du p50/p90/p95/p99 cho SLA va conformal, nhung gioi han cua paper la
mo hinh cong duoc chi du doan trung binh.

A1-6. Bang du doan L5 thay bang mo phong token bucket + bfifo, do tren goi
nen, bw=6 Mbps, K=13:

```text
 rho   | CBR mean/p95 | POISSON mean/p50/p95/loss | BURSTY mean/p50/p95/loss
 0.50  | 0.00 / 0.00  |  0.28 / 0.00 /  1.96/0.000 |  1.42 / 0.00 /  7.10/0.000
 0.60  | 0.00 / 0.00  |  0.57 / 0.00 /  3.59/0.000 |  2.96 / 0.80 / 12.59/0.001
 0.70  | 0.00 / 0.00  |  1.16 / 0.00 /  6.14/0.000 |  5.31 / 2.90 / 19.25/0.008
 0.80  | 0.00 / 0.00  |  2.55 / 0.48 / 11.15/0.000 |  8.05 / 6.00 / 23.24/0.029
 0.85  | 0.00 / 0.00  |  3.85 / 1.63 / 15.18/0.002 |  9.40 / 7.75 / 24.08/0.045
 0.90  | 0.00 / 0.00  |  5.77 / 3.53 / 19.55/0.006 | 10.67 / 9.57 / 24.70/0.064
 0.925 | 0.00 / 0.00  |  6.99 / 4.94 / 21.32/0.010 | 11.24 /10.46 / 24.92/0.075
 0.95  | 0.00 / 0.00  |  8.37 / 6.73 / 22.54/0.016 | 11.82 /11.37 / 25.10/0.087
 0.98  | 0.00 / 0.00  | 10.32 / 9.51 / 23.67/0.026 | 12.47 /12.41 / 25.29/0.100
 1.00  |23.17 /24.24  | 11.70 /11.60 / 24.10/0.035 | 12.89 /13.09 / 25.40/0.110
 1.05  |24.50 /26.03  | 14.74 /16.05 / 24.95/0.064 | 13.87 /14.65 / 25.56/0.135
```

Du doan dinh tinh moi:

```text
D1' CBR = 0.00 ms voi moi rho <= 0.98, nhay len ~23 ms tai rho = 1.00.
D2' POISSON: mean bat dau tach khoi 0 tu rho ~0.55, don dieu tang.
D3' Thu tu cbr < poisson < bursty giu nguyen o MEAN, khong phai p50.
D4' Delay mean bao hoa o ~45-50% tran, khong cham tran khi rho < 1.
D5' Loss bursty >= 1% tu rho ~0.72; poisson >= 1% tu rho ~0.92.
```

A1-7. Phep kiem do nhay `burst` hoan sang L.5:

```text
Quet burst {1600, 15000} tai bw=6, q=13, che do BURSTY, rho=0.85.
Du doan: q_delay(burst=15000) < q_delay(burst=1600) ro ret.
```

Ly do hoan: L.1 bom qua tai rat manh nen xo token luon can; burst khong the
hien tac dung hap thu burstiness. Can tai bursty duoi bao hoa.

A1-8. `measurements/l1_verify.py` sua them:

```text
kiem h2-eth0 va s2-eth1 trong hidden queue
lay mau backlog trong luc blast va bao cao p95/peak
kiem direct_packets_stat == 0
```

A1-9. Huy bo giam nhe RL5 reservoir sampling cho Phase L: file tho full-size
du kien duoi 400 MB truoc nen giu toan bo raw records. Do lai ton gio; phan
tich lai ton giay.

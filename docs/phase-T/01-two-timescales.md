# PHASE T -- T.1 TWO TIMESCALES

Ngay: 2026-07-30
Trang thai: chua chay do Phase T. Tai lieu nay dien so cho luoi Phase T va
thay the mot phan T4/T5 cua `00-preregistration.md` qua Amendment 2.

T.0 chot do cai gi: sai so cua PSA khi dung model tinh
`f(mode,bw,q,rho)` tren tai dong `rho(t)`. T.1 chot do o dau: cac gia tri
`T_relax`, `tau_rho`, `sigma_rho`, va phuong an du phong neu PSA fail.

--------------------------------------------------------------------
## 0. Cau Hoi

T.1 tra loi ba cau:

```text
1. T_relax bang bao nhieu?
2. Tai sao cbr tai rho=1.0 ky di?
3. Neu quasi-static fail thi thay bang gi?
```

Ket luan chinh: khong dung `inflation` cua Phase L lam truc hoanh chinh cua
Hinh T1. `T_relax` phai do truc tiep bang step response.

--------------------------------------------------------------------
## 1. T_relax Tu Lindley/RBM

Lindley recursion cho hang doi mot server:

```text
W[i+1] = max(0, W[i] + S[i] - A[i])
```

Trong code Reich hien co, `measurements/l7_fit.py`:

```python
service_ms = FRAME_BG * 8.0 / (bw_mbps * 1e6) * 1000.0
service_s = service_ms / 1000.0
q = 0.0
for t in timestamps:
    gap = 0.0 if prev is None else max(0.0, t - prev)
    q = max(0.0, q - gap / service_s) + 1.0
    values.append(q * service_ms)
```

`q` do bang so goi; `gap/service_s` la thoi gian giua hai goi quy ve don vi
phuc vu; `+1.0` la service cua mot goi fixed-size. Reich workload va Lindley
recursion la cung mot doi tuong, chi khac cach viet.

Trong heavy traffic, Lindley tien toi reflected Brownian motion (RBM):

```text
drift theta       = 1 - rho
variance sigma_V2 = rho * E[S] * (c_a^2 + c_s^2)
```

RBM co phan phoi dung ham mu, mean:

```text
E[V] = sigma_V2 / (2*theta)
     = rho/(1-rho) * (c_a^2+c_s^2)/2 * E[S]
```

Day la Kingman. Kingman cho mean dung, nhung khong cho toc do hoi phuc.

Hai co che quyet dinh `T_relax`:

```text
drift-limited : T_drift = 2*sigma_V2 / theta^2
buffer-limited: T_diff  = 2*B^2 / (pi^2*sigma_V2)

T_relax = 1 / (theta^2/(2*sigma_V2) + pi^2*sigma_V2/(2*B^2))
```

Voi cau hinh chinh `bw=6, q=13`:

```text
E[S] = 1512*8/(6e6) = 2.016 ms
B    = 13 * 2.016  = 26.208 ms
```

--------------------------------------------------------------------
## 2. Kiem Chung Bang Phase L

Cong thuc RBM da duoc doi chieu voi `T_relax` suy tu `inflation` trong
`campaign_state.json`. Bang duoi dung `c_a` do duoc va cau hinh `bw=6,q=13`.

```text
mode      rho   ca_do    T_do_median  T_do_min  T_do_max  T_RBM   do/RBM
poisson   0.70  1.007        62.1       11.9      90.4     24.0    2.59
poisson   0.85  1.007       119.9       55.1     194.0     52.7    2.27
poisson   0.90  1.004       134.0       63.6     212.8     63.0    2.13
poisson   0.95  1.007        83.9       47.6     204.8     68.5    1.22
poisson   0.98  1.005       108.7       38.4     300.1     69.3    1.57
poisson   1.05  1.006        66.4       33.7     121.5     62.6    1.06

h2        0.70  2.035        61.7       40.8     109.7     20.1    3.07
h2        0.90  1.987        21.7       18.1     115.0     19.2    1.13
h2        0.98  2.010        70.7       15.6     123.0     17.4    4.06

onoff     0.80  2.075       349.3      265.8    1267.5     19.0   18.43
onoff     0.90  2.203       297.0      164.3    1409.3     15.7   18.95
onoff     0.95  2.263       353.6       86.2    1221.0     14.2   24.97

cbr       0.90  0.004       113.3       35.9     198.0      0.0    n/a
cbr       1.00  0.008      7317.5     4811.8   10676.5  1180213.9 0.01
```

Ket luan:

```text
poisson: RBM khop hinh dang va do lon trong 1-3x.
h2     : RBM thap hon khoang 2-4x, vi H2 co duoi nang ma diffusion bo qua.
onoff  : RBM sai 15-25x, vi c_a khong biet tuong quan theo thoi gian.
cbr    : inflation duoi nguong do chu yeu jitter phan mem, khong phai hang doi.
```

Vi vay `inflation` khong du tin cay de lam mau so cua
`Lambda = tau_rho/T_relax`. Truc hoanh chinh phai dua tren step response.

--------------------------------------------------------------------
## 3. Tai Sao cbr Tai rho=1.0 Ky Di

Voi `cbr`, `c_a` gan 0 nen `sigma_V2` rat nho. Xet ba diem quanh rho 1.0:

```text
rho=0.98: theta=0.02 -> co drift -> hoi phuc nhanh
rho=1.00: theta=0    -> khong drift, sigma_V2 gan 0 -> critical slowing down
rho=1.02: theta=0.02 -> day len buffer nhanh -> hoi phuc nhanh
```

Tai `rho=1.00`, ca hai co che hoi phuc bien mat:

```text
khong drift     : khong co luc keo ve trang thai dung
gan nhu khong diffusion: hang doi khong tu lang thang nhanh qua buffer
```

He qua:

```text
link_model_v2.is_reliable("cbr", ..., 0.95<rho<1.05) = False
T_relax(cbr,rho=1.0) do duoc 4.8-10.7 s, lon nhat toan campaign
de Lambda >= 10 can tau_rho >= 50-100 s, bat kha trong cua so 90 s
```

Day la critical slowing down, khong phai bug fit.

--------------------------------------------------------------------
## 4. Step Response

Nguyen tac: do dung dinh nghia `T_relax`.

```text
giu rho=A trong T_hold
doi dot ngot sang rho=B tai t=0
do q(t)
lap lai N chu ky va ensemble-average cac doan transition
```

Tham so chot:

```text
T_hold = 3.0 s cho h2/poisson
N      = 60 chu ky
bin    = 20 ms
seeds  = 3 seed
```

Bang buoc do:

```text
#  mode      buoc rho        muc dich
1  h2        0.70 -> 0.85    vung Jensen manh
2  h2        0.85 -> 0.925   vung chuyen tiep
3  h2        0.925 -> 0.98   vung tai cao
4  poisson   0.70 -> 0.85
5  poisson   0.85 -> 0.925
6  poisson   0.925 -> 0.98
7  cbr       0.95 -> 0.98    canh vach, T_hold=30 s, 1 seed
8  cbr       0.98 -> 1.00    qua vach, T_hold=60 s, N=10, 1 seed
```

Budget:

```text
1-6: 6 * 6 phut * 3 seed = 108 phut
7  : 60 phut
8  : 20 phut
tong ~ 3.1 gio
```

Doc `T_relax` bang hai cach:

```text
primary: area / mean relaxation time

T_relax = integral_0^T_hold [qbar(t)-q_inf] dt / [qbar(0)-q_inf]

secondary: fit qbar(t) = q_inf + (q_0-q_inf)*exp(-t/T_exp)
```

Bootstrap confidence interval tren chu ky doc lap, khong tren cac bin.

Doi chung bat buoc:

```text
S-1: buoc A->A phai phang, lay lam san nhieu step response
S-2: buoc A->B va B->A cho T_relax khop trong 25%
S-3: poisson khop thu tu do lon voi cong thuc RBM trong 3x
```

Buoc `cbr 0.98->1.00` khong can doc ra mot `T_relax` sach; muc tieu la chung
minh no khong hoi tu trong 60 s, xac nhan D-T9.

--------------------------------------------------------------------
## 5. Reich(t), IDC, Va Vi Sao c_a Khong Du

Ket qua Phase L A7-4:

```text
mode      c_a mean   q mean ms   Reich mean ms
cbr         0.004      0.133         2.02
poisson     1.003      5.725        10.74
h2          2.032     11.041        35.40
onoff       2.312      6.631        25.91

corr(Reich, delay) = 0.938
```

`c_a` that bai vi no la thong ke bien cua tung gap. Hang doi phan ung voi
luong nap tich luy tren thang `T_relax`. `onoff` co `c_a` cao hon `h2` nhung
cac gap tuong quan tren thang tram ms; tren thang hang doi chuc ms, no trong
gan CBR luc ON va rong luc OFF. `h2` burst o thang goi nen delay cao hon.

IDC la dai luong nen tinh neu can mot hinh phu:

```text
IDC(t) = Var[N(t)] / E[N(t)]
```

IDC tai `t ~= T_relax` moi la cai hang doi cam nhan, khong phai `c_a` thuan.
Tinh IDC chi can cac file `_bgtx.bin` da co.

Phase T nen ghi `Reich(t)` trong tung cua so 1 s:

```text
Reich_mean, Reich_p95, corr(Reich(t), q(t))
```

Canh bao: Reich hien co trong `l7_fit.py` khong co tran buffer. Phase T can
ban co tran:

```python
def reich_bounded(timestamps, bw_mbps, q_pkts, warmup_s=0.0):
    service_ms = 1512 * 8.0 / (bw_mbps * 1e6) * 1000.0
    service_s = service_ms / 1000.0
    q = 0.0
    n_drop = 0
    prev = None
    out = []
    for t in timestamps:
        gap = 0.0 if prev is None else max(0.0, t - prev)
        q = max(0.0, q - gap / service_s)
        if q + 1.0 > q_pkts:
            n_drop += 1
        else:
            q += 1.0
        if t >= warmup_s:
            out.append(q * service_ms)
        prev = t
    return out, n_drop
```

Doi chung duong: `n_drop/n_packets` cua Reich bounded phai khop loss do duoc
Phase L trong khoang 30%.

--------------------------------------------------------------------
## 6. MOL Neu PSA Fail

PSA:

```text
q_hat(t) = f(rho(t))
```

MOL:

```text
q_hat(t) = f(rho_tilde(t))
rho_tilde = rho da loc thong thap
```

Loc bang EWMA voi hang so thoi gian `T_relax`:

```python
alpha = 1.0 - math.exp(-dt / T_relax)
rho_tilde = rho_tilde + alpha * (rho[k] - rho_tilde)
q_hat = f(rho_tilde)
```

Gioi han:

```text
tau_rho >> T_relax -> rho_tilde ~= rho     -> MOL ~= PSA
tau_rho << T_relax -> rho_tilde ~= rho_bar -> MOL ~= SSA
```

Them vao T3 vi chi la hau xu ly:

```text
q_mol_load_ms = integral lambda(t) f(rho_tilde(t)) dt / integral lambda(t) dt
err_mol_ms    = q_bg_load_ms - q_mol_load_ms
gain_mol      = |err_qs| / |err_mol|
```

Tien doan moi:

```text
MOL vuot PSA khi Lambda < 3
MOL trung PSA khi Lambda > 10
err_mol nguoc dau err_qs o vung dong
```

Neu PSA fail, Phase T van ban giao duoc mot model dong cu the cho Phase 20R:
EWMA-rho voi hang so `T_relax`.

--------------------------------------------------------------------
## 7. Luoi Cuoi Cung

T.1 thay doi hai quyet dinh cua T.0: `dt` va cach chon `sigma_rho`.

`dt` OU:

```text
cu : 0.100 s
moi: 0.005 s
```

Ly do: voi `tau_rho=0.2 s`, `dt=0.100 s` chi co 2 buoc moi thoi gian tuong
quan. Trong khi `T_relax_min ~ 0.020 s`, hang doi se thay canh bac thang
100 ms thay vi thay OU tron. Quy tac:

```text
dt <= min(tau_rho, T_relax_min) / 5
```

Chot `dt=0.005 s`.

`sigma_rho`:

```text
sigma_max = (1.05-rho_bar)/2.58
sigma_rho = a * sigma_max
a in {0.20, 0.90}
```

Ly do: giai `sigma_rho` tu muc `J` tao nhieu o khong dat o tai cao. Cach
`a*sigma_max` luon kha thi, khong co lo hong, va van tao dai `J` rong:
`0.07 -> 46`. `J` tro thanh truc cua hinh, khong phai truc thiet ke.

Luoi chot:

```text
NHANH CHINH
  mode     in {h2, poisson}                                      -> 2
  rho_bar  in {0.70, 0.85, 0.925, 0.98}                          -> 4
  a        in {0.20, 0.90}                                       -> 2
  tau_rho  in {0.2, 1.0, 5.0} s                                  -> 3
  seed     in {11,12,13,14,15}                                   -> 5
                                                        total = 240 diem

NHANH CBR
  cbr x rho_bar=0.98 x a in {0.20,0.90}
      x tau in {0.2,1.0,5.0} x 5 seed                  total = 30 diem

DOI CHUNG AM
  sigma_rho=0 x 9 to hop (mode,rho_bar) x 5 seed        total = 45 diem

DIEM CANH
  moi 30 diem: h2,rho_bar=0.85,a=0.90,tau=1.0,seed=999 total ~= 11 diem

TONG campaign chinh: 326 diem x 105 s = 9.5 gio
Step response: 3.1 gio
Tong Phase T do chinh: ~= 12.6 gio
```

Do phu `Lambda` uoc tinh tu T_relax P90 hien co:

```text
mode      rho_bar  T_relax_p90  tau=0.2  tau=1.0  tau=5.0
h2          0.700       110 ms      1.8      9.1     45.6
h2          0.850       104 ms      1.9      9.6     48.2
h2          0.925        97 ms      2.1     10.4     51.8
h2          0.980       123 ms      1.6      8.1     40.7
poisson     0.700        90 ms      2.2     11.1     55.3
poisson     0.850       194 ms      1.0      5.2     25.8
poisson     0.925       274 ms      0.7      3.7     18.3
poisson     0.980       300 ms      0.7      3.3     16.7
cbr         0.980       879 ms      0.2      1.1      5.7
```

--------------------------------------------------------------------
## 8. Tien Doan Bo Sung

D-T10. MOL vuot PSA o vung dong:

```text
gain_mol = |err_qs|/|err_mol| > 2 khi Lambda < 3
gain_mol ~= 1 khi Lambda > 10
err_mol nguoc dau voi err_qs o vung dong
```

D-T11. `T_relax` do bang step response:

```text
poisson: khop cong thuc RBM trong 3x
h2     : lon hon RBM khoang 2-4x
cbr@rho=1.00: khong doc duoc trong cua so 60 s
doi xung len/xuong S-2 khop trong 25%
```

D-T12. Hai co che tu phan tach theo `rho_bar`:

```text
rho_bar <= 0.85  : err_jensen + d_sampling chi phoi
rho_bar >= 0.925 : err_qs dong chi phoi, J < 0.8
```

--------------------------------------------------------------------
## 9. Ket Luan T.1

Quyet dinh chot:

```text
T_relax source : step response, khong phai inflation
OU dt          : 0.005 s
sigma_rho      : a*sigma_max, a in {0.20,0.90}
tau_rho        : {0.2,1.0,5.0}, bo 20 s
cbr branch     : chi rho_bar=0.98
Reich(t)       : ban co tran buffer
fallback       : tinh err_mol bang EWMA-rho
```

T.2 se la buoc code dau tien: `mininet/rho_spec.py`, bo sinh `rho(t)` thuan,
tai lap bit-exact va dung `dt=0.005 s`.

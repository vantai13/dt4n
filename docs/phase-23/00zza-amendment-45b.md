# AMENDMENT 23-45b -- Sua BUG trong doi chung da tinh (`cv_sawtooth_null`)

Ngay ky : 2026-08-22
Tag     : amendment-45b
Lesson  : 23.18 (sua), mo duong cho 23.19
Phat hien boi: ra soat cua tac gia ban ke hoach 23.18, sau khi doc
               `results/LIVE/phase-23/aoi_stall_anatomy.json`

## 1. Bug

`measurements/aoi_stall_anatomy.py` tinh null CV cua rang cua thuan bang:

```python
"cv_sawtooth_null": 0.5 / np.sqrt(12) / (trim["p05_ms"] / 1000 + 0.25)
#                                        ^^^^^^^^^^^^^^^^^ dung P05 LAM d
```

Voi `Uniform[d, d+T]`, `p05 = d + 0.05 T`, tuc `p05` LON HON `d` mot khoang
`0.05 x 500 = 25 ms`. Dung `p05` lam `d` lam MEAN null bi thoi len 25 ms, va
vi CV = sd/mean nen CV null bi keo XUONG.

Ban ke hoach 23.18 muc 7.3 dan ro *"P05 = 143.1 ms KHONG phai la san d"* roi
dong script o muc 5 lai vi pham dung dieu do. Loi nam trong CONG THUC DOI
CHUNG, khong nam trong du lieu.

## 2. Hai gia tri

```text
                              d dung        mean null     CV null
CU  (SAI, d = p05)            143.612 ms    393.612 ms    0.366700
MOI (DUNG, d = mean - T/2)    116.070 ms    366.070 ms    0.394289

CV quan sat (CLEAN, da cat warm-up)                       0.395182
khoang cach CU   : +0.028482
khoang cach MOI  : +0.000893        <- nho hon 32 lan
```

## 3. He qua: sau khi cat warm-up, AoI tren topology_v7 LA RANG CUA SACH

Ba doi chung doc lap, tinh tren `n = 133,814` mau CLEAN da cat 19 chu ky dau:

```text
sd Uniform[d, d+500] = 500/sqrt(12) = 144.3376 ms
sd quan sat                         = 144.6644 ms
ty so                               = 1.002265        LECH 0.23%

CV null dung  0.394289   vs   CV quan sat  0.395182   -> +0.000893

max AoI  full 1568.9 ms  ->  da cat 657.1 ms          DUOI BIEN MAT
ty le khoang refresh dai sau khi cat = 0.0000%        (do o Lesson 23.18)
```

`M-72b` cua Lesson 23.8 (gate hinh dang rang cua, MISS voi gap 0.0522) se
HIT khi tinh lai voi null DUNG tren du lieu DA CAT WARM-UP. Gate do khong
phai ngo cut; no la mot bug cong voi mot transient khoi dong.

**KHONG rut lai `M-72b` cua 23.8.** Gia tri do la ket qua tren du lieu CHUA
cat, voi null SAI. Theo nguyen tac amendment 23-44: giu nguyen con so, thu
hep pham vi hieu luc, cong bo ban moi canh ban cu.

## 4. He qua cho Lesson 23.19

```text
BO   Lua chon C (empirical renewal replay, giu ca duoi overrun)
     -> sau khi cat warm-up KHONG CON duoi de mo phong.

MO HINH  z(t) = d(link) + phase(t),  phase ~ Uniform[0, T]
         d       ~ 115.5 ms  (thay vi 51 ms)
         T       ~ 501.1 ms
         d(link) = d + alpha(link),  alpha da do, bien do 25.95 ms

MUC TIEU selfcheck  mean 366.070   sd 144.664   CV 0.395182   p05 143.612
```

## 5. Doi estimator chot `d`: MOMENT thay vi trung binh hai duong

`d = 114.11 ms` cua Lesson 23.18 la trung binh DON GIAN cua hai estimator,
mot trong hai phu thuoc hang so debias 50 ms chua duoc do. Estimator MOMENT

```text
T_hat = sd * sqrt(12) = 144.6644 * 3.46410 = 501.132 ms
d_hat = mean - T_hat/2 = 366.070 - 250.566 = 115.504 ms
```

dung TOAN BO du lieu (khong chi hai phan vi) va KHONG phu thuoc debias.
Chenh voi 114.11 chi 1.39 ms -- khong doi ket luan nao, nhung sach hon.

## 6. Du doan MOI -- dien TRUOC khi chay

Cac muc duoi day CHUA duoc nhin. Ngoai le duy nhat: `M-98` la HAU NGHIEM,
ghi ro nhu vay, vi no duoc phat hien khi ra soat artifact da co.

```text
ID      Dai luong                                          Nguon       Dai khoa       KQ
----------------------------------------------------------------------------------------
M-91  * KS test: AoI da cat vs Uniform[d_hat, d_hat+T_hat] [CO CHE]   D < 0.03       __
M-92    T tu p95-p05 so voi T tu sd                         [MO TA]    lech < 20 ms   __
M-93  * PROBE_BIAS DO DUOC (thay vi gia dinh 50 ms)         [CO CHE]   30 - 70 ms     __
M-94  * K1: corr(rho(k), T_eff(k-1,k))                      [CO CHE]   < -0.3         __
M-95  * K2: corr rieng phan khu T_eff(k-1,k) THAY VI (k,k+1)[CO CHE]   |r| < 0.10     __
M-96  * K3: khu theo 1/dt (quan he ti so) thay vi theo dt   [CO CHE]   |r| < 0.10     __
M-97    cat doi xung (bo them 5 chu ky cuoi): delta CV      [MO TA]    |d| < 0.005    __
M-98  # HAU NGHIEM: Var(d_transport) ~ E[d_transport]       [CO CHE]   R2 > 0.7       __
M-99  * hoi quy d_transport theo VI TRI THAT trong vong
        PATCH (suy tu spec topology), he so goc             [CO CHE]   3 - 9 ms/vi tri __
```

`*` = du doan CO CHE. `#` = hau nghiem, KHONG duoc tinh nhu du doan da ky.

## 7. Quy tac phan xu cho `corr(AoI, rho)` -- VIET TRUOC KHI THAY SO

Gia thuyet moi (b'): tuong quan am la artifact cua ESTIMATOR TOC DO CO
CUA SO. `bridge/collector.py:532-536` tinh `rho` tu `dbytes/dt` voi
`dt = t_source(k) - t_source(k-1)`, tuc `T_eff` cua khoang TRUOC. Lesson
23.18 khu `T_eff(k, k+1)` -- khoang HIEN TAI -- nen ghep noi van chay qua
`T_eff(k-1, k)`.

```text
M-94 HIT va (M-95 HIT hoac M-96 HIT)
    -> (b') DUOC XAC NHAN. corr(AoI,rho) RA KHOI threats to validity,
       chuyen thanh mot dong trong phan gioi han NHAC CU.
M-94 MISS
    -> (b') bi bac. corr O LAI threats to validity, co che van chua ro.
M-94 HIT nhung ca M-95 va M-96 deu MISS
    -> ghep noi co that nhung khong giai thich HET. BAO CAO nhap nhang,
       GIU trong threats to validity.
```

## 8. Phat biểu lai ve dong nhat thuc H4

Lesson 23.18 muc 4 phat biểu dong nhat thuc `alpha(l) = d_transport(l) -
mean(d_transport)` nhu bang chung cho co che vong PATCH. Phat biểu do QUA
MANH: dong nhat thuc dung THEO CAU TRUC tu chinh dinh nghia
`AoI = phase + d_transport`. Phan du cua no do dung MOT thu:

```text
residual(l) = E[phase(l)] - mean_l E[phase]
```

tuc "phase co phan bo giong nhau giua 8 link khong". RMS 2.473 ms tren chu
ky 500 ms = 0.5% la mot ket qua THAT va TOT, nhung no la kiem tra tinh NHAT
QUAN cua phep phan ra, khong phai bang chung co che.

Bang chung CO CHE la `M-98` (tich luy phuong sai) va `M-99` (vi tri that
trong vong PATCH). Bao cao 23.18 phai duoc sua theo.

## 9. Ba diem nho phai ghi

```text
(a) Chu ky 244 (chu ky CUOI) overrun o 3/30 run -> transient TAT MAY.
    Cat warm-up chi cat DAU. Phai bao cao ca cat doi xung (M-97).
(b) Probe bat dau MUON hon sync agent 1.25 s; stall o cycle 3 roi vao
    t = 1.0-1.5 s -> probe co the da bo lo MOT PHAN stall.
    => max AoI 1568.9 ms la CAN DUOI cua do lon stall that.
(c) `d_transport` dung `t_obs` SOM NHAT (estimator MIN). Probe luan phien
    fwd/rev khu bias vi tri doc TRONG TRUNG BINH, nhung phep lay MIN
    khong duoc khu -> thien ve luot probe doc link SOM.
    => d_transport bi danh gia THAP vai ms (get_ms ~ 4 ms).
```

## 10. No ky thuat mo cho Phase 24

Sau khi loai `cycle_trace` (do 20 Thing chu khong do 1 link), ca bon
estimator con lai deu den tu CUNG luong probe -- khong con phep kiem cheo
nao qua dong ho phia bridge.

```text
Sua bang MOT dong log trong sync_agent: ghi t_patch_done cho TUNG Thing
thay vi chi cycle_elapsed cho ca vong.
=> d_transport(l) = t_patch_done(l) - t_source(l), do phia bridge
=> khoi phuc kiem cheo hai dong ho VA do truc tiep vi tri vong PATCH
```

Chu ky: ____________

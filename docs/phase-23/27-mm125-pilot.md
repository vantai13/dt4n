# Lesson 23.19 -- sua truoc 5b, va PILOT mot cell cho M-125

Ngay     : 2026-08-22
Prereg   : `docs/phase-23/00zzg-amendment-49a.md` (tag `amendment-49a`)
Pham vi  : MOT cell (`poisson@0.925`), hai truc. KHONG phai BUOC 5b day du.

## 1. Hai sua truoc 5b

### 1.1 `M-125` tach lam hai

Do tren chinh hai parquet cua 5a (`z` trung binh THUC trong tung bin):

```text
bin   z_tb CU    ty trong CU   z_tb MOI   ty trong MOI   ty so
B0      75.00        0.0900     178.25        0.2494     2.377
B1     147.50        0.2000     303.12        0.2499     2.055
B2     247.50        0.2000     428.12        0.2499     1.730
B3     424.99        0.5100     553.40        0.2509     1.302
```

Bin cu rong khong deu (45/100/100/250 ms), bin moi deu. Trung binh theo bin
cua `q_hat` moi/cu se ra `~+30%`, MISS gia dai `+5..+13%` von suy tu ty so
MEAN z. Da tach `M-125a` (bien) va `M-125b` (moi bin, tien doan RIENG).

### 1.2 `d_base` thanh HAM cua ho so

`d_base` co dinh 107.775 ms (bu tru rieng cho `U3`) tai lap dung confound ma
`amendment 23-49 muc 3` duoc viet ra de sua:

```text
truoc sua:  U0 357.889   U1 380.389   U2 370.389   U3 366.014 ms
sau  sua:   U0 366.023   U1 366.022   U2 366.022   U3 366.014 ms
            trai 0.0091 ms  (M-132 dai khoa < 0.01)          HIT
```

`U1c`/`U2c` nay du thua (cho ket qua y het `U1`/`U2`); giu lai de khong lam
churn khoa ho so, da ghi la DU THUA.

> **Nguyen tac:** hang so bu tru phai la HAM cua thu no bu tru. Da lam dung
> cho `alpha -> U3` nhung dung mot buoc som o `U3 -> d_base`.

### 1.3 Doi chu ky ham suyt gay mot loi IM LANG

Them `profile_ms` len DAU chu ky `d_base_s()` lam moi cuoc goi cu
`d_base_s(DT)` truyen `dt` vao vi tri `profile_ms` -- va tra ve mot so SAI
mot cach im lang (`0.1159 - 0.005/1000`). Bo test bat duoc ngay.

Da bien no thanh loi ON AO: `d_base_s` kiem `profile_ms` co dung 8 phan tu
khong, khong thi `raise TypeError` kem goi y `d_base_s(dt=...)`.

## 2. ★ PILOT `M-125` -- mot cell, va ket qua rat manh

`poisson@0.925`, 5 seed, `n = 200.000`, `axis=legacy/U0` vs `axis=measured_v7/U3`,
`conformal_v2` mac dinh.

### `M-125b` -- dinh luat do gian `z^0.431` o BON diem

```text
bin     q CU     q MOI   ty so q   z_tb CU  z_tb MOI  tien doan    lech   KQ
B0    11.588    16.767     1.447      75.0     178.3     1.452    -0.4%   HIT
B1    15.635    21.123     1.351     147.5     303.1     1.364    -1.0%   HIT
B2    19.646    24.500     1.247     247.5     428.1     1.266    -1.5%   HIT
B3    24.322    26.895     1.106     425.0     553.4     1.121    -1.3%   HIT

4/4 bin trong +/-25%   -- va thuc te trong +/-1.5%
```

Bon ty so `z` khac nhau (1.30 den 2.38) cho bon tien doan khac nhau
(1.121 den 1.452), va ca bon deu khop trong `1.5%`. Dai khoa la `+/-25%`;
ket qua tot hon dai khoa **16 lan**.

```text
=> Dinh luat z^0.431 KHONG chi la MO TA. No DU DOAN duoc, o bon diem, khi
   trung tam bin doi gap 1.3 den 2.4 lan.
=> Day la dau vao truc tiep cho Lesson 23.28 (transfer giua bin tuoi).
```

### `M-125a` -- `q_hat` BIEN

```text
q_hat bien CU 20.5032 -> MOI 22.3289    +8.90%
dai khoa +5% .. +13%                     HIT
tien doan tu ty so mean z (1.2100)       +8.56%   -> lech 0.34 diem
```

### `M-126` -- noi bo run moi

```text
q_hat(B3)/q_hat(B0) = 1.604
tien doan (z_tb B3/B0)^0.431 = 1.630     lech -1.6%     HIT
```

## 3. Canh bao ve pham vi

```text
Day la MOT cell. BUOC 5b day du la 8 cell + ha nguon.
Ket qua o day KHONG duoc trich dan nhu ket qua cua 23.20.
No tra loi dung mot cau hoi: "dac ta M-125 da dung chua, va co dang chay
8 cell khong". Ca hai deu CO.
```

## 4. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-117 | amendment 23-49a commit RIENG, co tag, TRUOC khi sua code | PASS |
| G23-118 | M-132: moi ho so cung mean z trong +/-0.01 ms | PASS -- trai 0.0091 |
| G23-119 | `d_base_s` la HAM cua ho so, va cuoc goi sai bi RAISE | PASS |
| G23-120 | PILOT M-125a (bien) tren 1 cell | PASS -- +8.90% |
| G23-121 | PILOT M-125b (4 bin) tren 1 cell | PASS -- 4/4, lech <= 1.5% |
| G23-122 | PILOT M-126 tren 1 cell | PASS -- 1.604 vs 1.630 |

# AMENDMENT 23-47 -- Nguon that su cua lech M-91, va tien dang ky Task B

Ngay ky : 2026-08-22
Tag     : amendment-47
Lesson  : 23.19 Task A (sua ket luan) + Task B (tien dang ky)

## 1. CORRECTION: cai luoc KHONG giai thich M-91

Ban ra soat de xuat: mo phong 600 chien dich, lay dai 5-95% cua
(mean, p05, p50, p95), va bao ca ba lech quan sat deu nam trong dai
-> M-91 dong. **Phep so sanh do khong dong nhat.**

```text
So quan sat  : (phan vi quan sat) - (null KHOP TU chinh mau do)
So mo phong  : (phan vi mo phong) - (gia tri LY TUONG cua tham so that)
```

Khop moment hut theo du lieu, nen "lech so voi null da khop" co phan bo HEP
HON HAN "lech so voi gia tri ly tuong". Dung ve trai lam dai tien doan cho
ve phai thi dai bi thoi len 2-3 lan.

Lam lai cho dung -- moi chien dich mo phong deu di **y het** duong ma so
quan sat da di (khop moment tren chinh no, roi so phan vi), co ca trai doc
33 ms trong mot luot probe (do duoc, 4.713 ms moi read_pos):

```text
        sd       5%      95%    quan sat   trong 90%?
p05   1.50    -1.48    +3.15      +3.05      CO
p50   2.06    -3.12    +3.54      -7.93      KHONG   (~3.9 sigma)
p95   1.66    -3.63    +1.71      -8.98      KHONG   (~6.4 sigma)
```

Cai luoc dong gop khoang `+/-2 ms`, khong phai `8 ms`. **M-91 chua dong.**

## 2. Nguon THAT SU: `d_transport` la BIEN NGAU NHIEN LECH PHAI

Mo hinh `z = d + alpha(link) + Uniform[0,T]` coi `d + alpha` la HANG SO.
Do duoc thi khong:

```text
d_transport trong run, gop:  mean 164.89  median 155.79  sd 40.00
                             skewness +4.045   max 540.99 ms
```

Va lech phai cua AoI theo tung link bam sat lech phai cua `d_transport`
theo tung link:

```text
link   mean-med(AoI)   sd(d_tr)   skew(d_tr)   mean-med(d_tr)
ac           1.50        32.09       6.156          3.55
ad           1.73        32.14       6.522          3.84
bc           3.37        33.16       6.120          5.56
bd           6.48        36.17       4.897          9.17
uA          11.09        49.32       1.165         21.12
uB           4.03        47.44       1.139          9.90
vC           6.32        41.60       3.537         10.38
vD           8.36        49.00       2.093         16.98

corr( mean-med(AoI), mean-med(d_transport) ) = +0.9637
ty le trung binh                             =  0.527
```

Ty le `~0.5` dung nhu ky vong: cong them mot Uniform doi xung co `sd` lon
(144 ms) keo trung vi ve phia trung binh, lam nhat lech phai di khoang mot
nua.

```text
=> Lech M-91 KHONG phai artifact lay mau. No la MOT DAC TRUNG THAT cua he:
   vong PATCH thinh thoang cham, nen `d` co duoi phai.
=> Chuoi giai thich dong lai:
      alpha                  0.00 ms   (chung minh dai so, amendment 23-46)
      H8 nghich ly kiem tra  0.29 ms   (T_eff CV = 0.0046)
      cai luoc               ~2 ms     (dai tien doan lam dung)
      d_transport lech phai  phan con lai, corr 0.96 theo link
```

## 3. He qua cho mo hinh: `d` la PHAN BO, khong phai mot so

```text
z = d(t) + alpha(link) + Uniform[0, T]      voi d(t) ~ phan bo lech phai
```

Nhung **duoi cua `d` chi do duoc qua mot nhac cu tho**: estimator MIN,
luong tu hoa 100 ms, va bi khoa luoc. Hinh dang duoi vi the KHONG dang tin;
chi SU TON TAI cua no la chac.

```text
=> Task B sinh `aoi_model_v7` voi HAI muc:
   muc 1 (dung ngay)  d la HANG SO. Sai o momen 3, dung o momen 1 va 2.
                      Ghi ro rang no la xap xi, kem do lon sai so (7.93 ms
                      tren trung vi = 2.2% cua T).
   muc 2 (tuy chon)   d lay mau tu phan bo thuc nghiem. CHI dung de kiem
                      do nhay, KHONG dung lam mac dinh, vi duoi khong dang tin.
```

## 4. Cai luoc KHONG de doa ket luan -- kiem lai

Doi chieu voi `results/LIVE/phase-23/dsync_sensitivity.json` (headline
`BRACKET_SIGN_NOT_INVARIANT`), noi suy tuyen tinh diem doi dau cua
`lift_minus_swing`:

```text
cell             doi dau tai   cach d=115.9   so sigma (sd 3.325)
h2@0.700              98.3 ms       17.6 ms       5.3
poisson@0.850        149.2 ms       33.3 ms      10.0
poisson@0.900        162.2 ms       46.3 ms      13.9
poisson@0.925        khong doi dau       --        --
poisson@0.960        khong doi dau       --        --
```

Ket luan (khong lat trong `+/-6.5 ms`) DUNG. Nhung phai ghi kem gioi han:

```text
- diem doi dau noi suy TUYEN TINH qua mot khoang 124 ms (51 -> 175 ms).
  Con so "98.3 ms" khong co do chinh xac toi 0.1 ms.
- artifact do mang `status: SENSITIVITY_ONLY` va
  `limitation: does not measure AoI on topology_v7`
- no dung `z_edges` CU (0.055..0.5501), khong phu dai z moi.
=> "5.3 sigma" la mot khoang cach AN TOAN, khong phai mot phep do chinh xac.
```

## 5. Du doan cho Task B -- dien TRUOC khi chay

```text
ID       Dai luong                                          Nguon      Dai khoa      KQ
---------------------------------------------------------------------------------------
M-109 *  |alpha_fwd - alpha_rev| lon nhat tren 8 link       [CO CHE]   < 2 ms        __
M-110 *  selfcheck: mean/p05/p50/p95 quan sat nam trong
         dai 5-95% cua N=400 chien dich mo phong            [CO CHE]   4/4 nam trong __
M-111 *  PC: process_mode dung nham cho selfcheck -> FAIL   [CO CHE]   FAIL          __
M-112 *  PC: d = 143.6 ms (p05) -> selfcheck FAIL o mean    [CO CHE]   FAIL          __
M-113 *  NC: d=0.051, T=0.5, alpha=0 -> age_steps() trung
         KHIT sawtooth_age_steps()                          [CO CHE]   bit-exact     __
```

## 6. Quy tac phan xu M-109 -- VIET TRUOC

```text
M-109 HIT  -> luan phien fwd/rev da khu tuong tac thu-tu-doc x luoi luoc.
              alpha vung, nap so diem vao mo hinh.
M-109 MISS -> alpha bi nhiem. Dung TRUNG BINH fwd/rev va ghi CI cua alpha;
              KHONG duoc nap so diem.
```

## 7. Rang buoc thiet ke bat buoc cho `aoi_model_v7`

```text
1. TACH HAI CHE DO trong cung mot module:
     process_mode()     z = d + alpha(l) + Uniform[0,T]   <- PIPELINE dung
     instrument_mode()  process_mode() lay mau qua probe khoa <- SELFCHECK dung
   Gop lam mot = nap cai luoc vao pipeline. Do la loi te nhat co the xay ra
   o 23.19, va tinh vi hon d = 51 ms nhieu.
2. SELFCHECK SO THEO DAI, khong theo diem: pha ban dau cua 15 run la an so,
   nen doi khop diem la doi khop mot thu ngau nhien.
3. Tham so chot:
     T     = 500.2922 ms   bridge-side, KHONG bi luoc
     d     = 115.9 ms +/- 6.5 (95%)   qua probe, GHI CI, khong ghi so tran
     alpha = do; cho M-109
   Bo han 114.11 / 115.50 / 116.07 -- ca bon la cung mot so.
```

Chu ky: ____________

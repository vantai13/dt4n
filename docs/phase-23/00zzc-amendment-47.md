# AMENDMENT 23-47 -- Chan doan lay mau probe truoc khi xay mo hinh AoI

Ngay ky : 2026-08-22
Tag     : amendment-47
Lesson  : 23.19 Task A
Loai    : PREREGISTRATION + mot CORRECTION (muc 1)

## 1. CORRECTION: "positive control T = 500.0046 ms" KHONG dung

Ban ra soat de xuat: hieu chinh moment bang `Var(alpha)` cho
`T = 500.0046 ms`, khop chu ky DANH DINH `500 ms` trong `4.6 us`, va goi do
la positive control manh nhat cua do an.

So hoc tai lap chinh xac:

```text
Var(alpha) ddof=0 = 94.0804 ms^2      (mean(alpha) = -3.4e-14, kiem OK)
Var(z) quan sat   = 20927.80 ms^2
T = sqrt(12 x (20927.80 - 94.08)) = 500.0046 ms      <- tai lap dung
```

**Nhung doi tuong so sanh sai.** Chu ky refresh KHONG phai mot hang so danh
dinh chua biet -- no da duoc **DO TRUC TIEP**, khong qua mo hinh, tu hieu hai
gia tri `t_source` ke tiep:

```text
                                        T (ms)    lech so voi danh dinh
danh dinh                              500.0000            --
DO TRUC TIEP (t_source ke tiep)        500.3078        +0.3078
   8 link: 500.2875 .. 500.3370, trai 0.0495 ms, n = 3615 update/link
MO HINH (moment + Var(alpha))          500.0046        +0.0046
```

```text
mo hinh lech DANH DINH  : +0.0046 ms
mo hinh lech DO DUOC    : -0.3032 ms      <-- day moi la sai so that
do duoc  lech DANH DINH : +0.3078 ms
```

Vong sync **that su** chay o `500.31 ms`, khong phai `500.00 ms`. Mo hinh
cho `500.0046 ms` nen no lech gia tri THAT `0.30 ms`. Viec no roi rat gan
gia tri DANH DINH la mot **trung hop**: no gan danh dinh hon ca thuc te.

> Mot mo hinh khop gia tri DANH DINH sat hon khop gia tri DO DUOC thi khong
> phai da tai tao mot hang so cua he -- no dang bo qua mot hieu ung that
> co do lon dung bang khoang lech do.

Do lon `0.30 ms` khong ngau nhien: no la dau hieu phuong sai cua pha THAP
hon uniform mot chut.

```text
kiem phan ra voi T DO DUOC:
    T^2/12 + Var(alpha) = 20858.99 + 94.08 = 20953.07 ms^2
    Var(z) quan sat                        = 20927.80 ms^2   thieu -25.27
=> ty le phuong sai pha / uniform = 0.998788
```

**Va con so nay da chan gia thuyet H7 tu truoc khi chay:**

```text
luoc 5 rang deu (pha khoa hoan toan) cho ty le = 1 - 1/25 = 0.960000
quan sat                                       =           0.998788
=> pha KHONG bi khoa thanh luoc. Do lech uniform chi 0.12% phuong sai.
```

Tuy vay Task A van duoc chay, vi (a) ty le phuong sai la mot thong ke gop,
no khong loai duoc mot lech HINH DANG cuc bo, va (b) `M-91` va do lech
trung vi `-7.93 ms` van chua co nguyen nhan.

**So chot cap nhat:** `T = 500.3078 ms`, `d = mean - T/2 = 115.9165 ms`.
Ca hai deu DO DUOC. Bo `T = 500.0046 / d = 116.068`.

## 2. CORRECTION 2: bao cao 23.18 noi `alpha` giai thich lech hinh dang -- SAI

`docs/phase-23/22-aoi-stall-anatomy.md` muc 3 viet lech phan vi
`+3.05 / -7.93 / -8.98 ms` "da dinh danh (alpha tron 8 rang cua lech pha)".
Chung minh no KHONG the dung:

```text
Hon hop 8 phan Uniform[d+alpha_i, d+alpha_i+T], trong so bang nhau.
Voi x nam trong VUNG PHU (tat ca 8 phan deu phu):
    F(x) = (1/8) sum_i (x - d - alpha_i)/T = (x - d - mean(alpha))/T
         = (x - d)/T                          vi mean(alpha) = 0
=> trong vung phu, CDF cua hon hop TRUNG KHIT CDF cua mot rang cua don.
   Vung phu = [d + max(alpha), d + min(alpha) + T] = [d+17.3, d+491.3]
   p05, p50, p95 deu nam SAU trong vung phu.
=> alpha du doan lech = 0 o CA BA phan vi.
```

Lech `-7.93 ms` o trung vi phai den tu **co che khac**. Gia thuyet moi:

```text
H8  Do lech trung vi la NGHICH LY KIEM TRA (inspection paradox).
    Probe lay mau deu THEO THOI GIAN, nen khoang refresh DAI hon duoc lay
    mau nhieu hon (length-biased). Tuoi khi do khong phan bo Uniform[0,T]
    ma theo phan bo TUOI CAN BANG (equilibrium / residual life):
        f(a) = P(T_eff > a) / E[T_eff]
    Voi T_eff BIEN THIEN, phan bo nay LECH PHAI va trung vi TUT XUONG
    duoi E[T]/2 -- dung dau quan sat duoc.
```

## 3. Gia thuyet

```text
H6  Phan bo AoI DO DUOC = phan bo TRUNG BINH THEO THOI GIAN
    (probe lay mau khong thien lech)
H7  Lay mau TUONG UOC (T/T_s ~ 5.003): pha khoa mot phan -> LUOC lam mem
H8  Lech trung vi la nghich ly kiem tra do T_eff bien thien
```

## 4. DA XEM gi truoc khi ky

```text
DA XEM: T do truc tiep 500.3078 ms; Var(alpha) = 94.0804; ty le phuong sai
        pha/uniform = 0.998788; d suy ra 115.9165 ms; chung minh dai so o
        muc 2 (alpha khong the gay lech phan vi).
CHUA XEM: phan bo pha chuan hoa u, histogram cua no, KS cua no; jitter
        khoang probe; phan bo T_eff sau khi cat; trung vi cua phan bo tuoi
        can bang; moi so M-100..M-108.
```

## 5. Du doan -- dien TRUOC khi chay

```text
ID       Dai luong                                          Nguon      Dai khoa     KQ
---------------------------------------------------------------------------------------
M-100 *  KS(u trong 1 RUN, 1 LINK) vs Uniform[0,1]          [CO CHE]   D < 0.05     __
M-101 *  KS(u GOP 15 run, tung link) vs Uniform[0,1]        [CO CHE]   D < 0.02     __
M-103 *  histogram u 50 bin, 1 run: ty so max/min           [CO CHE]   < 3.0        __
M-104    sd khoang probe thuc te (jitter cua sleep)         [MO TA]    0.5 - 5 ms   __
M-107 *  H8: trung vi phan bo tuoi CAN BANG suy tu T_eff
         do duoc, so voi trung vi quan sat 358.141 ms       [CO CHE]   lech < 3 ms  __
M-108 *  mo hinh (d + alpha + tuoi can bang) tai tao
         p05 / p50 / p95                                    [CO CHE]   lech < 3 ms  __
```

`u` = vi tri chuan hoa trong chinh khoang refresh cua mau do:
`u = (t_obs - t_source - d_link) / T_eff(epoch do)`. Neu probe lay mau deu
theo thoi gian thi `u ~ Uniform[0,1]`, KHONG phu thuoc d hay alpha.

## 6. Quy tac phan xu -- VIET TRUOC

```text
M-100 HIT va M-103 HIT
    -> H6. Probe khong thien lech. Phan bo do duoc DUNG LA time-average.
       Selfcheck cua 23.19 nham vao no.

M-100 MISS nhung M-101 HIT
    -> pha khoa TRONG run nhung GOP 15 run thi day du.
       Selfcheck phai nham vao phan bo GOP, khong dung mot run le.

M-100 MISS va M-101 MISS
    -> H7. Phan bo do duoc BI THIEN LECH, KHONG duoc dung lam muc tieu.
       Phai sinh pha LY THUYET tu T va d da uoc luong.

M-107 HIT
    -> H8. Lech trung vi da co nguyen nhan. Mo hinh phai dung phan bo
       TUOI CAN BANG, khong phai Uniform[0,T].
M-107 MISS
    -> con mot co che thu ba chua biet. KHONG duoc viet mo hinh cho den khi
       tim ra. Ghi ro va dung.
```

## 7. KHONG duoc lam

```text
- KHONG doi khoang probe roi do lai de "sua": do la DU LIEU MOI, khong phai
  cung mot phep do. Neu can, do la mot chien dich rieng co amendment rieng.
- KHONG chon dai khoa sau khi thay histogram.
- KHONG viet selfcheck nham vao mean/sd/CV roi goi la da kiem: `d` va `T`
  duoc FIT TU chinh mean va sd, nen khop la TAUTOLOGY. Muc tieu phai gom
  it nhat mot dai luong KHONG duoc dung de fit (phan vi, hoac hinh dang).
```

Chu ky: ____________

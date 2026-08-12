# AMENDMENT 7 -- Phase 21R

Ngay ky: 2026-08-12
Nguoi ky: Codex theo yeu cau owner repo DT4N
Boi canh: sau khi chay `cert/freshness_requirement.py`.

Lesson nay dao nguoc ket qua 21R: tu muc tieu chat luong ra yeu cau do tuoi
`z*`, roi ra tan so dong bo.

## G1. Dong vong voi du doan truot Lesson 21R.2

Amendment 2 chan doan du doan `err_anchor` bi truot vi neo vao `err(z_max)`
thay vi `E_z[err(z)]` tren phan phoi AoI rang cua. Do lai tren cell chinh
`poisson@0.925`:

```text
E_z[err(z)] tren luoi rang cua = 0.217859
err(E[z]) voi E[z] = 0.3025    = 0.227436
err(z_max) voi z_max = 0.550   = 0.288742
do duoc rang cua                = 0.222399
```

Thu tu Jensen giu:

```text
0.217859 <= 0.227436 <= 0.288742
```

Do duoc rang cua nam gan `E_z[err(z)]`, khong gan `err(z_max)`. Chan doan cua
Lesson 21R.2 duoc xac nhan.

## G2. Hai cai san

```text
san vat ly : z >= d_sync = 0.051 s
san mo hinh: err(z=0, all rows) = 0.040297
```

Luu y nhan so: JSON cung luu `err_at_z0_test_rows = 0.040826`. Con so
`0.040297` la model floor tren all rows; cac chi so q_hat/gate van dung
calib/test split.

Tai `z=0`:

```text
rms(s_margin, all rows) = 2.142942 ms
q_hat(z=0)              = 3.694914 ms
accept(kappa=1)         = 0.842462
err|accept(kappa=1)     = 0.000131
```

Suy ra san mo hinh `4.03%` la san cua che do "buoc phai tra loi". No khong phai
san cua che do "duoc phep noi khong biet", vi cong loc ha error tren accepted
set xuong `0.0131%`.

## G3. Dao nguoc thanh yeu cau do tuoi

Cell chinh `poisson@0.925`:

| Muc tieu | z* | Kha thi vs d_sync? | Hz neu AoI mean | Hz neu AoI max |
|---|---:|---|---:|---:|
| `err_anchor <= 0.10`, khong cong loc | 0.046744 | NO | -- | -- |
| `err|accept <= 0.01`, `kappa=1` | 0.061035 | YES | 49.83 | 99.66 |
| `acceptance >= 0.50`, `kappa=1` | 0.094278 | YES | 11.55 | 23.11 |

Headline:

```text
Khong co cong chung nhan, muc tieu sai so quyet dinh 10% la bat kha thi o moi
tan so dong bo: no doi hoi AoI 46.7 ms, thap hon san truyen tin 51 ms. Voi
cong chung nhan, muc tieu 1% dat duoc o AoI 61.0 ms.
```

## G4. Bay "AoI toi da" vs "AoI ky vong"

Voi AoI rang cua:

```text
z_max  = d_sync + T
z_mean = d_sync + T / 2
```

Cung mot dac ta `z <= 61 ms`:

```text
dien giai AoI toi da  : T <= 0.010 s -> 99.66 Hz
dien giai AoI ky vong : T <= 0.020 s -> 49.83 Hz
```

Hai cach dien giai chenh dung 2 lan tan so. Vi vay moi phat bieu ve AoI phai
noi ro la peak/max hay mean.

## G5. Bien dang-chat-luong

Muc tieu `err|accept = 1%`, cell `poisson@0.925`:

| z | q_hat | kappa* | acceptance | Hz mean | Hz max |
|---:|---:|---:|---:|---:|---:|
| 0.055 | 10.0361 | 0.9790 | 0.6002 | 125.0 | 250.0 |
| 0.100 | 13.0036 | 1.1308 | 0.4325 | 10.2 | 20.4 |
| 0.150 | 15.5538 | 1.2437 | 0.2997 | 5.1 | 10.1 |
| 0.200 | 17.6879 | 1.3575 | 0.1973 | 3.4 | 6.7 |
| 0.300 | 21.0404 | 1.4489 | 0.1003 | 2.0 | 4.0 |
| 0.400 | 23.7591 | 1.6971 | 0.0291 | 1.4 | 2.9 |
| 0.550 | 26.8521 | 2.2159 | 0.0012 | 1.0 | 2.0 |

Gia tri bien cua dau tu:

```text
2.0 Hz -> 10.2 Hz  : acceptance 0.1003 -> 0.4325, gain +0.3322
10.2 Hz -> 125 Hz  : acceptance 0.4325 -> 0.6002, gain +0.1677
```

Knee nam o khoang `z=0.100`, `10.2 Hz` theo dien giai AoI mean. Khuyen nghi
van hanh: nang dong bo len khoang `10 Hz`, sau do dau tu them nen chuyen sang
cai thien mo hinh/measurement.

Quan sat quan trong: `kappa*` tang theo `z` tu `0.9790` len `2.2159`. Khi twin
cu hon, khong chi `q_hat` lon hon ma nguong tuong doi cung phai bao thu hon.
He van hanh that nen dieu chinh `kappa` theo AoI.

## G6. Cross-cell

| Cell | no-gate `err<=0.10` | gated `err<=0.01` | knee mean Hz | Ghi chu |
|---|---:|---:|---:|---|
| `poisson@0.925` | z*=0.0467, infeasible | z*=0.0610, feasible | 10.2 | main headline |
| `poisson@0.850` | z*=0.0492, infeasible | z*=0.0913, feasible | 10.2 | same qualitative result |
| `h2@0.700` | z*=0.1546, feasible | z*=0.1357, feasible | 10.2 | easier cell |

Ket qua tren khong noi "dong bo nhanh hon la vo ich". No noi quyet dinh dau tu
phai so sanh hai nut van: mua freshness bang ha tang, hoac mua safety/quality
bang abstention/certification.

## G7. Tong ket du doan tien dang ky

Sau cac lesson 21R:

```text
2 du doan trung: C2 suy bien tai o GO; kappa khong thu nguyen can thiet.
4 du doan truot: q_hat(B1), q_hat(B4), ti so B4/B1, P(accept|kappa=1),
                 z_cross/anchor bi anh huong boi scale va Jensen.
```

Hai nguyen nhan goc:

```text
1. Loi khop thang do: lay so o muc delay/path roi gan cho muc cost/margin.
2. Loi Jensen: neo vao f(z_max) thay vi E_z[f(z)] tren AoI rang cua.
```

Quy tac rut ra: moi con so lay tu artifact cu phai kem ba nhan `scale`,
`level`, va `row set`.

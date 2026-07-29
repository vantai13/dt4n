# AMENDMENT 6 -- Phase L / after pilot L.5

Artifact chinh:

```
results/phase-L/l5_pilot_0729_1336.json
```

## A6-1  Diem fail duy nhat la loi cua bang du doan

P1 cua pilot: `17/18`. Diem fail:

```
cbr, rho=1.00: du doan 23.17 ms, do duoc 4.153 ms sau khi tru san
```

Nguyen nhan: bang du doan cu cong probe len tren tai nen tai rho=1:

```
rho*C + 20*106 B/s = C + 2120 B/s
```

Do la qua tai ben vung 0.283%, du nho nhung tai rho=1 no lam hang doi bao hoa.
Code do L.4/L.5 dung dinh nghia moi: probe duoc tru khoi tai nen, nen
`rho_actual` gan dung nhan.

Bai hoc: sai lech 0.283% trong rho co the lam du doan sai 5.6 lan tai rho=1,
vi he so khuech dai `rho/(1-rho)` phan ky.

## A6-2  rho=1.00 la diem ky di

Tu `inflation_factor = SE_batch / SE_naive`, pilot cho thay `cbr, rho=1.00`
co inflation rat lon:

| diem | inflation | y nghia |
|---|---:|---|
| cbr rho=0.50 | 3.26 | mau con tuong quan nhung on |
| cbr rho=0.95 | 5.50 | hoi phuc cham hon |
| cbr rho=1.00 | 70.47 | diem toi han, n_eff cuc nho |
| h2 rho=1.00 | 3.38 | buffer da bao hoa tu truoc, co luc hoi phuc huu han |

Tai rho=1 chinh xac, hang doi gan nhu buoc di ngau nhien khong co drift keo ve
0. Vi vay trung binh mau khong hoi tu nhu cac diem khac. L.6 van giu diem nay
nhung them seed o dai toi han va bao cao no rieng.

Chot cho L.6:

- rho in `{0.98, 1.00, 1.02}` tai cau hinh `(6,13)` co them seed `16..20`.
- rho=1.00 bao cao mean, khoang giua seed, va chi so inflation/relaxation.
- Khong loai rho=1.00 khoi fit; band du rong o day la hanh vi dung.

## A6-3  PASTA phan ra ba thanh phan

Pilot tra loi cau hoi A5-6:

```
delta = packet_average - probe_average
      = offset kich thuoc goi + thien lech ket nap + PASTA that
```

Offset kich thuoc goi do truc tiep bang CBR:

| mode | rho | delta |
|---|---:|---:|
| cbr | 0.80 | +0.0215 ms |
| cbr | 0.95 | +0.0218 ms |

Bang phan ra:

| mode | rho | delta do | offset | ket nap | PASTA that | % q |
|---|---:|---:|---:|---:|---:|---:|
| poisson | 0.80 | +0.0771 | +0.0215 | -0.0114 | +0.0670 | +2.6% |
| poisson | 0.95 | -0.2464 | +0.0215 | -0.2522 | -0.0157 | -0.2% |
| h2 | 0.80 | +1.5320 | +0.0215 | -0.5287 | +2.0392 | +23.9% |
| h2 | 0.95 | +1.6531 | +0.0215 | -1.1627 | +2.7943 | +22.9% |

Kiem chung: Poisson tai rho=0.95 du doan delta `-0.2307 ms`, do `-0.2464 ms`,
lech `0.0157 ms` khoang 6%. H2 co PASTA that on dinh khoang 23% qua hai muc rho.

## A6-4  Giu 5 seed

Power analysis: `sd_between_seed_max_ms = 0.354`, nen n=2 da du de phan biet gap
4.72 ms. Van giu 5 seed vi seed nuoi band du cua Phase 21R; giam seed sau khi
nhin pilot de tiet kiem thoi gian la khong dang.

## A6-5  Ha tang sach

Pilot co `42/42` diem qua gate. `sd_between_seed` gan `se_batch_mean`, vi du:

| diem | sd_between_seed | se_batch_mean |
|---|---:|---:|
| h2 rho=0.80 | 0.212 | 0.263 |
| poisson rho=0.95 | 0.354 | 0.307 |
| h2 rho=0.95 | 0.262 | 0.279 |

Bien thien giua lan chay duoc giai thich boi bien thien noi tai cua hang doi,
khong thay dau hieu nhieu ngoai.

## A6-6  H2 lech duong nho va co he thong

H2 lech duong o ca 6 diem rho, trung binh khoang `+0.143 ms`. Mot phan la offset
kich thuoc goi `+0.0215 ms`, phan con lai la sai so bac hai cua mo hinh
token-bucket. Ghi lai, khong sua; no thuoc band du cua `link_model_v2`.

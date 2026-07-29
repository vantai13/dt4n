# AMENDMENT 2 -- Phase L

Ngay: 2026-07-29   Commit truoc: 3578842

## DA THAY SO NAO TRUOC KHI SUA

results/phase-L/l2_probe_0729_0748.json (lan chay FAIL, GIU LAI lam bang chung):

```text
V-L2b lech mot goi o moi bw.
Vi du bw=6, k=3: du doan -0.117 ms (AM), do duoc 2.172 ms.
```

results/phase-L/l2_probe_0729_0803.json (lan chay PASS sau khi sua cong thuc):

```text
V-L0 floor mean=0.1492 ms, sd=0.1335 ms, p99=0.3449 ms, max=4.1551 ms.
V-L2 zero-load means: bw8=0.1283, bw6=0.1265, bw4=0.1435 ms.
V-L2b max err k>=3: bw8=0.1547, bw6=0.1674, bw4=0.1376 ms.
```

## A2-1  SUA LOI DAI SO TRONG CONG THUC BAC THANG  (KHONG phai HARKing)

```text
CU  (sai) : d_k = ((k-2)*L - B)/C
MOI (dung): d_k = ((k-1)*L - B)/C   voi k >= 3 ; d_1 = d_2 = 0
```

Suy dien doc lap voi du lieu:

```text
T(t) = muc token (byte), tran B, tang deu toc do C.
Dieu kien nha goi (kernel htb_class_mode): T >= 0, KHONG phai T >= L.
T(0) = B.
goi 1: T = B >= 0            -> nha t=0, T <- B - L
goi 2: T = B - L = 88 >= 0   -> nha t=0, T <- B - 2L  (am)
goi k>=3: sau khi nha goi k-1 thi T = B - (k-1)L < 0,
          tang toc do C, cham 0 tai t_k = ((k-1)L - B)/C
```

Kiem bien k=3, bw=6:

```text
(2*1512 - 1600) / 750000 = 1.8987 ms
```

Bang so da tien dang ky o Amendment 1 KHONG DOI:

```text
bw=6: 0.000 0.000 1.899 3.915 5.931 7.947 9.963 11.979
```

Bang nay duoc tinh bang mo phong, khong bang dong cong thuc sai. Do do
du doan chua he thay doi; chi co dong chu mo ta cong thuc la sai. Day la
sua loi dai so, khong phai HARKing.

## A2-2  V-L2b nang cap tu PASS/FAIL thanh PHEP DO CO SO

Hoi quy:

```text
d_k = a*k + b, k=3..8
C = L/a
B = -b*C - L
```

Ket qua tren du lieu 0729_0803:

| bw danh nghia | C do duoc | sai so | B do duoc | sai so | R2 |
|---:|---:|---:|---:|---:|---:|
| 8.000 Mbps | 8.0164 Mbps | 0.20% | 1649 B | 3.1% | 0.99939 |
| 6.000 Mbps | 5.9969 Mbps | 0.05% | 1680 B | 5.0% | 0.99966 |
| 4.000 Mbps | 3.9907 Mbps | 0.23% | 1635 B | 2.2% | 0.99993 |

Y nghia: probe xac nhan doc lap rang `tc` cau hinh dung cai no bao cao.
Nguong regression test: |dC|/C < 1%, |dB|/B < 10%, R2 > 0.999.

## A2-3  BAC BO DINH LUONG GIA THUYET SERIALIZATION

```text
H0 (link noi tiep): OWD(tai 0) = san + 0.848/bw ms
H1 (token bucket) : OWD(tai 0) = san, khong phu thuoc bw
```

Dung san mean = 0.149 ms:

| bw | H0 du doan | H1 du doan | do duoc |
|---:|---:|---:|---:|
| 8 | 0.255 ms | 0.149 ms | 0.1283 ms |
| 6 | 0.290 ms | 0.149 ms | 0.1265 ms |
| 4 | 0.361 ms | 0.149 ms | 0.1435 ms |

```text
H0 du doan khoang cach bw4-bw8 = 0.106 ms
Do duoc                            = 0.0152 ms
Bien thien giua cac lan chay       ~ 0.022 ms
```

Ket luan: H0 bi bac bo. H1 duoc xac nhan bang so, khong chi bang lap luan
ma nguon kernel.

## A2-4  SAN NHIEU -- quy tac bao cao

- Khong bao cao `max`; dung o p99. San co mot gia tri lac 4.155 ms.
- San dong gop khoang 0.35 ms vao p99 cua moi phep do.
- San phai do >= 5 lan, bao cao mean +- CI95.
- San phai do lai o dau va cuoi moi phien chien dich de chan troi.
- Khi dung link_model_v2: tru san khoi trung binh do duoc, ghi ro gia tri da tru.
- Khong dieu tra chenh lech nho hon bien thien giua cac lan chay ~0.02 ms.

## A2-5  PROVENANCE DU LIEU THO

```text
CU : reservoir sampling 2000 mau cho cac diem khong luu raw
MOI: giu toan bo raw
```

Quy tac:

- Raw `.bin` khong vao git.
- `results/phase-L/raw/MANIFEST.sha256.json` vao git.
- Cuoi Phase L: dong goi raw thanh tar.gz, upload Zenodo, dien DOI vao
  manifest va gate decision.

Ly do: don gian hon, an toan hon, va Phase 21R can tung mau de tinh residual
conformal.

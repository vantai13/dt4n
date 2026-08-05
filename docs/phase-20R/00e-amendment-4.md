# AMENDMENT 4 -- Phase 20R.4: thay doi giua chien dich va hang so sentinel cu

Ngay: 2026-08-05

## A. Thay Doi Code Giua Chien Dich

Chien dich full chua hai commit trong provenance:

```text
65f15ec  2026-08-04 09:03  Phase 20R.4: freeze campaign start
c4a0704  2026-08-05 01:24  Phase 20R.4: add campaign point watchdog
```

Pham vi thay doi:

```text
measurements/l6_campaign_fine.py    | 131 +++++++++++++++++++++++++++++++++---
test/test_phase20r_campaign_grid.py |  16 +++++
2 files changed, 139 insertions(+), 8 deletions(-)
```

Diff doi voi cac file do that va mo hinh do rong:

```text
measurements/l6_campaign.py
measurements/load_gen.py
measurements/owd_probe.py
mininet/
twin/
```

Trong cac file tren, diff giua `65f15ec` va `c4a0704` la rong. Tim cua phep
do, `L6.measure(net, point)`, khong doi. Thay doi o `c4a0704` chi boc loi goi
do bang watchdog `deadline()` dua tren `ITIMER_REAL`, them cleanup khi point
bi treo, va them test cho behavior nay.

Voi diem do thanh cong, `SIGALRM` khong duoc gui, nen duong di phep do giong
truoc. Day la operational robustness, khong phai measurement semantics.

Bang chung thuc nghiem tren sentinel:

```text
SENTINEL tach theo commit (A/B test cho watchdog):
  65f15ec0  n=13  mean=10.865892  sd_pop=0.011970  sd_sample=0.012459
  c4a0704b  n= 6  mean=10.872600  sd_pop=0.017931  sd_sample=0.019643
  diff = +0.006708 ms   se = 0.008038   z = +0.83   OK
timeout_history: 0
```

Ket luan: `|z| < 2`, khong phan biet duoc hai commit bang sentinel. Ly do
them watchdog la mot so diem co the treo o teardown/PTY Mininet; ket qua cuoi
cung co retry `4/609 = 0.66%`, `failed_rows = 0`.

## B. SENTINEL_REF La Hang So Cu

`measurements/l6_campaign.py` truoc do hardcode:

```text
mean_ms = 10.751
sd_ms   = 0.212
```

Day la hang so pilot truoc Phase L, chua cap nhat sau khi Phase L chay xong.
So lai voi du lieu that:

```text
Phase L  sentinel (seed 999, h2|6|13, n=23):
  mean = 10.874913271091032 ms
  sd   = 0.012231184552304 ms  (sample)

Phase 20R sentinel (n=19):
  mean = 10.868010439445086 ms
  sd   = 0.014863659240588 ms  (sample)

Phase 20R - Phase L:
  diff = -0.006902831645945 ms
  se   = 0.004258196579511 ms
  z    = -1.621069
```

Ket luan: ha tang khong drift co y nghia thong ke giua Phase L va Phase 20R.
19 diem sentinel co z duong so voi reference cu chi vi reference cu bi lech
thap va sd cu qua rong.

Hanh dong: cap nhat `SENTINEL_REF` cho cac phase sau bang gia tri Phase L
exact. Ban lam tron la `(10.8749, 0.0120)`, nhung dung exact de tranh fail
gia o bien 3 sigma:

```python
SENTINEL_REF = {
    "mean_ms": 10.874913271091032,
    "sd_ms": 0.012231184552303593,
    "source": "results/phase-L/campaign_state.json, seed=999, h2|6|13",
    "note": "Gia tri cu (10.751, 0.212) la hang so pilot truoc Phase L. "
    "Voi sd = 0.212, mot drift 0.5 ms KHONG bi phat hien.",
}
```

Khong sua nguoc du lieu Phase 20R. Chien dich PASS theo ca reference cu va
reference Phase L that. Rui ro da chan cho tuong lai: `sd = 0.212` rong gap
khoang 17 lan do on dinh that, nen drift 0.5 ms co the khong bi phat hien.

## C. Vi Pham Don Dieu O CBR

Mot so cap ke cua `cbr` giam rat nho khi rho tang:

```text
cbr 6|13  rho=0.60 -> 0.65: 0.138170 -> 0.137388 ms
cbr 8|18  rho=0.60 -> 0.65: 0.143485 -> 0.129656 ms
```

Bien do nam duoi 2% san nhieu `0.4646 ms` va duoi 1% khe cost `2.21 ms`.
Nguyen nhan la CBR duoi bao hoa gan nhu khong co hang doi; delay xap xi mot
hang so quanh `0.13 ms`, nen thu tu tang/giam theo rho chi la dao dong do.

Day khong phai loi do. No la bang chung bo sung cho luan diem PC1:
`cbr` la doi chung duong ky vong `err = 0`, va da bi loai khoi gate tu
Amendment 1 va Amendment 2.

## D. Continuity CBR So Voi Phase L

Ba diem continuity cua `cbr` deu lech am nho so voi Phase L:

```text
cbr 4|10 rho=0.70: diff = -0.002974650 ms
cbr 6|13 rho=0.80: diff = -0.002578307 ms
cbr 8|18 rho=0.80: diff = -0.003357113 ms
```

Sign test `p = 0.125`, chua co y nghia. Bien do khoang `0.6%` san nhieu
`0.4646 ms`. Ghi nhan de theo doi, khong hanh dong.

## E. Truth Table Va Kiem Noi Suy Sau Khi Build

Ghi chu sau do: Section nay ghi lai ket qua cua mot check ad-hoc sai thu tuc.
Amendment 5 thay the ket luan cua Section E: ngan sach noi suy DAT sau khi
dung RMS, tru nhieu theo phuong sai, va chia 4 de quy tu nhip `2h` ve nhip `h`.

Bang tra duoc build lai sau amendment bang dung mien rho da ky trong
`04-campaign-grid.md`, khong giu cac diem Phase L ngoai mien 20R:

```text
truth rows          : 176
source phase-L      : 58
source phase-20R    : 118
so o (mode,bw,q)    : 9
n_seed min          : 5
truth_field metadata: q_mean_ms
```

Kiem tra ngan sach noi suy tuyen tinh voi nguong `0.0465 ms`:

```text
cbr      bw=4 q=10  0.0082 ms
cbr      bw=6 q=13  0.0080 ms
cbr      bw=8 q=18  0.0099 ms
h2       bw=4 q=10  0.1527 ms  VUOT
h2       bw=6 q=13  0.1221 ms  VUOT
h2       bw=8 q=18  0.0589 ms  VUOT
poisson  bw=4 q=10  0.2023 ms  VUOT
poisson  bw=6 q=13  0.3016 ms  VUOT
poisson  bw=8 q=18  0.2463 ms  VUOT
```

Ket luan cu cua check ad-hoc nay bi supersede boi Amendment 5. No khong phai
bang chung bang tra qua tho; no so mot uoc luong co nhieu voi mot ngan sach
danh cho dai luong that, lai dung max tren nhip `2h`.

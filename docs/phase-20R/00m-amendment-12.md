# AMENDMENT 12 -- Sua thuoc do cua 20R.6, khong sua gia thuyet

Ngay: 2026-08-07
Trang thai: ky truoc khi chay lai phan tich offline bang estimator bg.

## 1. Su Kien Kich Hoat

Chay B2, branch A', 30 run, 0 gate fail. Quy tac dung som cua Amendment 11
kich hoat: `topology_transfer_pass = false`. Da dung dung theo quy tac, chua
chay branch B/C.

Doc lai artifact cho thay fail khong phai do he thong/topology hong, ma do
thuoc do A' khong cung ho voi branch A:

```text
Branch A  = truth table do tren luong TAI/background
Branch A' = state live cu tinh loss/cost tren luong PROBE rieng
```

## 2. Nguyen Nhan Goc

RC1 -- estimator mismatch:

`l6_campaign.py` va truth table dung `bg = analyze(*_bg.bin, *_bgtx.bin)`.
`additivity_live.py` ban dau tinh loss/cost cua A' tu luong probe rieng. Voi
tai `h2`, PASTA khong ap dung; packet-average cua luong tai va time-average
cua probe la hai dai luong khac nhau.

RC2 -- khong du power:

Probe 5 pps x 70 s chi con khoang 300 goi sau warmup. Sai so nhi thuc cua
loss, sau khi nhan voi `w_loss = 3222..4516 ms`, lon hon margin `0.44 ms`
hang chuc den hang tram lan. Tang probe rate de sua power lai vi pham
`probe_intrusion <= 2%`.

RC3 -- stale constant:

`delta = 0.44 ms` la hang so phai sinh tu phase cu. Dinh nghia goc la `20%`
khe cost quyet dinh. Trong 20R, `w_loss` da duoc hieu chuan lai nen khe cost
phai tinh tai runtime theo `(mode, rho_bar)`.

## 3. Sua Gi

S1. A'/B link-level duoc rescore bang luong tai bg, khong chay lai Mininet.
File raw `*_bg.bin` va `*_bgtx.bin` da co tren dia. Script:

```text
measurements/additivity_rescore.py
```

S2. Analyzer tinh equivalence margin tai runtime:

```text
delta_path = 0.20 * measured_cost_gap_ms(mode, rho_bar)
delta_link = delta_path / 3
```

`A' - A` va `B - A'` dung `delta_link`; `C - sum(B)` dung `delta_path`.

S3. Bao cao ba contrast rieng:

```text
cost  : don vi ms, delta theo cost gap
delay : don vi ms, delta theo cost gap
loss  : don vi fraction, delta = 0.005
```

## 4. Khong Sua Gi

- Khong doi gia thuyet G6.
- Khong doi `rho_bar`, mode, seed, topology, qdisc.
- Khong bo diem nao.
- So do bang probe duoc giu lai trong state moi thanh `probe_loss`,
  `probe_cost_ms`, `probe_delay_ms` de lam doi chung PASTA.

## 5. Du Doan Truoc Rescore

```text
delta_pasta = delay_bg - delay_probe: duong voi h2, gan 0 voi poisson.
A' - A (bg) cua h2: trong +-20.53 ms path, tuc +-6.84 ms/link.
A' - A (bg) cua poisson: co the van vuot +-0.50 ms/link tren L2/L3.
```

Neu poisson van lech, dieu tra theo thu tu: `rho_actual`, noi suy truth table,
CPU/timing. Khong noi nguong hau nghiem.

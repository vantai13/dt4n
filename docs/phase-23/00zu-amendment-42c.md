# AMENDMENT 23-42c -- Lesson 23.8[A0]: sua control kiem chuan sai dai luong

Ngay: 2026-08-22
Trang thai: **SAU hai lan calibration-only A0; TRUOC topology_v7 outcome,
TRUOC A1--A5, va TRUOC khi sua lai instrument-calibration scorer.**

## 1. Hai MISS calibration-only

Hai artifact duoc giu nguyen:

```text
results/phase-23/a0_instrument_calibration_attempt1.json
results/phase-23/a0_instrument_calibration_attempt2.json
```

Attempt 1 dat `t_obs` sau GET va dung 20 Thing, trai voi pseudocode NC-do-1
va them batch-width khong duoc khoa. Attempt 2 sua hai sai lech implementation:

```text
M-68 cu : mean=1.010392 s, max=1.011232 s -> MISS nguong max 1.010 s
NC-do-2 : d xap xi 0.010 s, CV=0.557663 -> MISS dai 0.44..0.52
M-69    : max AoI=14.997816 s -> HIT
```

Khong artifact nao doc rho, certificate outcome, lift, swing, Delta, hoac bat
ky ket qua topology_v7 nao.

## 2. Loi dai luong cua M-68

Pseudocode dat `t_fake = now-1s`, sau do cho PATCH ack, roi moi dat `t_obs`.
Do do:

```text
AoI = t_obs - tSource = 1 s + PATCH latency + timestamp quantisation
```

Nguong `<=1.010 s` dong thoi gate do chinh xac timestamp va hieu nang PATCH;
mot PATCH 10.4 ms lam MISS du timestamp khong co offset. Control dung cho duong
timestamp la dong nhat thuc:

```text
R_ts = (t_obs - tSource_readback) - (t_obs - t_fake)
     = t_fake - tSource_readback
```

Voi `round(...,6)`, khoa truoc khi chay lai:

```text
M-68b  max |R_ts| <= 0.001 ms
```

M-68 goc van duoc bao cao MISS; M-68b khong doi no thanh HIT.

## 3. Loi dai luong cua NC-do-2

Neu `AoI ~ Uniform[d,d+T]` thi:

```text
mean = d + T/2
sd   = T/sqrt(12)
CV   = T/sqrt(12) / (d + T/2)
```

CV chi xap xi 0.48 khi `d` xap xi 51 ms. Calibration attempt 2 do
`min=11.46 ms`; CV ly thuyet luc do xap xi 0.55, khop `0.557663`. Vi vay
`CV in [0.44,0.52]` khong phai control shape doc lap voi tham so.

Thay bang hai control shape khoa truoc khi scorer chay lai, voi `T=0.5 s`:

```text
NC-do-2a  p95 - p05 in [0.42, 0.48] s
          (Uniform co population spread = 0.90*T = 0.45 s)

NC-do-2b  |CV_observed - CV_expected| <= 0.03
          d_hat = max(0, p05 - 0.05*T)
          CV_expected = T/sqrt(12)/(d_hat + T/2)
```

CV goc van duoc bao cao va prediction goc van la MISS. Control moi chi tra loi
cau hoi no duoc dinh do: shape co phai rang cua uniform khi full push hay khong.

## 4. Stop rule sua

```text
M-68b MISS                  -> DUNG, duong timestamp co offset/quantisation.
NC-do-2a hoac 2b MISS       -> DUNG, rang cua sai khi full push.
M-69 MISS                   -> rut VD-2.
Tat ca control sua HIT      -> duoc tiep tuc A1--A3.
```

Khong sua M-66, M-67, M-69; khong thay doi system outcome hay campaign grid.

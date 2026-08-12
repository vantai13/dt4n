# AMENDMENT 6 -- Phase 21R

Ngay ky: 2026-08-12
Nguoi ky: Codex theo yeu cau owner repo DT4N
Boi canh: sau khi chay `cert/usefulness_v2.py`.
Day la ket qua chinh cua phase.

## F1. H7 dat tren cell chinh

Cell `poisson@0.925`, tap TEST:

```text
n_test = 499967
anchor_err_declared = 0.220835
anchor_err_on_test  = 0.222399
```

H7 dung anchor tren tap TEST.

| kappa | accept rate | err\|accept | err/anchor_test | d_sla\|accept | regret\|accept | err\|reject |
|---:|---:|---:|---:|---:|---:|---:|
| 0.00 | 1.00000 | 0.222399 | 1.000 | 0.060752 | 1.7675 | -- |
| 0.25 | 0.78784 | 0.159862 | 0.719 | 0.039620 | 1.1190 | 0.45463 |
| 0.50 | 0.58551 | 0.103373 | 0.465 | 0.023434 | 0.6551 | 0.39054 |
| 0.75 | 0.41270 | 0.063964 | 0.288 | 0.013662 | 0.3740 | 0.33373 |
| 1.00 | 0.28354 | 0.032992 | 0.148 | 0.005904 | 0.1762 | 0.29736 |
| 1.25 | 0.18716 | 0.015784 | 0.071 | 0.002276 | 0.0804 | 0.26997 |
| 1.50 | 0.12114 | 0.007380 | 0.033 | 0.000908 | 0.0293 | 0.25204 |
| 2.00 | 0.04845 | 0.000867 | 0.004 | 0.000000 | 0.0019 | 0.23368 |
| 3.00 | 0.00747 | 0.000000 | 0.000 | 0.000000 | 0.0000 | 0.22407 |

```text
H7: accept >= 0.10 VA err|accept <= 0.5 * anchor_test = 0.111199
so diem thoa = 5
diem co acceptance lon nhat: kappa=0.50, accept=0.5855, err=0.1034 = 0.465*anchor
G12: accept(kappa=1) = 0.28354 <= 0.90  DAT
```

Bootstrap theo block:

```text
kappa=0.5: accept CI95 [0.5711, 0.6005], err|accept CI95 [0.0961, 0.1112]
kappa=1.0: accept CI95 [0.2687, 0.2987], err|accept CI95 [0.0281, 0.0380]
```

## F2. So sanh voi Phase 21 v7

Baseline v7 ke thua tu audit/lesson: `P(accept)=0.05726`, `err|accept=0.033897`,
`anchor=0.18682`.

| Method | Acceptance rate | err\|accept | Anchor | err/anchor | Gain accept |
|---|---:|---:|---:|---:|---:|
| v7, s_vs_a1, eps=0 | 0.05726 | 0.033897 | 0.18682 | 0.1814 | -- |
| 21R, kappa=1 | 0.28354 | 0.032992 | 0.222399 | 0.1483 | 4.95x |
| 21R, kappa=0.5 | 0.58551 | 0.103373 | 0.222399 | 0.4648 | 10.23x |

Headline:

```text
O cung muc rui ro tuong doi khoang 0.15x diem neo, phuong phap moi chap nhan
so quyet dinh gap gan 5 lan v7.
```

## F3. Cong loc phan biet duoc

| kappa | err\|accept | err\|reject | Ratio reject/accept |
|---:|---:|---:|---:|
| 0.25 | 0.159862 | 0.454625 | 2.84x |
| 1.00 | 0.032992 | 0.297358 | 9.01x |
| 2.00 | 0.000867 | 0.233679 | 269.56x |

Neu cong loc chi chon ngau nhien thi `err|accept ~= err|reject ~= 0.222`.
Thay vao do, cac ca sai bi don vao tap reject. Ket luan: twin biet no khong
biet.

## F4. d_sla va regret giam nhanh hon err

Tai `kappa=1`:

```text
err    : 0.222399 -> 0.032992   giam 6.7x
d_sla  : 0.060752 -> 0.005904   giam 10.3x
regret : 1.7675   -> 0.1762 ms  giam 10.0x
```

Cong loc khong chi loai loi; no loai loi dat truoc tien. Quyet dinh duoc chap
nhan co khe `m_hat` rong, nen ngay ca khi sai chung thuong sai it.

Amendment 1 A3 duoc xac nhan: `regret|accept(kappa=1)=0.1762 ms`, nho hon
`eps_regret=3.2222 ms` khoang 18.3 lan. C2 khong rang buoc o diem chung nhan.

## F5. Suy dien sau chon loc

Tai `kappa=1`, cell chinh:

```text
P(s_margin > q_hat)                 = 0.091316
P(s_margin > q_hat | accept)        = 0.121435
inflation                           = 1.3298x
P(m_true < 0)                       = 0.213514
P(m_true < 0 | accept)              = 0.030741
median(m_hat - q_hat | accept)      = 7.6171 ms
corr(s_margin, m_hat) tren TEST     = 0.1122
```

Bao phu conformal marginal khong tu dong chuyen sang tap con duoc chon; sau
chon loc, ti le vi pham coverage tang qua alpha. Day la vi pham that va phai
bao cao.

Nhung tuyen bo van hanh van giu: xac suat `m_true < 0` tren tap accept chi
`0.0307`, thap hon alpha rat xa. Ly do: accept co `m_hat >= q_hat`, trong khi
that bai quyet dinh can `s_signed > m_hat`, khong chi `s_margin > q_hat`.

Khong viet "conformal dam bao 90% tren tap duoc chap nhan". Cau do sai. Phan
sua sau chon loc de Future Work / Phase 22.

## F6. G10 va PC1

Tat ca 3 cell khong suy bien thoa H7:

| Cell | Best kappa | Acceptance | err\|accept | err/anchor_test | H7 |
|---|---:|---:|---:|---:|---|
| poisson@0.925 | 0.50 | 0.5855 | 0.1034 | 0.465 | PASS |
| poisson@0.850 | 0.50 | 0.5490 | 0.0943 | 0.427 | PASS |
| h2@0.700 | 0.50 | 0.7467 | 0.0532 | 0.421 | PASS |

```text
G10: >= 2 che do khong suy bien thoa H7  DAT
```

Positive control:

```text
cbr@0.700: q_hat ~ 0.007, accept(kappa=1)=1.0000, err|accept=0
PC1 DAT
```

`G12` khong dung de danh gia PC suy bien; acceptance 100% la hanh vi mong doi
khi err neo bang 0.

## F7. Xac nhan kappa khong thu nguyen

| Cell | q_hat bins | accept at kappa=1 |
|---|---:|---:|
| poisson@0.850 | 3.184 / 4.278 / 5.373 / 6.712 | 0.2409 |
| h2@0.700 | 6.820 / 8.856 / 11.003 / 13.541 | 0.4966 |

`h2@0.700` co q_hat lon hon nhung acceptance cao hon, vi khe quyet dinh cung
rong hon. Dung `kappa` khong thu nguyen la lua chon dung; dung nguong cong-tru
theo ms se mo bac tu do theo tung che do.

## F8. Tu vung bat buoc

```text
coverage (conformal)        = P(score <= q_hat)  ~ 0.90
acceptance rate (selective) = P(accept)          ~ 0.28 tai kappa=1
```

Trong paper, dung "coverage" cho conformal va "acceptance rate" cho selective
prediction.

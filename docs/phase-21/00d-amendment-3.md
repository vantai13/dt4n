# AMENDMENT 3 - Phase 21, truoc Lesson 21.3

Ngay: 2026-07-28
Trang thai truoc sua: Lesson 21.2, commit `3190b27`

## Da Thay So Nao Truoc Khi Sua

Nguon: Lesson 21.2 tren du lieu that.

```text
offered:
  eta2(z)       = 0.1239
  eta2(u)       = 0.0211
  eta2(z x u)   = 0.1349
  H1 ratio      = 2.074
  4/4 CI99.75 loai tru 0

measured:
  eta2(z)       = 0.0448 tren 2 bin
  eta2(u)       = 0.0498 tren 4 bin
  eta2(z x u)   = 0.0885

risk-coverage IN-SAMPLE:
  cov 0.0543 -> err 0.0333
  anchor cov 1.0000 -> err 0.1820
```

## A3.1. Nhom Mondrian Chinh

Cu:

```text
(z x u) la co-primary
```

Moi:

```text
CHINH = 1 chieu, 5 bin tuoi z
PHU   = 2 chieu, 5 x 4 o, bao cao trong phu luc
```

Ly do:

```text
eta2(u) = 0.0211 < 0.05
them u chi tang eta2 tu 0.1239 len 0.1349 (+0.011)
5 o thay vi 20 o -> n_g lon hon, q_hat on dinh hon, phat bieu don gian hon
```

Bao cao ca hai. Neu 2 chieu cho `P(accept)` cao hon dang ke tren D_test, ghi ro
va giai thich vi sao van chon 1 chieu lam chinh.

## A3.2. Bien The q_hat

Bao cao ca ba:

```text
(A) mot mau ngau nhien moi (block, o), seed 7100
(B) gop het mau, muc phan vi = ceil((n_blk+1)(1-alpha))/n_blk
(C) max cua s trong moi block
```

Quy tac chon chinh, ghi truoc khi do bao phu:

```text
chon bien the co |bao phu bien - muc tieu| nho nhat trong so cac bien the
thoa H4. Neu hoa, chon (A).
```

Voi (B), muc tieu la muc phan vi huu han-mau cua block split, khong phai 0.90
chinh xac. Tieu chi chon la tinh dung cua bao dam, khong phai `P(accept)`.

## A3.3. Doi Chung Duong V3

Cu:

```text
chia calib/test ngau nhien theo mau -> phai lam it nhat mot o lech > 0.05
```

Moi:

```text
V3 PASS <=> SD(bao phu | chia MAU) < 0.5 * SD(bao phu | chia BLOCK)
qua R = 200 lan chia moi loai
```

Ly do: chia theo mau lam hai nua cua cung block thong ke qua giong nhau. Ro ri
khong nhat thiet lam lech trung binh; no lam sup phuong sai va lam ta tin qua
muc vao uoc luong.

Bo sung V3c:

```text
leave-one-trace-out, hieu chuan tren 4 trace, test trace con lai, lap 5 lan.
V3c PASS <=> bien do bao phu qua 5 fold khong vuot 0.05.
Neu vuot: ghi vao Limitations nhu vi pham kha hoan doi o muc trace.
```

## Khong Sua

```text
alpha = 0.10
AGE_EDGES
U_EDGES
b_block / block physical length
ti le 50/50
seed 7000
score chinh s_vs_a1
ho tieu chi theo eps
H_C moi tu Amendment 1
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-28

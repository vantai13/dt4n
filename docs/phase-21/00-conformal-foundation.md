# PHASE 21.0 - Conformal Prediction Foundation

Ngay: 2026-07-27
Trang thai: ly thuyet nen cho Phase 22-23. Khong co code measurement trong
lesson nay.

Phase 20 la phep do mo ta: twin sai o muc quyet dinh bao nhieu. Phase 21-23
doi sang bai toan bao dam: khi nao controller duoc phep tin twin.

## 1. Bai Toan

Twin du doan `y_hat`, vi du delay/cost cua mot duong. Ta can mot khoang
`C(x)` sao cho:

```text
P(y_true in C(x)) >= 1 - alpha
```

Voi `alpha=0.1`, muc bao phu muc tieu la 90%.

Cac cach cu khong phu hop:

```text
Gaussian interval: y_hat +/- 1.96 sigma_hat
  -> sai neu loi khong chuan, doi xung, duoi nhe.
Bayesian posterior interval
  -> bao dam phu thuoc vao prior/model dung.
Bootstrap prediction interval
  -> chu yeu tiem can, khong phai bao dam mau huu han.
```

## 2. Loi Hua Cua Split Conformal

Split conformal cho bao dam:

```text
P(y in C(x)) >= 1 - alpha
distribution-free
model-agnostic
finite-sample
```

Gia dinh can thiet: du lieu calibration va diem test phai kha hoan doi
(`exchangeable`).

## 3. Thuat Toan Split Conformal

1. Chia du lieu thanh `D_train`, `D_calib`, `D_test`.
2. Tren `D_calib`, tinh nonconformity score:

```text
s_i = |y_i - y_hat(x_i)|
```

3. Lay phan vi:

```text
k = ceil((n + 1) * (1 - alpha))
q_hat = k-th smallest score among n calibration scores
```

4. Diem moi:

```text
C(x) = [y_hat(x) - q_hat, y_hat(x) + q_hat]
```

Neu `k > n`, dat `q_hat = +inf`. Thuat toan van dung, chi vo dung.

## 4. Vi Sao Hoat Dong

Neu `s_1, ..., s_n, s_{n+1}` kha hoan doi, hang cua `s_{n+1}` trong `n+1`
diem la deu tren `{1, ..., n+1}`. Do do diem test khong nam lon hon phan vi
`ceil((n+1)(1-alpha))` qua thuong xuyen hon `alpha`.

Bao dam cua conformal nam o thu hang, khong nam o gia dinh phan phoi. Day la ly
do cong thuc dung `(n+1)`, khong phai `n`.

## 5. Bien vs Co Dieu Kien

Conformal chuan cho bao phu bien:

```text
P(y in C(x)) >= 1 - alpha
```

Khong tu dong cho bao phu co dieu kien:

```text
P(y in C(x) | X = x) >= 1 - alpha for all x
```

Bay nay quan trong voi DT4N:

```text
90% trang thai de: bao phu 99%
10% trang thai gan bao hoa: bao phu 10%
bao phu bien van co the la 90%, nhung he thong nguy hiem
```

Day la phien ban muc-khoang cua luan diem Phase 20: chi so bien/muc gia tri co
the che giau loi tap trung o vung gan bao hoa.

## 6. Mondrian Theo Tuoi

Bao phu co dieu kien tai moi `x` la bat kha thi neu khong them gia dinh. Loi
thoat la bao phu theo nhom:

```text
P(y in C(x) | x in group g) >= 1 - alpha
```

Mondrian conformal lay phan vi rieng cho moi nhom:

```text
q_hat_g = conformal quantile of scores in group g
C(x) = y_hat(x) +/- q_hat_g(x)
```

Voi DT4N:

```text
group g = bin cua tuoi twin z
```

Ly do chon `z`:

```text
z quan sat duoc tai thoi diem quyet dinh
Phase 20 da do err(z) tang don dieu, 8/8 adjacent deltas CI99.4 > 0
z roi rac tu nhien tren rang cua 10 ms
```

## 7. Rang Buoc Bin

Voi moi bin `g`, can:

```text
n_g >= ceil(1 / alpha) - 1
```

Voi `alpha=0.1`, can toi thieu `n_g >= 9`; neu it hon, `q_hat=+inf`.

Trong thuc te nen nham `n_g >= 100` block/bin de phan vi on dinh.

## 8. Vi Pham Exchangeability Trong Trace

Phase 20 co `tau_core = 2.87 s`, `dt = 10 ms`. Hai mau gan nhau tuong quan rat
manh, nen mau theo thoi gian khong kha hoan doi o muc sample.

Cach chua chot cho Phase 22:

```text
block_len = round(5 * tau_core / dt) = 1435 samples = 14.35 s
gan nguyen block vao calib/test
khong cat giua block
```

Bao dam khi do phai phat bieu dung:

```text
coverage is claimed for exchangeable blocks of length 5 tau,
not for individual time samples inside a block.
```

Voi 5 trace, moi trace co khoang 100 block, tong khoang 500 block. Voi 5 bin
tuoi, ky vong khoang 100 block/bin.

## 9. Validation Bat Buoc Cho Phase 22

Chot truoc:

```text
V1 marginal empirical coverage gan 1 - alpha, sai lech < 2 diem phan tram
V2 coverage tung bin tuoi gan 1 - alpha
V3 positive control: chia calib/test ngau nhien theo sample, co y pha block
   -> ky vong bao phu lech ro so voi V1/V2
```

Neu V3 khong hong, co hai kha nang: du lieu it tuong quan hon tuong, hoac code
chua dung.

## 10. Noi Voi Phase 20 Va Phase 23

Phase 20 da do:

```text
err(z): 0 -> 0.073 -> 0.103 -> 0.146 -> 0.176 -> 0.223 -> 0.307 -> 0.419 -> 0.551
z:      0    0.05    0.10    0.20    0.298   0.50    1.0     2.0     4.0
```

Phase 22 phai sinh `q_hat(z)` tang theo tuoi va giai thich duoc `err(z)`.
Neu `q_hat(z)` phang trong khi `err(z)` tang manh, conformal khong bat duoc co
che hoac bi chi phoi boi nguon sai so khac.

Phase 23 trust gate:

```text
ACCEPT khi khoang cost cua action tot nhat tach khoi action con lai.
```

Du doan can ghi truoc Phase 22:

```text
coverage_gate(z) ~= P(cost_gap > 2 * q_hat_Bonf(z))
```

Cost gap Phase 20 co median khoang `1.08 ms`, p10 khoang `0.94 ms`. Neu
`q_hat(0.298) ~= 0.5 ms`, coverage gate co the quanh 50%. Neu
`q_hat(0.298) ~= 2 ms`, gate se rat bao thu va coverage thap.

# AMENDMENT 19 -- Phase T / T.6f dynamics-vs-instrumentation split

Ngay viet: 2026-08-03
Trang thai: T.6e paired-by-seed analysis da xong.

## Boi Canh

T.6e cho ket qua o 8 o khong phai cbr:

```text
err_dyn weighted = -0.0200 +/- 0.0046 ms
KTC 95%          = [-0.0290, -0.0110] ms
tan_du_doan / tan_quan_sat = 1.013
```

Thanh sai so ghep cap da sua mau thuan 4.52x cua T.6d. Tuy nhien, hieu ung
`-0.020 ms` dong nhat qua 8 o va D-T3 phang theo Lambda, nen van can phan biet:

```text
H_dong_luc : sai so quasi-static phu thuoc sigma_rho va Lambda
H_thiet_bi : offset cong tinh nho cua bo sinh tai khi rho(t) bien thien
```

Do lon `20 us` cung bac voi `Delta_hat = 15.8 us` cua Amendment 13, nen khong
duoc quy ket ngay la sai so quasi-static neu chua kiem tra scaling theo `a`
va `tau_rho`.

## Phep Kiem Phan Biet

Dung cac diem main khong phai cbr, tru baseline C cua cung o `(mode,rho_bar)`.
Sau do tach theo:

```text
a in {0.2, 0.9}
tau_rho in {0.2, 1.0, 5.0}
```

Neu la dong luc, `|err_dyn|` phai lon hon ro tai `a=0.9` so voi `a=0.2` va
lon hon khi `tau_rho` nho. Neu la chi phi thiet bi/offset cong tinh, cac nhom
nay phang trong do phan giai.

## Du Doan Truoc Khi Chay

```text
S1  err_dyn(a=0.2)                 : -0.020 +/- 0.007 ms
S2  err_dyn(a=0.9)                 : -0.020 +/- 0.007 ms
S3  ti so |a=0.9| / |a=0.2|        : khoang 1.0
S4  err_dyn tau=0.2 / 1 / 5        : -0.020 / -0.020 / -0.020 ms
S5  Ket luan nghieng ve            : thiet bi
```

Neu S3 gan 1 va S4 phang, khong duoc viet "sai so quasi-static = 20 us" nhu
ket luan dong luc. Phai viet dang can tren: `|err_quasi-static| < 0.029 ms`
tren dai on dinh, va hieu ung 20 us khong phan biet duoc voi offset thiet bi.

## Bao Cao Bat Buoc

T.6f phai bao cao:

```text
theo a:       n, mean, se, t cho a=0.2 va a=0.9, ti so |0.9|/|0.2|
theo tau_rho: n, mean, se, t cho tau=0.2, 1.0, 5.0
ket luan: dong_luc / thiet_bi / khong_phan_biet_duoc
```

`cbr@0.98` tiep tuc tach rieng, khong dung trong phep phan biet nay.

## Nguyen Tac Moi

NT-L22. Hieu ung duoc goi la "dong luc" phai scale theo truc dong luc cua
thiet ke. Neu phang theo `a` va `tau_rho`, no chi duoc bao cao nhu offset/can
tren tru khi co bang chung khac.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-03

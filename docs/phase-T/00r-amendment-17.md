# AMENDMENT 17 -- Phase T / T.6d cell-level D-T2 restatement

Ngay viet: 2026-08-03
Trang thai: T.6 confirmatory, T.6b baseline, va T.6c noise-floor diagnostic da xong.

## Boi Canh

T.6c da xac nhan: `se_batch_ms` cung bac hoac lon hon `sd_err_dyn_ms` trong
8 o khong phai cbr. `se_naive_ms` nho hon `se_batch_ms` nhieu lan do tu tuong
quan hang doi.

Ket luan: tieu chi D-T2 cu dung `sigma_ref ~ 0.17 ms`, nam duoi hoac cung bac
voi san nhieu `se_batch_ms`. Kiem tung diem do chu yeu do nhiễu cua phep do,
khong phai sai so quasi-static he thong.

## Trang Thai Phan Tich

A17 la **EXPLORATORY**.

Cac gia tri o Phan 1--2 cua huong dan T.6d da duoc tinh va hien thi truoc khi
amendment nay duoc viet. Do do Q1--Q6 ben duoi khong con mu. Chung duoc ghi
lai de khoa cach tinh, bao cao trung thuc, va tranh thay doi cach dien giai
sau khi chay script.

Ket qua confirmatory T.6 va exploratory T.6b/T.6c van phai duoc bao cao
nguyen ven. A17 chi bo sung cach phat bieu lai D-T2 o muc o.

## Sua Gi

A17.1. D-T2 duoc phat bieu lai o muc o, khong o muc diem:

```text
cu : |err_i| < sigma_i cho tung diem
moi: |mean_o(err_dyn)| < sigma voi moi o (mode, rho_bar)
```

A17.2. Bao cao hai bo thanh sai so:

```text
bao thu    : SE_tot = sqrt(SE_stat^2 + SE_C^2), trong so 1/SE_tot^2
thuc nghiem: do tan that giua 8 o khong phai cbr, t-test df=7
```

Neu hai bo thanh sai so khac nhau hon 2 lan, bao cao ti so va giai thich.

A17.3. Them kiem phi tham so tren dau cua 8 o khong phai cbr:

```text
sign test
Wilcoxon signed-rank
```

Ly do: hai phep kiem nay khong phu thuoc vao `SE_C`.

A17.4. Kiem mau thuan thanh sai so:

```text
ti_so = sqrt(mean(SE_tot^2)) / sd(mean_dyn giua 8 o)
```

Neu `ti_so > 2`, xem day la phat hien ve thanh sai so danh nghia, khong phai
phien toai ky thuat.

## Du Doan / Gia Tri Khoa Truoc Khi Chay Script

```text
Q1  So o mang dau am tren 8 o khong phai cbr : 8 / 8
Q2  Sign test p hai phia                     : 0.0078125
Q3  Mean khong trong so cua 8 o              : -0.0327 ms
Q4  KTC 95% cua mean do                      : [-0.0513, -0.0141] ms
Q5  Ti so thanh sai so A17.4                 : khoang 4.5
Q6  cbr@0.98 la o duy nhat co |t| > 2        : co
```

## Nguyen Tac Moi

NT-L17. Truoc khi so mot dai luong do duoc voi mot nguong, phai biet san nhieu
cua chinh dai luong do. Voi hang doi tu tuong quan, dung `se_batch_ms`, khong
dung `se_naive_ms`.

NT-L18. Khi thanh sai so danh nghia va do tan quan sat duoc lech hon 2 lan,
do la mot phat hien can bao cao.

NT-L19. Voi n nho va thanh sai so khong dang tin, kiem phi tham so tren dau
co gia tri chan doan rieng.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-03

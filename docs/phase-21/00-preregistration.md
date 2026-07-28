# PRE-REGISTRATION - Phase 21: Khoang du doan dieu kien-theo-tuoi

Ngay ky   : 2026-07-28
Git tag   : phase-21-start
Commit    : tag `phase-21-start` tro toi commit chot tai lieu nay
Tien de   : Phase 20 PASS (tag `phase-20-complete`)
Trang thai: CHOT. Sua doi sau ngay ky phai viet
            `docs/phase-21/00b-amendment-N.md` va ghi ro DA THAY SO NAO
            truoc khi sua.

## 0. Pilot Da Chay Truoc Khi Ky

Truoc khi chot tai lieu nay, mot pilot kha thi da duoc chay tren trace MO PHONG
AR(1) tu sinh:

```text
phi = exp(-dt/tau) = 0.99652
sigma = 0.010
LOAD_MEAN lay tu twin/topology_v7.py
```

Pilot nay KHONG dung 5 trace dong bang cua Phase 20. Muc dich la uoc luong bac
do lon cua `q_hat` va gap cost de thiet ke tieu chi, khong phai de kiem dinh
gia thuyet.

Ket qua pilot, chi dung lam feasibility, KHONG trich dan lam evidence:

```text
gap cost:   p10 0.920  p50 1.072  p75 2.033  p90 16.645 ms
            khop voi ghi chep cu p10 ~0.94, p50 ~1.08
s theo bin: p50 0.02-0.06 ms | p90 12.5-19.0 ms
P(separable) voi tieu chi 2*q_hat_{alpha/K} ~= 0.001
```

Hai quyet dinh thiet ke duoc dua ra tu pilot nay va duoc ghi truoc khi do tren
du lieu that:

```text
(i)  them score tren HIEU cost (P2b) lam CO-PRIMARY
(ii) them bien dieu kien u = khoang cach toi nguong (P4b) lam CO-PRIMARY
```

Ca hai co co so co che tu Phase 20, dac biet `risk_ratio = 8.94`, khong phai
mo nguong sau khi thay ket qua.

## 1. Ke Thua Tu Phase 20 - Khong Hieu Chuan Lai

```text
w_loss  = 1451.3766 ms/don-vi-loss
T_delay = 14.5138 ms
T_loss  = 0.010
tau_core= 2.87 s
b_block = 1435 mau = 14.35 s = 5*tau_core
EPS = EPS_REGRET = 1e-9, pha tie = chi so nho nhat
CHINH: 5 trace rho_offered_long{,_s1..s4}.csv
PHU  : 5 trace rho_measured_long{,_s1..s4}.csv
DUONG CO SO PHAI DANH BAI: err = 0.18233, d_sla = 0.07939
DIEM NEO FIG 3: coverage = 1.00 -> risk = 0.0794
```

## 2. Gia Thuyet

H_A. `q_hat(z)` tang theo `z`, va `q_hat(bin cuoi) / q_hat(bin dau) >= 1.5`.

H_B. Bao phu tung bin nam trong `(1-alpha) +/- 0.05`.

H_C. `0.10 <= P(accept) <= 0.90`. Day la gia thuyet giet. `P(accept)` do bang
tieu chi chinh P2b voi `eps = 0` trong P7.

Moi phan tich khac la EXPLORATORY.

## 3. Tam Quyet Dinh - P1 Den P8

### P1. Dai Luong Du Doan

```text
y     = cost_true(a) = delay_e2e(rho(t))   + w_loss * loss_e2e(rho(t))
y_hat = cost_twin(a) = delay_e2e(rho(t-z)) + w_loss * loss_e2e(rho(t-z))
```

Bien minh: cost la dai luong quyet dinh dua vao. Bao dam phai dat tren dai
luong gan quyet dinh nhat co the.

Ghi nhan: `link_model` tat dinh, nen toan bo sai so trong Phase 21 den tu
`rho` cu. Day la co y de co lap bien do cu. Sai so mo hinh danh cho Phase 24.

### P2. Diem Bat Tuan

Phase 21 co hai score confirmatory.

P2a, score tham chieu de so voi literature:

```text
s_abs(t,a) = |y(t,a) - y_hat(t,a)|
```

Bao cao:

```text
q_hat_alpha(bin)
q_hat_{alpha/K}(bin) voi Bonferroni
```

P2b, score CHINH dung cho gate:

```text
s_diff(t) = max over all pairs (a,b) of
            | (y(t,a)-y(t,b)) - (y_hat(t,a)-y_hat(t,b)) |
```

Bao cao:

```text
q_hat_diff(bin)
```

`s_diff` cho bao phu dong thoi moi hieu cost o muc `alpha` bang mot phan vi,
khong can Bonferroni. Ly do co che:

```text
1. topology_v7 co link chia se theo tap con, nen sai so common-mode triet tieu
   khi lay hieu.
2. max-score cho simultaneous coverage truc tiep tren dai luong gate can.
3. no luon chat hon hoac bang union bound khi cac cap cost tuong quan manh.
```

Du doan ghi truoc:

```text
q_hat_diff < 2*q_hat_{alpha/K} o moi bin
```

Khong dung `s_norm` trong phase nay. Neu dung sau nay, `sigma_hat` phai hoc tren
`D_train` rieng; khong duoc hoc tren `D_calib`.

### P2c. Cach Tinh q_hat O Muc Block

Chinh:

```text
(A) mot mau ngau nhien moi (block, o Mondrian), seed = 7100
    -> n_g = so block
    -> split conformal chuan, bao dam sach
```

Phu:

```text
(B) gop tat ca mau, phan vi o muc ceil((n_b+1)(1-alpha))/n_b
```

Bao thu:

```text
(C) max cua s trong moi block
```

Bao cao ca ba. Neu lech hon 10% giua cac cach tinh, dieu tra cau truc trong
block truoc khi dien giai.

### P3. Muc Tin Cay

```text
alpha = 0.10
coverage muc tieu = 90%
P2a can Bonferroni cho K=4: alpha/K = 0.025
P2b khong can Bonferroni vi max-score da cho simultaneous coverage
```

Kiem tra huong bat buoc:

```text
q_hat_{alpha/K} > q_hat_alpha
```

Bao cao `q_hat(alpha)` voi:

```text
alpha in {0.02, 0.05, 0.10, 0.20, 0.30, 0.50}
```

Day la exploratory, de lo ra vach da theo `alpha` neu co.

### P4. Nhom Mondrian

P4a, chieu tuoi:

```text
B1 [0.06,0.16)
B2 [0.16,0.26)
B3 [0.26,0.36)
B4 [0.36,0.46)
B5 [0.46,0.55]
```

P4b, chieu khoang cach toi nguong, CO-PRIMARY:

```text
sigma_z = 0.010 * sqrt(1 - exp(-2z/2.87))
u(t)    = min over links |rho_hat_link(t) - nguong gan nhat| / sigma_z
nguong  = {0.9250, 0.9325}
bin u   = U1 [0,1), U2 [1,2), U3 [2,3), U4 [3,inf)
```

Bien minh: Phase 20 do `risk_ratio = 8.94` voi bien `crossed`; `u` la phien
ban quan sat duoc tu twin cua bien do.

Rang buoc:

```text
n_g >= ceil(1/alpha) - 1 = 9 BLOCK moi o
muc tieu >= 50 block moi o
```

Quy tac gop, ghi truoc: o thieu block duoc gop voi o ke ben theo chieu `u`,
khong gop theo chieu `z`, vi `z` co co so ly thuyet manh hon.

Kiem tra o Lesson 21.1 truoc khi chay conformal.

Luu y da kiem chung:

```text
b_block = 1435 mau = 28.7 chu ky rang cua
moi block chua ca 50 gia tri tuoi
n_g theo chieu z = 500 block, khong phai 100
rang buoc >= 9 khong rang buoc theo chieu z, nhung co the rang buoc theo u
```

### P5. Chia Calib / Test

```text
Theo block b = 1435 mau.
Gan nguyen block.
Khong cat giua block.
Ti le: 50/50.
Hat giong chia: 7000.
```

Kiem chung doc lap phu:

```text
hieu chuan tren trace {0,1,2}
test tren trace {3,4}
```

### P6. Nguon Trace

```text
CHINH: rho_offered
PHU  : rho_measured
```

Ca hai deu bao cao. Khong chon nguon cho ket qua dep hon.

`rho_measured` co cua so 200 ms, nen phai dung `check_z_grid()` va che do
bracket de tranh aliasing tuoi. `rho_measured` la robustness/cross-check, khong
tron voi offered thanh mot con so.

### P7. Tieu Chi Co Ich - Ho Tieu Chi Theo eps

Tieu chi ACCEPT, dung P2b:

```text
gap_twin(t) = c_hat(nhi) - c_hat(tot nhat)
ACCEPT <=> gap_twin(t) >= q_hat_diff(g(t)) - eps
```

Suy ra tu chan tren regret:

```text
regret(a_hat) <= max(0, q_hat_diff(g) - gap_twin(t))
```

Chung minh nam trong `docs/phase-21/00-conformal-foundation.md` muc 11.

Y nghia:

```text
eps = 0      -> tieu chi tach roi, bao thu nhat
eps > 0      -> noi long co kiem soat
eps = inf    -> accept tat ca, quay ve diem neo Phase 20
```

Quet:

```text
eps = {0, 0.145, 0.725, 1.451, 2.9, 7.3, 14.5} ms
      = {0, 1%, 5%, 10%, 20%, 50%, 100%} cua T_delay
```

Moi `eps` cho mot diem tren duong risk-coverage cua Fig 3. Quet `eps` la hop
le vi day la tham so van hanh dat truoc; khong quet `alpha` de chon ket qua dep.

Gate H_C dung `eps = 0`:

```text
0.10 <= P(accept) <= 0.90
```

Bien minh hai phia:

```text
P(accept) < 0.10 -> gate abstain gan het
P(accept) > 0.90 -> gate accept gan het, gan nhu vo dung
```

Gap cost phai do o Lesson 21.1 tren du lieu that, khong lay tu pilot.

Loi trong ban nhap da sua:

```text
ub = (c[chosen] + q) - (c.min() - q)
```

Cong thuc nay thoai hoa thanh `2*q` vi `chosen = argmin`; no la hang so trong
moi bin va khong sinh duoc risk-coverage curve. Ngoai ra no dung `c` that,
khong kha thi luc controller quyet dinh.

### P8. Neu Fail Thi Sua Gi

Nhanh (a): `s(z)` phang, `eta^2 < 0.05`.

```text
Doi bien dieu kien u lam chinh, z lam phu.
Du lieu da co san tu P4b.
Ghi amendment, chay lai.
Toi da 1 lan.
```

Nhanh (b): `P(accept) < 0.10` tai `eps = 0`. Day la nhanh nguy hiem nhat va
la nhanh pilot du doan de xay ra.

```text
b1. Uu tien bao cao ca duong P(accept) theo eps thay vi mot diem.
    Neu ton tai eps <= 0.10*T_delay = 1.4514 ms cho P(accept) >= 0.10
    va risk tai do < 0.0794, thi GO.
b2. Dung Mondrian 2 chieu (z, u) day du thay vi chi z.
b3. Neu van fail, doi cau hoi paper:
    "khong ton tai khoang huu ich o alpha=0.10 tren che do nay".
    Bao cao nhu ket qua am co gia tri, kem duong q_hat(alpha) chi ra vach da.
    Neu can, mo Phase 21B tren che do vach da nhe hon voi prereg rieng.
```

Nhanh (c): `P(accept) > 0.90`.

```text
Tang K (topology nhieu duong hon) hoac siet nguong SLA trong phase moi.
Khong sua trong phase nay de lam ket qua dep hon.
```

Nhanh (d): bao phu sai, H3/H4/H6 fail.

```text
Day la loi hien thuc, khong phai ket qua khoa hoc.
Kiem theo thu tu:
1. cong thuc phan vi co dung (n+1) khong
2. co cat giua block khong
3. n_g dem block hay mau
4. calib/test co chung block khong
Khong chinh tham so cho bao phu dep len.
```

## 4. Doi Chung Bat Buoc

V1. Bao phu bien thuc nghiem:

```text
|do_duoc - (1-alpha)| <= 0.02
```

V2. Bao phu tung o Mondrian:

```text
|do_duoc - (1-alpha)| <= 0.05 moi o
```

V2b. Can tren:

```text
coverage khong duoc vuot (1-alpha) + 1/(n_g+1)
voi n_g = 250, tran = 0.9040
vuot tran = dau hieu ro ri, phai dieu tra
```

V3. Doi chung duong:

```text
chia calib/test ngau nhien theo mau, khong theo block
phai lam it nhat mot o lech > 0.05
neu khong lech: dung lai va dieu tra truoc khi tin ket qua chinh
```

V4. `q_hat` vo han check:

```text
moi o phai co n_g >= 9 BLOCK, neu khong thi RAISE
```

V5. Kiem chung noi tai:

```text
tinh lai err tu bang calib phai ra 0.18233
nguong khop: 1e-5
neu lech: bang xay sai, dung ngay
```

V6. Kiem tra huong:

```text
q_hat_diff < 2*q_hat_{alpha/K} o moi bin
```

## 5. Ngan Sach Lap

Toi da 2 vong sua. Moi vong chi sua mot thu (OFAT o cap thiet ke).

Truoc khi chay lai, viet amendment ghi ro DA THAY SO NAO.

Het 2 vong chua PASS thi dung, bao GVHD, va di theo nhanh P8(b3).

## 6. Rui Ro Da Biet

R1. Kha hoan doi van co the bi vi pham du da chia block. `b = 5*tau` giam
tuong quan nhung khong chung minh exchangeability tuyet doi. V3 se lo ra; neu
V3 bat thuong, mo amendment va can nhac `b = 10*tau`.

R2. Phan phoi `s` hai cuc do `link_model` la bac thang. Hau qua: `q_hat` o
`alpha = 0.10` co the bi chi phoi boi bien co vuot vach da. Day khong phai bug.

R3. San khau Q8 dat link loi ngay tren vach da:

```text
LOAD_MEAN loi 0.915-0.930
dai toi han 0.925-0.9325
sigma 0.010
```

Day la che do kho nhat co the: tot cho Phase 20 vi tin hieu manh, xau cho
Phase 21 vi it vung an toan.

R4. `link_model` tat dinh, nen sai so qua sach so voi thuc te. Giam nhe bang
cross-check tren `rho_measured`; sai so mo hinh de Phase 24.

R5. Chon bin sau khi nhin `s(z)` la HARKing. Chan boi P4.

R6. Mondrian 2 chieu chia nho `n_g`; mot so o co the thieu block. Chan boi V4
va quy tac gop da ghi trong P4.

## 7. Checklist Ky

```text
[x] alpha = 0.10
[x] score tham chieu = s_abs
[x] score chinh cho gate = s_diff
[x] split theo block 5*tau_core
[x] Mondrian theo age_bin z
[x] Mondrian 2 chieu (z, u) la co-primary
[x] gates H_A-H_C duoc chap nhan
[x] doi chung V1-V6 duoc chap nhan
[x] fail branches P8(a-d) duoc chap nhan
[x] pilot da khai bao la AR(1) mo phong, khong phai trace dong bang
[x] khong con placeholder hay lua chon mo
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-28

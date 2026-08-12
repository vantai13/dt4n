# AMENDMENT 1 -- Phase 21R

Ngay ky   : 2026-08-12
Nguoi ky  : Codex theo yeu cau owner repo DT4N
Trang thai: DA ky `00-preregistration.md` tai tag `phase-21R-start`.
            CHUA tinh bat ky `q_hat`, `s_margin`, hay ket qua nao tren tap seed
            da tien dang ky `{101,102,103,104,105}`.

## Vi sao co amendment nay

Ba van de duoi day duoc phat hien trong luc thiet ke `cert/margin_score.py`
(Lesson 21R.1), thuan bang suy luan toan hoc. Khong co ket qua thuc nghiem nao
tren seed da tien dang ky duoc quan sat truoc khi sua. Ca ba la mau thuan noi
bo hoac suy bien toan hoc cua ban tien dang ky, khong phai dieu chinh de dat
gate.

Bang chung kiem duoc: amendment nay duoc commit truoc bat ky file
`cert/build_calib_set_v2.py` dau tien.

## A1. He so trong C1: `2*q_hat` -> `1*q_hat`

Ban cu P7:

```text
C1 accept <=> gap_twin >= 2 * q_hat(z)
```

Van de: he so 2 chi dung khi `q_hat` duoc hieu chuan tren chi phi tung hanh
dong. P2 cua Phase 21R dinh nghia score tren BIEN quyet dinh:

```text
P(|m_true - m_hat| <= q_hat) >= 1 - alpha
=> m_true >= m_hat - q_hat
=> m_hat >= q_hat  ==>  m_true >= 0
```

Ban moi:

```text
C1 accept <=> m_hat >= 1 * q_hat(z)
```

Day la sua loi logic, khong phai noi long tuy tien. He so truoc `q_hat` do dai
luong ma `q_hat` duoc dat len quyet dinh.

## A2. Cong thuc C2 cu suy bien

Ban cu P7:

```text
accept <=> [c_hat(a_hat) + q_hat] - min_a[c_hat(a) - q_hat] <= eps_regret
```

Vi `a_hat = argmin_a c_hat(a)`, ve trai thanh:

```text
[c_hat(a_hat) + q_hat] - [c_hat(a_hat) - q_hat] = 2*q_hat
```

Do do tieu chi khong phu thuoc mau, chap nhan tat ca hoac tu choi tat ca.

Ban moi:

```text
ub_regret = max(0, q_hat(z) - m_hat)
C2 accept <=> ub_regret <= eps_regret
          <=> m_hat >= q_hat - eps_regret
```

Suy luan: regret tren cap `(a1,a2)` la `max(0, -m_true)` va
`m_true >= m_hat - q_hat`.

## A3. Tham so hoa khong thu nguyen cho C3

Ban cu P7 quet `eps` tinh bang ms. Van de:

```text
C1 = C3 tai eps = 0
C2 = C3 tai eps = eps_regret
```

`eps_regret(poisson@0.925) = 3.2222 ms`, trong khi `q_hat` du doan
`1.5-3.0 ms`, nen C2 co nguy co suy bien thanh chap nhan 100%. `eps` tinh
bang ms cung kho so sanh giua cac che do co thang cost khac nhau.

Ban moi:

```text
accept <=> m_hat >= kappa * q_hat(z)

kappa in {0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0}
```

Diem co ten:

```text
kappa = 0   -> diem neo, tin twin 100%
kappa = 1   -> C1, chung nhan
kappa = 2   -> quy uoc "khoang tach roi" cua v7, de so sanh lich su
kappa_C2(z) = max(0, 1 - eps_regret / q_hat(z))
```

Neu `kappa_C2 = 0`, bao cao ro rang C2 suy bien tai o do. Khong duoc giau vi
ban than do la mot ket qua: nguong SLA rong hon do bat dinh cua twin.

## A4. Cap nhat du doan `P(accept)`

Du doan cu dua tren nguong `2*q_hat`. Sau A1, nguong dung la `1*q_hat`.

```text
truoc: P(accept | C1) = 0.75 - 0.87
sau  : P(accept | C1, kappa=1) = 0.87 - 0.94
```

Co so chi tu twin, khong dung ground truth:

```text
P(gap >= 1.5 ms) ~ 0.936
P(gap >= 2.0 ms) = 0.915
P(gap >= 3.0 ms) = 0.872
```

He qua: gate 21R-G12 (`P(accept) <= 0.90`) nay nam ngay ranh gioi. Nhanh P10(c)
"accept gan het" tro thanh nhanh co xac suat cao nhat. Voi ho `kappa`, chi can
doc duong cong tai `kappa` lon hon; khong doi score/bin/cell.

Cac du doan khac giu nguyen:

```text
q_hat(B1) 1.5-2.2 ms
q_hat(B4) 2.0-3.0 ms
ti so     1.2-1.6
z_cross   0.05-0.10 s
anchor    0.27-0.31
```

## A5. Them score phu mot phia

P2 da co muc score phu. Bo sung:

```text
s_signed = m_hat - m_true
q_hat_one = quantile_{1-alpha}(s_signed)
```

Ly do: dai luong quyet dinh chi can chan mot phia `m_true >= 0`. Duoi vo hai
la twin bi quan (`m_true > m_hat`). Toan hoc:

```text
s_signed <= abs(s_signed) = s_margin
=> q_hat_one <= q_hat_two
```

Score chinh van la `s_margin` hai phia. `s_signed` bao cao song song, khong
thay the ket qua chinh.

## A6. Chan doan moi can bao cao

Bo sung vao cac lesson sau:

```text
pair_is_true_contender theo (mode, z_bin) -> rui ro R2
p90(s_margin)/p90(s_vs_a1)                -> loi tu viec thu hep K-1 -> 1
p90(s_margin)/p90(s_maxabs)               -> muc common-mode thuc su
q_hat_delay va q_hat_loss*w_loss          -> tach kenh theo audit Bang 2
```

## Ghi chu ve tinh toan ven

Khong muc nao trong amendment nay dua tren ket qua tren seed tien dang ky. A1
lam C1 de dat hon vi sua logic, nhung no cung lam G12 kho dat hon. A3 loai bo
hai diem suy bien va giu ket qua chinh la duong risk-coverage, nay quet theo
`kappa`.

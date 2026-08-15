# AMENDMENT 23-10 -- Lesson 23.2 threshold-family audit

Ngay: 2026-08-14

Ly do: Lesson 23.1 cho thay diem van hanh he thong nam o coverage cao
`0.74..0.79`, ngoai vung coverage thap ma Phase 22 da dung de danh gia ho
NHAN. Truoc khi chay Lesson 23.2, can khoa lai khung so sanh hai ho nguong va
cac doi chung dai so.

## A. Tau truth persistence

Ket qua Lesson 23.1 do duoc truth persistence cung thang thoi gian voi AR(1),
nhung fit mũ phai co dinh san doc lap:

```text
p_inf = sum_i P(a*=i)^2
log((agree(L) - p_inf) / (1 - p_inf)) = -L / tau_a
```

Fit `tau_a` dung cho cac lesson sau phai la fit mot tham so qua goc. Fit co
intercept tu do chi duoc giu nhu diagnostic de giai thich so cu.

## B. Hai ho nguong la hai bang xep hang

```text
NHAN : accept <=> min_j m_hat_j / q_hat_j >= kappa
CONG : accept <=> min_j (m_hat_j - q_hat_j) >= -epsilon
```

So sanh hai ho phai noi suy ve cung coverage. So sanh theo tham so tu nhien
`kappa` va `epsilon` khong co nghia.

Ho REGRET khong phai ho thu ba:

```text
max_j(q_hat_j - m_hat_j) <= epsilon
  <=> min_j(m_hat_j - q_hat_j) >= -epsilon
```

Gate G23-6b kiem mask REGRET va CONG giong bit-for-bit tren toan luoi
epsilon, ke ca epsilon am.

## C. Dinh nghia epsilon cua ho CONG

`epsilon` la mot so tuyet doi, dung chung cho ca ba slot:

```text
m_hat_j >= q_hat_j - epsilon
```

Khong dat `epsilon_j = delta * q_hat_j`, vi khi do CONG tro thanh NHAN voi
`kappa = 1 - delta`.

Luoi khong thu nguyen:

```text
epsilon = delta * q_bar
q_bar = mean_z q_hat_slot1(z), trong do q_hat_slot1(z) la marginal co trong so
        theo z_bin sau khi aggregate C3 that su tren key z_bin x m_hat_bin
        tren CALIB
delta in {-4,-3,-2,-1.5,-1,-0.5,-0.25,0,0.25,0.5,0.75,1,1.25,1.5}
```

`delta = 0` phai cho mask giong bitwise voi ho NHAN tai `kappa = 1` (V23-4).

## D. Predictions Lesson 23.2

```text
T5 [CO CHE]
   r_plus(epsilon) tai coverage 0.30 < r_times.
   Dai khoa: r_plus in [1.2, 1.8].

T6 [CO CHE]
   r_plus(epsilon) tai coverage 0.78 > r_times.
   Dai khoa: r_plus in [2.5, 6.0].

T7 [CO CHE]
   err_system(NHAN) < err_system(CONG) tai coverage = 0.30.
   Dai khoa: ti so in [0.90, 0.99].

T8 [KINH NGHIEM]
   Tai coverage = 0.78, hai ho khong phan biet ro:
   |delta err_system| < nua do rong CI ghep cap.

T9 [CO CHE]
   slot1_decides_share(CONG) > slot1_decides_share(NHAN)
   o cac coverage khop.
   Dai khoa: chenh > 0.05.
```

Nhanh fail viet truoc: neu CONG thang ro tai coverage cao voi CI am khong chua
0, ket luan "ho NHAN la chinh" cua Phase 22 chi dung trong vung coverage thap
ma Phase 22 khao sat. Ket qua do hop le va phai ghi lai trong gate decision.

## E. B6-sys cho Lesson 23.3

B6 trong plan cu xep theo `m_true`, phu hop voi bai toan du doan hang twin sai.
Phase 23 can oracle cho bai toan he thong voi fallback co dinh:

```text
s_sys(row) = loss(a_fallback) - loss(a_twin)
reject nhung hang co loi ich chuyen doi lon nhat
```

Lesson 23.3 phai bao cao B6-sys ben canh B6 cu neu noi ve "con cach toi uu
bao xa". Hang twin sai nhung fallback cung sai khong phai room he thong.

## F. Gates

```text
V23-4   CONG tai delta=0 == NHAN tai kappa=1, bit-for-bit.
G23-6b  CONG == REGRET tren moi epsilon trong luoi.
G23-7   CONG thoai hoa tren mot khoang epsilon, khong chi mot diem.
G23-8   Full coverage quy ve neo twin tren ca ba thang.
G23-9   Ba thang risk dong bien theo coverage hay can mat Pareto.
```

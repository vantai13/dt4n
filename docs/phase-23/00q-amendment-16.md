# AMENDMENT 23-16 -- Dinh ly phat bieu tren BIEN, khong tren CHI PHI

Ngay: 2026-08-15
Commit truoc 23.4: `98c1da1`

Ly do: G23-21c lam lo ra rang code dung `alpha/3` cho ba score slot, trong
khi dinh ly cu cua MASTER_PLAN v8 duoc nhac lai nhu `alpha/K = alpha/4` cho
bon khoang chi phi. Day la sua phat bieu cho khop cai dat Phase 22--23, khong
doi mot con so nao da do.

## Dinh ly thay the

Cho `K` hanh dong. Dat `a_mu = argmin_a y_hat(a)`. Voi `j = 1..K-1`, dat:

```text
m_j = cost(a_j) - cost(a_mu)
```

Day la khoang cach that so voi lua chon cua twin, theo rank doi thu cua twin.
Dung conformal Mondrian dieu kien theo cell `(z_bin, m_hat_bin)` o muc
`alpha/(K-1)` cho moi slot `j`.

Dieu kien chap nhan:

```text
m_hat_j >= q_hat_j(z_bin,m_hat_bin)  voi moi j = 1..K-1
```

Dinh ly: neu dieu kien tren thoa, `a_mu` toi uu voi xac suat it nhat
`1 - alpha`.

Chung minh: sai chi co the xay ra neu ton tai it nhat mot doi thu co
`m_j < 0` nhung score conformal cua slot do vuot threshold. Moi slot co xac
suat vi pham toi da `alpha/(K-1)`. Bonferroni tren `K-1` su kien cho:

```text
P(any slot violation) <= (K-1) * alpha/(K-1) = alpha
P(all needed margins certified) >= 1 - alpha
```

Do do dieu kien chap nhan bao dam `a_mu` la argmin that voi xac suat it nhat
`1 - alpha`.

## Vi sao chat hon ban cu

Ban cu chan `K` chi phi tuyet doi roi so sanh. Ban moi chan `K-1` hieu truc
tiep. Hang so cong chung trong chi phi triệt tieu trong hieu, dung voi phat
hien Lesson 23.0 rang regret tai tao duoc tu `m_true_j`. Vi vay khong can
chan chi phi tuyet doi cua `a_mu`.

He qua Bonferroni:

```text
ban cu : alpha/K     = 0.10/4 = 0.025000
ban moi: alpha/(K-1) = 0.10/3 = 0.033333
```

`alpha/(K-1)` cho threshold hep hon o cung muc family confidence, nen day la
mot tiet kiem Bonferroni that, khong phai noi long guarantee.

## Con so bi anh huong

Khong co ket qua so hoc nao cua Lessons 23.1--23.3 bi doi. Code da dung
`alpha_each_base = 0.033333333` tu dau. G23-21c bao cao ca hai moc:

```text
n_min_actual_score_slots = 29
n_min_if_split_over_4_actions = 39
min_n_eff_blocks_per_cell = 433
cells_below_actual = 0
cells_below_conservative = 0
```

Ket qua PASS ca theo split thuc te `alpha/3` va diagnostic bao thu `alpha/4`.

## Tai lieu bi supersede

Khong co file `MASTER_PLAN_v8.md` tracked trong repo hien tai. Noi nao trong
MASTER_PLAN ngoai repo phat bieu dinh ly bang bon khoang chi phi `alpha/K`
duoc xem la superseded boi amendment nay cho Phase 23.

Trong repo, cac phat bieu Phase 23 phai dung:

```text
hop le dong thoi tren K-1 = 3 bien
q_hat(z_bin,m_hat_bin), 2D Mondrian
```

Khong viet C3 nhu mot certificate age-only, va khong giai thich guarantee cua
C3 bang bon khoang chi phi tuyet doi.

## L21 sau amendment nay

Phan `alpha/3` vs `alpha/4` da dong: theorem cua C3 Phase 23 la theorem tren
`K-1` bien. Phan con lai cua L21 van la mot limitation rieng: action 1 gan
nhu chet trong cell `poisson@0.925`, nen co the ton tai mot ban rut gon
`K_eff-1 = 2`. Ban rut gon do chua duoc hieu chuan, chua co artifact, va khong
duoc dung de dien giai ket qua da do.

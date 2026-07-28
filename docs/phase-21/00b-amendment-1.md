# AMENDMENT 1 - Phase 21

Ngay: 2026-07-28
Trang thai truoc sua: `00-preregistration.md`, tag `phase-21-start`

## Da Thay So Nao Truoc Khi Sua

Nguon: pilot tren trace MO PHONG AR(1), khong phai 5 trace dong bang cua
Phase 20.

```text
phi = 0.99652
sigma = 0.010
LOAD_MEAN tu topology_v7.py
n = 200000

P(accept) tai eps=0, tieu chi cu 2*q_hat_{alpha/K} = 0.001
P(accept) tai eps=0, tieu chi q_hat_diff          = 0.016 - 0.030

Duong risk-coverage pilot, score s_range, nhom z_bin x u_bin:
  cov 0.016 -> err|acc 0.019
  cov 0.025 -> err|acc 0.033
  cov 0.058 -> err|acc 0.083
  cov 0.106 -> err|acc 0.149
  diem neo: cov 1.000 -> err 0.184

d_sla|accept khong don dieu:
  0.01816 -> 0.02491 -> 0.02402 -> 0.02806
```

## Sua Gi

### A1.1. Thuoc Risk Cua Duong Bien

Cu:

```text
risk = d_sla | accept
```

Moi:

```text
risk CHINH = err | accept
risk PHU 1 = d_sla | accept
risk PHU 2 = E[regret | accept]
```

Ly do: `d_sla|accept` la hieu co dieu kien; ca hai ve doi khi tap accept doi,
nen no co the khong don dieu theo coverage. `err|accept` la selective risk
sach hon va so truc tiep voi anchor `err = 0.18233`. Van bao cao `d_sla` de so
voi anchor Phase 20 `d_sla = 0.07939`.

### A1.2. Gia Thuyet H_C

Cu:

```text
0.10 <= P(separable) <= 0.90
```

Moi, PASS khi ca ba dung:

```text
1. ton tai diem voi coverage >= 0.01
   va err|acc <= 0.5 * 0.18233 = 0.09117
2. err|acc don dieu tang theo coverage tren toan dai eps, Spearman >= 0.9
3. ton tai >= 4 diem phan biet voi coverage trong [0.01, 0.90]
```

Ly do: nguong 0.10 tai `eps=0` khong co bien minh van hanh; ABSTAIN co nghia
giu route hien tai, nen coverage thap khong mac dinh la that bai. Thu paper can
la mot duong bien, khong phai mot diem. Tieu chi moi chat hon o tinh don dieu
va so diem duoc ve. Bao cao ca H_C cu va H_C moi; H_C cu khong bi xoa.

### A1.3. Bien Dieu Kien u

Cu:

```text
de ngo ca u_all va u_top2
```

Moi:

```text
chot u_all = min tren ca 8 link
bo u_top2
```

Ly do do duoc tren pilot:

```text
u_all : q_hat theo u_bin = 21.2 -> 17.0 ->  7.6 ->  6.8
u_top2: q_hat theo u_bin = 21.5 -> 18.3 -> 18.1 -> 18.4
```

`u_top2` that bai vi score lay max tren nhieu cap, khong chi cap top-2; bien
dieu kien va score phai cung pham vi.

## Khong Sua

```text
alpha = 0.10
AGE_EDGES
U_EDGES
b_block
ti le 50/50
seed 7000
w_loss / T_delay / T_loss ke thua Phase 20
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-28

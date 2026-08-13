# LESSON 22.1 -- simultaneous_score.py

Ngay: 2026-08-13

Trang thai: CODE + GOLDEN TEST. Chua cham artifact 21R/22 that.

## 1. San pham

| File | Vai tro |
|---|---|
| `cert/simultaneous_score.py` | kernel score dong thoi, 4 thu tuc FWER, tang labelled |
| `test/test_phase22_simscore.py` | 23 golden test khoa bat bien toan hoc |
| `docs/phase-22/00-preregistration.md` | revision 2: them P2b/P2c va sua bang du doan |

## 2. Ba bac tu do moi da chot

### D1 / P2b -- cot so sanh theo hang, khong theo danh tinh duong

Cot 0 la `a1` vs duong twin xep hang 2; cot 1 la `a1` vs hang 3; cot 2 la
`a1` vs hang 4. Duong cu the co the doi theo tung hang.

Ly do chon:

1. Rank slot dinh nghia duoc o moi hang nen kha hoan doi.
2. Danh tinh duong tao 12 nhom, ket hop 4 bin tuoi thanh 48 nhom va de rong.
3. Khop voi 21R, noi `top_two_by_twin` da chon theo hang.

He qua: phat bieu la ve thu hang theo twin, khong phai mot cap duong cu the.

### D2 / P2c -- hieu chuan tung slot, khong gop

`qhat_per_slot` tinh mot qhat rieng cho moi rank slot. Khong gop 3 score trong
cung mot hang vao mot pool 3n, vi ba score do phu thuoc do chung `e(a1)`.

Neu gop, `n` bi phong len 3 lan bang mau phu thuoc. Day cung kieu loi voi viec
chia calib/test theo hang trong positive-control V3 cua Phase 21R.

### D4 -- accept phai kiem moi slot

Bonferroni/Sidak co `qhat_j` rieng theo slot nen:

```text
accept <=> forall j: m_hat_j >= kappa * qhat_j
```

Max-score chi co mot `qhat` chung. Do `m_hat_2 <= m_hat_3 <= m_hat_4`, accept
rut gon thanh:

```text
accept <=> m_hat_2 >= kappa * qhat
```

Day la ket qua dep: voi max-score, nang cap tu chung nhan cap sang chung nhan
dong thoi khong doi logic cong, chi doi gia tri `qhat`.

## 3. Dry-run tren du lieu tong hop

Bo sinh:

| Bo sinh | Noi dung |
|---|---|
| independent | sai so twin doc lap giua cac hanh dong |
| butterfly | sai so link doc lap, sai so path = incidence(`topology_v7`) |

Thong so: `n = 400000`, `alpha = 0.10`, chia 50/50 calib/test theo thu tu
mang tong hop. Day KHONG phai artifact 21R.

### Independent

| Thu tuc | qhat | coverage dong thoi | coverage tung slot |
|---|---:|---:|---:|
| uncorrected | [3.4793, 3.4838, 3.4874] | 0.7629 | [0.8993, 0.8995, 0.8996] |
| Bonferroni | [4.5080, 4.5186, 4.5213] | 0.9144 | [0.9665, 0.9668, 0.9672] |
| Sidak | [4.4755, 4.4868, 4.4928] | 0.9115 | [0.9653, 0.9656, 0.9659] |
| max-score | [4.3759] | 0.9005 | [0.9612, 0.9608, 0.9611] |

`corr` trung binh giua cac cot `s_pair`: 0.2231.

### Butterfly incidence

| Thu tuc | qhat | coverage dong thoi | coverage tung slot |
|---|---:|---:|---:|
| uncorrected | [3.5480, 3.5468, 3.5569] | 0.7690 | [0.9005, 0.8992, 0.9010] |
| Bonferroni | [4.6369, 4.6261, 4.6364] | 0.9155 | [0.9674, 0.9661, 0.9670] |
| Sidak | [4.6042, 4.5943, 4.6052] | 0.9127 | [0.9661, 0.9650, 0.9658] |
| max-score | [4.4593] | 0.8999 | [0.9607, 0.9597, 0.9600] |

`corr` trung binh giua cac cot `s_pair`: 0.2410.

Ti so tren butterfly:

| Dai luong | Gia tri |
|---|---:|
| qhat_Bonferroni(slot0) / qhat_21R(slot0) | 1.3069 |
| qhat_Sidak(slot0) / qhat_21R(slot0) | 1.2977 |
| qhat_maxscore / qhat_21R(slot0) | 1.2568 |
| qhat_maxscore / max(qhat_Bonferroni) | 0.9617 |

## 4. Giai thich co che

Max-score chi chat hon Bonferroni khoang 3-6%, khong phai 10-15%.

Ly do: `s_pair_j = |e(a_j) - e(a1)|` da triet tieu common-mode error. Phan
chia se con lai den tu proper-subset sharing trong butterfly va tu so hang
chung `-e(a1)`, ma so hang nay ton tai ca khi sai so path doc lap. Do vay
butterfly chi tang tuong quan giua cac cot score tu 0.2231 len 0.2410 trong
dry-run tong hop.

Neu du lieu that sau nay cho max-score thang Bonferroni 15-20%, do la dau hieu
he that co nguon tuong quan manh hon incidence tuyen tinh nay.

## 5. Gate

| Gate | Test | Trang thai |
|---|---|---|
| G22-1a `s_margin <= s_sim` | GS-2 | PASS |
| G22-1b `s_sim = max(s_pair)` | GS-2b | PASS |
| G22-1c common-mode invariance | GS-3 | PASS |
| G22-1d K=2 suy bien ve margin | GS-5 | PASS |
| G22-1e cau noi voi `margin_score.s_vs_a1` | GS-2c | PASS |
| G22-14 three-label rule | GS-14 | PASS |
| PC22-2 uncorrected lam coverage tut | GS-12 | PASS |
| n >= 9 boundary | GS-15 | PASS |

## 6. Test da chay

```text
/tmp/dt4n-venv/bin/python -m pytest test/test_phase22_simscore.py -q
23 passed in 0.50s

/tmp/dt4n-venv/bin/python -m pytest test/test_phase21r_margin.py test/test_phase21r_calib.py -q
22 passed in 0.93s

/tmp/dt4n-venv/bin/python -m pytest -q
660 passed, 4 skipped in 170.30s
```

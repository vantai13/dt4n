# AMENDMENT 5 -- Phase 21R

Ngay ky: 2026-08-12
Nguoi ky: Codex theo yeu cau owner repo DT4N
Boi canh: sau khi chay `cert/conformal_v2.py`.
CHUA tinh duong cong risk-coverage cua Lesson 21R.6.

## E1. Lam ro bien the B

Lesson 21R.4 da canh bao khong tron `q_pooled`, `q_block_median`, va
`q_of_block_q`. Dinh chinh quan trong:

```text
Variant B = q_hat cua TAT CA hang calib, tai level ceil((n_BLOCK+1)(1-alpha))/n_BLOCK
```

Nghia la Variant B la "phan vi gop tai muc hieu chinh theo block", khong phai
"phan vi cua cac phan vi theo block". Vi vay q_hat Lesson 5 doi chieu voi cot
`q_pooled` cua Lesson 4, khong doi chieu voi `q_of_block_q`.

## E2. Gate dat tren cell chinh

Cell `poisson@0.925`, score `s_margin`, Variant B, `z_bin`.

```text
n_block calib = 500 moi bin
level = ceil(501 * 0.9) / 500 = 451 / 500 = 0.902
```

| Bin | q_hat | Coverage |
|---|---:|---:|
| B1 | 11.587758 | 0.91020 |
| B2 | 15.634801 | 0.91177 |
| B3 | 19.646107 | 0.90981 |
| B4 | 24.322243 | 0.90676 |

```text
coverage bien = 0.908684
G3 |0.908684 - 0.90| = 0.008684 <= 0.02      DAT
G4 max bin dev       = 0.011770 <= 0.05       DAT
G8 q(alpha/4) > q(alpha) moi bin             DAT
G6 V3 SD ratio       = 0.256182 < 0.50        DAT
```

Coverage hoi tren 0.90 la dau hieu dung: `level=0.902` lon hon 0.900 do hieu
chinh bao thu cua split conformal.

## E3. Phat hien phuong phap: ro ri lam phuong sai sup

Positive control V3, 20 split:

| Split | Coverage mean | Coverage SD |
|---|---:|---:|
| block | 0.90254 / 0.90395 / 0.90372 / 0.90272 | 0.00417 / 0.00423 / 0.00500 / 0.00470 |
| row leak | 0.90105 / 0.90134 / 0.90101 / 0.90067 | 0.00122 / 0.00145 / 0.00104 / 0.00094 |

```text
SD(row) / SD(block) = 0.256182
```

Phuong phap ro ri cho coverage gan 0.90 hon phuong phap dung. Vi vay doi chung
duong khong duoc hoi "coverage co gan 0.90 khong"; no phai hoi "coverage qua
cac split co on dinh bat thuong khong".

## E4. Kiem chung doc lap theo seed

Calib tren seed `{101,102,103}`, test tren `{104,105}`:

| Bin | q_hat | Coverage |
|---|---:|---:|
| B1 | 11.520279 | 0.90808 |
| B2 | 15.407788 | 0.90201 |
| B3 | 19.325661 | 0.89923 |
| B4 | 24.136398 | 0.90179 |

```text
coverage bien = 0.901887
```

Calib va test la cac quy dao rho tach biet hoan toan. Day la bang chung manh
nhat rang bao dam khong den tu chia se trang thai thoi gian trong cung trace.

## E5. A vs B va caveat bat buoc

| Variant | q_hat B1 | q_hat B2 | q_hat B3 | q_hat B4 | Coverage bins | Marginal |
|---|---:|---:|---:|---:|---|---:|
| A | 11.100814 | 15.775669 | 19.444059 | 26.057087 | .8963 .9148 .9068 .9281 | 0.91834 |
| B | 11.587758 | 15.634801 | 19.646107 | 24.322243 | .9102 .9118 .9098 .9068 | 0.90868 |
| C | 21.392284 | 28.754477 | 33.899490 | 45.904232 | .9985 .9979 .9959 .9979 | 0.99753 |

`A` la neo ly thuyet dung dinh ly huu han-mau nguyen ven, nhung nhieu. `B` la
ket qua chinh, on dinh hon vi dung tat ca hang. `C` la can tren bao thu.

Caveat bat buoc:

```text
Variant B on dinh hon muc dinh ly huu han-mau voi n=500 cho phep. Day khong
phai vi pham; no phan anh viec q_hat duoc uoc luong chinh xac hon tu du lieu
gop. Nhung bao dam huu han-mau chat che chi duoc khang dinh cho Variant A.
```

## E6. Cau noi vat ly -> q_hat

| Bin | q_hat conformal | 1.645 * rms | Ratio |
|---|---:|---:|---:|
| B1 | 11.587758 | 11.380854 | 1.01818 |
| B2 | 15.634801 | 15.323975 | 1.02028 |
| B3 | 19.646107 | 19.265418 | 1.01976 |
| B4 | 24.322243 | 24.070188 | 1.01047 |

Khop trong 2.1%. Phan du giai thich duoc boi `level=0.902` thay vi `0.900` va
duoi thuc nang hon nua-chuan mot chut. Day la chuoi khong chi do q_hat ma giai
thich no tu physics/decomposition:

```text
rms_e_model, rms_e_stale, cov -> rms_total(z) -> 1.645*rms -> q_hat conformal
```

## E7. Score mot phia

Score phu `s_signed`, Variant B:

| Bin | q_hai_phia | q_mot_phia | Loi | Coverage |
|---|---:|---:|---:|---:|
| B1 | 11.587758 | 10.465103 | 9.7% | 0.90511 |
| B2 | 15.634801 | 14.156768 | 9.5% | 0.90808 |
| B3 | 19.646107 | 18.029781 | 8.2% | 0.90898 |
| B4 | 24.322243 | 22.546635 | 7.3% | 0.90465 |

Loi 7-10%, coverage van dung. Van la ket qua phu theo P2, khong doi score chinh
cua Phase 21R.

## E8. Cross-cell caveat

Cac cell khong suy bien (`poisson@0.925`, `poisson@0.850`, `h2@0.700`) dat
G3/G4/G6/G8. `cbr@0.700` la positive control suy bien: score hai phia co
coverage bien `0.921027`, lech `0.021027`, nen G3 formal false sat nguong; G4,
G6, G8 van dat. Khong dung cell PC nay lam headline.

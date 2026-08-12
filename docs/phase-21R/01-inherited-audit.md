# Phase 21R -- Kiem toan ke thua (bang SO, moi so co provenance)

Ngay ghi: 2026-08-12      Nguoi ghi: Codex theo yeu cau owner repo DT4N

Muc dich cua file nay la khoa lai nhung gi Phase 21R duoc phep ke thua, nhung
gi phai sua, va nhung gi phai loai bo truoc khi viet code moi.

## Bang 1 -- q_hat cua v7 rong gap 4.4-9.2 lan nguong SLA cua chinh no

Nguon:

```text
results/phase-21/conformal_offered_z.json -> variant_B.qhat
cert/build_calib_set.py -> T_DELAY = 14.513765784675
```

| bin z | 0 | 1 | 2 | 3 | 4 |
|---|---:|---:|---:|---:|---:|
| q_hat (ms, thang cost) | 64.11 | 88.80 | 105.90 | 120.17 | 133.20 |
| q_hat / T_DELAY | 4.42 | 6.12 | 7.30 | 8.28 | 9.18 |

```text
coverage bien   = 0.90110
P(accept|eps=0) = 0.05726
```

Hai dong cuoi KHONG mau thuan. Chung la hai mat cua cung mot hien tuong:
conformal tu chua bang cach noi `q_hat`, nen bao phu van dung du score khong
huu ich.

## Bang 2 -- NGUYEN NHAN THAT: w_loss khuech dai sai so loss

```text
cost(a) = delay(a) + w_loss * loss(a)

w_loss(v7)             = 1451.38
w_loss(20R, poi@0.925)= 3222.24

sai so loss 0.01 -> 14.5 ms (v7) / 32.2 ms (20R)
sai so loss 0.05 -> 72.6 ms (v7)
sai so delay 0.3 ms -> 0.3 ms
```

Do lon cua `q_hat` KHONG den tu viec v7 chon score tuyet doi. v7 that ra da
dung `s_vs_a1`, mot score vi sai. Nguyen nhan chinh la he so khuech dai
`w_loss` tren kenh loss. Trieu tieu common-mode khong cuu duoc dieu nay, vi cac
duong di qua cac link loi khac nhau, vi du `ac` 4 Mbps va `bc` 6 Mbps.

He qua thiet ke cho 21R:

```text
Phai bao cao q_hat_delay (ms) va q_hat_loss * w_loss (ms).
```

## Bang 3 -- Chi phi 4 duong tai diem GO

Nguon:

```text
results/phase-20R/breakdown_scan_transfer_qt3_n120k.json
docs/phase-20R/07b-design-validation-v2.md
docs/phase-20R/99-gate-decision.md
```

```text
poisson @ 0.925

P1 = 112.9658
P3 = 120.5115
|P1 - P3| = 7.5457 ms

xep hang baseline = P1, P3, P4, P2
xep hang cascade  = P3, P1, P4, P2
r*                = [0.008805, 0.008868]
```

Cascade lam lat dung cap co khe quyet dinh nho nhat. Phase 21R vi the phai do
truc tiep tren score lien quan den khe quyet dinh, khong chi tren sai so tuyet
doi cua tung duong.

## Bang 4 -- SAN NHIEU THAT tren thang cost cho s_margin

San `0.4646 ms` trong Phase L la san cua KENH DELAY, MOT LINK. No KHONG phai
san cho `q_hat` tren thang cost cua mot HIEU hai duong.

Tinh lai tu `truth_table.parquet` cho cap canh tranh `P1` vs `P3`, chung link
`vC` nen link chung trieu tieu. Cac link khac nhau la `{uA, ac}` vs `{uB, bc}`.

| link | rho | n_pkt | se_delay | se_loss | se_loss * 3222 |
|---|---:|---:|---:|---:|---:|
| uA | 0.86 | 170134 | 0.06601 | 0.000058 | 0.1863 ms |
| ac | 0.98 | 283606 | 0.10379 | 0.000297 | 0.9583 ms |
| uB | 0.88 | 130107 | 0.06474 | 0.000171 | 0.5516 ms |
| bc | 0.98 | 283606 | 0.10379 | 0.000297 | 0.9583 ms |

```text
kenh delay = 0.1735 ms
kenh loss  = 1.4750 ms
TONG       = 1.4851 ms
SNR        = 7.5457 / 1.4851 = 5.08
```

Gate 21R-G11 phai dung san `1.49 ms`, khong dung `0.4646 ms`. Neu `q_hat` chay
ra duoi san nay, dieu do la dau hieu bug hoac dang so bang truth table voi
chinh no.

## Bang 5 -- e_model CO THAT, va no la SAI SO TONG QUAT HOA

`link_model_v2` duoc fit tren luoi rho THUA cua Phase L, 12 diem:

```text
{0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.925, 0.95, 0.98, 1.0, 1.02, 1.05}
```

`truth_table` do tren luoi DAY cua 20R, 28 diem:

```text
{0.50, 0.52, 0.54, ..., 1.04}
```

So sanh `truth_table.parquet` voi `link_model_v2.predict_delay()`:

| mode | max \|resid\| | mean \|resid\| |
|---|---:|---:|
| cbr | 0.0091 ms | 0.0034 ms |
| h2 | 0.1748 ms | 0.0508 ms |
| poisson | 0.2763 ms | 0.0535 ms |

Residual bang 0 tuyet doi tai 12 diem huan luyen, vi PCHIP di xuyen qua cac
diem do.

Phat bieu dung:

```text
e_model la sai so tong quat hoa cua link_model_v2 -- mot PCHIP fit tren luoi
rho thua -- so voi bang tra do day cua chien dich Phase 20R.
```

Khong duoc viet: `e_model la sai so cua mo hinh so voi vat ly that`.

## Bang 6 -- Sai sot da phat hien trong ban thao ke hoach Phase 21R

| Sai sot | Ket luan audit |
|---|---|
| "v7 dung s_abs" | SAI. v7 dung `s_vs_a1`, da la score vi sai. |
| `h2 @ 0.635` | Khong ton tai. Grid hop le la `[0.7, 0.85, 0.925, 0.96]`. |
| Bang `q90(s_margin)` / `P(detach)` | Khong co provenance trong artifact. Khong duoc chep. |
| AoI `[0.051, 0.548]` | Sai. Gia tri thuc nhan la `[0.055, 0.550]`, 100 muc. |
| San `0.4646 ms` | Sai thang do. San dung tren cost margin la khoang `1.49 ms`. |
| SNR `16.2` | Sai. SNR dung la `5.08`. |
| Anchor `0.295005` ghi cho `n=200k` | Sai ngu canh. `0.295005` la `n=120k, z=0.55`; `n=200k, z=0.55` la `0.290467`; sawtooth operational la `0.283220`. |
| bin `[0.30, 0.548]` | Loai mat `z=0.550`. Phai la `[0.30, 0.550]`. |
| bin tuoi can bang | Sai. B1 9%, B2 20%, B3 20%, B4 51%. |

## Ket luan kiem toan

GIU NGUYEN, KHONG DONG VAO:

```text
[v] Khung conformal v7: split theo block, Mondrian, positive control V3.
[v] Bai hoc Amendment 1: gate huu ich phai la duong cong, khong phai mot diem.
[v] Toan bo results/phase-21/*: phu luc kiem chung cheo, khong sua nguoc.
[v] truth_table.parquet: ground truth dong bang tu 20R.
[v] sla_calibration.json: T_delay, T_loss, w_loss theo tung o.
[v] measurements/decision_error_v2.py: TruthTable, _decomposition,
    rho_matrix_from_cell. Tai su dung, khong viet lai.
```

SUA trong Phase 21R:

```text
[v] s_vs_a1 -> s_margin lam score chinh.
[v] ground truth v1 -> truth_table 20R.
[v] global w_loss/T_delay -> w_loss/T_delay theo tung o.
[v] q_hat mot kenh -> q_hat_delay va q_hat_loss*w_loss.
[v] coverage mot diem -> risk-coverage frontier.
[v] e_model oracle-zero -> e_model tong quat hoa tren luoi rho day.
[v] age bins dung [0.055, 0.550] va bao cao ca bin chinh/binh phu.
[v] anchor 20R -> anchor moi tren cung thiet ke lay mau 21R.
```

LOAI BO:

```text
[x] v7 q_hat lam metric chat luong twin.
[x] P(accept)=0.057 nhu ket qua huu ich.
[x] W_LOSS/T_DELAY global cua v7.
[x] Bang q90/P(detach) khong co artifact.
[x] h2@0.635.
[x] san 0.4646 ms tren thang cost.
```

# Phase 20R -- Gate Decision (FINAL)

Ngay: 2026-08-12      Tag du kien: phase-20R-complete

Thay the ban 2026-08-06. Ban cu giu nguyen trong lich su git; khong sua nguoc
ket qua Phase 20R sau ranh gioi nay. Moi phat hien sau tag phai di vao erratum.

## 1. Phan quyet

GO -- nhanh (a), tai diem van hanh:

```text
mode = poisson
rho_bar = 0.925
z = 0.55
tau = 1.0
n = 120000
seeds = 101..105

err_total = 0.295005
d_sla     = 0.098596
```

Hai so tren lay tu `results/phase-20R/additivity_band_sawtooth.json`; day la
mat sawtooth operational da dung cho gate. `err_total` nam trong `[0.05,0.40]`
va `d_sla` lon hon 3.3x san 0.03.

## 2. Bang gate

| Gate | Ket qua | Ghi chu |
|---|---|---|
| G1 | DAT tren 6 o | `err(0.55)` trong `[0.05,0.40]` |
| G2 | DAT co co | 5/6 o giu DAT o dau xau nhat; `poisson@0.700` mong manh va khong dung lam GO |
| G3 | DAT moi o | Spearman(err,z) duong |
| G4 | **FAIL nhu da ky** | H3 don dieu theo `rho_bar` bi bac bo |
| G5 | DAT | NC1b=0, NC2 trong `[0.747,0.751]`, PC1 cbr=0 |
| G6-CASCADE | do xong, bao thu co gioi han | `r_path` am 4/4 |
| G6-BAND | LAT K4 trong pham vi cascade | binding `poisson/loss/common_mode`, first broken tai `poisson@0.925` |
| G7 | DAT | moi CI dung `se_batch` |
| QS-DELAY | DAT | Phase T residual delay nho hon bien sup do 29x |
| QS-LOSS | **DAT o GO; h2 khong ket luan duoc** | Amd 20, `results/phase-20R/qs_loss_residual.json` |
| ERR0 | DAT | Amd 19, `err=0` co co che khoa argmin |

## 3. Dong gop chinh

Phase 20R khong dong bang mot con so don le. Ket qua chinh la mot ho duong
cong:

```text
Decision error is band-limited in offered load, and band location depends on
traffic family, not load level alone.

poisson peak measured near rho_bar = 0.88
h2 peak sits at/lower than left edge of the original operational window
cbr remains zero over the reported reliable band
```

Do do monotonicity in load -- gia dinh ngam cua nhieu metric fidelity dong nhat
nhu MAPE -- bi bac bo. Mot twin dat tai mot tai co the khong dat o tai thap hon.

## 4. G4 FAIL

Tien dang ky yeu cau ghi FAIL neu H3 khong dat. Ket qua operational:

```text
poisson Spearman(err,rho_bar) = +0.2   exact p = 0.9167
h2      Spearman(err,rho_bar) = -1.0   exact p = 0.0833
```

Khong goi fail la pass. Muc dich khoa hoc cua G4 la kiem tra lieu regime van
hanh co la bien dieu kien hay khong; muc dich do van DAT bang bang chung khac:

```text
poisson err qua rho_bar: 0.1879 .. 0.4301   ti so 2.3x
h2      err qua rho_bar: 0.0017 .. 0.3898   ti so 229x
```

Confound da biet:

```text
sigma_rho bi buoc vao rho_bar qua sigma_max_regime().
Khi rho_bar tang, sigma co the giam cung luc.

=> Headline khoa hoc dung mat sigma co dinh / unimodal khi noi ve hinh dang.
=> Mat operational/sawtooth tra loi cau hoi ky thuat: he chay duoc o dau.
```

## 5. `err = 0` la che do, khong phai bug

Gia tri bien `err_total = 0.000000` trong poisson tai tai thap duoc giai thich
bang khoa argmin:

```text
lock_ratio = min_t(cost_second - cost_best) / max_t|cost_twin - cost_true|
```

Representative artifact `results/phase-20R/locked_argmin_check.json`:

```text
poisson@0.635  opt_share {P1:1.000}  gap 1.1219  twin_err 0.1899  ratio 5.91
poisson@0.650  opt_share {P1:1.000}  gap 1.0660  twin_err 0.1999  ratio 5.33
poisson@0.700  opt_share {P1:1.000}  gap 0.5134  twin_err 0.3758  ratio 1.37
poisson@0.850  3 duong tung toi uu   gap 0.0001  ratio 0.00
```

`ratio > 1` nghia la sai so twin khong bao gio dong duoc khe giua duong tot nhat
va duong nhi. `err = 0` la he qua co hoc.

## 6. QS-LOSS

QS-LOSS duoc do bang tai phan tich Phase T, khong chay Mininet moi:

```text
r_loss = (loss_do_dong - loss_QS_packet_weighted_dong)
       - (loss_do_control - loss_QS_packet_weighted_control)
```

Decision CI trong artifact la seed-cluster, packet-weighted, normal CI95:

```text
poisson a=0.9 : -0.000305  CI95 [-0.000555, -0.000055]  -> PASS
h2      a=0.9 : -0.000526  CI95 [-0.001037, -0.000015]  -> KHONG KET LUAN DUOC
nguong sup do: [-0.001, +0.00005]
```

Ba dieu phai noi cung luc:

```text
1. O GO la poisson, nen ket luan headline khong phu thuoc vao h2.
2. h2 cham/vuot can -0.001; khong duoc goi la PASS.
3. a=0.2 gan 0 hon ro so voi a=0.9, dung ky vong loss phi tuyen manh hon delay.
```

## 7. Pham vi hieu luc

```text
- Xep hang tuyet doi cac duong tai poisson@0.925 chi giu trong
  |r_path| < khoang 0.00886. Phase 21R phai chung nhan HIEU chi phi giua
  cac duong, khong chi phi tuyet doi tung duong.
- Path p95/p99 KHONG cong tinh. Moi phat bieu ve duoi phai do end-to-end.
- cbr, rho >= 0.95: `is_reliable = False`, loai khoi moi gate.
- QS-LOSS ap residual do o `(bw=6,q=13)` cho moi link: ngoai suy common-mode,
  chua co bang chung differential theo link class.
- Lo poisson onset giua 0.700 va 0.780 chua duoc lap day bang scan moi; khong
  ve noi suy qua lo nhu the da do.
```

## 8. Ban giao cho 21R

21R duoc phep dung tu 20R:

```text
[v] truth_table.parquet
[v] cost_v2.py va golden tests lien quan
[v] sla_calibration.json
[v] diem van hanh poisson@0.925 da qua G1/G2/G3/G7
[v] san nhieu 0.4646 ms lam moc so voi q_hat
[v] r_path ~= 0.00886 lam bien cascade cho ranking tuyet doi
```

21R khong duoc gia dinh:

```text
[x] xep hang tuyet doi cac duong on dinh ngoai bien cascade
[x] err don dieu theo tai
[x] QS-LOSS PASS tren h2
[x] p95/p99 cong tinh duoc
```

Ba gia thuyet ung vien ban giao cho 21R, bat buoc tien dang ky truoc khi dung:

```text
H9-post  P[r(s) < sigma_rho] vs err
H10      chuyen kenh la dieu kien CAN, khong DU
H11      err(rho_bar, sigma) co tach thanh f(rho_bar) * g(sigma) hay khong
```

Ca ba la THAM DO cua 20R, khong tinh la bang chung confirmatory cua 20R.

## 9. Threats to Validity

```text
R-20R-1  Truth table la noi suy theo rho, khong do lien tuc.
R-20R-2  Cac o chia se seed/trajectory family, khong doc lap hoan toan.
R-20R-3  Operational sigma thay doi cung rho_bar.
R-20R-4  G2 mong manh tai poisson@0.700; khong dung lam GO.
R-20R-5  Conformal 21R phai chung nhan difference, khong absolute path cost.
R-QS-1   QS-LOSS la reanalysis tren bw=6,q=13, khong live multi-link.
R-QS-2   h2 QS-LOSS chua ket luan duoc.
R-QS-3   Common-mode loss residual khong chung minh differential residual.
R-QS-4   Packet-weighted estimator tranh Jensen, nhung van dua tren model loss
         Phase L de tinh QS expectation.
R-ONSET  Chua lap day poisson onset 0.700..0.775.
```

## 10. Trang thai

```text
DONG. Tag: phase-20R-complete
Moi sua doi sau tag phai la ERRATUM, khong sua nguoc docs/phase-20R/ hay
results/phase-20R/.
```

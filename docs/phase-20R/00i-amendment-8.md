# AMENDMENT 8 -- Phase 20R.5: H7 cau truc don dinh cua err theo rho_bar

Ngay: 2026-08-06
Trang thai: KY TRUOC khi chay H7.

## Phat Hien Post-Hoc

Sau constant-sigma diagnostic, `poisson@0.70` co `err = 0.0000` trong khi
`poisson@0.85/0.925` co `err ~= 0.29`, va `h2@0.70` lai la dinh trong family.
Hinh dang nay khong phu hop voi mot confound `sigma_rho` don le.

Mot diagnostic post-hoc cho thay:

```text
1. Co dinh w_loss = 2500 lam err thay doi < 0.01 tuyet doi so voi w_loss hieu chuan.
2. Co dinh w_loss = 0 lam err sup xuong <= 0.0043 trong cac o da kiem.
```

Dien giai post-hoc: quyet dinh bi lat gan nhu hoan toan boi so hang loss
`w_loss * loss`, khong phai boi delay. Loss bat len trong mot dai hep cua
`rho_bar`; khi loss chua bat, ranking bi khoa theo delay; khi loss da ap dao,
ranking lai bi khoa theo loss. Err lon nhat nam o dai chuyen tiep.

## Gia Thuyet Moi H7

```text
H7a err(rho_bar) don dinh trong moi family, khong don dieu.
H7b dinh cua poisson nam trong [0.78, 0.93].
H7c dinh cua h2 nam duoi 0.70; them rho_bar thap se thay err tang khi rho_bar
    giam tu 0.70 xuong, roi giam tiep khi xuong nua.
H7d voi w_loss = 0, err < 0.02 o moi rho_bar va moi family.
```

H7 la gia thuyet moi, khong thay the H3. H3/G4 pre-registered van duoc doc
rieng va neu fail thi ghi fail.

## Kiem Dinh

Khong chay Mininet. Dung `truth_table.parquet` da do va AR(1) generator da ky.

Rho bo sung:

```text
rho_bar_extra = 0.65, 0.78, 0.88
sigma_rho     = 0.0096 co dinh
seed          = 101,102,103,104,105
n             = 200000
z doc chinh   = 0.55
```

Tinh kha thi mien truth table:

```text
rho_link_min ~= rho_bar - 0.0675 - 3.5 * 0.0096
0.65 -> 0.549  >= 0.52  OK
0.78 -> 0.679  >= 0.52  OK
0.88 -> 0.779  >= 0.52  OK
```

Lenh:

```bash
python3 -m measurements.decision_error_v2 --run-fixed \
  --sigma-override 0.0096 \
  --rho-bar-extra 0.65,0.78,0.88 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_unimodal.parquet

python3 -m measurements.decision_error_v2 --run-fixed \
  --sigma-override 0.0096 \
  --w-loss-override 2500 \
  --rho-bar-extra 0.65,0.78,0.88 \
  --n 200000 \
  --seeds 101,102,103,104,105 \
  --out results/phase-20R/decision_error_w2500.parquet

python3 -m measurements.decision_error_v2 --run-fixed \
  --sigma-override 0.0096 \
  --w-loss-override 0 \
  --rho-bar-extra 0.65,0.78,0.88 \
  --n 200000 \
  --seeds 101,102,103 \
  --out results/phase-20R/decision_error_delay_only.parquet
```

## PASS Criteria

```text
H7a/H7b PASS neu poisson co dung mot cuc dai noi bo trong [0.78,0.93].
H7c PASS neu h2 err tai 0.65 > err tai 0.70, chung to khi giam rho_bar tu
     0.70 xuong ta dang di len ve phia dinh nam duoi 0.70. Neu khong, H7c
     FAIL/PARTIAL va dinh h2 nam tai hoac tren mep luoi da test.
H7d PASS neu max err_total(w_loss=0, z=0.55) < 0.02.
```

## Khong Sua

Khong sua `02-prediction.md`, Q1-Q8, hay gate G1-G7. H3 van duoc ghi la bi
bac bo neu thong ke da tien dang ky khong dat. H7 la ket qua co che moi.

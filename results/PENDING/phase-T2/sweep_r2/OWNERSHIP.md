# QUYEN SO HUU CUA 166 LENH T2.6 LUOT 2   (A-T2-3)

estimand_id = RMS_ALLACTION_DELAY   (all_action / delay_ms, xem docs/GLOSSARY.md)

Chung KHONG bi vut. Chung do MOT DAI LUONG HOP LE cho MOT CAU HOI KHAC voi
cau hoi ma docs/phase-T2/01-prediction-signed.json hoi.

```text
LUAT: khong mot so nao trong thu muc nay duoc dung de phan quyet mot du doan
      D-T2.6-* cua T2-5. Ly do: du doan do song tren RMS_MARGIN_COST.
      Xem docs/phase-T2/00-preregistration.md muc AMENDMENT A-T2-3.
NGOAI LE DUY NHAT: D-T2.6-5 (NC-T2-2, doi chung noi giua hai nhanh) --
      no la doi chung VE SINH cua chinh decision_error_v2, khong nam trong
      signed_predictions, va DA PASS voi rel_span = 0.0.
```

## CHUYEN QUYEN SO HUU

```text
err_total(tau, z), d_sla(tau, z)     -> Phase 20R2 muc (1) va (2):
                                        twin sai bao nhieu, va gia bao nhieu
err theo tau                          -> 20R2 muc (4), truc chinh cua v10
ar1_clip_ratio, tt_domain_clip_max    -> V-T2-3 va muc Threats
canary 6 lan / 1 SHA-256 / span 0.0   -> bang chung moi truong on dinh
NC-T2-2 rel_span = 0.0                -> bang chung hai nhanh cham diem tren
                                         cung mot cua so (sau A-T2-2)
R5 trung vi max 0.086518% < 0.09%     -> gate ve sinh PASS
```

## SO DO DUOC, DE NGUOI SAU KHONG PHAI CHAY LAI

```text
n_commands            166      (run_log.jsonl)
n_rows                10940    (10400 khong ke canary)
seconds               1834.3
git_commit            d8956cf5650c023c809659aa0c58886b79388b4a
luoi tau              0.5 1 2 3 5 10 20 28
seed                  101..105 (+ 999 cho canary)
nhanh                 fixed 86 lenh | scaled 80 lenh
muc sigma             a in {0.5, 0.9}  (sigma = a * sigma_max_regime cua o)
Nguon: results/PENDING/phase-T2/hygiene_checks_r2.json
```

## MOC DOI CHIEU ESTIMAND (dung trong A-T2-3 muc L1)

```text
poisson@0.925, tau = 0.5, seed 101..105, nhanh fixed:
    rms_e_model = 0.3405 ms   khi a = 0.9  (sigma = 0.021802)
    rms_e_model = 0.3129 ms   khi a = 0.5  (sigma = 0.012112)
So cung o/cung tau cua 22.6 (RMS_MARGIN_COST, sigma = 0.0096) la 2.1400 ms.
sigma lon hon 2.27 lan ma so do nho hon 6.29 lan => hai dai luong khac nhau.
```

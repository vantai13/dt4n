# ERRATUM -- Phase 21 (v7)

Ngay ghi: 2026-08-12      Nguoi ghi: Codex theo yeu cau owner repo DT4N

Phase 21 da dong bang tai lieu `docs/phase-21/99-gate-decision.md`; repo hien
tai khong co tag `phase-21-complete`. File nay KHONG sua nguoc bat ky file nao
cua Phase 21. No ghi lai nhung han che duoc phat hien sau do, de Phase 21R
khong ke thua sai.

## E1. Ground truth bi o nhiem oracle

`cert/build_calib_set.py` dung `build_cost_tables()` (link_model v1) cho CA
`y = cost[rows]` LAN `yhat = cost[src]`. Cung MOT ham, chi khac chi so thoi
gian.

```text
=> e_model = 0 THEO CAU TRUC.
```

Moi phat bieu ve do rong `q_hat` cua v7 KHONG tach duoc sai so mo hinh khoi
sai so do cu. Cac gia tri da cong bo:

```text
q_hat(z)             = [64.11, 88.80, 105.90, 120.17, 133.20] ms
P(accept | eps=0)    = 0.05726
coverage bien        = 0.90110
```

Cac so nay VAN DUNG trong pham vi cua chung: mot the gioi khong co sai so mo
hinh. Chung KHONG duoc trich dan nhu ket qua ve chat luong twin. Chung tro
thanh phu luc "ket qua khi ground truth bi o nhiem" va la doi chung cheo cho
Phase 21R.

## E2. Nguong SLA ke thua da chet

```text
W_LOSS  = 1451.3765784675
T_DELAY =   14.513765784675
```

Hai gia tri tren nam trong `cert/build_calib_set.py` va den tu nguong Phase 20
v7. Gia tri hien hanh nam o `results/phase-20R/sla_calibration.json`, THEO
TUNG O. Vi du:

```text
poisson@0.925: w_loss = 3222.2447
               T_delay = 32.2224 ms
```

Phase 21R phai ke thua nguong theo tung o tu 20R, khong dung lai nguong global
v7.

## E3. Diem bat tuan: ghi chu LAM RO, KHONG phai loi

Ket qua v7 dung `--score s_vs_a1`, tuc:

```text
s_vs_a1 = max_a | e_a - e_a1 |,  a1 = argmin_a yhat(a)
```

Day DA LA mot diem bat tuan VI SAI, bat bien voi common-mode. Ghi chu nay duoc
them de tranh hieu nham trong cac tai lieu ke thua rang v7 dung score tuyet doi
`s_maxabs`. `s_maxabs` co duoc tinh va luu trong calib set, nhung KHONG duoc
dung cho bat ky ket qua cong bo nao.

Phase 21R thay `s_vs_a1` bang `s_margin`, chi tren cap hai hanh dong tot nhat
theo twin. Ly do la SIET CHAT, khong phai sua loi:

```text
s_margin <= s_vs_a1
```

## E4. Do dai block khac nhau giua v7 va 20R/21R

```text
v7      : TAU_CORE = 2.87 s -> b = 14.35 s
20R/21R : tau      = 1.00 s -> b =  5.00 s
```

Khong phai mau thuan: `2.87 s` la thoi gian tuong quan DO DUOC cua tai loi
thuc; `1.0 s` la tham so THIET KE cua qua trinh AR(1) tong hop
`SLA.ar1_matrix`. Hai phase noi ve hai qua trinh khac nhau. Phase 21R phai ghi
ro pham vi nay trong Threats to Validity.

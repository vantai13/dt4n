# AMENDMENT 23-69b -- sua leak stdout cua PILOT A069 truoc khi chay tiep

Ngay ky : 2026-08-26

Trang thai: ky SAU lan chay thu nhat bi dung, TRUOC cell thu hai.

## 0. Su co

Runner `tools/a069_pilot_new_cells.py` da gioi han JSON tong ket theo allowlist,
nhung tien trinh con `cert.build_calib_set_v3` tu in TOAN BO validation report
ra stdout. Lan chay dau da hoan tat build `poisson@0.740` va in report truoc
khi bi dung trong buoc giai `kappa_A`.

Da lo them diagnostic ngoai allowlist: `anchor_ci95`, `gap_true_pct`,
`mhat_bin_by_z_bin_calib_pct`, `corr_z_s_m_hat_calib`, `eps_regret_ms` va cac
truong validation/provenance. Chua chay cell thu hai; chua tao
`a069_pilot.json`; chua cham M-209..M-214.

## 1. Phan xu

```text
1. DUNG ngay tien trinh (exit 130).
2. Chuyen parquet/report cua lan dau sang:
   results/PENDING/phase-23/a069-contaminated-stdout/
3. `poisson@0.740` KHONG duoc goi la mu cho cac menh de dung bat ky diagnostic
   da lo o tren. Cac dai luong transfer/tai hieu chuan M-209..M-212 chua duoc
   tinh, nhung khi bao cao phai kem nhan PARTIALLY_UNBLINDED_INPUT_DIAGNOSTICS.
4. Sua runner: stdout builder -> DEVNULL; stderr chi giu trong tien trinh va
   chi dua ra khi build FAIL. Output cap cao van chi co allowlist A069 muc 3.
5. Build lai `poisson@0.740` tu dau tai duong LIVE; ban bi lo giu nguyen trong
   PENDING de bao toan audit trail, khong xoa.
```

## 2. Anh huong den lesson

Pilot do kho van duoc phep dung `err_neo`, block va `kappa_A` cua cell nay vi
chung da nam trong allowlist tu truoc. Null M-210 va cac phep cham P-1/P-2
khong duoc goi la hoan toan mu neu tap chua `poisson@0.740`; phai bao cao nhan
partial-unblinding tren. Khong doi nguong da ky va khong loai cell sau khi thay
ket qua.

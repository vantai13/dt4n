# AMENDMENT 17 -- Lesson 20R.7: chot cac lua chon con ho cua r(s)

Ngay ky: 2026-08-10
Trang thai: KY TRUOC KHI CHAY `measurements/margin_radius.py` tren du lieu.
Quan he: BO SUNG cho Amendment 15 sec.5 va sec.7. Khong sua Amd 16.

## 1. Cai da co, cai con ho

Amd 15 sec.5 da chot:

```text
r(s) = (cost_second - cost_best) / (2 * ||grad_rho cost||)
grad_rho cost = grad_rho delay + w_loss * grad_rho loss   (BAT BUOC day du)
```

Con ho ba dieu, chot o day truoc khi chay:

## 2. Nguon chi phi -- MEASURED TRUTH

`cost` va `grad` lay tu `TruthTable` (measured), khong tu `CostV2` (twin).

Ly do: `err` duoc dinh nghia la twin chon sai so voi su that do duoc. Trang
thai sinh ra `err` la trang thai ma hai duong tot nhat THAT SU gan nhau. Tinh
tren twin la do "twin nghi no mong manh o dau", khong phai "no mong manh that
o dau". Lesson 20R.7 la lesson co che nen phai dung canh quan that.

Ban twin duoc tinh song song nhu CHAN DOAN, khong phai ket luan.

## 3. w_loss -- THEO TUNG CELL

`w_loss` lay tu `measurement_cells()` cua chinh cell do, KHONG dung hang so
`mechanism_map.DEFAULT_W_LOSS`, vi hang so do chi la gia tri tai rho_bar=0.925:

```text
poisson 0.700 1656.4 | 0.850 2424.4 | 0.925 3222.2 | 0.960 3655.9
h2      0.700 2861.4 | 0.850 4021.4 | 0.925 4515.9 | 0.960 4722.7
```

Dung hang so 0.925 cho cell 0.700 la sai gan 2x. Guard test bat buoc.

## 4. Gradient -- DOC DOAN CHINH XAC, KHONG SAI PHAN

Bang tra tuyen tinh tung khuc, nen dao ham bac nhat la doc cua doan chua mau,
va no CHINH XAC. Khong dung `h` nao. Nhat quan voi Amd 16: bac 1 hop le, bac 2
khong ton tai.

```text
rho trung nut : lay trung binh doc trai va doc phai, va DEM lai.
rho ngoai mien: gia tri bi kep nhu TruthTable, doc dat 0, va DEM lai.
```

## 5. Diem van hanh cua phep kiem H1

```text
z          = 0.55        (diem van hanh cua Phase 20R)
n          = 200000
seeds      = 101,102,103,104,105
tau_rho    = 1.0
rho_source = calibration_ar1
err        = err_total tu decision_error_by_age_summary.parquet
thong ke   = median r(s) qua thoi gian, roi trung binh qua seed
kiem dinh  = Spearman mot phia, hoan vi chinh xac (n <= 9), alpha = 0.05
mau chinh  = r_bound (dang Amd 15 sec.5). r_exact chi la chan doan.
```

## 6. Pham vi -- phu thuoc giua cac cell

`ar1_matrix` chi gieo theo `seed`, khong theo `mode`. Do do `poisson` va `h2`
tai cung `rho_bar` dung CHUNG quy dao rho, chi khac tran tin cay cua family.
Tam cell khong phai tam quan sat doc lap. p-value hoan vi gia dinh
exchangeability nen no LAC QUAN. Bao cao kem canh bao nay, va doc phep kiem
theo tung family nhu ban bao thu hon.

## 7. Luat ket luan -- nhac lai Amd 15 sec.7, khong noi long

Neu `Spearman(median r(s), err) > 0` HOAC `p >= 0.05`:

```text
Ket luan: ban do co che khong ung ho giai thich err bang ban kinh cost-margin.
KHONG sua dinh nghia r(s).
KHONG doi kenh.
KHONG them bien the.
KHONG doi sang mot thong ke khac cua cung phan phoi le roi bao cao nhu H1.
```

Dieu khoan cuoi duoc them o day vi no la cach lach de nhat va Amd 15 chua chan.

## 8. Quan sat tham do

Neu trong qua trinh chay co dai luong khac to ra lien he manh voi `err`, no
duoc ghi vao muc "tham do" cua doc, gan nhan POST-HOC, va CHI duoc dua thanh
gia thuyet o mot Lesson sau, tien dang ky va kiem tren cell/seed CHUA DUNG.
No khong duoc tinh la bang chung cua Phase 20R.

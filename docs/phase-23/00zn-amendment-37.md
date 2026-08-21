# AMENDMENT 23-37 -- Lesson 23.7-quater: do lai ket luan duoi mo hinh tuong doi

Ngay: 2026-08-21
Trang thai: **TRUOC KHI MO HOAC SUA `cert/conditioning_audit.py`, TRUOC KHI
VIET CODE AUDIT TUONG DOI, TRUOC KHI CHAY, VA TRUOC KHI NHIN SO.**

## 1. Ly do va pham vi

Amendment 35 va `docs/phase-23/13-residual-level.md` da rut M-12a/M-12b,
M-15 va M-16. Cac ket luan do duoc do bang residual tuyet doi, tai phan bo
per-link va clip tai 0; S7/S8 da bac bo quyen dien giai vat ly cua nhanh do.
Rut ket luan ma khong co so thay the de lai mot lo trong. Amendment nay khoa
dai cho cac so thay the duoi mo hinh dung scope:

```text
loss'_p = loss_p * (1 + r_rel)
```

Khong xoa nhanh cu. Doi ten no thanh `*_absolute_superseded` va giu lam diem
doi chieu trong bang phan ra. Nhanh cu khong duoc dung lam ket luan chinh.

## 2. Estimand va dai khoa M-34..M-39

| ID | Dai luong (thang / muc / tap hang) | Nhan | Dai khoa |
|---|---|---|---|
| M-34 | flip fraction `a*` duoi `loss*(1+r_rel)`, co dieu kien tren tap **tu choi**, cell chinh, point | [CO CHE] | `0.02 .. 0.10` |
| M-35 | flip fraction `a*` co dieu kien tren tap **chap nhan**, cell chinh, point | [CO CHE] | `0.000 .. 0.008` |
| M-36 | `Delta=(1-gamma)(c_F2-c*)` duoi mo hinh tuong doi, cell chinh, point | [NGOAI SUY] | `-0.010 .. 0.000` |
| M-37 | dau cua `Delta` | [NGOAI SUY] | van am |
| M-38 | coverage duoi mo hinh tuong doi, PC: chi bom test | [DOI CHUNG] | `0.85 .. 0.90` |
| M-39 | coverage duoi mo hinh tuong doi, NC: bom ca calibration va test | [DOI CHUNG] | `>= 0.89` |

Ca ba cell `poisson@0.925`, `poisson@0.850`, `h2@0.700` bat buoc duoc chay
va bao cao. Dai chinh khoa cho M-34..M-39 duoc cham tai cell chinh; hai cell
held-out phai co cung truong, cung phep tinh va verdict doi chieu cung dai,
khong duoc retune sau khi nhin so.

Neu M-37 fail (`Delta >= 0`), khong sua dai. Bao cao ket qua am va chuyen
luan diem paper sang nhanh 4.3: certificate mua `c*`, khong mua sai so thap
hon.

## 3. Tach flip theo quyet dinh cong

`c_F2` va `c*` tinh tren tap tu choi, khong tren toan bo test rows. Vi vay
flip toan cuc khong duoc dung thay M-34/M-35. Audit bat buoc tra:

```text
flip_all_rows
flip_given_accept
flip_given_reject
n_accept
n_reject
identity_residual
concentration_ratio = flip_given_reject / flip_all_rows
```

Dong nhat thuc tong co trong so phai co `identity_residual < 1e-12`. Test
khong duoc ep `concentration_ratio > 1`; neu gia thuyet tap trung flip bi bac
bo, artifact va report phai ghi ket qua am nguyen ven.

`accept_set` va `y_hat` phai giong het giua baseline va perturbed. Cong tin
cay dung dau ra twin, khong duoc nhin ground truth. Neu mot trong hai doi,
audit dung voi loi ro ri su that.

## 4. Doi chieu nhanh tuyet doi superseded

Nhanh tuyet doi cu phai van tai lap duoc diem neo:

```text
perturbed Delta tai point = 0.04487496174747532
sai so tuyet doi cho phep  < 1e-9
```

Day la regression control de phat hien viec them nhanh moi lam hong pipeline
cu; no khong phuc hoi tinh hop le cho ket luan bi rut.

## 5. Dinh chinh ke toan M-28

Artifact S8 hien co hai estimand khac nhau:

```text
mean-of-ratios = mean_seed_relative          = -0.164792792566...
ratio-of-means = point / baseline_magnitude  = -0.15924... (chan doan)
```

M-28 chinh thuc dung **mean-of-ratios**, vi dai luong can ngoai suy la ti le
tren tung seed, khong phai hieu tuyet doi. `relative_point` trong ket qua
cham M-28 phai tro duy nhat toi mean-of-ratios. Uoc luong con lai duoc giu
voi ten ro `relative_point_ratio_of_means` lam chan doan, khong cham M-28.

Khong dien tay hai gia tri. Chung phai duoc tai sinh tu raw B/C ghep seed.

## 6. Dinh chinh doi chung M-33 cua Amendment 36

CI90 goc `[-0.0101350818, -0.0089084907]` den tu seed `104..108`. Vi vay:

- **M-33a:** tinh point moi tren tap con `104..108`, so voi CI90 goc; day la
  doi chung khop seed va la phan quyet chinh.
- **M-33b:** tinh point bo sung tren toan bo `101..108`; bao cao de tang do
  chinh xac va dung uoc luong `r_rel`, nhung khong thay verdict M-33a.

Analyzer phai khoa `w_loss` theo cell, ghi gia tri trong moi row va tu choi
tron row co `w_loss` khac nhau. `w_loss` chi doi loss sang ms trong Q2; khong
tham gia uoc luong residual loss.

## 7. Negative control repeatability cho campaign

Truoc khi dien giai `r_P1-r_P3`, campaign bo sung 8 nhom P1 lap lai voi cung
seed nhung khac thu tu lich, moi nhom gom 3 B row va 1 C row (32 live points):

```text
r_P1(luot 1) - r_P1(luot 2)
```

Day la repeatability floor cua phep hieu. Neu san nhieu cung bac voi
`r_P1-r_P3`, M-32 phai duoc ghi **INCONCLUSIVE** du CI bootstrap hep. Thay
doi nay tang ngan sach Amendment 36 tu 160 len 192 live points; khong duoc
khoi dong phan bo sung truoc khi runner/analyzer va schema row da khoa bang
test.

## 8. Output bat buoc

```text
results/phase-23/relative_conclusions_*.json
docs/phase-23/14-relative-conclusions.md
```

Moi artifact ghi estimand, scale, level, rowset, `r_rel`, provenance va verdict
M-34..M-39. Bao cao phai dat nhanh tuyet doi superseded va nhanh tuong doi
song song trong bang phan ra, khong xoa so cu.

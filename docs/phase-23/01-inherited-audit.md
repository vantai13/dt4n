# KIEM TOAN KE THUA -- Phase 23

Ngay: 2026-08-14

Muc tieu cua file nay la noi ro Phase 23 doc nhung artifact nao, ke thua
gioi han nao, va 7 phat hien nao cua Lesson 23.0 da duoc xu ly truoc khi ky.

## 1. Nguon goc artifact

Noi dung `results/phase-23/INHERITED.sha256` tai luc ky:

```text
d6904df8bfb919776e859ab186090df5a821c847859a37d532cf800f0f256234  results/phase-22/calib_set_v3.parquet
417b30f10abe8b40133038b2bb3bf6636c8cff3988a86ce3a731d01d00892d42  results/phase-22/conformal_sim_poisson_0.925.json
e32c72ab9bf0b852009c10128e7b91943bff47c434d8f79941feaebdd4f1fa89  results/phase-22/selective_poisson_0.925.json
3d2fb1e693ba579574b64884021fc50ae7197e90d666dae75772c361a43cd0fb  results/phase-22/config_matrix_poisson_0.925.json
659878301da7fdb7c3511aaba170a79fe172d6d6518142f5c66f464a4c2530b2  results/phase-22/tau_sweep_poisson_0.925.json
63353b8a68dfc35d370c0864ab5fab3516a72427a691fbaa2297cae1060e7108  results/phase-22/aoi_profiles_poisson_0.925.json
2fe8afe7c360b141ce49f10075f3c4d38e1675784217db041a63f651bc668163  results/phase-21R/anchor.json
0387d300dbdd039c004a7fc89d062a0e9219968be8ad0cfeac65e53cf34826db  results/phase-20R/sla_calibration.json
```

Neu mot sha256 thay doi, moi ket qua Phase 23 phu thuoc artifact do phai bi
coi la vo hieu cho den khi rebuild va ghi amendment.

## 2. Bang gioi han L1..L13

| ID | Gioi han | Trang thai tai dau Phase 23 |
|---|---|---|
| L1 | Ground truth la bang tra do day, khong phai chan ly vat ly | Mo, P23-C |
| L2 | Phuong sai e_model con nhieu do | Pham vi, khong phai gate Phase 23.0 |
| L3 | Bao dam tren AR(1) tong hop | Mo mot phan, can non-AR load |
| L4 | Variant A/B/C co nghia khac nhau | Bao cao song song neu dung |
| L5 | Post-selection coverage khong tu giu | Dong boi Phase 22 |
| L6 | Chung nhan cap, khong dong thoi K=4 | Dong boi Phase 22 |
| L7 | It ho tai ngoai poisson | Mo, can Phase 23 |
| L8 | Age-shape ratio chua la dinh luat | Dong trong pham vi AR(1) tau sweep |
| L9 | Chia seed co the lam p-value lac quan | Pham vi |
| L10 | Xep hang tuyet doi ke thua residual-bound 20R | Mo |
| L11 | AoI do tren cau/topology khac | Mo cho do truc tiep |
| L12 | AoI dong nhat tren 8 link | Dong trong pham vi U1/U2, PC4 mo dieu kien |
| L13 | Ti so tuoi can AoI dong nhat | Mo khi AoI trai rong |

## 3. Bay phat hien Lesson 23.0

| # | Phat hien | Muc | Xu ly |
|---|---|---|---|
| 1 | P18 dinh nghia `d_sla` mau thuan `_viol` | Chan | Viet lai P18: `sla_rate` va `d_sla` rieng |
| 2 | Thieu cot SLA theo tung duong | Chan | Them `sla_viol_p0..p3`, rebuild artifact |
| 3 | `regret` cho action bat ky tai tao duoc tu `m_true_*` | Tot | Them `relcost_matrix` va test doi chung |
| 4 | `calib_set_v3.parquet` khong track trong git | Cao | Rebuild local, ghi sha256 |
| 5 | B3 la ham bac thang 100 diem | TB | Sua G23-10, noi suy cung coverage |
| 6 | Ho REGRET dong nhat ho CONG | TB | P19 ha 3 ho thanh 2 ho + gate G23-6b |
| 7 | F2 STATIC = P1 dung, P1 dai 7.0 ms | Tot | Them F0 va disclosure `P(a*=P1)` |

## 4. Xu ly code va artifact

`cert/build_calib_set_v3.py` da luu them:

```text
sla_viol_p0, sla_viol_p1, sla_viol_p2, sla_viol_p3
```

Validation trong builder da kiem:

```text
V23_sla_twin_match = true
V23_sla_star_match = true
```

Artifact rebuild:

```text
results/phase-22/calib_set_v3.parquet
rows = 999945
sha256 = d6904df8bfb919776e859ab186090df5a821c847859a37d532cf800f0f256234
```

Test moi:

```text
test/test_phase23_prereg.py
```

kiem:

```text
1. du cot `sla_viol_p0..p3`
2. cot moi tai tao dung `viol_twin` va `viol_star`
3. `d_sla` neo = 0.060125306891879
4. `regret` tai tao tu `m_true_*` khop cot `regret`
```

## 5. Ba gioi han moi mo o Phase 23

L14  Ngu nghia fallback do ta chon, khong phai he thong that bat buoc. Mot
     router that co the dung ECMP, protected backup, hoac giu flow-level state.

L15  F1 STICKY reset dau moi block la quy uoc phuong phap de ngan ro ri
     calib/test. No co the lam F1 te hon mot he thong that khong reset.

L16  Ba thang risk `err`, `regret`, `sla_rate` do tren cung tap hang nen tuong
     quan. Khong duoc coi ba PASS la ba bang chung doc lap.

## 6. Ket luan audit

Phase 23.0 da dong hai chan duong truoc khi ky:

```text
1. SLA khong con bi dinh nghia sai thanh `cost > SLA`.
2. Artifact v3 da co du cot SLA theo moi duong de tinh fallback.
```

GO-2 duoc dong bang `cert.go2_restate` va artifact:

```text
results/phase-23/go2_fwer_restatement.json
```

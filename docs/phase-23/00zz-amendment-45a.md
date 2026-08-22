# AMENDMENT 23-45a -- Vai tro truc: CONSUMES vs MEASURES

Ngay ky : 2026-08-22
Tag     : amendment-45a
Lesson  : 23.18
Sua     : co che cua Lesson 23.17 (`test/test_no_stale_axes.py`,
          `measurements/validity.py`)

## 1. Van de

Lesson 23.18 sinh hai artifact moi:

```text
results/LIVE/phase-23/aoi_stall_anatomy.json
results/LIVE/phase-23/aoi_decomposition.json
```

Test chan cua 23.17 tu choi ca hai, vi `approved_for_live.aoi_axis` dang
RONG. Test lam DUNG viec cua no. Nhung ly do tu choi lai sai:

```text
Test gia dinh moi artifact trong LIVE/ DUNG truc tuoi z.
Hai artifact nay khong dung truc z -- chung DO ra truc z.
Mot phep do khong the bi lam sai boi chinh cai ma no dang do.
```

Day khong phai truong hop dac biet. Do la ly do NGAM khien ba file sau da
nam trong `LEGACY_EXEMPT` tu 23.17:

```text
phase-23/aoi_v7_estimates.json          "SO DO cua chinh truc z"
phase-23/dsync_sensitivity.json         "cong cu quet d_sync"
phase-23/a0_instrument_calibration.json "hieu chuan nhac cu do"
```

`LEGACY_EXEMPT` la mot danh sach ten, chi duoc ngan di. No khong dien dat
duoc LY DO. Amendment nay bien ly do ngam do thanh mot khai niem TUONG MINH.

## 2. Hai vai tro

```text
CONSUMES  artifact DUNG truc z de tinh ra ket qua.
          Truc sai -> ket qua chi dung co dieu kien.
          => phai cho nhan truc duoc DUYET (`approved_for_live`) moi vao LIVE.

MEASURES  artifact DO chinh truc z, hoac do nhac cu do no.
          Khong the bi lam sai boi cai no dang do.
          => vao LIVE duoc ngay, KHONG cho `approved_for_live`.
```

## 3. Rang buoc cho vai tro MEASURES

Mien `approved_for_live` KHONG co nghia la mien kiem tra. Artifact MEASURES
van phai:

```text
- co khoi `validity` voi `axis_role = "measures_axis"`
- ghi sha256 MA NGUON cua nhac cu (module sinh ra no)
- ghi sha256 cua moi file dau vao duoc doc
- KHONG duoc goi sawtooth_age_steps hay bat ky bo sinh z nao
  (neu goi thi no CONSUMES, khong phai MEASURES)
```

Rang buoc cuoi duoc test kiem bang cach doc ma nguon nhac cu, khong tin
loi khai.

## 4. Thay doi ma nguon

```text
measurements/validity.py     them ROLE_CONSUMES / ROLE_MEASURES,
                             tham so axis_role, ham
                             measurement_validity_block()
test/test_no_stale_axes.py   nhanh rieng cho axis_role = measures_axis
```

## 5. `approved_for_live` KHONG doi

Van RONG. Amendment nay khong duyet bat ky truc nao. Viec duyet truc moi
van phai qua mot amendment rieng sau Lesson 23.20, dung dieu kien go nhan
o amendment 23-44 muc 7.

## 6. Loi ra cho LEGACY_EXEMPT

Ba file legacy o muc 1 thuoc vai tro MEASURES nhung chua co khoi `validity`
(chung duoc sinh truoc co che 23.17). Khi nao chung duoc sinh lai, chung
phai chuyen sang `axis_role = "measures_axis"` va RA KHOI `LEGACY_EXEMPT`.
Danh sach do chi duoc ngan di -- amendment nay chi ra duong ngan no.

Chu ky: ____________

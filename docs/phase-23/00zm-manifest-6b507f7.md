# Manifest cho commit `6b507f7` (`add sth`)

Trang thai: **PHAN LOAI HOI CUU; KHONG PHAN TICH THEM DU LIEU**.

Commit `6b507f7` gom ba nhom khong lien quan. Manifest nay tach pham vi de
khong artifact nao bi dung nham trong cham diem hoac ket luan.

## 1. Pilot pre-S8 cua Lesson 23.7

Pham vi:

```text
results/phase-23/differential_live/
```

Day la 43 row pilot theo thiet ke tuyet doi cua Amendment 34. Amendment 35
da ha cap toan bo thanh **PILOT PRE-S8**. Khong row nao duoc dung de cham
M-31/M-32, dong L10, hoac dua ra ket luan ve residual vi sai.

File `p1_h2_0700_b.json` co ba row B nhung khong co nhanh C ghep cap:

```yaml
orphan_rows: 3
orphan_reason: missing_paired_C_branch
scoring_status: excluded
```

## 2. Checkpoint Q3 cua Amendment 36

Pham vi:

```text
results/phase-23/differential_live_v2/legacy_b.json
```

Day la checkpoint cua doi chung Q3, `legacy T123 @ rho=0.925`. Tai commit
`6b507f7`, state co `5/24` row B hoan tat va campaign dang do. No khong phai
artifact ket qua cuoi va khong duoc cham rieng khi chua co nhanh C ghep cap.

## 3. Vat lieu tham do Lesson 23.8

Pham vi:

```text
results/aoi/
results/calib/raw_aoi_routing_gcp_20260816.csv
results/gcp-smoke/
```

Day la vat lieu tham do AoI/GCP cho Lesson 23.8. Tai commit `6b507f7` chua co
amendment prereg bao tro. Vi vay khong duoc doc de khoa dai, cham prediction,
hoac dua ra ket luan. Chi duoc phan tich sau khi amendment Lesson 23.8 da
duoc ky va tag.

## 4. Nguyen tac su dung

- Khong noi ba nhom tren thanh mot campaign.
- Khong sua lai lich su commit `6b507f7`; manifest nay la lop ke toan bo sung.
- Moi bao cao sau nay phai neu ro amendment, rowset va trang thai scoring cua
  tung artifact duoc dung.

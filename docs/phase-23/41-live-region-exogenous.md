# Lesson 23.21h -- Vung song duoi SLA ngoai sinh

Ngay chay: 2026-08-24

Tien dang ky: `docs/phase-23/A062-amendment-62.md`, commit `cb8bd11`

Truc: AoI `measured_v7_uniform`, SLA `exogenous_g114_S-B`

Ket qua chinh: `results/LIVE/phase-23/live_region_sweep_slaB.json`

## 1. Ket luan

Sweep da chay du 12 cell tren SLA S-B ngoai sinh. Hai dinh nghia song dong y
o **10/12** cell:

```text
A  decision difficulty: err_neo >= 0.05
B  operational value:   regime == LIVE
```

Hai dinh nghia doc lap ve vung song -- sai so quyet dinh va tinh quan trong
cua quyet dinh duoi SLA -- dong y o 10/12 che do. Ket luan ve vung song do do
khong phu thuoc vao viec chi chon mot chi so. Hai bat dong la
`poisson@0.925` va `poisson@0.960`: twin van sai theo A, nhung S-B da
`COLLAPSED`, nen sai khong con gia tri van hanh theo B.

Bon metric moi duoc ky truoc M-176..M-179 deu PASS. Hai menh de ve dau duoc
giu tu truc cu, M_57 va M_47b, **MISS**; khong doi nguong va khong doi tap
cell sau khi xem ket qua.

## 2. Bang 12 cell

| cell | err_neo | A | regime B | B | dong y | lift-swing |
|---|---:|:-:|---|:-:|:-:|---:|
| poisson@0.925 | 0.238841 | 1 | COLLAPSED | 0 | 0 | +0.038123 |
| poisson@0.850 | 0.253484 | 1 | LIVE | 1 | 1 | -0.039333 |
| h2@0.700 | 0.154526 | 1 | LIVE | 1 | 1 | +0.011780 |
| poisson@0.700 | 0.003464 | 0 | TRIVIAL | 0 | 1 | +0.000582 |
| poisson@0.960 | 0.216085 | 1 | COLLAPSED | 0 | 0 | +0.003047 |
| h2@0.850 | 0.004173 | 0 | COLLAPSED | 0 | 1 | +0.006340 |
| h2@0.925 | 0.000242 | 0 | COLLAPSED | 0 | 1 | +0.000000 |
| h2@0.960 | 0.000524 | 0 | COLLAPSED | 0 | 1 | +0.000000 |
| h2@0.650 | 0.205513 | 1 | LIVE | 1 | 1 | +0.011607 |
| h2@0.675 | 0.180131 | 1 | LIVE | 1 | 1 | +0.089837 |
| poisson@0.875 | 0.257012 | 1 | LIVE | 1 | 1 | -0.018557 |
| poisson@0.900 | 0.252413 | 1 | LIVE | 1 | 1 | -0.030346 |

`regime B` trong bang khong duoc lay tu manifest da lam sach. Script tinh
lai no tu `S_pivotal` va CI, roi doi chieu nhan trong hai artifact
authoritative. Ket qua G23-214 la **12/12 khop**.

## 3. Metric va phan quyet

| Metric | Dai/menh de da ky | Do duoc | KQ |
|---|---|---:|:-:|
| M-176 | A/B dong y >= 8/12 | 10/12 | PASS |
| M-177 (`M_53'`) | rho_hit trong [0.900, 0.925] | 0.925; bracket [0.900, 0.925] | PASS |
| M-178 (`M_55'`) | err_neo p=.875 va p=.900 trong [0.20, 0.30] | 0.257012; 0.252413 | PASS |
| M-179 (`M_48b'`) | spread twin_deg tren moi A-live trong [1.00, 1.50] | 1.281290, 8 A-live | PASS |
| M_54 | dau `lift-swing` khong quay lai am sau khi duong | `[-,-,-,+]` | PASS |
| M_57 | h2 A-live co `lift-swing < 0` | h2@.650 = +0.011607 | **MISS** |
| M_47b | delta <= 0 tren moi A-live heldout | p@.875 = +0.000378; p@.900 = +0.003992 | **MISS** |

M_47b con ba cell dat dau am: p@.960 `-0.002345`, h2@.650 `-0.007104`,
h2@.675 `-0.023356`. Hai cell poisson moi duong la du de menh de `all`
MISS. M_53, M_55 va M_48b cu van `ADJUDICATED` vi chung la menh de ve muc
tren truc SLA noi sinh da bi thay.

## 4. Gate va doi chung

| Gate | Bang chung | KQ |
|---|---|:-:|
| G23-226 | 12/12 Wave-4 job qua G1..G4; 12 parquet + 12 report; digest va backup 12/12 SHA | PASS |
| G23-210 | manifest 14 feasible/unique; 10 base + 4 Wave 4; w=5000; whitelist sach | PASS |
| G23-211 | `--prepare-sla` fail-loud; `--calib-template` duoc doc/forward | PASS |
| G23-212b | 8 cell, 2340 truong; NHOM A lech 0, NHOM B lech 0 | PASS |
| G23-227 | NC_H chay 4/4 cell, 4/4 PASS | PASS |
| G23-213 | artifact 12 cell va bang A/B co so | PASS |
| G23-214 | regime tinh lai khop authoritative 12/12 | PASS |

G23-212b dung dung helper `analyze_base_cells()` ma sweep chinh goi, nhung
cau hinh no voi manifest 10-feasible-cell va bo U0 da ghim cua G23-212a.
Ket qua: 2340 truong chung, 0 truong chi co mot ve, NHOM A bit-exact lech 0,
NHOM B lech 0 voi dung sai `3.18e-12*|v|`. Gate nay chung minh patch chi them
bon cell/semantics moi, khong doi duong 8 cell nen.

NC_H duoc chay truoc khi analyze bon cell Wave 4. `fallback_triggered` la
`None`, khong phai `False`: SLA ngoai sinh khong co buoc calibration/fallback
de ma ket luan "da kiem va khong xay ra".

## 5. Dong G23-141/G23-142

Wave 4 sinh 4 cell x 3 bien the = 12 build. U0 legacy va U0 measured cua bon
cell moi duoc so sanh ghep cap de mo rong M-125:

```text
M-125a  12/12 cell HIT, delta +7.916% .. +10.886% (dai +5% .. +13%)
M-125b  48/48 o HIT
         32/32 o duoc tien dang ky la "dem" HIT
         max |lech| tren o dem = 3.464% (nguong 25%)
```

Artifact: `results/LIVE/phase-23/axis_remeasure_impact_wave4.json`. Vi vay
G23-141 va G23-142 ra khoi `PINNED_DEBT`; L41 dong.

## 6. Custody, digest va backup

`results/RAW/phase-21R/WAVE4_DIGESTS.json` liet ke dung tap 12 parquet theo
job matrix, khong dung glob rong. Ledger co 12 entry va 12 PASS. Manifest
14-cell co SHA-256:

```text
6e97ac054cce76284db3a7d3f674440408ee6f9f073c1e627b67a2bdbd1eae2d
```

Da sao 12 parquet, 12 sidecar report, ledger, manifest va digest sang:

```text
C:\Users\VAN TAI\dt4n-evidence-backup-2026-08-24
```

Kiem lai backup: 12/12 SHA parquet khop digest. Day la backup logic tren may
chu, khong phai ban sao off-site. `results/RAW/phase-21R` va
`results/SUPERSEDED/phase-21R` da duoc khoa chi-doc lai sau cua so ghi ngan.

## 7. Hai dinh chinh khi thi hanh

1. Runner Wave 4 can manifest 14-cell de build bon cell moi. Lan goi dau voi
   manifest mac dinh dung ngay o job 1 (`h2@0.650` khong co trong manifest),
   khong sinh file. Thu tu duoc sua: tao/dang ky manifest, roi moi build.
2. Huong dan cu dat measured Wave-4 vao `PENDING`. Tai luc chay, ca AoI
   `measured_v7_uniform` va SLA `exogenous_g114_S-B` da duoc duyet; de artifact
   hop le voi tier guard, 8 file measured vao `LIVE`, 4 control legacy vao
   `SUPERSEDED`. Nhan SLA khong doi vi hop dong 50 ms / 1% / 5000 khong doi.

## 8. Bon cau tu kiem

1. Mot menh de song qua doi truc khi phep doi giu bat bien dai luong ma menh
   de noi den. M_54 ve dau/thu tu co the duoc giu; M_55 ve muc tuyet doi phai
   ky lai.
2. Dai M-177 suy tu B (`S_pivotal`), con `rho_hit` cham bang A
   (`lift-swing`), nen khong vong tron. Dung chinh bon `lift-swing` Wave-4 de
   dat bien roi cham lai no moi la vong tron.
3. Ghi `False` se lam nguoi doc hieu sai rang fallback da duoc kiem va khong
   kich hoat. Su that la fallback khong ton tai tren duong SLA ngoai sinh.
4. G23-214 kiem hai duong code gan cung nhan B; M-176 so A voi B. Loi noi/ghep
   nhan B co the lam G23-214 FAIL trong khi mau sai do van tinh co lam A/B
   dong y >=8/12, tuc M-176 van PASS. Khi do artifact khong duoc tin.

## 9. File ket qua

File ket qua chinh, co the doc/chay lai va duoc cac test LIVE kiem tra, la:

```text
results/LIVE/phase-23/live_region_sweep_slaB.json
```

Bao cao nay la ban doc cho nguoi; JSON tren la artifact may-doc authoritative.

## 10. Kiem thu cuoi

```text
PYTHONPATH=. .venv/bin/pytest -q
1443 passed, 44 skipped, 11 deselected

PYTHONPATH=. .venv/bin/pytest -q -m custody
3 passed, 1495 deselected
```

Ngoai ra bo test trong tam sau khi sinh artifact dat 221 pass. Khong co gate
nao duoc danh PASS chi vi lenh chay thanh cong: moi gate deu tro toi ledger,
artifact hoac doi chung so hoc cu the o cac muc tren.

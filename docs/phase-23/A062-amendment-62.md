# AMENDMENT 23-62 -- Vung song duoi SLA ngoai sinh

Ngay ky : 2026-08-24
Lesson  : 23.21h (Viec 3)
Loai    : TIEN DANG KY THEO TRUC + DOI CHUNG AM + MO RONG 12 CELL
Prereq  : amendment-61b, `c2234c4`

Tai thoi diem ky file nay, `tools/run_23_20_matrix.py --wave 4` CHUA chay.
Bon parquet Dot 4 U3 measured-v7 chua ton tai. Moi nguong duoi day duoc suy
tu artifact da co truoc lesson, khong tu ket qua sap sinh.

## 1. Cau hoi va hai dinh nghia "song"

Bao cao CA HAI, khong ep chung thanh mot:

```text
A  decision difficulty:  err_neo >= 0.05
B  operational value:    regime == LIVE, suy tu S_pivotal duoi SLA S-B
```

A hoi twin co chon sai khong. B hoi viec chon sai co tao hau qua SLA khong.
`h2@0.850` la phan vi duong da co: err_neo cao tren artifact cu trong khi
`S_pivotal=0`, `regime=COLLAPSED` duoi S-B. Bat dong khong phai loi code.

Hai doan ket luan duoc viet TRUOC:

```text
NEU dong y >= 8/12:
  Hai dinh nghia doc lap ve vung song -- sai so quyet dinh va tinh quan trong
  cua quyet dinh duoi SLA -- dong y o N/12 che do. Ket luan vung song khong
  phu thuoc vao viec chi chon mot chi so.

NEU dong y < 8/12:
  Hai dinh nghia bat dong o N/12 che do. Bat dong co cau truc neu tap trung o
  tai cao: twin sai nhieu nhung moi duong deu vi pham SLA, nen cai sai khong
  tao gia tri van hanh. Day bac bo "do chinh xac twin ti le voi gia tri".
```

## 2. Phan xu bay metric cu theo TRUC

Truc cu la `self_calibrated` (DEPRECATED), w_loss thay doi theo cell. Truc
moi la `exogenous_g114_S-B`, w_loss=5000 dong nhat.

```text
M_53   rho_hit in [0.860,0.925]       ADJUDICATED: menh de ve MUC/BIEN cu
M_55   err_neo in [0.15,0.26]         ADJUDICATED: menh de ve MUC cu
M_48b  twin_deg spread in [1,1.3]     ADJUDICATED: menh de ve MUC cu

M_54   sign monotone theo rho          GIU: menh de DAI SO ve dau/thu tu
M_57   lift-swing < 0                  GIU: menh de ve dau
M_47b  delta <= 0 tren live heldout    GIU: menh de ve dau

M_56   h2 candidate live               VIET LAI: bao cao song theo A VA B
```

Nguyen tac: mot menh de chi song qua doi truc neu phep doi giu bat bien dung
dai luong ma menh de su dung. Dau/thu tu co the giu duoi bien doi don dieu
hoac phep ghep cap triet tieu truc; muc tuyet doi va bien so hoc thi khong.

## 3. Metric moi va nguon suy dai

`M-140` DA DUOC CAP cho `S_pivotal(poisson@0.875)` o amendment 23-53. De
khong tao va cham ma, bon metric moi dung dai ke tiep M-176..M-179:

| ID | Alias | Menh de da ky | Nguon DOC LAP co truoc run |
|---|---|---|---|
| M-176 | agreement | A va B dong y o >= 8/12 cell | Hai dinh nghia doc lap; dai 8..12 duoc chon truoc |
| M-177 | M_53' | `rho_hit` thuoc [0.900, 0.925] | B: poisson S_pivotal da do: 0.900 LIVE (0.324005), 0.925 COLLAPSED (0.00869) |
| M-178 | M_55' | err_neo cua p@0.875 VA p@0.900 moi gia tri thuoc [0.20, 0.30] | U3/S-B hang xom p@0.850=0.253484, p@0.925=0.238841; U0/S-B =0.261046/0.244516 |
| M-179 | M_48b' | spread twin_deg tren TAT CA cell A-live trong 12 cell thuoc [1.00, 1.50] | 8 cell U3/S-B da co: 1.216463; U0/S-B: 1.182298. Tran mo rong truoc khi them 4 cell |

M-177 khong vong tron: dai suy tu B (`S_pivotal`), con `rho_hit` do bang A
(`lift-swing`). Suy dai tu chinh `lift-swing` cua bon parquet Dot 4 sap sinh
roi cham lai no MOI la vong tron.

M-178 noi suy tu HAI DAU MUT da co tren cung truc/SLA/profile; khong dung
err_neo cua p@0.875/p@0.900 cu de dat bien. M-179 mo rong tran 1.216463 len
1.50 truoc khi biet twin_deg cua bon cell moi; metric moi gom ca 12 cell,
khong lap lai dinh nghia cu chi gom `E.ALL_CELLS`.

## 4. Truc va pham vi cell

Giu nhan `exogenous_g114_S-B` cho manifest moi. Nhan mo ta hop dong
`T_delay=50ms, T_loss=1%, w_loss=5000`; them cell chi doi pham vi lay mau,
khong tao hop dong moi. Registry co hai path, cung label, hai digest.

Hai dinh chinh so voi ban huong dan:

1. `sla_manifest_exogenous.build()` hien tra 12 cell, trong do 10 feasible.
   Manifest moi loc 10 feasible roi noi 4 Dot 4 -> DUNG 14 cell, khong phai
   noi ca 12 thanh 16.
2. Bao cao wave4 da duoc promote, path authoritative hien tai la
   `results/LIVE/phase-23/sla_exogenous_wave4.json`, khong phai PENDING.

Sweep ket qua bao cao 12 gate cell: 8 cell `E.ALL_CELLS` + 4 Dot 4. Hai cbr
feasible trong manifest giu vai tro pc1/ngu canh SLA, khong vao sweep.

## 5. Gate va tieu chi DUNG

```text
G23-226  12/12 job Dot 4 qua G1..G4; digest ghim; backup logic hoan tat.
G23-210  manifest 14 cell: 14 feasible, 4 Dot 4, 0 duplicate, w=5000;
         0 fixpoint, 0 derived, 0 ngoai whitelist.
G23-211  --prepare-sla fail loud; --calib-template duoc doc that.
G23-212b live_region tren 8 cell cu + manifest 10-cell semantics phai khop
          G23-212a ve A: NHOM A lech 0, NHOM B trong dung sai G23-219.
G23-227  NC_H truth_domain_check chay 4/4 Dot 4. FAIL -> DUNG.
G23-213  sweep 12 cell sinh duoc bang A/B va cac metric moi.
G23-214  regime B ghep theo (mode,rho) khop authoritative S-B + wave4 12/12.
```

`G23-214` kiem hai DUONG CODE cung gan nhan B. `M-176` so dinh nghia A voi
B. Vi vay G23-214 co the fail do noi/gan nhan sai trong khi M-176 van tinh co
pass; trong tinh huong do artifact 12-cell KHONG duoc tin.

Thu tu dung cung:

```text
wave4 gate fail     -> DUNG, khong noi nguong G4=9
G23-210 fail        -> DUNG, khong dung manifest
G23-212b fail       -> DUNG, khong tin so 12 cell
G23-227 fail        -> loai cell theo luat da ky va bao cao nguyen
M-176/M-177/178/179 miss -> BAO CAO MISS, khong noi dai
```

## 6. Dich artifact

```text
manifest  results/LIVE/phase-20R/sla_manifest_exogenous_S-B_14cells.json
sweep     results/LIVE/phase-23/live_region_sweep_slaB.json
digest    results/RAW/phase-21R/WAVE4_DIGESTS.json
report    docs/phase-23/41-live-region-exogenous.md
```

`results/RAW` dang read-only theo G23-221. De tao ledger digest moi, chi mo
quyen ghi dung thu muc/file can thiet trong cua so ngan, sau do khoa lai va
chay custody gate. Khong sua/ghi de ledger cu.

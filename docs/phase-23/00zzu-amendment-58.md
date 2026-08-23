# AMENDMENT 23-58 -- Xoa truong PHAI SINH, van tay parquet, va ep float64

Ngay ky : 2026-08-23
Tag     : amendment-58
Lesson  : 23.21g
Loai    : SUA LOI DU LIEU + DONG `G23-174` + DONG `L69`
Prereq  : amendment-57 (`46ed9fb`)

Gop BA thay doi vao MOT amendment de chi phai rebuild MOT lan.

## 1. LOI: manifest mang truong PHAI SINH tu vong fixpoint

`measurements/sla_manifest_exogenous.py` xoa `fixpoint_*` -- tuc xoa theo TEN.
Nhung NAM truong khong mang tien to do VAN la san pham cua vong fixpoint:

```text
cell             opt_viol MANIFEST   opt_viol DUNG (S-B)
poisson@0.700          0.15000            0.00000
poisson@0.850          0.14999            0.03157
poisson@0.925          0.15000            0.99131
poisson@0.960          0.15000            1.00000
h2@0.700               0.14999            0.88881
h2@0.850               0.15000            1.00000
h2@0.925               0.15000            1.00000
h2@0.960               0.15000            1.00000
```

Manifest khai "duong toi uu vi pham SLA 15% thoi gian". Su that duoi `S-B` la
**99-100%**. Sai 6.7 lan, o dung dai luong ma `L61` noi ve.

```text
opt_viol_rate         dau ra cua vong bisection, bi EP ve `target_viol` = 0.15
in_band               suy tu `opt_viol_rate`
cost_margin_mean_ms   phu thuoc `w_loss` (cu 1245..4722, moi 5000)
cost_margin_p10_ms    nt
opt_path_share        argmin cost, ma cost phu thuoc `w_loss`
                      -> DANH TINH cua duong toi uu doi theo
```

`opt_path_share` nang nhat ve khai niem: `P1` cua `poisson@0.700` di tu 0.874
xuong 0.766. Manifest dang khai mot duong toi uu KHONG CON toi uu nua.

Va `config` con nguyen bo may fixpoint (`n_bisect`, `n_fixpoint`, `p_hi`,
`p_lo`, `target_viol`, `tol_w`, `viol_band`) canh `endogenous: false` -- mot
file TU MAU THUAN. Reviewer doc `target_viol: 0.15` se hoi ngay.

### Muc nguy hiem: KHONG hong SO, nhung hong NHAN

Do duoc: khong file nao trong `cert/` doc `opt_viol_rate`, `opt_path_share`,
`cost_margin_mean_ms`, `cost_margin_p10_ms`, `target_viol`.

```text
=> 16 artifact LIVE dung o amendment 23-57 DUNG VE SO. Khong phai lam lai
   vi ly do so hoc.
```

Nhung `measurements/sla_calib_v2.py` doc chung **21 lan** -- va do chinh la
code sinh BANG va HINH cho paper. Day la mot qua min hen gio, se no vao dung
luc muon nhat va dat nhat.

### Sua: XOA, khong tinh lai

```text
Cach 1 (BI LOAI): nap gia tri dung tu `sla_exogenous_S-B.json` vao manifest
    -> HAI nguon su that cho cung mot dai luong
    -> phu thuoc nguoc tang: LIVE/ doc PENDING/  (cam)
Cach 2 (CHON): XOA han, ghi con tro toi nguon co tham quyen
    -> manifest lam DUNG mot viec: DINH NGHIA truc SLA
       (chinh no da khai `axis_role = "measures_axis"`)
    -> "khong co du lieu" AN TOAN hon "du lieu sai": KeyError keu to,
       so sai thi im lang. Nguyen tac fail-loud, giong `L42`.
```

Han che moi: `L70`.

## 2. `G23-174` -- van tay cua DAU RA

`L51` ghi: report cu KHONG luu digest cua parquet. Do duoc tren report hien tai:

```text
provenance.sha256 = { build_calib_set_v3.py, margin_score.py,
                      sla_calibration.json, truth_table.parquet }
    -> tat ca deu la DAU VAO. KHONG co digest cua parquet DAU RA.
```

Report ghi van tay cua moi thu di VAO, nhung khong ghi van tay cua thu di RA.
Nen khi tim thay mot file parquet tren dia, KHONG co cach nao chung minh no la
file ma report do mo ta -- va doi chung am muc duong ong that bai IM LANG.

```text
QUYET DINH: them khoi `output` voi `parquet_sha256`, `parquet_bytes`,
            `n_rows`, tinh SAU khi ghi va flush -- tren BYTE THAT tren dia,
            khong tren DataFrame trong bo nho.
```

## 3. Dong `L69` -- ep float64 truoc khi tinh phan vi

`gap_true` la `float32`. `np.percentile` tren float32 tich luy trong float32:

```text
float32 -> 28.544876098632812
float64 -> 28.54488258361816
lech tuong doi 2.0e-07 = dung bac cua eps_float32 (1.19e-07)
```

Khong phai loi logic. Nhung no dat mot SAN NHIEU 1e-7 vinh vien duoi moi doi
chung am, nghia la mot loi THAT co do lon 1e-7 se an duoi san do.

```text
QUYET DINH: ep `float64` TRUOC khi tinh phan vi.
            Sau do chay lai NC. Neu `M-167` chuyen tu MISS sang HIT thi do la
            HIT SAU KHI SUA NGUYEN NHAN, KHONG phai sau khi noi nguong.
            Ghi CA HAI lan do.
```

## 4. HE QUA: luoi 8 cell goc gan nhu chet duoi nguong trung thuc

```text
cbr@0.700      TRIVIAL     poisson@0.925  COLLAPSED (opt_viol 0.991)
cbr@0.850      TRIVIAL     poisson@0.960  COLLAPSED (1.000)
poisson@0.700  TRIVIAL     h2@0.850/0.925/0.960  COLLAPSED (1.000)
poisson@0.850  ★ LIVE      h2@0.700       AMBIGUOUS (CI chua 0.10)

1 LIVE · 1 AMBIGUOUS · 3 TRIVIAL · 5 COLLAPSED
```

Toan bo Phase 22 va Phase 23 chay tren luoi nay. Duoi nguong trung thuc, 6/8
cell la bai toan tam thuong hoac mang da sup.

```text
DAY LA MOT KET QUA, KHONG PHAI MOT TAI NAN. Da duoc du bao o `L54` va `K3`.
Nguong noi sinh khong chi lam THIEN LECH ket qua; no chon LUON CHO DE DO.
```

```text
QUYET DINH: KHONG chay ha nguon day du tren 8 cell cu -- 5 cell COLLAPSED
            cho ket qua vo nghia. Luoi chinh doi sang cell CO NGHIA.
            8 cell cu GIU nguyen duoi nhan ABLATION: bang "luoi goc duoi SLA
            ngoai sinh" la mot BANG CUA PAPER.
```

## 5. Du doan -- DIEN TRUOC KHI CHAY

| id | dai luong | loai | dai da ky | do duoc | KQ |
|---|---|---|---|---|---|
| M-172 | so truong so khop CHINH XAC trong NC (cu: 150/156) | CO CHE | >= 155/156 | | |
| M-173 | max\|diff\| cua NC sau khi ep float64 | CO CHE | < 1e-9 | | |
| M-174 | so truong phai sinh con sot trong manifest sau khi sua | CO CHE | 0 | | |
| M-175 | `parquet_sha256` khop byte tren dia o moi report moi | CO CHE | 100% | | |

```text
M-173  neu VAN ~1e-6 thi float64 chua an het, con cho khac dung float32.
       KHONG duoc noi nguong; phai tim cho do.
```

## 6. Gate

| id | noi dung | nguong |
|---|---|---|
| G23-196 | manifest KHONG con truong phai sinh tu SLA cu | bat buoc |
| G23-197 | `config` cua manifest KHONG con bo may fixpoint | bat buoc |
| G23-198 | moi calib report mang `output.parquet_sha256` (= `G23-174`) | bat buoc |
| G23-199 | parquet tren dia KHOP digest da ghi | bat buoc |
| G23-200 | NC duong ong sau khi ep float64 | max\|diff\| < 1e-9 |
| G23-201 | hai report KHONG duoc cung khai mot parquet | bat buoc |

`G23-198`/`G23-199` dong `G23-174` va mo duong cho `M-135`/`M-136`.

## 7. Nguyen tac moi

```text
NT 50 -- Khi thay mot gia tri NGUON, phai liet ke va xu ly moi truong
         PHAI SINH tu no. XOA THEO NGHIA, khong xoa theo TEN.

Xoa `fixpoint_*` la xoa theo ten. `opt_viol_rate` khong mang tien to do
nhung van la con de cua vong fixpoint. Cach kiem doc lap duy nhat: chay lai
phep tinh duoi gia tri MOI, so tung truong; truong nao doi thi truong do
LA phai sinh.
```

## 8. Han che moi

```text
  L70  Manifest ban dau (amendment 23-57) mang NAM truong phai sinh
       (`opt_viol_rate`, `in_band`, `cost_margin_mean_ms`,
       `cost_margin_p10_ms`, `opt_path_share`) va BAY khoa `config` cua vong
       fixpoint. `opt_viol_rate` ghi 0.15 trong khi su that duoi `S-B` la
       0.99-1.00. KHONG hong SO (duong ong khong doc chung) nhung hong NHAN
       (`sla_calib_v2` doc 21 lan de sinh bang/hinh paper).
```

## 9. Dieu KHONG lam

```text
- KHONG noi nguong `M-167`/`M-173` de bien MISS thanh HIT.
- KHONG nap gia tri dung tu `sla_exogenous_S-B.json` vao manifest (muc 1).
- KHONG xoa 8 cell cu: chung la BANG ABLATION cua paper (muc 4).
- KHONG chay lai 16 artifact vi ly do SO -- chung dung. Chay lai vi
  manifest doi sha va vi ep float64.
```

So ke tiep: `L71`, gate so 202, `M-176`, `K08`.

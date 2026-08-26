# AMENDMENT 23-70b -- Lesson 23.22d: M-210 tren cua so DO DUOC

Ngay ky : 2026-08-26

Moc     : sau `G23-277` PASS, truoc mot dong ma cham diem nao cua A070b

Loai    : TIEN DANG KY

## 0. Disclosure

### 0.1. DA XEM

`err_neo`, `n_calib_blocks`, `build_seconds` cua CA 12 cell nhanh W
(`a070_window_allowlist.json`, allowlist ba truong cua `A070` muc 2.2), va
`err_neo`/`kappa_A` cua 15 cell cu (12 A069/A068 + 3 cell song moi).

Da suy tu do: cua so chong lan do duoc `[0.7416, 0.7529]`, rong 0.0113
(`L111`); do nhay theo san song (`L112`); h2 bao hoa tai ~0.0394.

### 0.2. CHUA XEM

`kappa_A` cua 12 cell W -- KHONG thuoc allowlist `A070` muc 2.2 va chua
duoc giai niem. Va moi dai luong cham diem cua 12 cell W: `viol|accept`,
`acceptance`, `err|accept`, `anchor_err`, `qhat_source`.

Vi vay `M-210` VAN cham MU duoc: bien hoi quy `|log(kappa_A/kappa_B)|` va
bien phu thuoc `|acceptance_B - a*|` deu chua bi in.

## 1. Vi sao amendment nay ton tai

`A069` ky `M-210` phu thuoc dieu kien chong lan; `M-209` MISS o do phan
giai 0.040 nen `G23-271` bi dat NOT_RUN (`L109`). `G23-277` da chung minh
cua so TON TAI tai `rho` thuoc {0.744, 0.750}. Dieu kien tien quyet cua
`M-210` nay da DAT, nen no duoc mo lai -- va chi mo lai `M-210`, khong keo
theo `M-211`..`M-214` (chung thuoc nhanh E, ky rieng o `A070` muc 3).

Day la cau hoi ma `L92` thuc su muon: tai `rho` CO DINH, doi HO TAI co lam
thay doi quan he da do o Task B-3 khong. Truoc `G23-277` cau hoi nay khong
hoi duoc, vi khong co `rho` nao ca hai ho cung song.

## 2. Tap cell

```text
OVERLAP-4 (cell duy nhat pha duoc confound ho x tai):
    poisson@0.744, h2@0.744, poisson@0.750, h2@0.750
LIVE-15 = 8 cell A068 + 3 cell song A069 + OVERLAP-4
    (h2@0.740 cua A069 va h2@0.744 cua A070 la HAI cell khac nhau)
```

Moi cell dung parquet DA SINH; A070b KHONG sinh du lieu moi, nen khong co
pha sealed. `kappa_A` giai bang `RT.solve_kappa` tai `a* = 0.42679`.

## 3. Du doan

```text
M-222  MU. Nang luc cap GIUA HO tai cung rho (hoi sinh dieu kien M-209).
       Tren OVERLAP-4, tai n=250: so cap A->B GIUA HO co
       `viol|accept <= 0.10` VA `acceptance >= 0.20` phai >= 2.
       (Toi da co the dat 8 cap co huong giua ho.)
       [RUI RO] neu acceptance sup duoi san o cac cell nay thi MISS du cua
       so ton tai theo `err_neo`; do se la mot ket qua ve KHOANG CACH giua
       "song theo err_neo" va "dung duoc de chuyen giao".

M-223  MU. `M-210` nguyen van, tren LIVE-15, n=500, moi o ngoai cheo:
       hoi quy `|acceptance_B - a*|` tren `|log(kappa_A/kappa_B)|`
       (a) slope thuoc [0.40, 0.62]
       (b) them bien nhi phan cung_ho/khac_ho:
           |he so| <= 0.02 VA delta R^2 <= 0.02
       (c) Spearman >= +0.90
       HIT khi ca ba dat.
       Neu (b) MISS: ho tai la mot truc DOC LAP va `M-202` cua Task B-3 la
       hieu ung GHEP. `A069` da ghi truoc rang day quan trong hon null HIT.

M-224  MU. Doi chieu CUNG-RHO -- phep do duy nhat khong bi confound.
       Chi tren OVERLAP-4, tach theo tung rho thuoc {0.744, 0.750}:
       residual cua `|acceptance_B - a*|` sau khi tru mo hinh slope cua
       (a), so giua cap CUNG HO va cap KHAC HO.
       HIT khi |median residual khac_ho - median residual cung_ho| <= 0.02
       o CA HAI rho.
       Day la ve chat nhat cua A070b: `rho` bi giu CO DINH bang thiet ke,
       khong bang hieu chinh hoi quy.

NC-W-1  AM. Doi chung: neu thay bien ho tai bang mot nhan NGAU NHIEN co
       cung ti le (seed 232301), |he so| va delta R^2 phai roi vao cung
       dai da ky o (b). Neu nhan ngau nhien CUNG "khong co suc giai thich",
       ve (b) khong phan biet duoc gi va `M-223`(b) KHONG duoc trich dan
       nhu bang chung -- cung hinh dang `L99`/`NC-B3-1`.
```

STOP-RULE A070b: `M-222` MISS -> `M-224` khong cham (khong du cap giua ho),
ghi NOT_RUN co ly do; `M-223` VAN chay vi no dung LIVE-15 chu khong chi
OVERLAP-4. Stop-rule gan TUNG DU DOAN, theo `L109`.

## 4. No ghi truoc

```text
N1  Bien tren cua so dua tren MOT cell `h2@0.750` du san 0.0041, khong CI
    (`L112`). Neu `M-222`/`M-224` HIT, phat bieu van bi rang buoc boi do
    mong nay va phai in kem.
N2  OVERLAP-4 chi co 2 rho x 2 ho. Moi phat bieu cua `M-224` la ve HAI
    diem tai, khong phai ve mot vung.
N3  `M-223` va `M-224` dung CUNG mot tap cell; chung KHONG doc lap. Bao cao
    ca hai, khong gop thanh mot ket luan.
N4  Sau A070b, 12 cell W cung se CAN nhu ba cell A069 (`N4` cua `A069`).
```

## 5. Gate

| Gate | Noi dung |
|---|---|
| G23-285 | `M-222`, nang luc cap giua ho tai cung rho |
| G23-286 | `M-223`, `M-210` nguyen van tren LIVE-15 |
| G23-287 | `M-224`, doi chieu cung-rho |
| G23-288 | `NC-W-1`, doi chung nhan ngau nhien |

# Lesson 23.21d -- Mien song la mot MAT PHANG, va hai truc do hai thu khac nhau

Ngay    : 2026-08-23
Khoa boi: `00zzr-amendment-55.md` (tag `amendment-55`, commit `6df4c83`)
Artifact: `results/PENDING/phase-23/t_loss_local_fine.json`,
          `results/PENDING/phase-23/rho_grid_sigma_low.json`,
          `results/PENDING/phase-23/sigma_rho_plane.json`

## 1. Ket qua mot dong

```text
Sau khi sua dai luong vong tron, luan diem song nui MANH HON: tai nguong tu
hieu chuan, moi cell dat trung vi 93.6% muc huu ich toi da. Va luoi 2D cho
thay `S_pivotal` va `V` dat cuc dai o HAI CHO KHAC NHAU -- xac nhan `L55`
bang do luong thay vi bang lap luan.
```

## 2. Doi chieu du doan da ky

| id | dai da ky | do duoc | KQ |
|---|---|---|---|
| M-154 | trung vi `efficiency` tren 8/8 cell >= 0.90 | **0.9356** | **HIT** |
| M-155 | so cell `efficiency` >= 0.85: >= 7/8 | **7/8** | **HIT** |
| M-156 | dinh `h2` o `sigma` = 0.010 thuoc [0.60, 0.65] | **0.625, KEP DUOC** | **HIT** |
| M-157 | ty le o SONG tren luoi 2D thuoc [0.15, 0.50] | **0.2463** (33/134) | **HIT** |
| M-158 | mien song LIEN THONG | 8-lien-thong **CO**; 4-lien-thong `h2` tach 2 | **HIT\*** |
| M-159 | dinh `V` KHONG trung dinh `S_pivotal` | **KHONG trung, ca hai ho** | **HIT** |
| M-160 | Spearman(`t_endo`, `T*`) >= 0.95 | **0.9940** (8 cap) | **HIT** |

## 3. `G23-175`/`G23-176` -- dai luong dung, va no lam luan diem MANH HON

```text
cell             efficiency = S_piv(t_endo) / max_T S_piv
poisson@0.700       0.9839
h2@0.700            0.9802
poisson@0.850       0.9716
h2@0.850            0.9464
poisson@0.925       0.9247
poisson@0.960       0.9103   <- luoi cuc bo 1.05x
h2@0.925            0.8859
h2@0.960            0.8215   <- luoi cuc bo 1.05x

trung vi = 0.9356      min = 0.8215      7/8 cell >= 0.85
```

```text
CAU DUNG: "Tai nguong ma thu tuc tu hieu chuan sinh ra, moi cell dat 82-98%
           (trung vi 94%) muc huu ich TOI DA co the dat duoc o cell do."
```

Cau cu -- *"`S_pivotal` tai `T*` nam trong [0.864, 0.993]"* -- da bi RUT:
`S_pivotal(T*)` la cuc dai theo dinh nghia, nen dung no de chung minh nguong
nam o cuc dai la vong tron (amendment 23-55 muc 1).

Ket qua chinh cua 23.21c (`M-147` = 0.2216) KHONG bi anh huong: no do KHOANG
CACH giua hai diem, khong dinh den gia tri tai cuc dai.

### Luoi cuc bo -- va mot lan noi luoi

```text
                dai ban dau        T*        o mut?   dai sau khi noi
poisson@0.960   [0.0400, 0.0560]   0.05360   CO   ->  [0.0400, 0.0900]  -> khong
h2@0.960        [0.1500, 0.2400]   0.21107   khong
```

Buoc nhay tai diem noi suy giam tu 0.49 xuong 0.1087 (`poisson@0.960`) va tu
0.99 xuong 0.2489 (`h2@0.960`). Hai gia tri `efficiency` gio doc duoc.

Dai ban dau cho `poisson@0.960` QUA HEP nen dinh roi dung mut phai. Theo
`G23-173`, cach xu ly dung la NOI LUOI, khong phai goi mut la dinh. Ghi lai vi
day la lan thu hai `G23-173` phai duoc ap trong cung mot lesson.

## 4. `G23-177` -- doi chung `sigma` = 0.010: dinh `h2` KEP DUOC hai phia

```text
ho h2, sigma = 0.010 CO DINH:
   0.600     0.625     0.650     0.675     0.700 ...
  0.96076   0.99994   0.46503   0.00151   0.00000
            ^^^^^^^ DINH, kep boi 0.600 va 0.650

ho poisson, sigma = 0.010:  dinh o rho = 0.850 (0.99230) -- y het luoi chinh
```

Dinh cua `h2` nam o `rho` = 0.625 o CA BA cach dat: luoi chinh (`a` = 0.9),
`sigma` = 0.020, va `sigma` = 0.010. VI TRI dinh BAT BIEN voi cach dat
`sigma`, du DO LON thi khong.

## 5. `G23-178` -- doi chung mien phi tai giao diem hai luoi

```text
h2@0.625:  sigma(a = 0.9) = 0.02006  ~  sigma co dinh = 0.020
   luoi chinh        S_pivotal = 0.98355
   luoi doi chung    S_pivotal = 0.98374
   lech = 1.9e-04
```

Hai luoi duoc chay bang hai duong code khac nhau (`a` co dinh vs
`sigma_override`) va CAT NHAU tai duy nhat mot diem. O do chung cho cung so.
Cong cu tu kiem chinh no -- day la mot `NC` that, khong phai mot trung hop.

## 6. `G23-179` -- MIEN SONG tren mat phang `(rho, sigma)`

```text
poisson   (# = LIVE, o = chet, . = sigma > sigma_max)
 sigma  0.600 0.625 0.650 0.675 0.700 0.750 0.800 0.850 0.900 0.925
 0.072      .     .     .     .     .     .     #     .     .     .
 0.058      .     .     .     .     .     #     #     .     .     .
 0.046      .     .     .     .     o     o     #     #     .     .
 0.036      .     .     .     o     o     o     #     #     .     .
 0.028      .     .     o     o     o     o     #     #     #     .
 0.020      .     o     o     o     o     o     o     #     #     o
 0.016      .     o     o     o     o     o     o     #     o     o
 0.012      o     o     o     o     o     o     o     #     o     o
 0.008      o     o     o     o     o     o     o     #     o     o
 0.004      o     o     o     o     o     o     o     #     o     o

h2
 sigma  0.600 0.625 0.650 0.675 0.700 0.750 0.800 0.850 0.900 0.925
 0.046      .     .     .     .     #     o     o     o     .     .
 0.036      .     .     .     #     o     o     o     o     .     .
 0.028      .     .     #     #     o     o     o     o     o     .
 0.020      .     #     #     o     o     o     o     o     o     o
 0.012      #     #     #     o     o     o     o     o     o     o
 0.004      #     #     #     o     o     o     o     o     o     o

ty le o SONG = 33 / 134 = 0.2463
```

Ca hai ho cho mot SONG NUI CHEO: khi `sigma` tang, mien song TRUOT sang `rho`
CAO hon. `poisson` truot tu 0.850 (moi `sigma`) sang 0.750-0.800 o `sigma`
cao; `h2` truot tu 0.600-0.650 sang 0.700.

```text
=> Cau "vung song nam o rho thuoc [x, y]" la KHONG DAY DU (`L62`), va gio ta
   biet vi sao: no la mot lat cat NGANG cua mot song nui CHEO. Lat cat o
   `sigma` nao thi ra dai `rho` do.
```

`M-158`: mien song 8-LIEN THONG o ca hai ho. Voi `h2`, 4-lien-thong tach lam
HAI phan -- cho tach nam dung tren duong cheo, tuc do phan giai luoi chu khong
phai mot dut gay that. Ghi `HIT*`, va can luoi min hon de khang dinh.

## 7. `G23-180` -- `S_pivotal` va `V` dat cuc dai o HAI CHO KHAC NHAU

```text
ho        dinh S_pivotal              dinh V
poisson   rho=0.850  sigma=0.004      rho=0.850  sigma=0.046   V = 0.4120
          S = 1.0000                  S = 0.8944
h2        rho=0.600  sigma=0.004      rho=0.650  sigma=0.028   V = 0.4460
          S = 1.0000                  S = 0.6685
```

`M-159` da ky "KHONG trung" -- va do duoc dung la khong trung, o CA HAI ho.

Doc cho dung, va day la ket qua co gia tri nhat cua ban nay:

```text
`S_pivotal` dat 1.0000 khi `sigma` -> 0. Luc do cac duong gan nhu TINH va
nguong nam len giua chung, nen "co duong dat, co duong khong dat" gan nhu
LUON dung. Nhung V o do chi 0.24-0.28: khong co gi de quyet dinh, vi thu tu
cac duong khong doi.

`V` dat cuc dai o `sigma` TRUNG BINH (0.028-0.046): du bien dong de thu tu
cac duong THAY DOI theo thoi gian, nhung chua du de moi duong cung te.

=> `S_pivotal` do CAC DUONG KHAC NHAU BAO NHIEU.
   `V` do CHON DUNG LOI BAO NHIEU.
   Chung KHONG phai mot dai luong. `L55` duoc xac nhan bang DO LUONG.
```

Day la ly do bang HAI CHIEU (`G23-167`) la dieu kien CAN ve logic, khong phai
mot cach trinh bay dep.

## 8. `G23-182` -- `M-148` doi ten cho khop dinh nghia

Truong cu `M148_n_within_one_octave = 6` khong khop dinh nghia nao ma ten no
goi y. Do duoc:

```text
|log2| <= 0.322  (MOT BUOC LUOI)  ->  7/8 cell
|log2| <= 1.000  (MOT OCTAVE)     ->  8/8 cell
bracketed VA <= 1 octave          ->  6/8 cell   <- gia tri cu, ten sai
```

## 9. Dieu KHONG duoc ket luan

```text
- `M-153` GIU 4 cell, nhung cau giai thich "opt_viol < 1% la bai toan qua de"
  DA BI RUT (`L61`). `opt_viol` thap = ORACLE THANH CONG.
- Can duoi cua mien song ho `h2` van la artifact tham so hoa (`L59`):
  o `sigma` = 0.004 mien song cham `rho` = 0.600, la mut trai cua luoi 2D.
- `M-135` van khong dung duoc (`L57`).
```

## 10. Chua lam

```text
- Luoi 2D min hon quanh duong cheo cua ho `h2` (de chot 4-lien-thong).
- Mo rong luoi 2D xuong duoi `rho` = 0.600 (mien song ho `h2` cham mut trai).
- `G23-174` (test digest parquet) van NOT_RUN -> `M-135`/`M-136` van treo.
- Duyet truc: `approved_for_live` van rong. Artifact o `PENDING/`.
```

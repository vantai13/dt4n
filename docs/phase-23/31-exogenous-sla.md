# Lesson 23.21 -- SLA NGOAI SINH: dong S14, va mot co che bi BAC BO

Ngay    : 2026-08-23
Khoa boi: `00zzo-amendment-52.md` (tag `amendment-52`, commit `2ac8ec5`)
Artifact: `results/PENDING/phase-23/sla_exogenous_S-{A,B,C}.json`,
          `results/PENDING/phase-23/w_loss_sensitivity.json`

## 1. Ket qua mot dong

```text
S14 DA DONG: nguong SLA va w_loss gio la DAU VAO, khong con la nghiem cua
             mot vong diem bat dong.

Nhung du doan CO CHE cua chinh amendment 52 (M-138) bi BAC BO, va no keo
theo viec lap luan dang sau M-135 khong con dung vung.
```

## 2. Doi chieu du doan da ky

Ky luc `2ac8ec5`, do luc `--all-specs` chay xong. Khong dai nao bi noi.

| id | dai da ky | do duoc | KQ |
|---|---|---|---|
| M-133 | 3 cell COLLAPSED (dai 2..4) duoi S-B | **5** | **MISS** |
| M-134 | h2@0.850/0.925/0.960 CA BA COLLAPSED | ca ba COLLAPSED (`S_collapsed = 1.0000`) | **HIT** |
| M-135 | phan hoach S-B trung err_neo >= 0.05, >= 6/8 | **6/8** | **HIT** (sat bien) |
| M-136 | lift > swing bat bien qua sweep `w_loss` | -- | **BI CHAN** (muc 6) |
| M-137 | max \|dS_pivotal\| khi `w_loss` 1250 -> 20000 = 0 chinh xac | **0.0** | **HIT** |
| M-138 | `cost_margin(COLLAPSED) / cost_margin(LIVE) <= 0.50` | **2.7294** | **MISS, NGUOC DAU** |
| M-139 | max \|S_pivotal(S-A) - S_pivotal(S-B)\| <= 0.25 | **0.0** | **HIT** |

Ba HIT, hai MISS, mot bi chan. Bao cao NGUYEN ca hai MISS.

## 3. Bang chinh -- S-B (T_delay = 50 ms, T_loss = 1.0%, w = 5000)

```text
cell             regime       S_pivotal  S_trivial  S_collapsed  opt_viol
cbr@0.700        TRIVIAL         0.0000     1.0000       0.0000    0.0000
cbr@0.850        TRIVIAL         0.0000     1.0000       0.0000    0.0000
poisson@0.700    TRIVIAL         0.0033     0.9967       0.0000    0.0000
poisson@0.850    LIVE            0.8932     0.0754       0.0314    0.0316
poisson@0.925    COLLAPSED       0.0087     0.0000       0.9913    0.9913
poisson@0.960    COLLAPSED       0.0000     0.0000       1.0000    1.0000
h2@0.700         LIVE            0.1112     0.0000       0.8888    0.8888
h2@0.850         COLLAPSED       0.0000     0.0000       1.0000    1.0000
h2@0.925         COLLAPSED       0.0000     0.0000       1.0000    1.0000
h2@0.960         COLLAPSED       0.0000     0.0000       1.0000    1.0000

Tren TAM cell `gate`: 2 LIVE, 1 TRIVIAL, 5 COLLAPSED.
```

## 4. `M-138` -- co che duoc gia thiet bi BAC BO

Amendment 52 muc 6 dat gia thiet:

> `err_neo ~ 0` o cac cell `h2` tai cao KHONG phai vi "bai toan de" ma vi
> "mang da sup" -- khi moi duong deu te nhu nhau, `cost_margin` co lai nen
> chon sai ton rat it.

Do duoc, duoi S-B, tren tam cell `gate`:

```text
cost_margin_mean_ms, nhom COLLAPSED : 37.20  31.87  117.53  124.51  128.08
cost_margin_mean_ms, nhom LIVE      : 19.66  44.71

ti so mean(COLLAPSED) / mean(LIVE)  =  2.7294        du doan: <= 0.50
```

Khong nhung truot dai, no truot NGUOC DAU: bien chi phi o nhom sup **lon hon
2.7 lan**, khong phai nho di.

Doc cho dung: menh de "moi duong deu te nhu nhau" la SAI. Chung deu VI PHAM,
nhung vi pham voi muc rat khac nhau. Trong `cost = delay + w_loss * loss`, khi
`loss` vua cao vua tan mac giua cac duong, hieu giua duong tot nhat va duong
nhi lai GIAN RA. "Cung vi pham" khong keo theo "cung te".

```text
HE QUA: viec M-135 dat 6/8 KHONG duoc giai thich boi co che da de xuat.
        Hai phan hoach trung nhau, nhung LY DO thi chua biet.
        KHONG duoc viet trong paper rang chung trung nhau "vi mang sup".
```

Day la ly do `M-138` duoc ky nhu mot phep kiem CO CHE cua `M-135`: no ton tai
de tra loi cau hoi *trung nhau vi co che hay vi may man*. Cau tra loi do duoc
la: **khong phai vi co che nay**. Mot phep kiem lam dung viec cua no.

## 5. `M-139` va `M-137` -- hai so KHONG bang 0 mot cach tinh co

### S-A va S-B cho phan hoach TRUNG KHIT

```text
max |S_pivotal(S-A) - S_pivotal(S-B)| tren 8 cell gate = 0.0
phan hoach S-A == phan hoach S-B                        = True
```

Ly do doc duoc tu artifact cu: moi `t_delay` do duoc nam trong `[12.5, 47.2]`
ms, deu DUOI 50 ms. Nen o ca S-A (150 ms) lan S-B (50 ms), rang buoc TRE gan
nhu khong bao gio can; rang buoc duy nhat con hieu luc la MAT GOI, va hai spec
dung chung `T_loss = 1%`.

Dieu nay co gia tri cho paper: ket luan duoi S-B **khong nhay** voi viec chon
150 ms hay 50 ms lam ngan sach tre. Cau hoi "sao anh chon dung 50 ms" mat suc
nang -- trong khoang do, cau tra loi khong doi.

Doi lai, S-C (20 ms, 0.1%) doi that: 7 COLLAPSED thay vi 5, va `poisson@0.700`
nhay tu TRIVIAL sang LIVE. Cai lam ket luan doi la `T_loss`, khong phai
`T_delay`.

### `S_pivotal` bat bien voi `w_loss` -- do duoc dung bang 0

```text
G23_160_S_pivotal_max_dev = 0.0   qua w_loss in {1250, 5000, 20000}
```

Day KHONG phai may man va cung khong phai mot phat hien thuc nghiem: no la he
qua truc tiep cua viec `regime_shares()` khong nhan `w_loss` va khong nhan
`opt`. Ve mat kieu du lieu no KHONG THE phu thuoc vao chung.

```text
Cach manh nhat de dam bao mot bat bien khong phai la KIEM no, ma la lam cho
no khong the bi vi pham.
```

`test_regime_shares_signature_has_no_w_loss` khoa tinh chat do o cap chu ky
ham -- cung ky thuat da dung o `G23-115` (chan `L36` o KIEU du lieu chu khong
o gia tri). Con so `0.0` chi la xac nhan rang lap luan da duoc cai dat dung.

## 6. `M-136` BI CHAN -- va vi sao khong lam bua

`M-136` (lift > swing bat bien qua sweep `w_loss`) can chay
`cert.eight_cell_sweep` ba lan. Tam file calib can thiet KHONG co tren dia:

```text
results/SUPERSEDED/phase-22/calib_set_v3.parquet                 THIEU
results/SUPERSEDED/phase-22/calib_set_v3_{poisson,h2}_*.parquet  THIEU  (7 file)
```

Amendment 23-49g them chung vao `.gitignore` (38 duong parquet, 1.92 GB, lam
`git push` bi GitHub chan) kem ghi chu *"File tren dia giu nguyen; dung lai
bang `tools/run_23_20_matrix.py` khi can"*. Tren may nay chung khong con.

```text
QUYET DINH: bao cao M-136 la BI CHAN, khong dung so thay the.
```

Dung lai duoc bang `tools/run_23_20_matrix.py`, nhung do la dung lai duong ong
Dot 1 cua Lesson 23.20 -- mot thao tac RIENG, va neu ban dung khong khop tham
so goc thi doi chung am `G23-159` o muc duong ong tro thanh vo nghia mot cach
IM LANG. Do la rui ro te hon viec de trong mot o trong bang.

## 7. Doi chung

### `G23-159` -- tai tao artifact NOI SINH cu

Nap lai nguong + `w_loss` cu vao duong ong MOI, o dung `n` va `seed` cua
artifact cu:

```text
NC1_n_cells         = 10        ca 10 cell kha thi
NC1_max_d_opt_viol  = 0.0       CHINH XAC
NC1_max_d_share     = 0.0       CHINH XAC (4 duong x 10 cell)
NC1_max_d_margin    = 2.84e-14  KHONG phai 0
```

Ghi dung `2.84e-14` chu khong lam tron thanh `0.0`. Do la sai so cong don dau
phay dong khi lay trung binh 200 000 so thuc -- thu tu cong doi bit cuoi.
Nguong test la `1e-9`, tuc con chat hon sai so do NAM bac. Hai dai luong kia
la trung binh cua bool/dem nen chung bang 0 dung nghia den.

Mot loi nho trong ban nhap `selftest`: no truyen `n` tu CLI vao NC-1. Chay o
`n = 20 000` thi NC-1 "do" voi `d_opt_viol = 0.035` -- do vi SO MAU khac, chu
khong vi logic khac. Da sua thanh luon dung `n`/`seed` cua artifact cu. Mot
phep kiem do SAI LY DO con te hon mot phep kiem khong do.

### Doi chung khac

```text
NC2  S_trivial + S_pivotal + S_collapsed - 1 = 0.0   (10/10 cell)
PC1  SLA bat kha thi (0 ms, 0%)   -> S_collapsed = 1.0   (2/2 cell)
PC2  SLA de vo han (inf, 100%)    -> S_trivial   = 1.0   (2/2 cell)
```

`PC1`/`PC2` chung minh cong cu co SUC PHAN BIET o ca hai dau suy bien. Mot
cong cu khong bao gio tra `COLLAPSED` thi viec no tra `LIVE` khong co nghia.

### Doi chung duong (moi test phai thay DO it nhat mot lan)

```text
DC15  PIVOTAL_MIN 0.10 -> 0.15              -> DO
DC16  them `w_loss` vao regime_shares        -> DO
DC17  gan role = regime                      -> DO
DC18  doi mot hang so trong ar1_matrix       -> DO
DC19  import solve_percentile                -> DO
DC20  doi LOSS_EXCHANGE trong sla_calib_v2   -> DO
```

## 8. Han che

```text
  L46  S_pivotal do tren mo hinh rho DOC LAP theo link (S13 / L44, chua sua).
     Tuong quan tai that lam cac duong vi pham DONG THOI nhieu hon, nen
     S_pivotal THAT nho hon so o bang muc 3. Uoc luong hien tai la CAN TREN.
     Dieu nay lam ket luan "5 cell COLLAPSED" tro thanh CAN DUOI cua so cell
     that su sup -- tuc M-133 co the con truot XA hon.
  L47  Nguong ITU-T G.114 la ngan sach cho THOAI; topology_v7 khong duoc dac ta
     la thoai. Muon nguong nay la mot ANH XA hop ly, khong phai dac ta hop dong.
  L48  DINH CHINH amendment 52 muc 3: can duoi sweep 1250 KHONG bao 1245.6.
     So 1245.6 la cua hai cell `cbr` role=`pc1`; tam cell `gate` co dai
     [1656.4, 4722.7] va 1250 bao tron dai do. Sweep VAN du cho pham vi
     ket luan; chi cau chu trong amendment la thieu chinh xac.
```

## 9. Chua lam

```text
- M-136 va doi chung am o muc DUONG ONG: can dung lai 8 calib parquet (muc 6)
- Duyet truc: `approved_for_live` van RONG ca hai truc. Artifact cua lesson
  nay nam o PENDING/, KHONG phai LIVE/. Viec duyet la mot amendment RIENG,
  ky SAU khi doi chieu xong -- amendment 52 muc 10.
- L40 / L41 chua dong: ca hai can ket qua ha nguon duoi SLA moi.
```

Artifact cua lesson nay o `PENDING/` khong phai vi no kem, ma vi tai thoi diem
sinh ra `approved_for_live.sla_axis` con rong. Day la lan dau tang `PENDING`
(dung o `G23-136`) duoc dung THAT thay vi dien tap.

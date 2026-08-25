# AMENDMENT 23-67 -- ba han che cua Task B, va ba du doan ky lai

Ngay ky : 2026-08-25
Lesson  : 23.22 Task B (dinh chinh) + Task B-2 (tien dang ky)
Loai    : GHI HAN CHE + TIEN DANG KY
Moc     : sau `1d36622`

## 0. Disclosure

DA XEM: toan bo `transfer_matrix.json`, gom `T3` cua 56 o ngoai duong cheo,
phan tang theo huong va theo ti le thang `qhat`. Phat hien o muc 5 la
**POST-HOC** -- no den TU viec nhin so, khong tu mot gia thuyet co truoc. Do
la ly do no phai duoc ky lai va cham tren tap CHUA XEM.

CHUA XEM:

```text
`T3` cua 16 o trong ma tran 4x4 cell CHET. `run()` co tinh `dead_cellwise`
     nhung chi ghi TRUNG VI cua `T1_drift` vao artifact (`NC_1_dead_cell_
     control` co dung bon khoa: n_cells, median_drift_C3, median_drift_B2,
     hit). Khong mot gia tri `T3` nao cua cell chet duoc ghi hay in ra.
     -> `M-197` cham duoc MU tren tap nay.

`median(m_hat_1)` theo cell. Chua tinh bao gio.
     -> menh de 1 cua `M-198` MU hoan toan.

Moi dai luong cua Task B-2. `cert/recalibration_cost.py` chua ton tai.
     -> `M-199` MU.
```

⚠️ **Mot disclosure phai noi ro** (muc 6.2): menh de 2 cua `M-198` dung BIEN
KET QUA da xem (dau cua `viol - alpha` tren 56 o). No khong mu. Cai mu la
menh de 1; menh de 2 gan nhu la he qua cua menh de 1 neu menh de 1 trung.
Ghi ro de khong ai dem no thanh mot xac nhan doc lap.

## 1. L97 -- tien de cua `M-194` sai ve CAU TRUC, suy ra duoc TRUOC khi chay

`A066` muc 1.2 lap luan:

```text
C3 :  chap nhan <=> m_hat_j / qhat_j >= kappa      TI SO,  bat bien thang
B2 :  chap nhan <=> m_hat_1 >= c                   NGUONG TUYET DOI
```

**Nhung trong ma tran chuyen giao, `qhat` bi DONG BANG tu cell A.** Khi do:

```text
m_hat_j / qhat_j^A >= kappa    <=>    m_hat_j >= kappa * qhat_j^A
                                                  ^^^^^^^^^^^^^^^ HANG SO
```

C3-voi-`qhat`-dong-bang **cung la mot nguong tuyet doi**. Khac biet duy nhat
so voi B2: no la mot nguong tuyet doi theo `z_bin` va theo slot, con B2 la
MOT nguong toan cuc. Ca hai deu co thu nguyen; ca hai deu troi.

Do duoc: ti so trung vi 1.04x, va hai phan phoi chong khit.

```text
        min      q1      trung vi     q3      max
  C3  0.0047  0.1293    0.2090     0.3324  0.5186
  B2  0.0054  0.1292    0.2174     0.3398  0.5291
```

`A066b` bat dung nua lap luan nay cho `NC-3`, va tu do da suy ra `NC-3b`
("mang nguyen -> ca hai troi"). Nua con lai -- rang chinh KHOI CHINH cua ma
tran chay o che do `NC-3b` -- khong duoc rut ra khi soan `A066`.

> 🔑 **`M-194` MISS KHONG phai mot ket qua thuc nghiem.** No la mot he qua cau
> truc le ra phai suy duoc truoc khi chay. Doc 44 phai bao cao no nhu vay,
> KHONG duoc viet "chung toi kiem va thay B2 chuyen giao tot nhu C3".

Nguyen tac tong quat de ghi lai:

> Mot tinh chat cua LUAT khong tu dong la tinh chat cua LUAT VOI THAM SO DONG
> BANG. Dong bang mot tham so co thu nguyen bien mot quy tac bat bien thanh
> mot quy tac co thu nguyen.

## 2. L98 -- ve thu ba cua `M-193` do NHIEU TACH MAU, khong do wiring

```python
"hit": bool(max(d_viol) <= 1e-9 and max(d_acc) <= 1e-9 and max(b2_off) <= 0.02)
```

Hai ve dau la kiem wiring THAT, va chung PASS tuyet doi:

```text
max_abs_delta_violation_C3   = 0.000e+00     8/8 o
max_abs_delta_acceptance_C3  = 0.000e+00     8/8 o
```

Duong cheo tai tao **tung bit** hang `variant_sweep` @ `kappa=0.5` cua
`taxonomy_audit.json`.

Ve thu ba fail o `0.0206 > 0.02`. Nhung `b2_off` la `T1_drift_B2` tren duong
cheo, tuc:

```text
| acceptance cua B2 do tren TEST  -  acceptance cua C3 do tren CALIB |
```

Do la nhieu tach `calib`/`test` cong khac biet quy tac (C3 dung ca ba slot voi
`.all()`, B2 chi dung `m_hat_1`). **Doi chung:** `T1_drift_C3` tren CUNG duong
cheo chay tu 0.0036 den **0.0173** -- cung co. Neu 0.0206 la bang chung wiring
hong thi 0.0173 cung phai la, ma ve C3 lai trung bit.

```text
Gate G23-248 GIU FAIL -- dai da ky, khong noi sau khi xem.
Nhung doc PHAI ghi ro duong ong KHONG hong, kem con so doi chung 0.0173.
```

Khong co cau do, nguoi doc thay "M-193 FAIL" se ket luan nguoc han su that.

## 3. L99 -- `T1` bi TOI DA HOA boi mot score DOC LAP DU LIEU

```text
trung vi T1_drift tren 30 o giua ho:
    B1  (score NGAU NHIEN)      1.19e-05     <- it troi nhat
    C3  (conformal)             0.2090
    B2  (nguong tuyet doi)      0.2174
```

`score_B1_random` la `U(0,1)` o MOI cell, nen phan phoi cua no khong doi khi
che do doi, nen mot nguong hoc tren A cho dung ti le chap nhan tren B. Day
KHONG phai hien vat cua phep do (da sua mot hien vat nhu vay -- xem muc 3.1);
day la tinh chat THAT cua mot score doc lap du lieu.

> **Moi thang do co dang "X thay doi it den dau" deu duoc toi da hoa boi mot
> quy tac KHONG NHIN VAO DU LIEU.** Mot thang on dinh khong co so hang huu ich
> thi toi uu cua no la hang so. `T1` KHONG duoc bao cao mot minh; no phai luon
> di kem mot SAN HUU ICH (`T2` hoac `T3`).

Cung hinh dang, lan thu ba trong do an:

```text
Phase 22    FCR giu bao phu 0.0160 << alpha bang cach chap nhan 9.9%
Lesson 22   V-S "giu 12/12" mot phan bang `qhat = max mau` / `+inf` (`L91`,`L93`)
Task B      B1 co drift nho nhat bang cach khong nhin du lieu
```

### 3.1. Mot hien vat DA sua truoc khi ket luan

Ban dau `T1_drift_B1` dung `BL._accept_at_coverage(sb1, acceptance_on_A)`,
phep do EP dung ti le chap nhan cua A nen drift = 0 **do dung**, khong do tinh
chat cua B1. Da doi sang mang mot NGUONG `c_B1` do tren A, y het B2. Ket qua
khong doi ve chat (1.19e-05), nhung nay no noi duoc dieu no khang dinh.

## 4. Sinh lai `g23_242_rerun_diff.json` -- ham thuan, tat dinh

Artifact do thieu khoi `validity` va lam `test_no_stale_axes` do tu `b9d2774`.
No KHONG chua so do: no la mot **ham thuan** cua hai artifact khac, ca hai
ghim bang hash (`old_provenance.blob = 1e715ff3...`). Sinh lai la tat dinh --
cung hai dau vao cho cung dau ra.

Da doi chieu truoc/sau khoa theo khoa:

```text
them : ["validity"]      bot : []      doi : []
G23_242_hit = True, n_frozen_violations = 0, n_cells = 12, blob khong doi
```

Nen day KHONG phai "sinh lai artifact cua mot vong da ky"; day la them mot
khoi khai bao vao dau ra cua mot ham thuan. Ghi o day de viec do khong bi doc
thanh sua lich su.

## 5. M-197 -- ky lai phat hien CO DAU  [POST-HOC o tap song, cham o tap CHET]

### 5.1. Phat hien (DA XEM -- khong dem diem)

```text
T3 (viol|accept cua C3) tren 30 o GIUA HO, alpha = 0.10:
  poisson -> h2   n=15   min 0.0000   trung vi 0.0113   max 0.5273
  h2 -> poisson   n=15   min 0.0002   trung vi 0.2786   max 0.8396
                                       chenh 25x

Tren 56 o ngoai duong cheo, phan tang theo TI LE THANG:
  qhat mang sang QUA LON (scale_B < scale_A)  n=28  trung vi 0.0027   vuot alpha  0/28
  qhat mang sang QUA NHO (scale_B > scale_A)  n=28  trung vi 0.3736   vuot alpha 27/28

  Spearman( log(scale_B/scale_A) , viol|acc ):
     30 o giua ho          = +0.9813
     56 o ngoai duong cheo = +0.9874
```

`scale(cell)` duoc DINH NGHIA CHOT o day, va no la mot dai luong cua Task A0
(khong phu thuoc Task B): `qhat_slot1_mean` cua bien the **V-M tai `kappa=0`**
trong `results/LIVE/phase-23/taxonomy_audit.json`.

```text
poisson@0.700   1.0467     h2@0.650   16.1809     poisson@0.900  34.4153
poisson@0.850  15.5590     h2@0.675   21.3514     poisson@0.925  44.1072
poisson@0.875  23.7692     h2@0.700   27.6184     poisson@0.960  62.3353
                           h2@0.850   52.7210     h2@0.925   60.5615
                           h2@0.960   65.4591
```

### 5.2. Vi sao bang cham khong thay

```text
M-194  dung |drift|           -> bo DAU. Troi len va troi xuong gop lam mot.
M-195  dung |viol - alpha|    -> xep 0.0027 (an toan thua) CUNG HANG voi
                                 0.3736 (vo tham hai). Ca hai deu "ngoai dai".
```

Cung hinh dang voi `NT 51` (`A063` muc 2) va voi bai hoc `M-186`: **mot dai
luong GOP che mot hieu ung don ve MOT PHIA.**

### 5.3. Du doan ky lai   [KY THAT -- cham tren tap CHUA XEM]

```text
M-197  Tren 16 o cua ma tran 4x4 cell CHET (`NC-1`, T3 chua xem):
       (a) Spearman( log(scale_B/scale_A) , viol|acc cua C3 ) >= +0.70
       (b) phan tach theo DAU: viol trung vi cua nhom "qhat qua nho"
           (scale_B > scale_A) LON HON cua nhom "qhat qua lon"

[CO CHE]  thang cua `qhat` la thang cua `s`. Mang mot nguong do o mot phan
          phoi NHO vao mot phan phoi LON thi nguong thieu -> `s > qhat` nhieu
          -> vo bao phu. Chieu nguoc lai la bao thu.
[CANH BAO] o cell chet `err_neo ~ 0` va acceptance ~ 1, nen bien do co the
          nho hon nhieu. Nguong +0.70 (khong phai +0.98) da tinh den dieu do.
```

Cham ca hai menh de; `M-197` HIT khi CA HAI dat.

## 6. M-198 -- canh bao som KHONG CAN NHAN

### 6.1. Vi sao no cuu duoc phien ban dung cua cau da rut

`A066` muc 1.1 rut cau "conformal khong can nhan", va rut dung: `qhat` la phan
vi cua `s`, ma `s` can `y_true`. Nen `scale_B/scale_A` **can nhan**.

NHUNG `m_hat` la dau ra cua CHINH twin -- **khong can nhan**. Neu thang cua
`m_hat` bam thang cua `qhat`, thi co mot chi bao KHONG CAN NHAN cho biet
`qhat` mang sang dang o phia nao cua ranh gioi.

### 6.2. Du doan

```text
M-198  (1) Spearman( log(median m_hat_1 theo cell) , log(scale theo cell) )
           >= +0.85 tren 12 cell.                        [MU hoan toan]
       (2) Dung TI LE m_hat thay cho ti le qhat de du doan DAU cua
           (viol|acc - alpha) tren 56 o: dung >= 48/56.   [KHONG MU -- xem duoi]
```

⚠️ **Menh de (2) khong mu.** Bien ket qua (dau cua `viol - alpha` tren 56 o)
DA XEM, va da biet ti le `qhat` du doan no gan nhu tat dinh (0/28 va 27/28).
Nen neu (1) trung thi (2) gan nhu la he qua. `M-198` duoc cham, nhung trong
doc phai ghi ro **chi (1) mang thong tin moi**; (2) chi kiem rang phep thay
the khong lam hong gi.

Neu `M-198` trung, phat bieu duoc phep la:

> C3 cho mot **chi bao khong can nhan** ve viec `qhat` da cu va dang o phia
> nguy hiem -- vi `m_hat` la dau ra cua chinh twin. B2 khong co gi tuong ung:
> `c` la mot hang so tu do, khong co dai luong dong hanh nao de so.

## 7. M-199 -- Task B-2: chi phi tai hieu chuan

Menh de con lai cua Task B noi B2 thieu *"mot thu tuc da biet kem yeu cau co
mau do duoc"*. Dieu do CHUA duoc do. Do duoc, tren cung parquet.

```text
Tren moi cell, lay `n` block calib co nhan, n thuoc {10, 20, 30, 60, 120, 250, 500}:
    C3:  hieu chuan lai `qhat_B(n)`               -> do viol|accept tren test
    B2:  do lai `c_B(n)` (khop acceptance)        -> do viol|accept va err
```

```text
M-199  Voi n < 29 block (san hop le cua `alpha/3`, `L91`):
       C3 gan co `qhat_has_infinite` HOAC `qhat_at_sample_max` o >= 90% so
       lan lay mau; B2 tra ve mot `c` HUU HAN o 100% so lan va KHONG co co nao.

[CO CHE]  day la menh de "yeu cau co mau DO DUOC" o dang kiem duoc. No gan
          nhu chac trung vi co che da cai trong ma (`L91`, `L93`). Do KHONG
          phai diem yeu: no bien mot khang dinh DINH TINH thanh mot phep do.
[NHAN]    KY THAT. `cert/recalibration_cost.py` chua ton tai khi ky.
```

Bao cao kem, KHONG cham diem (chua co dai da ky): `n` nho nhat de C3 dat
`viol <= alpha`, `n` nho nhat de B2 dat cung `err`, va do tan cua quyet dinh
theo `n` (block bootstrap) cho ca hai.

## 8. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-257 | `M-197` tren 16 o cell CHET: Spearman(log ti le thang, viol C3) >= +0.70 VA viol trung vi nhom "qhat qua nho" > nhom "qhat qua lon" | tat/bat |
| G23-258 | `M-198`: Spearman(log median `m_hat_1`, log `scale`) >= +0.85 tren 12 cell VA du doan dau dung >= 48/56 o | tat/bat |
| G23-259 | `M-199`: voi `n < 29` block, C3 gan co o >= 90% lan lay mau; B2 tra `c` huu han 100% lan va khong co co | tat/bat |

Ban thao noi bo cap `G23-255..257` cho ba du doan nay -- **va cham**:
`G23-255`/`G23-256` da duoc cap cho `NC-3a`/`NC-3b` o `A066b`. Cap lai tu
`G23-257`.

## 9. Pham vi anh huong

```text
KHONG doi mot con so nao cua `transfer_matrix.json` (se ghi THEM
    `dead_cellwise` de cham `M-197`; day la du lieu DA TINH nhung chua ghi).
KHONG doi phan quyet `G23-248..256`.
KHONG doi `g23_242_rerun_diff.json` ngoai khoi `validity` (muc 4).
Task B-2 la mot module MOI, khong dung vao duong ong Task B.
```

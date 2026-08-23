# AMENDMENT 23-53 -- doc lai ket qua 23.21: thang do, y nghia, phan loai hai chieu

Ngay ky : 2026-08-23
Tag     : amendment-53
Lesson  : 23.21b
Loai    : DINH CHINH DIEN GIAI + TIEN DANG KY
Prereq  : amendment-52 (`2ac8ec5`), Lesson 23.21 (`86b9a62`)

## 0. Ba hieu chinh so voi ban thao ngoai repo

```text
(a) "bon parquet Dot 4 DA TON TAI trong repo" -- SAI. Ca bon THIEU, cung tinh
    trang .gitignore nhu tam parquet cua M-136:
        calib_set_v3_poisson_0.875.parquet   THIEU
        calib_set_v3_poisson_0.900.parquet   THIEU
        calib_set_v3_h2_0.650.parquet        THIEU
        calib_set_v3_h2_0.675.parquet        THIEU
    KET LUAN cua ban thao van dung, nhung vi mot ly do KHAC: `sla_exogenous`
    KHONG doc parquet -- no sinh `rho` bang `ar1_matrix`. Nen [3] chay duoc,
    va chay duoc ma khong dung den mot file calib nao.

(b) "G23-159 / G23-160 hien dang la DEBT" -- SAI ma. Hai ma do la gate 23.21
    da PASS o commit truoc. No Dot 4 la `G23-141` / `G23-142` (lesson 23.20C).

(c) Chay `sla_exogenous` tren 4 cell moi KHONG tra duoc `G23-141`/`G23-142`.
    Hai ma do dinh nghia "Dot 4: 12 build" va "mo rong M-125a/b len 12 cell /
    48 o" -- ca hai can calib parquet. Do la mot phep do KHAC. Chung GIU DEBT.
```

## 1. `M-135` GIU nguyen HIT, nhung MAT gia tri bang chung

Do lai tren `sla_exogenous_S-B.json` + `M125b.counted_cells`:

```text
phan hoach SLA      LIVE = {h2@0.700, poisson@0.850}          2 vs 6
phan hoach err_neo  >=0.05 = {h2@0.700, poisson@0.850,
                              poisson@0.925, poisson@0.960}   4 vs 4
so trung = 6/8
```

Voi hai bien do co dinh, so trung KHONG tu do. Goi `X = |SLA_live ∩ err_alive|`:

```text
X = 0  ->  2/8 trung   P = 0.2143
X = 1  ->  4/8 trung   P = 0.5714
X = 2  ->  6/8 trung   P = 0.2143   <- ket qua

So trung chi nhan {2, 4, 6}. 6/8 la GIA TRI LON NHAT CO THE.
P(trung >= 6/8 | gan nhan NGAU NHIEN) = 0.2143
kappa = (0.7500 - 0.5000) / (1 - 0.5000) = 0.5000
```

Nguong ">= 6/8" duoc ky khi CHUA BIET bien se la 2-vs-6. Do khong phai gian
lan; do la mot nguong ky tren THANG DO SAI. So trung tho bi bien chan, nen no
la mot thang do toi cho muc trung khop; dai luong dung la mot he so DIEU CHINH
MAY RUI (`kappa`, `adjusted Rand index`).

```text
QUYET DINH: M-135 GIU nguyen HIT trong bang doi chieu (khong sua ket qua da ky).
            Nhung MOI phat bieu ve no PHAI kem kappa va P(ngau nhien).

            KHONG duoc viet: "SLA ngoai sinh XAC NHAN vung song cu."
            Cau dung duy nhat: "Hai phan hoach trung o muc TRAN CO THE DAT,
            nhung voi n = 8 va bien 2-vs-6, muc trung nay khong phan biet
            duoc voi ngau nhien (kappa = 0.50, P = 0.214)."
```

Han che moi: `L49`.

## 2. `h2@0.700` doi nhan `LIVE` -> `AMBIGUOUS`

```text
S_pivotal = 0.111235          PIVOTAL_MIN = 0.10       vuot 1.12 diem %
```

Nhung `n = 200 000` KHONG phai 200 000 quan sat doc lap. Chuoi `rho` la AR(1):

```text
phi   = exp(-dt/tau) = exp(-0.005/1.0) = 0.995012
n_eff = n (1-phi)/(1+phi) = 200000 x 0.005/1.995 = 500.0

sd(S_pivotal) = sqrt(0.111235 x 0.888765 / 500) = 0.01406
z = (0.111235 - 0.100)/0.01406 = 0.80 sigma
CI95 (xap xi chuan) = [0.0837, 0.1388]      <- CHUA nguong 0.10
```

Va hai tieu chi DA KY mau thuan nhau dung o cell nay:

```text
tieu chi CHINH    S_pivotal = 0.1112 >= 0.10          -> LIVE
tieu chi THU CAP  opt_viol  = 0.8888 ngoai [0.01,0.50] -> in_band = false

Cell DUY NHAT co in_band = true trong ca artifact: poisson@0.850.
```

```text
QUYET DINH: them muc `AMBIGUOUS` vao tu vung `regime`.
            PIVOTAL_MIN GIU NGUYEN 0.10 -- KHONG ha nguong.
            Doi TU VUNG de no noi duoc su that, khong doi NGUONG de ra
            ket qua mong muon.

            AMBIGUOUS := CI95 (block bootstrap) cua S_pivotal CHUA PIVOTAL_MIN.
            Ap cho MOI cell, khong rieng h2@0.700.
```

CI phai la BLOCK bootstrap voi block >> tau. `iid` bootstrap se cho CI hep GIA
khoang `sqrt(200000/500) = 20` lan. Block = 1000 buoc = 5 s >> tau = 1 s,
trung don vi block da dung o `L38`.

Han che moi: `L50`.

## 3. Truc TRE la mot RANG BUOC TRO (inert constraint)

```text
percentile_of_t_delay = 100.00   o CA 10 cell
```

Tre tren duong toi uu KHONG BAO GIO vuot 50 ms, o bat ky cell nao, trong
200 000 buoc. Nen `M-139 = 0.0` (S-A va S-B cho phan hoach trung khit) khong
phai bang chung ve do ben cua ket luan -- no la he qua cua viec ca 150 ms lan
50 ms deu nam TREN tran tre quan sat duoc.

```text
MANH: ket luan BAT BIEN voi T_delay tren toan dai [50, 150] ms -- DO DUOC,
      khong phai gia dinh. Cau hoi "sao chon 50 ms" da chet.
YEU : toan bo phan hoach treo tren MOT so: T_loss = 1%. Ba spec roi rac
      khong du -- S-C chi di MOT phia (chat hon).
```

```text
QUYET DINH: thay ba spec roi rac bang mot QUET T_loss lien tuc, T_delay giu
            50 ms. Chi phi ~0: delay/loss da tinh, chi doi nguong va dem lai.
            T_LOSS_GRID = (0.001, 0.002, 0.005, 0.010, 0.020, 0.050, 0.100)
```

## 4. Phan loai HAI CHIEU thay cho mot chieu

`poisson@0.925` co `err_neo = 0.2345` (chon sai duong TON NHIEU) va
`S_pivotal = 0.0087` (chon dung duong KHONG cuu duoc SLA). Hai so nay KHONG
mau thuan -- chung do HAI loai huu ich khac nhau:

```text
                     | err_neo < 0.05          | err_neo >= 0.05
---------------------+-------------------------+---------------------------
S_pivotal >= 0.10    | (du kien TRONG)         | SLA-PIVOTAL
                     |                         |
---------------------+-------------------------+---------------------------
S_pivotal <  0.10    | ON DINH / TAM THUONG    | HAN CHE THIET HAI
                     |                         | (damage-limiting)
```

`HAN CHE THIET HAI`: SLA da hong, khong cuu duoc hop dong, nhung chon dung
duong VAN giam duoc ton that. Day la mot che do van hanh CO THAT.

CA HAI nguong DA duoc ky truoc: `0.10` o amendment 52 muc 5, `0.05` o
amendment 23-49b muc 1. Day la GHEP hai tieu chi da ky, KHONG phai nguong moi.

O goc tren-trai duoc du kien TRONG, va do la mot TIEN DOAN kiem duoc: neu chon
dung duong quyet dinh SLA thi twin cu PHAI sai du nhieu de dang chung nhan.

## 5. Cell chu luc doi: `poisson@0.925` -> `poisson@0.850`

Ly do TIEN NGHIEM (ca hai tieu chi deu ky truoc khi do):

```text
poisson@0.850  S_pivotal = 0.8932   CAO NHAT trong 10 cell
               opt_viol  = 0.0316   cell DUY NHAT co in_band = true
               err_neo   = 0.2310   twin cu sai nhieu -> chung nhan co gia tri
```

CA TAM cell van duoc cong bo day du. Doi cell chu luc KHONG phai chon loc hau
nghiem KHI VA CHI KHI tieu chi chon la tien nghiem va toan bo bang duoc cong
bo -- ca hai dieu kien deu thoa.

## 6. Du doan -- DIEN TRUOC KHI CHAY

Co so duoc phep: `sla_exogenous_S-{A,B,C}.json`, `w_loss_sensitivity.json`,
`axis_remeasure_impact_wave1.json`. Chua co so nao cho 4 cell Dot 4.

| id | dai luong | loai | dai da ky | do duoc | KQ |
|---|---|---|---|---|---|
| M-140 | `S_pivotal(poisson@0.875)` | NGOAI SUY | >= 0.30 | | |
| M-141 | `S_pivotal(poisson@0.900)` < `S_pivotal(poisson@0.875)` | CO CHE | DUNG | | |
| M-142 | dinh cua `S_pivotal(poisson, rho)` nam trong | NGOAI SUY | `rho` thuoc [0.850, 0.900] | | |
| M-143 | `h2@0.700`: CI95 block bootstrap CO chua 0.10 | CO CHE | CO | | |
| M-144 | so cell doi nhan sang `AMBIGUOUS` sau block bootstrap | NGOAI SUY | 1 (dai 1..3) | | |
| M-145 | ti so bien-pivotal / bien-trung-binh >= 1 tren cell MOI | CO CHE | >= 3/4 cell co buoc pivotal | | |
| M-146 | so cell LIVE giam don dieu khi `T_loss` giam 10% -> 0.1% | NGOAI SUY | don dieu KHONG TANG | | |

Ghi chu:

```text
M-143  la phep kiem chinh cai xap xi chuan o muc 2. Neu block bootstrap cho
       CI KHONG chua 0.10 thi xap xi chuan sai, va quyet dinh AMBIGUOUS o
       muc 2 phai xem lai. Du doan "CO" nen no la du doan DE -- nhung cai
       dang kiem la SU NHAT QUAN cua hai phuong phap, khong phai do kho.

M-145  Tren du lieu 23.21 ti so nay >= 1 o CA 4 cell co buoc pivotal
       (1.045, 1.072, 1.608, 2.159). Do la quan sat HAU NGHIEM. Kiem lai
       tren cell MOI de tranh chinh vong tren cung du lieu.

M-146  `T_loss` cang chat -> cang nhieu duong vi pham -> nhieu cell COLLAPSED.
       Nhung `S_pivotal` la mot DINH, nen so cell LIVE co the tang truoc khi
       giam. Dai ky la "KHONG TANG" tren nua chat cua quet.
```

`R_stab` (ti so on dinh) la mot gia thuyet co che HAU NGHIEM sinh tu du lieu
23.21. No KHONG duoc ky o ban nay va KHONG duoc dung de dien giai 23.21.
Neu muon kiem, phai ky rieng o mot amendment sau va kiem tren du lieu MOI.

## 7. Gate

| id | noi dung | nguong |
|---|---|---|
| G23-162 | `kappa` + `P(ngau nhien)` ghi canh MOI phat bieu ve `M-135` | bat buoc |
| G23-163 | CI block bootstrap cho `S_pivotal`, MOI cell kha thi | bat buoc |
| G23-164 | tu vung `regime` them `AMBIGUOUS`; `PIVOTAL_MIN` KHONG doi | bat buoc |
| G23-165 | quet `T_loss` lien tuc, mot bang thay ba spec roi rac | bat buoc |
| G23-166 | 4 cell Dot 4 chay tren `sla_exogenous` | bat buoc |
| G23-167 | bang phan loai hai chieu, ca 8 cell, ke ca o TRONG | bat buoc |
| G23-168 | doi chung: `iid` bootstrap cho CI hep hon block bootstrap | bao cao |

`G23-168` la doi chung duong cho chinh muc 2: neu `iid` va `block` cho CI
BANG NHAU thi lap luan `n_eff = 500` sai, va phai rut.

`G23-141`/`G23-142` GIU nguyen `DEBT`: chung can calib parquet, ma
`sla_exogenous` khong dung den. Chay 4 cell moi KHONG tra hai mon no do.

## 8. Bai hoc phuong phap -- lop loi thu BA

```text
  L34   noi suy TUYEN TINH diem doi dau qua khoang 124 ms  -> M-127/128/130 MISS
  L35   mo hinh khop mean va p05, lech 4.1 sigma o p50/p95 -> M-110 chi 2/4
  M-133 suy ti le vuot nguong tu MOT phan vi               -> lech 10 lan
        (t_loss = 0.0292 tai p90.4 -> doan P(loss>1%) > 10%;
         thuc te percentile_of_t_loss = 0.869 -> P = 99.13%)
```

```text
QUY TAC MOI (ap cho phan con lai cua Phase 23):

  Moi du doan suy tu <= 2 diem cua mot phan phoi PHAI kem:
    (a) gia dinh hinh dang duoc ghi TUONG MINH, VA
    (b) dai du doan rong gap doi so voi khi co duong cong day du.
  Neu khong thoa (a), du doan mang nhan [KHONG-CO-SO] va KHONG duoc tinh
  vao ti le HIT/MISS.
```

Quy tac nay cung la ly do `beta = 0.431` (fit HAI diem, `K01`/`L45`) dang lo
hon ve ngoai cua no.

## 9. Han che moi

```text
  L49  `M-135` dung thang do bi BIEN CHAN. Voi bien 2-vs-6 va 4-vs-4, so trung
       chi nhan {2,4,6} va 6/8 la tran. Nguong ">= 6/8" duoc ky truoc khi biet
       bien. Bang chung thuc o muc kappa = 0.50, n = 8, P(ngau nhien) = 0.214.
  L50  `S_pivotal` bao cao o 23.21 KHONG kem khoang tin cay. Voi AR(1)
       tau = 1 s, dt = 5 ms thi n_eff = 500 chu khong phai 200 000; sai so
       thuc lon gap ~20 lan so voi gia dinh iid.
  L51  Tam calib parquet cua `M-136` va bon parquet Dot 4 khong con tren dia
       va report cu KHONG luu digest cua chung. Neu dung lai ma tham so khong
       khop goc thi doi chung am muc duong ong tro thanh vo nghia IM LANG.
       => bao cao "khong tai dung duoc", KHONG dung so thay the.
```

## 10. Dieu KHONG lam

```text
- KHONG ha PIVOTAL_MIN (muc 2). Doi tu vung, khong doi nguong.
- KHONG sua ket qua M-133..M-139 da ky o 23.21.
- KHONG dung R_stab de dien giai 23.21 (muc 6).
- KHONG tra G23-141/G23-142 bang phep do khac (muc 0c).
- KHONG dung lai calib parquet luc nay: tap cell se doi sau khi co Dot 4,
  dung lai roi doi tap cell la lam hai lan (L51).
```

So ke tiep: `L52`, gate so 169, `M-147`, `K07`.

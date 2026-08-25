# AMENDMENT 23-66 -- Task B: ma tran chuyen giao C3 vs B2

Ngay ky : 2026-08-25          <-- TRUOC khi viet `cert/transfer_matrix.py`
Lesson  : 23.22 Task B
Loai    : TIEN DANG KY
Moc     : sau `6c47592` (`A065d` + doc 43 vong hai), truoc commit dau tien cua
          Task B

## 0. Disclosure

DA XEM: toan bo `taxonomy_audit.json` (`b9d2774`), gom `M-192` (bang
`min_blocks` theo `kappa`), thang `qhat` theo `rho_bar`, `spread_m` theo ho,
va **toan bo hang V-S tai `kappa = 0.5`**.

CHUA XEM: khong mot dai luong CHUYEN GIAO nao (`A != B`).
`cert/transfer_matrix.py` chua ton tai. `M-190`, `M-194`, `M-195`, `M-196` la
du doan MU.

### 0.1. `M-193` KHONG mu -- va do la chu dich

Duong cheo cua ma tran chuyen giao (hieu chuan tren cell A, trien khai tren
cell A) la **DUNG BANG** hang `variant_sweep` da co: cung `fit_config(calib,
"C3", 0.5, post="selective", multiplicity="bonferroni")`, cung
`evaluate_config(test, ...)`, cung tach `is_calib`. Nen dap an da nam trong
artifact:

```text
cell            viol|acc   acceptance   err|acc     pass_coverage
poisson@0.925    0.0817      0.3955      0.0840        True
poisson@0.850    0.0834      0.3203      0.0817        True
h2@0.700         0.0759      0.5859      0.0481        True
poisson@0.875    0.0814      0.3422      0.0857        True
poisson@0.900    0.0789      0.3621      0.0882        True
poisson@0.960    0.0831      0.4220      0.0675        True
h2@0.650         0.0847      0.4664      0.0651        True
h2@0.675         0.0790      0.5200      0.0513        True
```

Vi biet truoc dap an, `M-193` duoc ha tu "du doan" xuong **KIEM WIRING**, va
nguong duoc siet len muc BIT: duong cheo phai TAI TAO artifact, khong phai
"nam trong mot dai". Mot du doan ma ta biet dap an thi khong con la du doan;
cai duy nhat no con lam duoc la bat loi noi day. Vo o day -> DUNG, khong phai
phat hien.

## 1. Menh de trung tam -- va mot cau bi RUT LAI

### 1.1. RUT LAI

Ban thao noi bo truoc day viet: *"C3 hieu chuan lai duoc bang du lieu KHONG
NHAN; B2 can mot vong do lai co NHAN THAT."* **Cau nay SAI.**

```text
cert/simultaneous_score.py:82   def pair_scores(y_true, y_hat):
                          :89       err = errors(y_true, y_hat)     <- NHAN
cert/build_calib_set_v3.py:365      pair_s = SS.pair_scores(y_true, y_hat)
                          :418      data["s_pair_%d"] = pair_s[:, j]
```

`qhat` la phan vi cua `s`, va `s` la ham cua `y_true`. **Conformal cung can
nhan.** Cau tren KHONG duoc xuat hien trong bat ky ban thao nao. Reviewer dau
tien biet conformal se bac no ngay, va no se keo theo nghi ngo len moi thu
khac.

### 1.2. Ban dung -- hai khac biet, ca hai kiem duoc

```text
KHAC BIET 1 -- BAN CHAT THAM SO   (ca hai deu can nhan)

  qhat  la mot PHAN VI cua mot phan phoi quan sat duoc
        -> bai toan UOC LUONG: yeu cau co mau DA BIET (>= 29 block/o, `L91`),
           chung chi hop le mau-huu-han distribution-free,
           va ta DO DUOC khi no thieu du lieu (`L91`, `L93`, `L95`)

  c     la mot THAM SO TU DO do bang tim kiem tren mot tieu chi (err)
        -> khong ly thuyet co mau, khong chung chi,
           khong co cach biet khi nao no sai ngoai viec DO LAI err
           -- ma do lai err lai can dung thu ta dang thieu o che do moi

KHAC BIET 2 -- BAT BIEN THANG DO   (day la co che DUOC KIEM o `NC-3`)

  C3 :  chap nhan <=> m_hat_j / qhat_j >= kappa      TI SO
  B2 :  chap nhan <=> m_hat_1 >= c                   NGUONG TUYET DOI

  Neu che do moi lam ca `m_hat` va `s` gian theo cung he so lambda:
      qhat -> lambda*qhat,  ti so m_hat/qhat KHONG DOI  -> C3 tu dong theo
      c dung yen                                        -> B2 TROI hoan toan
```

Thang **that su doi rat lon** giua cac cell (`qhat` slot-1, V-M, `kappa = 0`):

```text
ho poisson      rho=0.700    1.0467
                rho=0.850   15.5590
                rho=0.875   23.7692
                rho=0.900   34.4153
                rho=0.925   44.1072
                rho=0.960   62.3353      <- 59.6x so voi rho=0.700

ho h2           rho=0.650   16.1809  ...  rho=0.960   65.4591
```

> 🔑 Menh de trung tam cua Task B, thay cho cau bi rut lai:
> **C3 ma hoa bat bien thang do vao CHINH luat quyet dinh; B2 thi khong.**

## 2. Thiet ke

### 2.1. Diem van hanh: `kappa = 0.50`

Tu `M-192` (`A065c`, DA KY truoc khi Task B ton tai; cham o `G23-246`):

```text
tai kappa = 0.50 : 8/8 cell song co min_blocks trong [421, 490] >> san on dinh 59
tai kappa = 1.00 : 4/8 cell roi duoi san (`M-191`, `G23-245`)
tai kappa = 2.00 : V-S KHONG CHAY -- no tra ve qhat cua V-N (`L95`, `G23-247`)
```

`kappa = 0.5` la diem DUY NHAT trong luoi ma V-S vua hop le vua on dinh tren
toan bo 8 cell song. **Day KHONG phai chon nguong theo du lieu Task B** -- no
la he qua cua mot phep do da tien dang ky, cham xong truoc khi Task B ton tai.
Phai khai ro nhu vay, neu khong nguoi doc se tuong ta doi diem van hanh cho
dep.

Neu tai `kappa = 0.5` mot cell bat ky cho
`qhat_source = "degenerate_fallback_to_none"` thi **Task B DUNG**: `M-192` noi
dieu do khong duoc xay ra, va chay tiep se la dan nhan `selective` len `none`
(`L95`).

Thu tuc: `post_variant = "selective"`, `simultaneous = True`,
`multiplicity = "bonferroni"`, `alpha_each = alpha/3`, `alpha = 0.10`.

### 2.2. Tap cell va ba khoi

Sinh TU artifact qua `live_region_flags()`, khong hard-code:

```text
SONG (A = err_neo >= 0.05, tieu chi DA KY amendment 23-62), 8 cell:
    poisson@{0.850, 0.875, 0.900, 0.925, 0.960}
    h2@{0.650, 0.675, 0.700}
CHET, 4 cell:  poisson@0.700, h2@{0.850, 0.925, 0.960}
```

Ma tran 8x8 = 64 o:

```text
DUONG CHEO    8 o   hieu chuan = trien khai.  KIEM WIRING (muc 0.1)
TRONG HO     26 o   p<->p 20 + h2<->h2 6  (da tru duong cheo)
GIUA HO      30 o   p->h2 15 + h2->p 15         *** KHOI CHINH
                                          8 + 26 + 30 = 64  ✓
```

### 2.3. `L92` -- rang buoc KHONG go duoc bang du lieu hien co

8 cell song: `h2` chi song o `rho_bar` THAP {0.650, 0.675, 0.700}; `poisson`
chi song o CAO {0.850 .. 0.960}. Khong `rho_bar` nao co ca hai ho cung song.

```text
DUOC PHEP noi : "chuyen giao qua CHE DO VAN HANH"
KHONG duoc noi: "chuyen giao qua HO TAI"
```

Khoi "GIUA HO" NHAT THIET cung la "rho thap <-> rho cao". Hai bien do bi
ghep hoan toan; khong mot phan tich hau ky nao tach duoc chung. Moi phat
bieu ket qua cua Task B phai mang rang buoc nay.

### 2.4. B2 duoc cho dieu kien TOT NHAT co the

`c` duoc do tren cell A de khop DUNG acceptance cua C3 tren chinh cell A.
Neu B2 van troi khi sang B, do khong phai vi ta dat no o mot diem bat loi.

## 3. Ba thang do -- va vi sao phai ba

```text
T1  ACCEPTANCE DRIFT   |acceptance(B) - acceptance_on_A|
    *** Thang CHINH. Ca C3 lan B2 deu co. Khong can qhat cho B2.
    Co che: ti so (bat bien thang) vs nguong tuyet doi (troi theo thang).

T2  SELECTIVE RISK     err|accept tai ACCEPTANCE KHOP tren B
    Thang cong bang: ep ca hai cung ti le chap nhan roi so risk.
    ⚠️ Day la thang ma C3 ~ B2 (`04-baselines.md`: Jaccard(C3,B2)@0.78 =
       0.9466). No PHAI co mat, de ta bao cao trung thuc rang dong gop
       KHONG nam o day.

T3  COVERAGE | ACCEPT  P(s > qhat_A | accept tren B) so voi alpha
    *** CHI C3 co. B2 khong co qhat nen khong co phat bieu bao phu.
    Viec B2 KHONG CO T3 chinh la dong gop -- phai noi thang ra.
```

> ⚠️ **Bay da nhan dien va TU CHOI:** ghep B2 voi mot `qhat` muon de no "cung
> co coverage". Lam vay la tu tay che ra thu ma ta dang chung minh la B2
> khong co. **Bao cao o TRONG, va giai thich vi sao no trong.** Ghim bang
> `T3_viol_given_accept_B2 = null` cong `T3_B2_has_no_coverage_claim = true`
> trong artifact, va bang mot test cam truong do mang gia tri so.

## 4. Nam du doan -- ky truoc

```text
M-193  DUONG CHEO [KIEM WIRING -- dap an da biet, muc 0.1]
       C3 tren duong cheo TAI TAO hang `variant_sweep` @ kappa=0.5 cua
       `taxonomy_audit.json`: |dviol|acc| <= 1e-9 va |dacceptance| <= 1e-9,
       8/8 o.
       B2 tren duong cheo: |acceptance(B) - acceptance_on_A| <= 0.02, 8/8 o
       (`c` la phan vi mau nen khop chi den do phan giai cua mau).
       [CO CHE] khong co gi de doan. Vo o day -> DUNG.

M-194  *** T1 GIUA HO: trung vi cua |T1_drift_B2| >= 3x trung vi cua
       |T1_drift_C3| tren 30 o.
       [NGOAI SUY] co che bat bien thang. Day la dong gop chinh.

M-195  T3 GIUA HO: C3 giu |viol|acc - alpha| <= 0.05 o >= 20/30 o.
       [NGOAI SUY] ⚠️ C3 KHONG co bao dam nao khi calib != test. Trung la
       PHAT HIEN THUC NGHIEM, khong phai he qua dinh ly. Neu MISS thi cung
       khong bac bo gi -- no chi noi bao dam dung o dau no duoc phat bieu.

M-196  T2 GIUA HO: trung vi cua |err|accept(C3) - err|accept(B2)| tai
       acceptance khop <= 0.02 (lay tren bon muc khop, 30 o).
       [CO CHE] hai phuong phap GAN NHAU ve risk -- day la KET QUA AM va no
       phai duoc bao cao manh nhu `M-194`.

M-190  *** BAT DOI XUNG: trung vi T1_drift_C3 cua (poisson -> h2) LON HON
       cua (h2 -> poisson).
       [TIEN DANG KY o `A065` muc 4.2, hau kiem tu `A065` muc 4]
       ⚠️ `L92`: chieu nay CUNG LA (rho cao -> rho thap). Neu TRUNG,
       KHONG duoc quy cho ho tai.
```

Cham `M-194`, `M-195`, `M-196`, `M-190` tren khoi GIUA HO (30 o). Khoi TRONG
HO (26 o) duoc bao cao lam thang do trung gian, KHONG cham diem -- no khong
co du doan da ky.

## 5. Doi chung bat buoc

```text
NC-1  DOI CHUNG AM -- 4 cell chet (poisson@0.700, h2@{0.850,0.925,0.960}).
      Ma tran 4x4 rieng. Du doan: T1 cua CA HAI <= 0.05 (trung vi).
      ⚠️ Neu KHONG nho -> "thiet hai" do o cell song la HIEN VAT cua duong
         ong, khong phai hieu ung chuyen giao. DUNG.

NC-2  DOI CHUNG DUONG -- B1 (`score_B1_random`, seed 23301).
      Du doan: T1 cua B1 >= T1 cua B2. Neu B1 ~ C3 thi thang T1 khong phan
      biet duoc gi va phai thiet ke lai.

NC-3  DOI CHUNG BAT BIEN -- nhan doi toan bo thang (`m_hat_*`, `s_pair_*`)
      x2 tren cell TRIEN KHAI, tren duong cheo.
      Du doan: acceptance cua C3 KHONG DOI (trung bit, vi ca hai ve cua
      `m_hat >= kappa * qhat` deu nhan 2 va `qhat` la phan vi cua `s` da
      nhan 2); acceptance cua B2 DOI (`c` dung yen).
      *** Kiem CO CHE TRUC TIEP, tat dinh, khong can cell moi, chay vai giay.
```

`NC-3` la doi chung manh nhat trong ba: no kiem DUNG co che duoc neu o muc
1.2, tach khoi moi thu khac.

## 6. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-248 | `M-193` duong cheo: C3 tai tao `variant_sweep` @`kappa=0.5`, sai khac tuyet doi <= 1e-9 o 8/8 o; B2 khop acceptance trong 0.02 o 8/8 o | tat/bat |
| G23-249 | `M-194` T1 giua ho: trung vi drift cua B2 >= 3x cua C3 tren 30 o | tat/bat |
| G23-250 | `M-195` T3 giua ho: C3 giu `abs(viol_given_accept - alpha) <= 0.05` o >= 20/30 o | tat/bat |
| G23-251 | `M-196` T2 giua ho: trung vi `abs(err_C3 - err_B2)` tai acceptance khop <= 0.02 | tat/bat |
| G23-252 | `M-190` bat doi xung: trung vi T1_drift_C3 (poisson->h2) > (h2->poisson) | tat/bat |
| G23-253 | `NC-1` doi chung am: tren ma tran 4x4 cell chet, trung vi T1 cua CA HAI <= 0.05 | tat/bat |
| G23-254 | `NC-2` doi chung duong: trung vi T1 cua B1 >= cua B2 | tat/bat |
| G23-255 | `NC-3` bat bien thang: nhan doi thang -> acceptance C3 trung BIT; acceptance B2 doi | tat/bat |

Ban thao noi bo cap `G23-248..254` (bay ma) va gop `NC-2` voi `NC-3`. Da
tach: hai doi chung kiem hai thu khac han (`NC-2` kiem thang T1 co phan biet
duoc khong; `NC-3` kiem co che bat bien), va gop chung lam mot gate se khien
mot cai vo che khuat cai kia.

## 7. Ket qua nao cung dung duoc

```text
M-194 HIT   C3 chuyen giao ben hon B2. Dong gop chinh, co co che, co NC-3
            xac nhan co che.
M-194 MISS  B2 cung ben nhu C3 o thang acceptance. Khi do dong gop cua C3
            RUT VE T3 (B2 khong co phat bieu bao phu nao) -- van la mot
            dong gop, nhung phai phat bieu hep lai va noi ro.
M-196 HIT   (du doan) hai phuong phap gan nhau ve risk -- ket qua AM, bao
            cao ngang hang voi M-194.
M-196 MISS  mot trong hai TOT HON HAN ve risk. Do se la mot phat hien lon
            hon ca M-194 va phai dieu tra rieng.
```

Khong nhanh nao trong so nay bien Task B thanh vo ich. Do la dieu kien de mot
tien dang ky la that.

## 8. Pham vi anh huong

```text
KHONG doi mot dong nao cua `taxonomy_audit.json` -- Task B chi DOC parquet.
KHONG chay lai Lesson 23.22 Task A.
KHONG sinh cell moi (`A065` muc 4.1 van ap dung: 18-cell manifest la mot
    lesson con, khong phai mot muc cua amendment nay).
KHONG ghi vao `results/RAW` hay `results/SUPERSEDED` (`L96`).
```

## 9. Output

```text
code      cert/transfer_matrix.py
test      test/test_phase23_transfer_matrix.py
artifact  results/LIVE/phase-23/transfer_matrix.json
doc       docs/phase-23/44-transfer-matrix.md  (viet SAU khi chay)
```

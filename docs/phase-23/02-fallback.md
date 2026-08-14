# LESSON 23.1 -- fallback semantics

Ngay: 2026-08-14

Trang thai: da chay lai sau Amendments 23-6..23-9. F3-a cu bi rut lai vi
look-ahead accounting; artifact hien hanh dung row-level installed-path
accounting. Ket qua `F2 STATIC @ kappa=0.25` da co paired CI, doi chung ngau
nhien cung coverage, luoi min [KHAM PHA], va V23-3 seed split.

## 1. Artifacts

```text
results/phase-23/fallback_poisson_0.925_k0.5.json
results/phase-23/fallback_grid_poisson_0.925_C3.json
results/phase-23/fallback_grid_poisson_0.925_C3.csv
results/phase-23/fallback_grid_err_reject_poisson_0.925_C3.png
results/phase-23/fallback_inference_poisson_0.925_C3_k0.25.json
results/phase-23/fallback_fine_grid_poisson_0.925_C3_exploratory.json
results/phase-23/fallback_fine_grid_poisson_0.925_C3_exploratory.csv
results/phase-23/fallback_fine_grid_err_reject_poisson_0.925_C3_exploratory.png
results/phase-23/fallback_v23_3_seed_split_poisson_0.925_C3_k0.25.json
results/phase-23/fallback_mechanism_diagnostics_poisson_0.925_C3.json
```

## Phat bieu cua Lesson 23.1

Chung toi chi ra rang nguong hoa von cua moi fallback la mot dong nhat thuc:
no bang dung `err|reject` cua chinh bo uoc luong bi tu choi. Mot fallback chi
cai thien risk he thong neu no vuot twin tren chinh tap ma certificate danh dau
la khong dang tin.

Tren topology 4-duong, F3 WAIT bi rut lai vi look-ahead bias va suy bien thanh
F1 theo installed-path accounting. Tai `kappa=0.5`, ca ba fallback lam he thong
te hon anchor. Tren luoi P8, `F2 STATIC @ kappa=0.25` cai thien ca ba thang
rui ro voi CI ghep cap khong chua 0 va giu tren split seed doc lap.

Co che: dieu kien `m_hat < kappa*q_hat(z)` chon cac hang ma khoang cach twin
nhin thay nho hon do bat dinh cua chinh twin. Khi do argmin cua twin giau nhieu
hon tin hieu, va chinh sach hop ly la co ve prior cau truc P1. Prior P1 cung
xau di tren tap reject, nhung khoan phat cua no gan nhu hang so; twin moi la
doi tuong suy giam manh theo kappa. Gia tri khoa hoc cua certificate la value
of information: o cung coverage, no tot hon bo chon ngau nhien 4.31 diem phan
tram err.

## 2. Controls first

Audit F3 va gates fallback:

```text
/tmp/dt4n-venv/bin/python -m pytest \
  test/test_phase23_fallback_audit.py test/test_phase23_fallback.py -q -s

ti le hang reject co the dung thong tin TUONG LAI: 0.8584
horizon trung binh: +168.5 ms
horizon lon nhat  : +445.0 ms
P(a*(t) == a*(t')) tren hang reject co the cho: 0.7753
```

Full regression sau inference controls:

```text
/tmp/dt4n-venv/bin/python -m pytest -q
759 passed, 1 skipped, 2 warnings in 292.50s (0:04:52)
```

## 3. Dong nhat thuc hoa von

Voi mot phan hoach accept/reject co dinh:

```text
R_neo = P(acc) * err|acc(twin) + P(rej) * err|reject(twin)
R_sys = P(acc) * err|acc(twin) + P(rej) * err|reject(fallback)
```

Hoa von `R_sys = R_neo` khi va chi khi:

```text
err|reject(fallback) == err|reject(twin)
```

Gate:

```text
G23-4b  break_even_err_reject == err_reject(twin)  (tol 1e-12)
```

Trong report `kappa=0.5`:

```text
break_even_err_reject = 0.35900086471189374
anchor.err_reject     = 0.35900086471189374
identity_residual     = 0.0
G23-4b                = PASS
```

## 4. Ket qua tai kappa = 0.5

| Policy tren reject | err\|reject | err_system | vs anchor err | regret_system (ms) | vs anchor regret | sla_system | vs anchor sla |
|---|---:|---:|---:|---:|---:|---:|---:|
| twin / B0 | 0.359001 | 0.222399 | 0.00% | 1.767461 | 0.00% | 0.153950 | 0.00% |
| F1 STICKY | 0.387477 | 0.236890 | +6.52% | 1.961192 | +10.96% | 0.156740 | +1.81% |
| F2 STATIC | 0.391007 | 0.238686 | +7.32% | 2.004680 | +13.42% | 0.156298 | +1.53% |
| F3-a WAIT | 0.387477 | 0.236890 | +6.52% | 1.961192 | +10.96% | 0.156740 | +1.81% |

Tai diem prereg `kappa=0.5`, F1/F2/F3-a deu te hon B0 tren ca ba thang.

## 5. Vi sao F3 cu bi rut lai

Ban cu cua `fallback_wait` da cham diem:

```text
a_chosen[t] = a_twin[t']    voi t' la refresh ke tiep
loss         = loss(a_chosen[t], state[t])
```

Do do, voi 85.84% hang reject co the cho, action duoc tao tu anh chup tuong lai
so voi hang dang duoc cham diem. Con so cu:

```text
err_system(F3-idl) = 0.166635
err_system(F3-exp) = 0.183222
```

bi rut lai. Sau Amendment 23-6:

```text
F3-a WAIT == F1 STICKY theo installed-path accounting.
err_system_exposed(F3-a) = err_system(F1) = 0.236890
```

`P(a*(t) == a*(t')) = 0.7753` qua cua so cho trung binh 168.5 ms la dai luong
dac trung cua he: chan ly rat tro. Nhung drift van la 22.47%, nen dung tuong
lai de cham diem qua khu khong the xem la sai so nho.

## 6. Co che shrinkage ve prior

F2 STATIC tai `kappa=0.25` duoc doc nhu shrinkage ve prior:

```text
m_hat lon          -> argmin(twin) mang tin hieu -> tin twin
m_hat < k*q_hat(z) -> tin hieu yeu hon do bat dinh -> co ve prior P1
```

`P1` la prior cau truc cua topology: duong ngan nhat theo thiet ke va khong co
phuong sai uoc luong. Khi twin noi cac duong gan hoa, argmin cua twin de bi
quyet dinh boi nhieu; F2 thay argmin nhieu do bang prior khong nhieu.

Ba so co che tai diem P8 tot nhat:

```text
P(reject)          = 0.262027
err|reject(twin)  = 0.438556
err|reject(F2)    = 0.392267
```

Hai duong `err|reject(twin)` va `err|reject(F2)` bien thien khac nhau theo
kappa: twin cao o vung reject cuc kho roi giam ve marginal; F2 gan phang hon
vi no la prior hang. Chung cat nhau giua `kappa=0.25` va `kappa=0.5`.

Khi chuyen tu tap toan the sang tap reject, ca twin lan P1 deu xau di. Bat bien
moi la do suy giam cua P1 gan nhu hang so trong khi twin thay doi manh theo
kappa:

| kappa | p_reject | err\|reject(twin) | err\|reject(P1) | suy giam twin | suy giam P1 |
|---:|---:|---:|---:|---:|---:|
| 0.20 | 0.206540 | 0.457734 | 0.393694 | +0.235335 | +0.053417 |
| 0.25 | 0.262027 | 0.438556 | 0.392267 | +0.216157 | +0.051991 |
| 0.50 | 0.508874 | 0.359001 | 0.391007 | +0.136602 | +0.050731 |

Do suy giam cua P1 chi bien thien khoang 5%, trong khi suy giam cua twin bien
thien khoang 72%. Day la phat bieu sach hon ti so `4.16x`: prior khong mien
nhiem voi tap kho, nhung no tra mot khoan phat gan co dinh; twin tra khoan
phat phu thuoc manh vao do yeu cua tin hieu.

## 7. Quet toan luoi P8

Luoi P8:

```text
{0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3, 4, 6, 8}
```

Hinh headline:

```text
results/phase-23/fallback_grid_err_reject_poisson_0.925_C3.png
```

Best point tren luoi P8:

| Scale | Best policy | kappa | system risk | vs anchor |
|---|---|---:|---:|---:|
| err | F2 STATIC | 0.25 | 0.210270 | -5.45% |
| regret | F2 STATIC | 0.25 | 1.598988 ms | -9.53% |
| sla_rate | F2 STATIC | 0.25 | 0.145156 | -5.71% |

G23-14 duoc cham tren luoi P8, khong phai luoi min.

## 8. Inference controls tai P8 best

Artifact:

```text
results/phase-23/fallback_inference_poisson_0.925_C3_k0.25.json
```

### E.1 -- paired block bootstrap

Estimand: `risk_system(F2 STATIC) - risk_system(anchor)`.

| Scale | Delta point | CI95 paired block | SE | Gate |
|---|---:|---:|---:|---|
| err | -0.012129 | [-0.018938, -0.005413] | 0.003466 | PASS |
| regret | -0.168473 ms | [-0.262459, -0.072658] | 0.048530 | PASS |
| sla_rate | -0.008795 | [-0.012869, -0.004960] | 0.001994 | PASS |

`nonzero_diff_on_accept = 0` tren ca ba thang. Doi chung nay xac nhan so sanh
la ghep cap dung: nhanh accept triet tieu hoan toan, chi hang reject dong gop.

```text
G23-14b  CI95 cua delta khong chua 0 tren ca ba thang: PASS
```

### E.2 -- matched-coverage random control

So sanh cung coverage `P(accept)=0.737973`, cung fallback F2 STATIC.

| Scale | cert + F2 | random + F2 mean | random CI95 | value of information | Gate |
|---|---:|---:|---:|---:|---|
| err | 0.210270 | 0.253349 | [0.252653, 0.254132] | +0.043079 | PASS |
| regret | 1.598988 | 2.298913 | [2.288400, 2.309905] | +0.699925 ms | PASS |
| sla_rate | 0.145156 | 0.168506 | [0.168117, 0.168971] | +0.023351 | PASS |

Day la doi chung quan trong nhat cua Lesson 23.1. Neu bo chon reject bi ngau
nhien hoa o cung ngan sach, risk tang manh. Certificate khong chi "cho phep
dung F2"; no chon dung tap hang de F2 co gia tri.

```text
G23-14c  cert + F2 < lower CI95(random + F2) tren ca ba thang: PASS
PC23-1b  random + F2 te hon anchor tren ca ba thang: PASS
```

Con so de dua vao abstract nen la `value_of_information` tren err:

```text
random + F2 - cert + F2 = +0.043079
```

Phan ra thanh hai ve:

```text
risk(random+F2) - anchor = +0.030950  # tranh tac hai cua abstain bua bai
anchor - risk(cert+F2)   = +0.012129  # thu loi ich cua abstain co chon loc
VOI                     = +0.043079
```

Ty trong xap xi: 71.8% tranh tac hai, 28.2% thu loi ich. Nghia la o cung
coverage, chung nhan khong chi tranh chi phi abstain; no dao nguoc dau cua chi
phi do.

## 9. Luoi min [KHAM PHA] sau Amendment 23-7

Artifact:

```text
results/phase-23/fallback_fine_grid_poisson_0.925_C3_exploratory.json
results/phase-23/fallback_fine_grid_poisson_0.925_C3_exploratory.csv
results/phase-23/fallback_fine_grid_err_reject_poisson_0.925_C3_exploratory.png
```

Luoi min chi duoc doc la [KHAM PHA], khong dung de cham G23-14.

| Scale | Best policy | kappa | system risk | vs anchor | Bien? |
|---|---|---:|---:|---:|---|
| err | F2 STATIC | 0.20 | 0.209172 | -5.95% | no |
| regret | F2 STATIC | 0.20 | 1.567691 ms | -11.30% | no |
| sla_rate | F2 STATIC | 0.20 | 0.145638 | -5.40% | no |

Argmin khong roi vao bien `0.05` hay `0.40`, nen lan lam min mot lan da phan
giai cuc tri trong vung nay. Ket qua nay khong thay the con so P8 `kappa=0.25`.

## 10. V23-3 seed split doc lap

Artifact:

```text
results/phase-23/fallback_v23_3_seed_split_poisson_0.925_C3_k0.25.json
```

Split:

```text
calib seeds = {101, 102, 103}
test seeds  = {104, 105}
n_test_rows = 399,978
P(accept)   = 0.746519
```

Paired block bootstrap tren `risk(F2 STATIC) - anchor`:

| Scale | Delta point | CI95 |
|---|---:|---:|
| err | -0.014083 | [-0.021546, -0.006988] |
| regret | -0.157020 ms | [-0.262897, -0.050668] |
| sla_rate | -0.007020 | [-0.011443, -0.002345] |

V23-3 PASS tren ca ba thang: ket qua `kappa=0.25` khong bien mat tren split
seed doc lap.

## 10b. Mechanism diagnostics sau V23-3

Artifact:

```text
results/phase-23/fallback_mechanism_diagnostics_poisson_0.925_C3.json
```

### F1 low-kappa counter-control

Ket qua quyet dinh cho co che shrinkage: F1 khong thang ro tai `kappa=0.20`
hay `0.25`, trong khi F2 thang ro o cung vung.

| kappa | policy | err_system | delta err vs anchor | CI95 | err\|reject | sticky_age |
|---:|---|---:|---:|---:|---:|---:|
| 0.20 | F1 STICKY | 0.222883 | +0.000484 | [-0.004618, +0.005390] | 0.460078 | 293.903 ms |
| 0.20 | F2 STATIC | 0.209172 | -0.013227 | n/a | 0.393694 | 293.903 ms |
| 0.25 | F1 STICKY | 0.224463 | +0.002064 | [-0.003238, +0.007420] | 0.446433 | 318.937 ms |
| 0.25 | F2 STATIC | 0.210270 | -0.012129 | [-0.018938, -0.005413] | 0.392267 | 318.937 ms |

Diagnostic F6:

```text
F6a delta err(F1@0.20) trong +/-0.003 va CI chua 0: HIT_WRONG_MECHANISM
F6b sticky_age_ms_mean < 20 ms: FAIL (do duoc 293.9 ms)
F6c err|reject(F1) gan err|reject(twin) trong +/-0.02: PASS
```

Nhanh fail quan trong khong kich hoat: F1 khong co CI am ro. Co che shrinkage
dung vung: F2 thang rieng vi prior P1 khong nhieu, khong phai vi bat ky
fallback nao cung vo hai o kappa thap. F6b fail cho thay truc giac "accept cach
nhau 6 ms" sai voi metric sticky_age; reject set van co cum theo tuoi. Theo
quy tac scoring, F6a khong duoc tinh la HIT co che: no trung so nhung co che
`sticky_age << tau` bi bac.

### Truth persistence

Ham tu tuong quan cua chan ly tren test rows:

| lag | agreement |
|---:|---:|
| 50 ms | 0.906058 |
| 100 ms | 0.868387 |
| 170 ms | 0.830632 |
| 250 ms | 0.798702 |
| 295 ms | 0.783124 |
| 500 ms | 0.731347 |
| 1000 ms | 0.651949 |

Fit mũ ve `p_infinity = 0.546237` cho `tau_a = 0.799 s`. Tai sticky age cua
F1@0.20 (`293.9 ms`, effective lag `295 ms`), `P(a*(t)=a*(t-L)) = 0.7831`,
khong phai xap xi `0.67` nhu uoc luong tho. Do do co che "hai luc triet tieu"
ban dau chua duoc xac nhan bang ham tu tuong quan marginal; can mot diagnostic
co dieu kien theo last accepted row neu muon giai thich chinh xac F1. Bai hoc
phuong phap van dung: moi ham cua `rho(t)` ke thua thang thoi gian AR(1), nen
khong duoc uoc luong sticky_age bang gia dinh doc lap theo hang.

### Diem cat kappa gan 0.40

Noi suy tu `kappa=0.25` va `0.50` du doan diem cat gan `0.398`. CSV luoi min
co `kappa=0.35` va `0.40`:

```text
static_err_system(0.35) - anchor = -0.002280
err|reject(twin) = 0.405573
err|reject(F2)   = 0.399333

static_err_system(0.40) - anchor = +0.003182
err|reject(twin) = 0.390164
err|reject(F2)   = 0.397886
```

Du doan `|delta(0.40)| < 0.003` truot rat sat (`+0.000182`). Chon diem
`0.35` van am nhe, `0.40` duong nhe, nen vung co loi cua F2 STATIC ket thuc
trong khoang `(0.35, 0.40)`, xap xi `kappa* ~ 0.38`. Khong lam min lan hai.

### Ba thang bat dong argmin

| Scale | best kappa tren luoi min | system risk |
|---|---:|---:|
| err | 0.20 | 0.209172 |
| regret | 0.20 | 1.567691 ms |
| sla_rate | 0.25 | 0.145156 |

`err` va `regret` chon `kappa=0.20`, `sla_rate` chon `kappa=0.25`. Khoang cach
`err(k=0.20) - err(k=0.25) = -0.001098`, nho hon nua do rong CI ghep cap
`0.006762`; bat dong khong co y nghia thong ke, nhung co y nghia cau truc.
`sla` khong phai ban min cua `err`: no hoi duong co vuot nguong tuyet doi hay
khong, khong hoi duong co phai argmin hay khong. Ban giao cho G23-9 o Lesson
23.2: do Spearman tren toan luoi coverage, khong gop ba thang thanh mot chi so.

### Cuc tri phang

Luoi min phan giai cuc tri: `kappa=0.20` co lang gieng hai phia va khong nam o
bien. Nhung cuc tri phang: `kappa=0.20` va `0.25` khong phan biet duoc trong
sai so do. Ve van hanh, day la tin tot: vung `[0.15, 0.30]` la plateau
exploratory; gate van cham o luoi goc `kappa=0.25`.

### Oracle-switch bound

Oracle switch chi duoc chon giua twin va P1 o tung hang, nen la can duoi cho
khong gian policy Lesson 23.1:

| Scale | anchor twin | F2@0.25 | oracle switch | room closed by F2 |
|---|---:|---:|---:|---:|
| err | 0.222399 | 0.210270 | 0.093956 | 9.44% |
| regret | 1.767461 | 1.598988 | 0.644484 | 15.00% |
| sla_rate | 0.153950 | 0.145156 | 0.112257 | 21.09% |

Voi `err`, oracle switch bang `P(twin sai AND P1 sai) = 0.093956`. Neu hai loi
doc lap, tich la `0.075677`; do duoc cao hon 24.15%, tuong quan Bernoulli
`0.0928`. Nghia la co mot lop hang kho cho ca twin lan prior. Neu hai chinh
sach sai cung cho, bo chon giua chung khong the cuu nhung hang do; Phase 24 can
nguon thong tin hoac hanh dong thu ba sai o cho khac.

Ket qua nay dong khung trung thuc: certificate da chung minh tin hieu ton tai
va khai thac duoc, nhung F2@0.25 moi dong 9.44% room oracle tren err. Du dia
con lai chu yeu nam o hanh dong thay the/fallback tot hon, khong chi o bo chon.

## 11. Doi chieu du doan F0..F6

| ID | Du doan | Do duoc sau audit | KQ |
|---|---|---:|---|
| F0 | `P(a*=P1)` 0.64-0.68, mo ta | 0.656141 all / 0.659724 test | N/A |
| F1 | `err_system(F2 STATIC)` tai k=0.5: 0.21-0.27 | 0.238686 | HIT |
| F2 | `err_system(F1 STICKY)` tai k=0.5: 0.17-0.24 | 0.236890 | HIT, gan tran |
| F3 | `err_system(F3 WAIT)` tai k=0.5: 0.10-0.18 | valid F3-a = 0.236890; so cu 0.183222 bi rut lai | VOID |
| F4 | thu tu `F2 > F1 > F3` | dung tai k=0.5, dao tai k=0.25 | VOID |
| F5 | delay F3 100-250 ms | 204.271 ms given reject | HIT diagnostic |
| F6 | best fallback beats anchor err 0.2224 | P8 best: F2, k=0.25, err=0.210270; CI paired PASS | HIT tren grid; FAIL tai k=0.5 |
| F6a | F1@0.20 delta err gan 0, CI chua 0 | +0.000484, CI [-0.004618, +0.005390], nhung sticky_age co che sai | HIT_WRONG_MECHANISM |
| F6b | F1@0.20 sticky_age < 20 ms | 293.903 ms | MISS diagnostic (47x) |
| F6c | F1@0.20 err\|reject gan twin trong +/-0.02 | 0.460078 vs 0.457734 | HIT diagnostic |
| K40 | `abs(delta(F2@0.40)) < 0.003` | +0.003182 | MISS, sat |

Du doan trung nho artifact F3 cu khong duoc cham la HIT. F4 bi cham VOID vi
vi pham P15: du doan thu tu cho mot ho kappa nhung khong dinh danh mien. F6a
tao them nhan moi: trung so nhung bi bac co che khong duoc tinh la HIT co che.

## 12. Gates

| Gate | Ket qua |
|---|---|
| G23-1 every policy has one action per row | PASS |
| G23-4 total probability identity | PASS |
| G23-4b break-even identity | PASS |
| G23-5 decision delay profile | PASS |
| F3 audit: production wait action equals installed path | PASS |
| G23-14 P8 best fallback beats anchor | PASS |
| G23-14b paired CI improves anchor, all scales | PASS |
| G23-14c matched random control, all scales | PASS |
| PC23-1b random + F2 worse than anchor | PASS |
| V23-3 independent seed split | PASS |
| F1 low-kappa counter-control: CI contains 0 | PASS |
| F6b sticky-age subprediction | FAIL |
| oracle-switch bound computed | PASS |
| truth persistence diagnostic | PASS |
| kappa=0.40 crossing prediction | FAIL, sat |

## 13. Ket luan Lesson 23.1

Thong diep dung sau audit khong phai "F3 wait giam loi 17.6%". Thong diep dung:

```text
1. Break-even cua fallback la err|reject(twin) tren cung tap reject.
2. F3-a suy bien thanh F1 neu cham theo duong dang cai that.
3. Tai kappa=0.5, fallback mien phi lam he thong te hon anchor.
4. Tren luoi P8, F2 STATIC tai kappa=0.25 giam risk tren ca err, regret,
   va sla_rate; CI ghep cap xac nhan khong phai nhieu.
5. Gia tri khoa hoc cua certificate la value of information: o cung coverage,
   random + F2 te hon cert + F2 4.31 diem phan tram err.
6. Doi chung F1 o kappa thap khong thang ro, nen co che shrinkage ve prior
   dung vung; nhung F6a la HIT_WRONG_MECHANISM vi sticky_age doc lap-theo-hang
   bi bac boi thang thoi gian AR(1).
7. Oracle switch cho thay loi twin va loi P1 tuong quan duong; room con lai
   nam o hanh dong/fallback moi, khong chi o bo chon reject.
```

Gia tri cua certificate trong Phase 23 vi vay la ba lop: bao dam formal tren
nhanh accept, bo phat hien tin hieu-qua-nhieu de co ve prior P1 khi can, va tin
hieu phan bo reject-set de chon luc nao dung fallback hay tai nguyen moi trong
Phase 24.

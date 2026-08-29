# CONSTANTS -- so hang so (nguon chan ly duy nhat cho moi so KHOA)

So thu BA, cung khuon voi `GATES.md` (ho `G23-*`) va `LIMITS.md` (ho `L*`).
Sua bang tay; KHONG sinh tu dong.

Duoc mo o amendment 23-51 sau khi kiem toan phat hien `beta = 0.431` -- tru cot
lap luan cua `M-125b` va dau vao cua Lesson 23.28 -- ton tai trong repo duy nhat
duoi dang mot hang so cung o `tools/check_bin_geometry.py:34`, khong co mot dong
nao noi no den tu dau.

`LIMITS.md` da du doan viec nay: *"Ba ho ID tren van CHUA co so. Neu chung bat
dau va cham nhu `L*` da va cham, hay tao `CONTROLS.md` theo dung khuon nay."*
Hang so mac cung mot benh, chi khac ten benh: khong phai va cham ma la MO COI
(khong co provenance).

## Quy tac

```text
1. Moi so KHOA -- so ma neu doi thi mot ket luan doi theo -- phai co mot dong
   o day. So trung gian, so chi dung mot lan trong mot script thi khong can.
2. Cot "fit the nao" phai du de NGUOI KHAC tai dung duoc con so. Ghi
   "do duoc" la CHUA DU; phai ghi do bao nhieu diem, uoc luong nao.
3. Cot "sai so" phai phan biet sai so KHI FIT voi cận hau kiem. Hai thu khac
   nhau ve ban chat: mot cai noi con so nay chac den dau, cai kia noi mo hinh
   dung den dau.
4. Hang so cung trong code phai khop dong tuong ung; `test_constants_ledger.py`
   ghim rang buoc do.
```

## Bang

| ma | hang so | gia tri | fit the nao | nguon | dung o dau | sai so |
|---|---|---:|---|---|---|---|
| K01 | `beta` -- so mu dan `q_hat` theo `z` | 0.431 | fit HAI DIEM log-log qua `(B0, B3)`; xem muc "K01" duoi | `docs/phase-22/00-preregistration.md:167` (z ly thuyet) + `05-selective-conformal.md:105` (q_hat) | `tools/check_bin_geometry.py`, `M-125b`, `M-126`, Lesson 23.28 | `sd(beta) = 0.0059` khi FIT (CI95 `[0.4195, 0.4425]`); `\|dbeta\| <= 0.034` la cận HAU KIEM (`L39`) |
| K02 | `Z_EDGES_V7` | (0.100, 0.241, 0.366, 0.491, 0.641) | tu phan vi cua truc tuoi DO DUOC | `00zze-amendment-48.md`, `measurements/aoi_model_v7.py:68` | `build_calib_set_v3` | -- (dinh nghia, khong phai uoc luong) |
| K03 | `d` -- tre transport cua AoI | 115.9 ms | moment bac 1 voi `T` do BRIDGE-SIDE; ba uoc luong 114.11 / 115.50 / 116.07 da duoc phan xu la CUNG mot so | `23-sampling-diagnostic.md`, `00zzd-amendment-47.md` muc 3 | `aoi_model_v7.D_SYNC_S = 0.1159` | `+/- 6.5 ms` (95%), do khoa luoc -- `L32` |
| K04 | `D_BASE` -- san tuoi co so | 107.775 ms | `d` tru TRUNG BINH THUC cua ho so sau luong tu hoa (U3: 8.125 ms, KHONG phai danh dinh 8.690) | `26-axis-integration.md`, `aoi_model_v7.d_base_s()` | `build_calib_set_v3` | ke thua K03 |
| K05 | `T` -- chu ky lam moi | 500.2922 ms | do BRIDGE-SIDE tu `t_source` ke tiep, khong bi luoc | `measurements/aoi_model_v7.py:25` | `aoi_model_v7` | `T/dt = 100.0584` khong nguyen -- day la LY DO khong dung rang cua |

| K06 | `w_loss` -- ty gia doi loss sang ms trong ham chi phi | 5000 | equal-budget: `w = T_delay / T_loss = 50 / 0.01`. KHONG phai mot fit -- la dinh nghia "dung het ngan sach TRE == dung het ngan sach MAT GOI" | `00zzo-amendment-52.md` muc 2a | `sla_exogenous`, `eight_cell_sweep` (qua artifact) | -- (lua chon co nguyen tac). Do nhay: sweep {1250, 5000, 20000} |

| K07 | Spearman(`t_loss_endo`, `T*`) -- do can chinh song nui | 1.0000 | `scipy.stats.spearmanr` tren BAY cap `(t_loss_endo, T*)` co `T*` XAC DINH; `T*` = argmax `S_pivotal` tren luoi log 1.25x, bo sung tu luoi cuc bo 1.05x | `t_loss_fine.json` + `t_loss_local_fine.json` + `sla_calibration.json`; `00zzq-amendment-54.md` muc 1a | Bang chung dinh luong cua `S14` | n = 7 cap. `h2@0.960` bi LOAI: cuc dai la CAO NGUYEN cham mut, `T*` khong xac dinh (`L63`). Ban truoc ghi 0.9940 tren 8 cap, trong do mot cap co `T*` sai |
| K08 | `CV_MAX_FOLDED` -- he so bien dong cuc dai cua ho folded normal | 0.755510639762867 | KHONG fit. Dan giai tich: `sup_theta CV = sqrt(pi/2 - 1)`, dat tai `theta = 0` (half-normal) | `A072-amendment-72.md` muc 4 | `cert/baselines_lit.py`, `M-227` | 0 (hang so toan hoc, khong phai uoc luong) |
| K09 | `RHO_MEASURED_HARD_CEILING` -- tran van hanh cua TX counter | 1.0094102536 | median p99 cua 49 link-run co p99 >1.0 tren 15 run CLEAN; nguong canh bao lich su la `K09 * 0.995 = 1.0043632023` | `A082`; `snr_censoring_artifact.json::G23_335_hard_ceiling`; `G-A003`; `G-L20` | Gia tri K09 giu nguyen. Gate censoring TUONG LAI phai dat tren bien chua bi cat: `p(rho_offered > K09) < 0.05`; khong dung `rho_measured` de quyet dinh censoring | MAD cua 49 p99 = 0.00003562; q2.5--q97.5 = [1.00208, 1.01064]. Co che framing/accounting overhead la GIA THUYET, khong phai fit co che |
| K10 | `TRUST_GATE_P99_MS` -- latency mot quyet dinh scalar | 0.222126 ms | microbenchmark `N=5000`, warm-up 200; pandas age-bin lookup + `cert.usefulness_v2._thresholds` + scalar compare | `results/SMOKE/phase-D/trust_gate_benchmark.json`; `tools/trust_gate_bench.py` | gate ngan sach D.6′ (`p99 <= 10 ms`) | mot lan do tren may cuc bo; infra kem theo: CPU p95 15.479%, 4 co canh bao deu false |
| K11 | `ARCHIVE_TAG` -- moc bat bien truoc custody action | `phase-D-cleanup-start` | annotated tag tai commit `fbde6a4`; tao truoc moi thao tac untrack/rewrite | `git show phase-D-cleanup-start`; `docs/phase-D/00-reproduction-audit.md` | phan giai provenance Phase 20--23 va goi Zenodo D.0 | -- (dinh danh bat bien, khong phai uoc luong); remote push phai duoc checker D.0 xac nhan |

So ke tiep duoc cap: **K12**.

## K01 -- `beta` chua bao gio co dong nguon goc

### Cai da tim thay

```text
tools/check_bin_geometry.py:34    BETA = 0.431          <- hang so cung
results/LIVE/phase-23/axis_remeasure_impact_wave1.json
                                  "dilation_exponent": 0.431   <- da vao artifact
00zzj-amendment-49d.md:156        "No khoa o Phase 22."

grep -rn "0.431" docs/phase-22/   ->  KHONG CO DONG NAO
```

Muoi tai lieu Phase 23 TRICH DAN `z^0.431`. Khong tai lieu nao DINH NGHIA no.

### Tai dung duoc

```python
import math
# docs/phase-22/00-preregistration.md:167
#   "z dai dien cho tien doan ly thuyet: B0 -> 0.077, B3 -> 0.425"
# docs/phase-22/05-selective-conformal.md:105  (kappa = 0)
#   q_hat theo bin = [11.588, 15.635, 19.646, 24.322]
beta = math.log(24.322 / 11.588) / math.log(0.425 / 0.077)   # -> 0.4340
```

Mot ung vien thu hai (bang bootstrap CI o `04-conformal-simultaneous.md:170`,
`q_hat = [15.2778, ..., 32.2376]`) cho `0.4371`.

```text
ung vien A (05-selective, kappa=0)   beta = 0.4340   lech +0.0030
ung vien B (04-conformal, CI mean)   beta = 0.4371   lech +0.0061
gia tri dang dung                    beta = 0.4310
```

KHONG ung vien nao tai dung DUNG `0.431`. Ca hai deu nam trong CI95 cua phep
fit, nen `0.431` la mot gia tri HOP LE -- nhung xuat xu chinh xac cua ba chu so
do van CHUA truy duoc. Ghi nguyen trang thai nay thay vi chon dai mot ung vien
roi ghi nhu the da biet.

### `sd(beta)` -- tinh tu CI Phase 22, khong can do moi

Voi fit hai diem, sai so chuan cua so mu la:

```text
sd(beta) = sqrt( sd(ln q0)^2 + sd(ln q3)^2 ) / ln(z3 / z0)
```

Lay tu `04-conformal-simultaneous.md:170` (block bootstrap, 200 draw):

```text
B0   mean 15.2778   CI95 [15.0584, 15.5054]   -> sd 0.1140   sd(ln) 0.00746
B3   mean 32.2376   CI95 [31.8204, 32.6735]   -> sd 0.2176   sd(ln) 0.00675
ln(z3/z0) = ln(0.425/0.077) = 1.7083

sd(beta)  = 0.0059
CI95      = [0.4195, 0.4425]
```

### Vi sao dieu nay KHONG lam hong `M-125b`

`beta` duoc fit tren phep doi BIN o truc CO DINH (du lieu Phase 22, truc tuoi
CU -- tuc truc mang loi `S12`). `M-125b` kiem no tren phep doi TRUC o bin CO
DINH. Hai thao tac khac nhau, nen day thuc su la tien doan NGOAI MAU. Lap luan
o `27-mm125-pilot.md` van dung.

Dieu can ghi vao paper la ba cau hoi reviewer se hoi, va cau tra loi:

```text
Q1  beta = 0.431 den tu dau?
A1  fit hai diem log-log tren du lieu Phase 22. Xuat xu chinh xac cua ba chu
    so chua truy duoc; hai ung vien tai dung cho 0.434 va 0.437.

Q2  beta fit tren truc CU -- truc vua bi tuyen la sai. Vi sao van dung duoc?
A2  vi no duoc fit tren phep doi BIN, con duoc KIEM tren phep doi TRUC. Ngoai
    mau theo dung nghia.

Q3  sai so cua beta KHI FIT la bao nhieu?
A3  sd = 0.0059, CI95 [0.4195, 0.4425]. Chu y: `L39` cho `|dbeta| <= 0.034`
    nhung do la cận HAU KIEM suy nguoc tu phan du, KHONG phai sai so fit.
    Sai so fit CHAT hon cận hau kiem khoang ba lan (1.96*sd = 0.0116 so voi
    0.034), nen bat dinh cua phep fit KHONG chi phoi phan du cua M-125b.
```

## Ma KHONG thuoc so nay

```text
G23-*  -> GATES.md
L*     -> LIMITS.md
S*     -> loi cau truc, dinh nghia trong PHASE_23_v3.md (NGOAI repo)
```

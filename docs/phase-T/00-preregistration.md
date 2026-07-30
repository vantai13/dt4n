# PHASE T -- TIEN DANG KY (T.0)

Ngay: 2026-07-30
Trang thai: chua chay bat ky phep do nao cua Phase T.
Commit quan sat: `79e5706`
Tien de: Phase L da co `link_model_v2` va gate decision trong
`docs/phase-L/99-gate-decision.md`.

Ban nay chot lai thiet ke Phase T sau audit tien de. Muc tieu cua Phase T
khong phai fit mot model moi, ma do sai so cua viec dung model tinh
`f(mode,bw,q,rho)` cua Phase L tren tai dong `rho(t)`.

--------------------------------------------------------------------
## T0. Kiem Toan Tien De

B1. `mininet/flow_engine.py` phat theo `time.monotonic()` va
`payload_bits/rate_sum_bps`, khong co nguon ngau nhien o thang goi. O thang
goi, traffic flow-level cua Phase 20 gan CBR; `c_a` nho khong phai bursty.

B2. Vi `flow_engine.py` phu thuoc dong ho that, lich goi khong tai lap
bit-exact theo seed. Phase T ke thua mau dung cua Phase L:
`mininet/load_spec.py` sinh schedule bang ham thuan va khoa bang SHA-256.

B3. `TrafficConfig.hurst` khong duoc ap dung `H=(3-kappa)/2` khi
`kappa >= 2`. Quan he nay chi dung voi `1 < kappa < 2`, noi thoi luong luong
co phuong sai vo han va tao long-range dependence. Voi `kappa >= 2`, Hurst
trung lap la `0.5`. Da sua trong `mininet/traffic_v7.py`.

B4. Phase T dung payload background 1470 B va frame 1512 B, dung voi
`mininet/load_spec.py` va `link_model_v2`. Khong dung payload 1400 B cua
`flow_engine.py` cho cac phep do Phase T.

B5. `LOAD_SIGMA_TARGET = 0.010` qua nho de do hieu ung dong. Phase T phai quet
`sigma_rho`; khong lay trace Phase 20 v7 hien tai lam bang chung du cho
quasi-static.

B6. Dinh nghia rho da chot trong `mininet/load_spec.py`:

```text
rho = (bg_pps*1512 + probe_pps*106) / (bw*1e6/8)
```

`twin/link_model.py` v1 van ton tai voi cac hang so cu
`NETEM_OCCUPANCY_COEF`, `OVERHEAD_FACTOR`, `OFFERED_CLIFF`. Phase T bi cam
import v1; guardrail nam o `test/test_phase_t_no_v1_import.py`.

--------------------------------------------------------------------
## T1. Dac Ta Tai Dong

Thang luong dung OU/AR(1) roi rac. T.0 ban dau dung `dt = 0.100 s`;
Amendment 2 chot lai `dt = 0.005 s` de tranh artefact canh bac thang:

```text
rho[k+1] = rho_bar + phi*(rho[k]-rho_bar) + eps_k
phi      = exp(-dt/tau_rho)
eps_k    ~ N(0, sigma_rho^2 * (1 - phi^2))
```

Clamp vao mien do duoc cua `link_model_v2`: `[0.50, 1.05]`. Moi run phai ghi
`n_clamped/n_steps`. De V-T3 co the pass truoc khi chay, ap dung rang buoc:

```text
sigma_rho <= (1.05 - rho_bar) / 2.58

rho_bar 0.700 -> sigma_rho <= 0.136
rho_bar 0.850 -> sigma_rho <= 0.078
rho_bar 0.925 -> sigma_rho <= 0.048
rho_bar 0.980 -> sigma_rho <= 0.027
```

Thang goi dung cac mode chinh `{cbr, poisson, h2}`. `onoff` khong vao luoi
chinh vi khong co `c_a` design co dinh, chi giu lam doi chung neu con budget.
Probe Poisson: 64 B payload, 106 B frame, 20 pps, tinh vao rho.

Ky thuat ghep hai thang: time-rescaling. Khong dung thinning, vi thinning keo
`c_a` ve gan 1 va pha burstiness thiet ke.

--------------------------------------------------------------------
## T2. Dai Luong Do

Tai su dung ha tang Phase L:

```text
background packets with timestamp -> packet/load-average OWD
probe Poisson 20 pps              -> time-average OWD by PASTA
tc -s qdisc backlog               -> independent queue/backlog view
```

Them cho Phase T:

```text
rho_thuc_te(t) : dem goi trong cua so 100 ms tu _bgtx.bin
Reich(t)       : Lindley/Reich workload scan trong tung cua so 1 s
c_a_window(t)  : CV gap trong tung cua so 100 ms
q_time_hat     : mean OWD tu goi background voi trong so 1/lambda(t_i)
```

--------------------------------------------------------------------
## T3. Sai So Bao Cao

Ba uoc luong delay that tren cung mot run:

```text
q_bg_load_ms = trung binh tho OWD goi background
q_bg_time_ms = trung binh OWD background voi trong so 1/lambda(t_i)
q_probe_ms   = trung binh OWD probe Poisson
```

Hai du bao tu `link_model_v2`:

```text
q_psa_load_ms = integral lambda(t) f(rho(t)) dt / integral lambda(t) dt
q_psa_time_ms = (1/T) integral f(rho(t)) dt
q_ssa_ms      = f(rho_bar)
```

Du bao MOL bo sung theo Amendment 2:

```text
rho_tilde(t)  = EWMA(rho(t), T_relax)
q_mol_load_ms = integral lambda(t) f(rho_tilde(t)) dt / integral lambda(t) dt
err_mol_ms    = q_bg_load_ms - q_mol_load_ms
gain_mol      = |err_qs_ms| / |err_mol_ms|
```

Ba thanh phan sai so, cong duoc bang dai so:

```text
err_qs_ms      = q_bg_load_ms  - q_psa_load_ms
err_jensen_ms  = q_psa_time_ms - q_ssa_ms
d_sampling_ms  = q_psa_load_ms - q_psa_time_ms
err_total_ms   = q_bg_load_ms  - q_ssa_ms
               = err_qs_ms + err_jensen_ms + d_sampling_ms
```

Quy uoc dau cua `err_jensen_ms` la sua doi bat buoc: voi ham loi,
`E[f(rho)] - f(E[rho])` duong. Neu dung dau nguoc, D-T5 se fail vi loi dinh
nghia chu khong vi du lieu.

Khong gop `d_sampling_ms` vao `err_qs_ms`. Trung binh goi background la
load-average; khi `lambda(t)` bien thien, no bi keo ve cac vung tai cao. PSA
chinh phai so voi `q_psa_load_ms`, khong phai `(1/T) integral f dt`.

--------------------------------------------------------------------
## T4. Luoi Do

Amendment 2 thay the luoi T.0 bang luoi duoi day sau audit T.1. Ly do:
giai `sigma_rho` tu muc `J` tao nhieu o khong dat o tai cao, va
`dt=0.100 s` qua tho so voi `T_relax_min`.

Doi luoi tuyet doi thanh cac truc vo huong:

```text
Lambda = tau_rho / T_relax(mode, rho_bar)
J      = |E[f(rho)] - f(rho_bar)| / sigma(mode,bw,q,rho_bar)
```

Truc dong:

```text
tau_rho in {0.2, 1.0, 5.0} s
```

Bo `tau_rho = 20 s` khoi luoi chinh vi cua so 90 s khong du de gate
`sigma_hat` va `tau_hat` pass mot cach co nghia; `tau in {0.2,1,5}` da trai
du dai `Lambda` can thiet.

Chon bien do tai dong bang ti le khoang trong toi bien mien:

```text
sigma_max = (1.05-rho_bar)/2.58
sigma_rho = a * sigma_max
a in {0.20, 0.90}
```

`J` van duoc tinh chinh xac va bao cao cho tung o, nhung la truc cua hinh,
khong phai truc thiet ke.

Rho grid:

```text
h2, poisson -> rho_bar in {0.70, 0.85, 0.925, 0.98}
cbr         -> rho_bar in {0.98}
```

Ly do cat `cbr`: o `rho <= 0.98`, Phase L cho delay gan phang, khong co tin
hieu Jensen/dynamic huu ich. Chi `rho_bar=0.98` co the cham vung chuyen tiep
quanh rho 1.0.

Cau hinh chinh sau Amendment 2:

```text
bw=6 Mbps, q=13
dt=0.005 s
seeds = {11, 12, 13, 14, 15}
nhanh chinh: h2/poisson x 4 rho_bar x a {0.20,0.90} x 3 tau x 5 seed = 240
nhanh cbr  : cbr,rho_bar=0.98 x a {0.20,0.90} x 3 tau x 5 seed = 30
doi chung am sigma_rho = 0 cho 9 to hop (mode,rho_bar) x 5 seed = 45
thu tu chay random toan phan, seed thu tu = 7000
diem canh: (h2, rho_bar=0.85, a=0.90, tau_rho=1.0, seed=999) moi 30 diem
```

Uoc tinh campaign chinh: 326 diem x 105 s, khoang 9.5 gio. Step response
bo sung khoang 3.1 gio, tong khoang 12.6 gio.

--------------------------------------------------------------------
## T5. Du Doan Truoc Khi Do

D-T1. Doi chung `sigma_rho = 0` phai tai tao Phase L trong 2%;
`schedule_digest` khop cho cung `(mode, rho, seed)`. Neu khong, dung lai.

D-T2. `err_qs -> 0` khi `Lambda -> infinity`; khi `Lambda >= 10`,
`|err_qs| < 0.1 * sigma_ref`.

D-T3. `|err_qs|` tang khi `Lambda` giam. Tai `Lambda ~ 1`, do lon cung bac
voi `J`.

D-T4. Dau ky vong cua `err_qs` la am o vung dong (`Lambda` nho), vi PSA
thuoong danh gia qua cao nghen khi hang doi khong kip dat trang thai dung cua
cac dinh tai ngan.

D-T5. `err_jensen` doi dau theo mode va `rho_bar`; tinh bang tich phan truc
tiep, khong dung `f''` PCHIP:

```text
h2      rho_bar=0.70            -> duong
h2      rho_bar=0.85/0.925/0.98 -> am
poisson rho_bar=0.70/0.85/0.925 -> duong
poisson rho_bar=0.98            -> am
```

D-T6. `d_sampling` duong o moi noi, xap xi
`f'(rho_bar)*sigma_rho^2/rho_bar`.

D-T7. `c_a_window` doc lap voi `(sigma_rho, tau_rho)` trong 10%.

D-T8. `c_a_pooled` khop cong thuc time-rescaling trong 5%:

```text
c_a_pooled = sqrt((1+c_design^2) * E[lambda] * E[1/lambda] - 1)
```

D-T9. `cbr` tai `rho_bar=0.98` co the cho `err_qs` lon va khong on dinh; day
la vung `link_model_v2.is_reliable() = False`.

D-T10. MOL vuot PSA o vung dong:

```text
gain_mol = |err_qs|/|err_mol| > 2 khi Lambda < 3
gain_mol ~= 1 khi Lambda > 10
err_mol nguoc dau voi err_qs o vung dong
```

D-T11. `T_relax` do bang step response:

```text
poisson: khop cong thuc RBM trong 3x
h2     : lon hon RBM khoang 2-4x
cbr@rho=1.00: khong doc duoc trong cua so 60 s
doi xung len/xuong S-2 khop trong 25%
```

D-T12. Hai co che tu phan tach theo `rho_bar`:

```text
rho_bar <= 0.85  : err_jensen + d_sampling chi phoi
rho_bar >= 0.925 : err_qs dong chi phoi, J < 0.8
```

Neu D-T1 hoac D-T7 sai thi dung lai va sua ha tang truoc khi do tiep.

--------------------------------------------------------------------
## T6. Tieu Chi

Dung nguong dia phuong, chuan hoa theo:

```text
sigma_ref = m.sigma(mode, bw, q, rho_bar)
```

Quyet dinh:

```text
|err_qs| / sigma_ref < 0.10  -> bo qua, Phase 20R khong doi
0.10 .. 1.00                -> cong vao band Phase 21R
> 1.00                      -> quasi-static khong dung, Phase 20R chuyen MOL
```

Khong dung mot nguong tuyet doi duy nhat. `sigma_schedule` thay doi lon giua
mode/link/rho; Phase 21R cung da chuan hoa nonconformity theo
`sigma(x)`, nen Phase T phai noi cung don vi.

--------------------------------------------------------------------
## T7. Doi Chung Bat Buoc

V-T0. Cung seed -> cung `trajectory_digest` va `schedule_digest`.

V-T1'. Unit test ham thuan OU dai `10^6` buoc: `sigma_hat` khop thiet ke
trong 1%.

V-T2'. Unit test ham thuan OU dai `10^6` buoc: `tau_hat` tu `r_1` khop thiet
ke trong 2%.

V-T1''/V-T2''. Tren cua so 90 s, day la mo ta run, khong phai gate chinh.
So sanh `sigma_hat` voi ky vong da hieu chinh thien lech huu han, nguong 15%.

V-T3. `n_clamped/n_steps < 1%`.

V-T4a. `c_a` trong cua so 100 ms:

```text
|mean(c_a_window) - c_a_design| < 0.10 * max(c_a_design, 0.05)
```

V-T4b. `c_a_pooled` khop cong thuc time-rescaling trong 5%.

V-T5. Doi chung am `sigma_rho = 0` tai tao Phase L trong 2%; digest khop khi
co cung seed.

V-T6. `rho_thuc_te(t)` do tu `_bgtx.bin` khop `rho(t)` thiet ke:
`RMSE < 0.01`.

V-T7. `d_sampling` do duoc khop du bao bac hai trong 30%, va `q_probe_ms`
khop `q_bg_time_ms` trong sai so chuan.

V-T8. Cong A5-7 giu nguyen: `socket_drops = 0`, `n_foreign = 0`,
`n_late_ratio < 0.1%`, `|rate_ratio - 1| < 0.001`.

--------------------------------------------------------------------
## T8. Neu Fail Thi Sua Gi

Nhanh (a), V-T4a fail: kiem time-rescaling vs thinning, kiem nghich dao
`Lambda(t)` co noi suy dung trong buoc `dt`, va dam bao `normalize_rate` chi
ap cho base process truoc khi rescale.

Nhanh (b), V-T5 fail: ha tang T lech Phase L. Kiem payload 1470 B, rho co
tinh probe, qdisc burst/bfifo, va `schedule_digest`.

Nhanh (c), `|err_qs| > sigma_ref` o vung binh thuong
(`rho_bar <= 0.925`, `Lambda >= 10`): truoc khi ket luan, kiem
`d_sampling` da tach dung. Neu da tach dung thi day la ket qua va Phase 20R
chuyen MOL.

Nhanh (d), loi lon chi o `cbr,rho_bar=0.98`: ky vong duoc. Ghi hop dong
`quasistatic_valid() = False` o dai do, khop `is_reliable()`.

Nhanh (e), V-T7 fail: kiem `lambda(t_i)` trong trong so `1/lambda` co dung
rho thiet ke khong; khong dung rho thuc te nhieu do luong cho trong so nay.

Ngan sach sua: toi da 2 vong; moi vong sua mot thu va ghi amendment.

--------------------------------------------------------------------
## T9. Rui Ro Da Biet

RT1. `tau_rho` lon can cua so dai. Giam nhe bang cach bo `tau=20 s`.

RT2. Clamp lam sai lech sigma. Giam nhe bang rang buoc kha thi T1 va van ghi
ti le clamp that.

RT3. `f` chi xac dinh tren `[0.50,1.05]`; cbr trong `(0.95,1.05)` unreliable.
Giam nhe bang clamp dung mien va ghi rieng cac diem vao vung unreliable.

RT4. `T_relax` suy tu batch means `k=6` tho. Them `tau_int` Sokal va thiet ke
step response T.1 de do truc tiep.

RT5. Campaign ton gio. Chia phien, checkpoint moi diem, dung mau tmux cua L.6.

RT6. Raw data khoang vai tram MB. Ghi manifest SHA-256 va kiem dung luong dia
truoc.

RT7. Doi chung M/G/inf co `c_a ~ 0.07`; khai bao no thuoc mode `cbr`, khong
doc thanh loi.

--------------------------------------------------------------------
## T10. Chu Ky

Xac nhan sau Amendment 2, truoc khi sang T.2:

```text
[x] T0 da dien bang so va bang chung code/result Phase L.
[x] T5 va T8 da dien truoc moi phep do Phase T.
[x] T4 da duoc thay bang luoi T.1: dt=0.005, sigma_rho=a*sigma_max.
[x] Da them step response lam nguon T_relax.
[x] Da them err_mol va D-T10/D-T11/D-T12.
[x] Da them guardrail khong import link_model v1 cho module Phase T.
[x] Da sua provenance Hurst cho kappa >= 2.
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-30

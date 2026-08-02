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
sigma_rho <= min(rho_bar - 0.50, 1.05 - rho_bar) / 2.58

rho_bar 0.700 -> sigma_rho <= 0.0775
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
rho_thuc_te(t) : dem goi trong cua so W tu _bgtx.bin, chi lam V-T6b mo ta
Reich(t)       : Lindley/Reich workload scan trong tung cua so 1 s
gap_u          : Lambda(T_i)-Lambda(T_{i-1}), dung cho V-T4a/V-T6a
c_a_pooled     : CV gap real-time gop, doi chung duong V-T4b
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

Amendment 5 chot them: moi tich phan PSA/MOL phai dung `rho(t)` THIET KE tu
`rho_spec`, khong dung `rho` do lai tu dem goi. `rho_thuc_te(t)` chi dung cho
V-T6b bias/noise. Dung `rho` do vao ca hai ve la tautology vi `q_i` va
`rho_hat` cung den tu mot dong goi, co the keo `err_qs` ve gan 0 gia tao.

`err_jensen_ms` va `d_sampling_ms` la dai luong MO HINH vi ca hai ve deu tinh
tu `f`. Chung khong phai phep do truc tiep; bang chung thuc nghiem cua chung
la khi `Lambda >> 10`, `err_qs ~ 0` nen `err_total` do duoc phai khop
`err_jensen + d_sampling`.

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
sigma_max = min(rho_bar-0.50, 1.05-rho_bar)/2.58
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

D-T1. Doi chung `sigma_rho = 0` phai tai tao Phase L. Sau Amendment 11,
kiem chinh bang khoi C' cung seed, `duration=70`, `warmup=10`: digest khop
bit-exact cho `h2/poisson`, va ti so cung-seed khong co lech he thong
`|mean(r)| < 0.005`, `sd(r) < 0.010`.

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

D-T7. `c_a_operational = CV(gap_u)` doc lap voi `(sigma_rho, tau_rho)`:
lech nho hon `max(4*SE_c_a(mode,n_gaps),0.005)` va `mean(gap_u)` trong 0.5%
quanh 1.0.

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

D-T13. Hai oracle tong hop cua T.4 phai xanh truoc T.5:

```text
Oracle 1: q_i = f(rho(t_i))      -> err_qs = 0 trong 3*SE
Oracle 2: q_i = f(mean(rho))     -> err_qs + err_jensen + d_sampling = 0
```

Neu D-T1, D-T7, hoac D-T13 sai thi dung lai va sua ha tang truoc khi do tiep.

--------------------------------------------------------------------
## T6. Tieu Chi

Dung nguong dia phuong, chuan hoa theo:

```text
sigma_ref = m.sigma(mode, bw, q, rho_bar)
```

Quyet dinh:

```text
|err_qs| < 2*SE               -> khong phan biet duoc voi 0 o phan giai nay
|err_qs| / sigma_ref < 0.10  -> bo qua, Phase 20R khong doi
0.10 .. 1.00                -> cong vao band Phase 21R
> 1.00                      -> quasi-static khong dung, Phase 20R chuyen MOL
```

Khong dung mot nguong tuyet doi duy nhat. `sigma_schedule` thay doi lon giua
mode/link/rho; Phase 21R cung da chuan hoa nonconformity theo
`sigma(x)`, nen Phase T phai noi cung don vi. Moi o phai bao cao
`err_qs ± SE`, voi `SE = sd_lambda[f(rho)]/sqrt(n_goi)`.

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

V-T4a. `c_a` trong thoi gian van hanh `u = Lambda(t)`:

```text
|CV(gap_u) - c_a_design| < max(4*SE_c_a(mode, n_gaps), 0.005)
```

V-T4b. `c_a_pooled` khop cong thuc time-rescaling trong 5%, chi ap dung khi
`c_a_predicted > 0.005`.

V-T5. Doi chung am `sigma_rho = 0` tai tao Phase L. V-T5b 105s cross-seed chi
la aggregate z diagnostic. Gate chinh sau Amendment 11 la khoi C' cung-seed:
`duration=70`, `warmup=10`, so `q_T(mode,rho,seed)` voi dung
`q_L(mode,rho,seed)`. Cong digest bit-exact phai chay tren `h2` hoac
`poisson`; `cbr@0.98` bao cao nhung khong lam gate vi vung toi han D-T9.

V-T6a. Cong ghep hai thang trong thoi gian van hanh:

```text
mean(gap_u) = 1.000 trong 0.5%
CV(gap_u)   = c_a_design theo gate V-T4a noise-scaled
```

V-T6b. `rho_thuc_te(t)` tren cua so W la mo ta nhieu dem. Bias duoc kiem theo
noise model cua dao dong renewal tai bien warm-up:

```text
rho_bias_sd_pred = (FRAME_BG/cap) * sqrt(c_a^2 * Lambda(warm_s) + 1) / meas_s
abs(rho_bias / rho_bias_sd_pred) < 3
```

Sau campaign, gate tap hop tren `rho_bias_z` phai co `abs(mean_z) < 3/sqrt(n)`
va `0.6 < sd_z < 1.6`.

V-T7. `d_sampling` do duoc khop du bao bac hai trong 30%, va `q_probe_ms`
khop `q_bg_time_ms` trong sai so chuan.

V-T8. Cong A5-7 giu nguyen: `socket_drops = 0`, `n_foreign = 0`,
`n_late_ratio < 0.1%`, `|rate_ratio - 1| < 0.001`.

V-T9a. Oracle 1 T.4: he quasi-static hoan hao cho `err_qs` bang 0 trong
`3*SE`.

V-T9b. Oracle 2 T.4: he tri tre hoan toan cho
`err_qs + err_jensen + d_sampling = 0` trong sai so so hoc.

--------------------------------------------------------------------
## T8. Neu Fail Thi Sua Gi

Nhanh (a), V-T4a/V-T6a fail: kiem time-rescaling vs thinning, kiem nghich dao
`Lambda(t)` co noi suy dung trong buoc `dt`, kiem `u_i=Lambda(T_i)`, va dam
bao `normalize_rate` chi ap cho base process truoc khi rescale.

Nhanh (b), V-T5 fail: ha tang T lech Phase L. Kiem payload 1470 B, rho co
tinh probe, qdisc burst/bfifo, va `schedule_digest`. Phai kiem tren
`h2`/`poisson`; `cbr` khong du de bat mutant reimplementation.

Nhanh (c), `|err_qs| > sigma_ref` o vung binh thuong
(`rho_bar <= 0.925`, `Lambda >= 10`): truoc khi ket luan, kiem
1) Oracle 1 xanh, 2) dang dung `rho` THIET KE, khong phai `rho` do,
3) `|err_qs| > 2*SE`, va 4) `d_sampling` da tach dung. Neu ca bon deu OK thi
day la ket qua va Phase 20R chuyen MOL.

Nhanh (d), loi lon chi o `cbr,rho_bar=0.98`: ky vong duoc. Ghi hop dong
`quasistatic_valid() = False` o dai do, khop `is_reliable()`.

Nhanh (e), V-T7 fail: kiem `lambda(t_i)` trong trong so `1/lambda` co dung
rho thiet ke khong; khong dung rho thuc te nhieu do luong cho trong so nay.

Nhanh (f), Oracle 1 fail: tang phan tich sai. Kiem trong so `lambda` trong
`q_psa_load_ms` va dinh nghia `rho`/`background_pps`.

Nhanh (g), Oracle 2 fail: kiem dau `err_jensen_ms` va thu tu phan ra ba
thanh phan.

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

RT8. Phan giai cua `err_qs` bi chan boi lay mau goi huu han:

```text
SE(err_qs) = sd_lambda[f(rho)] / sqrt(n_goi)
```

O `rho_bar=0.70, a=0.90` cua ca `h2` va `poisson`, SE mot seed lon hon nguong
`0.1*sigma_ref`. Giam nhe bang 5 seed, bao cao median/CI giua seed, bao cao
SE ky vong canh moi `err_qs`, va neu `|err_qs| < 2*SE` thi phan xu la
`khong_phan_biet_duoc_o_phan_giai_nay`, khong phai "bang 0".

--------------------------------------------------------------------
## T10. Chu Ky

Xac nhan sau Amendment 10, truoc khi resume G2/G3 T.5:

```text
[x] T0 da dien bang so va bang chung code/result Phase L.
[x] T5 va T8 da dien truoc moi phep do Phase T.
[x] T4 da duoc thay bang luoi T.1: dt=0.005, sigma_rho=a*sigma_max.
[x] T.2 da dinh chinh sigma_max thanh min hai phia va them rho_spec.py.
[x] Da them step response lam nguon T_relax.
[x] Da them err_mol va D-T10/D-T11/D-T12.
[x] Da them guardrail khong import link_model v1 cho module Phase T.
[x] Da sua provenance Hurst cho kappa >= 2.
[x] T.3 da them rho_schedule.py bang time-rescaling.
[x] V-T4a/V-T6 da sua thanh operational-time gate + counting-noise description.
[x] T.4 da them t4_validate.py, synthetic oracle, va mutation tests.
[x] Da them RT8 va phan loai khong phan biet duoc o phan giai nay.
[x] Da chot tich phan QS dung rho thiet ke, V-T5 kiem tren h2/poisson.
[x] T.5 da them rho_gen.py, t5_step.py, t5_campaign.py va packet_player.py.
[x] Step response dung T_area_v2 va step v2: buoc rong, binw=0.020, hold=0.6.
[x] Da them runbook tmux va blind discipline cho RUNLOG/UNBLINDING_LOG.
[x] V-T6b da doi tu nguong tuyet doi 0.002 sang z-score theo renewal boundary.
[x] T.5 runner chi retry gate transient; deterministic fail thi dung chien dich.
[x] Campaign state da tach public fields khoi `results/phase-T/sealed/`.
[x] G1 step v1 bi loai khoi fit truc hoanh; `ensemble_average` da sua nhan A/B.
[x] Step estimator da them gate bien do `abs(amp) > 5*SE(amp)`.
[x] Step v2 da doi sang buoc rho rong, 13 diem, `step_v2_state.json`.
[x] G2/G3 khong dung `ensemble_average`, nen duoc chay sau smoke A7 sach.
[x] V-T4a da doi tu nguong tuyet doi 0.02 sang `max(4*SE_c_a, 0.005)`.
[x] Da them `measurements/gate_specs.py` va meta-test false-fail/mutant.
[x] Quet tinh 315 diem cho V-T4a/V-T6b cho 0 fail gia.
[x] Da them V-T5a/V-T5b vao `gate_row()` va `measurements/t5_controls_audit.py`.
[x] Da them `corr_group` va `reference_sd_source` vao GateSpec.
[x] Amendment 11: bo V-T5b 2% tung diem; G2 105s aggregate z pass, h2@0.70 can C'.
[x] Da them `controls-samesed` C' cung-seed 45 diem, 70/10, chay truoc G3.
[x] Amendment 12: khoa digest bit-exact doc lap interpreter, them env provenance,
    va danh dau cong bit-exact `relax_policy="never"`.
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-01

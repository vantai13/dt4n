# AMENDMENT 14 -- Phase 20R.6: tach estimand va chuyen sang band-first

Ngay ky: 2026-08-09
Trang thai: §1-41 KY TRUOC KHI CHAY cascade v2. §42 la phan ket qua append
sau khi artifact final duoc tao.
Quan he: BO SUNG cho 07-design-validation.md. KHONG thay the, KHONG xoa.

---

## 1. SUA -- Luat dung som Amd 11 khong ap dung cho G6-CASCADE

### 1.1 Estimand cu (giu nguyen, van hieu luc)

G6-PRE (= G6-TRANSFER)

Bang loi: "Bang tra mot-link do tren SplitQdiscTopo co dung lai duoc tren
TandemTopo khong?"

Cong thuc: `A' - A`

Trang thai: DA DO XONG (48 diem, 8 seed, in-band, 2026-08-07). Ket qua KHONG
bi sua doi va van duoc bao cao nguyen trang.

### 1.2 Estimand can do (chua bao gio duoc do)

G6-CASCADE

Bang loi: "Chi phi do end-to-end tren duong 3-link co bang tong chi phi cua
tung link do rieng, TRONG CUNG topology, CUNG session, CUNG seed, CUNG
background, khong?"

Cong thuc: `r = C - sum_i(B_i)`

Muc: duong (path). Don vi: ms (delay), ti le tuyet doi (loss).

### 1.3 Ly do go luat dung

Trong bieu thuc `r = C - sum(B_i)`, dai luong A KHONG xuat hien. C va B do
trong cung topology, cung session, cung seed, cung background. Moi sai lech do
"TandemTopo khac SplitQdiscTopo" xuat hien o ca hai ve va triet tieu trong hieu;
day la common-mode error.

Luat dung Amd 11 duoc viet khi G6 con duoc dinh nghia la `C - sum(A)`, cong
thuc trong do A CO xuat hien. Voi dinh nghia `C - sum(B)`, tien de do khong con
dung.

Kiem tra chong-HARKing: neu ket qua `A' - A` da PASS, sua nay VAN can thiet, vi
no la loi estimand chu khong phai phan ung voi ket qua.

## 2. SUA -- G6-TRANSFER doi tu "gate" sang "scope of validity"

Cach viet cu: "G6-PRE FAIL cho h2"

Cach viet moi: "Bang tra mot-link chuyen giao duoc sang TandemTopo cho poisson
(moi kenh) va cho h2 o kenh delay; KHONG chuyen giao duoc cho h2 o kenh loss,
do lech -0.0101 (CI90 doc tu artifact cu)."

Khong do lai. Khong sua so. Chi doi cach phat bieu.

## 3. SUA -- Estimator cua kenh loss

### 3.1 Chan doan tu artifact da co

```text
additivity_branch_a_state.json          : 1470 B, 5 pps  ->    309 goi
additivity_branch_a_state_inband.json   :   64 B, 20 pps ->  1,179 goi
load_rows[].n_bg_sent (moi file)        :               -> 39,600 goi
```

Probe 1,179 goi bao loss = 0.000000. Background 39,600 goi bao khoang 4.55e-4.
Ky vong so goi mat trong 1,179 goi la khoang 0.53, nen xac suat thay dung 0 goi
mat xap xi 59%. Probe khong phan biet duoc `loss = 0` voi `loss = 4.5e-4`.

### 3.2 Tinh power truoc khi chay

Voi `p ~ 0.01`, `delta = 0.005`, 4 phep do, `Cov = 0`:

```text
1.645 * sqrt(4 * 0.0099 / n) <= 0.005  =>  n >= 4,286
Block factor B = 10                    =>  n >= 42,860
```

Background 39,600 goi / 60 s cho khoang 198,000 goi o 300 s: du power cho
nhanh B. Dong carve-out `phi = 0.25` tren L3 cho khoang 49,000 goi o 600 s:
du power cho nhanh C.

### 3.3 Estimator moi

Nhanh B: loss lay tu background counters:

```text
loss_B_i = 1 - n_bg_recv_i / n_bg_sent_i
```

Nhanh C: dong carve-out `hsrc -> hdst`, 1470 B, `phi = 0.25`, tru khoi ngan
sach moi link.

### 3.4 Bat bien cau truc

B va C phai giong het nhau tru so link ma dong do di qua. Neu C co dong
carve-out 1470 B `phi = 0.25`, thi B cung phai co dong do 1470 B `phi = 0.25`.
Vi pham bat bien nay thi ket qua khong duoc bao cao.

### 3.5 Bon RC duoc dong cung luc

- RC2 power: 1,179 -> 40,000+ goi.
- RC4 ngan sach: carve-out, tai thuc = `rho_bar`.
- RC6 kich thuoc goi: 1470 B ca hai nhanh.
- RC7 diem bom: cung diem, cung process, ca hai nhanh.

## 4. THEM -- Ba doi chung bat buoc

```text
DC-C1 positive : L1 lam phang manh -> |r| > 3*delta, dau AM. FAIL -> DUNG.
DC-C2 negative : rho_bar = 0.30    -> |r| <= delta, CI chua 0. FAIL -> DUNG.
DC-C3 estimator: loss(background) vs loss(carve-out) o nhanh B. FAIL -> DUNG.
```

## 5. THEM -- delta_loss doi tu hang so sang nguong gay dan xuat

Bo cach chon `delta = 0.005` lam gate. Thay bang:

```text
r* := min{ r' > 0 : it nhat mot ket luan K1..K5 gay khi bom +-r' }
```

Ket luan duoc kiem:

```text
K1 err in [0.05, 0.40] moi o
K2 d_sla_lower >= 0.03 o tap G2
K3 Spearman(err, z) > 0 moi o
K4 thu tu 4 duong khong hoan vi
K5 err(h2) vs err(poisson) khong dao thu hang
```

Bao cao: `he so an toan = r* / max|CI90(r)|`.

## 6. THEM -- Gate moi

G6-CASCADE-BAND:

```text
Duoi bien +-CI90 cua phan du ghep r, khong ket luan nao trong K1..K5 bi lat.
```

Ba muc: DAT / DAT CO CO / KHONG DAT. Khong dung PASS/FAIL nhi phan cho hang
nay.

## 7. Du doan ky truoc khi chay

```text
Dau cua r = C - sum(B), kenh loss  : AM, theo pay-bursts-only-once /
                                      arrival smoothing.
Dau cua r = C - sum(B), kenh delay : AM.
Do lon |r| ky vong, loss           : 1e-3 .. 2e-2 loss tuyet doi.
Do lon |r| ky vong, delay          : 0.1 .. 1.0 ms.
r* du doan (common_mode, loss)     : 0.02 .. 0.05 loss-path neu ket luan dau
                                      tien la ranking.
He so an toan du doan              : > 1 neu CI90 nam duoi khoang tren;
                                      nguoc lai DAT CO CO.
Ket luan gay dau tien du doan      : K4_path_ranking_preserved.
So voi transfer safety 3.714       : cascade thap hon, vi cascade do tuong tac
                                      lien-link trong cung hang doi/path thay vi
                                      sai lech topology-transfer mot-link.
I^2 du doan                        : < 50%, muc tieu 0..25% voi 8 seed.
```

Neu `r > 0` (nguoc PBOO), ket qua KHONG duoc bao cao ngay. Phai chay checklist:

```text
(a) co che khuech dai that? (burst amplification qua L1 -> L2 -> L3)
(b) confound? (probe_intrusion, DC-C2, c_a giua B va C)
(c) bug? (loss ghep NHAN, digest link dich, bat bien cau truc)
```

Neu ket qua inconclusive, ket luan se la:

```text
Phan du ghep khong tach duoc khoi 0 voi power hien tai; van bao cao band o hai
dau CI90. Neu dau mut xau nhat chua vuot r*, ket luan paper dung vung trong
toan bo mien tuong thich voi du lieu. Neu dau mut xau nhat vuot r*, bao cao
pham vi hieu luc theo tung ket luan K1..K5, khong goi chung la FAIL.
```

## 8. Luat dung som moi

```text
[ ] smoke / qdisc assert FAIL      -> DUNG
[ ] DC-C1 FAIL                     -> DUNG
[ ] DC-C2 FAIL                     -> DUNG
[ ] DC-C3 FAIL                     -> DUNG
[ ] probe_intrusion_ratio > 0.02   -> DUNG
```

Khong co dieu kien nao lien quan `A' - A`.

## 9. Nhung gi khong doi

- Moi artifact va van ban Lesson 20R.0 .. 20R.5: nguyen trang.
- Ket qua `A' - A`: nguyen trang, van bao cao.
- G1 G2 G3 G4 G5 G7 H6 H7 H8 H9 QS-DELAY: khong dung toi.
- `truth_table.parquet`: KHONG SUA. Viec bom phan du chi xay ra trong bo nho,
  qua lop `BiasedTruthTable`.

## 10. BO SUNG -- Common-mode khong kiem duoc err tren topology so chang deu

Neu bơm delay deu vao moi link voi muc `r/3`, va moi duong deu co dung 3 link:

```text
delay_path(P)' = sum_i(delay_i + r/3) = delay_path(P) + r
cost(P)'       = cost(P) + r
argmin(P)'     = argmin(P)
```

Vi vay `err` bat bien voi delay common-mode la mot dong nhat thuc dai so, khong
phai ket qua thuc nghiem. Day la E10 ap lai vao cong cu band-first: common-mode
va differential phai duoc tach rieng.

`band_v2.py` tu nay bao cao ba bien the khi residual co `per_unit` theo link:

```text
common_mode  : bom gia tri gop deu vao moi link
differential : bom r_i - mean(r_i) tren cac link da do
full         : bom r_i nguyen ban tren cac link da do
```

Neu residual khong co `per_unit L1/L2/L3`, hai bien the `differential/full`
khong duoc gia lap; tool ghi `supported=false`.

## 11. BO SUNG -- Residual cascade path-only chi do duoc common-mode

Thiet ke `C - sum(B)` do mot so o muc duong. Khi bơm vao bang tra muc link, neu
khong co them thong tin, cach duy nhat la chia deu cho 3 link. Do do residual
cascade hien tai chi kiem duoc thanh phan common-mode cua cascade.

Pham vi hieu luc bat buoc ghi:

```text
G6-CASCADE v2 do residual path-level va chi propagate duoc common-mode.
Tac dong cua thanh phan differential giua cac link chua duoc do trong thiet ke
nay, tru khi chay them mot nhanh tach duong con.
```

Lua chon mo rong truoc khi chay dai: them nhanh C2 probe qua L1+L2. Khi do:

```text
cascade(L1,L2)    = C2 - (B1 + B2)
cascade(L1,L2,L3) = C3 - (B1 + B2 + B3)
dong gop L3       = cascade3 - cascade2
```

Chi phi du kien: them 16 run, khoang 3 gio voi tham so 660 s.

## 12. BO SUNG -- Clip loss lam bien thanh can duoi

Mo hinh nhieu cong `loss' = clip(loss + r, 0, 1)` co the vi pham mien vat ly o
dau am, nhat la o o loss thap. Tu nay `band_v2.py` bao cao:

```text
clip_events
eval_count
clip_ratio = clip_events / eval_count
band_is_lower_bound = clip_ratio > 0.01
```

Neu `band_is_lower_bound=true`, bien o dau am la CAN DUOI cua tac dong that,
khong duoc viet nhu tac dong dung.

## 13. BO SUNG -- r* khong lay tu diem luoi tho

Quet thô chi cho biet `r*` nam trong khoang `(r_good, r_bad]`. Bao cao `r_bad`
lam `r*` thoi phong he so an toan theo huong co loi.

Tu nay sau khi luoi tho thay diem gay dau tien, `band_v2.py` chia doi den
`tol = 1e-4` va bao cao:

```text
r_star_lo <= r* <= r_star_hi
safety_lo = r_star_lo / max|CI90|
safety_hi = r_star_hi / max|CI90|
```

Neu khong gay toi `r_max`, safety la CAN DUOI, khong phai `null`.

`r_max` mac dinh theo kenh:

```text
loss     : max(0.05, 10 * max|CI90|)
delay_ms : max(5.0, 10 * max|CI90|)
```

## 14. BO SUNG -- Internal pilot truoc full run

Truoc khi chay 64 diem qua dem, co the chay pilot 3 seed:

```text
seeds = 101,102,103
B + C tai rho_bar=0.925
```

Pilot CHI duoc dung de uoc luong `sd(d_s)` va tinh lai so seed can thiet:

```text
n_seed = (1.645 * sd(d_s) / delta)^2
```

Lenh doc pilot:

```bash
python3 tools/pilot_power_only.py \
  --branch-b results/phase-20R/branch_b_pilot.json \
  --branch-c results/phase-20R/branch_c_pilot.json \
  --rho-bar 0.925 \
  --modes poisson,h2
```

Output chi gom `sd(d_s)`, `n_seed` quan sat, va `n_seed_required`; khong in
point estimate cua residual.

Khong dung pilot de quyet dinh dung/tiep dua tren gia tri `r`. Khong bao cao
ket qua pilot rieng. Khi chay tiep, tat ca seed duoc gop vao mot phan tich duy
nhat.

## 15. BO SUNG -- Golden transfer converter giu cong thuc legacy

`transfer_residual.py` giu nguyen cong thuc cua `additivity_band.py` de tai lap
bit-exact artifact cu:

```text
point = mean(vals)
se    = mean(se_i) / sqrt(k)
```

Cong thuc nghich phuong sai trong `residual_spec.pool_inverse_variance` van la
ham dung cho residual moi khi pre-register rieng. Voi converter legacy, khong
doi cong thuc de tranh tron "sua schema" voi "sua ket qua".

## 16. BO SUNG SAU REVIEW VONG 2 -- Smoke khong duoc trich dan

Golden drift check ngay 2026-08-09 cho ket qua:

```text
legacy additivity_band.py chay lai vs artifact cu: max_abs_delta = 0.0
```

Ket luan: `truth_table.parquet`, `sla_calibration.json`, va
`decision_error_v2.py` khong troi. Sai khac truoc do den tu tham so smoke
`n=2000`, khong den tu data/code drift.

Tu nay artifact `band_v2` phai tu ghi:

```text
seeds, n, rho_bar_filter
residual_file + sha256
truth_table + sha256
calibration + sha256
git_commit, git_dirty, wall_utc
is_smoke = (n < 50000)
```

Moi artifact co `is_smoke=true` chi dung de debug cong cu, khong duoc trich
so vao paper hoac ket luan Phase 20R.

## 17. BO SUNG -- Bien the residual phai dung mot scaling duy nhat

Voi residual co `per_unit L1/L2/L3`, ba vector bom duoc dinh nghia bang cung
mot he so:

```text
s = r_endpoint / point
common_mode_i  = s * mean(r_i)
differential_i = s * (r_i - mean(r_i))
full_i         = s * r_i
```

Do do bat bien:

```text
full = common_mode + differential
```

phai dung tung link, tung dau mut CI. Neu `point ~ 0`, khong duoc tu fallback
sang chuan hoa RMS; phai dung va pre-register quy tac khac truoc khi chay.

Tren kenh delay, vi moi duong trong `topology_v7` co 3 chang, thanh phan
common-mode cong cung mot hang so vao moi duong. He qua:

```text
d_err(full) == d_err(differential)    # delay channel only
```

Day la dong nhat thuc dai so, khong phai quan sat thuc nghiem.

## 18. BO SUNG -- Residual ap theo lop link, khong theo ten link

Ba link do trong `TandemTopo` dai dien cho lop `(bw, q)` trong `topology_v7`:

```text
L1 -> alpha (8,18)  -> {uA, vC}
L2 -> beta  (6,13)  -> {uB, ac, bc, bd, vD}
L3 -> gamma (4,10)  -> {ad}
```

Vi vay residual cua L1 phai bom vao ca `uA` va `vC`, khong chi vao link duoc
ghi trong `TANDEM_LINKS`. Test canh bat buoc: bom L1 tren kenh loss lam loss
cua `uA` va `vC` tang dung cung mot luong.

## 19. BO SUNG -- Scan cong bo min qua bien the va K5 dung `joint`

Scan khong duoc chi chay `common_mode`, vi day thuong la bien the it nguy hiem
nhat voi xep hang. Bao cao chinh thuc:

```text
safety_published = min safety_factor qua moi bien the duoc support
```

Voi bracket `r_star_lo <= r* <= r_star_hi`, dung `r_star_lo` de bao cao thang
bao thu. Neu khong gay toi `r_max`, gia tri do chi la can duoi.

`K5_family_order_preserved` so sanh `err(h2)` voi `err(poisson)`, nen ket qua
chinh cua K5 phai chay bien the `joint`: bom dong thoi residual cua tung mode
vao chinh bang tra cua mode do. Cac ket qua mot-mode duoc giu lam phu luc va
phai ghi ro la kich ban gia dinh.

## 20. BO SUNG -- Power Monte-Carlo cua band (da sua boi §21)

Ban dau tool dung cong thuc SE cua mot uoc luong err don le:

```text
se_unpaired = sqrt(err * (1 - err) / (n * len(seeds)))
```

Cong thuc nay KHONG dung cho `d_err = err_perturbed - err_base`, vi hai ve dung
cung seed va cung trace. Tu §21, tool chi ghi `se_unpaired_for_reference` de
doi chieu; ket luan ve `d_err` dung McNemar ghep cap.

## 21. BO SUNG -- `d_err` la tuong phan ghep cap, dung McNemar

Sua ngay 2026-08-09: `d_err` khong duoc kiem bang SE cua mot uoc luong err
don le. Hai ve `err_perturbed - err_base` dung cung seed, cung trace `rho(t)`,
cung chi so mau; chi khac bang tra. Vi vay day la thiet ke ghep cap.

Tool tu nay dem truc tiep:

```text
b = so mau: base DUNG, perturbed SAI
c = so mau: base SAI,  perturbed DUNG
D = b + c
d_err = (b - c) / N
se_paired = sqrt(D) / N
```

Voi `D <= 25`, tool dung exact sign test hai phia. Voi `D > 25`, tool dung
xap xi chuan McNemar va tinh p-value bang `erfc` de khong mat precision o z lon.

Artifact band phai ghi `b`, `c`, `n_discordant`, `n_total`, `se_paired`,
`p_mcnemar`, `p_mcnemar_method`, va `se_unpaired_for_reference`. Truong
`se_unpaired_for_reference` chi de doi chieu; khong dung de ket luan ve `d_err`.

## 22. BO SUNG -- Dong nhat thuc khong chay qua thong ke

Truong hop:

```text
channel = delay_ms
variant = common_mode
moi duong co cung so chang
```

la dong nhat thuc dai so cua `err`, khong phai mot uoc luong thong ke. Artifact
tu nay ghi:

```text
is_algebraic_identity = true
mc_resolvable = null
se_monte_carlo_method = algebraic_identity
n_discordant_range = [0, 0]
```

Khong duoc viet "khong du power" cho dong nay. Cau dung la: `d_err = 0` theo
dinh ly; rieng `d_sla` van co the doi vi day la chi tieu nguong.

## 23. BO SUNG -- Quy tac co gian cho `joint`

Ky truoc khi chay scan final: dung QT-1.

```text
QT-1 shared multiplier:
  anchor record dang quet dinh nghia s = r_endpoint / point(anchor)
  moi residual cung channel, moi mode, duoc nhan voi cung s
```

Dien giai: scan `joint` hoi "neu moi bang tra sai cung mot BOI SO so voi phan
du do duoc cua chinh no thi ket luan nao gay truoc?" Cach nay giu nhat quan
voi dinh nghia safety la boi so cua phan du da do.

## 24. DU DOAN SUA DOI, KY TRUOC SCAN FINAL

Du doan cu "common-mode luon hien hon differential" bi smoke scan bac bo. Ly do:
du doan cu suy tu chi tieu xep hang sang chi tieu nguong.

Du doan moi truoc khi chay `breakdown_scan_transfer.json` non-smoke:

```text
[x] Bien the rang buoc cho K4/K5 la differential/full o cac o xep hang.
[x] Bien the rang buoc cho K2 la common_mode o cac o nguong.
[x] safety_published se den tu poisson/loss, K2, common_mode.
[x] Gia tri safety_published ky vong: 2.5 .. 3.5 lan max|CI90|.
[x] Neu n=120000 dao nguoc mau hinh smoke, ghi la ket qua phu thuoc n va dieu
    tra truoc khi ket luan; khong chon ban nao dep hon.
```

Phat bieu muc tieu neu scan final xac nhan:

```text
Differential residual rang buoc ket luan ve xep hang. Common-mode residual
rang buoc ket luan ve nguong. Khong bien the nao chi phoi moi ket luan, nen
safety cong bo phai la min qua bien the.
```

## 25. LUAT DUNG CHO LESSON 20R.6

Lesson 20R.6 duoc coi la hoan thanh khi:

```text
[x] G6-CASCADE co con so + CI, hoac co van ban ghi ro vi sao khong do duoc.
[x] G6-TRANSFER da chuyen thanh scope of validity.
[x] Bang bien he thong transfer o n=120000, 4 bien the, ca hai dau CI90.
[x] safety_published = min qua bien the, kem dien giai.
[x] Moi con so trong docs doc truc tiep tu artifact non-smoke.
```

Khong mo rong them pham vi trong phase nay. Cac cai tien moi nhu bien the thu
nam, mo hinh loss nhan, hoac nhanh C2 hai-link se ghi vao future work neu chua
the doi ket luan hien tai.

## 26. KET QUA BAND TRANSFER NON-SMOKE SAU McNEMAR

Artifact: `results/phase-20R/band_v2_transfer.json`

```text
n = 120000, seeds = 101..105, is_smoke = false
variants = common_mode, differential, full, joint
```

Ket qua `d_err`:

```text
h2/loss common_mode        : mc_resolvable = false, p_min = 0.375
h2/loss differential/full  : mc_resolvable = true
h2/delay common_mode       : algebraic identity, mc_resolvable = null
h2/delay differential/full : mc_resolvable = true

poisson/loss moi bien the  : mc_resolvable = true
poisson/delay common_mode  : algebraic identity, mc_resolvable = null
poisson/delay differential/full : mc_resolvable = true
```

Dong co `|d_err|` lon nhat trong artifact:

```text
poisson/loss/full: max|d_err| = 0.0040204
err goc poisson@0.925 = 0.2950
```

`d_sla` o o thuoc G2:

```text
poisson@0.925 d_sla goc = 0.0986
d_d_sla xau nhat cua common_mode = -0.0088
d_sla xau nhat sau bom = 0.0898 > 0.03
```

Ket luan band transfer: trong bien CI90 do duoc, khong thay dich chuyen nao
gan mep G1/G2. Cac CI block chi noi rang dich chuyen nho nay co the phan biet
khoi nhieu Monte-Carlo co tuong quan thoi gian, khong noi rang no lon ve mat
ket luan.

## 27. DONG NHAT THUC THU BA -- `joint == full` trong band

Trong che do `band`, moi hang la metric cua mot o don le, vi du `h2@0.925`.
Metric nay chi goi:

```text
tt.path_tables(mode="h2", ...)
```

Do do viec `joint` bom them residual vao `poisson` khong the anh huong hang
`h2`, va nguoc lai. He qua:

```text
joint == full    # trong band per-cell metrics
```

Day la dong nhat thuc thiet ke, khong phai ket qua do. Artifact band tu nay ghi:

```text
equals_full_by_construction = true  # voi variant joint
n_independent_variants = 3          # common_mode, differential, full
```

`joint` chi co y nghia doc lap trong `scan`, noi ket luan K5 so sanh lien-mode.

## 28. `d_sla` co resolvability rieng, khong dung McNemar

`d_sla` la hieu cua hai chi bao vi pham SLA:

```text
delta_d_sla[t] = d_sla_perturbed[t] - d_sla_base[t] in {-1, 0, +1}
```

Vi vay khong dung McNemar. Sau §32, tool dung block bootstrap ghep cap cua
chuoi hieu de nhat quan voi G7:

```text
d_sla_se_method = block_bootstrap_paired_samplewise_d_sla_delta
d_sla_z_max = max abs(d_d_sla) / d_sla_se_block
d_sla_resolvable = 0 nam ngoai CI90 block cua it nhat mot dau CI
```

O cap hang, artifact ghi:

```text
d_sla_z_max
d_sla_resolvable
```

Truong `worst_endpoint_resolvable` chi ap dung cho `d_err`; khong thay the
kiem tra rieng cua `d_sla`.

## 29. SUA PHAT BIEU -- Single dissociation, khong phai double dissociation

Du lieu non-smoke cho thay phat bieu "differential rang buoc xep hang, common
rang buoc nguong" qua sach. Phat bieu dung hon:

```text
common-mode gan nhu chi tac dong nguong:
  - delay common-mode khong the doi err theo dong nhat thuc dai so
  - loss common-mode co the doi err vi loss ghep phi tuyen, nhung hieu ung yeu

differential tac dong ca xep hang va nguong.
```

Co che:

```text
delay_path = sum delay_i
  bom +c vao moi link -> moi duong +3c -> hieu giua duong khong doi

loss_path = 1 - product(1 - p_i)
  bom p_i + c vao moi link -> do dich path phu thuoc p_i cua chinh duong do
  -> common-mode cap link khong con common-mode cap path
```

Cau chot cho paper: tinh common-mode khong duoc bao toan qua phep ghep phi
tuyen. Do do bien the rang buoc phu thuoc vao ket luan va vao dang phep ghep.

## 30. CHECKLIST TRUNG KHOP HOAN HAO VA LUAT DUNG

Them muc prereg canh:

```text
[ ] Trung khop hoan hao: co o nao bang dung 0, hoac hai cot trung toi chu so
    cuoi? Neu co, chung minh do la dong nhat thuc va ghi test canh, hoac tim
    bug. Khong duoc coi la ket qua do.
```

Luat dung da ky:

```text
Sau khi hoan thanh H.1..H.10, Lesson 20R.6 DONG.
Moi phat hien ve sau ghi vao FUTURE_WORK.md, KHONG lam trong phase nay.

Danh sach future work:
  - mo hinh nhieu nhan thay vi cong cho kenh loss
  - nhanh C2 hai-link de tach dong gop cua L3
  - phan du cascade o rho_bar khac 0.925
  - bien the thu 5 (per-path residual)
```

File theo doi: `docs/phase-20R/FUTURE_WORK.md`.

Ly do: muc do nghiem trong cua bon vong ra soat da giam dan tu "sai ket luan"
sang "mat ket luan" sang "ghi chep/dien giai". Tieu chi dung la du de ket
luan, khong phai khong con khiem khuyet nao.

## 31. SUA -- r* cua K1/K2 nhay voi n

Du doan cu "`r*` it nhay voi n" bi bac bo boi baseline:

```text
                 n=2000      n=120000
h2 err           0.109351     0.072558
h2 d_sla         0.020362     0.015815
poisson err      0.288839     0.295005
poisson d_sla    0.063097     0.098596
```

K1/K2 la nguong tren mot trung binh uoc luong, nen `r*` ke thua bat dinh cua
trung binh do. Scan re `n=30000` chi duoc dung de BAO vung; gia tri cong bo
phai duoc quyet dinh o `n=120000`, hoac phai ghi ro do la smoke/pilot.

Quy tac scan hai tang:

```text
tang re  : tim bracket rong
tang dat : xac nhan bracket va refine r* tai n=120000
neu bracket n=120000 khong chua nghiem -> no rong, khong chon ban dep hon
```

## 32. SUA -- SE cua band dung block bootstrap de nhat quan G7

McNemar iid dung cho cap bat dong doc lap, nhung mau trong mot seed la chuoi
thoi gian tu `rho(t)`. Tu nay artifact band ghi ca iid va block:

```text
se_iid_mcnemar
se_block
ci90_block
inflation_factor = se_block / se_iid
block_len_requested = round(BLOCK_S / DT)
block_len = block_len_requested neu du mau
resolvable_block = 0 nam ngoai CI90 block
```

`worst_endpoint_resolvable` va `both_endpoints_resolvable` dung block CI, khong
dung p-value McNemar iid. `p_mcnemar_min` duoc giu de doi chieu lich su.

Chap nhan truoc: neu block bootstrap lam mot so dong true -> false, do la ket
qua dung hon, khong phai mat mat. Headline "khong lat ket luan" khong phu
thuoc vao viec `d_err` co khac 0 co y nghia hay khong.

## 33. KET QUA POTENCY VA CO CHE LOSS PHI TUYEN

Artifact band tu nay ghi:

```text
potency = max|d_err| / rms(vector bom tai endpoint xau nhat)
potency_ratio_diff_over_cm = potency(differential) / potency(common_mode)
```

Ket qua non-smoke:

```text
h2/loss      differential/common potency = 127.9x
poisson/loss differential/common potency =   2.64x
h2/delay va poisson/delay: common potency = 0 theo dong nhat thuc
```

Dien giai da sua: day la single dissociation, khong phai double dissociation.
Common-mode delay khong doi xep hang do delay ghep cong tinh va moi duong co
cung so chang. Common-mode loss co the doi xep hang vi loss ghep phi tuyen:

```text
loss_path = 1 - product(1 - p_i)
```

Mot dich chuyen deu o muc link khong duoc bao toan thanh dich chuyen deu o muc
path. Artifact ghi them `loss_common_mode_leakage` de theo doi do tan cua dao
ham path-loss theo tung mode; day la kiem tra co che, khong phai gate.

## 34. SUA -- RHO gate: sua nguon nhieu, khong noi nguong tuy tien

Chan doan ngay 2026-08-09: preflight B/L2 120 s fail `rho=0.00360` khong phai
loi ha tang. Cac gate khac deu sach:

```text
socket_drops = 0
foreign      = 0
late_ratio   = 4.1e-4 < 0.001
rate_error   = 1.9e-5 < 1e-4
```

Nguon lech la probe Poisson out-of-band: voi `probe_share = 0.16458`,
`duration = 120 s`, `N ~= 9797` nen `sd(rho_error) = probe_share/sqrt(N) =
0.00166`. Nguong co dinh `0.003` chi la `1.80 sigma`, tuong ung bao dong gia
khoang 7.1% moi diem, va khoang 36% cho 6 diem B preflight. Day la tinh chat
cua thiet ke gate ngan, khong phai tinh chat cua ket qua.

Sua da ky truoc khi chay lai:

1. Probe out-of-band dung Poisson dieu kien theo so goi co dinh:
   `n_packets = round(rate_pps_nominal * duration_s)`. Lich den la thong ke
   thu tu cua `n_packets` mau uniform tren `[0, duration_s)`, nen la mau chinh
   xac tu `Poisson | N=n`; `sd(N)=0`.
2. Artifact live ghi `probe_count_policy`, `n_probe_expected`, va metadata
   `rho_gate`.
3. Gate rho dung nguong duration-aware:

```text
sigma_counting = probe_share / sqrt(n_probe_expected)
rho_threshold  = max(0.003, 4 * sigma_counting)
```

Du doan truoc khi chay lai: voi fixed-count, `max_abs_total_rho_error` o moi
diem preflight 120 s phai ve muc jitter dinh thoi, ky vong < `5e-5`.

## 35. SUA -- QT-1 sai don vi, joint scan dung QT-3

Quy tac QT-1 cu cho `joint`:

```text
s = r_endpoint / point(anchor)
```

sau do ap cung `s` cho residual cua moi mode trong cung channel. Khi
`|point_poisson|` nho hon `|point_h2|`, dong `poisson/loss/joint` co the bi
rang buoc boi diem gay cua `h2` nhung lai duoc bieu dien bang don vi
`poisson`. Vi vay `safety_published` cu cua scan `n=30000` khong dien giai
duoc.

Tu nay scan `joint` dung QT-3:

```text
lambda = 1  <=>  moi mode bi bom dung bang endpoint CI90 xau nhat cua CHINH NO
vector_mode = lambda * vector_mode * ci_max_mode / |point_mode|
```

`lambda*` la he so an toan khong thu nguyen va doi xung theo mode anchor.
Artifact scan phai ghi:

```text
scan_axis = "lambda_ci90_multiple"
first_broken_cell
first_broken_detail
```

Band report van canonicalize `joint` thanh `full` cho metric per-cell; y nghia
doc lap cua `joint` chi nam o scan co cac ket luan lien-mode.

## 36. SUA -- K4 la ket luan tat dinh, khong phu thuoc seed/n

`K4_path_ranking_preserved` tinh ranking tu bang tra tai mot vector `rho` co
dinh:

```text
rho = C.rho_vector(rho_bar)
cost = tt.path_tables(mode, rho, w_loss)
ranking = argsort(cost)
```

Khong co seed, khong co `n`, khong co Monte-Carlo. Bang chung thuc nghiem
phu: cac dong gay boi K4 trong scan `n=2000` va `n=30000` khop bit hoac co
bracket chong nhau, trong khi K1/K2/K5 nhay 24-25%.

Tu nay artifact scan ghi them:

```text
scan_split_policy.K4_path_ranking_preserved =
  "deterministic_path_ranking_no_seed_no_n"
k4_deterministic.method = "deterministic_path_ranking"
k4_deterministic.n_dependence = "none"
```

K1/K2/K3/K5 van phai duoc quyet dinh tai `n` preregistered cua scan cong bo.
File `n=30000` chi dung de bao vung cho cac K Monte-Carlo, khong dung lam con
so cong bo cho K1/K2/K3/K5.

## 37. SUA -- guard paired cascade phai kiem link probe di qua

Guard cu trong `cascade_residual.py` so `trajectory_digest`, tuc digest cua ca
ba link. Dieu nay sai estimand voi thiet ke carve-out:

- Branch B/Li chi carve-out tren link Li; hai link khong duoc probe di qua van
  chay rho_bg day.
- Branch C carve-out tren ca ba link, vi probe di het T123.

Vi vay digest ca ba link giua B/Li va C khong the khop, va lech do la dung
thiet ke. Bat bien dung la:

```text
load_schedule_digests[link_dich_cua_B/Li]
  == load_schedule_digests[link_tuong_ung_cua_C]
```

Guard moi dung `traversed_link_digest(row, link)` va chi so digest cua chinh
link ma probe di qua. Link khong-dich duoc phep lech; neu chung khong lech thi
carve-out co the chua duoc ap dung.

He qua: pilot 3 seed fixed-count la paired hop le va duoc tinh vao tap du lieu
cuoi. Khong chay lai pilot.

## 38. SUA -- DC-C3 la doi chung qua trinh den, khong phai gate chung cho h2

DC-C3 cu so `probe_loss` voi `bg_loss` tren cung link. No chi la gate hop le khi
probe va background co cung qua trinh den. Voi `poisson`, dieu nay dung va
nghiem thu theo `|z| <= 3`.

Voi `h2`, background la bursty con probe out-of-band la Poisson fixed-count
muot hon. Trong FIFO chung, hai luong con co qua trinh den khac nhau co the co
ti le loss khac nhau; probe mat it hon background la hien tuong vat ly, khong
phai artifact cua thiet ke. Do do DC-C3 khong gate h2. H2 duoc chuyen thanh
doi chung co che DC-C3b: chay mot diem h2 voi probe sinh tu h2; neu |z| ve <= 3
thi xac nhan khac biet do qua trinh den.

Quan trong: `truth_table.loss` cua Phase L cung do loss cua probe, nen Phase L
va Phase 20R.6 dang nhat quan theo goc nhin probe. DC-C3 h2 khong chan ket qua
cascade.

## 39. PHAM VI -- can ghi c_a cho cac run carve-out

Phase L co metadata `c_a`, nhung run 20R.6 out-of-band truoc day chua dua c_a
len row tong hop. Tu nay row live ghi:

```text
load_rows[].c_a
c_a_by_link
c_a_bg_schedule_by_link
c_a_bg_actual_by_link
c_a_aggregate_schedule_by_link
c_a_aggregate_with_probe_by_link
```

`c_a_aggregate_with_probe_by_link` tai dung lich nen va lich probe fixed-count
de uoc luong c_a tong hop cua link ma probe di qua. Day la metadata pham vi:
contrast `C - sum(B)` van dung vi B/C dung cung carve-out, nhung viec bom phan
du cascade len bang tra gia dinh phan du on dinh theo c_a. Gia dinh nay chua la
gate da chung minh; neu can mo rong, dua vao `FUTURE_WORK.md`.

## 40. SUA -- loss cascade dung estimator probe, khong dung background loss

Muc nay thay the phan loss estimator o §3.3 cho cascade v2.

Ly do:

1. Nhanh C khong co dai luong "background loss end-to-end": background la
   link-local (`hload_i -> hsink_i`). Dung `bg_loss` cho B va `probe_loss` cho C
   la estimator mismatch (RC1).
2. `truth_table.loss` cua Phase L cung duoc do bang dong probe, nen dung
   `probe_loss` trong 20R.6 giu estimator nhat quan Phase L -> 20R.6.
3. Tren link probe di qua, `rho_bg` khop giua B/Li va C. Link khong di qua co
   lich khac nhau do carve-out, nhung khong anh huong phep do probe tren link
   dich.

Pham vi can viet ro trong report:

```text
Phan du cascade do bang dong probe muot nhung trong nen. Voi h2, probe va nen
co ti le loss khac nhau dang ke vi qua trinh den khac nhau; phan du bao cao la
cascade ma mot dong tham chieu muot trai qua, nhat quan voi cach bang tra duoc
do trong Phase L. Viec ngoai suy sang loss cua chinh nen chua duoc kiem.
```

`bg_loss` chi con la doi chung DC-C3/DC-C3b, khong tham gia estimand cascade.

## 41. SUA -- residual cascade muc duong chi ho tro common_mode

Residual cascade co `level = "per_path"` va khong co `per_unit` theo link. Do
do:

```text
supported(common_mode)   = true
supported(differential)  = false
supported(full)          = false
supported(joint)         = false
```

Khong duoc bom `differential = 0` roi dien giai "differential khong anh huong".
Do la bom rong im lang (RC8). Scan cascade cong bo chi dung `--variants
common_mode`.

## 42. KET QUA -- cascade v2 final seed 101-108

Artifact:

```text
results/phase-20R/residual_cascade.json
results/phase-20R/band_v2_cascade.json
results/phase-20R/breakdown_scan_cascade.json
results/phase-20R/tmux_logs/p20r6_scan_cascade.log
```

Residual `C - sum(B_i)`:

```text
mode     channel    r_path       se          CI90
poisson  loss       -0.009522    0.000373    [-0.010135, -0.008908]
poisson  delay_ms   -0.746400    0.059438    [-0.844166, -0.648633]
h2       loss       -0.009351    0.000432    [-0.010062, -0.008641]
h2       delay_ms   -0.449241    0.030064    [-0.498692, -0.399791]
```

Moi residual co `n_pairs = 8`, dau am 4/4, khong CI90 nao chua 0. Dau am khop
du doan pay-bursts-only-once: do tren duong end-to-end nho hon tong ba phep do
link rieng vi burst da duoc tra/lam phang o node truoc.

DC-C3:

```text
max |z| applicable = 2.084 <= 3.0  # poisson gate dat
max |z| all modes  = 28.632        # h2 khong gate theo §38
```

Band cascade `n=120000`:

```text
supported(common_mode)  = true  cho 4/4 residual
supported(differential) = false cho 4/4 residual
supported(full)         = false cho 4/4 residual
supported(joint)        = false cho 4/4 residual

poisson/loss/common_mode:
  d_err = [+0.024084, +0.029663]
  d_sla shift = [-0.079342, -0.067121]
  clip_ratio = 43.20%
  band_is_lower_bound = true
  worst_endpoint_resolvable = true
```

Scan cascade `n=120000`, `--variants common_mode`:

```text
safety_published = 0.868750
binding          = poisson / loss / common_mode
r*               = [0.008805, 0.008868]
first_broken     = K4_path_ranking_preserved
first_broken_cell= poisson@0.925
K4 detail        = P1,P3,P4,P2 -> P3,P1,P4,P2

poisson/delay safety = [4.533203, 4.533301], first_broken=K2
h2/loss safety       > 10.00
h2/delay safety      > 10.03
```

Doi chung co che K4: tai `poisson@0.925`, cost baseline cua hai duong bi lat
la cap gan nhau nhat:

```text
P1 = 112.9658
P3 = 120.5115
|P1-P3| = 7.5457  # nho nhat trong 6 cap
```

Do do K4 gay o dung cap co khe quyet dinh mong manh nhat, khop dien giai
decision-margin.

Dien giai da khoa: cascade residual am nen twin cong tinh la bao thu theo
huong da ky. Tuy nhien do bao thu do duoc lon hon nguong gay cua K4 tai
`poisson@0.925`, vi vay phat bieu cascade khong duoc danh PASS tuyet doi; no
duoc bao cao nhu scope-of-validity co safety `0.868750`.

Caveat bat buoc:

1. `clip_ratio=43.20%` tren `poisson/loss/common_mode`, nen bien am la CAN DUOI
   cua tac dong that trong mo hinh nhieu cong bi chan tai 0.
2. Residual cascade do o muc duong. Viec bom vao bang tra bang cach chia deu
   cho 3 link la xap xi tuyen tinh; voi loss per-link toi cap `0.075`, sai so
   bac hai khong con bo qua duoc.
3. Cac artifact phan tich nay ghi `git_dirty=true` vi repo chua co commit sach
   gom code/doc/artifact moi; khong can chay lai du lieu Mininet, nhung khi
   trich so vao ban nop can tao commit/chinh sach provenance sach.

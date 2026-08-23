# AMENDMENT 23-52 -- SLA ngoai sinh, uoc luong pivotal, va khoa du doan 23.21

Ngay ky : 2026-08-23
Tag     : amendment-52
Lesson  : 23.21
Loai    : TIEN DANG KY (dong S14)
Prereq  : amendment-51 (tag `amendment-51`, commit `09b19f4`)

## 0. Nam hieu chinh so voi ban thao ngoai repo

Ban thao duoc doi chieu voi HEAD `09b19f4` truoc khi ky. Nam cho lech, ghi lai
de khong ai phai doan lai:

```text
(a) GATE: ban thao dung G23-147..G23-155. Vung do DA duoc cap cho lesson
    23.20E o amendment 23-51 (cach day mot commit). Day suyt la va cham ma
    thu BAY. Ban nay dung G23-153 .. G23-161.

(b) LOSS_EXCHANGE nam o `measurements/sla_calib_v2.py:27`, KHONG phai o
    `twin/cost_v2.py`. Quan trong hon: Amendment 2 CO Y TACH no khoi `T_loss`
    (xem muc 2b). Quy tac equal-budget HOP NHAT lai hai thu do. Day la mot
    DAO NGUOC quyet dinh cu, phai tuyen bo, khong duoc lam lang le.

(c) `opt_viol_rate` KHONG dung chinh xac 0.1500 o ca 8 cell. Do duoc:
    {0.149995, 0.150000, 0.150005}. Bang chung S14 van dung -- do la dung
    sai so bisection -- nhung phai ghi dung so.

(d) `cert/eight_cell_sweep.py` DA co `sla_artifact` xuyen suot (dong 175, 180,
    187, 226, 251). Chi THIEU co CLI. Ban va nho hon ban thao mo ta nhieu.

(e) Gate "L44, L45 dong" SAI ma. Trong repo nay `L44` = S13 (rho doc lap theo
    link) va `L45` = xuat xu beta -- ca hai vua mo o amendment 23-51 va
    KHONG dong duoc boi 23.21. Han che ma 23.21 that su dong la `L40` va
    `L41`. Da sua o muc 7.
```

## 1. Van de duoc dong

`S14` -- nguong SLA va `w_loss` la NOI SINH. Bang chung do duoc tren
`results/LIVE/phase-20R/sla_calibration.json`:

```text
w_loss == t_delay_ms * 100      DUNG o ca 10 cell kha thi (sai so < 1e-9)
opt_viol_rate == 0.15           o ca 8 cell "gate", trong sai so bisection
                                {0.149995, 0.150000, 0.150005}
```

Hai dang thuc tren khong phai ket qua do duoc. Chung la hau qua co hoc cua
vong diem bat dong trong `measurements/sla_calib_v2.py::calibrate_cell`:

```text
w_loss --(2)--> argmin cost --(3)--> phan vi p --(1)--> t_delay --> w_loss

(1) w_loss  = t_delay / LOSS_EXCHANGE                        DINH NGHIA
(2) opt     = argmin(delay + w_loss * loss)
(3) t_delay = percentile(delay[opt], p), p giai bang bisection
              sao cho viol = TARGET_VIOL = 0.15
```

Mot nguong duoc giai nguoc tu chinh du lieu dang duoc danh gia thi khong con
la mot nguong; no la mot cach viet lai du lieu.

## 2. SLA ngoai sinh -- KHOA CHO TOAN BO PAPER

| id | T_delay | T_loss | w_loss | nguon |
|---|---:|---:|---:|---|
| S-A | 150 ms | 1.0% | 15000 | ITU-T G.114: one-way mouth-to-ear <= 150 ms chap nhan duoc cho thoai |
| **S-B** | **50 ms** | **1.0%** | **5000** | CHINH -- phan bo MOT chang trong ngan sach end-to-end G.114 |
| S-C | 20 ms | 0.1% | 20000 | che do dieu khien chat (tele-control / cong nghiep) |

### 2a. `w_loss` -- ty gia doi ngang ngan sach

```text
cost = delay_ms + w_loss * loss
Tai diem nguong, hai so hang phai nang NGANG NHAU:
    T_delay = w_loss * T_loss   =>   w_loss = T_delay / T_loss
```

Day la mot lua chon CO NGUYEN TAC, khong phai mot fit. Noi cach khac: "dung
het ngan sach TRE" duoc dinh gia bang "dung het ngan sach MAT GOI".

### 2b. Dao nguoc mot quyet dinh cua Amendment 2 -- tuyen bo tuong minh

`measurements/sla_calib_v2.py:403` ghi:

```text
"Amendment 2 tach LOSS_EXCHANGE = 0.01 khoi T_loss: 0.01 la ti gia quy doi
 loss sang ms, con T_loss la nguong SLA duoc hieu chuan tung o."
```

Va `test/test_phase20r_sla_calib.py::test_loss_exchange_is_distinct_from_calibrated_t_loss`
ghim su tach do: `abs(t_loss - LOSS_EXCHANGE) > 0.01`.

Viec tach la DUNG trong the gioi NOI SINH: `T_loss` khi do la mot phan vi do
duoc (0.00042 .. 0.19461 tuy cell), nen no khong the dong thoi la ti gia quy
doi -- ti gia phai chung cho moi cell.

Trong the gioi NGOAI SINH, `T_loss` khong con la phan vi do duoc; no la mot
NGAN SACH do ta dat. Luc do viec dat ti gia bang chinh ngan sach la co nghia:
day la dinh nghia cua equal-budget.

```text
QUYET DINH: trong `sla_exogenous`, loss_exchange := T_loss.
            Dang thuc `w_loss = t_delay_ms / loss_exchange` duoc GIU nguyen,
            nen truong `loss_exchange` khong bi nap nghia moi -- no van la
            "so chia sinh ra w_loss tu t_delay".

            `sla_calib_v2` KHONG bi sua. `LOSS_EXCHANGE = 0.01` va test ghim
            no GIU nguyen. Hai the gioi ton tai song song; doi chung am
            (G23-159) doi hoi dung the.
```

He qua phai theo doi: voi `S-C`, `loss_exchange = 0.001`. Moi noi doc truong
do se thay mot gia tri khac 0.01 lan dau tien. Da quet:
`cert/eight_cell_sweep.py:91, 182, 204, 215` -- deu DOC tu artifact, khong
hard-code. Khong con cho nao khac doc truong nay.

## 3. Do nhay `w_loss` (giu S-B co dinh)

```text
w_loss in {1250, 5000, 20000} = {w*/4, w*, w*x4}
```

Can duoi `1250` chon co y de BAO TRON dai noi sinh cu `[1245.6, 4722.7]`.
Sweep HAI PHIA quanh gia tri chinh; sweep mot phia la sweep yeu.

## 4. Uoc luong CHINH cua vung song -- `S_pivotal`

Voi moi buoc thoi gian, xet vector vi pham tren K = 4 duong:

```text
S_trivial   = P( khong duong nao vi pham )     -> chon duong VO NGHIA
S_collapsed = P( moi duong deu vi pham )       -> chon duong VO NGHIA
S_pivotal   = 1 - S_trivial - S_collapsed      -> chon duong QUYET DINH

Ba so cong lai dung bang 1. Day la mot PHAN HOACH.
```

Ban ke hoach cu dinh nghia vung song bang `0 < P(vi pham | duong toi uu) < 1`.
Dai luong do PHU THUOC `w_loss`, vi `w_loss` quyet dinh duong nao la "toi uu".
Tuc la phan hoach song/chet con dinh vao mot tham so tuy chon.

`S_pivotal` chi nhin TAP duong va nguong SLA, khong nhin duong nao DUOC CHON.
Bat bien nay khong duoc BAO DAM bang cach kiem gia tri, ma bang cach lam cho
no khong the bi vi pham: `regime_shares()` KHONG nhan `w_loss` va KHONG nhan
`opt` lam tham so. Vi pham duoc chan o CHU KY HAM, khong o gia tri -- cung ky
thuat da dung o `G23-115` (chan `L36` o KIEU du lieu).

`P(viol | opt)` VAN duoc tinh va bao cao, de doi chieu `M-133`/`M-134`.

## 5. Phan loai che do -- NGUONG KHOA TRUOC KHI NHIN SO

```text
LIVE      := S_pivotal >= 0.10
TRIVIAL   := S_pivotal <  0.10  va  S_trivial >= S_collapsed
COLLAPSED := S_pivotal <  0.10  va  S_collapsed > S_trivial

PIVOTAL_MIN = 0.10
  "Duoi 10% thoi gian ma viec chon duong quyet dinh SLA -- mot cong cu ho tro
   quyet dinh khong dang chung nhan."

VIOL_OPT_BAND = [0.01, 0.50]   (thu cap)
  0.01: SLA gan nhu luon dat -> khong can ho tro
  0.50: mang dat SLA chua toi nua thoi gian -> su co ha tang
```

Phep thu cho mot tieu chi tien nghiem THAT: ca hai nguong tren viet duoc ma
KHONG can biet bat ky con so ket qua nao.

## 6. Du doan -- DIEN TRUOC KHI CHAY

Co so duy nhat duoc phep dung: `results/LIVE/phase-20R/sla_calibration.json`
(cong bo tu Phase 20R) va `axis_remeasure_impact_wave1.json :: M125b.counted_cells`
(cong bo o Lesson 23.20). KHONG chay `sla_exogenous.py` truoc khi dien xong.

Co so suy luan, doc tu artifact cu:

```text
cell             t_delay(ms)   t_loss     <- phan vi ~85 tren duong TOI UU
poisson@0.700       16.564    0.00042
poisson@0.850       24.244    0.00722
poisson@0.925       32.222    0.02921
poisson@0.960       36.559    0.04791
h2@0.700            28.614    0.02645
h2@0.850            40.214    0.11026
h2@0.925            45.159    0.16684
h2@0.960            47.227    0.19461
cbr@0.700/0.850     12.456    0.00000     (role pc1)

Nhan xet 1: MOI t_delay < 50 ms. Duoi S-B, rang buoc TRE gan nhu khong can.
Nhan xet 2: T_loss = 1% cat NGANG cot t_loss. Ba cell h2 tai cao co t_loss
            11..19%, tuc tren duong TOI UU mat goi da vuot 1% o phan lon thoi
            gian -> ung vien COLLAPSED.
Nhan xet 3: err_neo >= 0.05 (amendment 23-49b) dem 4 cell:
            h2@0.700, poisson@0.850, poisson@0.925, poisson@0.960.
```

| id | dai luong | loai | dai da ky | do duoc | KQ |
|---|---|---|---|---|---|
| M-133 | so cell COLLAPSED duoi S-B (tren 8 cell gate) | CO CHE | 3 (dai 2..4) | | |
| M-134 | h2@0.850 / 0.925 / 0.960 co COLLAPSED khong | CO CHE | CA BA deu COLLAPSED | | |
| M-135 | phan hoach S-B trung phan hoach err_neo>=0.05 | NGOAI SUY | >= 6/8 cell | | |
| M-136 | ket luan lift > swing bat bien qua sweep w_loss | CO CHE | BAT BIEN (giu dau o ca 3 w_loss) | | |
| M-137 | max \|delta S_pivotal\| khi w_loss 1250 -> 20000 | NGOAI SUY | = 0 (chinh xac) | | |
| M-138 | cost_margin_mean(COLLAPSED) / cost_margin_mean(LIVE) | CO CHE | <= 0.50 | | |
| M-139 | max \|S_pivotal(S-A) - S_pivotal(S-B)\| tren 8 cell | NGOAI SUY | <= 0.25 | | |

Ghi chu tung du doan:

```text
M-137  la HE QUA cua muc 4, khong phai mot do luong doc lap. Neu no khac 0
       thi lap luan "phan hoach doc lap ham muc tieu" SAI va phai rut. Day
       la ly do dai la "= 0 chinh xac" chu khong phai mot dai rong.

M-138  la phep kiem CO CHE cua M-135. Gia thuyet: err_neo ~ 0 o cac cell h2
       tai cao KHONG phai vi "bai toan de" ma vi "mang da sup" -- khi moi
       duong deu te nhu nhau, bien chi phi co lai nen chon sai ton rat it.
       Neu M-138 dung, hai phan hoach trung nhau vi CUNG MOT CO CHE, khong
       phai vi may man.

M-139  S-A va S-B chi khac o T_delay (150 vs 50 ms), cung T_loss = 1%. Vi moi
       t_delay do duoc deu < 50 ms, rang buoc TRE gan nhu khong can o ca hai
       -> hai phan hoach phai gan trung nhau. Dai 0.25 de rong vi h2 la
       hyperexponential, duoi phai co the day khoi 50 ms dang ke.
```

Ba du doan `M-133`, `M-134`, `M-138` la CO CHE: MISS cua chung la thong tin
ve mang, khong phai loi cua cong cu.

## 7. Gate

| id | noi dung | nguong |
|---|---|---|
| G23-153 | SLA co dinh co nguon NGOAI, ghi trong amendment nay | bat buoc |
| G23-154 | MOT `w_loss` = 5000 cho paper, khoa trong `CONSTANTS.md` (K06) | bat buoc |
| G23-155 | sweep {1250, 5000, 20000} bao cao DU, KE CA khi doi ket luan | bat buoc |
| G23-156 | ket luan lift > swing bat bien qua sweep | bao cao |
| G23-157 | phan hoach SLA vs phan hoach err_neo, bang 8 cell day du | bao cao |
| G23-158 | `L40` va `L41` dong; nhan `CONDITIONAL_ON_SLA_AXIS` go | bat buoc |
| G23-159 | DOI CHUNG AM: nap lai SLA + w_loss NOI SINH cu -> tai tao artifact cu | diff = 0 |
| G23-160 | `S_pivotal` BAT BIEN qua ca ba `w_loss` | \|diff\| = 0 |
| G23-161 | `role` GIU semantics cu; phan loai moi o truong `regime` | bat buoc |

`G23-158` KHONG dong `L44`/`L45`: `L44` la `S13` (rho doc lap theo link, sua o
23.25/23.26) va `L45` la xuat xu `beta`. Ca hai vua mo o amendment 23-51 va
nam ngoai tam voi cua 23.21.

## 8. KHONG nap nghia moi vao truong cu

`measurements/decision_error_v2.py:96` va `cert/eight_cell_sweep.py:83` deu loc
bang `role == "gate"`. Neu gan `role` theo phan loai moi thi moi cell bi phan
la COLLAPSED se MAT `role == "gate"`, va `eight_cell_sweep` nem `ValueError`
tai mot noi RAT XA cho sua.

```text
role    truong DUONG ONG : "script nao chay tren cell nao"  -> GIU Y NGUYEN
regime  truong KHOA HOC  : "cell nay co dang chung nhan khong" -> TRUONG MOI
```

Breaking change ngam la loai te nhat: khong loi luc bien dich, loi luc chay,
va loi o cho xa nhat so voi cho sua.

## 9. Truong hop THAT BAI da du lieu

```text
Neu duoi S-B co < 2 cell LIVE:
  -> KHONG noi rong VIOL_OPT_BAND va KHONG ha PIVOTAL_MIN.
  -> Bao cao NGUYEN, roi dung S-A lam CHINH va ghi ly do.
  -> Viec doi spec CHINH phai la mot amendment RIENG, ky SAU khi bao cao S-B.
```

## 10. Dang ky truc

```text
docs/phase-23/axis_registry.json
  sla_axis["results/PENDING/phase-23/sla_exogenous_S-B.json"]
      label  = "exogenous_itu_g114_50ms_1pct"
      status = "ACTIVE"
  sla_axis["results/LIVE/phase-20R/sla_calibration.json"].status
      -> giu DEPRECATED (KHONG xoa: doi chung am G23-159 can no chay mai)

  approved_for_live.sla_axis += ["exogenous_itu_g114_50ms_1pct"]
  approved_for_live.aoi_axis += ["measured_v7_uniform"]
```

Duyet CA HAI truc CUNG LUC: mot artifact hop le khi MOI truc hop le
(amendment 23-49c muc 3). Day la dieu kien go nhan `CONDITIONAL_ON_SLA_AXIS`.

Viec duyet truc la mot amendment RIENG, ky SAU khi da co ket qua S-B va da
doi chieu `M-133..M-139`. Ban nay chi KHOA du doan; no KHONG duyet truc nao.

## 11. Han che moi

```text
L46  `S_pivotal` do tren mo hinh rho DOC LAP theo link (`S13`, `L44`, chua
     sua). Tuong quan tai that se lam cac duong vi pham DONG THOI nhieu hon
     -> `S_pivotal` THAT nho hon so do duoc. Uoc luong hien tai la CAN TREN.
L47  Nguong ITU-T G.114 la ngan sach cho THOAI. Nhiem vu cua `topology_v7`
     khong duoc dac ta la thoai. Viec muon nguong nay la mot ANH XA hop ly,
     KHONG phai mot dac ta hop dong.
```

## 12. Dieu KHONG lam trong amendment nay

```text
- KHONG sua measurements/sla_calib_v2.py (ke ca LOSS_EXCHANGE va test ghim no)
- KHONG duyet truc nao vao approved_for_live  (muc 10)
- KHONG doi hang so SLA_ARTIFACT o eight_cell_sweep -- doi = mat G23-159 vinh vien
- KHONG sua truong `role`                     (muc 8)
- KHONG chay sla_exogenous.py truoc khi tag amendment-52
```

So ke tiep: `L48`, gate so 162, `M-140`, `K07`.

(Viet "gate so 162" chu khong viet ma day du co chu dich:
`test_every_gate_id_mentioned_in_repo_is_in_the_ledger` quet MOI ma dang
`G23-<so>` trong `docs/`, `cert/`, `test/`. Nhac mot ma CHUA co dong trong
`GATES.md` se lam test do -- va o day ta dang noi ve mot so CHUA duoc cap.)

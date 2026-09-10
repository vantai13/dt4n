# GLOSSARY -- so dang ky ESTIMAND cua DT4N

Sinh o Lesson T2.2. Ly do ton tai: trong Phase T2 da hai lan mot CAI TEN
che HAI DAI LUONG hop le khac nhau.

```text
F1  (T2.0)  tau_load = 1.0 s  vs  tau_core = 2.87 s
T2.2        sigma_z cua `u` (co dieu kien)  vs  `sat` cua rms (hieu)
```

Hai lan khong phai trung hop. Do la trieu chung: repo thieu mot noi khai
bao MOI DAI LUONG bang toan, doc lap voi code. File nay la noi do.

Luat dung: mot nghi van CHI tro thanh loi SAU KHI grep xac nhan khong co
muc nao o day (va khong co tai lieu nao khac) giai thich no.

Moi muc: ky hieu - cong thuc - vai tro - dinh nghia goc (file:dong).

---

## tau_load

```text
Ky hieu   tau, tau_rho
Gia tri   THAM SO THIET KE, do nguoi dat. Legacy = 1.0 s.
Cong thuc phi = exp(-dt/tau)  -- he so AR(1) mot buoc
Vai tro   thoi gian tuong quan cua qua trinh tai TONG HOP (AR(1) sinh ra)
Goc       measurements/sla_calib_v2.py  (ar1_matrix, TAU_LOAD_LEGACY_S)
Tai lieu  docs/phase-21R/00-preregistration.md:441  (R9)
```

KHONG duoc co mac dinh im lang. `DEFAULT_TAU = 1.0` cu da len vao bon phase
ma khong ai ky, va sinh ra F4: chien dich 20R quet tau nhung giu z/tau co
dinh, khien err(tau) "gan phang" la mot TAUTOLOGY chu khong phai ket qua.

## tau_core

```text
Ky hieu   TAU_CORE_MEASURED_S
Gia tri   2.87 s -- DO DUOC, khong phai dat
Cong thuc uoc luong tu trace v7 that (tai loi Mininet)
DIA CHI   = tau do duoc cua link `ac` tren trace v7: 2.869 s
          docs/phase-20/00f-amendment-5.md muc A5.1 (bang tam link)
          Bay link con lai KHONG bang no, va trai rat rong:
              bc 2.441 | bd 2.605 | ac 2.869 | ad 3.958
              vC 17.38 | uB 21.70 | uA 22.87 | vD 32.00     (giay)
          => mot sigma_z dung CHUNG 2.87 cho ca TAM link la mot XAP XI,
             lech manh nhat o vD (32.00, gap 11 lan). Day KHONG pha bao
             dam bao phu (Mondrian hop le voi moi taxonomy co dinh truoc)
             nhung no lam bin KEM HIEU QUA -- va do chinh la ly do ton tai
             cua nhanh nhay cam `u_cond` (prereg T2 muc QD-1).
             Phai viet vao Threats to Validity, khong duoc "dong bo" thanh
             tau rieng tung link: doi dinh nghia u sau khi nhin du lieu la
             pha dieu kien "taxonomy co dinh TRUOC hieu chuan".
Vai tro   chuan hoa bien dieu kien u; B_BLOCK_S = 5*tau_core = 14.35 s
Goc       cert/build_calib_set.py:46          TAU_CORE_MEASURED_S
          measurements/decision_error.py:40    DEFAULT_TAU_CORE_S   <- CUNG MOT
                                               dai luong, ten khac, file khac
Tai lieu  docs/phase-21/99-erratum.md:76-80  (E4)
```

CANH BAO: 2.87 dang mang HAI TEN o hai file (lan thu BA trong phase nay mot
dai luong co nhieu ten). Chung KHONG mau thuan -- deu la thoi gian tuong quan
DO DUOC cua tai loi. Truoc khi "dong bo" hay "sua" mot trong hai, doc muc nay.
`DEFAULT_TAU_CORE_S` co mac dinh la HOP LE vi no la mot hang so DO DUOC (mac
dinh chinh la gia tri do duoc); khac han `tau_load` von la mot TRUC quet.

Khac `tau_load` ve BAN CHAT: mot cai do duoc tren tai that, mot cai dat ra
cho qua trinh tong hop. Khong phai mau thuan, khong duoc "dong bo" chung.

## sigma_z  (bien DIEU KIEN, truc u)

```text
Cong thuc sigma_z = sigma * sqrt(1 - exp(-2z/tau))
Hoi       "rho(t) co VUOT NGUONG khong, BIET rho(t-z)?"
Estimand  do lech chuan CO DIEU KIEN cua rho(t) | rho(t-z)
          Var[rho(t) | rho(t-z)] = sigma^2 (1 - phi_z^2),  phi_z = exp(-z/tau)
Vai tro   chia bin Mondrian: u = |rho_hat - nguong| / sigma_z
Goc       cert/build_calib_set.py:179
Tai lieu  docs/phase-21/00-preregistration.md:199-201  (P4b, TIEN DANG KY)
```

CANH BAO da biet: tu so dung `rho_hat = rho(t-z)` nhung mau so la do lech
CO DIEU KIEN -- tuc bo qua phan hoi quy ve trung binh `(1-phi_z)*|rho_hat-mu|`.
Sai sot ~5% o z/tau=0.05, ~63% o z/tau=1.0.
Day KHONG lam mat tinh hop le cua Mondrian conformal (bao phu van duoc bao
dam voi moi ham chia bin do duoc, mien la chon TRUOC khi nhin diem hieu
chuan); no chi lam bin KEM HIEU QUA. La van de SUC MANH, khong phai DUNG SAI.

## sat  (hoi quy SAI SO, luat rms)

```text
Cong thuc sat = sqrt(1 - exp(-z/tau))          -- KHONG co he so 2
          rms_pred = sqrt(em^2 + c*A^2*(1 - exp(-z/tau)))
Hoi       "twin sai bao nhieu khi giu nguyen gia tri cu?"
Estimand  phuong sai cua HIEU rho(t) - rho(t-z)
          Var[rho(t) - rho(t-z)] = 2 sigma^2 (1 - phi_z),  bien do A tu do
Vai tro   fit luat AR(1) cho rms_e_stale; sinh ratio(tau)
Goc       cert/tau_sweep.py:203,218
Khop voi  measurements/decision_error_v2.py CHI VE DANG HAM (ca hai la HIEU).
          KHONG TUONG THICH VE ESTIMAND -- xem muc "SO DANG KY ESTIMAND"
          va "DINH CHINH MUC `sat`" o cuoi file (A-T2-3).
```

## Quan he giua hai cong thuc tren -- doc ky truoc khi thiet ke T2.6

```text
sigma_z (co dieu kien) va sat (hieu) LECH NHAU HE SO 2 trong so mu:
      convA(tau) == convB(tau/2)   (kiem bang so, tools/t2_0_tau_audit.py)
```

Ca hai deu DUNG cho vai tro cua minh. Nhung truc tau cua hai kenh KHONG so
sanh truc tiep duoc. T2.6 phai ghi ro moi hinh dung estimand nao, neu khong
doi chung noi tai (tau=1.0, z=0.10) se lech co he thong.

## Cac dai luong khac can nho

```text
z          tuoi telemetry (giay). Trong van hanh that do SYNC PERIOD quyet
           dinh (DEFAULT_SYNC_PERIOD_S = 0.5 s, measurements/decision_error.py:37),
           KHONG co gian theo tau. Day la nhanh B.
z/tau      ti so chuan hoa. Giu no co dinh lam sigma_z BAT BIEN theo dinh
           nghia -- nguon goc cua tautology F4. Day la nhanh A.
block_s    kich thuoc block conformal = 5*tau, KHONG phai 5 giay.
           measurements/decision_error_v2.py:block_s_for_tau
MIN_BLOCKS ceil(1/alpha) - 1 = 9 voi alpha = 0.10. Ap cho MOI SEED.
tau_hat    uoc luong cua tau tu chuoi. CHI phuc vu gate V-T2-2. Do chech cua
           no theo T_sim/tau (so chu ky doc lap), KHONG theo tau. Nen so voi
           KY VONG HUU HAN MAU, khong voi gia tri thiet ke (nguyen tac T-G2).

---

## SO DANG KY ESTIMAND -- BAT BUOC (A-T2-3)

LUAT: moi artifact ghi mot dai luong o day PHAI mang truong `estimand_id`.
Mot artifact khong co `estimand_id` KHONG duoc dung de phan quyet bat ky du
doan da ky nao. Test canh: test/test_t2_estimand_registry.py

LY DO TON TAI CUA MUC NAY: hai dai luong khac han da cung mang ten cot
`rms_e_model` va da lam T2.6 luot 2 do sai dai luong so voi du doan da ky.
Dang ky theo DANG HAM la KHONG DU. Phai dang ky theo MUC va THANG.

```text
--------------------------------------------------------------------------
ID              RMS_MARGIN_COST
LEVEL           margin
POPULATION      chenh lech CHI PHI giua HAI hanh dong: hang nhat va hang nhi
                theo xep hang cua twin CU (stale). m = y[a2] - y[a1].
SCALE           cost_ms   -- chi phi = delay + w_loss * loss
UNIT            ms
BRANCH          z_fixed  -- z = sawtooth_age_steps(n, dt, SYNC_PERIOD=0.5,
                d_sync), goi trong cert/build_calib_set_v3.py:289 (_valid_rows).
                GIA TRI z do SYNC_PERIOD va d_sync quyet dinh, DOC LAP voi tau.
                n chi quyet dinh SO CHU KY, khong quyet dinh gia tri z.
                =>  NHANH B
CODE            cert/tau_sweep.py : build_at_tau -> decompose -> fit_ar1
ARTIFACT_FIELD  rows[].ar1_fit.rms_e_model ; rows[].ar1_fit.A ; .c
                rows[].scale = "cost_ms" ; rows[].level = "margin"
DUNG CHO        moi du doan cua docs/phase-T2/01-prediction-signed.json
                (D-T2.6-1, -2, -3, -4, -6, -7) va moi ti so
                R(tau) = q_hat[bin3] / q_hat[bin0]
GIA TRI MOC     rms_e_model = 2.1400 ms
                poisson@0.925, tau = 0.5, seed 101..105, sigma = 0.0096
                nguon: results/SUPERSEDED/phase-22/tau_sweep_poisson_0.925.json
                       rows[0].ar1_fit.rms_e_model = 2.1400081935285336
--------------------------------------------------------------------------
ID              RMS_ALLACTION_DELAY
LEVEL           all_action
POPULATION      MOI phan tu cua ma tran (n_hang, 4 duong). KHONG chon cap,
                KHONG xep hang.
SCALE           delay_ms  -- do tre THUAN; w_loss KHONG cham toi duoc
UNIT            ms
BRANCH          z_fixed HOAC z_scaled, theo co --z-mode
CODE            measurements/decision_error_v2.py : run_cell
ARTIFACT_FIELD  cot parquet rms_e_model / rms_e_stale / cov_e
DUNG CHO        err_total, d_sla va cac cau hoi decision-error cua 20R2.
                KHONG dung de phan quyet du doan T2-5.
GIA TRI MOC     rms_e_model = 0.3405 ms
                poisson@0.925, tau = 0.5, seed 101..105, nhanh fixed,
                a = 0.9 => sigma = 0.021802   (tung seed: 0.3394 .. 0.3426)
                va 0.3129 ms khi a = 0.5 => sigma = 0.012112
                nguon: results/PENDING/phase-T2/sweep_r2/*.parquet
                       (chi so lenh trong sweep_r2/run_log.jsonl)
--------------------------------------------------------------------------
ID              DECISION_ERR_BY_AGE
LEVEL           all_action
POPULATION      8 o `gate` cua luoi 20R2: c_a thuoc {poisson, h2} x rho_bar
                thuoc {0.700, 0.850, 0.925, 0.960}. Luoi KET QUA =
                8 o x 8 tau x 2 sigma x 5 seed = 640 o.
                Nguon phan hoach: results/LIVE/phase-20R/sla_calibration.json
                summary.n_gate_cells = 8 (KHONG suy tu `role`, artifact da
                phan hoach san).
                2 o `cbr` kha thi (rho_bar 0.700, 0.850) = DOI CHUNG DUONG,
                bao cao RIENG, KHONG gop vao bat ky trung binh nao. 2 o cbr
                con lai bi loai boi q8 (sigma_max_regime = 0).
                => Gop cbr vao trung binh la NGUY BIEN GOP: cbr la che do de
                   nhat, no KEO err trung binh XUONG.
SCALE           ti le (khong thu nguyen), trong [0, 1]
                /!\ KHONG phai delay_ms. `err` la TI LE hang sai, khong phai
                    mot do tre. KHONG duoc dat cung nguong voi d_sla.
UNIT            dimensionless
BRANCH          z_fixed -- lag TAT DINH k = round(z/dt),
                measurements/decision_error_v2.py:465. run_cell KHONG goi bo
                sinh AoI nao (T2-L8 dung ve tinh than, dinh chinh ve co che).
                Truc AoI vao qua VIEC CHON z, khong qua bo sinh.
CODE            measurements/decision_error_v2.py : run_cell
ARTIFACT_FIELD  per_z[<z_key>].err_total                        (dong 482)
                kem .err_model (483) va .err_stale (484) de phan ra
                kem .extrapolated (489) -- CO NGHIA "z ngoai mien tuoi that
                    [0.115, 0.615] cua truc measured", KHONG co nghia "sai".
DUNG CHO        RQ-20R2a, RQ-20R2c, RQ-20R2d
GIA TRI MOC     <dien SAU pilot 3 o cua 20R2.4, TRUOC chien dich>
--------------------------------------------------------------------------
ID              SLA_VIOL_BY_AGE
LEVEL           all_action
POPULATION      GIONG DECISION_ERR_BY_AGE (co chu dich: hai estimand phai noi
                ve cung mot quan the thi moi doc chung duoc trong mot ket luan)
SCALE           cost_ms -- DI QUA ham chi phi (delay + w_loss * loss), nen
                NHAY voi w_loss va voi truc SLA.
                /!\ Day la khac biet CHINH voi DECISION_ERR_BY_AGE:
                    err la TI LE, d_sla la CHI PHI. Khac ca THANG va DON VI.
                    Bang chung do duoc: G23-203 cho max|diff| = 0.0 tren
                    rms_e_*/cov_e (thang delay_ms) khi doi truc SLA, con
                    err_total/d_sla (di qua argmin bang chi phi) thi KHONG.
UNIT            ms
BRANCH          z_fixed
CODE            measurements/decision_error_v2.py : run_cell
ARTIFACT_FIELD  per_z[<z_key>].d_sla                            (dong 485)
DUNG CHO        RQ-20R2b
GIA TRI MOC     <dien sau pilot>
--------------------------------------------------------------------------
```

### VI SAO 20R2 KHONG TAI DUNG `RMS_ALLACTION_DELAY`

```text
RMS_ALLACTION_DELAY  DUNG  LEVEL          (all_action -- cung muc)
                     SAI   SCALE          (delay_ms  vs  ti le khong thu nguyen)
                     SAI   ARTIFACT_FIELD (rms_e_model  vs  err_total)

Hai truong sai la du. Tai dung no la lap lai DUNG loi A-T2-3: mot ten phu
len hai dai luong. Lan truoc cai gia la T2.6 luot 2 do sai dai luong so voi
du doan da ky.
```

/!\ CANH BAO CO CHE -- `estimand_id` STAMP O MUC ARTIFACT, KHONG O MUC TRUONG:

```text
measurements/decision_error_v2.py:48   ESTIMAND_ID = "RMS_ALLACTION_DELAY"
                              :453     "estimand_id": ESTIMAND_ID   <- dong vao artifact
                              :1028    "estimand_id": ESTIMAND_ID   <- va vao validity

Nghia la MOT artifact cua run_cell se mang MOT nhan, trong khi per_z[] cua no
chua BA estimand khac nhau:
    rms_e_model / rms_e_stale / cov_e  -> RMS_ALLACTION_DELAY  (delay_ms)
    err_total / err_model / err_stale  -> DECISION_ERR_BY_AGE  (ti le)
    d_sla                              -> SLA_VIOL_BY_AGE      (cost_ms)

Nhan o muc artifact KHONG DU DO PHAN GIAI de phan biet ba cai do. Vi vay
`ESTIMAND_BY_FIELD` duoc them vao module: no khai theo TRUONG, va no la thu
phai duoc trich dan khi phan quyet mot du doan 20R2.
Test canh: test/test_20r2_2_prediction.py, test/test_t2_estimand_registry.py
```

### HAI ID TREN KHONG SO SANH DUOC -- va day la BANG CHUNG SO

```text
    2.1400 ms   RMS_MARGIN_COST      sigma = 0.0096
    0.3405 ms   RMS_ALLACTION_DELAY  sigma = 0.021802
    CUNG o poisson@0.925, CUNG tau = 0.5, CUNG seed 101..105.

Doc theo HUONG, khong chi theo do lon: cai do sau chay voi sigma LON HON
2.27 lan ma cho so NHO HON 6.29 lan. Voi CUNG mot estimand, RMS phai TANG
theo sigma. Huong nguoc nhau la bang chung manh hon mot ti so don thuan.
```

```text
PHAN RA CO CHE -- do voi CUNG mot sigma de loai bien sigma
(poisson@0.925, tau=0.5, seed=101, sigma=0.0096, CUNG hang, CUNG z, cung mot
 xep hang theo twin CU tren thang chi phi):

    LEVEL=all_action  SCALE=delay  ->  0.3061 ms
    LEVEL=margin      SCALE=delay  ->  0.1316 ms      doi MUC
    LEVEL=margin      SCALE=cost   ->  2.1106 ms      doi THANG
                                       (~2.1400 tren 5 seed cua artifact)

    doi MUC   all_action -> margin :  x0.4298   GIAM 2.33 lan
    doi THANG delay      -> cost   :  x16.0422  TANG 16 lan
    tich                           :  x6.8947

CO CHE cua tung thua so:
  MUC   margin la HIEU cua hai duong. Sai so mo hinh co phan CHUNG giua cac
        duong (cung truth table, cung twin fit) nen phan chung TRIET TIEU khi
        lay hieu -- common-mode rejection.
  THANG cost = delay + w_loss * loss, va w_loss = 3222.244682 o o nay. Mot sai
        so loss co 1e-3 thanh sai so cost co 3.2 ms. Thang cost KHUECH DAI sai
        so loss hon ba nghin lan.

=> HAI TRUONG cua so dang ky, moi truong mot dong gop DO DUOC, hai huong NGUOC
   nhau, tich khop dung ti so quan sat. Day khong con la "hai so khac nhau";
   day la "hai so khac nhau VI dung hai truong ta vua dang ky".
   Tai lap: docs/phase-T2/00-preregistration.md muc A-T2-3, tieu muc
   "TAI LAP PHAN RA CO CHE".
```

Dang thuc `sqrt(rms_e_model^2 + 2*cov_e + rms_e_stale^2) = rms_total` DUNG
cho CA HAI harness, sai lech lon nhat 7.105e-15 (do chinh xac may) tren 100
hang tai tao cua 22.6. No la `Var(X+Y) = VarX + 2Cov + VarY`, mot dong nhat
thuc DAI SO -- no dung du hai ve dang do hai dai luong khac nhau.

```text
>>> MOT CONG THUC DUNG KHONG LAM HAI DAI LUONG BANG NHAU. <<<
```

CANH BAO VE MOT CON SO HAY BI DAN NHAM: `8.235915145897662` trong
results/PENDING/phase-T2/rms_reference_check_r2.json muc "example" la
`rms_total` CUA CHINH 22.6 tai z = 0.055, tau = 0.5 -- ve trai cua phep kiem
dong nhat thuc tren. No KHONG phai mot so do cua T2.6 va KHONG phai
RMS_ALLACTION_DELAY. Dung no lam bang chung "hai estimand lech nhau" la so
sanh rms_e_model voi rms_total, tuc mot loi cung ho voi loi dang duoc sua.

Bang chung: results/PENDING/phase-T2/rms_reference_check_r2.json
            cross_phase_estimand_verdict = "INCOMPATIBLE"

### DINH CHINH MUC `sat` (A-T2-3)

Dong cu trong muc `sat`:

```text
Khop voi  measurements/decision_error_v2.py:402
          e_stale = d_fresh[t] - d_fresh[t-z]   <- dung la HIEU
```

DONG NAY DA GAY MOT LOI THAT. Doc dung phai la:

```text
KHOP VE DANG HAM   ca hai deu la HIEU, ca hai theo luat sqrt(1 - exp(-z/tau)).
                   Dieu nay DUNG.
KHONG TUONG THICH VE ESTIMAND
                   cert/tau_sweep.py       -> RMS_MARGIN_COST
                   decision_error_v2.py    -> RMS_ALLACTION_DELAY
                   Xem SO DANG KY ESTIMAND o tren.
=> KHONG duoc suy tu "cung dang ham" ra "so sanh duoc".
   Dang ham la DIEU KIEN CAN, khong phai DIEU KIEN DU.
```

Ghi them: so dong ":402" cung DA TROI. Trong ban hien tai dong 402 nam trong
CHU KY cua `run_cell`; `e_stale` o dong 466 (run_cell) va 681 (fixed_summary).
Vi vay so dang ky nay neo bang ARTIFACT_FIELD va CODE theo TEN HAM, khong
theo so dong.

### QUY TAC BO SUNG MOT ID MOI

Truoc khi them mot dai luong vao mot artifact, tra loi DU 7 truong. Neu mot
truong khong tra loi duoc thi dai luong do CHUA DUOC DINH NGHIA XONG va
khong duoc do. Day la NT 65 (dat ten estimand truoc khi do) mo rong: dat DU
BAY TRUONG truoc khi do.

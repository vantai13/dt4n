# HOP DONG BAN GIAO T2 -> 21R2

Ngay: 2026-09-09. Nguon: A-T2-3 + ERRATUM A-T2-3.1/.2/.3,
`results/PENDING/phase-T2/sweep_r3/adjudication_r3.json`.

Nguyen tac: cai gi DUNG DUOC thi giao kem duong dan va test canh; cai gi
KHONG dung duoc thi khai thang kem ly do va thiet ke de sua. Mot ban giao
chi liet ke cai dung duoc la mot ban giao noi doi mot nua.

---

## GIAO DUOC -- dung ngay, khong hieu chuan lai

```text
H1  measurements/sla_calib_v2.py
    tau la THAM SO BAT BUOC cua ar1_matrix (khong con mac dinh im lang);
    n = n_for_tau(tau, dt) bao dam T_sim >= 50*tau;
    dem kep qua return_diagnostics (co OPT-IN, giu bit-exact NC-T2-1).

H2  cert/realizability_gate.py -- 9 tieu chi. MOI o phai qua truoc khi chay.
    PHAI truyen du sigma, clip_fraction, min_cell_blocks. Neu thieu, tieu chi
    ghi "not_evaluated" va KHONG duoc coi la PASS.
    !! GIOI HAN: gate KHONG chan tren theo sigma -- tieu chi sigma_feasible
       chi kiem sigma > 0 (do duoc: sigma = 99.0 van REALIZABLE). Tran sigma
       den tu twin/cost_v2.sigma_max_regime va phai ap RIENG.

H3  cert/tau_sweep.py
    truc sigma tuong minh: sigma= XOR a=, KHONG co mac dinh im lang;
    n theo tau (n_mode = per_tau | fixed);
    khop muc (--level-matched-blocks) de khu confound level(tau);
    moi hang mang estimand_id / scale / level / branch /
    conformal_level_used / n_calib_blocks / realizability.

H4  docs/GLOSSARY.md muc "SO DANG KY ESTIMAND" -- 7 truong bat buoc
    (LEVEL POPULATION SCALE UNIT BRANCH CODE ARTIFACT_FIELD).
    LUAT: artifact khong co estimand_id KHONG duoc dung de phan quyet mot du
    doan da ky. Test canh: test/test_t2_estimand_registry.py (17 test).

H5  TAU_GRID RIENG cho tung dt -- khong duoc tron:
        twin    dt = 0.005  ->  tau in {0.5, 1, 2, 3, 5, 10, 20, 28}
        testbed dt = 0.1    ->  tau in {2, 5, 30}   (Phase G DA DO)
    Paper GHI RO: "tau < 2 s chi khao sat trong twin."
    Bang chung testbed: docs/phase-G/66-g3b-results.md (|sai so| round-trip
    lon nhat 4.94% cho tau, 3.82% cho sigma, moi o la trung vi qua link/luot),
    T_run = 205*tau (docs/phase-G/77-g-closeout.md:213).

H6  Hop dong ba kenh tau: CUNG mot tau phai vao (a) bo sinh, (b) sigma_z
    Mondrian, (c) block b = 5*tau. Kiem bang assert tren artifact, khong bang
    quy uoc dat ten.

H7  Ket qua do vong 3: results/PENDING/phase-T2/sweep_r3/
        t2_6b_r0..17.json      18 lenh, 9 o x 2 muc a, 8 tau, 5 seed
        legacy_*.json          arm doi chung 22.6 (D-T2.6-9: 2.665e-12)
        sigmaprobe_*.json      arm chan doan sigma, HAU NGHIEM
        hygiene_r3.json        ba kiem co hoc
        level_probe_posthoc.json
        adjudication_r3.json
    Ba hinh: docs/phase-T2/figures/T2-{1,2,3}-*.png (sinh boi
    tools/t2_6b_figures.py; bien cua T2-3 doc TU realizability_gate).
```

---

## KHONG GIAO DUOC -- no khoa hoc, khai thang

```text
N1  *** err(tau), lift(tau), tau* ***
    THIEU: err_certified -- chua ai cai. Do duoc bang grep: `lift`,
    `err_certified`, `err_baseline` khong ton tai o ca hai harness, va
    `err_certified` khong ton tai trong bat ky tep .py nao cua repo.
    CAN: ap q_hat len tung quyet dinh, do sai so TREN TAP DUOC CHAP NHAN, so
    voi baseline khong gate.
    THIET KE DE XUAT (phai TIEN DANG KY o 21R2, KHONG ke thua tu day):
      . mot harness DUY NHAT phat ca q_hat lan err tren CUNG mot estimand
      . khai estimand_id cua err_certified TRUOC khi cai
      . lift_min la mot DUONG {0.05, 0.10, 0.20} (QD-2 giu nguyen)
      . du doan err(tau) ky truoc tu Sheppard: err = arccos(exp(-z/tau))/pi
    CAM: suy tau* tu R(tau). R la ti so BAN KINH KHOANG, lift la ti so SAI SO
    QUYET DINH. Quy doi giua chung dung loai loi ma A-T2-3 vua sua.

N2  Vi tri dinh R(tau) chi phan giai toi KHOANG BOC (1, 3) s.
    Muon min hon: TIEN DANG KY mot luoi co diem trong (1,3) o 21R2.
    KHONG duoc coi day la "mo rong luoi cua T2" -- T2-6(c) cam.

N3  *** Luat rms AR(1) KHONG hop le o poisson@0.850 tren truc sigma moi ***
    gate ar1_rms_total_fit_within_2pct do duoc:
        sigma = 0.0096            -> true   (ca 4 o)
        a = 0.5 (sigma = 0.0266)  -> false  (poisson@0.850)
        a = 0.9 (sigma = 0.0480)  -> false  (poisson@0.850)
    Tinh HOP LE cua chinh cai luat phu thuoc sigma. O nay bi bo khoi
    D-T2.6-1/-2/-6 o vong 3. 22.6 cung da co 3/9 FAIL cua D-T2.6-4 tap trung
    o `em` cua chinh o nay. BA duong doc lap cham cung mot cho => day la mot
    BAT THUONG DA BIET, can mot lesson rieng, khong phai mot diem du lieu.

N4  D-T2.6-4 FAIL 11/18 (22.6 da FAIL 3/9), chu yeu o `em`.
    Gia dinh "A, c, em doc lap voi tau" -- NEN CUA luat rms -- KHONG vung
    tren luoi tau rong hon va tren truc sigma moi.
    21R2 PHAI kiem lai gia dinh nay TRUOC khi dung luat, khong duoc ke thua.

N5  No DOI/K10 van BLOCKED (doc77 muc 6, D6). T2 khong mo khoa duoc.

N6  Artifact vong 3 KHONG mang khoi `validity`, nen truot
    test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for.
    30 tep duoc ghi vao PENDING_NO_VALIDITY_GRANDFATHERED kem ly do, KHONG
    duoc lang le bo qua. Hai duong sua deu bi chan, ca hai vi mot ly do DUNG:
      (1) sinh lai kem validity  -> PHA DAU VET: sweep_r3/run_log.jsonl ghi
          sha256 tung artifact va adjudication_r3.json da phan quyet tren
          chinh chung. Sinh lai la ghi de bang chung SAU khi da doc ket qua.
      (2) them `pending_on` vao ma nguon -> doi hoi khai CHINH XAC truc nao
          chua duyet. Artifact nay chay tren truc conformal/tau, khong phai
          aoi_axis hay sla_axis cua docs/phase-23/axis_registry.json. Doan
          mot nhan truc chi de qua mot test la DUNG loai loi A-T2-3 vua sua.
    21R2 PHAI: quyet dinh truc `pending_on` dung cho artifact chung nhan, roi
    cho cert/tau_sweep.py ghi validity NGAY TU LUC SINH. Khi do xoa 30 muc
    grandfather -- danh sach do chi duoc NGAN DI.
```

---

## CANH BAO CHO 21R2

```text
W1  sigma_total^2 = sigma_schedule^2 + bias_model^2 + err_tau^2
    KHONG dat err_tau bang bat ky dai luong nao cua T2 cho toi khi err_tau
    duoc khai estimand_id va khop MUC/THANG voi hai so hang kia. Day chinh
    la cho loi estimand se tai phat neu khong canh.

W2  Phan ra CO so hang tuong tac; bao cao PHAN DU (S27).
    KHONG dat gate "cong lai khop +/- 5%": no la tautology hoac tuning
    (bai hoc L2 muc 2).

W3  Tieu chi cong suat dang TI SO (bien do / nhieu) khong co khai niem
    "qua nho de quan tam". Tren o suy bien tu va mau cung co lai nen ti so
    van co the qua nguong. Luon di kem mot SAN TUYET DOI (o T2 la
    A < 0.01 cua QD-7).

W4  Hang so phan quyet: MOT nguon, IMPORT, khong chep.
    Bon loi trong bon luot cua T2 deu tu mot co che: chep lai mot con so
    thay vi doc lai no tu nguon. Vi du: hai bo nguong 10/3 va 5/2 cho DUNG
    NHAN tren du lieu cu -- nhan trung nhau KHONG chung minh nguong trung
    nhau. Chi khi ep tai tao mot CON SO (n_fail = 3) sai lech moi lo.
```

---

## KET QUA CUA PHASE, VIET THANG

```text
G-T2-8 ">= 5/7 du doan dinh tinh dung": KHONG DAT. 3 PASS / 7.
  PASS       D-T2.6-1  don dieu giam, 16/16
             D-T2.6-5  giao hai nhanh (estimand KHAC, ghi ro)
             D-T2.6-7  cbr chet, max|R-1| = 0.0161
  FAIL       D-T2.6-2  6 trong / 10 ngoai -- lan voi sai khac sigma (T-3)
             D-T2.6-4  7 pass / 11 fail -- 22.6 da co 3/9 fail (N4)
  DOC RIENG  D-T2.6-3  buou 7/8 arm, dinh trong khoang boc (1,3) s
             D-T2.6-6  knee ngoai luoi o moi o/z -- DUNG nhu da bao truoc
  tau_star   NOT_MEASURABLE_BY_THIS_INSTRUMENT

Mau so 7 khai TRUOC khi doc. Khong doi mau so, khong doi nguong.

Ket qua co gia tri nhat cua phase nay KHONG phai mot cong dat. Do la: luat
RMS AR(1) -- nen cua toan bo du doan theo tuoi -- khong giu duoc tinh doc lap
voi tau tren dai tau kha thi, va tinh hop le cua chinh no phu thuoc sigma.
Dieu do chi lo ra khi tau tro thanh mot TRUC that thay vi mot hang so mac dinh.
Bon trong bay du doan hoac FAIL hoac chi doc duoc co dieu kien. Voi mot du doan
KY TRUOC, do la thong tin; voi mot du doan ky sau, do se la khong co gi.
```

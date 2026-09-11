# 20R2 → 21R2 — Bàn giao

Đọc cùng `99-gate-decision.md`. Mọi con số ở đây có nguồn; không con số nào được
gõ tay.

---

## 1. Được phép trích dẫn gì

```text
DUOC TRICH (khang dinh)
  phan quyet PRIMARY 5/8 tren 8 o gate DA KY          06-adjudication.{json,md}
  SHAPE PASS 6/7 don dieu giam, 1 cap UNREADABLE      06-adjudication.json
  G4 holdout a=0.5 PASS 7/8 (5/6 o rui ro that)       06c-g4-score.json
  d_sla: S0/S1/S2 PASS                                07-dsla.json
  em do tren dieu kien 20R2, 20 hang, estimand
    RMS_ALLACTION_DELAY                               08-handoff-measurements.json

DUOC TRICH (mo ta / tham do -- PHAI dan nhan)
  bang theo TUNG O, ti so 0,006-1,655                 06b-per-cell.json
  do nhay quan the theo T2-R7                         06b-per-cell.json
  co che "so duong canh tranh", Delta_cond theo tau   06b, 06c, 07-dsla
  phan lop cau truc d_sla (13/16 = 0 theo cau truc)   07a-dsla-structure.json

KHONG DUOC TRICH
  bat ky so nao cua 2 o rho_bar = 0.96 lam HEADLINE   T2-R7 (§18.2)
  so gop 8 o cua d_sla nhu "gia cua sai"              bi so 0 CAU TRUC chi phoi
  bang em/A cua §13.5 nhu do tren 20R2                KE THUA tu T2, KHAC estimand
  a = 0.5 nhu phan quyet                              bang chua kiem o a=0.5 (D6)
```

---

## 2. ★ Bẫy estimand phải đọc trước khi dùng bảng `em/A`

Có **hai** đại lượng **khác nhau** cùng tên cột `rms_e_model`:

```text
decision_error_v2.rms_e_model  = RMS_ALLACTION_DELAY   (all_action, delay_ms)
cert/tau_sweep.py  rms_e_model = margin, cost_ms       (DI QUA w_loss)
```

`decision_error_v2.py:56-58` ghi rằng hai cái này **từng bị đọc lẫn nhau** và làm
**T2.6 lượt 2 đo SAI đại lượng** so với dự đoán đã ký (A-T2-3).

Bảng `em/A` ở prereg §13.5 **kế thừa** số của T2, nguồn là
`results/PENDING/phase-T2/sweep_r3` = **`cert.tau_sweep`**, tức estimand
**margin/cost_ms**. Chiến dịch 20R2 dùng `decision_error_v2`, tức
**`RMS_ALLACTION_DELAY`**.

⚠️ **Khi đóng phase này tôi đã suýt lặp lại đúng lỗi đó:** tôi tính `em` từ dữ liệu
chiến dịch, so với `em_bar` của T2, thấy lệch tới **−99%**, và gần như báo đó là
một phát hiện. Nó **không phải phát hiện** — nó là **lỗi phạm trù**. Chặn cơ học:
`test/test_20r2_8_handoff.py`.

⇒ **D4 và D5 KHÔNG đóng được bằng dữ liệu chiến dịch.** Chúng chỉ đóng được bằng
`cert.tau_sweep` chạy trên điều kiện 20R2.

---

## 3. Định danh được / không định danh được

```text
luat rms (cert/tau_sweep.py:268):
    rms_total(z) = sqrt( em^2 + c * A^2 * (1 - exp(-z/tau)) )

em   DINH DANH DUOC TRUC TIEP. rms_e_model KHONG phu thuoc z -- DO DUOC o ca 13
     diem z, 20/20 hang co spread = 0 tuyet doi. Day la mot DOI CHUNG cho luat
     rms, khong phai gia dinh.
A    KHONG dinh danh duoc. Luat chi cho TICH c*A^2 nhu MOT tham so, nen khong
     tach A khoi c. => em/A va span_ratio_to_pure KHONG tinh duoc tu parquet
     chien dich, va tool ban giao KHONG bia ra chung (co test chan).
```

`em` đo trên điều kiện 20R2 — **20 hàng, gồm cả `cbr@0.850`** mà T2 thiếu:
`docs/phase-20R2/08-handoff-measurements.json`.

---

## 4. Sổ nợ — trạng thái đúng khi đóng phase

```text
DA DONG
  20R2-D1  se_pilot_rel  -> bang do lai tren truc exogenous (§16.3)
  20R2-D3  luoi z vao ma -> §14.6
  20R2-D7  parquet pilot vao git -> §15.7
  20R2-D8  NEO B mot tau -> hygiene H6: 80 cap x 10 o, 0 lech (mien phi nho CRN)

CON MO -- ban giao 21R2
  20R2-D2  QUA HAN. GIA TRI MOC cua hai estimand van null. Han la "dien SAU pilot,
           TRUOC chien dich"; chien dich da chay xong. Khai o §17-D2. Neu can gia
           tri moc thi lay tu pilot va DAN NHAN DIEN MUON.
  20R2-D4  N3/N4 phan 20R2 chua do. CAN `cert.tau_sweep` tren dieu kien 20R2
           (~53 phut). KHONG the thay bang du lieu chien dich -- xem muc 2.
           Can du doan KY TRUOC cho N3/N4 -> do la mot gate rieng, thuoc 21R2.
  20R2-D5  cbr@0.850 chua co em/A. Gio DA CO `em` tren dieu kien 20R2 nhung o
           estimand RMS_ALLACTION_DELAY, KHONG phai estimand cua bang em/A.
           D5 nhu DA PHAT BIEU van MO. (Co test chan viec go nham thanh "da dong".)
  20R2-D6  bang CHUA kiem o a = 0.5. Moi so a=0.5 chi MO TA.
  20R2-D9  MOI: G4 sai HE THONG o poisson@0.700 -- du doan QUA CAO ca hai dieu
           kien (-38,8% o a=0.9, -28,5% o a=0.5), CUNG CHIEU. Chua giai thich.
           KHONG va mo hinh sau khi da thay du lieu.
  20R2-D10 MOI: 2/8 o cua phep thu G4 gan nhu KHONG THE TRUOT vi san tuyet doi
           0,02 (h2@0.925 tol/G4 = 91%; h2@0.960 moi gia tri trong [0;0,02] deu
           qua). "7/8" thuc chat la 5/6 o rui ro that. Can mot thong ke khac cho
           vung gan 0.
```

---

## 5. Threats to Validity — chuyển nguyên sang 21R2

```text
LINK DOC LAP  omega_0 = 0 THEO CAU TAO. ar1_matrix sinh 8 AR(1) DOC LAP; do duoc
              max |r| cheo = 0,023 (n = 200 000, seed 7). Gate 20R2-3' vi the
              thoa MOT CACH TAM THUONG -- KHONG phai tin tot. Moi ket luan cua
              20R2 dieu kien theo gia dinh link doc lap. Tai CHUNG giua cac link
              (Q7 canh bao) CHUA HE duoc do. ⇒ uu tien cao nhat cho 21R2.
T2-R7         2 o rho_bar = 0.96 danh dau EXTRAPOLATION_CONTAMINATED, KHONG lam
              headline. Toan bo 3 MISS cua 20R2.6 phu thuoc mot trong hai o do.
QUAN THE      Ti so theo tung o trai 0,006 - 1,655 (chenh ~300 lan). So GOP che
PHAN HOA      mat dieu do. Tu 20R2.7 bang theo TUNG O la BAT BUOC.
d_sla MU      Tren truc exogenous, 13/16 to hop gate co d_sla = 0 THEO CAU TRUC.
              Mot luoi SLA khac (vd T_delay = 150 ms) se cho phan hoach KHAC HAN
              va cac ket luan nay KHONG chuyen sang duoc.
MIEN MO HINH  20R2-L1: ket luan dieu kien theo mien cua bang tra do duoc.
PILOT XEM     §17.0: §17 duoc viet khi pilot da cho xem truoc hinh dang ket qua.
TRUOC         Da khai; chien dich lap lai pilot rat sat (tau=2 lech 0,65 sigma).
G4 LOI RE     G4 duoc CHON giua BA mo hinh tren du lieu kham pha (§19.2). Holdout
              lam nhe, KHONG xoa loi re do.
CRN           a=0.5 dung CUNG dong cu soc voi a=0.9: nhieu la CHUNG, cau truc
              KHAC. Mot holdout doc lap hoan toan se manh hon.
```

---

## 6. Bộ máy dùng lại được

```text
tools/20r2_5_plan.py        ke hoach la HAM THUAN cua dau vao (khong mang
                            git_commit) -> tat dinh, sinh lai ra cung sha
tools/20r2_5_run.py         so cai = write-ahead log (append + fsync), phat hien
                            file MO COI, guard 6 nhanh (da kill test du 6)
tools/20r2_5_hygiene.py     9 kiem; H5 co DOI CHUNG AM cua chinh no; H6 dong D8
                            mien phi nho CRN; H9 tach hang BUDGET khoi VALIDITY
tools/20r2_5_perfect_twin.py doi chung DUNG CU chay QUA run_cell, kem doi chung
                            cua doi chung (phai ton tai z>0 co err>0)
tools/20r2_6_adjudicate.py  bo cham DONG BANG; tu kiem bang Sheppard tai lap va
                            band == K_MC*se; kiem lai sha tung parquet
docs/inherited_restrictions.json + test  BANH COC cho HAN CHE ke thua
```

**Khuôn cho một gate mới** (dùng cho N3/N4 của D4):
prereg khoá cách đọc → tool + test trên **dữ liệu giả** → mutation test → commit →
**tag đóng băng** → push → chạy **một lần** → commit artifact.

⚠️ Khi dựng gate mới, đọc `docs/inherited_restrictions.json` **trước**, và trả lời
**từng** hạn chế bằng `ACCEPT` hoặc `OVERRIDE` trong prereg của phase mới — nếu
không, `test_inherited_restrictions.py` sẽ đỏ.

---

## 7. Bẫy hạ tầng đã trả giá — đừng trả lại

```text
results/SUPERSEDED co mode 555 (khoa ghi CO Y). Ghi vao do -> PermissionError
  GIUA CHUNG. Sua: mo tam -> tao thu muc -> TRA LAI khoa. ⚠️ git KHONG luu quyen
  thu muc, nen clone cua nguoi khac KHONG co khoa nay.
`| tee log` roi doc `$?` -> lay ma thoat cua `tee`, KHONG phai cua python. Mot lan
  chay CHET tung bi ghi thanh "rc=0". Dung `set -o pipefail` + ${PIPESTATUS[0]}.
mutation test: doi 1 ky tu giu NGUYEN kich thuoc file -> .pyc cu co the bi dung
  lai -> ket qua GIA. Xoa __pycache__ MOI buoc.
`git add -A` giua mot chuoi nhieu buoc -> GOP cac buoc vao mot commit. Stage TUNG
  duong dan khi mot commit can noi dung mot viec.
artifact ghim hash artifact khac -> KHONG tai lap tung byte sau khi cai bi ghim
  doi. 03-run-plan.json chi tai lap TAI commit a92f062d, khong tai HEAD.
```

# T2 — Phán quyết đóng phase

Ngày: 2026-09-09 UTC. Tag: `phase-T2-closed` (`2e122661`), sửa tiếp sau đó ở
`T2.4-fix` và Ưu tiên 2. Trạng thái: **`INSTRUMENT_LIMIT_ON_THE_HEADLINE`**.

T2 biến `tau` thành một trục thật và đo được đường cong `R(tau)` trên một
estimand đã đăng ký. Nó **không** đo được `tau*` — đại lượng đã hứa — vì
`lift(tau)` đòi `err_certified`, thứ không tồn tại trong bất kỳ harness nào
(đo bằng grep, không suy đoán). Đó là giới hạn của **dụng cụ**, được khai
trước khi đọc kết quả, không phải một thất bại phát hiện sau.

---

## 1. Câu hỏi nghiên cứu và phán quyết

| RQ | Câu hỏi | Phán quyết | Bằng chứng |
|---|---|---|---|
| RQ-T2a | `tau` sống ở bao nhiêu chỗ, mấy giá trị? | **HAI** đại lượng thật: `tau_load` = 1.0 (thiết kế) khác `tau_core` = 2.87 (đo được) | prereg F1; `tools/t2_0_tau_audit.py` |
| RQ-T2b | `R(tau)` là đường gì? | **CÓ BƯỚU**, 7/8 arm; đỉnh chỉ phân giải tới khoảng bọc (1, 3) s | `sweep_r3/adjudication_r3.json` D-T2.6-3 |
| RQ-T2c | Khi `tau` quay, lớp chứng nhận còn hợp lệ? | Ba kênh đã nối; nhưng **luật RMS AR(1) mất hiệu lực** ở sigma lớn tại `poisson@0.850` | handoff N3, N4 |
| RQ-T2d | `tau*` ở đâu? | **`NOT_MEASURABLE_BY_THIS_INSTRUMENT`** | handoff N1; `lift`/`err_certified` không tồn tại trong repo |

---

## 2. Kết quả chính — viết thẳng

```text
G-T2-8 ">= 5/7 du doan dinh tinh dung": KHONG DAT. 3 PASS / 7.
  PASS       D-T2.6-1  don dieu giam, 16/16
             D-T2.6-5  giao hai nhanh (estimand KHAC, ghi ro)
             D-T2.6-7  cbr chet, max|R-1| = 0.0161
  FAIL       D-T2.6-2  6 trong / 10 ngoai
             D-T2.6-4  7 pass / 11 fail
  DOC RIENG  D-T2.6-3  buou 7/8 arm, dinh trong khoang boc (1,3) s
             D-T2.6-6  knee ngoai luoi o moi o/z -- DUNG nhu da bao truoc
```

Mẫu số 7 khai **trước** khi đọc (ERRATUM A-T2-3.2 mục 4); không đổi mẫu số,
không đổi ngưỡng sau khi thấy số.

Kết quả có giá trị nhất **không** phải một cổng đạt. Đó là: **luật RMS AR(1)
— nền của toàn bộ dự đoán theo tuổi — không giữ được tính độc lập với `tau`
trên dải `tau` khả thi, và tính hợp lệ của chính nó phụ thuộc `sigma`.** Gate
`ar1_rms_total_fit_within_2pct` đo được: `true` ở `sigma = 0.0096` cho cả bốn
ô, `false` ở `poisson@0.850` khi `a` thuộc {0.5, 0.9}. Điều đó chỉ lộ ra khi
`tau` trở thành một TRỤC thật thay vì một hằng số mặc định.

---

## 3. Đóng góp

```text
(1) F4 -- chung minh err(tau) "gan phang" cua 20R la mot TAUTOLOGY: giu
    z/tau co dinh lam sigma_z bat bien THEO DINH NGHIA
(2) Tach tau_load / tau_core -- hai dai luong, mot ten (NT 64 soi nguoc)
(3) n = n_for_tau(tau, dt) -- ngan sach SUY TU tham so, khong dat truoc
(4) Doi chung bit-exact NC-T2-1, golden nam TRONG git
(5) realizability_gate 9 tieu chi, `not_evaluated` KHONG phai PASS;
    GATE_VERSION = 2 sau khi tieu chi headroom duoc thuc thi that
(6) SO DANG KY ESTIMAND: `estimand_id` bat buoc de phan quyet mot du doan
    da ky; test canh test_t2_estimand_registry.py
(7) Ket qua am co kiem soat cho truc omega (G-A020): c_analytic(1) =
    1.30653541 vs G5c do duoc 1.31226265 (+0.4384%)
(8) MOT SO VO THU NGUYEN quyet dinh truc tau co doc duoc khong: em/A
    (xem muc 4 duoi day)
```

### 3.1 `em/A` — tiêu chí đọc được của trục tuổi

Đặt `em = 0` trong luật rms thì `A` và `c` **triệt tiêu chính xác**:

```text
R(tau) = sqrt( (1 - e^(-z3/tau)) / (1 - e^(-z0/tau)) )
```

Còn lại MỘT đường `tau` thuần, giống nhau ở mọi ô — đó là mẫu số **tự nhiên**,
không phải một lựa chọn tuỳ tiện: nó là giới hạn của chính công thức khi sàn
mô hình bị đưa về 0. Với `z_rep = [0.077, 0.425]`, span của nó = `0.33915`.

So biên độ đo được với đường thuần đó, trên 16 arm (loại `cbr`: `A ~ 1e-4`,
ô suy biến theo QD-3/QD-7):

```text
Spearman(em/A, span/span_thuan) = 0.9706   p = 4.72e-10   n = 16
Pearson                          = 0.9337   p = 1.27e-07

cell             a       em/A   span/pure   do troi em
poisson@0.850   0.9    0.0327       0.764        2.9%
h2@0.700        0.9    0.0425       0.938        4.3%
h2@0.700        0.5    0.0663       1.569        2.0%
h2@0.925        0.9    0.0798       1.766        0.2%
h2@0.960        0.5    0.1463       2.194        0.8%
```

Phán quyết cho rủi ro `RT2-4` ("`err(tau)` ở mode h2 có bị bias tĩnh chi phối
không?"):

```text
(a) h2@0.700 KHONG bi chi phoi o a = 0.9: span/pure = 0.938, lech 6% khoi
    duong tau thuan. RT2-4 DONG cho o nay.
(b) h2@0.700 o a = 0.5 thi CO: 1.569. => phan quyet phu thuoc SIGMA, khong
    chi phu thuoc MODE. RT2-4 nhu duoc viet thieu mot truc.
(c) O bi chi phoi that su la h2@0.925 va h2@0.960 (1.77 - 2.19).
(d) Do TROI cua em chi dong gop <= 10.5% bien do (phan lon < 5%); MUC cua em
    moi la co che. Do la ly do D-T2.6-4 FAIL ma duong cong van doc duoc o
    nhung o co em/A nho.
```

> Đừng nhầm `em` ở đây với `L2-L6` (twin thừa 16.55% cho h2 tại `rho_bar` =
> 0.925, đơn vị ms delay). `em` ở đây là `rms_e_model` trên thang **chi phí**,
> tại `rho_bar` của từng ô. Liên quan nhưng **không đồng nhất** — đặt cạnh nhau
> như cùng một thang là đúng loại lỗi `A-T2-3`.

Nguồn: `results/PENDING/phase-T2/rt24_bias_decomposition.json`,
`tools/t2_rt24_bias_decomposition.py` (chỉ đọc).

---

## 4. Sổ giới hạn

```text
T2-L1  tau* khong do duoc bang dung cu nay (N1)
T2-L2  dinh R(tau) chi phan giai toi khoang boc (1, 3) s (N2)
T2-L3  luat RMS khong hop le o poisson@0.850 tren truc sigma moi (N3)
T2-L4  gia dinh "A, c, em doc lap voi tau" KHONG vung: 11/18 fail (N4)
T2-L5  TOAN BO T2.6 chay tren truc SLA `self_calibrated` -- truc DEPRECATED
       (loi cau truc S14), thay o Lesson 23.21 bang `exogenous_g114_S-B`.
       Ke thua CO CHU DICH de giu so sanh voi 22.6. Moi so cua T2 vi the
       DIEU KIEN theo truc SLA cu. Bang chung duong du lieu:
       tools/t2_sla_axis_provenance.py
T2-L6  tieu chi headroom cua gate khong hoat dong cho toi T2.4-fix; anh
       huong len vong 3 = 0 verdict doi (26 artifact, 196 o), NHUNG do la
       nho QD-7 (a <= 1) va QD-3 (loai cbr), KHONG nho gate
T2-L7  truc tau chay trong twin; realizability neo boi Phase G tai
       tau thuoc {2, 5, 30} s (|sai so| round-trip <= 4.94% cho tau va
       3.82% cho sigma, T_run = 205*tau)
T2-L8  T2 decision_error_v2.run_cell dung k = round(z/dt), KHONG goi bo
       sinh sawtooth. Ket qua neo vao luoi z trung mien legacy
       [0.055, 0.550] s; sawtooth nam o _sawtooth_metric_series, duong khac.
       Khong ke thua err/d_sla cho truc measured + exogenous cua A5.
       Dinh chinh 20R2.0/20R2.1; xem QD-33 va axis_audit.json.
```

---

## 5. Nợ chuyển ra

Xem `docs/phase-T2/07-handoff-21R2.md`: N1–N7 và N6-ERRATUM.
Tóm tắt: `err_certified` chưa cài (N1) · lưới τ mịn hơn trong (1,3) s (N2) ·
bất thường `poisson@0.850` (N3) · giả định độc lập τ (N4) · nợ DOI/K10 (N5) ·
31 artifact bất động khai qua sidecar (N6) · 17 tệp thiếu hẳn `validity` (N7).

---

## 6. Câu Threats-to-Validity viết sẵn

> The correlation time τ is a **design parameter of our load model, not a
> measured property of the network**. We therefore report a curve over τ
> rather than a single operating point. The τ axis is exercised in the twin
> (dt = 0.005 s); its physical realizability is anchored by Phase G, which
> reproduced AR(1) load on the kernel datapath at τ ∈ {2, 5, 30} s with a
> round-trip error of at most 4.94% in τ and 3.82% in σ (each cell a median
> over links and rounds, T_run = 205·τ). Values τ < 2 s are explored **in the
> twin only**. The certification layer inherits the self-calibrated SLA
> thresholds of Phase 20R to remain comparable with Lesson 22.6; that axis was
> superseded by an exogenous ITU-T G.114 manifest, so all Phase T2 numbers are
> **conditional on the earlier SLA axis**. Whether the age-ratio curve is
> readable at all is governed by a single dimensionless quantity, the ratio of
> the static model-error floor to the age amplitude (`em/A`): across 16 arms it
> explains the spread of the measured curve against the pure-τ law with
> Spearman ρ = 0.97.

---

## 7. Điều kiện mở lại

```text
. 21R2 cai err_certified            => mo lai T2.6 de do lift(tau) va tau*
. headline chuyen sang h2 o rho_bar cao => T2-L4 thanh CHAN, khong con la
                                       gioi han (em/A o do la 0.08 - 0.15)
. truc SLA doi sang exogenous_g114_S-B => MOI so cua T2 phai do lai
. mot vong dung sigma TUYET DOI tren o suy bien => QD-7 het che, gate v2
  moi la lop bao ve duy nhat
```

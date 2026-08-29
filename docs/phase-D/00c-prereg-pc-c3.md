# PRE-REGISTRATION — PC-C3: đọc `r` trên `cellA_long` (secondary analysis)

```text
Ngày ký                  2026-08-29
Trạng thái               SIGNED_BEFORE_ANY_CORRELATION_IS_COMPUTED
Tag khóa                 phase-D-pc-c3-start
Dữ liệu                  cellA_long đã thu dưới PC-C2″; 0 giây Mininet mới
Hạng bằng chứng          CONFIRMATORY (xem khẳng định ở mục 0)
```

## 0. Khẳng định liêm chính — bắt buộc, kiểm được

**Chưa từng có một hệ số tương quan nào được tính trên `cellA_long`.** Điều này
được kiểm bằng audit chứ không bằng trí nhớ, trước khi ký:

```text
grep corrcoef|pearson|corr|atanh|fisher trong ba tool da cham cellA_long
   tools/phase_d_pc_c2_second.py       -> khong co
   tools/phase_d_nugget_origin.py      -> khong co
   tools/phase_d_estimator_bias_sim.py -> khong co
quet moi truong dang r/corr/fisher trong artifact co chuoi "cellA_long"
   infra_cellA_long_summary.json / nugget_origin.json / pc_c2_second.json -> NONE
```

Mọi đại lượng đã tính trên `cellA_long` đều là **theo từng link** (ACF, `tau`,
signal fraction). Không có đại lượng nào **giữa hai link**.

Công bố đầy đủ những gì đã nhìn thấy và có thể ảnh hưởng tới người ký:

- `r` của campaign phase-23 (`uA-uB=+0.5986`, `vC-vD=+0.6376`) — dữ liệu cũ,
  đã nằm trong docs, và chính là mốc tham chiếu của bảng dự đoán bên dưới.
- `r` đóng băng của Cell C đã **vô tình bị nhìn** khi kiểm cấu trúc
  `cellC_analysis.json` ở đầu phiên. Chúng thuộc `sigma=0.10`, không phải cấu
  hình của `cellA_long`, và không được dùng để đặt bất kỳ band nào ở đây.
  Ghi ra để người đọc tự trừ hao.
- `tau` per-link và `n_eff` của `cellA_long` đã được tính **trước khi ký**, có
  chủ đích, như một phân tích công suất (mục 4). `tau` là đại lượng per-link,
  độc lập với outcome; biết nó không tiết lộ `r`.

## 1. Vì sao dữ liệu này, chứ không phải Cell C

Cell C đổi `sigma_edge: 0.03 -> 0.10`, mà `sigma` điều khiển **đồng thời**:

```text
N_bar = rho_bar^2/sigma^2 : 817 -> 74      <- bien cua H4
nugget                    : 0.63 -> 0.13   <- bien cua H6
```

Cell C là **confound cấu trúc**: nó không bao giờ tách được H4 khỏi H6. Cell C′
(`sigma=0.05`) cũng vậy, chỉ đổi ít hơn. Đây là lý do sâu xa khiến Cell C
`INVALID_RUN` không phải mất mát — nó là thí nghiệm sai.

`cellA_long` thì khác:

| | phase-23 (r=+0.5986) | cellA_long | |
|---|---|---|---|
| `sigma_edge` | 0.03 | 0.03 | **giữ nguyên** |
| `N_bar` | 817 | 817 | **giữ nguyên** → H4 nguyên vẹn |
| endpoint `hsrc` chung | có | có | **giữ nguyên** → H4 nguyên vẹn |
| bundle telemetry | ditto+probe+cycle, `reconcile=1` | tắt, `reconcile=30` | **chỉ cái này đổi** |
| nugget đo được | 0.632 | 0.136 | → H6 đổi |
| `T_run` | 120 s | 1505 s | và `n_eff` mới đủ |

`cellA_long` **giữ nguyên mọi biến của H4 và chỉ đổi biến của H6**. Đây là
thí nghiệm phân biệt mà cả Phase D′ chưa từng có.

Nó được thu như một đối chứng cho `tau` dưới PC-C2″. Đọc `r` từ nó là một
**câu hỏi mới trên dữ liệu cũ** — secondary analysis, hợp lệ vì được ký trước
khi nhìn (mục 0).

## 2. Estimator khóa trước

```text
truong chinh    rho_measured (results/RAW/phase-D/cellA_long/rho_measured_rep1.csv)
doi chung       rho_offered  (cung run) -- NC-C3, xem muc 5
tau             tau_int, ACF bien chuan hoa lag-0, cat tai lag dau ACF<=0,
                nlag = min(n//4, 50000)          <- nhu PC-C2'', KHONG dung 3000 (D-L19)
                do tu CHINH trace nay, tung link
tau_pair        max(tau_a, tau_b)
burn-in         ceil(5*tau_pair/dt)*dt
r               Pearson tren cua so sau burn-in, mot rep, KHONG noi trace
n_eff           (T - burn)/(2*tau_pair)
CI              Fisher: z=atanh(r), SE=1/sqrt(n_eff-3), CI=tanh(z +- 1.96*SE)
cap phan tich   ca 28 cap khong thu tu cua ma tran 8x8
factorial       nhom theo {shared_host} x {so link low-sigma}, dung
                mininet.traffic_v7.LOAD_CHANNELS va sigma tu meta_rep1.json
```

Cặp có `n_eff < 25` được đánh `diagnostic_only = true` và **không** tham gia
phán quyết. Primary là `uA-uB`; `vC-vD` là bản nhân độc lập trong cùng run.

## 3. ★ Bảng dự đoán ký trước — partition VÉT CẠN, không có lỗ

Dự đoán điểm:

```text
H4  endpoint x N_bar : N_bar=817 va hsrc chung KHONG doi ⟹ co che nguyen ven
                       r ~ +0.60   (moc phase-23: +0.5986 / +0.6376)
H6  shared meas noise: r ~ (1 - sf) * rho_shared = 0.136 * ~0.95 ~ +0.13
H0  khong co gi      : r ~ 0
```

Partition áp cho **từng** cặp primary, vét cạn trục thực:

| Khoảng `r` | Nhãn |
|---|---|
| `r < -0.10` | `UNRESOLVED_OUT_OF_BAND` |
| `-0.10 <= r < 0.00` | `H0` |
| `0.00 <= r <= 0.10` | `H6_H0_NOT_SEPARATED` |
| `0.10 < r <= 0.25` | `H6` |
| `0.25 < r < 0.45` | `UNRESOLVED_GAP` |
| `0.45 <= r <= 0.75` | `H4` |
| `r > 0.75` | `UNRESOLVED_OUT_OF_BAND` |

Ghi thẳng một điểm mà bản đề xuất đầu vào nói sai: **ba band KHÔNG rời nhau.**
Band H6 `[0.00,+0.25]` và band H0 `[-0.10,+0.10]` chồng lấn trên `[0.00,+0.10]`.
Không sửa band sau khi nhìn số; thay vào đó vùng chồng lấn được **ký trước**
thành nhãn riêng `H6_H0_NOT_SEPARATED`.

Phán quyết gộp hai primary, ký trước:

```text
ca hai cung mot nhan H4/H6/H0        -> nhan do
ca hai deu diagnostic_only            -> UNDERPOWERED_NO_VERDICT
hai primary khac nhan                 -> PRIMARY_REPLICATES_DISAGREE
moi truong hop con lai                -> UNRESOLVED
```

## 4. Phân tích công suất — tính TRƯỚC khi ký, có chủ đích

`tau_int` đo trên chính `cellA_long` (per-link, không phải outcome):

```text
uA 13.441  uB 17.370  vC 17.335  vD 15.240  ac 2.641  ad 6.755  bc 2.475  bd 3.630   (s)

cap        tau_pair   burn      n_eff     gate 25
uA-uB       17.370    87.0 s    40.81     PASS
vC-vD       17.335    86.8 s    40.90     PASS
ac-ad        6.755    33.8 s   108.88     PASS
bc-bd        3.630    18.2 s   204.76     PASS
uA-vC       17.335    86.8 s    40.90     PASS
```

**Lần đầu tiên trong cả dự án cả hai primary đều đạt `n_eff >= 25`.**

Nhưng công suất có giới hạn phải ký trước, không được phát hiện sau:

```text
n_eff ~ 40.8  ⟹  SE_z = 1/sqrt(40.8-3) = 0.163  ⟹  nua-do-rong CI(95%) = +-0.319 (thang z)

|z(0.60) - z(0.13)| = 0.693 - 0.131 = 0.562  >  0.319   ⟹ H4 vs H6  TACH DUOC
|z(0.13) - z(0.00)| = 0.131 - 0.000 = 0.131  <  0.319   ⟹ H6 vs H0  KHONG TACH DUOC
```

Vì vậy PC-C3 được ký với phạm vi đúng như nó có:

> PC-C3 có công suất để **xác nhận hoặc bác H4**. Nó **không** có công suất để
> tách H6 khỏi H0. Điều đó chấp nhận được vì câu hỏi sống còn là “`+0.6` có
> còn không khi CHỈ bundle telemetry đổi” — H4 nói còn, H6 và H0 đều nói
> không. Việc phân biệt H6 với H0 thuộc Phase G.

## 5. Đối chứng bắt buộc

```text
NC-C1  r(ac,ad) va r(bc,bd) thuoc [-0.10,+0.15]
NC-C2  r(uA,vC) thuoc [-0.10,+0.15]
NC-C3  r tren rho_offered cua CUNG run: moi cap edge ~0 (|r| <= 0.15).
       Offered la tai DANH DINH sinh doc lap tung link, nen no gan 0 duoi
       MOI gia thuyet. Day la doi chung cho GENERATOR, khong phai bien phan
       biet H4/H6 -- khong duoc doc no nhu bang chung cho gia thuyet nao.
PC-C1  warm_start_active = round(rho^2/sigma^2): da PASS 4/4 (817/856/817/875)
PC-C3m metadata dung sigma/duration/seed: da PASS
infra  bon co false: da PASS
```

## 6. Validity gate

```text
[ ] cap duoc ket luan co n_eff >= 25 (cap khong dat -> diagnostic_only)
[ ] burn-in thuc te >= 5*tau_pair, tau do tu chinh trace
[ ] NC-C1, NC-C2, NC-C3 dat
[ ] infra bon co false
[ ] khong thieu link, khong NaN, khong counter reset
[ ] file nay + tool commit va tag TRUOC khi chay
```

**Không phải gate: giả thuyết nào thắng.**

## 7. Giới hạn biết trước

```text
D-L27  n_runs = 1 (seed 41). Khong co phuong sai lien-run. n_eff trong-run cho
       CI Fisher hop le nhung KHONG thay the replicate doc lap.
D-L28  Bundle telemetry doi BON yeu to cung luc (ditto, aoi_probe, cycle_trace,
       reconcile_every 1->30). PC-C3 tach {bundle} khoi {sigma}; no KHONG tach
       duoc bon yeu to voi nhau. Can luoi 2x2 {ditto on/off} x {sigma} o Phase G.
D-L29  PC-C3 khong co cong suat tach H6 khoi H0 (muc 4). Ket qua trong
       [0.00,+0.10] duoc ghi H6_H0_NOT_SEPARATED, khong duoc ep ve mot phia.
```

## 8. Điều PC-C3 KHÔNG làm

- Không tái phân xử Cell C. Cell C vẫn `INVALID_RUN` dưới A001/A002.
- Không đọc outcome đóng băng của Cell C.
- Không đảo PC-C2″b FAIL, không hạ ngưỡng nào.
- Không tuyên bố cơ chế vật lý; kể cả khi H6 thắng, việc quy cho phần tử nào
  trong bundle vẫn thuộc Phase G (D-L28).

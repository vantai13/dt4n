# L2.0 — Kiểm toán khoảng cách cơ chế

Ngày: 2026-09-07 UTC.
Trạng thái: **`AUDIT_NO_MEASUREMENT`**. Không phân xử dữ liệu mới, không ký
gate đo, không chạy root/netns/tc/Mininet.

Số duy nhất được trích ở đây thuộc hai loại:
1. **Đã đo trước đây** — đọc lại từ artifact Phase L đã tồn tại
   [link_model_v2_fit.json](../../results/LIVE/phase-L/link_model_v2_fit.json).
2. **Suy ra bằng số học** — tái lập được bằng
   [tools/l2_0_audit_check.py](../../tools/l2_0_audit_check.py), khoá bằng
   [test/test_l2_0_audit.py](../../test/test_l2_0_audit.py) (10 test, không cần root).
   Artifact: [l2_0_audit_check.json](../../results/SMOKE/phase-L2/l2_0_audit_check.json).

Quy tắc lesson: mỗi dòng có bằng chứng `file:dòng`; mỗi khác biệt có dự đoán
**có dấu**; khác biệt nào chưa suy được hậu quả thì trở thành câu hỏi đo.

---

## 0. Sáu phát hiện của lượt rà

| # | Phát hiện | Hệ quả |
|---|---|---|
| **F1** | `q_mean_ms` là OWD **thô**, chưa trừ sàn (`l6_campaign.py:290,299`) | Cách tính SNR trong ghi chú kế hoạch là lỗi phạm trù. Kết luận vẫn đúng, và **mạnh hơn** |
| **F2** | Đường cong `cbr` **đã đo** phẳng từ ρ=0.50→0.95; R = **1.002** | Nhánh `c_a ≈ 0` của S37 **đã được xác nhận bằng dữ liệu có sẵn**, không cần đo lại |
| **F3** | Lập luận D/D/1 (§3.2 ghi chú) và ON-OFF (§3.4) **mâu thuẫn nhau** | D/D/1 chỉ là trường hợp riêng `n = 1`. "Phẳng với mọi ρ" **không** là kết luận tổng quát |
| **F4** | Công thức `ρ(n−1)²s/(2n)` **bỏ sót tín dụng burst tầng 2** | Bảng dự đoán ký trước sai **+152%** tại n=4. `R` không đổi |
| **F5** | `h2` — ngẫu nhiên mạnh — cho R = **3.716**, rơi vào dải `INCONCLUSIVE` | **Ngưỡng gate của ghi chú bị hiệu chuẩn sai.** `R` bị mất mát gói bóp méo |
| **F6** | Probe của nhánh `MAIN` bị chèn **sau** nguồn backlogged ở tầng 1 | Nó sẽ đo **641 ms** hàng đợi tầng 1, không phải ~7 ms của tầng 2. Lỗi chí mạng |

---

## 1. Bảng đối chiếu Phase L vs Phase G′

| Trục | Phase L | Phase G′ | Bằng chứng | Hậu quả **có dấu** |
|---|---|---|---|---|
| framework | Mininet + OVS, `s1-eth2` | veth thuần + netns, `g2v{i}` | `phase-L/01-infra.md:11-12,22` · `g2_kill_test.py:55,78-80` | **Chưa suy được** ⟹ câu hỏi đo `FLOOR` |
| ngữ nghĩa HTB | `rate 6mbit` **cố định** = CÁI LINK | `rate = ρ(t)·C`, ghi lại mỗi **100 ms** = BỘ ĐẶT TỐC ĐỘ | `01-infra.md:40` · `g2_kill_test.py:45,87-93` · `rate_controller.py:79-84` | ★ **S32** — hai vai trò đối lập |
| qdisc con | `bfifo limit 19656b` (**byte**) | `pfifo limit 300` (**khung**) | `01-infra.md:41` · `g2_kill_test.py:49,94-95` | ★ khác **đơn vị** |
| kích thước buffer | 19 656 B = **13 khung** (1512 B) | 300 × 1442 = **432 600 B** | `01-infra.md:71` · `g2_kill_test.py:49-50` | ★ G′ lớn **22×**; hai mục đích đối lập |
| `burst` tầng đo | `1600b` (= 1.06 khung) | `1442b` (= **đúng 1 khung**) | `01-infra.md:40` · `g2_kill_test.py:92` | ★ **1 khung ⟹ delay tầng 2 = 0** (§3) |
| khung tham chiếu | **1512 B** (payload 1470) | **1442 B** (payload 1400) | `02-probe-validation.md:44` · `blast_source.py:21` · `g2_kill_test.py:50` | lệch 4.63%, phải quy đổi; `bfifo` chứa **13** khung 1442 B |
| netem | có, **chiều VỀ** (`s2-eth2`, 3 ms) | không có | `01-infra.md:43` · `g2_kill_test.py:75-95` không gọi netem | chiều đo không đụng ⟹ **0 ms** |
| nguồn | `flow_engine`, 4 họ đã hiệu chuẩn | `blast_source` backlogged, blocking | `99-gate-decision.md:107-112` · `blast_source.py:21,29-32` | ★ **S31** — G′ chỉ sinh được một họ |
| đo cái gì | **OWD của chính dòng nền** | bộ đếm byte `/proc/net/dev` | `l6_campaign.py:284,290,299` · `byte_sampler.py:27-39` | ★ **S34** — G′ không có dụng cụ đo delay |
| probe phụ | Poisson 20 pps, đối chứng PASTA | không có | `l6_campaign.py:307-308` · `99-gate-decision.md:48` | L2 phải dựng lại probe |
| serialization | Mininet **không tính** ở chiều đo | chưa kiểm trên veth | `99-gate-decision.md:50-51` | **Chưa suy được** ⟹ câu hỏi đo `V-L2` |

### 1.1. ★ F1 — `q_mean_ms` là OWD thô, không phải delay hàng đợi

[`measurements/l6_campaign.py:290`](../../measurements/l6_campaign.py#L290) đặt
`owd = bg["owd_ms"]`, rồi dòng 299 ghi `"q_mean_ms": owd["mean"]`. Không có
phép trừ sàn ở bất kỳ đâu. Xác nhận độc lập:
[`measurements/l7_fit.py:228`](../../measurements/l7_fit.py#L228) phải viết
`floor = ybar[0] if mode == "cbr" else 0.0` — tức chính code fit đã coi mức
`cbr` **là** cái sàn.

Hai hệ quả:

- Ghi chú kế hoạch tính `SNR = 0.133 / 0.1453 = 0.92` như thể `0.133` là tín
  hiệu **trên** sàn. Không phải. `0.133` **đã bao gồm** sàn.
- Đại lượng đúng là phần **dôi ra**: `0.1330 − 0.1407 = −0.0077 ms`
  (`07-fit.md:111` trừ `02-probe-validation.md:37`). Tức **âm**, tức bằng không
  trong sai số.

> Kết luận của ghi chú (kiến trúc A chết) **đúng**, nhưng lý do mạnh hơn nó
> tưởng: tín hiệu `cbr` không phải "0.92 lần sàn", mà là **không tồn tại**.

### 1.2. ★ F2 — nhánh `c_a ≈ 0` của S37 đã có câu trả lời đo được

Đọc `delay_observed` của `cbr|6|13` từ artifact campaign đã chạy
([`link_model_v2_fit.json`](../../results/LIVE/phase-L/link_model_v2_fit.json)):

```text
rho      0.50   0.60   0.70   0.80   0.85   0.90   0.925  0.95  | 0.98   1.00    1.02
cbr ms   0.1386 0.1382 0.1415 0.1403 0.1408 0.1330 0.1392 0.1385| 0.1624 4.6904 24.17
```

**Phẳng tuyệt đối trên toàn dải dưới tới hạn**, rồi nổ ở ρ ≥ 1.0. Đây không
phải suy luận — đây là 728 điểm đã đo (`99-gate-decision.md:65`).

Bộ phân biệt tính trên **chính dữ liệu này**, không cần chạy gì:

| họ | c_a | d(0.60) ms | d(0.95) ms | **R** | loss@0.95 |
|---|---:|---:|---:|---:|---:|
| `cbr` | 0.004 | 0.1382 | 0.1385 | **1.002** | 0.0000 |
| `poisson` | 1.003 | 0.7099 | 8.4022 | **11.836** | 0.0151 |
| `h2` | 2.032 | 3.2781 | 12.1817 | **3.716** | 0.0892 |
| `onoff` | 2.312 | 0.1435 | 10.4550 | **72.841** | 0.0331 |

Tham chiếu lý thuyết: tất định **1.583**, M/D/1 Kingman **12.667**.

`poisson` đo được **11.836** so với Kingman **12.667** — lệch 6.6%. Đó là một
xác nhận độc lập rất mạnh rằng số hạng `1/(1−ρ)` có thật khi quá trình đến
ngẫu nhiên, và **biến mất hoàn toàn** khi nó tất định (`cbr`, R = 1.002).

---

## 2. Ba hằng số Phase L: đo lại hay suy được?

| hằng số | giá trị | nguồn | phụ thuộc khác biệt nào | phán quyết |
|---|---:|---|---|---|
| sàn nhiễu V-L0 | 0.1453 ms (SD 0.1186) | `02-probe-validation.md:25` | probe + host + framework; **không** phụ thuộc qdisc | **ĐO LẠI** — rẻ, 60 s, nhánh `FLOOR` |
| OWD tải-0 có HTB, bw=6 | 0.1407 ms | `02-probe-validation.md:37` | như trên, cộng ngữ nghĩa HTB | **ĐO LẠI** cùng `FLOOR` |
| sàn nửa-độ-rộng α=0.10 | 0.4646 ms | `99-gate-decision.md:98` | `sigma_schedule` của **họ lưu lượng** | **ĐO LẠI khi chốt họ** (L2.2) — vô nghĩa cho nguồn tất định, vì không có "schedule draw" |
| efficiency | 0.7653 | `99-gate-decision.md:147` | mô hình PCHIP + họ + lưới ρ | **PHỤ THUỘC L2.3**, không tái dùng trực tiếp |
| trần buffer | 26.21 ms | `01-infra.md:96` | `bfifo` byte / C | **SUY ĐƯỢC**; với khung 1442 B, `bfifo` chứa **13** khung (`19656 // 1442 = 13`) |

Ghi chú: `sigma_schedule = 0.2824 ms` giải thích `99.874%` phương sai đo
(`99-gate-decision.md:92-94`). Đại lượng đó là **phương sai của lần rút lịch
trình ngẫu nhiên**. Nguồn tất định không có lần rút nào, nên sàn 0.4646 ms
**không chuyển giao được** sang kiến trúc A. Đây là một chi phí ẩn của lựa
chọn ① mà ghi chú kế hoạch chưa tính.

---

## 3. ★ S37 — cưỡng chế tốc độ và ngẫu nhiên đến loại trừ nhau

```text
S37  TRÊN MỘT ĐƯỜNG DUY NHẤT, CƯỠNG CHẾ TỐC ĐỘ VÀ PHƯƠNG SAI ĐẾN LOẠI TRỪ NHAU

     · delay(ρ) tăng theo ρ       ⟸ CẦN phương sai của quá trình đến (Kingman)
     · cưỡng chế tốc độ chính xác ⟸ CẦN token bucket + hàng đợi
     · token bucket + hàng đợi    ⟹ LÀM MỊN phương sai đến

     ⟹ cùng một cơ chế vừa cho ρ(t) chính xác vừa cho quá trình đến ngẫu nhiên
        thì tự mâu thuẫn, TRỪ KHI hai thứ sống ở HAI THANG THỜI GIAN TÁCH BIỆT.
```

Trạng thái: nhánh `c_a ≈ 0` **đã xác nhận bằng đo** (§1.2, R = 1.002). Phần
còn lại — hành vi khi `burst > 1 khung` — vẫn là **suy luận chưa đo**.

### 3.1. F3 — hai lập luận trong ghi chú mâu thuẫn nhau

Ghi chú §3.2 nói: dòng đến **đều** ⟹ D/D/1 ⟹ hàng đợi không bao giờ vượt 1 gói
⟹ phẳng với **mọi** ρ < 1.
Ghi chú §3.4 nói: dòng đến là **ON-OFF tất định** ⟹ hàng đợi dâng tới `B`.

Không thể đồng thời đúng. Phân giải:

```text
n = B / L  (số khung trong một burst tầng 1)

n = 1  ⟹ tầng 1 nhả từng khung một, cách đều  ⟹ D/D/1  ⟹ delay = 0   ← §3.2 đúng Ở ĐÂY
n > 1  ⟹ tầng 1 nhả CỤM n khung rồi nghỉ      ⟹ ON-OFF ⟹ delay > 0   ← §3.4 đúng Ở ĐÂY
```

⟹ §3.2 là **trường hợp riêng n = 1** của §3.4, không phải một lập luận độc lập.
Và hiện trạng `g2_kill_test.py:92` đặt `burst = 1442b` = **đúng 1 khung**,
nên nó nằm chính xác ở ô `n = 1`.

> Kiến trúc A chết vì **tham số burst hiện tại**, không phải vì cấu trúc.
> Phân biệt này quan trọng: nó là lý do `B` trở thành trục quét của L2.0b.

### 3.2. F4 — dẫn xuất đúng, có tín dụng burst tầng 2

Cầu thang token bucket **đã đo** (`02-probe-validation.md:47-50`, khớp bảng
`:69-78` với sai số ≤ 0.040 ms):

```text
d_k = ((k − 1)·L − B₂) / C          kẹp ở 0
```

Chú ý `(k−1)`, không phải `k`: HTB nhả gói khi token **còn dương** rồi cho âm,
nên bucket 1600 B cho **hai** khung 1512 B đi tự do, không phải một. Đo được:
`d_1 = 0.074`, `d_2 = 0.044`, `d_3 = 1.877` ms (`02-probe-validation.md:71-73`).

Đặt `s = L·8/C` (thời gian phục vụ một khung), `β = B₂·8/C` (tín dụng burst
tầng 2, tính bằng ms). Tầng 1 nhả `n` khung tức thời mỗi chu kỳ `T = n·s/ρ`.
Thời gian chờ ảo là răng cưa `V(t) = max(0, v_max − t)` với
`v_max = max(0, (n−1)s − β)`. Theo PASTA, probe Poisson thấy trung bình thời gian:

```text
                      v_max²        ρ · max(0, (n−1)s − β)²
delay_q(ρ, n)  =  ───────────  =  ─────────────────────────
                      2·T                  2·n·s
```

Với `C = 6 Mbps`, `L = 1442 B`, `B₂ = 1600 B`:
`s = 1.92267 ms`, **`β = 2.13333 ms`**.

★ `β > s`. Tín dụng burst tầng 2 **lớn hơn một khung**. Ghi chú kế hoạch bỏ
sót số hạng này. Hậu quả có dấu:

| n | ρ=0.60 | ρ=0.80 | ρ=0.90 | ρ=0.95 | ghi chú kế hoạch (ρ=0.90) | sai lệch |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | — |
| 2 | **0.000** | **0.000** | **0.000** | **0.000** | 0.433 | ô chết |
| 4 | 0.515 | 0.687 | 0.773 | 0.816 | 1.947 | **+152%** |
| 8 | 2.502 | 3.336 | 3.752 | 3.961 | 5.299 | **+41%** |
| 12 | 4.702 | 6.269 | 7.053 | 7.445 | 8.724 | **+24%** |

Kiểm chéo độc lập bằng lấy mẫu Poisson răng cưa: khớp giải tích trong 3%
(`test_analytic_matches_independent_sawtooth_sampling`).

**`n = 2` là ô chết**: `(2−1)·1.92267 − 2.13333 < 0`. Lưới `B` phải bỏ qua nó.

### 3.3. Bộ phân biệt sống sót

`β` nằm ở tiền tố **không phụ thuộc ρ**, nên nó triệt tiêu trong tỉ số:

```text
                   delay_q(ρ=0.95) / delay_q(ρ=0.60)

  ON-OFF TẤT ĐỊNH   = 0.95 / 0.60                          = 1.583   (mọi n)
  M/D/1 (Kingman)   = [0.95/(2·0.05)] / [0.60/(2·0.40)]    = 12.667

  ⟹ TÁCH NHAU 8.0 LẦN.
```

Đối chiếu số **đã đo** (§1.2): `cbr` = 1.002, `poisson` = 11.836. Hai cực
thực nghiệm nằm đúng hai bên. Bộ phân biệt hợp lệ.

### 3.4. ★ F5 — nhưng ngưỡng gate của ghi chú bị hiệu chuẩn sai

Ghi chú đề xuất: `R ≤ 3.0 → S37_CONFIRMED`, `R ≥ 6.0 → S37_REFUTED`,
`3.0 < R < 6.0 → INCONCLUSIVE`.

Nhưng `h2` — `c_a = 2.032`, ngẫu nhiên **mạnh hơn** Poisson — cho **R = 3.716**,
rơi thẳng vào dải `INCONCLUSIVE`. Nguyên nhân: **mất mát gói cắt cụt đuôi**.
`h2` mất 8.92% ở ρ=0.95 (`loss_observed`), nên delay bị buffer chặn ở
~12 ms thay vì `3.2781 × 12.667 = 41.5` ms.

```text
⟹ R KHÔNG phải bộ phân biệt sạch khi có loss.
   Một cơ chế ngẫu nhiên mà mất gói có thể đọc nhầm thành "tất định".
   Đây là kiểu thất bại "cơ chế đúng, dụng cụ nói sai" của KILL-1.
```

**Sửa bắt buộc trước khi ký L2.0b:**

1. Thêm gate chặn **`LOSS-1`: loss ≤ 0.005 ở mọi ô của nhánh `MAIN`.** Ô nào
   vượt thì `R` của ô đó không đọc được. Lưới `n ≤ 12` thoả điều kiện này theo
   thiết kế (§3.5), nên đây là kiểm tra, không phải ràng buộc mới.
2. Đọc `R` **chỉ trên các ô loss ≈ 0**.
3. Với nhánh `PC`, dùng `ρ ∈ {0.60, 0.90}` thay cho `{0.60, 0.95}` nếu loss ở
   0.95 vượt ngưỡng — Phase L đo `poisson` loss@0.95 = 1.51%, đã sát mép.

### 3.5. Đối chứng tràn còn nguyên

`bfifo limit 19656 B` chứa `19656 // 1442 = 13` khung 1442 B. Đỉnh backlog
tầng 2 là `(n−1)` khung:

| n | đỉnh backlog (B) | so với 19 656 B |
|---:|---:|---|
| 4 | 4 326 | vừa |
| 8 | 10 094 | vừa |
| 12 | 15 862 | vừa |
| **26** | **36 050** | **TRÀN** |

⟹ lưới `n ≤ 12` không mất gói (thoả `LOSS-1`); `n = 26` mất `≈ (26−15)/26 ≈ 0.42`
(1 khung đi ngay + ~1 khung tín dụng burst + 13 khung vào buffer). Dự đoán
`> 0.20` của ghi chú an toàn.

---

## 4. Bộ lọc thông thấp của token bucket

Token bucket là **bộ lọc thông thấp trên tốc độ**, thang cắt

```text
T_c = B / (ρ · C)          B tính bằng byte, C bằng byte/s
```

Cấu trúc **chậm hơn** `T_c` bị shaper cưỡng chế; cấu trúc **nhanh hơn** `T_c`
đi xuyên qua. `B` chính là tần số cắt — tham số thiết kế quan trọng nhất của L2.

Tại ρ = 0.90, C = 6 Mbps (750 000 B/s):

| B (khung 1442 B) | B (byte) | `T_c` (ms) | đối chiếu thang |
|---:|---:|---:|---|
| 1 | 1 442 | **2.14** | dưới mọi thang quan tâm ⟹ **làm phẳng tất cả** — hiện trạng `g2_kill_test.py:92` |
| 4 | 5 768 | 8.54 | dưới thang hàng đợi |
| 8 | 11 536 | 17.09 | tiệm cận thang hàng đợi |
| 12 | 17 304 | **25.63** | ≈ thang hàng đợi **26.21 ms** (`01-infra.md:96`) |
| 13 | 18 746 | 27.76 | vượt thang hàng đợi |

Các thang khác trong hệ: `dt = 100 ms` (`g2_kill_test.py:45`),
`τ = 2 s` (`g2_kill_test.py:44`), τ mục tiêu 2–30 s.

```text
⟹ Có một CỬA SỔ TẦN SỐ TRỐNG giữa thang hàng đợi (~26 ms) và dt (100 ms).
   Đó là chỗ duy nhất mà "cấu trúc nhanh" và "cưỡng chế chậm" có thể cùng tồn
   tại. Lựa chọn ②a và ③ của L2.2 đều sống hoặc chết trong cửa sổ này.
   ⚠️ ĐÂY LÀ SUY LUẬN, CHƯA ĐO. Không được ký.
```

---

## 5. Phán quyết kiến trúc

| kiến trúc | phán quyết | lý do định lượng |
|---|---|---|
| **A** — blast backlogged + shaper, `burst = 1 khung` | **LOẠI** | `n = 1` ⟹ `v_max = 0` ⟹ `delay_q ≡ 0` với mọi ρ (§3.2). Xác nhận bằng đo: `cbr` R = 1.002, phẳng 0.1386→0.1385 trên ρ=0.50→0.95 |
| **B** — "shaper hoặc bind hoặc không bind" | **VIẾT LẠI** | Tiền đề sai. Token bucket **là** chế độ ở giữa, tham số hoá bởi `T_c = B/(ρC)` (§4) |
| **C** — cứu bằng `burst` lớn | **KHÔNG ĐỦ** | `delay_q ∝ ρ` tuyến tính, R = 1.583 với **mọi** n (§3.3). Burst lớn cho delay **cao hơn**, không cho `1/(1−ρ)` |

### Bộ lựa chọn L2.2 được viết lại

| | Lựa chọn | Chi phí | Rủi ro | Đánh đổi |
|---|---|---:|---|---|
| **①** | `c_a` là trục TWIN, testbed chạy `cbr` | 0 ngày | — | ⚠️ **RỖNG**. `cbr` delay = sàn, phẳng ⟹ closed-loop không có gì để chứng nhận. Thêm: sàn 0.4646 ms **không chuyển giao được** (§2) |
| **②a** | Điều biến tốc độ thang nhanh (`dt_fast ≈ 10 ms` + `σ_fast`) | 5–8 ngày | trung bình | Giữ kernel-enforcement ⟹ không mở lại `G-L98`. Nhưng là **họ lưu lượng MỚI** ⟹ `link_model_v2` phải hiệu chuẩn lại từ đầu |
| **②b** | Nguồn ngẫu nhiên + `burst ≈ q` (tách thang tần số) | 5–10 ngày | **cao** | Rủi ro quay lại `G-L98` nếu nguồn phải giữ tốc độ |
| **③** | `flow_engine` cho tầng B, shaper chỉ làm bao chậm | 3–5 ngày | **cao** | Có ngay 4 họ đã hiệu chuẩn ⟹ `link_model_v2` dùng lại được. Phải chứng minh `σ ⊥ τ` **vẫn giữ** |

📌 **③ được nâng hạng.** Trước đây loại vì `S14`. Nhưng `S14` khoá `σ` với `τ`
**trong cùng dải tần**; với `T_c = B/(ρC)` (§4), `flow_engine` chỉ cần cung cấp
cấu trúc **nhanh hơn** `T_c`, còn `(σ, τ)` chậm hơn `T_c` vẫn do shaper cưỡng
chế. Nếu hai thứ ở hai dải tần khác nhau thì `S14` không áp dụng.

★ **Bằng chứng mới ủng hộ ③, từ F1:**
[`l6_campaign.py:284,290,299`](../../measurements/l6_campaign.py#L284) cho thấy
`q_mean_ms` của Phase L là OWD **của chính dòng nền `flow_engine`**, còn probe
20 pps chỉ là đối chứng PASTA (`:307-308`). Nghĩa là toàn bộ `link_model_v2`
được hiệu chuẩn trên đúng cơ chế mà ③ đề xuất tái dùng. Không có khoảng cách
dụng cụ nào phải bắc cầu.

⚠️ Chưa kiểm `σ ⊥ τ` trên cơ chế lai. Không ký ③ dựa trên đoạn này.

---

## 6. Đề xuất L2.0b và dự đoán ký trước

### 6.1. Thứ tự lesson phải đổi

```text
KẾ HOẠCH CŨ:  L2.0 → L2.1 → {L2.2, L2.3} → L2.4
PHẢI THÀNH:   L2.0 → L2.0b → L2.2 → L2.1 → L2.3 → L2.4
```

Quyết định `c_a` (L2.2) là **điều kiện tiên quyết** của L2.1, vì nó quyết định
có tồn tại một tầng 2 có nghĩa hay không.

### 6.2. ★ F6 — lỗi chí mạng phải sửa trước khi dựng

Thiết kế trong ghi chú đặt probe ở root ns, đi qua **cả** tầng 1 lẫn tầng 2.
Nhưng `blast_source.py:29` dùng `setblocking(True)` và bơm liên tục, nên hàng
đợi `pfifo limit 300` ở tầng 1 (`g2_kill_test.py:95`) **luôn đầy**. Probe chèn
vào đuôi hàng đó sẽ đo:

| ρ | delay tầng 1 mà probe phải chịu |
|---:|---:|
| 0.60 | **961.3 ms** |
| 0.90 | **640.9 ms** |
| 0.95 | **607.2 ms** |

So với tín hiệu tầng 2 lớn nhất là **7.4 ms** ⟹ nhiễu lớn hơn tín hiệu **87×**.
Nhánh `MAIN` như đặc tả **không đo được cái nó định đo**.

**Sửa:** chèn probe từ **netns `l2mid`**, tức giữa hai tầng. Khi đó probe chỉ
đi qua tầng 2 và lấy mẫu đúng hàng đợi cần đo. Tải thêm không đáng kể:
`20 × (64+42) × 8 = 16.96 kbps = 0.28%` của 6 Mbps.

Đồng hồ vẫn hợp lệ: `ip netns add` chỉ tạo **network** namespace, không tạo
time namespace, nên `CLOCK_MONOTONIC` dùng chung toàn host ⟹ không có clock
skew, không cần PTP. Ghi vào prereg.

### 6.3. Topology

```text
  root ns                    ns l2mid                    ns l2sink
 ┌─────────┐               ┌───────────┐               ┌──────────┐
 │ blast   │──l2a══veth═══▶│l2a_p      │               │          │
 └─────────┘               │ (forward) │──l2b══veth═══▶│  l2b_p   │
                           │ ★ probe ──┼──────────────▶│  sink    │
                           └───────────┘               └──────────┘
  TẦNG 1 trên `l2a` (root ns)          TẦNG 2 trên `l2b` (ns l2mid)
  htb rate = ρ·C, burst = n khung      htb rate = C, burst 1600b
  pfifo limit 300                      bfifo limit 19656 B
  ← BỘ ĐẶT TỐC ĐỘ                       ← CÁI LINK (hằng số Phase L, KHÔNG đổi)
```

Ba quyết định thiết kế:

1. **ρ cố định mỗi run**, không dùng `rate_controller`. S37 là về **quá trình
   đến**, không về điều biến `ρ(t)`. Bỏ tầng điều biến ⟹ bớt một nguồn lỗi.
2. **Tầng 2 dùng đúng hằng số Phase L** (`01-infra.md:40-41`) ⟹ đối chứng
   dương so trực tiếp được với 5.725 ms đã đo. Đổi hằng số ở đây là vứt đi tài
   sản duy nhất mình có.
3. **Probe chèn ở `l2mid`** (§6.2), trừ nhánh `PC` nơi nguồn Poisson tự đo
   chính nó — đúng phương pháp Phase L (`l6_campaign.py:290`).

### 6.4. Năm nhánh

| Nhánh | Nguồn nền | Tầng 1 | Probe chèn tại | Mục đích |
|---|---|---|---|---|
| `FLOOR` | không có | — | `l2mid` | sàn nhiễu đường ống mới |
| `MAIN` | `blast_source` | `rate=ρC`, `burst=n` | `l2mid` | ★ đo `delay_q(ρ, n)` |
| `NC` | `blast_source` | `burst=1`, **tầng 2 = 10·C** | `l2mid` | tầng 2 không ràng buộc ⟹ delay về sàn |
| `OVF` | `blast_source` | `burst=26 khung` | `l2mid` | kiểm `bfifo` thật sự chặn ⟹ phải có loss |
| **`PC`** | `owd_probe --mode poisson` tại ρC | **bỏ tầng 1** | tự đo (root ns) | ★★ đối chứng dương |

`PC` làm ba việc cùng lúc: (1) chứng minh probe + tầng 2 **thấy** được hàng
đợi; (2) neo vào số đã đo của Phase L (5.725 ms tại ρ=0.90); (3) **chính là
thử nghiệm của lựa chọn ③** — `G-L98` nói userspace không giữ được **tốc độ**
chính xác, nó không nói userspace không sinh được **ngẫu nhiên**.

### 6.5. Bảng dự đoán ký trước

Hằng số: `C = 6 Mbps`, `L = 1442 B`, `s = 1.92267 ms`, `β = 2.13333 ms`,
sàn Phase L `0.1453 ms`.

`MAIN` — `delay_q = ρ·max(0,(n−1)s−β)²/(2ns)`, ms **trên** sàn:

| n (khung) | ρ=0.60 | ρ=0.80 | ρ=0.90 | ρ=0.95 |
|---:|---:|---:|---:|---:|
| 1 | 0.000 | 0.000 | 0.000 | 0.000 |
| 4 | 0.515 | 0.687 | 0.773 | 0.816 |
| 8 | 2.502 | 3.336 | 3.752 | 3.961 |
| 12 | 4.702 | 6.269 | 7.053 | 7.445 |

★ Lưới `B` bỏ `n = 2` (ô chết, §3.2). Dùng `B ∈ {1, 4, 8, 12}`.

```text
Q-1   R = delay_q(0.95)/delay_q(0.60) tại n=12   dự đoán 1.583  [1.35, 1.85]
Q-2   delay_q tại n=1, mọi ρ                      dự đoán ≈ 0    < 2× SD sàn
Q-3   độ dốc delay_q theo n tại ρ=0.90            dự đoán ~0.79 ms/khung, ±40%
LOSS-1 loss mọi ô MAIN                            dự đoán ≤ 0.005            ★ MỚI
NC    delay_q khi tầng 2 = 10C                    dự đoán ≈ 0
OVF   loss tại n=26, ρ=0.90                       dự đoán > 0.20  (≈ 0.42)
PC    delay_q Poisson tại ρ=0.90                  dự đoán 5.7 ms [3.0, 9.0]
      ← neo vào 99-gate-decision.md:110 poisson q mean = 5.725 ms
PC    R_PC = delay_q(0.95)/delay_q(0.60)          dự đoán 11.8   > 6
      ← neo vào MEASURED poisson R = 11.836, KHÔNG phải Kingman 12.667
FLOOR sàn nhiễu đường ống mới                     dự đoán 0.10–0.30 ms
```

Khoảng `[3.0, 9.0]` cho `PC` là cố ý rộng: đường ống khác Phase L (veth vs
Mininet, 1442 vs 1512 B). Khoảng hẹp hơn là tự lừa.

### 6.6. Gate và cây phán quyết

```text
| gate   | đại lượng                          | ngưỡng ký   |
|--------|------------------------------------|-------------|
| PC-1   | delay_q nhánh PC tại ρ=0.90        | >= 2.0 ms   | ← probe THẤY hàng đợi
| PC-2   | R_PC                                | >= 6.0      | ← probe thấy 1/(1−ρ)
| NC-1   | delay_q nhánh NC, mọi ρ             | <= 0.5 ms   |
| OVF-1  | loss nhánh OVF                      | >= 0.05     | ← bfifo thật sự chặn
| LOSS-1 | loss mọi ô MAIN                     | <= 0.005    | ★ MỚI (§3.4)
| F-1    | sàn nhiễu FLOOR                     | <= 0.40 ms  |
| Q-1    | R tại n=12                          | BÁO CÁO     |
| Q-2    | delay_q tại n=1                     | BÁO CÁO     |
| Q-3    | độ dốc theo n tại ρ=0.90            | BÁO CÁO     |

CÂY PHÁN QUYẾT — ký TRƯỚC, đọc theo thứ tự:

  PC-1 / PC-2 / NC-1 / OVF-1 / LOSS-1 FAIL  → `INVALID_INSTRUMENT`
      KHÔNG kết luận gì về S37. Một vòng chẩn đoán duy nhất, tham số cố định
      NGAY TẠI ĐÂY: tăng probe 20 → 50 pps, chạy lại MỘT lần.

  Sau khi năm gate trên PASS:
  Q-1 R <= 2.5   → `S37_CONFIRMED`
      ⟹ cưỡng chế tốc độ giết phương sai đến. L2.2 KHÔNG được chọn ①.
      ⟹ nếu PC-1 khớp Phase L trong [3,9] ms ⟹ ưu tiên ③.
  Q-1 R >= 6.0   → `S37_REFUTED` ⟹ kiến trúc A/C sống ở n đó, L2 rẻ đi ~1 tuần.
  2.5 < R < 6.0  → `INCONCLUSIVE` ⟹ mở rộng lưới ρ tới 0.98, chạy lại MỘT lần.

QUY TẮC DỪNG: một vòng chẩn đoán duy nhất cho cả lesson.
Chọn tham số sau khi thấy số là p-hacking.
```

★ **Ngưỡng `S37_CONFIRMED` hạ từ 3.0 xuống 2.5** vì `h2` đo được R = 3.716 với
loss 8.9% (§3.4). Ngưỡng 3.0 cũ nằm quá sát một cơ chế **ngẫu nhiên** đã biết.
`LOSS-1` là hàng rào chính; ngưỡng 2.5 là hàng rào thứ hai.

### 6.7. Đủ mẫu chưa?

Probe 20 pps × 60 s × 3 lượt = **3 600 mẫu/ô**. SD của răng cưa ≈ 6.2 ms tại
n=12, nên `SE = 0.10 ms`, và `SE(R) ≈ 0.041`. Mép gate `R = 2.5` cách dự đoán
1.583 **22 SE**. Dư sức.

Khoảng cách giữa các ô `n` tại ρ=0.90 nhỏ nhất là `3.752 − 0.773 = 2.98 ms`,
gấp **~30× SE**. Q-3 đọc được.

Thêm: khoảng probe trung bình 50 ms **lớn hơn** chu kỳ cụm `n·s/ρ = 25.6 ms`
tại n=12, nên các mẫu Poisson lấy pha gần như độc lập — không có aliasing.
Đây là lý do probe phải là **Poisson**, không phải CBR.

### 6.8. Ngân sách

```text
FLOOR   1 × 60 s                    =  1 phút
MAIN    4 n × 4 ρ × 3 lượt × 60 s   = 48 phút
NC      4 ρ × 1 × 60 s              =  4 phút
OVF     1 × 60 s                    =  1 phút
PC      4 ρ × 3 × 60 s              = 12 phút
────────────────────────────────────────────────
đo ≈ 66 phút + setup/teardown ≈ 1.5 giờ ⟹ vừa một ngày
```

---

## 7. Phán quyết Gate L2.0

| gate | nội dung | kết quả |
|---|---|---|
| L2.0-1 | Bảng đối chiếu đủ, mỗi dòng có `file:dòng` | ✅ §1, 11 trục |
| L2.0-2 | Mỗi khác biệt có dự đoán **có dấu** | ✅ §1; hai trục chưa suy được đã chuyển thành câu hỏi đo (`FLOOR`, `V-L2`) |
| L2.0-3 | Kiến trúc: A **LOẠI** có lý do định lượng; bộ lựa chọn L2.2 viết lại | ✅ §5 |
| L2.0-4 | Ba hằng số Phase L phân loại xong | ✅ §2, thêm phát hiện sàn 0.4646 ms không chuyển giao được |
| L2.0-5 | **S37** ghi thành giới hạn L2-L1, kèm dẫn xuất | ✅ §3, nhánh `c_a≈0` đã xác nhận bằng đo |
| L2.0-6 | **L2.0b** đề xuất với dự đoán ký trước | ✅ §6 |
| **L2.0-7** | ★ **MỚI**: lỗi trong ghi chú kế hoạch được ghi có mã và có sửa | ✅ F1–F6 tại §0 |

**Trạng thái: PASS.** Không có gate đo nào được ký ở đây.

## 8. Nợ chuyển tiếp

1. `S14` × `T_c`: chưa kiểm `σ ⊥ τ` khi cấu trúc nhanh và cưỡng chế chậm ở hai
   dải tần. Chặn việc ký lựa chọn ③.
2. Serialization trên veth: `99-gate-decision.md:50-51` nói Mininet không tính;
   chưa biết veth có tính không. Câu hỏi đo của `FLOOR`/`V-L2`.
3. Ứng viên ②a (điều biến `dt_fast ≈ 10 ms` + `σ_fast`) nằm trong cửa sổ tần
   số trống §4 nhưng **chưa đo, chưa kiểm, không được ký**.
4. `sigma_schedule` cho họ lưu lượng mới của ②a/②b phải đo lại từ đầu; sàn
   0.4646 ms của Phase L không chuyển giao.

# PRE-REGISTRATION — Phase D′ Lesson D.2 (Cell C + C′)

```text
Ngày ký                  2026-08-29
Trạng thái               SIGNED
Người ký                 Codex execution agent, theo chỉ thị của người dùng
Tag khóa                 phase-D-cellC-start
Quy tắc                  Không sửa bảng dự đoán sau tag; mọi đổi phải qua amendment
```

## 0. Bằng chứng đã có — khóa lại, không sửa sau khi chạy

Giai thừa 2×2 trên 28 cặp của `T1_corr_matrix_within_run` là phân tích hậu
kiểm (`POST_HOC_REANALYSIS_NOT_CONFIRMATORY`):

| Ô | n | Fisher r | Vai trò |
|---|---:|---:|---|
| chung host, cả hai low-σ/high-N | 2 | +0.6181 | ô phát hiện |
| chung host, cả hai core/high-σ | 4 | +0.0171 | bác H1 thuần |
| không chung host, cả hai low-σ/high-N | 4 | +0.0364 | bác H2/H3 |

Tỉ số ô then chốt / ô cao kế tiếp là 9.893×. Ô then chốt chỉ có hai cặp
`uA-uB` và `vC-vD`; đây là giới hạn D-L15.

Phân tích offered được làm trước khi ký theo đúng thứ tự D2-1:
`results/SMOKE/phase-D/factorial_offered.json`. Ô then chốt offered là
`+0.0048`, nên ủng hộ H6 ở mức hậu kiểm. Kết quả này đã được nhìn thấy và
không được gọi là bằng chứng xác nhận của các Cell C/C′ tương lai.

## 1. Giả thuyết cạnh tranh — phủ kín không gian diễn giải

- H1 endpoint-only: đã bị chống bởi `ac-ad`/`bc-bd` cùng host nhưng `r≈0.03`.
- H2 link-dynamics-only: đã bị chống bởi `uA-vC` cùng σ/τ nhưng khác host.
- H3 sampling/shared-transient: đã bị chống mô tả bởi cùng cặp `uA-vC`.
- H4 endpoint × low-σ: còn sống; cơ chế chưa nhận dạng (D-L13).
- H6 shared measurement noise: còn sống; `r≈Cov(εa,εb)/(σaσb)`.
- H0 không hiệu ứng: mọi ô gần 0 ở cả C và C′.

## 2. Thiết kế

Chỉ đổi `edge_sigma`; tất cả tham số còn lại giữ nguyên:

| Cell | core σ | edge σ | duration | seed | burn dự đoán |
|---|---:|---:|---:|---|---:|
| C | 0.10 | 0.10 | 240 s | 11, 12, 13 | 21.4 s |
| C′ | 0.10 | 0.05 | 400 s | 21, 22, 23 | 36 s |

Tham số chung: `rho_bar=0.925`, `kappa=2.5`, `size_min_kb=20`,
`log_dt=0.010 s`, `measured_window=0.200 s`, measurement mode `clean`.

Cell C giữ `tau_max=tau_ad=4.2769 s`; `55*tau_max=235.2 s`, làm tròn 240 s.
Cell C′ dự đoán `tau_edge=20.03*(0.03/0.05)^2=7.21 s`;
`55*tau_max≈397 s`, làm tròn 400 s.

Run dài đóng D-L14 giữ cấu hình hiện trạng (`core_sigma=0.10`,
`edge_sigma=0.03`), duration 1505 s, seed 31.

## 3. Bảng dự đoán ký trước — không sửa sau khi chạy

| Outcome | H1 | H4 ngưỡng | H6 luật σ⁻² | H0 |
|---|---:|---:|---:|---:|
| C `r(uA,uB)` | +.45…+.75 | −.10…+.15 | −.10…+.15 | ≈0 |
| C `r(vC,vD)` | +.45…+.75 | −.10…+.15 | −.10…+.15 | ≈0 |
| C `r(ac,ad)` [NC-C1] | ≈+.03 | ≈+.03 | ≈+.03 | ≈0 |
| C′ `r(uA,uB)` | +.45…+.75 | ≤+.08 hoặc ≥+.45 | +.18…+.28 | ≈0 |
| C′ `r(vC,vD)` | +.45…+.75 | ≤+.08 hoặc ≥+.45 | +.18…+.28 | ≈0 |

Chỉ Cell C′ tách H4 khỏi H6. Kết quả ngoài mọi khoảng được ghi
`UNRESOLVED`, mở limit mới và không bị ép vào một giả thuyết.

## 4. Estimator khóa

1. Tính ACF riêng từng link, từng rep; integral time scale cắt ở lag đầu có
   `ACF<=0`, không fit hàm mũ.
2. Với mỗi cặp, `tau_pair=max(tau_a,tau_b)` và bỏ ít nhất `5*tau_pair`.
3. Tính Pearson r riêng từng rep, không nối trace.
4. Gộp bằng `tanh(mean(atanh(clip(r_rep))))`.
5. `n_eff=(T_after_burn)/(2*tau_pair)`, không dùng row count.
6. In `r_rep`, pooled r, tau, burn, `n_eff`, metadata và infra flags.

Primary là `uA-uB`; `vC-vD` là bản nhân độc lập trong cùng run. `ac-ad`,
`bc-bd` và `uA-vC` là controls, không phải outcome để chọn sau khi nhìn số.

## 5. Đối chứng bắt buộc

- NC-C1: `r(ac,ad)` và `r(bc,bd)` trong cả hai cell vẫn thuộc
  `[-0.10,+0.15]`.
- NC-C2: `r(uA,vC)` trong cả hai cell vẫn thuộc `[-0.10,+0.15]`.
- PC-C1: edge `warm_start_active` khớp `round(rho^2/sigma^2)` trong sai số
  một flow: C khoảng 73–78, C′ khoảng 294–316.
- PC-C2: median tau edge đo bằng ACF giảm ít nhất 5× ở C và 2× ở C′ so với
  cấu hình 0.03; dự đoán lần lượt 11.1× và 2.8×.
- PC-C3: metadata ghi đúng σ, duration và seed.

## 6. Đo cơ chế bổ sung

Ba phép đo mong muốn để định vị cơ chế là `send_lag_series` trong
`FlowEngine.run`, `proc_cpu_ns` theo từng tiến trình FlowEngine và
`counter_read_dt` cho từng kênh. Nếu runner hiện tại chưa phát ra các trường
này, phải ghi giới hạn thay vì suy diễn gián tiếp rằng heap/CPU là cơ chế.

## 7. Validity gate

- Mọi primary/secondary/control pair có `n_eff>=25` ở cả ba rep và burn-in
  thực tế ít nhất `5*tau_pair`.
- Infra monitor phủ từng rep; bốn cờ CPU/swap/drop/clock đều false.
- NC-C1/NC-C2 và PC-C1/PC-C2/PC-C3 đạt.
- Không thiếu link, NaN correlation hay counter reset chưa xử lý.
- File này cùng tool offered và artifact offered đã commit; tag
  `phase-D-cellC-start` có trước timestamp raw Cell C/C′ đầu tiên.

Giả thuyết nào thắng không phải validity gate. Ngân sách tối đa một vòng;
nếu chưa phân giải thì ghi limit và chuyển Phase G.

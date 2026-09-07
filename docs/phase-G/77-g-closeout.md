# Phase G — đóng phạm vi đã kiểm chứng và bàn giao

Ngày: 2026-09-07 UTC. Trạng thái: **`CLOSED` trong phạm vi §3**, còn nợ
được bàn giao tại §6. Mốc: tag `phase-G-closed`.
Không phân xử dữ liệu mới, không nới gate, không đảo phán quyết lịch sử.
Không đồng nghĩa toàn bộ gate MASTER_PLAN v10 hoặc lưu trữ DOI đều PASS.

**Điều kiện chặn custody đã được giải quyết trước khi viết trạng thái CLOSED:**
clone HTTPS mới tại commit `b446d62dee33c4461e13e8343ca3b0dc65fa14e6` chạy
`verify_protected()` exit 0, mọi tag đã trích khớp origin; 120/120 tag
local và clone khớp object ID. Không chép dữ liệu từ workspace vào clone.
Bằng chứng máy: [g_closeout_clean_clone.json](../../results/SMOKE/phase-G2/g_closeout_clean_clone.json).
Kiểm lại bản closeout đã push là bước cuối, có receipt riêng sau tag.

## 1. Câu hỏi được giao và câu trả lời

RQ-G: thiết kế sinh tải có điều khiển được sigma, tau, c_a, omega,
và cấu trúc ghép nối nào đã được chứng minh trên testbed?

- **Sigma/tau:** các gate round-trip và độ dốc điểm PASS trên 5 ô, 9 lượt,
  8 link kernel veth/HTB. Độ dốc log tau theo log sigma −0.04818686,
  độ dốc log sigma-ratio theo log tau +0.01372423. Không diễn giải thành
  độc lập thống kê chính xác hoặc tương đương đã được chứng minh bằng CI.
- **Omega:** thu hồi trên 5 mức với sai lệch điểm lớn nhất 0.02713834.
  G5c hợp lệ: POWER_AXIS_HOLDS / REDUCIBLE_TO_EFFECTIVE_SIGMA theo surrogate
  đo được; G-A020 rút chiều quét trong phạm vi estimand hiện tại.
- **c_a:** chưa có sweep đo vật lý tương ứng; chuyển yêu cầu sang L2/20R2.
- **Coupling:** là covariance được thiết kế ở target rate rồi truyền qua
  shaping/đường đo. Không phải chứng minh bảo toàn byte xuyên đường nhiều hop.

## 2. Đối chiếu gate v10 với bằng chứng

MASTER_PLAN_v10 không có trong checkout. Cột yêu cầu dưới đây lấy từ bản
review người dùng cung cấp; đây là crosswalk closeout, không tiền đăng ký mới.
Không nhập “8/10 PASS mạnh” khi các đại lượng chưa tương ứng với yêu cầu.

| Gate | Yêu cầu theo review | Kết quả và giới hạn | Nguồn |
|---|---|---|---|
| G-1 | Round-trip sigma/tau ±20%; tau độc lập sigma | **PASS theo thống kê đã ký**: sai số trung vị ô tau tối đa 4.941%, sigma 3.819%; slope điểm qua gate. CI RT-O1 [-0.24129,0.18402] không nằm trong ±0.10; không chứng minh equivalence | [66](66-g3b-results.md), [66a](66a-g3b-uncertainty-addendum.md) |
| G-2 | Không còn phụ thuộc rho²/sigma² của tầng luồng cũ | **Đáp ứng về cấu trúc trong bộ sinh hiện tại**: physical_trace dùng AR target trực tiếp, không M/G/∞. Không nói mọi đại lượng downstream đều không thể chứa tỉ số đó | [58](58-prereg-g2-kill-test.md), tools/g3_dryrun.py::physical_trace |
| G-3 | Sai số omega <0.10 ở ≥4 điểm | **PASS trên 5 mức**: max abs error 0.02713834; doc64 giữ đầy đủ readjudication P7 | [64](64-g3a-omega-positive-control-results.md) |
| G-4 | r(uA,uB)<0.15 tại omega=0 | **PASS thống kê gộp**: max abs r trên 28 cặp=0.0705, dưới trung vị null đã sửa 0.0796. Max từng replicate đến 0.1808, nên không suy PASS cho mọi link-run | [59](59-amendment-g2-harness-defect-and-null.md), [60](60-kill-test-results.md) |
| G-5 | PPS từng host bất biến qua omega | **PARTIAL**: sigma_l bất biến trong covariance thiết kế; sink tracking error ≤4.60366e-05. Đây không phải kiểm định PPS từng host giữa các mức omega; chuyển phần chưa đo sang bàn giao | [64](64-g3a-omega-positive-control-results.md), [76](76-amendment-G-A020-omega-reduction.md) |
| G-6 | Lag ≤1 mẫu ở ≥95% link-run | **PASS diagnostic đã đo**: 104/104 chuỗi aligned tại lag0; không suy kiểm clock độc lập trên nhiều host/NIC | [68](68-measurement-path-cert-v2.md) |
| G-7 | Censoring <0.05 | **PASS cho target clipping đã ký**: G3a ≤0.00101, G3b ≤0.00557927; đều dưới 0.01. Không gộp thành chứng minh mọi dạng queue censoring | [64](64-g3a-omega-positive-control-results.md), [66](66-g3b-results.md) |
| G-8 | T_run≥50*tau | **PASS**: 205*tau ở các run G3a/G3b; tau30 chạy 6150 s | [65](65-prereg-g3b-sigma-tau-roundtrip.md), [66](66-g3b-results.md) |
| G-9 | Nhánh P đo k_phys, so ±20% | **RÚT TRONG PHẠM VI G-A020**, không phải PASS thực nghiệm: k_topo và covariance mô hình không thay một thí nghiệm bảo toàn byte vật lý | [76](76-amendment-G-A020-omega-reduction.md) |
| G-10 | Artifact phủ toàn Omega_ctrl | **PARTIAL**: inventory của miền đã đo có JSON và hash; chưa phủ rho_bar/c_a/dt và toàn lưới tích | §3, g_closeout_scope.json |
| G-11 | Cửa thoát khi G-1/G-4 FAIL | **Không kích hoạt** theo gate đã ký; không xóa các nợ độc lập còn lại | [60](60-kill-test-results.md), [66](66-g3b-results.md) |

## 3. Phạm vi chứng nhận và phần chưa đo

**Các ô G3b tại omega=0, dt=0.1 s, rho_bar≈0.857:**

| tau (s) | sigma_ref tại uA | Lượt | T_run/lượt (s) | Sai số tau trung vị ô | Sai số sigma trung vị ô |
|---:|---:|---:|---:|---:|---:|
| 2 | 0.028 | 2 | 410 | -0.770% | +0.310% |
| 2 | 0.045 | 2 | 410 | -4.941% | -3.819% |
| 5 | 0.028 | 2 | 1025 | -0.837% | +0.453% |
| 5 | 0.045 | 2 | 1025 | -1.112% | -1.510% |
| 30 | 0.036 | 1 | 6150 | -3.426% | +2.371% |

Ngoài ra G3a quét omega={0,.25,.5,.75,1} tại tau=2 s, dt=.1,
3 lượt/mức, 410 s/lượt. Đây **không** là quét tích 5 ô sigma/tau × 5 omega.
G4 tái phân tích 72 chuỗi G3b và 32 chuỗi G2, không chạy mạng mới;
certificate của G4 không tự chứng nhận residual model ở omega>0.

Chưa quét: dt khác .1, rho_bar khác cấu hình đã đo, c_a theo hop,
tau={1,3,10} trong grid round-trip G3b này, topology/host/NIC khác.
Bảng dt của certificate là `UNVALIDATED_MODEL_PREDICTION`, không phải số đo.
Các điểm chưa quét không được chứng nhận chỉ bằng nội suy.

Tau=30 đã chạy 6150 s ≈1.708 giờ **một lượt**, cho thấy run dài này khả thi
trên testbed đã dùng; không chứng minh mọi tau khác đều khả thi. Ngân sách
máy quan trọng nhưng không thay các ràng buộc telemetry, clipping và precision.
G0.5 cần dùng bằng chứng này khi lập ngân sách; không có MASTER_PLAN để sửa tại chỗ.

[Inventory Omega đã đo](../../results/SMOKE/phase-G2/g_closeout_scope.json) giữ nhãn
`SCOPE_INVENTORY_NOT_NEW_MEASUREMENT`; không tự nâng G-10 lên PASS.

## 4. Cơ chế: cái gì bị bác bỏ, cái gì còn dùng được

| Đại lượng | Userspace pacing G.3 | Kernel shaping G′ |
|---|---|---|
| r chéo link được báo cáo | 0.9999864422 | 0.0705, gộp 28 cặp ở omega0 |
| Mô hình tác động stall | Sai số cộng cùng dấu vào từng link | Lệch thời gian tác động qua biến thiên target từng link |
| Quiesce host | EMIT-3 vẫn thất bại sau khi p_stall_1ms giảm 26 lần | Host không quiesce trong các run đã báo cáo |
| Chi phí sai số còn lại | Common-mode áp đảo trong cấu hình pacing đã ký | Nugget không biến mất; KILL-3 FAIL, GO*; mô hình sau bổ sung MA(1) và quantization |

Nguồn: [54](54-limits-G-L98.md), [60](60-kill-test-results.md),
[61](61-amendment-G-A019-nugget-colour-and-sf-retirement.md), [68](68-measurement-path-cert-v2.md).
So sánh này tổng hợp các nghiên cứu có cấu hình khác nhau, không phải paired
A/B cùng dữ liệu. Giá trị 0.71–0.75 tại stall=5 ms là tính toán pacing của
G-L98 tại dt=.2; không đặt cạnh một số “~1e-3 đo được” của shaping như cùng
một estimand. KILL-3 từng cho thấy predictor chỉ tính phase shift bỏ sót nugget.

## 5. Sổ giới hạn được bàn giao

| Mã | Cách đọc khi closeout | Nguồn |
|---|---|---|
| G-L98 | Giới hạn pacing userspace dưới cấu hình/host đã ký; không là bất khả thi phổ quát | doc54 |
| G-L100 | Phân rã nugget và bias claim A có điều kiện; max r đo không là cận population | doc60/61 |
| G-L102 | Predictor phải tính mọi hạng nugget đã biết; giữ KILL-3 FAIL và GO* | doc60 |
| G-L103 | Residual phù hợp MA(1), ACF1≈−.5; đổi lag fit theo amendment đã ký | doc61/68 |
| G-L107 | Gate điểm không chứng minh equivalence; bất định và pooling phải đi cùng kết quả | doc66a |
| G-L109 | Cấu trúc coupling trong tập quan trọng; không chỉ là số K | doc70a |
| G-L110 | Chẩn đoán hai kênh thang/xếp hạng; không tự coi rank exchangeability là chứng minh bất biến phân phối khi omega đổi | doc70a, giới hạn doc76 §3 |
| G-L111 | Gate đơn điệu phải ghi chiều; P-3 lịch sử vẫn VOID | doc73/74/75 |
| G-L112 | Đọc cùng đính chính dấu: G5b L_scale=0.10706250, L_total=0.10177083, R=+0.00529167; câu “94.8%” không còn dùng như phân rã cộng | doc75 §4 |
| G-L113 | Quy gọn omega có điều kiện cấu trúc claim/model; proxy SD không tái chứng nhận qhat | doc76 §3–4 |
| G-L114 | Thiếu tag và file CITED_RAW làm đứt kiểm chứng từ clone; sửa bằng phân phối đúng tag/hash và kiểm clone thực | §5.1, doc76a |

### 5.1. G-L114 — remote tags và dependency của certificate

Tại lần kiểm 2026-09-07 có 120 tag local, 113 tag remote: thiếu **7**, gồm
5 tag được review nêu và thêm cert-v2/g5c-complete. Không phải 209 tag tên
riêng biệt; phải loại dòng peeled `^{}`. Không phát hiện tag cùng tên khác ID.
Clone thứ nhất tái hiện `invalid object name 'phase-G2-g5-prereg'`.

Sau push đủ tag, clone thứ hai vẫn thiếu g3b_sigma_tau_series.npz.
File 12,420,400 byte được phân loại CITED_RAW, cho phép phân phối Git bằng
ngoại lệ một file ràng buộc với hash certificate, giữ nguyên dữ liệu gốc.
Không đổi hàm verify_protected, nguồn Phase22 hay certificate. Quyết định
đầy đủ ở [76a](76a-custody-portability-repair.md); K10/DOI vẫn chưa được trả.

Clone thứ ba lấy hoàn toàn từ origin tại `b446d62d`:
verify_protected PASS, 120/120 tag khớp, không chép file ngoài clone.
Đây là điều kiện đã hoàn thành **trước** khi đóng phase.
Chuỗi kiểm thất bại/thành công được giữ trong hai JSON custody/clone §7.

Kiểm soát mới: `tools/check_phase_g_custody.py` mặc định kiểm backup local
và tag live trên origin; `--tags-only` dùng cho clone sạch. Missing tag,
khác object ID, origin không đọc được hoặc scan rỗng đều không PASS.
`--local-only`/API evaluate chỉ kiểm backup offline và ghi rõ phạm vi.
Kiểm tag không thay kiểm file; verify_protected vẫn kiểm từng hash evidence.
Test cuối **80 PASS trong 1.72 s**, log g_closeout_tests.log.

## 6. Nợ chuyển ra khỏi Phase G

| Nợ | Việc chưa được thiết lập | Bàn giao / điều kiện xử lý |
|---|---|---|
| D1 | Coupling do bảo toàn byte xuyên multi-hop | Threats to Validity; thiết kế riêng nếu claim sau cần |
| D2 | c_a theo hop chưa quét | L2/20R2 phải chốt estimand và instrumentation trước khi chạy |
| D3 | dt/rho_bar/topology khác | Kiểm transfer/đo lại đúng cấu hình trước khi dùng certificate |
| D4 | Va chạm namespace G-L90/G-L96 | Amendment phân xử riêng; không sửa các doc đã ký |
| D5 | kappa_time=5 và PC doc42 | Giữ nguyên; amendment riêng mới được rút |
| D6 | Version DOI/Zenodo K10 | Còn BLOCKED theo hồ sơ; GitHub/backup không là DOI |
| D7 | PPS từng host bất biến qua omega (G-5) | Chưa đủ bằng chứng trực tiếp; phase sau phải đo nếu còn yêu cầu này |
| D8 | Lưới đầy đủ Omega_ctrl (G-10) | L2/20R2 ký grid, fixed omega, điều kiện G-L113 và budget |

**Xung đột nhánh P trong review được giải quyết bằng phạm vi:** G-A020 chỉ
rút nhiệm vụ P phục vụ trục omega dư thừa. Nếu L2.2 cần đường multi-hop để
đo c_a thì đó là một yêu cầu khác, chưa được hủy bởi G-A020 và chưa được
chứng minh bằng generator C. Không gán c_a đã đo hoặc tự xóa nhánh đó.
Hợp đồng L2 phải quyết định instrumentation phù hợp trước thiết kế chiến dịch.

## 7. Artifact và SHA256

Các artifact nghiên cứu gốc giữ nguyên. Receipt kiểm remote/clone là kiểm
custody mới, không phải thí nghiệm sinh dữ liệu mới. JSON scope lưu cả danh
sách nguồn và hash; file raw G3b hiện tải được bằng clone Git.

| Artifact | SHA256 |
|---|---|
| [g2_kill_test.json](../../results/SMOKE/phase-G2/g2_kill_test.json) | `50a30667e33a2c076e731752b84c0d42a4ed608e3e05eea51c858b459e2ec6e7` |
| [g2_kill_null.json](../../results/SMOKE/phase-G2/g2_kill_null.json) | `21a39f3f46d1c8ad861813a66b548c1d87cb9e9f753197e42114412c43823754` |
| [g2_kill_series.npz](../../results/SMOKE/phase-G2/g2_kill_series.npz) | `64279ffe1610858383003587ef53a64eba2096f7c8083d8f7b8e8c00b48f986b` |
| [g3a_omega_sweep.json](../../results/SMOKE/phase-G2/g3a_omega_sweep.json) | `947a987f33889201034d86407c4efe78a8a9f05fe4ba5e42298ce4237b3ebe0e` |
| [g3a_readjudicated.json](../../results/SMOKE/phase-G2/g3a_readjudicated.json) | `351049ee17185cd2ac6909767316821b8efa9713a572716122655b1767b59757` |
| [g3b_sigma_tau.json](../../results/SMOKE/phase-G2/g3b_sigma_tau.json) | `e71d61c1bdef6c3b58c6c2b3d640847e5797e8e446169cb53f40ddf1318baf08` |
| [g3b_sigma_tau_series.npz](../../results/SMOKE/phase-G2/g3b_sigma_tau_series.npz) | `cfb519b7b46bdc95e186d4c96c0149a1127929ad8fe112c123b2b5cccb8eec13` |
| [g3b_orthogonality_audit.json](../../results/SMOKE/phase-G2/g3b_orthogonality_audit.json) | `0947ecd886ac62c488a71c52bda22434761dc6ea562c0d359eb4fd52d0e667ca` |
| [g4_nugget_model.json](../../results/SMOKE/phase-G2/g4_nugget_model.json) | `e5285b4319afe4b51a55b876630c009b16f5bb720a5dd58564d6d747477c9a9e` |
| [g5_estimand_transfer.json](../../results/SMOKE/phase-G2/g5_estimand_transfer.json) | `8d6b5ec7820c8deff1ac4151831a3627013972a2814b2c4dda27f83960add9b7` |
| [g5a_mechanism_audit.json](../../results/SMOKE/phase-G2/g5a_mechanism_audit.json) | `1c699b185b363bb95ecd1775a76a11d66aee04b98c8174a39801e56ae990d4e1` |
| [g5b_power_axis.json](../../results/SMOKE/phase-G2/g5b_power_axis.json) | `62239b1f5cef6e276e82854cc691e0ce2e0cfd5eb38f4adab68001b7dbb38600` |
| [g5c_monotone.json](../../results/SMOKE/phase-G2/g5c_monotone.json) | `10e44f07dd57f5bdbaad5ce7f83b878334dc1b47ea18cc30b51773cf24d75d3c` |
| [g6_sigma_eff.json](../../results/SMOKE/phase-G2/g6_sigma_eff.json) | `3ad56f7ac9351ffc3dcec6fa1b5e8af03a451d94839e9812d4f1e76a9c957977` |
| [g_closeout_custody_repair.json](../../results/SMOKE/phase-G2/g_closeout_custody_repair.json) | `bf1b33168f03d2f918803a0a000c50991219bfa8c790a43b9613573c711098f2` |
| [g_closeout_clean_clone.json](../../results/SMOKE/phase-G2/g_closeout_clean_clone.json) | `af3cd00f546f28420af02550cfa48e23b814ef5efe843ded9acc4ef0808c3f85` |
| [g3b_series_git_custody.json](../../results/SMOKE/phase-G2/g3b_series_git_custody.json) | `b7f492d8d4b45f6ea5615052c1a71cf5a5d97a6a2eef2617516ce3ea0eafbee6` |
| [g_closeout_tests.log](../../results/SMOKE/phase-G2/g_closeout_tests.log) | `df929fd212517bd9c70b3b75176d10f435455f67b8c41ab7924272f7b375021d` |
| [measurement_path_cert_v2.json](../../results/LIVE/phase-G2/measurement_path_cert_v2.json) | `6829990d257814e3f26e287cfa861de1121c563f2ac5814bd6d7d35da9f33a0b` |
| [g_closeout_scope.json](../../results/SMOKE/phase-G2/g_closeout_scope.json) | `b73d599683081de24ae6aae2a9a2dc7fb4adea21a13ada89ce621f7377598a24` |

Không mọi archive RAW/checkpoint của toàn Phase G đều đã đưa vào Git; receipt
clone chứng minh đúng chuỗi dependency của verify_protected và artifact trích
ở đây. Dữ liệu ngoài Git vẫn theo manifest/backup và còn nợ DOI.

## 8. Điều kiện mở lại phạm vi

Mở lại phần liên quan khi chiến dịch cần dt/rho_bar/topology/datapath khác,
G-L113 kích hoạt do đổi claim/ranking/model, cần coupling vật lý xuyên hop,
hoặc có evidence mới làm hỏng một gate/certificate/custody check.
Tính lại covariance chỉ là bước sàng lọc, không phải điều kiện đủ để đóng
lại G-L113. Không cần đợi proxy “không quy giản” mới nhận ra phạm vi đã đổi.
Không mở lại chỉ để lấy số đẹp hơn. Nợ DOI/namespace được xử lý ở luồng
custody/documentation riêng, không mặc nhiên chạy lại thí nghiệm.

## 9. Hợp đồng bàn giao L2 / T2′ — năm đầu vào

1. **Bộ sinh đã thử:** `mininet/rate_controller.py`, `blast_source.py`,
   `byte_sampler.py`, target `tools/g3_dryrun.py::physical_trace` và covariance
   `tools/g2_topology.py`. Kernel enforcement được đo trên veth/HTB cùng host,
   chưa bảo đảm NIC/host khác. Giữ kiểm backlog, drops, tracking và alignment.
2. **Đường đo:** `measurement_path_cert_v2.json`,
   `v=κ*(8L/(C*dt))²/12=(8L/(C*dt))²/6`, L=1442 B, κ=2 cố định.
   Không nhân κ thêm lần nữa. Dùng trong phạm vi certificate, không bỏ
   calibration/validation cho cấu hình telemetry mới chưa được kiểm.
3. **Trục và ngân sách:** bốn chiều dự kiến `(rho_bar,sigma,tau,c_a)` khi
   G-A020/G-L113 áp dụng; omega vẫn có giá trị trong mô hình/metadata.
   `sigma_eff_proxy` là nhãn chẩn đoán, không tự thay sigma generator.
   Tau={2,5,30} có số đo; round-trip dùng T_run=205*tau.
   Chiến dịch vẫn tuân T=200*max(tau_p,tau_g), kappa_time=5 của doc42;
   closeout không thay quy tắc đó bằng 205*tau một cách toàn cục.
4. **Khả thi:** giữ headroom/quantization, độ phân giải và độ dài theo tau,
   censoring/clipping cùng kiểm vận hành. Chỉ bỏ nhiệm vụ tối ưu omega_max
   trùng lặp trong G-A020; miền input `0<=omega<=1` vẫn bắt buộc.
   Review nêu tau>=5*dt nhưng doc58 dùng dt<=tau/20: không tự nới từ 20
   xuống 5 qua closeout. Không có implementation realizability_gate mới
   được tạo hay sửa ở đây; L2 phải ký đúng protocol nó dùng.
5. **Câu Threats có thể dùng:** “Coupling is realised as a designed covariance
   in the rate process and validated through kernel shaping and the measurement
   path on the tested veth/HTB configuration; it is not produced by byte
   conservation over a multi-hop path.”

Câu proxy trong review cũng cần giữ đúng đại lượng: sai lệch **0.4384%** là
so mean per-slot qhat ratio; với max-score qhat là **1.0528%**.
Sự gần nhau không chặn riêng độ lớn kênh ranking khi các cơ chế có thể bù nhau.
Không dùng câu “agreement bounds the ranking channel” như một kết quả đã chứng minh.

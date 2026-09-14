# AMENDMENT-20R2-A2 — chuyển gate 20R2-7 sang 21R2

Ngày 2026-09-14, triển khai theo hướng dẫn 20R2.9-A của người dùng. Đây là văn bản bổ sung; không sửa prereg hay artifact đã đóng và không đóng nợ bằng việc chuyển tên phase.

Gate 20R2-7 có nhãn **DEFERRED**. Phase nhận: **21R2**. Nợ **20R2-D4** là phép đo N3/N4 trên lưới 20R2, được ghi ở prereg §13.6, §13.8 và §13.9. Kết quả baseline T2 không được chép làm kết quả 20R2. Nợ này vẫn MỞ.

Điều kiện đóng ở 21R2:

1. Tiền đăng ký lưới, trục SLA/AoI, ngân sách và mapping tham số trước khi chạy chiến dịch bổ sung N3/N4; có producer ghi validity và inputs_sha256 tại nguồn.
2. Đo N3 (ar1_rms_total_fit_within_2pct) và N4 (A, c, em độc lập với τ) trên điều kiện 20R2 bằng chiến dịch thích hợp, giữ đủ raw, hash, lệnh và phiên bản mã để tái lập.
3. Báo PASS/FAIL từng tiêu chí và phạm vi từng ô; không yêu cầu dữ liệu phải thuận lợi mới được đóng việc đo. Xử lý ảnh hưởng của FAIL tới kết luận liên quan.
4. Công bố phán quyết bổ sung dẫn về gate 20R2-7, đối chiếu D4 và cập nhật sổ nợ có kiểm tra máy. Đến lúc đó 20R2-7 vẫn DEFERRED.

D11 (thiếu chuỗi ghim/trục tại nguồn) cũng có phần việc nhận ở 21R2 như [sổ gate](99b-gate-ledger.md), nhưng là nợ riêng; hoàn tất N3/N4 không tự đóng D11. Các phép đo độ nhạy 20R2.9-B không thuộc lần triển khai A này.

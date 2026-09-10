# 20R2.5 — Runbook chiến dịch

Tài liệu **thao tác**. Lý do và bằng chứng nằm ở `00-preregistration.md` §16.

⚠️ Không bước nào ở đây được chạy trước khi §11 được ký, commit, tag và **push**.
`tools.20r2_5_run` tự chặn, nhưng cái chặn là lưới an toàn, không phải quy trình.

---

## 0. Trạng thái hiện tại

```text
DA XONG (truoc ky)   sua P2/P4/P5 . do lai se pilot tren truc exogenous .
                     bang chap nhan cap nhat . 03-run-plan.json da sinh .
                     axis_audit sinh lai . .gitignore mo ngoai le co pham vi
CHUA LAM             §11 chua ky  <- NGUOI KY lam, khong cong cu nao lam ho
                     chien dich chua chay . ve sinh chua chay
```

---

## 1. Ký (người ký làm)

Điền `Nguoi ky`, `Ngay`, `Commit sha`, tick 6 ô xác nhận trong §11. Ô mới:

- ngân sách **74,53 phút** (không phải 29,4 — con số cũ là A7 kế thừa)
- băng **đã sửa**: `C_upper = 0,406418` (bản cũ 0,409554 đo trên trục sai)
- kế hoạch `03-run-plan.json` sha256 `a984020e104bb13b4743be5aca2d5e0eabf0d49558f53cc5f0d70c6ce4fdf662`

```bash
git add -A
git commit -m "20R2 prereg: ky gate 0-3 + §16"
git tag -a phase-20R2-prereg-signed -m "20R2 prereg signed"
git push origin main && git push origin phase-20R2-prereg-signed
git ls-remote --tags origin | grep prereg-signed      # BANG CHUNG, khong bo qua
```

Ký trên máy mình mà chưa push thì với mọi người khác **vẫn là chưa ký** —
guard kiểm cả remote vì lý do đó.

---

## 2. Chạy

⚠️ **Chạy trên ĐÚNG máy đã sinh `cpu_pilot.json`.** Pilot đã đo chênh lệch giữa
hai máy tới **+20%**, tức hai phần ba biên ±30% của H9. Chạy máy khác thì H9 có
thể trượt vì **máy**, không vì thiết kế. Trượt đó chỉ là hạng BUDGET (không làm
kết quả sai) nhưng sẽ phải giải thích.

⚠️ **Không để máy ngủ.** `tmux` giữ phiên khi rớt SSH nhưng **không** ngăn
suspend. **Không commit giữa chừng** — env fingerprint mang `git_commit` nên
resume sẽ dừng (đúng thiết kế).

⚠️ **Không mở parquet.** Chỉ nhìn dòng `ok` và số giây. Một số giây bất thường
ở điểm canh (τ=3 lẽ ra ~13 s) là tín hiệu **máy bị tải**, không phải tín hiệu
khoa học.

```bash
python -m tools.20r2_5_run --dry-run     # xem 167 lenh, khong chay gi
python -m tools.20r2_5_run               # ~75-97 phut
```

Guard chặn trước khi tiêu một giây CPU nào nếu: chưa có tag (local **hoặc**
remote), cây bẩn ngoài phần chiến dịch sở hữu, hoặc **kế hoạch/dụng cụ đổi sau
khi ký**.

Runner ghi `docs/phase-20R2/04-campaign-log.jsonl` (sổ cái, append + fsync) và
kẹp chiến dịch giữa hai lần đối chứng twin-hoàn-hảo (PRE và POST).

### Khi có sự cố

| Sự cố | Làm gì |
|---|---|
| `rc ≠ 0` | Runner **tự dừng**. Chẩn đoán rồi chạy lại — nó resume. Không chạy tiếp qua một lỗi chưa rõ |
| Ctrl-C, mất điện | Chạy lại. File **mồ côi** (có file, không dòng sổ) bị xoá và chạy lại |
| `file tren dia KHAC so cai` | **DỪNG.** Bằng chứng đã bị sửa. Không tự "sửa lại cho khớp" |
| `moi truong/commit KHAC phien truoc` | **DỪNG.** Một chiến dịch chỉ một commit, một môi trường |
| `twin-hoan-hao (pre): FAIL` | **DỪNG** — và đây là **tin tốt**: đối chứng vừa làm đúng việc của nó |

**Ba loại sự cố, ba đường sửa khác nhau:**

```text
HA TANG   disk full, OOM, mat dien, Ctrl-C
          -> sua ha tang, chay lai lenh. Resume tu xu ly file mo coi.
MA        traceback trong stderr_tail cua so cai
          -> KHONG sua tai cho. Amendment -> tag MOI (vd ...-signed-a1)
             -> doi TAG trong runner (thuoc ban ky moi) -> chay lai TOAN BO.
DUNG CU   twin-hoan-hao (pre) FAIL  -> xu nhu loai MA.
```

⚠️ Với hai loại sau, **ĐỪNG XOÁ sổ cái cũ**. Đổi tên thành
`04-campaign-log.aborted-1.jsonl` và **commit nó**. Một chiến dịch bị huỷ có
kiểm soát **là dữ liệu** (NT 21) — và nó chứng minh bạn không chạy lại cho tới
khi số "đẹp".

Một commit chỉ sửa tài liệu giữa hai phiên resume **cũng** làm runner dừng. Đó
là **đúng**: sổ cái ghi `git_commit` cho từng lệnh, và hygiene H2 đòi toàn
chiến dịch nằm trên một commit. Muốn resume thì `git stash`/quay về đúng commit
đã ký, hoặc chạy lại toàn bộ.

---

## 3. Vệ sinh — TRƯỚC khi mở bất kỳ kết quả nào

```bash
python -m tools.20r2_5_hygiene --out docs/phase-20R2/05-hygiene.json
```

```text
H1  du 167 lenh VA khop tung truong cua ke hoach     VALIDITY
H2  mot commit, mot moi truong, guard khong bi lach,
    VA signed_tag_commit == git_commit (tag khong bi doi)  VALIDITY
H3  sha tren dia khop so cai                         VALIDITY
H4  twin-hoan-hao PASS truoc lenh dau, sau lenh cuoi VALIDITY
H5  canary span = 0 VA cac lenh khac ra sha KHAC nhau VALIDITY
H6  CRN: hai nhanh trung tung bit tai z chung (dong D8) VALIDITY
H7  validity doc TAI NGUON, z_grid_id SUY RA          VALIDITY
H8  realizability luot 2 tren so DO DUOC              VALIDITY
H9  CPU trong ngan sach 74,53 phut +-30%              BUDGET  <- khong phan quyet validity
```

`H5` cần đối chứng âm của chính nó: nếu **mọi** lệnh ra cùng sha thì span = 0
vì một lý do tầm thường (ví dụ tham số seed bị bỏ qua), không phải vì máy ổn.

**Nếu FAIL:** vẫn **KHÔNG mở kết quả**. Phần `checks` của `05-hygiene.json`
không chứa một giá trị kết quả nào, nên đọc được mà **không phá mù**. Chẩn đoán
theo H nào đỏ — mỗi loại một đường sửa:

```text
H2 do -> tag BI DOI, hoac resume tren commit / moi truong khac
H5 do -> moi truong KHONG tat dinh
H6 do -> dispatch luoi z RO RI o mot tau ma NEO B chua tung kiem
H8 do -> mot o cu the khong dat realizability luot 2
```

Sửa **nguyên nhân**, không diễn giải. Nếu nguyên nhân là mã thì cần amendment +
tag mới + chạy lại **toàn bộ**. Không bao giờ "sửa dữ liệu".

**Nếu VALIDITY PASS:** commit nhân chứng, push, rồi gắn tag
`phase-20R2-campaign-hygiene`.

---

## 4. Nhân chứng

```bash
git add -A
git commit -m "20R2.5: chien dich 167 lenh + ve sinh"
```

Chỉ **sau** commit này mới được mở 20R2.6.

Vệ sinh phải được **commit** trước, không chỉ **chạy** trước: nếu vệ sinh và
kết quả cùng xuất hiện, thì khi kết quả xấu ta bị cám dỗ đi tìm một lỗi vệ
sinh để biện minh, còn khi kết quả đẹp ta bỏ qua lỗi vệ sinh. Commit trước
biến nó thành **nhân chứng có dấu thời gian** — đây là NT 56, tách gate
validity khỏi gate outcome, và là blind analysis của vật lý hạt.

---

## 5. Để dành cho 20R2.6

- Dự đoán ký tại `z = 0,365`; lưới có `0,366`. Độ dời Sheppard tương đối
  ~0,10–0,14%, không đáng kể so với băng ≥ 2,73%, nhưng **phải khai**.
- `cbr` = `DOWNGRADED_TO_DIAGNOSTIC`, báo cáo **riêng**, không gộp vào 8 ô gate.
- Đối chứng ×4 tại τ=28 vẫn **ngược hướng** (tỉ số 0,94) trên trục đã sửa —
  đó là lý do băng dùng luật gộp thay vì se từng ô.

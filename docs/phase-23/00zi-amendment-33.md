# AMENDMENT 23-33 -- Dinh chinh pham vi H2 cua Amendment 23-32

Ngay: 2026-08-21
Trang thai: **SAU KHI COMMIT AMENDMENT 23-32, NHUNG VAN TRUOC KHI VIET CODE
VA TRUOC KHI CHAY PHEP DO.**

Amendment 23-32 doc nham danh sach record tu mot output terminal bi cat va
ghi rang `residual_cascade.json` khong co `(mode=h2, channel=loss)`. Kiem tra
schema bang may sau khi commit cho thay file co du bon record:

```text
poisson  loss      per_path  -0.009521786236599921
poisson  delay_ms  per_path  -0.7463995189989756
h2       loss      per_path  -0.009351404492577604
h2       delay_ms  per_path  -0.44924137696913036
```

Day la loi cua nguoi ky khi doc output bi truncate, khong phai thay doi cua
artifact. Khong sua nguoc Amendment 23-32; dinh chinh bang file moi de lich su
quyet dinh van kiem toan duoc.

---

## 1. Sua pham vi truoc khi chay

`h2@0.700` la **APPLICABLE** bang chinh record H2 loss o tren. Ca ba cell khoa
cho lenh chay:

```text
poisson@0.925 -> record poisson/loss/per_path
poisson@0.850 -> record poisson/loss/per_path
h2@0.700      -> record h2/loss/per_path
```

Moi artifact phai ghi mode/channel/level/point/CI90 cua record no thuc su
dung. Test phai lam do neu mode cua cell va mode cua residual khac nhau.

---

## 2. Anh huong den bang du doan

M-23 mo rong dung nhu cau chu ban dau cua no: `H_path = 0` tai ca ba endpoint
tren **ca ba cell**.

M-24, M-25, M-26 van chi cham tren cell chinh `poisson@0.925`; khong doi dai,
khong them diem prediction-hit. Ket qua H2 va `poisson@0.850` ngoai M-23 la
[MO TA] / kiem tra kha nang lap lai qua cell.

Ba do lon endpoint van giu theo truc chung cua Lesson 23.7 de so sanh duoc
voi artifact cu:

```text
r_star     = -0.008868196569470351
point      = point cua CHINH residual record tung mode
ci90_worst = endpoint am co |r| lon nhat cua CHINH record tung mode
```

Voi Poisson, ba gia tri khong doi. Voi H2:

```text
r_star     = -0.008868196569470351
point      = -0.009351404492577604
ci90_worst = -0.010061922706130285
```

Quy tac record-specific cho `point` va `ci90_worst` thay the cau mo ho cua
Amendment 23-32 tren H2; no duoc khoa truoc khi code ton tai va truoc khi bat
ky a* nao duoc tai sinh.

---

## 3. Mốc prereg

Tag `lesson-23.7bis-pre-amd32` giu commit Amendment 32 co loi de doc. Tag
`lesson-23.7bis-pre` phai tro vao commit Amendment 33 nay va la mốc cuoi truoc
code/measurement.


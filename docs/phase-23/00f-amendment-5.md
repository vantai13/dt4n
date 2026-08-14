# AMENDMENT 23-5 -- Sticky diagnostics

Ngay: 2026-08-14

Ly do: F1 STICKY la stateful policy. Ket qua cua no duoc giai thich boi do
cu cua quyet dinh accept gan nhat va do dai chuoi reject, khong chi boi ti le
accept.

## Chan doan bat buoc

Lesson 23.1 phai bao cao, khong dung lam gate:

```text
sticky_age_ms_mean       : thoi gian tu lan accept gan nhat den hang reject
reject_run_len_mean      : do dai trung binh chuoi reject lien tiep
initial_state_share      : ti le reject dung P1 vi chua co accept nao trong block
```

Neu `initial_state_share > 0.05`, gioi han L15 long va phai ghi ro: reset dau
block lam F1 te hon dang ke so voi router that khong reset.

## Ky thuat

F1 STICKY duoc cai dat bang:

```text
groupby(block_id).ffill().fillna(P1)
```

Khong can loop Python/numba. R23-1 ("stateful sticky kho vector hoa") duoc giam
tu risk thanh implementation note.

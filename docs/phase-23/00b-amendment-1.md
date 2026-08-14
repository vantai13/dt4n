# AMENDMENT 23-1 -- Pilot disclosure for P1 static optimum

Ngay: 2026-08-14

Ly do: hoan thien cong bo thí điểm truoc khi chay Lesson 23.1. Ly do nay la
phep do/provenance, khong phai ket qua fallback.

## Noi dung

`docs/phase-23/00-preregistration.md` tai tag `phase-23-start` da cong khai:

```text
P(a* = P1), toan hang = 0.656141
P(a* = P1), test      = 0.659724
```

Ban chinh xac hon dung cho audit:

```text
P(a* = P1), toan hang = 0.6561410878
P(a* = P1), test      = 0.6597235418
```

## He qua

F0 la dong `[MO TA]`/pilot, khong tinh vao ti le prediction hit confirmatory.
F1..F4 van la `[CO CHE]` vi chung suy ra tu F0 qua lap luan ve reject set,
va chuoi lap luan do co the sai.

Khong xoa dong prediction nao.

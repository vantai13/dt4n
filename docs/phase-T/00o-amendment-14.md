# AMENDMENT 14 -- Phase T

Ngay viet: 2026-08-03
Du lieu chan doan: G3 dung tai idx 127 vao 2026-08-02.

## Trang Thai

Khoi G3 chay 127/279 diem va dung tai idx 127:

```text
idx 127: h2, rho=0.70, a=0.90, tau=1, seed=11
gate fail sau retry: A5-7_n_late
n_late_ratio = 1.517e-3 > 1e-3
max_late_ms  = 21.04 ms
```

Tat ca 127 diem da hoan thanh pass cac cong vat ly va cong trung thanh thiet ke
truc tiep: V-T4a, V-T6a, V-T6b.

## Loi Cu

`A5-7_n_late` dung nguong `1e-3`, mot so tron thua ke tu Phase L pilot, khong
duoc dan ra tu mo hinh nhieu nao.

```text
fail lan dau quan sat: 6 / 128 = 4.7%
max_false_fail khai bao: 1%
```

Hai khai bao sai trong `GateSpec`:

```text
reference_sd_source="analytic"  # khong co dan xuat analytic
kind="transient"                # n_late co thanh phan he thong theo mode/a/tau
```

## n_late Do Cai Gi

Trong `measurements/packet_player.py`, goi bi tinh late neu vong lap den no
muon hon lich hon 1 ms. Nhung timestamp gui thuc te `t_send` duoc dong vao goi,
nen do tre `t_recv - t_send` khong bi doi truc tiep. Goi tre duoc gui ngay, nen
vong lap tu bat kip.

Vay `n_late` la chi bao do trung thanh thiet ke, khong phai do chinh xac do.
Do trung thanh thiet ke da duoc gac truc tiep boi:

```text
V-T4a ca_operational
V-T6a rate_ratio
V-T6b rho_bias
```

## Chan Doan NT-L10

Tren 108 diem khong phai cbr:

```text
corr(n_late, ca_operational_z) = +0.003   KTC 95% [-0.19, +0.20]
corr(n_late, rho_bias_z)       = -0.130   KTC 95% [-0.32, +0.06]
corr(n_late, loss)             = +0.036
corr trong cau hinh (n_late, ca_z) = +0.107  (n=102)
```

O dai van hanh quan sat duoc, `n_late` giai thich duoi 4% phuong sai cua
`ca_operational_z` voi do tin cay 95%. Tuong quan am nho voi `rho_bias_z` dung
chieu vat ly, nhung `rho_bias` duoc do truc tiep va da duoc gac boi V-T6b.

## Sua Gi

A14.1. Doi `A5-7_n_late` tu nguong chat luong `1e-3` thanh nguong sup do
`1e-2`. Nguong moi cach xa dai van hanh: khoang 40x trung binh quan sat va 11x
cuc dai quan sat trong 127 diem dau.

A14.2. Them `A5-7_max_late` voi nguong `max_late_ms < 100 ms`, de bat mot lan
treo dai ma cong dem so goi tre co the bo sot.

A14.3. Them `warn_n_late = (n_late_ratio > 1e-3)`. Canh bao nay khong fail row;
T.6 se dung no cho sensitivity analysis.

A14.4. Luu attempt history public vao `row["attempts"]`. Neu row fail cu duoc
rerun pass, chuyen row fail cu vao `state["failed_row_history"]` thay vi mat
bang chung.

A14.5. Them meta-test trung thuc provenance cua gate: neu
`reference_sd_source="analytic"` thi phai co `noise_fn`, hoac la cong nhi phan
nguong 0. Cac so tron chon tay khong duoc khai la analytic.

A14.6. T.6 bat buoc bao cao bat doi xung loc:

```text
(a) toan bo 279 diem
(b) tap con dong nhat n_late_ratio < 1e-3
```

Neu ket luan D-T doi dau giua (a) va (b), bao cao ro va khong chon ben tien.

A14.7. Khong bat `SCHED_FIFO`/`taskset` giua chien dich. Giu tinh nhat quan cua
279 diem; ghi drift thoi gian gui vao threats to validity.

## Nguyen Tac Moi

NT-L14. Ket luan "khong co tuong quan" phai kem gioi han co hieu ung, khong chi
p-value.

NT-L15. Khi tieu chi chon mau doi giua chien dich, phai chung minh bien loc
khong tuong quan voi ket qua va bao cao tap con dong nhat.

NT-L16. Mot truong khai bao chi co gia tri khi co test kiem chung no trung
thuc.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-03

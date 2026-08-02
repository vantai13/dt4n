# PHASE T -- T.4 VALIDATION

Ngay: 2026-07-31
Deliverable: `measurements/t4_validate.py`,
`test/test_phase_t_validate.py`, va `test/test_phase_t_mutants.py`.

T.4 khong chay Mininet. Muc tieu la kiem tra xem cac cong Phase T co that su
bat duoc loi hay khong, va tao oracle tong hop cho tang phan tich truoc khi
sang campaign T.5.

--------------------------------------------------------------------
## Dinh Chinh Tu T.3

T.3 noi qua manh ve cam bay "chuan hoa sau khi rescale". Mutation testing cho
thay mutant nay song sot vi gan nhu vo hai trong he hien tai:

```text
he so k ~= 1.000016
anh huong ~= 0.0016%
```

Ly do: `lambda(rho)` tuyen tinh theo `rho`, nen `E[lambda] = lambda(E[rho])`
chinh xac. Van giu thu tu chuan hoa trong thoi gian van hanh truoc khi
rescale, vi do la hop dong dung va se quan trong neu anh xa `rho -> lambda`
ve sau thanh phi tuyen.

--------------------------------------------------------------------
## Mutation Testing

Mutant duoc cai rieng trong `test/test_phase_t_mutants.py`, khong dung vao
code san xuat.

```text
mutant             ket qua
round_inverse      bi V-T4a va gap>0 bat
thinning           bi V-T4a va V-T4b bat
normalize_after    song sot, duoc giai thich la vo hai trong he tuyen tinh
reimpl_const       cbr song sot, h2 digest do
bo trong so lambda bi Oracle 1 bat
dao dau jensen     bi Oracle 2 bat
```

Phat hien quan trong: V-T5 khong duoc chi chay `cbr`. Voi `cbr`,
`build_schedule()` tra `[mean_gap] * n`, nen mot ban tu cai lai duong hang so
co the trung bit. V-T5 digest bit-exact phai co `h2` hoac `poisson`.

V-T4b chi ap dung khi `c_a_predicted > 0.005`; duong hang so/cbr co gia tri
du doan gan 0 nen kiem sai so tuong doi la vo dinh.

--------------------------------------------------------------------
## Oracle Tong Hop

Oracle 1: he quasi-static hoan hao.

```text
q_i = f(rho(t_i))
dap an: err_qs = 0 trong san lay mau goi
```

Oracle nay bat loi bo trong so `lambda`, sai chi so thoi gian, hoac sai dinh
nghia rho trong `q_psa_load_ms`.

Oracle 2: he tri tre hoan toan.

```text
q_i = f(mean(rho))
dap an: err_qs + err_jensen + d_sampling = 0
```

Oracle nay bat loi dau `err_jensen` va loi phan ra ba thanh phan.

Ket qua voi code hien tai:

```text
mode      a     O1 err_qs_ms   SE_ms      O2 total
h2      0.20      +0.001271   0.001910   0.0
h2      0.90      +0.009428   0.008469   0.0
poisson 0.20      -0.000705   0.002286   0.0
poisson 0.90      -0.003788   0.011013   0.0
```

Oracle 1 khong dung nguong 0 tuyet doi, vi `q_bg_load` la trung binh mau tren
lich goi con `q_psa_load` la tich phan. San ly thuyet:

```text
SE(err_qs) = sd_lambda[f(rho)] / sqrt(n_goi)
```

--------------------------------------------------------------------
## Tautology Can Tranh

1. Khong dung `rho` do lai tu dem goi trong tich phan quasi-static.

Tich phan PSA/MOL phai dung `rho(t)` thiet ke tu `rho_spec`. Neu dung
`rho_hat` do tu chinh dong goi, `q_i` va `rho_hat` chia se cung nguon nhieu,
lam `err_qs` bi keo ve gan 0 gia tao.

2. `err_jensen` va `d_sampling` la dai luong mo hinh.

Chung duoc tinh tu `f`, khong phai do truc tiep. Cach kiem thuc nghiem la o
vung `Lambda >> 10`, noi `err_qs ~ 0`, thi `err_total` do duoc phai khop
`err_jensen + d_sampling`.

3. V-T5 la cong ha tang, khong phai bang chung model dung.

Duong `sigma_rho=0` kiem Phase T co tai tao Phase L hay khong: payload, qdisc,
probe, seed, digest. Bang chung model dung nam o predictive gate Phase L va
cac diem `sigma_rho > 0`.

4. `err_total = err_qs + err_jensen + d_sampling` la dong nhat thuc dai so.

Test no co gia tri phan mem, vi bat loi dau/thu tu/trong so, nhung khong phai
kiem nghiem vat ly.

5. Diem canh chi so voi chinh no qua thoi gian.

Sentinel co the trung cau hinh voi luoi chinh, nhung seed 999 phai duoc dung
de do drift may theo thoi gian, khong so voi cac o luoi khac.

6. So goi khac nhau giua cac o.

`n_base = int(Lambda_total)` lam n goi thay doi theo `rho_bar`. Moi bao cao
`err_qs` phai kem SE; hinh chinh dung `err_qs/sigma_ref`.

--------------------------------------------------------------------
## RT8: San Nhieu Cua err_qs

Hai o co SE mot seed lon hon nguong "bo qua duoc":

```text
mode      rho_bar   a     SE_ms      0.1*sigma_ref   SE/nguong
h2        0.70    0.90   0.009389   0.008144        1.153
poisson   0.70    0.90   0.003565   0.003152        1.131
```

Quy tac bao cao:

```text
neu |err_qs| < 2*SE:
    phan loai = khong_phan_biet_duoc_o_phan_giai_nay
```

Khong duoc viet "err_qs = 0" o cac o nay. Phai noi dung hon: voi mot seed,
thiet ke khong co du phan giai de phan biet sai so nho voi 0; 5 seed se giam
SE cua tom tat giua seed khoang `sqrt(5)`.

--------------------------------------------------------------------
## Anh Xa Cong Do Sang Nhanh Sua

```text
V-T0 digest lech       -> provenance/seed/dt sai
V-T3 clamp > 1%        -> kiem sigma_max_feasible va sigma_from_a
V-T4a do              -> kiem Lambda^-1 noi suy, thinning, operational time
V-T4a |z| > 4         -> kiem SE_c_a delta-method va moment generator
V-T4b do              -> kiem thinning hoac background_pps/lambda
V-T5a digest lech      -> kiem interpreter/provenance va delegation Phase L
V-T5b z aggregate do   -> kiem reference_sd_source; khong dung nguong 2% tung diem
V-T5b same-seed do     -> dung truoc G3; di nhanh T8(b) ha tang T lech Phase L
V-T6a rate lech        -> kiem n_base va Lambda_total
V-T6b |rho_bias_z| > 3 -> kiem renewal-boundary sd; neu van fail thi dung
rho_bias aggregate do  -> kiem drift bo phat nho nhung co he thong
Oracle 1 do            -> kiem trong so lambda va rho thiet ke
Oracle 2 do            -> kiem dau err_jensen va phan ra
|err_qs| lon           -> kiem Oracle 1, rho thiet ke, |err_qs| > 2*SE
```

--------------------------------------------------------------------
## Lenh Kiem Tra Lai

Chay rieng T.4:

```bash
pytest test/test_phase_t_validate.py test/test_phase_t_mutants.py -q
```

Chay nhom Phase T hien co:

```bash
pytest test/test_phase_t_no_v1_import.py test/test_traffic_v7_hurst.py test/test_phase_t_rho_spec.py test/test_phase_t_rho_schedule.py test/test_phase_t_validate.py test/test_phase_t_mutants.py -q
```

Chay full suite:

```bash
pytest -q
```

Ket qua tai thoi diem them T.4:

```text
pytest test/test_phase_t_validate.py test/test_phase_t_mutants.py -q
20 passed

pytest test/test_phase_t_no_v1_import.py test/test_traffic_v7_hurst.py test/test_phase_t_rho_spec.py test/test_phase_t_rho_schedule.py test/test_phase_t_validate.py test/test_phase_t_mutants.py -q
128 passed

pytest -q
302 passed, 4 skipped, 2 warnings
```

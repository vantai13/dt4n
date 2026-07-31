# AMENDMENT 5 -- Phase T

Ngay: 2026-07-31
Trang thai truoc sua: Phase T chua chay do song; T.4 chi them validation
ham thuan va synthetic oracle.
Tai lieu kem: `docs/phase-T/04-validation.md`.

## Da Thay Gi Truoc Khi Sua

T.3 da chot time-rescaling va cac cong V-T4a/V-T6a. T.4 them mutation
testing de hoi cau hoi khac: neu cai sai, cong co do khong?

Ket qua mutation testing bat duoc mot phat bieu qua manh va mot lo hong that:

```text
normalize_after song sot vi gan nhu vo hai: he so k ~= 1.000016
reimpl_const lot V-T5 neu chi kiem cbr
```

## Sua Gi

A5.1. Dinh chinh cam bay 2 cua T.3.

Chuan hoa sau khi rescale khong pha `rho(t)` trong he hien tai, vi
`lambda(rho)` tuyen tinh theo `rho`. Anh huong do duoc khoang `0.0016%`.
Van giu thu tu chuan hoa trong operational time truoc khi rescale de hop dong
phu thuoc thiet ke va de an toan neu anh xa `rho -> lambda` ve sau phi tuyen.

A5.2. V-T5 phai chay tren `h2` hoac `poisson`.

Voi `cbr`, `build_schedule()` tra `[mean_gap]*n`, khong qua `normalize_rate`,
nen mot ban tu cai lai duong hang so co the trung digest mot cach ngau nhien.
Digest bit-exact cua V-T5 phai co it nhat mot mode co schedule ngau nhien va
normalize, nhu `h2` hoac `poisson`.

A5.3. V-T4b chi ap dung khi `c_a_predicted > 0.005`.

Gan 0 thi sai so tuong doi vo dinh. Test da co dieu kien nay; prereg nay ghi
lai de khong ai go bo dieu kien.

A5.4. Them hai oracle tong hop cho tang phan tich.

```text
Oracle 1: q_i = f(rho(t_i))  -> err_qs = 0 trong 3*SE
Oracle 2: q_i = f(mean(rho)) -> err_qs + err_jensen + d_sampling = 0
```

Oracle 1 bat mutant bo trong so `lambda`; Oracle 2 bat mutant dao dau
`err_jensen`. Ca hai phai xanh truoc khi bat dau T.5.

A5.5. Quy tac chong tautology: tich phan QS dung `rho` thiet ke.

`rho` do tu dem goi chi dung cho V-T6b. Khong duoc dua `rho_hat` vao
`q_psa_load_ms` hoac `q_psa_time_ms`, vi `q_i` va `rho_hat` den tu cung dong
goi va co the lam `err_qs` sup ve gan 0 gia tao.

A5.6. Them RT8 va phan loai moi cho `err_qs`.

```text
SE(err_qs) = sd_lambda[f(rho)] / sqrt(n_goi)

neu |err_qs| < 2*SE:
    khong_phan_biet_duoc_o_phan_giai_nay
```

Hai o co SE mot seed lon hon nguong `0.1*sigma_ref`:

```text
h2,      rho_bar=0.70, a=0.90: SE/nguong ~= 1.153
poisson, rho_bar=0.70, a=0.90: SE/nguong ~= 1.131
```

Moi o Phase T phai bao cao `err_qs +/- SE`; hinh chinh dung
`err_qs/sigma_ref`.

## Code/Test Them

```text
measurements/t4_validate.py
test/test_phase_t_validate.py
test/test_phase_t_mutants.py
```

`test/test_phase_t_no_v1_import.py` duoc mo rong de canh ca
`mininet/rho_schedule.py` va `measurements/t4_validate.py`.

## Khong Sua

```text
rho_spec.py giu nguyen
rho_schedule.py giu thuat toan rescale chinh
load_spec.py giu nguyen
grid Phase T giu nhu Amendment 2/3
probe van Poisson hang 20 pps
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-31

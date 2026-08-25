# AMENDMENT 23-65d -- `selective` tut ve `none` khi suy bien o vong 0

Ngay ky : 2026-08-25
Lesson  : 23.22 (dinh chinh sau khi doc artifact vong hai)
Loai    : SUA NHAN SAI SU THAT + DINH CHINH DUONG DAN
Moc     : sau `b9d2774`

## 0. Disclosure

Phat hien nay den TU viec do `L94`: khi tra xem vi sao `min_blocks = None` tai
`kappa = 2`, thay `qhat` cua `selective` TRUNG BIT voi `none` tren 8/8 cell
song. Day la mot su that DA NAM trong artifact `b9d2774`; amendment nay chi
DAT TEN cho no, khong sinh so lieu moi.

KHONG chay lai. Truong `qhat_source` la mot NHAN cho mot su that da ghi
(`min_blocks_at_final_qhat = None` cong `n_iter = 0`), khong phai mot phep do.

## 1. L95 -- `selective` khoi tao bang `qhat` cua `none`

`cert/config_matrix.py`, nhanh `post == "selective"`:

```text
q = _qhat(calib, cols, keys, a_by)        # khoi tao = qhat cua thu tuc `none`
for it in range(max_iter):
    ...
    if min(nb) < floor_blocks:
        info.update(converged=False, degenerate=True, n_iter=it, cycle_len=0)
        break                              # THOAT, KHONG cap nhat q
```

Suy bien o **vong 0** ⟹ `q` chua tung duoc cap nhat ⟹ ket qua tra ve la gia
tri khoi tao. Va gia tri khoi tao la `_qhat` tren TOAN BO `calib` voi cung
`keys` -- tuc DUNG BANG `qhat` cua nhanh `none`.

Do duoc tren `results/LIVE/phase-23/taxonomy_audit.json` (`b9d2774`,
`git_hash = cced37a`, `git_dirty = false`), tai `kappa = 2`, tren CA 8 cell co
`A = True`:

```text
cell           n_iter   qhat V-S   qhat V-N   trung?   viol V-S   viol V-N
poisson@0.925     0      44.7109    44.7109    True     0.1897     0.1897
poisson@0.850     0      15.5910    15.5910    True     0.0667     0.0667
h2@0.700          0      28.3143    28.3143    True     0.2026     0.2026
poisson@0.875     0      23.8559    23.8559    True     0.0964     0.0964
poisson@0.900     0      34.5129    34.5129    True     0.1059     0.1059
poisson@0.960     0      62.6410    62.6410    True     0.1161     0.1161
h2@0.650          0      16.2334    16.2334    True     0.1357     0.1357
h2@0.675          0      21.5928    21.5928    True     0.1773     0.1773
```

Trung den chu so cuoi o 8/8, va `n_iter = 0` o 8/8 -- co che va so lieu khop.

### 1.1. Vi sao day la loi DUNG DAN, khong phai loi chan doan

`none` la thu tuc DA DO LA VO bao dam hau chon loc -- do la toan bo noi dung
cua `M-187`. Nen `min_blocks_at_final_qhat = None` KHONG co nghia "thieu du
lieu"; no co nghia **"V-S da thanh V-N"**.

```text
"V-S suy bien"   !=   "V-S than trong hon"
"V-S suy bien"   ==   "V-S IM LANG tro thanh V-N"
```

O 6/8 cell tren, `viol_given_accept` cua "V-S" vuot `alpha = 0.10` (0.1897,
0.2026, 0.1059, 0.1161, 0.1357, 0.1773), va no vuot vi thu tuc dang chay
khong phai thu tuc mang nhan.

Cac hang do deu co `pass_coverage = false`, nen KHONG mot ket luan da cong bo
nao doi. Cai sai la NHAN `post = "selective"` tren mot hang thuc su chay
`none`.

### 1.2. Anh huong toi `L94`

`L94` ghi hai cach doc `M-192` cho hai phan quyet nguoc (0.5 HIT / 2.0 MISS),
va chon DOAN LIEN TUC vi ly do NGU NGHIA ("mot dai thi phai lien tuc"). `L95`
cho mot ly do THUC CHAT manh hon:

```text
cach doc "max tren ca tap" -> kappa = 2.0
   nhung tai kappa = 2.0, V-S khong ton tai -- no la V-N doi ten.
   Cach doc do khong chi khac; no tro vao mot diem van hanh ma thu tuc
   duoc khuyen nghi KHONG CHAY.
```

Mot cach doc dan den mot diem van hanh noi thu tuc duoc khuyen nghi khong ton
tai thi khong phai mot cach doc canh tranh. Phan quyet `M-192 = HIT` giu
nguyen, voi ly do duoc CUNG CO.

## 2. Sua -- truong `qhat_source`

Nam gia tri:

```text
"fixed_point"                 vong lap hoi tu; `q` la diem bat dong
"cycle_max"                   phat hien chu trinh; `q` = max tren chu trinh
"iterate_not_converged"       het `max_iter`; `q` la mot iterate cua V-S,
                              chua hoi tu
"degenerate_partial"          suy bien o vong > 0; `q` la mot iterate hop le
"degenerate_fallback_to_none" suy bien o VONG 0; `q` = khoi tao = qhat cua `none`
```

Ban thao noi bo khai BON gia tri, khong co `iterate_not_converged`, va dat
`fixed_point` ngay sau moi lan `q = q_new`. **Da sua thanh nam**: mot lan chay
het `max_iter` co `q` DA doi (nen khong phai `L95`) nhung KHONG phai diem bat
dong, va goi no `fixed_point` la dung cai loi ma amendment nay dang sua --
mot nhan khang dinh dieu khong dung, du truong `converged = false` ben canh co
khai that. Cung tieu chuan da ap cho `post = "selective"` o muc 1.1.

Chi `degenerate_fallback_to_none` la truong hop nhan sai su that. Bon gia tri
kia deu la `selective` that.

Huong mac dinh: `degenerate_fallback_to_none` la GIA TRI KHOI TAO, va chi
duoc nang len khi `q` THUC SU doi. Lam nguoc lai (mac dinh `fixed_point`, ha
xuong khi suy bien) se khien mot nhanh `break` MOI trong tuong lai im lang tra
ve nhan sai. Mac dinh phai la GIA DINH XAU NHAT -- cung nguyen tac voi
`git_dirty` mac dinh `True` khi khong do duoc (`L78`). Ghim boi
`test_qhat_source_default_is_the_pessimistic_one`, doc thu tu trong ma nguon.

Chot chan o `evaluate_config`: khi gap `degenerate_fallback_to_none`, ghi
`procedure_actually_run = "none"` (KHONG phai `post`) va
`L95_collapsed_to_none = true`.

### 2.1. Mot quan sat ve pham vi cua `degenerate_partial`

Duoi san on dinh 59 (`L93`) thi `level == 1.0` va `_qhat` tra ve MAX cua mau,
nen `qhat` chi co the GIAM qua cac vong (max tren tap con <= max tren tap cha)
⟹ tap chon chi NO RA ⟹ so block khong bao gio giam sau vong 0. Trong che do
do, suy bien **luon** xay ra o vong 0, va do dung la dieu quan sat duoc: ca
8/8 hang suy bien trong artifact deu co `n_iter = 0`.

`degenerate_partial` chi den duoc khi `n_eff >= 59`. Da dung mot cell tong hop
120 block/o de cham nhanh do trong test -- neu khong, no la ma khong bao gio
chay va khong ai biet.

## 3. Dinh chinh duong dan output cua `G23-242`

`A065-amendment-65.md` muc 9 khai
`results/RAW/phase-23/g23_242_rerun_diff.json`. `results/RAW` da bi khoa
`chmod -R a-w` (amendment 23-61), nen duong dan do khong ghi duoc, va viec ghi
duoc vao do se pha custody. Duong dan dung, da dung khi chay:

    results/LIVE/phase-23/g23_242_rerun_diff.json

Tai lieu DA KY khong sua; anh xa song o day.

### 3.1. L96 -- va no khong phai mot vu don le

Khi viet cai chan cho muc 3, phat hien them **CHIN** cong cu co `--out*` mac
dinh tro vao tang DA KHOA:

```text
cert/abstain_cost.py                   --out-dir  results/SUPERSEDED/phase-23
cert/decomposition.py                             results/SUPERSEDED/phase-21R
cert/gate_report.py                               results/SUPERSEDED/phase-21R
cert/lesson23_7_calibration_2b.py                 results/SUPERSEDED/phase-23
cert/lesson23_7_feasibility.py                    results/SUPERSEDED/phase-23
cert/lesson23_7_range_calibration.py              results/SUPERSEDED/phase-23
cert/operational_sigma.py                         results/SUPERSEDED/phase-21R
cert/threshold_families.py                        results/SUPERSEDED/phase-23
tools/g23_212a_partial_nc.py           --out      results/RAW/phase-23
```

Chung co TU TRUOC khi tang bi khoa (23-61) -- hoi do duong dan con ghi duoc.
KHONG sua chung: output cua chung da dong bang, va doi duong dan mac dinh se
lam mat dau vet giua tai lieu cu va file that. Chung duoc GHIM thanh mot tap
DA KHAI BAO trong `test_no_tool_writes_into_frozen_tiers`, va phep so sanh la
BANG NHAU: them mot cong cu moi -> test do; sua mot cong cu cu ma quen go
khoi danh sach -> test cung do. Danh sach chi duoc NGAN di.

Co soi chi bat `--out*` (co GHI). Mac dinh DOC tro vao tang khoa la HOP LE:
`tools/check_phase20r6_structure.py` doc `--new-b/--new-c` tu
`results/SUPERSEDED/`, va do dung la cach dung tang do. Ban thao noi bo dung
mot regex bat MOI `default=` va no bao dong gia tren dung file nay.

## 4. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-247 | `test_selective_at_degenerate_kappa_is_bit_identical_to_none` doc thang artifact `b9d2774` va xac nhan >= 8 truong hop trung bit; VA `test_no_tool_writes_into_frozen_tiers` xanh | tat/bat |

## 5. Pham vi anh huong

`qhat_source` la NHAN. Khong doi luong dieu khien, khong doi mot con so nao:
`fit_config` tra ve dung `q` cu, `evaluate_config` tra ve dung cac so cu cong
ba truong moi.

KHONG chay lai. Neu ai do chay lai, `G23-242` phai van PASS voi `qhat_source`,
`procedure_actually_run`, `L95_collapsed_to_none` them vao `SWEEP_NEW_KEYS`.

## 6. Output

```text
code      cert/config_matrix.py   (qhat_source + procedure_actually_run)
tool      tools/g23_242_taxonomy_rerun_diff.py  (SWEEP_NEW_KEYS)
test      test/test_phase23_taxonomy_audit.py   (sau test moi)
artifact  KHONG doi -- khong chay lai
doc       docs/phase-23/LIMITS.md (`L95`, `L96`), docs/phase-23/GATES.md
```

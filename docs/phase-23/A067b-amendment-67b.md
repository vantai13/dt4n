# AMENDMENT 23-67b -- `L100` va hai phep sua do luong cua Task B-2

Ngay ky : 2026-08-25
Lesson  : 23.22 Task B-2
Loai    : GHI HAN CHE + SUA PHEP DO (truoc khi ket luan)
Moc     : sau `cf5f852`, trong khi Task B-2 dang chay

## 0. Disclosure

`M-199` (`A067` muc 7, `G23-259`) noi ve CO va ve tinh HUU HAN cua `c`. Hai
phep sua o muc 2 va 3 KHONG cham vao hai dai luong do -- da doi chieu:
`C3_flag_rate_below_floor = 1.00`, `B2_finite_rate_below_floor = 1.00`,
`B2_flag_rate_below_floor = 0.00` truoc va sau ca hai sua.

`L100` la POST-HOC: no den tu viec doc bang `n` sau lan chay dau.

## 1. L100 -- co cua `L93` MU DUNG trong truong hop cua `L95`

`cert/config_matrix.py` tinh co `qhat_at_sample_max` nhu sau:

```python
_nb = info.get("min_blocks_at_final_qhat")
info["qhat_at_sample_max"] = bool(
    _nb is not None and _nb < int(info.get("min_blocks_stable", 0)))
```

Nhung `min_blocks_at_final_qhat` la `None` **dung khi** vong lap `selective`
suy bien o vong 0 -- tuc dung truong hop `L95`. Nen mot lan chay:

```text
VUA chay `none` duoi nhan `selective`   (`L95`)
VUA o che do `qhat = max mau`           (`L93`)
```

se KHONG duoc mot co nao bat. Hai co bat khac nhau va cung mu o dung cho
giao nhau.

Do duoc tren `recalibration_cost.json`, tai `n = 30` block (ngay tren san hop
le 29), 80 lan lay mau moi cell x 8 cell:

```text
n = 30   qhat_has_infinite hoac qhat_at_sample_max  ->   2%
         qhat_source == "degenerate_fallback_to_none" ->  98%
         hai co cong `qhat_source`                   -> 100%
```

**98% so lan chay o `n = 30` la `none` doi ten, va he thong co cu bat duoc 2%.**

Truong `qhat_source` (`A065d`) bat duoc 100%. Do la ly do `A065d` khong phai
mot phep doi ten trang tri: no la co duy nhat con nhin thay o vung nay.

### 1.1. KHONG sua co, va vi sao

Co the sua bang cach ghi `min_blocks_at_final_qhat` ngay ca khi suy bien.
KHONG lam, vi hai ly do:

```text
1. `min_blocks_at_final_qhat` co nghia "so block o vong DA SINH RA `q` duoc
   tra ve". Khi suy bien o vong 0, `q` khong den tu mot vong nao -- no la gia
   tri khoi tao. Ghi mot so vao do se lam truong nay noi doi.
2. `M-199` da ky voi HAI co. Doi dinh nghia co giua chung se lam phan quyet
   khong con la phan quyet da ky.
```

Thay vao do: `C3_flagged_incl_source` duoc ghi RIENG trong artifact Task B-2,
va `M-199` van cham tren HAI co nhu da ky. Ai muon mot co day du thi dung
`qhat_source`.

## 2. Sua phep do (a) -- BO `B2_viol_given_accept`

Ban dau Task B-2 ghi `viol|accept` cho B2, do bang `s > qhat` voi `qhat` cua
C3. Do la **muon `qhat` cho B2** -- dung cai bay `A066` muc 3 da tu choi va
da ghim bang test o Task B.

O day no con te hon: khi `n < 29` thi `qhat = +inf`, nen `s > qhat` SAI voi
moi hang, nen B2 hien ra:

```text
n = 10   B2_viol_given_accept = 0.0000        <- "hoan hao"
```

Mot con so hoan hao sinh ra tu mot cong cu do hong. Da BO truong nay. Dai
luong so sanh duoc cua B2 la `err|accept`, khong can `qhat`.

## 3. Sua phep do (b) -- them bien the B2 MUC TIEU CO DINH

Ban dau `c` chi duoc khop voi acceptance cua C3 tren CUNG `calib_sub`. Duoi
san, C3 co `qhat = +inf` va chap nhan **0 hang**, nen B2 bi keo ve 0 theo, va
cot B2 o `n` nho khong noi duoc gi ve B2.

Them `c_B2_fixed`: `c` do tu `n` block de dat `target_acceptance` tren `n`
block do, trong do `target_acceptance` = acceptance ma C3 dat khi co TOAN BO
calib cua cell.

```text
`target` la mot lua chon THIET KE (dich den can dat), khong phai thu hoc duoc
tu `n` block, nen dua no vao KHONG lam ro ri du lieu vao `c(n)`.
```

Ca hai bien the deu duoc ghi. Bien the cu (`c_B2`) giu lai vi no la phep so
sanh "ca hai chi thay `n` block do va khong gi khac".

## 4. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-260 | `L100` do duoc: tai `n = 30`, ti le lan chay co `qhat_source = degenerate_fallback_to_none` LON HON ti le duoc hai co `L91`/`L93` bat, tren >= 6/8 cell | DIAGNOSTIC -- POST-HOC, khong dem diem |

## 5. Pham vi anh huong

```text
KHONG doi `M-199`: hai sua o muc 2/3 khong cham vao co hay tinh huu han cua `c`.
KHONG doi mot con so nao cua `transfer_matrix.json`.
KHONG doi `cert/config_matrix.py` (muc 1.1).
```

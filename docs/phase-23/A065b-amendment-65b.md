# AMENDMENT 23-65b -- Khai bao che do `qhat = max mau`

Ngay ky : 2026-08-25
Lesson  : 23.22 vong hai
Loai    : BO SUNG DIAGNOSTIC (khong doi mot con so nao)
Moc     : sau `1b21b2c`, TRUOC khi chay lai `taxonomy_audit`

## 0. Disclosure

Phat hien nay den TU viec sua `29 vs 30` cua amendment 23-65. Khi tra xem
`conformal_level` bang BAO NHIEU ngay tren san, thay no bang dung `1.0` tren
ca mot dai. Do duoc:

```text
alpha_bonferroni(0.10, 3) = 0.03333333333333333   ( == 0.1/3, da kiem )

    n = 28  ->  level = None
    n = 29  ->  level = 1.0          <- san HOP LE
    n = 40  ->  level = 1.0
    n = 58  ->  level = 1.0
    n = 59  ->  level = 0.9830508    <- san ON DINH
```

va voi `alpha = 0.10`: `n = 9..18 -> 1.0`, `n = 19 -> 0.94737`.

**Chua ai dem so cell roi vao dai do.** `M-191` duoi day la mot du doan MU.

Cai DA XEM khi soan amendment nay: ti so `qhat(kappa=1)/qhat(kappa=0)` cua
V-S trong `eefd34a` -- cell suy bien nhay 1.25..1.41x, cell hoi tu nhay
1.18x. Do la dau van tay gian tiep, khong phai phep dem.

## 1. L93 -- che do `qhat = max mau`

`cert/conformal_v2.py:87`:

```python
def empirical_qhat(values, level):
    return float(np.quantile(values, float(level), method="higher"))
```

Da kiem truc tiep: `empirical_qhat([1,5,2,9,3], 1.0) = 9.0 = max`. Nen khi
`level == 1.0`, **`qhat` chinh la gia tri LON NHAT trong tap duoc chon**.

```text
alpha/3     : san huu han 29, san level<1 = 59  ->  dai [29, 58]
alpha = 0.10: san huu han  9, san level<1 = 19  ->  dai  [9, 18]
```

Hau qua:

```text
(1) HUU HAN va HOP LE ve toan -- bao dam conformal VAN GIU.
(2) Nhung no do MOT quan sat cuc dai quyet dinh. Doi mot hang -> qhat nhay.
    Phuong sai khong lo.
(3) Va cuc ky bao thu -> acceptance sup -> "bao phu giu" mot cach TAM THUONG.
```

**Cung HINH DANG loi voi `qhat = +inf` cua `L91`:**

```text
qhat = +inf       vo dung hoan toan,  DI QUA IM LANG   -> da gan co (L91)
qhat = max mau    gan vo dung + BAT ON, DI QUA IM LANG -> chua co co
```

Ca hai la "hop le ve toan nhung vo nghia ve van hanh, khong duoc khai bao".
Nguyen tac fail-loud cua `L78` (`pin()`) ap cho ca hai.

## 2. Ranh gioi KHONG duoc vuot

**KHONG duoc nang chot chan tu 29 len 59.** Ba ly do:

```text
(1) 29 la san HOP LE -- toan hoc, da chung minh, khong duoc doi.
(2) 59 la san ON DINH -- mot moi quan tam VAN HANH, KHAC LOAI.
    Tron hai thu vao mot chot chan la danh mat kha nang phan biet
    "khong hop le" voi "hop le nhung bat on".
(3) 59 la mot NGUONG MOI dat SAU khi xem du lieu. Do la HARKing.
```

Viec dung: **KHAI BAO, khong chan.** Ghi ra so, de nguoi doc thay.

Ranh gioi nay duoc GHIM bang mot test doc ma nguon
(`test_stability_floor_does_not_gate_anything`): `"< floor_blocks" in src` va
`"< stable_blocks" not in src`. Sau nay ai thay `qhat_at_sample_max = true` va
phan xa nang chot chan se bi test do, va docstring giai thich vi sao.

## 3. M-191 -- so cell roi vao che do max mau   [KY THAT]

```text
M-191  So cell co `qhat_at_sample_max = true` tai `kappa = 1`, bien the V-S,
       tren 12 cell:  du doan **[1, 8]**.
```

Ly do khoang rong: chua ai do `min_blocks_at_final_qhat` bao gio.

```text
bien duoi 1  : da thay dau van tay gian tiep (qhat V-S nhay 1.25..1.41x o
               cell suy bien so voi 1.18x o cell hoi tu)
bien tren 8  : 6/12 da suy bien TRUOC khi sua, va chot chan chat hon (29 thay
               vi 9) co the day them cell vao dai [29,58]
```

> Ban review de xuat ma `M-195`. Da cap `M-191`: ma lon nhat dang dung la
> `M-190`, va nhay len 195 se de trong `M-191..194` khong ly do.

## 4. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-245 | M-191 trong dai [1, 8]; VA chot chan van la `floor_blocks`, KHONG phai `stable_blocks` (ghim bang test doc ma nguon) | tat/bat |

## 5. Pham vi anh huong -- khai TRUOC khi chay

Diagnostic THUAN. Khong doi luong dieu khien, khong doi mot con so nao.

```text
KHONG DOI : moi gia tri da co trong artifact
DUOC THEM : min_blocks_stable, min_blocks_at_final_qhat, qhat_at_sample_max
```

`G23-242` phai van PASS y het sau khi them patch nay. Neu no FAIL, patch
"diagnostic thuan" da khong thuan -> DUNG va revert.

## 6. Cai KHONG lam

```text
- KHONG nang chot chan (muc 2).
- KHONG sua `conformal_v2.empirical_qhat` -- `method="higher"` la dung, no
  bao dam `qhat` la mot diem mau THAT.
- KHONG sua `selective_conformal.py` -- o do alpha=0.10 va con so 9 DUNG;
  dai `[9,18]` cua no la mot moi quan tam RIENG, thuoc lesson so huu no.
- KHONG lat bat ky gate nao cua amendment 23-64.
```

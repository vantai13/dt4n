# 45 -- Lesson 23.22 Task B-2: chi phi tai hieu chuan

Ngay      : 2026-08-25
Lesson    : 23.22 Task B-2
Amendment : `A067` muc 7 (`M-199`, `G23-259`), `A067b` (`L100`, hai phep sua
            do luong truoc khi ket luan)
Artifact  : `results/LIVE/phase-23/recalibration_cost.json`
Chay      : 8 cell x 7 muc `n` x 10 lan lay mau, 8 phut 53 giay

## 0. Cau hoi va cau tra loi

Task B ket luan cai C3 co ma B2 khong la *"mot thu tuc da biet de tai lap
`qhat` tu du lieu co nhan cua che do moi, KEM YEU CAU CO MAU DO DUOC"*. Den
`A067` do van la mot khang dinh DINH TINH. Task B-2 do no.

```text
Cau tra loi co HAI VE, va ve thu hai bat loi cho C3:

  1. C3 BIET khi no khong du du lieu -- 100% so lan duoi san. B2 KHONG.
  2. C3 tra cho hieu biet do bang mot YEU CAU CO MAU LON HON NHIEU:
     no can ~250 block de dat dung diem van hanh, B2 can ~20.
```

## 1. `M-199` = HIT   (`G23-259`)

```text
San hop le cua `alpha/3` = 29 block (`L91`).
Duoi san (n = 10 va 20), 160 lan lay mau tren 8 cell:

    C3 gan co `qhat_has_infinite` hoac `qhat_at_sample_max`   100%   (nguong >= 90%)
    B2 tra `c` HUU HAN                                        100%
    B2 gan co                                                   0%   (khong co co)

8/8 cell HIT rieng le.
```

Duoi san, `conformal_level` tra `None` -> `_qhat` tra `+inf` -> C3 chap nhan
**0 hang**. No khong tra ra mot quyet dinh sai; no TU CHOI, va no noi ro tai
sao. B2 tu 10 block tra ve mot `c` huu han, mot ti le chap nhan hop ly, va
khong mot truong nao noi rang con so do dua tren 10 block.

## 2. Bang theo `n` -- gop 8 cell

```text
    n   co C3  +source sup none   viol C3    err C3 err B2fix     dr C3  dr B2fix
   10    100%     100%     100%       nan       nan    0.0826    0.4211    0.0516
   20    100%     100%     100%       nan       nan    0.0858    0.4211    0.0337
   30      2%     100%      98%    0.0033    0.0279    0.0754    0.2355    0.0237
   60     95%      95%       0%    0.0404    0.0494    0.0808    0.1191    0.0176
  120      1%       1%       0%    0.0620    0.0667    0.0867    0.0366    0.0169
  250      0%       0%       0%    0.0729    0.0702    0.0837    0.0203    0.0119
  500      0%       0%       0%    0.0815    0.0746    0.0862    0.0102    0.0091

co C3      hai co `L91`/`L93`
+source    hai co CONG `qhat_source == degenerate_fallback_to_none`
sup none   ti le lan chay chay `none` duoi nhan `selective` (`L95`)
dr         |acceptance do duoc  -  diem van hanh mong muon|
```

`viol C3` va `err C3` la `nan` o `n = 10, 20` vi C3 khong chap nhan hang nao.

## 3. ★ Ve BAT LOI cho C3: yeu cau co mau de dat DIEM VAN HANH

```text
acceptance trung binh tren 8 cell (diem van hanh mong muon ~ 0.427):

    n        C3        B2fix        sd C3 (trong cell)   sd B2fix
   10    0.0000       0.4255            0.0000            0.0790
   20    0.0000       0.4359            0.0000            0.0493
   30    0.2089       0.4127            0.0311            0.0404
   60    0.3230       0.4297            0.0305            0.0271
  120    0.3998       0.4296            0.0152            0.0181
  250    0.4174       0.4255            0.0051            0.0073
  500    0.4268       0.4271              --                --
```

```text
n nho nhat de |drift| <= 0.05 :   C3 = 120 block      B2 = 20 block
n nho nhat de |drift| <= 0.02 :   C3 = 500 block      B2 = 60 block
```

**B2 dat dung diem van hanh tu 10 block; C3 can nhieu hon mot bac do lon.**

Do khong phai mot bat ngo -- no la cung mot danh doi da ghi o doc 43 muc 13,
nay do o chieu TAI HIEU CHUAN:

```text
`qhat` la mot PHAN VI o duoi `1 - alpha/3 = 0.9667` -- mot thong ke DUOI, can
nhieu mau. `c` la mot phan vi o GIUA (~0.57 cho acceptance 0.43) -- mot thong
ke TRUNG TAM, hoi tu nhanh hon nhieu.

=> Cai C3 mua duoc (mot phat bieu bao phu voi chung chi mau-huu-han) duoc tra
   bang mot yeu cau co mau lon hon, o dung cho ma bao dam duoc phat bieu.
```

Va `err|accept` cua B2 tu 10 block la **0.0826**, so voi C3 dung toan bo 500
block la **0.0746**. Chenh 0.008. Khop voi `M-196` cua Task B (trung vi
`|derr|` = 0.00526): hai phuong phap gan nhu khong khac nhau ve risk.

## 4. Doc dung -- ba cai bay trong chinh bang tren

### 4.1. "C3 dat `viol <= alpha` tu `n = 30`" la mot cau BAY

`smallest_n_C3_viol_le_alpha = 30` tren ca 8/8 cell. Nhung o `n = 30`:

```text
acceptance = 0.2089  (muc tieu 0.427)      -> chap nhan mot NUA so hang
viol       = 0.0033  (alpha = 0.10)        -> bao thu gap 30 lan
sup ve none = 98%                          -> va no dang chay `none`
```

`viol` thap o day khong phai vi thu tuc tot; no thap vi thu tuc gan nhu khong
chap nhan gi. Cung hinh dang voi doc 44 muc 4.4 va voi `L99`: **mot thang do
"an toan" duoc toi da hoa boi viec khong hanh dong.**

> Moi phat bieu "C3 dat bao phu tu `n` block" PHAI kem mot san ACCEPTANCE.

### 4.2. B2 khong co `viol|accept`, va o trong do la ket qua  (`A067b` muc 2)

Ban dau Task B-2 ghi `viol|accept` cho B2, do bang `s > qhat` voi `qhat` cua
C3 -- tuc MUON `qhat` cho B2, dung cai bay `A066` muc 3 da tu choi. O day no
con te hon: khi `qhat = +inf` thi `s > qhat` sai voi moi hang, nen B2 hien ra

```text
n = 10   B2_viol_given_accept = 0.0000      <- "hoan hao"
```

Mot con so hoan hao sinh ra tu mot cong cu do hong. **Da bo truong nay** truoc
khi ket luan. Dai luong so sanh duoc cua B2 la `err|accept`, khong can `qhat`.

### 4.3. Cot B2 phai co MUC TIEU CO DINH  (`A067b` muc 3)

Neu `c` chi duoc khop voi acceptance cua C3 tren CUNG mau, thi duoi san C3
chap nhan 0 hang va B2 bi keo ve 0 theo -- cot B2 o `n` nho se khong noi duoc
gi ve B2. Bien the `c_B2_fixed` do `c` tu `n` block de dat diem van hanh mong
muon cua cell. `target` la mot lua chon THIET KE, khong phai thu hoc duoc tu
`n` block, nen no khong lam ro ri du lieu vao `c(n)`.

## 5. `L100` -- co cua `L93` MU dung trong truong hop cua `L95`  (`G23-260`)

Cot `co C3` khong don dieu theo `n`: 100% -> 100% -> **2%** -> 95% -> 1%.
Cai hom o `n = 30` la mot lo hong that.

```text
`qhat_at_sample_max` tinh tu `min_blocks_at_final_qhat`,
ma truong do la `None` DUNG khi vong lap suy bien o vong 0 -- tuc dung
truong hop `L95`.

=> mot lan chay VUA chay `none` duoi nhan `selective`
   VUA o che do `qhat = max mau`
   se KHONG duoc mot co nao bat.
```

Do duoc tai `n = 30`:

```text
hai co `L91`/`L93`                         2%
`qhat_source == degenerate_fallback_to_none`   98%
cong lai                                 100%

8/8 cell co ti le `qhat_source` LON HON ti le hai co  ->  G23-260
```

**98% so lan chay o `n = 30` la `none` doi ten, va he thong co cu bat duoc
2%.** Truong `qhat_source` (`A065d`) bat duoc 100% -- do la ly do no khong
phai mot phep doi ten trang tri: no la co duy nhat con nhin thay o vung giao
cua `L93` va `L95`.

KHONG sua co (`A067b` muc 1.1): `min_blocks_at_final_qhat` co nghia "so block
o vong DA SINH RA `q`", ghi mot so vao do khi suy bien se lam truong nay noi
doi; va `M-199` da ky voi HAI co.

## 6. Ket luan Task B-2 -- ba cau

```text
1. Menh de "yeu cau co mau DO DUOC" cua C3 la THAT va do duoc: 100% so lan
   duoi san hop le, C3 gan co va tu choi. B2 tra ve mot `c` huu han o 100% so
   lan va khong co dai luong nao de biet no vo nghia. (`M-199`, `G23-259`)

2. Cai gia cua hieu biet do la mot yeu cau co mau LON HON: C3 can 120 block
   de dat trong 0.05 cua diem van hanh va 500 block de dat trong 0.02; B2 can
   20 va 60. Ly do co che: `qhat` la mot phan vi DUOI (0.9667), `c` la mot
   phan vi TRUNG TAM.

3. Ve risk, hai ben van gan nhu khong khac nhau: `err|accept` cua B2 tu 10
   block la 0.0826, cua C3 tu 500 block la 0.0746. Khop voi `M-196`.
```

> 🔑 Chon giua C3 va B2 KHONG phai chon "dung" hay "sai". No la chon giua
> **mot thu tuc tu choi khi thieu du lieu va doi nhieu du lieu hon**, va
> **mot thu tuc luon tra loi va khong bao gio noi cho ban biet khi nao no
> doan**. Ca hai deu la mot lua chon ve NGAN SACH MAU -- dung ket luan thu ba
> cua Lesson 23.22 (doc 43 muc 17), nay do o chieu tai hieu chuan.

## 7. Cai con lai

```text
1. `L100` chua duoc sua trong `config_matrix.py` (co y, `A067b` muc 1.1).
   Neu mot lesson sau can mot co DAY DU, dung `qhat_source`, dung `L93`.

2. Bang muc 3 do o `kappa = 0.5`. Yeu cau co mau cua C3 phu thuoc `kappa`
   (`M-192`): o `kappa` lon hon tap chon co lai va can nhieu block hon nua.
   Chua do.

3. `n` nho nhat de B2 dat CUNG `err` nhu C3 -- chua cham, vi hai duong cong
   `err` gan nhu song song va khong cat nhau trong luoi `n` da chay.
```

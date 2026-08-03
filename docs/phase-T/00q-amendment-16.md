# AMENDMENT 16 -- Phase T / T.6c noise-floor check

Ngay viet: 2026-08-03
Trang thai: viet sau T.6b, truoc khi chay phep kiem `se_batch_ms` theo Phan 3.

## Boi Canh

T.6b cho thay baseline khoi C khong phat hien lech mo hinh co y nghia, nhung
D-T2 tren `err_dyn` van fail manh:

```text
D-T2 err_dyn Lambda>=10: pass 6/100, fail 94/100
mean_abs_ratio = 0.896688
```

Trong khi do, bang 9 o cho thay ket luan theo trung binh o on dinh hon nhieu:
8/9 o khong phat hien sai so dong luc, con `cbr@0.98` la o duy nhat lech lon.

Chan doan can kiem: D-T2 fail vi kiem tung diem duoi san phan giai cua phep do,
khong phai vi sai so quasi-static he thong lon.

## Du Doan Truoc Khi Chay

Phep kiem se so `se_batch_ms` trung binh cua cac sealed main rows voi
`sd_err_dyn_ms` trong bang 9 o T.6b.

Du doan khoa truoc khi chay:

```text
P1. Voi cac o h2/poisson, mean(se_batch_ms) se nam trong dai 0.05--0.28 ms.

P2. Voi cac o h2/poisson, mean(se_batch_ms) se cung bac voi sd_err_dyn_ms:
    ty_le = mean(se_batch_ms) / sd_err_dyn_ms nam trong [0.5, 2.0]
    cho it nhat 6/8 o.

P3. Voi cbr@0.98, mean(se_batch_ms) se cung bac voi sd_err_dyn_ms nhung duoc
    phep lon hon dai h2/poisson vi critical slowing down; bao cao rieng,
    khong dung de dat nguong cho 8 o on dinh.

P4. Neu P1/P2 dung, D-T2 tung diem phai duoc phat bieu lai la bi gioi han boi
    san nhieu. Ket qua confirmatory cu van bao cao, nhung ket luan khoa hoc
    chinh phai dua tren trung binh o va can tren 95%.
```

## Bao Cao Bat Buoc

Bang T.6c phai co moi o `(mode, rho_bar)`:

```text
mode, rho_bar, sd_err_dyn_ms, mean_se_batch_ms, mean_se_naive_ms, ratio_batch_to_sd
```

Va phai ghi ro day la **exploratory diagnostic** sau T.6b.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-03

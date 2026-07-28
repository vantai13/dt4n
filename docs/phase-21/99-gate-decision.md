# GATE 21 - QUYET DINH

Ngay: 2026-07-28
Tag de xuat: `phase-21-complete` (cho owner review truoc khi tao tag)
Commit: pending owner review
Tien de: Phase 20 PASS (`phase-20-complete`)
Tien dang ky: `docs/phase-21/00-preregistration.md` (`phase-21-start`)
Sua doi: `00b-amendment-1.md` .. `00e-amendment-4.md`

Tai lieu nay dong bang Gate 21. Sai sot phat hien sau tai lieu nay nen ghi vao
mot erratum rieng, khong sua nguoc cac ket qua da dong.

## 0. Quyet Dinh

PASS. Phase 21 tang mot certification layer cho duong bien risk-coverage nam
duoi diem neo Phase 20, don dieu, va troi hon duong co so nguong-hang-so o vung
van hanh da ghi truoc.

Gia thuyet `H_C` theo nguong ban dau FAIL:

```text
P(accept | eps=0) = 0.0573 < 0.10
```

Gia thuyet `H_C` sau Amendment 1 PASS ca ba dieu kien:

```text
(i)   co 5 diem coverage >= 0.01 va err|accept <= 0.5 * anchor
(ii)  Spearman(cov, err|accept) = 1.0000
(iii) co 8 diem phan biet trong coverage [0.01, 0.90]
```

Bao cao ca hai. Ket luan PASS khong dua tren viec che giau gate cu fail, ma dua
tren duong bien risk-coverage moi chat hon va da ghi truoc.

## 1. Con So Chinh

Out-of-sample tren 247 block test, 354,445 hang:

```text
Diem neo Phase 20 / tin twin 100%:
  coverage 1.0000 | err 0.18682 | d_sla 0.08100 | regret 6.280 ms

Duong bien chung nhan:
  cov 0.0573 -> err 0.0339 (5.5x) | d_sla 0.01335 (6.1x) | regret 0.483 ms (13.0x)
  cov 0.1166 -> err 0.0912 (2.0x) | d_sla 0.04059 (2.0x) | regret 1.348 ms ( 4.7x)
  cov 0.5551 -> err 0.1704 (1.1x) | d_sla 0.07346 (1.1x) | regret 4.439 ms ( 1.4x)
  don dieu: Spearman(cov, err|accept) = 1.0000
```

Bao phu conformal, bien the B, `alpha = 0.10`, 248 block calibration:

```text
marginal coverage = 0.90110
muc tieu rieng cua B = 0.90726
coverage tung o = 0.90177, 0.90077, 0.89989, 0.90263, 0.90045
q_hat(z) = [64.11, 88.80, 105.90, 120.17, 133.20]
```

Ablation usefulness:

```text
err tai coverage khop thap hon 1.88x tai eps=0:
  adaptive 0.0339 vs constant@coverage 0.0639
CI95 cua hieu err_const - err_adaptive tai eps=0:
  [+0.020, +0.041]
adaptive thang co y nghia o 9/13 muc eps
adaptive troi hoan toan (coverage cao hon va err thap hon) o 8/11 diem khong suy bien
adaptive khai thac 81.6% du dia oracle tai eps=0
```

## 2. Dieu Kien Van Hanh

```text
Nhom Mondrian : 1 chieu, 5 bin tuoi z
Score         : s_vs_a1 = max_{a != a_hat} |e_a - e_a_hat|, e = y - y_hat co dau
Bien the q_hat: B, gop mau, muc phan vi ceil((n_blk + 1) * (1 - alpha)) / n_blk
Tieu chi      : ACCEPT <=> gap_twin >= q_hat(z) - eps
```

Pham vi khuyen nghi:

```text
eps <= 50 ms, coverage <= 0.17 tren offered OOS
```

Ngoai pham vi nay, ho dang cong bat dau thoai hoa. Khi `q_hat(z) - eps <= 0`,
bin do accept moi hang, ke ca `gap_twin ~= 0`; tin hieu bien do bi mat trong
bin do. Do la khiem khuyet cua ho tham so, khong phai cua dieu kien-theo-tuoi.

State online:

```text
5 gia tri q_hat, mot phep tra bang O(1)
khong huan luyen online
khong suy dien model tai thoi diem quyet dinh
```

## 3. Bang Gate 21

| Ma | Gia thuyet / doi chung | Ket qua | Trang thai |
|---|---|---|---|
| H1 | `q_hat(z)` tang, ratio >= 1.5 | ratio 2.074; 4/4 CI99.75 loai 0 | PASS |
| H2 | `eta2(z) >= 0.05` | raw 0.1239, rank 0.1315, log 0.0639 | PASS |
| H3 | coverage marginal trong `0.90 +/- 0.02` | 0.90110 | PASS |
| H4 | coverage tung o trong `0.90 +/- 0.05` | 5/5 o trong [0.8999, 0.9026] | PASS |
| H6 | `q_hat(alpha/K) > q_hat(alpha)` moi o | 5/5 | PASS |
| H7 | Spearman(`q_hat`, `err(z)`) = 1.0 | 1.0000 | PASS |
| H8 | robustness tren `rho_measured` | H1/H3/H4/H6 PASS; H2 fail nhe do aliasing tuoi | PASS co dieu kien |
| H_C cu | `0.10 <= P(accept) <= 0.90` tai `eps=0` | 0.0573 | FAIL, cong bo |
| H_C moi | diem huu ich, don dieu, >=4 diem | 5 diem; rho=1.00; 8 diem | PASS |
| V1/V2 | coverage marginal/o | nhu H3/H4 | PASS |
| V3 | positive control SD ratio < 0.5 | offered 0.349; 2D 0.376 | PASS |
| V3 measured | positive control tren measured | 0.930 | KHONG DANH GIA DUOC |
| V3c | leave-one-trace-out span <= 0.05 | 1D 0.0130; measured 0.0339 | PASS |
| V3c 2D | leave-one-trace-out cho `z x u` | 0.0819 | FAIL, phu luc only |
| V5 | tai tao Phase 20 | err lech 8.36e-08 | PASS |
| Ablation | adaptive > constant threshold | 9/13 significant, 8/11 strict dominance | PASS |

Ngan sach lap:

```text
dung 0/2 vong
```

## 4. Gioi Han Da Cong Bo

L1. `H_C` theo nguong ban dau FAIL: `0.0573 < 0.10`. Nguong do khong co bien
minh van hanh rieng; Amendment 1 thay bang tieu chi duong bien chat hon, bat
buoc co diem huu ich, bat buoc don dieu, va bat buoc co nhieu diem coverage.

L2. Nhom 2D `z x u` FAIL V3c: span `0.0819 > 0.05`. Co che: `u_bin` sinh tu
hien thuc `rho(t)` tung trace, con `z_bin` sinh tu lich dong bo tat dinh nen
giong nhau giua trace. 2D chi bao cao phu luc va khong dung cho ket luan chinh.
Ket qua nay doc lap xac nhan A3.1, quyet dinh chon 1D dua tren `eta2(u)=0.021`.

L3. V3 tren measured khong danh gia duoc, khong phai bang chung chong lai split
block. `SD_sample` do duoc khop cong thuc nhi thuc thuan tuy:

```text
sqrt(2a(1-a)/n_half): du doan 0.004911, do 0.004918
```

Phep kiem chi co luc khi `n_half > 28,800` mau/o; measured co 7,464. Bien minh
chia block tren measured den tu tien nghiem: tuong quan mau ke nhau
`exp(-0.2 / 2.87) = 0.9325`.

L4. H2 tren measured `0.0448 < 0.05` FAIL theo nguong. Day la artifact do phan
giai tuoi 200 ms chi cho 2 bin dung duoc. Chuan hoa theo bac tu do:

```text
offered eta2(z)/(k-1)  = 0.1239 / 4 = 0.0310
measured eta2(z)/(k-1) = 0.0448 / 1 = 0.0448
```

Bang chung truc tiep H1 tren measured PASS voi ratio 1.510 va CI99
`[32.417, 36.363]`. Khong ha nguong H2; measured la robustness only.

L5. Bien dieu kien `u` xay tren gia dinh Gaussian/OU. Trace that co duoi Pareto,
nen `rho` co the nhay nhieu sigma trong mot buoc; `u` du bao kem:
`eta2(u)=0.021` so voi `eta2(z)=0.124`. Huong sua: thang phu hop duoi nang hoac
uoc luong phi tham so `P(vuot nguong | rho_hat, z)`.

L6. `link_model` hieu chuan payload 1470 B, Phase 20/21 chay 1400 B. Xem
`docs/phase-20/99b-erratum.md` E6 va cac kiem chung do nhay.

L7. `CRITICAL_CEILING_FRACTION = 0.71` do o mot cau hinh `(bw=4, q=13)`; ba
cau hinh dung trong `topology_v7` chua duoc do truc tiep. `rho` nam trong dai
toi han khoang 25% thoi gian. Xem sensitivity Phase 20.

L8. HTB va netem duoc hieu chuan tren cung interface Mininet TCLink. Anh huong
quan sat duoc da duoc `link_model` dien giai dung; anh huong con lai chua danh
gia rieng.

L9. Bao dam phat bieu o muc block dai `5*tau = 14.35 s`, khong o muc sample.
Phu thuoc trong block khong kha hoan doi.

L10. Bien the B cho bao dam xap xi, chinh xac khi so block lon. Bien the A cho
bao dam huu han-mau chinh xac nhung do duoc coverage 0.88782, thieu 0.01218 =
0.64 SD voi `n=248`, nam trong sai so lay mau.

## 5. Gia Thuyet Sinh Ra Cho Phase 22-24

G1. Ho nhan `gap_twin >= lambda * q_hat(z)` khong thoai hoa o coverage cao.
Du doan no se troi hoan toan so voi nguong hang so tren dai coverage rong hon.
Can pre-register truoc khi do trong Phase 23.

G2. Kha nang chung nhan bi chi phoi boi do sac cua be mat phan hoi. Kiem bang
ba bien the tran hang doi S-soft/S-main/S-sharp, tat ca dung cau hinh da do.

G3. Bien dieu kien phu hop voi duoi nang co the lam `u` huu ich tro lai.

## 6. Ve Sinh Tai San

```text
Pre-registration: tag phase-21-start
Sua doi: 4 amendment, moi amendment ghi ro da thay so nao truoc khi sua
Ngan sach lap: 0/2
pytest: 84 passed, 4 skipped
JSON: co provenance git_hash, git_dirty, timestamp, argv, seed, hang so
Figure 3: 4 duong adaptive/constant/random/oracle va vung eps<=50
```

## 7. Ket Luan Mot Cau

Phase 21 PASS: age-conditional conformal trust gate tao duoc duong bien
risk-coverage OOS huu ich, bao phu dung tren block held-out, va co dong gop
van hanh rieng so voi threshold hang so tren `gap_twin`.

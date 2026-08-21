# 14 -- Lesson 23.7-quater: ket luan thay the duoi residual tuong doi

Code: `cert/conditioning_audit.py --relative`  
Prereg: `docs/phase-23/00zn-amendment-37.md`  
Artifacts: `results/phase-23/relative_conclusions_*.json`

## 1. Ket qua chinh

Nhanh tuyet doi/per-link/clip cua Lesson 23.7 van duoc giu nhu doi chieu
`SUPERSEDED_BY_AMENDMENT_35`. Ket luan thay the dung:

```text
loss'_p = loss_p * (1 + r_rel)
```

Tai cell chinh, ket luan ve sai so he thong **khong dao dau**. `Delta` di tu
`-0.012868849` xuong `-0.016299076`; do lon dem am tang `26.66%`. Nhanh cu
tung cho `Delta=+0.044874962` tai point, nen dau duong cu duoc xac nhan la
artifact cua phep bom da bi supersede, khong phai ket luan thay the.

Hai cell held-out khong dong nhat. `poisson@0.850` di tu `+0.003120206` sang
`-0.005618371`, con `h2@0.700` van duong nhung giam tu `+0.003866255` xuong
`+0.002316153`. Vi vay phat bieu manh dung tai cell chinh va poisson held-out,
nhung khong duoc ngoai suy thanh `Delta<0` cho moi traffic family.

## 2. Cham M-34..M-39 khong retune

| ID | Dai khoa | poisson@0.925 | poisson@0.850 | h2@0.700 |
|---|---:|---:|---:|---:|
| M-34 flip given reject | 0.02--0.10 | 0.015201 MISS | 0.042103 HIT | 0.009592 MISS |
| M-35 flip given accept | 0.000--0.008 | 0.008667 MISS | 0.022004 MISS | 0.002636 HIT |
| M-36 Delta relative | -0.010--0.000 | -0.016299 MISS | -0.005618 HIT | +0.002316 MISS |
| M-37 Delta van am | CO | CO HIT | CO HIT | KHONG MISS |
| M-38 PC chi bom test | 0.85--0.90 | 0.847000 MISS | 0.872218 HIT | 0.862609 HIT |
| M-39 NC bom calib+test | >=0.89 | 0.922065 HIT | 0.923269 HIT | 0.920537 HIT |

M-36 cell chinh MISS o phia am hon dai (`-0.01630 < -0.010`), nen la miss
prereg nhung khong phai dao dau bat loi. M-38 cell chinh thieu cận duoi
`0.003000`; van phan biet ro voi NC, nhung khong duoc doi thanh HIT.

## 3. Flip co dieu kien va vai tro cua cong

| Cell | flip all test | flip given accept | flip given reject | reject/all concentration |
|---|---:|---:|---:|---:|
| poisson@0.925 | 0.010105 | 0.008667 | 0.015201 | 1.504351 |
| poisson@0.850 | 0.026426 | 0.022004 | 0.042103 | 1.593245 |
| h2@0.700 | 0.004166 | 0.002636 | 0.009592 | 2.302181 |

`flip_given_reject > flip_given_accept` va concentration ratio `>1` tren ca
ba cell. Day la bang chung co che rang flip don vao tap tu choi, dung noi
`c_F2` va `c*` duoc tinh. Tuy nhien M-34/M-35 van phai cham MISS neu nam
ngoai dai khoa; quan he thu tu khong duoc dung de thay the prediction da ky.

Moi cell co `389,974` test rows chap nhan va `109,993` test rows tu choi.
Dong nhat thuc gop lai conditional flip cho `identity_residual=0.0` chinh xac
tren ca ba cell.

## 4. Doi chung coverage M-38/M-39

| Cell | baseline | PC: qhat goc, test moi | NC: calib moi, test moi |
|---|---:|---:|---:|
| poisson@0.925 | 0.922749 | 0.847000 | 0.922065 |
| poisson@0.850 | 0.922319 | 0.872218 | 0.923269 |
| h2@0.700 | 0.920667 | 0.862609 | 0.920537 |

NC giu coverage tren nominal `0.90` o ca ba cell. PC tut ro khi chi test bi
bom, nen cap doi chung van phan biet duoc du cell chinh nam nhe ngoai dai
M-38 da khoa.

## 5. Dinh chinh ke toan M-28

Huong dan hau kiem da gan nham ten cho hai uoc luong. Tai sinh truc tiep tu
raw B/C seed `104..108` va doi chieu voi `per_unit/baseline_per_seed` cho:

| Mode | mean-of-ratios (M-28) | ratio-of-means (chan doan) |
|---|---:|---:|
| poisson | -0.164744220 | -0.164792793 |
| h2 | -0.066384422 | -0.066444530 |

Hai duong tai sinh khop tung seed. M-28 dung mean-of-ratios vi estimand can
ngoai suy la ti le. Sai khac nho khong doi verdict M-28.

## 6. Kiem soat va gioi han dien giai

Ca ba artifact dat:

```text
accept_set unchanged       : true
y_hat unchanged            : true
weighted flip identity     : 0.0
relative path clip ratio   : 0.0
git_dirty                  : false
```

Ket qua nay lap lo trong "rut ma khong thay the" cho cell chinh: duoi mo
hinh relative dung scope, `Delta` van am. No khong dong L10 vi residual vi
sai `r_P1-r_P3` van chua duoc do xong. Campaign Amendment 36 tiep tuc bi tam
dung tai checkpoint 5 row cho den khi quyet dinh tiep tuc Mininet.

## 7. S9 -- bat bien chi co gia tri tren truc da do

`tools/lift_decomposition_by_cell.py` chi tai phan ra artifact G23-23 da
commit tu 15/08; no khong do du lieu moi. C3 tai coverage `0.78` cho:

| Cell | twin_deg | prior_deg | lift | swing | Delta |
|---|---:|---:|---:|---:|---:|
| poisson@0.925 | 0.230948 | 0.054576 | 0.176372 | 0.117878 | -0.012869 |
| poisson@0.850 | 0.235830 | 0.125570 | 0.110259 | 0.124442 | +0.003120 |
| h2@0.700 | 0.237723 | 0.224379 | 0.013344 | 0.030918 | +0.003866 |

```text
twin_deg  max/min = 1.029x
prior_deg max/min = 4.111x
swing     max/min = 4.025x
```

C3 loc ra tap ma twin suy giam them gan 23 diem phan tram rat on dinh tren
ca ba cell. Thanh phan mat on dinh la fallback P1: tren tap reject, no cung
xau di va muc suy giam thay doi hon bon lan qua cell. Vi vay nut co chai
cross-cell la fallback, khong phai kha nang phat hien hang kho cua certificate.

Lesson 23.1 noi `prior_deg` gan nhu hang so khi quet `kappa` trong
`poisson@0.925`. Amendment 19 va muc gioi han trong `02-fallback.md` da thu
hep phat bieu nay dung truc. S9 lam nguyen tac do noi bat trong bao cao hien
tai: **mot bat bien chi co gia tri tren truc no duoc do; khong duoc chuyen tu
truc kappa sang truc cell ma khong do lai.**

## 8. Ket qua transfer C3 so voi B2

Tu cung artifact G23-23:

| Cell | B2 Delta | C3 Delta | C3 - B2 |
|---|---:|---:|---:|
| poisson@0.925 | -0.012984857 | -0.012868849 | +0.000116008 |
| poisson@0.850 | +0.004664308 | +0.003120206 | -0.001544102 |
| h2@0.700 | +0.007504495 | +0.003866255 | -0.003638240 |

B2 thang C3 `0.000116` tai cell hieu chuan, nhung C3 thang `0.001544` va
`0.003638` khi chuyen cell. Day la ket qua transfer/descriptive da ton tai:
C3 thoai hoa duyen dang hon nguong hang so duoc chinh tai cell goc. Bang nay
khong duoc dien giai thanh C3 co Delta am tuyet doi tren moi cell.

## 9. Residual tuong doi la objective misspecification

Voi `r_rel` ap dung chung tai tang path:

```text
cost'_p = delay_p + w_loss * loss_p * (1 + r_rel)
        = delay_p + w_eff * loss_p
w_eff   = w_loss * (1 + r_rel)
```

Tai cell chinh, `w_loss=1451.376578` va mean-of-ratios
`r_rel=-0.164744220`, nen `w_eff=1212.270676`, hay ti so `0.835255780`.
Do do Lesson 23.7-quater cung chinh xac la mot phep thu **objective
misspecification**: twin/gate van duoc tao theo `w_loss`, con ground truth
duoc cham theo `w_eff`.

Huong sai lech do duoc ha trong so loss, lam delay chiem ti trong lon hon va
co the co loi cho fallback P1. Day la confound phai cong khai khi dien giai
M-36; no khong phai bang chung rieng rang residual lam certificate tot hon.
Phep quet `w_eff/w_loss` hai phia quanh 1 se tach diem do nay khoi do ben dau.

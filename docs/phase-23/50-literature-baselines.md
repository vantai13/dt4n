# LESSON 23.23 -- LITERATURE BASELINE VA KHOANG KHONG-CONFORMAL

Ngay chay: 2026-08-27  
Cell: `poisson@0.925`  
Artifact: `results/LIVE/phase-23/baselines_lit.json`

## 1. Cau hinh, wiring va doi chung am

Tat ca C3/B8 dung cung split block, `POST_VARIANT=selective`, Bonferroni
`alpha_family=0.10`, `alpha_each=0.03333333333333333`, va `kappa=0.50`.
Du lieu co 999,495 hang; moi nhanh CALIB/TEST co 500 block.

`G23-289` PASS bit-for-bit: `max_abs_diff=0`, acceptance `0.395461650`,
`viol|accept=0.081721159`. `G23-290` chay du 200 hoan vi: `viol` mean
`0.078238594`, p95 `0.078443981`, max `0.078563159`; acceptance mean
`0.364949800`. p95 da duoc ghi vao A072 TRUOC nhanh chinh.

NC khong o cung diem van hanh voi C3: acceptance thap hon `0.030511850`
(7.72% tuong doi). Vi vay KHONG duoc doc `C3 > NC p95` nhu mot so sanh truc
tiep. Them nua, metric gop qua bin khong do rieng coverage co dieu kien ma
Mondrian mua. Hai diem nay vao `L128`.

## 2. Ket qua C3 va B8

| thu tuc | acceptance | `viol_given_accept` | `err_given_accept` | `err_system` | san acceptance |
|---|---:|---:|---:|---:|---|
| C3 conformal | 0.395462 | 0.081721 | 0.083978 | 0.274787 | dat |
| B8a Gaussian ngay tho `[MO TA]` | 0.673292 | 0.547114 | 0.154273 | 0.236413 | dat |
| B8b folded-Gaussian steel-man | 0.405077 | 0.087444 | 0.086742 | 0.273584 | dat |
| B8c plug-in quantile `[MO TA]` | 0.403601 | 0.088096 | 0.085865 | 0.273694 | dat |
| B8d block bootstrap percentile | 0.388199 | 0.076945 | 0.081461 | 0.276027 | dat |

B8b/B8c/B8d gan C3 ve so hoc, nhung KHONG co paired CI de goi la “khong
phan biet duoc” theo nghia thong ke. Tren bon thu tuc nay, span acceptance la
`0.016878`, span `viol|accept` la `0.011151`, span `err|accept` la `0.005281`.

## 3. Phan quyet -- kich ban K3 (`A072` muc 7)

CL-12 KHONG duoc phat bieu. `M-227` khong fire: 0/12 o co
`CI95_lo(CV) > K08`. `M-226` khong cung cap bang chung vo coverage:
`viol|accept` toan cell cua B8b la `0.087444`, duoi `alpha=0.10`; dai theo
bin `3/5` lai HONG-KHI-KY vi truc chi co 4 bin (`A073`).

CL-13 KHONG duoc nang. `M-230` khong fire 0/4 o, nhung day la dai KHONG THE
FIRE tren cell nay: moi o co 500 block, trong khi nguong tu choi la 29.
Ket qua khong fire KHONG mang thong tin ve CL-13; xem `A073` va `L125`.

## 4. Ket luan co the phat bieu

### 4.1. [MO TA] Hinh dang gan bien half-normal

CV trung binh 12 o la `0.756496597`; gia tri half-normal dung la
`sqrt(pi/2-1)=0.755510640`, lech `+0.1305%`. Tung o trai
`0.746884644..0.762847283`, do lech tuyet doi lon nhat `1.1417%`.

Day la mot giai thich co che hop ly cho K3: score nam gan bien `theta=0` cua
ho folded normal. Nhung bat doi xung M-227 van giu nguyen: CI khong vuot K08
KHONG chung minh Gaussian dung. Do do ket qua nay mang nhan `[MO TA]`, khong
chong do CL-12.

### 4.2. B8a hong vi cong thuc, khong phai vi Gaussian

Voi half-normal, `sd(|d|)/sigma=0.602810275` va
`q_(1-alpha/3)(|d|)/sigma=2.128045234`, nen ly thuyet cho
`q_B8a/q_dung=0.519492052`. Quan sat `q_B8a/q_C3=0.474172..0.510975`.
`viol|accept=0.547114` cua B8a la hau qua cua cong thuc thieu tham so vi tri;
no KHONG phai bang chung chong Gaussian. Nhan `[MO TA]` duoc giu.

### 4.3. B7 thoai hoa va tra mon no W9

B7 dung reject rule cua Chow (1970), voi nguong dat tren tuoi theo ket qua
cau truc cua Sun et al. (2017). Ba dieu chinh chuyen mien:

1. Xac suat hau nghiem cua Chow duoc thay bang loss ky vong do theo bin tuoi.
2. Nguong tin cay duoc dat tren tuoi; Sun et al. chi bien minh hinh dang.
3. Chi phi tu choi ngoai sinh duoc thay bang loss F2 STATIC tren CALIB.

`L_act` tang `0.177362 -> 0.230312 -> 0.269766 -> 0.297545`, tuc +67.76%,
nhung van luon duoi `L_fallback=0.365968`. Vi vay `h*=0.618125 s`, bang tuoi
lon nhat quan sat, va B7 thoai hoa thanh acceptance `1.0`.

B7 co `err|accept=0.238841`; C3 co `0.083978` tai acceptance `0.395462`, ti
so `2.844x`. Ket qua dung: tuoi CO tin hieu nhung mot nguong-tuoi-thuan khong
du de tu choi co loi duoi F2 static; can dai luong bien co dieu kien. Gioi
han: `h*` phu thuoc fallback; sticky/wait chua duoc thu (`L127`). B7 khong co
claim coverage va o `viol` phai de trong.

### 4.4. [MO TA] Gia thuyet du duoi tang theo tuoi

Tu output da gated, khoi phuc `sd(s)=q_B8a/Z_BONF` va so
`q_C3/sd(s)` voi gia tri half-normal `3.530207301`. Du duoi trung binh theo
slot o bon bin la `+3.71% / +4.62% / +4.69% / +7.55%`: tang don dieu, bin
cuoi gap khoang hai bin dau.

Day la gia thuyet sinh SAU khi xem du lieu. No KHONG chong do CL-* nao va
khong cho phep chay them alpha trong lesson nay. Xem `L126`.

## 5. Hai sai sot tien dang ky

A072 viet `>=3/5` va `>=4/5`, nhung nam canh Z chi tao bon bin. Khong doi
thanh 3/4 hay 4/4 sau khi xem du lieu. M-226/M-229 theo-bin ha xuong MO TA.

M-230 cung bat kha thi: 500 block/o >> san 29. Tu Lesson 23.24, A073 R5 bat
moi dai “ton tai >=k o” phai ghi dieu kien kha thi va co test truoc nhanh do.

Phep dao MoM `theta=h^-1(r)` dieu kien xau gan 0. Theo N5, chi `q_hat` duoc
dien giai; khong bao cao rieng `mu_hat` hay `sigma_hat` nhu uoc luong co y
nghia.

## 6. Ngan sach

```text
Gate da dung : G23-289 .. G23-296 = 8 / 8
Gate mo them : 0
```

Lesson het ngan sach. L125..L128 vao BACKLOG; khong phep do nao trong bon
dong do duoc chay o 23.23.

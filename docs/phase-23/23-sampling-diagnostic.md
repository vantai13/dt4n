# Lesson 23.19 Task A -- Chan doan lay mau probe

Ngay     : 2026-08-22
Prereg   : `docs/phase-23/00zzc-amendment-46.md` (tag `amendment-46`)
Artifact : `results/LIVE/phase-23/aoi_sampling_diagnostic.json`
Du lieu  : `results/RAW/phase-23/aoi_v7_campaign`, 15 run CLEAN, KHONG do moi

## 1. Ket qua: H7 -- phan bo do duoc BI THIEN LECH

```text
M-100  KS(u) trong 1 run 1 link, max :  0.18063   (trung vi 0.11588)   MISS
M-101  KS(u) gop 15 run, max         :  0.12812                        MISS
M-103  histogram 50 bin, max/min     :  152.0                          MISS
M-104  khoang probe 100.108 ms, jitter sd 0.0791 ms                    MISS

PHAN XU (cong thuc, amendment 23-46 muc 6): H7_BIASED_MUST_CORRECT
```

`u` = vi tri chuan hoa trong chinh khoang refresh cua mau do,
`u = (t_obs - t_source - d_link) / T_eff`. Neu probe lay mau deu theo thoi
gian thi `u ~ Uniform[0,1]`, khong phu thuoc `d` hay `alpha`.

Histogram cua `u` (gop 15 run, link `ac`, 50 bin):

```text
u=0.00-0.10    691   540   164   137   123
u=0.10-0.20    112   137   237   392   677
u=0.20-0.30    727   597   182   150   118
u=0.30-0.40    110   141   221   408   674
u=0.40-0.50    729   589   196   135   125
u=0.50-0.60    113   138   226   406   633
u=0.60-0.70    708   615   200   152   129
u=0.70-0.80    108   142   227   447   771
u=0.80-0.90    688   538   180   146   123
u=0.90-1.00     76    11     0     0     0
```

**Nam rang, cach deu dung `T/5`.** Ba bin rong. Ty so cao nhat / thap nhat
la 152.

## 2. Co che: khoa tuong uoc gan 5:1

```text
T_refresh   = 500.2922 ms      (do truc tiep tu t_source ke tiep, bridge-side)
khoang probe = 100.1080 ms     (do tu t_probe_start)
ty so        =   4.997524      <- gan mot so nguyen CHINH XAC

phan le -0.002476  ->  pha troi -0.2478 ms moi chu ky refresh
qua 224 chu ky (sau khi cat warm-up): troi 55.5 ms = 11.1% cua T
```

Moi run vi the chi quet duoc **11.1%** khong gian pha. Mười lăm run co pha
ban dau khac nhau nen gop lai phu nhieu hon, nhung van xa uniform
(`KS = 0.128`).

**Nguon tron pha nho hon nhieu so voi du kien.** Ban ra soat gia dinh jitter
cua `time.sleep` co 1-3 ms moi luot. Do duoc: **sd = 0.0791 ms**, nho hon
20-40 lan. Vong probe bu tru elapsed (`aoi_probe_v7.py:130`
`wait = interval - (now - t0)`), nen no giu nhip rat chuan -- va chinh su
chuan do la cai gay khoa pha.

> Mot nhac cu cang on dinh cang de bi khoa tuong uoc. Do la nghich ly cua
> phep do tuan hoan: `sleep` chinh xac hon lam phan bo do duoc TE HON.

## 3. Hai gia thuyet canh tranh deu bi BAC BO

### `alpha` khong the giai thich lech hinh dang (chung minh dai so)

Hon hop 8 phan `Uniform[d + alpha_i, d + alpha_i + T]`, trong so bang nhau.
Voi `x` trong vung phu (ca 8 phan deu phu):

```text
F(x) = (1/8) sum_i (x - d - alpha_i)/T = (x - d - mean(alpha))/T = (x - d)/T
```

vi `mean(alpha) = 0` theo dinh nghia. Vung phu la
`[d + max(alpha), d + min(alpha) + T] = [d+17.3, d+491.3]`, va `p05`, `p50`,
`p95` **deu nam sau trong vung phu**.

```text
=> alpha du doan lech = 0 o CA BA phan vi.
=> cau "lech 2% da dinh danh (alpha tron 8 rang cua lech pha)" trong bao cao
   Lesson 23.18 muc 3 la SAI. Da sua (amendment 23-46 muc 2).
```

### H8 (nghich ly kiem tra) cung khong du

```text
T_eff: E = 500.292 ms, sd = 2.297 ms, CV = 0.00459
trung vi neu Uniform[0,T]      : 250.146 ms
trung vi phan bo TUOI CAN BANG : 249.859 ms      -> chi lech -0.29 ms

M-107  trung vi mo hinh 365.990  vs  quan sat 358.141   ->  +7.848 ms   MISS
M-108  lech lon nhat qua p05/p50/p95: 8.736 ms                          MISS
```

`T_eff` qua on dinh (`CV = 0.0046`) nen nghich ly kiem tra chi giai thich
`0.29 ms` trong `7.93 ms`. **Con lai la cua cai luoc.**

## 4. He qua dinh luong: `d` khong duoc xac dinh chac nhu tuong

`d = mean(AoI) - T/2` gia dinh pha rai deu. Voi mot cai luoc, trung binh pha
lech khoi `T/2` mot luong phu thuoc pha ban dau. Mo phong lai chinh dieu kien
do duoc (`T`, khoang probe, jitter, 224 chu ky, 15 run, 400 lan lap):

```text
gop 15 run : bias trung binh +0.172 ms,  sd 3.325 ms
             khoang 90% [-5.11, +5.49] ms,  |bias| max quan sat 10.25 ms
mot run le : sd 13.170 ms,  |bias| max 24.75 ms
```

```text
=> d = 115.9 ms  +/- 6.5 ms (95%), CHI RIENG do lay mau.
```

Va dieu do sap xep lai toan bo cuoc tranh luan ve `d`:

```text
114.11 ms   trung binh hai duong (bao cao 23.18 lan dau)
115.50 ms   moment chua hieu chinh Var(alpha)
115.92 ms   moment voi T DO DUOC
116.07 ms   moment voi Var(alpha), "khop danh dinh trong 4.6 us"
   trai:  1.96 ms
   sai so lay mau: +/- 6.5 ms
=> CA BON LA CUNG MOT SO. Viec chon giua chung khong co y nghia thong ke.
```

Va no dong luon cau chuyen "positive control 4.6 microgiay": mot su khop o
muc `0.0046 ms` khong the co y nghia khi chinh dai luong do mang sai so lay
mau `6500 ms/1000`. Xem amendment 23-46 muc 1.

## 5. `T` thi KHONG bi anh huong

```text
T = 500.2922 ms
    do tu hieu hai `t_source` ke tiep -- dau thoi gian do BRIDGE dong,
    khong lien quan gi den thoi diem probe.
    8 link: 500.2875 .. 500.3370 ms, trai 0.0495 ms, n = 3615 update/link
```

Day la con so chac nhat cua ca chien dich, va no lech chu ky DANH DINH
`+0.3078 ms` -- mot do lech that, nhat quan, cua vong sync.

## 6. Duong di cho Task B

Quy tac phan xu da ky (amendment 23-46 muc 6) noi ro khi `H7`:

```text
Phan bo do duoc KHONG duoc dung lam muc tieu selfcheck.
Sinh pha LY THUYET tu T va d da uoc luong.
```

Nhung nhu vay selfcheck mat doi tuong so sanh. Duong di dung la
**mo hinh hoa CA NHAC CU**:

```text
mo hinh QUA TRINH   : z(t) = d + alpha(link) + Uniform[0, T]
mo hinh NHAC CU     : lay mau o 100.108 ms, jitter sd 0.0791 ms,
                      pha ban dau ngau nhien moi run, 224 chu ky, 15 run
selfcheck           : phan bo QUA PROBE MO PHONG phai khop phan bo quan sat
                      (p05 / p50 / p95 / hinh dang), KHONG phai qua trinh tho
pipeline dung       : qua trinh tho (dt = 5 ms doc tuy y)
```

Do la phep kiem TIEN NGHIEM dung: no kiem dong thoi mo hinh qua trinh VA mo
hinh nhac cu, va no khong the la tautology vi `d`, `T` khong duoc fit tu
`p05/p50/p95`.

```text
NO DO: chien dich tuong lai phai dung khoang probe KHONG tuong uoc voi chu
       ky sync -- vi du 97 ms, hoac ngau nhien hoa moi luot. Voi T ~ 500 ms,
       moi khoang chia het gan dung deu hong: 100, 125, 250 ms.
       Ghi vao backlog Phase 24 cung voi `t_patch_done` (23-45b muc 10).
```

**KHONG duoc** doi khoang probe roi do lai roi ghep vao du lieu nay: do la
du lieu MOI, khong phai cung mot phep do (amendment 23-46 muc 7).

## 7. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-91 | amendment 23-46 ky RIENG, co tag, TRUOC Task A | PASS |
| G23-92 | phan xu H6/H7 tinh bang CONG THUC | PASS -- H7_BIASED_MUST_CORRECT |
| G23-93 | neu H7: muc tieu selfcheck duoc hieu chinh va ghi ro | PASS -- muc 6 |
| G23-94 | dinh luong sai so lay mau len `d` | PASS -- +/-6.5 ms (95%) |

### Va cham ma gate

Ban ke hoach 23.19 danh so gate tu 91 den 102 (theo cach danh so cua ban ke hoach), trong do `G23-97`,
`G23-98`, `G23-99` **da duoc cap** cho Lesson 23.20 boi amendment 23-44 muc 5
(du doan `err_neo`, `q_hat`, so cell co loi). Task A dung `G23-91 .. G23-94`;
gate cua Task B..E se lay tu so 100 tro len, tranh vung da cap cho 23.20.

Day la va cham ma thu HAI trong hai lesson (truoc do la `L29`). `GATES.md`
da co so gate; **so LIMITS chua co**, va do la khoang trong da bat dau tra gia.

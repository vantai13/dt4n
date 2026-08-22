# Lesson 23.19 Task B + C -- `aoi_model_v7` va doi chung

Ngay     : 2026-08-22
Prereg   : `docs/phase-23/00zzd-amendment-47.md` (tag `amendment-47`)
Ma nguon : `measurements/aoi_model_v7.py`, `measurements/aoi_model_selfcheck.py`
Artifact : `results/LIVE/phase-23/aoi_model_selfcheck.json`

## 1. Mo hinh

```text
z(t, link) = d + alpha(link) + phase(t),    phase ~ Uniform[0, T]

d     = 115.9 ms  +/- 6.5 (95%)     qua probe -> MANG CI (L32)
T     = 500.2922 ms                 bridge-side, KHONG bi luoc
alpha = do theo link, bien do 25.95 ms, mean = 0 theo dinh nghia
```

`phase ~ Uniform[0,T]` la **dinh ly, khong phai gia dinh**: giua hai lan
refresh `dz/dt = 1`, va nguoi doc (controller, `dt = 5 ms`) khong dong bo voi
vong sync. Khong co gi de do -- chi `T` va `d` moi can do. Kiem: pipeline
`T/dt = 100.0584` (khong nguyen) nen quet pha gan deu; probe
`T/probe = 4.9975` nen thanh luoc 5 rang.

## 2. HAI CHE DO, tach bach

```text
process_mode()     qua trinh THAT           <- PIPELINE dung
instrument_mode()  qua trinh + probe khoa   <- SELFCHECK dung
```

Gop lam mot = nap cai luoc vao pipeline. Do la loi te nhat co the xay ra o
23.19 va tinh vi hon `d = 51 ms`: no khong lam sai MUC cua `z` ma lam sai
PHAN BO cua `z` theo tung bin tuoi.

Doi chung `M-111` chung minh selfcheck **phan biet duoc** hai che do.

## 3. Ket qua

```text
M-109b  alpha tinh lai vs cong bo, lech lon nhat :  0.970 ms   HIT
M-110   selfcheck instrument_mode                :  2/4        MISS
M-111   PC dung nham process_mode -> phai FAIL   :  FAIL       HIT
M-112   PC d = 143.6 ms -> phai FAIL o mean      :  FAIL       HIT
M-113   NC bit-exact voi sawtooth_age_steps      :  True       HIT
        (chay trong BO TEST, khong o artifact -- xem muc 6)
NC23v3-2 U0 sd 144.4226 vs T/sqrt(12) 144.4219   :  1e-5       HIT
```

### `M-109` nhu ban ke hoach ky thi KHONG ESTIMABLE

De xuat: so `alpha_fwd` voi `alpha_rev`. Chay thu cho lech toi `522 ms` tren
mot `alpha` co bien do `25.95 ms` -- vo ly. Nguyen nhan:

```text
Trong MOT chieu doc, `link` va `read_pos` cong tuyen HOAN TOAN.
Thiet ke khuyet hang (rank 8/9) -> he so tach TUY Y giua hai cot.
beta_ms_per_pos: gop = -1.61 (khop 23.8: -1.6447)
                 chi fwd = +72.24     chi rev = +72.19    <- vo nghia
```

**Luan phien fwd/rev khong chi giam bias -- no la thu lam `alpha` DINH DANH
DUOC.** Do dung la ly do `NC-R` cua Lesson 23.8 bao `design_rank 9/9`.

Thay bang `M-109b`: tinh lai `alpha` bang CUNG thiet ke tren du lieu DA CAT
warm-up (ban cong bo dung du lieu chua cat), roi so:

```text
link   cong bo    tinh lai     lech
ac      -8.690     -7.720     +0.970
ad      -8.541     -8.021     +0.520
bc      -8.559     -8.322     +0.237
bd      -6.721     -6.881     -0.160
uA     +12.111    +12.465     +0.354
uB     +17.263    +16.760     -0.503
vC      -2.682     -3.635     -0.953
vD      +5.819     +5.354     -0.465
                    lon nhat   0.970 ms   -> alpha VUNG
```

### `M-110` MISS -- va no MISS dung cho da biet truoc

```text
        dai tien doan (200 chien dich)   quan sat    
mean    [362.04, 370.51]                  366.07     TRONG
p05     [136.74, 147.46]                  143.61     TRONG
p50     [359.38, 373.45]                  358.14     NGOAI
p95     [585.44, 595.92]                  582.60     NGOAI
```

Mo hinh dung o **momen 1 va 2**, sai o **momen 3**. Nguyen nhan da xac dinh
o amendment 23-47 muc 2: `d` khong phai hang so ma la bien ngau nhien LECH
PHAI (`skew +4.045`), va lech phai cua AoI theo tung link bam sat lech phai
cua `d_transport` theo tung link (`corr = +0.9637`).

Da thu MUC 2 (lay mau `d` tu phan bo thuc nghiem): **te hon**, 1/4.

```text
Vi sao: `d` la HANG SO TRONG MOT EPOCH (moi probe cua cung mot epoch nhin
cung mot gia tri), khong phai iid theo tung mau. Lay mau iid them phuong
sai khong co that -> p05 tut tu 143.6 xuong dai [123.6, 133.8].
=> muon MUC 2 dung thi phai lay mau `d` THEO EPOCH, khong theo mau.
   Chua lam: hinh dang duoi cua `d` khong dang tin (L33).
```

**Selfcheck MISS nay la mot ket qua that, khong phai mot test hong** --
`M-111` va `M-112` chung minh selfcheck co suc phan biet: no FAIL dung khi
dung nham che do, va FAIL dung khi `d` sai.

## 3b. Test chan cua 23.17 bat duoc mot vi pham vai tro

Ban dau `aoi_model_selfcheck.py` chay `M-113` ngay trong script, tuc phai
`import sawtooth_age_steps`. `test_no_stale_axes.py` chan lai:

```text
phase-23/aoi_model_selfcheck.json: khai la measures_axis nhung nhac cu
measurements/aoi_model_selfcheck.py THUC SU dung
['measurements.decision_error', 'sawtooth_age_steps'].
```

Test dung: amendment 23-45a muc 3 quy dinh artifact vai tro MEASURES khong
duoc dung bat ky bo sinh z nao. Mot doi chung bit-exact thuoc ve BO TEST,
khong thuoc ve mot script sinh artifact -- va no da co san o
`test/test_phase23_aoi_model.py::test_negative_control_is_bit_exact`.
Da chuyen. Co che cua Lesson 23.17 vi the da chan mot vi pham THAT o
Lesson 23.19, khong phai mot vi pham gia dinh.

## 4. Phan quyet

```text
DUNG DUOC cho Lesson 23.20:
    process_mode() voi d = 115.9 ms, T = 500.2922 ms, alpha do duoc.
    Dung o momen 1 va 2. Thay `d = 51 ms` bang mot truc DO DUOC tren
    dung topology_v7 -- do la muc dich cua ca Phase 23.

GHI KEM (bat buoc):
    L32  d mang sai so lay mau +/-6.5 ms (95%)
    L33  duoi phai cua d ton tai nhung hinh dang khong dang tin;
         mo hinh coi d la hang so nen trung vi lech 7.93 ms = 2.2% cua T
    L34  diem doi dau gan nhat (98.3 ms) noi suy tuyen tinh qua khoang
         124 ms -- khoang cach an toan, khong phai phep do chinh xac

CHUA LAM (khong chan 23.20):
    lay mau `d` theo EPOCH de dong momen 3
    Task D (khoa Z_EDGES) va Task E (tich hop build_calib_set_v3)
```

## 5. Gate

| Gate | Noi dung | Trang thai |
|---|---|---|
| G23-95 | NC bit-exact voi `sawtooth_age_steps` | PASS |
| G23-96 | selfcheck co SUC PHAN BIET (M-111 va M-112 deu FAIL dung du kien) | PASS |
| G23-100 | selfcheck M-110: 4/4 thong ke nam trong dai | FAIL -- 2/4, nguyen nhan muc 3 |
| G23-101 | `alpha` vung (M-109b < 2 ms) | PASS -- 0.970 ms |
| G23-102 | `process_mode` va `instrument_mode` tach bach | PASS |

## 6. Ghi chu ve `M-113`

Doi chung bit-exact chay trong bo test
(`test/test_phase23_aoi_model.py::test_negative_control_is_bit_exact`, ba
cau hinh `n`/`dt`), khong chay trong script sinh artifact -- ly do o muc 3b.
Artifact chi ghi con tro toi test.

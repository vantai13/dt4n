# AMENDMENT 23-45 -- Du doan cho Lesson 23.18 (giai phau stall + phan ra d)

Ngay ky      : 2026-08-22
Tag          : amendment-45
Du lieu dung : results/RAW/phase-23/aoi_v7_campaign (30 run, Lesson 23.8)
               archive ~/archive/dt4n-raw-measurements-20260822.tar.gz
               sha256 a97fa0a5ebecb21ed90f85b35be14175c18f68e5181d41e8b2885c631167eceb

Trang thai: **TRUOC moi code phan tich cua 23.18.** Commit nay chi chua
mot file la chinh no.

## 0. CONG BO: da xem gi truoc khi ky

De ban ke hoach nay con gia tri, phai noi ro da nhin thay gi:

```text
DA XEM (cau truc, khong phai ket qua):
    schema cua aoi_*.jsonl va cycles_*.jsonl
    cycles cua 1/30 run: n=244 chu ky, cycle danh so 1..244, n_things=20,
        so chu ky overrun cua rieng run do = 1
    t_source LECH nhau giua 8 link trong 1 probe (phat hien co che, muc 1)
    bridge/collector.py, bridge/sync_agent.py

CHUA XEM (moi dai luong duoc du doan duoi day):
    vi tri cycle cua chu ky overrun (M-78)
    is_reconcile cua chu ky overrun (M-78c)
    thu tu scan/PATCH va tuong quan voi alpha (M-78e..g)
    CV sau khi cat warm-up (M-79), moi so d (M-81..M-85)
    corr(AoI,rho) sau cat (M-86), length-bias (M-87..89), CI long nhau (M-90)
```

## 1. SUA CO CHE: `t_source` la RIENG TUNG THING, khong dung chung

Ban ke hoach 23.18 muc 3.1 doc `bridge/collector.py:573-577` roi ket luan
`t_source` la dau chung cho ca 8 thing. **Sai.** Doc tiep:

```text
collector.py:576   't_source': t_cycle_start,   <- CHI la fallback, co nhan
                                                   "backward-compatible"
collector.py:585   data['t_source'] = t_i       <- hosts,   dau RIENG
collector.py:592   data['t_source'] = t_i       <- switches, dau RIENG
collector.py:608   data['t_source'] = t_i       <- links,    dau RIENG
```

Va docstring cua chinh ham do (collector.py:567-570) noi thang dieu nguoc lai
voi suy dien cua ban ke hoach:

> A0 (Amendment 23-42b): moi Thing mang dau thoi gian rieng tai thoi diem
> counter cua no sap duoc doc. Dau chung cho ca vong se xoa mat do lech tuoi
> giua cac link va lam estimand E3 khong do duoc.

Kiem chung tren du lieu: trong MOT probe, 8 link co 8 gia tri `t_source`
khac nhau. Vay nen:

```text
KHONG con dung:  "moi mau AoI trong cung chu ky chia se cung t_source"
KHONG con dung:  "d_transport = lock_wait + cycle_scan + PATCH"
                 (vi t_source da o SAU phan scan cua rieng thing do)
```

Day la tin TOT cho phep do: `t_source - t_cycle_start` la **do lech scan
cua tung thing, do duoc TRUC TIEP**, khong phai suy ra.

## 2. Gia thuyet duoc kiem

```text
H1  Stall ~1.4 s la TRANSIENT KHOI DONG (JVM/Ditto/Mininet warm-up).
H2  Stall la tinh chat THAT cua vong sync (GC, contention), ngau nhien.
H3  Stall la chu ky RECONCILE (full push).
H4  Trai AoI giua link do THU TU TUAN TU CUA TWIN, khong do mang.
    Sau khi sua muc 1, H4 tach lam HAI thanh phan DAU NGUOC NHAU:
      H4a  thu tu SCAN cua collector. Thing scan muon co t_source MOI hon
           -> AoI NHO hon  -> gradient AM theo vi tri scan.
      H4b  thu tu PATCH cua sync_agent (sync_agent.py:123, tuan tu).
           Thing patch muon nhin thay duoc MUON hon -> AoI LON hon
           -> gradient DUONG theo vi tri patch.
    Hai thanh phan nay TRIET TIEU MOT PHAN. Do rieng tung cai.

DA LOAI truoc khi chay, bang doc code:
    H5  ping dinh ky moi 20 chu ky
        -> bridge/collector.py:410 ghi ro
           "self.ping_every = ping_every   # legacy option; collect_all no
            longer pings"
        Loai bang bang chung ma nguon, khong bang do. Ghi lai viec loai nay
        vi loai mot gia thuyet cung la mot ket qua.
```

## 3. Du doan bang so -- DIEN TRUOC KHI CHAY

```text
ID      Dai luong                                         Nguon       Dai khoa        KQ
--------------------------------------------------------------------------------------
M-78  * ty le run co chu ky overrun dau tien o cycle < 20 [CO CHE]    >= 80% run      __
M-78b   so chu ky overrun moi run                         [MO TA]     1 - 2           __
M-78c * H3: ty le chu ky overrun co is_reconcile = true   [CO CHE]    < 0.5           __
M-78d   PROD co ~8 chu ky reconcile / run                 [CO CHE]    CO              __
M-78e * H4a: on dinh thu hang do lech SCAN giua cac run   [CO CHE]    corr > 0.8      __
M-78f * H4a: corr(alpha_link, do lech scan trung vi)      [CO CHE]    |corr| > 0.8    __
M-78g * H4b: on dinh thu hang do lech PATCH giua cac run  [CO CHE]    corr > 0.8      __
M-79  * CV CLEAN sau khi cat 20 chu ky dau                [CO CHE]    0.375 - 0.400   __
M-80    mean AoI CLEAN sau khi cat warm-up                [NGOAI SUY] 360 - 372 ms    __
M-81    d_transport trung vi (CLEAN, 15 run)              [MO TA]     ghi lai         __
M-81b * kiem cheo: |d_transport - (cycle_elapsed + 50ms)| [CO CHE]    <= 40 ms        __
M-82    cycle_elapsed cua chu ky overrun / trung vi       [NGOAI SUY] 2.5x - 3.5x     __
M-83  * phase = AoI - d_transport thuoc [0, T_eff]        [CO CHE]    >= 99.5% mau    __
M-84    san d chot cuoi (3 cach hoi tu)                   [NGOAI SUY] 115 - 132 ms    __
M-85    chenh lech lon nhat giua 3 cach uoc luong d       [CO CHE]    <= 15 ms        __
M-86    corr(AoI, rho) sau khi cat warm-up                [MO TA]     -0.10 .. -0.02  __
M-87    ty le MAU nam trong chu ky dai (T_eff > 0.55 s)   [CO CHE]    0.8% - 1.4%     __
M-88    ty le CHU KY dai                                  [MO TA]     0.40% - 0.85%   __
M-89    he so length-bias = M-87 / M-88                   [CO CHE]    2.0 - 3.5       __
M-90  * CI95 long nhau rong gap may lan CI95 gop iid      [CO CHE]    1.3x - 2.5x     __
```

`*` = du doan CO CHE: sai la co che sai, khong phai hieu chuan sai.

## 4. Quy tac phan xu H1 vs H2 -- VIET TRUOC KHI THAY SO

```text
M-78 >= 0.80   -> H1 STARTUP TRANSIENT. Cat warm-up, trong so duoi ~0.15%.
M-78 <= 0.50   -> H2 INTRINSIC. Giu duoi ~1.2%, dua vao mo hinh AoI.
0.50 < M-78 < 0.80 -> AMBIGUOUS. KHONG duoc chon. Chay them 5 run 600 s.
```

Vi sao 600 s chu khong phai them 15 run 120 s: cai can phan biet la
"su kien xay ra MOT LAN moi run" (H1) hay "su kien xay ra theo MOT TY LE
tren thoi gian" (H2). Keo dai run gap 5 lan giu nguyen so lan khoi dong
nhung nhan so co hoi ngau nhien len 5 lan -- H1 du doan van ~1 chu ky
overrun/run, H2 du doan ~5. Them run ngan chi nhan CA HAI len cung mot he so
nen KHONG phan biet duoc. Day la mot du doan phan biet duoc (differential
prediction), khong phai them mau.

## 5. Dieu KHONG duoc lam

```text
- KHONG doi dai khoa sau khi thay so.
- KHONG them gia thuyet sau khi thay du lieu (H1..H4 la day du; H5 da loai).
- KHONG doi WARMUP_CYCLES = 20 hay LONG_CYCLE_S = 0.55.
  Chung la HANG SO MODULE, khong phai co dong lenh, chinh de viec doi chung
  phai la mot hanh dong CO Y THUC (sua code + viet amendment moi).
- KHONG chon mot trong ba cach uoc luong d chi vi no dep hon.
  Ba cach lech > 15 ms nghia la CHUA HIEU HE -> dieu tra, khong chon bua.
```

## 6. Thong ke: CI phai theo THIET KE, khong duoc gop iid

15 run CLEAN khong phai 15 lan lap doc lap: chung la **5 muc rho x 3 lan lap**.
Gop iid gia dinh phuong sai giua cac muc rho bang 0. Lesson 23.8 do duoc E1
bien thien 2.126 ms tren 5 muc -> KHAC 0.

```text
Mo hinh   d_ij = mu + a_i + e_ij,  a_i ~ N(0, s2_between), i = 1..5
                                    e_ij ~ N(0, s2_within),  j = 1..3
uoc luong mu = trung binh cua 5 TRUNG BINH NHOM
bac tu do    = 4  (so muc rho - 1), KHONG phai 14
```

Bao cao **CA HAI** CI kem ty so M-90 va ICC. ICC gan 0 -> hai cach gan bang
nhau; ICC lon -> cach gop iid HEP GIA TAO.

Ghi chu ve amendment 23-44: CI95 ghi o do ([141.82, 144.38], t df=14) la CI
GOP IID. No khong sai ve so hoc va phuong phap da duoc ghi ro, nhung no la
CI cua mot mo hinh bo qua cau truc rho. Lesson 23.18 se bo sung CI long nhau
canh no; **khong rut** so cu, dung nguyen tac cua amendment 23-44.

## 7. Gioi han nhac cu -- ghi CANH so, khong phai o "future work"

```text
d_transport uoc luong bang "t_obs SOM NHAT nhin thay mot t_source".
Probe chay moi 100 ms -> gia tri that co the da xuat hien bat ky luc nao
trong 100 ms truoc do.
=> d_transport do duoc la CAN TREN.
=> bias HE THONG ky vong +50 ms (nua khoang probe).
=> tang so run KHONG lam bias nay nho di. Chi doi nhac cu moi lam duoc.
```

Chu ky: ____________

# AMENDMENT 23-76 -- LESSON 23.24b: CUU TRUC rho (dong `L30` truoc 23.25)

Ngay ky : 2026-08-27

Moc     : sau tag `lesson-23-24-complete`, TRUOC khi mo Lesson 23.25

Loai    : TIEN DANG KY mot phep do + MOT SUA MA NGUON

Commit  : `d5c5a8bcb969019efb2b639400b99f5668c22edf`
          (tag `lesson-23-24b-start`)

## 0. Vi sao amendment nay ton tai

`LIMITS.md` dong `L30` ghi:

```text
rho cua uA/uB do SAI CHIEU trong toan bo chien dich 23.8
   `00zzb-amendment-45c.md:99`
```

Va `aoi_decomposition.json::T5_partial_correlation.L30_note` ghi nguyen van:

```text
"canonical_link_key xep ten switch truoc nen hai canh bien phia nguon thanh
 link-sA-sSRC / link-sB-sSRC; util_direction=tx do chieu sA->SRC va sB->SRC,
 khong co luu luong. rho cua uA/uB vi the ~0 trong toan bo chien dich.
 KHONG anh huong AoI. Anh huong moi phan tich dung rho theo link."
```

Lesson 23.25 la DUNG mot phan tich nhu vay. Neu chay no tren du lieu chua
kiem, `Var(uA - uB)` se ~= 0 thay vi `2*sigma^2`, va ti so phuong sai se ra
mot so DEP, co CI, va SAI -- dung loai loi ma `00zzb-amendment-45c.md` muc 5
da canh bao: "MOT DU DOAN DUOC XAC NHAN BOI CHINH CAI LOI DA SINH RA NO."

## 1. Ngan sach gate (`A071` R1)

```text
Lesson 23.24b : 6 gate   G23-301 .. G23-306
KHONG lay tu ngan sach 5 gate cua 23.25. Vuot ngan sach -> DUNG lesson.
```

Bien minh theo `A071` R4 -- "neu KHONG lam, paper mat CAU NAO trong `CLAIMS.md`?"

```text
Khong lam -> KHONG mo duoc 23.25 -> khong dong duoc `S13`/`L44`/`L46`
-> `CL-08` va moi phat bieu ve chuyen giao GIU NGUYEN gioi han cua `L46`
   ("`S_pivotal` do tren mo hinh rho DOC LAP theo link"), tuc uoc luong hien
   tai chi la CAN TREN cua vung song, khong phai vung song.
=> Mat mot pham vi cu the cua `CL-08`. DUOC PHEP mo.
```

## 2. ★ KHAI BAO TRUNG THUC: mot phan ket qua DA duoc tinh TRUOC khi ky

### 2.1. R2 da chay truoc khi ky

Truoc khi amendment nay duoc ky, phep tinh o Task R2 (`rho` tu SO SACH cua bo
sinh tai) DA DUOC CHAY -- hai lan doc lap, va hai lan khop nhau.

```text
=> R2 KHONG duoc dang ky nhu mot du doan.
=> No mang nhan [MO TA -- DA DO TRUOC KHI KY].
=> KHONG duoc cap ma `M-*` co cham diem cho R2.
=> Con so cua R2 duoc bao cao, nhung KHONG duoc dem vao so diem du doan.
```

Ly do ghi muc nay: HARKing la rui ro nguy hiem nhat cho uy tin paper. Mot ket
qua tot ma khai sai thoi diem thi lam hong ca nhung ket qua duoc khai dung.

So da biet truoc khi ky (30 run, `meta_*.json`, TRACKED trong git):

```text
rho_gen = packets_sent * (payload_bytes + 42) * 8 / duration_s / cap_mbps

ti so rho_gen / rho_target, gop 30 run:
    uA 0.974   uB 0.991   ac 0.982   ad 0.997
    bc 0.978   bd 0.988   vC 0.976   vD 0.993

uA va uB CO tai, don dieu tang theo `rho_bar` (0.614 -> 0.884 o uA), va khoe
NGANG sau link kia. Khong co dau hieu link bi bo doi.
```

### 2.2. Phat hien lam RO rang cau hoi chinh VAN CON MO

Truoc khi ky, da truy nguon cua `rho_zero_share_by_link`:

```text
aoi_decomposition.json  <- measurements/aoi_decompose.py
                        <- aoi_*.jsonl
                        <- measurements/aoi_probe_v7.py
                        <- bridge.ditto_reader + twin.util_spec.UTIL_DIRECTION
```

Nghia la bang `zero_share` (uA 0.980595, uB 0.979594, sau link kia ~0.001)
do tren NHANH DITTO -- dung nhanh da biet la hong. No **khong** noi gi ve
`rho_measured_*.csv`.

```text
=> Cau hoi cua `M-236`/`M-237` (CSV co sach khong) VAN CHUA CO CAU TRA LOI.
=> Tai thoi diem ky, KHONG file `rho_measured_*.csv` nao duoc mo.
=> Do la mot tien dang ky HOP LE.
```

## 3. Du doan CO CHAM DIEM (dieu CHUA biet tai thoi diem ky)

| ID | Dai luong | Nguon | Dai khoa | Do | KQ |
|---|---|---|---|---|---|
| M-236 ★ | `zero_share(uA)` trong `rho_measured_*.csv` | [CO CHE] | < 0.05 | ___ | ___ |
| M-237 ★ | `zero_share(uB)` trong `rho_measured_*.csv` | [CO CHE] | < 0.05 | ___ | ___ |
| M-238 | `zero_share` lon nhat trong 6 link con lai | [MO TA] | < 0.05 | ___ | ___ |
| M-239 | `rho_csv(uA) / rho_gen(uA)`, gop 30 run | [NGOAI SUY] | 0.85 - 1.15 | ___ | ___ |
| M-240 | so link co `verdict = CLEAN` | [CO CHE] | 8 / 8 | ___ | ___ |
| M-241 | `corr(rho_csv, rho_gen)` tren 8 link x 10 cell | [NGOAI SUY] | >= 0.95 | ___ | ___ |

Co so cua `M-236`/`M-237`: `mininet/run_sync_v7.py::RhoLogger.link_interfaces()`
(dong 369) duyet `LINK_ENDPOINTS` -- mot ban do CO HUONG viet tay -- va lay
interface cua UPSTREAM. No KHONG goi `canonical_link_key`.

```text
Day la mot SUY LUAN TU MA NGUON, chua phai mot so do. `NT 39`: dai luong vat
ly phai duoc DO, khong duoc SUY. Vi vay no la mot DU DOAN, va no co the SAI.
```

DIEU KIEN KHA THI (`A073` R5): ca sau du doan deu co the fire theo hai chieu.
Neu `RhoLogger` cung dinh loi chieu (vi du `link_intf_for_node` tra nham dau),
`zero_share(uA)` se ~0.98 va `M-236` MISS. Do la mot ket qua HOP LE va se doi
ket luan sang `K2`.

## 4. Kich ban thi hanh -- KY TRUOC, khong dien giai lai sau khi nhin so

```text
K1  M-236 VA M-237 deu HIT (CSV sach)
    -> `rho_measured_*.csv` la nguon HOP LE cho Lesson 23.25.
    -> 23.25 chay duoc gan nhu nguyen ban ke hoach.
    -> `L30` THU HEP PHAM VI: chi con anh huong nhanh Ditto/twin, KHONG anh
       huong nhanh RhoLogger. Ghi thanh `L137`.

K2  M-236 HOAC M-237 MISS (CSV cung hong)
    -> `rho_measured_*.csv` KHONG dung duoc.
    -> Kiem tiep: snapshot log cua collector con khong (co `rxRate`)?
       Co   -> nhanh phuc hoi offline, mo `A077`.
       Khong -> Lesson 23.25 phai DO LAI toan bo 30 run (3 tuan may), hoac
                phat bieu lai voi 6/8 link va ghi ro han che.
    -> Trong CA HAI truong hop: KHONG duoc chay 23.25 tren du lieu hong.

K3  M-236/M-237 HIT nhung M-239 MISS (khong co zero, nhung lech MUC)
    -> hai nhac cu bat dong ve MUC chu khong ve SU TON TAI.
    -> Day la mot phat hien RIENG (co the la overhead, shaping, drop).
    -> Ghi `L138`, dung CSV cho 23.25 nhung CHI cho TUONG QUAN -- he so
       tuong quan BAT BIEN voi phep nhan thang, `corr(aX, bY) = corr(X, Y)`
       voi `a, b > 0` -- KHONG cho MUC TUYET DOI, tuc khong cho `Var(m)`.
```

## 5. Sua ma nguon duoc phep trong lesson nay

```text
(a) twin/link_direction.py             -- MOI, ban do link -> node thuong nguon
(b) bridge/collector.py                -- tra cuu ban do (a); giu fallback CO NHAN
(c) measurements/link_rho_audit.py     -- MOI, nhac cu kiem toan
(d) test/test_link_rho_audit.py        -- MOI

KHONG duoc sua:
  · mininet/run_sync_v7.py::RhoLogger  -- dang la nhanh DOI CHUNG. Sua no la
                                          doi hai thu cung luc.
  · twin/util_spec.py::UTIL_DIRECTION  -- doi hang so toan cuc se lam SAI 6
                                          link dang dung. Doi loi nay lay loi kia.
  · bridge/collector.py::canonical_link_key -- doi TEN Thing trong Ditto se
                                          lam moi artifact cu mat kha nang doi
                                          chieu. Ten GIU NGUYEN, chi HUONG doi.
```

## 6. Doi chung bat buoc

```text
NC-24b-1  Chay `link_rho_audit` hai lan tren cung dau vao -> ket qua phan
          quyet giong nhau BIT-FOR-BIT (tru truong `timestamp_utc`).

NC-24b-2 ★ Sua ma nguon o muc 5 KHONG lam doi bat ky artifact offline nao.
          Chung minh: `pytest test/ -q` xanh VA `git status --porcelain
          results/LIVE/` rong sau khi chay lai duong chung nhan.
          Co so: nhanh offline dung `aoi_model_v7` + `sla_calib_v2`, KHONG
          goi `bridge/collector.py`.

PC-24b-1 ★ DOI CHUNG DUONG. Cho `link_rho_audit` an mot CSV GIA LAP co
          uA/uB = 0 o 98% mau -> no PHAI ket luan `CSV_BROKEN` va liet ke
          DUNG `["uA", "uB"]`.
          Muc dich: chung minh nhac cu DU NHAY. Mot kiem toan luon bao "sach"
          thi vo dung -- cung hinh dang `L101` (nguong khong the fail).
```

## 7. Gate

| ma | noi dung | nguong |
|---|---|---|
| G23-301 | raw 426 MiB co SHA256 ghi trong tai lieu + DOI Zenodo | bat buoc |
| G23-302 | R2: `rho_gen` do duoc cho ca 8 link tren 30 run | bat buoc |
| G23-303 ★ | R3/R4: phan quyet `CSV_CLEAN` / `CSV_BROKEN`, co so | nhi phan |
| G23-304 | R4: `rho_csv / rho_gen` bao cao cho ca 8 link | bat buoc |
| G23-305 ★ | `NC-24b-2`: sua ma nguon khong doi artifact offline | diff = 0 |
| G23-306 | `PC-24b-1`: kiem toan bat duoc CSV gia lap hong | bat buoc |

## 8. Luu tru (`G23-74`)

```text
tar    : ~/dt4n-raw-phase23-aoi-20260827.tar.gz   (56 MiB nen, 426 MiB goc)
SHA256 : a88c669f741a308f067033f6f1ed370f696b6fee6b9d0e2132cf6ea3542bd7c1
DOI    : ___________________  (CHUA CO -- can tai khoan Zenodo cua tac gia)
```

```text
G23-301 CHUA DONG cho toi khi co DOI. SHA256 tra loi cau "file toi dang dung
CHINH LA file do"; DOI tra loi cau "file do ton tai tu ngay do". Can CA HAI.
Xem `results/RAW/README.md`.
```

## 9. Pham vi va gioi han cua chinh amendment nay

```text
N1  Lesson nay KHONG do moi tren Mininet. No doc du lieu da co. Moi ket luan
    gioi han o chien dich 23.8 (30 run, `aoi_v7_campaign`).

N2  `rho_measured_*.csv` bi `.gitignore:174` chan, nen KHONG co tren ban clone
    sach. `link_rho_audit` PHAI chay duoc tren clone sach va TU KHAI
    `status = INCOMPLETE_NO_CSV` thay vi gia vo thanh cong (`L78`).

N3  Phep kiem BAO TOAN LUU LUONG KHONG dung o testbed nay va KHONG duoc dung:
    `mininet/traffic_v7.py::LOAD_CHANNELS` nap moi link bang MOT luong
    MOT-CHANG rieng (`uA`: hsrc->hA; `ac`: hA->hC), nen byte vao `uA` KHONG
    chay tiep sang `ac` va `tp(uA) != tp(ac) + tp(ad)`. Do la `S13` o dang
    vat ly: testbed hien tai la `omega = 0` THEO THIET KE. Mot doi chung SAI
    con te hon khong co doi chung.

N4  `OVERHEAD_BYTES = 42` (Eth 14 + IPv4 20 + UDP 8). `/proc/net/dev` KHONG
    dem FCS (4 B) va preamble+IFG (20 B). Do nhay: neu overhead that la 46,
    `rho_gen` lech 4/1442 = 0.28%, nho hon dai `AGREE_BAND` (+-15%) hon 50
    lan. Khong chi phoi ket luan.

N5  Nguong phan quyet la HANG SO MODULE, KHONG phai co dong lenh. Doi chung
    bat buoc phai sua code + commit + amendment. Neu la co, se thu 1e-6, 1e-4,
    1e-3 cho toi khi ket luan vua y -- p-hacking khong de lai dau vet.

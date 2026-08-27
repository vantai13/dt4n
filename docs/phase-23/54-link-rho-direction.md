# LESSON 23.24b -- CUU TRUC `rho`: PHAN XU `L30`

Tien dang ky : `A076-amendment-76.md` (commit `fd8f0d7`, tag `amendment-76-signed`)
Artifact     : `results/LIVE/phase-23/link_rho_audit.json`
Ma           : `twin/link_direction.py` · `measurements/link_rho_audit.py`
               · sua `bridge/collector.py`
Test         : `test/test_link_rho_audit.py`
Nguon        : `results/RAW/phase-23/aoi_v7_campaign` -- 30 run, 30 `meta_*.json`
               (TRACKED), 30 `rho_measured_*.csv` (gitignore), 17970 mau/link

## 0. Ket qua mot dong

```text
G23-301  luu tru        DEBT   SHA256 co, DOI Zenodo CHUA co
G23-302  R2 generator   PASS   [MO TA -- DA DO TRUOC KHI KY]
G23-303  R3/R4 phan quyet PASS **CSV_CLEAN, 8/8 link**
G23-304  dong thuan     PASS   agree(uA) 0.998; corr 0.997219
G23-305  NC-24b-2       PASS   sua ma khong doi artifact offline
G23-306  PC-24b-1       PASS   kiem toan bat duoc CSV gia lap hong
```

**Kich ban `K1` duoc thi hanh.** `rho_measured_*.csv` la nguon HOP LE cho
Lesson 23.25.

## 1. Loi: "chieu do" bi suy tu "thu tu dat ten"

`bridge/collector.py:199` chuan hoa TEN link cho duy nhat -- viec do DUNG:

```python
def canonical_link_key(a, b):
    lo, hi = sorted([a, b])           # sap theo bang chu cai
    return 'link-%s-%s' % (lo, hi)
```

Loi o buoc sau: thu tu do bi MUON de quyet dinh CHIEU DO (`:204` ban cu):

```python
return link.intf1 if a <= b else link.intf2      # "side A theo bang chu cai"
```

cong voi `twin/util_spec.py:11` `UTIL_DIRECTION = 'tx'`.

```text
Bang chu cai la cong cu de DAT TEN. No khong biet nuoc chay ve dau.
```

Ap vao `topology_v7`:

| link | (upstream, downstream) | `sorted()` -> side A | dung chieu? |
|---|---|---|:--:|
| uA | (sSRC, sA) | **sA** | **KHONG** |
| uB | (sSRC, sB) | **sB** | **KHONG** |
| ac | (sA, sC) | sA | co |
| ad | (sA, sD) | sA | co |
| bc | (sB, sC) | sB | co |
| bd | (sB, sD) | sB | co |
| vC | (sC, sDST) | sC | co |
| vD | (sD, sDST) | sD | co |

Bang chu cai TINH CO dung o 6 link va TINH CO sai o 2. Khong co logic nao ca
-- va do chinh la ly do loi song sot: no khong sai HE THONG ma sai NGAU
NHIEN, nen moi kiem tra tong the (trung binh 8 link, tong 8 link) van "trong
co ve on".

Day la **silent data defect**: khong exception, khong canh bao, khong `NaN`.
`0.0` la mot `rho` hoan toan hop le. Moi kiem tra kieu "co phai so khong?",
"co trong [0,1] khong?" deu XANH. No chi lo ra khi hoi mot cau ve VAT LY.

`L30` gio la mot BIEU THUC CHAY DUOC, khong phai mot doan van:

```python
>>> [l for l in UPSTREAM_OF if not alphabetical_side_a_is_correct(l)]
['uA', 'uB']
```

## 2. Ba nhac cu doc lap

```text
NHAC CU 1 -- bo dem nhan qua DITTO   (nhanh Collector, DANG BI NGHI NGO)
    /proc/net/dev -> collector -> Ditto -> aoi_probe_v7 -> aoi_*.jsonl

NHAC CU 2 -- so sach bo sinh tai     (DOC LAP hoan toan)
    flow_engine[link].packets_sent. Bo sinh TU DEM so goi da ban ra. No
    KHONG doc /proc/net/dev va KHONG biet `canonical_link_key` ton tai.

NHAC CU 3 -- bo dem nhan qua RhoLogger  (nhanh CSV, PHAI KIEM)
    /proc/net/dev -> RhoLogger -> rho_measured_*.csv
    Dung `LINK_ENDPOINTS`, ban do CO HUONG viet tay, lay interface UPSTREAM.
```

## 3. R2 -- so sach bo sinh tai   `[MO TA -- DA DO TRUOC KHI KY]`

`A076` muc 2 khai ro: phep tinh nay DA chay truoc khi amendment duoc ky, nen
no KHONG duoc dem vao so diem du doan.

```text
ti so rho_gen / rho_target, gop 30 run:
    uA 0.974   uB 0.991   ac 0.982   ad 0.997
    bc 0.978   bd 0.988   vC 0.976   vD 0.993
```

`rho_gen` theo cell (bon link dai dien):

| cell | uA | uB | ac | vC |
|---|---:|---:|---:|---:|
| clean@0.700 | 0.6141 | 0.6655 | 0.7355 | 0.6220 |
| clean@0.850 | 0.7672 | 0.7949 | 0.8808 | 0.7746 |
| clean@0.925 | 0.8161 | 0.8617 | 0.9702 | 0.8383 |
| clean@0.960 | 0.8840 | 0.9205 | 0.9709 | 0.8744 |
| prod@0.700 | 0.6353 | 0.6418 | 0.7421 | 0.6258 |
| prod@0.960 | 0.8928 | 0.9127 | 0.9679 | 0.8589 |

`uA`/`uB` CO tai, va tai TANG DON DIEU theo `rho_bar`. Mot link "that su
rong" khong the co duong cong tang don dieu nhu vay.

## 4. ★ R3/R4 -- phan quyet: CSV SACH

| link | verdict | `zero_share` (CSV) | `rho_csv` | `rho_gen` | `agree` |
|---|---|---:|---:|---:|---:|
| uA | CLEAN | 0.001169 | 0.7808 | 0.7821 | 0.998 |
| uB | CLEAN | 0.000556 | 0.8151 | 0.8159 | 0.999 |
| ac | CLEAN | 0.000000 | 0.8886 | 0.9000 | 0.987 |
| ad | CLEAN | 0.000000 | 0.9034 | 0.9204 | 0.982 |
| bc | CLEAN | 0.000000 | 0.8811 | 0.8917 | 0.988 |
| bd | CLEAN | 0.000056 | 0.8943 | 0.9089 | 0.984 |
| vC | CLEAN | 0.001002 | 0.7822 | 0.7836 | 0.998 |
| vD | CLEAN | 0.001669 | 0.8254 | 0.8271 | 0.998 |

```text
n_clean = 8/8      corr(rho_csv, rho_gen) tren 80 cap = 0.997219
```

### Doi chieu quyet dinh -- CUNG 30 run, hai nhac cu

| link | `zero_share` nhanh DITTO | `zero_share` nhanh CSV |
|---|---:|---:|
| uA | **0.980595** | **0.001169** |
| uB | **0.979594** | **0.000556** |
| ac | 0.001056 | 0.000000 |
| vD | 0.001612 | 0.001669 |

Cung du lieu goc, cung link, hai duong doc -- mot hong, mot sach. Do la
bang chung dut khoat rang loi nam o NHANH DOC, khong o vat ly.

## 5. Y nghia cho Lesson 23.25

```text
DUOC   `rho_measured_*.csv` la nguon HOP LE. Cong thuc trung tam cua 23.25
       m(P1,P3) = (uA - uB) + (ac - bc) chay duoc tren nguon nay.
       `Var(uA - uB)` se KHONG bi sup gia tao.

CAM    dung `rho` TU DITTO (`aoi_*.jsonl`) cho bat ky phan tich nao theo
       TUNG LINK. Nhanh do van hong o uA/uB. Nhan `PRE_L30_FIX`.
```

## 6. Sua goc, va vi sao khong sua theo hai cach de hon

```text
KHONG doi `UTIL_DIRECTION = 'rx'`
    -> sua uA/uB nhung LAM HONG 6 link dang dung. Doi loi nay lay loi kia.

KHONG doi `canonical_link_key` de sap theo huong
    -> doi TEN Thing trong Ditto -> moi artifact cu mat kha nang doi chieu.

DA LAM: giu nguyen TEN, tra HUONG tu mot ban do rieng
    (`twin/link_direction.UPSTREAM_OF`), va khi khong tra duoc thi DAN NHAN
    thay vi im lang doan.
```

Thing gio TU MANG bang chung ve chieu do cua chinh no (`A075` R6):

```python
'utilIntf': util_intf.name,
'utilDirectionSource': link_direction_source(link),   # 'directed_map' | 'alphabetical_fallback'
```

Neu ai do them link moi ma quen vao ban do, artifact se mang
`"alphabetical_fallback"` va mot test quet duoc. **Loi tro thanh ON AO.**

Do duoc: ban sua doi DUNG `uA`/`uB` (`sA` -> `sSRC`, `sB` -> `sSRC`); sau
link con lai KHONG doi mot bit.

## 7. Doi chung

```text
PC-24b-1  DOI CHUNG DUONG (G23-306). Cho kiem toan an mot CSV gia lap co
          uA/uB = 0 o 98% mau -> ket luan `CSV_BROKEN`, liet ke DUNG
          ['uA','uB'], dong thuan sup <0.05 o link hong va giu ~1.0 o link
          lanh. Cung ma do do tren CSV sach cho `CSV_CLEAN`, nen cai chan
          PHAN BIET duoc. Mot kiem toan luon bao "sach" thi vo dung (`L101`).

NC-24b-1  Chay hai lan tren cung dau vao -> phan quyet giong het.

NC-24b-2  Sua `collector.py` khong doi mot artifact offline nao.
          `pytest test/ -q` = 1684 passed (1 fail la `L121` da biet),
          `git status --porcelain results/LIVE/` rong.
```

## 8. Vi sao KHONG dung phep kiem bao toan luu luong

Mot de xuat ban dau la kiem `tp(uA) = tp(ac) + tp(ad)`. **De xuat do SAI**
va da bi bo truoc khi chay.

`mininet/traffic_v7.py:30` cho thay moi link duoc nap bang MOT luong
MOT-CHANG rieng:

```python
LOAD_CHANNELS = {
    "uA": ("hsrc", "hA"),     # luong nay DUNG o hA
    "ac": ("hA",  "hC"),      # luong KHAC, bat dau tai hA
}
```

Byte vao `uA` KHONG chay tiep sang `ac`. Nen bao toan KHONG dung o testbed
nay -- va do **khong phai loi**, do chinh la `S13` o dang vat ly: testbed
hien tai la `omega = 0` THEO THIET KE, o ca tang twin lan tang Mininet.

```text
Neu chay phep kiem do, no se FAIL, va nguoi doc se tuong phep cuu du lieu
sai -- trong khi thuc ra PHEP KIEM moi la cai sai.
MOT DOI CHUNG SAI CON TE HON KHONG CO DOI CHUNG.
```

## 9. Chong p-hacking

Nguong phan quyet la HANG SO MODULE, KHONG phai co dong lenh (`A076` N5):

```python
ZERO_RHO_EPS = 1e-9 ; BROKEN_ZERO_SHARE = 0.50
CLEAN_ZERO_SHARE = 0.05 ; AGREE_LO, AGREE_HI = 0.85, 1.15
```

Neu la `--zero-eps`, ai do se thu `1e-6`, `1e-4`, `1e-3` cho toi khi ket
luan vua y, va viec do KHONG de lai dau vet trong git. La hang so module thi
doi no BAT BUOC phai sua code + commit + amendment.
`test_locked_constants_are_not_command_line_flags` ghim dieu do.

`OVERHEAD_BYTES = 42` (Eth 14 + IPv4 20 + UDP 8); `/proc/net/dev` KHONG dem
FCS (4 B) va preamble+IFG (20 B). Do nhay: neu overhead that la 46, `rho_gen`
lech `4/1442 = 0.28%`, nho hon dai dong thuan (+-15%) hon 50 lan.

## 10. Tai tao

```bash
.venv/bin/python -m pytest test/test_link_rho_audit.py -q
.venv/bin/python -m measurements.link_rho_audit \
    --campaign results/RAW/phase-23/aoi_v7_campaign \
    --out results/LIVE/phase-23/link_rho_audit.json
```

Thoi gian: 0.5 s. Tren ban clone SACH (khong co CSV vi `.gitignore:174`),
script van chay va TU KHAI `status = "INCOMPLETE_NO_CSV"` thay vi gia vo
thanh cong (`L78`).

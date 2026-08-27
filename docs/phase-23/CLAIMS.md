# CLAIMS -- phat bieu paper duoc phep dua ra

Moi dong la mot cau paper CO THE viet. Cot "Rang buoc" la cau PHAI in kem --
khong phai chu thich tuy chon.

`A071` R4: mo mot nhanh moi chi hop le khi no doi mot dong o day. Khong tra
loi duoc bang mot ID `CL-*` cu the -> KHONG duoc mo.

Quy uoc: `HIT/MISS` danh gia menh de, `PASS/FAIL` la trang thai gate. Mot
gate PASS KHONG tu dong cho phep trich dan -- xem `CL-08` va `CL-11`.

| ID | Phat bieu | Bang chung (gate + so) | Rang buoc PHAI in kem |
|---|---|---|---|
| CL-01 | Bo truc `m_hat` tang 4x hang chi mua 1.09--1.15x so block | `G23-231` `M-182` 3/3: 1.1458 / 1.0926 / 1.0929 | `M-181` MISS: block/o 436.4 / 457.6 / 457.5, dai da ky [440,500] chi dat 2/3 |
| CL-02 | Gia thuyet H-A dang MANH bi bac bo | `G23-234` `M-187` 2/3 MAIN, 4/12 toan bo | Bac bo o dang MANH; dang YEU chua duoc do |
| CL-03 | Dong gop nam o nhanh HANG, khong o nhanh phan giai | `G23-239` `M-188` 3/3: 0.5375 / 0.5315 / 0.5406 trong [0.45, 1.00] | `L90`: `M-186` (0/3) khong tach duoc gia thuyet khoi hien vat trung binh. `CL-03` phat bieu o muc `M-188`, KHONG o muc `M-186` |
| CL-04 | Mang nguyen `qhat_A` sang B KHONG ben hon B2 | `G23-249` `M-194` MISS: drift B2/C3 = 0.2174 / 0.2090 = 1.04x, dai da ky >= 3x | Ket luan la KHONG PHAN BIET DUOC, khong phai "bang nhau": thang drift cua Task B khong du suc phan biet |
| CL-05 | C3 co co chan doan khi mau khong du; B2 khong co | `G23-259` `M-199`: duoi 29 block, C3 gan co 100%; B2 huu han 100% va gan co 0% | `L100`: hai co `L91`/`L93` mu o vung giao; `qhat_source` la co duy nhat con nhin thay. `L104b`: `degenerate_partial` chiem 6.6% ngay tai `n*` = 120 |
| CL-06 | Sau tai hieu chuan, bao dam BAO PHU duoc khoi phuc tren 64/64 o | `G23-264` `M-203`: coverage 64/64, `viol` lon nhat 0.0800 <= alpha 0.10 | `L104`: tieu chi HOP cho 60/64; ve BIND la ACCEPTANCE (60/64), KHONG phai bao phu. PHAI bao cao tung ve rieng |
| CL-07 | Menh de bao toan DOI XUNG: C3-R giu `viol`, B2-R giu `acceptance` | `G23-267` `M-206`: `sd(err)` C3-R = 0.01500 < B2-R = 0.03531 | `M-206` la ket qua AM ve `err`: menh de bao toan ton tai o muc `viol`, KHONG o muc `err`. Cau noi hai muc la DIEU KIEN TACH ROI, chua duoc do |
| CL-08 | Chuyen giao GIUA HO TAI tai cung muc tai la KHA THI | `G23-285` `M-222` HIT: 3/4 cap co huong dung duoc tren OVERLAP-4 (`rho` in {0.744, 0.750}), `n` = 250. Bao phu giu 4/4: `viol` = 0.0719 / 0.0762 / 0.0758 / 0.0736, deu <= 0.10 | (1) Ve BIND la ACCEPTANCE, khong phai bao phu: `h2@0.750 -> poisson@0.750` co acceptance 0.1837 < san 0.20 (lan thu HAI cua `L104`). (2) Phat bieu chi ve HAI diem tai trong cua so rong 0.0113 (`L111`), va cua so do rat nhay voi san song (`L112`: san 0.040 cho 7 rho, 0.070 cho 0). (3) `L120`: ho tai VAN bi ghep voi don bay `kappa` ngay trong OVERLAP-4. (4) KHONG duoc mo rong thanh "ho tai khong quan trong" -- xem `CL-11` |
| CL-09 | `kappa` sai co GIA do duoc va DU DOAN DUOC theo `|log(kappa_A/kappa_B)|` | `G23-263` `M-202`: do doc 0.4776, Spearman +0.9674 (56 o). Tai lap: `G23-282` `M-220` 0.4873 / +0.9798 (110 o, 11 cell); `G23-286` `M-223`(a)(c) 0.4661 / +0.9804 (210 o, 15 cell) | `L113`: `M-202` KHONG phai xac nhan MU -- xem `CL-10`. Ba con so tren KHONG doc lap: chung dung chong tap cell |
| CL-10 | `M-202` KHONG duoc trich dan nhu mot xac nhan MU | `L113`: noi suy `trace` da in cua PILOT du doan do doc = 0.4144 TRUOC khi chay; that = 0.4776, lech 13.2% | Muc ro ri DA DUOC DO, khong phai uoc luong. Moi phat bieu ve `M-202` phai kem con so 13.2% |
| CL-11 | **CAM** phat bieu "ho tai KHONG them suc giai thich" | `G23-288` `NC-W-1` FIRE: nhan NGAU NHIEN cho he so -0.00261 va `delta R^2` +0.00009, ca hai TRONG dai da ky. 200 rut tham: 100% trong dai, `|he so|` p95 = 0.00874 | `L119`: dai cua `M-223`(b) rong gap 2.3 lan p95 cua doi chung am, nen ve (b) KHONG THE FAIL. `M-223`(b) HIT nhung khong mang thong tin. Ta KHONG phan biet duoc "ho tai that su vo hai" voi "phep do khong du do nhay". `M-224` MISS 1/2 `rho` (`G23-287`) cung KHONG cuu duoc ve nay |
| CL-12 | **CAM** phat bieu "khoang khong-conformal khong giu duoc bao dam tren truc tuoi" | `G23-292` `M-227` khong fire (0/12); B8b toan cell `viol|accept=0.087444 < alpha=0.10` | Kich ban K3. Dai theo-bin cua M-226 hong-khi-ky (`A073`), va M-227 la dieu kien DU de bac bo, khong phai dieu kien CAN. Chi duoc noi folded-Gaussian steel-man khong bi bac bo tren cell nay |
| CL-13 | **CAM** phat bieu "da quan sat C3 tu choi cap chung nhan khi mau khong du tren cell chinh" | `G23-295` `M-230` bat kha thi: 4/4 o co 500 block, san tu choi 29, tu choi 0/4 | Co che toan hoc da co tien le CL-05, nhung phep do 23.23 KHONG kiem no tren cell nao. Muon nang CL-13 phai qua L125 va xac dinh TRUOC cell co o duoi 29 block |
| CL-14 | Tuong quan tai THEO DUONG khong tac dong len do dung quyet dinh mot cach DOC LAP: theo dai so no phong dai phuong sai margin, nen tac dong ti le voi prior tinh. Du lieu 23.25 la DOI CHUNG AM + hieu chuan san nhieu; chua cho uoc luong path-coupling vat ly | `G23-307` dai so; `G23-315..333` audit identifiability/nugget/covariance/residual/censoring | (1) `k` va shared-host cong tuyen; contrast khong-host omega mo ta=-0.0173 (`L146`). (2) M1/M3 model misspec; scaled SE khong la CI vat ly (`L148/L150`). (3) Shortfall +0.902/+0.961 dinh vi artifact, nhung dose-response da ky MISS +0.657/+0.600 (`L147/L156`). (4) Edge nugget lambda=0.506--0.694; hai cap endpoint vuot tran independent-residual 1.380x/1.927x (`L140/L155`). (5) T5b target-cov measured/identity=0.8803--0.9577; moc omega=1 ke/cheo=1.3892/1.7191 (`L154`). (6) ACF margin err=0.1566--0.1758 thay T6 ~0.052 (`L149`). (7) Core clean@0.960 co tran p(>0.99)=0.474--0.504 (`L157`). (8) D3=0.3752 chi pilot; corrected UNDECIDED, khong la can duoi vo dieu kien (`L158`). (9) `mode=poisson` van chua kiem `c_a/c_s` (`L141`) |

## Phat bieu bi CAM (de doi chieu nhanh)

```text
CAM  "chuyen giao qua HO TAI luon dung"        -- CL-08 chi noi KHA THI, tai HAI diem tai
CAM  "ho tai khong phai mot truc doc lap"      -- CL-11, NC-W-1 da FIRE
CAM  "M-223(b) xac nhan null ve ho tai"        -- CL-11, ve (b) khong the fail
CAM  "M-202 la xac nhan mu"                    -- CL-10, ro ri do duoc 13.2%
CAM  "C3 tot hon B2 ve `err`"                  -- CL-07, bao toan o muc `viol`
CAM  moi ngoai suy tu luoi `rho` tho           -- L111
CAM  "B8b da bi chung minh vo bao dam"          -- CL-12, kich ban K3
CAM  "M-230 da kiem duoc co che tu choi"        -- CL-13, dai bat kha thi
CAM  doc `viol|accept` nhu mot bao dam co dinh ly  -- L135 canh bao (1)
     Conformal bao dam BIEN: P(s <= q_hat) >= 1 - alpha, ky vong tren mot
     diem test MOI, KHONG dieu kien gi. `viol|accept` dieu kien tren mot
     bien co PHU THUOC DU LIEU (viec NHAN), nen khong bao dam bien nao
     chuyen sang no -- day la suy luan SAU CHON LOC.
     CANH BAO NOI BO: `CL-06` va `CL-08` HIEN DANG trich `viol|accept`
     (`recalibrate_transfer.py:572`). Ca hai song sot ve SO -- khe do duoc
     o Lesson 23.24 luon DUONG (+0.0212/+0.0237/+0.0287) nen `viol|accept`
     la can TREN bao thu cua `viol` bien -- nhung CHU phai doi hoac SO phai
     doi. Xem `L136`. Chua duoc sua: ngan sach 23.24 het 4/4 (`A071` R1).
CAM  "bo mot hanh dong khong bao gio toi uu ma khong mat bao dam nao"
                                                -- G23-300 FAIL, kich ban K2;
                                                   L43 VAN MO
```

## Vi sao co ca `CL-08` va `CL-11`

Hai dong nay tra loi HAI cau hoi khac nhau, va A070b tra loi duoc mot, khong
tra loi duoc cai kia:

```text
"Co the chuyen giao giua hai ho tai cung rho khong?"   -> CO   (CL-08, M-222)
"Ho tai co phai mot truc doc lap khong?"               -> CHUA BIET (CL-11)
```

`M-222` la mot phep do NANG LUC: no dem xem bao nhieu cap thuc su dung duoc.
Mot phep dem nhu vay khong the bi lam gia boi thieu do nhay -- neu khong co
cap nao dung duoc, no se ra 0.

`M-223`(b) la mot kiem dinh NULL: no muon ket luan "he so gan 0". Moi bien vo
dung deu cho ket qua do, nen no CAN mot doi chung am de co nghia. Doi chung do
da FIRE. Day la ly do mot gate PASS (`G23-286`) van khong cho phep trich dan.

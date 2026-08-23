# AMENDMENT 23-51 -- Phan xu va cham ma `G23-*`, dong no gate 23.20,
#                    mo so CONSTANTS

Ngay ky : 2026-08-23
Tag     : amendment-51
Lesson  : 23.20E (so sach; KHONG co thi nghiem)
Loai    : PHAN XU VA CHAM ID + DONG NO + MO SO MOI

## 0. Vi sao amendment nay ton tai

Mot vong kiem toan tu Lesson 23.8 den 23.20 cho ket luan:

```text
KHOA HOC (so, phuong phap, ket luan)   ->  VUNG. Khong mot con so nao sai.
KE TOAN  (ma, so, provenance)          ->  CO RO.
```

Kiem lai doc lap tren artifact: `M-125a` 8/8 trong dai da ky (do duoc
+7.916% .. +10.272%, tien doan +8.564%, doc tu
`results/LIVE/phase-23/axis_remeasure_impact_wave1.json`). Bang trong
`30-close-23-20.md` khop artifact. Khong co lam dep so.

Sau phat hien deu thuoc tang ke toan chung cu. Nhung voi mot do an tu nhan la
co ky luat tien dang ky, ke toan chung cu CHINH LA dong gop phuong phap: neu
van ban dong lesson ghi sai ma gate, reviewer se dat cau hoi ve moi ma con lai.

Amendment nay xu ly bon phat hien phan xu duoc ngay. Hai phat hien con lai
(`23.7-23.13` chua anh xa, `S13`) duoc GHI NHAN chu chua dong -- xem muc 7.

## 1. Va cham ma thu SAU: `G23-135` / `G23-136`

```text
GATES.md + 29-waves-2-3-and-bin-geometry.md:145-146
    G23-135  phep kiem HINH HOC BIN         (da chay, sinh ra L39)
    G23-136  tang PENDING + `pending_on`    (da chay, co doi chung duong)

30-close-23-20.md:152-153
    G23-135  "Dot 4: 12 build"                  <- MA SAI
    G23-136  "M-125a/b mo rong 12 cell / 48 o"  <- MA SAI
```

NOI DUNG hai dong o `30-close-23-20.md` DUNG: ca hai viec do that su chua chay,
bi chan boi `S14`. Chi MA la sai; ma dung la `G23-141` / `G23-142`.

Hau qua neu de nguyen: `30-close-23-20.md` la van ban DONG lesson, tuc nguon se
duoc trich khi viet paper. O dang hien tai no bao rang phep kiem hinh hoc bin
CHUA chay -- trong khi phep kiem do da chay va da sinh ra `L39`, von la dau vao
cua Lesson 23.28.

```text
QUYET DINH: hai dong do la LOI DANH MA. Tai lieu DA KY nen KHONG sua.
            Anh xa G23-135 -> G23-141, G23-136 -> G23-142 duoc ghi o
            GATES.md muc "Va cham da phat hien" VA o
            test/test_phase23_gate_ledger.py :: ADJUDICATED_GATE_TYPO.
```

## 2. Vi sao test cu khong bat duoc

```python
def _rows():                    # chi doc GATES.md
    ...
    if len(cells) >= 4 and GATE_ID.match(cells[0]):   # bang o doc lesson
        out.append(...)                                # chi co BA cot -> bo qua

def test_every_gate_id_mentioned_in_repo_is_in_the_ledger():
    if gid not in known:        # MEMBERSHIP, khong phai NHAT QUAN TRANG THAI
```

Test cu tra loi "ma nay co ton tai khong", khong tra loi "ma nay co duoc mo ta
giong nhau o moi noi khong". Do dung la lo hong da sinh ra `L21` va `L29` o ho
`L*`. Amendment 23-50 bit cho `L*`; ban nay bit cho `G23-*`.

Test moi: `test_gate_status_is_consistent_across_documents`.

## 3. Ba phat hien PHU SINH tu chinh test moi

Test moi vua chay lan dau da tim ra bon do lech nua ma vong kiem toan bang mat
KHONG thay. Ghi lai ca bon vi chung minh hoa dung luan diem cua muc 2.

```text
28-axis-remeasure-impact.md:152   G23-123   PASS  vs so ADJUDICATED
99-gate-decision.md:63            G23-23    PASS  vs so DIAGNOSTIC
99-gate-decision.md:64            G23-15    FAIL  vs so DIAGNOSTIC
99-gate-decision.md:65            G23-17    FAIL  vs so DIAGNOSTIC
```

Ca bon KHAC loai voi muc 1: MA dung, TRANG THAI la trang thai dung tai thoi
diem VIET roi bi phan xu lai sau do.

```text
G23-123           bao cao Dot 1 viet TRUOC amendment 23-49c
G23-15/17/23      Lesson 23.6 (`06-reframe.md` muc 5, khoa boi amendment 23-25
                  muc 6) HA CAP nam gate xuong DIAGNOSTIC khi tai khung
                  fallback thanh tham so ngoai sinh
```

`06-reframe.md` ghi ro: KHONG mot con so nao bi rut lai, chi doi VAI TRO. Nen
day khong phai mau thuan ve ket qua, ma la do lech thoi gian trong so sach.

```text
QUYET DINH: ghi vao ADJUDICATED_STALE_STATUS + bang o GATES.md.
            KHONG sua bon tai lieu da ky.
```

### 3b. Hai lan test moi tu bat loi cua chinh no

Ban nhap dau dung `STATUS_WORD.search(line)` -- tim tu trang thai dau tien
trong ca DONG -- va sinh 10 bao dong GIA:

```text
"| G23-116 | PC-E4 ... M-121 FAIL dung du kien | PASS |"
                              ^^^^ trong o MO TA, bi doc thanh trang thai

"| G23-8 | PASS | DIAGNOSTIC | ... |"      bang REFRAME co HAI cot trang thai
                                          (CU -> MOI); cot thu hai bi bo qua
```

Da sua thanh: gom moi O bat dau bang mot tu trang thai, roi hoi trang thai o so
co nam trong tap do khong. Sau khi sua, 10 bao dong gia bien mat va bon do lech
THAT o muc 3 van con.

Ghi lai vi day la mot bai hoc cu the: mot phep kiem qua nhay bang mot phep kiem
vo dung, chi khac chieu -- nguoi ta se noi long no cho den khi no im.

## 4. `G23-97 .. G23-99`: dong vong lap ma DU KIEN

Ba ma nay duoc ky TRUOC o amendment 23-44 muc 5 lam tien doan cho Lesson 23.20.
Thuc te ba viec do DA chay -- nhung duoi ma khac. Khong ai dong vong lap.

```text
G23-97   doi chung am: sawtooth cu tai tao BIT-EXACT   -> da chay o G23-137
G23-98   q_hat moi/cu khop tien doan z^0.431           -> da chay o G23-129 + G23-130
G23-99   bang CU vs MOI cong bo du                     -> da chay o G23-138
```

```text
QUYET DINH: ba ma -> ADJUDICATED, evidence tro toi ma da thuc thi.
            KHONG doi thanh PASS: chung khong duoc cham truc tiep, va
            ADJUDICATED la tu vung dung cho "da phan xu, khong tu chay".
```

## 5. `CLOSED_LESSONS` va `PINNED_DEBT` -- lap dan co che da co san

`GATES.md` da tu viet luat: *"Gate thuoc mot lesson trong danh sach nay KHONG
duoc mang trang thai NOT_RUN. Neu chua ai cham thi trang thai dung la DEBT."*
Nhung `23.20` chua bao gio duoc them vao danh sach, nen nam gate NOT_RUN nam
trong mot lesson da DONG ma khong ai bi bao dong.

```text
QUYET DINH: them 23.20, 23.20A, 23.20B, 23.20C, 23.20D vao CLOSED_LESSONS.
            G23-141, G23-142 -> DEBT, va GHIM vao PINNED_DEBT.
```

Tieu chi vao `CLOSED_LESSONS` duoc dinh nghia o day cho lan sau:

```text
CO MOT TAI LIEU TUYEN BO DONG.  Khong phai "cac gate tinh co deu xanh".
```

Theo tieu chi do, ban kiem toan de xuat them ca `23.17`, `23.18`, `23.18b`,
`23.19*`. KHONG lam, vi:

```text
23.17     G23-74/G23-75 con MO mot cach CHINH DANG -- ca hai can thong tin xac
          thuc cua tac gia (Zenodo DOI; credential git). GATES.md da ghi ro
          "khong duoc cham PASS thay mat tac gia". Them 23.17 vao danh sach se
          ep chung sang DEBT, tuc bien mot viec DANG CHO thanh mot MON NO --
          sai ban chat, va lam ban sai lech tap DEBT da ghim.
23.18 / 23.18b / 23.19*   khong co tai lieu nao tuyen bo DONG.
```

Den 2026-08-23 chi `30-close-23-20.md` tuyen bo `DONG`.

## 6. `GATES.md` tu mau thuan: van xuoi phat bieu TRANG THAI

```text
GATES.md bang    G23-125  PASS
GATES.md van xuoi (ngay duoi)      "... NOT_RUN: bay script ha nguon ..."
```

Nguyen nhan goc: `GATES.md` tu khai la NGUON CHAN LY DUY NHAT, nhung van xuoi
trong chinh no cung phat bieu trang thai -- va van xuoi khong bi may doc, nen
no troi tu do.

```text
QUYET DINH: trong mot registry, van xuoi duoc phep giai thich PHAM VI va LY DO,
            TUYET DOI khong duoc phat bieu TRANG THAI. Trang thai chi song o
            bang, vi chi bang bi may doc.
```

Test moi `test_prose_in_ledger_does_not_restate_status` ghim luat do. Da sua
hai cho: dong ve `G23-125`/`G23-141`/`G23-142`, va dong ve `G23-83`/`G23-84`.

## 7. So CONSTANTS -- `beta = 0.431` khong co dong nguon goc

Phat hien quan trong nhat cho paper, du KHONG phai loi.

```text
tools/check_bin_geometry.py:34             BETA = 0.431      hang so cung
axis_remeasure_impact_wave1.json           "dilation_exponent": 0.431
00zzj-amendment-49d.md:156                 "No khoa o Phase 22."
grep -rn "0.431" docs/phase-22/            -> KHONG CO DONG NAO
```

Muoi tai lieu Phase 23 TRICH DAN `z^0.431`; khong tai lieu nao DINH NGHIA no.
Day la tru cot bien `M-125b` tu MO TA thanh TIEN DOAN, va la dau vao cua
Lesson 23.28.

Tai dung duoc hai ung vien tu Phase 22 (`0.4340` va `0.4371`), ca hai nam trong
CI95 cua phep fit nhung KHONG cai nao ra dung `0.431`. Ghi nguyen tinh trang do
thay vi chon dai mot ung vien roi viet nhu the da biet -- xem `L45`.

Tinh duoc SAI SO KHI FIT tu CI bootstrap Phase 22, khong can do moi:

```text
sd(beta) = 0.0059      CI95 = [0.4195, 0.4425]
```

Doi chieu quan trong cho paper: `L39` cho `|dbeta| <= 0.034`, nhung do la cận
HAU KIEM suy nguoc tu phan du, KHONG phai sai so fit. Sai so fit CHAT hon cận
hau kiem khoang ba lan (`1.96*sd = 0.0116` so voi `0.034`). Nghia la bat dinh
cua phep fit KHONG chi phoi phan du cua `M-125b` -- mot ket luan co loi cho lap
luan, va truoc ban nay khong ai chung minh duoc.

```text
QUYET DINH: mo `docs/phase-23/CONSTANTS.md`, so thu BA, cung khuon voi
            GATES.md va LIMITS.md. Ghi K01..K05 va ghim bang
            test/test_constants_ledger.py.
```

## 8. `S13` -- ghi vao so, chua sua

Xac nhan bang code, khong bang suy doan:

```python
# measurements/sla_calib_v2.py:66  -- docstring TU KHAI
"""Return rho matrix ``(n, 8)``: independent AR(1) per link."""
# dong 79, trong vong lap tung link
shocks = rng.standard_normal(int(n)) * sd_eps
```

Tam link co tam chuoi shock doc lap hoan toan. Nhung trong `topology_v7`
(butterfly) cac duong DUNG CHUNG link: mot luong lon qua link chung lam tai
tren nhieu duong tang CUNG LUC. Mo hinh doc lap danh gia THAP phuong sai cua
margin giua cac duong -> conformal band hep gia tao.

Ghi thanh `L44`. Diem can nho khi lam 23.21: `w_loss` moi se duoc hieu chuan
TREN CHINH mo hinh rho doc lap nay. Tuc la 23.21 KHONG lam `S13` te hon, nhung
cung KHONG sua no. Phai ghi ro dieu do khi cong bo ket qua 23.21.

## 9. Gate mo boi amendment nay

```text
G23-147  va cham G23-135/136 phan xu; anh xa song o hai noi va bi khoa
G23-148  bon do lech trang thai (G23-123, G23-15/17/23) phan xu
G23-149  G23-97..99 dong vong lap -> ADJUDICATED, tro toi ma da thuc thi
G23-150  CLOSED_LESSONS + PINNED_DEBT lap dan; khong gate NOT_RUN nao con
         nam trong lesson da dong
G23-151  van xuoi GATES.md khong con phat bieu trang thai
G23-152  CONSTANTS.md + test ghim; sd(beta) tai tinh duoc tu CI Phase 22
```

## 10. Dieu KHONG lam trong amendment nay

```text
- KHONG sua bat ky tai lieu DA KY nao de go va cham
- KHONG doi mot con so khoa hoc nao. Sau phat hien deu o tang ke toan.
- KHONG sua S13 (chi ghi thanh L44; sua o 23.25/23.26)
- KHONG dong no 23.7-23.13: `G23-37 .. G23-73` van NOT_RUN vi anh xa sang he
  danh so cua PLAN_v2 chua the lam -- `PLAN_v2.md` KHONG co trong repo va ban
  nay khong the tao ra no. `test_every_gate_row_in_plan_has_a_ledger_entry`
  van bi skip. Day la mon no K-D0b, van MO, va se chan Lesson 23.31.
- KHONG them 23.17/23.18/23.19* vao CLOSED_LESSONS (ly do o muc 5)
```

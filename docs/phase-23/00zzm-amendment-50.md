# AMENDMENT 23-50 -- Phan xu va cham ma `L21`, khoa anh xa vao hai noi

Ngay ky : 2026-08-23
Tag     : amendment-50
Lesson  : 23.20D (so sach; KHONG co thi nghiem)
Loai    : PHAN XU VA CHAM ID

## 0. Vi sao amendment nay ton tai

`test/test_limits_ledger.py` dong 24-25 (truoc ban nay) ghi:

```text
# `L21` da biet la va cham, dang MO, cho amendment 23-50 phan xu.
KNOWN_OPEN = {"L21"}
```

`docs/phase-23/LIMITS.md` ghi `TRANG THAI: MO`, va
`docs/phase-23/26-axis-integration.md:167` ghi `BUOC 7   L21 (amendment 23-50)`.

Ba noi trong repo deu tro den mot amendment MANG DUNG SO NAY va chua ai viet.
`KNOWN_OPEN` la mot mien tru: no lam `test_no_duplicate_limit_ids` bo qua `L21`.
Mien tru khong duoc song lau -- moi ngay no ton tai la mot ngay so han che co
mot ma mang hai nghia ma may khong con canh bao.

Amendment nay dong mien tru do.

## 1. Pham vi -- va cai KHONG thuoc pham vi

Mot ban huong dan ngoai repo de xuat amendment 23-50 lam BON viec: dang ky truc
AoI do duoc, tu choi duyet truc SLA, phan xu `L21`, va khoa thiet ke giai thua
2x2. Doi chieu voi trang thai repo ngay 2026-08-23 (HEAD `0259798`):

```text
dang ky truc AoI do duoc  -> DA XONG o amendment 23-49c.
                             sha256(measurements/aoi_model_v7.py)
                               = b6e55a7faceac3b2c736b304ec310a5fc537f000ba2715ff7e473811f737f151
                             nhan = measured_v7_uniform, status = ACTIVE.
                             (Ban huong dan ghi sha 856cce97... va nhan
                              measured_v7_renewal; ca hai KHONG ton tai trong
                              repo nay. Chuoi measured_v7_renewal chi xuat hien
                              trong docstring vi du o measurements/validity.py:22.)

tu choi duyet truc SLA     -> DA XONG. approved_for_live.sla_axis = [] va
                              phan xu duoc ghi o G23-123 + G23-140.

thiet ke giai thua 2x2     -> KHONG ap dung nua. Lesson 23.20 DA DONG
                              (commit 12ef8fe). Dot 1/2/3 da chay vao
                              SUPERSEDED/. Dot 4 bi chan boi S14 -- xem `L41`.

phan xu `L21`              -> CHUA LAM. Day la pham vi DUY NHAT cua ban nay.
```

Ghi lai doi chieu nay o day co chu dich: mot ban ke hoach lech pha voi repo la
mot su kien phai de lai dau vet, khong phai mot thu de sua lang le. Neu khong,
lan sau khong ai biet vi sao amendment 23-50 nho hon du kien.

## 2. Phan xu

```text
00p-amendment-15.md:144   "Khong gian hanh dong hieu dung la 3..."   DINH NGHIA
04-baselines.md:365       "Khong gian hanh dong hieu dung la 3..."   TRICH DAN
00s-amendment-18.md:139   "alpha/3 vs alpha/4 da dong boi Amd 23-16; pruning
                           action chet..."                           han che KHAC
```

Theo Quy tac cap ma #3 cua `LIMITS.md` -- *mot ma, mot han che; hai cho mo ta
cung mot han che thi mot la DINH NGHIA, cho kia chi TRICH DAN*:

```text
QUYET DINH: hai dong dau GIU ma L21.
            dong thu ba duoc cap ma moi L43.
```

Xac minh bang may, khong bang mat. Ham `_limit_definitions()` chuan hoa noi dung
thanh 40 ky tu dau, chu thuong, gom khoang trang. Ket qua do duoc:

```text
00p-amendment-15.md 144  'khong gian hanh dong hieu dung la 3 tron'
04-baselines.md     365  'khong gian hanh dong hieu dung la 3 tron'   <- TRUNG
00s-amendment-18.md 139  'alpha/3 vs alpha/4 da dong boi amendment'   <- KHAC
```

Hai dong dau trung nhau TUNG KY TU sau chuan hoa. Do la bang chung dinh
nghia-va-trich-dan, khong phai suy doan tu viec doc.

## 3. Vi sao L43 chu khong phai L39

Khi va cham duoc phat hien (Lesson 23.19 Task A, 2026-08-22) so ke tiep la
`L39`. Nhung tu do den nay `L39`, `L40`, `L41`, `L42` DA duoc cap:

```text
  L39   amendment 23-49d muc 2   phan du M-125b / hinh hoc bin
  L40   29-waves-2-3-and-bin-geometry.md muc 4   Dot 2 phu thuoc nguong SLA
  L41   amendment 23-49f muc 3   live_region_sweep phu thuoc --prepare-sla
  L42   amendment 23-49f muc 1   ban sao row-selection trong cell_matrices.py
```

(Bon dong tren duoc THUT LE co chu dich. Ban nhap dau tien khong thut le, va
`test_no_duplicate_limit_ids` do ngay: mot dong bat dau bang `L39` roi hai
khoang trang la mot DINH NGHIA theo `_limit_definitions()`, nen viec chi
TRICH DAN bon ma nay da vo tinh gan cho chung noi dung thu hai. Doi chung
duong khong co y dinh, ghi lai vi no chung minh cai chan dang hoat dong.)

Quy tac cap ma #1 cam tai su dung so. Nen:

```text
QUYET DINH: ma phan xu lay so ke tiep tai thoi diem KY (L43),
            khong phai tai thoi diem PHAT HIEN (L39).
            So ke tiep sau ban nay: L44.
```

Day chinh la co che sinh ra va cham ban dau: mot so duoc "danh dau truoc" trong
dau ai do roi bi cap cho viec khac. Khong danh dau truoc; doc so tai thoi diem ky.

## 4. Tai lieu da ky KHONG duoc sua

`00p-amendment-15.md`, `04-baselines.md`, `00s-amendment-18.md` deu DA KY.
Dong 139 cua `00s-amendment-18.md` VAN mang chuoi `L21` sau ban nay. Khong sua
mot ky tu nao trong ba file do.

Vi vay anh xa phai song o noi khac, va no song o HAI noi:

```text
docs/phase-23/LIMITS.md                          bang (dong L43) + muc "Va cham"
test/test_limits_ledger.py :: ADJUDICATED_ALIAS  anh xa may doc duoc
```

Hai noi nay bi KHOA vao nhau boi `test_adjudicated_aliases_are_documented`.
Nguyen tac: **mot quyet dinh khong duoc chi song trong test.** Neu ai do (ke ca
tac gia, ba thang sau) go `ADJUDICATED_ALIAS` ra ma quen `LIMITS.md`, hoac
nguoc lai, test do.

Ban nhap DAU cua `test_adjudicated_aliases_are_documented` chi kiem
`new in txt` -- "chuoi L43 co xuat hien dau do trong LIMITS.md khong". Doi
chung duong cho thay no VO HIEU: go han dong `| L43 |` khoi bang van PASS, vi
chuoi `L43` con nam trong van xuoi cua muc "Va cham". Da siet thanh: ma moi
phai co MOT DONG RIENG trong bang. Ghi lai vi day la bai hoc lap lai -- mot
phep kiem chua thay do bao gio thi chua duoc goi la phep kiem.

Them mot chan thu hai, `test_adjudicated_alias_fragments_still_match_a_real_line`:
manh 40 ky tu trong `ADJUDICATED_ALIAS` phai con khop MOT DONG THAT trong tai
lieu. Neu khong, anh xa da chet va va cham quay lai ma `test_no_duplicate_limit_ids`
khong con thay -- vi sau khi anh xa chet, hai noi dung lai roi vao cung ma `L21`
nhung `KNOWN_OPEN` gio da rong nen test SE do. Chan thu hai lam no do voi thong
diep DUNG thay vi thong diep "trung ma".

## 5. Gate mo boi amendment nay

```text
G23-143  L21 phan xu xong; KNOWN_OPEN rong va bo test van xanh
G23-144  anh xa song o hai noi va bi khoa vao nhau
G23-145  manh 40 ky tu con khop dong that -- anh xa khong chet im lang
G23-146  amendment nay la commit RIENG, co tag, truoc moi code cua 23.21
```

Chung KE TIEP `G23-142`. KHONG dung lai vung `G23-117 .. G23-122` (da cap cho
lesson `23.19F` o amendment 23-49a) -- do la va cham ma thu NAM va khong duoc
lap lai o day.

## 6. Dieu KHONG lam trong amendment nay

```text
- KHONG sua ba tai lieu da ky de go va cham          (muc 4)
- KHONG dang ky truc nao          -- da xong o 23-49c (muc 1)
- KHONG duyet truc nao vao approved_for_live
                                  -- truc SLA (S14) van bi tu choi den 23.21
- KHONG sua measurements/aoi_model_v7.py  -- doi sha se lam nhan tro ve
                                             UNREGISTERED va do test 23.17
- KHONG chay mot thi nghiem nao; ban nay chi cham vao so sach
```

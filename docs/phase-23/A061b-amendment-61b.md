# AMENDMENT 23-61b -- Chan va cham dich va don anh artifact legacy

Ngay ky : 2026-08-24
Lesson  : 23.21j (hau kiem custody, truoc Viec 3)
Loai    : PHAN QUYET THE HE + CHAN GHI DE + SUA INPUT SONG
Prereq  : amendment-61, `7331e84`

Amendment 62 van de danh cho Lesson 23.21h (Viec 3). Ban nay la phu luc cua
61 vi no phan xu bang chung moi tim thay trong khi kiem G23-223.

## 1. Gate khoa truoc code

```text
G23-224  tier_results phai DUNG truoc moi mutation neu mot dich da ton tai
         hoac hai move cung khai mot dich. Doi chung: dich gia phai lam gate DO,
         source va destination deu giu nguyen.

G23-225  trong source song cert/measurements/tools, moi cell legacy Phase 22
         (mode, rho_bar) chi anh xa toi DUNG MOT parquet literal. Doi chung L85
         voi hai ten cua poisson@0.925 phai lam gate DO.
```

## 2. L82 -- phan quyet theo THE HE

Bon report/parquet sau co cung cua so 13/08 04:33--04:35 UTC, cung
`git_hash=f95c6bee`, `git_dirty=true` va builder
`0f534288afa14c87...`:

```text
cbr@0.700          04:34:57
poisson@0.700      04:35:21
poisson@0.925      04:33:45
poisson@0.925 V3   04:35:45
```

Rieng `poisson@0.700` co report the he sau ngay 21/08 10:10:48, builder
`f02b1d1cf1237450...`; hai artifact eight-cell da ghim digest the he sau
`ec49deb8...`, trong khi file hien tai la `2267423d...` cua the he 13/08.

Do do ba file khong co digest lich su rieng duoc phan loai:

```text
UNKNOWN -> VERIFIED_SUPERSEDED_GENERATION
```

Nghia chinh xac: biet chung thuoc lo 13/08 da bi thay cho dau vao canonical
eight-cell/Phase 23. Day la bang chung cap LO, khong phai tuyen bo rang moi
artifact Phase 22 lich su tung doc lo 13/08 deu sai. Hanh dong khong doi: cam
tai dung. Bon trang thai nay la VERIFIED_ORIGINAL / NOT_ORIGINAL /
VERIFIED_SUPERSEDED_GENERATION / UNKNOWN (hien rong).

## 3. L83/L86 -- co che va blast radius

Tai commit phan tang `5e1837f`, `tools/tier_results.py` dung `git mv -f` cho
file tracked va `os.replace` cho file ignored. Ca hai cho phep ghi de dich;
`os.replace` giu mtime nguon. Co che khop ca digest bi lui tu the he 21/08 ve
13/08 va mtime hien tai 13/08.

Quet report cung stem/the he cho thay:

```text
1  va cham that o Phase 22: poisson@0.700, hai report cung tang
16 cap Phase-21R hop le: self_calibrated o SUPERSEDED, exogenous S-B o LIVE
```

Chan hai lop:

1. Preflight `lexists(dst)` + dich lap trong plan, chay truoc ca `--map-out`.
2. Bo `-f`. File ignored dung hard-link atomic roi unlink. Neu dich xuat hien
   sau preflight, link fail thay vi ghi de. Neu crash giua hai buoc, hai ten
   cung tro mot inode/byte; co du thua ten nhung khong mat byte.

## 4. G23-224 -- ket qua

```text
test_G23_224_existing_destination_stops_before_any_move       PASS
test_no_replace_move_keeps_atomic_publication_without_clobber PASS
test_no_replace_move_rejects_a_racing_destination             PASS
```

Doi chung duong xac nhan return code 2, thong bao co ca source/destination,
hai noi dung byte giu nguyen va file map khong duoc tao.

## 5. L85/G23-225 -- mot cell, mot parquet canonical

Truoc sua:

```text
eight_cell_sweep       poisson@0.925 -> calib_set_v3.parquet
phase23_cell_margins   poisson@0.925 -> calib_set_v3_poisson_0.925.parquet
```

Sau sua, ca hai doc `calib_set_v3.parquet` (14/08, digest historical khop).
Metadata cua ten legacy nay nam o `calib_set_v3_report.json`, nen resolver
chap nhan ca `<stem>.json` va `<stem>_report.json`.

Lint G23-225 doc AST cua `cert/*.py`, `measurements/*.py`, `tools/*.py`, chi
nhan string literal la mot path Phase 22 hoan chinh. Mau/profile/AoI Phase-21R
khong bi gom nham vao cell legacy. Doi chung hai literal L85 tao dung mot
conflict `poisson@0.925`; source sau sua khong con conflict.

Tac dong len ket qua da cong bo duoc do truc tiep bang cach chay ba ham tren
mapping cu va mapping canonical:

```text
G23-17a  all diffs=2  semantic/numeric diffs=0
G23-17b  all diffs=2  semantic/numeric diffs=0
G23-17c  all diffs=4  semantic/numeric diffs=0
```

Khac biet chi la `artifact`, `artifact_sha256`, `metadata.path` va
`metadata.sha256`. Cac artifact cu trong SUPERSEDED giu nguyen nhu lich su;
khong ghi de chung sau khi sua source. Ba phep so nay la regression test
`test_G23_225_canonical_input_preserves_published_numbers`, khong chi la mot
lan kiem thu cong.

## 6. L87 -- pham vi backup

Ban sao `C:\Users\VAN TAI\dt4n-evidence-backup-2026-08-24` va WSL VHDX gan
nhu chac cung tren o C:. No chong duoc loi logic (dung lop L83/L86), xoa
nham va hong ext4/VHDX; no khong chong hong dia vat ly, mat may, trom/chay.
Chua co tuyen bo backup hai thiet bi. Upload Drive/Zenodo la buoc ngoai
`[1]--[3]`, can tai khoan/DOI va khong duoc gia lap la da lam.

## 7. Xac minh chay duoc

```text
target G23-224/G23-225/G23-17       9 passed
ledger + dangling/custody lien quan 42 passed, 1 skipped, 3 deselected
full default suite                  1398 passed, 42 skipped, 11 deselected
                                     484.70 s (08:04)
custody rieng                       3 passed, 5 deselected
git diff --check                    PASS
```

Ba CLI G23-17a/b/c cung chay thanh cong voi input canonical va ghi JSON tam;
cac bang so chinh van la swing `0.117878` cho poisson@0.925 (17a),
`p(a*=P1)=0.659724` (17b), va `regret_neo=1.767461` (17c).

## 8. Ket luan

```text
G23-224 PASS  ghi de im lang bi chan ca preflight lan race sau preflight
G23-225 PASS  source song chi con mot path cho moi cell legacy
L82      SUA   3 VERIFIED_SUPERSEDED_GENERATION, UNKNOWN hien rong
L83/L86 SUA   nguyen nhan cu the + blast radius 1
L85      DONG  mapping song da thong nhat, ket qua so hoc khong doi
L87      MO    chua co backup tren thiet bi/remote doc lap
```
